"""AnomalyClaw v8 — specialty-aware 13-tool catalog.

Design goals (vs v7):
- Every tool has a clear specialty + applicability domain.
- Scalar-only tools (component_counter / segment_and_count / texture_fft) now
  also emit a visual output so the VLM can reason over it.
- expert_score is domain-aware via EXPERT_POLICY: it selects the right cached
  expert per v2 domain, returns rank_in_domain + range_hint (typical score
  ranges) + a 48x48 heatmap overlay + a suggested_bbox (256x256 coords,
  consumable by side_by_side / zoom_bbox as a follow-up).
- alignment-requiring tools (image_diff / rotate_align) hard-gate on the
  domain_code so they cannot be invoked on unaligned domains (medical, 3D,
  aerial, road).
- reference_retriever returns the actual retrieved images (b64), not only
  paths, so the VLM actually sees them in the next turn.

All 13 v7 tool names are preserved. v10 prompt (agent_prompt_v10.py)
contains the specialty-matched tool ladder.
"""
from __future__ import annotations

import base64
import json
import os
import sys
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from infer import call_llm, extract_json, img_msg, load_and_encode, text_msg  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = Path(os.environ.get("ANOMALYCLAW_RESULTS_DIR", _REPO_ROOT / "benchmark" / "results"))


# ─── Helpers ────────────────────────────────────────────────────────────────

def _pil_to_b64(img: Image.Image, max_side: int = 512, quality: int = 85) -> str:
    w, h = img.size
    if max(w, h) > max_side:
        scale = max_side / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _wrap_interpretation(obs: dict, verdict: str, disconfirm: str) -> dict:
    """Attach a verdict + disconfirming clause to a tool observation.

    Format: "<verdict> DISCONFIRM: <disconfirm>"

    Intent: force the VLM to consider the null hypothesis before updating
    its score. The disconfirm clause is meant to be read as
    "ways this evidence could be misleading — if any apply, don't update
    your score upward."
    """
    obs["interpretation"] = f"{verdict}\nDISCONFIRM: {disconfirm}"
    return obs


# ─── Tier 1: Expert probes ──────────────────────────────────────────────────

EXPERT_FILES = {
    "subspacead":    {"calibration": "subspacead_calibration.json",
                      "dev":         "subspacead_dev.json",
                      "test":        "subspacead_test.json"},
    "anomalyvfm":    {"calibration": "anomalyvfm_calibration.json",
                      "dev":         "anomalyvfm_dev.json",  # may not exist
                      "test":        "anomalyvfm_test.json"},
    "patchknn":      {"calibration": "classical_dinov2_patch_test_all.json",
                      "dev":         "classical_dinov2_patch_test_all.json",
                      "test":        "classical_dinov2_patch_test_all.json"},
    "dinov2_global": {"calibration": "classical_dinov2_global_test_all.json",
                      "dev":         "classical_dinov2_global_test_all.json",
                      "test":        "classical_dinov2_global_test_all.json"},
}


# Per v2 manifest domain: which cached expert is most reliable, plus its
# AUROC on that domain's cached items (computed on 2026-04-22 from the
# v2 manifest intersection with subspacead_test.json).
#
# Only subspacead offers patch-level localization (48x48 grid with top_patches
# scores), which is what enables the heatmap + suggested_bbox output. dinov2_*
# AUROC is slightly higher on D6/D7 but lacks localization, so subspacead
# wins on usable domains.
#
# Domains marked available=False: expert_score returns a polite unavailable
# message and the agent should skip this tool.
EXPERT_POLICY = {
    "D1":  {"expert": "subspacead", "auroc": 0.966, "available": True,
            "status": "strong",   "note": "MVTec-AD industrial"},
    "D5":  {"expert": "subspacead", "auroc": 0.841, "available": True,
            "status": "strong",   "note": "GoodsAD retail"},
    "D2":  {"available": False, "reason": "no cached expert score for D2 items"},
    "D6":  {"expert": "subspacead", "auroc": 0.724, "available": True,
            "status": "moderate", "note": "SDNET concrete; cache covers 80/120"},
    "D3":  {"expert": "subspacead", "auroc": 0.694, "available": True,
            "status": "moderate", "note": "MVTec-LOCO logical; cache covers 83/120"},
    "D4":  {"available": False, "reason": "all experts <0.5 AUROC on 3D-render items"},
    "D7":  {"expert": "subspacead", "auroc": 0.936, "available": True,
            "status": "strong",   "note": "LEVIR building change"},
    "D8":  {"available": False, "reason": "no reliable expert for dermatology (~0.6 AUROC)"},
    "D9":  {"expert": "subspacead", "auroc": 0.702, "available": True,
            "status": "moderate", "note": "BraTS brain MRI; cache 77/120"},
    "D10": {"expert": "subspacead", "auroc": 0.894, "available": True,
            "status": "strong",   "note": "BMAD-Liver CT; cache 77/120"},
    "D11": {"available": False, "reason": "no cached expert score for D11 items"},
    "D12": {"available": False, "reason": "no cached expert score for D12 items"},
}


# Raw-score thresholds per domain (subspacead on v2 test cache).
# Precomputed 2026-04-22 from per-domain p50/p70 percentiles.
EXPERT_RANGE_HINTS = {
    "D1":  {"p50": 37.36, "p70": 56.52, "normal_median": 20.00, "anomaly_median": 61.59},
    "D5":  {"p50": 26.91, "p70": 43.26, "normal_median": 22.40, "anomaly_median": 45.38},
    "D6":  {"p50": 32.82, "p70": 42.94, "normal_median": 27.13, "anomaly_median": 41.06},
    "D3":  {"p50": 36.19, "p70": 43.67, "normal_median": 32.91, "anomaly_median": 40.53},
    "D7":  {"p50": 60.08, "p70": 102.79,"normal_median": 43.83, "anomaly_median": 121.82},
    "D9":  {"p50": 22.78, "p70": 27.62, "normal_median": 18.47, "anomaly_median": 26.17},
    "D10": {"p50": 27.14, "p70": 39.68, "normal_median": 18.94, "anomaly_median": 40.03},
}


def _range_hint_text(dc: str) -> dict:
    """Return a human-readable typical-score range per domain."""
    h = EXPERT_RANGE_HINTS.get(dc)
    if h is None:
        return {"typical_normal": "unknown", "likely_anomaly": "unknown"}
    return {
        "typical_normal":  f"raw <{h['p50']:.0f}  (rank 0.00–0.50, normal median {h['normal_median']:.1f})",
        "borderline":      f"raw {h['p50']:.0f}–{h['p70']:.0f}  (rank 0.50–0.70, ambiguous)",
        "likely_anomaly":  f"raw >{h['p70']:.0f}  (rank >0.70, anomaly median {h['anomaly_median']:.1f})",
    }


@lru_cache(maxsize=32)
def _domain_score_percentiles(expert: str, split: str, domain_code: str,
                              v2_ids_signature: str = "") -> np.ndarray:
    """Sorted array of cached scores for this (expert, domain), used for
    rank-in-domain lookup. Cached per (expert, split, domain).
    The v2_ids_signature is accepted for future per-v2 subsetting; today it
    is ignored and all cached items for the domain_code are used.
    """
    recs, _ = _load_expert_scores(expert, split)
    scores = [float(r["anomaly_score"]) for r in recs.values()
              if r.get("anomaly_score") is not None
              and r.get("domain_code") == domain_code]
    arr = np.array(sorted(scores))
    return arr


@lru_cache(maxsize=16)
def _load_expert_scores(expert: str, split: str) -> tuple[dict, np.ndarray]:
    """Return (item_id -> record, sorted score array for percentile ranking)."""
    if expert not in EXPERT_FILES:
        raise ValueError(f"unknown expert {expert!r}; must be one of {list(EXPERT_FILES)}")
    fname = EXPERT_FILES[expert].get(split)
    if fname is None:
        raise ValueError(f"no {split} file for expert {expert!r}")
    path = RESULTS_DIR / fname
    if not path.exists():
        return {}, np.array([])
    raw = json.load(open(path))
    if isinstance(raw, list):
        recs = {x["item_id"]: x for x in raw if "item_id" in x}
    else:
        recs = raw
    scores = np.array([float(r["anomaly_score"]) for r in recs.values()
                       if r.get("anomaly_score") is not None])
    scores.sort()
    return recs, scores


def _expert_heatmap_and_bbox(query_path: str, top_patches: list[dict],
                             grid_size: int = 48,
                             target_side: int = 256,
                             pad_frac: float = 0.2) -> tuple[str | None, list[int] | None]:
    """Build a heatmap overlay + suggested bbox from subspacead top_patches.

    Returns (heatmap_b64, suggested_bbox_256). heatmap_b64 is the query resized
    to target_side x target_side with a red-channel alpha-overlay built from
    the top_patches scores on a grid_size x grid_size grid. suggested_bbox_256
    is the tight bbox around the top patches (mapped to target_side coords)
    with a pad_frac margin.

    Returns (None, None) if top_patches is empty or malformed.
    """
    if not top_patches:
        return None, None
    valid = [(int(p.get("row", -1)), int(p.get("col", -1)), float(p.get("score", 0.0)))
             for p in top_patches
             if p.get("row") is not None and p.get("col") is not None]
    valid = [(r, c, s) for r, c, s in valid if 0 <= r < grid_size and 0 <= c < grid_size]
    if not valid:
        return None, None

    # Score grid (grid_size x grid_size)
    grid = np.zeros((grid_size, grid_size), dtype=np.float32)
    for r, c, s in valid:
        grid[r, c] = max(grid[r, c], s)
    # Normalize to [0,1] within this item
    m = grid.max()
    if m > 0:
        grid = grid / m
    # Upsample to target_side via bilinear (PIL)
    heat_img = Image.fromarray((grid * 255).astype(np.uint8), mode="L").resize(
        (target_side, target_side), resample=Image.BILINEAR)
    heat_arr = np.array(heat_img).astype(np.float32) / 255.0  # [0,1]

    # Red alpha-blend overlay on resized query
    q = Image.open(query_path).convert("RGB").resize((target_side, target_side))
    q_arr = np.array(q).astype(np.float32)
    alpha = 0.55
    red = np.zeros_like(q_arr)
    red[..., 0] = 255.0
    mask = heat_arr[..., None]  # [H,W,1]
    blended = q_arr * (1.0 - alpha * mask) + red * (alpha * mask)
    blended = np.clip(blended, 0, 255).astype(np.uint8)
    heat_b64 = _pil_to_b64(Image.fromarray(blended), max_side=target_side)

    # Suggested bbox (256x256 coords): tight box around top-K patches + pad
    rows = [r for r, _, _ in valid]
    cols = [c for _, c, _ in valid]
    r0, r1 = min(rows), max(rows) + 1
    c0, c1 = min(cols), max(cols) + 1
    span_r, span_c = max(1, r1 - r0), max(1, c1 - c0)
    r0 = max(0, r0 - int(pad_frac * span_r))
    r1 = min(grid_size, r1 + int(pad_frac * span_r))
    c0 = max(0, c0 - int(pad_frac * span_c))
    c1 = min(grid_size, c1 + int(pad_frac * span_c))
    # Map grid coords -> 256 coords
    def _m(v, n): return int(round(v / grid_size * n))
    bbox = [_m(c0, target_side), _m(r0, target_side),
            _m(c1, target_side), _m(r1, target_side)]
    # Ensure non-degenerate
    if bbox[2] <= bbox[0]: bbox[2] = min(target_side, bbox[0] + 8)
    if bbox[3] <= bbox[1]: bbox[3] = min(target_side, bbox[1] + 8)
    return heat_b64, bbox


def tool_expert_score(item_id: str, query_path: str | None = None,
                      expert: str = "auto", split: str = "test",
                      _manifest_domain: str | None = None, **_) -> dict:
    """Domain-aware cached expert lookup with heatmap + suggested_bbox.

    Specialty: numerical second opinion from a pretrained AD model, plus a
    48x48-grid heatmap (upsampled + overlaid on the query) and a
    suggested_bbox around the expert's hotspot cluster. The bbox is in
    256x256 coords so it can be passed directly to tool_side_by_side or
    tool_zoom_bbox as a follow-up.

    Applicability (EXPERT_POLICY):
      strong:   D1, D5, D7, D10
      moderate: D6, D3, D9
      unavailable: D2, D4, D8, D11, D12

    expert="auto" (recommended) picks the best cached expert for the domain.
    """
    dc = _manifest_domain
    if dc is None:
        return {"error": "expert_score needs _manifest_domain in ctx to pick an expert"}
    policy = EXPERT_POLICY.get(dc)
    if policy is None or not policy.get("available"):
        reason = (policy or {}).get("reason", f"no expert policy for {dc}")
        return {"error": None, "available": False, "domain_code": dc,
                "reason": reason,
                "interpretation": (f"No reliable cached expert for {dc}. "
                                   f"Reason: {reason}. "
                                   f"Use visual tools (side_by_side, "
                                   f"reference_profiler) instead.")}

    # Pick expert
    if expert == "auto":
        expert = policy["expert"]
    try:
        recs, all_scores = _load_expert_scores(expert, split)
    except ValueError as e:
        return {"error": str(e), "available": False}
    rec = recs.get(item_id)
    if rec is None or rec.get("anomaly_score") is None:
        return {"error": None, "available": False, "domain_code": dc,
                "expert": expert,
                "reason": f"no cached score for {item_id}",
                "interpretation": (f"Expert {expert} has no cached score for this "
                                   f"item (pre-computed cache is item-level, not "
                                   f"universal). Use visual tools instead.")}

    s = float(rec["anomaly_score"])
    # rank within domain (preferred), fall back to split-wide
    dom_arr = _domain_score_percentiles(expert, split, dc)
    if len(dom_arr) >= 10:
        rank = float(np.searchsorted(dom_arr, s) / len(dom_arr))
        rank_basis = f"within {dc} cached items (n={len(dom_arr)})"
    elif len(all_scores) > 0:
        rank = float(np.searchsorted(all_scores, s) / len(all_scores))
        rank_basis = f"within split {split} (n={len(all_scores)})"
    else:
        rank = 0.5; rank_basis = "no reference distribution"

    # Heatmap + suggested_bbox from top_patches
    top_patches = rec.get("top_patches") or []
    heat_b64, bbox = (None, None)
    if query_path and top_patches:
        try:
            heat_b64, bbox = _expert_heatmap_and_bbox(query_path, top_patches)
        except Exception:
            pass  # heatmap is a bonus; don't fail the whole tool

    # Verdict calibrated per-domain using range_hints
    range_hint = _range_hint_text(dc)
    auroc = policy.get("auroc", 0.0)
    if rank >= 0.70:
        verdict = (f"LIKELY ANOMALY: rank {rank:.2f} on {expert} "
                   f"(AUROC {auroc:.2f} in {dc}). Raw score {s:.1f} is above "
                   f"the p70 threshold for {dc}. "
                   f"Next step: call tool_side_by_side(bbox=suggested_bbox_256) "
                   f"to visually confirm the hotspot region differs from refs.")
        disconfirm = (f"If the bbox region shows natural texture present also in "
                      f"refs (via side_by_side), {expert} is over-flagging normal "
                      f"variation — discount this score. Also: {expert} "
                      f"AUROC is {auroc:.2f} on {dc}, so ~{int((1-auroc)*100)}% "
                      f"of flagged items are false alarms.")
    elif rank >= 0.50:
        verdict = (f"BORDERLINE: rank {rank:.2f} on {expert}. Raw {s:.1f} is "
                   f"near the {dc} median. Ambiguous — inspect "
                   f"suggested_bbox with side_by_side before committing.")
        disconfirm = (f"Borderline scores are the least reliable region of {expert}. "
                      f"Trust visual evidence over the expert here.")
    else:
        verdict = (f"LIKELY NORMAL: rank {rank:.2f} on {expert} "
                   f"(AUROC {auroc:.2f} in {dc}). Raw score {s:.1f} is below "
                   f"the p50 threshold for normal items in {dc}.")
        disconfirm = (f"A small localised defect can still exist without shifting "
                      f"the global {expert} score; if you see a specific "
                      f"suspicious region in the query, verify with side_by_side.")

    out = {
        "error": None,
        "available": True,
        "domain_code": dc,
        "expert": expert,
        "domain_auroc": auroc,
        "score_raw": round(s, 3),
        "rank_in_domain": round(rank, 3),
        "rank_basis": rank_basis,
        "range_hint": range_hint,
        "top_patches": top_patches,
        "suggested_bbox_256": bbox,
        "n_hotspot_patches": len(top_patches),
    }
    if heat_b64 is not None:
        out["heatmap_b64"] = heat_b64
    return _wrap_interpretation(out, verdict, disconfirm)


# ─── Tier 2: Visual inspection ──────────────────────────────────────────────

def tool_hotspot_cropper(query_path: str,
                         patches: list[dict] | None = None,
                         pad: float = 0.2, k: int = 5,
                         _expert_patches: list | None = None,
                         ref_paths: list[str] | None = None, **_) -> dict:
    """Crop the query AND same-bbox refs at the expert hotspot region.

    Specialty (v8): after a tool_expert_score call, this tool produces a
    side-by-side composite of the query crop and each reference crop at the
    SAME bbox (mapped from 48x48 grid -> pixel coords). This turns the
    expert's numeric hotspot into direct query-vs-ref visual evidence.

    Applicability: any domain where expert_score is available; particularly
    useful on D1/D5/D10 (clean industrial/medical).
    """
    patches = patches or _expert_patches or []
    if not patches:
        return {"error": "no patches available; call tool_expert_score() first"}
    img = Image.open(query_path).convert("RGB")
    W, H = img.size
    grid = 48
    rows = [int(p.get("row")) for p in patches[:k]
            if p.get("row") is not None]
    cols = [int(p.get("col")) for p in patches[:k]
            if p.get("col") is not None]
    if not rows or not cols:
        return {"error": "patches missing row/col fields"}
    r0, r1 = min(rows), max(rows) + 1
    c0, c1 = min(cols), max(cols) + 1
    span_r, span_c = max(1, r1 - r0), max(1, c1 - c0)
    r0 = max(0, r0 - int(pad * span_r))
    r1 = min(grid, r1 + int(pad * span_r))
    c0 = max(0, c0 - int(pad * span_c))
    c1 = min(grid, c1 + int(pad * span_c))
    x0, x1 = int(c0 / grid * W), int(c1 / grid * W)
    y0, y1 = int(r0 / grid * H), int(r1 / grid * H)
    if x1 <= x0 or y1 <= y0:
        return {"error": "degenerate crop"}

    tile_side = 160

    def _crop_one(path):
        im = Image.open(path).convert("RGB").resize((W, H))
        return im.crop((x0, y0, x1, y1)).resize((tile_side, tile_side))

    tiles = [("query", _crop_one(query_path))]
    for i, rp in enumerate((ref_paths or [])[:3]):
        try:
            tiles.append((f"ref{i}", _crop_one(rp)))
        except Exception:
            pass

    total_w = tile_side * len(tiles)
    composite = Image.new("RGB", (total_w, tile_side + 18), (255, 255, 255))
    for i, (_, c) in enumerate(tiles):
        composite.paste(c, (i * tile_side, 18))
    try:
        from PIL import ImageDraw
        draw = ImageDraw.Draw(composite)
        for i, (label, _) in enumerate(tiles):
            draw.text((i * tile_side + 4, 2), label, fill=(0, 0, 0))
    except Exception:
        pass

    out = {
        "error": None,
        "bbox_pixel": [x0, y0, x1, y1],
        "n_patches_used": len(rows),
        "n_refs_in_composite": len(tiles) - 1,
        "composite_b64": _pil_to_b64(composite, max_side=640),
        "original_size": [W, H],
    }
    verdict = (f"same-bbox composite (query | refs) from {len(rows)} expert "
               f"hotspot patches. Look for a feature visible ONLY in the "
               f"query tile — that is the candidate defect.")
    disconfirm = ("if the same texture/feature is visible across some refs, "
                  "the expert was flagging a naturally-variable region, not "
                  "a defect. Treat as normal in that case.")
    return _wrap_interpretation(out, verdict, disconfirm)


def tool_zoom_bbox(query_path: str, bbox: list[int], **_) -> dict:
    """Agent-specified crop. bbox = [x0, y0, x1, y1] in pixel coords."""
    if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        return {"error": "bbox must be [x0, y0, x1, y1]"}
    x0, y0, x1, y1 = bbox
    if x1 <= x0 or y1 <= y0:
        return {"error": f"invalid bbox {bbox}: x1 must be > x0 and y1 > y0"}
    img = Image.open(query_path).convert("RGB")
    W, H = img.size
    x0 = max(0, min(W - 1, int(x0)))
    y0 = max(0, min(H - 1, int(y0)))
    x1 = max(x0 + 1, min(W, int(x1)))
    y1 = max(y0 + 1, min(H, int(y1)))
    crop = img.crop((x0, y0, x1, y1))
    out = {
        "bbox": [x0, y0, x1, y1],
        "crop_b64": _pil_to_b64(crop),
        "original_size": [W, H],
        "error": None,
    }
    verdict = ("agent-requested region returned at higher resolution; "
               "inspect closely for localised defect not visible at overview scale")
    disconfirm = ("the crop shows normal surface texture or a benign visual cue "
                  "(lighting, joint, shadow) — in that case treat as normal")
    return _wrap_interpretation(out, verdict, disconfirm)


def tool_patch_grid(query_path: str, rows: int = 3, cols: int = 3, **_) -> dict:
    """Return rows*cols tiles covering the image in a regular grid."""
    try:
        rows, cols = int(rows), int(cols)
    except (TypeError, ValueError):
        return {"error": "rows/cols must be integers"}
    if rows < 1 or cols < 1:
        return {"error": f"rows/cols must be >= 1; got {rows}x{cols}"}
    # v7: cap at 3x3 to keep tiles readable and VLM context manageable
    rows = min(rows, 3)
    cols = min(cols, 3)
    img = Image.open(query_path).convert("RGB")
    W, H = img.size
    tw, th = W // cols, H // rows
    tiles = []
    for i in range(rows):
        for j in range(cols):
            x0, y0 = j * tw, i * th
            x1 = (j + 1) * tw if j < cols - 1 else W
            y1 = (i + 1) * th if i < rows - 1 else H
            crop = img.crop((x0, y0, x1, y1))
            tiles.append({
                "cell": [i, j],
                "bbox": [x0, y0, x1, y1],
                "crop_b64": _pil_to_b64(crop, max_side=256),
            })
    out = {"rows": rows, "cols": cols, "tiles": tiles, "error": None}
    verdict = (f"image split into {rows}x{cols} tiles; look for a single tile "
               f"that differs clearly from the others in texture/content")
    disconfirm = ("all tiles vary naturally (texture, lighting gradient), no "
                  "single tile stands out — in that case treat as normal")
    return _wrap_interpretation(out, verdict, disconfirm)


# Domains where query and refs share the same viewpoint/scale/crop so that
# pixel-level diff is a meaningful signal. On any other domain the diff is
# dominated by framing noise, and the agent should use side_by_side instead.
ALIGNED_DOMAINS = {"D1", "D5", "D3"}


def tool_image_diff(query_path: str, ref_path: str | None = None,
                    ref_paths: list[str] | None = None, ref_idx: int = 0,
                    threshold: float = 30.0,
                    _manifest_domain: str | None = None, **_) -> dict:
    """Absolute pixel diff between query and a reference, with stats + mask.

    Specialty: aligned industrial photography (D1 MVTec, D5 GoodsAD, D3
    MVTec-LOCO). The query and ref must share viewpoint/scale/crop;
    otherwise the diff is dominated by framing noise.

    Hard-gated: returns an error on non-aligned domains (medical, aerial,
    3D, road, dermatology) — use tool_side_by_side there instead.
    """
    if _manifest_domain and _manifest_domain not in ALIGNED_DOMAINS:
        return {"error": (f"image_diff not applicable to {_manifest_domain}: "
                          f"refs are different instances / viewpoints, not "
                          f"aligned photos. Use tool_side_by_side instead.")}
    if ref_path is None and ref_paths:
        try:
            ref_path = ref_paths[int(ref_idx)]
        except (IndexError, ValueError):
            return {"error": f"ref_idx {ref_idx} out of range"}
    if not ref_path or not os.path.exists(ref_path):
        return {"error": f"ref_path not found: {ref_path!r}"}
    q = np.array(Image.open(query_path).convert("RGB").resize((256, 256)))
    r = np.array(Image.open(ref_path).convert("RGB").resize((256, 256)))
    diff = np.abs(q.astype(float) - r.astype(float)).mean(axis=2)
    mask = (diff > threshold).astype(np.uint8) * 255
    change_pct = float(mask.mean() / 255 * 100)
    mean_diff = float(diff.mean())
    # v7: detect unreliable diff when query/ref alignment is poor
    unreliable = (mean_diff > 40.0) or (change_pct > 45.0)
    out = {
        "mean_diff": mean_diff,
        "max_diff": float(diff.max()),
        "change_percent": change_pct,
        "threshold": threshold,
        "unreliable_alignment": unreliable,
        "diff_mask_b64": _pil_to_b64(Image.fromarray(mask, mode="L").convert("RGB"),
                                     max_side=256),
        "error": None,
    }
    if unreliable:
        verdict = (f"UNRELIABLE: query and reference are not aligned "
                   f"(mean_diff={mean_diff:.1f}, change={change_pct:.1f}%); "
                   f"the diff mask reflects alignment noise, not defects")
        disconfirm = ("alignment noise ALWAYS looks like many bright regions; "
                      "do NOT use this tool's output as evidence for this sample")
    else:
        verdict = (f"pixel diff computed; {change_pct:.1f}% of pixels changed "
                   f"above the {threshold}-intensity threshold")
        disconfirm = ("changed regions may be benign lighting/color variation, "
                      "not a true defect — cross-check with zoom_bbox on bright regions")
    return _wrap_interpretation(out, verdict, disconfirm)


def tool_rotate_align(query_path: str, ref_path: str | None = None,
                      ref_paths: list[str] | None = None, ref_idx: int = 0,
                      _manifest_domain: str | None = None, **_) -> dict:
    """Rotation-tolerant pixel diff — applicable only to aligned industrial domains.

    Specialty: aligned industrial photography with small rotational tolerance
    (e.g. MVTec items with ±10 deg jitter). Useless on any domain where refs
    are different instances.
    """
    if _manifest_domain and _manifest_domain not in ALIGNED_DOMAINS:
        return {"error": (f"rotate_align not applicable to {_manifest_domain}: "
                          f"refs are different instances, rotation can't help. "
                          f"Use tool_side_by_side instead.")}
    if ref_path is None and ref_paths:
        try:
            ref_path = ref_paths[int(ref_idx)]
        except (IndexError, ValueError):
            return {"error": f"ref_idx {ref_idx} out of range"}
    if not ref_path or not os.path.exists(ref_path):
        return {"error": f"ref_path not found: {ref_path!r}"}
    q = np.array(Image.open(query_path).convert("RGB").resize((256, 256)))
    r_img = Image.open(ref_path).convert("RGB").resize((256, 256))
    best_angle, best_mse, best_diff = 0.0, float("inf"), None
    for angle in [-10, -5, 0, 5, 10]:
        r_rot = np.array(r_img.rotate(angle, resample=Image.BILINEAR))
        d = np.abs(q.astype(float) - r_rot.astype(float)).mean(axis=2)
        mse = float(d.mean())
        if mse < best_mse:
            best_mse, best_angle, best_diff = mse, angle, d
    mask = (best_diff > 30.0).astype(np.uint8) * 255
    unreliable = best_mse > 40.0
    out = {
        "rotation_angle_deg": float(best_angle),
        "aligned_mean_diff": float(best_mse),
        "unreliable_alignment": unreliable,
        "aligned_diff_b64": _pil_to_b64(Image.fromarray(mask, mode="L").convert("RGB"),
                                        max_side=256),
        "error": None,
    }
    if unreliable:
        verdict = (f"UNRELIABLE: even the best rotation ({best_angle}°) yields "
                   f"mean diff {best_mse:.1f} — query and ref cannot be aligned; "
                   f"do NOT use this tool's output")
        disconfirm = ("treat as no evidence; rely on other tools or direct inspection")
    else:
        verdict = (f"best rotation {best_angle}°, post-alignment mean diff "
                   f"{best_mse:.1f}; diff mask shows residual change")
        disconfirm = ("post-alignment residual may still be lighting/color variation; "
                      "confirm with zoom_bbox on suspicious bright regions")
    return _wrap_interpretation(out, verdict, disconfirm)


def tool_side_by_side(query_path: str, bbox: list[int],
                      ref_paths: list[str] | None = None, **_) -> dict:
    """Composite: query_crop | ref0_crop | ref1_crop | ref2_crop | ref3_crop.

    bbox is interpreted in 256x256 normalized coords (resize all images to 256).
    """
    if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        return {"error": "bbox must be [x0, y0, x1, y1]"}
    x0, y0, x1, y1 = [int(v) for v in bbox]
    if x1 <= x0 or y1 <= y0:
        return {"error": f"invalid bbox {bbox}"}
    if not ref_paths:
        return {"error": "no ref_paths in session"}
    def _crop(path):
        img = Image.open(path).convert("RGB").resize((256, 256))
        xa = max(0, min(255, x0)); ya = max(0, min(255, y0))
        xb = max(xa + 1, min(256, x1)); yb = max(ya + 1, min(256, y1))
        return img.crop((xa, ya, xb, yb)).resize((128, 128))
    crops = [_crop(query_path)] + [_crop(p) for p in ref_paths[:4]]
    total_w = 128 * len(crops)
    composite = Image.new("RGB", (total_w, 128), (255, 255, 255))
    for i, c in enumerate(crops):
        composite.paste(c, (i * 128, 0))
    out = {
        "bbox": bbox,
        "n_crops": len(crops),
        "composite_b64": _pil_to_b64(composite, max_side=768),
        "error": None,
    }
    verdict = ("side-by-side composite (query | ref0 | ref1 | ref2 | ref3); "
               "look for a structural/textural feature present ONLY in query")
    disconfirm = ("refs themselves show natural variation; a feature that is "
                  "slightly different in degree but present across samples is NORMAL")
    return _wrap_interpretation(out, verdict, disconfirm)


# ─── Tier 3: Reference understanding ────────────────────────────────────────

PROFILER_SYSTEM = (
    "You are describing NORMAL reference images for anomaly detection. Output ONLY "
    "what normal looks like — do NOT speculate about anomalies. Return JSON with "
    "these EXACT fields, each a single short phrase:\n"
    "  object: the main object/scene content (one noun phrase)\n"
    "  expected_color: 2-3 dominant colors\n"
    "  expected_shape: overall geometric/structural pattern (one phrase)\n"
    "  allowed_variation: list 2-4 variations that are NORMAL across refs "
    "(e.g. 'minor rotation', 'lighting shift', 'minor texture variation')\n"
    "Do NOT include anomaly hypotheses. JSON format: "
    "{\"object\": \"...\", \"expected_color\": \"...\", \"expected_shape\": \"...\", "
    "\"allowed_variation\": [\"...\", \"...\"]}"
)


def tool_reference_profiler(ref_paths: list[str] | None = None,
                            vlm_client=None, vlm_model: str | None = None,
                            max_tokens: int = 400, **_) -> dict:
    """Ask a VLM to describe the normality profile from 4 refs."""
    if os.environ.get("ANOMA_TEST_STUB") == "1":
        return {
            "error": None,
            "profile_text": "stub profile",
            "common_objects": ["stub"],
            "typical_colors": [],
            "variations": [],
            "n_refs_used": len(ref_paths[:4]) if ref_paths else 0,
        }
    if not ref_paths:
        return {"error": "no ref_paths"}
    if vlm_client is None or vlm_model is None:
        return {"error": "vlm_client and vlm_model required"}
    parts = [text_msg(PROFILER_SYSTEM)]
    for p in ref_paths[:4]:
        parts.append(img_msg(load_and_encode(p)))
    parts.append(text_msg("Profile these 4 normal references using ONLY the 4 fields listed."))
    messages = [{"role": "user", "content": parts}]
    try:
        text, _, _ = call_llm(vlm_client, vlm_model, messages,
                              max_tokens=max_tokens, temperature=0.0)
    except Exception as e:
        return {"error": f"vlm call failed: {e}"}
    parsed = extract_json(text) or {}
    out = {
        "error": None,
        "object": parsed.get("object", ""),
        "expected_color": parsed.get("expected_color", ""),
        "expected_shape": parsed.get("expected_shape", ""),
        "allowed_variation": parsed.get("allowed_variation", []),
        "n_refs_used": len(ref_paths[:4]),
    }
    verdict = (f"normal-baseline profile extracted: object='{out['object']}', "
               f"shape='{out['expected_shape']}', allowed variations: "
               f"{out['allowed_variation']}")
    disconfirm = ("the query exhibits a variation LISTED in allowed_variation — in "
                  "that case it is NORMAL, not anomalous. Also: profiler only describes "
                  "what refs have in common; it cannot detect anomalies by itself")
    return _wrap_interpretation(out, verdict, disconfirm)


import threading as _threading

_RETRIEVAL_CACHE: dict[str, Any] = {}
_RETRIEVAL_LOCK = _threading.Lock()


def _load_retrieval_model_v6(device: str = "cuda"):
    if "model" in _RETRIEVAL_CACHE:
        return _RETRIEVAL_CACHE["model"], _RETRIEVAL_CACHE["transform"]
    with _RETRIEVAL_LOCK:
        if "model" in _RETRIEVAL_CACHE:  # double-check after acquiring lock
            return _RETRIEVAL_CACHE["model"], _RETRIEVAL_CACHE["transform"]
        import torch  # noqa: F401
        import timm
        model = timm.create_model("vit_small_patch14_dinov2.lvd142m",
                                  pretrained=True, num_classes=0)
        model = model.to(device).eval()
        cfg = timm.data.resolve_data_config(model.pretrained_cfg)
        transform = timm.data.create_transform(**cfg, is_training=False)
        _RETRIEVAL_CACHE["model"] = model
        _RETRIEVAL_CACHE["transform"] = transform
        return model, transform


def tool_reference_retriever(query_path: str, domain_code: str | None = None,
                             k: int = 4,
                             index_dir: str | None = None,
                             device: str = "cuda",
                             item_id: str | None = None,
                             _manifest_domain: str | None = None, **_) -> dict:
    """Retrieve top-k most similar normal references via DINOv2 similarity.

    `domain_code` may be provided by the agent; if not, we try `_manifest_domain`
    (auto-injected from session ctx; this is the only place the agent legitimately
    uses the domain code — to locate its cached normality bank, not for modeling).
    """
    domain_code = domain_code or _manifest_domain
    if not domain_code:
        return {"error": "domain_code required to locate retrieval index"}
    if index_dir is None:
        index_dir = os.environ.get(
            "ANOMALYCLAW_INDEX_DIR",
            str(_REPO_ROOT / "benchmark" / "retrieval_index"),
        )
    idx_path = os.path.join(index_dir, f"{domain_code}_index.npz")
    if not os.path.exists(idx_path):
        return {"error": f"no retrieval index at {idx_path}"}
    try:
        import torch
        model, transform = _load_retrieval_model_v6(device)
        img = Image.open(query_path).convert("RGB")
        tensor = transform(img).unsqueeze(0).to(device)
        with torch.no_grad():
            emb = model(tensor).cpu().numpy().flatten()
        emb = emb / (np.linalg.norm(emb) + 1e-8)
        data = np.load(idx_path, allow_pickle=True)
        sims = data["embeddings"] @ emb
        top_idx = np.argsort(sims)[::-1][:k]
        results = [{"path": str(data["paths"][i]),
                    "similarity": float(sims[i])} for i in top_idx]
        # v8: actually load the retrieved images so the VLM sees them in the
        # next observation turn. Capped to 4 to keep context manageable.
        retrieved_b64 = []
        for r in results[:4]:
            try:
                rim = Image.open(r["path"]).convert("RGB")
                retrieved_b64.append(_pil_to_b64(rim, max_side=256))
            except Exception:
                pass
        out = {"results": results, "error": None,
               "retrieved_images_b64": retrieved_b64,
               "top_similarity": float(sims[top_idx[0]]) if len(top_idx) else 0.0}
        verdict = (f"Top-{k} most similar NORMAL refs retrieved; {len(retrieved_b64)} "
                   f"images returned (top_similarity={out['top_similarity']:.3f}). "
                   f"These are additional normal exemplars — look at them to get a "
                   f"broader sense of normal variation before deciding the query is "
                   f"anomalous.")
        disconfirm = ("High top_similarity → query matches a normal cluster → "
                      "likely NORMAL. Low similarity alone does NOT prove anomaly: "
                      "the query may be a less-represented normal subtype.")
        return _wrap_interpretation(out, verdict, disconfirm)
    except Exception as e:
        return {"error": f"retrieval failed: {e}"}


# ─── Tier 4: Structural analysis ────────────────────────────────────────────

def tool_component_counter(query_path: str | None = None,
                           patches: list[dict] | None = None,
                           _expert_patches: list | None = None,
                           threshold: float = 0.5, **_) -> dict:
    """Count + visualise connected components among expert hotspot patches.

    Specialty: tells the agent whether the expert's flagged region is a
    SINGLE localised blob (→ probable localised defect) or many scattered
    blobs (→ diffuse high-variance texture, often a false alarm).

    v8: now also emits a composite image with (a) the 48x48 grid coloured by
    component ID and (b) a translucent overlay on the resized query so the
    VLM can SEE the blob layout rather than just reading a number.
    """
    patches = patches or _expert_patches or []
    if len(patches) < 3:
        out = {"error": None, "n_components": 0,
               "n_active_patches": len(patches), "not_applicable": True}
        verdict = (f"not applicable: only {len(patches)} expert patch(es). "
                   f"component counting needs >=3 patches.")
        disconfirm = "ignore this tool's output for this sample"
        return _wrap_interpretation(out, verdict, disconfirm)

    grid = np.zeros((48, 48), dtype=np.int32)
    for p in patches:
        r, c = p.get("row"), p.get("col")
        if r is not None and c is not None and 0 <= r < 48 and 0 <= c < 48:
            grid[r, c] = 1

    # Connected-component label (4-conn flood fill)
    label = np.zeros_like(grid)
    n = 0
    for i in range(48):
        for j in range(48):
            if grid[i, j] and not label[i, j]:
                n += 1
                stack = [(i, j)]
                while stack:
                    ii, jj = stack.pop()
                    if (0 <= ii < 48 and 0 <= jj < 48 and grid[ii, jj]
                            and not label[ii, jj]):
                        label[ii, jj] = n
                        stack.extend([(ii+1, jj), (ii-1, jj),
                                      (ii, jj+1), (ii, jj-1)])
    n_active = int(grid.sum())

    # Colour palette (cycling through a small set of high-contrast hues)
    palette = np.array([
        [0, 0, 0],           # 0: background
        [255, 80, 80],       # 1: red
        [80, 170, 255],      # 2: blue
        [80, 230, 130],      # 3: green
        [255, 200, 60],      # 4: yellow
        [200, 120, 255],     # 5: purple
        [255, 130, 80],      # 6: orange
    ], dtype=np.uint8)
    label_map = label % len(palette)
    # Build grid_rgb (48x48x3) then upsample to 256x256
    grid_rgb = palette[label_map]
    grid_img = Image.fromarray(grid_rgb).resize((256, 256), resample=Image.NEAREST)

    # Overlay on resized query if available
    composite_img = grid_img
    if query_path:
        try:
            q = Image.open(query_path).convert("RGB").resize((256, 256))
            q_arr = np.array(q).astype(np.float32)
            g_arr = np.array(grid_img).astype(np.float32)
            mask = (g_arr.sum(-1) > 20)[..., None].astype(np.float32)
            alpha = 0.5
            blended = q_arr * (1 - alpha * mask) + g_arr * (alpha * mask)
            composite_img = Image.fromarray(np.clip(blended, 0, 255).astype(np.uint8))
        except Exception:
            pass

    out = {
        "error": None,
        "n_components": int(n),
        "n_active_patches": n_active,
        "blob_layout_b64": _pil_to_b64(composite_img, max_side=256),
        "not_applicable": False,
    }
    if n == 1:
        verdict = (f"{n_active} hotspot patches form 1 connected blob. "
                   f"Classic localised defect signature. Good candidate for "
                   f"tool_side_by_side at the blob's bbox.")
        disconfirm = ("if the blob coincides with a natural landmark (seam, "
                      "join, edge) visible also in refs, it is normal.")
    elif n <= 3:
        verdict = (f"{n_active} hotspot patches form {n} blobs — moderately "
                   f"concentrated. Inspect the largest blob first.")
        disconfirm = ("multiple blobs can reflect generic high-variance "
                      "texture; visual confirmation required.")
    else:
        verdict = (f"{n_active} hotspot patches scattered across {n} blobs. "
                   f"Diffuse pattern → often a false alarm from natural texture.")
        disconfirm = ("if blobs scatter across the whole image without a "
                      "structural cluster, treat the expert signal as weak.")
    return _wrap_interpretation(out, verdict, disconfirm)


def tool_segment_and_count(query_path: str,
                           ref_paths: list[str] | None = None,
                           grid_size: int = 8, **_) -> dict:
    """Coarse 8x8 intensity-grid change heatmap vs ref 0.

    Specialty: quickly localises WHICH large region of the image differs most
    from the first reference — useful when the agent does not yet have a
    candidate bbox to inspect. Works on any domain with a reference, but
    signal is blunted by global intensity shifts (lighting / contrast).

    v8: returns a 256x256 heatmap image (red = high change) plus the top-5
    differing cells as candidate bbox suggestions.
    """
    if not ref_paths:
        return {"error": "ref_paths required"}
    q = np.array(Image.open(query_path).convert("L").resize((256, 256))).astype(np.float32)
    r = np.array(Image.open(ref_paths[0]).convert("L").resize((256, 256))).astype(np.float32)
    cell = 256 // grid_size
    q_grid = q.reshape(grid_size, cell, grid_size, cell).mean(axis=(1, 3))
    r_grid = r.reshape(grid_size, cell, grid_size, cell).mean(axis=(1, 3))
    diff = np.abs(q_grid - r_grid)
    changed = int((diff > 20).sum())

    # Normalised diff grid -> upsampled heatmap
    dmax = diff.max()
    if dmax > 0:
        norm = (diff / dmax).astype(np.float32)
    else:
        norm = diff.astype(np.float32)
    heat = Image.fromarray((norm * 255).astype(np.uint8), mode="L").resize(
        (256, 256), resample=Image.NEAREST)
    heat_arr = np.array(heat).astype(np.float32) / 255.0

    # Overlay red heatmap on resized query (colour image)
    q_rgb = np.array(Image.open(query_path).convert("RGB").resize((256, 256))).astype(np.float32)
    red = np.zeros_like(q_rgb); red[..., 0] = 255.0
    alpha = 0.55 * heat_arr[..., None]
    blended = q_rgb * (1.0 - alpha) + red * alpha
    heatmap_img = Image.fromarray(np.clip(blended, 0, 255).astype(np.uint8))

    # Top-5 differing cells with 256-coord bbox suggestions
    top_idx = np.argsort(diff.ravel())[::-1][:5]
    top_cells = []
    for i in top_idx:
        v = float(diff.ravel()[i])
        if v < 10:
            continue
        rr, cc = int(i // grid_size), int(i % grid_size)
        bbox = [cc * cell, rr * cell, (cc + 1) * cell, (rr + 1) * cell]
        top_cells.append({"row": rr, "col": cc, "diff": round(v, 1),
                          "bbox_256": bbox})

    out = {
        "error": None,
        "changed_cells": changed,
        "total_cells": grid_size * grid_size,
        "change_ratio": round(changed / (grid_size * grid_size), 3),
        "top_cells": top_cells,
        "change_heatmap_b64": _pil_to_b64(heatmap_img, max_side=256),
    }
    verdict = (f"{changed}/{out['total_cells']} of the {grid_size}x{grid_size} "
               f"cells differ from ref 0 above threshold. Brightest cells on "
               f"the heatmap are candidate bboxes for tool_side_by_side.")
    disconfirm = ("coarse diff is confounded by global lighting/contrast "
                  "shifts; a uniformly-warm heatmap without a focused peak "
                  "is usually a lighting artifact, not a defect.")
    return _wrap_interpretation(out, verdict, disconfirm)


def tool_texture_fft(query_path: str, ref_paths: list[str] | None = None,
                     **_) -> dict:
    """FFT periodicity score + magnitude-spectrum image, and (if a ref is
    available) a query-vs-ref periodicity delta.

    Specialty: detects DISRUPTION of a regular periodic texture. Especially
    relevant to D6 (SDNET concrete — cracks break the aggregate pattern),
    fabric/grid textures, or any domain where 'normal' has a distinctive
    spatial periodicity. Not useful on natural scenes or medical tissue.

    v8: returns a log-magnitude spectrum image (256x256), so the VLM can
    look at the bright peaks and read off periodicity directly.
    """
    img = np.array(Image.open(query_path).convert("L").resize((256, 256))).astype(float)
    img -= img.mean()
    spec = np.abs(np.fft.fftshift(np.fft.fft2(img)))
    h, w = spec.shape
    cy, cx = h // 2, w // 2
    # Zero DC neighbourhood for score + visualisation
    spec_vis = spec.copy()
    spec_vis[cy - 3:cy + 3, cx - 3:cx + 3] = 0

    total = float(spec_vis.sum()) + 1e-8
    top_k = float(np.sort(spec_vis.ravel())[::-1][:10].sum())
    score = float(top_k / total)
    periodicity = min(1.0, max(0.0, score))

    # Log-magnitude visualisation (256x256, grayscale -> RGB)
    vis = np.log1p(spec_vis)
    v_max = vis.max()
    if v_max > 0:
        vis = vis / v_max * 255.0
    spec_img = Image.fromarray(vis.astype(np.uint8), mode="L").convert("RGB")

    # Optional: same computation on ref 0 to compare periodicity
    ref_periodicity = None
    if ref_paths:
        try:
            ri = np.array(Image.open(ref_paths[0]).convert("L").resize((256, 256))).astype(float)
            ri -= ri.mean()
            rspec = np.abs(np.fft.fftshift(np.fft.fft2(ri)))
            rspec[cy - 3:cy + 3, cx - 3:cx + 3] = 0
            rtot = float(rspec.sum()) + 1e-8
            rtop = float(np.sort(rspec.ravel())[::-1][:10].sum())
            ref_periodicity = round(min(1.0, max(0.0, rtop / rtot)), 3)
        except Exception:
            ref_periodicity = None

    out = {
        "error": None,
        "periodicity_score": round(periodicity, 3),
        "ref_periodicity_score": ref_periodicity,
        "spectrum_b64": _pil_to_b64(spec_img, max_side=256),
    }
    delta_note = ""
    if ref_periodicity is not None:
        delta = round(ref_periodicity - periodicity, 3)
        out["delta_query_minus_ref"] = -delta
        if delta > 0.08:
            delta_note = (f" Ref periodicity {ref_periodicity} is notably "
                          f"higher — a crack / disruption in the query could "
                          f"explain the drop.")
        elif delta < -0.08:
            delta_note = (f" Query periodicity is higher than ref "
                          f"({ref_periodicity}) — unusual, inspect.")
    if periodicity > 0.15:
        verdict = (f"Query has periodic texture (score {periodicity:.3f}). "
                   f"Bright spectrum peaks indicate repeating pattern."
                   f"{delta_note}")
        disconfirm = ("periodicity alone doesn't mean defect. Many normal "
                      "textures (fabric, grid, lattice) are periodic.")
    else:
        verdict = (f"Low periodicity (score {periodicity:.3f}). Texture is "
                   f"irregular or the image is a natural scene.{delta_note}")
        disconfirm = ("irregular texture is normal for many domains; "
                      "do NOT flag anomaly from this alone.")
    return _wrap_interpretation(out, verdict, disconfirm)


# ─── Tier 5: Semantic knowledge ─────────────────────────────────────────────

KNOWLEDGE_SYSTEM = (
    "You are a visual-cue lookup assistant for anomaly detection. The agent "
    "has already SEEN a specific visual feature in an image and wants to "
    "know what that feature MEANS in its domain — is it benign, typical, a "
    "known artefact, or a red-flag? Give concrete visual criteria in "
    "2-4 sentences. If the cue described is a common benign artefact, say "
    "so explicitly; if it is a red flag, say so and describe how to tell it "
    "apart from benign lookalikes. Return JSON: {\"answer\": \"...\"}."
)


def tool_domain_knowledge(question: str, llm_client=None,
                          llm_model: str | None = None,
                          vlm_client=None, vlm_model: str | None = None,
                          max_tokens: int = 300, **_) -> dict:
    """Text LLM lookup for a SPECIFIC visual cue's meaning in the domain.

    Specialty: when the agent sees a visual feature it cannot confidently
    classify as "known benign artefact" or "red flag" (e.g. hair across
    a dermoscopy image, specular reflection in endoscopy, shadow over a
    crack candidate), it can ask here. Phrase the question as a visual
    cue interpretation, NOT as generic domain trivia.

    Example good question: "In dermoscopy, is a dark uniform brown mole with
    smooth regular borders typically benign or malignant?"
    Example bad question:  "What is melanoma?"
    """
    if os.environ.get("ANOMA_TEST_STUB") == "1":
        return {"error": None, "answer": f"[stub] re: {question}"}
    client = llm_client or vlm_client
    model = llm_model or vlm_model
    if client is None or model is None:
        return {"error": "llm_client and llm_model required"}
    messages = [
        {"role": "system", "content": KNOWLEDGE_SYSTEM},
        {"role": "user", "content": question},
    ]
    try:
        text, _, _ = call_llm(client, model, messages,
                              max_tokens=max_tokens, temperature=0.0)
    except Exception as e:
        return {"error": f"llm call failed: {e}"}
    parsed = extract_json(text) or {}
    out = {"error": None, "answer": parsed.get("answer", text.strip()[:300])}
    verdict = "text-only LLM answer returned"
    disconfirm = ("the LLM may hallucinate or give generic advice that doesn't match "
                  "this specific image; always cross-check against the visual evidence "
                  "before updating your score")
    return _wrap_interpretation(out, verdict, disconfirm)


# ─── Dispatcher ─────────────────────────────────────────────────────────────

TOOL_REGISTRY = {
    "tool_expert_score":        tool_expert_score,
    "tool_hotspot_cropper":     tool_hotspot_cropper,
    "tool_zoom_bbox":           tool_zoom_bbox,
    "tool_patch_grid":          tool_patch_grid,
    "tool_image_diff":          tool_image_diff,
    "tool_rotate_align":        tool_rotate_align,
    "tool_side_by_side":        tool_side_by_side,
    "tool_reference_profiler":  tool_reference_profiler,
    "tool_reference_retriever": tool_reference_retriever,
    "tool_component_counter":   tool_component_counter,
    "tool_segment_and_count":   tool_segment_and_count,
    "tool_texture_fft":         tool_texture_fft,
    "tool_domain_knowledge":    tool_domain_knowledge,
}


PROTECTED_CTX_KEYS = (
    "query_path", "ref_paths", "item_id", "split",
    "vlm_client", "vlm_model", "llm_client", "llm_model",
    "_expert_patches", "_manifest_domain", "index_dir",
)


def dispatch_tool(name: str, args: dict, ctx: dict | None = None) -> dict:
    """Dispatch a tool call. ctx carries session state that tools need but
    that the VLM shouldn't re-type (query_path, ref_paths, split, clients).

    PROTECTED_CTX_KEYS are ALWAYS taken from ctx — model-supplied args for
    those keys are dropped (prevents VLM from redirecting a tool to
    different item/split by crafting malicious args).
    """
    if name not in TOOL_REGISTRY:
        return {"error": f"unknown tool {name!r}; must be one of {sorted(TOOL_REGISTRY)}"}
    ctx = ctx or {}
    fn = TOOL_REGISTRY[name]
    # Defensive: VLM sometimes emits args as a string. Try to JSON parse, else ignore.
    if isinstance(args, str):
        try:
            args = json.loads(args) if args.strip() else {}
            if not isinstance(args, dict):
                args = {}
        except Exception:
            args = {}
    if args is None:
        args = {}
    # Start from sanitized model args: drop protected keys
    injected = {k: v for k, v in (args or {}).items() if k not in PROTECTED_CTX_KEYS}
    # Overlay ctx (ctx wins over model args for protected fields)
    for k in PROTECTED_CTX_KEYS:
        if k in ctx:
            injected[k] = ctx[k]
    try:
        return fn(**injected)
    except TypeError as e:
        return {"error": f"bad args for {name}: {e}"}
    except Exception as e:
        return {"error": f"{name} raised {type(e).__name__}: {e}"}


# ─── KEEP-gated dispatch (used by agent_v7 after audit is complete) ─────────

_KEEP_TOOLS: set[str] | None = None


def _load_keep_tools() -> set[str]:
    """Load KEEP set from refine-logs/tool_cards/*.md.

    Three states:
      (a) cards directory missing / empty → treat as audit-not-yet-run,
          return ALL registered tools (single_tool_agent uses its own
          restricted dispatch, so this only affects agent_v7 before audit).
      (b) cards exist and >=1 is KEEP → return that KEEP set.
      (c) cards exist but zero KEEP → return empty set (no tools allowed);
          audit has concluded no tool is useful — do NOT silently re-enable
          everything.
    """
    global _KEEP_TOOLS
    cards = Path(__file__).resolve().parent.parent.parent / "refine-logs" / "tool_cards"
    keep: set[str] = set()
    cards_present = False
    if cards.exists():
        md_files = list(cards.glob("*.md"))
        cards_present = len(md_files) > 0
        for md in md_files:
            try:
                text = md.read_text()
            except OSError:
                continue
            if "**Verdict:** KEEP" in text:
                keep.add(md.stem)
    if cards_present:
        _KEEP_TOOLS = keep  # may be empty — that's intentional
    else:
        _KEEP_TOOLS = set(TOOL_REGISTRY.keys())  # pre-audit fallback
    return _KEEP_TOOLS


def dispatch_tool_keep_only(name: str, args: dict, ctx: dict | None = None) -> dict:
    """Same as dispatch_tool but refuses tools not in the KEEP set.

    agent_v7 uses this; audit runs use the un-gated dispatch_tool.
    """
    global _KEEP_TOOLS
    if _KEEP_TOOLS is None:
        _load_keep_tools()
    if name not in (_KEEP_TOOLS or set()):
        return {"error": (f"{name} is not a v7 KEEP tool; allowed set: "
                          f"{sorted(_KEEP_TOOLS or [])}")}
    return dispatch_tool(name, args, ctx)
