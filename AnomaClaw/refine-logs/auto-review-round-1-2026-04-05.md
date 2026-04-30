# Autonomous Review Loop - Round 1

**Date**: 2026-04-05
**Reviewer mode**: senior ML reviewer (top-venue bar)
**Scope reviewed**: current 10-domain "AnomaClaw" agent direction, prior benchmark/design documents, current experiment tracker, and benchmark audit notes

## Bottom Line

- **Score**: `5/10` as a top-venue method paper in its current form
- **Verdict**: `Not ready`
- **Why**: the strongest empirical signal comes from retrieval, not from the agent. The current expert tool is too weak, the multi-call pipeline adds noise, and the "universal" claim is not yet supported by the current task mix and evidence package.

## What Is Currently Credible

1. Retrieval matters a lot. This is the cleanest positive result in the current system.
2. Cross-domain evaluation matters. The work is already showing that conclusions do not transfer cleanly across domains.
3. A pure LLM agent stack is not enough. The latest V3 result is useful negative evidence: more agent machinery can hurt.

## Ranked Critical Weaknesses and Minimum Fixes

### 1. The main claimed mechanism is not supported

The current evidence says the opposite of the intended method story: retrieval is strong, while extra agent structure does not produce a stable gain. Your own frozen paper framing argues for a minimal agent study without retrieval, routing, or tool stacks, but the current best system depends on retrieval and the latest tool-augmented agent regresses.

**Minimum fix**
- Run a decisive ablation that isolates:
  - retrieval only
  - retrieval + patch expert
  - retrieval + VLM
  - retrieval + patch expert + one VLM judge
  - current full agent
- Report macro AUROC, per-domain AUROC, cost, latency, and bootstrap confidence intervals.
- If the agent does not beat the simpler hybrid clearly, drop the "agent method" headline and reframe the paper as a benchmark plus hybrid design study.

### 2. "Universal anomaly detection" is too broad for the current task mix

You are mixing surface defects, semantic mismatches, medical lesions, logical anomalies, and natural-scene hazards into one macro number. That is acceptable for a benchmark, but not yet for a mechanism claim. Some domains are appearance-local, some are structural-relational, some are medically semantic. A single agent story across all of them is not demonstrated.

**Minimum fix**
- Partition the benchmark into at least three families:
  - local appearance anomaly
  - structural / logical anomaly
  - semantic / medical anomaly
- Report family-level results and claims separately.
- Make the universal claim modest: "one reference-based hybrid framework across multiple anomaly families," not "one mechanism explains all domains."

### 3. The expert signal is too weak to justify the tool pipeline

`1 - top1_similarity` on a global embedding is not a serious few-shot anomaly detector. It throws away location, alignment, local rarity, and score shape. That makes the Scout/Judge stages operate on weak evidence and amplifies LLM variance.

**Minimum fix**
- Replace the current expert with a proper dense patch-level few-shot AD tool.
- The first implementation should be:
  - retrieved normal refs
  - dense multi-scale DINOv2 patch features
  - kNN distance to a small reference patch bank
  - percentile pooling for image score
  - anomaly heatmap + top suspicious crops as outputs
- Compare this directly against the current global DINO score on all domains.

### 4. Fusion is ad hoc and the multi-call agent is too noisy

Right now the pipeline effectively asks several LLM stages to re-interpret uncertain evidence. Each call adds variance. The full V3 regression is exactly what I would expect from an under-grounded routed pipeline.

**Minimum fix**
- Collapse the pipeline to:
  - retrieval
  - one expert pass
  - optional one VLM adjudication pass only when the expert is uncertain
- Learn or calibrate the final fusion on the calibration split using a small model such as logistic regression or isotonic calibration, instead of hand-written score logic.

### 5. The evidence package is still below top-venue standard

You need stronger baselines and stronger statistics. Right now the paper does not yet answer the obvious reviewer question: "Why is this better than a proper few-shot AD model plus retrieval?"

**Minimum fix**
- Add at least these baselines:
  - DINOv2 PatchNN
  - PatchCore-style reference memory
  - WinCLIP-like patch matching baseline
  - a simple hybrid baseline: patch expert score + one VLM call
- Add bootstrap confidence intervals and significance on macro AUROC.
- Add a score-vs-cost plot.

### 6. Weak-domain diagnosis is incomplete

D5c liver and D9 LOCO are not just "bad domains"; they are diagnostic. Liver tests subtle local lesion sensitivity. LOCO tests structural and relational reasoning. If you cannot say exactly why each fails, the method is not mature.

**Minimum fix**
- For D5c: categorize failures into lesion too small, poor alignment, texture confusion, and contrast/phase mismatch.
- For D9: categorize failures into count, placement, missing part, wrong configuration, and benign view change.
- Show whether the patch expert or the VLM is responsible for each failure family.

## Recommended Few-Shot AD Integration

## Recommendation

Use a **retrieval-conditioned patch expert as the primary detector**, and keep the VLM as a **single-pass adjudicator only for uncertain or relational cases**.

If I had to choose one direction now, I would pick:

1. **Base expert**: PatchCore-style dense patch kNN over retrieved references using DINOv2 features.
2. **Add multi-scale pooling**: closer to WinCLIP in spirit, but keep the implementation simple and deterministic.
3. **Optional alignment branch**: only for stable-geometry domains such as brain MRI, liver CT, and some industrial categories.

I would **not** make RegAD-like registration the universal backbone. It is valuable, but only for aligned domains. I would also **not** rely on a pure CLIP-style semantic matcher as the main expert, because your hardest failures include subtle local defects and lesions where dense local features matter more.

## Recommended Fusion Policy

1. Run retrieval first. Keep this. It is currently your strongest component.
2. Build a small patch bank from the top retrieved normal references.
3. Compute:
   - image-level expert score
   - anomaly heatmap
   - top `m` suspicious crops
   - uncertainty features such as score margin, heatmap compactness, and agreement across retrieved refs
4. If the expert score is confidently low or high, return it directly.
5. Only if the expert is uncertain, call the VLM once with:
   - query image
   - retrieved refs
   - top suspicious crops
   - heatmap overlay or coordinates
   - short domain prompt
6. Fuse expert and VLM outputs with a calibrated head on the calibration split.

This is the right asymmetry:

- **expert** handles local appearance evidence
- **VLM** handles semantics, context, and relational validation

That is much cleaner than Scout -> Judge -> Expert -> Profile.

## Concrete Scoring Features for Fusion

Use a tiny calibration model over:

- `s_patch`: patch expert anomaly score
- `u_patch`: expert uncertainty or retrieval agreement margin
- `s_vlm`: VLM anomaly score
- `c_vlm`: VLM confidence
- `r_margin`: retrieval gap between best and second-best normal matches
- `h_compact`: heatmap compactness / concentration
- `domain_family`

Even a logistic regression should beat hand-written fusion if calibrated properly.

## Submission Assessment

### As a method paper

`No`. Not ready.

### As a benchmark + design-study paper

`Almost`, but only if you do the following before submission:

1. Reframe the paper around the benchmark and the retrieval-vs-agent lesson.
2. Replace the weak expert with a real patch-level few-shot AD model.
3. Show that a simple calibrated hybrid beats both retrieval-only and VLM-only.
4. Tighten the universal claim into family-aware evidence.

## Reviewer-style Summary

The project has a real paper in it, but not yet in the form currently implied by "tool-augmented universal anomaly detection agent." The strongest empirical story is that **reference selection is the primary driver**, pure agent complexity is unstable, and the right next step is a **retrieval-conditioned dense patch expert with selective VLM adjudication**. If you keep pushing a many-stage agent as the core novelty without proving clear gains over simpler hybrids, reviewers will reject it.
