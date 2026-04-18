# AnomalyClaw v6 — Resume Guide

**Last active**: 2026-04-18 ~08:00 CST
**Status**: v6 iteration complete, paper-ready result set available, skills updated.

---

## How to start the next conversation

Open a new Claude Code session in this repo, then say:

```
读 RESUME.md 了解上次做到哪。
```

Or in English:

```
Read RESUME.md to catch up on the v6 research state.
```

Claude will read this file first, then your specific next request.

## Project state in one paragraph

AnomalyClaw v6 is a per-item ReAct agent over 12 anomaly-detection domains.
After 10+ variant iterations (v6.0→v6.11, self-ensemble, post-hoc ensemble,
dev-frozen router), the honest finding is that **Fusion (w=0.2 SubspaceAD)**
is the strong baseline and **pure agents lose to Direct on Qwen3.5 dev**,
match Direct on GPT-5.4, and add marginal value through per-domain routing
that is not statistically significant against Fusion. A codex-exec audit on
2026-04-18 caught 5 critical issues (test-set selection leakage, retrieval
index contamination, thread race, dispatch injection, ensemble fallback)
which have all been fixed. Four ARIS skills were updated and one new skill
(`codex-review-checkpoint`) was created from the retrospective.

## Headline results (12-domain test, n=1418)

| Backbone | Direct | Fusion | Best Pure Agent | Router |
|----------|--------|--------|-----------------|--------|
| Qwen3.5-VL-27B | 0.7684 | 0.8142 | v6.5: 0.7713 | 0.8217 |
| SeedVL         | 0.7995 | 0.8075 | v6: 0.7823    | not computed |
| GPT-5.4        | 0.8463 | 0.8550 | v6.6: **0.8573** | 0.8577 |

Router used dev labels (unfair to Direct); it beats Direct significantly
but ties Fusion (p > 0.4 both backbones). The standalone agent (v6.6) on
GPT-5.4 is the cleanest **pure** win at +1.1pp over Direct.

## Key documents (read in this order when resuming)

1. `RESUME.md` — this file. Entry point.
2. `refine-logs/V6_RESULTS.md` — final results, TL;DR, honest caveats.
3. `refine-logs/EXPLORATION_JOURNAL.md` — per-round hypothesis/change/result/lesson for v6.0 → v6.11 + router.
4. `refine-logs/CODEX_REVIEW_2026-04-18.md` — independent adversarial review (5 critical + 6 major + 3 minor issues).
5. `docs/superpowers/specs/2026-04-16-real-ad-agent-design.md` — original spec.
6. `docs/superpowers/plans/2026-04-16-real-ad-agent.md` — original implementation plan.
7. `refine-logs/tool_effects_qwen3_v6_5.md` — per-tool AUROC delta (most tools are net-negative).
8. `refine-logs/expert_strategy_qwen3.md` — expert × fusion-weight ablation.
9. `refine-logs/case_studies_v6_5_qwen3.md` — top-5 wins/losses with thought chains.

## Code layout (active, v6)

```
benchmark/scripts/
├── agent_v6.py                 # core ReAct loop
├── agent_prompt_v6.py          # system prompt + tool catalog
├── agent_tools_v6.py           # 13 tools, TOOL_REGISTRY, dispatch_tool
├── agent_v6_{5,6,7,8,9,10,11}.py # variants (5 = baseline winner, 6 = self-ensemble, 8 = anchored)
├── run_baselines_v6.py         # Direct + Fusion(w=0.2) baseline runner
├── compose_ensemble.py         # offline post-hoc ensemble composition
├── router_dev_freeze.py        # dev-frozen per-domain router
├── compute_fusion_dev.py       # Fusion on dev split
├── analyze_tool_effects.py     # per-tool AUROC delta
├── expert_strategy_matrix.py   # expert × weight ablation
├── analyze_case_studies.py     # top-k wins/losses
├── build_retrieval_index_clean.py # train-only retrieval index (post-codex fix)
├── eval_v6.py                  # macro AUROC + bootstrap + permutation
├── sanity_v6.py                # 5-item end-to-end smoke test
└── launch_qwen35_replicas.sh   # 2 vLLM replicas (2 is the sweet spot)
```

Archived (do not use): `archive/v5_per_domain_router/` — old hardcoded router.

## Infrastructure tips

- **Launch Qwen3.5 vLLM**: `bash benchmark/scripts/launch_qwen35_replicas.sh`
  — launches 2 replicas on GPUs 0, 1 (sweet spot; 4 replicas hurt from KV
  contention). LB auto-starts on port 8210 but re-launch if dead:
  ```
  env -u HTTP_PROXY -u HTTPS_PROXY -u http_proxy -u https_proxy -u ALL_PROXY -u all_proxy \
    LB_N_REPLICAS=2 \
    nohup /hdd1/jiangxi/AD-Agent/.venv_qwen35/bin/python \
      /hdd1/jiangxi/AD-Agent/benchmark/scripts/vllm_lb.py \
      > /tmp/v6_vllm_logs/lb.log 2>&1 &
  ```
- **Free GPUs when idle**: `pkill -9 -f Qwen3.5; pkill -9 -f vllm_lb`
- **sub2api for GPT**: `curl http://localhost:8080/v1/chat/completions -H "Authorization: Bearer ..."`
  — currently routes `gpt-5.4` correctly (verified 2026-04-18). Every call
  logs (requested → served) to `/tmp/served_model.log` via
  `infer._log_served_model`.

## Where to go from here (priority-ordered)

1. **If writing paper**: main table is in `paper/sections/4_experiments.tex`.
   The 3-row × 3-backbone table is from v6.6 era — re-check with
   `V6_RESULTS.md` for current numbers. Findings 1-4 in that tex file
   are v5-era and need rewriting.

2. **If extending research**: the cleanest open question is **label-free
   per-item routing**. User flagged that the dev-frozen router's 480
   labels are unfair to Direct (0 labels). A router that uses
   test-time-available features (e.g. subspacead_rank, VLM confidence,
   patchknn similarity) without any dev label argmax would be a
   principled answer. codex's suggestion #5 outlines this.

3. **If running more experiments**: SeedVL router is NOT computed (would
   need SeedVL dev Fusion + v6.5, ~1.5hr API). Also there is +2pp
   headroom between current router (0.8217) and oracle (0.8438) on
   Qwen3.5 per `expert_strategy_qwen3.md`.

4. **If re-auditing**: re-run codex exec after each major change:
   ```
   /codex-review-checkpoint "post-experiment v6.X"
   ```
   The skill captures the review prompt template and saves output to
   `refine-logs/CODEX_REVIEW_<date>.md`.

## Skills that were updated from this retrospective

- `result-to-claim/SKILL.md` — added 5 pre-flight integrity checks (test-set
  selection leakage, label budget asymmetry, prompt-structure penalty,
  tool causal contribution, self-reported calibration)
- `experiment-bridge/SKILL.md` — Phase 3 sanity now checks for degenerate
  output distributions + domain-specific pathologies + GPU utilization
  pilot before scaling
- `experiment-plan/SKILL.md` — Phase 3 now requires per-tool causal
  ablation block in main paper (not appendix) and explicit label-budget
  declaration per compared system
- `research-refine/SKILL.md` — added Principle 5 on fair-comparison
  discipline (label budget must be specified up-front)
- **new** `codex-review-checkpoint/SKILL.md` — stage-boundary codex-exec
  audit as a first-class skill, with a tested prompt template that caught
  5 critical issues on v6

## Git state

```
Branch: main (clean on v6 artifacts)
Last v6 commit: cd8b10e V6_RESULTS.md: final honest writeup
Recent 10 commits:
  cd8b10e V6_RESULTS.md: final honest writeup of Qwen3.5 + GPT-5.4 router study
  d440a9a GPT-5.4 dev-frozen router: 0.8577, ties Fusion (honest limit)
  3828f43 journal: Round ROUTER dev-frozen routing breakthrough
  2b3e58a Dev-frozen router over {direct, fusion, v6.5 agent}: 0.8217
  98c5bc8 Dev-frozen per-domain router: pure agent, +2.15pp significant
  657ec2d DEV split: all pure-agent variants lose to Direct on Qwen3.5
  7e8fb1b Fix lambda signature in v6.4/5/7 + v6.10 self-consistency
  18de168 v6.9 minimal pure agent (zoom_bbox only)
  078922b Codex review fixes + v6.8 anchored + analysis tools
  0fe9d7b infer.call_llm: log (requested -> served) model id per process
```

Uncommitted: `multi_round_skeptic.py` (deleted), `inference.py/prompts.py/tools.py/utils.py` (modified by original repo, not mine). Safe to leave.

## Contact points

- `refine-logs/` — all exploration artifacts
- `docs/superpowers/{specs,plans}/` — design + plan docs
- `benchmark/results/` — all result JSONs (force-added past gitignore)
- `PROJECT_INDEX.md` (updated 2026-04-16 for v5) — slightly stale but useful for file locations

---

*Generated at end of v6 iteration by Claude Opus 4.7 (1M context).*
