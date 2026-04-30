# Literature Survey: Universal Visual Anomaly Detection Agent

**Date**: 2026-03-30
**Topic**: MLLM-based universal visual anomaly detection agent + active learning

---

## Landscape Summary

The MLLM-based anomaly detection field (2024-2026) has three major tracks:

1. **MLLM-based Industrial AD** (crowded): Fine-tuning or prompting MLLMs for industrial defect detection on MMAD/MVTec. Dominated by GRPO/SFT approaches (AnomalyR1, OmniAD, EMIT). AgentIAD claims 97.62% on MMAD but is essentially tool-augmented single-model inference, not a genuine agentic system.

2. **Universal/Cross-Domain AD** (emerging): UniVAD (CVPR 2025) is training-free and works across 9 datasets (industrial/logical/medical) using classical patch matching — no MLLM reasoning. No one has built a cross-domain MLLM agent.

3. **Agent Reasoning + Active Learning for AD** (nearly empty): Multi-agent debate exists for NLP reasoning. NearCAIPI (ECCV 2024 WS) is the only AL work for visual AD. No one combines agent reasoning with human-in-the-loop feedback for visual AD.

---

## Key Papers

### Track 1: MLLM-Based Industrial AD

| Paper | Venue | Method | MMAD Acc | Notes |
|-------|-------|--------|----------|-------|
| AnomalyGPT | AAAI 2024 | VLM fine-tuning | ~45% | Pioneer, industrial only |
| MMAD Benchmark | ICLR 2025 | Evaluation protocol | GPT-4o: 74.9% | Benchmark, not method |
| AgentIAD | arXiv 2025 | Tool-augmented model (Zoomer+Retriever) | 97.62% | Not a real agent, needs SFT+RL |
| AnomalyR1 | arXiv 2025 | GRPO end-to-end | — | Needs fine-tuning |
| OmniAD | arXiv 2025 | GRPO + patch localization | — | Industrial only |
| AD-Copilot | arXiv 2026 | Visual in-context comparison | 82.3% | Needs custom training |
| SAGE | ACM MM 2025 | Fact enhancement + E-DPO | — | Industrial focus |
| Judo | ICLR 2026 | Domain-oriented reasoning | — | Industrial QA |
| EMIT | arXiv 2025 | Difficulty-aware GRPO | — | Needs fine-tuning |
| MoXpert/Echo | PR 2025 | Multi-expert (4 modules) | — | Complex architecture |

### Track 2: Universal/Cross-Domain AD

| Paper | Venue | Method | Domains | Notes |
|-------|-------|--------|---------|-------|
| UniVAD | CVPR 2025 | Training-free clustering + patch matching | Industrial, logical, medical (9 datasets) | No MLLM, no agent |
| AD-FM | arXiv 2025 | Multi-stage reasoning + reward | Cross-dataset | Needs reward training |
| UMAD | arXiv 2024 | Benchmark | Multi-domain | No method |
| ADFM Workshop | ICCV 2025 | Community workshop | Multi-domain | Standardization effort |

### Track 3: Agent Reasoning & Active Learning

| Paper | Venue | Method | Notes |
|-------|-------|--------|-------|
| Multi-agent Debate | ICML 2024 | LLM debate for factuality | Not visual/AD |
| NearCAIPI | ECCV 2024 WS | AL for IAD | No agent, workshop only |
| ALPHA | 2025 | LLM-enabled AL for network AD | Not visual |

### Backbone Models

| Model | Architecture | Strength |
|-------|-------------|----------|
| GPT-4o/4.1 | Closed-source | Most general multimodal reasoning |
| Seed1.5-VL | 532M vision encoder + 20B MoE LLM | Fine-grained visual, native resolution, SOTA 38/60 benchmarks |

---

## Structural Gaps

1. **No training-free universal AD agent**: UniVAD is cross-domain but classical; all MLLM methods are industrial-only.
2. **No genuine agent system for AD**: AgentIAD is tool-augmented inference, not real multi-round reasoning.
3. **No cross-domain MLLM AD comparison**: Nobody compares GPT vs. specialized VLMs across diverse AD domains.
4. **Active learning + MLLM agent = empty niche**: NearCAIPI is the only AL for visual AD, with no agent component.
5. **No standardized cross-domain AD benchmark for MLLM agents**: Existing benchmarks are domain-specific.

---

## Opportunity

The intersection of (1) training-free cross-domain AD, (2) genuine agent-based reasoning, and (3) human-in-the-loop active learning is completely unoccupied. A universal AD agent tested across 8+ domains with GPT/SeedVL backends would be the first of its kind. If existing benchmarks are too large, a carefully sampled cross-domain benchmark would itself be a contribution.
