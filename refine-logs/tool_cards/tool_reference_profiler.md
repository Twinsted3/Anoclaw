# Tool Card: tool_reference_profiler

**Verdict:** DROP  
**Overall (dev n=480)**: tool=0.6785  direct=0.7599  Δ=-0.0814  
**Calls**: 442/480 (92.1%)  
**Errors**: 0  
**Multiple testing**: Tested 20 slices at α=0.05 (two-sided); expected false positive niches ≈ 0.50. CI uncorrected for multiple testing — dev-derived hints should be revalidated.  

## Positive niches (n≥10, Δ>0, 95% CI lower > 0)

_None found. Tool has no demonstrated niche on dev._

## Anti-niches (Δ<0, 95% CI upper < 0)

| slice [type, metric] | n | tool AUROC | direct AUROC | Δ | 95% CI |
|---|---|---|---|---|---|
| tool_used=True [diagnostic, macro] | 442 | 0.676 | 0.755 | -0.078 | [-0.139, -0.020] |
| n_turns>=2 (actually explored) [diagnostic, macro] | 442 | 0.676 | 0.755 | -0.078 | [-0.142, -0.019] |
| direct_margin>=0.30 (confident) [actionable_pre_call, macro] | 480 | 0.679 | 0.760 | -0.081 | [-0.137, -0.025] |
| subspacead_rank in [0.4,0.8) (moderate expert) [actionable_after_expert_score, macro] | 215 | 0.633 | 0.762 | -0.128 | [-0.260, -0.011] |
| subspacead_rank<=0.4 (weak expert) [actionable_after_expert_score, macro] | 177 | 0.535 | 0.695 | -0.160 | [-0.291, -0.018] |
| subspacead_rank>=0.8 (strong expert) [actionable_after_expert_score, macro] | 88 | 0.631 | 0.821 | -0.191 | [-0.576, -0.026] |
| domain=D5 [diagnostic, pooled] | 40 | 0.549 | 0.780 | -0.231 | [-0.421, -0.054] |
| domain=D4 [diagnostic, pooled] | 40 | 0.603 | 0.851 | -0.249 | [-0.400, -0.095] |
| domain=D6 [diagnostic, pooled] | 40 | 0.530 | 0.826 | -0.296 | [-0.483, -0.101] |

## All slices (audit)

| slice [type, metric] | n | tool | direct | Δ | 95% CI |
|---|---|---|---|---|---|
| domain=D1 [diagnostic, pooled] | 40 | 0.831 | 0.785 | +0.046 | [-0.091, +0.174] |
| domain=D10 [diagnostic, pooled] | 40 | 0.714 | 0.695 | +0.019 | [-0.133, +0.170] |
| domain=D5b [diagnostic, pooled] | 40 | 0.850 | 0.835 | +0.015 | [-0.088, +0.118] |
| domain=D5d [diagnostic, pooled] | 40 | 0.772 | 0.770 | +0.003 | [-0.190, +0.198] |
| domain=D7 [diagnostic, pooled] | 40 | 0.941 | 0.939 | +0.002 | [-0.121, +0.114] |
| tool_used=False [diagnostic, macro] | 38 | 0.810 | 0.822 | -0.012 | [-0.374, +0.309] |
| n_turns=1 (no tool, tool-offered) [diagnostic, macro] | 38 | 0.810 | 0.822 | -0.012 | [-0.390, +0.307] |
| domain=D5c [diagnostic, pooled] | 40 | 0.513 | 0.558 | -0.045 | [-0.257, +0.166] |
| domain=D8 [diagnostic, pooled] | 40 | 0.565 | 0.620 | -0.055 | [-0.229, +0.127] |
| tool_used=True [diagnostic, macro] | 442 | 0.676 | 0.755 | -0.078 | [-0.139, -0.020] |
| n_turns>=2 (actually explored) [diagnostic, macro] | 442 | 0.676 | 0.755 | -0.078 | [-0.142, -0.019] |
| domain=D2 [diagnostic, pooled] | 40 | 0.677 | 0.756 | -0.079 | [-0.299, +0.142] |
| direct_margin>=0.30 (confident) [actionable_pre_call, macro] | 480 | 0.679 | 0.760 | -0.081 | [-0.137, -0.025] |
| domain=D9 [diagnostic, pooled] | 40 | 0.598 | 0.704 | -0.106 | [-0.297, +0.074] |
| subspacead_rank in [0.4,0.8) (moderate expert) [actionable_after_expert_score, macro] | 215 | 0.633 | 0.762 | -0.128 | [-0.260, -0.011] |
| subspacead_rank<=0.4 (weak expert) [actionable_after_expert_score, macro] | 177 | 0.535 | 0.695 | -0.160 | [-0.291, -0.018] |
| subspacead_rank>=0.8 (strong expert) [actionable_after_expert_score, macro] | 88 | 0.631 | 0.821 | -0.191 | [-0.576, -0.026] |
| domain=D5 [diagnostic, pooled] | 40 | 0.549 | 0.780 | -0.231 | [-0.421, -0.054] |
| domain=D4 [diagnostic, pooled] | 40 | 0.603 | 0.851 | -0.249 | [-0.400, -0.095] |
| domain=D6 [diagnostic, pooled] | 40 | 0.530 | 0.826 | -0.296 | [-0.483, -0.101] |

## Agent hint (injected into agent_v7 prompt if KEEP)

**When to use tool_reference_profiler:** no documented positive niche on dev. DROPPED.
**Avoid tool_reference_profiler on:** `domain=D6` (Δ=-0.296 on n=40).
