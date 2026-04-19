# AnomalyClaw v8 — Resume Guide

**Last active**: 2026-04-20 ~06:10 CST (overnight autonomous session)
**Status**: v9 unified agent + MMAD full-type eval + active learning
pilot + Round 1 adversarial review complete. MMAD label bug fixed (see
§ MMAD). SeedVL Direct file swapped for consistent v6 provenance
(gain drops to +0.93pp non-significant). v9 agent does NOT
systematically beat Direct on MMAD MCQ aggregate. Active learning
pilot on 4 CrossDomainVAD domains mean Δ +3.5pp (D1 +7.33, D9 +11.11,
D5 −4.00, D12 −0.44).

---

## How to start the next conversation

```
Read RESUME.md, review-stage/AUTO_REVIEW.md, refine-logs/V8_RESULTS.md,
and paper/sections/4_experiments.tex to catch up.
```

## Project state in one paragraph

AnomalyClaw v8 is a training-free VAD system whose main method is
**score-diverse VLM-agent ensembling**: $s_{\mathrm{final}} = 0.5\cdot s_{\mathrm{Direct}} + 0.5\cdot s_{\mathrm{agent}}$
with the weight frozen on dev. On our **CrossDomainVAD-11** test
($n{=}1418$, 12 domains) the ensemble beats descriptor-only Direct on
all three backbones: Qwen3.5-VL-27B $+4.53$ pp (CI $[+2.82, +6.31]$,
$P{=}1.000$), SeedVL $+0.93$ pp (CI $[-0.32, +2.25]$, $P{=}0.927$, not
significant — a provenance fix relative to an earlier draft that used a
pre-v6 SeedVL Direct file),
GPT-5.4 $+1.74$ pp (CI $[+0.68, +2.86]$, $P{=}1.000$). The mechanism
is **rank-granularity**, not middle-zone mass: rank-preserving
transformations that remove all mid-mass still give $+4.68$ pp on
Qwen3.5 test. A secondary interpretable variant (v8 refutation agent)
gains $+1.28$ pp on Qwen3.5 test. On an independent benchmark **MMAD**
(Jiang et al., ICLR 2025; n=989 stratified across 38 classes), the
method generalises: pooled AUROC $0.781 \to 0.811$, $+3.03$ pp (CI
$[+1.48, +4.54]$, $P{=}0.999$, label bug fixed 2026-04-19).
MCQ accuracy does *not* transfer
($-0.8$ pp), consistent with the rank-granularity mechanism. An
auto-review-loop with GPT-5.4 xhigh ran 3 rounds and terminated at
6.0/10 "almost" after fixing narrative consistency. Paper sections
(abstract, intro, method, experiments, conclusion) are aligned.

## Headline results

### Main table — per domain × 3 backbones (CrossDomainVAD-11 test, n=1418)

| Domain | GPT-5.4 Direct / Ens / Δ | SeedVL Direct / Ens / Δ | Qwen3.5 Direct / Ens / Δ |
|---|---|---|---|
| D1 industrial | 0.932 / 0.965 / **+3.3** | 0.962 / 0.951 / −1.1 | 0.919 / 0.972 / **+5.3** |
| D2 retail | 0.815 / 0.810 / −0.5 | 0.851 / 0.862 / +1.1 | 0.725 / 0.780 / **+5.5** |
| D4 infra/derma | 0.799 / 0.796 / −0.4 | 0.745 / 0.708 / **−3.7** | 0.794 / 0.807 / +1.4 |
| D5 brain MRI | 0.793 / 0.794 / +0.1 | 0.720 / 0.749 / **+2.9** | 0.701 / 0.743 / **+4.2** |
| D5b brain MRI (BMAD) | 0.964 / 0.961 / −0.3 | 0.867 / 0.835 / −3.3 | 0.855 / 0.959 / **+10.4** |
| D5c liver CT | 0.789 / 0.849 / **+6.0** | 0.600 / 0.654 / **+5.4** | 0.624 / 0.676 / **+5.1** |
| D5d GI endoscopy | 0.901 / 0.914 / +1.4 | 0.901 / 0.885 / −1.6 | 0.905 / 0.867 / −3.8 |
| D6 LEVIR change | 0.856 / 0.839 / −1.7 | 0.736 / 0.728 / −0.8 | 0.792 / 0.789 / −0.3 |
| D7 HyperKvasir | 0.972 / 0.974 / +0.1 | 0.951 / 0.993 / **+4.2** | 0.923 / 0.961 / **+3.8** |
| D8 road | 0.704 / 0.758 / **+5.4** | 0.646 / 0.634 / −1.2 | 0.616 / 0.655 / **+3.9** |
| D9 MVTec-LOCO | 0.737 / 0.794 / **+5.7** | 0.723 / 0.809 / **+8.6** | 0.564 / 0.653 / **+8.9** |
| D10 VisA | 0.894 / 0.911 / +1.7 | 0.892 / 0.899 / +0.7 | 0.801 / 0.902 / **+10.1** |
| **Macro** | **0.846 → 0.864** | **0.800 → 0.809** | **0.768 → 0.814** |
| Macro Δ | **+1.74 pp** | **+0.93 pp** (n.s.) | **+4.53 pp** |
| 95 % CI | [+0.68, +2.86] | [+0.79, +3.47] | [+2.82, +6.31] |
| P(Δ>0) | 1.000 | 0.999 | 1.000 |

Per-backbone agent selection (dev-frozen): v6.5 on Qwen3.5, v6.5 on
SeedVL, v6.6 self-ensemble on GPT-5.4.

### Score-diversity ablation (Qwen3.5 test, controlled)

| Variant | Standalone | Ensemble | # unique | mid-mass % |
|---|---|---|---|---|
| Direct | 0.7684 | — | 11 | 0% |
| v6.5 original | 0.7713 | 0.8136 (+4.53) | 49 | 24% |
| **v6 EXT-RANK-PRESERVE** | 0.7713 | **0.8152 (+4.68)** | 49 | **0%** |
| v6 BIN (median-split) | 0.6928 | 0.7915 (+2.31) | **2** | 0% |
| v6 affine (a=0.25) | 0.7713 | 0.8155 (+4.71) | 49 | 100% |
| v8 original | 0.6710 | 0.7812 (+1.28) | ~15 | 0.4% |
| RANDOM [0.2,0.8] | 0.4845 | 0.7345 (−3.39) | 1418 | 100% |

→ Rank granularity is causal, middle-mass is correlational.

### Cross-benchmark: MMAD (Qwen3.5, stratified n=989 / 38 classes)

| Metric | Direct | Agent | Ensemble | Δ |
|---|---|---|---|---|
| MCQ accuracy (pooled) | 66.4% | 65.1% | 65.6% | **−0.8** |
| Score AUROC (pooled) | 0.781 | 0.743 | **0.811** | **+3.03** ([+1.48, +4.54], $P{=}0.999$, corrected labels) |

Per subset AUROC: DS-MVTec +1.6 pp, MVTec-LOCO +1.2 pp, VisA +3.2 pp.
(GoodsAD / MVTec-AD subsets are single-class in the sample → no AUROC.)

**MCQ accuracy does not transfer** — this is a *positive* paper finding: ensemble fixes ranks, not thresholds.

### v8 Refutation Agent (interpretable secondary contribution)

Three-phase protocol:
1. Turn 1 (no tool): VLM outputs `initial_score` + up to 3 `candidate_features` + `refutation_target`
2. Turn 2+: call `side_by_side`/`reference_profiler`/`reference_retriever`; emit `refutation_verdict` ∈ {found_in_ref, not_found, inconclusive}
3. Final: `remaining_candidate_features` empty → 0.05-0.20; any survive → 0.40-0.95

Qwen3.5 test: $+1.28$ pp (CI touches zero, $P(\Delta{>}0){=}0.962$). GPT-5.4 dev triple blend (0.5 Direct + 0.3 v6.6 + 0.2 v8): $0.839$ ($+2.4$ pp).

## Auto-review-loop outcome

| Round | Score | Verdict | Note |
|---|---|---|---|
| 1 | 4.5 | not ready | 7 weaknesses, including v8 pitched as main when v6 ensemble was stronger |
| 2 | — | partial (credit limit) | Codex ran own ablation, invalidated middle-mass claim → rank-granularity |
| 3 | **6.0** | **almost** | loop terminates; narrative consistency fixes applied |

Full log in `review-stage/AUTO_REVIEW.md`; raw reviewer responses in `review-stage/codex_review_r{1,2,3}_raw.out`.

## Key documents (read in this order)

1. `RESUME.md` — this file
2. `paper/sections/0_abstract.tex` — v8-era abstract with ensembling framing
3. `paper/sections/4_experiments.tex` — main table (per-domain × 3 backbones), score-diversity ablation, MMAD subsection
4. `refine-logs/V8_RESULTS.md` — comprehensive v8 results (pre-MMAD)
5. `review-stage/AUTO_REVIEW.md` — 3-round review log with method description + claims
6. `refine-logs/rank_granularity_ablation.txt` — raw ablation numbers
7. `refine-logs/per_domain_final_table.txt` — per-domain × backbone numbers
8. `refine-logs/CODEX_REVIEW_2026-04-18_v7.md` — v7-era codex audit that motivated tool fixes

## Code layout

```
benchmark/scripts/
├── agent_v6.py                  # core ReAct loop
├── agent_v6_5.py                # v6.5 variant (used on Qwen3.5/SeedVL main table)
├── agent_v6_6.py                # v6.6 self-ensemble (used on GPT-5.4 main table)
├── agent_v8.py                  # v8 refutation agent (schema fixed)
├── agent_prompt_v8.py           # three-phase refutation protocol
├── agent_tools_v7.py            # 13 tools with interpretation+disconfirm wrappers
├── mmad_eval.py                 # MMAD cross-benchmark evaluator
├── score_diversity_ablation.py  # controlled middle-mass ablation (round-1)
├── analyze_tool_flips.py        # per-item flip analysis
├── find_trigger_rules.py        # rank×direct cell grid
├── per_tool_domain_breakdown.py # per-tool × per-domain characterization
├── single_tool_agent.py         # single-tool audit runner
├── tool_audit_runner.py         # queue for 13 per-tool audits
├── build_tool_card.py           # per-tool tool_card.md generator
├── diagnose_tools.py            # v6.5 case sampling
└── launch_qwen35_replicas.sh    # 3 vLLM replicas launcher
```

## Artifacts

- `benchmark/results/v6_direct_{qwen3,gpt,seedvl}_{dev,test}.json` — Direct baselines
- `benchmark/results/v6_5_agent_qwen3_{dev,test}.json` — v6.5 on Qwen3.5 (main table)
- `benchmark/results/v6_6_agent_gpt_{dev,test}.json` — v6.6 on GPT-5.4 (main table)
- `benchmark/results/v6_agent_seedvl_test.json` — v6 on SeedVL (main table)
- `benchmark/results/v8_qwen3_{dev,test}.json` — v8 refutation
- `benchmark/results/mmad_anomaly_qwen3.json` — MMAD cross-benchmark (n=989)
- `benchmark/results/tool_audit/*.json` × 13 — per-tool single-tool audits
- `refine-logs/tool_cards/*.md` — 13 per-tool niche cards (all DROP)

## Infrastructure tips

- **Qwen3.5-VL-27B INT8 vLLM**: 3 replicas on GPUs 0/1/2 (single GPU each, FP8 quant). Launch inline (see `launch_qwen35_replicas.sh`, but it uses 4 GPUs; override to `for i in 0 1 2`). LB on port 8210.
- **Qwen env**: `export QWEN_API_BASE=http://localhost:8210/v1 QWEN_MODEL=Qwen3.5-VL-27B QWEN_API_KEY=EMPTY`
- **GPT-5.4 env**: sub2api on localhost:8080, `export GPT_MODEL=gpt-5.4`. v8 at test-scale concurrency (12 workers) rate-limits: use `--max_workers 2` or accept partial.
- **Free GPUs when idle**: `for p in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader); do kill -9 $p; done` (if you own them).

## Open items (optional future work)

1. **Rerun v8 on Qwen3.5 test with corrected schema** (~3 h) — will refresh +1.28 pp number; may move CI off zero.
2. **v9: continuous refutation scores.** Redesign the refutation protocol so the VLM emits a graded refutation strength per candidate instead of a verdict category. Hypothesis: v9's rank grid matches v6 → $+4.5$ pp gain with v8's interpretability.
3. **GPT-5.4 v8 test** via a different endpoint (not sub2api) to complete cross-model validation.
4. **Compile paper to PDF** — requires TeXLive install (not available locally).

## Git state

```
Branch: main (clean on latest)
Last 8 commits:
  cdee68f MMAD cross-benchmark evaluation (Qwen3.5-VL-27B, n=989 stratified)
  02cabc3 main-results table: per-domain across all 3 backbones
  118329c auto-review round 3 FINAL 6.0/10 'almost' + narrative consistency fixes
  652bcf1 auto-review round 2 (partial): codex exposed mid-mass/rank confound
  5157e8e auto-review-loop round 1: fixes from codex 4.5/10 feedback
  bfc1173 v8 test results + score-diversity insight
  60acd33 v8 dev WIN: agent+Direct ensemble +3.3pp (p=0.005) on Qwen3.5
  b0de33a v8 skeptical-verification agent: refutation-driven protocol
```

---

*Generated at end of v8 + cross-benchmark cycle by Claude Opus 4.7 (1M context).*
