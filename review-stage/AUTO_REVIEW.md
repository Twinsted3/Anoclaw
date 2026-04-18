# AnomalyClaw Auto Review Log

## Round 1 (2026-04-19 07:33 CST)

### Assessment Summary
- **Score**: 4.5 / 10 (NeurIPS/ICML bar)
- **Verdict**: not ready
- **Reviewer**: Codex GPT-5.4 xhigh (direct repo read, workspace-write sandbox)

### Key criticisms (ranked)

1. **Central method claim is weaker than headline result.** v8 is pitched as core, but strongest system is `0.5·Direct + 0.5·v6.5`. → Reframe v8 as interpretable diagnostic variant; make score-diverse ensembling the spine.
2. **v8 implementation carried stale old-schema text** (`h_normal`, `h_anomalous`, `initial_p_a`, "Update p_a") in prompts and history summaries at `agent_v8.py:6, 55, 129, 273`. → Fixed in this round.
3. **"Auditable trace" claim too strong.** Final JSON dropped `history`; only 46% of items had `refutation_verdicts`. → Fixed: `history` now exposed in output JSON (next v8 run will include).
4. **Score-diversity mechanism was correlational, not controlled.** → Added controlled ablation with v6-BIN, v8-SOFT, RANDOM transformations (post-hoc, no new inference).
5. **Ensemble recipe too simple vs simple baselines.** → Table updated to compare against Fusion and Direct self-ensemble; reframe in abstract.
6. **GPT-5.4 v8 test broken (85% JSON fail).** → Cross-model claim softened to dev-only in abstract.
7. **Router story competes with v6/v8.** → Abstract rewritten to pick "score-diverse ensembling" as the spine; router stays in body as a component.

### Reviewer raw response (summary — full at `/tmp/codex_review_r1.out`)

Reviewer: "The winning system is not v8; it is 0.5 Direct + 0.5 v6.5. ... Can be a nice secondary contribution after correction, not the lead contribution today. ... A cleaner publishable version would say: 'Training-free VAD benefits from score-diverse VLM-agent ensembling; the gain is explained by complementary rank structure, not stronger standalone agents.' ... With that package, this could move into a 6.5-7 range."

### Actions taken this round

1. Fixed `agent_v8.py` stale schema (4 places), exposed `history` in output JSON.
2. Wrote `benchmark/scripts/score_diversity_ablation.py`, computed controlled ablation on existing Qwen3.5 test data:
   - v6 original ensemble: +4.53 pp
   - v6-BIN (no mid-mass, preserved rank): +2.31 pp ← halved
   - v8 SOFT (100% mid-mass): +1.35 pp (from +1.22 without softening)
   - RANDOM middle-mass noise: **-3.39 pp** (ensemble hurts!)
3. Rewrote abstract to lead with score-diverse ensembling (main contribution) + v8 as secondary/interpretable variant.
4. Replaced Experiments §4 score-diversity subsection with a 5-row ablation table (Table~\ref{tab:score_diversity}) establishing that middle-mass is necessary-but-not-sufficient (needs signal).

### Results
| Variant | Standalone AUROC | Ensemble Δ |
|---|---|---|
| v6.5 original | 0.7713 | +4.53 pp |
| v6.5 BIN (rank-preserving binary) | 0.6928 | +2.31 pp |
| v8 original | 0.6710 | +1.22 pp |
| v8 SOFT (rank-preserving compression) | 0.6710 | +1.35 pp |
| RANDOM uniform [0.2, 0.8] | 0.4845 | **-3.39 pp** |

**Mechanism refined**: ensemble gain = (signal) + (middle-mass) + (error complementarity). v6 has all three.

### Status
- Continuing to Round 2.
- Fixes NOT requiring new VLM calls (mostly framing + ablation on existing data) are in.
- Items requiring rerun (corrected v8 re-inference, GPT test retry) are deferred due to compute budget; will flag in R2.
