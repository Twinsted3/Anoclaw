"""Agent v9 — Unified Task-Aware Agent (extends v8 refutation).

Accepts (image, refs?, question?, options?) and produces unified JSON:
  - anomaly_score (always)
  - mcq_answer (when options present)
  - free_text (when open-ended)

Mode is inferred inside turn 1 — no separate routing LLM call.

Reasoning branches:
  - detection / mcq_binary: v8 refutation protocol unchanged.
  - mcq_choice (4-way): observe → list evidence → match options → pick.
  - open_ended: observe → describe.

Every turn returns a JSON object with the fields needed for its mode
(omitted fields are null).
"""
from __future__ import annotations


TOOL_DESCRIPTIONS = """Tools available (call at most one per turn):

REFUTATION PROBES (detection / binary-AD mode):

  tool_side_by_side(bbox=[x0,y0,x1,y1])
    Composite cropping query+4 refs at the SAME bounding box. Best for
    refuting a localised feature: "at this position, does the feature
    appear in any ref?" bbox in 256x256 normalized coords (0-256).

  tool_zoom_bbox(bbox=[x0,y0,x1,y1])
    Full-resolution crop of ONE region of the query. Use to look more
    carefully. (Does NOT show refs.)

  tool_image_diff(ref_idx=0..3)
    Pixel diff query vs ref N. Returns change_percent and
    unreliable_alignment flag. Ignore if unreliable.

  tool_reference_retriever(k=4)
    Retrieves k nearest normal refs from the domain pool.

  tool_reference_profiler()
    Structured description of what refs share (object / colors /
    allowed variations). Use to check whether a feature is "allowed".

SUPPORTING PROBES:

  tool_expert_score(expert="subspacead")
    Returns normalized_rank. rank<=0.4 ⇒ normal-like, rank>=0.85 ⇒
    anomaly-like.

  tool_hotspot_cropper()
    After tool_expert_score(subspacead), crops the top hotspot patches.

  tool_domain_knowledge(question)
    Targeted text question to an LLM. May hallucinate; cross-check.
"""


SYSTEM_PROMPT = f"""You are AnomalyClaw, a visual reasoning agent
specialised in anomaly detection but able to answer four kinds of tasks:

MODES (inferred from inputs; do NOT ask the user):
  1. `detection`:    refs present, no question.
     → refutation protocol; output anomaly_score.
  2. `mcq_binary`:   refs + question + options like A/B (Yes/No).
     → refutation protocol; output anomaly_score AND mcq_answer.
  3. `mcq_choice`:   question + 4 options A/B/C/D (defect type,
                     location, object class, etc.).
     → observe + match evidence to options; output mcq_answer.
  4. `open_ended`:   question, no options.
     → describe; output free_text.

Every final JSON must contain ALL output fields (use null when NA):
{{
  "mode": "detection|mcq_binary|mcq_choice|open_ended",
  "anomaly_score": <float 0..1>,          // always produced
  "mcq_answer":    "A|B|C|D"|null,
  "free_text":     "<string>"|null,
  "rationale":     "<one or two sentences>",
  "confidence":    0..100,
  "refutation_trace": {{                  // ONLY for detection/mcq_binary
    "initial_score":    <float>|null,
    "candidate_features":[...]|null,
    "remaining_features":[...]|null,
    "refutation_verdicts":[...]|null,
    "updated_score":    <float>|null
  }}
}}

{TOOL_DESCRIPTIONS}

PROTOCOL BY MODE:

========= Mode 1 & 2: detection / mcq_binary (refutation) =========

Turn 1 (no tool):
  Output fields:
    mode: "detection" or "mcq_binary"
    refutation_trace.initial_score: gut anomaly score 0..1
    refutation_trace.candidate_features: list (0..3) of
      {{name, location_hint, looks_defect_like}}
    refutation_target: index into candidate_features (int|null)
  Action:
    - If candidate_features empty AND initial_score<0.3 →
      action="final", anomaly_score=0.05,
      rationale="nothing unusual observed vs refs".
    - Else action="call_tool" with a tool that can REFUTE the target
      feature (i.e. show it in refs).

Turn 2+:
  Output:
    refutation_verdict: "found_in_ref" | "not_found" | "inconclusive"
    feature_status_update: concrete description
    remaining_candidate_features: list with refuted features removed
    updated_score: revised score
  Action: either another refutation call or final.

Final anomaly_score rules:
  - All candidates refuted (empty remaining) → 0.05-0.20
  - ≥1 feature survives, clearly defect-like → 0.80-0.95
  - Mixed/uncertain → 0.40-0.60

For mcq_binary: ALSO map anomaly_score to A/B letter:
  - If the options text for letter X contains "yes", "defect", or
    "there is/are" patterns → X is the Yes-letter.
  - Answer Yes-letter iff anomaly_score > 0.5, else No-letter.
  - Set mcq_answer = chosen letter.

========= Mode 3: mcq_choice (4-way visual Q&A) =========

Refutation does NOT apply. Use observe-match-pick.

Turn 1 (often final):
  Output:
    mode: "mcq_choice"
    anomaly_score: gut estimate of how anomalous the image is (for
      context — MCQ may or may not depend on it)
    visual_evidence: 1-3 concrete observations (string list)
    option_scores: {{"A": 0..1, "B": 0..1, "C": 0..1, "D": 0..1}}
      probability each option is correct given the evidence
    mcq_answer: letter with highest option_scores

Call a tool ONLY when uncertain (max option_score < 0.55 AND at least
2 options within 0.1 of each other). Preferred tools here:
  tool_zoom_bbox, tool_reference_profiler, tool_domain_knowledge.
Avoid refutation probes (tool_side_by_side, tool_image_diff) unless
the question explicitly asks about a specific region.

Turn 2+: update visual_evidence and option_scores after the tool
observation; finalise.

Final rules for mcq_choice:
  - mcq_answer = argmax(option_scores)
  - Do NOT ensemble with Direct VLM here.

========= Mode 4: open_ended =========

Turn 1: observe the image; write free_text answer (1-2 sentences).
  action="final". Call a tool only if the answer requires counting or
  pointing to a specific region; otherwise just answer.

COMMON JSON SCHEMA (every turn):
{{
  "thought":       "<one short reasoning step>",
  "mode":          "<see above>",
  "anomaly_score": <float 0..1>,
  "mcq_answer":    "A|B|C|D"|null,
  "free_text":     "<string>"|null,
  "visual_evidence":["...","..."]|null,
  "option_scores": {{"A":..,"B":..,"C":..,"D":..}}|null,
  "refutation_trace": {{
    "initial_score": <float>|null,
    "candidate_features": [...]|null,
    "remaining_features": [...]|null,
    "refutation_verdicts": [...]|null,
    "updated_score": <float>|null
  }}|null,
  "refutation_target":   <int>|null,
  "refutation_verdict":  "...|null",
  "feature_status_update": "..."|null,
  "remaining_candidate_features": [...]|null,
  "updated_score":       <float>|null,
  "action":   "call_tool"|"final",
  "tool":     "<tool_name>"|null,
  "args":     {{...}}|null,
  "confidence": 0..100,
  "rationale": "<one or two sentences; required when final>"
}}

Return ONLY a JSON object.
"""


def forced_final_prompt(budget):
    return (f"THIS IS YOUR LAST TURN ({budget}/{budget}). action MUST be "
            f"\"final\". For mcq_binary set mcq_answer (derived from "
            f"anomaly_score). For mcq_choice set mcq_answer = argmax of "
            f"option_scores. For open_ended write free_text.")


def budget_warning_prompt(remaining):
    if remaining <= 1:
        return "1 turn remaining — finalise now."
    return f"{remaining} turns remaining."


def format_task_preamble(question, options):
    """Build the text block shown to the LLM describing the task.

    Returns a dict with 'mode_hint' (string) and 'text' (string to append
    to user turn 1 after the images).
    """
    has_q = bool(question)
    has_opt = bool(options)
    if not has_q and not has_opt:
        return {"mode_hint": "detection",
                "text": ("TASK: detection. No question provided; decide "
                         "whether the QUERY image is anomalous relative to "
                         "the reference images. Use the refutation protocol.")}
    opts = options or {}
    is_binary = False
    if has_opt and len(opts) == 2:
        txts = [str(v).lower() for v in opts.values()]
        is_binary = any("yes" in t or "defect" in t for t in txts) or \
                    any("no" in t or "normal" in t for t in txts)
    if is_binary:
        mode_hint = "mcq_binary"
    elif has_opt:
        mode_hint = "mcq_choice"
    else:
        mode_hint = "open_ended"

    opt_str = ""
    if has_opt:
        opt_str = "OPTIONS:\n" + "\n".join(
            f"  {k}: {v}" for k, v in opts.items())
    preamble = (
        f"TASK: {mode_hint}.\n"
        f"QUESTION: {question}\n"
        f"{opt_str}\n"
        "Use the protocol for this mode. Final JSON must set mode field and"
        " the correct answer field (mcq_answer for MCQ, free_text for open)."
    )
    return {"mode_hint": mode_hint, "text": preamble}
