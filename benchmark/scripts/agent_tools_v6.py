"""AnomalyClaw v6 — 13-tool catalog for the ReAct agent.

Design invariants:
- No per-domain branching inside tools. Domain code is never a modeling input
  (only used by tool_reference_retriever to locate its cached index file).
- Pure functions where possible; cache expensive resources at module level.
- Each tool returns a JSON-serializable dict with an `error` key on failure.

Tiers:
  1. Expert probes: tool_expert_score
  2. Visual inspection: hotspot_cropper, zoom_bbox, patch_grid, image_diff,
                        rotate_align, side_by_side
  3. Reference understanding: reference_profiler, reference_retriever
  4. Structural: component_counter, segment_and_count, texture_fft
  5. Knowledge: domain_knowledge
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

RESULTS_DIR = Path("/hdd1/jiangxi/AD-Agent/benchmark/results")


# ─── Helpers ────────────────────────────────────────────────────────────────

def _pil_to_b64(img: Image.Image, max_side: int = 512, quality: int = 85) -> str:
    w, h = img.size
    if max(w, h) > max_side:
        scale = max_side / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


# ─── Tier 1: Expert probes ──────────────────────────────────────────────────

EXPERT_FILES = {
    "subspacead":    {"calibration": "subspacead_calibration.json",
                      "test":        "subspacead_test.json"},
    "anomalyvfm":    {"calibration": "anomalyvfm_calibration.json",
                      "test":        "anomalyvfm_test.json"},
    "patchknn":      {"calibration": "classical_dinov2_patch_test_all.json",
                      "test":        "classical_dinov2_patch_test_all.json"},
    "dinov2_global": {"calibration": "classical_dinov2_global_test_all.json",
                      "test":        "classical_dinov2_global_test_all.json"},
}


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


def tool_expert_score(item_id: str, expert: str = "subspacead",
                      split: str = "test", **_) -> dict:
    """Look up a cached expert anomaly score + its percentile rank within `split`.

    Returns: {expert, score, normalized_rank, top_patches, interpretation, error}
    """
    try:
        recs, all_scores = _load_expert_scores(expert, split)
    except ValueError as e:
        return {"error": str(e)}
    rec = recs.get(item_id)
    if rec is None or rec.get("anomaly_score") is None:
        return {"error": f"no cached score for {item_id} in {expert}/{split}"}
    s = float(rec["anomaly_score"])
    if len(all_scores) == 0:
        rank = 0.5
    else:
        rank = float(np.searchsorted(all_scores, s) / len(all_scores))
    interp = ("strong anomaly signal" if rank >= 0.80 else
              "weak signal"           if rank <= 0.40 else
              "moderate / ambiguous signal")
    return {
        "expert": expert,
        "score": s,
        "normalized_rank": rank,
        "top_patches": rec.get("top_patches") or [],
        "interpretation": interp,
        "error": None,
    }


# ─── Tier 2: Visual inspection ──────────────────────────────────────────────

def tool_hotspot_cropper(query_path: str, patches: list[dict] | None = None,
                         pad: float = 0.15, k: int = 5,
                         _expert_patches: list | None = None, **_) -> dict:
    """Crop query image around top-k expert-flagged patches (48x48 grid).

    If `patches` is not provided, falls back to `_expert_patches` from session
    context (populated by a prior tool_expert_score call).
    """
    patches = patches or _expert_patches or []
    if not patches:
        return {"error": "no patches available; call tool_expert_score(subspacead) first"}
    img = Image.open(query_path).convert("RGB")
    W, H = img.size
    grid = 48
    rows = [p.get("row") for p in patches[:k] if p.get("row") is not None]
    cols = [p.get("col") for p in patches[:k] if p.get("col") is not None]
    if not rows or not cols:
        return {"error": "patches missing row/col fields"}
    r0, r1 = min(rows), max(rows) + 1
    c0, c1 = min(cols), max(cols) + 1
    span_r, span_c = r1 - r0, c1 - c0
    r0 = max(0, r0 - max(1, int(pad * max(span_r, 1))))
    r1 = min(grid, r1 + max(1, int(pad * max(span_r, 1))))
    c0 = max(0, c0 - max(1, int(pad * max(span_c, 1))))
    c1 = min(grid, c1 + max(1, int(pad * max(span_c, 1))))
    x0, x1 = int(c0 / grid * W), int(c1 / grid * W)
    y0, y1 = int(r0 / grid * H), int(r1 / grid * H)
    if x1 <= x0 or y1 <= y0:
        return {"error": "degenerate crop"}
    crop = img.crop((x0, y0, x1, y1))
    return {
        "bbox": [x0, y0, x1, y1],
        "crop_b64": _pil_to_b64(crop),
        "original_size": [W, H],
        "error": None,
    }


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
    return {
        "bbox": [x0, y0, x1, y1],
        "crop_b64": _pil_to_b64(crop),
        "original_size": [W, H],
        "error": None,
    }


def tool_patch_grid(query_path: str, rows: int = 3, cols: int = 3, **_) -> dict:
    """Return rows*cols tiles covering the image in a regular grid."""
    try:
        rows, cols = int(rows), int(cols)
    except (TypeError, ValueError):
        return {"error": "rows/cols must be integers"}
    if rows < 1 or cols < 1 or rows > 8 or cols > 8:
        return {"error": f"rows/cols must be in [1, 8]; got {rows}x{cols}"}
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
    return {"rows": rows, "cols": cols, "tiles": tiles, "error": None}


def tool_image_diff(query_path: str, ref_path: str | None = None,
                    ref_paths: list[str] | None = None, ref_idx: int = 0,
                    threshold: float = 30.0, **_) -> dict:
    """Absolute pixel diff between query and a reference, with stats + mask.

    Accepts either `ref_path` directly or `ref_idx` + `ref_paths` from session.
    """
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
    return {
        "mean_diff": float(diff.mean()),
        "max_diff": float(diff.max()),
        "change_percent": change_pct,
        "threshold": threshold,
        "diff_mask_b64": _pil_to_b64(Image.fromarray(mask, mode="L").convert("RGB"),
                                     max_side=256),
        "error": None,
    }


def tool_rotate_align(query_path: str, ref_path: str | None = None,
                      ref_paths: list[str] | None = None, ref_idx: int = 0,
                      **_) -> dict:
    """Try rotations [-10,-5,0,5,10] deg on ref, pick min-MSE, then return aligned diff."""
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
    return {
        "rotation_angle_deg": float(best_angle),
        "aligned_mean_diff": float(best_mse),
        "aligned_diff_b64": _pil_to_b64(Image.fromarray(mask, mode="L").convert("RGB"),
                                        max_side=256),
        "error": None,
    }


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
    return {
        "bbox": bbox,
        "n_crops": len(crops),
        "composite_b64": _pil_to_b64(composite, max_side=768),
        "error": None,
    }


# ─── Tier 3: Reference understanding ────────────────────────────────────────

PROFILER_SYSTEM = (
    "You are analyzing normal reference images. Describe what they have in common "
    "in terms of: (1) objects/scene content, (2) colors, (3) textures, (4) structural "
    "components, (5) typical variations across the references. Be factual and concise. "
    "Return JSON: {\"profile_text\": \"1-3 sentences\", \"common_objects\": [...], "
    "\"typical_colors\": [...], \"variations\": [...]}"
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
    parts.append(text_msg("Profile these 4 normal references."))
    messages = [{"role": "user", "content": parts}]
    try:
        text, _, _ = call_llm(vlm_client, vlm_model, messages,
                              max_tokens=max_tokens, temperature=0.0)
    except Exception as e:
        return {"error": f"vlm call failed: {e}"}
    parsed = extract_json(text) or {}
    return {
        "error": None,
        "profile_text": parsed.get("profile_text", text[:200]),
        "common_objects": parsed.get("common_objects", []),
        "typical_colors": parsed.get("typical_colors", []),
        "variations": parsed.get("variations", []),
        "n_refs_used": len(ref_paths[:4]),
    }


_RETRIEVAL_CACHE: dict[str, Any] = {}


def _load_retrieval_model_v6(device: str = "cuda"):
    if "model" in _RETRIEVAL_CACHE:
        return _RETRIEVAL_CACHE["model"], _RETRIEVAL_CACHE["transform"]
    import torch
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
                             index_dir: str = "/hdd1/jiangxi/AD-Agent/benchmark/retrieval_index",
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
        return {"results": results, "error": None}
    except Exception as e:
        return {"error": f"retrieval failed: {e}"}


# ─── Tier 4: Structural analysis ────────────────────────────────────────────

def tool_component_counter(patches: list[dict] | None = None,
                           _expert_patches: list | None = None,
                           threshold: float = 0.5, **_) -> dict:
    """Count connected components among top-k expert patches (48x48 grid, 4-conn)."""
    patches = patches or _expert_patches or []
    if not patches:
        return {"error": None, "n_components": 0, "n_active_patches": 0}
    grid = np.zeros((48, 48), dtype=np.uint8)
    for p in patches:
        r, c = p.get("row"), p.get("col")
        if r is not None and c is not None and 0 <= r < 48 and 0 <= c < 48:
            grid[r, c] = 1
    n, seen = 0, np.zeros_like(grid, dtype=bool)
    for i in range(48):
        for j in range(48):
            if grid[i, j] and not seen[i, j]:
                n += 1
                stack = [(i, j)]
                while stack:
                    ii, jj = stack.pop()
                    if (0 <= ii < 48 and 0 <= jj < 48 and grid[ii, jj]
                            and not seen[ii, jj]):
                        seen[ii, jj] = True
                        stack.extend([(ii+1, jj), (ii-1, jj),
                                      (ii, jj+1), (ii, jj-1)])
    return {"error": None, "n_components": int(n),
            "n_active_patches": int(grid.sum())}


def tool_segment_and_count(query_path: str, ref_paths: list[str] | None = None,
                           grid_size: int = 8, **_) -> dict:
    """Coarse structural-change signal via 8x8 intensity-grid diff vs ref 0."""
    if not ref_paths:
        return {"error": "ref_paths required"}
    q = np.array(Image.open(query_path).convert("L").resize((256, 256)))
    r = np.array(Image.open(ref_paths[0]).convert("L").resize((256, 256)))
    cell = 256 // grid_size
    q_grid = q.reshape(grid_size, cell, grid_size, cell).mean(axis=(1, 3))
    r_grid = r.reshape(grid_size, cell, grid_size, cell).mean(axis=(1, 3))
    diff = np.abs(q_grid - r_grid)
    changed = int((diff > 20).sum())
    top_idx = np.argsort(diff.ravel())[::-1][:5]
    top_diffs = [{"row": int(i // grid_size), "col": int(i % grid_size),
                  "diff": float(diff.ravel()[i])} for i in top_idx
                 if diff.ravel()[i] > 10]
    return {
        "error": None,
        "changed_cells": changed,
        "total_cells": grid_size * grid_size,
        "change_ratio": round(changed / (grid_size * grid_size), 3),
        "top_differences": top_diffs,
    }


def tool_texture_fft(query_path: str, **_) -> dict:
    """FFT periodicity score: top-10 peak energy / total spectrum energy."""
    img = np.array(Image.open(query_path).convert("L").resize((256, 256))).astype(float)
    img -= img.mean()
    spec = np.abs(np.fft.fftshift(np.fft.fft2(img)))
    h, w = spec.shape
    cy, cx = h // 2, w // 2
    spec[cy - 3:cy + 3, cx - 3:cx + 3] = 0
    total = float(spec.sum()) + 1e-8
    top_k = float(np.sort(spec.ravel())[::-1][:10].sum())
    score = float(top_k / total)
    return {"error": None, "periodicity_score": min(1.0, max(0.0, score))}


# ─── Tier 5: Semantic knowledge ─────────────────────────────────────────────

KNOWLEDGE_SYSTEM = (
    "You are a domain knowledge assistant for visual anomaly detection. "
    "Answer the question in 2-4 sentences with concrete visual details. "
    "Do not hedge. Return JSON: {\"answer\": \"...\"}"
)


def tool_domain_knowledge(question: str, llm_client=None,
                          llm_model: str | None = None,
                          vlm_client=None, vlm_model: str | None = None,
                          max_tokens: int = 300, **_) -> dict:
    """Text-only LLM query. Agent phrases its own question; no domain hint baked in."""
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
    return {"error": None, "answer": parsed.get("answer", text.strip()[:300])}


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
