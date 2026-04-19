# AnomalyClaw Auto Review Log — v9 loop

**Loop start**: 2026-04-19 23:36 CST
**Prior loop**: v8 paper closed at 6.0/10 "almost" (archived as
`AUTO_REVIEW.v8.md`, `REVIEW_STATE.v8.json`).

**Difficulty**: nightmare (`codex exec`, GPT reads repo directly)
**Max rounds**: 4
**Reviewer**: GPT-5.4 via codex CLI, `model_reasoning_effort=xhigh`

---

## Round 1 — in progress

### Concurrent work
- v9 unified agent: `agent_v9.py`, `agent_prompt_v9.py`, `mmad_eval_v9.py`
  committed; dev500 run in progress (PID 207516; n~110 of 2302 at 23:45).
- Active learning pilot: `active_learning.py` + driver committed; experiments
  queued after dev500 finishes.
- Codex review: launched 23:36 as background `codex exec` (PID 211359);
  output at `review-stage/codex_v9_review_r1_raw.out`.

### Self-discovered critical finding (pre-review)
While codex was still probing the repository, we noticed that its early
data-inspection commands surfaced a label-assignment bug that the prior
v8 paper's MMAD section was built on top of:

**Bug**: `mmad_eval.py` (and the initial `mmad_eval_v9.py`) derives
`label_gt` as

```python
label_gt = 0 if ("good" in key.lower() or "normal" in key.lower()) else 1
```

The substring match is against the full path `key`. Because the dataset
directory is named `GoodsAD`, `"good" in "goodsad/food_box/..."` is
always true, and **every GoodsAD item (anomalous or not) receives
label=0**. This silently depressed the paper's reported pooled MMAD
AUROC.

### Fix
- `benchmark/scripts/mmad_eval_v9.py:42` now derives AD labels from
  `options[Answer]` (exact MCQ ground truth), with fallback to the
  immediate parent folder (`good|normal|ok` $\to 0$).
- `benchmark/scripts/mmad_eval.py:70` same fix (legacy file).
- `benchmark/scripts/mmad_relabel.py` (new): post-processing script that
  rewrites `label_gt` on any existing result JSON using the correct rule.

### Recomputed paper numbers (Qwen3.5, n=989 stratified AD subset)

| Metric        | Old (buggy) | Fixed        | Δ          |
|---------------|-------------|--------------|------------|
| Direct AUROC  | 0.7079      | **0.7811**   | +7.32 pp   |
| Ensemble AUROC| 0.7310      | **0.8114**   | +8.04 pp   |
| Δ (Ens−Direct)| +2.31 pp    | **+3.03 pp** | +0.72 pp   |
| 95% CI        | [+0.8,+3.9] | [+1.48,+4.54]| shifted +  |
| P(Δ > 0)      | 0.996       | **0.999**    | +          |

GoodsAD subset now has both label classes present; AUROC computable:
Direct 0.628, Ensemble 0.665, +3.69 pp.

**Effect on paper claim**: direction and qualitative story unchanged
(ensembling helps AUROC, MCQ accuracy unchanged). Magnitude is *larger*
than previously reported — the bug underestimated the improvement.

### Paper updates
- `paper/sections/4_experiments.tex` §4 MMAD table + narrative
  replaced with corrected numbers; added a footnote disclosing the
  label-derivation rule.
- `RESUME.md` MMAD line updated.

### Pending
- Await codex review completion (20-45 min typical).
- Dev500 continues; post-process with `mmad_relabel.py` before analysis.

---
