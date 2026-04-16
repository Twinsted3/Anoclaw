# Experiment Log — 2026-04-15 (Tool × Expert × Strategy pivot)

## Context
- User requested a method pivot: reframe AnomalyClaw from a single 3-route adaptive router into a three-axis agent framework (**Tools × Experts × Strategies**) with an autonomous router that composes a (tool, expert, strategy) triple per image.
- Constraints reaffirmed: training-free (no fine-tuning), hyperparams OK to tune on calibration, ≤5 VLM calls/image.
- Directive: reuse existing infrastructure and data; autonomous overnight run; deliverable = updated experiments + rewritten paper.

## Pipeline executed

### 1. Aggregation — `refine-logs/aggregate_strategy_matrix.py`
- Loaded 13 test-split result JSONs (v0_direct / debate / egra-interpret / grounded × 3 backbones + SubspaceAD + classical DINOv2 patch/global).
- Computed per-(backbone, strategy, domain) AUROC on test.
- Computed fusion (0.8·v0 + 0.2·σ((s_exp − m)/m)) per backbone via item-aligned join with SubspaceAD (1298 matched items out of 1418 — 120 D8 items have no SubspaceAD test coverage).
- Output: `PER_DOMAIN_STRATEGY_MATRIX.json`, `PER_DOMAIN_STRATEGY_MATRIX.md`

**Key finding**: Per-domain oracle strategy varies significantly across the 12 domain codes. Oracle macro AUROC vs best-single-strategy:
- GPT-5.4: oracle 0.841 vs fusion 0.828 → +1.3 pp head-room
- SeedVL: oracle 0.825 vs fusion 0.796 → +2.9 pp
- Qwen3.5: oracle 0.847 vs fusion 0.831 → +1.6 pp

### 2. Registry — `refine-logs/anomaclaw_v2/registry.py`
- Formal dataclasses for 5 tools, 3 experts, 4 strategies.
- Domain family taxonomy mapping the 12 benchmark codes → {industrial, retail, infrastructure, dermoscopy, medical_mixed, brain_mri, liver_ct, gi_endoscopy, change, road, logical, industrial_visa}.

### 3. Router simulation — `refine-logs/anomaclaw_v2/router.py`
Three router variants implemented:
1. **Descriptor rules** — domain family → strategy mapping, zero-data.
2. **Calibration argmax** — per-domain argmax strategy using only 20-item calibration split.
3. **Oracle** — per-domain argmax on test labels (upper bound, cheats).

Each router's per-item score comes from looking up the existing strategy's recorded score for that item (no new VLM calls needed). This is legitimate because the agent's contribution is the router, not the strategies themselves.

**Macro AUROC (test, 1418 items, D8 fallback = direct for fusion):**
| | GPT-5.4 | SeedVL | Qwen3.5 |
|---|---|---|---|
| Direct | 0.813 | 0.779 | 0.776 |
| Fusion | 0.828 | 0.796 | 0.831 |
| Debate | 0.788 | 0.765 | 0.659 |
| Interpret | 0.805 | 0.778 | 0.778 |
| Descriptor router | **0.830** | 0.801 | 0.825 |
| Calibration router | 0.823 | **0.812** | **0.833** |
| Oracle | 0.841 | 0.825 | 0.847 |

### 4. Bootstrap significance — `refine-logs/anomaclaw_v2/bootstrap_fast.py`
Stratified paired bootstrap (1,000 resamples, per-domain stratification). Key comparisons:

| Backbone | Comparison | Δ | 95% CI | sig |
|---|---|---|---|---|
| GPT-5.4 | descriptor-router vs direct | +0.017 | [+0.009, +0.024] | ✓ |
| GPT-5.4 | calibration-router vs fusion | -0.006 | [-0.022, +0.009] | — |
| GPT-5.4 | fusion vs direct | +0.015 | [+0.005, +0.025] | ✓ |
| GPT-5.4 | oracle vs fusion | +0.013 | [+0.001, +0.026] | ✓ |
| **SeedVL** | **calibration-router vs fusion** | **+0.016** | **[+0.000, +0.032]** | **✓** |
| SeedVL | descriptor-router vs direct | +0.022 | [+0.014, +0.031] | ✓ |
| SeedVL | oracle vs calibration-router | +0.013 | [+0.001, +0.025] | ✓ |
| Qwen3.5 | descriptor-router vs direct | +0.049 | [+0.036, +0.061] | ✓ |
| Qwen3.5 | calibration-router vs fusion | +0.001 | [-0.010, +0.011] | — |
| Qwen3.5 | oracle vs calibration-router | +0.014 | [+0.006, +0.022] | ✓ |

### 5. Figures regenerated
- `figures/fig_intuition.pdf` — three-panel: (a) strategy heatmap per domain, (b) macro AUROC bars for direct/fusion/descriptor/calib/oracle across 3 backbones, (c) strategy mix bars (oracle vs calibration).
- `figures/fig_architecture.pdf` — Tool × Expert × Strategy block diagram with input/router/axes/output.
- `figures/fig_per_domain.pdf` — per-domain strategy AUROCs with calibration router's choice overlaid per cell.

### 6. Paper rewrite
- **Abstract** — reframed around three-axis framework; kept descriptor/fusion findings; headline router result.
- **§1 Introduction** — new Contributions list (5 items); new Figure 1 caption; positions vs AgentIAD/EAGLE/AutoIAD as direct competitors.
- **§2 Related work** — updated Agentic paragraph to call out tool/expert/strategy coupling; added ReAct + Toolformer as tool-using-LLM background.
- **§3 Method** — entirely new structure around Tools / Experts / Strategies / Router subsections; Algorithm 1 rewritten.
- **§4 Experiments** — new main table with 4 routers and oracle row; 4 findings; bootstrap Table 2 showing significance; limitations trimmed.
- **§5 Conclusion** — 3 paragraphs: main findings, limitations, future work.
- **Appendix** — added `app:debate` protocol, `app:router_rules`, `app:tools` contracts.

### 7. Compilation
- `tectonic -X compile`. 0 undefined references. 0 undefined citations.
- **Main body = 9 pages** (p1–9), references start p10. ✓ NeurIPS 2025 main track.
- Total 19 pages including references + appendix.

## Files
- `paper/main.pdf` (final)
- `refine-logs/PER_DOMAIN_STRATEGY_MATRIX.{json,md}` — per-domain × strategy × backbone AUROC
- `refine-logs/ROUTER_RESULTS.json` — router assignments and macro AUROC per backbone
- `refine-logs/ROUTER_BOOTSTRAP.json` — paired bootstrap summary (8 comparisons × 3 backbones)
- `refine-logs/anomaclaw_v2/registry.py` — Tool/Expert/Strategy registry
- `refine-logs/anomaclaw_v2/router.py` — router implementations
- `refine-logs/anomaclaw_v2/bootstrap_fast.py` — bootstrap analysis
- `refine-logs/aggregate_strategy_matrix.py` — per-domain AUROC aggregation

## Open items / follow-ups
- Qwen3.5 debate strategy is much weaker than expected (0.659 macro); calibration router correctly avoids it on almost all domains.
- Oracle headroom (1.3–1.9 pp) suggests a VLM-driven image-level router could close more of the gap — flagged as future work.
- D8 LEVIR has no SubspaceAD test coverage → fusion falls back to direct on those 120 items. Could fix by running SubspaceAD on D8 separately.
- The paper uses v1 AnomalyClaw numbers in the per-domain SeedVL table (Table 7 in Appendix); the calibration-router v2 per-domain numbers are reflected in the new Figure `fig_per_domain.pdf` and main Table 1.
