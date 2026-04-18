# Tool Card: tool_expert_score

**Verdict:** DROP  
**Overall (dev n=480)**: tool=0.7026  direct=0.7599  Δ=-0.0573  
**Calls**: 402/480 (83.8%)  
**Errors**: 0  
**Multiple testing**: Tested 20 slices at α=0.05 (two-sided); expected false positive niches ≈ 0.50. CI uncorrected for multiple testing — dev-derived hints should be revalidated.  

## Positive niches (n≥10, Δ>0, 95% CI lower > 0)

_None found. Tool has no demonstrated niche on dev._

## Anti-niches (Δ<0, 95% CI upper < 0)

| slice [type, metric] | n | tool AUROC | direct AUROC | Δ | 95% CI |
|---|---|---|---|---|---|
| tool_used=True [diagnostic, macro] | 402 | 0.681 | 0.763 | -0.082 | [-0.147, -0.017] |
| n_turns>=2 (actually explored) [diagnostic, macro] | 402 | 0.681 | 0.763 | -0.082 | [-0.149, -0.016] |
| subspacead_rank in [0.4,0.8) (moderate expert) [actionable_after_expert_score, macro] | 215 | 0.593 | 0.762 | -0.168 | [-0.301, -0.045] |
| domain=D6 [diagnostic, pooled] | 40 | 0.590 | 0.826 | -0.236 | [-0.426, -0.069] |

## All slices (audit)

| slice [type, metric] | n | tool | direct | Δ | 95% CI |
|---|---|---|---|---|---|
| domain=D10 [diagnostic, pooled] | 40 | 0.810 | 0.695 | +0.115 | [-0.051, +0.289] |
| domain=D7 [diagnostic, pooled] | 40 | 1.000 | 0.939 | +0.061 | [+0.000, +0.151] |
| domain=D1 [diagnostic, pooled] | 40 | 0.814 | 0.785 | +0.029 | [-0.133, +0.182] |
| domain=D5c [diagnostic, pooled] | 40 | 0.586 | 0.558 | +0.029 | [-0.163, +0.212] |
| subspacead_rank>=0.8 (strong expert) [actionable_after_expert_score, macro] | 88 | 0.824 | 0.821 | +0.003 | [-0.409, +0.164] |
| domain=D4 [diagnostic, pooled] | 40 | 0.816 | 0.851 | -0.035 | [-0.175, +0.082] |
| direct_margin>=0.30 (confident) [actionable_pre_call, macro] | 480 | 0.703 | 0.760 | -0.057 | [-0.114, +0.002] |
| domain=D2 [diagnostic, pooled] | 40 | 0.696 | 0.756 | -0.060 | [-0.289, +0.161] |
| domain=D5d [diagnostic, pooled] | 40 | 0.696 | 0.770 | -0.074 | [-0.258, +0.120] |
| tool_used=True [diagnostic, macro] | 402 | 0.681 | 0.763 | -0.082 | [-0.147, -0.017] |
| n_turns>=2 (actually explored) [diagnostic, macro] | 402 | 0.681 | 0.763 | -0.082 | [-0.149, -0.016] |
| domain=D9 [diagnostic, pooled] | 40 | 0.620 | 0.704 | -0.084 | [-0.297, +0.161] |
| subspacead_rank<=0.4 (weak expert) [actionable_after_expert_score, macro] | 177 | 0.610 | 0.695 | -0.085 | [-0.195, +0.020] |
| domain=D5b [diagnostic, pooled] | 40 | 0.749 | 0.835 | -0.086 | [-0.230, +0.045] |
| tool_used=False [diagnostic, macro] | 78 | 0.706 | 0.825 | -0.119 | [-0.262, +0.187] |
| n_turns=1 (no tool, tool-offered) [diagnostic, macro] | 78 | 0.706 | 0.825 | -0.119 | [-0.257, +0.183] |
| subspacead_rank in [0.4,0.8) (moderate expert) [actionable_after_expert_score, macro] | 215 | 0.593 | 0.762 | -0.168 | [-0.301, -0.045] |
| domain=D8 [diagnostic, pooled] | 40 | 0.449 | 0.620 | -0.171 | [-0.380, +0.037] |
| domain=D5 [diagnostic, pooled] | 40 | 0.605 | 0.780 | -0.175 | [-0.352, +0.003] |
| domain=D6 [diagnostic, pooled] | 40 | 0.590 | 0.826 | -0.236 | [-0.426, -0.069] |

## Agent hint (injected into agent_v7 prompt if KEEP)

**When to use tool_expert_score:** no documented positive niche on dev. DROPPED.
**Avoid tool_expert_score on:** `domain=D6` (Δ=-0.236 on n=40).
