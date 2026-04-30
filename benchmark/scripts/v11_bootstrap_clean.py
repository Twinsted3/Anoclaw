"""Sensitivity check: bootstrap v11 vs blend on the subset of items where
the v9 trajectory succeeded (no 'malformed JSON after retries' error).

Responds to R5 reviewer concern: part of the +2.05 pp gain may come from
the Controller downweighting broken v9 outputs (v9_score=0.5 fallback).
Excluding those items tests whether the gain survives on the clean
v9+Direct disagreement signal alone.
"""
from __future__ import annotations
import argparse, json, os
from pathlib import Path
import numpy as np
from sklearn.metrics import roc_auc_score


V9_ERROR = "malformed JSON after retries"


def load_data(directory, exclude_v9_error=True):
    out = {}
    for p in sorted(Path(directory).glob("D*.json")):
        d = p.stem
        rows = json.load(open(p))
        clean = []
        dropped = 0
        for x in rows:
            gt = x.get("label_gt")
            if gt is None:
                continue
            v9 = x.get("v9_score")
            dv = x.get("direct_score")
            if v9 is None or dv is None:
                continue
            if exclude_v9_error and V9_ERROR in (x.get("error") or ""):
                dropped += 1
                continue
            blend = 0.5 * v9 + 0.5 * dv
            final = x.get("anomaly_score", blend)
            clean.append((int(gt), float(blend), float(final)))
        if clean:
            out[d] = (np.array(clean), dropped)
    return out


def macro_auc(per_domain, col):
    aucs = []
    for d, (arr, _) in per_domain.items():
        gts = arr[:, 0].astype(int)
        if len(np.unique(gts)) < 2:
            continue
        aucs.append(roc_auc_score(gts, arr[:, col]))
    return float(np.mean(aucs))


def bootstrap(per_domain, B=1000, seed=0):
    rng = np.random.default_rng(seed)
    blend_d, final_d = [], []
    for b in range(B):
        bl_a, fi_a = [], []
        for d, (arr, _) in per_domain.items():
            n = len(arr)
            idx = rng.integers(0, n, size=n)
            sub = arr[idx]
            gts = sub[:, 0].astype(int)
            if len(np.unique(gts)) < 2:
                continue
            bl_a.append(roc_auc_score(gts, sub[:, 1]))
            fi_a.append(roc_auc_score(gts, sub[:, 2]))
        if bl_a:
            blend_d.append(np.mean(bl_a))
            final_d.append(np.mean(fi_a))
    return np.array(blend_d), np.array(final_d)


def report(directory, label, bootstraps=1000):
    data = load_data(directory, exclude_v9_error=True)
    total = sum(len(arr) for arr, _ in data.values())
    dropped = sum(d for _, d in data.values())
    kept_pct = 100 * total / (total + dropped) if (total + dropped) else 0
    print(f"\n== {label} (excluding v9-error items) ==")
    print(f"Kept {total} / {total + dropped} items ({kept_pct:.1f}%); "
          f"dropped {dropped} with v9 'malformed JSON'.")

    print(f"{'D':<4}{'kept':>6}{'drop':>5}{'blend':>8}{'final':>8}{'Δ':>9}")
    print('-' * 40)
    for d in sorted(data.keys(), key=lambda s: int(s[1:])):
        arr, drop = data[d]
        gts = arr[:, 0].astype(int)
        if len(np.unique(gts)) < 2:
            continue
        ab = roc_auc_score(gts, arr[:, 1])
        af = roc_auc_score(gts, arr[:, 2])
        print(f"{d:<4}{len(arr):>6}{drop:>5}{ab:>8.3f}{af:>8.3f}{(af-ab)*100:>+8.2f}pp")

    blend = macro_auc(data, 1)
    final = macro_auc(data, 2)
    print(f"Macro: blend={blend:.4f}  final={final:.4f}  Δ={(final-blend)*100:+.2f}pp")

    bl_b, fi_b = bootstrap(data, bootstraps)
    df = (fi_b - bl_b) * 100
    lo, hi = np.percentile(df, [2.5, 97.5])
    p_pos = float(np.mean(df > 0))
    print(f"Bootstrap ({bootstraps}): mean Δ {df.mean():+.2f}pp  CI [{lo:+.2f},{hi:+.2f}]  P>0 {p_pos:.3f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bootstraps", type=int, default=1000)
    args = ap.parse_args()
    report("benchmark/results/verbalized/v11_eval_test", "v11 FULL (meta+domain)", args.bootstraps)
    report("benchmark/results/verbalized/v11_eval_test_meta_only", "v11 META-ONLY", args.bootstraps)


if __name__ == "__main__":
    main()
