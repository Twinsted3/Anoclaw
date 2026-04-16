# AnomalyClaw: Research Idea & Method Specification

**Date**: 2026-04-15 (revised after iteration 1 produced agent ≈ direct)
**Status**: ACTIVE — implementation must conform to this spec.

## 1. Problem statement

Cross-domain visual anomaly detection (VAD) under a training-free constraint:
- One agent must handle 11+ heterogeneous domains (industrial texture, retail, infrastructure, dermoscopy, medical imaging, GI endoscopy, remote-sensing change, road obstacle, logical anomaly).
- No fine-tuning of the VLM or the experts.
- Reference-based: each query has 1–10 normal references.
- VLM call budget: ≤ 5 calls/image; target average ≤ 3 calls/image (relaxed from 1.3 — too few calls leaves no operating room for tool composition).

## 2. Hard success criterion

The agent must beat **direct VLM (v0)** — i.e. the no-agent baseline that just calls the VLM with the descriptor — by **≥ 5 pp macro AUROC** on the test split, on at least one backbone (Qwen3.5 first), then on GPT-5.4 and SeedVL.

- Qwen3.5 direct = 0.776 → target ≥ 0.826
- SeedVL direct = 0.779 → target ≥ 0.829
- GPT-5.4 direct = 0.813 → target ≥ 0.863

Score fusion (`0.8·s_v0 + 0.2·σ(s_exp)`) already beats direct on all three backbones (Qwen3.5 +5.5 pp, SeedVL +1.7 pp, GPT-5.4 +1.5 pp), so the simplest agent (apply per-domain fusion when expert is reliable, direct otherwise) should comfortably clear +5 pp on Qwen3.5 and meet or approach it on SeedVL/GPT-5.4.

## 3. Core thesis

A VAD agent should be a **composition of tools, experts, and strategies** orchestrated by a VLM router, not just a router over fixed strategies. The +5 pp comes from the agent **giving the VLM new visual evidence** — high-resolution hotspot crops, retrieved-similar references, knowledge-augmented prompts — that no single fixed pipeline provides.

## 4. Three orthogonal axes (frozen)

### 4.1 Tools — action primitives (zero or few VLM calls)
| Tool | Function | Cost |
|---|---|---|
| `domain_descriptor` | Returns task-anchored anomaly definition for the domain. | 0 |
| `reference_retriever` | DINOv2-CLS cosine similarity → top-k similar refs from the pool. | 0 |
| `hotspot_cropper` | Crops the expert hotspot (top-k patches) into a tight bbox. | 0 |
| `component_counter` | Connected-component count on the expert hotspot map. | 0 |
| `knowledge_lookup` | Returns a domain-specific keyword list for prompt injection. | 0 |

### 4.2 Experts — pretrained anomaly detectors (cached per item)
| Expert | Strength | Backbone |
|---|---|---|
| SubspaceAD | Industrial texture, retail, logical, liver CT | DINOv2-giant + PCA |
| Patch-kNN | Infrastructure cracks, dermoscopy | DINOv2-giant patches |
| DINOv2-global | GI endoscopy, sanity check | DINOv2-giant CLS |

### 4.3 Strategies — VLM inference recipes
| Strategy | VLM calls | Description |
|---|---|---|
| `direct` | 1 | Descriptor-only prompt with full image + refs. |
| `fusion` | 1 | Direct + post-hoc blend with expert score (`s = (1−w)·s_v0 + w·σ(s_exp)`). |
| `zoom_fusion` | 1 | Direct call, but the VLM input is augmented with the expert hotspot crop as an additional image. Then post-hoc blend. |
| `retrieve_fusion` | 1 | Direct call with top-k retrieved refs (instead of random first-k). Then post-hoc blend. |
| `knowledge_fusion` | 1 | Direct call with knowledge_lookup keywords injected into the descriptor prompt. Then post-hoc blend. |
| `interpret` | ≤ 2 | Direct call; if v0 says normal AND expert hotspot is strong + concentrated, second call with crop. |
| `debate` | 2 | Proposer + advocate, rule-based aggregation. |
| `multi_view` | 2–3 | (a) full-image VLM call, (b) zoom-crop VLM call, (c) blend with expert + cross-call confidence. Two views give the VLM both global context and high-res defect signal. |
| `verify_then_blend` | 2 | (a) zoom_fusion VLM call with descriptor + crop, (b) refute-call asks "is the flagged region truly anomalous given the references", (c) blend two confidences with expert. |

### 4.4 Per-domain knobs (calibrated, frozen)
- **Per-domain fusion weight** `w(d)` selected from grid `{0, 0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0}` on calibration.
- **Strategy selection** `S(d)` chosen by autonomous planner (text-only VLM call) or calibration argmax — frozen per backbone after the calibration pass.
- **Expert choice** per domain (which of SubspaceAD / Patch-kNN / global is the primary score input).

## 5. Autonomous orchestration (the agent loop)

For each test item:
```
1. Look up plan = router(domain)         # cached per (backbone, domain)
   plan = {tools: [...], expert: ..., strategy: ..., w: ...}
2. Run pre-strategy tools                # zero VLM calls
   - if domain_descriptor in tools: descriptor = lookup(d)
   - if knowledge_lookup in tools: keywords = lookup(d)
   - if reference_retriever in tools: refs = retriever(query, ref_pool, k=2)
   - if hotspot_cropper in tools and strategy=zoom_fusion:
        crop = cropper(query, expert_patches)
3. Build VLM prompt from (descriptor, [keywords], refs, [crop])
4. Execute strategy:
   - direct/fusion/zoom_fusion/retrieve_fusion/knowledge_fusion: 1 VLM call → score
   - interpret: 1 VLM call; conditional 2nd call
   - debate: 2 VLM calls
5. Final score = blend(VLM score, expert score, w)
6. Emit decision trace JSON
```

## 6. Implementation contract (must match)

- File: `benchmark/scripts/run_anomaclaw_v3.py`
- For each strategy, the agent MUST execute the chosen action — no silent online overrides that discard the planned strategy.
- The autonomous-planner VLM call MUST output the JSON plan and its reasoning; the trace is emitted with every item.
- Tools that don't add new visual evidence are no-ops (e.g. `knowledge_lookup` is a prompt injector; `component_counter` produces a structural prior used only when the strategy says so).

## 7. Path to +5 pp

Per-domain `w` alone gives ≤ +1.4 pp (calibration overfits 20-item splits). Strategy switching alone caps at oracle = +1.6 pp on Qwen3.5. **The remaining gap must come from new visual signal**: zoom + retrieval + knowledge.

Expected per-strategy contribution on Qwen3.5 (hypothesis to be validated):
- Per-domain `w` from calibration: +0.5 pp (over-fit-corrected estimate)
- `zoom_fusion` on D1/D5b/D5c/D10 (industrial + medical with focal lesions): +1.5–3 pp
- `retrieve_fusion` on D2 retail (heterogeneous pool): +0.5–1 pp
- `knowledge_fusion` on D4/D5/D5b/D5c/D5d (medical/infrastructure where keywords help): +1–2 pp
- Strategy choice captures the rest of the oracle gap: +0.5 pp

Sum (idealised, additive): +4–6 pp.

## 8. Validation order

1. Implement `zoom_fusion` strategy (highest single-bullet leverage). Calibrate per-domain `w`.
2. Run on Qwen3.5 calibration (220 items, fast). Confirm calibration macro AUROC ≥ fusion + 4 pp.
3. If yes → Qwen3.5 test (1418 items). Target: ≥ 0.881.
4. If yes → port to SeedVL test, then GPT-5.4 (limited budget).
5. If calibration falls short → add `retrieve_fusion` and re-test.
6. If still short → add `knowledge_fusion` + autonomous tool composition.

## 9. Anti-goals (do not do)

- Do not add an "online expert override" that silently replaces the chosen strategy.
- Do not introduce per-image VLM router calls that add cost without proven AUROC gain.
- Do not tune any hyperparameter on test or dev — calibration only.
- Do not claim AUROC numbers without paired bootstrap CIs against fusion.
