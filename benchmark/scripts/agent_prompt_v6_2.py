"""Agent v6.2 prompt: keep v6 behavior, but output label+confidence so we
can use Direct's score_from_v0 mapping for consistent calibration.

Key change: final JSON has {label: "normal"|"anomalous", confidence: 0..1}
(identical to Direct), no self-reported "score". Score is derived via the
same monotone rule as the baselines.
"""
from __future__ import annotations

TOOL_CATALOG = """Available tools (call at most one per turn):

EXPERT PROBES — note: trained mostly on industrial surface-defect data.
  They tend to be noisy on: semantic change detection between two scenes,
  natural imagery where anomaly is context-based, medical intensity-based
  pathology. Use them on images that look like manufactured industrial
  objects; be skeptical otherwise.

  tool_expert_score(expert="subspacead"|"anomalyvfm"|"patchknn"|"dinov2_global")
    Returns {score, normalized_rank, interpretation, top_patches}.
    rank>=0.80 means strong anomaly signal (for industrial-like content).

VISUAL INSPECTION
  tool_hotspot_cropper(k=5): zoom top-k subspacead hotspots. Needs prior expert_score.
  tool_zoom_bbox(bbox=[x0,y0,x1,y1]): pixel-level crop you specify.
  tool_patch_grid(rows=N, cols=M): N x M grid tiles (max 8 x 8).
  tool_image_diff(ref_idx=0..3): aligned diff vs ref. GOOD for before/after change detection.
  tool_rotate_align(ref_idx=0..3): try rotations then diff.
  tool_side_by_side(bbox): query + 4 refs cropped to same bbox.

REFERENCE
  tool_reference_profiler(): VLM describes what the refs have in common.
  tool_reference_retriever(k=4): re-pull similar refs from normal pool.

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

PROTOCOL: On each turn, return ONLY a JSON object:

If you want to call a tool:
{{
  "thought":   "<one or two sentences>",
  "action":    "call_tool",
  "tool":      "<tool_name>",
  "args":      {{ ... }},
  "confidence": <integer 0..100>
}}

If you are ready to decide:
{{
  "thought":   "<one or two sentences>",
  "action":    "final",
  "label":     "normal" | "anomalous",
  "confidence": <float 0.0 to 1.0 — how sure you are of this label>,
  "rationale": "<one or two sentences>"
}}

GUIDELINES:
- Use a tool only if it will change your answer. If the query already looks
  clearly normal or clearly anomalous against the refs, output final at
  turn 1 without calling any tool.
- Each tool call costs one turn. Budget is tight.
- If a tool result contradicts your visual judgment on a non-industrial image,
  trust your visual judgment — the tool may not fit that image type.
- Return valid JSON only. No prose outside the JSON.
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
