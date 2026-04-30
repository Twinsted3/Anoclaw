"""Agent v12_mmad prompt — fork of agent_prompt_v10 that unblocks
targeted tool use for MMAD non-AD question types (Defect Localization,
Object Classification, etc.).

Diff vs v10:
  - MODE 2 (anomaly_analysis): now ENCOURAGES tool_image_diff +
    tool_hotspot_cropper / tool_segment_and_count for WHERE / LOCATION
    / WHICH-SIDE questions; encourages tool_expert_score for
    WHAT-KIND / TYPE / CATEGORY questions. The earlier "AVOID
    side_by_side and image_diff" ban is removed.
  - MODE 3 (object_analysis): the hard "action MUST be final, Do NOT
    call any tool" rule is replaced with a softer "default is final;
    tool_zoom_bbox is permissible for fine-grained part / count / shape
    / colour questions". Hardcoded coercion in agent_v12_mmad main
    loop is also removed.

If MMAD dev500 letter accuracy on non-AD non-trivially exceeds v10's,
promote to v15.

Original v10 docstring follows.
---
Agent v10 prompt — v9 unified task-aware agent + specialty-matched
13-tool ladder for agent_tools_v8.

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


TOOL_DESCRIPTIONS = """Tools available (call at most one per turn).
Each tool has a SPECIALTY — match the tool to what you actually need.

== CONTRAST / REFUTATION (compare query to refs) ==

  tool_side_by_side(bbox=[x0,y0,x1,y1])
    SPECIALTY: refute a localised query feature against all 4 refs at once.
    Shows query crop | ref0 | ref1 | ref2 | ref3 at the SAME bbox.
    WHEN: you have a specific suspicious region and want to check whether
    that feature is also present in any normal ref. bbox in 256x256 coords.

  tool_reference_profiler()
    SPECIALTY: text-level NORMAL baseline — what do the refs have in
    common, and what variation is NORMAL across them.
    WHEN: your turn-1 candidate_features are ambiguous and you need to
    know what counts as normal before scoring.

  tool_reference_retriever(k=4)
    SPECIALTY: pulls k ADDITIONAL nearest normal refs (returned as loaded
    images) from the domain's normal bank via DINOv2 similarity.
    WHEN: the 4 provided refs look too narrow (one viewpoint, one
    instance) and you suspect the query is a less-represented normal
    subtype. You will SEE the retrieved images in the next turn.

== LOCALISED VISUAL INSPECTION ==

  tool_zoom_bbox(bbox=[x0,y0,x1,y1])
    SPECIALTY: single-image high-resolution crop of the QUERY (no refs).
    WHEN: you already know the feature is not present in refs and need
    to see the query region at full resolution, OR side_by_side would
    be cluttered.

  tool_patch_grid(rows=3, cols=3)
    SPECIALTY: systematic spatial scan of the whole query (3x3 tiles).
    WHEN: you DON'T have a candidate bbox yet and the suspicious region
    could be anywhere.

== PIXEL-LEVEL DIFF (ALIGNED DOMAINS ONLY) ==

  tool_image_diff(ref_idx=0..3)
    SPECIALTY: strict pixel diff query-vs-ref N. Returns a change mask +
    change_percent.
    APPLICABLE: D1 (MVTec-AD), D2 (GoodsAD), D5 (MVTec-LOCO) only —
    aligned industrial photography.
    OTHER DOMAINS: the tool refuses. Use side_by_side instead.

  tool_rotate_align(ref_idx=0..3)
    SPECIALTY: pixel diff with small rotation tolerance (±10 deg).
    APPLICABLE: same aligned industrial domains as image_diff.

== EXPERT SECOND OPINION (cached pretrained AD model, per-domain) ==

  tool_expert_score()   (leave expert as "auto" — DO NOT specify)
    SPECIALTY: numerical second opinion from a pretrained AD model. Returns
    rank_in_domain, typical score ranges for this domain, a red heatmap
    overlay on the query, and a suggested_bbox_256 around the hotspot
    cluster.
    AVAILABLE domains (auto picks subspacead):
      strong:   D1 (AUROC 0.97), D2 (0.84), D7 (0.94), D10 (0.89)
      moderate: D4 (0.72), D5 (0.69), D9 (0.70)
      unavailable: D3, D6, D8, D11, D12 — the tool says so and returns
                   available=False.
    WHEN: you want an independent score + a concrete bbox to inspect.
    STANDARD FOLLOW-UP: tool_side_by_side(bbox=expert.suggested_bbox_256)
    in the next turn to visually verify the hotspot vs refs.

  tool_hotspot_cropper()
    SPECIALTY: after tool_expert_score, crops the query AND the refs at
    the expert hotspot bbox and returns a query | ref0 | ref1 | ref2
    composite image.
    WHEN: alternative to side_by_side at the expert's bbox — use either.

== STRUCTURAL / TEXTURE ANALYTICS (with visual outputs) ==

  tool_component_counter()
    SPECIALTY: after expert_score, tells you whether the hotspots form
    ONE concentrated blob (localised defect signature) or MANY scattered
    blobs (often false alarm). Returns a coloured blob-layout image.
    WHEN: expert borderline — quick structural sanity check.

  tool_segment_and_count()
    SPECIALTY: coarse 8x8-grid intensity diff vs ref 0. Returns a change-
    heatmap image + 5 candidate bboxes at the largest-diff cells.
    WHEN: you don't yet have a target bbox; the heatmap points WHERE to
    look next. Works on any domain with refs but blunted by global
    lighting shift.

  tool_texture_fft()
    SPECIALTY: periodicity disruption. Returns a log-magnitude spectrum
    image and query-vs-ref periodicity delta.
    BEST DOMAINS: D4 concrete (cracks break aggregate periodicity),
    fabric/grid/lattice textures. NOT useful for natural scenes or
    medical tissue.

== KNOWLEDGE LOOKUP ==

  tool_domain_knowledge(question="...")
    SPECIALTY: text lookup for a SPECIFIC visual cue's meaning in this
    domain. Ask about a cue you can see but can't confidently label.
    GOOD: "In dermoscopy, is a dark uniform brown mole with smooth
    borders typically benign or malignant?"
    BAD : "What is melanoma?"
"""


REFUTATION_LADDER = """REFUTATION LADDER (pick the lowest rung that resolves your uncertainty):

  L1. reference_profiler()      — cheap, text: "what is normal here?"
  L2. side_by_side(bbox)        — visual query-vs-refs at a specific region.
  L3. expert_score()            — numeric 2nd opinion + heatmap +
                                   suggested_bbox. Applicable: D1,D2,D4,D5,
                                   D7,D9,D10. Skip on D3,D6,D8,D11,D12.
                                   Standard follow-up: L2 at that bbox.
  L4. reference_retriever(k=4)  — pull 4 extra normal images (actually
                                   visible) when refs look too narrow.
  L5. zoom_bbox(bbox)           — single high-res crop (no refs).
  L6. segment_and_count         — coarse change heatmap to LOCATE region
                                   before picking a bbox.
      component_counter         — is expert hotspot localised or diffuse.
      texture_fft               — periodicity disruption (D4 concrete etc).
  L7. image_diff / rotate_align — ONLY on D1,D2,D5 (aligned industrial).
                                   Tool refuses elsewhere.

Rule: most items need ONE tool. The typical failure is stopping at L2
when still uncertain — climb to L3 in that case. After expert_score,
the expected follow-up is a side_by_side at the suggested bbox.
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
  - **Turn 1 default is action="final"**. Populate option_scores and
    mcq_answer directly. BUT: if the question matches one of the
    sub-types below, the corresponding tool is the standard pipeline
    and should NOT be skipped on turn 1.
  - **Sub-type → recommended tool**:
      * Question asks WHERE / LOCATION / POSITION / WHICH SIDE / WHICH
        REGION the defect is →
          1) tool_segment_and_count() (no bbox yet, get a heatmap
             pointing to candidate regions), THEN turn 2:
          2) tool_hotspot_cropper() / tool_image_diff(ref_idx=0) at the
             candidate region. Use the visual evidence to pick the
             option whose described location matches the hotspot.
      * Question asks WHAT KIND / TYPE / CATEGORY / CLASS of defect →
          tool_expert_score() for an independent classifier signal +
          heatmap; the suggested_bbox tells you where to look in turn 2
          via tool_hotspot_cropper.
      * Question asks how to DESCRIBE / characterise the defect (size,
        colour, shape, severity) →
          tool_zoom_bbox(bbox) at the candidate region; or
          tool_domain_knowledge for a text lookup of the visual cue's
          meaning.
      * Otherwise (Defect Analysis with no spatial / categorical hook)
        → final on turn 1.
  - Tools `tool_side_by_side` and `tool_image_diff` are NO LONGER
    blocked in this mode — they are useful for spatial questions. Use
    them when the question's wording justifies them (see sub-types
    above).
  - Aim for AT MOST ONE tool call per item except for the WHERE /
    LOCATION pipeline which uses two (heatmap → crop).

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
  - **Turn 1 default is action="final"**. Most object identity
    questions can be answered from a direct look at the query.
  - Targeted tool use is permitted (NOT required) ONLY for these
    sub-types:
      * Question asks COUNT / NUMBER OF (parts, holes, components,
        cells) → tool_zoom_bbox at the relevant region for a high-res
        recount. Use sparingly — a clear initial count is preferable.
      * Question asks the PRECISE SHAPE of a small structural feature
        (e.g. "what shape is the hole", "what kind of edge") and the
        feature is too small in the query thumbnail → tool_zoom_bbox.
      * Question is genuinely ambiguous between two options
        (max(option_scores) < 0.55, top-2 within 0.10) AND a specific
        region of the query is named in the question → tool_zoom_bbox
        on that region.
      * Otherwise → action="final" on turn 1. Empirically, tool calls
        in this mode have historically hurt accuracy; only use a tool
        when one of the rules above is clearly satisfied.
  - Output visual_evidence, option_scores, mcq_answer when finalising.

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

{REFUTATION_LADDER}

====================================================================
REFUTATION PROTOCOL (anomaly_detection only)
====================================================================
Turn 1 (no tool):
  Populate refutation_trace.initial_score, .candidate_features (up to 3
  items {{name, location_hint, looks_defect_like}}), refutation_target
  = index of the most defect-like candidate.
  - If candidate_features empty AND initial_score < 0.3 → action="final",
    anomaly_score = 0.05.
  - Else action="call_tool" picking the LOWEST ladder rung that matches
    your uncertainty. Use the SPECIALTY of each tool as the guide.
    Typical choices:
      * suspicious localised region found → L2 side_by_side(bbox) or
        L3 expert_score() (strong/moderate domains).
      * refs seem too narrow → L4 reference_retriever(k=4).
      * no idea where to look → L6 segment_and_count().
      * aligned industrial + clean refs → L7 image_diff also valid.

Turn 2+:
  refutation_verdict ∈ {{found_in_ref, not_found, inconclusive}}.
  Remove refuted features. updated_score:
    all refuted → 0.05-0.20;
    ≥1 surviving defect-like → 0.80-0.95;
    mixed/uncertain → 0.40-0.60.
  When an expert_score hotspot SURVIVES a side_by_side check (the
  same feature is NOT in any ref), that is strong evidence — set
  updated_score 0.85-0.95.
  Finalise when the candidate list is empty or budget runs out.

Return ONLY a JSON object.
"""


DOMAIN_HINTS = {
    "D1":  ("D1 — MVTec-AD (aligned industrial). expert_score is STRONG here "
            "(AUROC 0.97). Standard pipeline on a suspicious candidate: "
            "expert_score → side_by_side(bbox=suggested_bbox_256). "
            "image_diff / rotate_align are also applicable (refs are aligned "
            "photographs of the same item)."),
    "D2":  ("D2 — GoodsAD (retail, mostly aligned). expert_score STRONG "
            "(AUROC 0.84). expert_score → side_by_side is the standard pipeline. "
            "image_diff applicable when refs look tightly cropped."),
    "D3":  ("D3 — complex industrial. expert_score is NOT available for this "
            "domain. Rely on side_by_side + reference_profiler; consider "
            "reference_retriever when refs look narrow."),
    "D4":  ("D4 — SDNET concrete cracks. expert_score MODERATE (AUROC 0.72). "
            "texture_fft can detect crack-induced disruption of the aggregate "
            "pattern — useful when no candidate bbox is obvious. image_diff NOT "
            "applicable (different photographs)."),
    "D5":  ("D5 — MVTec-LOCO logical. expert_score MODERATE (AUROC 0.69). "
            "image_diff applicable (aligned). Anomalies here are often LOGICAL "
            "(wrong count / wrong part) — reference_profiler helps define the "
            "correct configuration before scoring."),
    "D6":  ("D6 — Real3D-AD point-cloud renders. expert_score NOT reliable "
            "(all experts <0.5 AUROC here). Prefer side_by_side at multiple "
            "viewpoints and reference_retriever."),
    "D7":  ("D7 — LEVIR aerial building change. expert_score STRONG "
            "(AUROC 0.94). segment_and_count can quickly LOCATE the changed "
            "region; follow with expert_score + side_by_side at the suggested "
            "bbox. image_diff NOT applicable (different capture dates, "
            "seasonal / radiometric shift)."),
    "D8":  ("D8 — dermoscopy. expert_score NOT reliable (~0.6 AUROC). Use "
            "side_by_side for ABCDE-style contrast vs benign nevi in the refs; "
            "domain_knowledge for specific visual-cue lookup (hair artefact, "
            "bubble, ink marking)."),
    "D9":  ("D9 — BraTS brain MRI. expert_score MODERATE (AUROC 0.70). Refs "
            "are normal brain slices at similar levels; image_diff NOT "
            "applicable (slice positions differ). expert_score + side_by_side "
            "at the suggested_bbox is the standard pipeline for focal lesions."),
    "D10": ("D10 — BMAD-Liver CT. expert_score STRONG (AUROC 0.89). For "
            "suspicious intrahepatic lesions, expert_score → side_by_side "
            "at suggested_bbox is the standard pipeline. image_diff NOT "
            "applicable (different slice levels)."),
    "D11": ("D11 — HyperKvasir GI endoscopy. expert_score NOT available. "
            "side_by_side + zoom_bbox for suspicious mucosal features "
            "(polyps, ulcers, tumours). domain_knowledge helpful."),
    "D12": ("D12 — Road safety driving scenes. expert_score NOT available. "
            "Anomalies are unexpected objects on road; use side_by_side + "
            "zoom_bbox on candidate objects. image_diff / rotate_align NOT "
            "applicable."),
}


def format_domain_hint(domain_code: str | None) -> str:
    """Return a per-domain guidance block to prepend to the user turn-1 msg.

    Empty string when the domain is unknown so the agent falls back to the
    generic ladder.
    """
    if not domain_code or domain_code not in DOMAIN_HINTS:
        return ""
    return (f"DOMAIN-SPECIFIC TOOL GUIDANCE:\n{DOMAIN_HINTS[domain_code]}\n"
            f"Use this to PICK THE RIGHT TOOL — it is not a substitute for "
            f"visual reasoning.")


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
    qlow = (question or "").lower()
    if mode_hint == "object_analysis":
        extra = (
            "\n\nClassifier suggests mode = object_analysis (物体分析模式). "
            "The reference images have been omitted from this prompt "
            "because the question is about the query object's own identity. "
            "Default = finalise in turn 1. tool_zoom_bbox is permissible "
            "for fine-grained count / shape / part questions if the "
            "feature is too small in the query thumbnail."
        )
        if any(k in qlow for k in ("how many", "number of", "count",
                                   "shape of", "what color", "what colour",
                                   "structure of")):
            extra += (
                "\n  (HINT: this question phrasing suggests a fine-grained "
                "feature — tool_zoom_bbox at the named region may help.)"
            )
    elif mode_hint == "anomaly_analysis":
        extra = (
            "\n\nClassifier suggests mode = anomaly_analysis (异常分析模式). "
            "The query is assumed to be anomalous; use the refs for "
            "contrast, not for refutation."
        )
        # Sub-type detection: localisation / classification / description.
        is_loc = any(k in qlow for k in (
            "where", "location", "located", "position",
            "which side", "which region", "which part of",
            "in the upper", "in the lower", "in the left", "in the right",
            "at the top", "at the bottom", "near the"))
        is_cls = any(k in qlow for k in (
            "what kind of defect", "what type of defect",
            "category of defect", "class of defect",
            "what defect", "which defect"))
        is_desc = any(k in qlow for k in (
            "describe", "characterize", "characterise",
            "how severe", "size of", "color of", "colour of",
            "shape of the defect"))
        if is_loc:
            extra += (
                "\n  (SUBTYPE = LOCALISATION: standard pipeline is "
                "tool_segment_and_count() in turn 1 to get a change "
                "heatmap, then tool_hotspot_cropper() or "
                "tool_image_diff(ref_idx=0) on the hottest region in "
                "turn 2.)"
            )
        elif is_cls:
            extra += (
                "\n  (SUBTYPE = CLASSIFICATION: standard pipeline is "
                "tool_expert_score() for an independent classifier "
                "signal + suggested_bbox, then tool_hotspot_cropper() "
                "in turn 2.)"
            )
        elif is_desc:
            extra += (
                "\n  (SUBTYPE = DESCRIPTION: a single tool_zoom_bbox "
                "at the candidate region or tool_domain_knowledge text "
                "lookup is usually enough.)"
            )
        else:
            extra += (
                "\n  (No spatial/categorical sub-type detected — final "
                "on turn 1 is fine.)"
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
