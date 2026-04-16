# v5 Per-Domain Router (Archived 2026-04-16)

This directory contains the v5 agent code that was superseded by v6. v5 used
per-domain hardcoded strategy selection (`QWEN35_AGENT_PLAN_REACT.json`) and
per-domain offline hyperparameters, which the audit showed was:

1. Not a real agent — strategy fixed before inference.
2. Over-crediting the agent — +5.5pp of the +6.28pp gain came from fusion
   alone, not routing.
3. Hyperparameter-overfit — fusion weight `w` and expert choice argmaxed on
   ~20 calibration items per domain with no held-out.

v6 replaces this with a per-item ReAct agent that has no offline tuning.

Spec: `docs/superpowers/specs/2026-04-16-real-ad-agent-design.md`
Plan: `docs/superpowers/plans/2026-04-16-real-ad-agent.md`

## Files archived here

- `benchmark/scripts/run_anomaclaw_v3.py` — main v5 runner
- `benchmark/scripts/react_skill.py` — v5 skill prompt
- `benchmark/scripts/agent_infer.py`, `agent_infer_v3.py`, `agent_infer_v4.py`
- `refine-logs/QWEN35_AGENT_PLAN_REACT.json`, `SEEDVL_AGENT_PLAN.json`
- `refine-logs/per_domain_w.py`, `per_domain_strategy_calib.py`
- `refine-logs/aggregate_strategy_matrix.py`
- `refine-logs/PER_DOMAIN_W.json`, `PER_DOMAIN_EXPERT.json`,
  `PER_DOMAIN_STRATEGY_MATRIX.{json,md}`, `ROUTER_*.json`, `V3_RESULTS_SUMMARY.json`
