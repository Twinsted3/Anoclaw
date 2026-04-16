# Codex Review Round 1 — 2026-04-13

**Overall**: Borderline reject. Solid empirical hook but overclaims agent contribution.

## Critical Issues (must fix)

1. **Overclaims agent**: SeedVL +2.9pp is real but GPT tie undermines "agent" narrative. Reframe: descriptors are main contribution, agent is complementary.
2. **Route B contradicts principle**: "expert as evidence, not oracle" but Route B uses 0.7 expert weight. Fix wording or justify.
3. **Score extraction unspecified**: How exactly is AUROC score computed from VLM JSON output? Need precise formula.
4. **Benchmark underspecified**: Need per-domain appendix (source, normal/anomaly definition, ref selection, split IDs, licenses).
5. **Route C (enumerate) is prototype at 60%**: Either remove from main method or fully evaluate. Currently misleading.
6. **No statistical tests**: Need paired bootstrap CIs for v0 vs AnomalyClaw.
7. **No budget-matched baselines**: Need random escalation at 1.3 calls to show routing signal matters.

## Important Issues

8. **Grouped macro by type**: Report texture/medical/alignment/logical group averages, not just 11-domain macro.
9. **Descriptor ablation**: Show per-domain old→new descriptor impact systematically.
10. **VLM/expert complementarity matrix**: Show per-domain who is right/wrong.
11. **Full ablation table**: All 6 failed variants with test numbers.
12. **Release supplementary material during review**: descriptors, prompts, split IDs.

## Minor Issues

13. Inconsistent domain numbering (D1-D11 vs D01-D11).
14. Some placeholder citations.
15. Page budget check needed.
