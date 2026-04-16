# AnomalyClaw Improvement Plan

**Date**: 2026-04-13
**Status**: Paper draft compiled (87KB), codex R1 review received (borderline reject)
**Goal**: Address all codex feedback to reach accept territory

## Priority 1: Experiments Needed (blocks submission)

### E1. Qwen3.5 agent_v1 test ⏳
- **Status**: Running (15%, ~2h ETA)
- **Expected**: ≥ 0.800 macro (+0.8pp over v0 0.792)
- **Paper impact**: Fills "pending" in Table 2, confirms 3-backbone consistency
- **If worse than v0**: Report honestly, note it matches the "inverse scaling" pattern

### E2. Budget-matched baselines
- **What**: At same 1.3 calls/image budget, compare:
  - v0 + random escalation (randomly re-examine 30% of items)
  - v0 + confidence-based escalation (re-examine 30% lowest-confidence items)
  - AnomalyClaw (expert-disagreement escalation)
- **Why**: Codex reviewer wants proof that the ROUTING SIGNAL matters, not just extra calls
- **How**: Post-hoc from existing v0 + agent_v1 data (no new API calls needed)
- **Effort**: 2h analysis + write-up

### E3. Paired bootstrap CIs for v0 vs AnomalyClaw
- **What**: Per-backbone paired bootstrap test (v0 vs agent, same items)
- **Why**: Statistical significance of +2.9pp on SeedVL
- **How**: Extend evaluate.py with paired bootstrap
- **Effort**: 1h

### E4. Descriptor ablation table
- **What**: Show old_descriptor → new_descriptor AUROC per domain per backbone
- **Why**: C1 (descriptor) is the main claim, needs systematic evidence
- **How**: Already have gpt54 old-desc test (0.754) and new-desc (0.825). Need SeedVL/Qwen old-desc baselines.
- **Effort**: 4h (need to rerun v0 with old descriptors on SeedVL/Qwen)

### E5. VLM/Expert complementarity matrix
- **What**: 2×2 table per domain: VLM correct+expert correct / VLM wrong+expert correct / etc.
- **Why**: Shows WHERE the agent adds value (expert catches VLM misses)
- **How**: Post-hoc from existing results
- **Effort**: 2h

## Priority 2: Writing Improvements (important but not blocking)

### W1. Architecture figure (Figure 1)
- **What**: Perceive → Expert → Adaptive Route diagram with 4 routes
- **How**: Mermaid or TikZ
- **Effort**: 1h

### W2. Per-domain comparison bar chart (Figure 2)
- **What**: Grouped bars showing DINOv2 vs SubspaceAD vs v0 vs AnomalyClaw per domain
- **How**: matplotlib from test JSON data
- **Effort**: 30min

### W3. Routing distribution figure (Figure 3)
- **What**: Stacked bar showing agree/trust/interpret per domain
- **How**: matplotlib from agent raw_output
- **Effort**: 30min

### W4. Fix placeholder citations
- **What**: Replace [placeholder_*] with real BibTeX entries
- **How**: Search Semantic Scholar / arXiv
- **Effort**: 2h

### W5. Introduction rewrite for AnomalyClaw framing
- **What**: Current intro still has EGRA language. Rewrite for AnomalyClaw + 3 failure modes
- **Effort**: 1h

## Priority 3: Future Experiments (nice to have, not blocking)

### F1. Component-enumeration tool improvement
- **Current**: 60% accuracy on D10 logical with 4 refs
- **Plan**: Detection (GroundingDINO) → Crop → Count → Compare pipeline
- **Expected**: 75%+ accuracy
- **Effort**: 8h

### F2. Multi-expert adaptive selection
- **Current**: SubspaceAD for all domains
- **Plan**: Agent learns which expert per item from calibration features (not domain labels)
- **Expected**: +1-2pp from using DINOv2-PatchNN on D03 infrastructure
- **Effort**: 4h

### F3. Larger calibration set
- **Current**: 20 items/domain (too small for reliable threshold calibration)
- **Plan**: Use dev split (40 items) as extended calibration
- **Expected**: Better threshold transfer → stronger test results
- **Effort**: 8h (rerun all experiments)

## Execution Order

1. **Today**: E3 (bootstrap CIs, 1h) + E5 (complementarity matrix, 2h) + E2 (budget baselines, 2h)
2. **Tomorrow AM**: W1-W3 (figures, 2h) + W5 (intro rewrite, 1h) + W4 (citations, 2h)
3. **Tomorrow PM**: E1 result → fill Table 2 → E4 (descriptor ablation, 4h)
4. **Day 3**: F1 (enumerate improvement) + F2 (multi-expert) if time permits
5. **Day 4**: Final codex R2 review → fix → submit
