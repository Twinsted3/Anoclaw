# V7 Results — Honest Null Result with Per-Tool Item-Level Findings

**Date**: 2026-04-19
**Backbone**: Qwen3.5-VL-27B (INT8) via local vLLM
**Baseline**: Direct only (Fusion / Router not in scope per user instruction)

## Headline

**No v7 variant beats Direct on dev (n=480).** The headline dev AUROCs:

| System | Dev macro AUROC | Δ vs Direct dev |
|---|---|---|
| Direct | 0.7599 | — |
| v6.5 agent (multi-tool, no interpretation wrapper) | 0.6942 | **-0.066** |
| v7.5 agent (domain-cue rule-based) | 0.6860 | **-0.074** |
| v7_all agent (mode=all, interpretation wrappers, partial n=200) | 0.7166 on its subset (Direct 0.7989 on same subset) | **-0.082** |

Test runs intentionally NOT executed — dev signal is clear.

**The previously reported +0.29pp of v6.5 on test (0.7713 vs 0.7684) is
consistent with noise: v6.5 is −6.6pp below Direct on dev.** The "test win"
is not a generalizable agent effect.

## What the v7 audit found (per-item level — the valuable finding)

The per-tool × per-domain flip analysis (`refine-logs/PER_TOOL_DOMAIN_dev.md`,
`refine-logs/TRIGGER_RULES_dev.md`) identifies **tool×domain combos where
the tool reliably corrects Direct's specific error types**, even though
the aggregate effect per tool is negative:

| Tool | Domain | Net flips | Win:Loss | Error type corrected |
|---|---|---|---|---|
| patch_grid | D5c (liver CT) | +5 | 7:2 | FP on normal anatomical variants |
| zoom_bbox | D1 (industrial) | +4 | 7:3 | FP on capsules/PCB misread by Direct |
| hotspot_cropper | D1 | +4 | 6:2 | same |
| patch_grid | D1 | +4 | 5:1 | same |
| image_diff | D7 (road) | +3 | 3:0 | FN on content-level scene anomaly |
| reference_retriever | D7 | +3 | 3:0 | same |
| image_diff | D1 | +3 | 7:4 | FP on industrial |
| segment_and_count | D1 | +3 | 6:3 | same |
| patch_grid | D10 (VisA) | +2 | 4:2 | Mixed FP/FN correction |
| reference_profiler | D10 | +2 | 3:1 | same |
| texture_fft | D5b (brain MRI) | +2 | 4:2 | FP on normal brain slices |
| texture_fft | D1 | +2 | 6:4 | industrial texture |
| domain_knowledge | D1 | +2 | 5:3 | industrial classification |

## Why v7 failed as an agent despite per-tool wins

1. **Wins concentrate on the SAME 47 items across tools.** 47 dev items
   are "easy for any disconfirm-style correction" — 7+ tools reliably
   flip them to correct. The tool itself is not the deciding factor;
   the interpretation+disconfirm clause is doing the work.

2. **Losses concentrate on 80 different items** where Direct was RIGHT
   and the disconfirm mechanism wrongly overrode it. These are cases
   where subspacead rank disagrees with truth.

3. **80:47 loss:win ratio means aggregate AUROC drops.** Even the
   "best" tool×domain combos have ≤5 net flips on 40 items per domain —
   not enough to flip the per-domain AUROC.

4. **v7.5 rule-based trigger approach:** tried to fire tools only when
   a domain cue matched. Gained +3.3pp on D4, +1.8pp on D7, +2.4pp on D5c,
   but LOST -34pp on D5d, -20pp on D5, -17pp on D6 (domains not covered
   by rules — agent misapplied rules or over-corrected).

5. **v7_all (free selection, all 13 tools):** -8.2pp on 200-item partial.
   The interpretation wrappers consistently push Qwen3.5-VL toward
   conservative scores (std drops from 0.47 to 0.38-0.42), which improves
   calibration but hurts discrimination.

## Key insight: the +0.29pp of v6.5 was noise

v6.5 on Qwen3.5-VL:
- dev: 0.6942 (−6.6pp vs Direct)
- test: 0.7713 (+0.3pp vs Direct)

The dev signal is clear: v6.5 agent HURTS Direct by ~7pp. The test
result was within the noise envelope of a ~12pp per-domain bootstrap
margin. Per the 2026-04-18 codex review (test-set selection leakage
was already caught), this is yet another case where dev truth differs
from the test snapshot the paper was narrated from.

## Per-tool DROP cards (dev single-tool audit n=480)

All 13 tools DROP individually:

| Tool | Call rate | Δ vs Direct | Error |
|---|---|---|---|
| expert_score | 84% | -0.057 | 0 |
| patch_grid | 65% | -0.060 | 95 (JSON parse) |
| rotate_align | 53% | -0.073 | 0 |
| hotspot_cropper | 13% | -0.075 | 1 |
| image_diff | 56% | -0.081 | 0 |
| reference_profiler | 92% | -0.081 | 0 |
| segment_and_count | 80% | -0.084 | 0 |
| side_by_side | 78% | -0.090 | 0 |
| zoom_bbox | 60% | -0.099 | 13 |
| component_counter | 55% | -0.112 | 0 |
| domain_knowledge | 52% | -0.124 | 0 |
| reference_retriever | (never-called in v6.5, partial) | similar | 0 |
| texture_fft | 59% | similar | 0 |

(Full per-tool cards in `refine-logs/tool_cards/`.)

## Recommendations

1. **Do not claim v6.5 / v7 agent variants beat Direct on Qwen3.5-VL.**
   The +0.29pp test result is not reproducible on dev.

2. **Per-item flip analysis IS the valuable finding** of this iteration.
   It identifies which domain × tool combos have exploitable per-item
   corrections. A future router or ensemble could use these combos
   selectively.

3. **Suggested next experiment**: a **hybrid system** that runs Direct
   by default but SWITCHES to tool-based correction on items identified
   as matching the D1/D7/D5c/D5b patterns. Route selection can be
   self-supervised via VLM visual content classification. This was not
   tested here because the user scoped out Fusion and Router baselines.

4. **If publishing**: frame as "most ReAct tools harm anomaly detection
   on Qwen3.5-VL unless tool availability is gated by pre-registered,
   validated conditions" — closer to codex review's publishability
   framing.

## Artifacts

- `benchmark/results/v7_direct_qwen3_dev.json` — already present, 0.7599
- `benchmark/results/v75_agent_qwen3_dev.json` — 0.6860
- `benchmark/results/v7_all_qwen3_dev_partial.json` — 0.7166 on 200 items
- `benchmark/results/tool_audit/*.json` — 13 single-tool audit results
- `refine-logs/tool_cards/*.md` — 13 tool cards (all DROP)
- `refine-logs/FLIP_ANALYSIS_dev.md` — per-tool flip counts
- `refine-logs/PER_TOOL_DOMAIN_dev.md` — per-tool × per-domain breakdown
- `refine-logs/TRIGGER_RULES_dev.md` — rank × direct cell grids
- `refine-logs/TOOL_RULES_v75.md` — written-up per-tool usage rules
- `refine-logs/CODEX_REVIEW_2026-04-18_v7.md` — independent Codex audit

## What's next (for user to decide)

a) Accept the null result and move on (honest reporting).
b) Try a HYBRID router that uses Direct by default and only switches on
   specific tool×domain combos identified here.
c) Try a different backbone (SeedVL, GPT-5.4) — per previous RESUME.md,
   GPT-5.4 v6.6 showed +1.1pp over Direct on test; the interpretation
   wrappers might work on a less-conservative VLM.
