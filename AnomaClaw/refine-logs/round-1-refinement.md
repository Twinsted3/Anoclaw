# Round 1 Refinement

## Problem Anchor
- **Bottom-line problem**: Current VLM-based AD methods are either single-pass (systematic FP bias, Spe<20%) or fine-tuned (losing cross-domain generalizability). No training-free multi-agent system exists for cross-domain visual AD.
- **Must-solve bottleneck**: VLMs conflate "visually different from reference" with "anomalous." They lack domain-adaptive reasoning about what constitutes a genuine anomaly vs. normal variation.
- **Non-goals**: (1) Model training/fine-tuning. (2) Pipeline automation. (3) Replacing traditional AD models. (4) Pixel-level segmentation.
- **Constraints**: Training-free (frozen VLM APIs). k=4 references. 7 domains. Target NeurIPS 2026 / AAAI 2027.
- **Success condition**: BA>70% across all domains, Spe>50% everywhere, qualitative evidence of reasoning-based FP correction.

## Anchor Check
- Original bottleneck: VLMs' false-positive bias from conflating "different" with "anomalous"
- Why the revised method still addresses it: Reference-grounded normality constraints directly provide the missing knowledge of "what counts as normal variation" vs "what counts as genuine anomaly"
- Reviewer suggestions rejected as drift: NONE — reviewer's reframing sharpens the contribution without changing the problem

## Simplicity Check
- Dominant contribution after revision: **Reference-Grounded Normality Constraints (RGNC)** — structured normality profiles built from few-shot references that condition VLM reasoning
- Components removed: bbox from claims, "once per domain" amortization (now per-reference-set), 4th profile bucket (caveats merged into benign_variations)
- Reviewer suggestions rejected as unnecessary complexity: None — all suggestions simplify
- The mechanism is still smallest adequate: ONE new component (normality profile) that conditions existing VLM inference

## Changes Made

### 1. Reframed contribution: "Domain-Grounded Debate" → "Reference-Grounded Normality Constraints"
- Reviewer said: Paper doesn't isolate whether gain comes from profile or debate. If profile-conditioned single-pass works, debate is decorative.
- Action: Reframe main contribution as RGNC. Debate becomes one optional verifier, validated by 2×2 factorial.
- Reasoning: The normality profile IS the mechanism. Debate is just one way to apply it.
- Impact: Sharper, more defensible claim.

### 2. Tightened protocol specification
- Reviewer said: "Phase 1 once per domain" conflicts with per-query references. Score formula inconsistent.
- Action: Profile built from exact reference set available at inference. Fixed 3-bucket schema via structured output. Single score formula defined.
- Reasoning: Eliminates evaluation leakage and ambiguity.
- Impact: Reproducible, implementable protocol.

### 3. Added 2×2 factorial ablation
- Reviewer said: Missing the key ablation to prove what the mechanism is.
- Action: Core experiment is now {baseline, profile-only, debate-only, profile+debate} at k=4.
- Reasoning: This cleanly isolates whether the gain comes from profile, debate, or both.
- Impact: Stronger evidence for the contribution claim.

### 4. Removed unnecessary elements
- Reviewer said: bbox unnecessary, benchmark as contribution dilutes focus.
- Action: Removed bbox. Benchmark moved from "contribution" to "evaluation setting."
- Impact: Tighter paper scope.

## Revised Proposal

# Research Proposal: AnomaClaw — Reference-Grounded Normality Constraints for Training-Free Cross-Domain Visual Anomaly Detection

## Problem Anchor
[Same as above — verbatim]

## Technical Gap
[Same root cause analysis as round 0]

The failure has two components: (1) perception bias (VLMs report all differences), (2) missing domain grounding (no knowledge of what "normal variation" means). The smallest fix is a structured normality profile that provides this missing grounding.

## Method Thesis
- **One-sentence thesis**: Reference-grounded normality constraints — structured profiles of normal visual patterns, benign variations, and anomaly indicators derived from few-shot references — fix VLMs' false-positive bias in cross-domain anomaly detection without any training.
- **Why smallest adequate**: ONE new component (the normality profile) conditions existing VLM inference. No new models, no training, no external tools.
- **Why timely**: Modern VLMs have the visual and reasoning capacity for AD but lack domain-specific grounding. A structured profile is the most natural way to inject this grounding via prompting, leveraging the VLM's own structured output capability.

## Contribution Focus
- **Dominant contribution**: Reference-Grounded Normality Constraints (RGNC) — a structured normality profile built from few-shot references that conditions frozen VLM reasoning, resolving the sensitivity-specificity tradeoff.
- **Supporting contribution**: Empirical analysis showing when and why multi-agent debate is additionally beneficial on top of RGNC (2×2 factorial).
- **Evaluation setting** (not a contribution): Cross-domain AD benchmark across 7 domains with few-shot scaling study.

## Proposed Method

### Complexity Budget
- **Frozen/reused**: VLM backbone (GPT-5.4, SeedVL-2.0) via API, with structured output / function-calling
- **New**: Normality Profile schema + two prompt templates (profiler, verifier). Zero trainable parameters.
- **Excluded**: bbox, fine-tuning, external AD models, Zoomer tools

### System Overview

```
Input: query image Q + reference set R = {r_1, ..., r_k}  (k=4)

Step 1: Build Normality Profile (per reference set, cached)
  NP = VLM.structured_output(
    images = R,
    schema = NormalityProfile
  )
  
Step 2: Profile-Conditioned Inspection
  Variant A (single-pass): 
    result = VLM.structured_output(
      images = R + [Q],
      context = NP,
      schema = InspectionResult
    )
  
  Variant B (with verifier):
    claims = VLM.structured_output(  # Advocate
      images = R + [Q],
      context = NP,
      schema = AnomalyClaims
    )
    verdict = VLM.structured_output(  # Verifier
      context = NP + claims,
      images = [Q],
      schema = VerifierVerdict
    )
    result = aggregate(claims, verdict)
```

### Core Mechanism: Normality Profile

**Schema** (3 buckets, structured output):
```json
{
  "normal_patterns": [
    "string: visual characteristic shared across normal references"
  ],
  "benign_variations": [
    "string: variation that is still normal (e.g., lighting, angle, artifact)"
  ],
  "red_flags": [
    "string: indicator of genuine anomaly in this domain"
  ]
}
```

**Construction**: Built from the exact k reference images available at inference. Not pooled across the dataset. Cached only when the same reference set is reused.

**Conditioning**: The profile is prepended as structured context to both the advocate and verifier prompts. It provides:
1. What to expect (normal_patterns) → reduces surprise-based FPs
2. What to ignore (benign_variations) → prevents flagging normal variation
3. What to flag (red_flags) → preserves sensitivity for genuine anomalies

### Inspection Protocol

**Variant A: Profile-Conditioned Single-Pass (RGNC)**
```
Prompt: "You are inspecting a {domain_context}.
         Here is the normality profile for this domain: {NP}
         Reference images show the normal state.
         Examine the query image.
         If it matches normal_patterns and any differences are benign_variations, label NORMAL.
         If it shows red_flags not explainable as benign_variations, label ANOMALOUS."
         
Output schema:
{
  "label": "normal" | "anomalous",
  "evidence": "string",
  "matched_pattern": "which normal_pattern or red_flag matched",
  "confidence": float 0-1
}
```

**Variant B: Profile-Conditioned Debate (RGNC+D)**
Step 2a — Advocate: Same as V1 but with NP context. Outputs claims with `matched_red_flag` field.
Step 2b — Verifier: Receives NP + claims. For each claim, checks against `benign_variations`. Returns `{claim_id, refute_confidence, justification}`.
Step 2c — Score: `score = max_claim(confidence × (1 - refute_confidence))`. Label = score > 0.5.

### Why this works
The normality profile acts as a **domain-specific decision boundary** expressed in natural language:
- Below the boundary (benign_variations): ignore
- Above the boundary (red_flags): flag

This is analogous to how human inspectors learn: first understand what "normal" looks like, then know what "defective" looks like, and only then inspect new items against that mental model.

### Failure Modes
1. **Insufficient references** (k<2): Profile too narrow → min k=4
2. **VLM hallucination in profile**: May invent non-existent patterns → validated by cross-checking profile against reference images
3. **Ambiguous domains**: Some anomalies are genuinely borderline → profile acknowledges this in benign_variations (e.g., "minor asymmetry is normal for skin nevi")

## Claim-Driven Validation Sketch

### Claim 1 (Main): RGNC fixes false-positive bias
- **2×2 factorial at k=4**:
  | | No Profile | With Profile (RGNC) |
  |---|---|---|
  | Single-pass | V0 baseline | **Variant A** |
  | With debate | V3 | **Variant B** |
- **Metric**: Per-domain AUROC, Specificity, Balanced Accuracy
- **Expected**: RGNC (Variant A) > V0, and Variant B > V3. Profile effect > debate effect.

### Claim 2 (Supporting): Profile quality scales with references
- **k=2, 4, 8 ablation** with Variant A
- **Expected**: Monotonic improvement, diminishing returns after k=4

### Claim 3 (Analysis): When is debate additionally helpful?
- **Compare Variant A vs Variant B** per domain
- **Expected**: Debate helps on domains with fine-grained anomalies (D1, D4), less so on semantic domains (D7, D8)

## Compute & Timeline
- API cost: ~$80 for full 2×2 × 6 domains × 120 items
- Timeline: 1 week experiments, 2 weeks paper
