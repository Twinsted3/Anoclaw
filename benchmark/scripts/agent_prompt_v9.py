"""Agent v9 — Unified Task-Aware Agent (extends v8 refutation).

Accepts (image, refs?, question?, options?) and produces unified JSON.

Four modes, inferred by the LLM itself from (question, options) in
turn 1 — no extra routing call, no dataset-type leakage:

  anomaly_detection  异常检测模式  — no question OR Yes/No binary on
                                     whether the query is anomalous.
                                     Refutation protocol → anomaly_score.
                                     For Yes/No MCQ also outputs mcq_answer
                                     by mapping score > 0.5 to the Yes-letter.

  anomaly_analysis   异常分析模式  — 4-way MCQ that assumes the query IS
                                     anomalous and asks WHICH defect / WHERE
                                     / how to describe it / which class of
                                     anomaly. Uses the reference images for
                                     contrast. Observe → option_scores → argmax.

  object_analysis    物体分析模式  — 4-way MCQ about the query object's own
                                     identity / structure / appearance. Refs
                                     are different normal instances and only
                                     add noise. **Ignore refs.** Tool budget
                                     is mostly 0; call tool_zoom_bbox or
                                     tool_domain_knowledge only when clearly
                                     helpful.

  open_qa            开放问答      — question, no options. Describe via
                                     free_text.

Mode IDs are stable strings (the ones above) — the prompt tells the LLM to
self-identify and output the mode field in its JSON.
"""
from __future__ import annotations


TOOL_DESCRIPTIONS = """Tools available (call at most one per turn):

REFUTATION / CONTRAST PROBES (anomaly_detection / anomaly_analysis):

  tool_side_by_side(bbox=[x0,y0,x1,y1])
    Composite cropping query+4 refs at the SAME bounding box. Best for
    refuting a localised feature against the reference pool.
    bbox is in 256x256 normalized coords (0-256).

  tool_zoom_bbox(bbox=[x0,y0,x1,y1])
    Full-resolution crop of ONE region of the query. Does NOT show refs.
    Usable in any mode when a specific region matters.

  tool_image_diff(ref_idx=0..3)
    Pixel diff query vs ref N. Returns change_percent and
    unreliable_alignment flag. Ignore when unreliable.

  tool_reference_retriever(k=4)
    Retrieves k nearest normal refs from the domain pool.

  tool_reference_profiler()
    Structured description of what refs share (object / colors /
    allowed variations).

SUPPORTING PROBES:

  tool_expert_score(expert="subspacead")
    Returns normalized_rank. rank<=0.4 ⇒ normal-like, rank>=0.85 ⇒
    anomaly-like.

  tool_hotspot_cropper()
    After tool_expert_score(subspacead), crops the top hotspot patches.

  tool_domain_knowledge(question)
    Targeted text question to an LLM. May hallucinate; cross-check.
"""


SYSTEM_PROMPT = f"""You are AnomalyClaw, a visual reasoning agent. Every
query you receive belongs to one of four modes. You must self-identify
the mode in turn 1 from the question text and the option texts — there
is no external routing signal.

====================================================================
MODE 1 · anomaly_detection   (异常检测模式)
====================================================================
Trigger:
  - No question given, OR
  - Question like "Is there any defect / damage / anomaly?" with binary
    Yes/No options.
Goal:
  - Output anomaly_score ∈ [0,1] (1 = certainly anomalous).
  - For the Yes/No MCQ variant also set mcq_answer = the letter whose
    option_text contains "Yes"/"defect"/"there is" when score > 0.5,
    else the other letter.
Protocol:
  - Follow the refutation protocol (see below). The query is NORMAL
    until a candidate feature SURVIVES refutation.
  - Reference images are relevant and should be used.

====================================================================
MODE 2 · anomaly_analysis    (异常分析模式)
====================================================================
Trigger:
  - 4-way MCQ whose question or options mention a defect / anomaly /
    damage / crack / scratch / contamination / missing part / broken /
    stain / deformation / misalignment / spot / tear / hole / bend.
  - The question presupposes that the query IS anomalous and asks
    which defect, where, how to describe it, or how severe.
Goal:
  - option_scores: {{"A":..,"B":..,"C":..,"D":..}}
  - mcq_answer = argmax(option_scores)
  - anomaly_score: gut estimate (this mode does not require calibration)
Protocol:
  - Observe the query together with the refs; the refs give you the
    NORMAL baseline to contrast against.
  - Call tool_side_by_side, tool_zoom_bbox, or tool_image_diff when a
    specific region is relevant.
  - Do NOT run the full refutation protocol; a single targeted
    observation plus the option-scoring is usually enough.

====================================================================
MODE 3 · object_analysis     (物体分析模式)
====================================================================
Trigger:
  - 4-way MCQ about the query object's own identity, structure,
    appearance, components, colour, number of parts, or category.
  - Question does NOT mention defect / anomaly / damage semantics.
    Typical phrasings: "What kind of product is this?", "How many
    components?", "What is the shape of the opening?", "Where is the
    label placed?".
Goal:
  - option_scores + mcq_answer.
  - anomaly_score = 0.5 (undefined for this mode).
Protocol:
  - The reference images are different normal instances of the same
    product and are IRRELEVANT for identity questions — **ignore them**.
    Focus on the QUERY image alone.
  - **action MUST be "final" in turn 1.** Do NOT call any tool in this
    mode. Empirically, tool calls in object_analysis collapse
    accuracy by ~15 pp. If a specific region is referenced in the
    question (e.g. "around the opening"), describe it from your
    direct look at the query; do not invoke tool_zoom_bbox.
  - Output visual_evidence, option_scores, mcq_answer all at turn 1.

====================================================================
MODE 4 · open_qa             (开放问答)
====================================================================
Trigger:
  - Question present, no options.
Goal:
  - free_text: 1-2 sentence answer.
Protocol:
  - Observe the query; refs optional. Default turn 1 final.

====================================================================
UNIFIED OUTPUT SCHEMA (every turn)
====================================================================
{{
  "thought": "<one short reasoning step>",
  "mode": "anomaly_detection" | "anomaly_analysis" |
          "object_analysis" | "open_qa",
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
  "refutation_verdict":  "found_in_ref"|"not_found"|"inconclusive"|null,
  "feature_status_update": "..."|null,
  "remaining_candidate_features": [...]|null,
  "updated_score":       <float>|null,
  "action":   "call_tool"|"final",
  "tool":     "<tool_name>"|null,
  "args":     {{...}}|null,
  "confidence": 0..100,
  "rationale": "<one or two sentences; required when final>"
}}

{TOOL_DESCRIPTIONS}

====================================================================
REFUTATION PROTOCOL (anomaly_detection only)
====================================================================
Turn 1 (no tool):
  Populate refutation_trace.initial_score, .candidate_features (up to 3
  items {{name, location_hint, looks_defect_like}}), refutation_target
  = index of the most defect-like candidate.
  - If candidate_features empty AND initial_score < 0.3 → action="final",
    anomaly_score = 0.05.
  - Else action="call_tool" with a tool that can REFUTE the target
    (side_by_side, reference_profiler, reference_retriever).

Turn 2+:
  refutation_verdict ∈ {{found_in_ref, not_found, inconclusive}}.
  Remove refuted features. updated_score:
    all refuted → 0.05-0.20;
    ≥1 surviving defect-like → 0.80-0.95;
    mixed/uncertain → 0.40-0.60.
  Finalise when the list is empty or budget runs out.

Return ONLY a JSON object.
"""


def forced_final_prompt(budget):
    return (f"THIS IS YOUR LAST TURN ({budget}/{budget}). action MUST be "
            f"\"final\". For anomaly_detection set anomaly_score (and "
            f"mcq_answer if Yes/No options were given). For "
            f"anomaly_analysis / object_analysis set option_scores and "
            f"mcq_answer. For open_qa write free_text.")


def budget_warning_prompt(remaining):
    if remaining <= 1:
        return "1 turn remaining — finalise now."
    return f"{remaining} turns remaining."


_DEFECT_KEYWORDS = (
    "defect", "anomal", "damage", "crack", "scratch", "contamination",
    "missing", "broken", "stain", "deformation", "misalign",
    "spot", "tear", "faulty", "hole", "bend", "split",
    "discoloration",
)
_OBJECT_Q_PATTERNS = (
    "what kind of", "what type of", "how many", "what color", "what colour",
    "what shape", "what is the object", "describe the object",
    "structure of the object", "details of the object", "which category",
    "which class", "what category",
    "where is", "where are", "what feature", "what tone", "what pattern",
    "what does the", "what are the", "which part",
)


def _classify_mcq_choice(question: str, options: dict) -> str:
    """Classify a 4-way MCQ as `anomaly_analysis` or `object_analysis`.

    Source of truth: the textual question + option strings the agent
    will see anyway. No dataset metadata.
    """
    q = (question or "").lower()
    opts_txt = " ".join(str(v) for v in (options or {}).values()).lower()
    blob = q + " || " + opts_txt
    has_defect = any(k in blob for k in _DEFECT_KEYWORDS)
    has_object_pattern = any(p in q for p in _OBJECT_Q_PATTERNS)
    if has_defect and not has_object_pattern:
        return "anomaly_analysis"
    if has_object_pattern and not has_defect:
        return "object_analysis"
    # Ambiguous. Use a secondary cue: if ANY option mentions a defect-like
    # property, lean to anomaly_analysis; else lean to object_analysis
    # (question is then about the object itself).
    if has_defect:
        return "anomaly_analysis"
    return "object_analysis"


def format_task_preamble(question, options):
    """Build the task preamble the agent sees on turn 1.

    Returns a dict with 'mode_hint' (classifier's best guess; the LLM is
    free to override in its JSON output) and 'text'.

    The classifier does NOT read dataset metadata — only (question,
    options) text.
    """
    has_q = bool(question)
    has_opt = bool(options)
    if not has_q and not has_opt:
        return {"mode_hint": "anomaly_detection",
                "text": ("TASK MODE (无问题): anomaly_detection. "
                         "Decide whether the QUERY image is anomalous "
                         "relative to the reference images via the "
                         "refutation protocol.")}
    opts = options or {}
    is_binary = False
    if has_opt and len(opts) == 2:
        txts = [str(v).lower() for v in opts.values()]
        is_binary = any("yes" in t or "defect" in t for t in txts) or \
                    any(t.startswith("no") or "normal" in t for t in txts)
    if is_binary:
        mode_hint = "anomaly_detection"
    elif has_opt:
        mode_hint = _classify_mcq_choice(question or "", opts)
    else:
        mode_hint = "open_qa"

    opt_str = ""
    if has_opt:
        opt_str = "OPTIONS:\n" + "\n".join(
            f"  {k}: {v}" for k, v in opts.items())

    extra = ""
    if mode_hint == "object_analysis":
        extra = (
            "\n\nClassifier suggests mode = object_analysis (物体分析模式). "
            "The reference images have been omitted from this prompt "
            "because the question is about the query object's own identity. "
            "Call tool_zoom_bbox or tool_domain_knowledge only when they "
            "clearly help; otherwise finalise in turn 1."
        )
    elif mode_hint == "anomaly_analysis":
        extra = (
            "\n\nClassifier suggests mode = anomaly_analysis (异常分析模式). "
            "The query is assumed to be anomalous; use the refs for "
            "contrast, not for refutation. A single targeted "
            "tool_side_by_side / tool_zoom_bbox is usually enough."
        )
    elif mode_hint == "anomaly_detection":
        if has_opt:
            extra = (
                "\n\nClassifier suggests mode = anomaly_detection "
                "(异常检测模式, Yes/No MCQ). Use the refutation protocol; "
                "map anomaly_score to mcq_answer using the option texts."
            )
    elif mode_hint == "open_qa":
        extra = "\n\nClassifier suggests mode = open_qa (开放问答)."

    preamble = (
        f"TASK:\n"
        f"QUESTION: {question}\n"
        f"{opt_str}"
        f"{extra}\n"
        "You are free to override the classifier suggestion in your JSON "
        "output if you read the question and options differently."
    )
    return {"mode_hint": mode_hint, "text": preamble}
