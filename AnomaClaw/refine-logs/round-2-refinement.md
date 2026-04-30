# Round 2 Refinement

## Problem Anchor (Updated per reviewer guidance)
- **Bottom-line problem**: Frozen VLMs used for visual anomaly detection suffer from systematic false-positive bias (Specificity<20%) because they conflate any visual difference from references with anomaly, lacking domain-grounded reasoning about normal variation.
- **Must-solve bottleneck**: VLMs lack domain-specific knowledge of what constitutes "normal variation" vs "genuine anomaly." This knowledge cannot be injected by prompting alone or by simply adding more references.
- **Non-goals**: (1) Model training/fine-tuning. (2) Pipeline automation. (3) Pixel-level segmentation.
- **Constraints**: Training-free (frozen VLM APIs). k=4 references. 7 domains.
- **Success condition**: BA>70% across all domains, Spe>50% everywhere, with ablation evidence that the structured normality profile is the causal mechanism.

## Anchor Check
- Original bottleneck: FP bias from ungrounded VLM reasoning
- Revised anchor removes "multi-agent" framing — the problem is about grounding, not about number of agents
- All reviewer changes accepted — they sharpen the anchor

## Simplicity Check
- Dominant contribution: RGNC (Reference-Grounded Normality Constraints)
- Variant A (single-pass with profile) is the **main method**
- Variant B (with verifier) is an optional extension, only promoted if ablation shows clear lift
- Components removed: "multi-agent" from problem statement, debate from main contribution
- Profile items now cite reference indices for inspectability

## Revised Proposal

# AnomaClaw: Reference-Grounded Normality Constraints for Training-Free Visual Anomaly Detection

## Problem Anchor
[Updated — see above]

## Method Thesis
Structured normality constraints — profiles of normal patterns, benign variations, and red flags, each grounded to specific reference images — fix VLMs' false-positive bias in cross-domain anomaly detection without any training. The key insight is that VLMs have the perceptual and reasoning capacity for AD but lack a domain-specific decision boundary; RGNC provides this boundary as a natural-language constraint set derived from few-shot references.

## Contribution Focus
- **Dominant**: RGNC — a structured, reference-grounded constraint set that conditions frozen VLM inspection. Not just "better prompting" — it is a constraint schema with grounded evidence links, validated by a structure-vs-length control.
- **Supporting**: Analysis of when additional verification (claim checking) helps on top of RGNC.
- **Evaluation setting**: Cross-domain AD benchmark, 6 domains, k=2/4/8 scaling.

## Method

### Step 1: Build Normality Profile

Input: k=4 reference images R = {r_1, r_2, r_3, r_4}

The VLM produces a **cited constraint set** via structured output:

```json
{
  "normal_patterns": [
    {"pattern": "symmetric round/oval lesion shape", "evidence_refs": [1, 2, 3, 4]},
    {"pattern": "uniform brown pigmentation", "evidence_refs": [1, 3]}
  ],
  "benign_variations": [
    {"variation": "slight color range from light to dark brown", "evidence_refs": [2, 4]},
    {"variation": "hair artifacts overlaying lesion", "evidence_refs": [3]}
  ],
  "red_flags": [
    {"flag": "highly irregular/jagged borders", "distinguishes_from": "normal_patterns[0]"},
    {"flag": "multicolor pattern (blue, white, red)", "distinguishes_from": "normal_patterns[1]"}
  ]
}
```

Key design choices:
- Each normal_pattern and benign_variation cites which reference images support it (`evidence_refs`)
- Each red_flag explicitly states which normal_pattern it contrasts with (`distinguishes_from`)
- This makes the profile **inspectable** and **grounded**, not just free-text prose

Construction: from the exact k references available at inference. Cached when same reference set repeats.

### Step 2: Profile-Conditioned Inspection (Main Method: RGNC)

```
Prompt:
  "You are inspecting a {domain}. 
   Normality profile (from reference images): {NP}
   Reference images: [r_1, ..., r_k]
   Query image: [Q]
   
   Compare the query to the references using the normality profile:
   - If query matches normal_patterns and differences are benign_variations → NORMAL
   - If query shows red_flags not explainable as benign_variations → ANOMALOUS
   
   Output (structured):"
   
Output schema:
{
  "label": "normal" | "anomalous",
  "reasoning": "string",
  "matched_constraint": "constraint_id that determined the verdict",
  "anomaly_score": float 0-1
}
```

Single VLM call. Total cost per item: 1 API call (+ 1 amortized profile call per reference set).

### Step 2b (Optional Extension): Claim Verification

If RGNC single-pass is insufficient (validated by ablation):

```
Step 2b-i: Advocate produces claims with matched_red_flag
Step 2b-ii: Verifier checks claims against benign_variations + reference images R
  (Verifier gets R to recover from profile errors)
Step 2b-iii: Score = max_claim(confidence × (1 - refute_confidence))
```

Total cost: 2 API calls per item. Only used if 2×2 ablation shows clear lift.

### Why RGNC is more than prompting

The anti-pseudo-novelty argument:

| Approach | What it does | Why it's different from RGNC |
|----------|-------------|------------------------------|
| Better prompt | Tells VLM "look for defects" | No domain-specific constraint set |
| Domain hint | Tells VLM "this is a skin lesion" | No structured boundary between normal and anomalous |
| More references | Shows VLM more normal examples | VLM still lacks explicit reasoning about what variation is acceptable |
| **RGNC** | **Provides grounded constraint set with cited evidence** | **Explicit decision boundary: normal_patterns vs red_flags, each grounded to references** |

**Control experiment**: Same VLM, same token budget, but unstructured free-text normality summary instead of structured RGNC. If RGNC wins, the structure (not the extra text) is the mechanism.

## Validation

### Core: 2×2 Factorial + Structure Control (k=4, GPT-5.4, 6 domains)

| Method | Profile | Verifier | Expected BA |
|--------|---------|----------|-------------|
| V0 Baseline | No | No | ~60% |
| RGNC (Variant A) | **Structured** | No | **>70%** |
| Debate-only (V3) | No | Yes | ~65% |
| RGNC+V (Variant B) | **Structured** | Yes | ≥Variant A |
| Unstructured summary | Free-text | No | <Variant A |

The last row is the **anti-pseudo-novelty control**.

### Supporting: k-scaling
k=2, 4, 8 with RGNC. Expected: diminishing returns after k=4.

### Analysis: Per-domain debate benefit
Compare A vs B per domain. Report when verification helps.

## Compute
- API: ~$100 for full matrix
- Timeline: 1 week experiments, 2 weeks paper
