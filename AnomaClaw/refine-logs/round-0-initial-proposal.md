# Research Proposal: AnomaClaw — Training-Free Multi-Agent Visual Anomaly Detection via Domain-Grounded Debate

## Problem Anchor
- **Bottom-line problem**: Current VLM-based AD methods are either single-pass (systematic FP bias, Spe<20%) or fine-tuned (losing cross-domain generalizability). No training-free multi-agent system exists for cross-domain visual AD.
- **Must-solve bottleneck**: VLMs conflate "visually different from reference" with "anomalous." They lack domain-adaptive reasoning about what constitutes a genuine anomaly vs. normal variation.
- **Non-goals**: (1) Model training/fine-tuning. (2) Pipeline automation. (3) Replacing traditional AD models. (4) Pixel-level segmentation.
- **Constraints**: Training-free (frozen VLM APIs). k=4 references. 7 domains. Target NeurIPS 2026 / AAAI 2027.
- **Success condition**: BA>70% across all domains, Spe>50% everywhere, qualitative evidence of reasoning-based FP correction.

## Technical Gap

### Current Pipeline Failure Point
Single-pass VLM inspection (our V0 baseline) achieves high sensitivity (>90%) but catastrophically low specificity (<20%) on most domains. The VLM reports every visual difference as an anomaly — a different product variant, normal anatomical variation, lighting change, or background clutter all trigger false positives.

### Why Naive Fixes Are Insufficient
- **More references (k=2→4→8)**: Our ablation shows k=4 is optimal (AUROC 0.71→0.80), but specificity plateaus. More images help the VLM understand "normal range" but don't fix the reasoning flaw.
- **Better prompts**: Our domain-specific prompts (D5 medical) improved Spe from 10%→40% but AUROC stayed at 0.47. Prompts can't inject domain expertise the VLM doesn't have.
- **Simple debate (V3 advocate+skeptic)**: Improves specificity (+20-40%) on clear domains (D1, D4, D7) but overcorrects on ambiguous domains (D2, D5, D8), collapsing sensitivity. The skeptic has no principled basis for distinguishing genuine anomalies from normal variation.

### Root Cause Analysis
The failure has two independent components:
1. **Perception bias**: VLMs are biased toward reporting differences (trained on "spot the difference" tasks). This is an inherent model behavior, not fixable by prompting alone.
2. **Missing domain grounding**: The skeptic in V3 debate is generic — it challenges claims without domain-specific knowledge of what "normal variation" means. Without grounding, it either under-challenges (preserving FPs) or over-challenges (killing TPs).

### Smallest Adequate Intervention
**Domain-Grounded Debate**: A two-phase system where Phase 1 builds a domain-specific "normality profile" from references, and Phase 2 uses this profile to ground the debate. The profile provides the missing domain knowledge that prevents the skeptic from being either too permissive or too aggressive.

## Method Thesis
- **One-sentence thesis**: Domain-grounded debate — where a normality profile learned from few-shot references anchors the skeptic's reasoning — is the minimal mechanism that fixes VLMs' false-positive bias while preserving sensitivity across diverse domains.
- **Why smallest adequate**: Only one new component (the normality profiler) is added to the existing advocate-skeptic debate. Everything else is frozen VLM inference.
- **Why timely**: Foundation models have the reasoning capacity for debate but lack domain grounding — our profiler fills exactly this gap without any training.

## Contribution Focus
- **Dominant contribution**: Domain-Grounded Debate (DGD) — a training-free multi-agent protocol where a normality profiler provides domain-specific context to anchor the skeptic agent's reasoning, resolving the sensitivity-specificity tradeoff in VLM-based AD.
- **Supporting contribution**: Cross-domain AD benchmark with systematic few-shot scaling study (k=2/4/8) across 7 diverse domains.
- **Explicit non-contributions**: Not a new model architecture. Not a new training objective. Not pixel-level localization.

## Proposed Method

### Complexity Budget
- **Frozen/reused**: VLM backbone (GPT-5.4, SeedVL-2.0) — used as-is via API
- **New components**: (1) Normality Profiler prompt template, (2) Grounded Skeptic prompt template. Both are prompt engineering, zero trainable parameters.
- **Tempting additions intentionally excluded**: (a) Perceptive Zoomer tool (AgentIAD) — adds implementation complexity, orthogonal to our contribution; (b) fine-tuning on AD data (AD-Copilot) — violates our training-free constraint; (c) traditional AD model as expert (EAGLE) — adds dependency on pre-trained models.

### System Overview

```
Input: query image + k=4 normal reference images

Phase 1: Domain Profiling (once per domain, amortized)
┌──────────────────────────────────┐
│ Normality Profiler Agent         │
│ Input: k reference images        │
│ Output: NormalityProfile JSON    │
│   - visual_characteristics[]     │
│   - acceptable_variations[]      │
│   - genuine_anomaly_indicators[] │
│   - domain_specific_caveats[]    │
└──────────────────────────────────┘

Phase 2: Grounded Inspection (per query)
┌──────────────────────────────────┐
│ Step 2a: Advocate Agent          │
│ Input: profile + refs + query    │
│ Output: anomaly claims[]         │
│   {type, evidence, confidence,   │
│    bbox, profile_violation}      │
│                                  │
│ Step 2b: Grounded Skeptic Agent  │
│ Input: profile + claims + query  │
│ Output: rebuttals[]              │
│   {refute_confidence,            │
│    profile_justification,        │
│    likely_cause}                  │
│                                  │
│ Step 2c: Score Aggregation       │
│ score = max(conf - refute_conf)  │
│ label = score > 0.5              │
└──────────────────────────────────┘
```

### Core Mechanism: Domain-Grounded Debate

**Phase 1: Normality Profiler**

The profiler analyzes all k reference images and produces a structured JSON profile:
```json
{
  "domain_summary": "dermoscopic images of skin lesions",
  "visual_characteristics": [
    "small symmetric round/oval shape",
    "uniform brown/tan coloring",
    "regular smooth borders",
    "homogeneous pigment distribution"
  ],
  "acceptable_variations": [
    "slight color variation from light to dark brown",
    "hair artifacts overlaying the lesion",
    "different lesion sizes (2-8mm)",
    "minor asymmetry in benign nevi"
  ],
  "genuine_anomaly_indicators": [
    "highly irregular/jagged borders",
    "multicolor pattern (blue, white, red within one lesion)",
    "marked asymmetry in shape or color",
    "diameter >6mm with uneven features"
  ],
  "domain_caveats": [
    "lighting and camera angle can create apparent asymmetry",
    "dermoscopic artifacts (bubbles, ruler marks) are not anomalies"
  ]
}
```

This profile is generated ONCE per domain (amortized across all queries in that domain).

**Phase 2a: Advocate Agent (Profile-Aware)**

Unlike V0/V1 which simply compare query to references, the Advocate receives the normality profile and must:
1. First describe what normal looks like (from the profile)
2. Then identify deviations that match the profile's `genuine_anomaly_indicators`
3. Each claim must include a `profile_violation` field explaining which indicator was triggered

**Phase 2b: Grounded Skeptic Agent**

The key innovation. Unlike V3's generic skeptic, this skeptic receives both the normality profile and the advocate's claims. For each claim, it must:
1. Check whether the claimed anomaly matches any `acceptable_variations` in the profile
2. Check whether the evidence is consistent with `domain_caveats` (e.g., lighting artifacts)
3. Only assign high refute_confidence if the claim can be explained by profile-defined normal variation
4. Preserve low refute_confidence (i.e., agree with advocate) when the anomaly matches `genuine_anomaly_indicators`

This grounding prevents:
- Over-challenging (killing TPs): because the skeptic knows what genuine anomalies look like
- Under-challenging (preserving FPs): because the skeptic knows what normal variation looks like

**Phase 2c: Score Aggregation**

Same as V3: `score = max(claim_conf - refute_conf) + 0.5`, clipped to [0, 1].

### Why the mechanism stays small
- Phase 1 is a single VLM call per domain (amortized to near-zero cost per item)
- Phase 2 is exactly two VLM calls per item (same as V3)
- Total cost: 2 API calls per item + 1 amortized call per domain
- No new models, no training, no external tools, no databases

### Exact role of the VLM
The VLM serves as both the perception engine and the reasoning engine. It is used in three roles:
1. **Domain analyst** (Phase 1): Synthesizes visual patterns from reference images into a structured profile
2. **Anomaly advocate** (Phase 2a): Detects visual deviations, grounded by the profile
3. **Anomaly skeptic** (Phase 2b): Challenges claims, grounded by the profile

The VLM is never fine-tuned. The profile serves as a "soft domain adapter" that conditions the VLM's reasoning without changing its weights.

### Failure Modes and Diagnostics
1. **Profile quality degrades with insufficient references**: If k<2, the profile may be too narrow. Mitigation: minimum k=4 requirement, validated by ablation.
2. **Collective delusion** (M3MAD-Bench finding): Both advocate and skeptic may agree on a wrong answer. Mitigation: the profile provides an external anchor independent of the query, reducing model self-agreement.
3. **Profile doesn't capture domain complexity**: Some domains (medical) have nuanced normality that k=4 images can't fully represent. Mitigation: include `domain_caveats` in the profile that explicitly flag ambiguous cases.

### Novelty and Elegance Argument
**Closest work**:
- AgentIAD: Single agent + tools. No debate, no domain profiling.
- AD-Copilot: Fine-tuned comparison encoder. Not training-free.
- EAGLE: Uses PatchCore expert. Requires pre-trained AD model.
- V3 (our baseline): Generic debate without domain grounding. Specificity improvement but sensitivity collapse.

**Exact difference**: DGD adds ONE component (the normality profile) that serves as a shared grounding context for both agents. This is not "another module" — it is a structured prompt context derived from the reference images. The key insight is that the sensitivity-specificity tradeoff in VLM debate is caused by ungrounded reasoning, and grounding through a normality profile is the minimal fix.

## Claim-Driven Validation Sketch

### Claim 1: DGD improves specificity without sacrificing sensitivity
- **Minimal experiment**: Compare V0 (baseline), V3 (ungrounded debate), DGD across 6 domains, k=4, GPT-5.4
- **Metric**: Per-domain AUROC, Sensitivity, Specificity, Balanced Accuracy
- **Expected evidence**: DGD achieves BA>70% on all domains where V3 achieves BA<60% (D2, D5, D8)

### Claim 2: Domain profiling is the key mechanism (ablation)
- **Minimal experiment**: DGD-full vs DGD-no-profile (debate without profile, same as V3) vs DGD-generic-profile (same profile for all domains)
- **Metric**: AUROC difference
- **Expected evidence**: DGD-full > DGD-generic-profile > DGD-no-profile, showing domain-specific profiling matters

### Claim 3: Few-shot scaling (supporting)
- **Minimal experiment**: k=2, k=4, k=8 ablation across domains with DGD
- **Metric**: AUROC vs k
- **Expected evidence**: Diminishing returns after k=4, confirming our benchmark design choice

## Experiment Handoff Inputs
- **Must-prove claims**: (1) DGD > V3 on specificity, (2) Profile ablation shows grounding matters
- **Must-run ablations**: (1) k=2/4/8, (2) with/without profile, (3) generic vs domain-specific profile
- **Critical datasets**: D1-D8 benchmark (excluding D6 pending replacement)
- **Highest-risk assumption**: That the VLM can generate a useful normality profile from only 4 reference images

## Compute & Timeline Estimate
- **GPU-hours**: 0 (API-only)
- **API cost**: ~$50-100 for full benchmark run (GPT-5.4 via sub2api)
- **Timeline**: 1 week for full experimental validation, 2 weeks for paper writing
