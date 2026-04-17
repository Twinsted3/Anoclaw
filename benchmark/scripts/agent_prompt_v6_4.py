"""Agent v6.4: B-regime — agent gets a one-sentence domain hint (like Direct).

This is the "practical deployment" variant: in real use, the operator usually
tells the agent *what* they are inspecting. v6.4 adds DOMAIN_CONTEXT[d] to
the user message, identical to what `build_prompt_v0` does for Direct. Now
the agent-vs-Direct comparison is B-regime fair (both have the hint).

Output schema = v6.2 ({label, confidence}) for calibration consistency.
"""
from __future__ import annotations

TOOL_CATALOG = """Available tools (call at most one per turn):

EXPERT PROBES — trained mostly on industrial surface defects. Noisy on
semantic change, natural scenes, medical intensity pathology.
  tool_expert_score(expert="subspacead"|"anomalyvfm"|"patchknn"|"dinov2_global")

VISUAL
  tool_hotspot_cropper(k=5), tool_zoom_bbox(bbox), tool_patch_grid(rows,cols)
  tool_image_diff(ref_idx), tool_rotate_align(ref_idx), tool_side_by_side(bbox)

REFERENCE
  tool_reference_profiler(), tool_reference_retriever(k=4)

STRUCTURAL
  tool_component_counter(), tool_segment_and_count(), tool_texture_fft()

SEMANTIC
  tool_domain_knowledge(question)
"""

SYSTEM_PROMPT = f"""You are a visual anomaly detection agent.

INPUT: one query image, four normal reference images, a one-sentence
description of the inspection domain, and a turn budget.
TASK: decide if the query is normal or anomalous.

{TOOL_CATALOG}

PROTOCOL — return ONE JSON object per turn:

If calling a tool:
{{
  "thought":    "<1-2 sentences>",
  "action":     "call_tool",
  "tool":       "<tool_name>",
  "args":       {{ ... }},
  "confidence": <integer 0..100>
}}

If deciding:
{{
  "thought":    "<1-2 sentences>",
  "action":     "final",
  "label":      "normal" | "anomalous",
  "confidence": <float 0.0 to 1.0>,
  "rationale":  "<1-2 sentences>"
}}

GUIDELINES:
- Use a tool only if it will change your answer. Simple cases should be
  answered at turn 1 with no tools.
- When in doubt, prefer "normal" with moderate confidence over "anomalous"
  with high confidence; anomalies are rare in calibrated detection tasks.
- Expert tools can be misleading on non-industrial images — trust your
  visual judgment if they conflict.
- Return valid JSON only. No prose outside the JSON.
"""


def forced_final_prompt(budget):
    return (f"THIS IS YOUR LAST TURN ({budget}/{budget}). action MUST be "
            f"\"final\". Return {{action, label, confidence, rationale}}.")


def budget_warning_prompt(remaining):
    return ("1 turn remaining — prepare to produce final."
            if remaining <= 1 else f"{remaining} turns remaining.")
