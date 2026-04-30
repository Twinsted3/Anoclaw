"""Aggregate verbalized v5 (parallel-Direct + refutation, alpha=0.5) results.

For each variant in {passive, anchor, l1, l2, l1l2}:
  - per-domain AUROC on test
  - macro AUROC
  - paired delta vs Passive (12-domain stratified bootstrap, 1000 resamples)
  - p(delta > 0)
"""
import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

DOMAINS = ["D1","D5","D2","D6","D3","D4","D7","D8","D9","D10","D11","D12"]


def load_dir(d, suffix=""):
    """Return {domain: list of (item_id, label, score)}."""
    out = {}
    for D in DOMAINS:
        candidates = [f"{D}{suffix}.json", f"{D}_v5_passive.json", f"{D}_v5_anchor.json",
                      f"{D}_v5_l1.json", f"{D}_v5_l2.json", f"{D}_v5_l1l2.json"]
        f = None
        for c in candidates:
            p = Path(d) / c
            if p.exists() and p.stat().st_size > 1000:
                f = p; break
        if f is None:
            out[D] = None
            continue
        r = json.load(open(f))
        rows = []
        for x in r:
            lbl = x.get("label_gt")
            if lbl is None:
                lbl = x.get("label")
            sc = x.get("anomaly_score")
            if x.get("error") is not None:
                continue
            if lbl is None or sc is None:
                continue
            rows.append((x.get("item_id"), int(lbl), float(sc)))
        out[D] = rows
    return out


def per_domain_auroc(d):
    out = {}
    for D in DOMAINS:
        rows = d.get(D)
        if not rows:
            out[D] = None
            continue
        y = [r[1] for r in rows]
        s = [r[2] for r in rows]
        if len(set(y)) < 2:
            out[D] = None
        else:
            out[D] = float(roc_auc_score(y, s))
    return out


def stratified_paired_bootstrap(per_dom_a, per_dom_b, n_boot=1000, seed=0):
    """For each bootstrap replicate, for each domain resample items with
    replacement, recompute per-domain AUROC for both methods, take macro,
    take diff."""
    rng = np.random.default_rng(seed)
    deltas = []
    common = [D for D in DOMAINS if per_dom_a.get(D) and per_dom_b.get(D)]
    # Index items by id for both
    a_by_dom = {D: per_dom_a[D] for D in common}
    b_by_dom = {D: per_dom_b[D] for D in common}
    # Item pairing across methods by item_id
    pairs_by_dom = {}
    for D in common:
        a_map = {r[0]: r for r in a_by_dom[D]}
        b_map = {r[0]: r for r in b_by_dom[D]}
        ids = sorted(a_map.keys() & b_map.keys())
        pairs_by_dom[D] = [(i, a_map[i], b_map[i]) for i in ids]

    for _ in range(n_boot):
        macro_a = []; macro_b = []
        for D in common:
            pairs = pairs_by_dom[D]
            n = len(pairs)
            idx = rng.integers(0, n, n)
            ya = [pairs[i][1][1] for i in idx]
            sa = [pairs[i][1][2] for i in idx]
            yb = [pairs[i][2][1] for i in idx]
            sb = [pairs[i][2][2] for i in idx]
            if len(set(ya)) < 2 or len(set(yb)) < 2:
                continue
            macro_a.append(roc_auc_score(ya, sa))
            macro_b.append(roc_auc_score(yb, sb))
        if macro_a and macro_b:
            deltas.append(np.mean(macro_b) - np.mean(macro_a))
    deltas = np.array(deltas)
    lo, hi = np.percentile(deltas, [2.5, 97.5])
    p = float((deltas > 0).mean())
    return float(lo), float(hi), p, float(deltas.mean()), float(deltas.std())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--passive_dir",
                    default="/hdd1/jiangxi/AD-Agent/benchmark/results/v2/v12_passive_test")
    ap.add_argument("--root",
                    default="/hdd1/jiangxi/AD-Agent/benchmark/results/verbalized")
    ap.add_argument("--n_boot", type=int, default=1000)
    args = ap.parse_args()

    runs = {
        "Passive (v12)": Path(args.passive_dir),
        "+Anchor":       Path(args.root) / "v5_eval_anchor",
        "+L1 inv":       Path(args.root) / "v5_eval_l1",
        "+L2 cls":       Path(args.root) / "v5_eval_l2",
        "+L1+L2":        Path(args.root) / "v5_eval_l1l2",
    }
    loaded = {n: load_dir(p) for n, p in runs.items()}
    aurocs = {n: per_domain_auroc(d) for n, d in loaded.items()}

    print("\n=== Per-domain AUROC ===")
    head = f"{'method':14s}|" + "|".join(f"{D:>6}" for D in DOMAINS) + "| Macro"
    print(head)
    for n, per in aurocs.items():
        cells = []
        vals = []
        for D in DOMAINS:
            v = per.get(D)
            if v is None:
                cells.append("  N/A ")
            else:
                cells.append(f"{v:.4f}"[:6])
                vals.append(v)
        macro = float(np.mean(vals)) if vals else float("nan")
        print(f"{n:14s}|" + "|".join(f"{c:>6}" for c in cells) + f"| {macro:.4f}")

    print("\n=== Bootstrap 95% CI on Macro Δ vs Passive (v12) ===")
    base = loaded["Passive (v12)"]
    base_macro = np.mean([v for v in aurocs["Passive (v12)"].values() if v is not None])
    print(f"Passive (v12) macro = {base_macro:.4f}")
    print(f"{'variant':14s} | {'macro':>7} | {'delta':>7} | {'95% CI':>22} | p(>0)")
    for n in ["+Anchor", "+L1 inv", "+L2 cls", "+L1+L2"]:
        if not aurocs[n]: continue
        var_macro_vals = [v for v in aurocs[n].values() if v is not None]
        var_macro = np.mean(var_macro_vals) if var_macro_vals else float("nan")
        lo, hi, p, mu, _ = stratified_paired_bootstrap(
            base, loaded[n], n_boot=args.n_boot)
        print(f"{n:14s} | {var_macro:>7.4f} | {var_macro-base_macro:>+7.4f} | "
              f"[{lo*100:>+5.2f}, {hi*100:>+5.2f}] pp     | {p:.3f}")

    # Per-domain Δ table
    print("\n=== Per-domain Δ vs Passive (v12) [pp] ===")
    print(f"{'Dom':>4} {'Passive':>8} " +
          " ".join(f"{n:>10}" for n in ["+Anchor","+L1 inv","+L2 cls","+L1+L2"]))
    for D in DOMAINS:
        base_v = aurocs["Passive (v12)"].get(D)
        if base_v is None:
            print(f"{D:>4}    ----   " + "  ----".rjust(10) * 4)
            continue
        cells = []
        for n in ["+Anchor", "+L1 inv", "+L2 cls", "+L1+L2"]:
            v = aurocs[n].get(D)
            if v is None:
                cells.append("  N/A   ")
            else:
                d = (v - base_v) * 100
                sign = "+" if d >= 0 else ""
                cells.append(f"{v:.3f}({sign}{d:.1f})")
        print(f"{D:>4} {base_v:>8.4f} " + " ".join(f"{c:>14}" for c in cells))


if __name__ == "__main__":
    main()
