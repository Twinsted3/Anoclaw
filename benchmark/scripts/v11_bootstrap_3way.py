"""Three-way paired stratified bootstrap: v10 blend vs v11 full vs v11 meta-only.

Reads both v11_eval_test/ (meta + domain rulebook) and v11_eval_test_meta_only/
(meta-rules only), matches by item_id, and reports macro deltas with CIs.
"""
from __future__ import annotations
import argparse, json, os
from pathlib import Path
import numpy as np
from sklearn.metrics import roc_auc_score


def load_matched(full_dir, meta_dir):
    """Return {domain_code: ndarray[n, 4]} with columns (gt, blend, full, meta)."""
    out = {}
    for p in sorted(Path(full_dir).glob("D*.json")):
        d = p.stem
        full_rows = json.load(open(p))
        meta_path = Path(meta_dir) / f"{d}.json"
        if not meta_path.exists():
            continue
        meta_rows = json.load(open(meta_path))
        m_idx = {x["item_id"]: x for x in meta_rows}
        rows = []
        for x in full_rows:
            m = m_idx.get(x["item_id"])
            if m is None:
                continue
            gt = x.get("label_gt")
            if gt is None:
                continue
            v9 = x.get("v9_score")
            dv = x.get("direct_score")
            if v9 is None or dv is None:
                continue
            blend = 0.5 * v9 + 0.5 * dv
            full = x.get("anomaly_score", blend)
            meta = m.get("anomaly_score", blend)
            rows.append((int(gt), float(blend), float(full), float(meta)))
        if rows:
            out[d] = np.array(rows)
    return out


def macro_auc(data, col):
    aucs = []
    for d, arr in data.items():
        gts = arr[:, 0].astype(int)
        if len(np.unique(gts)) < 2:
            continue
        aucs.append(roc_auc_score(gts, arr[:, col]))
    return float(np.mean(aucs))


def bootstrap(data, B, seed=0):
    rng = np.random.default_rng(seed)
    blend_d, full_d, meta_d = [], [], []
    for b in range(B):
        bl_a, fu_a, me_a = [], [], []
        for d, arr in data.items():
            n = len(arr)
            idx = rng.integers(0, n, size=n)
            sub = arr[idx]
            gts = sub[:, 0].astype(int)
            if len(np.unique(gts)) < 2:
                continue
            bl_a.append(roc_auc_score(gts, sub[:, 1]))
            fu_a.append(roc_auc_score(gts, sub[:, 2]))
            me_a.append(roc_auc_score(gts, sub[:, 3]))
        if bl_a:
            blend_d.append(np.mean(bl_a))
            full_d.append(np.mean(fu_a))
            meta_d.append(np.mean(me_a))
    return (np.array(blend_d), np.array(full_d), np.array(meta_d))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", default="benchmark/results/verbalized/v11_eval_test")
    ap.add_argument("--meta", default="benchmark/results/verbalized/v11_eval_test_meta_only")
    ap.add_argument("--bootstraps", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    data = load_matched(args.full, args.meta)
    total = sum(len(v) for v in data.values())
    print(f"Loaded {total} matched items across {len(data)} domains.\n")

    print(f"{'D':<4}{'n':>4}{'blend':>8}{'v11f':>8}{'v11m':>8}{'Δf':>9}{'Δm':>9}{'Δm-f':>9}")
    print('-' * 59)
    for d in sorted(data.keys(), key=lambda s: int(s[1:])):
        arr = data[d]
        gts = arr[:, 0].astype(int)
        if len(np.unique(gts)) < 2:
            continue
        ab = roc_auc_score(gts, arr[:, 1])
        af = roc_auc_score(gts, arr[:, 2])
        am = roc_auc_score(gts, arr[:, 3])
        print(f"{d:<4}{len(arr):>4}{ab:>8.3f}{af:>8.3f}{am:>8.3f}"
              f"{(af-ab)*100:>+8.2f}pp{(am-ab)*100:>+8.2f}pp{(am-af)*100:>+8.2f}pp")

    blend = macro_auc(data, 1)
    full = macro_auc(data, 2)
    meta = macro_auc(data, 3)
    print(f"\nMacro AUROC (point estimate):")
    print(f"  blend (v10)       = {blend:.4f}")
    print(f"  v11 full          = {full:.4f}  (Δ vs blend {(full-blend)*100:+.2f} pp)")
    print(f"  v11 meta-only     = {meta:.4f}  (Δ vs blend {(meta-blend)*100:+.2f} pp)")
    print(f"  Δ(full − meta)    = {(full-meta)*100:+.2f} pp")

    print(f"\nBootstrap ({args.bootstraps} resamples, stratified paired):")
    bl_b, fu_b, me_b = bootstrap(data, args.bootstraps, args.seed)
    df = (fu_b - bl_b) * 100
    dm = (me_b - bl_b) * 100
    dfm = (fu_b - me_b) * 100

    def ci(arr):
        lo, hi = np.percentile(arr, [2.5, 97.5])
        return f"[{lo:+.2f}, {hi:+.2f}]"

    def ppos(arr):
        return float(np.mean(arr > 0))

    print(f"  Δ v11_full vs blend : mean {df.mean():+.2f} pp  CI {ci(df)}  P>0 {ppos(df):.3f}")
    print(f"  Δ v11_meta vs blend : mean {dm.mean():+.2f} pp  CI {ci(dm)}  P>0 {ppos(dm):.3f}")
    print(f"  Δ full vs meta       : mean {dfm.mean():+.2f} pp  CI {ci(dfm)}  P>0 {ppos(dfm):.3f}")


if __name__ == "__main__":
    main()
