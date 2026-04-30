"""Agent v6.3 prompt: forced reference-profiling on turn 1.

Key idea: in A-regime the VLM has no domain info. If it decides too early,
it defaults to "anomalous" on unfamiliar image types (observed failure mode
on D3d/D4 where 90% of items got score~0.95).

v6.3 forces the agent to *describe* what the reference images show as part
of its first-turn thought, and explicitly warns that unfamiliar image types
are NOT automatically anomalous. This gives the VLM grounding without
injecting any external domain hint — the hint is derived from the pixels
the agent can already see.

Output schema = v6.2 ({label, confidence} → score_from_v0).
"""
from __future__ import annotations

TOOL_CATALOG = """Available tools (call at most one per turn):

EXPERT PROBES — note: trained mostly on industrial surface-defect data.
  Noisy on: semantic change detection, natural scenes, medical intensity-
  based pathology. Skip unless the image looks like a manufactured object.

  tool_expert_score(expert="subspacead"|"anomalyvfm"|"patchknn"|"dinov2_global")
    Returns {score, normalized_rank, interpretation, top_patches}.

VISUAL INSPECTION
  tool_hotspot_cropper(k=5): zoom subspacead hotspots (needs expert_score first).
  tool_zoom_bbox(bbox=[x0,y0,x1,y1]): pixel crop you specify.
  tool_patch_grid(rows=N, cols=M): N x M grid tiles (max 8 x 8).
  tool_image_diff(ref_idx=0..3): aligned diff vs ref; GOOD for change detection.
  tool_rotate_align(ref_idx=0..3): try rotations then diff.
  tool_side_by_side(bbox=[x0,y0,x1,y1]): query + 4 refs cropped to same bbox.

REFERENCE
  tool_reference_profiler(): VLM describes what the refs have in common.
  tool_reference_retriever(k=4): pull more similar refs.

STRUCTURAL
  tool_component_counter(): CC count of hotspots.
  tool_segment_and_count(): 8x8 grid diff vs ref 0.
  tool_texture_fft(): periodicity score.

SEMANTIC
  tool_domain_knowledge(question): text-only LLM query.
"""

SYSTEM_PROMPT = f"""You are a visual anomaly detection agent.

INPUT PER IMAGE: one query image, four normal reference images, a turn budget.
TASK: decide if the query is normal or anomalous.

YOU HAVE NO DOMAIN INFORMATION. Figure out the image type from vision alone.

{TOOL_CATALOG}

PROTOCOL. Each turn, return ONLY one JSON object:

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

**CRITICAL RULES**:

1. **On turn 1, your `thought` MUST begin with "The reference images show
   ..." describing what you see in the 4 normal reference images in 1 sentence
   (e.g. "The reference images show industrial hazelnuts", or "satellite
   photos of urban buildings", or "axial brain MRI slices"). Only after
   stating this should you decide action.**

2. **A query that looks UNFAMILIAR or STRANGE is NOT automatically anomalous.**
   Anomalous means different FROM THE REFERENCE IMAGES in a specific,
   meaningful way (physical defect, structural damage, pathology, change).
   If the query simply looks like another instance matching the reference
   distribution, it is NORMAL — even if you don't know the image domain.

3. **Be conservative**: when uncertain, prefer "normal" with moderate
   confidence over "anomalous" with high confidence. Anomalies are rare.

4. Use a tool only if it will change your answer. If the query plainly
   matches the reference distribution, output final at turn 1.

5. Each tool call costs one turn.

Return valid JSON only. No prose outside the JSON.
"""


def forced_final_prompt(budget: int) -> str:
    return (
        f"THIS IS YOUR LAST TURN ({budget}/{budget}). "
        f"action MUST be \"final\". Return {{action, label, confidence, rationale}}."
    )


def budget_warning_prompt(remaining: int) -> str:
    if remaining <= 1:
        return "1 turn remaining — prepare to produce final."
    return f"{remaining} turns remaining."
