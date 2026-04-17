# Tool Usage and Effect Analysis
- **Agent results**: `benchmark/results/v6_5_agent_qwen3_test.json` (n=1418)
- **Direct baseline**: `benchmark/results/v6_direct_qwen3_test.json` (n=1418)
- **Agent macro AUROC**: 0.7713  (across 12 domains)
- **Direct macro AUROC**: 0.7684
- **Items with 0 tool calls**: 268/1418 (18.9%)

## Turn-count distribution

| turns | count | pct |
|---|---|---|
| 1 | 268 | 18.9% |
| 2 | 209 | 14.7% |
| 3 | 283 | 20.0% |
| 4 | 266 | 18.8% |
| 5 | 392 | 27.6% |

## Per-tool usage and effect

Macro AUROC on items WHERE the tool was called, comparing agent vs Direct on those same items. Δ = agent - direct (positive = tool helped).

| tool | #items | cov% | call_count | agent AUROC | direct AUROC | Δ |
|------|--------|------|-----------|-------------|--------------|---|
| tool_expert_score | 1078 | 76.0% | 1155 | 0.7308 | 0.7364 | -0.0055 |
| tool_hotspot_cropper | 606 | 42.7% | 609 | 0.7190 | 0.7663 | -0.0473 |
| tool_reference_profiler | 459 | 32.4% | 459 | 0.6253 | 0.7195 | -0.0942 |
| tool_side_by_side | 422 | 29.8% | 502 | 0.6420 | 0.6638 | -0.0218 |
| tool_image_diff | 285 | 20.1% | 297 | 0.6180 | 0.6299 | -0.0119 |
| tool_zoom_bbox | 41 | 2.9% | 48 | 0.7767 | 0.7067 | +0.0700 |
| tool_component_counter | 30 | 2.1% | 34 | 0.5107 | 0.6444 | -0.1337 |
| tool_patch_grid | 20 | 1.4% | 20 | 0.5278 | 0.5833 | -0.0556 |
| tool_rotate_align | 12 | 0.8% | 12 | 0.4833 | 0.7667 | -0.2833 |
| tool_domain_knowledge | 4 | 0.3% | 4 | 1.0000 | 1.0000 | +0.0000 |
| tool_segment_and_count | 1 | 0.1% | 1 | 0.0000 | 0.0000 | +0.0000 |

### Subset: NO tool called (n=268)

- agent AUROC: 0.8297
- direct AUROC: 0.8646
- Δ = -0.0348

## Per-domain tool usage (count of items using tool)

| domain | component_counter | domain_knowledge | expert_score | hotspot_cropper | image_diff | patch_grid | reference_profiler | rotate_align | segment_and_count | side_by_side | zoom_bbox | no_tool |
|--|--|--|--|--|--|--|--|--|--|--|--|--|
| D1 (n=120) | 1 | 0 | 87 | 55 | 20 | 0 | 13 | 6 | 0 | 14 | 2 | 30 |
| D10 (n=120) | 0 | 0 | 101 | 85 | 29 | 0 | 5 | 3 | 0 | 21 | 4 | 17 |
| D2 (n=120) | 1 | 1 | 100 | 64 | 22 | 0 | 44 | 3 | 0 | 27 | 2 | 7 |
| D4 (n=120) | 0 | 0 | 99 | 60 | 14 | 0 | 23 | 0 | 0 | 23 | 8 | 17 |
| D5 (n=120) | 0 | 1 | 95 | 72 | 18 | 1 | 34 | 0 | 0 | 41 | 0 | 25 |
| D5b (n=120) | 0 | 0 | 75 | 72 | 23 | 0 | 27 | 0 | 0 | 37 | 2 | 43 |
| D5c (n=120) | 0 | 0 | 101 | 17 | 7 | 0 | 19 | 0 | 0 | 8 | 0 | 17 |
| D5d (n=120) | 0 | 0 | 87 | 69 | 12 | 0 | 26 | 0 | 0 | 34 | 9 | 30 |
| D6 (n=98) | 0 | 0 | 57 | 20 | 91 | 4 | 58 | 0 | 1 | 58 | 6 | 7 |
| D7 (n=120) | 0 | 0 | 76 | 61 | 7 | 3 | 30 | 0 | 0 | 19 | 5 | 41 |
| D8 (n=120) | 0 | 2 | 111 | 0 | 24 | 8 | 96 | 0 | 0 | 93 | 3 | 5 |
| D9 (n=120) | 28 | 0 | 89 | 31 | 18 | 4 | 84 | 0 | 0 | 47 | 0 | 29 |

