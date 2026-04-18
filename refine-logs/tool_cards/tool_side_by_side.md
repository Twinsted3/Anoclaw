# Tool Card: tool_side_by_side

**Verdict:** DROP  
**Overall (dev n=480)**: tool=0.6697  direct=0.7599  Δ=-0.0902  
**Calls**: 374/480 (77.9%)  
**Errors**: 0  
**Multiple testing**: Tested 20 slices at α=0.05 (two-sided); expected false positive niches ≈ 0.50. CI uncorrected for multiple testing — dev-derived hints should be revalidated.  

## Positive niches (n≥10, Δ>0, 95% CI lower > 0)

_None found. Tool has no demonstrated niche on dev._

## Anti-niches (Δ<0, 95% CI upper < 0)

| slice [type, metric] | n | tool AUROC | direct AUROC | Δ | 95% CI |
|---|---|---|---|---|---|
| direct_margin>=0.30 (confident) [actionable_pre_call, macro] | 480 | 0.670 | 0.760 | -0.090 | [-0.150, -0.032] |
| tool_used=True [diagnostic, macro] | 374 | 0.643 | 0.762 | -0.120 | [-0.195, -0.039] |
| n_turns>=2 (actually explored) [diagnostic, macro] | 374 | 0.643 | 0.762 | -0.120 | [-0.192, -0.046] |
| subspacead_rank in [0.4,0.8) (moderate expert) [actionable_after_expert_score, macro] | 215 | 0.582 | 0.762 | -0.180 | [-0.303, -0.060] |
| domain=D6 [diagnostic, pooled] | 40 | 0.550 | 0.826 | -0.276 | [-0.444, -0.106] |
| domain=D5 [diagnostic, pooled] | 40 | 0.468 | 0.780 | -0.312 | [-0.548, -0.056] |

## All slices (audit)

| slice [type, metric] | n | tool | direct | Δ | 95% CI |
|---|---|---|---|---|---|
| domain=D1 [diagnostic, pooled] | 40 | 0.862 | 0.785 | +0.077 | [-0.064, +0.220] |
| tool_used=False [diagnostic, macro] | 106 | 0.728 | 0.696 | +0.032 | [-0.109, +0.177] |
| n_turns=1 (no tool, tool-offered) [diagnostic, macro] | 106 | 0.728 | 0.696 | +0.032 | [-0.111, +0.183] |
| domain=D7 [diagnostic, pooled] | 40 | 0.970 | 0.939 | +0.031 | [-0.054, +0.124] |
| domain=D8 [diagnostic, pooled] | 40 | 0.619 | 0.620 | -0.001 | [-0.249, +0.252] |
| domain=D5c [diagnostic, pooled] | 40 | 0.549 | 0.558 | -0.009 | [-0.232, +0.215] |
| subspacead_rank<=0.4 (weak expert) [actionable_after_expert_score, macro] | 177 | 0.681 | 0.695 | -0.014 | [-0.131, +0.110] |
| subspacead_rank>=0.8 (strong expert) [actionable_after_expert_score, macro] | 88 | 0.800 | 0.821 | -0.021 | [-0.393, +0.139] |
| domain=D5b [diagnostic, pooled] | 40 | 0.799 | 0.835 | -0.036 | [-0.156, +0.076] |
| domain=D10 [diagnostic, pooled] | 40 | 0.636 | 0.695 | -0.059 | [-0.183, +0.061] |
| direct_margin>=0.30 (confident) [actionable_pre_call, macro] | 480 | 0.670 | 0.760 | -0.090 | [-0.150, -0.032] |
| domain=D9 [diagnostic, pooled] | 40 | 0.610 | 0.704 | -0.094 | [-0.290, +0.120] |
| domain=D4 [diagnostic, pooled] | 40 | 0.739 | 0.851 | -0.112 | [-0.302, +0.080] |
| tool_used=True [diagnostic, macro] | 374 | 0.643 | 0.762 | -0.120 | [-0.195, -0.039] |
| n_turns>=2 (actually explored) [diagnostic, macro] | 374 | 0.643 | 0.762 | -0.120 | [-0.192, -0.046] |
| domain=D2 [diagnostic, pooled] | 40 | 0.636 | 0.756 | -0.120 | [-0.307, +0.084] |
| domain=D5d [diagnostic, pooled] | 40 | 0.599 | 0.770 | -0.171 | [-0.398, +0.052] |
| subspacead_rank in [0.4,0.8) (moderate expert) [actionable_after_expert_score, macro] | 215 | 0.582 | 0.762 | -0.180 | [-0.303, -0.060] |
| domain=D6 [diagnostic, pooled] | 40 | 0.550 | 0.826 | -0.276 | [-0.444, -0.106] |
| domain=D5 [diagnostic, pooled] | 40 | 0.468 | 0.780 | -0.312 | [-0.548, -0.056] |

## Agent hint (injected into agent_v7 prompt if KEEP)

**When to use tool_side_by_side:** no documented positive niche on dev. DROPPED.
**Avoid tool_side_by_side on:** `domain=D5` (Δ=-0.312 on n=40).
