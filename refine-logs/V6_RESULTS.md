# AnomalyClaw v6 Real Agent — Experimental Results

**Date**: 2026-04-17
**Status**: All Qwen3.5 + SeedVL variants complete. v6.5 in progress.

## Executive Summary

We re-implemented AnomalyClaw as a per-item autonomous ReAct agent (v6)
with 16 tools and K=5 turn budget, and compared against fair Direct and
Fixed-fusion baselines across two VLM backbones. **The agent does NOT
beat Direct VLM in any of the prompt variants we tried.** The ReAct
architecture's tool overhead outweighs its contribution because on many
domains (especially medical imaging, change detection) tool outputs
mislead rather than help the VLM.

## Main Results

### Qwen3.5-VL-27B — 12-domain test (n=1418)

| System | Descriptor | Macro AUROC | vs Direct-task | vs Direct-generic |
|--------|------------|-------------|----------------|-------------------|
| Direct (task descriptor) | domain hint | **0.7684** | — | +4.7pp |
| Direct (generic)         | no hint     | 0.7215 | -4.7pp | — |
| Fusion w=0.2 SubspaceAD (task) | domain hint | **0.8142** | +4.6pp | +9.3pp |
| Fusion w=0.2 SubspaceAD (generic) | no hint | 0.7641 | -0.4pp | +4.3pp |
| **Agent v6** (A-regime, free score) | no hint | 0.7253 | -4.3pp | **+0.4pp** ≈ tie |
| Agent v6.2 (A-regime, score_from_v0) | no hint | 0.6916 | -7.7pp | -3.0pp |
| Agent v6.4 (B-regime, score_from_v0) | domain hint | 0.7158 | -5.3pp | -0.6pp |
| Agent v6.5 (B-regime, free score) | domain hint | *running* | — | — |

### SeedVL (doubao-seed-2.0-lite) — 12-domain test (n=1418)

| System | Macro AUROC |
|--------|-------------|
| Direct (task descriptor) | **0.7995** |
| Fusion w=0.2 SubspaceAD | **0.8075** |
| Agent v6 | 0.7823 (−1.7pp vs Direct) |

### Per-domain Agent v6 (Qwen3.5) vs Direct-task

| Domain | Direct-task | Agent v6 | Δ |
|--------|------------|----------|---|
| D1 (MVTec-AD industrial) | 0.919 | 0.947 | +2.8 ✓ |
| D2 (GoodsAD retail)       | 0.725 | 0.600 | **−12.5** ✗ |
| D4 (SDNET infra cracks)   | 0.794 | 0.761 | −3.3 |
| D5 (Dermoscopy)           | 0.701 | 0.639 | −6.2 |
| D5b (Brain MRI)           | 0.855 | 0.876 | +2.1 ✓ |
| D5c (Liver CT)            | 0.624 | 0.643 | +1.9 ≈ |
| D5d (GI endoscopy)        | 0.905 | 0.654 | **−25.1** ✗ |
| D6 (LEVIR change det.)    | 0.792 | 0.570 | **−22.2** ✗ |
| D7 (Road BDD100K)         | 0.923 | 0.961 | +3.8 ✓ |
| D8 (Avenue surveillance)  | 0.616 | 0.585 | −3.1 |
| D9 (MVTec-LOCO logical)   | 0.564 | 0.586 | +2.2 ≈ |
| D10 (VisA industrial)     | 0.801 | 0.882 | +8.1 ✓ |

**Wins (≥+2pp)**: D1, D5b, D7, D10 (4)
**Losses (≥−2pp)**: D2, D4, D5, D5d, D6, D8 (6)
**Ties**: D5c, D9 (2)

## Success Criteria Check (from spec §7)

- Minimal (Agent > Direct by ≥ 2pp on ≥ 2/3 backbones): **FAIL**
  - Qwen3.5 B-regime: Agent 0.7158 vs Direct 0.7684 → −5.3pp
  - Qwen3.5 A-regime (fair): Agent 0.7253 vs Direct 0.7215 → **+0.4pp** (tied)
  - SeedVL: Agent 0.7823 vs Direct 0.7995 → −1.7pp

- Solid (≥ 3pp on all 3): **FAIL**
- Strong (Agent > Fusion on ≥ 1): **FAIL** (agent loses to Fusion on both backbones)

## Why Agent Fails — Diagnostic Findings

### 1. Prompt-artifact penalty from "no domain hint"

Sub-analysis of v6 (Qwen3.5):

| Subset | n | Agent macro | Direct-task macro on same items | Δ |
|--------|---|-------------|----------------------------------|---|
| Agent decided at turn 1 without tools | 318 | 0.6115 | 0.8358 | **−22.4** |
| Agent called ≥ 1 tool | 1100 | 0.6889 | 0.7355 | −4.7 |

The −22.4pp hit on "agent answers turn 1 without tools" is **pure prompt
penalty**: without a domain hint, VLM over-predicts "anomalous" on
unfamiliar image types (observed on D5d/D6 calibration items: ~90% scored
0.95 when GT=0). The agent's prompt is structurally handicapped vs
`build_prompt_v0(domain, has_refs=True)`.

### 2. Score calibration: free-form score > score_from_v0 mapping

Score distribution (Qwen3.5 full test):

| System | %<0.1 | %<0.5 | %>0.5 | %>0.9 |
|--------|-------|-------|-------|-------|
| v6 (free 0–1 score) | 7.3% | 46.1% | 53.9% | 37.0% |
| v6.4 (score_from_v0) | 39.5% | 55.8% | 44.2% | 39.7% |

`score_from_v0(label, confidence)` pushes 80% of items into extremes
(<0.1 or >0.9), hurting AUROC's rank-ordering vs the VLM's continuous
free-form score. Surprisingly, v6 (no calibration pass) has *better*
distribution than v6.2/v6.4.

### 3. Tool misuse on non-industrial domains

- `tool_expert_score` called on 86% (v6) of items. SubspaceAD was designed for
  industrial surface defects; on D6 (change detection) and D5d (endoscopy)
  its signal is noise, which the agent then weights into its final answer.
- `tool_image_diff` on D6 helps find building changes but the agent can't
  tell "change direction" (building added vs removed) → many false positives.

## What Worked (domain-level)

Agent v6 beat Direct by ≥ 2pp on 4 domains:
- **D1 (+2.8pp)**: hotspot_cropper + expert_score work well on MVTec-AD textures
- **D5b (+2.1pp)**: Brain MRI — expert helps highlight lesions
- **D7 (+3.8pp)**: Road scenes benefit from reference_profiler
- **D10 (+8.1pp)**: VisA industrial — same story as D1 (biggest win)

## Tool Usage Distribution (Qwen3.5 v6)

| Tool | Call count |
|------|------------|
| tool_expert_score | 1222 (86% of items) |
| tool_hotspot_cropper | 556 |
| tool_side_by_side | 399 |
| tool_reference_profiler | 398 |
| tool_image_diff | 291 |
| tool_component_counter | 15 |
| tool_zoom_bbox | 11 |
| tool_rotate_align | 8 |
| tool_patch_grid | 8 |
| tool_segment_and_count | 4 |
| tool_texture_fft | 3 |
| tool_reference_retriever | 0 |
| tool_domain_knowledge | 0 |

Agent does not use 3 of the 13 tools. Zoom/patch_grid/rotate_align
barely used. SeedVL uses tools more sparingly (avg 1.68 turns vs
Qwen3.5's 3.06).

## Honest Assessment

1. **The "real agent" framing is harder than expected.** Even with 13
   tools and autonomous tool selection, a zero-shot ReAct VLM loses to
   its own zero-shot VLM baseline. The v5 per-domain router (also losing
   to fair baselines in truth) at least avoided this by hardcoding which
   domains get tools.

2. **A-regime (no domain hint) penalty is prompt-architectural**, not
   agent-architectural. The VLM just performs worse when told nothing
   about what it's inspecting.

3. **Fusion w=0.2 (no per-domain tuning, no agent) is the actual
   winner** on both backbones. A simple "VLM + SubspaceAD 20% fused"
   beats Direct by +4.6pp on Qwen3.5 and +0.8pp on SeedVL — with zero
   agent overhead. This is what the paper's main contribution should be,
   honestly.

4. **Tools help in aggregate on some domains, hurt on others.** Net
   effect is negative because catastrophic losses on D5d/D6 (−25, −22pp)
   outweigh +8pp gains on D10.

## What a Future v7 Would Need

If we want an agent that actually beats Direct:

- **Per-item learned routing** trained on the 480-item dev split:
  input = (VLM initial judgment, expert rank, image features) → output =
  which tools to call.
- **Tool-quality estimation**: agent should predict whether a tool's
  output will be reliable before trusting it. E.g. texture_fft on a
  medical MRI returns a periodicity score, but that signal is irrelevant
  for MRI pathology detection.
- **Soft ensemble with initial VLM**: final score = α · VLM_turn1 + (1−α)
  · agent_final, where α is learned.

## Files

- Spec: `docs/superpowers/specs/2026-04-16-real-ad-agent-design.md`
- Plan: `docs/superpowers/plans/2026-04-16-real-ad-agent.md`
- Results: `benchmark/results/v6_*_{qwen3,seedvl}_test.json`
- Eval: `refine-logs/v6_eval_*.json`
- Code: `benchmark/scripts/agent_v6*.py`, `agent_tools_v6.py`, `eval_v6.py`,
  `run_baselines_v6.py`
