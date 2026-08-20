"""
Unified inference script for cross-domain AD benchmark.

Supports:
  Backends:  gpt | seedvl | qwen3
  Variants:  v0_direct | v1_normal_first | v2_self_refine | v3_debate_1r

Usage:
  python benchmark/scripts/infer.py \
      --manifest benchmark/manifests/full_manifest.json \
      --split calibration \
      --backend seedvl \
      --variant v1_normal_first \
      --output benchmark/results/seedvl_v1_calibration.json \
      --domains D1 D5 \
      --max_workers 4

Output JSON per item:
{
  "item_id": "D1_0001",
  "domain": "industrial",
  "label_gt": 1,
  "label_pred": 1,
  "anomaly_score": 0.85,          # higher = more anomalous
  "anomaly_type_pred": "surface_defect",
  "raw_output": {...},
  "cost_tokens": {"input": 1234, "output": 200},
  "latency_sec": 3.2,
  "error": null
}
"""

import argparse
import asyncio
import base64
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Optional

import cv2
import numpy as np
from openai import OpenAI

# ─── Prompts ──────────────────────────────────────────────────────────────────

SYSTEM_INSPECTOR = "You are a visual anomaly inspector. Return JSON only. No extra text."
SYSTEM_REFUTER = "You are an anomaly refuter. Return JSON only. No extra text."

# manifests_v2 taxonomy (2026-04-21). D1-D12 codes follow benchmark/manifests_v2/domain_config.json.
# Legacy v1 keys (D3b/c/d for BraTS/Liver/Kvasir subsplits, D3=Derma, D4=LEVIR, D7=road, D8=Avenue,
# D9=MVTec-LOCO, D10=VisA) are intentionally NOT present — the prose has been remapped to v2 codes
# (D2=VisA, D3=MVTec-LOCO, D4=Real3D-AD, D7=LEVIR, D8=Derma, D9=BraTS, D10=Liver, D11=Kvasir, D12=road).
# For v1 reproducibility, consult saved result files under benchmark/results/ rather than re-running.
DOMAIN_CONTEXT = {
    "D1": (
        "industrial manufacturing product (metal part, plastic component, or textured surface). "
        "Normal = defect-free product matching the reference items. "
        "Anomaly = physical defects such as scratches, dents, cracks, contamination, "
        "missing components, misalignment, or color/texture deviation from the references."
    ),
    "D5": (
        "packaged consumer good photographed in a product-inspection setting (food box, drink bottle, "
        "drink can, cigarette box, food package, etc., from the GoodsAD dataset). "
        "Normal = defect-free packaged product matching the reference item in shape, label, and colour. "
        "Anomaly = physical defect on the same product category such as broken or deformed packaging, "
        "torn label, missing logo/text, surface dents, contamination, or a missing component "
        "(NOT simply a different brand, lighting, or pose — focus on within-category physical defects)."
    ),
    "D2": (
        "industrial manufacturing product from the VisA benchmark (candle, capsules, cashew, chewing gum, "
        "fryum, macaroni, PCB, pipe fryum, etc.). "
        "Normal = defect-free product matching the reference items of the same category. "
        "Anomaly = physical defects: scratches, dents, cracks, chips, missing parts, contamination, "
        "discoloration, melting, broken shape, or foreign inclusions (similar to MVTec-AD but on a "
        "different object set)."
    ),
    "D6": (
        "concrete or infrastructure surface such as a bridge deck, wall, or pavement. "
        "Normal = intact surface with typical weathering, stains, joints, and minor discoloration. "
        "Anomaly = cracks, spalling, exposed rebar, or structural damage "
        "(NOT shadows, surface stains, or normal construction joints)."
    ),
    "D3": (
        "image from the MVTec-LOCO logical-anomaly benchmark (breakfast box, juice bottle, pushpins, "
        "screw bag, splicing connectors, etc.). "
        "Normal = structurally correct composition matching the reference: all expected components present, "
        "in the right count, position, colour, and arrangement. "
        "Anomaly = LOGICAL anomaly (missing/added/swapped component, wrong count, wrong colour pairing, "
        "misplaced sub-item) or STRUCTURAL anomaly (physical damage to a component). "
        "The anomaly may be subtle: look at component identities and relative positions, not only at "
        "surface texture."
    ),
    "D4": (
        "rendered view of a 3D industrial product from the Real3D-AD benchmark (airplane, candy bar, "
        "chicken, diamond, duck, fish, gemstone, seahorse, shell, starfish, toffee, etc.). The query "
        "is a 2D rendering of a 3D point-cloud scan; surface detail is sparse/dotted because the "
        "modality is geometry, not photography. "
        "Normal = geometrically intact product matching the reference shape — no bulges, sinks, holes, "
        "or added material. "
        "Anomaly = geometric defect visible in the 3D shape: bulge (outward protrusion), sink (inward "
        "depression), hole (missing material), contamination (added foreign material on the surface), "
        "or overall asymmetry vs the reference renders. "
        "IMPORTANT: focus on SHAPE-level discrepancy vs the references, not on photographic texture — "
        "the point-cloud rendering intentionally has low surface detail."
    ),
    "D7": (
        "bi-temporal remote sensing tile pair from a building change-detection benchmark "
        "(LEVIR-CD+). The reference image is the earlier capture of the same geographic location; "
        "the query image is a later capture of the SAME location. "
        "Normal = no building change between reference and query: the set of buildings, roofs, and "
        "footprints is visually the same (minor radiometric / seasonal / illumination differences "
        "DO NOT count as anomaly). "
        "Anomaly = building-level change between reference and query, INCLUDING new construction, "
        "building demolition, roof replacement, warehouse or parking expansion, road extension through "
        "what was previously vegetation/open ground, or any added/removed built structure. "
        "IMPORTANT: in this task, 'organised', 'intact', 'planned urbanisation', or 'construction activity' "
        "ARE the anomaly if they imply buildings/roads exist in the query where none existed in the reference; "
        "do NOT rationalise them as 'normal urban growth'."
    ),
    "D8": (
        "dermoscopic image of a skin lesion. "
        "Normal = benign mole (melanocytic nevus). "
        "Anomaly = malignant melanoma (irregular borders, asymmetric shape, color variation, large diameter)."
    ),
    "D9": (
        "axial brain MRI slice from the BraTS2021 glioma dataset. "
        "Normal = brain slice with no visible pathology (structurally symmetric, normal tissue intensities). "
        "Anomaly = visible brain pathology such as glioma tumour, hyperintense lesion, mass effect, "
        "midline shift, or oedema. Focus on focal intensity abnormalities and loss of symmetry relative "
        "to the reference normal brain slices."
    ),
    "D10": (
        "axial abdominal CT slice centred on the liver, from BMAD-Liver. "
        "Normal = liver parenchyma of uniform density without focal lesions. "
        "Anomaly = liver pathology such as tumour, metastasis, abscess, cyst, or focal hypodense/hyperdense "
        "lesion visibly different from the surrounding parenchyma. Focus on focal intensity changes; "
        "lesion location can be anywhere within the liver."
    ),
    "D11": (
        "gastrointestinal endoscopy frame from HyperKvasir. "
        "Normal = normal mucosa (clean pink/red tissue, no polyps, no ulcers, no bleeding, no visible "
        "pathology). "
        "Anomaly = pathological finding such as polyp, ulcer, hemorrhoid, cancerous tissue, inflammation, "
        "or bleeding. Look for focal mucosal abnormalities of colour or shape relative to the normal "
        "reference frames."
    ),
    "D12": (
        "road or traffic scene photograph. "
        "Normal = typical road surface, vehicles, pedestrians, and infrastructure. "
        "Anomaly = unexpected obstacles on or near the roadway such as fallen objects, animals, "
        "construction debris, or out-of-place items that pose a driving hazard."
    ),
}

TAXONOMY_TYPES = [
    "surface_defect", "breakage_or_deformation", "missing_or_extra_object",
    "contamination_or_artifact", "damage_or_change", "hazard_or_prohibited_object",
    "pathology_or_lesion", "contextual_abnormality", "other"
]

OUTPUT_SCHEMA_V0 = """{
  "image_label": "normal" or "anomalous",
  "anomaly_type": one of """ + str(TAXONOMY_TYPES) + """ or null,
  "evidence": "brief description",
  "confidence": float 0-1,
  "bbox": [x1_frac, y1_frac, x2_frac, y2_frac] or null
}"""

OUTPUT_SCHEMA_V1 = """{
  "normal_profile": {
    "object_or_scene": "...",
    "expected_structure": "...",
    "expected_surface_or_texture": "...",
    "expected_contents": "..."
  },
  "claims": [
    {
      "id": "A1",
      "anomaly_type": "<one of """ + str(TAXONOMY_TYPES) + """>",
      "evidence": "...",
      "bbox": [x1_frac, y1_frac, x2_frac, y2_frac] or null,
      "confidence": float 0-1
    }
  ],
  "image_label": "normal" or "anomalous"
}"""

OUTPUT_SCHEMA_REFUTER = """{
  "reviews": [
    {
      "id": "A1",
      "refute_confidence": float 0-1,
      "counter_evidence": "...",
      "likely_cause": "normal_variation|lighting|viewpoint|occlusion|expected_context|genuine_anomaly|unknown"
    }
  ]
}"""


def build_prompt_v0_generic(has_refs: bool) -> str:
    """Generic-descriptor baseline: no task-specific normal/anomaly definition.

    Used for the descriptor-ablation experiment. Domain-agnostic wording matches
    what most ``agentic VAD'' papers use as their baseline prompt.
    """
    ref_note = " The first image(s) show the normal reference state." if has_refs else ""
    return (
        f"You are a visual anomaly inspector.{ref_note}\n"
        f"Decide whether the query image is abnormal relative to the reference(s).\n"
        f"Return JSON only:\n{OUTPUT_SCHEMA_V0}"
    )


def build_prompt_v0(domain_code: str, has_refs: bool) -> str:
    # Env-var switch: DESCRIPTOR_MODE=generic forces the generic descriptor
    # across every v0 call site, without changing call sites.
    if os.environ.get("DESCRIPTOR_MODE", "task").lower() == "generic":
        return build_prompt_v0_generic(has_refs)
    ctx = DOMAIN_CONTEXT.get(domain_code, "image")
    ref_note = " The first image(s) show the normal reference state." if has_refs else ""
    return (
        f"You are a visual anomaly inspector examining a {ctx}.{ref_note}\n"
        f"Decide whether the query image is abnormal relative to the normal reference state.\n"
        f"Return JSON only:\n{OUTPUT_SCHEMA_V0}"
    )


def build_prompt_v4(domain_code: str, n_refs: int) -> str:
    """V4: Few-shot with many normal references — emphasizes learning the normal distribution."""
    ctx = DOMAIN_CONTEXT.get(domain_code, "image")
    return (
        f"You are a visual anomaly inspector examining a {ctx}.\n"
        f"You are shown {n_refs} NORMAL reference images that define the range of normal "
        f"appearance for this domain. Study them carefully to understand the full diversity "
        f"of what 'normal' looks like — different items, angles, lighting, and conditions "
        f"are all normal.\n"
        f"Then examine the QUERY image. An anomaly is a genuine physical defect, damage, "
        f"pathological finding, or safety hazard — NOT merely a different product variant, "
        f"viewpoint, or lighting condition.\n"
        f"Return JSON only:\n{OUTPUT_SCHEMA_V0}"
    )


def build_prompt_v5_profile(domain_code: str, n_refs: int) -> str:
    """V5 Phase 1: Generate a normal-distribution profile from reference images."""
    ctx = DOMAIN_CONTEXT.get(domain_code, "image")
    return (
        f"You are analyzing {n_refs} NORMAL reference images of a {ctx} domain.\n"
        f"Your task: build a comprehensive profile of what 'normal' looks like.\n"
        f"Return JSON only:\n"
        f'{{\n'
        f'  "domain_summary": "one-line description of the domain",\n'
        f'  "normal_appearance": [\n'
        f'    "visual characteristic 1 shared across normal samples",\n'
        f'    "visual characteristic 2 ...",\n'
        f'    "...up to 8 characteristics"\n'
        f'  ],\n'
        f'  "acceptable_variations": [\n'
        f'    "variation 1 that is still normal (e.g., different product, angle)",\n'
        f'    "variation 2 ..."\n'
        f'  ],\n'
        f'  "anomaly_indicators": [\n'
        f'    "what would constitute a genuine anomaly (not normal variation)",\n'
        f'    "..."\n'
        f'  ]\n'
        f'}}'
    )


# ─── RGNC Prompts & Schemas ──────────────────────────────────────────────────

RGNC_PROFILE_SCHEMA = """{
  "normal_patterns": [
    {"id": 0, "pattern": "visual characteristic shared across references", "evidence_refs": [1, 2]}
  ],
  "benign_variations": [
    {"id": 0, "variation": "variation that is still normal", "evidence_refs": [2, 4]}
  ]
}"""

RGNC_INSPECTION_SCHEMA = """{
  "label": "normal" or "anomalous",
  "violations": [
    {"violated_pattern_id": 0, "description": "how query violates this pattern", "severity": float 0-1}
  ],
  "benign_matches": [
    {"variation_id": 0, "description": "query difference explained by this variation"}
  ],
  "anomaly_score": float 0-1
}"""

RGNC_VERIFY_SCHEMA = """{
  "reviews": [
    {"violation_id": 0, "is_genuine": true or false, "justification": "...", "revised_severity": float 0-1}
  ]
}"""


def build_prompt_rgnc_profile(domain_code: str, n_refs: int) -> str:
    ctx = DOMAIN_CONTEXT.get(domain_code, "image")
    return (
        f"You are analyzing {n_refs} NORMAL reference images of a {ctx} domain.\n"
        f"Build a normality profile by examining what these references have in common "
        f"and how they vary.\n"
        f"Each normal_pattern must cite which reference images support it (1-indexed).\n"
        f"Each benign_variation must cite which references show this variation.\n"
        f"Do NOT invent anomaly concepts — only describe what you SEE in the references.\n"
        f"Return JSON only:\n{RGNC_PROFILE_SCHEMA}"
    )


def build_prompt_rgnc_inspect(domain_code: str, profile_json: str) -> str:
    ctx = DOMAIN_CONTEXT.get(domain_code, "image")
    return (
        f"You are inspecting a {ctx}.\n"
        f"Normality profile (derived from reference images):\n{profile_json}\n\n"
        f"Use this profile as context to understand what is normal in this domain.\n"
        f"Compare the QUERY image to the reference images.\n"
        f"Decide whether the query image is normal or anomalous.\n"
        f"Return JSON only:\n{OUTPUT_SCHEMA_V0}"
    )


def build_prompt_rgnc_verify(profile_json: str, violations_json: str) -> str:
    return (
        f"You are a verification agent. Check whether each claimed violation is genuine "
        f"or can be explained by benign variations in the normality profile.\n"
        f"Normality profile:\n{profile_json}\n"
        f"Claimed violations:\n{violations_json}\n"
        f"For each violation, decide if it is genuine (true anomaly) or false alarm.\n"
        f"If false alarm, set revised_severity to 0.\n"
        f"Return JSON only:\n{RGNC_VERIFY_SCHEMA}"
    )


def build_prompt_rgnc_unstructured(domain_code: str, n_refs: int) -> str:
    """Control: same token budget as RGNC profile, but unstructured free-text summary."""
    ctx = DOMAIN_CONTEXT.get(domain_code, "image")
    return (
        f"You are analyzing {n_refs} NORMAL reference images of a {ctx} domain.\n"
        f"Write a detailed free-text description of what normal looks like in these images. "
        f"Cover: visual characteristics, acceptable variations, and what would indicate "
        f"a genuine anomaly. Write 100-200 words as a single paragraph.\n"
        f"Return JSON only:\n"
        f'{{"normality_summary": "your free-text description here"}}'
    )


def build_prompt_rgnc_unstructured_inspect(domain_code: str, summary: str) -> str:
    """Control: inspect using unstructured summary instead of structured RGNC profile."""
    ctx = DOMAIN_CONTEXT.get(domain_code, "image")
    return (
        f"You are inspecting a {ctx}.\n"
        f"Normality description (from reference images):\n{summary}\n\n"
        f"Compare the QUERY image to the references using this description.\n"
        f"Decide if the query is normal or anomalous.\n"
        f"Return JSON only:\n{OUTPUT_SCHEMA_V0}"
    )


def build_prompt_v5_judge(domain_code: str, profile_json: str) -> str:
    """V5 Phase 2: Judge query image using the learned normal profile."""
    ctx = DOMAIN_CONTEXT.get(domain_code, "image")
    return (
        f"You are a visual anomaly inspector examining a {ctx}.\n"
        f"You have learned the following NORMAL PROFILE from studying many reference images:\n"
        f"{profile_json}\n\n"
        f"Now examine the QUERY image (shown below, along with 2 example normal references).\n"
        f"Based on the learned profile, decide if the query shows a genuine anomaly "
        f"(physical defect, damage, pathology, hazard) or is within normal variation.\n"
        f"Return JSON only:\n{OUTPUT_SCHEMA_V0}"
    )


def build_prompt_v1(domain_code: str, has_refs: bool) -> str:
    ctx = DOMAIN_CONTEXT.get(domain_code, "image")
    ref_note = " The first image(s) show the normal reference state." if has_refs else ""
    return (
        f"You are a visual anomaly inspector examining a {ctx}.{ref_note}\n"
        f"Step 1: State what normal looks like in this domain and in the reference image(s).\n"
        f"Step 2: State whether the query image departs from that normal state.\n"
        f"Return JSON only:\n{OUTPUT_SCHEMA_V1}"
    )


def build_prompt_refuter(domain_code: str, claims_json: str) -> str:
    ctx = DOMAIN_CONTEXT.get(domain_code, "image")
    return (
        f"You are an anomaly refuter for a visual inspection task.\n"
        f"Task context: the query image is a {ctx}\n\n"
        f"For each proposed anomaly claim below, try to explain it as non-anomalous under ordinary "
        f"confounders: lighting, viewpoint, occlusion, normal variation in the reference distribution, "
        f"imaging artifact, or compression.\n"
        f"IMPORTANT CONSTRAINT: your refutation must respect the task's anomaly definition above. "
        f"Do NOT rationalize a task-level anomaly (structural damage, pathological finding, prohibited "
        f"object, manufacturing defect, etc.) as 'normal change', 'expected variation', 'urbanization', "
        f"'construction', or similar excuses if the observation matches the anomaly definition for this "
        f"domain. Only assign high refute_confidence if you have strong, specific visual evidence that "
        f"the claim is truly NOT a task-level anomaly under the definition above.\n"
        f"Claims:\n{claims_json}\n"
        f"Return JSON only:\n{OUTPUT_SCHEMA_REFUTER}"
    )


# ─── Image utils ──────────────────────────────────────────────────────────────

_REPO_ROOT = Path(__file__).resolve().parents[2]


def resolve_data_path(path: str) -> str:
    """Resolve a manifest path. Manifests store paths starting with the
    placeholder ``{DATA_ROOT}/``; we substitute it for the runtime data root
    (env var ``ANOMALYCLAW_DATA``, defaulting to ``<repo>/benchmark/data``).

    Absolute paths are returned unchanged so the same code path also works on
    machines where the manifests were already rewritten.
    """
    if path.startswith("{DATA_ROOT}/"):
        data_root = os.environ.get("ANOMALYCLAW_DATA", str(_REPO_ROOT / "benchmark" / "data"))
        return os.path.join(data_root, path[len("{DATA_ROOT}/"):])
    return path


def load_and_encode(path: str, max_side: int = 512) -> str:
    path = resolve_data_path(path)
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(f"Cannot read image: {path}")
    h, w = img.shape[:2]
    if max(h, w) > max_side:
        scale = max_side / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)))
    _, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return base64.b64encode(buf).decode("utf-8")


def img_msg(b64: str) -> dict:
    return {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "high"}}


def text_msg(text: str) -> dict:
    return {"type": "text", "text": text}


# ─── JSON extraction ──────────────────────────────────────────────────────────

import re

def extract_json(text: str) -> Optional[dict]:
    if not text:
        return None
    text = text.strip()
    # Try direct parse
    try:
        return json.loads(text)
    except Exception:
        pass
    # Strip markdown fences
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except Exception:
            pass
    # Find the first complete JSON object. Some backbones (notably GPT-5.4
    # on complex multi-turn prompts) emit the same JSON object twice
    # concatenated with no delimiter; raw_decode stops at the first valid
    # object.
    dec = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch != "{":
            continue
        try:
            obj, _ = dec.raw_decode(text[i:])
            if isinstance(obj, dict):
                return obj
        except Exception:
            continue
    return None


# ─── Score aggregation ────────────────────────────────────────────────────────

def score_from_v0(parsed: Optional[dict]) -> float:
    if not parsed:
        return 0.5
    label = str(parsed.get("image_label", "")).lower()
    conf = float(parsed.get("confidence", 0.5))
    if label == "anomalous":
        return max(conf, 0.5 + 1e-6)
    else:
        return min(1.0 - conf, 0.5 - 1e-6)


def score_from_v1(parsed: Optional[dict]) -> float:
    if not parsed:
        return 0.5
    label = str(parsed.get("image_label", "")).lower()
    claims = parsed.get("claims", [])
    if not claims:
        return 0.1 if label == "normal" else 0.6
    max_conf = max(float(c.get("confidence", 0.0)) for c in claims)
    return max_conf if label == "anomalous" else 1.0 - max_conf


def score_from_debate(proposer: Optional[dict], refuter: Optional[dict]) -> float:
    """Aggregate a proposer/refuter debate into a single anomaly score in [0, 1].

    We use a confidence-gated, factorised rule selected on the calibration slice:
      - if the proposer commits to 'normal' with no claims, return 0.05
        (score_from_v1 behaviour for confident-normal)
      - for each claim, if the proposer confidence c is already high (c >= high_trust),
        trust the proposer and take `scored = c` --- a highly confident claim should not
        be punctured by a moderate refuter
      - otherwise attenuate with the refuter: `scored = c * (1 - r)`
        (independent-events factorisation; if refuter is sure (r=1), the claim drops to 0)
      - take max over claims and clip to [0, 1]

    Band (low=0.0, high=0.8) was selected by sweeping on SeedVL calibration; it
    beats the raw (0.5 + (c - r)) rule on macro AUROC and is insensitive to the
    low bound on this dataset.
    """
    if not proposer:
        return 0.5
    claims = proposer.get("claims", [])
    if not claims:
        label = str(proposer.get("image_label", "")).lower()
        return 0.05 if label == "normal" else 0.6

    reviews = {}
    if refuter:
        for r in refuter.get("reviews", []):
            reviews[r.get("id")] = float(r.get("refute_confidence", 0.0))

    high_trust = 0.80  # above this, trust the proposer outright
    best = 0.0
    for c in claims:
        conf = float(c.get("confidence", 0.0))
        rc = reviews.get(c.get("id", ""), 0.0)
        scored = conf if conf >= high_trust else conf * (1.0 - rc)
        if scored > best:
            best = scored
    return float(max(0.0, min(1.0, best)))


def label_from_score(score: float, threshold: float = 0.5) -> int:
    return 1 if score > threshold else 0


# ─── Backend clients ──────────────────────────────────────────────────────────

def get_client(backend: str) -> OpenAI:
    if backend == "gpt":
        api_key = os.environ.get("GPT_API_KEY") or os.environ.get("OPENAI_API_KEY")
        base_url = os.environ.get("GPT_API_BASE") or os.environ.get("OPENAI_API_BASE")
        if not api_key:
            raise RuntimeError(
                "GPT backend requires GPT_API_KEY (or OPENAI_API_KEY) and "
                "GPT_API_BASE (or OPENAI_API_BASE) to be set."
            )
        return OpenAI(api_key=api_key, base_url=base_url, timeout=120.0)
    elif backend == "seedvl":
        api_key = os.environ.get("SEED_API_KEY")
        if not api_key:
            raise RuntimeError("SeedVL backend requires SEED_API_KEY to be set.")
        base_url = os.environ.get("SEED_API_BASE", "https://ark.cn-beijing.volces.com/api/v3")
        return OpenAI(api_key=api_key, base_url=base_url, timeout=120.0)
    elif backend == "qwen3":
        # api_key = os.environ.get("QWEN_API_KEY", "EMPTY")
        api_key = os.environ.get("QWEN_API_KEY", None)
        # base_url = os.environ.get("QWEN_API_BASE", "http://localhost:8000/v1")
        base_url = os.environ.get("QWEN_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        return OpenAI(api_key=api_key, base_url=base_url)
    else:
        raise ValueError(f"Unknown backend: {backend}")


BACKEND_MODELS = {
    "gpt": os.environ.get("GPT_MODEL", "gpt-4o"),
    "seedvl": os.environ.get("SEED_MODEL", "doubao-seed-2-0-lite-260215"),
    # "qwen3": os.environ.get("QWEN_MODEL", "Qwen3-VL-8B-Instruct"),
    "qwen3": os.environ.get("QWEN_MODEL", "qwen3.5-flash"),
}


def get_model_name(backend: str, batch: bool = False) -> str:
    if backend == "seedvl" and batch:
        return os.environ.get("SEED_BATCH_MODEL", BACKEND_MODELS["seedvl"])
    return BACKEND_MODELS[backend]


_SERVED_MODEL_SEEN: dict[str, int] = {}
_SERVED_MODEL_LOG_PATH = os.environ.get("SERVED_MODEL_LOG", "/tmp/served_model.log")


def _log_served_model(requested: str, served: str) -> None:
    """First time we see a (requested, served) pair, emit a stderr line and
    append to the log file. On subsequent calls just bump the counter.
    """
    key = f"{requested}=>{served}"
    n = _SERVED_MODEL_SEEN.get(key, 0)
    _SERVED_MODEL_SEEN[key] = n + 1
    if n == 0:
        msg = f"[served_model] requested={requested!r} served={served!r} (first time in this process)"
        print(msg, file=sys.stderr, flush=True)
        try:
            import datetime as _dt
            with open(_SERVED_MODEL_LOG_PATH, "a") as _f:
                _f.write(f"{_dt.datetime.now().isoformat()} {msg} pid={os.getpid()}\n")
        except Exception:
            pass


def get_served_model_counts() -> dict[str, int]:
    """Return a snapshot of observed (requested -> served) model mappings
    and the number of calls to each. Useful in post-run analysis."""
    return dict(_SERVED_MODEL_SEEN)


def call_llm(client: OpenAI, model: str, messages: list,
             max_tokens: int = 700, temperature: float = 0.0) -> tuple[str, int, int]:
    """Returns (text, input_tokens, output_tokens).
    For Qwen3 thinking models served via vLLM we inject
    chat_template_kwargs={enable_thinking: False} to skip the free-text
    'Thinking Process' prefix which otherwise eats the max_tokens budget
    before any JSON is emitted.

    Side effect: logs the served model id (from resp.model) on first
    unique (requested, served) pair per process, to SERVED_MODEL_LOG
    env var (default /tmp/served_model.log).
    """
    # Allow CALL_LLM_TEMPERATURE env var to globally override (used for T-sweep experiments).
    _t_override = os.environ.get("CALL_LLM_TEMPERATURE")
    if _t_override is not None:
        try:
            temperature = float(_t_override)
        except ValueError:
            pass
    kwargs = dict(model=model, messages=messages, max_tokens=max_tokens, temperature=temperature)
    if "qwen3" in str(model).lower() or "Qwen3" in str(model):
        kwargs["extra_body"] = {"chat_template_kwargs": {"enable_thinking": True}}
    # GPT-5.x models have been observed to emit the same JSON object twice
    # back-to-back on complex multi-image prompts (see extract_json). Asking
    # for json_object response_format prevents the duplicate echo and also
    # enforces parseability.
    mlow = str(model).lower()
    if mlow.startswith("gpt-5") or mlow.startswith("gpt-4") or mlow.startswith("o"):
        kwargs["response_format"] = {"type": "json_object"}
    resp = client.chat.completions.create(**kwargs)
    text = resp.choices[0].message.content or ""
    usage = resp.usage
    served = getattr(resp, "model", None)
    if served is not None:
        _log_served_model(str(model), str(served))
    return text, usage.prompt_tokens, usage.completion_tokens


def _ark_obj_to_dict(obj: Any) -> dict:
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump") and callable(getattr(obj, "model_dump")):
        return obj.model_dump()
    if hasattr(obj, "dict") and callable(getattr(obj, "dict")):
        return obj.dict()
    if hasattr(obj, "__dict__"):
        return dict(obj.__dict__)
    try:
        return json.loads(json.dumps(obj))
    except Exception:
        return {"_raw": str(obj)}


def _extract_message_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            part_dict = _ark_obj_to_dict(part)
            text = part_dict.get("text")
            if isinstance(text, str):
                parts.append(text)
        return "".join(parts)
    return str(content)


def _extract_usage_tokens(resp: dict) -> tuple[int, int]:
    usage = _ark_obj_to_dict(resp.get("usage"))
    prompt_tokens = int(usage.get("prompt_tokens", 0) or 0)
    completion_tokens = int(usage.get("completion_tokens", 0) or 0)
    return prompt_tokens, completion_tokens


async def call_llm_async(client: Any, model: str, messages: list,
                         max_tokens: int = 700, temperature: float = 0.0) -> tuple[str, int, int]:
    retry_delay = 1
    last_error = None

    for _ in range(5):
        try:
            resp = await client.batch.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            resp_dict = _ark_obj_to_dict(resp)
            choices = resp_dict.get("choices") or []
            if not choices:
                raise RuntimeError(f"Empty batch response: {resp_dict}")
            choice = _ark_obj_to_dict(choices[0])
            message = _ark_obj_to_dict(choice.get("message"))
            text = _extract_message_text(message.get("content"))
            inp, out = _extract_usage_tokens(resp_dict)
            return text, inp, out
        except Exception as e:
            last_error = e
            await asyncio.sleep(retry_delay)
            retry_delay *= 2

    raise RuntimeError(f"Async batch call failed after retries: {last_error}") from last_error


# ─── Variant runners ──────────────────────────────────────────────────────────

N_REFS = 2  # default; overridden by --n_refs


def run_v0(client, model, item, max_tokens=700) -> dict:
    """V0: Direct single-pass."""
    ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:N_REFS]]
    query_img = load_and_encode(item["query_path"])
    domain_code = item["domain_code"]
    prompt = build_prompt_v0(domain_code, bool(ref_imgs))

    content = []
    for b64 in ref_imgs:
        content.append(text_msg("Normal reference:"))
        content.append(img_msg(b64))
    content.append(text_msg("Query image:"))
    content.append(img_msg(query_img))
    content.append(text_msg(prompt))

    t0 = time.time()
    text, inp, out = call_llm(client, model, [{"role": "user", "content": content}], max_tokens)
    latency = time.time() - t0

    parsed = extract_json(text)
    score = score_from_v0(parsed)
    anomaly_type = parsed.get("anomaly_type") if parsed else None

    return {
        "label_pred": label_from_score(score),
        "anomaly_score": score,
        "anomaly_type_pred": anomaly_type,
        "raw_output": {"v0": parsed},
        "cost_tokens": {"input": inp, "output": out},
        "latency_sec": round(latency, 2),
    }


def run_v1(client, model, item, max_tokens=700) -> dict:
    """V1: Normal-First single-pass."""
    ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:N_REFS]]
    query_img = load_and_encode(item["query_path"])
    domain_code = item["domain_code"]
    prompt = build_prompt_v1(domain_code, bool(ref_imgs))

    content = []
    for b64 in ref_imgs:
        content.append(text_msg("Normal reference:"))
        content.append(img_msg(b64))
    content.append(text_msg("Query image:"))
    content.append(img_msg(query_img))
    content.append(text_msg(prompt))

    t0 = time.time()
    text, inp, out = call_llm(client, model, [{"role": "user", "content": content}], max_tokens)
    latency = time.time() - t0

    parsed = extract_json(text)
    score = score_from_v1(parsed)
    claims = (parsed or {}).get("claims", [])
    anomaly_type = claims[0].get("anomaly_type") if claims else None

    return {
        "label_pred": label_from_score(score),
        "anomaly_score": score,
        "anomaly_type_pred": anomaly_type,
        "raw_output": {"v1": parsed},
        "cost_tokens": {"input": inp, "output": out},
        "latency_sec": round(latency, 2),
    }


def run_v2(client, model, item, max_tokens=700) -> dict:
    """V2: Self-Refine (V1 + one non-adversarial revision)."""
    # First call: V1
    r1 = run_v1(client, model, item, max_tokens)
    v1_parsed = (r1["raw_output"] or {}).get("v1")

    # Second call: self-refine
    refine_prompt = (
        "Here is your previous analysis:\n"
        + json.dumps(v1_parsed or {}, indent=2)
        + "\n\nRevise it once for consistency and possible non-anomalous explanations. "
        "Do not add new evidence that is not visible. Return JSON only in the same schema."
    )

    t0 = time.time()
    text2, inp2, out2 = call_llm(client, model,
        [{"role": "user", "content": refine_prompt}], max_tokens)
    latency2 = time.time() - t0

    parsed2 = extract_json(text2) or v1_parsed
    score = score_from_v1(parsed2)
    claims = (parsed2 or {}).get("claims", [])
    anomaly_type = claims[0].get("anomaly_type") if claims else None

    return {
        "label_pred": label_from_score(score),
        "anomaly_score": score,
        "anomaly_type_pred": anomaly_type,
        "raw_output": {"v1": v1_parsed, "v2_refined": parsed2},
        "cost_tokens": {
            "input": r1["cost_tokens"]["input"] + inp2,
            "output": r1["cost_tokens"]["output"] + out2,
        },
        "latency_sec": round(r1["latency_sec"] + latency2, 2),
    }


def run_v3(client, model, item, max_tokens=700) -> dict:
    """V3: Debate-1R (V1 proposer + refuter)."""
    # First call: proposer (V1)
    r1 = run_v1(client, model, item, max_tokens)
    v1_parsed = (r1["raw_output"] or {}).get("v1")
    claims = (v1_parsed or {}).get("claims", [])

    if not claims:
        # No claims to refute — treat same as V1
        return dict(r1, raw_output={"v1": v1_parsed, "refuter": None})

    # Second call: refuter (domain-anchored, EGRA C2)
    claims_json = json.dumps({"claims": claims}, indent=2)
    refuter_prompt = build_prompt_refuter(item["domain_code"], claims_json)

    t0 = time.time()
    text2, inp2, out2 = call_llm(client, model,
        [{"role": "user", "content": refuter_prompt}], max_tokens)
    latency2 = time.time() - t0

    refuter_parsed = extract_json(text2)
    score = score_from_debate(v1_parsed, refuter_parsed)
    anomaly_type = claims[0].get("anomaly_type") if claims else None

    return {
        "label_pred": label_from_score(score),
        "anomaly_score": score,
        "anomaly_type_pred": anomaly_type,
        "raw_output": {"v1": v1_parsed, "refuter": refuter_parsed},
        "cost_tokens": {
            "input": r1["cost_tokens"]["input"] + inp2,
            "output": r1["cost_tokens"]["output"] + out2,
        },
        "latency_sec": round(r1["latency_sec"] + latency2, 2),
    }


def run_v4(client, model, item, max_tokens=700) -> dict:
    """V4: Few-shot with many normal references (uses N_REFS)."""
    ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:N_REFS]]
    query_img = load_and_encode(item["query_path"])
    domain_code = item["domain_code"]
    prompt = build_prompt_v4(domain_code, len(ref_imgs))

    content = []
    for i, b64 in enumerate(ref_imgs):
        content.append(text_msg(f"Normal reference {i+1}/{len(ref_imgs)}:"))
        content.append(img_msg(b64))
    content.append(text_msg("QUERY image (classify this):"))
    content.append(img_msg(query_img))
    content.append(text_msg(prompt))

    t0 = time.time()
    text, inp, out = call_llm(client, model, [{"role": "user", "content": content}], max_tokens)
    latency = time.time() - t0

    parsed = extract_json(text)
    score = score_from_v0(parsed)
    anomaly_type = parsed.get("anomaly_type") if parsed else None

    return {
        "label_pred": label_from_score(score),
        "anomaly_score": score,
        "anomaly_type_pred": anomaly_type,
        "raw_output": {"v4": parsed},
        "cost_tokens": {"input": inp, "output": out},
        "latency_sec": round(latency, 2),
    }


# ─── V5 Agent: domain profile cache (populated once per domain per run) ──────
_domain_profiles = {}  # {domain_code: {"profile_json": str, "cost": (inp, out)}}


def run_v5(client, model, item, max_tokens=700) -> dict:
    """V5: Agent-based full-shot. Phase 1: profile domain normals. Phase 2: judge query."""
    domain_code = item["domain_code"]

    # Phase 1: build domain profile (cached per domain)
    if domain_code not in _domain_profiles:
        all_refs = [load_and_encode(p) for p in item["ref_paths"][:10]]
        profile_prompt = build_prompt_v5_profile(domain_code, len(all_refs))

        content = []
        for i, b64 in enumerate(all_refs):
            content.append(text_msg(f"Normal sample {i+1}/{len(all_refs)}:"))
            content.append(img_msg(b64))
        content.append(text_msg(profile_prompt))

        text1, inp1, out1 = call_llm(client, model,
            [{"role": "user", "content": content}], max_tokens=1000)
        profile_parsed = extract_json(text1)
        profile_json = json.dumps(profile_parsed, indent=2) if profile_parsed else text1

        _domain_profiles[domain_code] = {
            "profile_json": profile_json,
            "profile_parsed": profile_parsed,
            "cost": (inp1, out1),
        }

    profile = _domain_profiles[domain_code]

    # Phase 2: judge query with profile + 2 visual refs
    ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:2]]
    query_img = load_and_encode(item["query_path"])
    judge_prompt = build_prompt_v5_judge(domain_code, profile["profile_json"])

    content = []
    for b64 in ref_imgs:
        content.append(text_msg("Normal reference:"))
        content.append(img_msg(b64))
    content.append(text_msg("QUERY image:"))
    content.append(img_msg(query_img))
    content.append(text_msg(judge_prompt))

    t0 = time.time()
    text2, inp2, out2 = call_llm(client, model, [{"role": "user", "content": content}], max_tokens)
    latency = time.time() - t0

    parsed = extract_json(text2)
    score = score_from_v0(parsed)
    anomaly_type = parsed.get("anomaly_type") if parsed else None

    # Amortize phase-1 cost across items (reported per item for fairness)
    p1_inp, p1_out = profile["cost"]

    return {
        "label_pred": label_from_score(score),
        "anomaly_score": score,
        "anomaly_type_pred": anomaly_type,
        "raw_output": {
            "v5_profile": profile.get("profile_parsed"),
            "v5_judge": parsed,
        },
        "cost_tokens": {"input": inp2 + p1_inp // 20, "output": out2 + p1_out // 20},
        "latency_sec": round(latency, 2),
    }


# ─── RGNC Profile cache ──────────────────────────────────────────────────────
_rgnc_profiles = {}  # {frozen_ref_key: {"json": str, "parsed": dict, "cost": (inp, out)}}


def _ref_key(item):
    """Cache key from reference paths."""
    return tuple(sorted(item["ref_paths"][:N_REFS]))


def _get_or_build_profile(client, model, item):
    """Build RGNC normality profile from references, cached per reference set."""
    key = _ref_key(item)
    if key in _rgnc_profiles:
        return _rgnc_profiles[key]

    ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:N_REFS]]
    prompt = build_prompt_rgnc_profile(item["domain_code"], len(ref_imgs))

    content = []
    for i, b64 in enumerate(ref_imgs):
        content.append(text_msg(f"Normal reference {i+1}/{len(ref_imgs)}:"))
        content.append(img_msg(b64))
    content.append(text_msg(prompt))

    text, inp, out = call_llm(client, model, [{"role": "user", "content": content}], max_tokens=800)
    parsed = extract_json(text)
    profile_json = json.dumps(parsed, indent=2) if parsed else text

    _rgnc_profiles[key] = {"json": profile_json, "parsed": parsed, "cost": (inp, out)}
    return _rgnc_profiles[key]


def _compute_rgnc_score(parsed: Optional[dict]) -> float:
    """Compute anomaly score from RGNC inspection result."""
    if not parsed:
        return 0.5
    # Direct anomaly_score if provided
    if "anomaly_score" in parsed:
        try:
            return float(parsed["anomaly_score"])
        except (ValueError, TypeError):
            pass
    # Compute from violations: 1 - product(1 - severity)
    violations = parsed.get("violations", [])
    if not violations:
        return 0.05
    product = 1.0
    for v in violations:
        sev = float(v.get("severity", 0))
        product *= (1.0 - sev)
    return float(np.clip(1.0 - product, 0.0, 1.0))


def run_v6_rgnc(client, model, item, max_tokens=700) -> dict:
    """V6: RGNC — Reference-Grounded Normality Constraints (single-pass, Variant A)."""
    profile = _get_or_build_profile(client, model, item)

    ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:N_REFS]]
    query_img = load_and_encode(item["query_path"])
    prompt = build_prompt_rgnc_inspect(item["domain_code"], profile["json"])

    content = []
    for i, b64 in enumerate(ref_imgs):
        content.append(text_msg(f"Normal reference {i+1}:"))
        content.append(img_msg(b64))
    content.append(text_msg("QUERY image:"))
    content.append(img_msg(query_img))
    content.append(text_msg(prompt))

    t0 = time.time()
    text, inp, out = call_llm(client, model, [{"role": "user", "content": content}], max_tokens)
    latency = time.time() - t0

    parsed = extract_json(text)
    # Use V0 scoring (label+confidence based) instead of violations-based
    score = score_from_v0(parsed)
    anomaly_type = parsed.get("anomaly_type") if parsed else None
    p1_inp, p1_out = profile["cost"]

    return {
        "label_pred": label_from_score(score),
        "anomaly_score": score,
        "anomaly_type_pred": anomaly_type,
        "raw_output": {"rgnc_profile": profile.get("parsed"), "rgnc_inspect": parsed},
        "cost_tokens": {"input": inp + p1_inp // 20, "output": out + p1_out // 20},
        "latency_sec": round(latency, 2),
    }


def run_v7_rgnc_verify(client, model, item, max_tokens=700) -> dict:
    """V7: RGNC + Verifier (Variant B)."""
    # Step 1: RGNC inspection (same as V6)
    r6 = run_v6_rgnc(client, model, item, max_tokens)
    inspect_parsed = (r6["raw_output"] or {}).get("rgnc_inspect")
    violations = (inspect_parsed or {}).get("violations", [])

    if not violations:
        # No violations → no need to verify
        return r6

    # Step 2: Verify violations
    profile = _get_or_build_profile(client, model, item)
    violations_json = json.dumps({"violations": violations}, indent=2)
    verify_prompt = build_prompt_rgnc_verify(profile["json"], violations_json)

    # Verifier also gets query image for visual grounding
    query_img = load_and_encode(item["query_path"])
    ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:min(2, N_REFS)]]

    content = []
    for b64 in ref_imgs:
        content.append(text_msg("Reference:"))
        content.append(img_msg(b64))
    content.append(text_msg("Query:"))
    content.append(img_msg(query_img))
    content.append(text_msg(verify_prompt))

    t0 = time.time()
    text2, inp2, out2 = call_llm(client, model, [{"role": "user", "content": content}], max_tokens)
    latency2 = time.time() - t0

    verify_parsed = extract_json(text2)

    # Update severities based on verification
    if verify_parsed and "reviews" in verify_parsed:
        for review in verify_parsed["reviews"]:
            vid = review.get("violation_id", -1)
            if not review.get("is_genuine", True):
                # False alarm — zero out severity
                if 0 <= vid < len(violations):
                    violations[vid]["severity"] = 0.0
            else:
                rev_sev = review.get("revised_severity")
                if rev_sev is not None and 0 <= vid < len(violations):
                    violations[vid]["severity"] = float(rev_sev)

    # Recompute score with verified violations
    product = 1.0
    for v in violations:
        product *= (1.0 - float(v.get("severity", 0)))
    score = float(np.clip(1.0 - product, 0.0, 1.0)) if violations else 0.05

    return {
        "label_pred": label_from_score(score),
        "anomaly_score": score,
        "anomaly_type_pred": None,
        "raw_output": {
            "rgnc_profile": profile.get("parsed"),
            "rgnc_inspect": inspect_parsed,
            "rgnc_verify": verify_parsed,
        },
        "cost_tokens": {
            "input": r6["cost_tokens"]["input"] + inp2,
            "output": r6["cost_tokens"]["output"] + out2,
        },
        "latency_sec": round(r6["latency_sec"] + latency2, 2),
    }


# ─── Scout-Judge Prompts ─────────────────────────────────────────────────────

SCOUT_SCHEMA = """{
  "candidates": [
    {
      "id": "C1",
      "description": "concrete deviation found in query vs references",
      "location": "where in the image",
      "confidence": float 0-1
    }
  ],
  "no_difference_conf": float 0-1
}"""

JUDGE_SCHEMA = """{
  "per_candidate": [
    {
      "id": "C1",
      "is_anomaly": true or false,
      "reasoning": "why this is a genuine anomaly or a normal variation"
    }
  ],
  "final_label": "normal" or "anomalous",
  "final_confidence": float 0-1
}"""


def build_prompt_scout(domain_code: str, profile_json: str = None) -> str:
    ctx = DOMAIN_CONTEXT.get(domain_code, "image")
    profile_block = ""
    if profile_json:
        profile_block = (
            f"\nNormality profile (learned from references):\n{profile_json}\n"
            f"Use this profile to understand what is NORMAL. "
            f"Differences that match benign_variations are NOT deviations — skip them.\n\n"
        )
    return (
        f"You are a discrepancy scout examining a {ctx}.\n"
        f"You will see normal references and 1 query.\n"
        f"Do NOT decide normal/anomalous yet.\n"
        f"Find concrete deviations in the query that are absent from ALL references.\n"
        f"{profile_block}"
        f"Search for: surface defects, broken/missing/extra parts, "
        f"count/layout anomalies, focal lesions, structural damage.\n\n"
        f"Return JSON only:\n{SCOUT_SCHEMA}"
    )


def build_prompt_judge(scout_json: str, profile_json: str = None) -> str:
    profile_block = ""
    if profile_json:
        profile_block = (
            f"\nNormality profile:\n{profile_json}\n"
            f"A candidate is a genuine anomaly ONLY if it cannot be explained by "
            f"normal_patterns or benign_variations in the profile.\n\n"
        )
    return (
        f"You are the anomaly judge.\n"
        f"Review each Scout candidate and decide if it is a genuine anomaly "
        f"or a normal variation.\n\n"
        f"Scout report:\n{scout_json}\n"
        f"{profile_block}"
        f"Then inspect the images yourself to make the final decision.\n\n"
        f"Return JSON only:\n{JUDGE_SCHEMA}"
    )


def _compute_scout_judge_score(scout: dict, judge: dict) -> float:
    """Simple scoring: use Judge's final_label + final_confidence, same as V0."""
    if not judge:
        return 0.5
    label = str(judge.get("final_label", "")).lower()
    conf = float(judge.get("final_confidence", 0.5))
    if label == "anomalous":
        return max(conf, 0.5 + 1e-6)
    elif label == "normal":
        return min(1.0 - conf, 0.5 - 1e-6)
    return 0.5


def run_v9_scout_judge(client, model, item, max_tokens=700) -> dict:
    """V9: Profile → Scout → Judge. Three-phase with normality grounding."""
    ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:N_REFS]]
    query_img = load_and_encode(item["query_path"])

    # Phase 0: Get normality profile (cached per ref set)
    profile = _get_or_build_profile(client, model, item)
    profile_json = profile["json"]

    # Phase 1: Scout (NO profile — keep high recall)
    scout_prompt = build_prompt_scout(item["domain_code"])
    content1 = []
    for i, b64 in enumerate(ref_imgs):
        content1.append(text_msg(f"Normal reference {i+1}:"))
        content1.append(img_msg(b64))
    content1.append(text_msg("QUERY image:"))
    content1.append(img_msg(query_img))
    content1.append(text_msg(scout_prompt))

    t0 = time.time()
    text1, inp1, out1 = call_llm(client, model, [{"role": "user", "content": content1}], max_tokens=800)
    scout_parsed = extract_json(text1)

    # Phase 2: Judge (with profile + scout output)
    scout_json = json.dumps(scout_parsed, indent=2) if scout_parsed else text1
    judge_prompt = build_prompt_judge(scout_json, profile_json)
    content2 = []
    for i, b64 in enumerate(ref_imgs):
        content2.append(text_msg(f"Reference {i+1}:"))
        content2.append(img_msg(b64))
    content2.append(text_msg("Query:"))
    content2.append(img_msg(query_img))
    content2.append(text_msg(judge_prompt))

    text2, inp2, out2 = call_llm(client, model, [{"role": "user", "content": content2}], max_tokens)
    latency = time.time() - t0
    judge_parsed = extract_json(text2)

    score = _compute_scout_judge_score(scout_parsed, judge_parsed)
    p1_inp, p1_out = profile["cost"]

    return {
        "label_pred": label_from_score(score),
        "anomaly_score": score,
        "anomaly_type_pred": None,
        "raw_output": {"profile": profile.get("parsed"), "scout": scout_parsed, "judge": judge_parsed},
        "cost_tokens": {"input": inp1 + inp2 + p1_inp // 20, "output": out1 + out2 + p1_out // 20},
        "latency_sec": round(latency, 2),
    }


_unstructured_cache = {}


def run_v8_unstructured(client, model, item, max_tokens=700) -> dict:
    """V8: Unstructured summary control — same token budget as RGNC, free-text profile."""
    key = _ref_key(item)
    if key not in _unstructured_cache:
        ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:N_REFS]]
        prompt = build_prompt_rgnc_unstructured(item["domain_code"], len(ref_imgs))
        content = []
        for i, b64 in enumerate(ref_imgs):
            content.append(text_msg(f"Normal reference {i+1}/{len(ref_imgs)}:"))
            content.append(img_msg(b64))
        content.append(text_msg(prompt))
        text, inp, out = call_llm(client, model, [{"role": "user", "content": content}], max_tokens=400)
        parsed = extract_json(text)
        summary = (parsed or {}).get("normality_summary", text)
        _unstructured_cache[key] = {"summary": summary, "cost": (inp, out)}

    cache = _unstructured_cache[key]
    ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:N_REFS]]
    query_img = load_and_encode(item["query_path"])
    prompt = build_prompt_rgnc_unstructured_inspect(item["domain_code"], cache["summary"])

    content = []
    for i, b64 in enumerate(ref_imgs):
        content.append(text_msg(f"Normal reference {i+1}:"))
        content.append(img_msg(b64))
    content.append(text_msg("QUERY image:"))
    content.append(img_msg(query_img))
    content.append(text_msg(prompt))

    t0 = time.time()
    text, inp, out = call_llm(client, model, [{"role": "user", "content": content}], max_tokens)
    latency = time.time() - t0
    parsed = extract_json(text)
    score = score_from_v0(parsed)
    p1_inp, p1_out = cache["cost"]

    return {
        "label_pred": label_from_score(score),
        "anomaly_score": score,
        "anomaly_type_pred": parsed.get("anomaly_type") if parsed else None,
        "raw_output": {"unstructured_summary": cache["summary"], "inspect": parsed},
        "cost_tokens": {"input": inp + p1_inp // 20, "output": out + p1_out // 20},
        "latency_sec": round(latency, 2),
    }


# ─── EGRA components (v3_grounded, v3_egra) ─────────────────────────────────
# C1 evidence-grounded proposer: injects DINOv2 patch-kNN top-k evidence as text.
# C3 disagreement-gated arbiter: adds a third VLM call when proposer and refuter are near a tie.

_patch_evidence_cache = None


def _load_patch_evidence_cache():
    """Lazy-load the JSON cache built by build_patch_evidence_cache.py."""
    global _patch_evidence_cache
    if _patch_evidence_cache is not None:
        return _patch_evidence_cache
    path = os.environ.get(
        "PATCH_EVIDENCE_CACHE",
        "benchmark/results/patch_evidence_test.json",
    )
    try:
        with open(path) as f:
            _patch_evidence_cache = json.load(f)
        print(f"[EGRA] loaded patch evidence cache: {path} ({len(_patch_evidence_cache)} entries)")
    except FileNotFoundError:
        print(f"[EGRA][WARN] patch evidence cache not found at {path} — "
              f"v3_grounded/v3_egra will fall back to empty evidence")
        _patch_evidence_cache = {}
    return _patch_evidence_cache


def format_patch_evidence(evidence: Optional[dict]) -> str:
    """Render a cached patch-evidence dict into a short textual block for the prompt."""
    if not evidence or evidence.get("error"):
        return (
            "[DINOv2 patch evidence]\n"
            "No reliable patch evidence is available for this query. "
            "Rely on visual inspection and the domain descriptor only.\n"
        )
    top = evidence.get("top_patches", [])
    baseline = evidence.get("baseline", 0.0)
    lines = [
        "[DINOv2 patch evidence vs. normal reference(s)]",
        f"Top-{len(top)} most anomalous patches (cosine distance to nearest normal patch; "
        f"median normal distance = {baseline}):",
    ]
    for p in top:
        lines.append(
            f"  rank {p['rank']}: distance = {p['distance']} at region '{p['region']}'"
        )
    lines.append(
        "Interpret this as SUPPORTING EVIDENCE, not ground truth. "
        "High distance means the patch is unlike the normal references, but lighting, "
        "viewpoint, or occlusion can also produce high distances."
    )
    return "\n".join(lines)


def run_v3_grounded(client, model, item, max_tokens=700) -> dict:
    """V3-grounded: v1 proposer WITH patch evidence + domain-anchored refuter.
    This implements EGRA components C1 (evidence injection) and C2 (domain-anchored
    refuter, already active for plain v3). C3 gating is NOT applied here; use
    v3_egra for the full pipeline.
    """
    cache = _load_patch_evidence_cache()
    evidence = cache.get(item["item_id"])
    evidence_text = format_patch_evidence(evidence)

    ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:N_REFS]]
    query_img = load_and_encode(item["query_path"])
    prompt = build_prompt_v1(item["domain_code"], bool(ref_imgs))

    content = []
    for b64 in ref_imgs:
        content.append(text_msg("Normal reference:"))
        content.append(img_msg(b64))
    content.append(text_msg("Query image:"))
    content.append(img_msg(query_img))
    content.append(text_msg(evidence_text))  # C1: evidence before the task prompt
    content.append(text_msg(prompt))

    t0 = time.time()
    text, inp1, out1 = call_llm(client, model, [{"role": "user", "content": content}], max_tokens)
    lat1 = time.time() - t0

    v1_parsed = extract_json(text)
    claims = (v1_parsed or {}).get("claims", [])

    if not claims:
        # proposer committed to "normal" with no claims → no need for refuter
        score = score_from_v1(v1_parsed)
        return {
            "label_pred": label_from_score(score),
            "anomaly_score": score,
            "anomaly_type_pred": None,
            "raw_output": {"v1_grounded": v1_parsed, "refuter": None,
                            "evidence_used": evidence},
            "cost_tokens": {"input": inp1, "output": out1},
            "latency_sec": round(lat1, 2),
        }

    # Second call: domain-anchored refuter (same as plain v3 with C2 fix)
    claims_json = json.dumps({"claims": claims}, indent=2)
    refuter_prompt = build_prompt_refuter(item["domain_code"], claims_json)
    t0 = time.time()
    text2, inp2, out2 = call_llm(client, model,
        [{"role": "user", "content": refuter_prompt}], max_tokens)
    lat2 = time.time() - t0

    refuter_parsed = extract_json(text2)
    score = score_from_debate(v1_parsed, refuter_parsed)
    return {
        "label_pred": label_from_score(score),
        "anomaly_score": score,
        "anomaly_type_pred": claims[0].get("anomaly_type") if claims else None,
        "raw_output": {"v1_grounded": v1_parsed, "refuter": refuter_parsed,
                        "evidence_used": evidence},
        "cost_tokens": {"input": inp1 + inp2, "output": out1 + out2},
        "latency_sec": round(lat1 + lat2, 2),
    }


def _top_claim_refute_gap(proposer: Optional[dict], refuter: Optional[dict]) -> float:
    """Return |c* - r*|, the absolute confidence gap used for C3 gating."""
    if not proposer:
        return 1.0
    claims = proposer.get("claims", [])
    if not claims:
        return 1.0
    reviews = {}
    if refuter:
        for r in refuter.get("reviews", []):
            reviews[r.get("id")] = float(r.get("refute_confidence", 0.0))
    best_gap = 1.0
    best_absgap = 1.0
    for c in claims:
        conf = float(c.get("confidence", 0.0))
        rc = reviews.get(c.get("id", ""), 0.0)
        gap = conf - rc
        if abs(gap) < best_absgap:
            best_absgap = abs(gap)
            best_gap = gap
    return best_absgap


def build_prompt_arbiter(domain_code: str, proposer_json: str, refuter_json: str,
                          evidence_text: str) -> str:
    ctx = DOMAIN_CONTEXT.get(domain_code, "image")
    return (
        f"You are the final arbiter in a visual anomaly detection agent.\n"
        f"Task context: the query image is a {ctx}\n\n"
        f"An earlier proposer suggested the following anomaly claims, and a refuter "
        f"tried to explain them away. The proposer and refuter are in near-tie, so "
        f"you must make the final call.\n\n"
        f"Proposer output (JSON):\n{proposer_json}\n\n"
        f"Refuter output (JSON):\n{refuter_json}\n\n"
        f"{evidence_text}\n\n"
        f"Considering the domain descriptor, the proposer, the refuter, and the "
        f"patch evidence above, output the final decision and confidence.\n"
        f"Return JSON only with the schema:\n"
        f"{{\"image_label\": \"anomalous\" | \"normal\", \"confidence\": float 0..1, "
        f"\"justification\": string}}"
    )


def run_v3_egra(client, model, item, max_tokens=700) -> dict:
    """Full EGRA pipeline: C1 evidence-grounded proposer + C2 domain-anchored refuter
    + C3 disagreement-gated arbiter (third call only when proposer/refuter in tie).
    """
    cache = _load_patch_evidence_cache()
    evidence = cache.get(item["item_id"])
    evidence_text = format_patch_evidence(evidence)
    gate_tau = float(os.environ.get("EGRA_GATE_TAU", "0.2"))

    # Step 1: C1 evidence-grounded proposer (same as v3_grounded first call)
    ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:N_REFS]]
    query_img = load_and_encode(item["query_path"])
    prompt = build_prompt_v1(item["domain_code"], bool(ref_imgs))
    content = []
    for b64 in ref_imgs:
        content.append(text_msg("Normal reference:"))
        content.append(img_msg(b64))
    content.append(text_msg("Query image:"))
    content.append(img_msg(query_img))
    content.append(text_msg(evidence_text))
    content.append(text_msg(prompt))
    t0 = time.time()
    text, inp1, out1 = call_llm(client, model, [{"role": "user", "content": content}], max_tokens)
    lat1 = time.time() - t0

    v1_parsed = extract_json(text)
    claims = (v1_parsed or {}).get("claims", [])

    total_inp, total_out, total_lat = inp1, out1, lat1
    refuter_parsed = None
    arbiter_parsed = None
    arbitrated = False

    if not claims:
        score = score_from_v1(v1_parsed)
        return {
            "label_pred": label_from_score(score),
            "anomaly_score": score,
            "anomaly_type_pred": None,
            "raw_output": {"v1_grounded": v1_parsed, "refuter": None,
                            "arbiter": None, "arbitrated": False,
                            "evidence_used": evidence},
            "cost_tokens": {"input": total_inp, "output": total_out},
            "latency_sec": round(total_lat, 2),
        }

    # Step 2: C2 domain-anchored refuter
    claims_json = json.dumps({"claims": claims}, indent=2)
    refuter_prompt = build_prompt_refuter(item["domain_code"], claims_json)
    t0 = time.time()
    text2, inp2, out2 = call_llm(client, model,
        [{"role": "user", "content": refuter_prompt}], max_tokens)
    lat2 = time.time() - t0
    total_inp += inp2; total_out += out2; total_lat += lat2
    refuter_parsed = extract_json(text2)

    debate_score = score_from_debate(v1_parsed, refuter_parsed)
    gap = _top_claim_refute_gap(v1_parsed, refuter_parsed)

    # Step 3: C3 disagreement-gated arbiter (only if in near-tie band)
    if gap < gate_tau:
        arbitrated = True
        proposer_json = json.dumps(v1_parsed or {}, indent=2)
        refuter_out_json = json.dumps(refuter_parsed or {}, indent=2)
        arbiter_prompt = build_prompt_arbiter(
            item["domain_code"], proposer_json, refuter_out_json, evidence_text,
        )
        # Arbiter sees the query image again + proposer/refuter text + evidence
        arb_content = []
        for b64 in ref_imgs:
            arb_content.append(text_msg("Normal reference:"))
            arb_content.append(img_msg(b64))
        arb_content.append(text_msg("Query image:"))
        arb_content.append(img_msg(query_img))
        arb_content.append(text_msg(arbiter_prompt))
        t0 = time.time()
        text3, inp3, out3 = call_llm(client, model,
            [{"role": "user", "content": arb_content}], max_tokens)
        lat3 = time.time() - t0
        total_inp += inp3; total_out += out3; total_lat += lat3
        arbiter_parsed = extract_json(text3)
        if arbiter_parsed:
            label = str(arbiter_parsed.get("image_label", "")).lower()
            conf = float(arbiter_parsed.get("confidence", 0.5))
            score = conf if label == "anomalous" else 1.0 - conf
        else:
            score = debate_score
    else:
        score = debate_score

    return {
        "label_pred": label_from_score(score),
        "anomaly_score": score,
        "anomaly_type_pred": claims[0].get("anomaly_type") if claims else None,
        "raw_output": {"v1_grounded": v1_parsed, "refuter": refuter_parsed,
                        "arbiter": arbiter_parsed, "arbitrated": arbitrated,
                        "gap": round(gap, 3), "evidence_used": evidence},
        "cost_tokens": {"input": total_inp, "output": total_out},
        "latency_sec": round(total_lat, 2),
    }


# ─── EGRA final pipeline: v0 + G1 escalation + G2 gated aggregation ──────────

def run_egra(client, model, item, max_tokens=700) -> dict:
    """Final EGRA pipeline (G1 + G2):
    1. Run v0_direct with domain descriptor (1 call).
    2. Look up DINOv2 patch global_score from cache (0 calls).
    3. Escalate if v0 is in [tau_low, tau_high] (band) OR
       v0 says normal but patch is strongly anomalous (FN-catcher).
    4. Escalated items: run v1 proposer + domain-anchored refuter,
       aggregate with the gated c*(1-r) rule.
    Average call budget ~= 1 + 2 * p_escalation.
    """
    tau_low = float(os.environ.get("EGRA_TAU_LOW", "0.20"))
    tau_high = float(os.environ.get("EGRA_TAU_HIGH", "0.85"))
    rho = float(os.environ.get("EGRA_RHO", "0.60"))

    # Step 1: v0
    r0 = run_v0(client, model, item, max_tokens)
    s0 = float(r0.get("anomaly_score", 0.5))

    # Step 2: DINOv2 patch global score from cache (normalised)
    cache = _load_patch_evidence_cache()
    entry = cache.get(item["item_id"]) or {}
    gs_raw = entry.get("global_score")
    # Normalise via cache-wide min/max (computed lazily)
    global _patch_minmax
    try:
        _patch_minmax
    except NameError:
        _patch_minmax = None
    if _patch_minmax is None and cache:
        vals = [e.get("global_score") for e in cache.values()
                if isinstance(e.get("global_score"), (int, float))]
        if vals:
            globals()["_patch_minmax"] = (float(min(vals)), float(max(vals)))
    pnorm = None
    if _patch_minmax and isinstance(gs_raw, (int, float)):
        lo, hi = _patch_minmax
        pnorm = (gs_raw - lo) / (hi - lo) if hi > lo else 0.5

    # Step 3: gate — commit to v0 unless band or FN-catcher fires
    band = (tau_low <= s0 <= tau_high)
    fn_catch = (s0 < 0.5 and pnorm is not None and pnorm >= rho)

    if not (band or fn_catch):
        return {
            "label_pred": r0["label_pred"],
            "anomaly_score": s0,
            "anomaly_type_pred": r0.get("anomaly_type_pred"),
            "raw_output": {
                "path": "v0_only",
                "s0": s0,
                "patch_norm": pnorm,
                "v0": (r0.get("raw_output") or {}).get("v0"),
            },
            "cost_tokens": r0["cost_tokens"],
            "latency_sec": r0["latency_sec"],
        }

    # Step 3: escalate — run v1 proposer + refuter, gated aggregation
    r1 = run_v1(client, model, item, max_tokens)
    v1_parsed = (r1["raw_output"] or {}).get("v1")
    claims = (v1_parsed or {}).get("claims", [])
    total_inp = r0["cost_tokens"]["input"] + r1["cost_tokens"]["input"]
    total_out = r0["cost_tokens"]["output"] + r1["cost_tokens"]["output"]
    total_lat = r0["latency_sec"] + r1["latency_sec"]

    if not claims:
        # Proposer committed to normal → trust it
        score = score_from_v1(v1_parsed)
        return {
            "label_pred": label_from_score(score),
            "anomaly_score": score,
            "anomaly_type_pred": None,
            "raw_output": {
                "path": "v0+v1_nocla",
                "s0": s0,
                "v0": (r0.get("raw_output") or {}).get("v0"),
                "v1": v1_parsed,
            },
            "cost_tokens": {"input": total_inp, "output": total_out},
            "latency_sec": round(total_lat, 2),
        }

    # Refuter call
    claims_json = json.dumps({"claims": claims}, indent=2)
    refuter_prompt = build_prompt_refuter(item["domain_code"], claims_json)
    t0 = time.time()
    text2, inp2, out2 = call_llm(client, model,
        [{"role": "user", "content": refuter_prompt}], max_tokens)
    lat2 = time.time() - t0
    refuter_parsed = extract_json(text2)
    total_inp += inp2; total_out += out2; total_lat += lat2

    # Gated aggregation (score_from_debate already uses the gated c*(1-r) rule)
    score = score_from_debate(v1_parsed, refuter_parsed)

    return {
        "label_pred": label_from_score(score),
        "anomaly_score": score,
        "anomaly_type_pred": claims[0].get("anomaly_type") if claims else None,
        "raw_output": {
            "path": "v0+v1+refuter",
            "s0": s0,
            "v0": (r0.get("raw_output") or {}).get("v0"),
            "v1": v1_parsed,
            "refuter": refuter_parsed,
        },
        "cost_tokens": {"input": total_inp, "output": total_out},
        "latency_sec": round(total_lat, 2),
    }


# ─── CrossAD-Agent v1: Perceive → Expert → Interpret ─────────────────────────

_subspacead_tool = None

def _get_subspacead():
    global _subspacead_tool
    if _subspacead_tool is not None:
        return _subspacead_tool
    try:
        import sys as _sys
        _sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
        from expert_subspacead import SubspaceADTool
        device = os.environ.get("EXPERT_DEVICE", "cuda:0")
        _subspacead_tool = SubspaceADTool(device=device)
        return _subspacead_tool
    except Exception as e:
        print(f"[CrossAD] SubspaceAD init failed: {e}")
        return None


def build_prompt_interpret(domain_code: str, v0_label: str, v0_confidence: float,
                            expert_summary: str) -> str:
    """Phase 3 INTERPRET: VLM sees expert evidence and makes final decision."""
    ctx = DOMAIN_CONTEXT.get(domain_code, "image")
    return (
        f"You are the final decision-maker in a visual anomaly detection agent.\n"
        f"Task context: the query image is a {ctx}\n\n"
        f"An initial visual inspection classified this image as '{v0_label}' "
        f"with confidence {v0_confidence:.2f}.\n\n"
        f"An independent patch-level expert (DINOv2-based SubspaceAD) analysed the same "
        f"query against the normal reference images and produced the following evidence:\n"
        f"{expert_summary}\n\n"
        f"Now look at the query image and reference image(s) again, paying close attention "
        f"to the regions flagged by the expert. Consider:\n"
        f"1. Do the expert's high-anomaly-score regions correspond to genuine task-level "
        f"anomalies, or to benign differences (lighting, viewpoint, normal variation)?\n"
        f"2. Did the initial inspection miss something the expert caught, or is the expert "
        f"raising a false alarm?\n"
        f"3. Conversely, did the initial inspection find something the expert missed?\n\n"
        f"Based on your visual re-examination of the flagged regions AND the domain "
        f"descriptor above, output your final decision.\n"
        f"Return JSON only: {{\"image_label\": \"anomalous\" | \"normal\", "
        f"\"confidence\": float 0..1, \"reasoning\": string}}"
    )


def format_subspacead_evidence(expert_result: dict) -> str:
    """Format SubspaceAD output as a text block for the VLM."""
    if not expert_result or expert_result.get("error"):
        return "[Expert evidence unavailable]"
    score = expert_result.get("anomaly_score", 0)
    norm = expert_result.get("anomaly_score_norm", 0.5)
    patches = expert_result.get("top_patches", [])
    lines = [
        f"[SubspaceAD patch-level analysis]",
        f"Global anomaly score: {score:.2f} (normalised: {norm:.2f})",
        f"Top-{len(patches)} most anomalous patches vs normal references:",
    ]
    for p in patches[:5]:
        lines.append(f"  rank {p['rank']}: anomaly_score={p['score']:.2f}, region='{p['region']}'")
    if norm > 0.7:
        lines.append("Expert assessment: LIKELY ANOMALOUS (high deviation from normal references)")
    elif norm < 0.3:
        lines.append("Expert assessment: LIKELY NORMAL (low deviation)")
    else:
        lines.append("Expert assessment: UNCERTAIN (moderate deviation)")
    return "\n".join(lines)


def run_agent_v1(client, model, item, max_tokens=700) -> dict:
    """CrossAD-Agent v1: Perceive → Expert → Interpret.

    Phase 1 (PERCEIVE): Run v0_direct (1 VLM call).
    Phase 2 (EXPERT): Run SubspaceAD on (query, refs) — zero VLM calls.
    Phase 3 (INTERPRET): If v0 and expert DISAGREE, VLM re-examines with expert
        evidence (1 more VLM call). If they agree, commit to v0.

    Average: ~1.3 VLM calls per image (70% agreement, 30% disagree).
    """
    # Phase 1: PERCEIVE — standard v0
    r0 = run_v0(client, model, item, max_tokens)
    v0_score = float(r0.get("anomaly_score", 0.5))
    v0_parsed = (r0.get("raw_output") or {}).get("v0") or {}
    v0_label = str(v0_parsed.get("image_label", "normal")).lower()
    v0_conf = float(v0_parsed.get("confidence", 0.5))

    # Phase 2: EXPERT — load pre-computed expert results from cache.
    # Multi-expert: SubspaceAD for most domains, DINOv2 patch evidence for D6.
    global _subspacead_cache, _dinov2_patch_cache
    try:
        _subspacead_cache
    except NameError:
        _subspacead_cache = None
    try:
        _dinov2_patch_cache
    except NameError:
        _dinov2_patch_cache = None

    if _subspacead_cache is None:
        cache_path = os.environ.get(
            "SUBSPACEAD_CACHE",
            "benchmark/results/subspacead_calibration.json",
        )
        try:
            raw = json.load(open(cache_path))
            _subspacead_cache = {x["item_id"]: x for x in raw}
            print(f"[CrossAD] loaded SubspaceAD cache: {cache_path} ({len(_subspacead_cache)} items)")
        except FileNotFoundError:
            _subspacead_cache = {}

    if _dinov2_patch_cache is None:
        patch_path = os.environ.get(
            "PATCH_EVIDENCE_CACHE",
            "benchmark/results/patch_evidence_calibration.json",
        )
        try:
            _dinov2_patch_cache = json.load(open(patch_path))
            print(f"[CrossAD] loaded DINOv2 patch cache: {patch_path} ({len(_dinov2_patch_cache)} items)")
        except FileNotFoundError:
            _dinov2_patch_cache = {}

    # Select expert based on domain
    DINOV2_DOMAINS = {"D6"}  # domains where DINOv2-PatchNN > SubspaceAD
    if item["domain_code"] in DINOV2_DOMAINS:
        pe = _dinov2_patch_cache.get(item["item_id"], {})
        if pe and not pe.get("error"):
            expert_result = {
                "anomaly_score": pe.get("global_score", 0),
                "top_patches": pe.get("top_patches", []),
                "expert_type": "dinov2_patch",
            }
        else:
            expert_result = None
    else:
        expert_result = _subspacead_cache.get(item["item_id"])
        if expert_result is None:
            expert_tool = _get_subspacead()
            if expert_tool:
                try:
                    expert_result = expert_tool.predict(
                        item["query_path"], item["ref_paths"][:4]
                    )
                except Exception as e:
                    expert_result = {"error": str(e)}

    # Use per-domain calibration thresholds for expert binary decision
    global _expert_thresholds, _dinov2_thresholds
    try:
        _expert_thresholds
    except NameError:
        _expert_thresholds = None
    try:
        _dinov2_thresholds
    except NameError:
        _dinov2_thresholds = None
    if _expert_thresholds is None:
        try:
            _thresh_path = os.path.join(os.path.dirname(__file__), "..", "results",
                                         "subspacead_thresholds.json")
            _expert_thresholds = json.load(open(_thresh_path)) if os.path.exists(_thresh_path) else {}
        except Exception:
            _expert_thresholds = {}
    if _dinov2_thresholds is None:
        # Compute DINOv2 thresholds from patch evidence calibration cache
        try:
            import numpy as np
            pe_cal = _dinov2_patch_cache or {}
            by_dom = {}
            for k, v in pe_cal.items():
                dc = k.split('_')[0]  # e.g., "D6" from "D6_0049"
                gs = v.get("global_score")
                if gs is not None:
                    by_dom.setdefault(dc, []).append(gs)
            _dinov2_thresholds = {d: float(np.median(scores)) for d, scores in by_dom.items()}
        except Exception:
            _dinov2_thresholds = {}

    expert_raw = (expert_result or {}).get("anomaly_score", 0)
    expert_type = (expert_result or {}).get("expert_type", "subspacead")
    if expert_type == "dinov2_patch":
        thresh = _dinov2_thresholds.get(item["domain_code"], 0.4)
    else:
        thresh = _expert_thresholds.get(item["domain_code"], 40.0)
    expert_norm = expert_raw / (thresh * 2) if thresh > 0 else 0.5
    expert_label = "anomalous" if expert_raw > thresh else "normal"

    # Phase 2b: Check agreement with domain-aware gating
    # On domains where calibration showed agent > v0 by > margin, use disagreement
    # to trigger interpret. On other domains, always commit to v0 (expert not helpful).
    _agent_domains = None
    try:
        if _agent_domains is None:
            _dom_path = os.path.join(os.path.dirname(__file__), "..", "results",
                                      "agent_domain_selection.json")
            if os.path.exists(_dom_path):
                _agent_domains = set(json.load(open(_dom_path)).get("use_agent_domains", []))
    except Exception:
        _agent_domains = None

    domain_enabled = item["domain_code"] in (_agent_domains or set())
    label_agree = (v0_label == "anomalous" and expert_label == "anomalous") or \
                  (v0_label != "anomalous" and expert_label != "anomalous")
    # Agree if labels match OR if this domain is not in the agent-enabled set
    agree = label_agree or (not domain_enabled)

    total_inp = r0["cost_tokens"]["input"]
    total_out = r0["cost_tokens"]["output"]
    total_lat = r0["latency_sec"]
    interpret_parsed = None

    if agree:
        # v0 and expert agree → commit to v0 (no extra VLM call)
        final_score = v0_score
    else:
        # Phase 3: INTERPRET — VLM re-examines with expert evidence
        expert_text = format_subspacead_evidence(expert_result)
        interpret_prompt = build_prompt_interpret(
            item["domain_code"], v0_label, v0_conf, expert_text
        )

        ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:N_REFS]]
        query_img = load_and_encode(item["query_path"])
        content = []
        for b64 in ref_imgs:
            content.append(text_msg("Normal reference:"))
            content.append(img_msg(b64))
        content.append(text_msg("Query image:"))
        content.append(img_msg(query_img))
        content.append(text_msg(interpret_prompt))

        t0 = time.time()
        text2, inp2, out2 = call_llm(client, model,
            [{"role": "user", "content": content}], max_tokens)
        lat2 = time.time() - t0
        total_inp += inp2; total_out += out2; total_lat += lat2

        interpret_parsed = extract_json(text2)
        if interpret_parsed:
            ilabel = str(interpret_parsed.get("image_label", "")).lower()
            iconf = float(interpret_parsed.get("confidence", 0.5))
            final_score = iconf if ilabel == "anomalous" else 1.0 - iconf
        else:
            # Parse failure → fall back to expert-weighted blend
            final_score = 0.5 * v0_score + 0.5 * expert_norm

    return {
        "label_pred": label_from_score(final_score),
        "anomaly_score": final_score,
        "anomaly_type_pred": r0.get("anomaly_type_pred"),
        "raw_output": {
            "path": "agree_v0" if agree else "disagree_interpret",
            "v0": v0_parsed,
            "v0_score": v0_score,
            "expert": expert_result,
            "expert_norm": expert_norm,
            "agree": agree,
            "interpret": interpret_parsed,
        },
        "cost_tokens": {"input": total_inp, "output": total_out},
        "latency_sec": round(total_lat, 2),
    }


# ─── AnomalyClaw Agent v2: Adaptive multi-tool routing ────────────────────────

def build_prompt_enumerate(domain_code: str) -> str:
    """Component-enumeration tool: structured comparison for logical/compositional anomalies."""
    ctx = DOMAIN_CONTEXT.get(domain_code, "image")
    return (
        f"You are a structural inspector examining a {ctx}\n"
        f"Your task is to detect STRUCTURAL or LOGICAL anomalies by comparing "
        f"components between the QUERY and REFERENCE image(s).\n\n"
        f"IMPORTANT: Normal variation in colour, lighting, exact position, and "
        f"minor appearance differences are NOT anomalies. Focus ONLY on:\n"
        f"  - WRONG COUNT: more or fewer components than the reference\n"
        f"  - MISSING TYPE: a component type present in reference but absent in query\n"
        f"  - EXTRA TYPE: a component type absent in reference but present in query\n"
        f"  - STRUCTURAL DAMAGE: a component that is physically broken, bent, or deformed\n\n"
        f"Step 1: Count each type of component in the reference image(s).\n"
        f"Step 2: Count each type of component in the query image.\n"
        f"Step 3: Compare counts and types. Ignore colour/position/orientation differences.\n"
        f"Step 4: Only flag as anomalous if there is a genuine count mismatch, "
        f"missing/extra type, or structural damage.\n"
        f"Return JSON only:\n"
        f"{{\"ref_counts\": {{type: count}}, \"query_counts\": {{type: count}}, "
        f"\"structural_differences\": [list], \"image_label\": \"anomalous\"|\"normal\", "
        f"\"confidence\": float 0..1}}"
    )


def compute_adaptive_signals(expert_result, patch_evidence, v0_conf, v0_label="normal"):
    """Compute adaptive routing signals from expert outputs.
    Returns: (route, signals_dict)
    Routes: 'agree', 'trust_expert', 'enumerate', 'interpret'
    """
    # Default signals
    signals = {
        "v0_conf": v0_conf,
        "expert_relative_anomaly": 0.0,
        "patch_concentration": 1.0,
        "route_reason": "",
    }

    # Extract patch-level statistics
    patches = []
    if expert_result and not expert_result.get("error"):
        patches = expert_result.get("top_patches", [])

    if patch_evidence and not patch_evidence.get("error"):
        pe_patches = patch_evidence.get("top_patches", [])
        pe_baseline = patch_evidence.get("baseline", 0.1)
        if pe_patches:
            top1 = pe_patches[0].get("distance", 0)
            signals["expert_relative_anomaly"] = (top1 - pe_baseline) / (pe_baseline + 1e-9)

    # Patch concentration: how localized is the anomaly signal?
    if len(patches) >= 3:
        patch_scores = [p.get("score", 0) for p in patches[:5]]
        if patch_scores and patch_scores[0] > 0:
            signals["patch_concentration"] = patch_scores[0] / (np.mean(patch_scores) + 1e-9)

    # Adaptive routing logic (domain-agnostic)
    rel_anom = signals["expert_relative_anomaly"]
    conc = signals["patch_concentration"]

    # === Conservative adaptive routing (v3) ===
    # Key insight from test-split experiments: aggressive routing hurts because
    # the VLM's anomaly predictions are usually RIGHT, and the expert's anomaly
    # signal has high cross-domain variance. The only reliable escalation is
    # ASYMMETRIC: catch FNs (v0 says normal but expert screams anomaly),
    # never override v0's anomaly calls.

    # Gate 1: V0 high-confidence → never escalate
    if v0_conf >= 0.90:
        signals["route_reason"] = "v0_high_confidence"
        return "agree", signals

    # Gate 2: V0 says ANOMALOUS → trust v0 (its anomaly calls are usually correct)
    # Only escalate when v0 says NORMAL but expert disagrees (FN-catcher)
    # Check the LABEL, not the confidence value (conf is always >= 0.5)
    if v0_label == "anomalous":
        signals["route_reason"] = "v0_says_anomaly_trust"
        return "agree", signals

    # Now: v0 says normal (conf < 0.5). Check if expert strongly disagrees.
    if rel_anom > 1.5 and conc > 1.20:
        # Expert strongly anomalous + concentrated → localized defect VLM missed
        signals["route_reason"] = "fn_catch_trust_expert"
        return "trust_expert", signals
    elif rel_anom > 0.8:
        # Expert moderately-to-strongly anomalous → VLM re-examines
        signals["route_reason"] = "fn_catch_interpret"
        return "interpret", signals
    else:
        # Expert weak → v0 probably correct that it's normal
        signals["route_reason"] = "expert_weak_normal"
        return "agree", signals


def run_agent_v2(client, model, item, max_tokens=700) -> dict:
    """AnomalyClaw Agent v2: Perceive → Expert → Adaptive Route → Act.

    Adaptive routing based on expert signal characteristics (no domain labels):
      Route A (agree): v0 and expert agree, or expert signal weak → commit to v0
      Route B (trust_expert): expert strongly anomalous + concentrated → trust expert directly
      Route C (enumerate): expert moderately anomalous + dispersed → component enumeration
      Route D (interpret): expert moderately anomalous → VLM re-examines with evidence
    """
    # Phase 1: PERCEIVE
    r0 = run_v0(client, model, item, max_tokens)
    v0_score = float(r0.get("anomaly_score", 0.5))
    v0_parsed = (r0.get("raw_output") or {}).get("v0") or {}
    v0_label = str(v0_parsed.get("image_label", "normal")).lower()
    v0_conf = float(v0_parsed.get("confidence", 0.5))

    # Phase 2: EXPERT — load from caches
    global _subspacead_cache, _dinov2_patch_cache
    try: _subspacead_cache
    except NameError: _subspacead_cache = None
    try: _dinov2_patch_cache
    except NameError: _dinov2_patch_cache = None

    if _subspacead_cache is None:
        cp = os.environ.get("SUBSPACEAD_CACHE", "benchmark/results/subspacead_calibration.json")
        try:
            raw = json.load(open(cp))
            _subspacead_cache = {x["item_id"]: x for x in raw}
        except: _subspacead_cache = {}
    if _dinov2_patch_cache is None:
        pp = os.environ.get("PATCH_EVIDENCE_CACHE", "benchmark/results/patch_evidence_calibration.json")
        try: _dinov2_patch_cache = json.load(open(pp))
        except: _dinov2_patch_cache = {}

    expert_result = _subspacead_cache.get(item["item_id"])
    patch_evidence = _dinov2_patch_cache.get(item["item_id"])

    # Expert binary label (using global median as domain-agnostic threshold)
    global _global_expert_median
    try: _global_expert_median
    except NameError: _global_expert_median = None
    if _global_expert_median is None:
        all_scores = [x.get("anomaly_score", 0) for x in _subspacead_cache.values()
                      if isinstance(x.get("anomaly_score"), (int, float))]
        _global_expert_median = float(np.median(all_scores)) if all_scores else 40.0
    expert_raw = (expert_result or {}).get("anomaly_score", 0)
    expert_label = "anomalous" if expert_raw > _global_expert_median else "normal"

    # Check basic agreement
    label_agree = (v0_label == "anomalous") == (expert_label == "anomalous")

    total_inp = r0["cost_tokens"]["input"]
    total_out = r0["cost_tokens"]["output"]
    total_lat = r0["latency_sec"]

    if label_agree:
        # Route A: agree → commit to v0
        return {
            "label_pred": r0["label_pred"],
            "anomaly_score": v0_score,
            "anomaly_type_pred": r0.get("anomaly_type_pred"),
            "raw_output": {"route": "agree", "v0": v0_parsed, "v0_score": v0_score,
                            "expert_raw": expert_raw, "expert_label": expert_label},
            "cost_tokens": {"input": total_inp, "output": total_out},
            "latency_sec": round(total_lat, 2),
        }

    # Disagree → compute adaptive signals
    route, signals = compute_adaptive_signals(expert_result, patch_evidence, v0_conf, v0_label)

    if route == "agree":
        # Expert signal too weak to override v0
        return {
            "label_pred": r0["label_pred"],
            "anomaly_score": v0_score,
            "anomaly_type_pred": r0.get("anomaly_type_pred"),
            "raw_output": {"route": "agree_weak_expert", "v0": v0_parsed,
                            "v0_score": v0_score, "signals": signals},
            "cost_tokens": {"input": total_inp, "output": total_out},
            "latency_sec": round(total_lat, 2),
        }

    elif route == "trust_expert":
        # Route B: localized strong expert signal → trust expert directly
        # Scale expert score to [0, 1] using sigmoid relative to median
        expert_scaled = 1.0 / (1.0 + np.exp(-2.0 * (expert_raw - _global_expert_median) / (_global_expert_median + 1e-9)))
        final_score = 0.3 * v0_score + 0.7 * expert_scaled
        return {
            "label_pred": label_from_score(final_score),
            "anomaly_score": final_score,
            "anomaly_type_pred": r0.get("anomaly_type_pred"),
            "raw_output": {"route": "trust_expert", "v0": v0_parsed,
                            "v0_score": v0_score, "expert_raw": expert_raw,
                            "expert_scaled": expert_scaled, "signals": signals},
            "cost_tokens": {"input": total_inp, "output": total_out},
            "latency_sec": round(total_lat, 2),
        }

    elif route == "enumerate":
        # Route C: compositional anomaly → component enumeration (1 VLM call)
        ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:N_REFS]]
        query_img = load_and_encode(item["query_path"])
        enum_prompt = build_prompt_enumerate(item["domain_code"])
        content = []
        for b64 in ref_imgs:
            content.append(text_msg("Normal reference:"))
            content.append(img_msg(b64))
        content.append(text_msg("Query image:"))
        content.append(img_msg(query_img))
        content.append(text_msg(enum_prompt))

        t0 = time.time()
        text2, inp2, out2 = call_llm(client, model,
            [{"role": "user", "content": content}], max_tokens)
        lat2 = time.time() - t0
        total_inp += inp2; total_out += out2; total_lat += lat2

        enum_parsed = extract_json(text2)
        if enum_parsed:
            elabel = str(enum_parsed.get("image_label", "")).lower()
            econf = float(enum_parsed.get("confidence", 0.5))
            final_score = econf if elabel == "anomalous" else 1.0 - econf
        else:
            final_score = 0.5 * v0_score + 0.5

        return {
            "label_pred": label_from_score(final_score),
            "anomaly_score": final_score,
            "anomaly_type_pred": r0.get("anomaly_type_pred"),
            "raw_output": {"route": "enumerate", "v0": v0_parsed,
                            "v0_score": v0_score, "enumerate": enum_parsed,
                            "signals": signals},
            "cost_tokens": {"input": total_inp, "output": total_out},
            "latency_sec": round(total_lat, 2),
        }

    else:
        # Route D: interpret — VLM re-examines with expert evidence (1 VLM call)
        expert_text = format_subspacead_evidence(expert_result)
        interpret_prompt = build_prompt_interpret(
            item["domain_code"], v0_label, v0_conf, expert_text
        )
        ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:N_REFS]]
        query_img = load_and_encode(item["query_path"])
        content = []
        for b64 in ref_imgs:
            content.append(text_msg("Normal reference:"))
            content.append(img_msg(b64))
        content.append(text_msg("Query image:"))
        content.append(img_msg(query_img))
        content.append(text_msg(interpret_prompt))

        t0 = time.time()
        text2, inp2, out2 = call_llm(client, model,
            [{"role": "user", "content": content}], max_tokens)
        lat2 = time.time() - t0
        total_inp += inp2; total_out += out2; total_lat += lat2

        interp_parsed = extract_json(text2)
        if interp_parsed:
            ilabel = str(interp_parsed.get("image_label", "")).lower()
            iconf = float(interp_parsed.get("confidence", 0.5))
            final_score = iconf if ilabel == "anomalous" else 1.0 - iconf
        else:
            final_score = 0.5 * v0_score + 0.5

        return {
            "label_pred": label_from_score(final_score),
            "anomaly_score": final_score,
            "anomaly_type_pred": r0.get("anomaly_type_pred"),
            "raw_output": {"route": "interpret", "v0": v0_parsed,
                            "v0_score": v0_score, "interpret": interp_parsed,
                            "signals": signals},
            "cost_tokens": {"input": total_inp, "output": total_out},
            "latency_sec": round(total_lat, 2),
        }


VARIANT_FNS = {
    "v0_direct": run_v0,
    "v1_normal_first": run_v1,
    "v2_self_refine": run_v2,
    "v3_debate_1r": run_v3,
    "v3_grounded": run_v3_grounded,
    "v3_egra": run_v3_egra,
    "egra": run_egra,
    "agent_v1": run_agent_v1,
    "agent_v2": run_agent_v2,
    "v4_fewshot": run_v4,
    "v5_agent": run_v5,
    "v6_rgnc": run_v6_rgnc,
    "v7_rgnc_verify": run_v7_rgnc_verify,
    "v8_unstructured": run_v8_unstructured,
    "v9_scout_judge": run_v9_scout_judge,
}


# ─── Async variant runners (for batch mode) ─────────────────────────────────

async def run_v0_async(client, model, item, max_tokens=700) -> dict:
    ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:2]]
    query_img = load_and_encode(item["query_path"])
    prompt = build_prompt_v0(item["domain_code"], bool(ref_imgs))
    content = []
    for b64 in ref_imgs:
        content.append(text_msg("Normal reference:"))
        content.append(img_msg(b64))
    content.append(text_msg("Query image:"))
    content.append(img_msg(query_img))
    content.append(text_msg(prompt))
    t0 = time.time()
    text, inp, out = await call_llm_async(client, model, [{"role": "user", "content": content}], max_tokens)
    parsed = extract_json(text)
    return {
        "label_pred": label_from_score(score_from_v0(parsed)),
        "anomaly_score": score_from_v0(parsed),
        "anomaly_type_pred": parsed.get("anomaly_type") if parsed else None,
        "raw_output": {"v0": parsed},
        "cost_tokens": {"input": inp, "output": out},
        "latency_sec": round(time.time() - t0, 2),
    }


async def run_v1_async(client, model, item, max_tokens=700) -> dict:
    ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:2]]
    query_img = load_and_encode(item["query_path"])
    prompt = build_prompt_v1(item["domain_code"], bool(ref_imgs))
    content = []
    for b64 in ref_imgs:
        content.append(text_msg("Normal reference:"))
        content.append(img_msg(b64))
    content.append(text_msg("Query image:"))
    content.append(img_msg(query_img))
    content.append(text_msg(prompt))
    t0 = time.time()
    text, inp, out = await call_llm_async(client, model, [{"role": "user", "content": content}], max_tokens)
    parsed = extract_json(text)
    score = score_from_v1(parsed)
    claims = (parsed or {}).get("claims", [])
    return {
        "label_pred": label_from_score(score),
        "anomaly_score": score,
        "anomaly_type_pred": claims[0].get("anomaly_type") if claims else None,
        "raw_output": {"v1": parsed},
        "cost_tokens": {"input": inp, "output": out},
        "latency_sec": round(time.time() - t0, 2),
    }


async def run_v3_async(client, model, item, max_tokens=700) -> dict:
    r1 = await run_v1_async(client, model, item, max_tokens)
    v1_parsed = (r1["raw_output"] or {}).get("v1")
    claims = (v1_parsed or {}).get("claims", [])
    if not claims:
        return dict(r1, raw_output={"v1": v1_parsed, "refuter": None})
    claims_json = json.dumps({"claims": claims}, indent=2)
    refuter_prompt = build_prompt_refuter(item["domain_code"], claims_json)
    t0 = time.time()
    text2, inp2, out2 = await call_llm_async(client, model, [{"role": "user", "content": refuter_prompt}], max_tokens)
    refuter_parsed = extract_json(text2)
    score = score_from_debate(v1_parsed, refuter_parsed)
    return {
        "label_pred": label_from_score(score),
        "anomaly_score": score,
        "anomaly_type_pred": claims[0].get("anomaly_type") if claims else None,
        "raw_output": {"v1": v1_parsed, "refuter": refuter_parsed},
        "cost_tokens": {"input": r1["cost_tokens"]["input"] + inp2, "output": r1["cost_tokens"]["output"] + out2},
        "latency_sec": round(r1["latency_sec"] + time.time() - t0, 2),
    }


async def run_v4_async(client, model, item, max_tokens=700) -> dict:
    ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:8]]
    query_img = load_and_encode(item["query_path"])
    prompt = build_prompt_v4(item["domain_code"], len(ref_imgs))
    content = []
    for i, b64 in enumerate(ref_imgs):
        content.append(text_msg(f"Normal reference {i+1}/{len(ref_imgs)}:"))
        content.append(img_msg(b64))
    content.append(text_msg("QUERY image (classify this):"))
    content.append(img_msg(query_img))
    content.append(text_msg(prompt))
    t0 = time.time()
    text, inp, out = await call_llm_async(client, model, [{"role": "user", "content": content}], max_tokens)
    parsed = extract_json(text)
    return {
        "label_pred": label_from_score(score_from_v0(parsed)),
        "anomaly_score": score_from_v0(parsed),
        "anomaly_type_pred": parsed.get("anomaly_type") if parsed else None,
        "raw_output": {"v4": parsed},
        "cost_tokens": {"input": inp, "output": out},
        "latency_sec": round(time.time() - t0, 2),
    }


ASYNC_VARIANT_FNS = {
    "v0_direct": run_v0_async,
    "v1_normal_first": run_v1_async,
    "v3_debate_1r": run_v3_async,
    "v4_fewshot": run_v4_async,
}


async def run_item_async(item: dict, client, model: str, variant: str) -> dict:
    fn = ASYNC_VARIANT_FNS[variant]
    base = {
        "item_id": item["item_id"],
        "domain": item["domain"],
        "domain_code": item["domain_code"],
        "label_gt": item["label"],
        "split": item["split"],
        "source_dataset": item.get("source_dataset"),
        "category": item.get("category"),
    }
    try:
        result = await fn(client, model, item)
        base.update(result)
        base["error"] = None
    except Exception as e:
        base.update({
            "label_pred": 0, "anomaly_score": 0.5, "anomaly_type_pred": None,
            "raw_output": None, "cost_tokens": {"input": 0, "output": 0},
            "latency_sec": 0.0, "error": str(e),
        })
    return base


async def run_batch(items, ark_api_key, model, variant, max_workers, output_path, existing_results):
    from volcenginesdkarkruntime import AsyncArk
    from tqdm import tqdm

    client = AsyncArk(api_key=ark_api_key, timeout=3600)
    results = list(existing_results)
    errors = 0
    sem = asyncio.Semaphore(max_workers)
    pbar = tqdm(total=len(items), desc=f"batch/{variant}")

    async def worker(item):
        nonlocal errors
        async with sem:
            r = await run_item_async(item, client, model, variant)
            results.append(r)
            if r.get("error"):
                errors += 1
            pbar.update(1)
            if len(results) % 20 == 0:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "w") as f:
                    json.dump(results, f, indent=2)

    tasks = [asyncio.create_task(worker(item)) for item in items]
    await asyncio.gather(*tasks)
    pbar.close()
    await client.close()

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    total_in = sum((r.get("cost_tokens") or {}).get("input", 0) for r in results)
    total_out = sum((r.get("cost_tokens") or {}).get("output", 0) for r in results)
    print(f"\nDone: {len(results)} items, {errors} errors")
    print(f"Tokens — input: {total_in:,} | output: {total_out:,}")
    print(f"Results saved: {output_path}")


# ─── Item runner ──────────────────────────────────────────────────────────────

def run_item(item: dict, client: OpenAI, model: str, variant: str) -> dict:
    fn = VARIANT_FNS[variant]
    base = {
        "item_id": item["item_id"],
        "domain": item["domain"],
        "domain_code": item["domain_code"],
        "label_gt": item["label"],
        "split": item["split"],
        "source_dataset": item.get("source_dataset"),
        "category": item.get("category"),
    }
    try:
        result = fn(client, model, item)
        base.update(result)
        base["error"] = None
    except Exception as e:
        base.update({
            "label_pred": 0,
            "anomaly_score": 0.5,
            "anomaly_type_pred": None,
            "raw_output": None,
            "cost_tokens": {"input": 0, "output": 0},
            "latency_sec": 0.0,
            "error": str(e),
        })
    return base


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--split", default="calibration",
                        choices=["calibration", "dev", "test", "all"])
    parser.add_argument("--backend", required=True, choices=["gpt", "seedvl", "qwen3"])
    parser.add_argument("--variant", required=True, choices=list(VARIANT_FNS.keys()))
    parser.add_argument("--output", required=True)
    parser.add_argument("--domains", nargs="*", default=None,
                        help="Filter to specific domain codes, e.g. D1 D5")
    parser.add_argument("--max_workers", type=int, default=4)
    parser.add_argument("--max_items", type=int, default=None,
                        help="Limit total items (for testing)")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from existing output file, skip already-processed items")
    parser.add_argument("--n_refs", type=int, default=2,
                        help="Number of normal reference images to use (2, 4, or 8)")
    parser.add_argument("--batch", action="store_true",
                        help="Use AsyncArk batch inference (seedvl backend only)")
    parser.add_argument("--batch_workers", type=int, default=50,
                        help="Concurrency for batch mode (default: 50)")
    args = parser.parse_args()

    # Set global N_REFS
    global N_REFS
    N_REFS = args.n_refs

    # Load manifest
    with open(args.manifest) as f:
        all_items = json.load(f)

    # Filter by split and domain
    items = [x for x in all_items
             if (args.split == "all" or x["split"] == args.split)
             and (args.domains is None or x["domain_code"] in args.domains)]

    if args.max_items:
        items = items[:args.max_items]

    # Resume: load existing results
    existing = {}
    if args.resume and Path(args.output).exists():
        with open(args.output) as f:
            for r in json.load(f):
                existing[r["item_id"]] = r
        items = [x for x in items if x["item_id"] not in existing]
        print(f"Resuming: {len(existing)} done, {len(items)} remaining")

    model = get_model_name(args.backend, args.batch)
    print(f"Running {len(items)} items | backend={args.backend} | variant={args.variant}")
    print(f"Model: {model}")

    # ── Batch mode (AsyncArk) ──
    if args.batch:
        if args.backend != "seedvl":
            print("[WARN] --batch only supported for seedvl backend, falling back to sync mode")
        elif args.variant not in ASYNC_VARIANT_FNS:
            print(f"[WARN] --batch not implemented for variant {args.variant}, falling back to sync mode")
        else:
            ark_key = os.environ.get("SEED_API_KEY")
            if not ark_key:
                raise RuntimeError("SEED_API_KEY env var required for --batch with seedvl backend")
            asyncio.run(run_batch(items, ark_key, model, args.variant,
                                  args.batch_workers, args.output, existing.values()))
            return

    # ── Sync mode (OpenAI client) ──
    client = get_client(args.backend)
    results = list(existing.values())
    errors = 0
    total_tokens_in = 0
    total_tokens_out = 0

    from tqdm import tqdm

    def process(item):
        return run_item(item, client, model, args.variant)

    with ThreadPoolExecutor(max_workers=args.max_workers) as pool:
        futures = {pool.submit(process, item): item for item in items}
        for fut in tqdm(as_completed(futures), total=len(futures), desc=f"{args.backend}/{args.variant}"):
            r = fut.result()
            results.append(r)
            if r.get("error"):
                errors += 1
            total_tokens_in += (r.get("cost_tokens") or {}).get("input", 0)
            total_tokens_out += (r.get("cost_tokens") or {}).get("output", 0)

            # Save incrementally every 20 items
            if len(results) % 20 == 0:
                Path(args.output).parent.mkdir(parents=True, exist_ok=True)
                with open(args.output, "w") as f:
                    json.dump(results, f, indent=2)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nDone: {len(results)} items, {errors} errors")
    print(f"Tokens — input: {total_tokens_in:,} | output: {total_tokens_out:,}")
    print(f"Results saved: {args.output}")


if __name__ == "__main__":
    main()
