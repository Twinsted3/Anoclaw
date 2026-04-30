#!/usr/bin/env python3
"""
AnomalyClaw: Async Parallel Experiment Runner
==============================================
High-throughput version with async API calls and worker pool.

Usage:
  # Local methods (same as sync)
  python run_experiments_async.py --method patchcore --domains all

  # VLM methods with concurrency
  python run_experiments_async.py --method vlm_direct --backend seedvl --domains all --workers 8
  python run_experiments_async.py --method retrieval_vlm --backend seedvl --workers 4
  python run_experiments_async.py --method expert_vlm --backend seedvl --workers 4
  python run_experiments_async.py --method symmetric_debate --backend seedvl --workers 4
  python run_experiments_async.py --method anomaclaw --backend seedvl --workers 4
"""

import argparse
import asyncio
import base64
import json
import os
import sys
import time
import traceback
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

# Reuse from sync runner
from run_experiments import (
    MANIFEST_PATH, RESULT_DIR, MAX_IMAGE_DIM, SEED, BACKENDS, ALL_DOMAINS,
    resize_if_needed, load_image_rgb, load_manifest, compute_auroc,
    run_clip_zeroshot, run_patchcore, _encode_rgb, _parse_vlm_score,
    _extract_anomaly_score_from_verdict,
)

# ---------------------------------------------------------------------------
# Async VLM client
# ---------------------------------------------------------------------------

_async_client = None
_model_name = ""


def setup_async_client(backend: str):
    global _async_client, _model_name
    from openai import AsyncOpenAI
    cfg = BACKENDS[backend]
    _async_client = AsyncOpenAI(base_url=cfg["base_url"], api_key=cfg["api_key"])
    _model_name = cfg["model"]
    return _model_name


async def vlm_call(messages: List[Dict], temperature: float = 0.0,
                   max_tokens: int = 600) -> str:
    """Single async VLM API call."""
    kwargs = dict(
        model=_model_name,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    # Disable thinking mode for Qwen3.5
    if "Qwen3.5" in _model_name or "qwen3.5" in _model_name.lower():
        kwargs["extra_body"] = {"chat_template_kwargs": {"enable_thinking": False}}
    resp = await _async_client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content or ""


def _build_image_message(b64: str, detail: str = "auto") -> Dict:
    return {
        "role": "user",
        "content": [
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": detail},
            }
        ],
    }


# ---------------------------------------------------------------------------
# Async method implementations
# ---------------------------------------------------------------------------

async def async_vlm_direct(item: Dict) -> float:
    """VLM-Direct: query image only, no references."""
    query_rgb = load_image_rgb(item["query_path"])
    b64 = _encode_rgb(query_rgb)

    messages = [
        {"role": "system", "content": (
            "You are an anomaly detection system. Examine the image and determine "
            "if it contains any anomalies or defects. Output strict JSON only."
        )},
        _build_image_message(b64),
        {"role": "user", "content": (
            "Is this object/scene normal or does it contain anomalies/defects?\n"
            "Output JSON: {\"verdict\": \"normal\" or \"anomaly\", \"confidence\": 0.0-1.0, "
            "\"reasoning\": \"brief explanation\"}"
        )},
    ]

    text = await vlm_call(messages)
    return _parse_vlm_score(text)


async def async_retrieval_vlm(item: Dict) -> float:
    """Retrieval+VLM: DINOv2 retrieval evidence + VLM with reference."""
    from experts import RetrievalExpert
    ret_expert = RetrievalExpert(top_k=4)
    ret_report = ret_expert.analyze(item["query_path"], item["ref_paths"], item["domain_code"])

    query_rgb = load_image_rgb(item["query_path"])
    q_b64 = _encode_rgb(query_rgb)

    ref_b64 = ""
    if item["ref_paths"]:
        ref_rgb = load_image_rgb(item["ref_paths"][0])
        ref_b64 = _encode_rgb(ref_rgb)

    messages = [
        {"role": "system", "content": (
            "You are an anomaly detection system. Compare the query image against "
            "the normal reference and retrieval evidence. Output strict JSON."
        )},
    ]
    if ref_b64:
        messages.append(_build_image_message(ref_b64))
        messages.append({"role": "user", "content": "Normal reference image."})
    messages.append(_build_image_message(q_b64))
    messages.append({"role": "user", "content": (
        f"Query image. Compare with the normal reference.\n"
        f"Retrieval evidence:\n{ret_report}\n\n"
        "Is the query normal or anomalous?\n"
        "Output JSON: {\"verdict\": \"normal\" or \"anomaly\", \"confidence\": 0.0-1.0, "
        "\"reasoning\": \"brief explanation\"}"
    )})

    text = await vlm_call(messages)
    return _parse_vlm_score(text)


async def async_expert_vlm(item: Dict) -> float:
    """Expert-Informed VLM: patch + retrieval evidence + single VLM call."""
    from experts import ExpertPool
    pool = ExpertPool()
    reports = pool.run_selected(
        ["patch", "retrieval"], item["query_path"], item["ref_paths"], item["domain_code"]
    )
    evidence = "\n\n".join(f"[{n.upper()}]\n{r}" for n, r in reports.items())

    query_rgb = load_image_rgb(item["query_path"])
    q_b64 = _encode_rgb(query_rgb)

    ref_b64 = ""
    if item["ref_paths"]:
        ref_rgb = load_image_rgb(item["ref_paths"][0])
        ref_b64 = _encode_rgb(ref_rgb)

    messages = [
        {"role": "system", "content": (
            "You are an anomaly detection system with expert evidence. Compare the query "
            "image against the reference and expert analysis. Output strict JSON."
        )},
    ]
    if ref_b64:
        messages.append(_build_image_message(ref_b64))
        messages.append({"role": "user", "content": "Normal reference image."})
    messages.append(_build_image_message(q_b64))
    messages.append({"role": "user", "content": (
        f"Query image.\nExpert evidence:\n{evidence}\n\n"
        "Use expert scores as grounding but trust your visual judgment.\n"
        "Output JSON: {\"verdict\": \"normal\" or \"anomaly\", \"confidence\": 0.0-1.0, "
        "\"reasoning\": \"brief explanation\"}"
    )})

    text = await vlm_call(messages)
    return _parse_vlm_score(text)


async def async_symmetric_debate(item: Dict) -> float:
    """Symmetric debate: two identical agents, same prompt."""
    query_rgb = load_image_rgb(item["query_path"])
    q_b64 = _encode_rgb(query_rgb)

    ref_b64 = ""
    if item["ref_paths"]:
        ref_rgb = load_image_rgb(item["ref_paths"][0])
        ref_b64 = _encode_rgb(ref_rgb)

    sys_msg = {
        "role": "system", "content": (
            "You are an anomaly detection agent. Be objective. Output strict JSON."
        )
    }

    # Round 1: Agent A proposes
    msgs_a = [sys_msg]
    if ref_b64:
        msgs_a.append(_build_image_message(ref_b64))
        msgs_a.append({"role": "user", "content": "Normal reference."})
    msgs_a.append(_build_image_message(q_b64))
    msgs_a.append({"role": "user", "content": (
        "Query image. List any anomalies.\n"
        "Output JSON: {\"claims\": [{\"id\":\"A1\",\"description\":\"...\",\"confidence\":0.0-1.0}], "
        "\"verdict\": \"normal\" or \"anomaly\"}"
    )})

    text_a = await vlm_call(msgs_a)

    # Round 2: Agent B reviews
    msgs_b = [sys_msg]
    if ref_b64:
        msgs_b.append(_build_image_message(ref_b64))
        msgs_b.append({"role": "user", "content": "Normal reference."})
    msgs_b.append(_build_image_message(q_b64))
    msgs_b.append({"role": "user", "content": (
        f"Another agent said:\n{text_a}\n\n"
        "Do you agree? Challenge or confirm.\n"
        "Output JSON: {\"verdict\": \"normal\" or \"anomaly\", \"confidence\": 0.0-1.0}"
    )})

    text_b = await vlm_call(msgs_b)

    score_a = _parse_vlm_score(text_a)
    score_b = _parse_vlm_score(text_b)
    return (score_a + score_b) / 2.0


async def async_symmetric_debate_expert(item: Dict) -> float:
    """Symmetric debate WITH expert evidence (Table 4, Config 4)."""
    from experts import ExpertPool
    pool = ExpertPool()
    reports = pool.run_selected(
        ["patch", "retrieval"], item["query_path"], item["ref_paths"], item["domain_code"]
    )
    evidence = "\n\n".join(f"[{n.upper()}]\n{r}" for n, r in reports.items())

    query_rgb = load_image_rgb(item["query_path"])
    q_b64 = _encode_rgb(query_rgb)
    ref_b64 = ""
    if item["ref_paths"]:
        ref_rgb = load_image_rgb(item["ref_paths"][0])
        ref_b64 = _encode_rgb(ref_rgb)

    sys_msg = {"role": "system", "content":
        "You are an anomaly detection agent. Be objective. Output strict JSON."}

    # Agent A with expert evidence
    msgs_a = [sys_msg]
    if ref_b64:
        msgs_a.append(_build_image_message(ref_b64))
        msgs_a.append({"role": "user", "content": "Normal reference."})
    msgs_a.append(_build_image_message(q_b64))
    msgs_a.append({"role": "user", "content": (
        f"Query image.\nExpert evidence:\n{evidence}\n\n"
        "List any anomalies.\n"
        "Output JSON: {\"claims\": [{\"id\":\"A1\",\"description\":\"...\",\"confidence\":0.0-1.0}], "
        "\"verdict\": \"normal\" or \"anomaly\"}"
    )})
    text_a = await vlm_call(msgs_a)

    # Agent B reviews with same expert evidence
    msgs_b = [sys_msg]
    if ref_b64:
        msgs_b.append(_build_image_message(ref_b64))
        msgs_b.append({"role": "user", "content": "Normal reference."})
    msgs_b.append(_build_image_message(q_b64))
    msgs_b.append({"role": "user", "content": (
        f"Expert evidence:\n{evidence}\n\n"
        f"Another agent said:\n{text_a}\n\n"
        "Do you agree? Challenge or confirm.\n"
        "Output JSON: {\"verdict\": \"normal\" or \"anomaly\", \"confidence\": 0.0-1.0}"
    )})
    text_b = await vlm_call(msgs_b)

    return (_parse_vlm_score(text_a) + _parse_vlm_score(text_b)) / 2.0


async def async_anomaclaw(item: Dict, depth: int = 2,
                          use_experts: bool = True,
                          expert_list: Optional[List[str]] = None) -> float:
    """AnomalyClaw: full adversarial debate with expert grounding (async)."""
    import re

    # Collect expert evidence
    expert_evidence = ""
    if use_experts:
        from experts import ExpertPool
        from controller import AutonomousController
        pool = ExpertPool()
        ctrl = AutonomousController()
        experts_to_run = expert_list or ctrl.select_experts(item["domain_code"])
        reports = pool.run_selected(
            experts_to_run, item["query_path"], item["ref_paths"], item["domain_code"]
        )
        evidence_parts = [f"[{n.upper()} EXPERT]\n{r}" for n, r in reports.items()]
        expert_evidence = "\n\n".join(evidence_parts)

    # Get debate depth
    if depth is None:
        from controller import AutonomousController
        ctrl = AutonomousController()
        depth = ctrl.get_max_depth(item["domain_code"])

    # Load images
    query_rgb = load_image_rgb(item["query_path"])
    q_b64 = _encode_rgb(query_rgb)
    ref_b64 = ""
    if item["ref_paths"]:
        ref_rgb = load_image_rgb(item["ref_paths"][0])
        ref_b64 = _encode_rgb(ref_rgb)

    # Proposer system prompt
    proposer_sys = (
        "You are the Anomaly Proposer in an adversarial anomaly detection system. "
        "Compare normal reference with query image using expert evidence. "
        "Identify ALL potential anomalies with detailed justification. "
        "Output MUST be strict JSON (no markdown)."
    )

    # Advocate system prompt
    advocate_sys = (
        "You are the Normality Advocate. Challenge every anomaly claim with counter-evidence: "
        "lighting, angle, compression, texture variation, manufacturing tolerance. "
        "Only concede when evidence is overwhelming. Output strict JSON."
    )

    from vad2_prompts import proposer_cold, proposer_iterative, advocate_prompt
    from vad2_system import _extract_json

    final_claims = {}
    final_reviews = {}
    final_decisions = {}
    normal_profile = None
    tbd_ids = None

    for round_idx in range(depth):
        # Proposer
        if round_idx == 0 or not tbd_ids:
            prop_prompt = proposer_cold(expert_reports=expert_evidence)
        else:
            tbd_claims = [final_claims[cid] for cid in tbd_ids if cid in final_claims]
            prop_prompt = proposer_iterative(
                json.dumps({"claims": tbd_claims}, ensure_ascii=False),
                expert_reports=expert_evidence,
            )

        prop_msgs = [{"role": "system", "content": proposer_sys}]
        if ref_b64:
            prop_msgs.append(_build_image_message(ref_b64))
            prop_msgs.append({"role": "user", "content": "Normal reference image."})
        prop_msgs.append(_build_image_message(q_b64))
        prop_msgs.append({"role": "user", "content": prop_prompt})

        prop_text = await vlm_call(prop_msgs, max_tokens=800)

        try:
            prop_json = _extract_json(prop_text)
        except Exception:
            prop_json = {}

        claims = prop_json.get("claims", []) or []
        if isinstance(prop_json.get("normal_profile"), dict):
            normal_profile = prop_json["normal_profile"]

        for c in claims:
            cid = c.get("id")
            if cid:
                final_claims[cid] = c

        # Advocate
        if round_idx == 0:
            focus_claims = list(final_claims.values())
        else:
            focus_claims = [final_claims[cid] for cid in (tbd_ids or []) if cid in final_claims]
            if not focus_claims:
                break

        adv_prompt = advocate_prompt(json.dumps({"claims": focus_claims}, ensure_ascii=False))

        adv_msgs = [{"role": "system", "content": advocate_sys}]
        if ref_b64:
            adv_msgs.append(_build_image_message(ref_b64))
            adv_msgs.append({"role": "user", "content": "Normal reference image."})
        adv_msgs.append(_build_image_message(q_b64))
        adv_msgs.append({"role": "user", "content": adv_prompt})

        adv_text = await vlm_call(adv_msgs, max_tokens=800)

        try:
            adv_json = _extract_json(adv_text)
        except Exception:
            adv_json = {}

        reviews = adv_json.get("reviews", []) or []
        for r in reviews:
            rid = r.get("id")
            if rid:
                final_reviews[rid] = r

        # Aggregate
        review_map = {r.get("id"): r for r in reviews}
        tbd_ids = []
        for c in focus_claims:
            cid = c.get("id")
            if not cid:
                continue
            conf = float(c.get("confidence", 0.0) or 0.0)
            r = review_map.get(cid, {})
            ref_conf = float(r.get("refute_confidence", 0.0) or 0.0)

            if ref_conf >= 0.6:
                final_decisions[cid] = "Invalid"
            elif conf >= 0.6 and ref_conf <= 0.4:
                final_decisions[cid] = "Valid"
            else:
                final_decisions[cid] = "TBD"
                tbd_ids.append(cid)

        if not tbd_ids:
            break

    # Compute continuous anomaly score from claim/review confidences
    # For each claim: effective_score = claim_conf * (1 - refute_conf)
    # Final score = max over all claims (or 0.05 if no claims)
    if not final_claims:
        return 0.05  # No claims at all → very likely normal

    claim_scores = []
    for cid, claim in final_claims.items():
        c_conf = float(claim.get("confidence", 0.5) or 0.5)
        review = final_reviews.get(cid, {})
        r_conf = float(review.get("refute_confidence", 0.3) or 0.3)
        effective = c_conf * (1.0 - r_conf)
        claim_scores.append(effective)

    return max(claim_scores) if claim_scores else 0.05


# ---------------------------------------------------------------------------
# Normal Calibration Cache (singleton)
# ---------------------------------------------------------------------------

_calibration_cache = None


def _get_calibration_cache():
    global _calibration_cache
    if _calibration_cache is None:
        from experts import NormalCalibrationCache
        _calibration_cache = NormalCalibrationCache()
    return _calibration_cache


async def _ensure_calibration(item: Dict, depth: int = 2) -> Dict:
    """Get or compute calibration data for this item's category.

    Returns the cached calibration dict with keys:
      expert_baseline, normal_variation_profile, false_positive_flags, typical_appearance
    """
    from vad2_prompts import calibration_round_prompt
    from vad2_system import _extract_json

    cache = _get_calibration_cache()
    category = item.get("category", "unknown")
    domain_code = item["domain_code"]
    key = cache.get_cache_key(domain_code, category)

    cached = cache.get(key)
    if cached is not None:
        return cached

    ref_paths = item["ref_paths"]

    # Step 1: Compute expert baseline (GPU only, no VLM)
    expert_baseline = cache.compute_expert_baseline(ref_paths, domain_code)

    # Step 2: VLM calibration call — Proposer examines normal refs
    ref_b64s = []
    for p in ref_paths[:3]:
        try:
            ref_rgb = load_image_rgb(p)
            ref_b64s.append(_encode_rgb(ref_rgb))
        except Exception:
            pass

    cal_prompt = calibration_round_prompt()

    cal_msgs = [
        {"role": "system", "content": (
            "You are the Anomaly Proposer. You are examining CONFIRMED NORMAL reference "
            "images to characterize what normal looks like. Output strict JSON only."
        )},
    ]
    for b64 in ref_b64s:
        cal_msgs.append(_build_image_message(b64))
    cal_msgs.append({"role": "user", "content": "These are all confirmed NORMAL reference images."})
    cal_msgs.append({"role": "user", "content": cal_prompt})

    cal_text = await vlm_call(cal_msgs, max_tokens=600)

    # Parse calibration JSON
    try:
        cal_json = _extract_json(cal_text)
    except Exception:
        cal_json = {}

    data = {
        "expert_baseline": expert_baseline,
        "normal_variation_profile": cal_json.get("normal_variation_profile", {}),
        "false_positive_flags": cal_json.get("false_positive_flags", []),
        "typical_appearance": cal_json.get("typical_appearance", ""),
    }
    cache.put(key, data)
    return data


async def async_anomaclaw_normalcal(item: Dict, depth: int = 2,
                                     use_experts: bool = True,
                                     expert_list: Optional[List[str]] = None) -> float:
    """AnomalyClaw with Normal Calibration: calibrated Advocate grounding (async).

    Same debate structure as async_anomaclaw, but the Advocate receives concrete
    evidence about what NORMAL looks like from a per-category calibration round.
    """
    import re

    # --- Calibration round (cached per category) ---
    cal_data = await _ensure_calibration(item)
    cal_cache = _get_calibration_cache()
    calibration_evidence = cal_cache.format_calibration_evidence(cal_data)

    # --- Collect expert evidence (same as baseline anomaclaw) ---
    expert_evidence = ""
    if use_experts:
        from experts import ExpertPool
        from controller import AutonomousController
        pool = ExpertPool()
        ctrl = AutonomousController()
        experts_to_run = expert_list or ctrl.select_experts(item["domain_code"])
        reports = pool.run_selected(
            experts_to_run, item["query_path"], item["ref_paths"], item["domain_code"]
        )
        evidence_parts = [f"[{n.upper()} EXPERT]\n{r}" for n, r in reports.items()]
        expert_evidence = "\n\n".join(evidence_parts)

    # Get debate depth
    if depth is None:
        from controller import AutonomousController
        ctrl = AutonomousController()
        depth = ctrl.get_max_depth(item["domain_code"])

    # Load images
    query_rgb = load_image_rgb(item["query_path"])
    q_b64 = _encode_rgb(query_rgb)
    ref_b64 = ""
    if item["ref_paths"]:
        ref_rgb = load_image_rgb(item["ref_paths"][0])
        ref_b64 = _encode_rgb(ref_rgb)

    # System prompts (same as baseline)
    proposer_sys = (
        "You are the Anomaly Proposer in an adversarial anomaly detection system. "
        "Compare normal reference with query image using expert evidence. "
        "Identify ALL potential anomalies with detailed justification. "
        "Output MUST be strict JSON (no markdown)."
    )
    advocate_sys = (
        "You are the Normality Advocate in an adversarial anomaly detection system. "
        "You have calibration data from confirmed normal images. "
        "Use this evidence to make GROUNDED refutations. "
        "Challenge every claim with specific counter-evidence. "
        "Output MUST be strict JSON (no markdown)."
    )

    from vad2_prompts import proposer_cold, proposer_iterative, advocate_prompt_calibrated
    from vad2_system import _extract_json

    final_claims = {}
    final_reviews = {}
    final_decisions = {}
    tbd_ids = None

    for round_idx in range(depth):
        # --- Proposer (same as baseline) ---
        if round_idx == 0 or not tbd_ids:
            prop_prompt = proposer_cold(expert_reports=expert_evidence)
        else:
            tbd_claims = [final_claims[cid] for cid in tbd_ids if cid in final_claims]
            prop_prompt = proposer_iterative(
                json.dumps({"claims": tbd_claims}, ensure_ascii=False),
                expert_reports=expert_evidence,
            )

        prop_msgs = [{"role": "system", "content": proposer_sys}]
        if ref_b64:
            prop_msgs.append(_build_image_message(ref_b64))
            prop_msgs.append({"role": "user", "content": "Normal reference image."})
        prop_msgs.append(_build_image_message(q_b64))
        prop_msgs.append({"role": "user", "content": prop_prompt})

        prop_text = await vlm_call(prop_msgs, max_tokens=800)

        try:
            prop_json = _extract_json(prop_text)
        except Exception:
            prop_json = {}

        claims = prop_json.get("claims", []) or []
        for c in claims:
            cid = c.get("id")
            if cid:
                final_claims[cid] = c

        # --- Advocate (CHANGED: uses calibrated prompt) ---
        if round_idx == 0:
            focus_claims = list(final_claims.values())
        else:
            focus_claims = [final_claims[cid] for cid in (tbd_ids or []) if cid in final_claims]
            if not focus_claims:
                break

        adv_prompt = advocate_prompt_calibrated(
            json.dumps({"claims": focus_claims}, ensure_ascii=False),
            calibration_evidence,
        )

        adv_msgs = [{"role": "system", "content": advocate_sys}]
        if ref_b64:
            adv_msgs.append(_build_image_message(ref_b64))
            adv_msgs.append({"role": "user", "content": "Normal reference image."})
        adv_msgs.append(_build_image_message(q_b64))
        adv_msgs.append({"role": "user", "content": adv_prompt})

        adv_text = await vlm_call(adv_msgs, max_tokens=800)

        try:
            adv_json = _extract_json(adv_text)
        except Exception:
            adv_json = {}

        reviews = adv_json.get("reviews", []) or []
        for r in reviews:
            rid = r.get("id")
            if rid:
                final_reviews[rid] = r

        # --- Aggregate (same as baseline) ---
        review_map = {r.get("id"): r for r in reviews}
        tbd_ids = []
        for c in focus_claims:
            cid = c.get("id")
            if not cid:
                continue
            conf = float(c.get("confidence", 0.0) or 0.0)
            r = review_map.get(cid, {})
            ref_conf = float(r.get("refute_confidence", 0.0) or 0.0)

            if ref_conf >= 0.6:
                final_decisions[cid] = "Invalid"
            elif conf >= 0.6 and ref_conf <= 0.4:
                final_decisions[cid] = "Valid"
            else:
                final_decisions[cid] = "TBD"
                tbd_ids.append(cid)

        if not tbd_ids:
            break

    # --- Score computation (same as baseline) ---
    if not final_claims:
        return 0.05

    claim_scores = []
    for cid, claim in final_claims.items():
        c_conf = float(claim.get("confidence", 0.5) or 0.5)
        review = final_reviews.get(cid, {})
        r_conf = float(review.get("refute_confidence", 0.3) or 0.3)
        effective = c_conf * (1.0 - r_conf)
        claim_scores.append(effective)

    return max(claim_scores) if claim_scores else 0.05


async def async_anomaclaw_judge(item: Dict, depth: int = 1,
                                 use_experts: bool = True,
                                 expert_list: Optional[List[str]] = None) -> float:
    """AnomalyClaw with Judge: depth-1 debate + holistic Judge synthesis (async).

    Instead of rule-based claim aggregation, a Judge VLM call synthesizes all
    evidence (claims, reviews, expert scores, calibration) into a single score.
    """
    import re

    # --- Calibration ---
    cal_data = await _ensure_calibration(item)
    cal_cache = _get_calibration_cache()
    calibration_evidence = cal_cache.format_calibration_evidence(cal_data)

    # --- Expert evidence ---
    expert_evidence = ""
    if use_experts:
        from experts import ExpertPool
        from controller import AutonomousController
        pool = ExpertPool()
        ctrl = AutonomousController()
        experts_to_run = expert_list or ctrl.select_experts(item["domain_code"])
        reports = pool.run_selected(
            experts_to_run, item["query_path"], item["ref_paths"], item["domain_code"]
        )
        evidence_parts = [f"[{n.upper()} EXPERT]\n{r}" for n, r in reports.items()]
        expert_evidence = "\n\n".join(evidence_parts)

    # Load images
    query_rgb = load_image_rgb(item["query_path"])
    q_b64 = _encode_rgb(query_rgb)
    ref_b64 = ""
    if item["ref_paths"]:
        ref_rgb = load_image_rgb(item["ref_paths"][0])
        ref_b64 = _encode_rgb(ref_rgb)

    # --- Proposer (single round) ---
    from vad2_prompts import proposer_cold, advocate_prompt_calibrated, judge_synthesis_prompt
    from vad2_system import _extract_json

    proposer_sys = (
        "You are the Anomaly Proposer in an adversarial anomaly detection system. "
        "Compare normal reference with query image using expert evidence. "
        "Identify ALL potential anomalies with detailed justification. "
        "Output MUST be strict JSON (no markdown)."
    )

    prop_prompt = proposer_cold(expert_reports=expert_evidence)
    prop_msgs = [{"role": "system", "content": proposer_sys}]
    if ref_b64:
        prop_msgs.append(_build_image_message(ref_b64))
        prop_msgs.append({"role": "user", "content": "Normal reference image."})
    prop_msgs.append(_build_image_message(q_b64))
    prop_msgs.append({"role": "user", "content": prop_prompt})

    prop_text = await vlm_call(prop_msgs, max_tokens=800)

    try:
        prop_json = _extract_json(prop_text)
    except Exception:
        prop_json = {}

    claims = prop_json.get("claims", []) or []

    if not claims:
        return 0.05  # No claims → likely normal

    # --- Advocate (calibrated, single round) ---
    advocate_sys = (
        "You are the Normality Advocate with calibration data from normal images. "
        "Challenge every anomaly claim with grounded counter-evidence. "
        "Output MUST be strict JSON (no markdown)."
    )

    adv_prompt = advocate_prompt_calibrated(
        json.dumps({"claims": claims}, ensure_ascii=False),
        calibration_evidence,
    )

    adv_msgs = [{"role": "system", "content": advocate_sys}]
    if ref_b64:
        adv_msgs.append(_build_image_message(ref_b64))
        adv_msgs.append({"role": "user", "content": "Normal reference image."})
    adv_msgs.append(_build_image_message(q_b64))
    adv_msgs.append({"role": "user", "content": adv_prompt})

    adv_text = await vlm_call(adv_msgs, max_tokens=800)

    try:
        adv_json = _extract_json(adv_text)
    except Exception:
        adv_json = {}

    reviews = adv_json.get("reviews", []) or []

    # --- Judge (NEW: holistic synthesis) ---
    judge_sys = (
        "You are the Final Judge in an anomaly detection system. "
        "Synthesize all evidence into a single holistic judgment. "
        "Output MUST be strict JSON (no markdown)."
    )

    judge_prompt = judge_synthesis_prompt(
        claims_json=json.dumps({"claims": claims}, ensure_ascii=False),
        reviews_json=json.dumps({"reviews": reviews}, ensure_ascii=False),
        expert_evidence=expert_evidence,
        calibration_evidence=calibration_evidence,
    )

    judge_msgs = [{"role": "system", "content": judge_sys}]
    if ref_b64:
        judge_msgs.append(_build_image_message(ref_b64))
        judge_msgs.append({"role": "user", "content": "Normal reference image."})
    judge_msgs.append(_build_image_message(q_b64))
    judge_msgs.append({"role": "user", "content": judge_prompt})

    judge_text = await vlm_call(judge_msgs, max_tokens=400)

    return _parse_vlm_score(judge_text)


# ---------------------------------------------------------------------------
# Async dispatcher
# ---------------------------------------------------------------------------

ASYNC_METHODS = {
    "vlm_direct": async_vlm_direct,
    "retrieval_vlm": async_retrieval_vlm,
    "expert_vlm": async_expert_vlm,
    "symmetric_debate": async_symmetric_debate,
    "symmetric_debate_expert": async_symmetric_debate_expert,
    "anomaclaw": async_anomaclaw,
    "anomaclaw_normalcal": async_anomaclaw_normalcal,
    "anomaclaw_judge": async_anomaclaw_judge,
}

LOCAL_METHODS = {
    "clip_zeroshot": run_clip_zeroshot,
    "patchcore": run_patchcore,
}


async def run_item_async(method: str, item: Dict, semaphore: asyncio.Semaphore,
                         **kwargs) -> Tuple[str, float]:
    """Run a single item with concurrency control."""
    async with semaphore:
        if method in ASYNC_METHODS:
            fn = ASYNC_METHODS[method]
            if method in ("anomaclaw", "anomaclaw_normalcal", "anomaclaw_judge"):
                score = await fn(item, **kwargs)
            else:
                score = await fn(item)
        else:
            # Run local methods in thread pool
            import functools
            loop = asyncio.get_event_loop()
            fn = LOCAL_METHODS[method]
            score = await loop.run_in_executor(None, functools.partial(fn, item))
        return item["item_id"], score


async def run_experiment_async(
    method: str,
    domains: List[str],
    backend: str = "",
    max_per_domain: Optional[int] = None,
    output_dir: str = RESULT_DIR,
    workers: int = 8,
    resume: bool = True,
    **method_kwargs,
) -> Dict[str, Any]:
    """Run experiment with async parallelism."""

    # Setup
    model = ""
    if method in ASYNC_METHODS:
        if not backend:
            raise ValueError(f"Method {method} requires --backend")
        model = setup_async_client(backend)

    items = load_manifest(MANIFEST_PATH, domains, split="test", max_per_domain=max_per_domain)
    print(f"\n{'='*60}")
    print(f"Experiment: {method} | Backend: {backend or 'local'} | Workers: {workers}")
    print(f"Items: {len(items)} | Domains: {', '.join(domains)}")
    print(f"{'='*60}\n")

    # Output paths
    tag = f"{method}_{backend}" if backend else method
    for k, v in method_kwargs.items():
        if v is not None:
            tag += f"_{k}={v}"
    os.makedirs(output_dir, exist_ok=True)
    results_path = os.path.join(output_dir, f"{tag}_results.json")
    detail_path = os.path.join(output_dir, f"{tag}_detail.jsonl")

    # Resume
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

    # Filter out completed items
    pending_items = [i for i in items if i["item_id"] not in completed]
    print(f"  Pending: {len(pending_items)} items")

    # Prepare results from completed
    all_results = {}  # item_id -> (score, label, domain_code)
    for item_id, entry in completed.items():
        all_results[item_id] = (entry["score"], entry["label"], entry["domain_code"])

    # Run with semaphore
    semaphore = asyncio.Semaphore(workers)
    start_time = time.time()
    detail_f = open(detail_path, "a")
    errors = 0
    done_count = len(completed)

    # Process in batches for progress reporting
    batch_size = workers * 2
    for batch_start in range(0, len(pending_items), batch_size):
        batch = pending_items[batch_start:batch_start + batch_size]

        tasks = []
        for item in batch:
            tasks.append(run_item_async(method, item, semaphore, **method_kwargs))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for item, result in zip(batch, results):
            if isinstance(result, Exception):
                errors += 1
                if errors <= 5:
                    print(f"  [{item['item_id']}] ERROR: {result}")
                continue

            item_id, score = result
            label = item["label"]
            dc = item["domain_code"]

            entry = {
                "item_id": item_id,
                "domain_code": dc,
                "category": item.get("category", ""),
                "label": label,
                "score": score,
            }
            detail_f.write(json.dumps(entry) + "\n")
            detail_f.flush()

            all_results[item_id] = (score, label, dc)
            done_count += 1

        # Progress
        elapsed = time.time() - start_time
        total_done = done_count
        rate = (total_done - len(completed)) / elapsed if elapsed > 0 else 0

        all_scores = [v[0] for v in all_results.values()]
        all_labels = [v[1] for v in all_results.values()]
        current_auroc = compute_auroc(all_labels, all_scores)

        print(f"  [{total_done}/{len(items)}] AUROC={current_auroc:.4f} | "
              f"{rate:.2f} items/s | errors={errors}")

    detail_f.close()
    elapsed = time.time() - start_time

    # Compute per-domain AUROC
    domain_scores = defaultdict(list)
    domain_labels = defaultdict(list)
    for score, label, dc in all_results.values():
        domain_scores[dc].append(score)
        domain_labels[dc].append(label)

    domain_aurocs = {}
    for dc in sorted(domain_scores.keys()):
        domain_aurocs[dc] = compute_auroc(domain_labels[dc], domain_scores[dc])

    macro_auroc = float(np.nanmean(list(domain_aurocs.values())))
    all_s = [v[0] for v in all_results.values()]
    all_l = [v[1] for v in all_results.values()]
    micro_auroc = compute_auroc(all_l, all_s)

    results_out = {
        "method": method,
        "backend": backend,
        "model": model,
        "tag": tag,
        "domains": domains,
        "total_items": len(items),
        "completed": len(all_results),
        "errors": errors,
        "elapsed_seconds": round(elapsed, 1),
        "workers": workers,
        "macro_auroc": round(macro_auroc, 4),
        "micro_auroc": round(micro_auroc, 4),
        "domain_aurocs": {k: round(v, 4) for k, v in domain_aurocs.items()},
        "method_kwargs": {k: v for k, v in method_kwargs.items() if v is not None},
    }

    with open(results_path, "w") as f:
        json.dump(results_out, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"Results: {method} ({backend or 'local'})")
    print(f"  Macro AUROC: {macro_auroc:.4f}")
    print(f"  Micro AUROC: {micro_auroc:.4f}")
    print(f"  Per-domain:")
    for dc in sorted(domain_aurocs.keys()):
        print(f"    {dc}: {domain_aurocs[dc]:.4f}")
    print(f"  Time: {elapsed:.0f}s | Errors: {errors} | Rate: {(len(all_results)-len(completed))/max(elapsed,1):.2f}/s")
    print(f"  Saved: {results_path}")
    print(f"{'='*60}\n")

    return results_out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="AnomalyClaw Async Experiment Runner")
    parser.add_argument("--method", type=str, required=True,
                        choices=["clip_zeroshot", "patchcore", "vlm_direct",
                                 "retrieval_vlm", "expert_vlm", "symmetric_debate",
                                 "symmetric_debate_expert", "anomaclaw",
                                 "anomaclaw_normalcal", "anomaclaw_judge"])
    parser.add_argument("--backend", type=str, default="",
                        choices=["", "seedvl", "seedvl_pro", "gpt4o", "gpt54", "qwen25vl", "qwen35"])
    parser.add_argument("--domains", type=str, default="all")
    parser.add_argument("--max_per_domain", type=int, default=None)
    parser.add_argument("--output_dir", type=str, default=RESULT_DIR)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--no_resume", action="store_true")

    # AnomalyClaw params
    parser.add_argument("--depth", type=int, default=None)
    parser.add_argument("--use_experts", type=str, default=None)
    parser.add_argument("--expert_list", type=str, default=None)

    args = parser.parse_args()

    domains = ALL_DOMAINS if args.domains == "all" else args.domains.split(",")

    kwargs = {}
    if args.depth is not None:
        kwargs["depth"] = args.depth
    if args.use_experts is not None:
        kwargs["use_experts"] = args.use_experts.lower() == "true"
    if args.expert_list:
        kwargs["expert_list"] = args.expert_list.split(",")

    asyncio.run(run_experiment_async(
        method=args.method,
        domains=domains,
        backend=args.backend,
        max_per_domain=args.max_per_domain,
        output_dir=args.output_dir,
        workers=args.workers,
        resume=not args.no_resume,
        **kwargs,
    ))


if __name__ == "__main__":
    main()
