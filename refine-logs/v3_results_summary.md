# Verbalized Self-Evolution v3 — Final Results

**Date**: 2026-04-22 (overnight run)
**Backbone**: Qwen3.5-VL-27B (4 DP replicas on GPU 0/1/2/7)
**Dataset**: CrossDomainVAD-11 manifests_v2 test split (12 domains, n=1418)

## Macro AUROC

| Variant | Macro | Δ vs Passive |
|---|---|---|
| Passive v9 (no rulebook) | 0.6685 | — |
| + Anchor (1-sentence task anchor) | 0.6885 | **+2.00 pp** |
| + L1 inv (ref-only invariants) | 0.6603 | −0.82 pp |
| + L2 cls (K=10 cluster-reflected) | **0.6958** | **+2.73 pp** |
| + L1+L2 (offline stack) | 0.6708 | +0.23 pp |

## Per-domain AUROC

| Dom | Source | Pass | +Anch | +L1inv | +L2cls | +L1+L2 |
|---|---|---:|---:|---:|---:|---:|
| D1 | MVTec-AD | 0.918 | 0.897 | 0.895 | 0.851 | 0.874 |
| D2 | GoodsAD | 0.598 | 0.574 | 0.577 | 0.639 | 0.672 |
| D3 | VisA | 0.783 | 0.811 | 0.819 | 0.748 | 0.812 |
| D4 | SDNET | 0.581 | 0.555 | 0.697 | **0.735** | 0.634 |
| D5 | MVTec-LOCO | 0.654 | 0.594 | 0.672 | 0.664 | 0.600 |
| D6 | Real3D-AD | 0.509 | 0.593 | 0.469 | 0.507 | 0.578 |
| D7 | LEVIR | 0.614 | 0.734 | 0.644 | **0.828** | 0.668 |
| D8 | DermaMNIST | 0.647 | 0.664 | 0.540 | 0.549 | 0.522 |
| D9 | BraTS | 0.720 | 0.722 | 0.661 | **0.825** | 0.682 |
| D10 | BMAD-Liver | 0.504 | 0.493 | 0.464 | 0.501 | 0.461 |
| D11 | HyperKvasir | 0.570 | **0.706** | 0.568 | 0.581 | 0.624 |
| D12 | BDD+RA | 0.924 | 0.921 | 0.917 | 0.922 | 0.923 |

## Per-domain Δ vs Passive

| Dom | +Anch | +L1inv | +L2cls | +L1+L2 |
|---|---:|---:|---:|---:|
| D1 | -2.0 | -2.3 | -6.7 | -4.4 |
| D2 | -2.4 | -2.2 | +4.1 | **+7.3** |
| D3 | +2.8 | **+3.5** | -3.5 | +2.9 |
| D4 | -2.7 | +11.6 | **+15.4** | +5.3 |
| D5 | -6.0 | +1.8 | +0.9 | -5.4 |
| D6 | **+8.4** | -3.9 | -0.1 | +7.0 |
| D7 | +12.0 | +3.0 | **+21.4** | +5.4 |
| D8 | +1.7 | -10.7 | -9.8 | -12.5 |
| D9 | +0.2 | -5.9 | **+10.5** | -3.8 |
| D10 | -1.1 | -3.9 | -0.3 | -4.3 |
| D11 | **+13.6** | -0.2 | +1.1 | +5.4 |
| D12 | -0.4 | -0.7 | -0.2 | -0.2 |

## Framework comparison (macro Δ vs Passive v9)

| Variant | v1 full-dump | v2 RAG-compressed | v3 invariant-L1 + cluster-L2 |
|---|---:|---:|---:|
| +L1 | -5.2 | -1.4 | -0.8 |
| +L2 | -0.6 | -1.2 | **+2.7** |
| +L1+L2 | -0.1 | -0.9 | +0.2 |

## Key findings

1. **Anchor is free lunch**: injecting a 1-sentence task anchor
   (from `domain_config.json` `description`+`anomaly_type` fields)
   gives +2.0 pp macro with zero oracle cost. Matches §4 Table 12
   descriptor finding. Biggest single-domain win on D11 GI endoscopy
   (+13.6 pp) where the anchor names "polyp/ulcer" concretely.

2. **L2 cluster rules beat per-item rules decisively**: by reflecting
   on the full batch of K=10 balanced FN+FP dev items, the reflector
   identifies 1–3 common patterns per side rather than 10 noisy
   per-item rules. Normal_tolerance rules are constrained to
   "specific feature, not blanket suppression". Net: +2.7 pp macro,
   with D7 satellite +21.4 pp and D9 brain MRI +10.5 pp as headlines.

3. **Self-supervised invariants have a domain-type boundary**:
   L1 extracts ref-verified invariants (count, symmetry, spatial
   layout, color, texture, structural). Works on MVTec-LOCO
   logical (D5 +1.8), VisA (D3 +3.5), SDNET cracks (D4 +11.6).
   Fails on medical subtlety (D8 −10.7, D9 −5.9, D10 −3.9) where
   "normal" is a statistical distribution not an extractable
   invariant. L1 macro is net negative (−0.8 pp).

4. **Stacking does not help on average**: L1+L2 = +0.2 pp (nearly
   zero) because L1's low-confidence invariants on medical domains
   dilute L2's oracle-grounded signal. Best single strategy is
   L2 alone (+2.7 pp).

5. **Parse-failure rate stable at ~1-5%** across all v3 variants
   (down from v1's 10-24%). Compression + brief markdown list is
   more schema-friendly than dumped JSON.

## Implementation artifacts

- Code: `benchmark/scripts/verbalized_v3.py`
- Rulebooks: `benchmark/results/verbalized/v3_l1/*.json`,
  `benchmark/results/verbalized/v3_l2/*.json`
- Eval: `benchmark/results/verbalized/v3_eval_{anchor,l1,l2,l1l2}/*.json`
- Passive baseline: `benchmark/results/verbalized/passive_test/*.json`

## Deferred / future

- Bootstrap CI on macro Δ (compute ~10min each)
- Stratification breakdown by (structural vs medical vs satellite)
  domain type — the paper narrative already writes itself from the
  per-domain table
- Writing §5 paper section with the new numbers
- Round 4 codex review on the filled §5
