# Literature Review: VLM Agent Systems for Visual Anomaly Detection (2025-2026)

**Date**: 2026-03-31 | **Focus**: Last 2 months + key 2025 works

---

## 1. Landscape Overview

### The field is organized around 4 axes:

| Axis | Key Papers | Trend |
|------|-----------|-------|
| **VLM as AD detector** | AnomalyGPT, Anomaly-OV, IADGPT, MoXpert | Fine-tuned VLMs for industrial AD |
| **Agent-based AD** | AgentIAD, AutoIAD, AD-Copilot, EAGLE | **Hottest area** (4 papers in 4 months) |
| **Multi-agent debate** | DMAD, M3MAD-Bench, VipAct, AlignVQA | Maturing, but **NOT yet applied to AD** |
| **Benchmarks** | MMAD, ADNet, M3-AD, BMAD | MMAD is de facto standard |

---

## 2. Most Important Papers (Ranked by Relevance to AnomaClaw)

### Tier 1: Direct Competitors / Must-Read

| Paper | Venue | Method | Key Insight for Us |
|-------|-------|--------|-------------------|
| **AD-Copilot** | arXiv Mar 2026 | Comparison Encoder + Chat-AD 620K dataset | **82.3% on MMAD** (current SOTA). Uses visual in-context comparison. Our closest competitor. |
| **AgentIAD** | arXiv Dec 2025 | Single agent + 2 tools (Perceptive Zoomer + Comparative Retriever) | Tool-augmented CoT reasoning. SFT+GRPO training. Best binary accuracy on MMAD. |
| **EAGLE** | arXiv Feb 2026 | PatchCore expert → visual+text prompts → frozen MLLM | **Tuning-free**. Uses traditional AD model to guide VLM attention. |
| **MMAD** | ICLR 2025 | Benchmark: 7 subtasks, 39K QA, 8K images | **De facto IAD benchmark**. GPT-4o only 74.9%. |
| **Anomaly-OneVision** | CVPR 2025 Highlight | Look-Twice Feature Matching + specialist MLLM | **88.6% AUROC** zero-shot across 5 datasets. First specialist MLLM for ZSAD. |

### Tier 2: Important Context

| Paper | Venue | Method | Relevance |
|-------|-------|--------|-----------|
| **AutoIAD** | arXiv Aug 2025 | Manager + sub-agents for full IAD pipeline | Multi-agent for pipeline construction, not for reasoning |
| **MoXpert** | Pattern Recog. 2025 | Gated MoE (4 experts) for MMAD | +7.4% on MVTec. Shows MoE architecture works for IAD |
| **M3MAD-Bench** | arXiv Jan 2026 | Benchmark for multi-agent debate | **"Collective delusion" is main failure mode**. Diverse teams help. |
| **VipAct** | AAAI 2026 | Orchestrator + specialized agents + tools | System-2 reasoning for visual perception. 90.8% on depth tasks. |
| **DMAD** | ICLR 2025 | Diverse reasoning approaches break "fixed mental set" | Diverse agents outperform uniform ones in fewer rounds |
| **ADNet** | arXiv Nov 2025 | 380 categories, 49 datasets, 196K images | Largest multi-domain AD benchmark. Shows SOTA drops from 90.6% to 78.5% |

### Tier 3: Relevant Technical References

| Paper | Venue | Method | Relevance |
|-------|-------|--------|-----------|
| **VERA** | CVPR 2025 | Verbalized learning for video AD | Learns guiding questions to decompose "anomaly" |
| **PromptMoE** | AAAI 2026 | Expert prompt MoE for ZSAD | Dynamic per-instance prompt composition on CLIP |
| **VisualAD** | CVPR 2026 | Language-free zero-shot AD | Removes text encoder entirely, pure vision |
| **FoundAD** | ICLR 2026 | DINOv3-based few-shot AD | Nonlinear projection onto natural image manifold |
| **Few-Shot Inspection** | VISAPP 2025 | ViP-LLaVA + ICL | Fine-tuned on 941 images, provides defect coordinates |
| **EMIT** | arXiv Jul 2025 | Difficulty-aware GRPO for IAD | +7.77% on MMAD over InternVL3-8B |
| **Debating for VLMs** | EMNLP 2025 | Debate protocols for VQA | Fine-tuning on debate traces improves reasoning |

---

## 3. Gap Analysis: Where AnomaClaw Fits

### What EXISTS:
1. **VLM as AD detector** — well-explored (AnomalyGPT, Anomaly-OV, etc.)
2. **Single-agent + tools** — AgentIAD (zoom + retrieve)
3. **Pipeline automation** — AutoIAD (multi-agent but for training pipeline, not reasoning)
4. **Multi-agent debate for VQA** — DMAD, M3MAD-Bench (general reasoning, not AD)

### What does NOT exist (our gap):
1. **Multi-agent debate/collaboration specifically for visual AD** — NO paper does this
2. **Cross-domain AD benchmark for VLM agents** — MMAD is QA-focused, not binary AD
3. **Few-shot reference scaling ablation** — nobody studies k=2 vs k=4 vs k=8
4. **Agent-based normal distribution profiling** — our V5 concept is novel
5. **Domain-adaptive agent reasoning for AD** — no paper customizes agent behavior per domain

### Direct competition analysis:

| System | vs AnomaClaw | Their Advantage | Our Advantage |
|--------|-------------|-----------------|---------------|
| AD-Copilot | Closest competitor | 82.3% MMAD, fine-tuned Comparison Encoder | We're tuning-free, multi-domain, agent-based |
| AgentIAD | Single-agent + tools | SFT+GRPO trained, tool-augmented | We use multi-agent debate (richer reasoning) |
| EAGLE | Tuning-free guidance | PatchCore expert guidance | We don't need a pre-trained AD model |
| AutoIAD | Multi-agent | Pipeline automation | We do reasoning, not pipeline construction |
| MMAD benchmark | Our eval target | Established benchmark, 7 subtasks | We offer cross-domain binary AD focus |

---

## 4. Key Takeaways for AnomaClaw Design

### From the literature:

1. **Tool-augmented agents win**: AgentIAD's Perceptive Zoomer (crop suspicious regions) and Comparative Retriever (retrieve normal refs) → we should consider similar tools
2. **Debate needs diversity**: M3MAD-Bench shows "collective delusion" when agents agree too easily. DMAD shows diverse reasoning styles help.
3. **MMAD is the benchmark to beat**: We need to evaluate on MMAD for credibility
4. **Few-shot context is powerful**: Multiple papers show k-shot references significantly help VLMs
5. **Domain-specific prompting matters**: Papers like VERA learn domain-specific "guiding questions"

### Suggested AnomaClaw architecture (refined):

```
Phase 1: Domain Profiling Agent
  - Analyzes k normal references
  - Outputs domain-specific "what to look for" profile
  
Phase 2: Multi-Agent Inspection
  - Advocate Agent: Identifies all potential anomalies (with zooming tool)
  - Skeptic Agent: Challenges each claim with domain knowledge from Profile
  - Judge Agent: Synthesizes debate into final verdict
  
Phase 3: Confidence Calibration
  - Uses reference comparison for confidence scoring
```

This is differentiated from:
- AgentIAD (single agent, no debate)
- AD-Copilot (no agent architecture, just fine-tuned model)
- EAGLE (no agent, just expert guidance)
- AutoIAD (pipeline agent, not reasoning agent)

---

## 5. Datasets Mentioned by User

### BMAD (Benchmarks for Medical AD)
- **Paper**: Bao et al., arXiv 2306.11876
- **Datasets**: BraTS2021 (Brain), BTCV+LiTS (Liver), RESC+OCT2017 (Retinal), **RSNA (Chest X-ray)**, Camelyon16 (Histopath)
- **Download**: Google Drive (needs proxy)
- **For us**: RSNA Chest X-ray is much cleaner than CheXpert for D5

### UniMMAD (Unified Multi-Modal Multi-Class AD)
- **Benchmarks used**: MVTec-3D, Eyecandies, MulSen-AD, BraTs, UniMed
- **For us**: Good comparison targets for traditional model baselines

### Dinomaly2 (Detect Them All)
- **Paper**: Unified framework for full-spectrum unsupervised AD
- **For us**: Strong traditional baseline to compare against

---

## 6. Publication Strategy Implications

### Positioning options:
1. **"First multi-agent debate system for cross-domain visual AD"** — true, nothing exists
2. **"Agent-based few-shot AD with domain profiling"** — our V5 concept is novel
3. **"Cross-domain AD benchmark for VLM agents"** — ADNet exists but is for traditional methods, not VLM agents

### Target venues (2026 deadlines):
- NeurIPS 2026 (May deadline)
- AAAI 2027 (Aug deadline)
- ICLR 2027 (Oct deadline)

### Must-cite papers:
1. MMAD (ICLR 2025) — benchmark
2. AD-Copilot (2026) — closest competitor
3. AgentIAD (2025) — agent-based AD
4. DMAD (ICLR 2025) — multi-agent debate
5. Anomaly-OV (CVPR 2025) — zero-shot AD with VLM
