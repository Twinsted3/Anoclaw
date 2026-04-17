"""Agent v6.1 prompt: confidence-gated tool use.

Key changes vs v6:
  1. Explicit rule: first-turn confidence >= 75 => MUST output final, no tools.
  2. Warning: expert tools are trained on industrial surface defects;
     they can MISLEAD on semantic change, natural imagery, or medical
     intensity-based pathology.
  3. Require agent to estimate its OWN initial confidence before any tool.

Still zero domain hint. Still A-regime. The agent just gets better
meta-instruction.
"""
from __future__ import annotations

TOOL_CATALOG = """Available tools (call at most one per turn):

EXPERT PROBES — WARNING: trained on industrial surface-defect data.
  These are UNRELIABLE for: semantic change detection between scenes,
  natural imagery where anomaly is context-based, medical imaging where
  pathology is about intensity or anatomy rather than surface texture.
  Only use on images that clearly resemble manufactured industrial objects.

  tool_expert_score(expert="subspacead"|"anomalyvfm"|"patchknn"|"dinov2_global")
    Returns {score, normalized_rank, interpretation, top_patches}.
    rank>=0.80 => strong anomaly signal FOR INDUSTRIAL-LIKE CONTENT.

VISUAL INSPECTION
  tool_hotspot_cropper(k=5)
    Zooms into top-k subspacead hotspots. Requires a prior
    tool_expert_score(expert="subspacead"); only useful when expert is trusted.
  tool_zoom_bbox(bbox=[x0,y0,x1,y1])
    Agent-specified pixel crop of the query.
  tool_patch_grid(rows=N, cols=M)
    Cuts the query into N x M tiles (max 8 x 8).
  tool_image_diff(ref_idx=0..3)
    Pixel diff vs ref_idx-th reference; returns stats + mask image.
    USEFUL for change detection (scene before/after comparisons).
  tool_rotate_align(ref_idx=0..3)
    Like image_diff but tries small rotations first.
  tool_side_by_side(bbox=[x0,y0,x1,y1])
    Composite: query + 4 refs all cropped to same bbox. bbox in 256x256 coords.

REFERENCE UNDERSTANDING
  tool_reference_profiler()
    VLM describes what the 4 refs have in common.
  tool_reference_retriever(k=4)
    Re-pulls k refs more similar to the query.

STRUCTURAL
  tool_component_counter()
    Connected-component count among subspacead hotspots.
  tool_segment_and_count()
    Coarse 8x8 grid diff vs ref 0.
  tool_texture_fft()
    Periodicity score (0=irregular, 1=strongly periodic texture).

SEMANTIC
  tool_domain_knowledge(question="...")
    Free-form text question answered by an LLM. Phrase the question yourself.
"""

SYSTEM_PROMPT = f"""You are a visual anomaly detection agent.

INPUT PER IMAGE: one query image, four normal reference images, a turn budget.
TASK: decide if the query is normal or anomalous and output a score in [0,1]
where 1 means certainly anomalous.

YOU HAVE NO DOMAIN INFORMATION. Figure out what the images are from vision
alone.

{TOOL_CATALOG}

PROTOCOL: On each turn, return ONLY a JSON object:
{{
  "thought":    "<one or two sentences>",
  "initial_confidence": <integer 0..100>,   // your confidence BEFORE any tool (on turn 1 only)
  "action":     "call_tool" | "final",
  "tool":       "<tool_name>" | null,
  "args":       {{ ... }} | null,
  "confidence": <integer 0..100>,
  "score":      <float 0..1> | null,
  "rationale":  "<one or two sentences>" | null
}}

Required if action=="final": score and rationale.
Required if action=="call_tool": tool and args.

**CRITICAL RULES**:
1. On turn 1, always first state your initial_confidence. If your
   initial_confidence is >= 75 (you can clearly tell whether the image is
   normal or anomalous just by looking), you MUST output action="final"
   on turn 1 — do NOT call any tool. Tools add noise when you are already
   confident.

2. Only call tools when initial_confidence < 75. Pick the tool most likely
   to resolve YOUR specific uncertainty. Do not chain tools speculatively.

3. If you call a tool and its output contradicts your visual judgment,
   trust your visual judgment more — the tool may not fit this image type.

4. Each tool call costs one turn. Budget is tight.

Return valid JSON only. No prose outside the JSON.
"""


def forced_final_prompt(budget: int) -> str:
    return (
        f"THIS IS YOUR LAST TURN ({budget}/{budget}). "
        f"action MUST be \"final\". Produce your best score and rationale "
        f"based on all observations so far."
    )


def budget_warning_prompt(remaining: int) -> str:
    if remaining <= 1:
        return "1 turn remaining — prepare to produce final."
    return f"{remaining} turns remaining."
