# Tool Card: tool_domain_knowledge

**Verdict:** DROP  
**Overall (dev n=480)**: tool=0.6357  direct=0.7599  Δ=-0.1242  
**Calls**: 250/480 (52.1%)  
**Errors**: 0  
**Multiple testing**: Tested 20 slices at α=0.05 (two-sided); expected false positive niches ≈ 0.50. CI uncorrected for multiple testing — dev-derived hints should be revalidated.  

## Positive niches (n≥10, Δ>0, 95% CI lower > 0)

_None found. Tool has no demonstrated niche on dev._

## Anti-niches (Δ<0, 95% CI upper < 0)

| slice [type, metric] | n | tool AUROC | direct AUROC | Δ | 95% CI |
|---|---|---|---|---|---|
| direct_margin>=0.30 (confident) [actionable_pre_call, macro] | 480 | 0.636 | 0.760 | -0.124 | [-0.185, -0.064] |
| subspacead_rank<=0.4 (weak expert) [actionable_after_expert_score, macro] | 177 | 0.525 | 0.695 | -0.170 | [-0.286, -0.045] |
| tool_used=True [diagnostic, macro] | 250 | 0.550 | 0.755 | -0.205 | [-0.309, -0.102] |
| n_turns>=2 (actually explored) [diagnostic, macro] | 250 | 0.550 | 0.755 | -0.205 | [-0.297, -0.099] |
| domain=D4 [diagnostic, pooled] | 40 | 0.643 | 0.851 | -0.209 | [-0.377, -0.067] |
| subspacead_rank in [0.4,0.8) (moderate expert) [actionable_after_expert_score, macro] | 215 | 0.547 | 0.762 | -0.215 | [-0.339, -0.075] |
| domain=D6 [diagnostic, pooled] | 40 | 0.526 | 0.826 | -0.300 | [-0.477, -0.145] |
| domain=D5 [diagnostic, pooled] | 40 | 0.470 | 0.780 | -0.310 | [-0.536, -0.071] |

## All slices (audit)

| slice [type, metric] | n | tool | direct | Δ | 95% CI |
|---|---|---|---|---|---|
| domain=D1 [diagnostic, pooled] | 40 | 0.830 | 0.785 | +0.045 | [-0.094, +0.200] |
| domain=D5b [diagnostic, pooled] | 40 | 0.870 | 0.835 | +0.035 | [-0.060, +0.140] |
| domain=D7 [diagnostic, pooled] | 40 | 0.965 | 0.939 | +0.026 | [-0.041, +0.104] |
| tool_used=False [diagnostic, macro] | 230 | 0.721 | 0.748 | -0.027 | [-0.123, +0.061] |
| n_turns=1 (no tool, tool-offered) [diagnostic, macro] | 230 | 0.721 | 0.748 | -0.027 | [-0.113, +0.065] |
| domain=D10 [diagnostic, pooled] | 40 | 0.643 | 0.695 | -0.052 | [-0.229, +0.137] |
| subspacead_rank>=0.8 (strong expert) [actionable_after_expert_score, macro] | 88 | 0.749 | 0.821 | -0.072 | [-0.301, +0.125] |
| domain=D5c [diagnostic, pooled] | 40 | 0.475 | 0.558 | -0.083 | [-0.304, +0.137] |
| domain=D5d [diagnostic, pooled] | 40 | 0.646 | 0.770 | -0.124 | [-0.340, +0.077] |
| direct_margin>=0.30 (confident) [actionable_pre_call, macro] | 480 | 0.636 | 0.760 | -0.124 | [-0.185, -0.064] |
| domain=D2 [diagnostic, pooled] | 40 | 0.598 | 0.756 | -0.159 | [-0.374, +0.063] |
| subspacead_rank<=0.4 (weak expert) [actionable_after_expert_score, macro] | 177 | 0.525 | 0.695 | -0.170 | [-0.286, -0.045] |
| domain=D8 [diagnostic, pooled] | 40 | 0.444 | 0.620 | -0.176 | [-0.407, +0.069] |
| domain=D9 [diagnostic, pooled] | 40 | 0.520 | 0.704 | -0.184 | [-0.417, +0.047] |
| tool_used=True [diagnostic, macro] | 250 | 0.550 | 0.755 | -0.205 | [-0.309, -0.102] |
| n_turns>=2 (actually explored) [diagnostic, macro] | 250 | 0.550 | 0.755 | -0.205 | [-0.297, -0.099] |
| domain=D4 [diagnostic, pooled] | 40 | 0.643 | 0.851 | -0.209 | [-0.377, -0.067] |
| subspacead_rank in [0.4,0.8) (moderate expert) [actionable_after_expert_score, macro] | 215 | 0.547 | 0.762 | -0.215 | [-0.339, -0.075] |
| domain=D6 [diagnostic, pooled] | 40 | 0.526 | 0.826 | -0.300 | [-0.477, -0.145] |
| domain=D5 [diagnostic, pooled] | 40 | 0.470 | 0.780 | -0.310 | [-0.536, -0.071] |

## Agent hint (injected into agent_v7 prompt if KEEP)

**When to use tool_domain_knowledge:** no documented positive niche on dev. DROPPED.
**Avoid tool_domain_knowledge on:** `domain=D5` (Δ=-0.310 on n=40).
