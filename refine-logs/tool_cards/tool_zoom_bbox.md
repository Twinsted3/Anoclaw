# Tool Card: tool_zoom_bbox

**Verdict:** DROP (diagnostic-only positives exist but are not prompt-actionable — see discussion)  
**Overall (dev n=480)**: tool=0.6610  direct=0.7599  Δ=-0.0989  
**Calls**: 290/480 (60.4%)  
**Errors**: 13  
**Multiple testing**: Tested 20 slices at α=0.05 (two-sided); expected false positive niches ≈ 0.50. CI uncorrected for multiple testing — dev-derived hints should be revalidated.  

## Positive niches (n≥10, Δ>0, 95% CI lower > 0)

| slice [type, metric] | n | tool AUROC | direct AUROC | Δ | 95% CI |
|---|---|---|---|---|---|
| domain=D1 [diagnostic, pooled] | 40 | 0.912 | 0.785 | +0.127 | [+0.001, +0.263] |

**Actionable positives**: none — all positives are diagnostic-only slices (e.g. domain labels the agent cannot observe).

## Anti-niches (Δ<0, 95% CI upper < 0)

| slice [type, metric] | n | tool AUROC | direct AUROC | Δ | 95% CI |
|---|---|---|---|---|---|
| direct_margin>=0.30 (confident) [actionable_pre_call, macro] | 480 | 0.661 | 0.760 | -0.099 | [-0.154, -0.045] |
| tool_used=True [diagnostic, macro] | 290 | 0.650 | 0.755 | -0.105 | [-0.187, -0.036] |
| n_turns>=2 (actually explored) [diagnostic, macro] | 290 | 0.650 | 0.755 | -0.105 | [-0.183, -0.029] |
| subspacead_rank in [0.4,0.8) (moderate expert) [actionable_after_expert_score, macro] | 215 | 0.602 | 0.762 | -0.160 | [-0.284, -0.036] |
| domain=D4 [diagnostic, pooled] | 40 | 0.655 | 0.851 | -0.196 | [-0.390, -0.034] |
| domain=D5 [diagnostic, pooled] | 40 | 0.441 | 0.780 | -0.339 | [-0.523, -0.117] |
| domain=D6 [diagnostic, pooled] | 40 | 0.481 | 0.826 | -0.345 | [-0.521, -0.174] |

## All slices (audit)

| slice [type, metric] | n | tool | direct | Δ | 95% CI |
|---|---|---|---|---|---|
| domain=D1 [diagnostic, pooled] | 40 | 0.912 | 0.785 | +0.127 | [+0.001, +0.263] |
| domain=D7 [diagnostic, pooled] | 40 | 0.988 | 0.939 | +0.049 | [-0.011, +0.129] |
| domain=D5b [diagnostic, pooled] | 40 | 0.832 | 0.835 | -0.003 | [-0.138, +0.135] |
| domain=D10 [diagnostic, pooled] | 40 | 0.682 | 0.695 | -0.013 | [-0.182, +0.170] |
| domain=D5c [diagnostic, pooled] | 40 | 0.532 | 0.558 | -0.025 | [-0.241, +0.185] |
| domain=D5d [diagnostic, pooled] | 40 | 0.722 | 0.770 | -0.047 | [-0.231, +0.128] |
| domain=D9 [diagnostic, pooled] | 40 | 0.644 | 0.704 | -0.060 | [-0.288, +0.176] |
| tool_used=False [diagnostic, macro] | 190 | 0.689 | 0.766 | -0.077 | [-0.177, +0.028] |
| n_turns=1 (no tool, tool-offered) [diagnostic, macro] | 190 | 0.689 | 0.766 | -0.077 | [-0.174, +0.025] |
| direct_margin>=0.30 (confident) [actionable_pre_call, macro] | 480 | 0.661 | 0.760 | -0.099 | [-0.154, -0.045] |
| tool_used=True [diagnostic, macro] | 290 | 0.650 | 0.755 | -0.105 | [-0.187, -0.036] |
| n_turns>=2 (actually explored) [diagnostic, macro] | 290 | 0.650 | 0.755 | -0.105 | [-0.183, -0.029] |
| subspacead_rank<=0.4 (weak expert) [actionable_after_expert_score, macro] | 177 | 0.580 | 0.695 | -0.115 | [-0.251, +0.026] |
| subspacead_rank>=0.8 (strong expert) [actionable_after_expert_score, macro] | 88 | 0.701 | 0.821 | -0.120 | [-0.534, +0.026] |
| domain=D2 [diagnostic, pooled] | 40 | 0.605 | 0.756 | -0.151 | [-0.365, +0.080] |
| subspacead_rank in [0.4,0.8) (moderate expert) [actionable_after_expert_score, macro] | 215 | 0.602 | 0.762 | -0.160 | [-0.284, -0.036] |
| domain=D8 [diagnostic, pooled] | 40 | 0.436 | 0.620 | -0.184 | [-0.407, +0.035] |
| domain=D4 [diagnostic, pooled] | 40 | 0.655 | 0.851 | -0.196 | [-0.390, -0.034] |
| domain=D5 [diagnostic, pooled] | 40 | 0.441 | 0.780 | -0.339 | [-0.523, -0.117] |
| domain=D6 [diagnostic, pooled] | 40 | 0.481 | 0.826 | -0.345 | [-0.521, -0.174] |

## Agent hint (injected into agent_v7 prompt if KEEP)

**tool_zoom_bbox has diagnostic-only positives** — DROP because no prompt-actionable trigger is available.
**Avoid tool_zoom_bbox on:** `domain=D6` (Δ=-0.345 on n=40).
