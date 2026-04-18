# Tool Card: tool_patch_grid

**Verdict:** DROP  
**Overall (dev n=480)**: tool=0.6999  direct=0.7599  Δ=-0.0600  
**Calls**: 310/480 (64.6%)  
**Errors**: 95  
**Multiple testing**: Tested 20 slices at α=0.05 (two-sided); expected false positive niches ≈ 0.50. CI uncorrected for multiple testing — dev-derived hints should be revalidated.  

## Positive niches (n≥10, Δ>0, 95% CI lower > 0)

_None found. Tool has no demonstrated niche on dev._

## Anti-niches (Δ<0, 95% CI upper < 0)

| slice [type, metric] | n | tool AUROC | direct AUROC | Δ | 95% CI |
|---|---|---|---|---|---|
| direct_margin>=0.30 (confident) [actionable_pre_call, macro] | 480 | 0.700 | 0.760 | -0.060 | [-0.115, -0.009] |
| subspacead_rank in [0.4,0.8) (moderate expert) [actionable_after_expert_score, macro] | 215 | 0.645 | 0.762 | -0.116 | [-0.235, -0.003] |
| subspacead_rank<=0.4 (weak expert) [actionable_after_expert_score, macro] | 177 | 0.555 | 0.695 | -0.141 | [-0.253, -0.013] |
| tool_used=True [diagnostic, macro] | 310 | 0.628 | 0.772 | -0.144 | [-0.230, -0.063] |
| n_turns>=2 (actually explored) [diagnostic, macro] | 310 | 0.628 | 0.772 | -0.144 | [-0.224, -0.062] |
| domain=D6 [diagnostic, pooled] | 40 | 0.508 | 0.826 | -0.319 | [-0.482, -0.167] |
| domain=D5 [diagnostic, pooled] | 40 | 0.448 | 0.780 | -0.333 | [-0.543, -0.101] |

## All slices (audit)

| slice [type, metric] | n | tool | direct | Δ | 95% CI |
|---|---|---|---|---|---|
| domain=D10 [diagnostic, pooled] | 40 | 0.816 | 0.695 | +0.121 | [-0.016, +0.275] |
| domain=D5c [diagnostic, pooled] | 40 | 0.633 | 0.558 | +0.075 | [-0.154, +0.293] |
| domain=D1 [diagnostic, pooled] | 40 | 0.855 | 0.785 | +0.070 | [-0.070, +0.204] |
| domain=D7 [diagnostic, pooled] | 40 | 0.996 | 0.939 | +0.057 | [+0.000, +0.141] |
| tool_used=False [diagnostic, macro] | 170 | 0.790 | 0.755 | +0.034 | [-0.113, +0.102] |
| n_turns=1 (no tool, tool-offered) [diagnostic, macro] | 170 | 0.790 | 0.755 | +0.034 | [-0.112, +0.099] |
| domain=D5b [diagnostic, pooled] | 40 | 0.845 | 0.835 | +0.010 | [-0.125, +0.142] |
| domain=D8 [diagnostic, pooled] | 40 | 0.588 | 0.620 | -0.032 | [-0.212, +0.150] |
| direct_margin>=0.30 (confident) [actionable_pre_call, macro] | 480 | 0.700 | 0.760 | -0.060 | [-0.115, -0.009] |
| domain=D5d [diagnostic, pooled] | 40 | 0.706 | 0.770 | -0.064 | [-0.228, +0.099] |
| domain=D9 [diagnostic, pooled] | 40 | 0.626 | 0.704 | -0.078 | [-0.336, +0.173] |
| domain=D2 [diagnostic, pooled] | 40 | 0.643 | 0.756 | -0.114 | [-0.322, +0.074] |
| domain=D4 [diagnostic, pooled] | 40 | 0.736 | 0.851 | -0.115 | [-0.266, +0.015] |
| subspacead_rank in [0.4,0.8) (moderate expert) [actionable_after_expert_score, macro] | 215 | 0.645 | 0.762 | -0.116 | [-0.235, -0.003] |
| subspacead_rank>=0.8 (strong expert) [actionable_after_expert_score, macro] | 88 | 0.688 | 0.821 | -0.134 | [-0.443, +0.058] |
| subspacead_rank<=0.4 (weak expert) [actionable_after_expert_score, macro] | 177 | 0.555 | 0.695 | -0.141 | [-0.253, -0.013] |
| tool_used=True [diagnostic, macro] | 310 | 0.628 | 0.772 | -0.144 | [-0.230, -0.063] |
| n_turns>=2 (actually explored) [diagnostic, macro] | 310 | 0.628 | 0.772 | -0.144 | [-0.224, -0.062] |
| domain=D6 [diagnostic, pooled] | 40 | 0.508 | 0.826 | -0.319 | [-0.482, -0.167] |
| domain=D5 [diagnostic, pooled] | 40 | 0.448 | 0.780 | -0.333 | [-0.543, -0.101] |

## Agent hint (injected into agent_v7 prompt if KEEP)

**When to use tool_patch_grid:** no documented positive niche on dev. DROPPED.
**Avoid tool_patch_grid on:** `domain=D5` (Δ=-0.333 on n=40).
