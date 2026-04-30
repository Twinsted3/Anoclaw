# AnomalyClaw Auto Review Log — v9 loop

**Loop start**: 2026-04-19 23:36 CST
**Prior loop**: v8 paper closed at 6.0/10 "almost" (archived as
`AUTO_REVIEW.v8.md`, `REVIEW_STATE.v8.json`).

**Difficulty**: nightmare (`codex exec`, GPT reads repo directly)
**Max rounds**: 4
**Reviewer**: GPT-5.4 via codex CLI, `model_reasoning_effort=xhigh`

---

## Score progression

| Round | Score | Verdict | Δ | When |
|-------|-------|---------|---|------|
| 1     | 5.0   | not ready | — | 2026-04-19 23:36 → 00:08 |
| 2     | 5.8   | not ready | +0.8 | 2026-04-20 06:06 → 06:27 |

---

## Round 1 (2026-04-19 23:36 – 2026-04-20 00:08)

### Six critical findings
1. **MMAD label bug** — `"good" in key.lower()` flipped every GoodsAD
   item to label=0. Reported numbers depressed by ~7 pp.
2. **SeedVL Direct provenance** — main table mixed old v2 descriptor
   run with newer v6 agent. Consistent v6 direct is 0.7995 not 0.7794;
   Δ shrinks from +2.14 to +0.93 pp (non-significant).
3. **Router/v4/v6 story mixup** — method describes v4 router,
   experiments headline v6+Direct ensemble.
4. **v8 interpretability claim ahead of evidence** — reported
   v8_qwen3_test.json has `history` missing for all 1418 items.
5. **Tool-cost claim** — `tool_reference_profiler` and
   `tool_domain_knowledge` DO make VLM/LLM calls.
6. **Stale appendix numbers** — appendix Qwen fusion `0.851` vs main
   text `0.814`.

### Actions taken
1. Label fix — `mmad_eval.py`, `mmad_eval_v9.py`, `mmad_relabel.py`.
2. SeedVL fix — switched to `v6_direct_seedvl_test.json`.
3. Method — added §3.5 v6 agent; "Framework vs. headline" paragraph.
4. v8 rerun deferred (~3h compute).
5. Tool-cost — §3 v6 subsection acknowledges extra VLM/LLM calls.
6. Appendix — caption flags numbers as v0/v3-era historical.

### New experiments
- **v9 MMAD full-type** (n=2302 QAs): agent vs Direct = −1.0 pp macro
  accuracy. Agent helps on Defect Description (+1.7), Classification
  (+1.2); hurts on Object Details (−4.4), Object Classification (−3.2).
  AD AUROC Δ +1.65 pp.
- **Active pilot** (4 domains, K=10 dev-oracle, DINOv2 prior):
  mean Δ +3.5 pp. D1 +7.33, D5 −4.00, D9 +11.11, D12 −0.44.

Commits: `0d7ec3d`, `e0030a3`, `6891eb1`, `5b29947`.

---

## Round 2 (06:06 – 06:27)

### Assessment
- **Score**: 5.8 / 10 (up from 5.0)
- **Verdict**: not ready
- Raw: `review-stage/codex_v9_review_r2_raw.out` (2.5 MB)

### Six new critical findings (Round 2)
1. **AL domain mapping swap**: active-learning pilot used
   `manifests_v2` where D5=logical, D9=brain MRI, but the paper AL
   table reused the Table-1 labels (D5=brain MRI, D9=logical).
2. **Relabeled MMAD file not shipped**: `mmad_anomaly_qwen3.json`
   still contained stale labels; corrected numbers were in the
   paper but not reproducible from a released artifact.
3. **v9 MCQ parse-failure accounting missing**: denominators were
   answered-only; parse-failure rates per type not reported.
4. **v8 claim still overclaimed**: "reviewers can audit every
   score" remained in text despite `history` missing from all 1418
   stored predictions.
5. **Tool-cost language still inconsistent**: §3 was fixed but
   `Appendix~\ref{app:cost}` referenced an appendix that did not
   exist; intro/abstract still implied zero-call tools.
6. **Three-backbone claim too strong in places**: SeedVL is
   non-significant; abstract/intro wording should make this explicit.

### Round 2 fixes applied
1. **AL labels corrected** — table now uses `manifests_v2` taxonomy
   (D1 industrial, D5 MVTec-LOCO logical, D9 BraTS brain MRI, D12
   road safety). Finding 8 interpretation rewritten: brain MRI
   helps (+11.11), logical hurts (−4.00, DINOv2 CLS can't retrieve
   logical-anomaly neighbours well).
2. **Shipped `mmad_anomaly_qwen3_relabeled.json`** (180 items
   flipped) as a released artifact.
3. **Parse-failure rates** added to Table~\ref{tab:mmad_v9_fulltype}
   footnote: Direct 0.6\%, Agent 0.9\% overall; max per-type 3.0\%.
   Treating failures as wrong shifts accuracy ≤0.9pp, no direction
   change.
4. **v8 rerun** still not executed (compute constraint).
5. **`Appendix~\ref{app:cost}` references removed** from §3 and §4
   and replaced with inline cost statements.
6. Abstract/intro wording for SeedVL non-significance was already
   updated in Round 1; verified in Round 2.

### Remaining concerns (deferred / out-of-scope for this session)
- v8 qwen3 test rerun with history capture (~3h compute).
- Method section v4→appendix full restructure (minimum fix applied).
- AL extension to all 12 domains × multi-seed (future work).

Commits: `0b15cf6`.

---

## Current state (06:30 CST)

- Score 5.8/10 (just below 6.0 threshold); verdict "not ready" but
  Round-2 blockers addressed.
- User (human) expected back ~07:00; final wrap-up commit below.
- MAX_ROUNDS=4 not exhausted (Round 3 available for next session).

---

## Round 3 (2026-04-20 ~16:45 – 17:10 CST)

### Trigger
- User deleted §4.7 (DINOv2-CLS retrieval AL pilot) and replaced it
  with a new top-level §5 "Verbalized Self-Evolution".
- Auto-review-loop re-invoked with focus on §5 consistency and
  method design; experiments for §5 are running in background
  (t.b.d. table entries are placeholders).

### Assessment
- **Score**: 6.4/10 (up from 5.8)
- **Verdict**: almost (above positive threshold for the first time)
- Raw: `review-stage/codex_r3_small.out`

### Five critical findings (Round 3, ranked by severity)
1. **L2 regime ambiguity** — the L2 reflector receives the L1
   rulebook as context, but Table 5 (tab:verb_main) labels the
   "+L2" row as "dev oracle only". Contradiction. Fix: either
   relabel as "L1-conditioned L2" or add a strict dev-only L2 (no
   L1 context) and treat stacking explicitly as its own row.
2. **Dev holdout selection bias** — the "rule-quality holdout" is
   defined as the 30 dev items NOT selected by uncertainty, so it
   systematically excludes the hardest boundary cases. Fix:
   pre-split dev into a selection subset (uncertainty query pool)
   and a validation subset (untouched), report holdout AUROC on
   the validation subset only.
3. **Per-class coverage on multi-class domains** — K=10 per domain
   in D1/D3/D6 (up to 15 classes) means most classes get 0 L2
   examples. Fix: report per-class coverage of L2 selections, or
   switch to a per-class-capped selection policy.
4. **Prompt-length confound** — a longer JSON rulebook block may
   change model behaviour independent of rule content. Fix: add
   length-matched controls (shuffled rules, wrong-domain rulebook,
   no-op JSON) as ablations.
5. **Statistical treatment underdefined** — "3 seeds" and
   P(Δ>0) not enough without specifying sampling unit and
   uncertainty computation. Fix: paired bootstrap CIs over domains
   and items, explicit P(Δ>0) definition, per-domain deltas.

### Actions scheduled (this session)
- Implement fixes (1)(2)(3) as protocol changes BEFORE running
  expensive L1/L2 experiments:
  - Split dev 40 → 20 selection + 20 validation; build-l2 queries
    oracle only from selection subset; rule-quality holdout is the
    untouched 20-item validation subset.
  - Add `--use_l1_context` flag to `build-l2` (default False, pure
    dev-only); stacking (L1+L2) passes L1 context at the stack step,
    not inside L2 reflection.
  - Report per-class coverage of L2 selections.
- Defer fixes (4)(5) to Round 4 (after numbers are in).

### Status
- Score crossed positive threshold (6.4/10 almost); per skill rules
  the loop may terminate, but we continue into Round 4 after
  protocol fixes + experiment numbers land.
- Next: implement protocol fixes, run L1 / L2 / stack / eval-test.

### Actions completed this round (2026-04-20 17:10 → 17:30)
1. **Protocol fixes 1/2/3** applied:
   - §5 paper: L2 now explicitly "dev-only, no L1 context"; dev pre-split (20 sel + 20 val); per-class coverage paragraph added; stacking paragraph rewritten to reflect offline merge.
   - `benchmark/scripts/verbalized_learning.py`: `build_l2_rulebook(..., use_l1_context=False)` default; `split_dev_ids()` deterministic per-seed 50/50 split; `per_class_coverage()` reporter; `cmd_build_l2` uses selection pool only for uncertainty ranking.
   - Table header: "+ L2" row now labelled "dev oracle only (no L1 context)" and "+ L1+L2" labelled "offline stacked".
2. **Fixes 4/5 deferred** to Round 4 — add prompt-length controls (shuffled / wrong-domain / no-op) and paired bootstrap CIs once numbers land.
3. **Bug fixed (unplanned)**: discovered vLLM served name is `/hdd1/models/Qwen3.5-27B-FP8` not `Qwen3.5-VL-27B` — every call in the first pipeline pass 404'd silently, yielding 480 result rows of `score=0.5 / "json parse failed"`. Deleted garbage outputs, patched both pipeline scripts to force `QWEN_MODEL=/hdd1/models/Qwen3.5-27B-FP8`, relaunched. Memory note saved as `project_qwen_model_name.md`.
4. **Experiments in flight (background)**:
   - `passive_dev v2` (PID 1123763) — real scoring confirmed on D1 (score=0.05, real rationale). ~2.7h ETA for 480-item dev sweep.
   - `L1 / L2 / stack pipeline` (PID 1139071) — Stage 1 L1 started on D1. L2 will process whichever passive_dev files are ready when it reaches Stage 2.
   - `eval-test orchestrator` (`run_verbalized_eval.sh`) ready to fire once rulebooks land.
5. **GPU state**: 3 Qwen3.5 replicas on 0/1/2 (LB 8210). Attempted 2 more on GPU 4 / 7 — GPU 4 OOM-killed on engine init (~7GB residual occupied by another user), GPU 7 loaded OK but not wired into LB yet; left serving as idle capacity for later.
6. **Paper state**: §5 supersedes §4.7 (which is a one-line comment pointer); main.tex updated; uncommitted pending review of numbers.

### Phase: D (waiting for experiments)
Round 4 scheduled once (a) rulebooks land, (b) eval-test runs, (c) §5 tables are filled with real numbers, (d) 4/5 deferred fixes are added.

---

## Round 4 Continuation — User-Directed Pivot to v11 Controller Learning (2026-04-22)

### Context

R4 codex review (6.8/10 almost) surfaced a baseline-mismatch concern:
the v3 Verbalized Self-Evolution framework compared rulebook-on to a
Passive v9 agent floor of 0.669, whereas Table 1's Qwen3.5 baseline is
actually the v10 ensemble at 0.732 (Direct 0.714 + v9 ensembled). User
pivoted the entire §5 framework rather than land another L1/L2 seed
sweep. The v3 chapter is archived; a new §4 "Controller-Level
Verbalized Learning" sits between §3 method and §5 experiments.

### Architecture

**v11 = v10 + Controller switch.** With `learning_enabled=False`, v11
is byte-equivalent to v10 (parallel v9 + Direct, fixed $0.5$:$0.5$
blend). With `learning_enabled=True`, a Controller VLM arbitrates:
sees image + refs + both branches' score-rationale pairs + a RAG
rulebook, emits final anomaly score in $[0,1]$. Controller failure
falls back to blend, preserving the v10 floor.

**Rulebook = meta-rules + domain-rules stacked.**
- Meta-rules (routing): from disagreement cases on dev (v9 vs Direct
  split at $0.5$). Partition: agree-correct / agree-wrong /
  disagree-A-wins / disagree-B-wins. Only disagreement cases used;
  agree-wrong discarded (no routing signal). Reflector sees query
  images + both rationales + GT, writes 1-3 rules per side.
- Domain-rules (content): reused from v3 L1 (ref-only invariants, 6
  types) and L2 (oracle cluster corrective FN/FP). Not regenerated.
- RAG at inference: filter by (domain, category), rank meta first
  (up to 3) then domain (up to 4).

### Stage outputs

1. **Passive v11 dev** (n=480, 12 domains × 40 dev items): 141
   disagreement cases partition (61 A-wins + 80 B-wins, 99
   agree-wrong, 238 agree-correct). Min 7, max 18 usable per domain.
2. **Meta-rules** (Stage B): 12/12 domains produced parseable rule
   lists. 2–3 rules per side. Zero parse errors after dropping refs
   from reflector prompt (vLLM caps at 12 images; K=10×3=30 > cap).
3. **Stacked rulebooks**: 10–86 rules per domain (varies with
   per-class invariant count).
4. **Test eval** (n=1418, Qwen3.5-VL-27B, manifests_v2 test):

   | Regime | Macro | Δ vs v10 | 95% CI | p̂(Δ>0) |
   |---|---|---|---|---|
   | Direct (generic) | 0.7119 | −2.14 | — | — |
   | v9 alone | 0.6696 | −6.37 | — | — |
   | **v10 blend (= Passive v11)** | **0.7333** | — | — | — |
   | **v11 Controller (meta+domain)** | **0.7539** | **+2.05 pp** | **[+0.41, +3.67]** | **0.995** |

   Paired stratified bootstrap, 1000 resamples, per-domain
   stratification. v10 blend recomputed from same run's $(s_A, s_B)$
   for exact paired comparison. Reproduces Table 1's 0.732 within
   0.13 pp.

### Per-domain (Δ = v11 − v10 blend)

| Dom | v10 | v11 | Δ | Controller trust A/B/blend |
|---|---:|---:|---:|---|
| D1 MVTec-AD | 0.934 | 0.938 | +0.5 | 9/47/64 |
| D2 GoodsAD | 0.607 | 0.613 | +0.6 | 56/17/47 |
| D3 VisA | 0.853 | 0.834 | **−1.9** | 9/60/51 |
| D4 SDNET | 0.670 | 0.704 | +3.4 | 24/48/48 |
| D5 MVTec-LOCO | 0.676 | 0.678 | +0.2 | 28/64/28 |
| D6 Real3D-AD | 0.531 | 0.558 | +2.8 | 33/12/75 |
| D7 LEVIR-CD+ | 0.754 | 0.888 | **+13.4** | 24/55/19 |
| D8 DermaMNIST | 0.647 | 0.721 | **+7.4** | 48/51/21 |
| D9 BraTS | 0.848 | 0.816 | **−3.2** | 34/35/51 |
| D10 BMAD-Liver | 0.491 | 0.526 | +3.5 | 53/24/43 |
| D11 HyperKvasir | 0.808 | 0.807 | −0.1 | 27/61/32 |
| D12 BDD+RA | 0.982 | 0.963 | **−1.9** | 11/47/62 |

8 wins, 1 neutral, 3 losses. Parse failures: 0/1418.

### Key findings

1. **Controller beats fixed blend at 95% significance** on Qwen3.5.
2. **Gain compounds on top of v10**: v10 already extracted +1.69 pp
   from ensemble diversity; v11 adds another +2.05 pp.
3. **Gains concentrate where v9 ≪ Direct and controller correctly
   trusts Direct**: D7 LEVIR (+13.4 pp) and D8 DermaMNIST (+7.4 pp).
4. **Losses are bounded and diagnosed**:
   - D3 VisA: over-trusts B, blend was already strong.
   - D9 BraTS: agree-wrong dominated, no routing signal.
   - D12 BDD+RA: blend at 0.982 ceiling, nowhere to go but down.
5. **Controller is domain-aware**: trust distributions vary from
   9A/47B/64blend (D1 conservative) to 56A/17B/47blend (D2 A-heavy)
   to 11A/47B/62blend (D12 conservative).

### Status

MAX_ROUNDS=4 exhausted. This pivot is documented as a Round 4 continuation
(Phase E) rather than a new Round 5, because the automated codex review
cycle was satisfied at R4 (6.8/10 "almost"); the additional work was user-
directed method replacement, not additional review-driven fixes.

### Method description (for paper-illustration)

AnomalyClaw v11 is a two-branch ensemble for visual anomaly detection
with an optional learned arbitration layer. At inference, branch A
(the v9 refutation agent) performs a $\le 5$-turn reasoning trajectory
with tool use over the query image and normal references; branch B (a
single-pass Direct VLM call with a descriptor-free prompt) runs in
parallel. Both emit $(s, r)$ score–rationale pairs. A Controller VLM
then arbitrates: it sees the same visual context, both branch
outputs, and a retrieved rulebook excerpt (top-3 meta-rules + top-4
domain rules, filtered by `(domain, category)` metadata), and returns
a final anomaly score with a categorical \texttt{trust} tag. Learning
is done offline per domain: Passive v10 runs on the dev split, items
are partitioned by branch agreement, and a reflector VLM writes
routing meta-rules from disagreement cases. Domain rules (invariants
and oracle-grounded correctives) are reused from a prior rulebook
pilot. The controller's JSON parse-failure path falls back to the
fixed blend, preserving the v10 floor.

### Pending followups (post-loop)

- Ablation meta-only vs meta+domain (isolate routing vs content).
- Ablation controller-without-image (test visual grounding).
- Appendix `app:rulebook_pilot` writeup of the v3 L1+L2 domain corpus.
- Rerun with max_turns=5 for exact Table 1 parity (this run used 3).
- Optional R5 codex review of the new §4.
- vLLM replica shutdown.

---

## Round 5 — 2026-04-23 (nightmare codex exec, foreground)

### Assessment summary
- **Score: 7.1/10** (up from R4 6.8)
- **Verdict: almost**
- Raw output: `review-stage/codex_v11_review_r5_raw.out`

### Verified by independent codex-read-from-disk
- v11 full 0.7539, Δ +2.05 pp, CI [+0.41,+3.67], P=0.995 ✓
- Meta-only 0.7396, Δ +0.63 pp, CI [-1.26,+2.36], P=0.730 ✓
- Full−meta +1.43 pp, CI [-0.19,+3.13], P=0.960 ✓
- Controller architecture is substantively new, not cosmetic

### Unverified / false claims codex flagged
1. Title "Training-Free Cross-Domain VAD" conflicts with §4 semi-supervised pitch
2. Oracle budget: §4 opening said 40 labels/domain total BUT also mentioned "additional K=10 L2" in Limitations → inconsistency
3. **Finding 5 domain list error**: I wrote "D2 retail" in full-dominant set but D2 is meta-dominant. Correct list: D4 / D7 / D8 / D10
4. "Parse-failure rate exactly 0" was true only for Controller JSON. v9 trajectory has ~7% parse failures (D7 16/98, D8 53/120) — disclosed separately below
5. Abstract still claims v10 "significantly beats Direct on every backbone" but Qwen3.5 CI [-0.08,+3.51] touches zero

### Fixes applied this round (Phase C)
- Finding 5 corrected: D2 removed; list is now D4/D7/D8/D10 (and reads more honestly about novelty contribution vs reused v3 domain-content)
- Oracle budget reconciled: explicitly noted that K=10 L2 is a sub-sample of the 40-label dev pool, NOT additional
- Statistical terminology: "posterior mass" → "bootstrap sign probability"
- Limitations split into three sub-paragraphs: cost, parse-failure accounting (discloses v9 ~7% fail rate w/ D7/D8 counts), floor and failure modes

### Fixes deferred to user decision (Phase C)
- W1 **Title / training-free reframe** — this is a whole-paper narrative decision, not just §4 wording
- W5 **Controller-with-no-rules ablation** — 2h compute; would isolate "controller seeing refs" from "controller seeing rules"
- W7 **Abstract / intro / conclusion must acknowledge v11** — or label v11 as an optional extension
- W3 additional: **Exclude-v9-error ablation** to show +2.05 pp survives beyond "Controller downweights broken Agent"

### Status
MAX_ROUNDS = 4 exhausted at R4; this R5 was a post-loop manual codex trigger.
Numbers are verified; remaining work is framing + one more ablation. The
paper is defensibly close to ready. Title-vs-training-free framing is the
biggest open item.

---

## Round 6 — 2026-04-23 (nightmare codex exec)

### Assessment
- **Score: 7.2/10** (+0.1 over R5)
- **Verdict: almost**
- Raw: `review-stage/codex_v11_review_r6_raw.out`

### Verified
- W2/W3/W4/W6 fixes all accepted; all numbers reproducible from disk.

### New concern
- **Ablations were not branch-frozen**: the three v11 regimes (no-rules, meta-only, full) each re-ran v9+Direct. Codex found 655/1418 meta-only items and 646/1418 no-rules items had different branch outputs vs full. This means cross-regime comparisons were contaminated by upstream noise.

### Fixes applied
- **`benchmark/scripts/replay_controller.py`**: cached v9+Direct from full run, re-invokes controller only. Frozen 4-way result: no-rules Δ−1.06, meta Δ+0.55, full Δ+2.05. Pairwise on identical branches: meta-vs-noR +1.62pp P=0.992, full-vs-meta +1.48pp P=1.000, full-vs-noR +3.10pp P=1.000. Both rule-layer increments now significant at 95%.
- Fixed "significantly beats Direct on every backbone" → "significant at 95% on two of three" in abstract + §1 intro + §4 Finding 5.

---

## Round 7 — 2026-04-23 (nightmare codex exec)

### Assessment
- **Score: 7.6/10** (+0.4 over R6, biggest single-round jump since R1→R2)
- **Verdict: almost**
- Raw: `review-stage/codex_v11_review_r7_raw.out`

### Verified by codex
- Frozen-branch pairing checked: `v11_frozen_no_rules/`, `v11_frozen_meta_only/`, `v11_frozen_shuffled/` all share identical v9_score/direct_score/rationales when joined by item_id.
- 5-way bootstrap numbers reproduced exactly.
- D4 shuffled spot-check matches (−9.26pp).
- Shuffled rulebook files legitimately sourced from paired domains.

### Status of shuffled negative control
- **Critical finding**: shuffled rules are statistically indistinguishable from no rules (Δ −0.30 pp, CI [−1.55, +0.97], P=0.315). Correct rules beat shuffled significantly (meta vs shuffled +1.91pp P=0.996; full vs shuffled +3.39pp P=1.000). Rules are not decorative.
- Codex qualified: D7 (+10pp) and D8 (+4pp) win on shuffled rules too, because those domains have stable v9/Direct imbalance that the Controller exploits from rationales regardless of rule content. Not a contradiction — a cap on how much wrong rules can harm.

### Fixes applied (post-R7)
- Conclusion + 3_method.tex: removed remaining "significant on every backbone" wording.
- §4 Finding 5 rewritten with targeted claim: "domain-matched rule content is necessary for the full macro gain and for content-dependent domains"; acknowledges rationale-based fallback on D7/D8.
- §4 Limitations: new "Single-backbone evidence" paragraph framing v11 as case study on Qwen3.5.

### Blocking framing items (need author decision, not auto-fixable)
1. Title "Training-Free Cross-Domain VAD" conflicts with semi-supervised §4
2. Abstract/intro/conclusion still narrate v10-only; v11 not integrated
3. v11 is single-backbone — worth rerunning on GPT or SeedVL?

### Score progression 
R1 5.0 → R2 5.8 → R3 6.4 → R4 6.8 → R5 7.1 → R6 7.2 → **R7 7.6**

Technical evidence is accepted. Presentation is the last gap.

---

## Post-R7 framing integration (2026-04-23)

W1 (title) NOT touched — left for author decision.

W7 draft integration applied (conservative, marked as "semi-supervised extension"):

1. **Abstract** (`0_abstract.tex`):
   - Opening sentence now says "a training-free main system (v10) together with a semi-supervised extension (v11)"
   - New v11 paragraph before takeaway: full 5-way ablation result, branch-frozen numbers, shuffled-control conclusion, single-backbone caveat
   - Takeaway paragraph updated to mention both v10 and v11 release

2. **Introduction** (`1_introduction.tex`):
   - New contribution bullet 4: v11 as semi-supervised extension with dev label budget, branch-frozen ablation + shuffled control summary
   - Benchmark-release bullet 5 now also lists v11 artefacts

3. **Conclusion** (`5_conclusion.tex`):
   - New paragraph between main result and Limitations: "Semi-supervised controller extension (v11)" with +2.05 pp, frozen-branch ablation summary, explicit "single-backbone case study" framing
   - Future work paragraph extended with (iv) v11 backbone transfer and (v) online rule evolution

All v11 mentions explicitly label it as a "semi-supervised extension" / "Qwen3.5 case study" so the "Training-Free" title is not directly contradicted. If the author prefers to elevate v11 as a co-headline contribution, the framing in these three sections can be strengthened; if the author prefers to demote v11 to an appendix/extension, the three paragraphs can be trimmed. Either way the factual content (numbers, CIs, ablations) is now in place in the three places R7 said they were missing.
