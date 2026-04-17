# Expert × Strategy Matrix
- Direct: `benchmark/results/v6_direct_qwen3_test.json`
- Output: `refine-logs/expert_strategy_qwen3.md`

## Macro AUROC by system

| System | Macro |
|--------|------|
| Direct + subspacead α=0.2 | 0.8142 |
| Direct + subspacead α=0.3 | 0.8127 |
| Direct + subspacead α=0.1 | 0.8121 |
| Direct + subspacead α=0.5 | 0.8117 |
| Direct ⊕max⊕ subspacead | 0.8033 |
| Direct + subspacead α=0.8 | 0.7964 |
| Direct + patchknn α=0.1 | 0.7929 |
| Direct ⊕max⊕ dinov2_global | 0.7899 |
| Direct ⊕max⊕ patchknn | 0.7898 |
| Direct + anomalyvfm α=0.1 | 0.7863 |
| Direct + patchknn α=0.2 | 0.7859 |
| Direct + dinov2_global α=0.1 | 0.7854 |
| Direct + patchknn α=0.3 | 0.7826 |
| Direct + anomalyvfm α=0.2 | 0.7811 |
| Direct + dinov2_global α=0.2 | 0.7791 |
| Direct + patchknn α=0.5 | 0.7785 |
| Direct + anomalyvfm α=0.3 | 0.7776 |
| Direct ⊕max⊕ anomalyvfm | 0.7764 |
| Direct ⊕min⊕ subspacead | 0.7761 |
| Direct + dinov2_global α=0.3 | 0.7760 |
| Direct + dinov2_global α=0.5 | 0.7737 |
| Direct + anomalyvfm α=0.5 | 0.7717 |
| Direct VLM | 0.7684 |
| Direct + anomalyvfm α=0.8 | 0.7603 |
| Direct ⊕min⊕ anomalyvfm | 0.7583 |
| Direct + patchknn α=0.8 | 0.7571 |
| subspacead alone | 0.7560 |
| Direct ⊕min⊕ patchknn | 0.7526 |
| Direct ⊕min⊕ dinov2_global | 0.7461 |
| Direct + dinov2_global α=0.8 | 0.7432 |
| patchknn alone | 0.6352 |
| dinov2_global alone | 0.6284 |
| anomalyvfm alone | 0.6213 |
| **ORACLE (per-domain best row)** | **0.8438** |

## Oracle per-domain choice (upper bound)

| Domain | Best system | AUROC |
|--------|-------------|-------|
| D1 | Direct + subspacead α=0.8 | 0.9783 |
| D10 | Direct ⊕max⊕ subspacead | 0.9154 |
| D2 | subspacead alone | 0.8406 |
| D4 | Direct + dinov2_global α=0.1 | 0.9389 |
| D5 | Direct ⊕max⊕ anomalyvfm | 0.7721 |
| D5b | Direct + subspacead α=0.2 | 0.9483 |
| D5c | Direct + subspacead α=0.5 | 0.7061 |
| D5d | Direct + anomalyvfm α=0.1 | 0.9146 |
| D6 | Direct ⊕max⊕ patchknn | 0.7945 |
| D7 | dinov2_global alone | 1.0000 |
| D8 | Direct + patchknn α=0.8 | 0.6444 |
| D9 | Direct + subspacead α=0.5 | 0.6725 |

## Per-domain AUROC matrix (selected)

| domain | Direct VLM | Direct + subsp | Direct + anoma | Direct + patch | Direct + dinov |
|--|--|--|--|--|--|
| D1 | 0.919 | 0.973 | 0.975 | 0.939 | 0.956 |
| D10 | 0.801 | 0.908 | 0.828 | 0.814 | 0.826 |
| D2 | 0.725 | 0.828 | 0.678 | 0.727 | 0.717 |
| D4 | 0.794 | 0.798 | 0.815 | 0.925 | 0.933 |
| D5 | 0.701 | 0.745 | 0.758 | 0.701 | 0.748 |
| D5b | 0.855 | 0.948 | 0.902 | 0.799 | 0.792 |
| D5c | 0.624 | 0.689 | 0.674 | 0.702 | 0.601 |
| D5d | 0.905 | 0.895 | 0.913 | 0.866 | 0.855 |
| D6 | 0.792 | 0.732 | 0.675 | 0.720 | 0.710 |
| D7 | 0.923 | 0.984 | 0.896 | 0.971 | 0.974 |
| D8 | 0.616 | 0.616 | 0.616 | 0.637 | 0.626 |
| D9 | 0.564 | 0.654 | 0.643 | 0.631 | 0.611 |

