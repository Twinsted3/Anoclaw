# Autonomous Review Loop - Round 2

**Date**: 2026-04-05
**Reviewer mode**: senior ML reviewer (top-venue bar)
**Scope reviewed**: updated V4 summary in `AUTO_REVIEW.md`, saved V4 sample-level result files, and prior round-1 review

## Bottom Line

- **Score**: `6.5/10`
- **Verdict**: `Almost`, but still **not ready** for submission
- **Reason for score increase**: one major technical objection has been addressed. The work now has a credible new empirical result: a real patch-level expert improves the best system when its evidence is exposed to the VLM as context rather than used as a router.

## What Has Been Convincingly Addressed

1. **The expert is no longer weak.**
   - The global DINO score objection from round 1 is substantially fixed.
   - The patch expert is now a legitimate few-shot AD component rather than a placeholder score.

2. **The multi-stage routed agent story has been productively falsified.**
   - This is a useful result, not a failure.
   - The new evidence says that routing and score fusion are unstable, while expert-grounded VLM judgment works better.

3. **A simpler and better method has emerged.**
   - The strongest result is now `V4 Expert-Informed`, not the older Scout/Judge-style pipeline.
   - That is a cleaner paper story.

## What The New Evidence Actually Supports

The work no longer supports:

- "few-shot expert should route the agent"
- "expert confidence is reliable enough for skipping VLM calls"

The work now supports:

- "few-shot patch evidence improves VLM anomaly judgment when provided as structured evidence"
- "expert-as-context is more robust than expert-as-router"

That is a publishable mechanism claim if you verify it cleanly.

## Ranked Remaining Weaknesses and Minimum Fixes

### 1. The causal claim for `Expert-Informed` is not yet proven

Right now the best result could still be challenged as "more useful prompt text" rather than genuine use of patch-level evidence. The paper needs to show that the gain comes from expert evidence specifically.

**Minimum fix**
- Add a targeted ablation set:
  - retrieval + VLM only
  - retrieval + VLM + generic extra explanation text of matched length
  - retrieval + VLM + global-similarity text only
  - retrieval + VLM + patch expert text
  - retrieval + VLM + patch expert text plus suspicious crops / coordinates
- Keep token budget approximately matched where possible.
- If patch expert text still wins, your mechanism claim becomes much more defensible.

### 2. Experimental discipline is still below submission standard

You explicitly note there is no calibration-split tuning yet, no confidence intervals, and no proper classical baseline table. That is still a blocker for a top venue.

**Minimum fix**
- Freeze calibration/dev/test protocol and rerun the final table without test-time tuning.
- Add bootstrap confidence intervals for macro AUROC and for the main pairwise comparisons.
- Add at least:
  - DINOv2 PatchNN
  - your PatchCore-style expert as a standalone baseline
  - a WinCLIP-like baseline if feasible
  - the simple hybrid baseline that corresponds to your final claim

### 3. Result bookkeeping is not clean enough yet

The markdown summary now presents a 10-domain macro result, but the saved V4 JSON result file still contains additional domain codes (`D6`, `D8`) beyond that 10-domain table. That kind of mismatch will trigger reviewer distrust if it leaks into the paper.

**Minimum fix**
- Make one canonical evaluation manifest per paper table.
- Save one metrics file per run with:
  - exact domain list
  - item counts per domain
  - per-domain AUROC
  - macro aggregation rule
- Ensure the reported macro is reproducible from that exact artifact.

### 4. The best method improves accuracy, but not efficiency

`V4 Expert-Informed` is your best method, but it still uses `100%` VLM calls. So the work now has a stronger accuracy story than before, but not yet a cost-efficiency story. If you oversell efficiency, reviewers will push back.

**Minimum fix**
- Present two operating points:
  - **best accuracy**: `Expert-Informed`
  - **best efficiency**: routed hybrid
- Add a cost-vs-AUROC plot and do not claim the same method dominates both.
- If possible, test a low-cost variant that always includes expert text but compresses VLM input aggressively.

### 5. The hardest domains still reveal unresolved mechanism gaps

`D5c Liver` remains poor, and `D4 Concrete` regresses relative to the earlier best. These are not side issues.

What they mean:

- `D5c Liver`: the current patch evidence is not enough for subtle lesion discrimination under CT appearance variation.
- `D4 Concrete`: the patch expert may be emphasizing texture irregularity that is not aligned with what the VLM needs for crack judgment.

**Minimum fix**
- For `D5c`, add one domain-specific branch:
  - registration/alignment for CT if geometry is stable, or
  - slice-window / contrast-aware preprocessing and lesion-scale crop prompts.
- For `D4`, inspect whether top-1% pooling is too brittle; compare percentile pooling variants and crop scales.
- Add a failure taxonomy for both domains and show whether the error is from the expert, the VLM, or their interaction.

### 6. The paper story is still broader than the evidence

You are closer now, but the safest claim is still not "universal anomaly detection agent." The evidence is stronger for a **cross-domain reference-based hybrid design study** than for a universal agent framework.

**Minimum fix**
- Re-title and frame the paper around:
  - cross-domain benchmark
  - patch expert + VLM hybrid
  - expert-as-context vs expert-as-router
- Report family-level results and explicitly note which anomaly families benefit most.

## Re-Assessment of Prior Concerns

### Addressed

1. **Weak expert signal**: largely addressed.
2. **Overbuilt multi-call pipeline**: addressed by simplification and empirical falsification.
3. **Need for a cleaner hybrid story**: addressed.

### Partially addressed

1. **Fusion mechanism**: improved, but not yet causally proven.
2. **Universal claim**: still too broad.
3. **Weak-domain diagnosis**: still incomplete.

### Not yet addressed

1. **Classical baselines**
2. **Calibration and significance**
3. **Cost-vs-accuracy analysis**
4. **Strict result accounting**

## Submission Assessment

### As a method paper

Still `No`, but much closer.

### As a benchmark + hybrid design paper

`Almost yes`, if you complete the minimum evidence package above.

## Reviewer-style Summary

This round meaningfully improved the work. The important discovery is not that a few-shot expert can replace the VLM, but that **structured patch-level expert evidence can improve VLM judgment when used as context rather than as a gate**. That is a cleaner, more believable, and more publishable story than the earlier routed-agent design. The remaining gap is now mostly experimental rigor and claim control, not basic method direction.
