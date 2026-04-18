# Tool Card: tool_reference_retriever

**Verdict:** DROP  
**Overall (dev n=480)**: tool=0.6472  direct=0.7599  Δ=-0.1127  
**Calls**: 223/480 (46.5%)  
**Errors**: 0  
**Multiple testing**: Tested 20 slices at α=0.05 (two-sided); expected false positive niches ≈ 0.50. CI uncorrected for multiple testing — dev-derived hints should be revalidated.  

## Positive niches (n≥10, Δ>0, 95% CI lower > 0)

_None found. Tool has no demonstrated niche on dev._

## Anti-niches (Δ<0, 95% CI upper < 0)

| slice [type, metric] | n | tool AUROC | direct AUROC | Δ | 95% CI |
|---|---|---|---|---|---|
| direct_margin>=0.30 (confident) [actionable_pre_call, macro] | 480 | 0.647 | 0.760 | -0.113 | [-0.173, -0.057] |
| tool_used=False [diagnostic, macro] | 257 | 0.622 | 0.759 | -0.137 | [-0.242, -0.039] |
| n_turns=1 (no tool, tool-offered) [diagnostic, macro] | 257 | 0.622 | 0.759 | -0.137 | [-0.230, -0.046] |
| subspacead_rank<=0.4 (weak expert) [actionable_after_expert_score, macro] | 177 | 0.557 | 0.695 | -0.138 | [-0.251, -0.013] |
| domain=D5b [diagnostic, pooled] | 40 | 0.645 | 0.835 | -0.190 | [-0.337, -0.030] |
| subspacead_rank in [0.4,0.8) (moderate expert) [actionable_after_expert_score, macro] | 215 | 0.543 | 0.762 | -0.219 | [-0.347, -0.091] |
| domain=D6 [diagnostic, pooled] | 40 | 0.561 | 0.826 | -0.265 | [-0.415, -0.111] |
| domain=D2 [diagnostic, pooled] | 40 | 0.491 | 0.756 | -0.265 | [-0.477, -0.061] |

## All slices (audit)

| slice [type, metric] | n | tool | direct | Δ | 95% CI |
|---|---|---|---|---|---|
| domain=D7 [diagnostic, pooled] | 40 | 1.000 | 0.939 | +0.061 | [+0.000, +0.159] |
| domain=D5c [diagnostic, pooled] | 40 | 0.601 | 0.558 | +0.044 | [-0.143, +0.237] |
| domain=D1 [diagnostic, pooled] | 40 | 0.801 | 0.785 | +0.016 | [-0.146, +0.150] |
| subspacead_rank>=0.8 (strong expert) [actionable_after_expert_score, macro] | 88 | 0.812 | 0.821 | -0.009 | [-0.316, +0.170] |
| domain=D8 [diagnostic, pooled] | 40 | 0.586 | 0.620 | -0.034 | [-0.244, +0.190] |
| tool_used=True [diagnostic, macro] | 223 | 0.644 | 0.697 | -0.053 | [-0.175, +0.043] |
| n_turns>=2 (actually explored) [diagnostic, macro] | 223 | 0.644 | 0.697 | -0.053 | [-0.176, +0.036] |
| domain=D10 [diagnostic, pooled] | 40 | 0.609 | 0.695 | -0.086 | [-0.263, +0.116] |
| direct_margin>=0.30 (confident) [actionable_pre_call, macro] | 480 | 0.647 | 0.760 | -0.113 | [-0.173, -0.057] |
| domain=D5 [diagnostic, pooled] | 40 | 0.646 | 0.780 | -0.134 | [-0.338, +0.075] |
| domain=D4 [diagnostic, pooled] | 40 | 0.716 | 0.851 | -0.135 | [-0.310, +0.014] |
| tool_used=False [diagnostic, macro] | 257 | 0.622 | 0.759 | -0.137 | [-0.242, -0.039] |
| n_turns=1 (no tool, tool-offered) [diagnostic, macro] | 257 | 0.622 | 0.759 | -0.137 | [-0.230, -0.046] |
| subspacead_rank<=0.4 (weak expert) [actionable_after_expert_score, macro] | 177 | 0.557 | 0.695 | -0.138 | [-0.251, -0.013] |
| domain=D5d [diagnostic, pooled] | 40 | 0.596 | 0.770 | -0.174 | [-0.380, +0.044] |
| domain=D5b [diagnostic, pooled] | 40 | 0.645 | 0.835 | -0.190 | [-0.337, -0.030] |
| domain=D9 [diagnostic, pooled] | 40 | 0.513 | 0.704 | -0.191 | [-0.439, +0.054] |
| subspacead_rank in [0.4,0.8) (moderate expert) [actionable_after_expert_score, macro] | 215 | 0.543 | 0.762 | -0.219 | [-0.347, -0.091] |
| domain=D6 [diagnostic, pooled] | 40 | 0.561 | 0.826 | -0.265 | [-0.415, -0.111] |
| domain=D2 [diagnostic, pooled] | 40 | 0.491 | 0.756 | -0.265 | [-0.477, -0.061] |

## Agent hint (injected into agent_v7 prompt if KEEP)

**When to use tool_reference_retriever:** no documented positive niche on dev. DROPPED.
**Avoid tool_reference_retriever on:** `domain=D2` (Δ=-0.265 on n=40).
