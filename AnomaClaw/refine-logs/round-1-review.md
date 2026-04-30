# Round 1 Review (GPT-5.4)

## Scores

| Dimension | Score |
|-----------|-------|
| Problem Fidelity | 8/10 |
| Method Specificity | 6/10 |
| Contribution Quality | 6/10 |
| Frontier Leverage | 8/10 |
| Feasibility | 8/10 |
| Validation Focus | 6/10 |
| Venue Readiness | 6/10 |
| **Overall** | **6.8/10** |

## Verdict: REVISE

## Key Criticisms

### CRITICAL: Method Specificity (6/10)
- "Phase 1 once per domain" conflicts with "query + k references" input
- Score formula inconsistent (max(conf-refute) vs +0.5)
- bbox unnecessary for image-level AD
- **Fix**: Define conditioning unit as exact reference set. Remove bbox. Fixed schema. One score formula.

### CRITICAL: Contribution Quality (6/10)
- Paper doesn't isolate whether gain comes from profile or debate
- If profile-conditioned single-pass works, debate is decorative
- **Fix**: Reframe as "reference-induced domain grounding" as main contribution. Debate is one verifier option, only if ablations prove it necessary.

### IMPORTANT: Validation Focus (6/10)
- Missing 2x2 factorial: {baseline, profile only, debate only, profile+debate}
- **Fix**: Run the 2x2 factorial at k=4.

### IMPORTANT: Venue Readiness (6/10)
- Can be dismissed as "prompt recipe"
- **Fix**: Schema-constrained structured output. Reproducible profile. One clean claim.

## Simplification Opportunities
1. Delete bbox from claim schema
2. Collapse profile to 3 buckets: normal_patterns, benign_variations, red_flags
3. Build profile from query-available references, not domain-wide pool

## Modernization Opportunities
1. Use structured output / function-calling for profile and claims
2. Replace score subtraction with single verifier entailment judgment
3. Keep foundation-model native — delete and replace with stronger structured VLM inference

## Drift Warning: NONE

## Strongest Version (reviewer's suggestion)
"Reference-grounded normality constraints fix false-positive bias in frozen VLM anomaly detection, with debate used only if empirically necessary."

<details>
<summary>Raw Reviewer Response</summary>

This is closer to viable than most early proposals because it identifies a real bottleneck and adds a small intervention. The main risk is not problem drift; it is that the paper currently does not cleanly establish whether the contribution is `domain grounding` or `multi-agent debate`, and the protocol is not yet specified tightly enough for a top-venue method paper.

[Full response saved in REFINE_STATE context]

</details>
