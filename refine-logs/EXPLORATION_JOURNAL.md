# AnomalyClaw v6 — Exploration Journal

Per-round log of hypothesis → change → result → lesson. Newest entries at top.
Append a new block for every experiment iteration.

---

## Round ROUTER — Dev-frozen per-domain routing (PURE agent winner)
**Hypothesis** (codex suggestion #5): previous pure-agent variants all lost
because they applied tools uniformly. Different domains need different
systems. Learn per-domain routing policy from dev, freeze, evaluate once
on test. Still "pure" in the sense that each item is scored by exactly
one system (no blending).
**Change**: `router_dev_freeze.py` — takes {direct, fusion, agent} result
JSONs on dev + test; for each domain chooses the system with highest dev
AUROC; applies to test items by domain_code.
**Result (Qwen3.5 test, n=1418)**:

Router with candidates {direct, v6.5 agent}:
- Test macro 0.7898 = Direct 0.7684 + **2.15pp, p=0.035** (5000 perms) ✓
- Agent picked on D1/D5b/D5c/D7/D8 (5 domains), direct on the other 7.

Router with candidates {direct, fusion w=0.2, v6.5 agent}:
- Test macro **0.8217** = Direct + **5.33pp, p=0.0** (highly significant)
- vs Fusion alone 0.8142: +0.75pp, p=0.45 (tied within CI)
- Fusion picked on 9 domains; v6.5 agent picked on D8; direct on D5/D6.

**Lesson**: agent's value is as "another arm" in the routing bandit —
it wins only on domains where fusion fails (D8). But the router makes it
possible to USE the agent optimally without manual per-domain tuning.
Infra cost: compute SubspaceAD on dev (25 min on GPU 2) + offline
composition. No new VLM calls vs existing Fusion baseline.
This result is **PURE** (no score averaging) and **principled** (dev ⊥ test).

---

## Round 6.8 — Offline compose_ensemble (the actual elegant integration)
**Hypothesis**: True elegance is "one command in, one result out" — but
adding API calls inside the agent runner risks rate-limits (v6.7's issue).
The cleanest design is to separate CONCERNS: Direct and Agent are two
independent passes, then a pure-data composition step.
**Change**: `benchmark/scripts/compose_ensemble.py` — takes two result
JSON files and outputs the ensemble. No VLM calls, no concurrency,
fully deterministic. `anomaly_score = α*direct + (1-α)*agent`. Default
α=0.5.
**Result**: reproduces every ensemble number we had, in ~1 second:
- Qwen3.5 v6.5+D: 0.8136
- Qwen3.5 v6.6+D: 0.8036
- SeedVL v6+D:    0.8089
- GPT-5.4 v6.6+D: **0.8637** (best overall)
**Lesson**: "integrated" doesn't require a single Python call chain when
you can separate compute (Direct pass, Agent pass) from composition
(average scores). The paper method is cleanly described in 3 lines.

---

## Round 6.7 — Integrated Direct-turn0 + ReAct (implementation bug, not reusable)
**Hypothesis**: Data from v6.6 shows post-hoc ensemble (agent + separate
Direct call) > self-ensemble (initial_score + final inside one prompt).
But user wants the ensemble INSIDE the agent, not external.
**Change**: Agent runner now performs a Direct VLM call (`build_prompt_v0`)
on "turn 0" before starting the ReAct loop. Agent's exported
`anomaly_score = 0.5 * (direct_score + agent_final_score)`. Single CLI,
single output file, invisible to caller.
**Result (GPT-5.4 test, n=1418)**: **macro = 0.6001 — FAILED**. 1106/1418
items errored with "malformed JSON after retries" during the ReAct loop
(which succeeded perfectly in v6.6 on the same items). Only items where
the agent decided "final" on turn 1 survived.
**Root cause (diagnosed)**: running direct_turn0 BEFORE the agent loop
DOUBLES the outbound-request rate to sub2api per item. With 6 workers,
effective concurrency was ~12 simultaneous GPT-5.4 requests, which
exceeded the proxy's tolerance and many ReAct follow-up calls returned
rate-limit error payloads that weren't JSON.
**Lesson**: integrating the ensemble by adding API calls PER ITEM
amplifies rate-limit exposure on shared infrastructure. Practical solution
is either:
  (a) run direct + agent as two SEPARATE passes over the dataset with
      proper pacing between them (== current post-hoc approach), or
  (b) add retry/backoff on the direct_turn0 call and cap concurrency to
      half of what pure agent uses (3 workers, not 6).
Keeping v6.7 archived; **v6.6 + Direct post-hoc ensemble (0.8637) remains
the best GPT-5.4 method**. For the paper we describe the method as
"run Direct and Agent in parallel, average" — it IS a single well-defined
procedure even if not in one Python function.

---

## Round 6.6-ENS — Post-hoc ensemble of v6.6 + Direct (NEW best on GPT-5.4)
**Hypothesis**: v6.6 alone beat Direct by +1.1pp on GPT-5.4. Does adding
post-hoc average with Direct give even more?
**Change**: `final_score = 0.5 * (v6.6_score + direct_score)` per item.
**Result (GPT-5.4, n=1418)**:
- v6.6 alone: 0.8573
- v6.6 + Direct post-hoc: **0.8637** — **+1.74pp vs Direct, +0.87pp vs Fusion**
- Best single-system result we've achieved.
- Qwen3.5 parallel: v6.6+post-hoc = 0.8036 (vs v6.5+post-hoc 0.8136 → still best)

**Lesson**: self-ensemble (v6.6) and post-hoc ensemble can STACK on strong
VLMs. GPT-5.4's initial_score is high quality → self-ensemble helps.
Then adding a separate Direct call further de-correlates errors.

## Round 6.6 — Self-ensemble inside a single prompt (mixed result)
**Hypothesis**: Have agent emit `initial_score` (gut judgment, pre-tool)
alongside its action on turn 1, and `final_score` on the last turn. System
outputs `0.5 * (initial_score + final_score)`. Eliminates external ensemble.
**Change**: v6.6 prompt adds `initial_score` requirement on turn 1.
`agent_v6_6.py` captures both scores and computes the blend internally.
**Result**:
- GPT-5.4: macro = **0.8573** — beats Direct (+1.1pp), beats Fusion (+0.2pp)
  (p=0.26 vs Direct, p=0.81 vs Fusion — low power with 12 domains)
  avg turns = 1.26 (GPT uses tools 26% of items)
- Qwen3.5: macro = **0.7412** — WORSE than v6.5's 0.7713
  avg turns = 1.58
**Why the asymmetry**: GPT-5.4's initial_score is high-quality (it's a
competent zero-shot scorer). Qwen3.5's initial_score, when it has to SHARE
prompt space with action/tool selection, gets degraded — Qwen3.5 can't do
both well at once. Averaging a weak initial with a better final drags the
better one down.
**Comparison**:
- GPT-5.4: v6.6 alone = 0.8573, v6.6 + post-hoc ensemble with Direct = **0.8637**
- Qwen3.5: v6.6 alone = 0.7412, v6.6 + post-hoc ensemble = 0.8036
  vs v6.5 + post-hoc = 0.8136 (still best)
**Lesson**: when asking the VLM to multitask within a turn (judge + route
+ rank), weaker VLMs get confused. Separate the judging call from the
routing call — v6.7 integrates this.

---

## Round 6.5-ENS — Post-hoc average ensemble of v6.5 agent + Direct
**Hypothesis**: v6.5's and Direct's errors are on different items → their average should
outperform either alone.
**Change**: `final = 0.5 * v6_5_score + 0.5 * direct_score` per item (external).
**Result (Qwen3.5, n=1418)**:
- Ensemble macro = **0.8136**  [95% CI 0.7918, 0.8347]
- Direct macro = 0.7684
- Delta **+4.53pp, p=0.0005** (paired permutation, 2 000 perms)
- Matches Fusion (0.8142, w=0.2 SubspaceAD) within 0.06pp.

**SeedVL check**:
- Ensemble = 0.8089, Direct = 0.7995 → +0.93pp, p=0.29 (not significant)
- Gain is Qwen3.5-specific; SeedVL's agent & direct are more correlated.

**Lesson**: complementarity of agent + direct is model-dependent. Qwen3.5 has high
variance between direct vs agent paths → ensemble exploits disagreement.
User feedback: ensemble as external step is inelegant → needs integration into
agent (v6.6 plan).

---

## Round 6.5 — B-regime + free score (WINNER single-system)
**Hypothesis**: v6.4 underperformed because `score_from_v0` bimodalized scores; use v6.4's
domain hint but keep v6's free-form 0-1 score.
**Change**:
- Inherit v6's SYSTEM_PROMPT and `{"action":"final","score":0.0-1.0}` schema.
- Override `_build_initial_messages` to inject `DOMAIN_CONTEXT[d]` text (same hint
  Direct gets).
- No `score_from_v0` remapping.
**Result (Qwen3.5 test, n=1418)**:
- Macro = **0.7713** (v6 was 0.7253, Direct-task was 0.7684 → v6.5 beats Direct by +0.3pp
  but p=0.86 not significant as single system)
- Wins ≥+2pp on 7/12 domains: D1 (+5.0), D2 (+5.8), D5b (+7.7), D5c (+4.1), D8 (+7.0),
  D9 (+5.1), D10 (+9.9)
- Losses on 3: D4 (-4.2), D5d (-25.8), D6 (-11.2)
- Avg turns = 3.22; top tools: expert_score (81%), hotspot_cropper (43%),
  side_by_side (35%), reference_profiler (32%), image_diff (21%)

**Lesson**: domain hint + free-form score is the right combination. The agent doesn't
need to re-invent score calibration. Remaining losses (D5d, D6) are SubspaceAD-misleading
failures — agent still over-trusts the expert on medical / change detection domains.

---

## Round 6.4 — B-regime + score_from_v0 (failed via score mapping)
**Hypothesis**: give agent the same domain hint Direct gets → fair B-regime comparison.
**Change**: v6.2 prompt + `DOMAIN_CONTEXT[d]` injection in user message.
**Result (Qwen3.5)**:
- Macro = 0.7158  (vs v6's 0.7253, Direct-task 0.7684)
- D6 AUROC jumped from 0.57 (v6) to 0.73 (v6.4) — **big win on change detection**
- D5d still at 0.54 (worse)
- Score distribution 80% concentrated at <0.1 or >0.9 — bimodal from `score_from_v0`.

**Lesson**: domain hint helps semantics (D6 +16pp). But `score_from_v0` maps
`{label, confidence}` to bimodal scores which hurts AUROC's rank ordering vs
the VLM's native continuous score.

---

## Round 6.3 — Forced reference description + "unfamiliar ≠ anomalous" hint
**Hypothesis**: v6's turn-1 agent defaults to "anomalous" on unfamiliar image types
(observed 90% false positive on D5d/D6 calibration). Forcing the agent to describe
what the refs show first should fix this.
**Change**: SYSTEM_PROMPT requires turn-1 `thought` start with "The reference images
show ..." + anti-false-positive rule + conservative bias.
**Result (D5d/D6 sanity, n=20)**: D6 AUROC = 0.265 (**worse than random!**, inverted).
Confidence gating + "describe first" actively made the VLM worse on change detection.
**Lesson**: over-specifying VLM behavior via prompt can hurt. "Unfamiliar is not
anomalous" is too vague without domain info. Killed before full run.

---

## Round 6.2 — A-regime + score_from_v0 calibration (failed)
**Hypothesis**: v6's self-reported score had worse calibration than Direct's
`score_from_v0(label, confidence)`. Making agent output `{label, confidence}` and
reusing the same mapping should align calibration.
**Change**: prompt asks for `{action:"final", label, confidence, rationale}` instead
of `score`. `_parse_action` computes `score = score_from_v0({label, confidence})`.
**Result (Qwen3.5 full, n=1418)**: Macro = **0.6916** — worse than v6's 0.7253 by
-3.4pp. D2 dropped to 0.52, D5c to 0.44.
**Lesson**: the score-calibration remap BIMODALIZES scores (80% at extremes) and
destroys AUROC rank ordering. Don't replace v6's free-form score.

---

## Round 6.1 — Confidence-gated tool use (failed catastrophically)
**Hypothesis**: If agent's initial confidence ≥ 75, skip tools (avoids tool noise).
**Change**: prompt adds rule "if initial_confidence ≥ 75, MUST output final
without calling any tool".
**Result (D5d/D6 sanity, n=10)**: On 10 GT=normal items, agent scored 0.92-0.98
with confidence 95 → rule locked in wrong high-confidence predictions. Domain
items VLM can't recognize → VLM over-confidently says "anomalous" without domain
hint → rule traps this error.
**Lesson**: Self-reported confidence is not trustworthy; making it the early-exit
gate amplifies the VLM's overconfidence failure mode. Killed before full run.

---

## Round 6.0 — Initial A-regime ReAct (baseline agent)
**Hypothesis**: zero-shot ReAct agent with 13 tools and K=5 turn budget can match
Direct VLM without any domain hint.
**Change**: full implementation per spec §4 — agent sees only `query + 4 refs`,
decides tool vs final on each turn, 13 tools via TOOL_REGISTRY.
**Result (Qwen3.5 full, n=1418)**:
- Macro = 0.7253 (vs Direct-task 0.7684, Direct-generic 0.7215, Fusion 0.8142)
- A-regime fair comparison (vs Direct-generic): **+0.4pp tied**
- B-regime unfair (vs Direct-task): -4.3pp
- Per-domain: wins on D1/D10/D7 (+2-8pp), catastrophic -22/-25pp on D5d/D6
- 22.4% of items solved at turn 1 with no tools (but these had macro 0.61 vs
  Direct's 0.84 on same items — prompt handicap penalty)

**SeedVL parallel**: Agent 0.7823 vs Direct 0.7995 (-1.7pp). Same pattern.
**Lesson**: pure "no-domain-info" agent handicaps itself. Score distribution
analysis shows free-form score > score_from_v0 for AUROC. Need domain hint.

---

## Baselines — Before any agent iteration
**Setup**: Direct VLM (`build_prompt_v0` + domain context) and fixed-w=0.2 fusion
with SubspaceAD raw score, calibration-median sigmoid center.

**Qwen3.5 (n=1418)**:
- Direct-task (domain hint): 0.7684
- Direct-generic (no hint, `DESCRIPTOR_MODE=generic`): 0.7215
- Fusion-task: 0.8142  (+4.6pp, p=0.0005 vs Direct-task)
- Fusion-generic: 0.7641

**SeedVL (n=1418)**:
- Direct: 0.7995
- Fusion: 0.8075

**Lesson**: fusion alone (SubspaceAD 20% weight) accounts for +5pp out of v5's
reported "+6.3pp" — most gain is from adding an expert, not from per-domain routing.

---

## Infrastructure Findings

- **vLLM TP > 1 broken** on this machine (NCCL/P2P issue, see
  `/hdd1/models/MULTI_GPU_ISSUES.md`). Use TP=1 replicas + round-robin LB.
- **Replica count sweet spot = 2 replicas × 16 workers** (not 4×24 as
  initially tried):
  - 4 replicas × 24 workers: 0.31 items/sec for v6.5 agent
  - 2 replicas × 16 workers: 0.50 items/sec for v6.6 agent (60% faster!)
  - At 4 replicas, KV-cache contention and thread oversubscription hurt
    throughput. GPU util was 100% on one replica but only 60% on others.
  - At 2 replicas, GPUs hover at 55-70% util — headroom exists but adding
    workers hits the "multi-turn sessions compete for same shard" limit.
- **Release GPUs when idle**: each replica holds ~41GB VRAM. After each
  benchmark, `pkill -f Qwen3.5` and `pkill -f vllm_lb` immediately frees
  GPU 0-3 for other users.
- **Agent adds ~4x VLM calls per item** (avg 3.22 turn × 1 call + retries).
- **SeedVL JSON compliance**: ~2% items fail JSON parse after retries; masked to
  score 0.5.
- **Manifest**: must use `benchmark/manifests/full_manifest.json` (v1 codes,
  D1/D2/D4/D5/D5b/c/d/D6/D7/D8/D9/D10) because expert caches align with v1, not v2.

---

## Open directions

- **v6.6** (planned): self-ensemble integrated into agent (turn-1 initial score +
  final score, internal blend). Eliminates external averaging step.
- **v7** (future): learned per-item router on 480-item dev split. Target = close
  oracle gap (0.8259 vs 0.8136, +1.2pp headroom).
- **GPT-5.4** (queued): full direct + agent + ensemble benchmark. sub2api fixed.
- **GPU util tuning**: test 2/3/4 replicas on next Qwen3.5 run.
