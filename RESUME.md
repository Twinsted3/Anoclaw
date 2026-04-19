# AnomalyClaw v8 — Resume Guide

**Last active**: 2026-04-19 ~08:20 CST
**Status**: v8 iteration complete; auto-review-loop terminated at 6.0/10 "almost" (threshold met).

---

## How to start the next conversation

```
Read RESUME.md, review-stage/AUTO_REVIEW.md, and refine-logs/V8_RESULTS.md
to catch up on the v8 + score-diverse-ensemble study.
```

## Project state in one paragraph

AnomalyClaw v8 is a per-item ReAct agent for visual anomaly detection over 12 domains, extending v6.5 with a refutation protocol and a post-hoc ensemble. The **headline result** on Qwen3.5-VL-27B test ($n{=}1418$) is a simple $0.5\cdot\text{Direct}+0.5\cdot\text{v6-agent}$ ensemble reaching macro AUROC **0.8136**, beating descriptor-only Direct **0.7684** by **+4.53 pp** (stratified paired bootstrap 95% CI [+2.82, +6.31], $P(\Delta>0)=1.000$). The v8 refutation agent contributes +1.28 pp on Qwen3.5 test (CI touches zero) and provides auditable traces. The ensemble mechanism is **rank granularity**, not middle-zone mass: controlled rank-preserving transformations confirm causality. An auto-review-loop with GPT-5.4 xhigh ran three rounds and terminated at 6.0/10 "almost" after addressing the narrative-consistency fixes; no further experiments were required. The paper abstract, introduction, method, experiments, and conclusion are all aligned on the score-diverse ensembling story.

## Headline results (test split, n=1418, Qwen3.5-VL-27B)

| System | macro AUROC | Δ vs Direct | CI |
|---|---|---|---|
| Direct | 0.7684 | — | — |
| v6.5 agent alone | 0.7713 | +0.29 | noise |
| v8 refutation alone | 0.6710 | −9.74 | — |
| **0.5·Direct + 0.5·v6-agent** | **0.8136** | **+4.53** | **[+2.82, +6.31]**, $P{=}1.000$ |
| 0.6·Direct + 0.4·v8 | 0.7812 | +1.28 | [-0.001, +0.027], $P{=}0.962$ |
| Triple 0.5·Dir + 0.1·v6 + 0.4·v8 | 0.8036 | +3.52 | --- |

GPT-5.4 dev ($n{=}480$): best triple 0.5·Dir + 0.3·v66 + 0.2·v8 reaches 0.8388 (+2.4 pp over Dir 0.8153). GPT-5.4 v8 test is broken by sub2api rate-limits; kept as dev-only.

## Key documents (read in this order)

1. `RESUME.md` — this file.
2. `review-stage/AUTO_REVIEW.md` — auto-review log (3 rounds), final score 6.0 "almost".
3. `refine-logs/V8_RESULTS.md` — v8 experimental results + score-diversity insight.
4. `refine-logs/V8_NOTES.md` — live notebook (log of what worked and didn't).
5. `refine-logs/rank_granularity_ablation.txt` — controlled rank-preserving ablation numbers.
6. `refine-logs/CODEX_REVIEW_2026-04-18_v7.md` — the v7-era adversarial review that motivated the tool fixes.
7. `paper/sections/{0_abstract, 1_introduction, 3_method, 4_experiments, 5_conclusion}.tex` — final aligned paper.

## Code layout (v8 era, active)

```
benchmark/scripts/
├── agent_v6.py                   # core ReAct loop (v6 baseline)
├── agent_v6_5.py                 # v6.5 variant (free-form, used in main ensemble)
├── agent_v6_6.py                 # v6.6 self-ensemble (GPT-5.4 strongest pure agent)
├── agent_v7.py                   # v7 with KEEP-gate (superseded)
├── agent_v8.py                   # v8 refutation agent (schema fixed 2026-04-19)
├── agent_prompt_v8.py            # v8 prompt: three-phase refutation protocol
├── agent_tools_v7.py             # 13 tools with interpretation+disconfirm wrappers
├── single_tool_agent.py          # single-tool audit runner
├── tool_audit_runner.py          # queue for 13 per-tool audits
├── build_tool_card.py            # per-tool slice analysis → tool_card.md
├── analyze_tool_flips.py         # per-item flip analysis
├── find_trigger_rules.py         # rank×direct cell grid trigger discovery
├── per_tool_domain_breakdown.py  # per-tool × per-domain characterization
├── score_diversity_ablation.py   # controlled ablation (round-1 version)
├── diagnose_tools.py             # v6.5 case sampling for manual diagnosis
└── launch_qwen35_replicas.sh     # 3 vLLM replicas (INT8 single-GPU each)
```

## Key artifacts

- `benchmark/results/v6_direct_qwen3_{dev,test}.json` — Direct baseline (dev 0.7599, test 0.7684)
- `benchmark/results/v6_5_agent_qwen3_{dev,test}.json` — v6.5 agent (dev 0.6942, test 0.7713)
- `benchmark/results/v8_qwen3_{dev,test}.json` — v8 refutation agent (dev 0.6865, test 0.6710)
- `benchmark/results/v75_agent_qwen3_dev.json` — v7.5 domain-rule agent (dev 0.6860, deprecated)
- `benchmark/results/tool_audit/*.json` × 13 — per-tool single-tool audits
- `benchmark/results/v6_6_agent_gpt_dev.json`, `v75_agent_gpt_dev.json`, `v8_agent_gpt_dev.json` — GPT-5.4 dev runs
- `refine-logs/tool_cards/*.md` — 13 per-tool niche discovery cards (all DROP)
- `refine-logs/FLIP_ANALYSIS_dev.md`, `PER_TOOL_DOMAIN_dev.md`, `TRIGGER_RULES_dev.md` — per-item analyses

## Infrastructure tips

- **Launch Qwen3.5-VL-27B INT8 vLLM**: 3 replicas on GPUs 0, 1, 2 (single GPU each, FP8 quant). See shell snippet at the top of `review-stage/codex_review_r1_raw.out` or use `bash benchmark/scripts/launch_qwen35_replicas.sh` (note: that script launches 4 replicas; override `for i in 0 1 2; do ... done`).
- **Load balancer**: `LB_N_REPLICAS=3 python benchmark/scripts/vllm_lb.py` on port 8210, env-clear-proxy.
- **Qwen3.5 env**: `export QWEN_API_BASE=http://localhost:8210/v1 QWEN_MODEL=Qwen3.5-VL-27B QWEN_API_KEY=EMPTY`.
- **GPT-5.4 env**: sub2api on localhost:8080, `export GPT_MODEL=gpt-5.4`. v8 test at 12-worker concurrency is rate-limited; use `--max_workers 2` or accept partial.
- **Free GPUs when idle**: `pkill -9 -f Qwen3.5-27B-FP8; pkill -9 -f vllm_lb`.
- **All v8 inference has fixed agent_v8.py schema** as of 2026-04-19 ~08:20; the stored test JSON (`v8_qwen3_test.json`) was produced before the schema fix — rerun takes ~3 h of vLLM time.

## What's next (if extending)

1. **Rerun v8 Qwen3.5 test with corrected schema** (~3 h) to refresh the +1.28 pp number; may move CI off zero.
2. **v9: continuous refutation scores.** Redesign the refutation protocol so the VLM emits a graded refutation strength per candidate instead of a verdict category. Hypothesis: v9 reaches v6's rank granularity and therefore matches the +4.5 pp gain while preserving v8's interpretability.
3. **GPT-5.4 v8 test via a different endpoint** (not sub2api) to complete cross-model validation.
4. **Submit paper.** The auto-review-loop gave 6.0/10 "almost" and flagged only narrative fixes, all applied; the compiled PDF should clear the 6.5-7 bar for a training-free-VAD venue.

## Git state

```
Branch: main (clean)
Last v8 commit chain:
  <latest>: round 3 narrative consistency (intro, method, conclusion, v8 signif, fusion framing)
  652bcf1: round 2 (partial) — rank-granularity correction, abstract + §4 mechanism rewrite
  5157e8e: round 1 fixes — stale schema, history trace, controlled ablation, reframe
  bfc1173: v8 test results + score-diversity insight
  60acd33: v8 dev win +3.3pp + GPT dev v6.6 +0.9pp
  b0de33a: v8 skeptical-verification agent (refutation)
  1591c8e: v7.5 per-tool × per-domain rules
  b5beaac: v7.5 + flip analysis
```

---

*Generated at end of v8 + auto-review-loop cycle by Claude Opus 4.7 (1M context).*
