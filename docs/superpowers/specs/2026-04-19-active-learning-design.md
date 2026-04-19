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

This is a **dev-oracle semi-supervised domain-adaptation** protocol — the
oracle pool comes from the \emph{dev} split (not test), so it is
structurally impossible for oracle labels to leak into the test AUROC.

1. **Passive pass** (no oracle):
   - Run agent v9 on all test items of D. Collect
     (image, score, rationale, confidence).
2. **Uncertainty selection on DEV**:
   - Run agent v9 on all dev items of D first to obtain dev scores.
   - Confusion score: $|s_\text{agent} - 0.5|$ (lowest ⇒ most uncertain).
     Extensions (disagreement-weighted, confidence-weighted) are future
     work; the current implementation uses only $|s-0.5|$ to keep the
     MVP simple.
   - Pick top-$K{=}10$ most confusing dev items.
3. **Oracle query** (GT label from the manifest's `label` field):
   - For each selected DEV item, read the ground-truth label $y \in
     \{0,1\}$ from the manifest. No test labels touched.
4. **Build per-domain RAG** using the labelled dev items:
   - Key: DINOv2 CLS embedding of the query image.
   - Value: (image path, label, agent's rationale at the time of query).
5. **Active pass on TEST**:
   - For each test item in D, retrieve top-$3$ nearest DEV neighbours by
     DINOv2 cosine similarity and inject them as text lines into the
     agent's turn-1 user message:
     ``RECENT LABELLED EXAMPLES FROM THIS DOMAIN: [N1] label=…
     similarity=… — \<rationale\>''. (Future work: pass the neighbour
     images too; the current MVP uses text-only neighbours.)
   - Agent re-runs v9 with the augmented context; tool calls unchanged.
6. **Evaluation**: per-domain AUROC on the full test split,
   \emph{pre} vs \emph{post} active pass. Oracle pool is dev (disjoint
   from test) so this is not active-learning-with-test-holdout; the right
   framing is ``semi-supervised domain adaptation with $K$ labelled
   examples per domain''.

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
