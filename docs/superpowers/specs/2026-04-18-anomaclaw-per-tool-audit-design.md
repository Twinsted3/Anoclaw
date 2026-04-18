---
title: AnomaClaw v7 — Per-Tool Causal Audit & Niche-Aware Agent
date: 2026-04-18
status: approved
backbone: Qwen3.5-VL-27B (INT8)
baseline: Direct only (Fusion / Router not used for comparison in v7)
---

# AnomaClaw v7 — Per-Tool Causal Audit & Niche-Aware Agent

## Motivation

v6.5 agent on Qwen3.5-VL reaches 0.7713 macro AUROC vs Direct 0.7684 (Δ=+0.29pp, not significant). Per-tool causal analysis (`refine-logs/tool_effects_qwen3_v6_5.md`) shows **10 of 11 tools are net-negative** on the subset where they are called:

| Tool | Coverage | Δ vs Direct |
|---|---|---|
| zoom_bbox | 2.9% | **+7.0pp** (only positive tool) |
| expert_score | 76% | -0.55pp |
| hotspot_cropper | 42.7% | -4.7pp |
| reference_profiler | 32.4% | **-9.4pp** |
| side_by_side | 29.8% | -2.2pp |
| image_diff | 20.1% | -1.2pp |
| component_counter | 2.1% | -13.3pp |
| patch_grid | 1.4% | -5.6pp |
| rotate_align | 0.8% | **-28pp** |
| domain_knowledge | 0.3% | 0 (n=4) |
| segment_and_count | 0.1% | 0 (n=1) |

The current agent is essentially a noisier Direct. To become a real agent, each tool must have a **documented niche** (a slice of input space where it provably helps), and the agent prompt must surface these niches so the model can compose tools intentionally rather than by habit.

## Success Criteria

1. Every retained tool has a tool card with n≥10 samples in its niche and Δ>0 with bootstrap CI lower bound > 0 on that niche
2. `agent_v7` beats `Direct` on Qwen3.5-VL dev (n=480) with macro AUROC delta significant at p<0.05
3. Agent_v7 runs on test n=1418 **exactly once** for final reporting
4. Each tool card is reproducible from saved raw results

## Non-Goals

- Not targeting Fusion (0.8142) or Router (0.8217) — per user instruction, only Direct is the baseline
- Not adding new tools in v7 — strictly audit and trim the existing 11
- Not changing the underlying VLM, experts, or retrieval index

## Architecture

### Per-Tool Protocol (5 steps)

**Step 1 — Diagnosis (manual, no new runs)**
- From `v6_5_agent_qwen3_test.json`, sample up to 20 cases where the tool was invoked (10 hits, 10 misses)
- Inspect tool output, agent thought chain, final score
- Classify failure mode: (a) wrong trigger, (b) unclear output, (c) VLM misreads a valid output

**Step 2 — Redesign (code change in `agent_tools_v7.py` / `agent_prompt_v7.py`)**
- Fix trigger: add prompt-level gate or description that narrows when the tool is offered
- Fix output schema: add explicit verdict hint, include disconfirming "IF X THEN normal" line to prevent confirmation bias
- Preserve backward-compatible signature so `single_tool_agent` can swap

**Step 3 — Isolated Evaluation (parallel)**
- Build `single_tool_agent.py`: Direct-style prompt + only one tool + ReAct loop (default 3 turns; auto-retry at 5 turns if all slices Δ≤0)
- Run on dev n=480
- Save raw results → `benchmark/results/tool_audit/<tool>.json`

**Step 4 — Niche Discovery (analysis)**
- Slice results by:
  - Domain (12 slices)
  - Expert score quantile (low/mid/high)
  - Direct score margin (|Direct-0.5| low/mid/high)
  - VLM initial confidence (if computable)
  - Reference image availability
- For each slice compute Δ vs Direct + bootstrap 95% CI
- Niche condition: **n≥10 AND Δ>0 AND bootstrap CI lower bound > 0**
- If no slice passes → DROP with justification
- Write `refine-logs/tool_cards/<tool>.md`

**Step 5 — Composition**
- Collect KEEP tools and their cards
- Inject full tool cards (not abstract summaries) into `agent_v7` prompt
- Run on dev n=480 → verify Δ > Direct
- Run on test n=1418 **once**

### Infrastructure

**vLLM**
- 3 replicas on GPUs 0, 1, 2 (Qwen3.5-VL-27B INT8, single card each)
- LB on port 8210 (reuse `vllm_lb.py`)
- Per-replica concurrency = 3, total concurrent workers = 9
- **Shutdown when idle**: after Phase B completes, kill replicas; restart only for Phase C dev+test runs

**Queue**
- 11 per-tool jobs, concurrency = 9
- Each worker: single_tool_agent.py → JSON → build_tool_card.py
- Failure isolation: per-worker log, one crash does not halt queue

### Files

New files:
- `benchmark/scripts/single_tool_agent.py` — parameterised single-tool ReAct runner
- `benchmark/scripts/tool_audit_runner.py` — queue driver for 11 tools
- `benchmark/scripts/build_tool_card.py` — slice analysis + card generator
- `benchmark/scripts/agent_v7.py` — composed agent with tool cards in prompt
- `benchmark/scripts/agent_tools_v7.py` — redesigned tools
- `benchmark/scripts/agent_prompt_v7.py` — redesigned prompt with tool cards

Output artifacts:
- `benchmark/results/tool_audit/<tool>.json` × 11
- `refine-logs/tool_cards/<tool>.md` × 11
- `benchmark/results/v7_agent_qwen3_dev.json`
- `benchmark/results/v7_agent_qwen3_test.json`
- `refine-logs/V7_RESULTS.md`

### Data Discipline

- **Dev only for slicing / redesign.** Any tuning that touches test results is forbidden
- **Test runs exactly once** after dev composition is frozen
- **Tool cards must cite raw numbers** with bootstrap CI to prevent cherry-picking
- **Original v6 retrieval index** is used (already cleaned per 2026-04-18 codex audit)

## Risk & Mitigation

| Risk | Mitigation |
|---|---|
| All 11 tools DROP (agent degenerates to Direct) | Acceptable outcome — report as honest finding |
| Niche found is fluke (small-sample noise) | Bootstrap CI lower bound > 0 requirement, n≥10 |
| Redesigned output confuses VLM differently | Step 1 diagnosis re-audits after single-tool run |
| vLLM replicas race condition | 3 replicas with LB, per-worker JSON isolation |
| GPU waste | Kill vLLM between Phase B and Phase C |

## Timeline

- Phase A (diagnosis + redesign, serial): ~2-3 hours depending on how many tools survive audit
- Phase B (parallel single-tool eval): ~20 minutes (11 tools × 480 samples × 3 turns / 9 concurrent)
- Phase C (compose + dev + test): ~25 minutes (dev + test at 9 concurrent)

Total wall-clock estimate: 3-4 hours.

## Out of Scope

- SeedVL and GPT-5.4 backbones: not run in v7 (Qwen3.5-VL only per user focus)
- Router / Fusion baselines: not re-computed (not the target)
- New tools beyond current 11: not added
- Paper-level result table updates: v7 is a research step, reporting goes into V7_RESULTS.md only
