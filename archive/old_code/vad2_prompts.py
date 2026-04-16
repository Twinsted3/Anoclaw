
# AnomalyClaw Adversarial Debate Prompts
# Design:
# - 2 model calls per round (Proposer + Advocate)
# - Strict JSON output for rule-based aggregation
# - Expert evidence injected as text context


PROPOSER_SYSTEM = (
    "You are the Anomaly Proposer in an adversarial anomaly detection system. "
    "Your task: compare normal reference images with the query image, using any provided expert evidence, "
    "and identify ALL potential anomalies with detailed justification. "
    "If the image is normal, describe the object's structure and function. "
    "Output MUST be strict JSON (no markdown, no extra text)."
)


ADVOCATE_SYSTEM = (
    "You are the Normality Advocate in an adversarial anomaly detection system. "
    "Your sole objective: argue that each proposed anomaly is NOT actually anomalous. "
    "Challenge every claim with counter-evidence: lighting, angle, compression, texture variation, "
    "manufacturing tolerance, or other benign explanations. "
    "Only concede (low refute_confidence) when the evidence for anomaly is truly overwhelming. "
    "Output MUST be strict JSON (no markdown, no extra text)."
)

# Legacy alias for backward compatibility
REFUTER_SYSTEM = ADVOCATE_SYSTEM

MMAD_ANSWERER_SYSTEM = (
    "You are an industrial visual QA assistant. You will receive: normal sample images, query images, "
    "and a structured detection report (normal_profile + anomalies + decisions). "
    "Your task is to answer MMAD multiple-choice questions. Output strict JSON only."
)


def proposer_cold(expert_reports: str = "", domain_knowledge: str = "") -> str:
    """Generate cold-start proposer prompt with optional expert evidence."""
    base = """Compare the normal reference images with the query image and output the following (anomaly list may be empty):

Requirements:
- Output JSON only
- MUST output normal_profile (even if anomalies exist)
- Each anomaly must be "verifiable": clear location and visible evidence
- Location uses normalized bbox: [x1,y1,x2,y2] (0~1), plus relative description (e.g., top-left/center/edge)
- For anomalies: category, appearance, evidence, analysis (likely_cause, impact)
- For normal profile: category, location, appearance, components, structure, function
- Confidence (0~1) and severity (0~1) for each anomaly"""

    if domain_knowledge:
        base += f"\n\n<DOMAIN_KNOWLEDGE>\n{domain_knowledge}\n</DOMAIN_KNOWLEDGE>"

    if expert_reports:
        base += f"\n\n<EXPERT_EVIDENCE>\n{expert_reports}\n</EXPERT_EVIDENCE>"
        base += "\nUse the expert evidence above as quantitative grounding for your assessment. "
        base += "The expert provides patch-level distance scores and similarity metrics that you cannot compute from pixels alone. "
        base += "However, you retain full decision authority — discount the expert when visual evidence contradicts it."

    base += """

Output schema (follow strictly):
{
  "normal_profile": {
    "category": "string",
    "location": {"bbox": [0.0,0.0,1.0,1.0], "relative": "string"},
    "appearance": "string",
    "components": ["string"],
    "structure": "string",
    "function": "string"
  },
  "claims": [
    {
      "id": "A1",
      "category": "other",
      "location": {"bbox": [0.0,0.0,1.0,1.0], "relative": "string"},
      "appearance": "string",
      "evidence": "string",
      "analysis": {"likely_cause": "string", "impact": "string"},
      "confidence": 0.0,
      "severity": 0.0
    }
  ]
}"""
    return base.strip()


# Backward-compatible constant (no expert evidence)
PROPOSER_COLD = proposer_cold()


def proposer_iterative(tbd_claims_json: str, expert_reports: str = "") -> str:
    prompt = (
        "Below are anomalies marked TBD from the previous round (JSON). "
        "For each one, rewrite more precisely:\n"
        "- Keep the same id for each claim\n"
        "- Improve verifiability: more precise bbox, object part, visible evidence comparison\n"
        "- Do NOT add unrelated new anomalies (unless you have clear evidence)\n"
        "- Preserve and output normal_profile as-is\n"
        "Output JSON with the same schema as cold_start.\n\n"
    )
    if expert_reports:
        prompt += f"<EXPERT_EVIDENCE>\n{expert_reports}\n</EXPERT_EVIDENCE>\n\n"
    prompt += f"<TBD_CLAIMS_JSON>\n{tbd_claims_json}\n</TBD_CLAIMS_JSON>"
    return prompt


def advocate_prompt(claims_json: str) -> str:
    """Normality Advocate prompt — challenge each anomaly claim."""
    return (
        "You will receive a list of anomaly claims (JSON). For each claim, provide your "
        "rebuttal or concession:\n"
        "- refute_confidence: 0~1 (higher = more confident this is NOT an anomaly)\n"
        "- Challenge with specific counter-evidence: lighting reflection, viewing angle, "
        "compression artifact, normal texture variation, manufacturing tolerance, etc.\n"
        "- If you cannot refute (it genuinely looks anomalous), explain why and give low refute_confidence\n"
        "Output JSON only, schema:\n"
        "{\n"
        '  "reviews": [\n'
        "    {\n"
        '      "id": "A1",\n'
        '      "refute_confidence": 0.0,\n'
        '      "counter_evidence": "string",\n'
        '      "likely_cause": "normal_variation|lighting|viewpoint|compression|occlusion|unknown|genuine_anomaly"\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        f"<CLAIMS_JSON>\n{claims_json}\n</CLAIMS_JSON>"
    )

# Legacy alias
def refuter_prompt(claims_json: str) -> str:
    return advocate_prompt(claims_json)


def calibration_round_prompt() -> str:
    """Prompt the Proposer to examine normal reference images and characterize normal variation."""
    return """You are examining NORMAL reference images (confirmed non-anomalous).
Your task: characterize what "normal" looks like for this category so that
an anomaly reviewer can distinguish genuine anomalies from normal variation.

Examine the reference images carefully and output JSON describing:

1. normal_variation_profile: What visual variations exist AMONG these normal samples?
   - Color/brightness range, texture patterns, shape variation, surface features
2. false_positive_flags: Features that MIGHT look anomalous to an untrained eye but are
   actually normal for this category. Be specific about visual features you observe.
3. typical_appearance: A concise canonical description of what this object/scene looks like.

Output strict JSON only:
{
  "normal_variation_profile": {
    "color_range": "string describing color/brightness variation among normals",
    "texture_patterns": "string describing texture variation among normals",
    "shape_variation": "string describing shape/size variation among normals",
    "surface_features": "string describing surface characteristics and normal imperfections"
  },
  "false_positive_flags": [
    {"feature": "specific visual feature", "reason_not_anomalous": "why this is normal"}
  ],
  "typical_appearance": "concise canonical description"
}""".strip()


def advocate_prompt_calibrated(claims_json: str, calibration_evidence: str) -> str:
    """Enhanced Advocate prompt with normal calibration evidence for grounded refutation."""
    return (
        "You will receive a list of anomaly claims (JSON). For each claim, provide your "
        "rebuttal or concession.\n\n"
        "IMPORTANT: You have calibration data from confirmed NORMAL images of this category.\n"
        "Use this evidence to make GROUNDED refutations — not just generic counter-arguments.\n\n"
        f"<NORMAL_CALIBRATION>\n{calibration_evidence}\n</NORMAL_CALIBRATION>\n\n"
        "Refutation guidelines:\n"
        "- If a claimed anomaly matches a feature in the normal variation profile, refute with HIGH confidence\n"
        "- If a claimed anomaly matches a known false positive flag, refute with HIGH confidence\n"
        "- If the expert anomaly score is within the normal baseline range, cite this as evidence for normality\n"
        "- Only concede (low refute_confidence) when the evidence clearly exceeds normal variation\n\n"
        "For each claim:\n"
        "- refute_confidence: 0~1 (higher = more confident this is NOT an anomaly)\n"
        "- counter_evidence: specific reasoning grounded in the calibration data\n"
        "- likely_cause: normal_variation|lighting|viewpoint|compression|occlusion|unknown|genuine_anomaly\n\n"
        "Output JSON only, schema:\n"
        "{\n"
        '  "reviews": [\n'
        "    {\n"
        '      "id": "A1",\n'
        '      "refute_confidence": 0.0,\n'
        '      "counter_evidence": "string",\n'
        '      "likely_cause": "string"\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        f"<CLAIMS_JSON>\n{claims_json}\n</CLAIMS_JSON>"
    )


def judge_synthesis_prompt(
    claims_json: str, reviews_json: str,
    expert_evidence: str, calibration_evidence: str = ""
) -> str:
    """Judge prompt — synthesize all evidence into a single holistic anomaly assessment."""
    base = (
        "You are the Final Judge in an anomaly detection system. You have received:\n"
        "1. Anomaly claims from the Proposer\n"
        "2. Rebuttals from the Normality Advocate\n"
        "3. Expert evidence (quantitative analysis)\n"
    )
    if calibration_evidence:
        base += "4. Normal calibration data (what normal looks like for this category)\n"

    base += (
        "\nSynthesize ALL evidence and make a single, holistic judgment.\n"
        "Do NOT simply average scores — weigh the quality of arguments.\n"
        "A strong rebuttal grounded in normal calibration data should outweigh a vague anomaly claim.\n"
        "A precise anomaly claim with clear visual evidence that exceeds normal variation should stand.\n\n"
    )

    if calibration_evidence:
        base += f"<NORMAL_CALIBRATION>\n{calibration_evidence}\n</NORMAL_CALIBRATION>\n\n"

    base += f"<EXPERT_EVIDENCE>\n{expert_evidence}\n</EXPERT_EVIDENCE>\n\n"
    base += f"<ANOMALY_CLAIMS>\n{claims_json}\n</ANOMALY_CLAIMS>\n\n"
    base += f"<ADVOCATE_REVIEWS>\n{reviews_json}\n</ADVOCATE_REVIEWS>\n\n"

    base += (
        "Output strict JSON:\n"
        "{\n"
        '  "verdict": "normal" or "anomaly",\n'
        '  "confidence": 0.0-1.0,\n'
        '  "reasoning": "brief synthesis of key evidence"\n'
        "}"
    )
    return base


def mmad_answerer_prompt(questions_text: str, report_json: str) -> str:
    return (
        "Based on the images and the detection report below, answer the MMAD multiple-choice questions.\n"
        "- Output JSON only\n"
        "- Must include field mmad_answers\n"
        "- mmad_answers must be an array matching the number of questions\n"
        "- Each element is a single uppercase letter (A/B/C/D/E)\n\n"
        "Output schema:\n"
        '{\n  "mmad_answers": ["A"]\n}\n\n'
        f"<DETECTION_REPORT_JSON>\n{report_json}\n</DETECTION_REPORT_JSON>\n\n"
        f"<MMAD_QUESTIONS>\n{questions_text}\n</MMAD_QUESTIONS>"
    )
