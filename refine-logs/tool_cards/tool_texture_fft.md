# Tool Card: tool_texture_fft

**Verdict:** DROP  
**Overall (dev n=280)**: tool=0.6961  direct=0.7939  Δ=-0.0979  
**Calls**: 185/280 (66.1%)  
**Errors**: 0  
**Multiple testing**: Tested 15 slices at α=0.05 (two-sided); expected false positive niches ≈ 0.38. CI uncorrected for multiple testing — dev-derived hints should be revalidated.  

## Positive niches (n≥10, Δ>0, 95% CI lower > 0)

_None found. Tool has no demonstrated niche on dev._

## Anti-niches (Δ<0, 95% CI upper < 0)

| slice [type, metric] | n | tool AUROC | direct AUROC | Δ | 95% CI |
|---|---|---|---|---|---|
| direct_margin>=0.30 (confident) [actionable_pre_call, macro] | 280 | 0.696 | 0.794 | -0.098 | [-0.167, -0.027] |
| tool_used=True [diagnostic, macro] | 185 | 0.627 | 0.751 | -0.125 | [-0.224, -0.033] |
| n_turns>=2 (actually explored) [diagnostic, macro] | 185 | 0.627 | 0.751 | -0.125 | [-0.221, -0.040] |
| subspacead_rank in [0.4,0.8) (moderate expert) [actionable_after_expert_score, macro] | 146 | 0.674 | 0.849 | -0.175 | [-0.303, -0.061] |
| domain=D6 [diagnostic, pooled] | 40 | 0.600 | 0.826 | -0.226 | [-0.400, -0.068] |
| domain=D5 [diagnostic, pooled] | 40 | 0.441 | 0.780 | -0.339 | [-0.535, -0.146] |

## All slices (audit)

| slice [type, metric] | n | tool | direct | Δ | 95% CI |
|---|---|---|---|---|---|
| tool_used=False [diagnostic, macro] | 95 | 0.899 | 0.872 | +0.028 | [-0.080, +0.145] |
| n_turns=1 (no tool, tool-offered) [diagnostic, macro] | 95 | 0.899 | 0.872 | +0.028 | [-0.083, +0.150] |
| domain=D7 [diagnostic, pooled] | 40 | 0.960 | 0.939 | +0.021 | [-0.077, +0.116] |
| domain=D8 [diagnostic, pooled] | 40 | 0.637 | 0.620 | +0.017 | [-0.135, +0.160] |
| domain=D1 [diagnostic, pooled] | 40 | 0.784 | 0.785 | -0.001 | [-0.156, +0.142] |
| domain=D4 [diagnostic, pooled] | 40 | 0.814 | 0.851 | -0.037 | [-0.149, +0.066] |
| direct_margin>=0.30 (confident) [actionable_pre_call, macro] | 280 | 0.696 | 0.794 | -0.098 | [-0.167, -0.027] |
| subspacead_rank<=0.4 (weak expert) [actionable_after_expert_score, macro] | 93 | 0.563 | 0.682 | -0.120 | [-0.279, +0.059] |
| domain=D2 [diagnostic, pooled] | 40 | 0.636 | 0.756 | -0.120 | [-0.301, +0.070] |
| tool_used=True [diagnostic, macro] | 185 | 0.627 | 0.751 | -0.125 | [-0.224, -0.033] |
| n_turns>=2 (actually explored) [diagnostic, macro] | 185 | 0.627 | 0.751 | -0.125 | [-0.221, -0.040] |
| subspacead_rank in [0.4,0.8) (moderate expert) [actionable_after_expert_score, macro] | 146 | 0.674 | 0.849 | -0.175 | [-0.303, -0.061] |
| domain=D6 [diagnostic, pooled] | 40 | 0.600 | 0.826 | -0.226 | [-0.400, -0.068] |
| subspacead_rank>=0.8 (strong expert) [actionable_after_expert_score, macro] | 41 | 0.547 | 0.859 | -0.312 | [-0.700, +0.172] |
| domain=D5 [diagnostic, pooled] | 40 | 0.441 | 0.780 | -0.339 | [-0.535, -0.146] |

## Agent hint (injected into agent_v7 prompt if KEEP)

**When to use tool_texture_fft:** no documented positive niche on dev. DROPPED.
**Avoid tool_texture_fft on:** `domain=D5` (Δ=-0.339 on n=40).
