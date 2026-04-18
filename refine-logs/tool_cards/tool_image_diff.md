# Tool Card: tool_image_diff

**Verdict:** DROP  
**Overall (dev n=480)**: tool=0.6791  direct=0.7599  Δ=-0.0808  
**Calls**: 269/480 (56.0%)  
**Errors**: 0  
**Multiple testing**: Tested 20 slices at α=0.05 (two-sided); expected false positive niches ≈ 0.50. CI uncorrected for multiple testing — dev-derived hints should be revalidated.  

## Positive niches (n≥10, Δ>0, 95% CI lower > 0)

_None found. Tool has no demonstrated niche on dev._

## Anti-niches (Δ<0, 95% CI upper < 0)

| slice [type, metric] | n | tool AUROC | direct AUROC | Δ | 95% CI |
|---|---|---|---|---|---|
| direct_margin>=0.30 (confident) [actionable_pre_call, macro] | 480 | 0.679 | 0.760 | -0.081 | [-0.134, -0.025] |
| tool_used=True [diagnostic, macro] | 269 | 0.611 | 0.746 | -0.134 | [-0.223, -0.049] |
| n_turns>=2 (actually explored) [diagnostic, macro] | 269 | 0.611 | 0.746 | -0.134 | [-0.228, -0.038] |
| subspacead_rank in [0.4,0.8) (moderate expert) [actionable_after_expert_score, macro] | 215 | 0.579 | 0.762 | -0.182 | [-0.305, -0.046] |
| subspacead_rank>=0.8 (strong expert) [actionable_after_expert_score, macro] | 88 | 0.584 | 0.821 | -0.237 | [-0.599, -0.028] |
| domain=D2 [diagnostic, pooled] | 40 | 0.469 | 0.756 | -0.288 | [-0.501, -0.071] |
| domain=D6 [diagnostic, pooled] | 40 | 0.439 | 0.826 | -0.387 | [-0.571, -0.213] |

## All slices (audit)

| slice [type, metric] | n | tool | direct | Δ | 95% CI |
|---|---|---|---|---|---|
| domain=D1 [diagnostic, pooled] | 40 | 0.852 | 0.785 | +0.067 | [-0.100, +0.240] |
| domain=D7 [diagnostic, pooled] | 40 | 1.000 | 0.939 | +0.061 | [+0.000, +0.152] |
| domain=D5b [diagnostic, pooled] | 40 | 0.871 | 0.835 | +0.036 | [-0.087, +0.145] |
| domain=D10 [diagnostic, pooled] | 40 | 0.730 | 0.695 | +0.035 | [-0.096, +0.168] |
| domain=D9 [diagnostic, pooled] | 40 | 0.694 | 0.704 | -0.010 | [-0.235, +0.239] |
| domain=D5c [diagnostic, pooled] | 40 | 0.528 | 0.558 | -0.030 | [-0.225, +0.160] |
| domain=D5d [diagnostic, pooled] | 40 | 0.733 | 0.770 | -0.037 | [-0.217, +0.141] |
| subspacead_rank<=0.4 (weak expert) [actionable_after_expert_score, macro] | 177 | 0.651 | 0.695 | -0.044 | [-0.162, +0.074] |
| tool_used=False [diagnostic, macro] | 211 | 0.703 | 0.753 | -0.050 | [-0.134, +0.064] |
| n_turns=1 (no tool, tool-offered) [diagnostic, macro] | 211 | 0.703 | 0.753 | -0.050 | [-0.143, +0.065] |
| direct_margin>=0.30 (confident) [actionable_pre_call, macro] | 480 | 0.679 | 0.760 | -0.081 | [-0.134, -0.025] |
| domain=D5 [diagnostic, pooled] | 40 | 0.647 | 0.780 | -0.133 | [-0.325, +0.050] |
| tool_used=True [diagnostic, macro] | 269 | 0.611 | 0.746 | -0.134 | [-0.223, -0.049] |
| n_turns>=2 (actually explored) [diagnostic, macro] | 269 | 0.611 | 0.746 | -0.134 | [-0.228, -0.038] |
| domain=D8 [diagnostic, pooled] | 40 | 0.479 | 0.620 | -0.141 | [-0.345, +0.067] |
| domain=D4 [diagnostic, pooled] | 40 | 0.708 | 0.851 | -0.144 | [-0.338, +0.044] |
| subspacead_rank in [0.4,0.8) (moderate expert) [actionable_after_expert_score, macro] | 215 | 0.579 | 0.762 | -0.182 | [-0.305, -0.046] |
| subspacead_rank>=0.8 (strong expert) [actionable_after_expert_score, macro] | 88 | 0.584 | 0.821 | -0.237 | [-0.599, -0.028] |
| domain=D2 [diagnostic, pooled] | 40 | 0.469 | 0.756 | -0.288 | [-0.501, -0.071] |
| domain=D6 [diagnostic, pooled] | 40 | 0.439 | 0.826 | -0.387 | [-0.571, -0.213] |

## Agent hint (injected into agent_v7 prompt if KEEP)

**When to use tool_image_diff:** no documented positive niche on dev. DROPPED.
**Avoid tool_image_diff on:** `domain=D6` (Δ=-0.387 on n=40).
