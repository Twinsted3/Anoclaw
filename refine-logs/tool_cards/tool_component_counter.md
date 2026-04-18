# Tool Card: tool_component_counter

**Verdict:** DROP  
**Overall (dev n=480)**: tool=0.6477  direct=0.7599  Δ=-0.1122  
**Calls**: 264/480 (55.0%)  
**Errors**: 0  
**Multiple testing**: Tested 20 slices at α=0.05 (two-sided); expected false positive niches ≈ 0.50. CI uncorrected for multiple testing — dev-derived hints should be revalidated.  

## Positive niches (n≥10, Δ>0, 95% CI lower > 0)

_None found. Tool has no demonstrated niche on dev._

## Anti-niches (Δ<0, 95% CI upper < 0)

| slice [type, metric] | n | tool AUROC | direct AUROC | Δ | 95% CI |
|---|---|---|---|---|---|
| direct_margin>=0.30 (confident) [actionable_pre_call, macro] | 480 | 0.648 | 0.760 | -0.112 | [-0.176, -0.047] |
| subspacead_rank in [0.4,0.8) (moderate expert) [actionable_after_expert_score, macro] | 215 | 0.633 | 0.762 | -0.129 | [-0.270, -0.024] |
| tool_used=True [diagnostic, macro] | 264 | 0.617 | 0.762 | -0.146 | [-0.231, -0.057] |
| n_turns>=2 (actually explored) [diagnostic, macro] | 264 | 0.617 | 0.762 | -0.146 | [-0.231, -0.053] |
| subspacead_rank<=0.4 (weak expert) [actionable_after_expert_score, macro] | 177 | 0.546 | 0.695 | -0.149 | [-0.281, -0.015] |
| domain=D5d [diagnostic, pooled] | 40 | 0.584 | 0.770 | -0.186 | [-0.381, -0.006] |
| domain=D6 [diagnostic, pooled] | 40 | 0.538 | 0.826 | -0.289 | [-0.445, -0.140] |
| domain=D5 [diagnostic, pooled] | 40 | 0.480 | 0.780 | -0.300 | [-0.535, -0.091] |

## All slices (audit)

| slice [type, metric] | n | tool | direct | Δ | 95% CI |
|---|---|---|---|---|---|
| domain=D1 [diagnostic, pooled] | 40 | 0.863 | 0.785 | +0.078 | [-0.070, +0.235] |
| domain=D7 [diagnostic, pooled] | 40 | 0.977 | 0.939 | +0.039 | [+0.000, +0.111] |
| domain=D5b [diagnostic, pooled] | 40 | 0.825 | 0.835 | -0.010 | [-0.154, +0.112] |
| domain=D10 [diagnostic, pooled] | 40 | 0.683 | 0.695 | -0.012 | [-0.198, +0.165] |
| subspacead_rank>=0.8 (strong expert) [actionable_after_expert_score, macro] | 88 | 0.758 | 0.821 | -0.063 | [-0.423, +0.105] |
| tool_used=False [diagnostic, macro] | 216 | 0.679 | 0.755 | -0.075 | [-0.166, +0.022] |
| n_turns=1 (no tool, tool-offered) [diagnostic, macro] | 216 | 0.679 | 0.755 | -0.075 | [-0.168, +0.014] |
| domain=D5c [diagnostic, pooled] | 40 | 0.467 | 0.558 | -0.090 | [-0.316, +0.142] |
| domain=D9 [diagnostic, pooled] | 40 | 0.612 | 0.704 | -0.091 | [-0.349, +0.159] |
| direct_margin>=0.30 (confident) [actionable_pre_call, macro] | 480 | 0.648 | 0.760 | -0.112 | [-0.176, -0.047] |
| domain=D4 [diagnostic, pooled] | 40 | 0.731 | 0.851 | -0.120 | [-0.285, +0.035] |
| subspacead_rank in [0.4,0.8) (moderate expert) [actionable_after_expert_score, macro] | 215 | 0.633 | 0.762 | -0.129 | [-0.270, -0.024] |
| tool_used=True [diagnostic, macro] | 264 | 0.617 | 0.762 | -0.146 | [-0.231, -0.057] |
| n_turns>=2 (actually explored) [diagnostic, macro] | 264 | 0.617 | 0.762 | -0.146 | [-0.231, -0.053] |
| subspacead_rank<=0.4 (weak expert) [actionable_after_expert_score, macro] | 177 | 0.546 | 0.695 | -0.149 | [-0.281, -0.015] |
| domain=D2 [diagnostic, pooled] | 40 | 0.588 | 0.756 | -0.169 | [-0.384, +0.027] |
| domain=D5d [diagnostic, pooled] | 40 | 0.584 | 0.770 | -0.186 | [-0.381, -0.006] |
| domain=D8 [diagnostic, pooled] | 40 | 0.425 | 0.620 | -0.195 | [-0.414, +0.019] |
| domain=D6 [diagnostic, pooled] | 40 | 0.538 | 0.826 | -0.289 | [-0.445, -0.140] |
| domain=D5 [diagnostic, pooled] | 40 | 0.480 | 0.780 | -0.300 | [-0.535, -0.091] |

## Agent hint (injected into agent_v7 prompt if KEEP)

**When to use tool_component_counter:** no documented positive niche on dev. DROPPED.
**Avoid tool_component_counter on:** `domain=D5` (Δ=-0.300 on n=40).
