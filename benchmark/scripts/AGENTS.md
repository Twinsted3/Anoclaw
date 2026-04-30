# AnomalyClaw Agent Family

Last updated: 2026-04-21

This document describes the agent runners under `benchmark/scripts/` that
produce anomaly-detection (AD) scores and MCQ answers on CrossDomainVAD-11
(`benchmark/manifests_v2/`). Only the **v10** agent is canonical for §4
main-table results; the older v6.x / v7 / v8 variants remain for ablation
and reproducibility of earlier drafts.

---

## Canonical for §4: `agent_v10.py`

### Architecture (AD mode)

```
                 ┌──────────── parallel ────────────┐
                 │                                  │
   item (refs,   │  run_v0 (infer.py)               │
   query) ──────►│    • generic-descriptor prompt   │───► direct_score
                 │    • DESCRIPTOR_MODE=generic     │
                 │                                  │
                 │  run_v9_item (agent_v9.py)       │
                 │    • task preamble (mode hint)   │
                 │    • turn 1: initial_score,       │
                 │      candidate_features,          │
                 │      action=(tool_call|final)    │
                 │    • turn 2-N: tool dispatch,     │
                 │      refutation, updated_score   │
                 │    • final turn: anomaly_score   │───► v9_score
                 │                                  │
                 └──────────────────────────────────┘
                                  │
                                  ▼
                    anomaly_score =
                      w_direct · direct_score + w_v9 · v9_score
                    (default w_direct = w_v9 = 0.5)
```

### Mode dispatch (agent-decided, not pre-routed)

1. v9 determines `mode` on turn 1 from the task preamble + VLM override.
2. v10 reads `v9.mode` **after** v9 returns.
3. Branch:
   - `mode == "anomaly_detection"` → blend as above, `anomaly_score` is
     the ensemble.
   - `mode in {"mcq_choice_anomaly", "mcq_choice_object",
     "object_analysis", "open_end", ...}` → **pass-through**: no Direct
     call is blended in, `anomaly_score = v9_score`, and
     `mcq_answer` / `free_text` / `option_scores` are populated from v9.

For non-AD modes the Direct call that ran in parallel is **discarded**
(paid its API cost but not used in the output). In practice the main
driver `agent_v10.main()` invokes v10 with `question=None, options=None`,
so Direct is only launched when the caller already knows the item is AD —
you pay for Direct only when it will be used.

### Parallel execution

Direct (`run_v0`) and v9 (`run_v9_item`) share no state. v10 launches
Direct on a daemon `threading.Thread` and runs v9 on the calling thread.
Wall-time per item = `max(direct_time, v9_trajectory_time)`. Both hit the
same VLM backend; throughput is limited by backend concurrency (sub2api
pool, Qwen vLLM load balancer, SeedVL API), not by v10's nested pools.

### Error fallback

| Failure | Fallback |
|---|---|
| Direct call raises | `direct_score = None`, `anomaly_score = v9.score` |
| v9 trajectory raises (very rare) | `v9 = None`, `anomaly_score = direct_score` |
| Both fail | `anomaly_score = None` with `error` populated |
| Agent runs but `v9.score is None` | `anomaly_score = direct_score` |

All failure modes leave the result record well-formed with all schema
keys present.

### Output schema

Every row has these fields (union across AD and MCQ modes):

| Field | AD mode | MCQ/open mode |
|---|---|---|
| `anomaly_score` | blended ensemble | `v9.score` (pass-through) |
| `direct_score` | independent Direct score | `null` |
| `v9_score` | v9 agent final score | same |
| `v9_initial_score` | v9 turn-1 guess | same |
| `v9_updated_score` | v9 score after refutation | same |
| `mcq_answer` | `null` | v9's chosen option |
| `free_text` | `null` | v9's open-ended text |
| `option_scores` | `null` | v9's per-option scores |
| `mode` | `"anomaly_detection"` | e.g. `"mcq_choice_anomaly"` |
| `n_turns`, `tools_used`, `candidate_features`, `refutation_verdicts`, `history` | v9 trajectory details | same |
| `w_direct`, `w_v9` | ensemble weights used | same (unused for non-AD) |
| `error`, `direct_error` | individual call errors | same |

### CLI

```
DESCRIPTOR_MODE=generic \
  python3 benchmark/scripts/agent_v10.py \
    --manifest benchmark/manifests_v2/full_manifest.json \
    --split test --backend {gpt,seedvl,qwen3} \
    --output benchmark/results/v2/v10_agent_{backend}_test.json \
    --max_turns 5 --max_workers 6 \
    --w_direct 0.5 --w_v9 0.5 \
    --resume
```

`DESCRIPTOR_MODE=generic` makes the Direct call use
`build_prompt_v0_generic` (no DOMAIN_CONTEXT). Without the env var the
Direct call uses the task-anchored v0 descriptor — valid for ablations
but **not** what §4 reports.

### Reading the results

§4 Table 1 needs three columns per backbone:

```
Direct column  : benchmark/results/v2/v0_direct_generic_{backbone}_test.json
                 field  = anomaly_score  (standalone Direct run)

Agent column   : benchmark/results/v2/v10_agent_{backbone}_test.json
                 field  = v9_score       (v10 also stores standalone v9)

Ensemble column: benchmark/results/v2/v10_agent_{backbone}_test.json
                 field  = anomaly_score  (v10's internal 0.5·D + 0.5·v9 blend)
```

v10 also holds its own `direct_score` (the Direct call v10 ran internally).
Use the **standalone** `v0_direct_generic_*_test.json` for the Direct column
to avoid any coupling concern; v10's internal Direct is primarily there for
the ensemble blend.

---

## Sibling agents

### `agent_v9.py` — unified task-aware agent (§5 baseline)

- Refutation-style agent with `candidate_features` + `refutation_verdicts`
- Mode-aware: one runner handles AD + MCQ + open-ended via
  `format_task_preamble(question, options)` classifier hint; VLM can
  override
- **No internal Direct call**; `anomaly_score` comes from the `final`
  action alone
- §5 passive-baseline runs use this agent directly
  (`run_passive_test_all.sh`)
- `agent_v10.py` wraps this; do not deprecate

### `agent_v6.py` / `agent_v6_5.py` / `agent_v6_6.py` — legacy descriptor agents

- Pre-v9 ReAct loop with DOMAIN_CONTEXT injection on turn 1
- **v6.6** has an internal `0.5 * (initial_score + final_score)`
  self-ensemble baked into `anomaly_score` output
- Used for the v1 paper; retained only for reproducing earlier numbers.
  New §4 work should use v10.

### `agent_v7.py`, `agent_v75.py`, `agent_v8.py` — iterated ablations

- v7: RGNC verification variant (see
  `refine-logs/CODEX_REVIEW_2026-04-18_v7.md`)
- v8: unstructured refutation (precursor of v9's refutation design)
- Not part of the canonical §4/§5 story; kept only for provenance.

---

## Design decisions worth keeping

**Why parallel Direct + v9 instead of sequential?**
Direct call latency (~2-5 s/item) overlaps with v9's turn-1 VLM call, so
`max(direct, v9) < direct + v9`. Given v9 trajectories average
10-20 s/item, the overlap saves ~20% wall-clock per AD item.

**Why is the blend post-hoc (not inside v9's reasoning)?**
Keeping Direct independent maximises ensemble diversity. If Direct's
output fed into v9's context, v9's final score would correlate more
strongly with Direct and the blend gain would shrink. This was exactly
the Option III-vs-Option-II discussion: Option III (parallel + post-hoc
blend) gives the largest empirical gain (~+2–4 pp over v9 alone on Qwen3.5,
vs Option II's +0.66 pp from v9-internal init/final blend).

**Why 0.5 / 0.5 weights by default?**
Matches v1 paper's convention. Ablation sweep (e.g. `0.3/0.7`, `0.7/0.3`)
should be run on a dev split, not test, if paper claims tuned weights.
The CLI exposes `--w_direct` / `--w_v9` for exactly this.

**Why single-tool-per-turn in v9?**
Reactive planning: tool arguments often depend on prior observations
(e.g., `tool_hotspot_cropper` bbox comes from `tool_image_diff` output).
Parallel multi-tool-per-turn loses this dependency. Empirically only
~5.9% of items use 2 tools, so multi-tool would save < 5% latency. See
discussion in the main tracking conversation (2026-04-21).

---

## Known contamination and manifest policy

- `infer.DOMAIN_CONTEXT` and `agent_tools.DOMAIN_KNOWLEDGE` were rewritten
  from v1 keys to v2 keys on 2026-04-21. v6.x runs produced **before**
  that rewrite with `--manifest manifests_v2/` are contaminated and must
  not be used for v2 paper numbers.
- `agent_v9.py` and `agent_v10.py` do not read DOMAIN_CONTEXT by default;
  they are safe across the rewrite. (v10 calls `run_v0`, which does read
  DOMAIN_CONTEXT — set `DESCRIPTOR_MODE=generic` to bypass.)
- Retrieval indices under `benchmark/retrieval_index/` were remapped
  2026-04-21 from v1 codes to v2 codes; v1 originals are kept as
  `*_index.npz.v1_*` backups.

See `docs/V2_MIGRATION_HANDOFF.md` and the `project_manifest_v2_canonical`
memory entry for the broader migration context.
