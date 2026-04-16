# Experiment Audit Report — 2026-04-13

## Audit Summary

| Check | Status | Notes |
|-------|--------|-------|
| GPT-5.4 v0 test AUROC | **CORRECTED** | Was 0.813 (with D8), now 0.823 (excl D8) |
| Agent v1 calibration macro | PASS | 0.837 verified |
| Agent v1 test macro | PASS | 0.826 verified |
| Data leakage (cal↔test) | PASS | 0 overlap |
| SubspaceAD thresholds from cal only | PASS | Verified median computation |
| No test-split threshold tuning | PASS | Thresholds frozen from calibration |
| Domain descriptors complete | PASS | 13 descriptors for 13 domains |
| Error rates | PASS | 0% errors on all test runs |

## Corrected Numbers (excl D8 Avenue)

| Method | Test macro AUROC |
|--------|-----------------|
| GPT-5.4 v0 (correct descriptors) | **0.825** |
| CrossAD-Agent v1 (all domains) | **0.826** (+0.1pp) |
| CrossAD-Agent v1 (cal-guided selection) | **0.830** (+0.5pp) |
| v0 (old descriptors) | 0.754 |

## Key Findings Verified
1. Domain descriptor fix: +7.1pp macro (0.754 → 0.825)
2. CrossAD-Agent adds +0.5pp on top with calibration-guided domain selection
3. Agent most valuable on D2 retail (+5.1pp) and D10 VisA (+1.5pp)
4. No data leakage between splits
5. All thresholds frozen from calibration, never tuned on test
