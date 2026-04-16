# Paper Plan

**Title**: AnomalyClaw: Training-Free Cross-Domain Visual Anomaly Detection via Expert-Grounded Adaptive Reasoning
**One-sentence contribution**: AnomalyClaw is a training-free agent that adaptively combines VLM single-pass reasoning with non-parametric patch-level expert evidence through a disagreement-triggered interpret mechanism, achieving +2.9pp macro AUROC over single-pass VLM on an 11-domain cross-domain benchmark while demonstrating that task-anchored domain descriptors alone provide the dominant +7.1pp improvement.
**Venue**: ICLR 2026
**Type**: Method + Empirical (diagnostic)
**Date**: 2026-04-13
**Page budget**: 9 pages (main body to Conclusion end, excluding references & appendix)
**Section count**: 6

## Claims-Evidence Matrix

| Claim | Evidence | Status | Section |
|-------|----------|--------|---------|
| C1: Task-anchored descriptors +7.1pp | GPT-5.4 test 0.754→0.825; D08 +33pp, D06 +31pp | Fully supported | §3.2, §4.1 |
| C2: AnomalyClaw improves non-frontier VLMs | SeedVL +2.9pp (9/11 domains); GPT tie | Fully supported | §4.2 |
| C3: Expert-VLM complementarity exploitable | SubspaceAD 1.000 on D11 vs VLM 0.85; oracle 0.898 | Fully supported | §3.4, §4.4 |
| C4: Debate/refuter agents uniformly fail | 6 variants tested, all ≤v0 on test | Fully supported | §4.3 |
| C5: Asymmetric escalation is key | FN-catcher only; never flip VLM anomaly calls | Supported by design | §3.3 |

## Structure

### §0 Abstract (150-250 words)
- **What**: AnomalyClaw agent for cross-domain training-free VAD
- **Why hard**: VLMs fail silently on domains where world-knowledge conflicts with task definition
- **How**: Perceive (v0) → Expert (SubspaceAD) → Adaptive Route (4 routes)
- **Result**: SeedVL +2.9pp, GPT tie; descriptors alone +7.1pp
- **Remarkable**: 11-domain benchmark; 6 failed agent variants documented

### §1 Introduction (1.5 pages)
- **Hook**: VLMs as default zero-shot VAD tool, but single-pass conflates 3 failure modes
- **Gap**: Prior agentic VAD adds complexity without reliable gains (debate hurts -5.6pp)
- **Contribution**: AnomalyClaw + descriptors + benchmark + negative findings
- **Hero figure**: Fig 1 — architecture diagram + per-domain comparison (v0 vs AnomalyClaw vs expert)
- **Key citations**: MMAD, AgentIAD, EAGLE, PatchCore, WinCLIP, SubspaceAD

### §2 Related Work (1 page)
- Classical training-free AD (PatchCore, WinCLIP, AnomalyCLIP)
- VLM-based AD (AnomalyGPT, MMAD)
- Agentic AD (AgentIAD, EAGLE, AutoIAD)
- Self-refinement and debate (general LLM literature)
- Cross-domain benchmarks

### §3 Method (2 pages)
- §3.1 Overview (Perceive → Expert → Route)
- §3.2 Task-anchored descriptors
- §3.3 Adaptive routing (ρ, κ signals + v0 confidence gate)
- §3.4 Expert pool (SubspaceAD + DINOv2-PatchNN)
- §3.5 Algorithm pseudocode + design principles
- §3.6 Component enumeration tool (prototype for logical anomaly)

### §4 Experiments (3 pages)
- §4.1 Setup (benchmark, backbones, baselines, metrics)
- §4.2 Main results (Table 2: 3 backbones × methods)
- §4.3 Per-domain analysis (Table 3: SeedVL breakdown)
- §4.4 Ablation: why simpler agents fail (6 variants)
- §4.5 Expert analysis (SubspaceAD vs AnomalyVFM vs DINOv2)
- §4.6 Routing behaviour

### §5 Conclusion (0.5 pages)
- Restate: descriptors are dominant; agent helps weaker backbones
- Limitations: GPT tie; enumerate 60%; calibration threshold transfer
- Future: larger calibration; better routing; detection-based counting

## Figure Plan

| ID | Type | Description | Data Source | Priority |
|----|------|-------------|-------------|----------|
| Fig 1 | Architecture | AnomalyClaw pipeline: Perceive→Expert→Route with 4 routes | manual/mermaid | HIGH |
| Fig 2 | Grouped bar | Per-domain AUROC: v0 vs AnomalyClaw vs SubspaceAD (SeedVL) | test results JSON | HIGH |
| Fig 3 | Heatmap | Expert-VLM complementarity: which method wins per domain per backbone | calibration JSONs | MEDIUM |
| Fig 4 | Stacked bar | Routing distribution per domain (agree/trust/enumerate/interpret) | agent raw_output | MEDIUM |
| Table 1 | Table | Benchmark composition (11 domains) | BENCHMARK_SPEC.json | HIGH |
| Table 2 | Table | Main results: 3 backbones × {DINOv2, SubspaceAD, v0, AnomalyClaw} | test JSONs | HIGH |
| Table 3 | Table | Per-domain SeedVL breakdown | test JSON | HIGH |
| Table 4 | Table | Ablation of 6 failed variants | calibration JSONs | HIGH |

## Citation Plan
- §1: MMAD, PatchCore, WinCLIP, AnomalyGPT [problem motivation]
- §2: AgentIAD, EAGLE, AutoIAD [agentic AD]; SubspaceAD, AnomalyCLIP [few-shot/zero-shot]; MVTec-AD, VisA, MVTec-LOCO [benchmarks]; Self-Refine, LLM Debate [general]
- §3: SubspaceAD [expert]; DINOv2 [backbone]; TAB, GroundingAgent [tool-use agent inspiration]
- §4: benchmarks cited per domain source dataset

## Next Steps
- [ ] /paper-figure to generate Fig 2, 3, 4 and Tables
- [ ] /paper-write to polish existing LaTeX
- [ ] /paper-compile to build PDF
- [ ] /auto-paper-improvement-loop with codex exec review
