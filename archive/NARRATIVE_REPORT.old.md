# AnomalyClaw: Training-Free Cross-Domain Visual Anomaly Detection via Expert-Grounded Adaptive Reasoning

## Research Question
Can a training-free agent that adaptively combines VLM reasoning with non-parametric expert evidence outperform single-pass VLM prompting for cross-domain visual anomaly detection?

## Key Claims

### Claim 1: Task-anchored domain descriptors are the dominant contribution
- **Evidence**: GPT-5.4 v0 test AUROC improves from 0.754 (generic descriptors) to 0.825 (task-anchored descriptors), a +7.1pp gain across 11 domains.
- **Per-domain**: D08 LEVIR building change +33pp (0.496→0.827), D06 liver CT +31pp (0.433→0.745), D08 surveillance +12pp.
- **Root cause discovered**: D08 was LEVIR-CD+ (building change detection), not xBD disaster damage. The original descriptor told VLM to look for "collapsed buildings" when the actual anomaly was "new construction."
- **This finding is backbone-independent**: all three VLMs (GPT-5.4, SeedVL, Qwen3.5) benefit.

### Claim 2: AnomalyClaw agent improves non-frontier backbones
- **SeedVL**: agent test macro 0.818 vs v0 0.789 = **+2.9pp**, 9/11 domains improved.
- **GPT-5.4**: agent test macro 0.826 vs v0 0.825 = +0.1pp (matches frontier baseline).
- **Interpretation**: The agent's marginal value scales inversely with backbone strength. It helps most where v0 has room to improve.

### Claim 3: Expert-VLM complementarity is real and exploitable
- **SubspaceAD** (DINOv2-giant + PCA, training-free) reaches 1.000 AUROC on D11 VisA calibration where best VLM is 0.85.
- **VLM** dominates on semantic domains: D07 endoscopy 0.88 vs SubspaceAD 0.53, D08 LEVIR 0.83 vs 0.46.
- **Oracle** (max per domain): macro 0.898 — showing 7pp headroom above current best.
- **AnomalyClaw** exploits this by running both, using disagreement as the escalation signal.

### Claim 4: Debate-style agents uniformly fail
- v1 Normal-First: -3.6pp on Qwen3.5 (structured prompt overwhelms token budget).
- v2 Self-Refine: worse than v1 (more calls ≠ better).
- v3 Debate: -5.6pp on SeedVL (refuter rationalises correct predictions).
- EGRA (per-item escalation to debate): calibration +2.2pp → test +0.3pp (doesn't transfer).
- Evidence injection into proposer: -6pp (distracts VLM).
- Third-call arbiter: fires 66%, net negative.

### Claim 5: Asymmetric escalation is the key design principle
- Only escalate when VLM says NORMAL but expert says ANOMALY (FN-catcher).
- Never override VLM's anomaly predictions (they're usually correct).
- This asymmetry prevents the dominant failure mode: flipping confident correct answers.

## Quantitative Results

### Main Table (test split, 11 domains, excl D8 Avenue, n=1298)

| Method | GPT-5.4 | SeedVL | Qwen3.5 |
|--------|---------|--------|---------|
| DINOv2-PatchNN | 0.640 | 0.640 | 0.640 |
| SubspaceAD | 0.756 | 0.756 | 0.756 |
| v0 Direct (descriptors) | 0.825 | 0.789 | 0.792 |
| **AnomalyClaw** | **0.826** | **0.818** | pending |

### SeedVL Per-Domain (test, where agent gains are largest)

| Domain | DINOv2 | SubspaceAD | v0 | AnomalyClaw | Δ |
|--------|--------|------------|-----|-------------|---|
| D01 Industrial | 0.69 | 0.97 | 0.87 | 0.95 | +8pp |
| D02 Retail | 0.62 | 0.84 | 0.86 | 0.89 | +3pp |
| D03 Infrastructure | 0.80 | 0.70 | 0.66 | 0.72 | +6pp |
| D06 Liver CT | 0.68 | 0.70 | 0.49 | 0.56 | +7pp |
| D10 Logical | 0.62 | 0.66 | 0.65 | 0.71 | +6pp |
| D11 VisA | 0.60 | 0.91 | 0.88 | 0.91 | +3pp |

### Calibration Ablation (GPT-5.4, n=240)

| Variant | Calibration macro | Note |
|---------|------------------|------|
| v0 Direct | 0.785 | Baseline |
| v1 Normal-First | 0.761 | -2.4pp |
| v2 Self-Refine | 0.726 | -5.9pp |
| v3 Debate (naive) | 0.713 | -7.2pp |
| v3 Debate (gated) | 0.744 | -4.1pp |
| AnomalyClaw v1 | **0.837** | **+5.2pp** |

### Expert Benchmark (calibration, macro AUROC)
- SubspaceAD: 0.766 (strong on D01/D11/D05/D09, fails on D03/D08)
- AnomalyVFM: 0.599 (uniformly weak, dropped)
- DINOv2-PatchNN: 0.640 (strong on D03/D09)

## Architecture

```
Phase 1: PERCEIVE (1 VLM call)
  VLM v0 with task-anchored descriptor → label, confidence, score

Phase 2: EXPERT (0 VLM calls)  
  SubspaceAD (DINOv2-giant PCA on references) → anomaly score, top-k patches
  DINOv2 Patch-kNN → patch distances, baseline

Phase 3: ADAPTIVE ROUTE (0 or 1 VLM call)
  Compute signals: ρ (relative anomaly), κ (patch concentration)
  Route A: Agree (v0 and expert same label) → commit [~63%]
  Route B: Trust Expert (strong concentrated signal) → blend [~4%]
  Route C: Enumerate (strong dispersed signal) → component comparison [prototype]
  Route D: Interpret (moderate signal) → VLM re-examines with evidence [~33%]
```

Average: 1.33 VLM calls per image.

## Figures Needed
1. **Figure 1**: Architecture diagram showing Perceive → Expert → Adaptive Route
2. **Figure 2**: Per-domain AUROC comparison (v0 vs AnomalyClaw vs experts), grouped bar chart
3. **Figure 3**: Expert-VLM complementarity heatmap (which method wins per domain)
4. **Figure 4**: Routing distribution per domain (stacked bar)
5. **Table 1**: Benchmark composition (11 domains)
6. **Table 2**: Main results (3 backbones × methods)
7. **Table 3**: Per-domain breakdown (SeedVL)
8. **Table 4**: Ablation of failed variants

## Benchmark
- **Name**: CrossDomainVAD-11
- **Domains**: 11 (industrial ×2, retail, infrastructure, medical ×4, remote sensing, road, logical)
- **Total test items**: 1,298 (excl D8 Avenue, behavioral anomaly out of scope)
- **Protocol**: calibration (20/domain) → dev (40) → test (120), frozen splits
- **Reference-based**: each query has 1-10 normal reference images
- **Spec**: benchmark/BENCHMARK_SPEC.json

## Key Technical Contributions
1. Task-anchored domain descriptors (+7pp, the dominant finding)
2. AnomalyClaw agent: Perceive → Expert → Adaptive Route architecture
3. CrossDomainVAD-11 benchmark (11 domains, 1,298 test items)
4. Comprehensive ablation of 6 failed agent variants (negative findings)
5. Expert-VLM complementarity analysis (SubspaceAD vs VLM per domain)
