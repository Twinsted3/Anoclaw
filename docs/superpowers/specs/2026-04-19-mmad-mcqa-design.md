# AnomalyClaw v9 — Unified Task-Aware Agent (MMAD MCQA + Open-Ended)

**Date**: 2026-04-19
**Owner**: autonomous session (user asleep, approved full autonomy)
**Status**: spec approved by user; implementation in progress

## Goal

Extend v8 refutation agent into a single unified agent that accepts
`(image, refs?, question?, options?)` and produces task-aware outputs:
continuous anomaly_score for detection, MCQ letter for 4-choice questions,
free-text for open-ended. Mode is inferred by the LLM itself during the
first cognitive pass — no separate routing LLM call.

## Scope

- **Primary benchmark**: MMAD (39,670 questions across 9 types). Calibrate
  per-class thresholds on 989-item stratified dev sample; report on full
  8,366-image test.
- **Secondary benchmark**: CrossDomainVAD-11 (must not regress v8 results).
- **Backbones**: Qwen3.5-VL-27B primary; GPT-5.4 optional later.

## Non-Goals

- No new expert tools. Reuse agent_tools_v7's 13 tools.
- No retrieval changes this milestone (that lives in spec #2).
- No fine-tuning (milestone #3).

## Design

### Output schema (unified final JSON)

```json
{
  "anomaly_score": 0.0..1.0,       // always, even when MCQ is primary
  "mcq_answer":   "A|B|C|D|null",  // when options provided
  "free_text":    "str|null",      // when open-ended question provided
  "rationale":    "one sentence",
  "confidence":   0..100,
  "refutation_trace": {              // v8 fields retained
    "initial_score": float,
    "candidate_features": [...],
    "remaining_features": [...],
    "refutation_verdicts": [...],
    "updated_score": float
  }
}
```

### Input → mode inference rules

| Has `options` | Has `question` | Has `refs` | Mode |
|---------------|----------------|-----------|------|
| no            | no             | yes       | `detection` (CrossDomainVAD) |
| yes (Yes/No)  | yes            | yes       | `mcq_binary` (MMAD AD)        |
| yes (4-way)   | yes            | optional  | `mcq_choice` (MMAD defect/object) |
| no            | yes            | optional  | `open_ended`                  |

Mode inference happens inside the LLM's turn-1 JSON — no routing call.

### Mode-specific reasoning

- `detection` + `mcq_binary`: v8 refutation protocol unchanged. For
  `mcq_binary`, map final `anomaly_score` to A/B letter via per-class
  threshold (calibrated on dev).
- `mcq_choice`: different prompt branch — "observe, list visual evidence,
  match evidence to options, pick best letter". Tool calls optional; if
  the agent feels uncertain it can still call visual_inspection,
  reference_profiler, etc.
- `open_ended`: observe + describe. No MCQ letter.

### Ensemble (unchanged from v8)

Only for AD subset:
```
s_ensemble = 0.5 * s_direct + 0.5 * s_agent
A/B letter = sign(s_ensemble - τ_class)
```

For non-AD types: use agent's `mcq_answer` directly; Direct VLM reported
as baseline only.

### Per-class threshold calibration

For AD subset only. On 989-item stratified dev:
1. Compute `s_ensemble` for each dev item.
2. For each class c (e.g., "bottle", "cable", "capsule"), sweep
   τ ∈ {0.05, 0.10, ..., 0.95}; pick τ* maximizing MCQ accuracy on class c.
3. Apply τ*_c on full-test items of class c.

Fallback: global τ* if class has <10 dev items.

## File plan

- **Create**:
  - `benchmark/scripts/agent_prompt_v9.py` — task-aware system prompt
  - `benchmark/scripts/agent_v9.py` — extends v8 with `question`/`options`
  - `benchmark/scripts/mmad_eval_v9.py` — full-type evaluator
  - `benchmark/scripts/mmad_calibrate.py` — threshold calibration
  - `benchmark/results/mmad_v9_dev989.json` — calibration results
  - `benchmark/results/mmad_v9_fulltest.json` — full test results
- **Modify**:
  - `benchmark/scripts/agent_tools_v7.py`: NO changes (tool set frozen)

## Run plan

1. **Sanity** (50 items, all 9 types sampled): verify agent runs, MCQ
   letters parse, Direct VLM baseline works.
2. **Dev calibration** (989 items × 9 types ≈ 4500 QAs): fit per-class
   thresholds for AD; report per-type accuracy.
3. **Full test** (8366 items × 9 types = 39670 QAs): apply calibrated
   thresholds; report per-type accuracy and AD AUROC.
4. **Sanity regression**: rerun v9 on CrossDomainVAD test; must match v8
   Qwen3.5 ±0.5pp macro AUROC.

## Success criteria

| Metric | Target |
|--------|--------|
| CrossDomainVAD macro AUROC (v9 vs v8) | ≥ v8 − 0.5pp |
| MMAD AD MCQ accuracy | ≥ Direct + 1pp (currently −0.8pp) |
| MMAD AD AUROC | ≥ Direct + 1pp (currently +2.31pp) |
| MMAD defect types MCQ accuracy (agent vs Direct) | agent wins ≥3 of 4 types |
| MMAD object types MCQ accuracy (agent vs Direct) | agent within 2pp of Direct |

## Risks & mitigations

- **Prompt becomes bloated with 4 modes** → keep single system prompt but
  with clear mode-conditional subsections; turn-1 user message declares
  mode via the presence/absence of question+options.
- **MCQ answer parsing fails** → strict JSON retry loop (same as v8); on
  final failure, fallback to highest-probability letter from direct VLM.
- **Descriptive questions need different tools** → initial ranking: prefer
  visual_inspection and reference_profiler; fall back to others if agent
  requests them. No hard gate.

## Terminal state

Hand off to spec #2 (active self-evolution) after:
- Full MMAD test complete
- Per-type accuracy table added to paper §4
- Updated RESUME.md
