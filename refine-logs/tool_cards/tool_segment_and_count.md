# Tool Card: tool_segment_and_count

**Verdict:** DROP  
**Overall (dev n=480)**: tool=0.6763  direct=0.7599  Δ=-0.0836  
**Calls**: 385/480 (80.2%)  
**Errors**: 0  
**Multiple testing**: Tested 20 slices at α=0.05 (two-sided); expected false positive niches ≈ 0.50. CI uncorrected for multiple testing — dev-derived hints should be revalidated.  

## Positive niches (n≥10, Δ>0, 95% CI lower > 0)

_None found. Tool has no demonstrated niche on dev._

## Anti-niches (Δ<0, 95% CI upper < 0)

| slice [type, metric] | n | tool AUROC | direct AUROC | Δ | 95% CI |
|---|---|---|---|---|---|
| direct_margin>=0.30 (confident) [actionable_pre_call, macro] | 480 | 0.676 | 0.760 | -0.084 | [-0.143, -0.023] |
| tool_used=True [diagnostic, macro] | 385 | 0.667 | 0.757 | -0.090 | [-0.159, -0.015] |
| n_turns>=2 (actually explored) [diagnostic, macro] | 385 | 0.667 | 0.757 | -0.090 | [-0.162, -0.021] |
| subspacead_rank in [0.4,0.8) (moderate expert) [actionable_after_expert_score, macro] | 215 | 0.612 | 0.762 | -0.149 | [-0.282, -0.025] |
| domain=D6 [diagnostic, pooled] | 40 | 0.649 | 0.826 | -0.177 | [-0.322, -0.048] |
| domain=D2 [diagnostic, pooled] | 40 | 0.504 | 0.756 | -0.253 | [-0.490, -0.034] |
| domain=D5 [diagnostic, pooled] | 40 | 0.466 | 0.780 | -0.314 | [-0.496, -0.129] |

## All slices (audit)

| slice [type, metric] | n | tool | direct | Δ | 95% CI |
|---|---|---|---|---|---|
| domain=D7 [diagnostic, pooled] | 40 | 0.995 | 0.939 | +0.056 | [-0.004, +0.150] |
| domain=D5b [diagnostic, pooled] | 40 | 0.874 | 0.835 | +0.039 | [-0.084, +0.147] |
| domain=D1 [diagnostic, pooled] | 40 | 0.812 | 0.785 | +0.027 | [-0.109, +0.148] |
| domain=D5c [diagnostic, pooled] | 40 | 0.570 | 0.558 | +0.012 | [-0.192, +0.219] |
| domain=D10 [diagnostic, pooled] | 40 | 0.688 | 0.695 | -0.008 | [-0.169, +0.175] |
| domain=D8 [diagnostic, pooled] | 40 | 0.562 | 0.620 | -0.057 | [-0.280, +0.180] |
| domain=D4 [diagnostic, pooled] | 40 | 0.781 | 0.851 | -0.070 | [-0.210, +0.060] |
| domain=D5d [diagnostic, pooled] | 40 | 0.689 | 0.770 | -0.081 | [-0.244, +0.096] |
| direct_margin>=0.30 (confident) [actionable_pre_call, macro] | 480 | 0.676 | 0.760 | -0.084 | [-0.143, -0.023] |
| tool_used=True [diagnostic, macro] | 385 | 0.667 | 0.757 | -0.090 | [-0.159, -0.015] |
| n_turns>=2 (actually explored) [diagnostic, macro] | 385 | 0.667 | 0.757 | -0.090 | [-0.162, -0.021] |
| tool_used=False [diagnostic, macro] | 95 | 0.629 | 0.734 | -0.105 | [-0.227, +0.035] |
| n_turns=1 (no tool, tool-offered) [diagnostic, macro] | 95 | 0.629 | 0.734 | -0.105 | [-0.226, +0.050] |
| subspacead_rank<=0.4 (weak expert) [actionable_after_expert_score, macro] | 177 | 0.585 | 0.695 | -0.110 | [-0.229, +0.006] |
| subspacead_rank>=0.8 (strong expert) [actionable_after_expert_score, macro] | 88 | 0.704 | 0.821 | -0.117 | [-0.488, +0.055] |
| subspacead_rank in [0.4,0.8) (moderate expert) [actionable_after_expert_score, macro] | 215 | 0.612 | 0.762 | -0.149 | [-0.282, -0.025] |
| domain=D6 [diagnostic, pooled] | 40 | 0.649 | 0.826 | -0.177 | [-0.322, -0.048] |
| domain=D9 [diagnostic, pooled] | 40 | 0.525 | 0.704 | -0.179 | [-0.438, +0.108] |
| domain=D2 [diagnostic, pooled] | 40 | 0.504 | 0.756 | -0.253 | [-0.490, -0.034] |
| domain=D5 [diagnostic, pooled] | 40 | 0.466 | 0.780 | -0.314 | [-0.496, -0.129] |

## Agent hint (injected into agent_v7 prompt if KEEP)

**When to use tool_segment_and_count:** no documented positive niche on dev. DROPPED.
**Avoid tool_segment_and_count on:** `domain=D5` (Δ=-0.314 on n=40).
