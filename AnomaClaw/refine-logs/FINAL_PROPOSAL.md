# Final Proposal

**Working Title**: Beyond Industrial: A Cross-Domain Benchmark and Minimal Agent Design Study for Training-Free MLLM Anomaly Detection

**Target Venue**: CVPR 2027 or NeurIPS 2026

**Date**: 2026-03-31

## Problem Anchor

Training-free MLLM anomaly detection is currently overfit to industrial benchmarks, so we still do not know which reference-based reasoning designs actually transfer across operational visual domains under realistic API budgets.

## Method Thesis

A minimal reference-based agent that first states what normal looks like and then performs at most one bounded adversarial check is the smallest training-free MLLM design worth testing for cross-domain anomaly detection.

## Dominant Contribution

The paper's dominant contribution is a public, rigorously sampled, cross-domain benchmark plus a cost-matched design study that isolates the minimal transferable agent recipe for training-free MLLM anomaly detection.

## Supporting Contribution

The supporting contribution is a backbone analysis showing where a generalist MLLM (`GPT-4o/4.1`) and a fine-grained specialist VLM (`Seed1.5-VL`) fail differently under the same benchmark, prompt family, and call budget.

## Scope Tightening Decisions

- Keep the paper image-only. Drop true temporal video anomaly detection.
- Keep surveillance as still-frame anomaly inspection sampled from public surveillance anomaly datasets.
- Define one unified task for the main paper: reference-based image-level anomaly decision with optional coarse anomaly type and optional coarse bounding box.
- Do not make segmentation the main task. Report localization only where public masks or boxes already exist.
- Do not include active learning, memory, human feedback, routing, or retrieval modules in this paper.
- Do not claim a new full agent framework. Claim a minimal, testable design study around normal-first reasoning and bounded debate.
- Use one open reproducibility baseline only: `Qwen2.5-VL-7B-Instruct`.
- Keep debate depth small. `2-round debate` is an ablation to test diminishing returns, not the final headline method.

## Problem Definition

Each benchmark item contains:

- one query image
- up to two normal reference images
- a binary label: `normal` or `anomalous`
- a coarse anomaly type label for anomalous items
- optional region annotation if the source dataset provides one

The model must decide whether the query image is abnormal relative to the reference normal state of the same object, scene, imaging modality, or operating context.

## Concrete Method

### Overview

The method is intentionally small:

1. Receive query image `Q`, reference normal images `R1, R2` if available, and a short domain tag.
2. Build a structured `normal_profile` from the reference images and the query scene.
3. Generate one or more anomaly claims in strict JSON with confidence and optional coarse bbox.
4. Optionally call a refuter once to challenge each claim as normal variation, lighting, viewpoint, occlusion, noise, expected clutter, or non-anomalous domain pattern.
5. Aggregate proposer and refuter outputs with fixed thresholds tuned only on the benchmark calibration split.

### Minimal Agent Variants

- `V0 Direct`: single-pass anomaly decision, no explicit normal profile.
- `V1 Normal-First`: single-pass, but must emit `normal_profile` before anomaly decision.
- `V2 Self-Refine`: proposer output followed by one non-adversarial revision pass from the same model. This is a control for "extra call" without debate.
- `V3 Bounded Debate`: proposer plus one refuter pass.
- `V4 Two-Round Debate`: second proposer-refuter pass only for uncertain samples. This is an ablation, not the default deployment candidate.

### Final Candidate Method

The final candidate method entering the main paper is `V3 Bounded Debate`, built on `V1 Normal-First`.

Rationale:

- `V1` is the minimal structural prior that could transfer across domains.
- `V3` is the minimal adversarial check that tests whether agentic disagreement adds value beyond prompt decomposition.
- `V4` exists only to show whether extra rounds are unnecessary.

### Output Schema

All variants must return JSON only.

```json
{
  "normal_profile": {
    "object_or_scene": "string",
    "expected_structure": "string",
    "expected_surface_or_texture": "string",
    "expected_contents": "string"
  },
  "claims": [
    {
      "id": "A1",
      "anomaly_type": "surface_defect|breakage|missing_or_extra|contamination|damage_change|hazard_object|pathology|contextual_abnormality|other",
      "evidence": "string",
      "bbox": [0.0, 0.0, 1.0, 1.0],
      "confidence": 0.0
    }
  ],
  "image_label": "normal|anomalous"
}
```

The refuter returns:

```json
{
  "reviews": [
    {
      "id": "A1",
      "refute_confidence": 0.0,
      "counter_evidence": "string",
      "likely_cause": "normal_variation|lighting|viewpoint|occlusion|compression|expected_context|genuine_anomaly|unknown"
    }
  ]
}
```

### Aggregation Rule

- A claim is `valid` if `confidence >= 0.60` and `refute_confidence <= 0.40`.
- A claim is `invalid` if `refute_confidence >= 0.60`.
- Otherwise the claim is `uncertain`.
- The image is `anomalous` if at least one claim is valid.
- The image is `normal` if all claims are invalid or no claims are proposed.
- For AUROC, the image anomaly score is `max(confidence - refute_confidence)` over all claims, with `0` if no claim exists.

Thresholds are fixed once on the calibration split and then frozen for all domains and all test runs.

### Prompt Family

The paper will freeze one prompt family across all models and domains, with only the domain tag and anomaly taxonomy inserted.

`Direct prompt`

```text
You are a visual anomaly inspector.
Given one query image and up to two normal reference images, decide whether the query is abnormal relative to the normal references.
Return JSON only with image_label, anomaly_type, evidence, confidence, and optional bbox.
```

`Normal-first prompt`

```text
You are a visual anomaly inspector.
First state what normal looks like in this domain and in these reference images.
Then decide whether the query image departs from that normal state.
Return JSON only with normal_profile, claims, and image_label.
```

`Refuter prompt`

```text
You are an anomaly refuter.
For each proposed anomaly claim, try to explain it as non-anomalous: normal variation, lighting, viewpoint, occlusion, expected context, or imaging artifact.
Return JSON only with refute_confidence, counter_evidence, and likely_cause.
```

### Why This Method Is Small Enough

- No fine-tuning
- No memory bank
- No external retrieval
- No domain-specific tool stack
- No routing policy in the main claim
- No temporal modeling

This keeps the method defensible as a design-principles study rather than an overbuilt agent system.

## Benchmark Design

The benchmark is reference-based and image-only. It covers eight operational domains:

1. Industrial manufacturing
2. Retail shelf monitoring
3. Parcel or baggage screening
4. Maintenance or infrastructure inspection
5. Medical radiology
6. Remote sensing disaster damage
7. Road or traffic scene anomaly
8. Surveillance frame anomaly

Each domain contributes `180` benchmark items:

- `20` calibration items
- `40` development items
- `120` final test items

Total main benchmark size: `1,440` items.

## Main Claims

### What We Claim

- Industrial-only evaluation is insufficient for judging training-free MLLM anomaly detection.
- `Normal-First` is a stronger cross-domain prior than direct single-pass prompting.
- One bounded adversarial check is sometimes useful, but extra rounds must justify themselves under matched cost.
- GPT-style generalist MLLMs and fine-grained specialist VLMs fail differently across domains and anomaly types.

### What We Do Not Claim

- We do not claim a universal anomaly detector that solves all domains.
- We do not claim debate is always beneficial.
- We do not claim routing is necessary or stable enough for the main paper.
- We do not claim superiority to fully supervised or fine-tuned specialists on every domain.
- We do not claim temporal surveillance understanding.
- We do not claim medical or safety deployment readiness.

## Why This Version Can Reach 8+

- The story is now one paper with one dominant contribution: benchmark-backed minimal design principles.
- The benchmark is not an afterthought; it is the mechanism for validating the thesis.
- The method is intentionally small and easy to isolate.
- The extra-call confound is handled by `Self-Refine`.
- Cost is a first-class metric rather than an appendix detail.
- The paper is useful even under mixed or negative outcomes.

## Acceptance Bar

This proposal is strong enough for top-tier submission only if the final results show at least one of the following:

- cross-domain rankings differ materially from industrial-only conclusions
- `Normal-First` beats `Direct` consistently across several domains
- `Bounded Debate` helps on a non-trivial subset of domains under matched budget
- the GPT vs Seed error profile difference is clear and actionable

If none of these happen, the paper should be reframed as a benchmark and negative-results paper, not a method paper.
