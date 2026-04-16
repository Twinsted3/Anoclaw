# AnomalyClaw v6: Real Autonomous Anomaly Detection Agent — Design Spec

**Date**: 2026-04-16
**Status**: Approved (pending user sign-off on this doc)
**Supersedes**: v5 per-domain router (`run_anomaclaw_v3.py`, `QWEN35_AGENT_PLAN_REACT.json`)

---

## 1. Motivation

Audit of v5 revealed three structural issues:

1. **Not a real agent.** High-level strategy is hardcoded per-domain in `QWEN35_AGENT_PLAN_REACT.json`; agent has no per-item autonomy over strategy.
2. **Unfair reported gain.** Headline "+6.28pp over Direct" bundles fusion (+5.5pp) with agent routing; the agent's own contribution is only +0.8pp over a fixed-w fusion baseline.
3. **Per-domain hyperparameters overfitted.** Fusion weight `w` and expert choice argmaxed on ~20 calibration items per domain with no held-out validation; some calib AUROCs near 1.0 indicate multi-comparison overfitting.

v6 rebuilds the agent so the VLM itself drives every per-item decision, and restructures experiments so the agent's contribution is isolated from fusion's contribution.

## 2. Goals

- **G1**: Per-item autonomous agent — no per-domain hardcoded strategy, expert, weight, or tool subset.
- **G2**: Fair main comparison — 3-row main table (Direct / Fixed-fusion / Agent) where Fixed-fusion is a strong baseline, not a weak direct.
- **G3**: Cross-backbone generalization — validate on Qwen3.5-VL-27B + SeedVL + GPT-5.4.
- **G4**: Statistical rigor — bootstrap CI + paired permutation test vs strongest baseline.

## 3. Non-Goals

- External benchmarks (MVTec-AD official split). Stays on existing 12-domain manifest.
- Localization / segmentation output. Only image-level AUROC.
- RL / supervised policy training. Pure prompt-engineered ReAct.
- Backwards compatibility with v5 agent code. v5 is archived, not maintained.

## 4. Architecture

### 4.1 Agent loop (per item)

```
State: history = [], budget = K (default 5)
Inputs to VLM: [query img, 4 normal refs, tool catalog, history, budget_remaining]

Forbidden inputs: domain code, domain hint, expert scores pre-computed,
                  per-domain plan, any offline hyperparameter.

loop t = 1..K:
    if t == K: prompt includes "THIS IS YOUR LAST TURN. action MUST be 'final'."
    VLM returns strict JSON:
      {
        "thought": "<free text reasoning>",
        "action": "call_tool" | "final",
        "tool": "<name>" | null,
        "args": { ... } | null,
        "confidence": 0..100,
        "score": 0.0..1.0 | null,   # required if action=final
        "rationale": "<text>" | null # required if action=final
      }
    if action == "final": break
    else: observation = execute_tool(tool, args)
          history.append({t, thought, tool, args, obs})
    # at t=K if action is still call_tool, observation is discarded
    # and a forced-final sub-call is made with prompt: "budget exhausted,
    # produce final now based on all prior observations"

Note: agent may return action=final at t=1 without calling any tool
(legitimate — means direct VLM judgment is sufficient).
```

Output: `{item_id, score, rationale, n_turns, tools_used, history}`

**No post-hoc fusion.** Whatever score the agent outputs is the score used for AUROC. This keeps the attribution clean — agent's final score is its responsibility.

### 4.2 Tool catalog (16 tools, 5 tiers)

**Tier 1 — Expert probes (1 tool, 4 experts behind it)**
- `tool_expert_score(name)` where name ∈ {subspacead, anomalyvfm, patchknn, dinov2_global}. Returns score + normalized rank within domain-split.

**Tier 2 — Visual inspection (6)**
- `tool_hotspot_cropper(k=5)` — auto-crop top-k expert hotspots
- `tool_zoom_bbox([x0,y0,x1,y1])` — agent-specified crop
- `tool_patch_grid(rows, cols)` — N×N systematic grid tiles
- `tool_image_diff(ref_idx)` — pixel diff vs ref i, high-diff mask returned
- `tool_rotate_align(ref_idx)` — align query to ref, then diff
- `tool_side_by_side(bbox)` — return query crop + 4 ref crops for comparison

**Tier 3 — Reference understanding (2)**
- `tool_reference_profiler()` — VLM caption of 4 refs: colors/shapes/textures/components
- `tool_reference_retriever(k=4)` — re-retrieve top-k most similar refs from domain's full normal pool (DINOv2 global similarity)

**Tier 4 — Structural analysis (3)**
- `tool_component_counter(threshold)` — connected-component count over expert hotspot mask
- `tool_segment_and_count(expected_type)` — SAM-based object segmentation + count
- `tool_texture_fft()` — FFT-based periodic-pattern disruption score

**Tier 5 — Semantic knowledge (1)**
- `tool_domain_knowledge(question)` — text-only LLM query ("what makes a normal MRI?"). Agent must formulate the question; no domain code passed.

### 4.3 Prompt design

- System prompt describes agent's role + tool catalog + JSON schema + budget constraints
- Per-tool "when to use" guidance (one line each)
- Budget discipline: confidence >80 → can terminate early; at t=K-1 VLM is warned "1 turn left"; at t=K VLM must produce `final`
- **No domain-specific prompts.** One universal prompt across all 12 domains.

### 4.4 Code archival plan

```
archive/v5_per_domain_router/
├── benchmark/scripts/
│   ├── run_anomaclaw_v3.py
│   ├── react_skill.py
│   ├── agent_infer_v3.py
│   └── agent_infer_v4.py
├── refine-logs/
│   ├── QWEN35_AGENT_PLAN_REACT.json
│   ├── SEEDVL_AGENT_PLAN.json
│   ├── per_domain_w.py
│   ├── per_domain_strategy_calib.py
│   ├── aggregate_strategy_matrix.py
│   ├── PER_DOMAIN_W.json
│   ├── PER_DOMAIN_EXPERT.json
│   ├── PER_DOMAIN_STRATEGY_MATRIX.json
│   └── ROUTER_*.json
└── README.md  (why archived)
```

### 4.5 New file layout

```
benchmark/scripts/
├── agent_v6.py              # ReAct loop, CLI entry
├── agent_tools_v6.py        # 16 tools, no per-domain branching
├── agent_prompt_v6.py       # system prompt + tool catalog text
├── run_baselines_v6.py      # direct + fixed-fusion
└── eval_v6.py               # AUROC + bootstrap + permutation test

refine-logs/V6_RESULTS.md    # main + ablation tables
```

## 5. Experimental design (fair)

### 5.1 Main table

3 rows × 3 backbones (Qwen3.5-VL-27B / SeedVL / GPT-5.4):

| System | Per-item compute | Expert | Per-domain hyperparam |
|--------|------------------|--------|----------------------|
| Direct | 1 VLM call | none | none |
| Expert-fusion (strong baseline) | 1 VLM call + 1 expert lookup, final = 0.8·VLM + 0.2·σ(expert) | SubspaceAD only, fixed | **none** (global w=0.2, global median) |
| **Our agent (v6)** | 1..K VLM calls + tool observations | chosen per-item by agent | **none** |

**Reported per cell**: macro AUROC + 95% bootstrap CI. Paired permutation test between Agent and Expert-fusion.

### 5.2 Ablations (appendix)

A1. Ablate per tool (remove one at a time from catalog).
A2. Budget sweep: K ∈ {1, 2, 3, 5, 10}.
A3. Oracle per-domain router (argmax on test) — upper bound gap.
A4. Agent with hidden domain hint (A vs B signal regimes) — sensitivity to input purity.
A5. Turns-vs-accuracy Pareto curve.
A6. Tool usage distribution per domain (qualitative).

### 5.3 Protocol invariants

- **Calibration split used only for**: (a) computing `subs_median` for the Expert-fusion baseline's sigmoid center, (b) `tool_reference_retriever`'s pool. Never for choosing strategies or weights.
- **Test split**: evaluated exactly once per system × backbone. No re-running after seeing results.
- **Fixed seeds**: `random.seed(42)`, `np.random.seed(42)`, deterministic VLM temperature=0.
- **No test-set label leakage**: all label accesses come from `benchmark/manifests/full_manifest.json` (v1) filtered by `split`.
- **Manifest choice**: using v1 not v2 because cached expert scores align with v1 codes (D1/D2/D4/D5/D5b/D5c/D5d/D6/D7/D8/D9/D10 = 12 domains). v2 renumbered and lacks expert caches for D3/D11/D12.

### 5.4 Statistical tests

- **Bootstrap**: for each (system, domain), resample items 1000× with replacement, recompute AUROC, take 2.5/97.5 percentiles.
- **Paired permutation**: for each (domain) compare agent vs fusion — flip 50% of item labels 10000× and compute null distribution of Δ-AUROC.

## 6. Execution plan (high-level)

| Phase | Deliverable | Est. time |
|-------|-------------|-----------|
| P1 | Archive v5 code | 30 min |
| P2 | Implement 16 tools | 1 day |
| P3 | Implement agent loop + prompt | 1 day |
| P4 | Implement baselines + eval | 0.5 day |
| P5 | GPT-5.4 code review via codex MCP | 1 hr |
| P6 | Sanity test 10 items Qwen3.5 | 30 min |
| P7 | Full benchmark 3 backbones × 3 systems × 1418 items | 2-3 days (SeedVL API is the bottleneck) |
| P8 | Aggregate + paper update | 1 day |

Total: ≈ 6-7 days wall-clock.

## 7. Success criteria (conservative)

- **Minimal viable result**: Agent macro AUROC > Direct by ≥ 2pp on ≥ 2 of 3 backbones.
- **Solid result**: Agent > Direct by ≥ 3pp on all 3 backbones. Agent and Expert-fusion comparable (within CI).
- **Strong result**: Agent > Expert-fusion by any margin on ≥ 1 backbone.

Agent does NOT need to beat Expert-fusion to be publishable — "per-item autonomous tool use matches hand-engineered fusion while adding interpretability and generalizing to novel domains" is a viable thesis. Main fair comparison is Agent vs Direct; Agent vs Fusion is secondary.

## 8. Open risks

1. **VLM JSON compliance.** 16-tool catalog is big; Qwen may fail to emit valid JSON. Mitigation: schema-constrained decoding if vLLM supports, else retry-on-parse-failure loop (max 2).
2. **SeedVL cost.** 1418 items × avg ~2.5 turns × SeedVL per-call cost = nontrivial. Mitigation: run agent + fusion + direct in one dispatch, cache all VLM responses, keep K=5 tight.
3. **GPT-5.4 routing bug.** sub2api routes to gpt-5.1 per PROJECT_INDEX.md. User will fix. **Action**: when P7 reaches GPT-5.4 dispatch, if routing still returns 5.1, pause and remind user to fix sub2api before proceeding.
4. **Agent worse than fusion.** Honest outcome possible. Mitigation: narrative pivot to "agent is comparable but interpretable" + cost-vs-accuracy Pareto.

## 9. What this spec does NOT commit to

- Specific VLM prompt wording (iterate during P3).
- Exact SAM variant for `tool_segment_and_count` (pick smallest that works).
- Whether `tool_rotate_align` uses cv2 keypoint-match or DINOv2 feature match (decide in P2).
- Per-figure layout for paper (deferred to post-results).

---

## Sign-off

- [ ] User approves this design → proceed to writing-plans
