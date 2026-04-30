# Autonomous Review Loop - Round 3

**Date**: 2026-04-05
**Reviewer mode**: senior ML reviewer (top-venue bar)
**Scope reviewed**: updated round-3 summary in `AUTO_REVIEW.md`, saved V4 sample-level artifacts, prior round-1 and round-2 reviews

## Bottom Line

- **Score**: `7/10`
- **Verdict**: `Almost`
- **Submission readiness**: still **not ready today**, but now very close if the remaining evaluation hygiene is completed cleanly

## Why The Score Increased

Three previously major objections are now substantially addressed:

1. **Causality is now much more convincing**
   - The matched ablation sequence is good:
     - `Ret+VLM = 0.866`
     - `+Knowledge = 0.860`
     - `+Knowledge+GenericCtx = 0.870`
     - `+Knowledge+ExpertCtx = 0.877`
   - This is the right pattern. Generic extra text helps a little, but the specific expert patch evidence helps more.

2. **The hybrid now clearly beats the classical and VLM baselines**
   - `DINOv2-Global = 0.653`
   - `DINOv2-PatchNN = 0.661`
   - `PatchCore Expert = 0.831`
   - `Ret+VLM = 0.866`
   - `ExpertCtx = 0.877`
   - This is a real hierarchy, not noise.

3. **The paper has a sharper mechanism story**
   - The publishable finding is now:
   - **Patch-level expert evidence improves VLM anomaly judgment, but using the expert as a router is weaker than using it as evidence/context.**

That is a legitimate and interesting design conclusion.

## What Is Now Credible

The work now credibly supports the following claims:

1. Retrieval is the strongest first-stage ingredient.
2. A proper patch-level few-shot expert is useful.
3. Expert evidence is more valuable as structured context than as a gating mechanism.
4. A simple hybrid can outperform both vision-only and VLM-only baselines across the 10-domain benchmark.

## Ranked Remaining Weaknesses and Minimum Fixes

### 1. The current best result is still a test-set oracle

`Family-Adaptive Fusion = 0.885` is the most attractive number in the table, but by your own description the family alphas were optimized on the test set. That makes it an analysis result, not a valid headline method result.

**Minimum fix**
- Move alpha selection to calibration or dev only.
- Freeze one family map and one alpha per family before final test evaluation.
- Report both:
  - **validated best method**: whatever survives the held-out protocol
  - **oracle analysis**: retained as an upper-bound diagnostic only

Until that is done, the defensible headline is `ExpertCtx = 0.877`, not `0.885`.

### 2. The statistics package is still incomplete

You say bootstrap CIs are computed but not yet formatted. Until the final table shows uncertainty and pairwise significance, reviewers can still dismiss small margins such as `0.877` vs `0.873` or `0.885` vs `0.877`.

**Minimum fix**
- Add bootstrap confidence intervals for:
  - macro AUROC
  - per-domain AUROC where important
  - pairwise delta for `Ret+VLM` vs `ExpertCtx`
  - pairwise delta for `ExpertCtx` vs `V2 Agent`
- In the paper, emphasize larger and more stable gaps such as the classical-to-hybrid jump, not only tiny method-to-method gains.

### 3. The headline claim must be tightened one more time

The evidence is now stronger for a **cross-domain hybrid evidence design** than for a **universal anomaly detection agent**. If you keep the old framing, you will invite objections about the remaining weak domains and the lack of stable efficiency gains.

**Minimum fix**
- Headline the paper as:
  - cross-domain benchmark
  - retrieval + patch expert + VLM hybrid
  - expert-as-context vs expert-as-router
- Treat "agent" as secondary language or drop it entirely from the central claim.

### 4. Cost is still a secondary story, not a primary win

You now have two operating points, which is good. But the best-accuracy system still uses `100%` VLM calls, so this is not yet an accuracy-and-efficiency breakthrough.

**Minimum fix**
- Present the Pareto story explicitly:
  - **best accuracy**: family-adaptive or `ExpertCtx` depending validation
  - **best efficiency**: routed hybrid at `41%` VLM calls
- Add the cost-vs-AUROC plot and make clear that the paper offers a tradeoff frontier, not one method that dominates everything.

### 5. D5c remains a substantive weakness, not just a noisy tail case

`D5c Liver` remains materially weaker than the rest of the benchmark. That is acceptable if diagnosed honestly, but not if buried inside a macro average.

**Minimum fix**
- Keep the current failure analysis and make it sharper:
  - lesion size / subtlety
  - alignment / slice mismatch
  - contrast-window issues
  - expert-only hit, VLM-only hit, both miss
- If feasible, add one targeted appendix experiment:
  - simple registration/alignment or
  - crop/window prompting for liver CT

You do not need to solve liver perfectly. You do need to show you understand why it fails.

### 6. The baseline package is much better, but still one baseline short of bulletproof

The current baselines are good enough for a serious draft, but `WinCLIP` or a stronger patch-comparison baseline would still strengthen the paper against the obvious reviewer question: "Did you just beat weak classical baselines?"

**Minimum fix**
- If you can implement `WinCLIP`, do it.
- If not, be explicit that the main classical comparison set is `DINOv2-Global`, `DINOv2-PatchNN`, and your `PatchCore-style` expert, and explain why those are the most relevant training-free few-shot comparators for this setting.

This is now a moderate issue, not a critical blocker.

## Re-Assessment of Prior Concerns

### Fully addressed

1. **Weak expert signal**
2. **Need for causal ablation**
3. **Need for a cleaner hybrid story**
4. **Need for basic classical baselines**

### Partially addressed

1. **Weak-domain diagnosis**
2. **Cost-vs-accuracy positioning**
3. **Claim control around universality**

### Still blocking final submission

1. **Test-set-tuned family fusion**
2. **Missing final CI/significance presentation**
3. **Need final held-out evaluation protocol freeze**

## Submission Assessment

### As a method paper

Borderline, but still not quite there.

### As a benchmark + hybrid design paper

Now genuinely close.

If you validate the family-adaptive fusion off test, finalize the CI/significance table, and present the paper as a benchmark-backed hybrid design study rather than a grand agent paper, this could become submission-ready.

## Reviewer-style Summary

This is the first round where the work looks like a potentially publishable paper rather than a promising system exploration. The strongest story is no longer "an agent with more tools and rounds performs better." The stronger and more defensible story is: **retrieval provides strong reference grounding, a patch-level expert adds complementary local evidence, and the VLM uses that evidence best when it is presented as context rather than as a routing signal.** That is a good result. The remaining job is to turn a good result into a rigorous paper artifact.
