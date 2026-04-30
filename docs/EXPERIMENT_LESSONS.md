# AD-Agent / AnomalyClaw Experiment Lessons

Project-specific operating rules learned from AnomalyClaw v6 (2026-04-18 retrospective).
Read this before running `/experiment-plan`, `/experiment-bridge`, `/result-to-claim`,
or `/research-refine` on this project.

## Pre-flight Integrity Checks (before any Codex judgment on results)

Before handing results to Codex or writing a claim, answer these five questions.
If any is "yes", flag it explicitly so the verdict accounts for it.

1. **Test-set selection leakage** — was the "best" method/variant chosen by
   comparing multiple candidates on the TEST set? If yes, the reported test
   number is selection-biased; treat as exploratory until re-validated on a
   held-out split. Dev or calibration splits are legitimate for method
   selection; test is for a single final evaluation.

2. **Label-budget asymmetry between compared systems** — does the winning
   method use more labeled data (per-domain dev argmax, fitted thresholds)
   than the baselines it beats? If yes, the comparison is unfair. Either
   (a) equalize label budget, (b) include a baseline that uses the same
   budget, or (c) frame the gain as "dev-supervised upper bound" rather
   than a direct win.

3. **Prompt-structure penalty** — if two VLM-based systems have different
   JSON output schemas (e.g. `{label, confidence}` vs `{action, tool, score}`),
   their outputs are not directly comparable. Run a no-tool control: does
   the agent's output on items where it called zero tools match the Direct
   baseline on those same items? If the gap is > 2pp with no tool calls,
   the "agent gain" is confounded by prompt differences.

4. **Tool causal contribution** — for every tool in the agent's toolbox,
   compute AUROC on items that *invoked* the tool vs. Direct baseline on
   those same items. Publish the per-tool delta table. Without this,
   "more tools is better" is faith-based. On v6 (2026-04-18) 9 of 13
   tools had net-negative effect, one had −28.3pp — aggregate "agent"
   numbers were misleading until the per-tool table was produced.

5. **Self-reported calibration sanity** — if the system uses VLM-reported
   `confidence` for routing or early-exit, check that correct and wrong
   items have *distinguishable* confidence distributions on a holdout.
   If avg(conf | correct) ≈ avg(conf | wrong), confidence is uncalibrated
   and routing on it amplifies errors rather than filtering them.
   (Qwen3.5 specifically exhibits uninformative confidence.)

These five were added after a v6 retrospective where (1) test-set iteration,
(2) 480-label dev router vs 0-label baseline, and (5) Qwen3.5's
uninformative confidence all combined into overstated wins.

## Sanity Check Protocol (before scaling up any run)

Beyond checking for exceptions, also check:

- **Output is not degenerate** — all 0.5, all 1.0, constant predictions, or
  high JSON-parse failure rate. These catch prompt/schema/over-confidence
  bugs that don't throw but will invalidate the full run. A histogram of
  output scores on the sanity items is cheap and frequently catches
  silent failures.

- **Domain-specific pathology** — if sanity surfaces a pathology (e.g., a
  variant performs well on D1 but catastrophically on D5d/D6, as observed
  on 2026-04-18 with v6.3 confidence gating), stop and diagnose BEFORE
  scaling up. A 10-item sanity that crashes on 50% of problematic-domain
  items is a hard stop, not a warning.

- **GPU / throughput pilot** — for new workloads on new hardware configs,
  measure `nvidia-smi --query-gpu=utilization.gpu` during sanity. If
  utilization is < 60% with N workers, raise workers or lower replicas —
  do not default to "more replicas is faster". Observed on shared A6000
  nodes: **2 replicas × 16 workers beat 4 replicas × 24 workers by 60%
  throughput**, due to KV-cache contention.

## Experiment Plan Requirements (AnomalyClaw-specific)

Any `EXPERIMENT_PLAN.md` for this project must specify:

- **Label budget** for each system — zero-shot? fitted on calibration?
  fitted on dev? Two systems with different label budgets are not
  directly comparable; flag this explicitly in every block where it matters.

- **Mandatory per-tool causal ablation block** in the main paper (not the
  appendix) — for every tool T: AUROC on items that invoked T vs. the
  plain baseline on those same items. Without this, "more tools is
  better" is unsupported.

- **Test-split discipline** — state which split is used for what. Default:
  calibration → hyperparameter/prompt selection within a fixed architecture;
  dev → method/variant/architecture selection; test → single final
  evaluation. Any plan that selects among variants on test is
  selection-biased; flag at plan-review time.

## Method Design Principle: Fair Comparison Is Part of the Method

For every system this project's papers compare against, the proposal must
specify that system's label budget, calibration data, and hyperparameter
search space. A "method" that needs per-domain dev labels cannot claim
wins over a zero-shot baseline without adjusting for the label budget —
either equalize, or frame explicitly as a dev-supervised upper bound.
Reviewer prompts during method refinement should actively check this.
