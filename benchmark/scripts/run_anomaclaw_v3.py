"""AnomalyClaw v3 runner — Tool x Expert x Strategy agent with autonomous planning.

Key components:
  - Tools: domain_descriptor, reference_retriever, hotspot_cropper,
    component_counter, knowledge_lookup
  - Experts (cached): SubspaceAD, DINOv2 patch-kNN, DINOv2 global
  - Strategies: direct / fusion / debate / interpret
  - Autonomous planner: a text-only VLM call per domain that emits
      {"tools": [...], "expert": "...", "strategy": "..."}
  - Online override: if strategy != interpret and v0 says normal but expert rho > 0.8,
    promote to interpret regardless of plan.

Run once per (backbone, domain) → cached plan → executed per item.

Usage:
  python benchmark/scripts/run_anomaclaw_v3.py \
    --manifest benchmark/manifests/full_manifest_v2.json \
    --split test --backend seedvl \
    --output benchmark/results/anomaclaw_v3_seedvl_test.json \
    --max_workers 8
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import numpy as np
from openai import OpenAI
from PIL import Image

# Reuse infer.py utilities
sys.path.insert(0, str(Path(__file__).parent))
from infer import (  # noqa: E402
    DOMAIN_CONTEXT,
    OUTPUT_SCHEMA_V0,
    build_prompt_v0,
    call_llm,
    extract_json,
    get_client,
    get_model_name,
    img_msg,
    label_from_score,
    load_and_encode,
    run_v0,
    run_v3,
    score_from_v0,
    text_msg,
)

# Tools 1-3 already wired:
from agent_tools import (  # noqa: E402
    DOMAIN_KNOWLEDGE,
    tool_visual_retrieval,
)
from additional_tools import (  # noqa: E402
    tool_image_diff,
    tool_segment_and_count,
    tool_anomaly_heatmap_text,
)


# ---------------------------------------------------------------------------
# Tool 4: hotspot_cropper
# ---------------------------------------------------------------------------
def tool_hotspot_cropper(query_path: str, patches: list[dict],
                         pad: float = 0.15, k: int = 5) -> dict | None:
    """Take top-k expert patch coordinates (48x48 grid) and return a tight crop."""
    if not patches:
        return None
    img = Image.open(query_path).convert("RGB")
    W, H = img.size
    rows = [p.get("row", -1) for p in patches[:k] if "row" in p]
    cols = [p.get("col", -1) for p in patches[:k] if "col" in p]
    if not rows:
        return None
    grid = 48
    r0, r1 = min(rows), max(rows) + 1
    c0, c1 = min(cols), max(cols) + 1
    # Pad
    span_r, span_c = r1 - r0, c1 - c0
    r0 = max(0, r0 - max(1, int(pad * span_r)))
    r1 = min(grid, r1 + max(1, int(pad * span_r)))
    c0 = max(0, c0 - max(1, int(pad * span_c)))
    c1 = min(grid, c1 + max(1, int(pad * span_c)))
    # Convert to image coords
    x0 = int(c0 / grid * W)
    x1 = int(c1 / grid * W)
    y0 = int(r0 / grid * H)
    y1 = int(r1 / grid * H)
    if x1 <= x0 or y1 <= y0:
        return None
    crop = img.crop((x0, y0, x1, y1))
    return {"bbox": [x0, y0, x1, y1], "crop": crop, "size": (W, H)}


# ---------------------------------------------------------------------------
# Tool 5: component_counter (only for logical anomaly domains)
# ---------------------------------------------------------------------------
def tool_component_counter(patches: list[dict], threshold: float = 0.5) -> dict:
    """Connected-component count over the top-k patches' positions in 48x48 grid."""
    if not patches:
        return {"n_components": 0}
    grid = np.zeros((48, 48), dtype=np.uint8)
    for p in patches:
        r, c = p.get("row"), p.get("col")
        if r is not None and c is not None and 0 <= r < 48 and 0 <= c < 48:
            grid[r, c] = 1
    # 4-connectivity flood-fill
    n = 0
    seen = np.zeros_like(grid, dtype=bool)
    for i in range(48):
        for j in range(48):
            if grid[i, j] and not seen[i, j]:
                # BFS
                n += 1
                stack = [(i, j)]
                while stack:
                    ii, jj = stack.pop()
                    if not (0 <= ii < 48 and 0 <= jj < 48):
                        continue
                    if seen[ii, jj] or not grid[ii, jj]:
                        continue
                    seen[ii, jj] = True
                    stack.extend([(ii + 1, jj), (ii - 1, jj), (ii, jj + 1), (ii, jj - 1)])
    return {"n_components": int(n), "n_active_patches": int(grid.sum())}


# ---------------------------------------------------------------------------
# Expert score loader (cached)
# ---------------------------------------------------------------------------
class ExpertCache:
    def __init__(self, results_dir: Path):
        # Load BOTH test and calibration splits so the cache works for either
        self.subspacead = {**self._load_dict(results_dir / "subspacead_calibration.json"),
                          **self._load_dict(results_dir / "subspacead_test.json")}
        self.patchknn = self._load_dict(results_dir / "classical_dinov2_patch_test_all.json")
        self.global_ = self._load_dict(results_dir / "classical_dinov2_global_test_all.json")
        # Calibration median (used for sigmoid centre)
        subs_calib = self._load_list(results_dir / "subspacead_calibration.json")
        scores = [x["anomaly_score"] for x in subs_calib if "anomaly_score" in x]
        self.subs_median = float(np.median(scores)) if scores else 1.0

    @staticmethod
    def _load_list(p: Path) -> list:
        if not p.exists():
            return []
        return json.load(open(p))

    @staticmethod
    def _load_dict(p: Path) -> dict[str, dict]:
        if not p.exists():
            return {}
        data = json.load(open(p))
        if isinstance(data, dict):
            return data
        return {x.get("item_id"): x for x in data if "item_id" in x}

    def get(self, item_id: str) -> dict[str, Any]:
        s = self.subspacead.get(item_id, {})
        p = self.patchknn.get(item_id, {})
        g = self.global_.get(item_id, {})
        # Compute rho/kappa from patch result
        top_patches = s.get("top_patches") or []
        d_max = top_patches[0]["score"] if top_patches else None
        d_top5 = float(np.mean([t["score"] for t in top_patches[:5]])) if top_patches else None
        # Use patch-knn anomaly_score as a baseline distance
        p_score = p.get("anomaly_score")
        kappa = (d_max / d_top5) if (d_max and d_top5) else None
        rho = ((d_max - p_score) / max(p_score, 1e-6)) if (d_max and p_score) else None
        return {
            "subspacead_score": s.get("anomaly_score"),
            "subspacead_top_patches": top_patches,
            "patchknn_score": p_score,
            "global_score": g.get("anomaly_score"),
            "rho": rho,
            "kappa": kappa,
            "subs_median": self.subs_median,
        }


# ---------------------------------------------------------------------------
# Autonomous planner — text-only VLM call
# ---------------------------------------------------------------------------
PLAN_SCHEMA = """{
  "tools": ["subset of: domain_descriptor, reference_retriever, hotspot_cropper, component_counter, knowledge_lookup"],
  "expert": "one of: subspacead, patchknn, dinov2_global",
  "strategy": "one of: direct, fusion, zoom_fusion, debate, interpret",
  "reasoning": "1-2 sentence justification"
}"""

PLAN_SYSTEM = """You are the routing controller of a visual anomaly detection agent.
Given a target domain, you select a TOOL combination, an EXPERT, and a STRATEGY.

Tool catalogue:
- domain_descriptor: returns the task-anchored anomaly definition (always cheap; recommend for every domain).
- reference_retriever: ranks references by visual similarity (helpful when the reference pool is large or heterogeneous).
- hotspot_cropper: crops the expert's top-k anomaly patches (only useful with the interpret strategy).
- component_counter: counts connected components in the expert hotspot map (only useful for logical-anomaly domains where missing/extra parts matter).
- knowledge_lookup: returns a domain-specific keyword list (medical, infrastructure, logical).

Expert catalogue:
- subspacead: PCA-residual on DINOv2 patches; strong on industrial texture, retail, logical, liver CT.
- patchknn: patch-level nearest-neighbour distance; strong on infrastructure (cracks), dermoscopy.
- dinov2_global: global CLS distance; cheap sanity expert.

Strategy catalogue:
- direct: one VLM call with the descriptor — best when the VLM's world knowledge is the bottleneck (semantic domains: GI endoscopy, change detection, road obstacle).
- fusion: VLM call blended with the expert score using a per-domain calibrated weight — best for texture-dominant industrial / medical / logical / dermoscopy.
- zoom_fusion: ONE VLM call where the input includes the full image AND a high-resolution crop of the expert's hotspot, then blended with the expert score. Best for industrial defects, medical focal lesions, dermoscopy, and any domain where the anomaly is small / fine-grained and easily missed at full-image resolution.
- debate: two VLM calls (proposer + adversarial advocate) — best when VLM confidence is unreliable on subtle medical scans.
- interpret: VLM call; if it says NORMAL but the expert disagrees with a concentrated hotspot, a second VLM call examines the hotspot crop — safety net.

You must output a JSON plan and one sentence of reasoning. Be terse and decisive.
"""


def _planner_user_message(domain_code: str, descriptor: str,
                          knowledge: dict, n_refs: int) -> str:
    family_hint = knowledge.get("domain", "unknown family")
    crit_lines = knowledge.get("anomaly_criteria", [])
    crit = "\n  - " + "\n  - ".join(crit_lines[:3]) if crit_lines else ""
    return (
        f"Domain code: {domain_code}\n"
        f"Domain family: {family_hint}\n"
        f"Reference pool size for a query: {n_refs}\n"
        f"Anomaly criteria:{crit}\n\n"
        f"Task-anchored descriptor:\n{descriptor}\n\n"
        f"Decide tools / expert / strategy.\n"
        f"Return JSON only:\n{PLAN_SCHEMA}"
    )


# ---------------------------------------------------------------------------
# RAG knowledge store — accumulates normality profiles during runtime.
# Key: (domain_code, category) → {normal_patterns, benign_variations, n_refs_seen}
# The agent retrieves existing knowledge before processing + stores new findings.
# ---------------------------------------------------------------------------
import threading

_rag_store: dict[str, dict] = {}  # key = "domain:category"
_rag_lock = threading.Lock()
_profile_cache: dict[tuple, dict] = {}  # ref_paths tuple → profile


def rag_retrieve(domain_code: str, category: str = "") -> str:
    """Retrieve accumulated normality knowledge for this domain+category."""
    key = f"{domain_code}:{category}"
    with _rag_lock:
        entry = _rag_store.get(key) or _rag_store.get(f"{domain_code}:")
    if not entry:
        return ""
    patterns = entry.get("normal_patterns", [])
    variations = entry.get("benign_variations", [])
    parts = []
    if patterns:
        parts.append("Known normal patterns: " + "; ".join(str(p) for p in patterns[:5]))
    if variations:
        parts.append("Known benign variations: " + "; ".join(str(v) for v in variations[:4]))
    return "\n".join(parts)


def rag_store(domain_code: str, category: str, profile: dict):
    """Store/merge a normality profile into the RAG."""
    key = f"{domain_code}:{category}"
    with _rag_lock:
        existing = _rag_store.get(key, {"normal_patterns": [], "benign_variations": [], "n": 0})
        # Merge: add new patterns, deduplicate by string
        for p in (profile.get("normal_patterns") or []):
            if str(p) not in [str(x) for x in existing["normal_patterns"]]:
                existing["normal_patterns"].append(p)
        for v in (profile.get("benign_variations") or []):
            if str(v) not in [str(x) for x in existing["benign_variations"]]:
                existing["benign_variations"].append(v)
        existing["n"] += 1
        # Keep max 8 patterns / 6 variations
        existing["normal_patterns"] = existing["normal_patterns"][:8]
        existing["benign_variations"] = existing["benign_variations"][:6]
        _rag_store[key] = existing


_plan_cache: dict[tuple[str, str], dict] = {}


def autonomous_plan(client, model: str, domain_code: str, n_refs: int) -> dict:
    """Cache-keyed by (model, domain_code)."""
    key = (model, domain_code)
    if key in _plan_cache:
        return _plan_cache[key]
    descriptor = DOMAIN_CONTEXT.get(domain_code, "image")
    knowledge = DOMAIN_KNOWLEDGE.get(domain_code, {})
    user = _planner_user_message(domain_code, descriptor, knowledge, n_refs)
    messages = [
        {"role": "system", "content": PLAN_SYSTEM},
        {"role": "user", "content": user},
    ]
    text, inp, out = call_llm(client, model, messages, max_tokens=350)
    parsed = extract_json(text)
    plan = {
        "tools": (parsed or {}).get("tools", ["domain_descriptor"]),
        "expert": (parsed or {}).get("expert", "subspacead"),
        "strategy": (parsed or {}).get("strategy", "fusion"),
        "reasoning": (parsed or {}).get("reasoning", ""),
        "plan_cost": {"input": inp, "output": out},
        "raw_text": text,
    }
    # Sanitise
    if plan["strategy"] not in {"direct", "fusion", "zoom_fusion", "debate", "interpret"}:
        plan["strategy"] = "fusion"
    if plan["expert"] not in {"subspacead", "patchknn", "dinov2_global"}:
        plan["expert"] = "subspacead"
    _plan_cache[key] = plan
    return plan


# ---------------------------------------------------------------------------
# Strategy executors
# ---------------------------------------------------------------------------
def strategy_direct(client, model, item, plan, expert_info):
    return run_v0(client, model, item)


def strategy_fusion(client, model, item, plan, expert_info, w: float = 0.2):
    r0 = run_v0(client, model, item)
    s0 = float(r0.get("anomaly_score", 0.5))
    sx = expert_info.get("subspacead_score")
    if sx is None or expert_info.get("subs_median") in (None, 0):
        return r0
    m = expert_info["subs_median"]
    sig = 1.0 / (1.0 + np.exp(-2.0 * (sx - m) / max(m, 1e-6)))
    final = (1 - w) * s0 + w * sig
    r0["anomaly_score"] = float(final)
    r0["label_pred"] = label_from_score(final)
    r0["raw_output"] = {**(r0.get("raw_output") or {}),
                        "fusion": {"v0_score": s0, "expert_score": sx,
                                   "expert_sig": float(sig), "w": w, "final": float(final)}}
    return r0


def strategy_debate(client, model, item, plan, expert_info):
    return run_v3(client, model, item)


# ---------------------------------------------------------------------------
# Per-domain fusion weight, calibrated and frozen.
# ---------------------------------------------------------------------------
_PER_DOMAIN_W = None


def _load_per_domain_w(model_name: str) -> dict:
    global _PER_DOMAIN_W
    if _PER_DOMAIN_W is None:
        try:
            _PER_DOMAIN_W = json.load(open("/hdd1/jiangxi/AD-Agent/refine-logs/PER_DOMAIN_W.json"))
        except Exception:
            _PER_DOMAIN_W = {"per_backbone": {}}
    # Map model_name -> backbone key
    bk = "qwen35"  # default
    if "doubao" in str(model_name).lower() or "seed" in str(model_name).lower():
        bk = "seedvl"
    elif "gpt" in str(model_name).lower() or "chatgpt" in str(model_name).lower():
        bk = "gpt54"
    return _PER_DOMAIN_W.get("per_backbone", {}).get(bk, {})


def strategy_fusion_perdomain(client, model, item, plan, expert_info):
    """Fusion with per-domain calibrated weight."""
    wmap = _load_per_domain_w(model)
    w = wmap.get(item["domain_code"], {}).get("w", 0.2)
    return strategy_fusion(client, model, item, plan, expert_info, w=w)


# ---------------------------------------------------------------------------
# Multi-expert support: AnomalyVFM expert score cache (loaded lazily).
# ---------------------------------------------------------------------------
_AVFM_CACHE = None
_AVFM_MEDIAN = None


def _load_avfm():
    global _AVFM_CACHE, _AVFM_MEDIAN
    if _AVFM_CACHE is None:
        path = Path("/hdd1/jiangxi/AD-Agent/benchmark/results/anomalyvfm_test.json")
        if not path.exists():
            _AVFM_CACHE = {}
            _AVFM_MEDIAN = 0.5
        else:
            data = json.load(open(path))
            _AVFM_CACHE = {x["item_id"]: x for x in data if "item_id" in x}
            _AVFM_MEDIAN = float(np.median([x["anomaly_score"] for x in data
                                            if x.get("anomaly_score") is not None]))
    return _AVFM_CACHE, _AVFM_MEDIAN


def strategy_fusion_avfm(client, model, item, plan, expert_info, w: float = 0.2):
    """Fusion with AnomalyVFM expert (zero-shot, fine-tuned VFM + LoRA)."""
    r0 = run_v0(client, model, item)
    s0 = float(r0.get("anomaly_score", 0.5))
    avfm, m = _load_avfm()
    a = avfm.get(item["item_id"], {}).get("anomaly_score")
    if a is None or m in (None, 0):
        return r0
    sig = 1.0 / (1.0 + np.exp(-2.0 * (float(a) - m) / max(m, 1e-6)))
    final = (1 - w) * s0 + w * sig
    r0["anomaly_score"] = float(final)
    r0["label_pred"] = label_from_score(final)
    r0["raw_output"] = {**(r0.get("raw_output") or {}),
                        "fusion_avfm": {"v0_score": s0, "expert_score": float(a),
                                        "expert_sig": float(sig), "w": w,
                                        "final": float(final)}}
    return r0


def strategy_subs_only(client, model, item, plan, expert_info):
    """Expert-only score (no VLM call). Used when calibration shows the expert dominates."""
    sx = expert_info.get("subspacead_score")
    m = expert_info.get("subs_median")
    if sx is None:
        return {
            "label_pred": 0, "anomaly_score": 0.5,
            "anomaly_type_pred": None,
            "raw_output": {"subs_only": {"reason": "no_score"}},
            "cost_tokens": {"input": 0, "output": 0},
            "latency_sec": 0.0,
        }
    sig = 1.0 / (1.0 + np.exp(-2.0 * (float(sx) - m) / max(m, 1e-6))) if m else 0.5
    return {
        "label_pred": label_from_score(sig),
        "anomaly_score": float(sig),
        "anomaly_type_pred": None,
        "raw_output": {"subs_only": {"expert_score": sx, "sig": float(sig)}},
        "cost_tokens": {"input": 0, "output": 0},
        "latency_sec": 0.0,
    }


def strategy_avfm_only(client, model, item, plan, expert_info):
    """AnomalyVFM expert-only (no VLM call)."""
    avfm, m = _load_avfm()
    a = avfm.get(item["item_id"], {}).get("anomaly_score")
    if a is None:
        return {"label_pred": 0, "anomaly_score": 0.5,
                "raw_output": {"avfm_only": {"reason": "no_score"}},
                "cost_tokens": {"input": 0, "output": 0}, "latency_sec": 0.0}
    sig = 1.0 / (1.0 + np.exp(-2.0 * (float(a) - m) / max(m, 1e-6)))
    return {
        "label_pred": label_from_score(sig),
        "anomaly_score": float(sig),
        "anomaly_type_pred": None,
        "raw_output": {"avfm_only": {"expert_score": a, "sig": float(sig)}},
        "cost_tokens": {"input": 0, "output": 0},
        "latency_sec": 0.0,
    }


# ---------------------------------------------------------------------------
# Strategy: zoom_fusion — VLM call with [refs, full_image, hotspot_crop]
# Idea: give VLM a high-resolution view of the expert-flagged region in the SAME call.
# Cost: 1 VLM call per item. Adds new visual signal that direct/fusion miss.
# ---------------------------------------------------------------------------
def _zoom_prompt(domain_ctx: str, has_crop: bool) -> str:
    crop_note = (" The LAST image is a high-resolution crop centred on the patch with the "
                 "largest expert anomaly signal — examine it for fine defects that may be "
                 "invisible in the full-image view.") if has_crop else ""
    return (
        f"You are a visual anomaly inspector examining a {domain_ctx}. "
        f"The first image(s) show the normal reference state.{crop_note}\n"
        f"Decide whether the QUERY image is abnormal relative to the normal reference state.\n"
        f"Return JSON only:\n{OUTPUT_SCHEMA_V0}"
    )


def strategy_zoom_fusion(client, model, item, plan, expert_info):
    """Single VLM call with [refs, full_image, expert_crop]; blend with per-domain w."""
    import base64
    import io
    from infer import N_REFS

    domain = item["domain_code"]
    ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:N_REFS]]
    query_img = load_and_encode(item["query_path"])

    # Build expert crop if patches exist
    patches = expert_info.get("subspacead_top_patches") or []
    crop = tool_hotspot_cropper(item["query_path"], patches, k=5)
    crop_b64 = None
    if crop is not None:
        buf = io.BytesIO()
        crop["crop"].save(buf, format="JPEG", quality=88)
        crop_b64 = base64.b64encode(buf.getvalue()).decode()

    ctx = DOMAIN_CONTEXT.get(domain, "image")

    content = []
    for b64 in ref_imgs:
        content.append(text_msg("Normal reference:"))
        content.append(img_msg(b64))
    content.append(text_msg("Query image (full):"))
    content.append(img_msg(query_img))
    if crop_b64 is not None:
        content.append(text_msg("Expert-flagged hotspot crop (high-res view):"))
        content.append(img_msg(crop_b64))
    content.append(text_msg(_zoom_prompt(ctx, has_crop=crop_b64 is not None)))

    t0 = time.time()
    text, inp, out = call_llm(client, model,
        [{"role": "user", "content": content}], max_tokens=400)
    parsed = extract_json(text) or {}
    s0 = float(score_from_v0(parsed))

    # Blend with expert score (per-domain w)
    sx = expert_info.get("subspacead_score")
    if sx is None or expert_info.get("subs_median") in (None, 0):
        final = s0
        sig = None
    else:
        m = expert_info["subs_median"]
        sig = 1.0 / (1.0 + np.exp(-2.0 * (sx - m) / max(m, 1e-6)))
        wmap = _load_per_domain_w(model)
        w = wmap.get(domain, {}).get("w", 0.2)
        final = (1 - w) * s0 + w * sig

    return {
        "label_pred": label_from_score(final),
        "anomaly_score": float(final),
        "anomaly_type_pred": parsed.get("anomaly_type") if parsed else None,
        "raw_output": {
            "zoom_fusion": {
                "v0_with_crop": parsed,
                "vlm_score": s0,
                "expert_score": sx,
                "expert_sig": float(sig) if sig is not None else None,
                "w": float(wmap.get(domain, {}).get("w", 0.2)) if sx is not None else None,
                "final": float(final),
                "had_crop": crop_b64 is not None,
                "crop_bbox": crop.get("bbox") if crop else None,
            }
        },
        "cost_tokens": {"input": inp, "output": out},
        "latency_sec": round(time.time() - t0, 2),
    }


def _interpret_prompt(dmax: float, sx: float, m: float) -> str:
    return (
        f"You previously examined this image and concluded it was NORMAL.\n"
        f"However a non-parametric expert flagged a spatially concentrated anomaly hotspot\n"
        f"(top-1 patch distance = {dmax:.3f}, expert anomaly score = {sx:.3f}, "
        f"threshold = {m:.3f}).\n\n"
        f"The hotspot crop is shown below as the LAST image. Re-examine it specifically for "
        f"the kind of anomaly defined by the task descriptor. If the hotspot reveals a "
        f"genuine defect that you initially missed, change your label to anomalous and "
        f"explain. If the hotspot is benign (texture variation, lighting, normal feature), "
        f"keep your normal call.\n\n"
        f"Return JSON only:\n{OUTPUT_SCHEMA_V0}"
    )


def strategy_interpret(client, model, item, plan, expert_info):
    """Asymmetric: run direct; if normal AND rho > 0.8, second VLM call with hotspot crop."""
    r0 = run_v0(client, model, item)
    v0_parsed = ((r0.get("raw_output") or {}).get("v0") or {})
    v0_label = str(v0_parsed.get("image_label", "normal")).lower()
    rho = expert_info.get("rho")
    if v0_label != "normal" or rho is None or rho <= 0.8:
        # No escalation
        r0["raw_output"] = {**(r0.get("raw_output") or {}),
                            "interpret": {"escalated": False, "rho": rho}}
        return r0
    # Escalate
    patches = expert_info.get("subspacead_top_patches") or []
    crop = tool_hotspot_cropper(item["query_path"], patches, k=5)
    if crop is None:
        r0["raw_output"] = {**(r0.get("raw_output") or {}),
                            "interpret": {"escalated": False, "reason": "no_crop"}}
        return r0
    # Encode original + crop and call
    import io
    import base64
    buf = io.BytesIO()
    crop["crop"].save(buf, format="JPEG", quality=85)
    crop_b64 = base64.b64encode(buf.getvalue()).decode()

    ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:2]]
    query_img = load_and_encode(item["query_path"])

    content = []
    for b64 in ref_imgs:
        content.append(text_msg("Normal reference:"))
        content.append(img_msg(b64))
    content.append(text_msg("Original query image:"))
    content.append(img_msg(query_img))
    content.append(text_msg("Expert-flagged hotspot crop:"))
    content.append(img_msg(crop_b64))
    content.append(text_msg(_interpret_prompt(
        dmax=float(patches[0].get("score", 0.0)),
        sx=float(expert_info.get("subspacead_score") or 0),
        m=float(expert_info.get("subs_median") or 0))))

    t0 = time.time()
    text, inp, out = call_llm(client, model, [{"role": "user", "content": content}], max_tokens=400)
    parsed = extract_json(text) or {}
    s = score_from_v0(parsed)
    r0["anomaly_score"] = float(s)
    r0["label_pred"] = label_from_score(s)
    r0["raw_output"] = {**(r0.get("raw_output") or {}),
                        "interpret": {
                            "escalated": True, "rho": rho,
                            "crop_bbox": crop["bbox"],
                            "interpret_response": parsed,
                            "interpret_score": float(s),
                        }}
    r0["cost_tokens"]["input"] += inp
    r0["cost_tokens"]["output"] += out
    r0["latency_sec"] = round((r0.get("latency_sec") or 0) + (time.time() - t0), 2)
    return r0


# ---------------------------------------------------------------------------
# Strategy: tool_augmented_fusion — the real agent strategy.
# Uses ALL tools: retriever (better refs), knowledge (keyword prompt), cropper
# (high-res view), then blends with the chosen expert.
# Cost: 1 VLM call (with enriched input) + 0 for tools.
# ---------------------------------------------------------------------------
def strategy_tool_augmented_fusion(client, model, item, plan, expert_info):
    """One VLM call with tool-enriched input, then blend with expert."""
    import base64
    import io
    from infer import N_REFS
    domain = item["domain_code"]
    ctx = DOMAIN_CONTEXT.get(domain, "image")
    tools_used = plan.get("tools") or ["domain_descriptor"]

    # Tool 1: reference_retriever — pick most similar refs
    if "reference_retriever" in tools_used:
        try:
            retrieved = tool_visual_retrieval(item["query_path"], domain, k=N_REFS)
            if retrieved:
                ref_paths = [p for p, s in retrieved]
            else:
                ref_paths = item["ref_paths"][:N_REFS]
        except Exception:
            ref_paths = item["ref_paths"][:N_REFS]
    else:
        ref_paths = item["ref_paths"][:N_REFS]
    ref_imgs = [load_and_encode(p) for p in ref_paths]

    # Tool 2: knowledge_lookup — inject domain keywords into prompt
    knowledge_note = ""
    if "knowledge_lookup" in tools_used:
        kw = DOMAIN_KNOWLEDGE.get(domain, {})
        criteria = kw.get("anomaly_criteria", [])
        fps = kw.get("common_false_positives", [])
        if criteria:
            knowledge_note = (
                "\nDomain-specific anomaly criteria:\n- " +
                "\n- ".join(criteria[:4]) +
                ("\nCommon false positives (NOT anomalies):\n- " +
                 "\n- ".join(fps[:3]) if fps else "")
            )

    # Tool 3: hotspot_cropper — add expert hotspot crop to VLM input
    crop_b64 = None
    if "hotspot_cropper" in tools_used:
        patches = expert_info.get("subspacead_top_patches") or []
        crop = tool_hotspot_cropper(item["query_path"], patches, k=5)
        if crop is not None:
            buf = io.BytesIO()
            crop["crop"].save(buf, format="JPEG", quality=88)
            crop_b64 = base64.b64encode(buf.getvalue()).decode()

    # Tool 4: component_counter — inject count as text hint
    count_note = ""
    if "component_counter" in tools_used:
        patches = expert_info.get("subspacead_top_patches") or []
        cc = tool_component_counter(patches)
        if cc.get("n_components", 0) > 0:
            count_note = (f"\nExpert hotspot analysis: {cc['n_components']} spatially "
                          f"distinct anomaly clusters detected ({cc.get('n_active_patches', 0)} "
                          f"active patches). Consider whether component count or arrangement "
                          f"differs from the references.")

    # Build prompt with tool enrichments
    crop_note = ""
    if crop_b64:
        crop_note = (" The LAST image is a high-resolution crop of the region flagged "
                     "by an expert anomaly detector — examine it for fine defects.")
    prompt = (
        f"You are a visual anomaly inspector examining a {ctx}. "
        f"The first image(s) show the normal reference state.{crop_note}"
        f"{knowledge_note}{count_note}\n"
        f"Decide whether the QUERY image is abnormal relative to the normal reference state.\n"
        f"Return JSON only:\n{OUTPUT_SCHEMA_V0}"
    )

    # Build content
    content = []
    for b64 in ref_imgs:
        content.append(text_msg("Normal reference:"))
        content.append(img_msg(b64))
    content.append(text_msg("Query image:"))
    content.append(img_msg(load_and_encode(item["query_path"])))
    if crop_b64:
        content.append(text_msg("Expert-flagged hotspot crop:"))
        content.append(img_msg(crop_b64))
    content.append(text_msg(prompt))

    t0 = time.time()
    text, inp, out = call_llm(client, model,
                              [{"role": "user", "content": content}], max_tokens=400)
    parsed = extract_json(text) or {}
    s0 = float(score_from_v0(parsed))

    # Blend with expert score
    expert_name = plan.get("expert", "subspacead")
    sx, m_exp = None, None
    if expert_name == "anomalyvfm":
        avfm_cache, m_exp = _load_avfm()
        sx = avfm_cache.get(item["item_id"], {}).get("anomaly_score")
    else:
        sx = expert_info.get("subspacead_score")
        m_exp = expert_info.get("subs_median")

    if sx is not None and m_exp not in (None, 0):
        sig = 1.0 / (1.0 + np.exp(-2.0 * (float(sx) - m_exp) / max(m_exp, 1e-6)))
        w = 0.2  # default; could use per-domain w
        final = (1 - w) * s0 + w * sig
    else:
        final = s0
        sig = None

    return {
        "label_pred": label_from_score(final),
        "anomaly_score": float(final),
        "anomaly_type_pred": parsed.get("anomaly_type") if parsed else None,
        "raw_output": {
            "tool_augmented_fusion": {
                "vlm_score": s0,
                "expert_name": expert_name,
                "expert_score": sx,
                "expert_sig": float(sig) if sig is not None else None,
                "final": float(final),
                "tools_used": tools_used,
                "had_crop": crop_b64 is not None,
                "had_knowledge": bool(knowledge_note),
                "had_retrieval": "reference_retriever" in tools_used,
                "response": parsed,
            }
        },
        "cost_tokens": {"input": inp, "output": out},
        "latency_sec": round(time.time() - t0, 2),
    }


# ---------------------------------------------------------------------------
# Strategy: react — per-item autonomous ReAct agent.
#
# Call 1 (Observe+Plan): VLM sees refs+query+descriptor → outputs initial
#   assessment + which tools to invoke (from the tool catalogue).
# Execute tools: run requested tools, format results as text/images.
# Call 2 (Decide): VLM sees original images + tool outputs → final label.
# Then blend with expert (fusion).
#
# Cost: 2 VLM calls + 0 tool calls.  Average ~2 calls/item.
# ---------------------------------------------------------------------------

REACT_PLAN_SCHEMA = """{
  "initial_label": "normal" or "anomalous" or "uncertain",
  "confidence": float 0-1,
  "tool_calls": ["list of tool names to invoke, or empty if confident"],
  "reasoning": "why you need (or don't need) these tools"
}"""

def _build_react_system(expert_info: dict) -> str:
    """Build the ReAct system prompt with expert evidence injected."""
    from react_skill import format_expert_evidence
    return format_expert_evidence(expert_info)


def _react_plan_prompt(domain_ctx: str) -> str:
    return (
        f"You are inspecting a {domain_ctx}. "
        f"The reference images show the NORMAL state. The last image is the QUERY.\n\n"
        f"Form an initial assessment, then decide which tools to invoke.\n"
        f"Return JSON only:\n{REACT_PLAN_SCHEMA}"
    )


REACT_DECIDE_SCHEMA = OUTPUT_SCHEMA_V0


def _react_decide_prompt(domain_ctx: str, tool_results: str) -> str:
    return (
        f"You are inspecting a {domain_ctx}. "
        f"The reference images show the NORMAL state. The query image follows.\n\n"
        f"You previously requested tool assistance. Here are the results:\n"
        f"{tool_results}\n\n"
        f"Using ALL available evidence (your visual inspection + tool outputs), "
        f"make your FINAL decision.\n"
        f"Return JSON only:\n{REACT_DECIDE_SCHEMA}"
    )


def strategy_react(client, model, item, plan, expert_info):
    """Per-item ReAct: VLM autonomously decides which tools to call."""
    import base64
    import io
    from infer import N_REFS

    domain = item["domain_code"]
    ctx = DOMAIN_CONTEXT.get(domain, "image")
    ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:N_REFS]]
    query_img = load_and_encode(item["query_path"])

    # --- RAG: retrieve accumulated knowledge ---
    category = item.get("category", "")
    rag_knowledge = rag_retrieve(domain, category)

    # --- Call 1: Observe + Plan ---
    content1 = []
    for b64 in ref_imgs:
        content1.append(text_msg("Normal reference:"))
        content1.append(img_msg(b64))
    content1.append(text_msg("Query image:"))
    content1.append(img_msg(query_img))
    # Inject RAG knowledge if available
    plan_prompt = _react_plan_prompt(ctx)
    if rag_knowledge:
        plan_prompt = (f"[Prior knowledge from analyzing similar items]\n{rag_knowledge}\n\n"
                       + plan_prompt)
    content1.append(text_msg(plan_prompt))

    t0 = time.time()
    react_system = _build_react_system(expert_info)
    text1, inp1, out1 = call_llm(client, model,
        [{"role": "system", "content": react_system},
         {"role": "user", "content": content1}], max_tokens=300)
    plan_parsed = extract_json(text1) or {}
    initial_label = str(plan_parsed.get("initial_label", "uncertain")).lower()
    initial_conf = float(plan_parsed.get("confidence", 0.5))
    tool_calls = plan_parsed.get("tool_calls") or []

    # Override: if expert disagrees with VLM, force tool calls even if VLM is confident
    sx_val = expert_info.get("subspacead_score") or 0
    m_val = expert_info.get("subs_median") or 1
    expert_ratio = sx_val / max(m_val, 1e-6)
    vlm_expert_agree = (
        (initial_label == "normal" and expert_ratio < 1.5) or
        (initial_label == "anomalous" and expert_ratio > 0.8)
    )
    # Restrict tool_calls to what the plan allows (VLM may request tools not in the plan)
    allowed_tools = set(plan.get("tools") or ["hotspot_cropper", "reference_profiler",
                        "component_counter", "knowledge_lookup", "reference_retriever",
                        "image_diff", "segment_and_count", "anomaly_heatmap"])
    tool_calls = [t for t in tool_calls if t.strip().lower() in allowed_tools]

    if not tool_calls and not vlm_expert_agree:
        # Expert disagrees → force allowed tools
        forced = [t for t in ["hotspot_cropper", "reference_profiler"] if t in allowed_tools]
        tool_calls = forced or ["hotspot_cropper"]

    # If VLM is confident AND expert agrees → commit without tools
    if not tool_calls and initial_conf >= 0.90 and vlm_expert_agree:
        s0 = score_from_v0({"image_label": initial_label, "confidence": initial_conf})
        # Still blend with expert
        sx = expert_info.get("subspacead_score")
        m_exp = expert_info.get("subs_median")
        if sx is not None and m_exp not in (None, 0):
            sig = 1.0 / (1.0 + np.exp(-2.0 * (float(sx) - m_exp) / max(m_exp, 1e-6)))
            final = 0.8 * float(s0) + 0.2 * sig
        else:
            final = float(s0)
        return {
            "label_pred": label_from_score(final),
            "anomaly_score": float(final),
            "anomaly_type_pred": None,
            "raw_output": {"react": {
                "plan": plan_parsed, "tool_calls": [], "tools_skipped": True,
                "vlm_calls": 1, "final_source": "plan_confident",
            }},
            "cost_tokens": {"input": inp1, "output": out1},
            "latency_sec": round(time.time() - t0, 2),
        }

    # --- Execute requested tools ---
    tool_results_parts = []
    tool_images = []
    tools_executed = []

    for tool_name in tool_calls:
        tool_name = tool_name.strip().lower()
        if tool_name == "hotspot_cropper":
            patches = expert_info.get("subspacead_top_patches") or []
            crop = tool_hotspot_cropper(item["query_path"], patches, k=5)
            if crop is not None:
                buf = io.BytesIO()
                crop["crop"].save(buf, format="JPEG", quality=88)
                tool_images.append(("Expert hotspot crop (high-res):",
                                   base64.b64encode(buf.getvalue()).decode()))
                tool_results_parts.append(
                    f"[hotspot_cropper] Cropped region at bbox {crop['bbox']} "
                    f"(top-1 expert patch score: {patches[0].get('score', 0):.1f})")
                tools_executed.append("hotspot_cropper")
            else:
                tool_results_parts.append("[hotspot_cropper] No anomalous patches detected by expert.")

        elif tool_name == "knowledge_lookup":
            kw = DOMAIN_KNOWLEDGE.get(domain, {})
            criteria = kw.get("anomaly_criteria", [])
            fps = kw.get("common_false_positives", [])
            parts = []
            if criteria:
                parts.append("Anomaly criteria:\n- " + "\n- ".join(criteria[:4]))
            if fps:
                parts.append("Common false positives (NOT anomalies):\n- " + "\n- ".join(fps[:3]))
            tool_results_parts.append(f"[knowledge_lookup] {chr(10).join(parts)}" if parts
                                      else "[knowledge_lookup] No domain knowledge available.")
            tools_executed.append("knowledge_lookup")

        elif tool_name == "reference_profiler":
            # VLM-based: analyze refs to discover what's normal (cached per ref set)
            ref_key = tuple(sorted(item["ref_paths"][:N_REFS]))
            if ref_key not in _profile_cache:
                prof_content = []
                for b64 in ref_imgs:
                    prof_content.append(text_msg("Normal reference:"))
                    prof_content.append(img_msg(b64))
                prof_content.append(text_msg(
                    f"You are analyzing {len(ref_imgs)} NORMAL reference images.\n"
                    f"Build a normality profile: what do these references have in common, "
                    f"and what variations between them are still normal.\n"
                    f"Return JSON: {{\"normal_patterns\": [\"pattern1\", ...], "
                    f"\"benign_variations\": [\"variation1\", ...]}}"
                ))
                prof_text, prof_inp, prof_out = call_llm(client, model,
                    [{"role": "user", "content": prof_content}], max_tokens=500)
                _profile_cache[ref_key] = extract_json(prof_text) or {"raw": prof_text}
                inp1 += prof_inp
                out1 += prof_out
            profile = _profile_cache[ref_key]
            patterns = profile.get("normal_patterns", [])
            variations = profile.get("benign_variations", [])
            prof_text = ""
            if patterns:
                prof_text += "Normal patterns: " + "; ".join(str(p) for p in patterns[:4])
            if variations:
                prof_text += "\nBenign variations (NOT anomalies): " + "; ".join(str(v) for v in variations[:3])
            tool_results_parts.append(f"[reference_profiler] {prof_text}" if prof_text
                                      else "[reference_profiler] Could not build profile.")
            tools_executed.append("reference_profiler")
            # Store in RAG for future items
            rag_store(domain, item.get("category", ""), profile)

        elif tool_name == "component_counter":
            patches = expert_info.get("subspacead_top_patches") or []
            cc = tool_component_counter(patches)
            tool_results_parts.append(
                f"[component_counter] {cc['n_components']} spatially distinct anomaly clusters, "
                f"{cc.get('n_active_patches', 0)} active patches.")
            tools_executed.append("component_counter")

        elif tool_name == "reference_retriever":
            try:
                retrieved = tool_visual_retrieval(item["query_path"], domain, k=N_REFS)
                if retrieved:
                    sims = [f"{s:.3f}" for _, s in retrieved]
                    tool_results_parts.append(
                        f"[reference_retriever] Top-{len(retrieved)} similar normals "
                        f"(cosine sims: {', '.join(sims)})")
                    # Replace ref images with retrieved ones
                    ref_imgs = [load_and_encode(p) for p, _ in retrieved]
                    tools_executed.append("reference_retriever")
                else:
                    tool_results_parts.append("[reference_retriever] No retrieval index available.")
            except Exception:
                tool_results_parts.append("[reference_retriever] Retrieval failed.")

        elif tool_name == "image_diff":
            try:
                diff = tool_image_diff(item["query_path"], item["ref_paths"][0])
                tool_results_parts.append(f"[image_diff] {diff['description']}")
                tools_executed.append("image_diff")
            except Exception as e:
                tool_results_parts.append(f"[image_diff] Failed: {e}")

        elif tool_name == "segment_and_count":
            try:
                seg = tool_segment_and_count(item["query_path"], item["ref_paths"][:1])
                tool_results_parts.append(f"[segment_and_count] {seg['description']}")
                tools_executed.append("segment_and_count")
            except Exception as e:
                tool_results_parts.append(f"[segment_and_count] Failed: {e}")

        elif tool_name == "anomaly_heatmap":
            hm = tool_anomaly_heatmap_text(expert_info)
            tool_results_parts.append(f"[anomaly_heatmap] {hm}")
            tools_executed.append("anomaly_heatmap")

    # Always inject expert evidence as text
    sx = expert_info.get("subspacead_score") or 0
    m_exp_val = expert_info.get("subs_median") or 1
    ratio = sx / max(m_exp_val, 1e-6)
    expert_text = (
        f"[expert_evidence] Expert anomaly score: {sx:.1f} "
        f"(median={m_exp_val:.1f}, ratio={ratio:.1f}x). "
    )
    if ratio > 3:
        expert_text += "Expert is VERY CONFIDENT this is anomalous."
    elif ratio > 1.5:
        expert_text += "Expert sees a MODERATE anomaly signal."
    elif ratio > 0.8:
        expert_text += "Expert signal is WEAK — borderline."
    else:
        expert_text += "Expert sees NOTHING unusual."
    tool_results_parts.insert(0, expert_text)

    tool_results_text = "\n".join(tool_results_parts) if tool_results_parts else "No tool results."

    # --- Call 2: Decide with tool evidence ---
    content2 = []
    for b64 in ref_imgs:
        content2.append(text_msg("Normal reference:"))
        content2.append(img_msg(b64))
    content2.append(text_msg("Query image:"))
    content2.append(img_msg(query_img))
    for label, b64 in tool_images:
        content2.append(text_msg(label))
        content2.append(img_msg(b64))
    content2.append(text_msg(_react_decide_prompt(ctx, tool_results_text)))

    text2, inp2, out2 = call_llm(client, model,
        [{"role": "user", "content": content2}], max_tokens=400)
    decide_parsed = extract_json(text2) or {}
    s_call2 = float(score_from_v0(decide_parsed))

    # ASYMMETRIC policy: tools can only ESCALATE, never downgrade.
    # If Call 1 said anomalous (score > 0.5), keep Call 1 score — don't allow tools to dismiss.
    # If Call 1 said normal, take Call 2 AS-IS — trust VLM's fresh assessment WITH tool evidence.
    # (Previous max(call1, call2) was too aggressive → FP explosion.)
    s_call1 = float(score_from_v0({"image_label": initial_label, "confidence": initial_conf}))
    if s_call1 > 0.5:
        # VLM already thinks anomalous → trust it, skip Call 2 result
        s0 = s_call1
    else:
        # VLM thinks normal → let Call 2 (with tool evidence) make the final call
        s0 = s_call2

    # Blend with expert
    expert_name = plan.get("expert", "subspacead")
    sx, m_exp = None, None
    if expert_name == "anomalyvfm":
        avfm_cache, m_exp = _load_avfm()
        sx = avfm_cache.get(item["item_id"], {}).get("anomaly_score")
    else:
        sx = expert_info.get("subspacead_score")
        m_exp = expert_info.get("subs_median")

    if sx is not None and m_exp not in (None, 0):
        sig = 1.0 / (1.0 + np.exp(-2.0 * (float(sx) - m_exp) / max(m_exp, 1e-6)))
        final = 0.8 * s0 + 0.2 * sig
    else:
        final = s0

    return {
        "label_pred": label_from_score(final),
        "anomaly_score": float(final),
        "anomaly_type_pred": decide_parsed.get("anomaly_type") if decide_parsed else None,
        "raw_output": {"react": {
            "plan": plan_parsed,
            "tool_calls": tool_calls,
            "tools_executed": tools_executed,
            "tool_results": tool_results_text,
            "decide_response": decide_parsed,
            "vlm_calls": 2,
            "vlm_score": s0,
            "expert_name": expert_name,
            "expert_score": sx,
            "final": float(final),
        }},
        "cost_tokens": {"input": inp1 + inp2, "output": out1 + out2},
        "latency_sec": round(time.time() - t0, 2),
    }


STRATEGY_FNS = {
    "direct": strategy_direct,
    "fusion": strategy_fusion_perdomain,
    "fusion_global": strategy_fusion,
    "fusion_subs": lambda c, m, it, p, e: strategy_fusion(c, m, it, p, e, w=0.2),
    "fusion_avfm": strategy_fusion_avfm,
    "subs_only": strategy_subs_only,
    "avfm_only": strategy_avfm_only,
    "zoom_fusion": strategy_zoom_fusion,
    "tool_augmented_fusion": strategy_tool_augmented_fusion,
    "react": strategy_react,
    "debate": strategy_debate,
    "interpret": strategy_interpret,
}


# ---------------------------------------------------------------------------
# Per-item runner
# ---------------------------------------------------------------------------
def run_item(item, client, model, expert_cache: ExpertCache, fixed_plan: dict | None = None):
    domain = item["domain_code"]
    n_refs = len(item.get("ref_paths") or [])
    plan = fixed_plan or autonomous_plan(client, model, domain, n_refs)
    expert_info = expert_cache.get(item["item_id"])
    rho = expert_info.get("rho")
    # Execute what the planner chose; no online override (the override
    # silently replaced every "fusion" with "interpret" on industrial domains
    # and discarded the expert blend, which was the root cause of v3 trailing
    # fusion on our first end-to-end runs; cf. Limitations).
    online_strategy = plan["strategy"]
    online_override = False

    fn = STRATEGY_FNS[online_strategy]
    try:
        r = fn(client, model, item, plan, expert_info)
        r["plan"] = {
            "tools": plan.get("tools"),
            "expert": plan.get("expert"),
            "strategy_planned": plan["strategy"],
            "strategy_executed": online_strategy,
            "online_override": online_override,
            "reasoning": plan.get("reasoning"),
        }
        r["expert_signals"] = {"rho": rho, "kappa": expert_info.get("kappa"),
                               "subspacead": expert_info.get("subspacead_score")}
        # Augment item metadata
        for k in ("item_id", "domain", "domain_code", "label_gt", "split",
                  "source_dataset", "category"):
            r[k] = item.get(k)
        return r
    except Exception as e:
        return {
            **{k: item.get(k) for k in ("item_id", "domain", "domain_code",
                                        "label_gt", "split")},
            "error": str(e),
            "plan": plan,
            "anomaly_score": 0.5,
        }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--split", default="test")
    parser.add_argument("--backend", required=True, choices=["gpt", "seedvl", "qwen3"])
    parser.add_argument("--output", required=True)
    parser.add_argument("--domains", nargs="*", default=None)
    parser.add_argument("--max_items", type=int, default=None)
    parser.add_argument("--max_workers", type=int, default=8)
    parser.add_argument("--results_dir", default="benchmark/results")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--use_calib_router", action="store_true",
                        help="Skip planner; use precomputed calibration-argmax assignment")
    parser.add_argument("--use_zoom_router", action="store_true",
                        help="Skip planner; force a zoom_fusion-default rule-based plan")
    parser.add_argument("--agent_plan", default=None,
                        help="Path to per-domain agent plan JSON (e.g. QWEN35_AGENT_PLAN.json)")
    parser.add_argument("--n_refs", type=int, default=2)
    args = parser.parse_args()

    # Set N_REFS in infer module
    import infer
    infer.N_REFS = args.n_refs

    with open(args.manifest) as f:
        all_items = json.load(f)
    items = [x for x in all_items
             if x["split"] == args.split
             and (args.domains is None or x["domain_code"] in args.domains)]
    if args.max_items:
        items = items[:args.max_items]
    print(f"Loaded {len(items)} items")

    expert_cache = ExpertCache(Path(args.results_dir))
    client = get_client(args.backend)
    model = get_model_name(args.backend)
    print(f"Model: {model}")

    # Resume: skip already-done items
    existing = {}
    if args.resume and Path(args.output).exists():
        try:
            existing = {r["item_id"]: r for r in json.load(open(args.output))
                        if r.get("anomaly_score") is not None and not r.get("error")}
            items = [x for x in items if x["item_id"] not in existing]
            print(f"Resume: {len(existing)} already done, {len(items)} to do")
        except Exception:
            pass

    # Zoom router rule (fixed): zoom_fusion for industrial/medical/logical,
    # direct for semantic. Used when --use_zoom_router is set.
    ZOOM_RULE = {
        "D1": "zoom_fusion", "D2": "zoom_fusion", "D4": "zoom_fusion",
        "D5": "zoom_fusion", "D5b": "zoom_fusion", "D5c": "zoom_fusion",
        "D5d": "direct", "D6": "direct", "D7": "direct", "D8": "direct",
        "D9": "zoom_fusion", "D10": "zoom_fusion",
    }

    # If an explicit agent plan file is given, use that directly.
    AGENT_PLAN = None
    if args.agent_plan:
        AGENT_PLAN = json.load(open(args.agent_plan))
        print(f"Using agent plan from {args.agent_plan}: default={AGENT_PLAN.get('default_strategy')}")
        for d, info in AGENT_PLAN.get("per_domain", {}).items():
            print(f"  {d}: strategy={info.get('strategy')} expert={info.get('expert')} calib_auroc={info.get('calib_auroc')}")

    # Pre-warm planner: compute one plan per (model, domain) up-front so that
    # parallel workers don't all race to call the planner.
    if not args.use_calib_router and not args.use_zoom_router and not args.agent_plan:
        unique_domains = sorted({x["domain_code"] for x in items})
        for d in unique_domains:
            n_r = next((len(x.get("ref_paths") or []) for x in items if x["domain_code"] == d), 2)
            p = autonomous_plan(client, model, d, n_r)
            print(f"  plan[{d}] = {p['strategy']:9s} expert={p['expert']:11s} "
                  f"tools={p['tools']} :: {p.get('reasoning', '')[:100]}")
        # Save planner trace
        plan_trace = {f"{model}|{d}": _plan_cache.get((model, d)) for d in unique_domains}
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output.replace(".json", "_plans.json"), "w") as f:
            json.dump(plan_trace, f, indent=2, default=str)
    else:
        # Calibration router fixed assignment (loaded from previous analysis)
        calib_path = Path("/hdd1/jiangxi/AD-Agent/refine-logs/ROUTER_RESULTS.json")
        rr = json.load(open(calib_path))
        bk_key = {"gpt": "gpt54", "seedvl": "seedvl", "qwen3": "qwen35"}[args.backend]
        assn = rr[bk_key]["calibration_assignment"]
        print(f"Using calibration router assignment: {assn}")

    # Sequential or parallel
    results = list(existing.values())
    errors = 0

    def process(item):
        if AGENT_PLAN:
            info = AGENT_PLAN.get("per_domain", {}).get(item["domain_code"], {})
            strat = info.get("strategy", AGENT_PLAN.get("default_strategy", "fusion_subs"))
            fp = {"strategy": strat, "expert": info.get("expert"),
                  "tools": info.get("tools", ["domain_descriptor"]),
                  "reasoning": f"agent plan calib_auroc={info.get('calib_auroc')}"}
            return run_item(item, client, model, expert_cache, fixed_plan=fp)
        if args.use_zoom_router:
            strat = ZOOM_RULE.get(item["domain_code"], "fusion")
            fp = {"strategy": strat, "expert": "subspacead",
                  "tools": ["domain_descriptor", "hotspot_cropper"],
                  "reasoning": "zoom router rule"}
            return run_item(item, client, model, expert_cache, fixed_plan=fp)
        if args.use_calib_router:
            strat = assn.get(item["domain_code"], "fusion")
            if strat in ("fusion_v0_subspace",):
                strat = "fusion"
            if strat == "subspacead":
                strat = "fusion"
            fp = {"strategy": strat, "expert": "subspacead", "tools": ["domain_descriptor"],
                  "reasoning": "calibration argmax"}
            return run_item(item, client, model, expert_cache, fixed_plan=fp)
        return run_item(item, client, model, expert_cache)

    from tqdm import tqdm
    with ThreadPoolExecutor(max_workers=args.max_workers) as pool:
        futures = {pool.submit(process, item): item for item in items}
        for fut in tqdm(as_completed(futures), total=len(futures), desc="anomaclaw_v3"):
            r = fut.result()
            results.append(r)
            if r.get("error"):
                errors += 1
            # Incremental save every 25
            if len(results) % 25 == 0:
                Path(args.output).parent.mkdir(parents=True, exist_ok=True)
                with open(args.output, "w") as f:
                    json.dump(results, f, indent=2, default=str)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Done: {len(results)} items, {errors} errors -> {args.output}")


if __name__ == "__main__":
    main()
