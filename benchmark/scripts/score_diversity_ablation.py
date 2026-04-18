"""Controlled ablation: does middle-zone mass CAUSE ensemble gain, or
is it correlated with something else (standalone AUROC, error
complementarity)?

Transformations applied to the v6.5 agent's scores and the v8 agent's
scores on Qwen3.5 test (post-hoc, no new inference):

  v6-BIN:   quantize v6.5 scores to {0.05, 0.95} (remove middle mass).
  v8-SOFT:  remap v8 scores through a sigmoid-compressing function to
            inflate middle mass (Platt-like): x → 0.5 + (x-0.5)/2.
  SHUFFLE:  random middle-mass control — replace v6.5 scores with
            uniform[0.2, 0.8] noise. Measures whether random middle
            mass alone helps the ensemble.

If the score-diversity hypothesis holds:
  - v6-BIN + Direct should drop toward Direct alone (loses middle mass).
  - v8-SOFT + Direct should rise toward v6 + Direct (gains middle mass).
  - SHUFFLE + Direct should give ZERO gain (random noise has no signal).

We also report rank correlation and per-item error complementarity
between the base scores as supplementary diagnostics.
"""
from __future__ import annotations
import json
import numpy as np
from sklearn.metrics import roc_auc_score
from scipy.stats import spearmanr
from collections import defaultdict


def macro(items, get_score):
    by_d = defaultdict(list)
    for x in items:
        if x.get("label_gt") is None:
            continue
        by_d[x["domain_code"]].append(x)
    aurocs = []
    for d, it in by_d.items():
        y = [i["label_gt"] for i in it]
        s = [get_score(i) for i in it]
        if len(set(y)) > 1:
            aurocs.append(roc_auc_score(y, s))
    return float(np.mean(aurocs))


def main():
    direct = {x["item_id"]: x for x in
              json.load(open("benchmark/results/v6_direct_qwen3_test.json"))}
    v65 = {x["item_id"]: x for x in
           json.load(open("benchmark/results/v6_5_agent_qwen3_test.json"))}
    v8 = {x["item_id"]: x for x in
          json.load(open("benchmark/results/v8_qwen3_test.json"))}

    # Common item set
    items = [x for x in direct.values() if x["item_id"] in v65 and x["item_id"] in v8]
    print(f"n={len(items)}")

    def quantize_v65(i):
        s = v65[i["item_id"]]["anomaly_score"]
        return 0.05 if s < 0.5 else 0.95

    rng = np.random.default_rng(42)
    rand_map = {i["item_id"]: rng.uniform(0.2, 0.8) for i in items}
    def shuffle_val(i):
        return rand_map[i["item_id"]]

    # Also compute a "preserve rank, binarize to 0.05/0.95" for v65 AND a
    # sigmoid-compressed v8 that preserves rank but squeezes into [0.2, 0.8]
    v65_scores = np.array([v65[i["item_id"]]["anomaly_score"] for i in items])
    v8_scores = np.array([v8[i["item_id"]]["anomaly_score"] for i in items])
    # v65-bin: map median-split to {0.05, 0.95}
    v65_med = np.median(v65_scores)
    def v65_bin(i):
        return 0.95 if v65[i["item_id"]]["anomaly_score"] > v65_med else 0.05
    # v8-soft: sigmoid compression, preserves rank
    # y = 0.5 + (x - 0.5) / 2  ⇒ maps [0,1] to [0.25, 0.75]
    def v8_soft(i):
        x = v8[i["item_id"]]["anomaly_score"]
        return 0.5 + (x - 0.5) / 2

    # Headline AUROCs
    print()
    print("=== Standalone AUROCs ===")
    for name, fn in [("Direct",                lambda i: direct[i["item_id"]]["anomaly_score"]),
                     ("v6.5 original",         lambda i: v65[i["item_id"]]["anomaly_score"]),
                     ("v6.5 BIN (rank-preserving {0.05,0.95})", v65_bin),
                     ("v8 original",           lambda i: v8[i["item_id"]]["anomaly_score"]),
                     ("v8 SOFT (compressed to [0.25,0.75])", v8_soft),
                     ("RANDOM middle-mass",    shuffle_val)]:
        m = macro(items, fn)
        print(f"  {name:45s} {m:.4f}")

    print()
    print("=== 0.5 × Direct + 0.5 × X ===")
    for name, fn in [("v6.5 original",           lambda i: v65[i["item_id"]]["anomaly_score"]),
                     ("v6.5 BIN",                v65_bin),
                     ("v8 original",             lambda i: v8[i["item_id"]]["anomaly_score"]),
                     ("v8 SOFT",                 v8_soft),
                     ("RANDOM middle-mass",      shuffle_val),
                     ("v6.5 original * Direct (geomean)", lambda i: (direct[i["item_id"]]["anomaly_score"] * v65[i["item_id"]]["anomaly_score"])**0.5)]:
        def blend(i, fn=fn):
            return 0.5 * direct[i["item_id"]]["anomaly_score"] + 0.5 * fn(i)
        m = macro(items, blend)
        print(f"  0.5 Direct + 0.5 {name:45s} {m:.4f}")

    # Middle-zone mass computation
    print()
    print("=== Middle-zone mass and std ===")
    for name, vals in [
        ("Direct",         np.array([direct[i["item_id"]]["anomaly_score"] for i in items])),
        ("v6.5 original",  v65_scores),
        ("v6.5 BIN",       np.array([v65_bin(i) for i in items])),
        ("v8 original",    v8_scores),
        ("v8 SOFT",        np.array([v8_soft(i) for i in items])),
        ("RANDOM",         np.array([shuffle_val(i) for i in items])),
    ]:
        mid = ((vals >= 0.2) & (vals <= 0.8)).mean() * 100
        print(f"  {name:45s} mean={vals.mean():.3f} std={vals.std():.3f} mid%={mid:.1f}")

    # Rank correlation and error complementarity diagnostics
    print()
    print("=== Rank correlation (Spearman ρ) with Direct ===")
    dr = np.array([direct[i["item_id"]]["anomaly_score"] for i in items])
    for name, s in [("v6.5 original", v65_scores), ("v6.5 BIN", np.array([v65_bin(i) for i in items])),
                     ("v8 original", v8_scores), ("v8 SOFT", np.array([v8_soft(i) for i in items])),
                     ("RANDOM",      np.array([shuffle_val(i) for i in items]))]:
        rho, _ = spearmanr(dr, s)
        print(f"  {name:45s} ρ={rho:.3f}")

    print()
    print("=== Per-item error complementarity ===")
    y = np.array([i["label_gt"] for i in items])
    dr_err = np.abs(dr - y)
    for name, s in [("v6.5 original", v65_scores), ("v6.5 BIN", np.array([v65_bin(i) for i in items])),
                     ("v8 original", v8_scores), ("v8 SOFT", np.array([v8_soft(i) for i in items])),
                     ("RANDOM",      np.array([shuffle_val(i) for i in items]))]:
        err = np.abs(s - y)
        cos = np.dot(dr_err, err) / (np.linalg.norm(dr_err) * np.linalg.norm(err) + 1e-12)
        print(f"  {name:45s} error-cos with Direct = {cos:.3f}")


if __name__ == "__main__":
    main()
