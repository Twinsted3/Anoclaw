# AnomaClaw — Research Idea Report
我们做的是视觉异常检测的通用智能体,分为三个部分.第一个是tools,包含很多,比如物体识别的tool,通用的检索参考图的tool,检索领域知识的tool(对于需要知识的领域比如医疗),分割物体的tool(对  
  于多物体的样例比如MVTec-LOCO),计数的tool,Crop的tool(对于背景过多的),等等,通用的和专用的都可以,并且可拓展.                                                                          
  第二个部分是expert,包括多种模型,工业的zero-shot和few-shot,医疗领域的zero-shot和few-shot,等等,不过数量不能太多且每个都需要前期验证一下.最后一个部分是多种处理方案,比如直接VLM判断,  
  或者现在文章里写的VLM和expert做fusion,再或者我们实验过的debate机制,然后还有主动学习机制(这个先不用实验).                                                                           
  然后我们的智能体要学会自主调用和组合,我们的实验其实就是先找到对于不同领域的不同数据最佳的组合,然后调式智能体能够自主生成对应的组合(其实就是把prompt或者skill写清楚).不过我们文章不 
  能这么写,不能说我们是调出来的,而要根据最后的设计说我们这么设计的理由(可以反推出来).
维护一个RAG库,在运行过程中把正常的知识总结进去
  
**Direction**: Agent + Active Learning for Industrial Anomaly Detection
**Generated**: 2026-03-16
**System**: 9× NVIDIA RTX A6000 GPUs
**Existing codebase**: Multi-round Skeptic-Verifier agent system on MMAD benchmark
**Ideas evaluated**: 10 generated → 8 survived filtering → 3 piloted → **1 recommended (full system) + 2 backups**

---

## Landscape Summary

The IAD field in 2025-2026 is dominated by two parallel tracks: (1) MLLM-based reasoning (optimizing MMAD accuracy via SFT+GRPO), and (2) classical unsupervised detection (PatchCore/WinCLIP variants, optimizing MVTec AUROC). Neither track addresses the **deployment gap**: after a model is deployed, it encounters unknown defect types, misses hard cases, and has no mechanism to improve from rare but valuable human annotations.

The multi-round Skeptic-Verifier system already in this codebase is a strong foundation — it implements iterative reasoning via External Skeptic + Internal Verifier. What it lacks is (a) a **confidence signal to decide when to stop vs. query a human**, and (b) a mechanism to **store and reuse human feedback** without retraining.

Active learning for visual IAD is a near-empty field: NearCAIPI (ECCV 2024 Workshop) is the only paper. All existing memory banks (PatchCore, MRAD, TMUAD) are **static** — no one has built a dynamically-updated non-parametric memory from human annotations. This is AnomaClaw's core opportunity.

The existing Skeptic-Verifier system provides a unique advantage: the **reasoning trace** contains rich uncertainty signals (number of debate rounds, whether verifier reached consensus, semantic hesitation tokens) that can drive a far more informative query strategy than simple uncertainty sampling.

---

## Recommended Ideas (ranked)

---

### 🏆 Idea 1: **AnomaClaw** — Full System Paper
*Agent-Aware Active Learning for IAD with Tri-Layer Non-Parametric Memory*

- **Hypothesis**: An IAD agent equipped with (1) reasoning-trace-based query strategy and (2) tri-layer non-parametric memory can achieve state-of-the-art performance on MVTec AD/VisA under limited annotation budgets, with monotonically improving detection as the memory grows — all without any weight updates.

- **Core innovation**:
  1. **Agent-Aware Query Score (AAQS)**: composite uncertainty signal from (i) number of Skeptic-Verifier debate rounds, (ii) final verifier confidence score, (iii) retrieval similarity of nearest normal reference, (iv) memory coverage density. AAQS drives query decisions.
  2. **Tri-Layer Non-Parametric Memory**:
     - Normal Reference Memory (NRM): CLIP features of confirmed normals → richer comparison set for Comparative Retriever
     - Anomaly Exemplar Bank (AEB): annotated defect images → agent retrieves for direct comparison
     - Correction Experience Bank (CEB): (query_embedding, wrong_pred, correct_label, correction_reason) triples → soft-retrieval adjusts agent's reasoning
  3. **Memory-Augmented Detection**: at inference, retrieve from all three layers and inject into agent context before first reasoning round.

- **Minimum experiment**:
  1. Implement AAQS on existing Skeptic-Verifier — measure correlation with actual errors (does high AAQS predict wrong predictions? AUC > 0.7 = positive signal)
  2. Implement NRM update: after 10 human annotations, re-run detection — measure AUROC improvement on VisA bottle category

- **Expected outcome**: AAQS correlates with errors (AUC > 0.7); +2-5% AUROC after 20 annotations vs. no-feedback baseline

- **Novelty**: 9.5/10 — No paper combines (agent reasoning uncertainty) + (human-in-the-loop AL) + (non-parametric tri-layer memory) for visual IAD

- **Closest work**:
  - AgentIAD (tool-use agent for IAD, no feedback loop)
  - MRAD (static memory bank, no AL)
  - NearCAIPI (AL for IAD, no agent signals, workshop only)

- **Feasibility**: 4/5 — existing Skeptic-Verifier is the agent backbone; memory bank can use CLIP features (off-shelf); AL protocol simulation is straightforward

- **Risk**: MEDIUM — main risk is that AAQS doesn't predict errors well; mitigation: even a weak correlation is publishable + memory update still helps

- **Contribution type**: New method + empirical findings + new benchmark protocol

- **Pilot result**: Pending (see Phase 5)

- **Reviewer's likely objection**: "Is the agent-aware query strategy actually better than simple CLIP embedding distance?" → We ablate AAQS components; if agent signals add >1% AUC over naive uncertainty, the claim stands.

- **Why we should do this**: Complete system with three novel components in a completely unoccupied niche. Single rejection point but very defensible on novelty. Target: CVPR 2027 or NeurIPS 2026.

---

### 🥈 Idea 2: **MemoryGrows** — Incremental Normal Reference Memory for IAD
*Budget-Constrained Normal Sample Annotation Improves Comparison-Based Detection*

- **Hypothesis**: Selectively annotating and adding confirmed-normal samples to a non-parametric reference memory improves comparison-based IAD, and a diversity-maximizing selection strategy outperforms random and uncertainty-based selection under equal annotation budgets.

- **Core innovation**:
  - Diversity-aware normal sample selection: greedily select samples whose CLIP features maximally expand coverage of the normal reference distribution (max-min distance to existing memory)
  - Compare three strategies: random, uncertainty-based (low CLIP similarity to existing normals), and diversity-based (max coverage gain)
  - Use the Skeptic-Verifier's comparison tool to retrieve from the growing normal memory

- **Minimum experiment**:
  - On MVTec AD, simulate AL protocol: start with 5 normal samples, add 5 per round, measure AUROC change over 5 rounds (25 total annotations)
  - 3 strategies: random, uncertainty, diversity. Single category (e.g., carpet) as pilot.

- **Expected outcome**: Diversity strategy > uncertainty ≈ random at k=5,10,15 budget; +3-8% AUROC over static 5-shot baseline

- **Novelty**: 7/10 — closest: PatchCore (static memory), FastRef (prototype refinement without AL). No paper studies how to grow the normal reference memory via AL.

- **Feasibility**: 5/5 — pure Python/CLIP, no training, fast iteration

- **Risk**: LOW — diversity sampling for memory growth has worked in other domains; the question is how much it helps and whether the margin is large enough

- **Contribution type**: Empirical finding + simple method

- **Pilot result**: Pending

- **Reviewer's likely objection**: "Isn't this just PatchCore + greedy coreset update?" → Key diff: we study the AL acquisition strategy, we have annotation budget simulation, and we use VLM comparison tool (not just patch distance).

- **Why we should do this**: Fast to implement, clear positive signal likely, strong baseline for comparing to Idea 1's full system.

---

### 🥉 Idea 3: **DebateScore** — Agent Reasoning Trace as Uncertainty Proxy
*Calibrating When to Trust the Skeptic-Verifier Agent*

- **Hypothesis**: Structural features of the Skeptic-Verifier's multi-round reasoning trace (debate length, consensus speed, semantic hedging tokens) are better calibrated uncertainty proxies than softmax confidence for IAD queries, enabling a more efficient active learning query strategy.

- **Core innovation**:
  - Extract 5 trace features: (i) number of rounds until convergence, (ii) initial confidence score, (iii) final confidence score, (iv) semantic hedging words in reflection ("uncertain", "borderline", etc.), (v) nearest-neighbor similarity to existing memory
  - Train a lightweight uncertainty head (logistic regression, no GPU) on trace features to predict whether the agent will be wrong
  - Compare uncertainty calibration (ECE, AUC-ROC of error prediction) against: softmax, temperature scaling, ensemble disagreement

- **Minimum experiment**:
  - Run existing Skeptic-Verifier on 200 MMAD samples
  - Extract trace features for each sample
  - Compute correlation of each feature with error indicator
  - Logistic regression: 5-feature → error probability. AUC > 0.65 = positive pilot signal.

- **Expected outcome**: Round count + confidence delta are the most predictive features; combined AAQS achieves AUC > 0.70 for error prediction

- **Novelty**: 8/10 — using structured reasoning trace features for uncertainty estimation in multi-agent IAD is novel; relates to "calibration of LLM agents" literature but domain-specific

- **Feasibility**: 5/5 — just run inference and analyze logs; no new model needed

- **Risk**: LOW — even if predictive power is weak (AUC 0.60), it's an interesting negative result about agent self-calibration

- **Contribution type**: Empirical finding + diagnostic tool

- **Pilot result**: Can run immediately on existing system

- **Reviewer's likely objection**: "Small dataset → noisy estimates" → Use cross-validation; report confidence intervals; cite calibration literature

- **Why we should do this**: Building block for Idea 1; independently publishable as an analysis paper; requires only existing infrastructure.

---

### Idea 4: **CorrectionReplay** — Experience Replay from Agent Mistakes
*Non-Parametric Correction Bank Reduces Repeated Errors*

- **Hypothesis**: Storing (wrong_query_embedding, correct_label, correction_reason) triples in a correction bank and soft-retrieving them at inference time reduces systematic error recurrence without model retraining.

- **Core innovation**: At inference, retrieve top-k most similar past mistakes from CEB using CLIP embedding distance; inject retrieved correction summaries as "prior knowledge" into agent prompt before reasoning begins.

- **Minimum experiment**:
  - Simulate 20 corrections on VisA categories
  - Measure re-error rate on similar-looking samples with/without CEB injection
  - Metric: what % of correction-similar queries are now answered correctly?

- **Novelty**: 8/10 — retrieval-augmented generation for corrective experience is well-studied in NLP but novel in visual IAD agents

- **Feasibility**: 4/5 — requires CLIP embeddings + prompt engineering

- **Risk**: MEDIUM — depends on VLM's ability to use retrieved corrections in context

---

### Idea 5: **BudgetCurve** — AL Benchmark Protocol for Visual IAD
*The First Active Learning Evaluation Protocol on MVTec AD / VisA*

- **Hypothesis**: Establishing a standardized active learning evaluation protocol (fixed budget sizes, oracle simulation, evaluation metrics) reveals significant performance differences between query strategies and enables reproducible AL research in visual IAD.

- **Core innovation**:
  - Define AL simulation protocol: start with 0 labeled defects, sequentially query oracle (ground truth labels), measure AUROC/F1 as function of annotation budget (0, 5, 10, 20, 50 labels)
  - Evaluate 5 baselines: random, uncertainty, diversity, typical uncertainty (BADGE), AAQS
  - Create evaluation code + standard splits → open source

- **Minimum experiment**:
  - Implement protocol on MVTec AD bottle (simplest category)
  - Compare random vs. uncertainty vs. diversity on 5-20 annotation budgets
  - Expected: diversity > random at low budget; curve saturates around 20-30 labels

- **Novelty**: 7/10 — pure contribution is the protocol and empirical study; methodology is not novel

- **Feasibility**: 5/5 — straightforward implementation

- **Risk**: LOW — can't fail; it's an evaluation contribution

---

## Eliminated Ideas

| Idea | Reason eliminated |
|------|-------------------|
| RLHF fine-tuning from annotation feedback | Requires model retraining → catastrophic forgetting, high compute, violates non-parametric constraint |
| Multi-agent debate for uncertainty aggregation | Already done in MAD (2602.14251) for tabular AD |
| Zero-shot AL with CLIP only (no agent) | Too shallow, doesn't use agent's reasoning advantage |
| SFT on correction data | Requires retraining; goes against design principle |
| Prompt optimization from annotation | Soft prompt tuning needs gradient; hard prompt rewriting is too noisy |

---

## Pilot Experiment Plan (Phase 5)

### Pilot 1: DebateScore (Idea 3) — immediately runnable

**Command**: Run existing Skeptic-Verifier on MMAD subset (200 samples), extract trace features, compute error prediction AUC.
- **GPU**: Not needed (inference on Doubao API + CPU feature extraction)
- **Estimated time**: ~30-60 min
- **Success metric**: AUC > 0.65 for error prediction from trace features

### Pilot 2: MemoryGrows (Idea 2) — fast MVP

**Command**: Implement NRM with CLIP features, test random/diversity selection on MVTec bottle.
- **GPU**: 1 GPU for CLIP inference
- **Estimated time**: ~60-90 min
- **Success metric**: Diversity strategy AUROC > random strategy at k=10 budget

### Pilot 3: AAQS correlation (component of Idea 1)

**Command**: After Pilot 1 extracts trace features, add CLIP similarity as 5th feature, measure combined AAQS AUC.
- **GPU**: 1 GPU for CLIP
- **Estimated time**: ~30 min (extends Pilot 1)
- **Success metric**: Combined AAQS AUC > individual features alone

---

## Suggested Execution Order

1. **Run Pilot 1 (DebateScore)** — no code changes needed; run existing system on MMAD, analyze logs. ~1 hour.
2. **Run Pilot 2 (MemoryGrows)** — implement CLIP-based NRM + diversity selection. ~2 hours.
3. **Pilot 3 follows from Pilot 1** — combine features into AAQS. ~30 min.
4. If pilots positive → **implement full AnomaClaw system** (Idea 1)
5. If Pilot 2 positive but AAQS weak → **fall back to Idea 2** as primary contribution

## Next Steps

- [ ] **Pilot 1**: Run Skeptic-Verifier on MMAD, extract trace features, compute error prediction AUC
- [ ] **Pilot 2**: Implement NRM + diversity AL on MVTec AD bottle
- [ ] **Pilot 3**: Combine into AAQS
- [ ] Review pilot results → decide on full system scope
- [ ] `/novelty-check` for Idea 1 (full system) against concurrent arXiv papers
- [ ] `/research-review` with external reviewer
- [ ] Implement full AnomaClaw system
- [ ] `/run-experiment` full-scale evaluation
- [ ] `/auto-review-loop` until submission-ready
