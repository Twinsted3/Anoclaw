# Per-Domain × Strategy Matrix

## Macro AUROC summary (test split)

| Backbone | Strategy | Macro AUROC | n domains | n items |
|----------|----------|-------------|-----------|---------|
| expert | global | 0.6284 | 12 | 1418 |
| expert | patchknn | 0.6352 | 12 | 1418 |
| expert | subspacead | 0.7560 | 11 | 1298 |
| gpt54 | debate | 0.7876 | 12 | 1418 |
| gpt54 | direct | 0.8130 | 12 | 1418 |
| gpt54 | fusion_v0_subspace | 0.8418 | 11 | 1298 |
| gpt54 | grounded | 0.6648 | 12 | 1418 |
| gpt54 | interpret | 0.8048 | 12 | 1418 |
| qwen35 | debate | 0.6589 | 12 | 1418 |
| qwen35 | direct | 0.7762 | 12 | 1418 |
| qwen35 | fusion_v0_subspace | 0.8526 | 11 | 1298 |
| qwen35 | interpret | 0.7779 | 12 | 1418 |
| seedvl | debate | 0.7649 | 12 | 1418 |
| seedvl | direct | 0.7794 | 12 | 1418 |
| seedvl | fusion_v0_subspace | 0.8066 | 11 | 1298 |
| seedvl | interpret | 0.7783 | 12 | 1418 |

## Per-domain AUROC per strategy

### gpt54

| Domain | direct | fusion_v0_subspace | debate | interpret | grounded | ExpertSubspace | Oracle |
|--------|---|---|---|---|---|---|---|
| D1 | 0.962 | 0.988 | 0.940 | 0.962 | 0.933 | 0.966 | 0.988 (gpt54:fusion_v0_subspace) |
| D10 | 0.878 | 0.929 | 0.837 | 0.878 | 0.500 | 0.908 | 0.929 (gpt54:fusion_v0_subspace) |
| D2 | 0.774 | 0.849 | 0.784 | 0.779 | 0.774 | 0.841 | 0.849 (gpt54:fusion_v0_subspace) |
| D4 | 0.623 | 0.648 | 0.698 | 0.658 | 0.673 | 0.701 | 0.800 (expert:patchknn) |
| D5 | 0.796 | 0.808 | 0.787 | 0.784 | 0.780 | 0.672 | 0.808 (gpt54:fusion_v0_subspace) |
| D5b | 0.934 | 0.943 | 0.917 | 0.935 | 0.500 | 0.893 | 0.943 (gpt54:fusion_v0_subspace) |
| D5c | 0.745 | 0.751 | 0.634 | 0.694 | 0.500 | 0.698 | 0.751 (gpt54:fusion_v0_subspace) |
| D5d | 0.890 | 0.880 | 0.785 | 0.839 | 0.500 | 0.530 | 0.890 (gpt54:direct) |
| D6 | 0.827 | 0.755 | 0.778 | 0.826 | 0.815 | 0.464 | 0.827 (gpt54:direct) |
| D7 | 0.968 | 0.989 | 0.896 | 0.932 | 0.977 | 0.984 | 1.000 (expert:global) |
| D8 | 0.677 | — | 0.698 | 0.684 | 0.525 | — | 0.698 (gpt54:debate) |
| D9 | 0.683 | 0.721 | 0.698 | 0.687 | 0.500 | 0.660 | 0.721 (gpt54:fusion_v0_subspace) |

**Oracle macro AUROC (gpt54)**: 0.8503

### seedvl

| Domain | direct | fusion_v0_subspace | debate | interpret | grounded | ExpertSubspace | Oracle |
|--------|---|---|---|---|---|---|---|
| D1 | 0.874 | 0.952 | 0.846 | 0.881 | — | 0.966 | 0.966 (expert:subspacead) |
| D10 | 0.878 | 0.922 | 0.850 | 0.881 | — | 0.908 | 0.922 (seedvl:fusion_v0_subspace) |
| D2 | 0.863 | 0.887 | 0.875 | 0.878 | — | 0.841 | 0.887 (seedvl:fusion_v0_subspace) |
| D4 | 0.660 | 0.686 | 0.668 | 0.630 | — | 0.701 | 0.800 (expert:patchknn) |
| D5 | 0.760 | 0.769 | 0.792 | 0.772 | — | 0.672 | 0.792 (seedvl:debate) |
| D5b | 0.864 | 0.917 | 0.859 | 0.857 | — | 0.893 | 0.917 (seedvl:fusion_v0_subspace) |
| D5c | 0.492 | 0.521 | 0.546 | 0.497 | — | 0.698 | 0.698 (expert:subspacead) |
| D5d | 0.876 | 0.862 | 0.818 | 0.854 | — | 0.530 | 0.876 (seedvl:direct) |
| D6 | 0.822 | 0.725 | 0.687 | 0.819 | — | 0.464 | 0.822 (seedvl:direct) |
| D7 | 0.936 | 0.969 | 0.952 | 0.958 | — | 0.984 | 1.000 (expert:global) |
| D8 | 0.677 | — | 0.625 | 0.659 | — | — | 0.677 (seedvl:direct) |
| D9 | 0.651 | 0.663 | 0.661 | 0.652 | — | 0.660 | 0.663 (seedvl:fusion_v0_subspace) |

**Oracle macro AUROC (seedvl)**: 0.8349

### qwen35

| Domain | direct | fusion_v0_subspace | debate | interpret | grounded | ExpertSubspace | Oracle |
|--------|---|---|---|---|---|---|---|
| D1 | 0.903 | 0.976 | 0.809 | 0.903 | — | 0.966 | 0.976 (qwen35:fusion_v0_subspace) |
| D10 | 0.800 | 0.914 | 0.611 | 0.800 | — | 0.908 | 0.914 (qwen35:fusion_v0_subspace) |
| D2 | 0.672 | 0.828 | 0.608 | 0.657 | — | 0.841 | 0.841 (expert:subspacead) |
| D4 | 0.712 | 0.732 | 0.663 | 0.757 | — | 0.701 | 0.800 (expert:patchknn) |
| D5 | 0.762 | 0.808 | 0.618 | 0.749 | — | 0.672 | 0.808 (qwen35:fusion_v0_subspace) |
| D5b | 0.849 | 0.942 | 0.677 | 0.844 | — | 0.893 | 0.942 (qwen35:fusion_v0_subspace) |
| D5c | 0.684 | 0.771 | 0.533 | 0.680 | — | 0.698 | 0.771 (qwen35:fusion_v0_subspace) |
| D5d | 0.918 | 0.912 | 0.750 | 0.863 | — | 0.530 | 0.918 (qwen35:direct) |
| D6 | 0.828 | 0.773 | 0.736 | 0.811 | — | 0.464 | 0.828 (qwen35:direct) |
| D7 | 0.911 | 0.983 | 0.902 | 0.916 | — | 0.984 | 1.000 (expert:global) |
| D8 | 0.598 | — | 0.508 | 0.680 | — | — | 0.680 (qwen35:interpret) |
| D9 | 0.676 | 0.741 | 0.491 | 0.676 | — | 0.660 | 0.741 (qwen35:fusion_v0_subspace) |

**Oracle macro AUROC (qwen35)**: 0.8515
