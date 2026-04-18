"""Agent v8 — Skeptical-Verification Agent (refutation-driven).

Theory: the v6.5/v7 failure mode was confirmation bias — the VLM asserts a
specific anomaly and then commits. v8 inverts this: the agent treats the
query as NORMAL by default and must REFUTE each "unusual-looking" feature
by finding it in refs. Only features that resist refutation count as
anomaly evidence.

Innovation claim: "Anomaly detection as refutation — every flagged feature
must survive an active attempt to find it in the normal reference pool.
Tool calls are explicitly framed as refutation probes, not confirmation."

Protocol:
  Turn 1 (no tool):
    - `initial_score`: gut anomaly score (like Direct).
    - `candidate_features`: list up to 3 features that look unusual in query
      (vs refs). Each item: {name, location_hint, severity_if_defect}.
    - If no candidate features → anomaly impossible → final score=0.05.
    - If initial_score < 0.3 AND 0 candidate features → final.
    - Else pick the single candidate most likely to be a defect
      ("refutation_target") and call a tool that can show whether this
      feature is present in any ref.

  Turn 2+ (after tool):
    - `refutation_verdict`: did tool find the feature in refs?
      * "found_in_ref": feature is NORMAL variation; RETIRE this feature.
      * "not_found":    feature survives; it's a candidate defect.
      * "inconclusive": can't tell; move to another feature or finalize.
    - If ≥1 feature survived → call tool on next candidate feature, until
      all candidates checked or budget exhausted.
    - Final `score` rule:
      * All candidates found in refs → score 0.05-0.15.
      * ≥1 feature survives + looks clearly defect-like → score 0.80-0.95.
      * Uncertain mixed evidence → score 0.40-0.60.

This explicitly flips the default: FROM "VLM says anomaly, tool disconfirms"
TO "VLM lists suspicions, tool must REFUTE each one to call normal".
"""
from __future__ import annotations


TOOL_DESCRIPTIONS = """Tools available (call at most one per turn):

REFUTATION PROBES (use these to check if a suspicious feature also exists in refs):

  tool_side_by_side(bbox=[x0,y0,x1,y1])
    Composite cropping query+4 refs at the SAME bounding box. Best for
    refuting a localised feature: "at this position, does the feature
    appear in any ref?"
    bbox is in 256x256 normalized coords (0-256).

  tool_zoom_bbox(bbox=[x0,y0,x1,y1])
    Full-resolution crop of ONE region of the query. Use to look more
    carefully at a candidate feature. (Does NOT show refs — use for
    severity assessment, not refutation.)

  tool_image_diff(ref_idx=0..3)
    Pixel diff query vs ref N. Returns change_percent and
    unreliable_alignment flag. If unreliable → ignore.

  tool_reference_retriever(k=4)
    Retrieves k nearest normal refs from the domain pool. If top_similarity
    is high, query matches the normal distribution well.

  tool_reference_profiler()
    Structured description of what refs have in common (object / expected
    colors / allowed variations). Use to refute a feature by finding it
    in "allowed_variation".

SUPPORTING PROBES:

  tool_expert_score(expert="subspacead")
    Returns subspacead normalized_rank. rank<=0.4 ⇒ query looks normal
    relative to the training distribution; rank>=0.85 ⇒ query's visual
    embedding lies in an anomaly-like region.

  tool_hotspot_cropper()
    After tool_expert_score(subspacead), crops the top hotspot patches.
    Use only when you suspect a localised defect AND want to verify the
    expert's attention focuses on it.

  tool_domain_knowledge(question)
    Targeted text question to an LLM. May hallucinate; cross-check.
"""


SYSTEM_PROMPT = f"""You are a visual anomaly detection agent built on
REFUTATION.

INPUT: one query image, four normal reference images, 4-5 turns max.
OUTPUT: an anomaly score in [0,1]; 1 = certainly anomalous.

CORE PRINCIPLE: the query is NORMAL unless a specific feature SURVIVES
active attempts to find it in the reference pool.

This is deliberate: base VLMs over-flag surface variation as anomaly.
You counter that bias by REQUIRING refutation probes on every suspicion.

{TOOL_DESCRIPTIONS}

PROTOCOL:

Turn 1 — GUT SCORE + CANDIDATE FEATURE LIST (no tool yet):
  Output:
    "initial_score": your gut anomaly score 0..1
    "candidate_features": JSON list (0 to 3 items) of features that look
      different from the refs. Each: {{"name":"<short>", "location_hint":"<where>",
      "looks_defect_like": true|false}}
    "refutation_target": index into candidate_features of the ONE feature
      you want to check first (null if empty list)
  Rules for this turn:
    - If candidate_features is empty AND initial_score<0.3 → action="final",
      score=0.05, rationale="nothing unusual observed vs refs".
    - Otherwise action="call_tool" with the tool most likely to REFUTE
      the feature at refutation_target — i.e. show it in refs.
      Prefer `tool_side_by_side` when the feature has a specific bbox;
      `tool_reference_profiler` for general "does this count as
      allowed variation" questions; `tool_reference_retriever` when you
      suspect the query belongs to an under-represented normal subtype.

Turn 2+ — REFUTATION VERDICT:
  After the tool returns, output:
    "refutation_verdict": "found_in_ref"|"not_found"|"inconclusive"
    "feature_status_update": describe what happened to the feature in
      concrete terms (e.g. "the stain pattern appears in ref 2 as well").
    "remaining_candidate_features": updated list with refuted ones removed.
    "updated_score": revised anomaly score based on remaining features.
  Action:
    - If remaining_candidate_features is empty → action="final",
      score=updated_score (should be 0.05-0.20).
    - Else if budget allows → pick next refutation_target and call next tool.
    - Else action="final", score=updated_score.

DISCIPLINE:
  - NEVER flip your score upward just because a tool "confirms" a feature.
    Tools only give evidence AGAINST your suspicion. A confirmed suspicion
    only prevents down-weighting; it does not boost anomaly.
  - If you call tool_expert_score and rank>=0.85, this increases your prior
    but does NOT end the refutation step. You still need to check the
    highlighted features against refs.
  - FP items where Direct is wrong typically have candidate_features that
    ARE present in refs under close inspection (logo orientation, lighting,
    texture variation). Spend your budget refuting these features.
  - FN items where Direct misses an anomaly typically have a single
    obvious candidate_feature that no ref shares (wrong object class, new
    structure). The tool will confirm NOT_FOUND.

JSON SCHEMA (every turn):
{{
  "thought": "<one or two sentences>",
  "initial_score":                <float 0..1; turn 1 only>,
  "candidate_features":           [{{...}}, ...] | null,
  "refutation_target":            <int|null>,
  "refutation_verdict":           "found_in_ref"|"not_found"|"inconclusive"|null,
  "feature_status_update":        "<one sentence>"|null,
  "remaining_candidate_features": [{{...}}, ...] | null,
  "updated_score":                <float 0..1>|null,
  "action":                       "call_tool"|"final",
  "tool":                         "<tool_name>"|null,
  "args":                         {{...}}|null,
  "confidence":                   <0..100>,
  "score":                        <float 0..1 required when action=='final'>,
  "rationale":                    "<one or two sentences required when final>"
}}

Return ONLY a JSON object.
"""


def forced_final_prompt(budget):
    return (f"THIS IS YOUR LAST TURN ({budget}/{budget}). action MUST be "
            f"\"final\". Set score=updated_score (or initial_score if no "
            f"update happened). If remaining_candidate_features is empty, "
            f"score should be low (0.05-0.20).")


def budget_warning_prompt(remaining):
    if remaining <= 1:
        return "1 turn remaining — finalise now."
    return f"{remaining} turns remaining."
