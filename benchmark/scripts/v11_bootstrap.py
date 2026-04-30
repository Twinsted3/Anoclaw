"""Stratified paired bootstrap CI for v11 controller vs v10 blend on manifests_v2 test.

Reads benchmark/results/verbalized/v11_eval_test/D*.json, for each item extracts:
  - v9_score, direct_score       → v10 blend = 0.5 * (v9 + direct)
  - anomaly_score                → v11 controller final
  - label_gt                     → ground truth
  - domain_code                  → stratum

Computes macro AUROC on both series, then draws B paired stratified bootstrap
resamples (items sampled with replacement within each domain stratum; same
resampled index set used for both v10 blend and v11). Reports macro delta CI
and posterior mass P(delta > 0).

Usage:
  python v11_bootstrap.py [--bootstraps 1000] [--dir benchmark/results/verbalized/v11_eval_test]
"""
from __future__ import annotations
import argparse, json, os, sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score


def load_items(directory: str):
    """Return {domain_code: list of (gt, v9, direct, v11)} plus per-domain item order."""
    out = defaultdict(list)
    for p in sorted(Path(directory).glob("D*.json")):
        results = json.load(open(p))
        for x in results:
            gt = x.get("label_gt")
            score = x.get("anomaly_score")
            if gt is None or score is None:
                continue
            v9 = x.get("v9_score") if x.get("v9_score") is not None else score
            dv = x.get("direct_score") if x.get("direct_score") is not None else score
            out[x["domain_code"]].append((int(gt), float(v9), float(dv), float(score)))
    return dict(out)


def macro_auroc(per_domain_scores, score_idx: int) -> float:
    """score_idx: 1=v9, 2=direct, 3=v11. Always use idx 0 as gt."""
    aucs = []
    for dc, rows in per_domain_scores.items():
        gts = [r[0] for r in rows]
        sc = [r[score_idx] for r in rows]
        if len(set(gts)) < 2:
            continue
        aucs.append(roc_auc_score(gts, sc))
    return float(np.mean(aucs))


def blend_series(rows):
    return [(r[0], 0.5 * r[1] + 0.5 * r[2]) for r in rows]


def macro_auroc_blend(per_domain):
    aucs = []
    for dc, rows in per_domain.items():
        bs = blend_series(rows)
        gts = [r[0] for r in bs]
        sc = [r[1] for r in bs]
        if len(set(gts)) < 2:
            continue
        aucs.append(roc_auc_score(gts, sc))
    return float(np.mean(aucs))


def bootstrap_paired(per_domain, B: int, seed: int = 0):
    """Stratified paired bootstrap. Resample items within each domain; compute
    macro AUROC for blend and v11 on the same resampled indices."""
    rng = np.random.default_rng(seed)
    deltas = []
    blends_mu = []
    v11s_mu = []
    domains = sorted(per_domain.keys())
    # Pre-extract arrays for speed
    dom_arrays = {}
    for dc in domains:
        rows = per_domain[dc]
        arr = np.array([(r[0], 0.5*r[1]+0.5*r[2], r[3]) for r in rows])
        dom_arrays[dc] = arr

    for b in range(B):
        blend_aucs = []
        v11_aucs = []
        for dc in domains:
            arr = dom_arrays[dc]
            n = len(arr)
            idx = rng.integers(0, n, size=n)
            sub = arr[idx]
            gts = sub[:, 0].astype(int)
            if len(np.unique(gts)) < 2:
                continue  # skip degenerate resample for this domain
            blend_aucs.append(roc_auc_score(gts, sub[:, 1]))
            v11_aucs.append(roc_auc_score(gts, sub[:, 2]))
        if not blend_aucs:
            continue
        mb = float(np.mean(blend_aucs)); mv = float(np.mean(v11_aucs))
        blends_mu.append(mb); v11s_mu.append(mv); deltas.append(mv - mb)
    return np.array(deltas), np.array(blends_mu), np.array(v11s_mu)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="benchmark/results/verbalized/v11_eval_test")
    ap.add_argument("--bootstraps", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    per_domain = load_items(args.dir)
    if not per_domain:
        print(f"No data in {args.dir}")
        sys.exit(1)

    print(f"Loaded {sum(len(v) for v in per_domain.values())} items across "
          f"{len(per_domain)} domains")
    # Per-domain breakdown
    for dc in sorted(per_domain.keys()):
        rows = per_domain[dc]
        gts = [r[0] for r in rows]
        v9 = roc_auc_score(gts, [r[1] for r in rows]) if len(set(gts))>1 else float('nan')
        dr = roc_auc_score(gts, [r[2] for r in rows]) if len(set(gts))>1 else float('nan')
        bl = roc_auc_score(gts, [0.5*r[1]+0.5*r[2] for r in rows]) if len(set(gts))>1 else float('nan')
        v11 = roc_auc_score(gts, [r[3] for r in rows]) if len(set(gts))>1 else float('nan')
        print(f"  {dc:<4} n={len(rows):>4}  direct={dr:.4f}  v9={v9:.4f}  blend={bl:.4f}  v11={v11:.4f}  Δ={(v11-bl)*100:+.2f}pp")

    blend_macro = macro_auroc_blend(per_domain)
    v11_macro = macro_auroc(per_domain, 3)
    direct_macro = macro_auroc(per_domain, 2)
    v9_macro = macro_auroc(per_domain, 1)

    print(f"\nMacro AUROC (point estimate):")
    print(f"  direct  = {direct_macro:.4f}")
    print(f"  v9      = {v9_macro:.4f}")
    print(f"  blend   = {blend_macro:.4f}  (== v10)")
    print(f"  v11     = {v11_macro:.4f}")
    print(f"  Δ v11−blend = {(v11_macro-blend_macro)*100:+.2f}pp")

    print(f"\nBootstrap ({args.bootstraps} resamples, seed={args.seed}, stratified paired):")
    deltas, blends_mu, v11s_mu = bootstrap_paired(per_domain, args.bootstraps, args.seed)
    if len(deltas) == 0:
        print("  no valid resamples")
        return
    lo, hi = np.percentile(deltas*100, [2.5, 97.5])
    p_pos = float(np.mean(deltas > 0))
    print(f"  mean Δ    = {np.mean(deltas)*100:+.2f}pp")
    print(f"  median Δ  = {np.median(deltas)*100:+.2f}pp")
    print(f"  95% CI    = [{lo:+.2f}, {hi:+.2f}] pp")
    print(f"  P(Δ>0)    = {p_pos:.3f}")
    print(f"  blend mean  = {blends_mu.mean():.4f}")
    print(f"  v11 mean    = {v11s_mu.mean():.4f}")


if __name__ == "__main__":
    main()
