# AnomalyClaw — Per-Domain Active Self-Evolution (Spec #2)

**Date**: 2026-04-19
**Status**: spec drafted during autonomous session; will be verified post-#1.

## Goal

When the agent encounters a new domain (object class, scene type), it should
self-evolve — i.e. accumulate domain-specific knowledge from a small number
of human-labelled (or oracle-GT in experiments) examples and use that
knowledge to answer future queries from the same domain more accurately.

Mechanism: active selection of confusing items, GT query, inject retrieved
neighbors as few-shot evidence in the agent's system prompt.

## Scope

- **Benchmark**: CrossDomainVAD-11 (12 domains, 1418 test items) — primary.
- **Budget**: K=10 oracle queries per domain (realistic human labelling
  budget).
- **Backbone**: Qwen3.5-VL-27B primary.

## Protocol (per domain D)

1. **Passive pass** (no oracle):
   - Run agent v9 on all test items of D. Collect (image, score, rationale,
     confidence).
2. **Uncertainty selection**:
   - Score confusion = |agent_score − 0.5| × weight_uncertainty
                      + |direct − agent| × weight_disagreement
                      − confidence/100 × weight_confidence
   - Pick top-K=10 most confusing items.
3. **Oracle query** (simulated in experiments via dataset ground truth):
   - For each selected item, obtain true label y ∈ {0,1}.
4. **Build per-domain RAG** using the labelled items:
   - Key: DINOv2 CLS embedding of the item's query image.
   - Value: (image path, label, agent's rationale after GT correction).
5. **Active pass**:
   - For each remaining test item in D, retrieve top-3 nearest labelled
     neighbors from D's RAG, include their (image, label, rationale) in
     the agent's turn-1 user message as "RECENT LABELLED EXAMPLES FROM
     THIS DOMAIN".
   - Agent re-runs v9 with the augmented context; tool calls unchanged.
6. **Evaluation** on the hold set (test items not selected as oracle):
   - Metric: per-domain AUROC, before vs after.

## Decoupling from test-set leakage

- Oracle queries use GT labels from the test split — but those items are
  removed from the metric (hold = test \ seed). This is standard active
  learning eval.
- Document in paper: "active protocol leaks labels on 10 items per domain
  by design; AUROC is computed on the remaining held-out items only".

## Output schema (per-domain RAG entry)

```json
{
  "domain": "D1",
  "item_id": "...",
  "image_path": "...",
  "dinov2_cls_b64": "<1024-dim vector as base64-float32>",
  "label_gt": 0|1,
  "rationale_initial": "agent's pre-oracle rationale",
  "rationale_corrected": "rewrite after oracle correction (optional)"
}
```

## File plan

- **Create**:
  - `benchmark/scripts/active_learning.py` — per-domain loop driver
  - `benchmark/scripts/dinov2_embed.py` — reusable CLS embedder (cache)
  - `benchmark/results/active_learning_q35_d1d12.json`
- **Reuse**:
  - `benchmark/scripts/agent_v9.py` — pass extra kwarg `few_shot_context`
  - `benchmark/scripts/mmad_eval_v9.py` — not used for this milestone

## Evaluation metrics

| Metric | Aggregation | Target |
|--------|-------------|--------|
| AUROC per-domain (hold set) | 12 values | avg ≥ Passive + 2pp |
| AUROC per-domain Δ (AL − Passive) | 12 values | ≥9 domains positive |
| Wilcoxon signed-rank (12 paired Δ) | one-sided | p < 0.05 |
| Querying cost | N queries | ≤ 120 (10/domain × 12) |

## Ablations (budget permitting)

- Vary K ∈ {0, 5, 10, 20}.
- Random vs uncertainty-based selection.
- With/without rationale_corrected in RAG.

## Risks

- Qwen3.5-VL context window: 4096 tokens × few-shot images may exceed.
  Mitigation: pass at most 3 few-shot images; downsample each to 384px.
- RAG retrieval may pick uninformative neighbors. Mitigation: re-use
  DINOv2 CLS embedder already used in agent_tools for patch_knn.

## Scheduling within this autonomous session

This spec is drafted but implementation/experiments are **blocked by #1**
(MMAD MCQA evaluation running on Qwen3.5 cluster). Will start after
MMAD dev calibration finishes.
