# Tool Card: tool_rotate_align

**Verdict:** DROP  
**Overall (dev n=480)**: tool=0.6866  direct=0.7599  Δ=-0.0733  
**Calls**: 254/480 (52.9%)  
**Errors**: 0  
**Multiple testing**: Tested 20 slices at α=0.05 (two-sided); expected false positive niches ≈ 0.50. CI uncorrected for multiple testing — dev-derived hints should be revalidated.  

## Positive niches (n≥10, Δ>0, 95% CI lower > 0)

_None found. Tool has no demonstrated niche on dev._

## Anti-niches (Δ<0, 95% CI upper < 0)

| slice [type, metric] | n | tool AUROC | direct AUROC | Δ | 95% CI |
|---|---|---|---|---|---|
| direct_margin>=0.30 (confident) [actionable_pre_call, macro] | 480 | 0.687 | 0.760 | -0.073 | [-0.131, -0.014] |
| tool_used=True [diagnostic, macro] | 254 | 0.594 | 0.734 | -0.140 | [-0.239, -0.051] |
| n_turns>=2 (actually explored) [diagnostic, macro] | 254 | 0.594 | 0.734 | -0.140 | [-0.231, -0.050] |
| domain=D6 [diagnostic, pooled] | 40 | 0.598 | 0.826 | -0.229 | [-0.373, -0.082] |
| domain=D5 [diagnostic, pooled] | 40 | 0.539 | 0.780 | -0.241 | [-0.430, -0.022] |
| domain=D2 [diagnostic, pooled] | 40 | 0.432 | 0.756 | -0.324 | [-0.529, -0.121] |

## All slices (audit)

| slice [type, metric] | n | tool | direct | Δ | 95% CI |
|---|---|---|---|---|---|
| domain=D1 [diagnostic, pooled] | 40 | 0.879 | 0.785 | +0.094 | [-0.029, +0.230] |
| domain=D5b [diagnostic, pooled] | 40 | 0.914 | 0.835 | +0.079 | [-0.009, +0.180] |
| domain=D7 [diagnostic, pooled] | 40 | 0.995 | 0.939 | +0.056 | [-0.005, +0.146] |
| domain=D8 [diagnostic, pooled] | 40 | 0.602 | 0.620 | -0.018 | [-0.231, +0.178] |
| domain=D10 [diagnostic, pooled] | 40 | 0.664 | 0.695 | -0.031 | [-0.202, +0.147] |
| domain=D5d [diagnostic, pooled] | 40 | 0.732 | 0.770 | -0.037 | [-0.203, +0.127] |
| domain=D5c [diagnostic, pooled] | 40 | 0.520 | 0.558 | -0.038 | [-0.248, +0.153] |
| domain=D4 [diagnostic, pooled] | 40 | 0.809 | 0.851 | -0.043 | [-0.207, +0.120] |
| tool_used=False [diagnostic, macro] | 226 | 0.680 | 0.732 | -0.052 | [-0.165, +0.043] |
| n_turns=1 (no tool, tool-offered) [diagnostic, macro] | 226 | 0.680 | 0.732 | -0.052 | [-0.159, +0.044] |
| direct_margin>=0.30 (confident) [actionable_pre_call, macro] | 480 | 0.687 | 0.760 | -0.073 | [-0.131, -0.014] |
| subspacead_rank<=0.4 (weak expert) [actionable_after_expert_score, macro] | 177 | 0.587 | 0.695 | -0.108 | [-0.240, +0.014] |
| subspacead_rank in [0.4,0.8) (moderate expert) [actionable_after_expert_score, macro] | 215 | 0.633 | 0.762 | -0.128 | [-0.247, +0.007] |
| tool_used=True [diagnostic, macro] | 254 | 0.594 | 0.734 | -0.140 | [-0.239, -0.051] |
| n_turns>=2 (actually explored) [diagnostic, macro] | 254 | 0.594 | 0.734 | -0.140 | [-0.231, -0.050] |
| subspacead_rank>=0.8 (strong expert) [actionable_after_expert_score, macro] | 88 | 0.676 | 0.821 | -0.145 | [-0.440, +0.030] |
| domain=D9 [diagnostic, pooled] | 40 | 0.555 | 0.704 | -0.149 | [-0.376, +0.069] |
| domain=D6 [diagnostic, pooled] | 40 | 0.598 | 0.826 | -0.229 | [-0.373, -0.082] |
| domain=D5 [diagnostic, pooled] | 40 | 0.539 | 0.780 | -0.241 | [-0.430, -0.022] |
| domain=D2 [diagnostic, pooled] | 40 | 0.432 | 0.756 | -0.324 | [-0.529, -0.121] |

## Agent hint (injected into agent_v7 prompt if KEEP)

**When to use tool_rotate_align:** no documented positive niche on dev. DROPPED.
**Avoid tool_rotate_align on:** `domain=D2` (Δ=-0.324 on n=40).
