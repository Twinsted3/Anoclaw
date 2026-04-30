# AnomaClaw — Literature Survey
**Date:** 2026-03-16

---

## 1. Agent-Based IAD Systems

| Paper | Venue | Method | Key Result | Limitation |
|-------|-------|--------|------------|-----------|
| AgentIAD (arXiv:2512.13671) | 2025.12 | Single-agent, Perceptive Zoomer + Comparative Retriever, SFT+GRPO | 97.62% Acc on MMAD | Structured CoT only; no planning/reflection/memory; fixed tool set |
| AutoIAD (arXiv:2508.05503) | 2025.08 | Manager agent + Data/Loader/Designer/Trainer sub-agents, AutoML pipeline | SOTA AUROC on MVTec | No reasoning-time agent; AutoML paradigm; no deployment-time loop |
| AD-AGENT (arXiv:2505.12594) | 2025.05 | Multi-agent, NL→AD pipeline (PyOD/PyGOD/TSLib), shared workspace | Reliable scripts on tabular/graph/time-series | Not visual IAD; offline pipeline building |
| AnomaMind (arXiv:2602.13807) | 2026.02 | Agentic time-series AD, coarse-to-fine, tool-augmented + RL | Consistent improvement on TS benchmarks | Time-series only; no visual IAD |
| AnomalyR1 (arXiv:2504.11914) | 2025.04 | VLM + GRPO, ROAM metric, segmentation mask output | SOTA on MMAD (3B model) | No agent loop; single-pass; no human feedback |
| EMIT (arXiv:2507.21619) | 2025.07 | Difficulty-aware GRPO on InternVL3-8B | +7.77% on MMAD | Discriminative training; no reasoning chain |
| OmniAD (arXiv:2505.22039) | 2025.05 | Multimodal reasoning for IAD | 79.1 on MMAD, beats GPT-4o | No agent loop |

**Key gap:** No system has Planning + Reflection + Memory as a complete IAD agent loop.

---

## 2. Active Learning for IAD / Visual Inspection

| Paper | Venue | Scenario | Key Idea | Gap |
|-------|-------|----------|----------|-----|
| NearCAIPI | ECCV 2024 Workshop | Visual IAD (RGB) | Interactive ML + AL sample selection + explainable feedback | Workshop only; not on MVTec/VisA main benchmarks |
| LEIAD (arXiv:2212.14621) | 2022 | Industrial time-series | Weak supervision + AL with minimal user interactions | Time-series; not visual |
| AL + Industrial Time Series (FSMJ 2025) | FSMJ 2025 | Industrial time-series | Autoencoder latent space + budget-constrained expert feedback | Not visual IAD |
| Few-shot + AL Defect Detection (IJPR 2024) | IJPR 2024 | Manufacturing visual | AL to select few-shot support set | Non-standard benchmark |
| Explainable IAD for IoT (arXiv:2512.08885) | SAC 2026 | Industrial IoT | Interactive online isolation forest; human adjusts thresholds | IoT/tabular; not visual patch-level IAD |

**Key gap:** **Zero** papers on active learning specifically designed for MVTec AD / VisA image-level benchmarks at top venues.

---

## 3. Memory Banks & Non-Parametric Retrieval for IAD

| Paper | Venue | Method | Relevance |
|-------|-------|--------|-----------|
| PatchCore (CVPR 2022) | CVPR 2022 | Coreset memory bank from pretrained features | Foundational; our memory builds on this paradigm |
| MRAD (arXiv:2602.00522) | 2026.02 | Frozen CLIP + two-level memory bank (image+pixel), train-free | Direct motivation: retrieval replaces parametric model |
| TMUAD (arXiv:2508.21795) | 2025.08 | 3-memory framework: class text + object image + patch features | Multi-granularity memory for structural+logical anomalies |
| FastRef (arXiv:2506.21398) | 2025.06 | Fast prototype refinement for few-shot IAD; integrates PatchCore/WinCLIP | Few-shot prototype memory; supports 1/2/4-shot |

**Key opportunity:** Existing memory banks are **static** (built once). No work builds **dynamically-updated** non-parametric memory from human-in-the-loop feedback.

---

## 4. Uncertainty / Confidence in MLLMs and Agents

- **Adaptive+Explainable AI Agents (arXiv:2510.03859):** LLM-supported XAI agents for IoT AD with memory buffers; uses attention for uncertainty — but IoT domain, not visual IAD.
- **Self-Evolving Multi-Agent (arXiv:2602.16738):** Hierarchical edge/fog/cloud agents for predictive maintenance; consensus voting for uncertainty aggregation — no agent-aware query strategy.
- **No paper** designs query strategies using agent reasoning traces (tool call patterns, reflection outputs, retrieval similarity scores) as uncertainty signals for active learning.

---

## 5. Benchmark Landscape

| Benchmark | Type | Scale | Usage |
|-----------|------|-------|-------|
| MVTec AD | 15 categories, 5354 test images | Industrial RGB | Standard IAD benchmark |
| VisA | 12 categories, 9621 images | Visual inspection | Harder, multi-instance |
| MMAD | 39,672 QA pairs, 8,366 images | MLLM evaluation | Agent/reasoning benchmark |
| MMAD-BBox | Extension of MMAD | Localization | Spatial grounding evaluation |

---

## 6. Landscape Narrative

The IAD field is undergoing a paradigm shift from traditional unsupervised methods (PatchCore, SPADE, RD4AD) toward MLLM-based reasoning. However, this shift has created a bifurcation: **reasoning-focused papers** optimize for MMAD benchmark accuracy, while **detection-focused papers** optimize for MVTec/VisA AUROC. Neither addresses real deployment scenarios where:

1. Models encounter **unknown defect types** not seen in training
2. **Budget-constrained human experts** can annotate a limited number of samples
3. The system should **improve continuously** from accumulated feedback

The closest work to our direction is AgentIAD, which adds tool-use to a VLM but remains fundamentally a structured CoT system (no state, no learning from feedback). NearCAIPI (ECCV 2024 Workshop) is the only work combining active learning with visual IAD, but it's unpublished at top venues and uses a simple uncertainty-based query strategy without agent signals.

**The intersection of (1) full agent reasoning loop + (2) active learning + (3) non-parametric memory update is completely unoccupied.**

---

## 7. Key Gaps Identified

1. **No agent with full P+R+M loop for visual IAD** (planning, reflection, memory all together)
2. **No AL protocol on MVTec/VisA** at top venues
3. **No agent-aware query strategy** — exploiting agent's own reasoning uncertainty
4. **No dynamic memory update** from human feedback (all existing memory banks are static)
5. **No benchmark** for measuring AL efficiency in visual IAD (budget vs. performance curve)
6. **No correction experience replay** — when agents make mistakes and get corrected, this knowledge isn't stored and reused
