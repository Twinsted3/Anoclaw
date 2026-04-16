# Experiment Plan: Descriptor Ablation Completion (SeedVL + Qwen3.5)

**Problem**: The AnomalyClaw paper's "task-anchored descriptors dominate" claim is currently only supported on GPT-5.4 test (0.761→0.825, +6.4 pp). SeedVL and Qwen3.5 test-split v0 numbers are all with task-anchored descriptors; we lack the paired generic-descriptor runs to prove the claim holds across backbones. Codex reviewer flagged this as a MAJOR issue.

**Method thesis**: A single-sentence task-anchored domain descriptor (defining normal/anomaly for the specific task) moves training-free single-pass VLM VAD performance substantially, consistently across VLM backbones, at zero inference cost.

**Date**: 2026-04-14

## Claim Map

| Claim | Why It Matters | Minimum Convincing Evidence | Linked Blocks |
|-------|----------------|-----------------------------|---------------|
| C1 (headline): Task-anchored descriptors dominate across three VLM backbones | Paper's Finding 1; currently only proven on 1 of 3 backbones | Paired-item test-split v0 with BOTH generic and task-anchored descriptors on SeedVL and Qwen3.5; positive, statistically significant gap at $p<0.05$ on both | B1, B2, B3 |
| C2 (supporting): The gap magnitude varies with backbone but the direction does not | Rules out the anti-claim that descriptors only help frontier VLMs | Per-domain + macro AUROC for generic vs task-anchored on SeedVL and Qwen3.5; report all 11 per-domain deltas | B3 |
| **Anti-claim to rule out**: The GPT-5.4 +6.4 pp is an artifact of that one model's pre-training, not a general effect | | See C1 |

**Minimum convincing evidence per reviewer**: A 3-row × 3-column descriptor ablation table (3 backbones × {generic v0, task-anchored v0, Δ with 95% CI}), all on the same 1298-item paired test set.

## Paper Storyline

- **Main paper must prove**: C1 (descriptor claim generalises to SeedVL and Qwen3.5 on test split).
- **Appendix can support**: per-domain breakdown for SeedVL and Qwen3.5 (companion to Appendix C GPT-5.4 per-domain table).
- **Experiments intentionally cut**: re-running descriptor ablation on debate/debate-gated/self-refine variants — those are already established as calibration-only negative results.

## Experiment Blocks

### Block 1: SeedVL generic-descriptor sweep on test split (MUST-RUN)
- **Claim tested**: C1 (descriptor effect generalises to SeedVL)
- **Why this block exists**: Without it, the descriptor claim in the abstract is unverified for 2 of 3 backbones
- **Dataset / split / task**: CrossDomainVAD-11 test split (1298 items across 11 domains, same as existing task-anchored run)
- **Compared systems**:
  - SeedVL v0 Direct with **generic descriptor** (new run)
  - SeedVL v0 Direct with **task-anchored descriptor** (already exists: `seedvl_agent_v1_test.json` embedded v0 or `seedvl_v0_direct_test_all_v2.json`)
- **Metrics**: per-domain AUROC, macro AUROC, stratified paired bootstrap Δ, 95% CI
- **Setup details**:
  - Model: `doubao-seed-2-0-lite-260215` via `localhost:8080/v1` sub2api proxy
  - Temperature 0, max_tokens 700
  - Prompt: `build_prompt_v0_generic()` — new function with domain-agnostic wording
  - Reuse existing SubspaceAD and DINOv2 caches
  - Deterministic seed (none — VLM is temp=0)
- **Success criterion**: macro AUROC gap $>0$ with 95% CI excluding zero (paired bootstrap, $n{=}1298$, per-domain stratified)
- **Failure interpretation**:
  - If gap positive but CI includes 0 → soft evidence; keep claim but report as "trend-level not significant"
  - If gap negative on SeedVL → rewrite claim as "descriptors help frontier but not non-frontier VLMs"; remove the "across three backbones" wording
- **Table/figure target**: new row in `tab:descriptor_ablation` (appendix C) + updated Fig 1(a) and Finding 1 wording
- **Priority**: MUST-RUN

### Block 2: Qwen3.5 generic-descriptor sweep on test split (MUST-RUN)
- **Claim tested**: C1 (descriptor effect generalises to Qwen3.5)
- **Why this block exists**: Completes the 3-backbone picture; Qwen3.5 is our open-weight backbone, so positive result is also relevant for cost-constrained deployments
- **Dataset / split / task**: Same 1298-item test split
- **Compared systems**:
  - Qwen3.5-VL-27B v0 Direct with **generic descriptor** (new run)
  - Qwen3.5-VL-27B v0 Direct with **task-anchored descriptor** (already exists: `qwen35_agent_v1_test.json` embedded v0 or `qwen35_v0_direct_test_all_v2.json`)
- **Metrics**: same as Block 1
- **Setup details**:
  - Model: `Qwen3.5-27B-FP8` via `localhost:8200/v1` vLLM server (already running)
  - Temperature 0, max_tokens 700, `enable_thinking=False`
  - Prompt: `build_prompt_v0_generic()` (same function as Block 1)
  - Reuse existing caches
- **Success criterion**: same as Block 1
- **Failure interpretation**: same as Block 1
- **Table/figure target**: same as Block 1
- **Priority**: MUST-RUN

### Block 3: Post-hoc bootstrap and per-domain tables (MUST-RUN, analysis only)
- **Claim tested**: C2 (uniformity of direction)
- **Why this block exists**: Turns raw scores from B1/B2 into paper-ready evidence
- **Dataset / split / task**: Merged with existing task-anchored test-split scores
- **Compared systems**: 3 backbones × {generic, task-anchored}
- **Metrics**: macro AUROC per backbone; paired bootstrap (stratified by domain, 1000 resamples) for Δ; per-domain AUROC gaps on SeedVL and Qwen3.5
- **Setup details**: Reuse `paper/figures/gen_bootstrap_cis.py` structure; add descriptor mode as third dimension
- **Success criterion**: 3-backbone × 3-column ablation table populated; all three Δ's reported with CI; paper's Finding 1, Fig 1(a), abstract, and Appendix C updated
- **Failure interpretation**: n/a (analysis pass)
- **Table/figure target**: Updated `tab:descriptor_ablation` in Appendix C (add 2 new sections); updated Fig 1(a) with 3 backbones instead of 1; updated Finding 1 and abstract wording
- **Priority**: MUST-RUN

### Block 4 (NICE-TO-HAVE): Calibration-split cross-check
- **Claim tested**: Generic→task-anchored effect holds on calibration too (sanity check matching prior calibration-only claim in the paper)
- **Priority**: NICE-TO-HAVE — only if test-split results are borderline and we need more evidence
- **Reuse**: existing calibration files (`seedvl_v0_direct_calibration*.json`, `qwen35_v0_direct_calibration_egra.json`)
- **Cost**: 0 (data already exists, just post-hoc analysis)

## Run Order and Milestones

| Milestone | Goal | Runs | Decision Gate | Cost (wall-clock) | Risk |
|-----------|------|------|---------------|-------------------|------|
| M0 (Sanity) | Add `build_prompt_v0_generic()`, smoke-test 20 items on each backbone | R001, R002 | Both backends return parseable JSON; scores in [0,1] | ~10 min | Prompt format rejected by VLM |
| M1 (Qwen run) | Full Qwen3.5 generic-descriptor sweep, 1298 items | R003 | ≥95% items with parsed output, no systematic JSON failures | ~1 h | vLLM server crash; GPU OOM |
| M2 (SeedVL run) | Full SeedVL generic-descriptor sweep, 1298 items | R004 | ≥95% items with parsed output, no rate-limit failures | ~1 h | API rate limit; key expiration |
| M3 (Analysis) | Recompute macro AUROC + bootstrap for both, regenerate fig_intuition and descriptor ablation table | R005 | All 3 backbones populated in ablation table | ~20 min | n/a |
| M4 (Paper update) | Update abstract, Finding 1, Fig 1(a) caption, Appendix C | R006 | Codex re-review | ~30 min | Residual inconsistencies |

**Total estimated wall-clock**: ~3 hours (assuming backends are stable).

**Go / no-go gates**:
- After M0: if prompts fail to produce valid JSON, iterate on prompt wording before launching full sweep.
- After M1: if Qwen generic is worse than task-anchored by > 3 pp, proceed to M2. If Qwen generic is *better*, halt and investigate (prompt ambiguity).

## Compute and Data Budget

- **Total estimated GPU-hours**: Qwen3.5 occupies 1 GPU already; no additional GPU cost. SeedVL is remote API.
- **API cost (SeedVL doubao-seed-2-0-lite)**: ~1300 items × ~1.5k input tokens × $0.3/1M = **~$0.60 total**. Negligible.
- **Data preparation needs**: None (manifests and caches all exist).
- **Human evaluation needs**: None.
- **Biggest bottleneck**: SeedVL API rate limit if configured conservatively (unknown; will throttle if needed).

## Risks and Mitigations

- **Risk: generic prompt triggers VLM refusal (safety filter) on medical/surveillance domains.**
  Mitigation: prompt says ``You are a visual anomaly inspector''; same wording worked for GPT-5.4 generic run. If refusals appear, log them and treat as parse failures (conservative score 0.5).

- **Risk: Qwen3.5 generic is actually *better* than task-anchored (reverses our narrative).**
  Mitigation: report honestly. Means the VLM's prior already encodes the task, and our descriptor claim should be scoped to GPT-5.4 and SeedVL.

- **Risk: vLLM server at port 8200 crashes during 1300-item run.**
  Mitigation: existing `run_experiments_async.py` has resume-from-checkpoint; restart and continue.

- **Risk: SeedVL API key expired / quota exhausted.**
  Mitigation: prompt user to refresh; not a hard blocker since GPT-5.4 + Qwen3.5 still give 2-backbone evidence if SeedVL fails.

## Final Checklist
- [x] Main paper tables are covered (Fig 1a, Table in Appendix C, abstract claim)
- [x] Novelty is isolated (this is about C1 only, not the agent)
- [x] Simplicity is defended (we don't need new descriptors; just applying the existing ones to more backbones)
- [x] Frontier contribution is not claimed here (descriptor is backbone-agnostic by design)
- [x] Nice-to-have runs (B4 calibration cross-check) separated from must-run
