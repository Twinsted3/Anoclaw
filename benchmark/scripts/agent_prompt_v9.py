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
specialised in anomaly detection but able to answer five kinds of
tasks:

MODES (inferred from inputs; do NOT ask the user):
  1. `detection`:          refs present, no question.
       → refutation protocol; output anomaly_score.
  2. `mcq_binary`:         refs + question + options like A/B (Yes/No).
       → refutation protocol; output anomaly_score AND mcq_answer.
  3. `mcq_choice_defect`:  question asks about a DEFECT
                           (classification, localization, description,
                           analysis of a defect / damage / crack /
                           anomaly).
       → observe + match evidence to options; refs are informative.
       Output mcq_answer.
  4. `mcq_choice_object`:  question asks about the QUERY OBJECT itself
                           (what it is, how many components, colour,
                           structure, details) — NO anomaly semantics.
       → **IGNORE the reference images entirely** (they are of other
       normal instances and only add noise). Answer from the query
       alone. Tool budget is zero in the typical case; at most one
       `tool_zoom_bbox` or `tool_domain_knowledge` call if genuinely
       uncertain. Do NOT run refutation or call `tool_side_by_side`,
       `tool_image_diff`, `tool_reference_profiler`,
       `tool_reference_retriever`, `tool_expert_score`,
       `tool_hotspot_cropper`.
       Output mcq_answer.
  5. `open_ended`:         question, no options.
       → describe; output free_text.

How to pick between mcq_choice_defect and mcq_choice_object when both
options are descriptive 4-way MCQ:
  - If the question / options mention defect, anomaly, damage, crack,
    scratch, contamination, missing part, broken, wrong colour, stain,
    deformation, misalignment, spot, tear → mode = mcq_choice_defect.
  - If the question is "what is the object", "how many components",
    "what colour is the object", "what is the shape", "structure of
    the object", "details of the object", or the options enumerate
    object categories / structural counts / colours / shapes →
    mode = mcq_choice_object. The reference images are irrelevant
    in this mode because the task is about the query's own identity,
    not about how it differs from normals.

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

========= Mode 3: mcq_choice_defect (4-way defect Q&A) =========

Refutation does NOT apply. Use observe-match-pick.

Turn 1 (often final):
  Output:
    mode: "mcq_choice_defect"
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

Final rules for mcq_choice_defect:
  - mcq_answer = argmax(option_scores)
  - Do NOT ensemble with Direct VLM here.

========= Mode 4: mcq_choice_object (4-way object Q&A) =========

The question is about the query object's IDENTITY / STRUCTURE /
APPEARANCE — not about defects. Reference images are IRRELEVANT here.

Turn 1 (almost always final):
  Output:
    mode: "mcq_choice_object"
    visual_evidence: 1-2 concrete observations about the QUERY image
      only (what it looks like, its colour, its parts)
    option_scores: {{"A": 0..1, "B": 0..1, "C": 0..1, "D": 0..1}}
      probability each option matches the query
    mcq_answer: argmax(option_scores)
    anomaly_score: 0.5 (undefined for this mode; set to 0.5 to
      satisfy the unified schema)

Tool budget is 0 in the common case. Call a tool only when the query
requires extreme zoom (tool_zoom_bbox) or external knowledge
(tool_domain_knowledge, e.g.\ "which product category is this?").
Do NOT call reference-based tools (side_by_side, image_diff,
reference_profiler, reference_retriever) in this mode — the refs are
simply different normal instances of the same product and do not
help answer the question.

Final rule: mcq_answer = argmax(option_scores). Do not ensemble.

========= Mode 5: open_ended =========

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


_DEFECT_KEYWORDS = (
    "defect", "anomal", "damage", "crack", "scratch", "contamination",
    "missing", "broken", "wrong", "stain", "deformation", "misalign",
    "spot", "tear", "faulty", "hole", "bend", "chip",
)
_OBJECT_KEYWORDS = (
    "what is the object", "what kind of", "what type of object",
    "how many", "what color", "what colour", "what shape",
    "what are the object", "structure of the object", "details of the object",
    "describe the object", "object's structure", "object's details",
    "which category", "which class", "what category",
)


def _classify_mcq_choice(question: str, options: dict) -> str:
    """Return 'mcq_choice_defect' or 'mcq_choice_object'.

    Rule: if defect/anomaly vocabulary appears in the question or in any
    option text, it is a defect question. Otherwise if the question
    matches object-identity patterns, it is an object question. Default
    (ambiguous) → defect (safer — agent keeps refs in the prompt).
    """
    q = (question or "").lower()
    opts_txt = " ".join(str(v) for v in (options or {}).values()).lower()
    blob = q + " || " + opts_txt
    has_defect = any(k in blob for k in _DEFECT_KEYWORDS)
    has_object = any(k in q for k in _OBJECT_KEYWORDS)
    if has_defect and not has_object:
        return "mcq_choice_defect"
    if has_object and not has_defect:
        return "mcq_choice_object"
    # Both or neither: lean on dataset-specific clue — if the question
    # text is about "what is" / "how many" / "which" → object.
    if any(p in q for p in ("what is ", "how many ", "which ", "what colour",
                            "what color", "what shape")):
        return "mcq_choice_object"
    return "mcq_choice_defect"


def format_task_preamble(question, options, task_type_hint=None):
    """Build the text block shown to the LLM describing the task.

    Returns a dict with 'mode_hint' (string) and 'text' (string to append
    to user turn 1 after the images).

    `task_type_hint` (optional): when the caller already knows the
    question category (e.g. the MMAD `type` field — "Object Structure",
    "Defect Classification"), pass it here and the mode hint will be
    set deterministically. Keyword-based classification is used only
    as fallback.
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
        if task_type_hint:
            # Authoritative override from dataset metadata (e.g. MMAD)
            t = task_type_hint.lower()
            if "defect" in t or "anomal" in t:
                mode_hint = "mcq_choice_defect"
            elif t.startswith("object"):
                mode_hint = "mcq_choice_object"
            else:
                mode_hint = _classify_mcq_choice(question or "", opts)
        else:
            mode_hint = _classify_mcq_choice(question or "", opts)
    else:
        mode_hint = "open_ended"

    opt_str = ""
    if has_opt:
        opt_str = "OPTIONS:\n" + "\n".join(
            f"  {k}: {v}" for k, v in opts.items())

    extra = ""
    if mode_hint == "mcq_choice_object":
        extra = (
            "\n\nThis is mode `mcq_choice_object` — the question is about "
            "the QUERY IMAGE's own object identity/structure/appearance, "
            "NOT about any defect. **IGNORE the reference images entirely "
            "— they are of other normal instances and only add noise.** "
            "Answer from the query image alone. Do not call refutation "
            "tools; default to action='final' in turn 1 with "
            "option_scores and mcq_answer."
        )

    preamble = (
        f"TASK: {mode_hint}.\n"
        f"QUESTION: {question}\n"
        f"{opt_str}"
        f"{extra}\n"
        "Use the protocol for this mode. Final JSON must set mode field and"
        " the correct answer field (mcq_answer for MCQ, free_text for open)."
    )
    return {"mode_hint": mode_hint, "text": preamble}
