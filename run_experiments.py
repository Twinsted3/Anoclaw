#!/usr/bin/env python3
"""
AnomalyClaw: Unified Experiment Runner
=======================================
Runs all methods from EXPERIMENT_BRIDGE_GUIDE.md on the D1-D12 benchmark.

Usage:
  # Expert-only baselines (no API cost)
  python run_experiments.py --method patchcore --domains D1,D2,D3
  python run_experiments.py --method clip_zeroshot --domains all

  # Single-pass VLM
  python run_experiments.py --method vlm_direct --backend seedvl --domains all
  python run_experiments.py --method retrieval_vlm --backend seedvl
  python run_experiments.py --method expert_vlm --backend seedvl

  # Debate methods
  python run_experiments.py --method symmetric_debate --backend seedvl
  python run_experiments.py --method anomaclaw --backend seedvl

  # Ablations
  python run_experiments.py --method anomaclaw --ablation debate --backend seedvl
  python run_experiments.py --method anomaclaw --ablation experts --backend seedvl
  python run_experiments.py --method anomaclaw --ablation depth --depth 1 --backend seedvl

  # Multi-VLM
  python run_experiments.py --method anomaclaw --backend gpt4o
  python run_experiments.py --method anomaclaw --backend gpt54

  # Sanity check (2 items per domain)
  python run_experiments.py --method patchcore --domains D1 --max_per_domain 2
"""

import argparse
import csv
import json
import os
import sys
import time
import traceback
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MANIFEST_PATH = "benchmark/manifests_v2/full_manifest.json"
RESULT_DIR = "result/experiments"
MAX_IMAGE_DIM = 512
SEED = 42

# Backend configs
BACKENDS = {
    "seedvl": {
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "api_key": "***REDACTED-SEED-KEY***",
        "model": "doubao-seed-2-0-lite-260215",
    },
    "seedvl_pro": {
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "api_key": "***REDACTED-SEED-KEY***",
        "model": "doubao-seed-2-0-pro-260215",
    },
    "gpt4o": {
        "base_url": "http://localhost:8080/v1",
        "api_key": "***REDACTED-GPT-KEY***",
        "model": "gpt-4o",
    },
    "gpt54": {
        "base_url": "http://localhost:8080/v1",
        "api_key": "***REDACTED-GPT-KEY***",
        "model": "gpt-5.4",
    },
    "qwen25vl": {
        "base_url": "http://localhost:8001/v1",
        "api_key": "EMPTY",
        "model": "Qwen/Qwen2.5-VL-7B-Instruct",
    },
    "qwen35": {
        "base_url": "http://localhost:8210/v1",
        "api_key": "EMPTY",
        "model": "Qwen3.5-VL-27B",
    },
}

ALL_DOMAINS = [f"D{i}" for i in range(1, 13)]

# ---------------------------------------------------------------------------
# Image loading
# ---------------------------------------------------------------------------

def resize_if_needed(frame_rgb, max_dim=MAX_IMAGE_DIM):
    h, w = frame_rgb.shape[:2]
    if max(h, w) <= max_dim:
        return frame_rgb
    scale = max_dim / max(h, w)
    return cv2.resize(frame_rgb, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)


def load_image_rgb(path: str):
    frame_bgr = cv2.imread(path)
    if frame_bgr is None:
        raise ValueError(f"Cannot read image: {path}")
    return resize_if_needed(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))


# ---------------------------------------------------------------------------
# Manifest loading
# ---------------------------------------------------------------------------

def load_manifest(manifest_path: str, domains: List[str], split: str = "test",
                  max_per_domain: Optional[int] = None) -> List[Dict]:
    with open(manifest_path) as f:
        manifest = json.load(f)

    items = [m for m in manifest if m["domain_code"] in domains and m["split"] == split]

    if max_per_domain is not None:
        import random
        rng = random.Random(SEED)
        filtered = []
        for dc in sorted(set(i["domain_code"] for i in items)):
            dc_items = [i for i in items if i["domain_code"] == dc]
            # Stratified: half normal, half anomalous
            normals = [i for i in dc_items if i["label"] == 0]
            anomalies = [i for i in dc_items if i["label"] == 1]
            rng.shuffle(normals)
            rng.shuffle(anomalies)
            half = max_per_domain // 2
            filtered.extend(normals[:half])
            filtered.extend(anomalies[:half])
        items = filtered

    return items


# ---------------------------------------------------------------------------
# AUROC computation
# ---------------------------------------------------------------------------

def compute_auroc(labels: List[int], scores: List[float]) -> float:
    """Compute AUROC without sklearn dependency."""
    if len(set(labels)) < 2:
        return float("nan")

    pairs = sorted(zip(scores, labels), reverse=True)
    tp = 0
    fp = 0
    tp_prev = 0
    fp_prev = 0
    auc = 0.0
    total_pos = sum(labels)
    total_neg = len(labels) - total_pos

    if total_pos == 0 or total_neg == 0:
        return float("nan")

    prev_score = None
    for score, label in pairs:
        if prev_score is not None and score != prev_score:
            auc += (fp - fp_prev) * (tp + tp_prev) / 2.0
            tp_prev = tp
            fp_prev = fp
        if label == 1:
            tp += 1
        else:
            fp += 1
        prev_score = score

    auc += (fp - fp_prev) * (tp + tp_prev) / 2.0
    return auc / (total_pos * total_neg)


# ---------------------------------------------------------------------------
# Method: CLIP Zero-Shot
# ---------------------------------------------------------------------------

_clip_state = {}

def _get_clip():
    if "model" in _clip_state:
        return _clip_state["model"], _clip_state["processor"], _clip_state["device"]

    import torch
    try:
        from transformers import CLIPModel, CLIPProcessor
    except ImportError:
        raise ImportError("pip install transformers")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_name = "openai/clip-vit-base-patch16"
    print(f"  Loading CLIP model: {model_name}...")
    model = CLIPModel.from_pretrained(model_name).to(device).eval()
    processor = CLIPProcessor.from_pretrained(model_name)
    _clip_state["model"] = model
    _clip_state["processor"] = processor
    _clip_state["device"] = device
    return model, processor, device


def run_clip_zeroshot(item: Dict) -> float:
    """CLIP zero-shot: P(defective) vs P(normal)."""
    import torch
    from PIL import Image

    model, processor, device = _get_clip()

    img = Image.open(item["query_path"]).convert("RGB")
    texts = ["a photo of a normal object", "a photo of a defective object with anomaly"]

    inputs = processor(text=texts, images=img, return_tensors="pt", padding=True).to(device)
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits_per_image[0]  # [2]
        probs = logits.softmax(dim=-1).cpu().numpy()

    return float(probs[1])  # P(defective)


# ---------------------------------------------------------------------------
# Method: PatchCore Expert
# ---------------------------------------------------------------------------

def run_patchcore(item: Dict) -> float:
    """PatchCore expert: calibrated anomaly score from DINOv2 patch features."""
    from experts import PatchExpert
    expert = PatchExpert(max_refs=8, top_fraction=0.01)

    report = expert.analyze(item["query_path"], item["ref_paths"], item["domain_code"])
    # Parse calibrated score from report
    for line in report.split("\n"):
        if "Calibrated score:" in line:
            return float(line.split(":")[-1].strip())
    return 0.5


# ---------------------------------------------------------------------------
# VLM-based methods: shared infrastructure
# ---------------------------------------------------------------------------

def _setup_vlm_backend(backend_name: str):
    """Configure the OpenAI-compatible client for VLM calls."""
    from openai import AsyncOpenAI
    from agents import set_default_openai_api, set_default_openai_client, set_tracing_disabled

    cfg = BACKENDS[backend_name]
    set_default_openai_api("chat_completions")
    set_tracing_disabled(True)
    client = AsyncOpenAI(base_url=cfg["base_url"], api_key=cfg["api_key"])
    set_default_openai_client(client)
    return cfg["model"]


def _extract_anomaly_score_from_verdict(report: Dict) -> float:
    """Convert debate report to continuous anomaly score [0,1].

    Uses claim_confidence * (1 - refute_confidence) for each claim,
    then takes the max. This gives a smooth score that reflects both
    the Proposer's confidence and the Advocate's ability to refute.
    """
    claims = report.get("claims", {})
    reviews = report.get("reviews", {})

    if not claims:
        return 0.05  # No claims → very likely normal

    claim_scores = []
    for cid, claim in claims.items():
        c_conf = float(claim.get("confidence", 0.5) or 0.5)
        review = reviews.get(cid, {})
        r_conf = float(review.get("refute_confidence", 0.3) or 0.3)
        effective = c_conf * (1.0 - r_conf)
        claim_scores.append(effective)

    return max(claim_scores) if claim_scores else 0.05


# ---------------------------------------------------------------------------
# Method: VLM-Direct (query only, no references)
# ---------------------------------------------------------------------------

def run_vlm_direct(item: Dict, model: str) -> float:
    """Single VLM call with query image only, no references."""
    from agents import Agent, Runner, RunConfig
    from utils import VisualContext, encode_image

    query_rgb = load_image_rgb(item["query_path"])
    b64 = _encode_rgb(query_rgb)

    agent = Agent(
        name="VLM_Direct",
        instructions=(
            "You are an anomaly detection system. Examine the query image and determine "
            "if it contains any anomalies or defects. Output strict JSON only."
        ),
        tools=[],
    )

    prompt = (
        "Look at this image. Is this object/scene normal or does it contain anomalies/defects?\n"
        "Output JSON: {\"verdict\": \"normal\" or \"anomaly\", \"confidence\": 0.0-1.0, "
        "\"reasoning\": \"brief explanation\"}"
    )

    messages = [
        {"role": "user", "content": [
            {"type": "input_image", "detail": "auto",
             "image_url": f"data:image/jpeg;base64,{b64}"}
        ]},
        {"role": "user", "content": "Query image."},
        {"role": "user", "content": prompt},
    ]

    run_config = RunConfig(
        model=model,
        trace_include_sensitive_data=False,
    )

    result = Runner.run_sync(agent, input=messages, run_config=run_config)
    text = result.final_output if hasattr(result, "final_output") else str(result)

    return _parse_vlm_score(text)


def _encode_rgb(frame_rgb) -> str:
    """Encode RGB numpy array to base64 JPEG."""
    import base64
    frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
    ok, buf = cv2.imencode(".jpg", frame_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    if not ok:
        raise ValueError("cv2.imencode failed")
    return base64.b64encode(buf.tobytes()).decode("utf-8")


def _parse_vlm_score(text: str) -> float:
    """Parse VLM JSON output into anomaly score."""
    import re
    text = (text or "").strip()

    # Try JSON parse
    try:
        # Strip code fence
        fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if fence:
            text = fence.group(1).strip()
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end > start:
            obj = json.loads(text[start:end+1])
            verdict = obj.get("verdict", "").lower()
            confidence = float(obj.get("confidence", 0.5) or 0.5)
            if "anomal" in verdict or "defect" in verdict:
                return max(0.5, confidence)
            elif "normal" in verdict:
                return min(0.5, 1.0 - confidence)
            return 0.5
    except Exception:
        pass

    # Fallback: keyword matching
    text_lower = text.lower()
    if "anomal" in text_lower or "defect" in text_lower:
        return 0.7
    elif "normal" in text_lower:
        return 0.3
    return 0.5


# ---------------------------------------------------------------------------
# Method: Retrieval + VLM
# ---------------------------------------------------------------------------

def run_retrieval_vlm(item: Dict, model: str) -> float:
    """DINOv2 retrieval evidence + single VLM call with references."""
    from agents import Agent, Runner, RunConfig
    from experts import RetrievalExpert
    from utils import load_visual_ctx

    # Get retrieval evidence
    ret_expert = RetrievalExpert(top_k=4)
    ret_report = ret_expert.analyze(item["query_path"], item["ref_paths"], item["domain_code"])

    # Load images
    query_rgb = load_image_rgb(item["query_path"])
    ref_rgb = load_image_rgb(item["ref_paths"][0]) if item["ref_paths"] else None

    visual_ctx = load_visual_ctx(
        [query_rgb],
        few_shot_frames=[ref_rgb] if ref_rgb is not None else None,
    )

    agent = Agent(
        name="Retrieval_VLM",
        instructions=(
            "You are an anomaly detection system. Compare the query image against "
            "the normal reference image and retrieval evidence. Output strict JSON."
        ),
        tools=[],
    )

    prompt = (
        "Compare the query image with the normal reference.\n"
        f"Retrieval evidence:\n{ret_report}\n\n"
        "Is the query normal or anomalous?\n"
        "Output JSON: {\"verdict\": \"normal\" or \"anomaly\", \"confidence\": 0.0-1.0, "
        "\"reasoning\": \"brief explanation\"}"
    )

    from vad2_system import _vision_messages
    messages = _vision_messages(visual_ctx, prompt_text=prompt)

    run_config = RunConfig(model=model, trace_include_sensitive_data=False)
    result = Runner.run_sync(agent, input=messages, run_config=run_config)
    text = result.final_output if hasattr(result, "final_output") else str(result)
    return _parse_vlm_score(text)


# ---------------------------------------------------------------------------
# Method: Expert-Informed VLM
# ---------------------------------------------------------------------------

def run_expert_vlm(item: Dict, model: str) -> float:
    """Full expert evidence (patch + retrieval) + single VLM call."""
    from agents import Agent, Runner, RunConfig
    from experts import ExpertPool
    from utils import load_visual_ctx

    pool = ExpertPool()
    reports = pool.run_selected(
        ["patch", "retrieval"], item["query_path"], item["ref_paths"], item["domain_code"]
    )
    evidence = "\n\n".join(f"[{n.upper()}]\n{r}" for n, r in reports.items())

    query_rgb = load_image_rgb(item["query_path"])
    ref_rgb = load_image_rgb(item["ref_paths"][0]) if item["ref_paths"] else None
    visual_ctx = load_visual_ctx(
        [query_rgb],
        few_shot_frames=[ref_rgb] if ref_rgb is not None else None,
    )

    agent = Agent(
        name="Expert_VLM",
        instructions=(
            "You are an anomaly detection system with expert evidence. Compare the query "
            "image against the reference and expert analysis. Output strict JSON."
        ),
        tools=[],
    )

    prompt = (
        "Compare the query image with the normal reference.\n"
        f"Expert evidence:\n{evidence}\n\n"
        "Use the expert scores as quantitative grounding but make your own visual judgment.\n"
        "Output JSON: {\"verdict\": \"normal\" or \"anomaly\", \"confidence\": 0.0-1.0, "
        "\"reasoning\": \"brief explanation\"}"
    )

    from vad2_system import _vision_messages
    messages = _vision_messages(visual_ctx, prompt_text=prompt)

    run_config = RunConfig(model=model, trace_include_sensitive_data=False)
    result = Runner.run_sync(agent, input=messages, run_config=run_config)
    text = result.final_output if hasattr(result, "final_output") else str(result)
    return _parse_vlm_score(text)


# ---------------------------------------------------------------------------
# Method: Symmetric Debate
# ---------------------------------------------------------------------------

def run_symmetric_debate(item: Dict, model: str) -> float:
    """Two identical VLM agents debate (same prompt, no asymmetric roles)."""
    from agents import Agent, Runner, RunConfig
    from utils import load_visual_ctx
    from vad2_system import _vision_messages, _extract_json

    query_rgb = load_image_rgb(item["query_path"])
    ref_rgb = load_image_rgb(item["ref_paths"][0]) if item["ref_paths"] else None
    visual_ctx = load_visual_ctx(
        [query_rgb],
        few_shot_frames=[ref_rgb] if ref_rgb is not None else None,
    )

    symmetric_instructions = (
        "You are an anomaly detection agent. Examine images and debate whether "
        "the query contains anomalies. Be objective. Output strict JSON."
    )

    agent_a = Agent(name="Debater_A", instructions=symmetric_instructions, tools=[])
    agent_b = Agent(name="Debater_B", instructions=symmetric_instructions, tools=[])

    run_config = RunConfig(model=model, trace_include_sensitive_data=False)

    # Round 1: Agent A proposes
    prompt_a = (
        "Compare the query image with the normal reference.\n"
        "List any anomalies you see.\n"
        "Output JSON: {\"claims\": [{\"id\": \"A1\", \"description\": \"...\", "
        "\"confidence\": 0.0-1.0}], \"verdict\": \"normal\" or \"anomaly\"}"
    )
    msgs_a = _vision_messages(visual_ctx, prompt_text=prompt_a)
    result_a = Runner.run_sync(agent_a, input=msgs_a, run_config=run_config)
    text_a = result_a.final_output if hasattr(result_a, "final_output") else str(result_a)

    # Round 2: Agent B reviews
    prompt_b = (
        "Another agent analyzed this image and produced:\n"
        f"{text_a}\n\n"
        "Do you agree? Challenge or confirm each claim.\n"
        "Output JSON: {\"verdict\": \"normal\" or \"anomaly\", \"confidence\": 0.0-1.0, "
        "\"reasoning\": \"your assessment\"}"
    )
    msgs_b = _vision_messages(visual_ctx, prompt_text=prompt_b)
    result_b = Runner.run_sync(agent_b, input=msgs_b, run_config=run_config)
    text_b = result_b.final_output if hasattr(result_b, "final_output") else str(result_b)

    # Aggregate: average both verdicts
    score_a = _parse_vlm_score(text_a)
    score_b = _parse_vlm_score(text_b)
    return (score_a + score_b) / 2.0


# ---------------------------------------------------------------------------
# Method: AnomalyClaw (full system)
# ---------------------------------------------------------------------------

def run_anomaclaw(item: Dict, model: str, depth: Optional[int] = None,
                  use_experts: bool = True, expert_list: Optional[List[str]] = None,
                  debate_type: str = "asymmetric") -> float:
    """Full AnomalyClaw system with configurable ablation parameters."""
    from utils import load_visual_ctx
    from vad2_system import DualVADAgentSystem, DualVADConfig

    query_rgb = load_image_rgb(item["query_path"])
    ref_rgb = load_image_rgb(item["ref_paths"][0]) if item["ref_paths"] else None
    visual_ctx = load_visual_ctx(
        [query_rgb],
        few_shot_frames=[ref_rgb] if ref_rgb is not None else None,
    )

    cfg = DualVADConfig(
        model=model,
        depth_quota=depth or 2,
        use_experts=use_experts,
        domain_code=item["domain_code"],
    )
    system = DualVADAgentSystem(config=cfg)

    report = system.run(
        visual_ctx,
        query_path=item["query_path"],
        ref_paths=item["ref_paths"],
        domain_code=item["domain_code"],
    )

    return _extract_anomaly_score_from_verdict(report)


# ---------------------------------------------------------------------------
# Ablation configurations
# ---------------------------------------------------------------------------

ABLATION_CONFIGS = {
    # Table 4: Debate ablation
    "debate": {
        "single_no_expert":    {"method": "expert_vlm_custom", "use_experts": False, "debate": False},
        "single_with_expert":  {"method": "expert_vlm_custom", "use_experts": True, "debate": False},
        "symmetric_no_expert": {"method": "symmetric_debate", "use_experts": False},
        "symmetric_with_expert": {"method": "symmetric_debate", "use_experts": True},
        "asymmetric":          {"method": "anomaclaw", "use_experts": True, "debate_type": "asymmetric"},
    },
    # Table 5: Expert pool ablation
    "experts": {
        "debate_only":     {"method": "anomaclaw", "use_experts": False},
        "retrieval_only":  {"method": "anomaclaw", "use_experts": True, "expert_list": ["retrieval"]},
        "patch_only":      {"method": "anomaclaw", "use_experts": True, "expert_list": ["patch"]},
        "patch_retrieval": {"method": "anomaclaw", "use_experts": True, "expert_list": ["patch", "retrieval"]},
        "all_experts":     {"method": "anomaclaw", "use_experts": True, "expert_list": ["patch", "retrieval", "texture"]},
    },
    # Table 6: Depth ablation
    "depth": {
        "depth_1": {"method": "anomaclaw", "depth": 1},
        "depth_2": {"method": "anomaclaw", "depth": 2},
        "depth_3": {"method": "anomaclaw", "depth": 3},
        "depth_4": {"method": "anomaclaw", "depth": 4},
    },
}


# ---------------------------------------------------------------------------
# Main dispatcher
# ---------------------------------------------------------------------------

def run_single_item(method: str, item: Dict, model: str = "", **kwargs) -> float:
    """Dispatch to the appropriate method and return anomaly score [0,1]."""
    if method == "clip_zeroshot":
        return run_clip_zeroshot(item)
    elif method == "patchcore":
        return run_patchcore(item)
    elif method == "vlm_direct":
        return run_vlm_direct(item, model)
    elif method == "retrieval_vlm":
        return run_retrieval_vlm(item, model)
    elif method == "expert_vlm":
        return run_expert_vlm(item, model)
    elif method == "symmetric_debate":
        return run_symmetric_debate(item, model)
    elif method == "anomaclaw":
        return run_anomaclaw(
            item, model,
            depth=kwargs.get("depth"),
            use_experts=kwargs.get("use_experts", True),
            expert_list=kwargs.get("expert_list"),
            debate_type=kwargs.get("debate_type", "asymmetric"),
        )
    else:
        raise ValueError(f"Unknown method: {method}")


def run_experiment(
    method: str,
    domains: List[str],
    backend: str = "",
    max_per_domain: Optional[int] = None,
    output_dir: str = RESULT_DIR,
    resume: bool = True,
    **method_kwargs,
) -> Dict[str, Any]:
    """Run a full experiment and return results."""

    # Setup VLM backend if needed
    model = ""
    vlm_methods = {"vlm_direct", "retrieval_vlm", "expert_vlm", "symmetric_debate", "anomaclaw"}
    if method in vlm_methods:
        if not backend:
            raise ValueError(f"Method {method} requires --backend (seedvl, gpt4o, gpt54)")
        model = _setup_vlm_backend(backend)

    # Load test items
    items = load_manifest(MANIFEST_PATH, domains, split="test", max_per_domain=max_per_domain)
    print(f"\n{'='*60}")
    print(f"Experiment: {method} | Backend: {backend or 'local'} | Items: {len(items)}")
    print(f"Domains: {', '.join(domains)}")
    print(f"{'='*60}\n")

    # Prepare output
    tag = f"{method}_{backend}" if backend else method
    for k, v in method_kwargs.items():
        if v is not None:
            tag += f"_{k}={v}"
    os.makedirs(output_dir, exist_ok=True)
    results_path = os.path.join(output_dir, f"{tag}_results.json")
    detail_path = os.path.join(output_dir, f"{tag}_detail.jsonl")

    # Resume support
    completed = {}
    if resume and os.path.exists(detail_path):
        with open(detail_path) as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    completed[entry["item_id"]] = entry
                except Exception:
                    pass
        print(f"  Resuming: {len(completed)} items already done")

    # Run
    all_scores = []
    all_labels = []
    domain_scores = defaultdict(list)
    domain_labels = defaultdict(list)
    errors = 0
    start_time = time.time()

    detail_f = open(detail_path, "a")

    for i, item in enumerate(items):
        item_id = item["item_id"]
        if item_id in completed:
            entry = completed[item_id]
            score = entry["score"]
            label = entry["label"]
        else:
            try:
                score = run_single_item(method, item, model, **method_kwargs)
                label = item["label"]

                entry = {
                    "item_id": item_id,
                    "domain_code": item["domain_code"],
                    "category": item.get("category", ""),
                    "label": label,
                    "score": score,
                }
                detail_f.write(json.dumps(entry) + "\n")
                detail_f.flush()

            except Exception as e:
                errors += 1
                print(f"  [{item_id}] ERROR: {e}")
                if errors <= 3:
                    traceback.print_exc()
                continue

        all_scores.append(score)
        all_labels.append(label)
        dc = item["domain_code"]
        domain_scores[dc].append(score)
        domain_labels[dc].append(label)

        if (i + 1) % 20 == 0 or i == len(items) - 1:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            current_auroc = compute_auroc(all_labels, all_scores)
            print(f"  [{i+1}/{len(items)}] AUROC={current_auroc:.4f} | "
                  f"{rate:.1f} items/s | errors={errors}")

    detail_f.close()
    elapsed = time.time() - start_time

    # Compute per-domain AUROC
    domain_aurocs = {}
    for dc in sorted(domain_scores.keys()):
        domain_aurocs[dc] = compute_auroc(domain_labels[dc], domain_scores[dc])

    macro_auroc = np.nanmean(list(domain_aurocs.values()))
    micro_auroc = compute_auroc(all_labels, all_scores)

    results = {
        "method": method,
        "backend": backend,
        "model": model,
        "tag": tag,
        "domains": domains,
        "total_items": len(items),
        "completed": len(all_scores),
        "errors": errors,
        "elapsed_seconds": round(elapsed, 1),
        "macro_auroc": round(float(macro_auroc), 4),
        "micro_auroc": round(float(micro_auroc), 4),
        "domain_aurocs": {k: round(v, 4) for k, v in domain_aurocs.items()},
        "method_kwargs": {k: v for k, v in method_kwargs.items() if v is not None},
    }

    with open(results_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Print summary
    print(f"\n{'='*60}")
    print(f"Results: {method} ({backend or 'local'})")
    print(f"  Macro AUROC: {macro_auroc:.4f}")
    print(f"  Micro AUROC: {micro_auroc:.4f}")
    print(f"  Per-domain:")
    for dc in sorted(domain_aurocs.keys()):
        print(f"    {dc}: {domain_aurocs[dc]:.4f}")
    print(f"  Time: {elapsed:.0f}s | Errors: {errors}")
    print(f"  Saved: {results_path}")
    print(f"{'='*60}\n")

    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="AnomalyClaw Experiment Runner")
    parser.add_argument("--method", type=str, required=True,
                        choices=["clip_zeroshot", "patchcore", "vlm_direct",
                                 "retrieval_vlm", "expert_vlm", "symmetric_debate",
                                 "anomaclaw"],
                        help="Method to run")
    parser.add_argument("--backend", type=str, default="",
                        choices=["", "seedvl", "seedvl_pro", "gpt4o", "gpt54", "qwen25vl", "qwen35"],
                        help="VLM backend")
    parser.add_argument("--domains", type=str, default="all",
                        help="Comma-separated domain codes (e.g., D1,D2) or 'all'")
    parser.add_argument("--max_per_domain", type=int, default=None,
                        help="Max items per domain (for testing)")
    parser.add_argument("--output_dir", type=str, default=RESULT_DIR)
    parser.add_argument("--no_resume", action="store_true")

    # Ablation params
    parser.add_argument("--ablation", type=str, default="",
                        choices=["", "debate", "experts", "depth"],
                        help="Ablation study type")
    parser.add_argument("--ablation_config", type=str, default="",
                        help="Specific ablation config name")
    parser.add_argument("--depth", type=int, default=None, help="Override debate depth")
    parser.add_argument("--use_experts", type=str, default=None,
                        help="true/false override for expert usage")
    parser.add_argument("--expert_list", type=str, default=None,
                        help="Comma-separated expert names")

    args = parser.parse_args()

    domains = ALL_DOMAINS if args.domains == "all" else args.domains.split(",")

    # Build method kwargs
    kwargs = {}
    if args.depth is not None:
        kwargs["depth"] = args.depth
    if args.use_experts is not None:
        kwargs["use_experts"] = args.use_experts.lower() == "true"
    if args.expert_list:
        kwargs["expert_list"] = args.expert_list.split(",")

    # Handle ablation studies
    if args.ablation and args.ablation_config:
        configs = ABLATION_CONFIGS.get(args.ablation, {})
        cfg = configs.get(args.ablation_config)
        if cfg is None:
            print(f"Available configs for {args.ablation}: {list(configs.keys())}")
            sys.exit(1)
        method = cfg.pop("method", args.method)
        kwargs.update(cfg)
        run_experiment(method, domains, args.backend, args.max_per_domain,
                       args.output_dir, not args.no_resume, **kwargs)
    elif args.ablation:
        # Run all configs for this ablation
        configs = ABLATION_CONFIGS.get(args.ablation, {})
        for config_name, cfg in configs.items():
            print(f"\n>>> Ablation config: {config_name}")
            cfg_copy = dict(cfg)
            method = cfg_copy.pop("method", args.method)
            run_experiment(method, domains, args.backend, args.max_per_domain,
                           args.output_dir, not args.no_resume, **cfg_copy)
    else:
        run_experiment(args.method, domains, args.backend, args.max_per_domain,
                       args.output_dir, not args.no_resume, **kwargs)


if __name__ == "__main__":
    main()
