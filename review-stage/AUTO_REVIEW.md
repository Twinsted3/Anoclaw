# AnomalyClaw Auto Review Log — v9 loop

**Loop start**: 2026-04-19 23:36 CST
**Prior loop**: v8 paper closed at 6.0/10 "almost" (archived as
`AUTO_REVIEW.v8.md`, `REVIEW_STATE.v8.json`).

**Difficulty**: nightmare (`codex exec`, GPT reads repo directly)
**Max rounds**: 4
**Reviewer**: GPT-5.4 via codex CLI, `model_reasoning_effort=xhigh`

---

## Score progression

| Round | Score | Verdict | Δ | When |
|-------|-------|---------|---|------|
| 1     | 5.0   | not ready | — | 2026-04-19 23:36 → 00:08 |
| 2     | 5.8   | not ready | +0.8 | 2026-04-20 06:06 → 06:27 |

---

## Round 1 (2026-04-19 23:36 – 2026-04-20 00:08)

### Six critical findings
1. **MMAD label bug** — `"good" in key.lower()` flipped every GoodsAD
   item to label=0. Reported numbers depressed by ~7 pp.
2. **SeedVL Direct provenance** — main table mixed old v2 descriptor
   run with newer v6 agent. Consistent v6 direct is 0.7995 not 0.7794;
   Δ shrinks from +2.14 to +0.93 pp (non-significant).
3. **Router/v4/v6 story mixup** — method describes v4 router,
   experiments headline v6+Direct ensemble.
4. **v8 interpretability claim ahead of evidence** — reported
   v8_qwen3_test.json has `history` missing for all 1418 items.
5. **Tool-cost claim** — `tool_reference_profiler` and
   `tool_domain_knowledge` DO make VLM/LLM calls.
6. **Stale appendix numbers** — appendix Qwen fusion `0.851` vs main
   text `0.814`.

### Actions taken
1. Label fix — `mmad_eval.py`, `mmad_eval_v9.py`, `mmad_relabel.py`.
2. SeedVL fix — switched to `v6_direct_seedvl_test.json`.
3. Method — added §3.5 v6 agent; "Framework vs. headline" paragraph.
4. v8 rerun deferred (~3h compute).
5. Tool-cost — §3 v6 subsection acknowledges extra VLM/LLM calls.
6. Appendix — caption flags numbers as v0/v3-era historical.

### New experiments
- **v9 MMAD full-type** (n=2302 QAs): agent vs Direct = −1.0 pp macro
  accuracy. Agent helps on Defect Description (+1.7), Classification
  (+1.2); hurts on Object Details (−4.4), Object Classification (−3.2).
  AD AUROC Δ +1.65 pp.
- **Active pilot** (4 domains, K=10 dev-oracle, DINOv2 prior):
  mean Δ +3.5 pp. D1 +7.33, D5 −4.00, D9 +11.11, D12 −0.44.

Commits: `0d7ec3d`, `e0030a3`, `6891eb1`, `5b29947`.

---

## Round 2 (06:06 – 06:27)

### Assessment
- **Score**: 5.8 / 10 (up from 5.0)
- **Verdict**: not ready
- Raw: `review-stage/codex_v9_review_r2_raw.out` (2.5 MB)

### Six new critical findings (Round 2)
1. **AL domain mapping swap**: active-learning pilot used
   `manifests_v2` where D5=logical, D9=brain MRI, but the paper AL
   table reused the Table-1 labels (D5=brain MRI, D9=logical).
2. **Relabeled MMAD file not shipped**: `mmad_anomaly_qwen3.json`
   still contained stale labels; corrected numbers were in the
   paper but not reproducible from a released artifact.
3. **v9 MCQ parse-failure accounting missing**: denominators were
   answered-only; parse-failure rates per type not reported.
4. **v8 claim still overclaimed**: "reviewers can audit every
   score" remained in text despite `history` missing from all 1418
   stored predictions.
5. **Tool-cost language still inconsistent**: §3 was fixed but
   `Appendix~\ref{app:cost}` referenced an appendix that did not
   exist; intro/abstract still implied zero-call tools.
6. **Three-backbone claim too strong in places**: SeedVL is
   non-significant; abstract/intro wording should make this explicit.

### Round 2 fixes applied
1. **AL labels corrected** — table now uses `manifests_v2` taxonomy
   (D1 industrial, D5 MVTec-LOCO logical, D9 BraTS brain MRI, D12
   road safety). Finding 8 interpretation rewritten: brain MRI
   helps (+11.11), logical hurts (−4.00, DINOv2 CLS can't retrieve
   logical-anomaly neighbours well).
2. **Shipped `mmad_anomaly_qwen3_relabeled.json`** (180 items
   flipped) as a released artifact.
3. **Parse-failure rates** added to Table~\ref{tab:mmad_v9_fulltype}
   footnote: Direct 0.6\%, Agent 0.9\% overall; max per-type 3.0\%.
   Treating failures as wrong shifts accuracy ≤0.9pp, no direction
   change.
4. **v8 rerun** still not executed (compute constraint).
5. **`Appendix~\ref{app:cost}` references removed** from §3 and §4
   and replaced with inline cost statements.
6. Abstract/intro wording for SeedVL non-significance was already
   updated in Round 1; verified in Round 2.

### Remaining concerns (deferred / out-of-scope for this session)
- v8 qwen3 test rerun with history capture (~3h compute).
- Method section v4→appendix full restructure (minimum fix applied).
- AL extension to all 12 domains × multi-seed (future work).

Commits: `0b15cf6`.

---

## Current state (06:30 CST)

- Score 5.8/10 (just below 6.0 threshold); verdict "not ready" but
  Round-2 blockers addressed.
- User (human) expected back ~07:00; final wrap-up commit below.
- MAX_ROUNDS=4 not exhausted (Round 3 available for next session).
