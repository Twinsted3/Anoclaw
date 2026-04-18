# Trigger Rule Discovery — dev n=480

## Setup

Each item is placed in a (rank × direct_confidence) cell:
- rank: subspacead normalized rank (lo ≤0.4, md 0.4-0.8, hi ≥0.8)
- direct_confidence: |direct_score - 0.5| (uncertain <0.15, moderate 0.15-0.30, confident ≥0.30)

Flip values: +2=flip→correct, +1=improved, 0=neutral, -1=worsened, -2=flip→wrong.
Cell **net_flips = sum of flip values**. Positive net = tool net-helps in that cell.

## Per-tool cell grids (net_flips, n_items)

### tool_component_counter

| rank\direct | uncertain | moderate | confident |
|---|---|---|---|
| rank=lo | -33 (n=124) | — | -12 (n=53) |
| rank=md | -10 (n=113) | — | -50 (n=102) |
| rank=hi | -2 (n=22) | — | -9 (n=66) |

### tool_domain_knowledge

| rank\direct | uncertain | moderate | confident |
|---|---|---|---|
| rank=lo | -30 (n=124) | — | -8 (n=53) |
| rank=md | -13 (n=113) | — | -57 (n=102) |
| rank=hi | +0 (n=22) | — | -14 (n=66) |

### tool_expert_score

| rank\direct | uncertain | moderate | confident |
|---|---|---|---|
| rank=lo | -34 (n=124) | — | -9 (n=53) |
| rank=md | -30 (n=113) | — | -75 (n=102) |
| rank=hi | -4 (n=22) | — | -2 (n=66) |

### tool_hotspot_cropper

| rank\direct | uncertain | moderate | confident |
|---|---|---|---|
| rank=lo | -22 (n=123) | — | -4 (n=53) |
| rank=md | +3 (n=113) | — | -60 (n=102) |
| rank=hi | -3 (n=22) | — | +1 (n=66) |

### tool_image_diff

| rank\direct | uncertain | moderate | confident |
|---|---|---|---|
| rank=lo | -15 (n=124) | — | +0 (n=53) |
| rank=md | +1 (n=113) | — | -42 (n=102) |
| rank=hi | -1 (n=22) | — | -12 (n=66) |

### tool_patch_grid

| rank\direct | uncertain | moderate | confident |
|---|---|---|---|
| rank=lo | -8 (n=91) | — | -2 (n=46) |
| rank=md | -8 (n=100) | — | -37 (n=84) |
| rank=hi | +1 (n=14) | — | +4 (n=50) |

### tool_reference_profiler

| rank\direct | uncertain | moderate | confident |
|---|---|---|---|
| rank=lo | -14 (n=124) | — | -6 (n=53) |
| rank=md | -5 (n=113) | — | -56 (n=102) |
| rank=hi | +7 (n=22) | — | -10 (n=66) |

### tool_rotate_align

| rank\direct | uncertain | moderate | confident |
|---|---|---|---|
| rank=lo | -37 (n=124) | — | -11 (n=53) |
| rank=md | +2 (n=113) | — | -39 (n=102) |
| rank=hi | -3 (n=22) | — | -2 (n=66) |

### tool_segment_and_count

| rank\direct | uncertain | moderate | confident |
|---|---|---|---|
| rank=lo | -24 (n=124) | — | -8 (n=53) |
| rank=md | +0 (n=113) | — | -51 (n=102) |
| rank=hi | -1 (n=22) | — | +0 (n=66) |

### tool_side_by_side

| rank\direct | uncertain | moderate | confident |
|---|---|---|---|
| rank=lo | -25 (n=124) | — | -6 (n=53) |
| rank=md | +7 (n=113) | — | -67 (n=102) |
| rank=hi | +1 (n=22) | — | +1 (n=66) |

### tool_texture_fft

| rank\direct | uncertain | moderate | confident |
|---|---|---|---|
| rank=lo | -6 (n=68) | — | +1 (n=16) |
| rank=md | -2 (n=27) | — | -30 (n=36) |
| rank=hi | +2 (n=6) | — | -2 (n=7) |

### tool_zoom_bbox

| rank\direct | uncertain | moderate | confident |
|---|---|---|---|
| rank=lo | -21 (n=121) | — | -3 (n=52) |
| rank=md | -8 (n=110) | — | -57 (n=99) |
| rank=hi | +3 (n=20) | — | -6 (n=65) |

## Cross-tool cell summary

Averaged net_flips per cell across all tools. A consistently positive cell → robust trigger.

| rank\direct | uncertain | moderate | confident |
|---|---|---|---|
| rank=lo | avg_net=-22.4 (n̄=116, 0/12 tools +) | — | avg_net=-5.7 (n̄=49, 1/12 tools +) |
| rank=md | avg_net=-5.2 (n̄=104, 4/12 tools +) | — | avg_net=-51.8 (n̄=95, 0/12 tools +) |
| rank=hi | avg_net=+0.0 (n̄=20, 5/12 tools +) | — | avg_net=-4.2 (n̄=60, 3/12 tools +) |

## Items where ≥7 tools correctly flipped (robust exploitable items)

These items are candidates that any tool (with disconfirm clause) reliably corrects — suggests the effect is PROMPT-driven, not tool-specific.

Found 47 such items.

| item_id | domain | label | direct | rank | +tools | -tools |
|---|---|---|---|---|---|---|
| D1_0084 | D1 | 0 | 0.95 | 0.02 | 12 | 0 |
| D1_0038 | D1 | 0 | 0.98 | 0.26 | 12 | 0 |
| D2_0092 | D2 | 1 | 0.01 | 0.63 | 12 | 0 |
| D2_0095 | D2 | 1 | 0.02 | 0.86 | 12 | 0 |
| D1_0064 | D1 | 0 | 0.98 | 0.24 | 11 | 0 |
| D2_0037 | D2 | 0 | 0.98 | 0.19 | 11 | 0 |
| D6_0000 | D6 | 0 | 0.95 | 0.82 | 11 | 0 |
| D6_0039 | D6 | 0 | 0.95 | 0.85 | 11 | 0 |
| D6_0015 | D6 | 0 | 0.98 | 0.62 | 11 | 0 |
| D7_0135 | D7 | 1 | 0.02 | 0.97 | 11 | 0 |
| D9_0022 | D9 | 0 | 0.99 | 0.28 | 11 | 0 |
| D9_0078 | D9 | 0 | 0.99 | 0.11 | 11 | 0 |
| D9_0079 | D9 | 0 | 0.98 | 0.16 | 11 | 0 |
| D10_0002 | D10 | 0 | 0.95 | 0.07 | 11 | 0 |
| D5b_0045 | D5b | 0 | 0.98 | 0.31 | 11 | 0 |
| D5b_0031 | D5b | 0 | 0.98 | 0.51 | 11 | 0 |
| D5c_0035 | D5c | 0 | 0.95 | 0.81 | 11 | 0 |
| D5c_0131 | D5c | 1 | 0.02 | 0.90 | 11 | 0 |
| D5c_0174 | D5c | 1 | 0.05 | 0.97 | 11 | 0 |
| D5d_0045 | D5d | 0 | 0.92 | 0.40 | 11 | 0 |
| D5d_0135 | D5d | 1 | 0.02 | 0.48 | 11 | 0 |
| D1_0009 | D1 | 0 | 0.95 | 0.13 | 10 | 0 |
| D9_0057 | D9 | 0 | 0.99 | 0.35 | 10 | 0 |
| D9_0121 | D9 | 1 | 0.01 | 0.58 | 10 | 0 |
| D9_0168 | D9 | 1 | 0.01 | 0.73 | 10 | 0 |
| D10_0076 | D10 | 0 | 0.98 | 0.12 | 10 | 0 |
| D5b_0067 | D5b | 0 | 0.98 | 0.53 | 10 | 0 |
| D5c_0100 | D5c | 1 | 0.05 | 0.79 | 10 | 0 |
| D5c_0165 | D5c | 1 | 0.02 | 0.87 | 10 | 0 |
| D1_0088 | D1 | 0 | 0.95 | 0.29 | 9 | 0 |
| D6_0063 | D6 | 0 | 0.98 | 0.60 | 9 | 0 |
| D6_0017 | D6 | 0 | 0.95 | 0.75 | 9 | 0 |
| D7_0159 | D7 | 1 | 0.02 | 0.87 | 9 | 0 |
| D5c_0070 | D5c | 0 | 0.95 | 0.91 | 9 | 0 |
| D5d_0023 | D5d | 0 | 0.98 | 0.39 | 9 | 0 |
| D1_0114 | D1 | 1 | 0.02 | 0.19 | 8 | 0 |
| D4_0176 | D4 | 1 | 0.05 | 0.82 | 8 | 0 |
| D8_0072 | D8 | 0 | 0.95 | 0.50 | 8 | 0 |
| D9_0039 | D9 | 0 | 0.98 | 0.05 | 8 | 0 |
| D10_0156 | D10 | 1 | 0.01 | 0.51 | 8 | 0 |

## Items where ≥7 tools wrongly flipped (universal LOSS items)

Found 80 such items.

| item_id | domain | label | direct | rank | -tools | +tools |
|---|---|---|---|---|---|---|
| D2_0170 | D2 | 1 | 0.98 | 0.13 | 12 | 0 |
| D2_0080 | D2 | 0 | 0.02 | 0.02 | 12 | 0 |
| D4_0128 | D4 | 1 | 0.95 | 0.42 | 12 | 0 |
| D4_0155 | D4 | 1 | 0.95 | 0.50 | 12 | 0 |
| D5_0030 | D5 | 0 | 0.05 | 0.21 | 12 | 0 |
| D5_0117 | D5 | 1 | 0.95 | 0.72 | 12 | 0 |
| D5_0158 | D5 | 1 | 0.95 | 0.35 | 12 | 0 |
| D1_0179 | D1 | 1 | 0.95 | 0.54 | 11 | 0 |
| D2_0133 | D2 | 1 | 0.98 | 0.08 | 11 | 0 |
| D2_0162 | D2 | 1 | 0.98 | 0.80 | 11 | 0 |
| D4_0106 | D4 | 1 | 0.95 | 0.49 | 11 | 0 |
| D5_0167 | D5 | 1 | 0.95 | 0.48 | 11 | 0 |
| D6_0111 | D6 | 1 | 0.98 | 0.66 | 11 | 0 |
| D6_0110 | D6 | 1 | 0.98 | 0.36 | 11 | 0 |
| D6_0145 | D6 | 1 | 0.95 | 0.65 | 11 | 0 |
| D6_0130 | D6 | 1 | 0.98 | 0.54 | 11 | 0 |
| D8_0126 | D8 | 1 | 0.95 | 0.50 | 11 | 0 |
| D9_0128 | D9 | 1 | 0.99 | 0.24 | 11 | 0 |
| D9_0100 | D9 | 1 | 0.99 | 0.41 | 11 | 0 |
| D9_0129 | D9 | 1 | 0.98 | 0.04 | 11 | 0 |
| D9_0090 | D9 | 1 | 0.98 | 0.03 | 11 | 0 |
| D5c_0004 | D5c | 0 | 0.02 | 0.94 | 11 | 0 |
| D5c_0042 | D5c | 0 | 0.02 | 0.88 | 11 | 0 |
| D5d_0129 | D5d | 1 | 0.98 | 0.31 | 11 | 0 |
| D5d_0161 | D5d | 1 | 0.98 | 0.51 | 11 | 0 |
| D5d_0166 | D5d | 1 | 0.98 | 0.47 | 11 | 0 |
| D2_0107 | D2 | 1 | 0.95 | 0.32 | 10 | 0 |
| D4_0126 | D4 | 1 | 0.95 | 0.63 | 10 | 0 |
| D5_0032 | D5 | 0 | 0.05 | 0.87 | 10 | 0 |
| D5_0112 | D5 | 1 | 0.95 | 0.75 | 10 | 0 |
| D5_0115 | D5 | 1 | 0.95 | 0.57 | 10 | 0 |
| D6_0133 | D6 | 1 | 0.98 | 0.82 | 10 | 0 |
| D6_0137 | D6 | 1 | 0.95 | 0.38 | 10 | 0 |
| D6_0123 | D6 | 1 | 0.98 | 0.74 | 10 | 0 |
| D6_0136 | D6 | 1 | 0.98 | 0.70 | 10 | 0 |
| D6_0106 | D6 | 1 | 0.98 | 0.64 | 10 | 0 |
| D9_0047 | D9 | 0 | 0.02 | 0.13 | 10 | 0 |
| D9_0041 | D9 | 0 | 0.02 | 0.79 | 10 | 0 |
| D9_0032 | D9 | 0 | 0.02 | 0.07 | 10 | 0 |
| D9_0176 | D9 | 1 | 0.99 | 0.31 | 10 | 0 |

## Proposed trigger rule (for agent prompt injection)

If robust cells exist (avg_net>0 AND majority of tools +), synthesize an agent rule: 'When you observe rank∈X and your current score is in direct_conf∈Y, apply disconfirm-style reconsideration.'
