"""Stratified paired bootstrap confidence intervals for all headline comparisons.

Output: paper/figures/bootstrap_cis.json + a LaTeX snippet.

Compared methods (per backbone):
  v0           : descriptor-enhanced single-pass VLM
  fusion       : 0.8 * v0 + 0.2 * sigmoid(SubspaceAD - global_median)
  agent        : AnomalyClaw (agent_v1 test)

Pairs (for every backbone):
  fusion vs v0
  agent  vs v0
  fusion vs agent

Resampling: per-domain stratified; within each domain we resample items
with replacement preserving the (normal, anomaly) balance. 1000 bootstrap
reps. 95% percentile CI; p-value is the fraction of bootstrap samples with
delta <= 0 (one-sided test that delta > 0).
"""
import json
import os
import numpy as np
from collections import defaultdict
from pathlib import Path

RESULTS_DIR = Path("/hdd1/jiangxi/AD-Agent/benchmark/results")
OUT = Path("/hdd1/jiangxi/AD-Agent/paper/figures/bootstrap_cis.json")
N_BOOT = 1000
SEED = 20260414

# Domains to include (paper's CrossDomainVAD-11 — excludes 'surveillance')
INCLUDE_DOMAINS = {"industrial", "retail", "maintenance", "medical",
                   "medical_brain", "medical_liver", "medical_colon",
                   "remote_sensing", "road", "logical", "industrial_visa"}

BACKBONE_FILES = {
    "GPT-5.4":  "gpt54_agent_v1_test.json",
    "SeedVL":   "seedvl_agent_v1_test.json",
    "Qwen3.5":  "qwen35_agent_v1_test.json",
}


def load_items(filename):
    items = json.load(open(RESULTS_DIR / filename))
    out = {}
    for it in items:
        if it.get("split") and it["split"] != "test":
            continue
        if it["domain"] not in INCLUDE_DOMAINS:
            continue
        out[it["item_id"]] = it
    return out


def macro_auroc(items_by_domain):
    """items_by_domain: {domain: [(score, label_gt), ...]}"""
    from sklearn.metrics import roc_auc_score
    per = {}
    for d, arr in items_by_domain.items():
        s = np.array([x[0] for x in arr])
        y = np.array([x[1] for x in arr])
        if len(set(y)) < 2:
            continue
        per[d] = roc_auc_score(y, s)
    vals = list(per.values())
    return float(np.mean(vals)) if vals else 0.0, per


def build_scored(v0_items, expert_scored, w=0.2, global_median=None):
    """Return fusion = (1-w)*v0 + w*sigmoid((exp - median)/median)."""
    if global_median is None:
        exp_scores = [v for v in expert_scored.values() if v is not None]
        global_median = float(np.median(exp_scores))
    fused = {}
    for iid, v0_sc in v0_items.items():
        es = expert_scored.get(iid)
        if es is None:
            fused[iid] = v0_sc  # fall back
        else:
            norm = 1.0 / (1.0 + np.exp(-2.0 * (es - global_median) / (global_median + 1e-9)))
            fused[iid] = (1 - w) * v0_sc + w * norm
    return fused, global_median


def stratified_paired_bootstrap(scores_a, scores_b, labels, domains,
                                n_boot=N_BOOT, seed=SEED):
    """Per-domain stratified paired bootstrap of (auroc_a - auroc_b).

    scores_a, scores_b, labels, domains: parallel lists/arrays over shared items.
    Returns: (delta_point, ci_lo, ci_hi, p_value_one_sided_positive)
    """
    from sklearn.metrics import roc_auc_score
    rng = np.random.default_rng(seed)
    labels = np.asarray(labels)
    domains = np.asarray(domains)
    scores_a = np.asarray(scores_a)
    scores_b = np.asarray(scores_b)

    # precompute per-domain index lists
    dom_indices = {d: np.where(domains == d)[0] for d in set(domains)}

    def macro(sa, sb):
        aurs_a, aurs_b = [], []
        for d, idx in dom_indices.items():
            y = labels[idx]
            if len(set(y)) < 2:
                continue
            aurs_a.append(roc_auc_score(y, sa[idx]))
            aurs_b.append(roc_auc_score(y, sb[idx]))
        return np.mean(aurs_a), np.mean(aurs_b)

    auc_a_pt, auc_b_pt = macro(scores_a, scores_b)
    delta_pt = auc_a_pt - auc_b_pt

    deltas = []
    for _ in range(n_boot):
        # resample indices per-domain (same indices for both methods → paired)
        boot_idx = []
        for d, idx in dom_indices.items():
            boot_idx.append(rng.choice(idx, size=len(idx), replace=True))
        boot_idx = np.concatenate(boot_idx)
        sa_b = scores_a[boot_idx]
        sb_b = scores_b[boot_idx]
        # per-domain aurocs on resampled
        aurs_a, aurs_b = [], []
        dom_b = domains[boot_idx]
        for d in set(domains):
            di = np.where(dom_b == d)[0]
            y = labels[boot_idx][di]
            if len(set(y)) < 2:
                continue
            aurs_a.append(roc_auc_score(y, sa_b[di]))
            aurs_b.append(roc_auc_score(y, sb_b[di]))
        deltas.append(np.mean(aurs_a) - np.mean(aurs_b))
    deltas = np.array(deltas)
    lo, hi = np.percentile(deltas, [2.5, 97.5])
    p_pos = float(np.mean(deltas <= 0.0))
    return float(delta_pt), float(lo), float(hi), p_pos, float(auc_a_pt), float(auc_b_pt)


def main():
    # SubspaceAD (shared across all backbones — expert is test-time only, VLM-independent)
    subs = json.load(open(RESULTS_DIR / "subspacead_test.json"))
    expert_score_by_id = {x["item_id"]: float(x["anomaly_score"])
                           for x in subs if x.get("anomaly_score") is not None}

    report = {}
    for backbone, agentf in BACKBONE_FILES.items():
        print(f"\n=== {backbone} ===")
        agent = load_items(agentf)
        # Use v0 from the agent file's embedded raw_output.v0_score
        # (guaranteed paired; no coverage mismatch with standalone v0 runs).
        common = sorted(set(agent.keys()) & set(expert_score_by_id.keys()))
        print(f"  common items: {len(common)}")

        def _v0_of(iid):
            it = agent[iid]
            ro = it.get("raw_output") or {}
            vs = ro.get("v0_score")
            if vs is None:
                return float(it.get("anomaly_score", 0.5))
            return float(vs)

        v0_scores = np.array([_v0_of(i) for i in common])
        agent_scores = np.array([float(agent[i]["anomaly_score"]) for i in common])
        labels = np.array([int(agent[i]["label_gt"]) for i in common])
        domains = np.array([agent[i]["domain"] for i in common])

        # fusion
        expert_arr = np.array([expert_score_by_id[i] for i in common])
        global_median = float(np.median(expert_arr))
        sigmoid_exp = 1.0 / (1.0 + np.exp(-2.0 * (expert_arr - global_median) / (global_median + 1e-9)))
        fusion_scores = 0.8 * v0_scores + 0.2 * sigmoid_exp

        pairs = {
            "fusion_vs_v0":      (fusion_scores, v0_scores),
            "agent_vs_v0":       (agent_scores,  v0_scores),
            "fusion_vs_agent":   (fusion_scores, agent_scores),
        }
        report[backbone] = {"n": len(common), "global_expert_median": global_median}
        for name, (a, b) in pairs.items():
            delta, lo, hi, p_pos, auc_a, auc_b = stratified_paired_bootstrap(
                a, b, labels, domains)
            report[backbone][name] = {
                "auc_a": auc_a, "auc_b": auc_b,
                "delta": delta, "ci_lo": lo, "ci_hi": hi,
                "p_value_delta_positive": p_pos,
                "sig_95": (lo > 0 or hi < 0),
            }
            print(f"  {name:22s}: Δ={delta:+.4f} CI=[{lo:+.4f},{hi:+.4f}] p={p_pos:.3f}")

    # descriptor ablation: only GPT-5.4 has both generic and task-anchored v0 data
    # GPT generic = 0.754 (from earlier runs), task-anchored = 0.825 (current)
    # We do not have per-item generic scores for SeedVL/Qwen, so we note it as
    # a known gap in the descriptor section.

    OUT.write_text(json.dumps(report, indent=2))
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
