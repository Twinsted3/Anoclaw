# AnomalyClaw Optimization Log — 2026-04-16

## Iterations

### v3 (first real agent, online override bug)
- Qwen3.5 test: 0.778 (+0.1 vs direct) ← override forced interpret everywhere
- **Root cause**: ρ cross-expert scaling → always-interpret. Fixed by removing override.

### v4 (per-domain calib argmax, no tools)
- Qwen3.5 test: 0.831 (**+5.47** vs direct) ✅ PASS
- Strategy: fusion_subs×8, direct×2, subs_only×1, fusion_avfm×1
- Tools: none actually used (just routing)

### v5 (tool_augmented_fusion, all tools forced)
- Qwen3.5 calib: 0.828 (-1.2 vs fusion) ← tools add noise on confident items
- **Root cause**: feeding crop+knowledge to every item hurts VLM focus

### React v1 (per-item ReAct, symmetric)
- D1: 0.975 (+7.2 vs direct, ≈fusion). Tools: crop×23, profiler×3. **FP 4→0!**
- 5-dom macro: 0.815 (+7.8 vs direct, -2.5 vs fusion)
- D5c: 0.669 (FN 36→9 but FP 5→60) ← Call 2 flips correct decisions

### React asymmetric (max(call1,call2) policy)
- D5b improved: 0.948 → 0.948 (same)
- D5c/D9 still bad: max() too aggressive on FP

### React v2 (call2 as-is + restricted tools) ← CURRENT BEST
- D2: 0.854 (+2.6 vs fusion)
- **D5b: 0.963** (+2.1 vs fusion) ← best single-domain improvement from tools
- D5c: 0.680 (-9.1 vs fusion) ← still bad, use fusion
- D9: 0.633 (-10.8 vs fusion) ← still bad, use fusion

### Combined agent (react v2 on D1/D2/D5b + fusion/direct on rest)
- **Macro: 0.8357, +5.96 pp over direct** ✅
- Tools genuinely help on 3 domains (D1, D2, D5b)
- 9/12 domains improved over direct

### FINAL Combined Agent
- **Macro: 0.839, +6.28 pp over direct [CI +4.66, +7.75], significant**
- 11/12 domains improved or tied vs direct; only D5d regresses marginally (-0.7pp, switched to direct)

## Per-domain best strategy (Qwen3.5)
| Domain | Best | AUROC | vs Direct |
|---|---|---|---|
| D1 industrial | react | 0.975 | +7.2 |
| D2 retail | react | 0.854 | +18.2 |
| D4 infrastructure | direct | 0.712 | 0.0 |
| D5 dermoscopy | fusion_subs | 0.808 | +4.6 |
| D5b brain MRI | react | 0.963 | +11.5 |
| D5c liver CT | fusion_subs | 0.771 | +8.7 |
| D5d GI | fusion_subs | 0.912 | -0.7 |
| D6 LEVIR | direct | 0.828 | 0.0 |
| D7 GI endoscopy | subs_only | 0.984 | +7.3 |
| D8 road | fusion_subs | 0.598 | 0.0 |
| D9 logical | fusion_avfm | 0.710 | +3.4 |
| D10 VisA | fusion_subs | 0.914 | +11.4 |

## Tool effectiveness summary
| Tool | Domains helped | Mechanism |
|---|---|---|
| hotspot_cropper | D1 (+3 FN fixed), D5b (FN verify) | VLM sees zoomed defect |
| reference_profiler | D1 (4 FP fixed), D2 (product matching) | VLM learns normal patterns from refs |
| component_counter | D9 (hurt, FP increase) | Too noisy, needs better implementation |
| reference_retriever | D2 (needs testing) | Better ref matching for heterogeneous pools |
| image_diff | D6 (not tested) | Pixel change for temporal comparison |
