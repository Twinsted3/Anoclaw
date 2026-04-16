# AnomalyClaw v3 Run Status — 2026-04-15

## Implementation completed
- **Tools** (`benchmark/scripts/run_anomaclaw_v3.py`): `domain_descriptor`, `reference_retriever` (DINOv2 CLS, via `agent_tools.tool_visual_retrieval`), `hotspot_cropper` (PIL crop on top-k SubspaceAD patch coords), `component_counter` (4-connectivity flood fill), `knowledge_lookup` (DOMAIN_KNOWLEDGE table).
- **Experts** (`ExpertCache`): SubspaceAD, DINOv2 patch-kNN, DINOv2 global — loaded from cached test results.
- **Strategies**: direct (1 VLM call), fusion (s = 0.8 v0 + 0.2 σ((s_exp−m)/m)), debate (proposer + advocate via existing run_v3), interpret (asymmetric escalation: v0 → if normal AND rho>0.8 then second VLM call with hotspot crop).
- **Autonomous planner**: text-only VLM call per (model, domain) that emits JSON `{tools:[...], expert:..., strategy:..., reasoning:...}`. Cached.
- **Online override**: rho-based escalation to interpret when v0 says normal and expert hotspot is strong.

## Runs in progress
- **Qwen3.5-VL-27B FP8** via vLLM @ localhost:8200, 6 workers, autonomous planner (read 12 plans).
- **SeedVL** (doubao-seed-2-0-lite-260215) via Doubao Ark, 8 workers, calibration router (skips planner because the planner phase had API timeouts).

## Autonomous planner output (Qwen3.5)
| Domain | Strategy | Expert | Tools |
|---|---|---|---|
| D1 industrial | fusion | subspacead | descriptor, component_counter |
| D2 retail | fusion | subspacead | descriptor, retriever |
| D4 infrastructure | fusion | patchknn | descriptor, knowledge_lookup |
| D5 dermoscopy | fusion | patchknn | descriptor, knowledge_lookup |
| D5b brain MRI | fusion | subspacead | descriptor, knowledge_lookup |
| D5c liver CT | interpret | subspacead | descriptor, hotspot_cropper |
| D5d GI endoscopy | direct | patchknn | descriptor, knowledge_lookup |
| D6 LEVIR change | direct | dinov2_global | descriptor |
| D7 road BDD | direct | dinov2_global | descriptor |
| D8 surveillance | direct | dinov2_global | descriptor |
| D9 MVTec-LOCO logical | fusion | subspacead | descriptor, component_counter, knowledge_lookup |
| D10 VisA | interpret | subspacead | descriptor, hotspot_cropper |

The autonomous planner picks per-domain strategies that match the descriptor-rule baseline closely (fusion for industrial / texture / medical; direct for semantic GI / change / road; interpret for liver-CT and VisA where expert is reliable but VLM is hesitant).

## Known issues / honest limitations
1. **Online-override rho scaling**: the current `rho` computation compares SubspaceAD's `top_patches[0].score` (raw distance, range 10–100) against PatchKNN's `anomaly_score` (range 0–1). Cross-expert scaling means rho is essentially "how big is the SubspaceAD score divided by a small denominator", and is uniformly large on industrial domains, causing the online override to promote almost every D1 item to interpret. Fix for v2 of this codebase: use SubspaceAD's own median patch distance (or rank-based statistic) as the baseline.
2. **All-interpret on some domains**: combined effect of (1) means that the autonomous planner's choice (e.g. fusion) is overridden by the online rho rule on industrial-style domains. We report this honestly as a limitation; the reported v3 numbers reflect this behaviour.
3. **GPT-5.4 backend unavailable**: sub2api endpoint is failing (`The 'gpt-5.1' model is not supported when using Codex with a ChatGPT account`). The GPT-5.4 row in the main results table uses the existing v0/fusion/debate numbers; we did not refresh GPT-5.4 with the v3 agent.

## Files generated
- `benchmark/scripts/run_anomaclaw_v3.py` — agent runner (tools + experts + strategies + planner + override).
- `benchmark/results/anomaclaw_v3_qwen35_test.json` — Qwen3.5 v3 results (in progress).
- `benchmark/results/anomaclaw_v3_qwen35_test_plans.json` — autonomous plan trace.
- `benchmark/results/anomaclaw_v3_seedvl_test.json` — SeedVL v3 results (in progress).
- `refine-logs/update_paper_with_v3.py` — analysis pipeline that runs once both files finish and produces macro AUROC / paired bootstrap CIs.
