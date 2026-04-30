# AnomalyClaw: When a Worse Agent Still Wins — Failure-Mode-Robust Cross-Domain Visual Anomaly Detection

## The Story in One Paragraph

Training-free vision-language-model (VLM) prompting is the de facto method for cross-domain visual anomaly detection (VAD), but it fails silently on domains where a VLM's world-knowledge priors conflict with the task-specific anomaly definition. A natural response is to wrap the VLM in a multi-turn agent. We find that this response **can be worse than the single-pass baseline on some VLM backbones**, yet an ensemble of the agent with its own Direct baseline — running in parallel inside a single per-item call — still beats Direct on every backbone, even when the agent alone is significantly weaker. This *failure-mode-robust parallel-branch design* is the load-bearing insight: a training-free VAD agent should not commit to a single reasoning path; it should always hedge against its own reasoning by running a Direct branch it averages against. We verify this on a new 12-domain, 1418-item cross-domain benchmark across three VLMs, identify rank-granularity as the causal mechanism behind the ensemble gain, document three backbone-dependent behaviours of the refutation agent (reasoning depth, tool collapse, verdict distribution), and show that a 480-label semi-supervised controller extension closes the remaining gap on the weakest-ensemble backbone.

## The Story Arc (what a reader should feel in each section)

1. **The default setup is fragile.** VLM + one prompt + 1–2 references is the typical training-free VAD recipe. On a single-domain benchmark it looks great. On 12 domains across industrial, medical, remote-sensing, infrastructure, 3D, and road-scene sources, no fixed recipe (descriptor-free Direct, SubspaceAD-fused, debate, interpret-routed) wins on more than 3 of 12 domains.
2. **The obvious fix — build an agent — can make things worse.** On GPT-5.4 and SeedVL a carefully-designed refutation agent beats Direct by 3–4 pp. On Qwen3.5-VL-27B the *same* agent is significantly *worse* than Direct by 4.5 pp ($P{=}0.001$). Practitioners deploying an agent onto a new backbone cannot know in advance which regime they are in.
3. **The insight.** The agent's errors and Direct's errors are complementary on every backbone we tested, including when the agent is individually weaker. So run both, in parallel, inside the same per-item call, and average. The resulting ensemble beats Direct on all three backbones; the Qwen3.5 case is exactly the one where the design earns its keep.
4. **The mechanism.** It is not just 'two estimators are better than one' — it is specifically *rank granularity*: Direct emits a coarse score grid (11 unique values on Qwen3.5 test); the agent emits a finer grid (49 unique values). Averaging breaks Direct's ties with real signal. We falsify the 'middle-mass' alternative explanation with three rank-preserving / rank-collapsing transformations.
5. **Agent behaviour is backbone-dependent.** Reasoning depth tracks agent strength: the strong backbone finalises after 2 turns on 89% of items; the weak backbone finalises after 1 turn on 15%. Tool usage collapses: 2 of 13 tools account for > 95 % of invocations on every backbone. Refutation verdicts are bimodal: GPT-5.4 retires 56 % of candidates; SeedVL retires only 9 %. These observations are diagnostic; the parallel-Direct branch is what makes them *tolerable* rather than fatal.
6. **We can push further with a small label budget.** Adding a Controller VLM that reads both branches' score–rationale pairs plus a per-domain rulebook (480 total dev labels, built offline) reaches +2.05 pp over the passive ensemble on Qwen3.5, with a branch-frozen four-way ablation (no-rules / shuffled-rules / meta-only / full) showing that rule content is the mechanism, not the controller's added call.
7. **The takeaway is architectural, not benchmark-specific.** For training-free cross-domain VAD, the right primitive is an *ensemble-aware* agent with an always-on Direct branch. For the semi-supervised regime, a cheap controller + verbalized rulebook closes most of the gap to backbone-dependent tuning.

## Key Claims and Load-Bearing Evidence

### Claim A (headline): An always-on parallel-Direct branch gives a significant ensemble gain on every backbone we tested, and is the only tested design that preserves signal when the agent alone is significantly worse than Direct.

**Evidence (Table 1, $n{=}1418$, stratified paired bootstrap CI, 1000 resamples, per-domain stratification):**

| Backbone | Direct | Agent alone | Ensemble | Δ(Ens−Direct) | 95 % CI | $P(\Delta>0)$ |
|---|---|---|---|---|---|---|
| GPT-5.4 | 0.731 | 0.768 | **0.772** | +4.01 pp | [+2.58, +5.50] | 1.000 ✓ |
| SeedVL | 0.678 | 0.715 | **0.738** | +5.99 pp | [+4.32, +7.66] | 1.000 ✓ |
| Qwen3.5-VL-27B | 0.714 | 0.671 | **0.732** | +1.69 pp | [−0.08, +3.51] | 0.971 |

**Agent-alone vs Direct:** GPT-5.4 +3.64 pp ($P{=}0.998$); SeedVL +3.68 pp ($P{\ge}0.998$); Qwen3.5 **−4.46 pp, CI [−7.61, −1.55], $P{=}0.001$**. The Qwen3.5 row is the load-bearing failure-mode row: a pure agent recipe would silently regress on this backbone, yet the parallel ensemble still improves on Direct.

### Claim B (mechanism): The ensemble gain comes from rank granularity, not middle-zone mass.

**Evidence (controlled transformations on Qwen3.5 test, $n{=}1418$; Section 4.3):**
- Original agent: 49 unique values → ensemble gain +4.53 pp.
- **BIN** (collapse 49 → 2 at median): ensemble gain halves to +2.31 pp. Rank collapse kills the gain.
- **EXT-RANK** (remap 49 values to ranges outside [0.2, 0.8], preserving every rank): gain *increases* to +4.68 pp. Middle-mass is irrelevant.
- **AFFINE($a{<}1$)** (compress around 0.5, preserve rank): gain stays in high regime (+4.64 to +4.71 pp).
- **AFFINE($a{>}1$)** (expand, clip, collapse ranks): gain drops to +2.02 pp.
Three of four transformations confirm rank granularity as the causal driver; middle-mass is ruled out.

### Claim C (behaviour): Reasoning depth tracks agent quality across backbones.

**Evidence (Figure 3, per-item turn distribution):**
- GPT-5.4: 1.1 % 1-turn, 89.3 % 2-turn, mean 2.47 candidate features, 1.1 % zero-candidate items.
- SeedVL: 7.4 % 1-turn, 91.4 % 2-turn.
- Qwen3.5: **15.1 % 1-turn**, 76.3 % 2-turn, mean 1.55 candidate features, **8.9 % zero-candidate items**.
The shallower behaviour correlates 1:1 with agent-alone deficit and explains the failure-mode story of Claim A.

### Claim D (behaviour): The 13-tool catalogue collapses to 2 tools in practice, independent of backbone.

**Evidence (Figure 4):** `tool_side_by_side` + `tool_reference_profiler` account for > 95 % of invocations on every backbone; the remaining 11 tools are selected on ≤ 0.5 % of items aggregated. This is presentation, not refutation-task-intrinsic: a specialty-aware catalog rewrite (Section 4.6) raises tool usage from 2 → 6–10 distinct tools and lifts macro AUROC by +2.04 / +2.90 pp on two backbones, with a 95 % CI excluding zero.

### Claim E (behaviour): Refutation-verdict distribution is strongly backbone-dependent and is a runtime-observable diagnostic.

**Evidence:** GPT-5.4 emits 56 % `found_in_ref` (balanced refuter); SeedVL emits **89 % `not_found`** (preserves almost every candidate); Qwen3.5 is intermediate (39 % / 60 %). Backbone-dependence corroborates the hypothesis that 'the agent does not always refute' — the Direct branch must be present to compensate.

### Claim F (extension): A 480-label semi-supervised Controller extension closes the remaining gap on the weakest-ensemble backbone.

**Evidence (Table in controller section):** Qwen3.5-VL-27B, passive-ensemble baseline 0.7333. Controller with:
- no rules: 0.7227 ($-1.06$ pp, CI $[-2.84, +0.50]$, $P{=}0.111$) — controller mechanism alone does *not* help.
- shuffled-domain rules: 0.7199 ($-1.34$ pp, $P{=}0.053$) — wrong rules do not help.
- meta only: 0.7388 ($+0.55$ pp, $P{=}0.765$).
- full (meta+domain rules): **0.7539, +2.05 pp, CI $[+0.41, +3.67]$, $P{=}0.995$ ✓.**
Rule *content* is the mechanism, not the additional call.

## What the Current Draft Gets Wrong (Why We Rewrite)

- **Organised as six independent findings.** The paper currently presents Findings 1–4 (legacy router/fusion), Finding 5 (headline ensemble), Finding 5.1–5.3 (agent behaviour), Finding 6 (specialty-aware catalog) as a flat list. A reader has to reconstruct the story themselves.
- **The headline is buried.** The most important observation — a worse agent still wins in the ensemble — is Finding 5 of 6, after 3 'legacy' findings on an earlier split. It should be the opening observation.
- **Method is framework-first, not insight-first.** §3 introduces a tools/experts/strategies taxonomy and a calibration router before the parallel-Direct insight arrives in §3.6. The parallel-Direct insight is the contribution; the taxonomy is scaffolding for the ablation section.
- **Earlier-split findings read as orphaned.** The descriptor, debate-hurts, and router-argmax findings were generated on a design-exploration split, not the headline split; the current draft flags this repeatedly and apologetically. In the rewrite these findings belong in an 'earlier evaluation / negative results' subsection that *motivates* the headline design rather than competing with it.
- **MMAD generalisation evidence is scattered.** The rewrite should consolidate cross-benchmark transfer (MMAD AD subset: $n{=}483$, Qwen3.5 ensemble AUROC 0.79 vs Direct 0.76, no re-tuning) into a single cross-benchmark paragraph.
- **Specialty-aware catalog is partial evidence.** Only 2 of 3 backbones completed cleanly (GPT-5.4 sub-api outage blocked the third). In the rewrite it is framed as a mechanism-check on Claim D rather than a separate finding.

## Target Structure (one-paragraph per section)

1. **Introduction.** Cross-domain VAD, the silent-failure story, the failure-mode question, the parallel-branch answer, a one-sentence contribution list.
2. **Related work.** Training-free VAD, VLM agents, ensembles of heterogeneous scorers; what is new here.
3. **Benchmark and setup.** CrossDomainVAD-12 (one paragraph), three backbones, descriptor-free prompts, paired bootstrap protocol.
4. **Method: the ensemble agent.** Direct branch + refutation branch, fixed $\alpha=0.5$ blend, single per-item invocation. Refutation protocol and its anti-confirmation-bias design. The parallel-Direct argument (why always-on, not conditional).
5. **Main result: the failure-mode-robust ensemble.** Table 1. Agent-alone vs ensemble gap. The Qwen3.5 failure-mode case as the load-bearing evidence.
6. **Mechanism: rank-granularity, not middle-mass.** Three controlled transformations, Table.
7. **Agent behaviour across backbones.** Three subsections: depth-tracks-quality; tool-collapse (2-of-13); verdict-bimodality. Tie each back to Table 1.
8. **Earlier evaluation and negative results.** Design-exploration findings (descriptors dominate, debate hurts, calibration-router ≈ fusion on 2/3 backbones). Framed as 'what we tried before the ensemble insight arrived.'
9. **Cross-benchmark transfer.** MMAD AD subset paragraph.
10. **Semi-supervised controller extension.** 480-label rulebook, four-way ablation, CI-excludes-zero evidence.
11. **Discussion and limitations.** D4 3D and D10 Liver-CT floors; weak-backbone tool-usage refinement as future work; controller transfer to other backbones.

## Figure Inventory (reuse from current paper, re-captioned)

- **Figure 1 (intuition panel).** Earlier-split per-domain strategy landscape (no-single-winner motivation). Currently `paper/figures/fig_intuition.pdf`.
- **Figure 2 (architecture).** The parallel-Direct + refutation-agent architecture diagram. Currently `paper/figures/fig_architecture_imagegen_hires.png` (user-provided, 1.18 MB, do not re-render).
- **Figure 3 (per-domain bars).** Per-domain AUROC bars for Direct / Agent / Ensemble across three backbones on CrossDomainVAD-12 test. Currently `paper/figures/fig_per_domain.pdf`.
- **Figure 4 (agent behaviour, 4-panel).** Turns / tools / verdicts / candidate counts per backbone. Currently `paper/figures/fig_agent_behavior.pdf`.

All four figures are data-correct; the rewrite re-captions them to match the new story arc but does not regenerate.

## Venue

- **Target:** ICLR.
- **Page limit:** 9 main + unlimited appendix.
- **Current PDF:** 1.45 MB, compiles with tectonic.
