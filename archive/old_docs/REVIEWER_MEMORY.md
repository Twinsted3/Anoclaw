# Reviewer Memory

## Context for Review
This is a fresh review of the AnomaClaw paper for a top ML venue (NeurIPS/ICML level).

**Author's stated main contribution**: Generality — using an agent approach to solve common problems of MLLM-based visual anomaly detection. Multi-domain is NOT the main innovation point; the cross-domain benchmark is supporting evidence.

**Key MLLM problems the system claims to address**:
1. Lack of quantitative grounding (VLMs cannot compute patch distances)
2. Hallucination and missed subtle anomalies
3. Domain-blind reasoning (no domain-specific calibration)

**Previous review history** (from earlier rounds, different framing):
- Round 1 (5/10): Expert too weak, agent contribution unsupported, universal claim too broad
- Round 2 (6.5/10): Expert-as-context validated, causal claim unproven
- Round 3 (7/10): Causality confirmed, but fusion alphas were test-set oracle
- Round 4 (7.5/10): Cal-tuned fusion validated, approved with minor cleanup

**Current review focus**: The paper needs re-evaluation under the NEW framing — is the "agent solving MLLM problems" story coherent, well-supported, and novel enough for a top venue?

## Round 1 (Session 2) — Score: 4.5/10
- **Suspicion**: Authors may relabel the fixed winning pipeline as "agentic" after abandoning the actual multi-agent systems
- **Suspicion**: Silent filtering from 12-domain raw manifest to 10-domain final benchmark
- **Suspicion**: Mixed token accounting in Pareto plot
- **Suspicion**: Overclaiming logical-family benefits when fusion slightly hurts D9 (0.7919 vs 0.7957)
- **Suspicion**: "Generality" claims are hand-engineered via per-domain knowledge and manual family labels
- **Unresolved**: Code-paper mismatches (FAISS claim, sigmoid calibration, domain-identical claim)
- **Key finding**: The "agent" thesis is NOT supported by the winning system. Reviewer suggests reframing to "training-free expert-grounded VLM hybrid for cross-domain VAD"

## Round 2 (Session 2) — Score: 6.2/10
- **Verified**: Agent thesis dropped, FAISS fixed, domain-identical fixed, D6/D8 disclosed, causal gain honestly reported
- **NEW suspicion**: Paper says VLM sees sigmoid-calibrated score, but code injects raw_patch_distance — fixed in Round 2
- **Suspicion**: "Limitation 3 solved" narrative overclaims — domain calibration is just manual family labels + small post-hoc fusion
- **Suspicion**: Final 10-domain pipeline not fully reproducible from repo — fixed with reproduce_final_results.py
- **Unresolved**: Figure placeholders still blocking; novelty vs EAGLE/AgentIAD still weak

## Round 3 (Session 2) — Score: 7.2/10
- **Resolved**: Figure placeholders replaced with real figures
- **Resolved**: Expert text channel matches code
- **Resolved**: Reproduction script works, benchmark filtering reproducible
- **NEW**: CI upper bound was stale (0.939 vs verified 0.937) — fixed
- **NEW**: EAGLE bib entry was placeholder — fixed with proper metadata
- **Persistent**: Novelty positioning borderline but adequate for workshop/second-tier; may need strengthening for NeurIPS
- **Persistent**: Final method is post-hoc reconstructed, not single canonical pipeline
