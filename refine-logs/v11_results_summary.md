# v11 Controller Learning — Final Results

**Date**: 2026-04-22 (overnight run)
**Backbone**: Qwen3.5-VL-27B (4 DP replicas on GPU 0/1/2/7, LB on port 8210)
**Dataset**: CrossDomainVAD-12 manifests_v2 test split (12 domains, n=1418)

## Macro AUROC

| Regime | Macro | Δ vs v10 | 95% CI | p̂(Δ>0) |
|---|---|---|---|---|
| Direct (generic descriptor) | 0.7119 | −2.14 | — | — |
| v9 agent alone | 0.6696 | −6.37 | — | — |
| v10 blend (= Passive v11) | 0.7333 | — | — | — |
| **v11 Controller (meta+domain RAG)** | **0.7539** | **+2.05 pp** | [+0.41, +3.67] | 0.995 |

Paired stratified bootstrap, 1000 resamples, per-domain stratification. The v10
blend re-computed from v9_score + direct_score on the same run (exact paired
comparison). Reproduces Table 1 Qwen3.5 ens 0.732 within 0.13 pp.

## Per-domain

| Dom | Source | n | v10 | v11 | Δ (pp) | A | B | blend |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| D1 | MVTec-AD | 120 | 0.934 | 0.938 | +0.5 | 9 | 47 | 64 |
| D2 | GoodsAD | 120 | 0.607 | 0.613 | +0.6 | 56 | 17 | 47 |
| D3 | VisA | 120 | 0.853 | 0.834 | −1.9 | 9 | 60 | 51 |
| D4 | SDNET | 120 | 0.670 | 0.704 | +3.4 | 24 | 48 | 48 |
| D5 | MVTec-LOCO | 120 | 0.676 | 0.678 | +0.2 | 28 | 64 | 28 |
| D6 | Real3D-AD | 120 | 0.531 | 0.558 | +2.8 | 33 | 12 | 75 |
| D7 | LEVIR-CD+ | 98 | 0.754 | 0.888 | **+13.4** | 24 | 55 | 19 |
| D8 | DermaMNIST | 120 | 0.647 | 0.721 | **+7.4** | 48 | 51 | 21 |
| D9 | BraTS | 120 | 0.848 | 0.816 | −3.2 | 34 | 35 | 51 |
| D10 | BMAD-Liver | 120 | 0.491 | 0.526 | +3.5 | 53 | 24 | 43 |
| D11 | HyperKvasir | 120 | 0.808 | 0.807 | −0.1 | 27 | 61 | 32 |
| D12 | BDD+RA | 120 | 0.982 | 0.963 | −1.9 | 11 | 47 | 62 |

Wins: 8/12 (D1,D2,D4,D5,D6,D7,D8,D10), Neutral: 1 (D11), Losses: 3 (D3,D9,D12).

## Pipeline artifacts

- Agent code: `benchmark/scripts/agent_v11.py`
- Learning pipeline: `benchmark/scripts/verbalized_v4.py` (partition, meta-rule
  reflector, stack, RAG retrieval)
- Bootstrap: `benchmark/scripts/v11_bootstrap.py`
- Passive dev (Stage A): `benchmark/results/verbalized/v11_passive_dev/*.json`
- Meta-rules (Stage B): `benchmark/results/verbalized/v4_meta/D*_meta.json`
- Stacked rulebooks (Stage C): `benchmark/results/verbalized/v4_rulebook/D*.json`
- Test eval (Stage D): `benchmark/results/verbalized/v11_eval_test/D*.json`
- Paper section: `paper/sections/controller_learning.tex` (new §4 between §3 method and §5 experiments)

## Disagreement statistics (across 12 domains, 40-item dev each)

| Bucket | Count | Usage |
|---|---|---|
| agree_correct | 238 | ignored (no signal) |
| agree_wrong | 99 | discarded (no routing signal) |
| disagree_a_wins | 61 | reflector input (trust Agent rules) |
| disagree_b_wins | 80 | reflector input (trust Direct rules) |

Meta-rule yield: 2–3 rules per side per domain, 12/12 domains parseable.

## Key findings

1. **Controller arbitration beats fixed blend at 95%**: +2.05 pp macro, CI
   [+0.41, +3.67], P=0.995. Gain compounds on top of v10's +1.69 pp over
   single-call Direct (Table 1).
2. **D7 (+13.4 pp) and D8 (+7.4 pp) carry the macro**: both are domains where
   v9 is significantly weaker than Direct and the controller correctly learns
   to trust Direct.
3. **Regressions are bounded and explained**: D3 over-trusts B, D9 has
   agree_wrong dominated by both-branch misses (no routing signal), D12 at the
   ceiling (0.982 blend has nowhere to go but down).
4. **Controller is domain-aware**: trust distribution varies dramatically
   (A-heavy on D2/D10; B-heavy on D3/D5/D7/D11/D12; blend-heavy on D1/D6).
5. **Parse-failure rate 0.00%**: 1418/1418 items produced a parseable
   controller JSON.

## Gotchas

- vLLM --limit-mm-per-prompt image=12 caps the meta-rule reflector. With K=10
  cases × (query+2 refs) = 30 images, we exceed the cap. Workaround: reflector
  sees only query images; refs implicit via branch rationales.
- DESCRIPTOR_MODE=generic must be set for agent_v11 to match Table 1's Direct
  baseline. Otherwise Direct uses domain-anchored prompts and the comparison
  is no longer apples-to-apples.
- Ablation of meta-only vs meta+domain not run yet — that would isolate the
  routing signal from the content signal. Deferred.

## Meta-only ablation (2026-04-23)

Stripped the domain layer (invariants + corrective FN/FP) from the rulebook,
kept only disagreement-derived meta-rules. Re-ran on the same 1418 test items.

| Regime | Macro | Δ vs v10 | 95% CI | P(Δ>0) |
|---|---:|---:|---|---:|
| v10 blend | 0.7333 | — | — | — |
| v11 meta only | 0.7396 | +0.63 | [−1.26, +2.36] | 0.730 |
| v11 meta+domain (full) | **0.7539** | **+2.05** | **[+0.41, +3.67]** | **0.995** |
| Δ(full − meta) | — | +1.43 | [−0.19, +3.13] | 0.960 |

**Conclusion**: the full stack is significant at 95%; meta-only alone is
directionally positive but NOT significant. Domain rules contribute an
incremental ~1.4 pp that is nearly significant. Meta-rules carry routing
signal but cannot substitute for the invariant + corrective content layer.

Per-domain (Δm = v11_meta − blend; Δf = v11_full − blend):

| Dom | blend | v11_meta | v11_full | Δm (pp) | Δf (pp) | pattern |
|---|---:|---:|---:|---:|---:|---|
| D1 MVTec-AD | 0.933 | 0.960 | 0.938 | +2.7 | +0.5 | meta ≥ full (noise) |
| D2 GoodsAD | 0.607 | 0.619 | 0.613 | +1.2 | +0.6 | meta ≥ full (noise) |
| D3 VisA | 0.853 | 0.867 | 0.834 | +1.4 | −1.9 | meta fixes, full overcorrects |
| D4 SDNET | 0.670 | 0.630 | 0.704 | −4.0 | +3.4 | full ≫ meta (invariants carry) |
| D5 LOCO | 0.676 | 0.700 | 0.678 | +2.4 | +0.2 | meta ≥ full (noise) |
| D6 Real3D-AD | 0.531 | 0.565 | 0.558 | +3.4 | +2.8 | tied |
| D7 LEVIR | 0.754 | 0.841 | 0.888 | +8.7 | +13.4 | full > meta (both positive) |
| D8 DermaMNIST | 0.647 | 0.599 | 0.721 | −4.8 | +7.4 | full ≫ meta (FN/FP rules carry) |
| D9 BraTS | 0.848 | 0.796 | 0.816 | −5.2 | −3.2 | full loses less than meta |
| D10 BMAD-Liver | 0.491 | 0.495 | 0.526 | +0.4 | +3.5 | full > meta |
| D11 HyperKvasir | 0.808 | 0.839 | 0.807 | +3.2 | −0.1 | meta > full |
| D12 BDD+RA | 0.982 | 0.963 | 0.962 | −1.8 | −1.9 | tied |

Four cleanly full-dominant domains (D4/D7/D8/D10), four meta-dominant
(D1/D3/D5/D11), four tied. This is more nuanced than a uniform story in
either direction — the two rule layers contribute complementary signal.

Artefacts: `benchmark/results/verbalized/v11_eval_test_meta_only/` and
`benchmark/scripts/v11_bootstrap_3way.py`.

## V9-error sensitivity check (2026-04-23, post R5)

R5 reviewer flagged that part of the +2.05 pp gain may come from Controller
rescuing items where v9 parse-failed (malformed JSON after retries). Dropping
those 100 items (~7%) and re-bootstrapping on the clean subset n=1318:

| Regime | Macro blend | Macro final | Δ | 95% CI | P(Δ>0) |
|---|---:|---:|---:|---|---:|
| v11 full | 0.7324 | 0.7498 | +1.73 | [+0.07, +3.29] | 0.982 |
| v11 meta-only | 0.7245 | 0.7305 | +0.60 | [-0.97, +2.12] | 0.771 |

Full gain survives at 95% (CI barely above zero). Loss of ~0.3 pp vs full-set
headline (+2.05) indicates part of the gain did come from "Controller
downweights broken v9". Remaining +1.73 pp is legitimate clean arbitration.

Per-domain (clean subset):
- D7 LEVIR: +8.86 (was +13.39) — biggest reduction from dropping errors
- D8 DermaMNIST: +9.52 (was +7.42) — slightly BIGGER on clean (surprising)
- D2 GoodsAD: -0.04 (was +0.61) — flipped to zero
- D3 VisA: -3.49 (was -1.88) — worse
- D10 BMAD-Liver: +4.61 (was +3.49) — better
- Other domains within 1 pp of full-set

Artefact: `benchmark/scripts/v11_bootstrap_clean.py`.

## No-rules ablation (2026-04-23, post R5 W5)

R5 reviewer asked for a controller-no-rules control to isolate "Controller-
as-mechanism" from "Controller + rules". Re-ran v11 on test with
rulebook_dir="" (Controller still sees image+refs+branches, but no rules).

Final 4-way comparison (n=1418, all 12 domains, paired stratified bootstrap 1000):

| Regime | Macro | Δ vs blend | 95% CI | P(Δ>0) |
|---|---:|---:|---|---:|
| v10 blend | 0.7333 | — | — | — |
| v11 no-rules | 0.7275 | **−0.58** | [−2.57, +1.37] | 0.260 |
| v11 meta-only | 0.7396 | +0.63 | [−1.26, +2.36] | 0.730 |
| v11 full (meta+domain) | **0.7539** | **+2.05** | **[+0.41, +3.67]** | **0.995** |

Pairwise (all paired-bootstrap):
- no-rules vs blend: −0.62pp, CI [−2.57,+1.37], P=0.260 (controller alone hurts on avg)
- meta vs no-rules: +1.21pp, CI [−0.71,+3.15], P=0.906 (routing rules help)
- full vs meta-only: +1.46pp, CI [−0.19,+3.13], P=0.960 (content rules help)
- **full vs no-rules: +2.67pp, CI [+0.78,+4.36], P=0.997** (rulebook contribution significant)

Per-domain (ΔnoR = v11_noR − blend):
- D4 SDNET: −11.75pp (biggest no-rules loss — controller without invariants
  hallucinates about cracks)
- D12 BDD: −4.57pp (no-rules destroys a near-ceiling blend)
- D9 BraTS: −9.01pp (agree-wrong domain, no-rules makes it worse)
- D7 LEVIR: +8.43pp (but full does +13.4, so rules still help)
- Most domains in [−5, +5] pp range with no-rules

**Interpretation**: The v11 Controller mechanism alone is NOT the source of
the gain. It is the rulebook that teaches the Controller when to trust
which branch. Removing rules reveals a tendency to over-correct blend.

Artefacts: `benchmark/results/verbalized/v11_eval_test_no_rules/` and
`benchmark/scripts/v11_bootstrap_4way.py`.

## Branch-frozen ablation (2026-04-23, post R6 W5)

R6 reviewer caught that my original 4-way ablation re-ran v9+Direct each
time, so branches weren't identical across regimes. Fix: cache the full
run's v9_score/v9_rationale/direct_score/direct_rationale, and re-invoke
ONLY the Controller VLM with different rule prompts on those cached inputs.

Script: `benchmark/scripts/replay_controller.py`.
Frozen outputs: `benchmark/results/verbalized/v11_frozen_no_rules/` and
`benchmark/results/verbalized/v11_frozen_meta_only/`.

### Frozen 4-way result (n=1418, 12 domains)

| Regime | Macro | Δ vs blend | 95% CI | P(Δ>0) |
|---|---:|---:|---|---:|
| v10 blend | 0.7333 | — | — | — |
| v11 no-rules (frozen) | 0.7227 | **−1.06** | [−2.84, +0.50] | 0.111 |
| v11 meta-only (frozen) | 0.7388 | +0.55 | [−0.98, +2.11] | 0.765 |
| v11 full (from full run) | **0.7539** | **+2.05** | **[+0.41, +3.67]** | **0.995** |

### Pairwise (branch-frozen, paired bootstrap 1000)

| Pair | Δ (pp) | CI | P>0 |
|---|---:|---|---:|
| no-rules vs blend | −1.04 | [−2.84, +0.50] | 0.111 |
| meta vs blend | +0.57 | [−0.98, +2.11] | 0.765 |
| full vs blend | **+2.05** | [+0.41, +3.67] | **0.995** |
| **meta vs no-rules** | **+1.62** | **[+0.34, +3.03]** | **0.992** |
| **full vs meta-only** | **+1.48** | **[+0.65, +2.36]** | **1.000** |
| **full vs no-rules** | **+3.10** | **[+1.77, +4.42]** | **1.000** |

### Interpretation

Both rule layers now significant at 95% on truly paired branches:
- Meta-rules (routing) contribute +1.62pp over empty-rulebook controller
- Domain rules (invariants + correctives) contribute +1.48pp on top of meta
- Together the rulebook contributes +3.10pp over no-rules controller

The arbitration MECHANISM alone (no-rules controller) is mean-negative
(−1.04pp, CI barely includes zero). This cleanly answers R6: rules
carry the gain, not the mechanism.

Comparison with unfrozen ablation (superseded):
- Unfrozen full-vs-meta: +1.46pp, P=0.960 (nearly significant)
- Frozen full-vs-meta:   +1.48pp, P=1.000 (highly significant — much tighter CI)
- Unfrozen meta-vs-noR:  +1.21pp, P=0.906
- Frozen meta-vs-noR:    +1.62pp, P=0.992

Unfrozen runs introduced ~0.2pp upstream noise (different v9/Direct per
regime) that widened CIs. Frozen replay removes that noise.

## Shuffled-rules negative control (2026-04-23)

R6 W6 asked for a negative control: do rules matter because they have
correct content, or just because they're any text in the prompt slot?
Test: pair D1↔D7, D2↔D8, ..., D6↔D12 so each domain receives another
domain's rulebook. Branch-frozen replay using the same v9/Direct cache.

### 5-way result (branch-frozen, n=1418)

| Regime | Macro | Δ vs blend | 95% CI | P(Δ>0) |
|---|---:|---:|---|---:|
| v10 blend | 0.7333 | — | — | — |
| no-rules | 0.7227 | −1.06 | [−2.84, +0.50] | 0.111 |
| **shuffled** | **0.7199** | **−1.34** | [−3.04, +0.32] | 0.053 |
| meta-only | 0.7388 | +0.55 | [−0.98, +2.11] | 0.765 |
| full (meta+domain) | **0.7539** | **+2.05** | [+0.41, +3.67] | **0.995** |

### Pairwise (branch-frozen bootstrap 1000)

| Pair | Δ (pp) | CI | P>0 | Interpretation |
|---|---:|---|---:|---|
| shuffled vs no-rules | −0.30 | [−1.55, +0.97] | 0.315 | indistinguishable |
| meta vs shuffled | **+1.91** | [+0.58, +3.26] | **0.996** | correct routing rules beat wrong ones |
| full vs shuffled | **+3.39** | [+1.87, +4.79] | **1.000** | correct rulebook ≫ wrong rulebook |
| meta vs no-rules | +1.62 | [+0.34, +3.03] | 0.992 | routing rules significant |
| full vs meta | +1.48 | [+0.65, +2.36] | 1.000 | domain rules significant |

### Per-domain shuffled behavior

Wrong rules actively hurt on content-dependent domains:
- D4 SDNET: −9.26pp (received D10 liver rules, structural crack reasoning destroyed)
- D9 BraTS: −13.51pp (received D3 VisA rules, medical arbitration wrong)
- D3 VisA: −4.94pp (received D9 brain MRI rules)
- D6 Real3D-AD: −3.35pp (received D12 road rules)

Neutral or slight positive on disagreement-driven domains:
- D7 LEVIR: +10.02pp (received D1 MVTec rules, but v9-weak pattern so Controller trusts B regardless)
- D8 DermaMNIST: +4.22pp (received D2 retail rules, but controller still finds patterns)
- D11 HyperKvasir: +1.50pp

### Conclusion

Rules are **not decorative**: scrambled rules provide no benefit over no
rules (indistinguishable, P=0.315). Correct rules beat scrambled rules
significantly. The Controller is genuinely reading and applying rule
content, not just conditioning on "something in the rule slot".

Artefacts: `benchmark/results/verbalized/v4_rulebook_shuffled/` (wrong-domain
rulebooks), `benchmark/results/verbalized/v11_frozen_shuffled/` (eval),
`benchmark/scripts/v11_bootstrap_5way.py`.

## v12 tool-catalog comparison (2026-04-24)

**Motivation**: does the Controller gain compound with tool-catalog
upgrades, or are they substitutes?

Ran v12 (v9 with v8 tool catalog + v10 prompt, v11 controller unchanged)
with:
- its own v12-rulebook (relearned meta-rules on v12 dev trajectories)
- v12-meta-only (domain rules stripped)
- v11's original rulebook (for cross-check)

### Full comparison

| Variant | v11 branches | v12 branches |
|---|---:|---:|
| Blend | 0.7333 | **0.7532** (+1.99pp tool lift) |
| + Controller no-rules | 0.7227 | 0.7379 |
| + Controller meta-only | 0.7388 | 0.7365 |
| + Controller full | **0.7539 (+2.05pp)** | 0.7339 (−1.93pp) |

### Per-domain v12 relearn (full) vs v12 blend

Wins: D7 +3.5pp (0.870→0.904), D8 +1.6, D11 +1.4, D12 +1.1, D6 +0.9, D1 ±0
Losses: **D10 −15.2pp** (disaster), D9 −6.0, D3 −4.5, D4 −3.8, D5 −1.8
Mixed: D2 ±0

### Key findings

1. **v12 blend 0.7532 ≈ v11 full 0.7539** (within 0.07pp). Tool upgrade
   and Controller learning are *substitute* paths, not complements.
2. **v12 + learning is MEAN-NEGATIVE** regardless of which rulebook
   (v11's or v12's own). Both −1.7 and −1.9 pp.
3. **Disagreement signal thinner on v12**: dev cases drop from 141
   (v11) to 97 (v12). v8 tools aligned the two branches better, so less
   routing signal for controller to learn.
4. **D10 is consistent -15pp disaster** in v12 learning regimes:
   something about v12's v9 rationale + controller interaction pushes
   scores wrong.

### Implication for paper narrative

Added §4 subsection "Controller learning vs tool-catalog upgrade"
(`ssec:ctrl_vs_tools`) with Table `tab:controller_vs_tools`. Frames
v11 Controller learning as a substitute path for tool upgrades on
this backbone, not a stacking gain. Directly addresses R7 single-
backbone concern with a principled scoping claim: *learning value is
bounded by branch-quality ceiling*.

Artefacts:
- `benchmark/results/verbalized/v12_eval_test/` (v12 + v11 rulebook)
- `benchmark/results/verbalized/v12_passive_dev/` (v12 dev outputs)
- `benchmark/results/verbalized/v12_meta/` (v12-trained meta rules)
- `benchmark/results/verbalized/v12_rulebook/` (stacked v12 rulebook)
- `benchmark/results/verbalized/v12_relearn_full/` (replay with v12 rulebook)
- `benchmark/results/verbalized/v12_relearn_meta_only/` (replay meta only)
- `benchmark/scripts/agent_v12.py`, `run_v12_eval_test.sh`, `run_v12_passive_dev.sh`
