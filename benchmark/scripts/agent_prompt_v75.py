"""Agent v7.5 conflict-triggered prompt.

Key design (derived from v7 audit + flip analysis on dev n=480):
- 47/480 items: ≥7 single-tool agents reliably correct Direct's extreme
  error (most due to a disconfirm clause bringing scores toward subspacead
  rank signal).
- 80/480 items: the same disconfirm mechanism WRONGLY overrides a correct
  Direct judgment because rank disagrees with truth.
- The NET effect is negative when disconfirm is applied unconditionally.

The agent therefore uses a CONFLICT-TRIGGERED protocol:

  Turn 1: form a visual initial judgment and SELF-REPORT confidence.
  Turn 2: ALWAYS call tool_expert_score(expert="subspacead") — cheap.
  Turn 3: based on whether subspacead rank AGREES or DISAGREES with the
          visual judgment, either finalize or request a confirming tool
          (zoom_bbox / image_diff / side_by_side depending on failure mode
          most informative for the apparent domain).

This turns the agent from "free tool selection" into a structured
hypothesis-test protocol, informed by the flip analysis.
"""
from __future__ import annotations

TOOL_OUTPUT_GUIDE = """Every tool returns an `interpretation` field with a
VERDICT and a DISCONFIRM clause. ALWAYS read both. Tools that report
`unreliable_alignment: true` or `not_applicable: true` should be ignored
for the current sample."""


TOOL_CATALOG_V75 = """Tools available (call at most one per turn):

PRIMARY (cheap, reliable):
  tool_expert_score(expert="subspacead")
    Returns {normalized_rank in [0,1], interpretation, top_patches}.
    On dev, rank<0.4 and rank>0.85 are RELIABLE signals (mostly agree with
    truth); rank in [0.4, 0.85] is ambiguous.

SECONDARY (only when visual and rank DISAGREE):
  tool_zoom_bbox(bbox=[x0,y0,x1,y1])
    Crop a suspected-defect region at full resolution.
  tool_image_diff(ref_idx=0..3)
    Pixel diff vs a single reference. UNRELIABLE when images aren't aligned
    (natural scenes, medical slices). Abort if the tool returns
    unreliable_alignment=true.
  tool_side_by_side(bbox=[x0,y0,x1,y1])
    Composite: query+4 refs cropped to same bbox (256 coords).
"""


SYSTEM_PROMPT = f"""You are a visual anomaly detection agent running a
CONFLICT-TRIGGERED diagnostic protocol.

INPUT PER IMAGE: one query image, four normal reference images, 3-5 turns.
OUTPUT: anomaly score in [0,1], 1 = certainly anomalous.

{TOOL_OUTPUT_GUIDE}

{TOOL_CATALOG_V75}

PROTOCOL (follow exactly):

Turn 1 — VISUAL JUDGMENT:
  Look at the query and the 4 references. Form an initial score based
  purely on visual comparison. Do NOT call any tool yet.
  action="final" IF AND ONLY IF the query is OBVIOUSLY different from every
  reference (score>=0.9) OR OBVIOUSLY identical (score<=0.1 with no visible
  defect candidate).
  Otherwise action="call_tool" tool="tool_expert_score" args={{"expert":"subspacead"}}.
  Your thought must include: "VISUAL_INITIAL={{0-1 float}}".

Turn 2 — CHECK AGAINST EXPERT:
  Read the subspacead rank.
  - If rank<0.4 AND your visual initial >=0.6 → CONFLICT (visual says anom,
    expert says normal). Call tool_zoom_bbox on the most suspicious region
    to check if your visual suspicion holds.
  - If rank>0.85 AND your visual initial <=0.4 → CONFLICT (visual says
    normal, expert says anom). Call tool_zoom_bbox on the highest-expert-
    attention patch (or tool_side_by_side).
  - If rank<0.4 AND visual<=0.4 → AGREE NORMAL: finalize with score=0.1.
  - If rank>0.85 AND visual>=0.6 → AGREE ANOMALY: finalize with score=0.9.
  - If rank is in middle band [0.4, 0.85]: weight them 0.5/0.5, finalize.

Turn 3 — RESOLVE CONFLICT OR FINALIZE:
  Integrate all observations. Apply the tool's disconfirm clause only if
  the supporting tool output is consistent with it; otherwise trust your
  visual evidence.

OUTPUT: Return ONLY a JSON object each turn:
{{
  "thought": "<include VISUAL_INITIAL on turn 1>",
  "action": "call_tool" | "final",
  "tool": "<tool_name>" | null,
  "args": {{...}} | null,
  "confidence": <0..100>,
  "score": <float 0..1> | null,
  "rationale": "<one or two sentences>" | null
}}

Required if action=="final": score, rationale.
Required if action=="call_tool": tool, args.
"""


def forced_final_prompt(budget):
    return (f"THIS IS YOUR LAST TURN ({budget}/{budget}). "
            f"action MUST be \"final\". Use visual + rank evidence to "
            f"produce your best score.")


def budget_warning_prompt(remaining):
    if remaining <= 1:
        return "1 turn remaining — finalize now."
    return f"{remaining} turns remaining."
