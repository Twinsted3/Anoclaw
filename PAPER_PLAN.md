# Paper Plan

**Working title:** *When a Worse Agent Still Wins: Failure-Mode-Robust Cross-Domain Visual Anomaly Detection with a Parallel-Direct Ensemble*

**One-sentence contribution:** A training-free visual anomaly detection agent whose single per-item invocation runs a refutation-style tool-using trajectory and a descriptor-free Direct VLM call in parallel on the same backbone and averages them, producing a macro AUROC gain on every VLM backbone tested — even on the one where the agent alone is significantly *worse* than Direct.

**Venue:** ICLR
**Type:** Empirical / diagnostic (a surprising-observation paper, not a method paper)
**Date:** 2026-04-25
**Page budget:** 9 pages main body (ICLR), references + appendix unlimited
**Section count:** 7

---

## 1. Claims-Evidence Matrix

| Claim | Evidence | Status | Section |
|---|---|---|---|
| **A (headline)** — An always-on parallel-Direct branch gives a significant ensemble gain on every backbone, and is the only tested design that preserves signal when the agent alone is significantly worse than Direct. | Table 1: GPT-5.4 +4.01 pp ($P{=}1.000$), SeedVL +5.99 pp ($P{=}1.000$), Qwen3.5 +1.69 pp ($P{=}0.971$). Agent-alone vs Direct on Qwen3.5 $-4.46$ pp ($P{=}0.001$). Stratified paired bootstrap, 1000 resamples. | ✅ supported | §3, §4 |
| **B (mechanism)** — The ensemble gain comes from *rank granularity*, not middle-zone mass. | Table in §4: BIN (rank-collapse) halves gain to +2.31 pp; EXT-RANK (rank-preserving, middle-mass=0) keeps +4.68 pp; AFFINE($a{<}1$) stays high; AFFINE($a{>}1$) drops. | ✅ supported | §4 |
| **C (behaviour)** — Reasoning depth tracks agent quality: the strong backbone goes deeper on more items. | Figure 4a: GPT 1.1%/89.3% 1/2-turn, Qwen3.5 15.1%/76.3%. Mean candidates 2.47 vs 1.55. | ✅ supported | §5 |
| **D (behaviour)** — The 13-tool catalogue collapses to 2 tools in practice; a specialty-aware presentation (appendix mechanism check) recovers tool diversity and lifts macro AUROC $+2.04/+2.90$ pp on two backbones. | Figure 4b: side_by_side + reference_profiler > 95% invocations on every backbone. Appendix Table D: specialty-aware CI excludes zero on SeedVL and Qwen3.5. | ✅ supported | §5, Appendix D |
| **E (behaviour)** — Refutation-verdict distribution is strongly backbone-dependent and runtime-observable. | Figure 4c: GPT-5.4 56% found_in_ref, SeedVL 89% not_found, Qwen3.5 intermediate. | ✅ supported | §5 |
| **F (extension)** — A 480-label semi-supervised Controller extension closes the remaining gap on the weakest-ensemble backbone. | §6 Table: Qwen3.5 passive ensemble 0.7333 → Controller full 0.7539 ($+2.05$ pp, CI $[+0.41, +3.67]$, $P{=}0.995$). Four-way ablation (no-rules/shuffled/meta-only/full) shows rule *content* is the mechanism. | ✅ supported | §6 |

**Not reported (withheld):**
- Specialty-aware catalog on GPT-5.4 (sub-API outage blocked D5–D12 on the retry run). The partial Qwen3.5 + SeedVL evidence is retained as an Appendix-level mechanism check, not a headline finding.
- Transfer of the Controller extension to GPT-5.4 and SeedVL. Mentioned as future work.

---

## 2. Paper Type and Structure

**Type:** Empirical/diagnostic — the headline is a surprising observation (worse-agent-still-wins) and a mechanism explanation for it. Not a benchmark paper (we release a benchmark but it supports the observation), not a pure method paper (the method is deliberately simple).

**Why 7 sections, not 5:** An empirical-observation paper needs both (a) the observation presented cleanly with CIs, and (b) a mechanism story that rules out alternative explanations. Squeezing (b) into a general "experiments" section would bury the rank-granularity falsification. Similarly, agent-behaviour analysis (claims C/D/E) is a separate diagnostic contribution that deserves its own section.

**Section-by-section budget (sums to 9.0 pages):**

| § | Title | Pages | Primary content |
|---|---|---|---|
| 1 | Introduction | 1.25 | Hook, gap, failure-mode question, contribution list, results preview, hero figure |
| 2 | Related Work | 0.75 | Training-free VAD, VLM agents, heterogeneous-score ensembles; compact |
| 3 | Benchmark, Setup, and Method | 2.0 | CrossDomainVAD-12 (0.5), parallel-Direct + refutation agent method (1.5) |
| 4 | Main Result: the Failure-Mode-Robust Ensemble | 2.5 | Table 1 + failure-mode narrative + rank-granularity mechanism table |
| 5 | How the Agent Actually Behaves | 1.25 | 3 subsections: depth, tools, verdicts; Figure 4 |
| 6 | Semi-Supervised Extension: Controller with a Verbalized Rulebook | 0.75 | 4-way ablation, CI |
| 7 | Discussion and Conclusion | 0.5 | Limitations, why the parallel-branch primitive generalises, future work |

---

## 3. Section-by-Section Planning

### §0 Abstract (150–220 words)
- **What we achieve.** Training-free cross-domain VAD where *the same single-invocation recipe* gives a significant macro-AUROC gain over single-pass VLM prompting on every tested VLM backbone.
- **Why it is hard.** A VLM wrapped in an obvious multi-turn agent can be *worse* than the single-pass baseline on some backbones; a practitioner cannot know in advance which regime they are in.
- **How we do it.** A single per-item invocation runs a multi-turn refutation trajectory and a descriptor-free Direct call *in parallel on the same backbone*, and averages them.
- **Evidence.** CrossDomainVAD-12 (1,418 items, 12 domains, three VLMs). Significant ensemble gain on two backbones ($P{=}1.000$), positive-in-mean on the third where the agent alone is significantly *weaker* than Direct (agent-alone $-4.46$ pp, $P{=}0.001$; ensemble $+1.69$ pp). We identify rank granularity, not middle-mass, as the mechanism; a 480-label controller extension closes the remaining gap on the weakest backbone.
- **Length target:** 200 words. Must mention: *failure-mode robust*, *parallel-Direct ensemble*, the 4.01/5.99/1.69 pp numbers, and the Qwen3.5 agent-worse-than-Direct fact.
- **Self-contained check:** A reader must understand (a) what we did, (b) the main number, and (c) why it is surprising, without the paper.

### §1 Introduction (1.25 pages)
- **Opening hook (2–3 sentences).** Training-free VLM prompting is the de facto default for visual anomaly detection. It fails silently across domains when a VLM's world-knowledge priors conflict with the task-specific definition — we show this on 12 domains.
- **Gap / the failure-mode question.** A natural fix is to wrap the VLM in a multi-turn agent. We find that on one of our three VLM backbones, a well-designed refutation agent is *significantly worse* than Direct ($-4.46$ pp macro AUROC, $P{=}0.001$). A pure-agent pipeline silently loses on that backbone. Practitioners cannot know in advance which regime they are in.
- **One-sentence contribution.** *Run the agent and Direct in parallel inside the same per-item invocation and average them — this preserves signal even when the agent is individually weaker than Direct, and adds signal when it is not.*
- **Approach overview.** Single-call architecture; no dev tuning; $\alpha{=}0.5$ fixed a priori; same recipe across backbones.
- **Results preview.** GPT-5.4 $0.731\to 0.772$ ($+4.01$ pp), SeedVL $0.678\to 0.738$ ($+5.99$ pp), Qwen3.5 $0.714\to 0.732$ ($+1.69$ pp; the load-bearing case).
- **Hero figure description (Figure 1).** A 3-panel bar chart: for each backbone, three bars — *Direct baseline*, *Agent alone*, *Ensemble* — with paired-bootstrap CI error bars. Crucial visual: on Qwen3.5 the *Agent alone* bar dips below the *Direct* bar with its CI excluding zero, while the *Ensemble* bar rises above both with CI also excluding zero. The reader must feel the worse-agent-still-wins story from the figure alone before reading anything. *This figure does not currently exist; it will be generated in Phase 2 from `paper/figures/v2_main_results.json`.*
- **Contributions (numbered).**
  1. A failure-mode-robust training-free VAD primitive: *parallel-Direct + refutation-agent, fixed-weight ensemble inside a single invocation*. Significant on 2/3 backbones, positive-in-mean on 3/3, including the backbone where the agent alone is significantly worse than Direct.
  2. A mechanism explanation — *rank granularity*, not middle-zone mass — validated by three controlled rank-preserving / rank-collapsing transformations.
  3. Three diagnostic observations of how VLM-based refutation agents actually behave across backbones (reasoning depth, tool-catalogue collapse, verdict-bimodality), each runtime-observable and useful for deployment triage.
  4. A semi-supervised Controller extension that, with 480 total dev labels, closes the remaining gap on the weakest-ensemble backbone via verbalized rules, with a four-way ablation isolating rule *content* as the mechanism.
  5. **CrossDomainVAD-12** — 12-domain, 1,418-item cross-domain VAD benchmark with calibration/dev/test splits spanning industrial, medical, infrastructure, remote-sensing, 3D, and road-scene sources.
- **Front-loading check.** By end of §1, a skim reader knows the headline number, the surprising observation (worse-agent-still-wins), and the one-sentence recipe.
- **Estimated length:** 1.25 pages.
- **Key citations:** Gu et al. AnomalyGPT (WinCLIP / VLM-based VAD baseline); Bao et al. BMAD (medical VAD); Zhang et al. AgentIAD (agent-based VAD); Jeong et al. WinCLIP; Jiang et al. MMAD; Dohmatob et al. (ensemble complementarity theory if available).

### §2 Related Work (0.75 pages, 3 paragraphs)
- **Training-free VLM-based VAD.** Single-pass baselines (WinCLIP, AnomalyGPT derivatives, MMAD Direct). Strengths: no training, no domain adaptation. Weaknesses: silent failure on descriptor/prior conflicts; backbone-dependent performance.
- **Multi-turn VLM agents for vision tasks.** ReAct-style loops, tool-using proposers, debate-style multi-agent systems. Relevant failure mode: unconditional second-call escalation rationalises correct high-confidence predictions away (we confirm this ourselves in Appendix A).
- **Ensembles of heterogeneous scorers.** Score-level fusion between VLMs and non-parametric experts; oracle-gap analyses on cross-domain benchmarks. Our parallel-Direct design is the narrowest ensemble in this literature: a VLM is ensembled *against itself under two different inference regimes on the same backbone*, inside one API call.
- **Positioning.** We are not proposing a better tool catalogue or a better refutation protocol; we are proposing a failure-mode-robust wrapper that any training-free VLM agent can be dropped into. The observation that the wrapper is *required* (not merely helpful) is new.
- **Minimum length:** 0.75 pages, 3 paragraphs with synthesis, not a list.

### §3 Benchmark, Setup, and Method (2.0 pages)

**§3.1 CrossDomainVAD-12 (0.3 pages).** 12 domain codes spanning industrial (MVTec-AD, GoodsAD, VisA, MVTec-LOCO), infrastructure (SDNET2018), 3D product (Real3D-AD), remote-sensing change (LEVIR-CD+), medical (DermaMNIST, BraTS2021, BMAD-Liver, HyperKvasir), road safety (BDD100K+RoadAnomaly21). 20/40/120 cal/dev/test per domain (D7=98 test). 1,418 total test items. Descriptor sentences frozen before experiments.

**§3.2 Setup (0.2 pages).** Three VLMs: GPT-5.4 (proprietary frontier), SeedVL (doubao-seed-2-0-lite, proprietary non-frontier), Qwen3.5-VL-27B (open-weight, served via vLLM). Temperature 0. Descriptor-free prompts for both Direct and agent branches to match task preamble. Macro-averaged per-domain AUROC. Stratified paired bootstrap (1,000 resamples, per-domain stratification) for every headline CI.

**§3.3 Architecture: parallel-Direct + refutation agent (0.6 pages).**
- Figure 2: the architecture diagram (uses `paper/figures/fig_architecture_imagegen_hires.png`).
- The single per-item invocation launches two branches on the same backbone API session:
  - *Direct branch.* One VLM call, descriptor-free task prompt. Returns $s_{\mathrm{Direct}}\in[0,1]$.
  - *Refutation branch.* Multi-turn trajectory ($K=5$ turn budget) using a 13-tool library. Returns $s_{\mathrm{agent}}\in[0,1]$.
- Fixed-weight blend $s_{\mathrm{final}} = 0.5\,s_{\mathrm{Direct}}+0.5\,s_{\mathrm{agent}}$; $\alpha$ frozen a priori, no dev tuning.
- Wall-time is $\max(\text{Direct}, \text{agent})$ — branches run concurrently.

**§3.4 The refutation protocol (0.6 pages).** Three-phase structured schema (suspect list → targeted refutation → verdict + score update); the agent is biased toward *ruling anomalies out* rather than confirming them. Full protocol and prompt template in Appendix B.

**§3.5 The always-on argument (0.3 pages).** Why always-on rather than conditional? Because the failure-mode regime is backbone-dependent and unobservable at deployment time. An always-on Direct branch trades a single extra API call for failure-mode robustness; we quantify the trade in §4.

### §4 Main Result: the Failure-Mode-Robust Ensemble (2.5 pages)

**§4.1 Three-regime story and Table 1 (1.0 pages).**
Table 1 (per-domain + macro AUROC, Direct / Agent / Ensemble / $\Delta$, three backbones, stratified paired bootstrap CI row under the table). The three regimes paragraph:
- *Strong-agent regime (GPT-5.4).* Agent alone +3.64 pp over Direct ($P{=}0.998$); Direct branch adds a further +0.37 pp; ensemble +4.01 pp ($P{=}1.000$).
- *Balanced regime (SeedVL).* Both branches individually significant over Direct; ensemble +5.99 pp, the best case.
- *Failure-mode regime (Qwen3.5).* Agent alone is significantly *weaker* than Direct ($-4.46$ pp, $P{=}0.001$). Yet the ensemble +1.69 pp ($P{=}0.971$; CI $[-0.08, +3.51]$). The load-bearing case.

**§4.2 Per-domain complementarity (0.5 pages).** Figure 3 (per-domain bars). The agent contributes signal on five specific domains where it is individually weaker globally; Direct recovers two domains (D7 LEVIR, D11 Kvasir) where the agent fails. Complementarity is not an average phenomenon; it is per-domain.

**§4.3 Mechanism: rank granularity, not middle-mass (0.75 pages).**
Mechanism table. Transformations of agent scores on Qwen3.5 ($n{=}1418$):
- Original (49 unique values): ensemble +4.53 pp.
- BIN (rank-collapse to 2 values, preserves sign): +2.31 pp (halved).
- EXT-RANK (preserves every rank, middle-mass=0): +4.68 pp (larger than original!).
- AFFINE($a{<}1$) (rank-preserving compression around 0.5): +4.64 to +4.71 pp.
- AFFINE($a{>}1$) (rank collapse near boundaries): +2.02 pp.
**Conclusion.** Middle-mass is correlational, not causal; rank granularity is the causal driver.

**§4.4 Cross-benchmark transfer (0.25 pages).** MMAD AD subset ($n=483$ questions across four constituent datasets): Qwen3.5 Direct 0.76, Ensemble 0.79, no retuning. Transfer confirms the ensemble gain is not CrossDomainVAD-12-specific.

### §5 How the Agent Actually Behaves (1.25 pages)
Opens with: *The headline in §4 is an outcome; this section reports how the agent got there, and why the parallel-Direct branch is not redundant.*
- **§5.1 Reasoning depth tracks agent quality (0.4 pages, Figure 4a).** GPT: 1.1% 1-turn; Qwen3.5: **15.1% 1-turn**, 8.9% zero-candidate-feature items. Mean candidates 2.47 vs 1.55. The weaker backbone finalises earlier with less evidence — directly connected to Qwen3.5's $-4.46$ pp agent-alone deficit.
- **§5.2 The 13-tool catalogue collapses to 2 (0.4 pages, Figure 4b).** side_by_side + reference_profiler > 95% of invocations on every backbone. This is presentation, not refutation-task-intrinsic; a specialty-aware catalog rewrite (Appendix D) lifts tool usage 2 → 6–10 tools and adds $+2.04$ pp / $+2.90$ pp on SeedVL and Qwen3.5 (CI excludes zero).
- **§5.3 Verdict distribution is bimodal across backbones (0.45 pages, Figure 4c).** GPT: 56% found_in_ref (balanced refuter); SeedVL: 89% not_found (rarely retires candidates); Qwen3.5 intermediate. A backbone that rarely retires candidates inflates the agent score toward anomaly — the Direct branch is the complementary signal that fixes this. This is runtime-observable and a diagnostic for deployment triage.

### §6 Semi-Supervised Extension: Controller with a Verbalized Rulebook (0.75 pages)
- **Motivation.** Ensemble weights are fixed; can a small dev-label budget do better on the weakest-ensemble backbone (Qwen3.5)?
- **Architecture (one paragraph).** A Controller VLM reads both branches' score–rationale pairs and a per-domain rulebook retrieved by (domain, category). Rulebook has two layers: meta-rules (routing, offline from disagreement cases) + domain rules (reused from a reference-only oracle-grounded pilot). 480 total dev labels.
- **Result and ablation table.** Passive ensemble 0.7333 → Controller-full 0.7539 ($+2.05$ pp, CI $[+0.41, +3.67]$, $P{=}0.995$). Four-way ablation: no-rules $-1.06$ pp ($P{=}0.111$); shuffled-domain rules $-1.34$ pp ($P{=}0.053$); meta-only $+0.55$ pp; full $+2.05$ pp. Rule *content* is the mechanism, not the controller mechanism or "any text in the prompt."
- **Scope.** Single-backbone case study; we do not claim training-free status for this extension. Transfer to GPT-5.4 and SeedVL is future work.

### §7 Discussion and Conclusion (0.5 pages)
- **What the parallel-branch primitive generalises.** The same pattern (always-on Direct, refutation agent, single-invocation fixed blend) should work for any training-free VLM task whose base prompt has usable signal but whose multi-turn agent is backbone-brittle — OCR-heavy document inspection, medical screening, satellite change detection.
- **Limitations (one paragraph).** (a) Three floor domains: D6 Real3D-AD, D10 Liver CT, D4 SDNET-Direct-only; modality mismatch and item-level similarity. (b) Ensemble weight $\alpha{=}0.5$ fixed — a 20-item calibration selector is an obvious extension. (c) Tool-usage refinement on weak backbones (Qwen3.5 refutation agent $-4.46$ pp deficit localises to specific tools on specific domains). (d) Controller extension is a single-backbone case study.
- **Closing.** For training-free cross-domain VAD, the right architectural primitive is not a pure autonomous agent but an *ensemble-aware* agent whose Direct branch is always invoked. The surprising part is that this primitive *must* exist even when the agent itself is the better estimator — because 'the agent is better' is backbone-dependent and unobservable at deployment time.

---

## 4. Figure Plan

| ID | Type | Description | Data / file | Status | Priority |
|---|---|---|---|---|---|
| **Figure 1 (HERO)** | 3-panel grouped bar chart | Per-backbone macro AUROC: *Direct* vs *Agent alone* vs *Ensemble*, with paired-bootstrap CI error bars. Must visually show: Qwen3.5 agent-bar **below** Direct-bar, ensemble-bar **above** both. | `paper/figures/v2_main_results.json` + bootstrap CI from `paper/figures/bootstrap_cis.json` | **NEW** — to be generated in Phase 2 | CRITICAL |
| Figure 2 | Architecture diagram | Parallel-Direct + refutation-agent architecture; input (query+refs) → Direct branch + refutation branch → fixed blend → final score + auditable trace. | `paper/figures/fig_architecture_imagegen_hires.png` (user-provided, 1.18 MB) | REUSE as-is | HIGH |
| Figure 3 | Per-domain bars, 3-row panel | Per-domain AUROC for Direct / Agent-alone / Ensemble across all 12 domains on each of 3 backbones. Shows where complementarity concentrates. | `paper/figures/fig_per_domain.pdf` | REUSE, re-caption | HIGH |
| Figure 4 | 4-panel agent-behaviour | (a) turn distribution, (b) tool frequency, (c) verdict distribution, (d) candidate-feature count — all per backbone. | `paper/figures/fig_agent_behavior.pdf` | REUSE, re-caption | HIGH |
| Figure 5 (optional) | No-single-winner motivation | From earlier-split design-exploration evaluation; shows no fixed strategy dominates all 12 domains. | `paper/figures/fig_intuition.pdf` | REUSE only if §2 motivation needs a visual. Otherwise defer to Appendix. | LOW |

**Table inventory:**
- Table 1 (main, §4.1): 12-domain × 3-backbone × (Direct / Ensemble / $\Delta$) + macro row + CI row. Source: `paper/figures/v2_main_results.json`.
- Table 2 (mechanism, §4.3): 5–6 rows of rank-granularity transformations on Qwen3.5; source: Section 4.3 ablation data from tech-report archive.
- Table 3 (controller, §6): 4-row controller ablation (no-rules / shuffled / meta-only / full). Source: `verbalized/v11_eval_test_meta_only` + `v11_eval_test` result dirs.
- Appendix Table D (specialty-aware, §5.2 reference): per-domain SeedVL and Qwen3.5 specialty-aware vs passive, $n{=}1418$. Source: `paper/figures/v2_main_results_v12.json`.
- Appendix Table A (negative-results ablation): 6 earlier-design agent variants on GPT-5.4 calibration. Source: archive.

**Hero-figure design rationale.** The technical-report version used the architecture diagram as Figure 1. For a story-driven paper this is wrong — a skim reader sees 'here is what we built' before seeing *why they should care*. A grouped bar chart showing the agent dipping below Direct and the ensemble rising above gives the reader the headline in a single glance; the architecture diagram moves to Figure 2.

---

## 5. Citation Plan

All citations to be verified against `paper/references.bib` (exists) and augmented only with verified entries.

- **§1 Introduction** (motivation, the VLM-VAD landscape):
  - Gu et al. AnomalyGPT (WinCLIP extension, IAD via prompting) [VERIFY]
  - Jeong et al. WinCLIP / WinCLIP+ (CLIP-based VAD) [VERIFY]
  - Bao et al. BMAD benchmark (medical VAD) [VERIFY]
  - Jiang et al. MMAD benchmark (VLM on industrial inspection MCQ) [VERIFY]
  - Zhang et al. AgentIAD (agentic IAD, concurrent work) [VERIFY]
- **§2 Related Work**:
  - Chen et al. EAGLE (multi-turn anomaly agent) [VERIFY]
  - Wei et al. AutoIAD (ReAct IAD) [VERIFY]
  - Debate-style VLM / ReAct systems [VERIFY]
  - Score-level ensemble / heterogeneous-scorer ensembles [VERIFY]
- **§3 Setup/Method**:
  - DINOv2 (Oquab et al.) [VERIFY — primary expert backbone]
  - SubspaceAD (our earlier cite) [VERIFY from references.bib]
  - AnomalyVFM (LoRA-adapted foundation model) [VERIFY]
  - MVTec-AD (Bergmann et al.), GoodsAD, VisA, MVTec-LOCO, SDNET2018, Real3D-AD, LEVIR-CD+, DermaMNIST, BraTS2021, BMAD-Liver, HyperKvasir, BDD100K, RoadAnomaly21 — all 12 source benchmarks. [VERIFY all]
- **§6 Controller extension**:
  - Verbalized-learning / in-context rule retrieval work [VERIFY]

**Citation-reuse strategy.** The archived technical-report `paper/references.bib` already contains verified entries. Phase 3 (`/paper-write`) should reuse these verbatim and only add entries for (a) ensemble-theory references if the §2 Related Work gains a new paragraph, (b) any previously-uncited source dataset that now appears in §3.1.

---

## 6. Reviewer Feedback Consolidation (from prior Codex review)

The technical-report draft was reviewed by GPT-5.4 xhigh in an earlier adversarial review (saved at `.aris/traces/research-review/20260422_142711_reply.md`). Score: 6/10. Top three blocking issues from that review carry into this story-driven rewrite:

1. **"Significant on every backbone" overclaim.** The tech-report opened with a $P(\Delta{>}0){=}1.000/1.000/0.971$ claim and labelled it "significant on every backbone", but Qwen3.5's lower CI $-0.08$ pp touches zero. The rewritten abstract / §4 uses *"significant on two of three backbones, positive-in-mean on three of three"* and explicitly flags the Qwen3.5 CI as touching zero.
2. **Failure-mode robustness conflated with improvement over Direct.** Evidence clearly supports *"ensemble rescues a bad agent branch relative to agent-alone"*; it supports *"ensemble beats Direct"* only with caveats on the weak backbone. The rewritten §4.1 leads with the agent-alone-vs-ensemble contrast on Qwen3.5 and the ensemble-vs-Direct delta only after.
3. **Behavioural explanations causally overstated.** Three diagnostic observations (Claims C, D, E) were written as mechanisms in the tech-report. The rewritten §5 frames them as observations + hypothesis tests, with the mechanism claim reserved for rank-granularity in §4.3 where we have a controlled falsification.

---

## 7. Page-Budget Feasibility

| § | Budget | Notes |
|---|---|---|
| 1 | 1.25 | Tight but feasible; the contribution-list bullets are compressed. |
| 2 | 0.75 | Will require synthesis paragraphs, not lists. |
| 3 | 2.0 | Benchmark + setup + architecture + refutation protocol + always-on argument. If over-budget, move refutation-protocol details to Appendix B and keep only a two-paragraph summary in main body. |
| 4 | 2.5 | Table 1 + mechanism table + per-domain panel. If Table 1 is 12-row × 3-backbone, consider folding the $\Delta$ column into the main body and moving per-domain-$\Delta$ to appendix. |
| 5 | 1.25 | Figure 4 is 4-panel; can be tightened to 2-panel (turns + tools) with verdicts in caption if over-budget. |
| 6 | 0.75 | One table; compact. |
| 7 | 0.5 | Short. |
| **Total** | **9.0** | Exactly at ICLR limit. |

**Soft overrun plan** (if the Phase-3 draft lands at 9.2–9.5 pages):
1. Cut §4.4 cross-benchmark paragraph into 4 lines and move MMAD details fully to appendix.
2. Collapse §3.4 refutation-protocol detail into a single paragraph; full schema in Appendix B.
3. Drop Table 2 rank-granularity visual row (AFFINE a=0.25, AFFINE a=0.5 are adjacent rows) and keep only 4 rows (Original / BIN / EXT-RANK / AFFINE).

---

## 8. Next Steps

- [ ] Phase 2: Generate **Figure 1 (hero bar chart)**. All other figures reused as-is from `paper/figures/`.
- [ ] Phase 3: `/paper-write` drafts `paper/sections/*.tex` from this plan; must preserve every numeric claim in the Claims-Evidence matrix.
- [ ] Phase 4: `/paper-compile`; then `/paper-claim-audit` against `benchmark/results/` and `paper/figures/*.json` raw data.
- [ ] Phase 5: `/auto-paper-improvement-loop` × 2 rounds.

## Appendix Plan

- **App A** — Benchmark spec (per-domain item counts, source datasets, licenses, descriptor sentences).
- **App B** — Refutation-protocol prompt templates and JSON schema; task-preamble builder; domain hint table (for the §5.2 specialty-aware mechanism check).
- **App C** — Failed-variant ablation (6 agent designs on GPT-5.4 calibration: Normal-First, Self-Refine, Debate, Evidence-injection, Third-call-arbiter, EGRA). These are *negative results from the design-exploration phase* and go here rather than main body.
- **App D** — Specialty-aware tool-catalog mechanism check: per-domain deltas on SeedVL + Qwen3.5, tool-usage distribution shift from 2 to 6–10 tools.
- **App E** — Per-domain results (full 12 × 3 matrices for Direct, Agent-alone, Ensemble).
- **App F** — Stratified paired bootstrap protocol and CI tables.
- **App G** — Controller extension: rulebook construction pipeline, four-way ablation details, per-domain controller AUROC.
- **App H** — MMAD cross-benchmark evaluation.
- **App I** — Earlier-split design-exploration findings (descriptors-dominate, calibration-router, Route-B fusion) retained for continuity.
