# Experiment Log: Descriptor ablation completion

**Started**: 2026-04-14
**Purpose**: Add generic-descriptor baseline for SeedVL and Qwen3.5 on test split to complete 3-backbone descriptor ablation.

## R000 — Implement generic descriptor + CLI switch

### Plan
Add `build_prompt_v0_generic()` in `benchmark/scripts/infer.py` and wire it via the existing `EGRA_DESCRIPTOR_MODE` environment variable (task|generic, default task). Minimally invasive: only changes the prompt builder selection.

### Log
- 2026-04-14 R000: added `build_prompt_v0_generic(has_refs)` + `DESCRIPTOR_MODE` env-var switch in `build_prompt_v0()`. Verified round-trip: generic mode produces domain-agnostic prompt, task mode unchanged.
- Status: **DONE**

## R001 — Qwen3.5 smoke test (20 items)

### Command
```
DESCRIPTOR_MODE=generic \
python3 -m benchmark.scripts.infer \
  --backend qwen3 \
  --variant v0_direct \
  --manifest benchmark/manifests/full_manifest.json \
  --split test \
  --max_items 20 \
  --output benchmark/results/qwen35_v0_generic_smoke.json \
  --max_workers 4
```

### Log
- 2026-04-14 R001: Qwen3.5 smoke 20/20 parsed, scores 0.000..0.980, latency ~3s/item. OK.
- Status: **DONE**

## R002 — SeedVL smoke test (20 items)
- 2026-04-14 R002: SeedVL smoke 20/20 parsed, scores 0.020..1.000, latency ~5s/item. OK.
- Status: **DONE**

## R003 — Qwen3.5 full test sweep (1298 items)
- Launched in background. ETA ~60-80 min based on smoke test latency × 1298/20.

## R004 — SeedVL full test sweep (1298 items)
- Launched in background. ETA ~100-120 min.

### Issue + Fix
- 22:48 R004 batch mode FAILED: all 1418 items returned "account is invalid" 400 errors. Batch endpoint requires a different model name (probably an "ep-..." endpoint id) than sync. Smoke test passed because it used sync.
- 22:55 Restarted R004 in sync mode (8 workers). ETA ~15 min (1418 × 5s / 8).

- 23:45 R003 Qwen full run done: 1418 items, 0 errors, 989K tokens in / 158K tokens out. Wall-clock: ~70 min.
- 23:45 R004 SeedVL sync rerun done: 1418 items, 0 errors, 5.7M tokens in / 812K tokens out. Wall-clock: ~45 min.
- Status: **DONE**

## R005 — Bootstrap analysis (paired, stratified)

### Results

| Backbone | Generic | Task-anchored | Δ | 95% CI | Sig @ 5% |
|----------|---------|---------------|---|--------|----------|
| GPT-5.4  | 0.761 | 0.825 | +6.4 pp | [+4.4, +8.4] | ✓ |
| SeedVL   | 0.748 | 0.789 | +4.1 pp | [+1.6, +6.4] | ✓ |
| Qwen3.5  | 0.760 | 0.792 | +3.2 pp | [+1.0, +5.5] | ✓ |

All three 95% CIs exclude zero; direction is consistent across frontier + non-frontier + open-weight backbones. **C1 claim (descriptors generalise across backbones) verified.**

Gain magnitude scales with backbone capability (GPT-5.4 largest, Qwen3.5 smallest) — intuitive: stronger models extract more from explicit task anchoring.

- Status: **DONE**

## R006 — Paper update
- Updated abstract: "+6.4/+4.1/+3.2 pp on GPT-5.4, SeedVL, Qwen3.5 (all significant)"
- Updated intro Fig 1 caption, contributions bullet, Finding 1
- Updated Appendix C: full 3-column per-domain ablation table (33 cells)
- Updated Conclusion
- Regenerated fig_intuition.pdf: Panel (a) now shows 3-backbone grouped bars
- Recompiled: 18 pages total, main body ~10 pages, 0 undefined refs, 0 overfull.
- Status: **DONE**

## Summary

Successfully completed descriptor ablation on 3 backbones with full test-split evidence. Key deliverables:

| File | Purpose |
|------|---------|
| `benchmark/results/qwen35_v0_direct_generic_test.json` | Qwen3.5 generic-descriptor test predictions |
| `benchmark/results/seedvl_v0_direct_generic_test.json` | SeedVL generic-descriptor test predictions |
| `paper/figures/descriptor_cis.json` | Paired bootstrap + per-domain output |
| `paper/figures/gen_descriptor_bootstrap.py` | Bootstrap script (reproducible) |
| `paper/figures/gen_intuition.py` (updated) | Fig 1 with 3-backbone Panel (a) |
| `paper/sections/A_appendix.tex` (updated) | Full 33-cell per-domain ablation |

The paper's headline descriptor claim is now defensible across 3 backbones, addressing the codex R2 critical issue (C2) directly.
