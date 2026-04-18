# Tool Card: tool_hotspot_cropper

**Verdict:** DROP  
**Overall (dev n=480)**: tool=0.6849  direct=0.7599  Δ=-0.0750  
**Calls**: 64/480 (13.3%)  
**Errors**: 1  
**Multiple testing**: Tested 20 slices at α=0.05 (two-sided); expected false positive niches ≈ 0.50. CI uncorrected for multiple testing — dev-derived hints should be revalidated.  

## Positive niches (n≥10, Δ>0, 95% CI lower > 0)

_None found. Tool has no demonstrated niche on dev._

## Anti-niches (Δ<0, 95% CI upper < 0)

| slice [type, metric] | n | tool AUROC | direct AUROC | Δ | 95% CI |
|---|---|---|---|---|---|
| tool_used=False [diagnostic, macro] | 416 | 0.693 | 0.760 | -0.067 | [-0.131, -0.007] |
| n_turns=1 (no tool, tool-offered) [diagnostic, macro] | 384 | 0.687 | 0.758 | -0.071 | [-0.139, -0.002] |
| direct_margin>=0.30 (confident) [actionable_pre_call, macro] | 480 | 0.685 | 0.760 | -0.075 | [-0.130, -0.021] |
| subspacead_rank in [0.4,0.8) (moderate expert) [actionable_after_expert_score, macro] | 215 | 0.603 | 0.762 | -0.159 | [-0.289, -0.033] |
| domain=D6 [diagnostic, pooled] | 40 | 0.633 | 0.826 | -0.194 | [-0.368, -0.031] |
| domain=D2 [diagnostic, pooled] | 40 | 0.551 | 0.756 | -0.205 | [-0.393, -0.015] |
| domain=D5 [diagnostic, pooled] | 40 | 0.482 | 0.780 | -0.298 | [-0.516, -0.071] |

## All slices (audit)

| slice [type, metric] | n | tool | direct | Δ | 95% CI |
|---|---|---|---|---|---|
| domain=D7 [diagnostic, pooled] | 40 | 0.995 | 0.939 | +0.056 | [+0.000, +0.135] |
| domain=D1 [diagnostic, pooled] | 40 | 0.833 | 0.785 | +0.047 | [-0.065, +0.179] |
| domain=D10 [diagnostic, pooled] | 40 | 0.713 | 0.695 | +0.017 | [-0.148, +0.182] |
| domain=D8 [diagnostic, pooled] | 40 | 0.625 | 0.620 | +0.005 | [-0.203, +0.208] |
| domain=D9 [diagnostic, pooled] | 40 | 0.674 | 0.704 | -0.030 | [-0.287, +0.234] |
| domain=D5c [diagnostic, pooled] | 40 | 0.516 | 0.558 | -0.041 | [-0.242, +0.155] |
| domain=D5b [diagnostic, pooled] | 40 | 0.786 | 0.835 | -0.049 | [-0.198, +0.104] |
| tool_used=False [diagnostic, macro] | 416 | 0.693 | 0.760 | -0.067 | [-0.131, -0.007] |
| subspacead_rank>=0.8 (strong expert) [actionable_after_expert_score, macro] | 88 | 0.752 | 0.821 | -0.069 | [-0.297, +0.116] |
| n_turns=1 (no tool, tool-offered) [diagnostic, macro] | 384 | 0.687 | 0.758 | -0.071 | [-0.139, -0.002] |
| direct_margin>=0.30 (confident) [actionable_pre_call, macro] | 480 | 0.685 | 0.760 | -0.075 | [-0.130, -0.021] |
| subspacead_rank<=0.4 (weak expert) [actionable_after_expert_score, macro] | 177 | 0.614 | 0.695 | -0.081 | [-0.200, +0.035] |
| domain=D4 [diagnostic, pooled] | 40 | 0.752 | 0.851 | -0.099 | [-0.279, +0.069] |
| domain=D5d [diagnostic, pooled] | 40 | 0.659 | 0.770 | -0.111 | [-0.275, +0.074] |
| tool_used=True [diagnostic, macro] | 64 | 0.629 | 0.743 | -0.113 | [-0.247, +0.100] |
| n_turns>=2 (actually explored) [diagnostic, macro] | 96 | 0.656 | 0.810 | -0.154 | [-0.273, +0.014] |
| subspacead_rank in [0.4,0.8) (moderate expert) [actionable_after_expert_score, macro] | 215 | 0.603 | 0.762 | -0.159 | [-0.289, -0.033] |
| domain=D6 [diagnostic, pooled] | 40 | 0.633 | 0.826 | -0.194 | [-0.368, -0.031] |
| domain=D2 [diagnostic, pooled] | 40 | 0.551 | 0.756 | -0.205 | [-0.393, -0.015] |
| domain=D5 [diagnostic, pooled] | 40 | 0.482 | 0.780 | -0.298 | [-0.516, -0.071] |

## Agent hint (injected into agent_v7 prompt if KEEP)

**When to use tool_hotspot_cropper:** no documented positive niche on dev. DROPPED.
**Avoid tool_hotspot_cropper on:** `domain=D5` (Δ=-0.298 on n=40).
