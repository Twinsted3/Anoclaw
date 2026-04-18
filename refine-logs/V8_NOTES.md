# V8 Live Notebook — Skeptical-Verification (Refutation-Driven) Agent

_updated 2026-04-19 ~03:50 CST_

## Theory

Core innovation: flip the default assumption from "anomaly-until-refuted"
(v6.5/v7 style, where VLM asserts anomaly and then accumulates tool
observations) to "normal-until-survived-refutation". Concretely:

- Turn 1 (no tool): VLM produces `initial_score` + a list of up to 3
  `candidate_features` (things that look unusual about the query) +
  `refutation_target` (the one suspicion it wants to check first).
- Turn 2+: agent calls a REFUTATION tool (side_by_side, reference_profiler,
  or reference_retriever) whose job is to find each candidate feature in
  the reference pool. If found → feature is refuted (it's normal
  variation); if not found → feature survives as anomaly evidence.
- Final: remaining_candidate_features == 0 → score 0.05–0.20; any survive
  → score 0.40–0.95 proportional to defect-likeness.

Theoretical claim: **VLMs over-flag surface variation as anomaly because
their pattern-matcher has no mechanism for "it's unusual-looking but
normal". The refutation protocol provides that mechanism: every flagged
feature is given an explicit chance to be dismissed.**

## Why this is a real agent (not just another prompt trick)

1. **Explicit hypotheses** — the candidate_features list names what the
   agent thinks is suspicious, with a location and a severity estimate.
2. **Counterfactual discipline** — for each feature the agent must
   articulate "what would refute this?" (the tool call encodes this).
3. **Sequential belief update** — each refutation verdict updates the
   candidate list, changing the final score.
4. **Tool calls are diagnostic, not accumulative** — each call either
   retires a feature or confirms it. No "add evidence then average".

This maps to scientific-agent structure: hypothesis, prediction, test,
update. The v6.5 agent did not require the first three.

## Results (continuously updated)

### Sanity 1 (2026-04-19 03:30, 10 items D1 label=0)
- direct: 8/10 correct
- v8 pure: **10/10 correct**
- v8 fixed D1_0038 (direct=0.98→v8=0.05) and D1_0084 (0.95→0.05)

### Sanity 2 (2026-04-19 03:40, 72 items mixed 12 domains × 6)
macro AUROC:
- direct: 0.8333
- v8 pure: 0.7269 (-10.6pp, too aggressive on some domains)
- **0.5×(direct + v8): 0.8889 (+5.6pp over Direct)** ← ensemble wins
- 0.3×direct + 0.7×v8: 0.8219
- 0.7×direct + 0.3×v8: same range

Key reading: v8 by itself is too refutation-heavy — some true anomalies
get their features "found in ref" (weak tool discrimination) and drop
out. But blending v8 with Direct recovers the bias: Direct gives a
high-confidence perceptual prior; v8 pulls down the over-confident FPs;
average lands right.

### Full dev partial (50 items, mostly D1 + early D2)
- v8 pure: 0.8425
- direct subset: 0.7850
- **v8 + direct w_direct=0.3: 0.8850 (+10.0pp)**

D1 is v8's best domain. Full dev will include D5/D6/D9 which are
known-harder for the refutation protocol.

### GPT-5.4 dev (full, n=480) — updated with v8

| System | dev AUROC | Δ vs Direct |
|---|---|---|
| Direct | 0.8153 | — |
| v6.6 self-ensemble | 0.8242 | +0.9pp |
| v7.5 (domain rules) | 0.7795 | -3.6pp |
| **v8 refutation (pure)** | 0.7731 | -4.2pp |
| direct + v8 (0.6/0.4) | 0.8272 | +1.2pp |
| direct + v6.6 (0.5) | 0.8372 | +2.2pp |
| **best triple (0.5 dir + 0.3 v66 + 0.2 v8)** | **0.8388** | **+2.4pp** |

v8 pure underperforms v6.6 on GPT-5.4 because GPT is less over-confident —
v6.6's self-ensemble is already a correction. Adding v8 as 20% of triple
blend squeezes an extra +0.16pp. On Qwen3.5 (which IS over-confident) v8
is the dominant ensemble signal.

v6.6 is already +0.9pp pure (first time any pure agent beats Direct on
GPT-5.4 dev). Blending with Direct adds another +1.4pp.

## Cross-model insight

Both Qwen3.5 v8 and GPT-5.4 v6.6 have the SAME pattern: **pure agent
is marginal, but agent+direct ensemble is significantly better than
either alone**. Two different agent mechanisms (refutation vs
self-ensemble), two different VLMs, same ensemble gain.

This suggests the publishable framing is:
**"Agent-Augmented Direct" — Direct provides fast perceptual prior,
Agent provides structural verification, their ensemble dominates both**

Not "agent replaces direct", but "agent refines direct".

## Experiment log

| Time | Variant | Result | Next |
|---|---|---|---|
| 03:30 | v8 sanity 10 D1 | 10/10 correct | extend sanity |
| 03:45 | v8 sanity 72 mixed | pure=0.7269 blend=0.8889 | run full dev |
| 03:48 | v8 partial 50 D1+D2 | pure=0.8425 blend=0.8850 | wait for full |
| 03:49 | GPT v6.6 dev | 0.8242 (+0.9pp) blend 0.8379 (+2.3pp) | ✓ validates ensemble |
| 03:49 | GPT v7.5 dev | 0.7795 (-3.6pp) | ✗ domain rules don't help GPT either |
