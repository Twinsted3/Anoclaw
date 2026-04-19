"""Aggregate active_learning.py per-domain outputs into a summary.

Usage:
  python benchmark/scripts/al_summarize.py \
    --dir benchmark/results/active_learning \
    --out benchmark/results/al_summary.json
"""
from __future__ import annotations
import argparse
import glob
import json
import os


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="benchmark/results/active_learning")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(args.dir, "al_qwen35_D*.json")))
    print(f"Found {len(files)} domain files.")

    rows = []
    for f in files:
        try:
            d = json.load(open(f))
        except Exception as e:
            print(f"[err] {f}: {e}")
            continue
        rows.append({
            "domain": d.get("domain", os.path.basename(f)),
            "k": d.get("k"),
            "fewshot_k": d.get("fewshot_k"),
            "selection": d.get("selection"),
            "auroc_passive": d.get("auroc_passive"),
            "auroc_active": d.get("auroc_active"),
            "delta_auroc": d.get("delta_auroc"),
            "n_passive": len(d.get("passive", [])),
            "n_active": len(d.get("active", [])),
            "auroc_error": d.get("auroc_error"),
        })

    print(f"\n{'Domain':8s} {'Passive':>10s} {'Active':>10s} {'Δ':>8s} {'n':>5s}")
    n_pos = 0
    n_total = 0
    deltas = []
    for r in rows:
        if r["delta_auroc"] is not None:
            n_total += 1
            if r["delta_auroc"] > 0:
                n_pos += 1
            deltas.append(r["delta_auroc"])
        p = r["auroc_passive"]
        a = r["auroc_active"]
        d = r["delta_auroc"]
        print(f"  {r['domain']:6s} "
              f"{p:>10.4f} " if p is not None else f"  {r['domain']:6s} {'?':>10s} ", end="")
        print(f"{a:>10.4f} {d:>+8.4f} {r['n_active']:>5d}" if a is not None
              else f"{'?':>10s} {'?':>8s} {r['n_active']:>5d}")

    if deltas:
        import statistics
        mean_delta = statistics.mean(deltas)
        print(f"\nMean Δ across {len(deltas)} domains: {mean_delta:+.4f}")
        print(f"Positive in {n_pos}/{n_total} domains")
        # Paired signed-rank test (Wilcoxon)
        try:
            from scipy.stats import wilcoxon
            stat, p = wilcoxon([-d for d in deltas], alternative="less")
            print(f"Wilcoxon signed-rank one-sided (Δ>0): p={p:.4f}")
        except Exception:
            pass

    if args.out:
        out = {"rows": rows, "n_positive": n_pos, "n_total": n_total,
               "mean_delta": (sum(deltas) / len(deltas)) if deltas else None}
        with open(args.out, "w") as f:
            json.dump(out, f, indent=2)
        print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
