"""
AnomaClaw Agent V4: Expert-First, VLM-Adjudication.

Architecture:
  1. DINOv2 retrieval → top-k refs
  2. PatchCore expert → anomaly score + patch distances + heatmap info
  3. If expert is confident → trust directly (no VLM call)
  4. If expert is uncertain → one VLM call with refs + expert signal

Modes:
  baseline        — random refs, VLM direct (V0)
  retrieval       — DINOv2 refs, VLM direct (V2-retrieval)
  expert_only     — DINOv2 refs, PatchCore expert only (no VLM)
  expert_vlm      — expert + VLM for uncertain cases
  agent           — expert + VLM + domain knowledge (full agent)
"""

import argparse
import base64
import json
import os
import sys
import time
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, List, Dict, Any

import cv2
import numpy as np
from openai import OpenAI


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

sys.path.insert(0, str(Path(__file__).parent))
from agent_tools import tool_visual_retrieval, tool_domain_knowledge
from patch_expert import patch_expert_score

# ─── Image utils ──────────────────────────────────────────────────────────────

def load_and_encode(path: str, max_side: int = 512) -> str:
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(f"Cannot read: {path}")
    h, w = img.shape[:2]
    if max(h, w) > max_side:
        scale = max_side / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)))
    _, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return base64.b64encode(buf).decode("utf-8")

def img_msg(b64): return {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "high"}}
def text_msg(t): return {"type": "text", "text": t}

def extract_json(text):
    if not text: return None
    text = text.strip()
    try: return json.loads(text)
    except: pass
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if m:
        try: return json.loads(m.group(1).strip())
        except: pass
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try: return json.loads(m.group(0))
        except: pass
    return None

def call_llm(client, model, content, max_tokens=700):
    resp = client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": content}],
        max_tokens=max_tokens, temperature=0.0)
    text = resp.choices[0].message.content or ""
    return text, resp.usage.prompt_tokens, resp.usage.completion_tokens

# ─── Domain context ──────────────────────────────────────────────────────────

DOMAIN_CONTEXT = {
    "D1": "industrial manufacturing product",
    "D2": "retail product or shelf item",
    "D4": "concrete or infrastructure surface",
    "D5": "dermoscopic image of a skin lesion",
    "D5b": "brain MRI slice",
    "D5c": "liver CT slice",
    "D5d": "gastrointestinal endoscopy image",
    "D7": "road or traffic scene",
    "D9": "assembled product with multiple components (check logical correctness)",
    "D10": "industrial product (PCB, capsule, candle, etc.)",
}

# Anomaly families for structured reasoning
ANOMALY_FAMILY = {
    "D1": "local_appearance", "D10": "local_appearance", "D2": "local_appearance",
    "D4": "local_appearance",
    "D5": "semantic_medical", "D5b": "semantic_medical", "D5c": "semantic_medical",
    "D5d": "semantic_medical",
    "D7": "semantic_scene",
    "D9": "logical_structural",
}

# ─── Scoring ─────────────────────────────────────────────────────────────────

OUTPUT_SCHEMA = """{
  "image_label": "normal" or "anomalous",
  "anomaly_type": "type or null",
  "evidence": "brief description",
  "confidence": float 0-1
}"""

def score_from_response(parsed):
    if not parsed: return 0.5
    label = str(parsed.get("label", parsed.get("image_label", parsed.get("final_label", "")))).lower()
    conf = float(parsed.get("confidence", parsed.get("final_confidence", 0.5)))
    if "anomal" in label:
        return max(conf, 0.5 + 1e-6)
    elif "normal" in label:
        return min(1.0 - conf, 0.5 - 1e-6)
    return 0.5


# ─── Mode: Baseline ─────────────────────────────────────────────────────────

def run_baseline(client, model, item, n_refs=4):
    ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:n_refs]]
    query_img = load_and_encode(item["query_path"])
    ctx = DOMAIN_CONTEXT.get(item["domain_code"], "image")

    content = []
    for b64 in ref_imgs:
        content.append(text_msg("Normal reference:"))
        content.append(img_msg(b64))
    content.append(text_msg("Query image:"))
    content.append(img_msg(query_img))
    content.append(text_msg(
        f"You are inspecting a {ctx}. The reference images show the normal state.\n"
        f"Decide whether the query image is normal or anomalous.\n"
        f"Return JSON only:\n{OUTPUT_SCHEMA}"
    ))

    t0 = time.time()
    text, inp, out = call_llm(client, model, content)
    parsed = extract_json(text)
    return {
        "anomaly_score": score_from_response(parsed),
        "raw_output": {"method": "baseline", "response": parsed},
        "cost_tokens": {"input": inp, "output": out},
        "latency_sec": round(time.time() - t0, 2),
    }


# ─── Mode: Retrieval ────────────────────────────────────────────────────────

def run_retrieval(client, model, item, n_refs=4):
    retrieved = tool_visual_retrieval(item["query_path"], item["domain_code"], k=n_refs)
    if not retrieved:
        return run_baseline(client, model, item, n_refs)

    ref_paths = [p for p, s in retrieved]
    ref_imgs = [load_and_encode(p) for p in ref_paths]
    query_img = load_and_encode(item["query_path"])
    ctx = DOMAIN_CONTEXT.get(item["domain_code"], "image")

    content = []
    for i, b64 in enumerate(ref_imgs):
        content.append(text_msg(f"Normal reference {i+1}:"))
        content.append(img_msg(b64))
    content.append(text_msg("Query image:"))
    content.append(img_msg(query_img))
    content.append(text_msg(
        f"You are inspecting a {ctx}. The reference images are the most visually "
        f"similar normal samples.\n"
        f"Decide whether the query image is normal or anomalous.\n"
        f"Return JSON only:\n{OUTPUT_SCHEMA}"
    ))

    t0 = time.time()
    text, inp, out = call_llm(client, model, content)
    parsed = extract_json(text)
    return {
        "anomaly_score": score_from_response(parsed),
        "raw_output": {"method": "retrieval", "retrieved": [(p, round(s,3)) for p,s in retrieved], "response": parsed},
        "cost_tokens": {"input": inp, "output": out},
        "latency_sec": round(time.time() - t0, 2),
    }


# ─── Mode: Expert Only (no VLM) ─────────────────────────────────────────────

def run_expert_only(client, model, item, n_refs=4):
    """Pure PatchCore expert — no VLM calls at all."""
    t0 = time.time()

    # Retrieve best refs
    retrieved = tool_visual_retrieval(item["query_path"], item["domain_code"], k=n_refs)
    if retrieved:
        ref_paths = [p for p, s in retrieved]
    else:
        ref_paths = item["ref_paths"][:n_refs]

    # Run patch expert
    expert = patch_expert_score(item["query_path"], ref_paths, max_refs=n_refs)

    return {
        "anomaly_score": expert["anomaly_score"],
        "raw_output": {"method": "expert_only", "expert": expert},
        "cost_tokens": {"input": 0, "output": 0},
        "latency_sec": round(time.time() - t0, 2),
    }


# ─── Mode: Expert + VLM (adjudication for uncertain) ────────────────────────

EXPERT_CONFIDENCE_HIGH = 0.75  # expert score > this → trust as anomalous
EXPERT_CONFIDENCE_LOW = 0.25   # expert score < this → trust as normal

def run_expert_vlm(client, model, item, n_refs=4):
    """Expert-first with VLM adjudication for uncertain cases."""
    t0 = time.time()
    domain_code = item["domain_code"]
    ctx = DOMAIN_CONTEXT.get(domain_code, "image")
    inp_total, out_total = 0, 0

    # Step 1: Retrieval
    retrieved = tool_visual_retrieval(item["query_path"], domain_code, k=n_refs)
    if retrieved:
        ref_paths = [p for p, s in retrieved]
        sims = [s for _, s in retrieved]
    else:
        ref_paths = item["ref_paths"][:n_refs]
        sims = []

    # Step 2: Patch expert
    expert = patch_expert_score(item["query_path"], ref_paths, max_refs=n_refs)
    expert_score = expert["anomaly_score"]

    # Step 3: If expert is confident, return directly
    if expert_score > EXPERT_CONFIDENCE_HIGH or expert_score < EXPERT_CONFIDENCE_LOW:
        return {
            "anomaly_score": expert_score,
            "raw_output": {
                "method": "expert_vlm", "path": "expert_confident",
                "expert": expert,
                "retrieval_sims": [round(s,3) for s in sims],
            },
            "cost_tokens": {"input": 0, "output": 0},
            "latency_sec": round(time.time() - t0, 2),
        }

    # Step 4: Expert uncertain → VLM adjudication
    ref_imgs = [load_and_encode(p) for p in ref_paths[:3]]  # 3 refs to save tokens
    query_img = load_and_encode(item["query_path"])

    expert_info = (
        f"\n--- Expert Model Analysis ---\n"
        f"PatchCore anomaly score: {expert_score:.3f} (0=normal, 1=anomalous)\n"
        f"Patch-level assessment: {expert['interpretation']}\n"
        f"Top patch distances: {expert.get('top_patch_distances', [])}\n"
        f"Global similarity to refs: {expert.get('global_similarity', 'N/A')}\n"
        f"Expert confidence: {expert['confidence']}\n"
        f"NOTE: The expert model found borderline evidence. "
        f"Use your visual judgment to make the final call.\n"
    )

    content = []
    for i, b64 in enumerate(ref_imgs):
        content.append(text_msg(f"Normal reference {i+1}:"))
        content.append(img_msg(b64))
    content.append(text_msg("Query image:"))
    content.append(img_msg(query_img))
    content.append(text_msg(
        f"You are inspecting a {ctx}.\n"
        f"{expert_info}\n"
        f"The automated expert found borderline results. "
        f"Look carefully at the query vs references and decide.\n"
        f"Return JSON only:\n{OUTPUT_SCHEMA}"
    ))

    text, inp, out = call_llm(client, model, content, max_tokens=500)
    inp_total += inp; out_total += out
    parsed = extract_json(text)
    vlm_score = score_from_response(parsed)

    # Fuse expert + VLM scores (weighted average, expert gets slight priority)
    fused_score = 0.4 * expert_score + 0.6 * vlm_score

    return {
        "anomaly_score": fused_score,
        "raw_output": {
            "method": "expert_vlm", "path": "vlm_adjudication",
            "expert": expert,
            "vlm_response": parsed,
            "expert_score": expert_score,
            "vlm_score": vlm_score,
            "fused_score": fused_score,
            "retrieval_sims": [round(s,3) for s in sims],
        },
        "cost_tokens": {"input": inp_total, "output": out_total},
        "latency_sec": round(time.time() - t0, 2),
    }


# ─── Mode: Full Agent (expert + VLM + knowledge) ────────────────────────────

def _build_knowledge_text(knowledge):
    if not knowledge: return ""
    text = f"\n--- Domain Knowledge: {knowledge.get('domain', '')} ---\n"
    text += f"Normal: {knowledge.get('normal', '')}\n"
    text += "Anomaly criteria:\n"
    for c in knowledge.get("anomaly_criteria", []):
        text += f"  - {c}\n"
    text += "Common false positives (do NOT flag these):\n"
    for fp in knowledge.get("common_false_positives", []):
        text += f"  - {fp}\n"
    return text


def run_agent(client, model, item, n_refs=4):
    """Full agent: expert + VLM + domain knowledge + family-aware reasoning."""
    t0 = time.time()
    domain_code = item["domain_code"]
    ctx = DOMAIN_CONTEXT.get(domain_code, "image")
    family = ANOMALY_FAMILY.get(domain_code, "unknown")
    inp_total, out_total = 0, 0

    # Step 1: Retrieval
    retrieved = tool_visual_retrieval(item["query_path"], domain_code, k=n_refs)
    if retrieved:
        ref_paths = [p for p, s in retrieved]
        sims = [s for _, s in retrieved]
    else:
        ref_paths = item["ref_paths"][:n_refs]
        sims = []

    # Step 2: Patch expert
    expert = patch_expert_score(item["query_path"], ref_paths, max_refs=n_refs)
    expert_score = expert["anomaly_score"]

    # Step 3: Domain knowledge
    knowledge = tool_domain_knowledge(domain_code)
    knowledge_text = _build_knowledge_text(knowledge)

    # Step 4: Decision routing
    # For local_appearance domains, trust expert more (good at texture/surface)
    # For semantic/logical domains, always use VLM (expert can't reason about semantics)
    if family == "local_appearance":
        high_thresh = 0.80
        low_thresh = 0.20
    elif family == "logical_structural":
        # Expert is weak for logical anomalies — always use VLM
        high_thresh = 0.95  # almost never skip VLM
        low_thresh = 0.05
    else:
        high_thresh = 0.75
        low_thresh = 0.25

    if expert_score > high_thresh or expert_score < low_thresh:
        return {
            "anomaly_score": expert_score,
            "raw_output": {
                "method": "agent", "path": "expert_confident",
                "expert": expert, "family": family,
                "retrieval_sims": [round(s,3) for s in sims],
            },
            "cost_tokens": {"input": 0, "output": 0},
            "latency_sec": round(time.time() - t0, 2),
        }

    # Step 5: VLM adjudication with full context
    ref_imgs = [load_and_encode(p) for p in ref_paths[:3]]
    query_img = load_and_encode(item["query_path"])

    expert_info = (
        f"\n--- Expert Model Analysis ---\n"
        f"PatchCore anomaly score: {expert_score:.3f} (0=normal, 1=anomalous)\n"
        f"Assessment: {expert['interpretation']}\n"
        f"Top patch distances: {expert.get('top_patch_distances', [])}\n"
        f"Global similarity: {expert.get('global_similarity', 'N/A')}\n"
    )

    # Family-specific VLM instructions
    if family == "logical_structural":
        family_instruction = (
            "IMPORTANT: This is a logical/structural anomaly domain. "
            "Count components, check positions, verify correct assembly. "
            "The expert model can only detect appearance differences — "
            "you must judge logical correctness yourself."
        )
    elif family == "semantic_medical":
        family_instruction = (
            "This is a medical imaging domain. Look for pathological features "
            "(lesions, masses, abnormal tissue). Minor acquisition differences "
            "(brightness, position) are NOT anomalies."
        )
    elif family == "semantic_scene":
        family_instruction = (
            "This is a scene-level anomaly domain. Look for unexpected objects "
            "or hazards on the road. Normal traffic is NOT anomalous."
        )
    else:
        family_instruction = (
            "Look for surface defects, damage, or contamination. "
            "Minor lighting/angle differences are NOT anomalies."
        )

    content = []
    for i, b64 in enumerate(ref_imgs):
        content.append(text_msg(f"Normal reference {i+1}:"))
        content.append(img_msg(b64))
    content.append(text_msg("Query image:"))
    content.append(img_msg(query_img))
    content.append(text_msg(
        f"You are an anomaly detection agent inspecting a {ctx}.\n"
        f"{expert_info}"
        f"{knowledge_text}\n"
        f"{family_instruction}\n\n"
        f"The expert model is uncertain. Make your visual judgment.\n"
        f"Return JSON only:\n{OUTPUT_SCHEMA}"
    ))

    text, inp, out = call_llm(client, model, content, max_tokens=500)
    inp_total += inp; out_total += out
    parsed = extract_json(text)
    vlm_score = score_from_response(parsed)

    # Fuse scores based on family
    if family == "local_appearance":
        # Expert is more reliable for texture anomalies
        fused = 0.5 * expert_score + 0.5 * vlm_score
    elif family == "logical_structural":
        # VLM is essential for logical reasoning
        fused = 0.2 * expert_score + 0.8 * vlm_score
    elif family == "semantic_medical":
        # Both contribute
        fused = 0.35 * expert_score + 0.65 * vlm_score
    else:
        fused = 0.3 * expert_score + 0.7 * vlm_score

    return {
        "anomaly_score": fused,
        "raw_output": {
            "method": "agent", "path": "vlm_adjudication",
            "expert": expert, "vlm_response": parsed,
            "expert_score": expert_score, "vlm_score": vlm_score,
            "fused_score": fused, "family": family,
            "retrieval_sims": [round(s,3) for s in sims],
        },
        "cost_tokens": {"input": inp_total, "output": out_total},
        "latency_sec": round(time.time() - t0, 2),
    }


# ─── Mode: Expert-Informed VLM (always call VLM with expert context) ─────────

def run_expert_informed(client, model, item, n_refs=4):
    """Always call VLM, but provide expert analysis as additional context.
    No routing, no score fusion — VLM makes the final decision."""
    t0 = time.time()
    domain_code = item["domain_code"]
    ctx = DOMAIN_CONTEXT.get(domain_code, "image")
    family = ANOMALY_FAMILY.get(domain_code, "unknown")

    # Step 1: Retrieval
    retrieved = tool_visual_retrieval(item["query_path"], domain_code, k=n_refs)
    if retrieved:
        ref_paths = [p for p, s in retrieved]
        sims = [s for _, s in retrieved]
    else:
        ref_paths = item["ref_paths"][:n_refs]
        sims = []

    # Step 2: Patch expert (runs on GPU, no API cost)
    expert = patch_expert_score(item["query_path"], ref_paths, max_refs=n_refs)

    # Step 3: Domain knowledge
    knowledge = tool_domain_knowledge(domain_code)
    knowledge_text = _build_knowledge_text(knowledge)

    # Step 4: Build expert context for VLM
    expert_context = (
        f"\n--- Automated Analysis (DINOv2 PatchCore) ---\n"
        f"Patch-level anomaly score: {expert['raw_patch_distance']:.3f} "
        f"(higher=more different from refs)\n"
        f"Global similarity to best ref: {expert.get('global_similarity', 'N/A')}\n"
        f"Assessment: {expert['interpretation']}\n"
    )

    # Family-specific guidance
    if family == "logical_structural":
        family_note = (
            "IMPORTANT: The automated model can only detect visual differences, "
            "not logical errors. YOU must check: correct count, correct positions, "
            "correct component types."
        )
    elif family == "semantic_medical":
        family_note = (
            "The automated model detects unusual image patches. In medical images, "
            "normal anatomical variation can look unusual. Focus on pathological "
            "features, not acquisition differences."
        )
    else:
        family_note = ""

    # Step 5: VLM call with full context
    ref_imgs = [load_and_encode(p) for p in ref_paths[:n_refs]]
    query_img = load_and_encode(item["query_path"])

    content = []
    for i, b64 in enumerate(ref_imgs):
        content.append(text_msg(f"Normal reference {i+1}:"))
        content.append(img_msg(b64))
    content.append(text_msg("Query image (classify this):"))
    content.append(img_msg(query_img))
    content.append(text_msg(
        f"You are an anomaly detection agent inspecting a {ctx}.\n"
        f"{expert_context}"
        f"{knowledge_text}\n"
        f"{family_note}\n\n"
        f"Use the automated analysis as one signal, but make your own visual judgment.\n"
        f"Return JSON only:\n{OUTPUT_SCHEMA}"
    ))

    text, inp, out = call_llm(client, model, content, max_tokens=500)
    parsed = extract_json(text)
    vlm_score = score_from_response(parsed)

    return {
        "anomaly_score": vlm_score,
        "raw_output": {
            "method": "expert_informed",
            "expert": expert,
            "vlm_response": parsed,
            "vlm_score": vlm_score,
            "family": family,
            "retrieval_sims": [round(s,3) for s in sims],
        },
        "cost_tokens": {"input": inp, "output": out},
        "latency_sec": round(time.time() - t0, 2),
    }


# ─── Mode: Retrieval+Knowledge (ablation: no expert, just knowledge text) ────

def run_retrieval_knowledge(client, model, item, n_refs=4):
    """Ablation: retrieval + domain knowledge text, NO expert context."""
    t0 = time.time()
    domain_code = item["domain_code"]
    ctx = DOMAIN_CONTEXT.get(domain_code, "image")

    retrieved = tool_visual_retrieval(item["query_path"], domain_code, k=n_refs)
    if retrieved:
        ref_paths = [p for p, s in retrieved]
    else:
        ref_paths = item["ref_paths"][:n_refs]

    knowledge = tool_domain_knowledge(domain_code)
    knowledge_text = _build_knowledge_text(knowledge)

    ref_imgs = [load_and_encode(p) for p in ref_paths[:n_refs]]
    query_img = load_and_encode(item["query_path"])

    content = []
    for i, b64 in enumerate(ref_imgs):
        content.append(text_msg(f"Normal reference {i+1}:"))
        content.append(img_msg(b64))
    content.append(text_msg("Query image (classify this):"))
    content.append(img_msg(query_img))
    content.append(text_msg(
        f"You are an anomaly detection agent inspecting a {ctx}.\n"
        f"{knowledge_text}\n\n"
        f"Use the domain knowledge to guide your analysis. "
        f"Return JSON only:\n{OUTPUT_SCHEMA}"
    ))

    text, inp, out = call_llm(client, model, content, max_tokens=500)
    parsed = extract_json(text)
    return {
        "anomaly_score": score_from_response(parsed),
        "raw_output": {"method": "retrieval_knowledge", "response": parsed},
        "cost_tokens": {"input": inp, "output": out},
        "latency_sec": round(time.time() - t0, 2),
    }


# ─── Mode: Knowledge-Informed (ablation: knowledge text but NO expert) ──────

def run_knowledge_only_informed(client, model, item, n_refs=4):
    """Ablation: retrieval + knowledge + generic analysis prompt (no expert model)."""
    t0 = time.time()
    domain_code = item["domain_code"]
    ctx = DOMAIN_CONTEXT.get(domain_code, "image")
    family = ANOMALY_FAMILY.get(domain_code, "unknown")

    retrieved = tool_visual_retrieval(item["query_path"], domain_code, k=n_refs)
    if retrieved:
        ref_paths = [p for p, s in retrieved]
        sims = [s for _, s in retrieved]
    else:
        ref_paths = item["ref_paths"][:n_refs]
        sims = []

    knowledge = tool_domain_knowledge(domain_code)
    knowledge_text = _build_knowledge_text(knowledge)

    # Generic analysis text (same length/format as expert context, but no real signal)
    generic_context = (
        f"\n--- Automated Analysis (Visual Comparison) ---\n"
        f"Reference similarity range: "
        f"{f'{min(sims):.3f} to {max(sims):.3f}' if sims else 'unknown'}\n"
        f"Number of references compared: {len(ref_paths)}\n"
        f"Assessment: Compare the query carefully against all references.\n"
    )

    if family == "logical_structural":
        family_note = (
            "IMPORTANT: Check correct count, correct positions, "
            "correct component types."
        )
    elif family == "semantic_medical":
        family_note = (
            "Focus on pathological features, not acquisition differences."
        )
    else:
        family_note = ""

    ref_imgs = [load_and_encode(p) for p in ref_paths[:n_refs]]
    query_img = load_and_encode(item["query_path"])

    content = []
    for i, b64 in enumerate(ref_imgs):
        content.append(text_msg(f"Normal reference {i+1}:"))
        content.append(img_msg(b64))
    content.append(text_msg("Query image (classify this):"))
    content.append(img_msg(query_img))
    content.append(text_msg(
        f"You are an anomaly detection agent inspecting a {ctx}.\n"
        f"{generic_context}"
        f"{knowledge_text}\n"
        f"{family_note}\n\n"
        f"Make your visual judgment.\n"
        f"Return JSON only:\n{OUTPUT_SCHEMA}"
    ))

    text, inp, out = call_llm(client, model, content, max_tokens=500)
    parsed = extract_json(text)
    return {
        "anomaly_score": score_from_response(parsed),
        "raw_output": {"method": "knowledge_informed", "response": parsed,
                       "retrieval_sims": [round(s,3) for s in sims]},
        "cost_tokens": {"input": inp, "output": out},
        "latency_sec": round(time.time() - t0, 2),
    }


# ─── Runner ──────────────────────────────────────────────────────────────────

MODE_FNS = {
    "baseline": run_baseline,
    "retrieval": run_retrieval,
    "expert_only": run_expert_only,
    "expert_vlm": run_expert_vlm,
    "agent": run_agent,
    "expert_informed": run_expert_informed,
    "retrieval_knowledge": run_retrieval_knowledge,
    "knowledge_informed": run_knowledge_only_informed,
}


def run_item(item, client, model, mode, n_refs):
    fn = MODE_FNS[mode]
    base = {
        "item_id": item["item_id"], "domain": item["domain"],
        "domain_code": item["domain_code"], "label_gt": item["label"],
        "split": item["split"], "source_dataset": item.get("source_dataset"),
        "category": item.get("category"),
    }
    try:
        result = fn(client, model, item, n_refs)
        base["label_pred"] = 1 if result["anomaly_score"] > 0.5 else 0
        base.update(result)
        base["error"] = None
    except Exception as e:
        import traceback
        base.update({"label_pred": 0, "anomaly_score": 0.5, "raw_output": None,
                      "cost_tokens": {"input": 0, "output": 0}, "latency_sec": 0.0,
                      "error": f"{str(e)}\n{traceback.format_exc()}"})
    return base


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="/hdd1/jiangxi/AD-Agent/benchmark/manifests/full_manifest.json")
    parser.add_argument("--split", default="test")
    parser.add_argument("--mode", required=True, choices=list(MODE_FNS.keys()))
    parser.add_argument("--output", required=True)
    parser.add_argument("--domains", nargs="*", default=None)
    parser.add_argument("--n_refs", type=int, default=4)
    parser.add_argument("--max_workers", type=int, default=4)
    parser.add_argument("--max_items", type=int, default=None)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    with open(args.manifest) as f:
        all_items = json.load(f)
    items = [x for x in all_items
             if (args.split == "all" or x["split"] == args.split)
             and (args.domains is None or x["domain_code"] in args.domains)]
    if args.max_items:
        items = items[:args.max_items]

    existing = {}
    if args.resume and Path(args.output).exists():
        with open(args.output) as f:
            for r in json.load(f):
                existing[r["item_id"]] = r
        items = [x for x in items if x["item_id"] not in existing]
        print(f"Resuming: {len(existing)} done, {len(items)} remaining")

    api_key = os.environ.get("GPT_API_KEY")
    base_url = os.environ.get("GPT_API_BASE")
    if not api_key:
        api_key = "***REDACTED-GPT-KEY***"
        base_url = "http://localhost:8080/v1"
    model = os.environ.get("GPT_MODEL", "gpt-5.4")
    client = OpenAI(api_key=api_key, base_url=base_url, timeout=120.0)

    print(f"Running {len(items)} items | mode={args.mode} | model={model}")

    results = list(existing.values())
    from tqdm import tqdm

    # For expert_only mode, no VLM needed → single worker (GPU bound)
    max_w = 1 if args.mode == "expert_only" else args.max_workers

    with ThreadPoolExecutor(max_workers=max_w) as pool:
        futures = {pool.submit(run_item, item, client, model, args.mode, args.n_refs): item for item in items}
        for fut in tqdm(as_completed(futures), total=len(futures), desc=args.mode):
            r = fut.result()
            results.append(r)
            if len(results) % 20 == 0:
                Path(args.output).parent.mkdir(parents=True, exist_ok=True)
                with open(args.output, "w") as f:
                    json.dump(results, f, indent=2, cls=NumpyEncoder)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2, cls=NumpyEncoder)

    errors = sum(1 for r in results if r.get("error"))
    print(f"\nDone: {len(results)} items, {errors} errors")
    print(f"Results saved: {args.output}")


if __name__ == "__main__":
    main()
