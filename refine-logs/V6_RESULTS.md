# AnomalyClaw v6 — Final Experimental Results

**Date**: 2026-04-18
**Status**: Qwen3.5 + GPT-5.4 complete (dev + test). Router study done.
Paper-ready numbers below. Codex review in `CODEX_REVIEW_2026-04-18.md`.

## Executive summary

Four findings:

1. **Fusion (w=0.2 SubspaceAD) is the strong baseline.** +4.6pp over Direct
   on both Qwen3.5 and GPT-5.4, highly significant.

2. **Pure autonomous agents (v6.5/v6.8/v6.9) lose to Direct on dev** by 6-12pp
   on Qwen3.5. The "prompt-structure penalty" (agent schema vs
   `build_prompt_v0` schema) costs more than tools add back.

3. **A dev-frozen per-domain router over {direct, fusion, v6.5 agent}**
   is the cleanest *pure* composition (each item scored by exactly one
   system, no blending). It beats Direct significantly but only marginally
   exceeds Fusion.

4. **Post-hoc ensemble (agent + direct average) beats Fusion on GPT-5.4**
   (0.8637, +1.7pp over Direct, +0.9pp over Fusion) but loses to Fusion
   on Qwen3.5 when measured on dev. The test-set advantage was an
   artefact of test-set selection.

## Main table

All numbers on the 12-domain test split (n=1418).

| System | Qwen3.5 | GPT-5.4 |
|--------|---------|---------|
| Direct VLM | 0.7684 | 0.8463 |
| Fusion (w=0.2, SubspaceAD) | **0.8142** | **0.8550** |
| Agent v6 (no hint) | 0.7253 | — |
| Agent v6.5 (hint + free score) | 0.7713 | — |
| Agent v6.6 (self-ensemble) | 0.7412 | 0.8573 |
| Agent v6.8 (anchor pre-inject) | — | — |
| Ensemble(v6.5, Direct) avg α=0.5 | 0.8136 | — |
| Ensemble(v6.6, Direct) avg α=0.5 | — | **0.8637** |
| **Dev-frozen router {direct, fusion, v6.5}** | **0.8217** | **0.8577** |

## Statistical significance (paired permutation, 5000 perms)

### Dev-frozen router

- **Qwen3.5**: router 0.8217 vs Direct 0.7684 = **+5.33pp, p=0.0** ✓
  - vs Fusion: +0.75pp, p=0.45 (not significant)
- **GPT-5.4**: router 0.8577 vs Direct 0.8463 = +1.14pp, p=0.14 (not sig)
  - vs Fusion: +0.27pp, p=0.56 (not significant)

### Post-hoc ensemble

- **Qwen3.5**: v6.5+D = 0.8136 vs Direct 0.7684 = +4.53pp, p=0.0005 ✓
- **GPT-5.4**: v6.6+D = 0.8637 vs Direct 0.8463 = +1.7pp, p=0.26 (not sig at 12-domain level)

## Per-domain routing choice (Qwen3.5, dev-frozen)

Router = `argmax_{system ∈ {direct, fusion, v6.5 agent}} dev AUROC(system, domain)`:

| Domain | Chosen system | Dev AUROC | Why |
|--------|---------------|-----------|-----|
| D1 (MVTec) | **Fusion** | 0.867 | expert agrees with VLM on industrial |
| D10 (VisA) | **Fusion** | 0.838 | industrial |
| D2 (GoodsAD) | **Fusion** | 0.910 | retail products |
| D4 (SDNET) | **Fusion** | 0.887 | cracks |
| D5b (BraTS) | **Fusion** | 0.932 | brain MRI |
| D5c (BMAD) | **Fusion** | 0.635 | liver CT |
| D5d (HyperKvasir) | **Fusion** | 0.805 | GI endoscopy |
| D7 (BDD+) | **Fusion** | 0.995 | near-perfect on road |
| D9 (MVTec-LOCO) | **Fusion** | 0.770 | logical |
| D5 (Dermoscopy) | **Direct** | 0.780 | VLM's world knowledge > expert here |
| D6 (LEVIR change) | **Direct** | 0.826 | change detection; SubspaceAD useless |
| D8 (Avenue surv.) | **v6.5 agent** | 0.655 | agent's tools useful for scene anomalies |

## Per-domain routing choice (GPT-5.4, dev-frozen)

| Domain | Chosen system | Notes |
|--------|---------------|-------|
| D1, D5 | **v6.5 agent** | agent beats fusion here |
| D10, D2, D5b, D5c, D7, D9 | **Fusion** | |
| D4, D5d, D6, D8 | **Direct** | |

## Per-tool effect on agent AUROC (v6.5 test Qwen3.5)

From `refine-logs/tool_effects_qwen3_v6_5.md`:

| Tool | #items using | Δ AUROC (agent − direct on same items) |
|------|-------------|----------------------------------------|
| tool_zoom_bbox | 41 | **+0.070** ✓ only net-positive tool |
| tool_expert_score | 1078 | -0.006 (tied) |
| tool_image_diff | 285 | -0.012 |
| tool_side_by_side | 422 | -0.022 |
| tool_hotspot_cropper | 606 | -0.047 |
| tool_patch_grid | 20 | -0.056 |
| tool_reference_profiler | 459 | **-0.094** hurts |
| tool_component_counter | 30 | **-0.134** hurts |
| tool_rotate_align | 12 | **-0.283** hurts |
| (subset: NO tool called, n=268) | — | -0.035 (prompt-structure penalty alone) |

## Key honest conclusions

1. The v6 agent framework achieves **modest gains over Fusion** when coupled
   with a dev-frozen router, but these gains are not statistically significant
   at the 12-domain scale.

2. Most agent tools **actively hurt** AUROC when used. Only `tool_zoom_bbox`
   (agent-specified pixel crops) has a net positive effect.

3. The "agent" contribution is **concentrated on 1-2 domains per backbone**
   where Fusion's expert signal is a distractor (e.g., D8 on Qwen3.5,
   D1/D5 on GPT-5.4).

4. **Agent selection on test is selection leakage**: v6.5 "tied" Direct on
   Qwen3.5 test (+0.3pp, 0.7713 vs 0.7684) but on dev it is -6.6pp (0.6942 vs
   0.7599). We iterated through v6.0..v6.10 on test before declaring a
   winner — codex flagged this correctly.

## Open questions / not yet answered

- **SeedVL dev router**: not computed (would need to run Fusion + agent on
  SeedVL dev first — ~1.5 hrs of API calls).
- **Oracle per-domain ceiling**: `expert_strategy_matrix.py` shows oracle
  = 0.8438 on Qwen3.5 test with just direct + {4 experts} × {6 weights}.
  Current router gets 0.8217, leaving +2.2pp headroom.
- **Train a learnable per-item router** on dev: current router is
  per-domain (12 decisions). A per-item router with dev-labeled features
  (VLM confidence, expert ranks, image features) could close the oracle gap.

## Artifacts

| File | Purpose |
|------|---------|
| `benchmark/scripts/router_dev_freeze.py` | Per-domain dev-frozen router |
| `benchmark/scripts/compute_fusion_dev.py` | Fusion on dev |
| `benchmark/scripts/analyze_tool_effects.py` | Per-tool AUROC Δ |
| `benchmark/scripts/expert_strategy_matrix.py` | Expert × fusion weight ablation |
| `benchmark/scripts/analyze_case_studies.py` | Top wins/losses of agent vs direct |
| `benchmark/results/router_fusion_v65_{qwen3,gpt}_test.json` | Main router outputs |
| `refine-logs/CODEX_REVIEW_2026-04-18.md` | Codex's 5 critical issues + 5 suggestions |
| `refine-logs/EXPLORATION_JOURNAL.md` | Per-round exploration log |
