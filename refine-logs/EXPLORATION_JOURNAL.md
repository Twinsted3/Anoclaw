# AnomalyClaw v6 — Exploration Journal

Per-round log of hypothesis → change → result → lesson. Newest entries at top.
Append a new block for every experiment iteration.

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
- **4 replicas on GPU 0-3** at 85% util with 24 workers gives ~18min full test
  (1418 items × 1 VLM call).
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
