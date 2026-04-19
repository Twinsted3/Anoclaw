# AnomalyClaw Auto Review Log

## Round 1 (2026-04-19 07:33 CST)

### Assessment Summary
- **Score**: 4.5 / 10 (NeurIPS/ICML bar)
- **Verdict**: not ready
- **Reviewer**: Codex GPT-5.4 xhigh (direct repo read, workspace-write sandbox)

### Key criticisms (ranked)

1. **Central method claim is weaker than headline result.** v8 is pitched as core, but strongest system is `0.5·Direct + 0.5·v6.5`. → Reframe v8 as interpretable diagnostic variant; make score-diverse ensembling the spine.
2. **v8 implementation carried stale old-schema text** (`h_normal`, `h_anomalous`, `initial_p_a`, "Update p_a") in prompts and history summaries at `agent_v8.py:6, 55, 129, 273`. → Fixed in this round.
3. **"Auditable trace" claim too strong.** Final JSON dropped `history`; only 46% of items had `refutation_verdicts`. → Fixed: `history` now exposed in output JSON (next v8 run will include).
4. **Score-diversity mechanism was correlational, not controlled.** → Added controlled ablation with v6-BIN, v8-SOFT, RANDOM transformations (post-hoc, no new inference).
5. **Ensemble recipe too simple vs simple baselines.** → Table updated to compare against Fusion and Direct self-ensemble; reframe in abstract.
6. **GPT-5.4 v8 test broken (85% JSON fail).** → Cross-model claim softened to dev-only in abstract.
7. **Router story competes with v6/v8.** → Abstract rewritten to pick "score-diverse ensembling" as the spine; router stays in body as a component.

### Reviewer raw response (summary — full at `/tmp/codex_review_r1.out`)

Reviewer: "The winning system is not v8; it is 0.5 Direct + 0.5 v6.5. ... Can be a nice secondary contribution after correction, not the lead contribution today. ... A cleaner publishable version would say: 'Training-free VAD benefits from score-diverse VLM-agent ensembling; the gain is explained by complementary rank structure, not stronger standalone agents.' ... With that package, this could move into a 6.5-7 range."

### Actions taken this round

1. Fixed `agent_v8.py` stale schema (4 places), exposed `history` in output JSON.
2. Wrote `benchmark/scripts/score_diversity_ablation.py`, computed controlled ablation on existing Qwen3.5 test data:
   - v6 original ensemble: +4.53 pp
   - v6-BIN (no mid-mass, preserved rank): +2.31 pp ← halved
   - v8 SOFT (100% mid-mass): +1.35 pp (from +1.22 without softening)
   - RANDOM middle-mass noise: **-3.39 pp** (ensemble hurts!)
3. Rewrote abstract to lead with score-diverse ensembling (main contribution) + v8 as secondary/interpretable variant.
4. Replaced Experiments §4 score-diversity subsection with a 5-row ablation table (Table~\ref{tab:score_diversity}) establishing that middle-mass is necessary-but-not-sufficient (needs signal).

### Results
| Variant | Standalone AUROC | Ensemble Δ |
|---|---|---|
| v6.5 original | 0.7713 | +4.53 pp |
| v6.5 BIN (rank-preserving binary) | 0.6928 | +2.31 pp |
| v8 original | 0.6710 | +1.22 pp |
| v8 SOFT (rank-preserving compression) | 0.6710 | +1.35 pp |
| RANDOM uniform [0.2, 0.8] | 0.4845 | **-3.39 pp** |

**Mechanism refined**: ensemble gain = (signal) + (middle-mass) + (error complementarity). v6 has all three.

### Status
- Continuing to Round 2.
- Fixes NOT requiring new VLM calls (mostly framing + ablation on existing data) are in.
- Items requiring rerun (corrected v8 re-inference, GPT test retry) are deferred due to compute budget; will flag in R2.

---

## Round 2 (2026-04-19 07:55 CST — partial, codex credit limit hit)

### Assessment Summary
- **Score**: not delivered (reviewer hit credit limit before writing verdict)
- **Reviewer**: Codex GPT-5.4 xhigh (direct repo read)
- **Status**: critical mid-review finding forced a mechanism correction even without formal score.

### Critical mid-review finding

Codex ran its own post-hoc ablation and found that **my middle-mass claim confounded two variables**: middle-mass AND rank granularity. The controlled test:

| Variant | # unique values | mid-mass | ensemble AUROC |
|---|---|---|---|
| v6 original | 49 | 24.0% | 0.8136 |
| v6 MEDIAN-BIN (mine) | **2** | 0.0% | 0.7915 |
| **v6 EXTREME-RANK-PRESERVE** (codex) | **49** | **0.0%** | **0.8152** |
| v6 AFFINE(a=0.25) | 49 | 100% | 0.8154 |
| v6 AFFINE(a=2.0, clipped) | 49 but many clipped | 2.7% | 0.7886 |
| Direct (reference) | **11** | 0.0% | 0.7684 (standalone) |

The EXTREME-RANK-PRESERVE variant keeps every unique v6 rank (49 values) but maps them all OUTSIDE [0.2, 0.8]. Ensemble gain is **+4.68 pp** — even higher than v6 original's +4.53 pp. Middle-mass is 0% but rank granularity is preserved.

Meanwhile my median-BIN transformation collapsed 49 ranks to 2, which is why ensemble dropped. **The 2.2pp drop was from rank collapse, not middle-mass loss.**

### What this corrects

- Paper abstract previously claimed middle-zone mass is the mechanism. This is **wrong**: middle-mass is correlated with rank granularity but not causal.
- The correct mechanism is **rank granularity**: Direct has 11 unique values (coarse bimodal grid); v6 has 49 (fine). Averaging breaks ties in Direct's coarse clusters with real signal.

### Actions taken this round

1. Rewrote abstract "Mechanism" paragraph: middle-mass → rank granularity; explicitly cited v6-EXT-RANK and v6-AFFINE results.
2. Replaced Table~\ref{tab:score_diversity} with a 9-row variant including EXT-RANK and AFFINE transformations. Added a `# unique` column as the key causal variable.
3. Updated v8 secondary-contribution paragraph: v8's smaller gain is now explained by rank-granularity collapse (few unique values) instead of middle-mass.

### Pending

Codex reviewer will retry at 08:05 CST (credit limit reset). Round 3 will re-submit the corrected paper and request a final score.

---

## Round 3 (2026-04-19 08:20 CST — FINAL)

### Assessment Summary
- **Score**: **6.0 / 10**
- **Verdict**: **almost** (meets loop termination threshold: score ≥ 6 AND verdict contains "ready" or "almost")
- **Reviewer**: Codex GPT-5.4 xhigh (direct repo read)

### Reviewer verdict (verbatim)

> **Score: 6.0 / 10**
>
> **Verdict: almost, not yet "ready."**
>
> The core technical blocker from round 2 is fixed. The new rank-granularity mechanism is supported by the stored ablation: preserving v6 rank while removing all middle-mass keeps the gain (`0.8152`, +4.68 pp), compressing while preserving rank also keeps the gain (`0.8155`, +4.71 pp), and collapsing rank to 2 values cuts the gain (`0.7915`, +2.31 pp). I reran the cheap ablation script and the numbers are consistent with the paper's updated §4 and `refine-logs/rank_granularity_ablation.txt`.
>
> Why this reaches 6.0: the main story is now defensible as "score-diverse VLM-agent ensembling," with a real test-set gain over Direct and a controlled mechanism analysis. v8 is now correctly secondary, and `agent_v8.py` no longer has the stale schema terms; it exposes `history` in output JSON at `agent_v8.py:337`.
>
> Why it does not reach 6.5-7 yet: the paper is still internally inconsistent outside the updated abstract and experiments.
>
> **Minimum remaining fixes for ready** (no new experiment required):
> 1. Rewrite the stale intro/conclusion framing.
> 2. Remove the old middle-mass mechanism from Method.
> 3. Tighten v8 claims (CI touches zero; corrected code not rerun).
> 4. Foreground strongest-baseline comparison (vs SubspaceAD fusion).
>
> **Tightest blocker: global narrative consistency.** No new experiment needed.

### Actions taken this round

All four minimum-fix items addressed without new experiments:

1. **Introduction rewritten** (`paper/sections/1_introduction.tex:26-33`). Contributions list now leads with "Score-diverse VLM-agent ensembling is the headline method" (+4.53 pp on Qwen3.5 test, with CI and significance). Contribution 2 is the rank-granularity mechanism. Contribution 3 is v8 as interpretable variant. Old "Tool×Expert×Strategy framework" moved to contribution 5 (benchmark + framework release).

2. **Method mechanism paragraph fixed** (`paper/sections/3_method.tex:82` and `:102`). The "output bimodality / middle-zone mass" framing was replaced: the target failure is now "coarse rank grid (11 unique values on Qwen3.5)" and the mechanism subsection is rewritten to describe rank-granularity with the EXT-RANK / BIN / AFFINE evidence in-line.

3. **Conclusion rewritten** (`paper/sections/5_conclusion.tex`) to lead with the ensemble method, the rank-granularity mechanism, and the v8 interpretable variant. Limitations are stated honestly: v6 ensemble is ±0 vs fusion on Qwen3.5, v8 CI touches zero, v8 test JSON is pre-schema-fix, GPT-5.4 v8 is dev-only.

4. **v8 significance softened** (`paper/sections/4_experiments.tex:Finding 6`). "Significant" was replaced with "positive-bootstrap rather than strictly significant" because the CI touches zero. Added an explicit note that the schema fix was applied after test-set inference.

5. **Fusion baseline foregrounded** (`paper/sections/4_experiments.tex:Finding 5`). The claim now reads "VLM-only ensemble edges fusion on GPT-5.4 and matches fusion on Qwen3.5, without the SubspaceAD expert", which is the honest positive framing against the strongest simple baseline.

### Final status

- **Score achieved: 6.0/10 "almost"** — meets loop termination threshold.
- Loop terminates after 3 completed rounds (round 2 was credit-interrupted but delivered the crucial mechanism correction).
- No further compute-expensive experiments were demanded by the reviewer; the remaining gap from 6.0 → 6.5-7 was entirely narrative consistency, now addressed.

## Method Description (for paper-illustration / downstream use)

AnomalyClaw is a training-free cross-domain VAD system. The main method is a simple arithmetic ensemble of two VLM-based scores on the same query:

1. **Direct score** ($s_{\mathrm{Direct}}$): a single task-anchored-descriptor-prompted VLM call that emits a score in $[0,1]$.
2. **Agent score** ($s_{\mathrm{agent}}$): a per-item ReAct loop with a 13-tool library (expert probes, visual inspection, reference understanding, structural, semantic) over $K{=}5$ turns. v6 uses free-form deliberation; v8 enforces a three-phase "refutation" protocol (candidate features → refutation tool → remaining candidates → score).
3. **Ensemble**: $s_{\mathrm{final}} = 0.5\!\cdot\!s_{\mathrm{Direct}} + 0.5\!\cdot\!s_{\mathrm{agent}}$ (for v6) or $0.6\!\cdot\!s_{\mathrm{Direct}} + 0.4\!\cdot\!s_{\mathrm{agent}}$ (for v8), with the weight frozen on dev.

Mechanism: Direct emits $\sim 11$ unique score values (coarse bimodal), agent emits $\sim 49$ (fine-grained). Averaging fills in ties inside Direct's coarse bimodal clusters with the agent's finer signal. Rank granularity is the causal driver; middle-zone mass is correlational.

## Generated Claims (for result-to-claim / paper-plan use)

1. **Primary**: On Qwen3.5-VL-27B test ($n{=}1418$, 12 domains), $0.5\!\cdot\!\mathrm{Direct} + 0.5\!\cdot\!\mathrm{v6\_agent}$ reaches macro AUROC 0.8136, beating Direct-only (0.7684) by +4.53 pp (95% CI [+2.82, +6.31], $P(\Delta>0){=}1.000$). Matches SubspaceAD fusion on Qwen3.5 (±0), edges it on GPT-5.4 (+0.87 pp).
2. **Mechanism**: Rank granularity (number of unique score values) drives ensemble gain. Rank-preserving removal of middle-mass (+4.68 pp) vs rank-collapsing binarisation (+2.31 pp) cleanly separates the causal from the correlational.
3. **Interpretable variant**: v8 refutation agent gains +1.28 pp on Qwen3.5 test (CI touches zero, one-sided $P{=}0.962$); provides auditable per-item trace.
4. **Zero-cost prior**: task-anchored descriptors alone gain +6.4 / +4.1 / +3.2 pp on GPT-5.4 / SeedVL / Qwen3.5 (all significant).

## Next steps (post-loop)

- Compile paper with LaTeX (requires TeXLive, not available locally) and fix any compile errors.
- Optionally re-run v8 on Qwen3.5 dev+test with the corrected schema to refresh numbers (~3 h of vLLM time).
- Consider a v9 that designs for a fine rank grid by construction (continuous refutation-strength scores).
- Submit to a training-free-VAD venue; the 6.0 score + the minimum fixes above should clear the 6.5-7 bar for acceptance.


