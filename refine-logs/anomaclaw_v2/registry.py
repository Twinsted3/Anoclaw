"""AnomalyClaw v2 Tool × Expert × Strategy registry.

This module defines the three orthogonal axes of the agent framework. Each entry is a
small, inspectable dataclass — the agent orchestrates them via a VLM router that emits a
JSON plan of the form::

    {
      "tools": ["domain_descriptor", "hotspot_cropper"],
      "expert": "subspacead",
      "strategy": "interpret"
    }

The registry is intentionally minimal (5 tools, 3 experts, 4 strategies) so that a reader
can audit the entire decision space without reading code.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


# ---------------------------------------------------------------------------
# Tools — action primitives the agent can chain before strategy execution.
# Each tool has zero or one VLM call; most are compute-only.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Tool:
    name: str
    summary: str
    inputs: List[str]
    outputs: List[str]
    vlm_calls: int  # 0 or 1
    applies_to: List[str]  # domain family tags


TOOLS: Dict[str, Tool] = {
    "domain_descriptor": Tool(
        name="domain_descriptor",
        summary=(
            "Returns the task-anchored text descriptor for the current domain. "
            "States what counts as normal/anomalous, resolves generic-prior / task "
            "conflicts (e.g. 'planned urbanisation IS the anomaly' for D08)."
        ),
        inputs=["domain_code"],
        outputs=["descriptor_text"],
        vlm_calls=0,
        applies_to=["industrial", "retail", "infrastructure", "medical",
                    "change", "road", "logical"],
    ),
    "reference_retriever": Tool(
        name="reference_retriever",
        summary=(
            "Ranks reference images by DINOv2-CLS cosine similarity to the query. "
            "Returns top-k; used to present the most relevant normals to the VLM "
            "when the pool is large or heterogeneous."
        ),
        inputs=["query_image", "reference_pool"],
        outputs=["top_k_refs"],
        vlm_calls=0,
        applies_to=["industrial", "retail", "medical", "logical"],
    ),
    "hotspot_cropper": Tool(
        name="hotspot_cropper",
        summary=(
            "Reads top-k patch coordinates from the expert and returns a tight crop "
            "around the hotspot (with reference-aligned context). Used to hand "
            "expert-localised evidence to the VLM during the interpret strategy."
        ),
        inputs=["query_image", "expert_patches"],
        outputs=["crop_bbox", "cropped_image"],
        vlm_calls=0,
        applies_to=["industrial", "infrastructure", "medical", "logical"],
    ),
    "component_counter": Tool(
        name="component_counter",
        summary=(
            "Connected-component analysis on the expert hotspot map. Returns "
            "number of components and per-component summary statistics. Used as a "
            "structural prior for logical anomaly domains (e.g. missing/extra parts)."
        ),
        inputs=["expert_hotspot_map"],
        outputs=["num_components", "component_stats"],
        vlm_calls=0,
        applies_to=["logical"],
    ),
    "knowledge_lookup": Tool(
        name="knowledge_lookup",
        summary=(
            "Retrieves domain-specific lexicons for VLM prompts (e.g. 'lesion, "
            "haemorrhage' for medical; 'crack, spalling' for infrastructure). "
            "Grounds the VLM in terminology a generic prompt would miss."
        ),
        inputs=["domain_code"],
        outputs=["keyword_list"],
        vlm_calls=0,
        applies_to=["medical", "infrastructure", "logical"],
    ),
}


# ---------------------------------------------------------------------------
# Experts — pretrained, non-parametric anomaly detectors. Pre-computed and
# cached per benchmark; no expert VLM call during inference.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Expert:
    name: str
    summary: str
    backbone: str
    score_type: str
    strong_on: List[str]
    weak_on: List[str]


EXPERTS: Dict[str, Expert] = {
    "subspacead": Expert(
        name="subspacead",
        summary=(
            "Training-free PCA subspace reconstruction residual on DINOv2-giant "
            "patch tokens (99% EV). Yields a scalar anomaly score and top-k "
            "hotspot patches."
        ),
        backbone="dinov2-giant",
        score_type="reconstruction_residual",
        strong_on=["industrial_texture", "logical", "liver_ct"],
        weak_on=["semantic_change", "gi_endoscopy"],
    ),
    "patchknn": Expert(
        name="patchknn",
        summary=(
            "Patch-level k-nearest-neighbour distance on DINOv2-giant tokens. "
            "Cosine distance from each query patch to its nearest reference "
            "patch; 48x48 grid."
        ),
        backbone="dinov2-giant",
        score_type="patch_distance",
        strong_on=["infrastructure", "dermoscopy"],
        weak_on=["logical", "change"],
    ),
    "dinov2_global": Expert(
        name="dinov2_global",
        summary=(
            "Global CLS-token cosine distance between query and mean reference "
            "embedding. Cheap but coarse; used as a sanity expert."
        ),
        backbone="dinov2-giant",
        score_type="global_distance",
        strong_on=["gi_endoscopy"],
        weak_on=["fine_grained_defects"],
    ),
}


# ---------------------------------------------------------------------------
# Strategies — inference schemes the agent can execute once tools and experts
# have been selected.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Strategy:
    name: str
    summary: str
    vlm_calls: int
    uses_expert: bool


STRATEGIES: Dict[str, Strategy] = {
    "direct": Strategy(
        name="direct",
        summary=(
            "Single-pass VLM call with the task-anchored domain descriptor. "
            "Best for semantic domains where the VLM's world knowledge is the "
            "bottleneck (e.g. road obstacle, GI endoscopy)."
        ),
        vlm_calls=1,
        uses_expert=False,
    ),
    "fusion": Strategy(
        name="fusion",
        summary=(
            "Single VLM call blended with the expert score: "
            "s = 0.8 * v0 + 0.2 * sigmoid((s_exp - m) / m). "
            "Best for texture / few-shot industrial where the expert is "
            "reliably discriminative but the VLM disambiguates borderline cases."
        ),
        vlm_calls=1,
        uses_expert=True,
    ),
    "debate": Strategy(
        name="debate",
        summary=(
            "Proposer-Advocate debate: the VLM first proposes a label with "
            "evidence, then re-examines under an adversarial prompt. The final "
            "score aggregates both. Best when VLM confidence calibration is "
            "unreliable (e.g. small medical anomalies with ambiguous context)."
        ),
        vlm_calls=2,
        uses_expert=False,
    ),
    "interpret": Strategy(
        name="interpret",
        summary=(
            "Asymmetric router: if the VLM says normal and the expert strongly "
            "disagrees on a concentrated hotspot, issue a second VLM call with "
            "the hotspot crop as evidence. Matches AnomalyClaw v1 Route D."
        ),
        vlm_calls=1.3,  # average
        uses_expert=True,
    ),
}


# ---------------------------------------------------------------------------
# Domain family taxonomy — the router uses this to narrow the tool/expert/
# strategy space based on the descriptor.
# ---------------------------------------------------------------------------
DOMAIN_FAMILY: Dict[str, str] = {
    "D1": "industrial",
    "D2": "retail",
    "D3": "infrastructure",
    "D4": "dermoscopy",
    "D5": "medical_mixed",
    "D5b": "brain_mri",
    "D5c": "liver_ct",
    "D5d": "gi_endoscopy",
    "D6": "change",
    "D7": "gi_endoscopy",
    "D8": "road",
    "D9": "road",
    "D10": "logical",
    "D11": "industrial",
    "D12": "industrial_visa",
}


def describe_agent_plan(domain_code: str, plan: Dict[str, object]) -> str:
    """Human-readable trace of an agent plan; used in Appendix examples."""
    lines = [f"Domain={domain_code} ({DOMAIN_FAMILY.get(domain_code, 'unknown')})"]
    lines.append(f"  Tools: {plan.get('tools', [])}")
    lines.append(f"  Expert: {plan.get('expert', '—')}")
    lines.append(f"  Strategy: {plan.get('strategy', '—')}")
    return "\n".join(lines)
