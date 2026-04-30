# §4 Edit Plan — v1 → v2 (manifests_v2, v10 agent)

Drafted 2026-04-22 04:45 for user review. Data: `paper/figures/v2_main_results.json` + `v2_table1_draft.tex`.

## Scope

§4 was written around: v1 manifest (D5b/c/d subsplits, D8=Avenue), v6.5/v6.6
agents, descriptor Direct. All three need to change.

## Three levels of rewrite (user picks one)

### Level 1 — Minimal (target: 2-3 h)

Keep most prose; swap only what must change.

Files to edit:
- `paper/sections/4_experiments.tex` lines 7-8 (benchmark paragraph): rewrite
  domain list to v2 taxonomy (D1–D12, Real3D-AD, DermaMNIST independent,
  drop Avenue).
- Lines 22-49 (Table 1): replace whole table with
  `paper/figures/v2_table1_draft.tex` contents.
- Lines 51-54 (Bootstrap CI summary): replace v1 CIs with v2 CIs.
- Line 80 (Finding 5 opening): change "AnomalyClaw v6 agent" framing to
  "AnomalyClaw v10 agent" + update headline numbers (0.864/0.814/0.809 →
  0.772/0.732/0.738). Keep most of paragraph intact.
- Line 24 (Table 1 caption): agent choice line "v6.5 on Qwen3.5/SeedVL, v6.6
  on GPT-5.4" → "v10 (v9 refutation + parallel Direct) on all three".

Keep:
- §4.2 score-diversity ablation (v6.5 data) — add footnote "ablation run on
  v1 manifest with v6.5; v2 numbers use v10".
- All v8 refutation prose — mark as historical.
- Finding 1 descriptor ablation (v1 numbers) — mark as v1.

Risk: reviewer will notice §4.2 ablation uses v6.5 while main table uses v10.

### Level 2 — Moderate (recommended, target: 4-5 h)

Level 1 +

- Rewrite Finding 5 around v10's 3-backbone story: "GPT agent strong, Direct
  marginal; SeedVL balanced; Qwen3.5 agent weak, Direct saves". Highlight
  the new Qwen3.5 finding: agent alone significantly worse than Direct
  (-4.46 pp) but ensemble still positive — demonstrates v10 robustness.
- Drop the v8 refutation paragraph (Finding 6) entirely — v8 is historical.
- Rewrite §4.3 "Statistical significance" to match new v2 CIs.
- Rewrite §4.2 ablation caveat section or DROP it (v6.5 vs v10 mismatch).

Risk: paper is re-angled; might change claim structure.

### Level 3 — Full rewrite (target: 8-10 h)

Level 2 + re-run score-diversity ablation on v9 scores, regenerate all
per-domain appendix tables, redraw per-domain bar chart.

Risk: large time sink; may not change acceptance odds.

## My recommendation

**Level 2**. The v2 story is genuinely richer (ensemble saves weak agents),
and the v8/v6.5 prose is no longer accurate. Level 1 leaves a reviewer trap
at §4.2. Level 3 is overkill for a migration.

## Data artefacts ready

- `paper/figures/v2_main_results.json` — full per-domain AUROC + bootstrap
  CIs for all 3 backbones.
- `paper/figures/v2_table1_draft.tex` — drop-in Table 1 replacement.
- `benchmark/results/v2/v10_agent_{gpt,seedvl,qwen3}_test.json` — raw v10 output.
- `benchmark/results/v2/v0_direct_generic_{gpt,seedvl,qwen3}_test.json` — raw
  standalone Direct (superseded by v10's internal direct_score, kept as
  sanity check).

## Headline numbers (for abstract update if needed)

```
GPT-5.4 :  Direct 0.731 → Ens 0.772 (+4.01 pp, sig, P=1.000)
SeedVL  :  Direct 0.678 → Ens 0.738 (+5.99 pp, sig, P=1.000)
Qwen3.5 :  Direct 0.714 → Ens 0.732 (+1.69 pp, P=0.971, CI touches 0)
```

Legacy v1 numbers (for comparison):
```
GPT-5.4 v1: 0.846 → 0.864 (+1.74 pp) — v2 is -9 pp overall but stronger Δ
SeedVL  v1: 0.800 → 0.809 (+0.93 pp) — v2 larger gain (+5.99 vs +0.93)
Qwen3.5 v1: 0.768 → 0.814 (+4.53 pp) — v2 smaller gain (+1.69 vs +4.53)
```
