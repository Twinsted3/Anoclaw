# AnomalyClaw Auto Review Log — v9 loop

**Loop start**: 2026-04-19 23:36 CST
**Prior loop**: v8 paper closed at 6.0/10 "almost" (archived as
`AUTO_REVIEW.v8.md`, `REVIEW_STATE.v8.json`).

**Difficulty**: nightmare (`codex exec`, GPT reads repo directly)
**Max rounds**: 4
**Reviewer**: GPT-5.4 via codex CLI, `model_reasoning_effort=xhigh`

---

## Round 1 (2026-04-19 23:36 – 2026-04-20 00:08)

### Assessment
- **Score**: 5.0 / 10
- **Verdict**: not ready
- Raw: `review-stage/codex_v9_review_r1_raw.out` (431 KB)

### Reviewer's six critical findings
1. **MMAD label bug** — `"good" in key.lower()` flipped every GoodsAD
   item to label=0. Reported numbers depressed by ~7 pp.
2. **SeedVL Direct provenance** — main table mixes old v2 descriptor
   run with newer v6 agent. Consistent v6 direct is 0.7995 not 0.7794;
   Δ shrinks from +2.14 pp to +0.93 pp (non-significant at 95%).
3. **Router / v4 / v6 story mixup** — method describes v4 router,
   experiments headline v6+Direct ensemble; reader cannot tell which
   system is canonical.
4. **v8 interpretability claim ahead of evidence** — reported
   v8_qwen3_test.json has `history` missing despite code fix.
5. **Tool-cost claim** — `tool_reference_profiler` and
   `tool_domain_knowledge` DO make VLM/LLM calls, but paper calls all
   13 tools "zero-call".
6. **Stale appendix numbers** — appendix Qwen fusion `0.851` vs main
   text `0.814`; appendix rows are v0/v3-era.

### Actions taken in Round 1
1. **Label fix** — `mmad_eval.py`, `mmad_eval_v9.py` rewritten;
   `mmad_relabel.py` new post-processing script. Recomputed MMAD
   AUROC on the 989-item pilot: Direct 0.7079 → 0.7811,
   Ensemble 0.7310 → 0.8114, **Δ +3.03 pp (95% CI [+1.48, +4.54],
   P=0.999 over 1000 bootstraps).** GoodsAD AUROC now reportable
   (Direct 0.628 → Ensemble 0.665, +3.69 pp). Paper §4 MMAD table
   and text updated; RESUME.md updated.
2. **SeedVL fix** — main table now uses `v6_direct_seedvl_test.json`
   (0.7995) consistently with GPT/Qwen. New Δ = +0.93 pp, CI
   [-0.32, +2.25], P=0.927. Caption updated: "positive-mean but
   CI crosses 0"; the "all-three-backbones significant" claim is
   dropped.
3. **Method section** — added `§3.5 The v6 ReAct agent (headline
   system)` between the v4 router exposition and §3.6 v8 refutation,
   plus a "Framework vs. headline recipe" paragraph at the top of §3.
4. **v8 rerun** — deferred (would consume 3 h of vLLM). §4 Finding 6
   continues to disclose the limitation.
5. **Tool-cost** — §3 v6 subsection now states the two tools that
   make extra VLM/LLM calls.
6. **Appendix** — negative-controls table caption flags its numbers as
   v0/v3-era, not comparable to v6 headline.

### New experiments in Round 1
- **v9 MMAD full-type (n=2302 QAs across 9 types)**: aggregated macro
  accuracy Direct 79.5% vs Agent 78.5% = −1.0 pp. Not a
  systematic gain. Agent niche: Defect Description (+1.7 pp),
  Defect Classification (+1.2 pp). Losses: Object Details (-4.4 pp),
  Object Classification (-3.2 pp). AD subset AUROC: Direct 0.7592
  → Agent 0.7233 → Ens 0.7757 (+1.65 pp). Section 4.6 in paper,
  positioned as architectural (not numerical) contribution.
- **Active self-evolution pilot** (K=10 dev-oracle, DINOv2 neighbour
  prior, 4 domains × 30 test items): D1 +7.33 pp, D5 −4.00 pp,
  D9 +11.11 pp, D12 −0.44 pp. Mean Δ +3.5 pp. Section 4.7.

### Round 1 state after fixes
Committed as: `0d7ec3d` (MMAD/SeedVL fixes), `e0030a3` (method/spec
alignment), `6891eb1` (v9 paper section), `5b29947` (AL pilot +
fewshot fix). Pipeline still running when Round 2 launched.

---

## Round 2 (2026-04-20 06:06 — in progress)

Launched after Round-1 fixes + v9 dev500 + AL pilot completed.
Prompt at `/tmp/codex_v9_review_r2_prompt.txt`; raw output at
`review-stage/codex_v9_review_r2_raw.out`.

### Status
- GPT-5.4 reading the repo; expected completion ~06:30 CST.
- Will record score / verdict / new findings here.
