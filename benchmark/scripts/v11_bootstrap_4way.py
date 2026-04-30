"""Four-way paired stratified bootstrap: v10 blend vs three v11 variants.

Reads v11_eval_test/ (meta+domain), v11_eval_test_meta_only/ (routing only),
and v11_eval_test_no_rules/ (controller but no rulebook). Matches by item_id
across all three and reports macro deltas with CIs.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from sklearn.metrics import roc_auc_score


def load_matched(full_dir, meta_dir, nor_dir):
    out = {}
    for p in sorted(Path(full_dir).glob("D*.json")):
        d = p.stem
        full_rows = json.load(open(p))
        meta_p = Path(meta_dir) / f"{d}.json"
        nor_p = Path(nor_dir) / f"{d}.json"
        if not (meta_p.exists() and nor_p.exists()):
            continue
        m_idx = {x["item_id"]: x for x in json.load(open(meta_p))}
        n_idx = {x["item_id"]: x for x in json.load(open(nor_p))}
        rows = []
        for x in full_rows:
            m = m_idx.get(x["item_id"])
            nx = n_idx.get(x["item_id"])
            if m is None or nx is None:
                continue
            gt = x.get("label_gt")
            if gt is None:
                continue
            v9 = x.get("v9_score")
            dv = x.get("direct_score")
            if v9 is None or dv is None:
                continue
            blend = 0.5 * v9 + 0.5 * dv
            rows.append((
                int(gt), float(blend),
                float(nx.get("anomaly_score", blend)),
                float(m.get("anomaly_score", blend)),
                float(x.get("anomaly_score", blend)),
            ))
        if rows:
            out[d] = np.array(rows)
    return out


def macro_col(data, col):
    aucs = []
    for d, arr in data.items():
        gts = arr[:, 0].astype(int)
        if len(np.unique(gts)) < 2:
            continue
        aucs.append(roc_auc_score(gts, arr[:, col]))
    return float(np.mean(aucs))


def bootstrap(data, B=1000, seed=0):
    rng = np.random.default_rng(seed)
    cols = [[], [], [], []]  # blend, no_rules, meta, full
    for b in range(B):
        acc = [[] for _ in range(4)]
        for d, arr in data.items():
            n = len(arr)
            idx = rng.integers(0, n, size=n)
            sub = arr[idx]
            gts = sub[:, 0].astype(int)
            if len(np.unique(gts)) < 2:
                continue
            for ci in range(4):
                acc[ci].append(roc_auc_score(gts, sub[:, 1+ci]))
        if acc[0]:
            for ci in range(4):
                cols[ci].append(np.mean(acc[ci]))
    return [np.array(c) for c in cols]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", default="benchmark/results/verbalized/v11_eval_test")
    ap.add_argument("--meta", default="benchmark/results/verbalized/v11_eval_test_meta_only")
    ap.add_argument("--nor", default="benchmark/results/verbalized/v11_eval_test_no_rules")
    ap.add_argument("--bootstraps", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    data = load_matched(args.full, args.meta, args.nor)
    total = sum(len(v) for v in data.values())
    print(f"Loaded {total} matched items across {len(data)} domains.\n")

    print(f"{'D':<4}{'n':>4}{'blend':>8}{'noR':>8}{'meta':>8}{'full':>8}  "
          f"{'ΔnoR':>8}{'Δmeta':>8}{'Δfull':>8}")
    print('-' * 78)
    for d in sorted(data.keys(), key=lambda s: int(s[1:])):
        arr = data[d]
        gts = arr[:, 0].astype(int)
        if len(np.unique(gts)) < 2:
            continue
        ab = roc_auc_score(gts, arr[:, 1])
        an = roc_auc_score(gts, arr[:, 2])
        am = roc_auc_score(gts, arr[:, 3])
        af = roc_auc_score(gts, arr[:, 4])
        print(f"{d:<4}{len(arr):>4}{ab:>8.3f}{an:>8.3f}{am:>8.3f}{af:>8.3f}  "
              f"{(an-ab)*100:>+7.2f}{(am-ab)*100:>+7.2f}{(af-ab)*100:>+7.2f}")

    labels = ["blend", "no-rules", "meta-only", "full (meta+domain)"]
    macros = [macro_col(data, 1+i) for i in range(4)]
    print(f"\nMacro AUROC (point estimate):")
    for label, m in zip(labels, macros):
        dlt = f"  Δ vs blend {(m - macros[0])*100:+.2f} pp" if label != "blend" else ""
        print(f"  {label:<22} = {m:.4f}{dlt}")

    print(f"\nBootstrap ({args.bootstraps} resamples, stratified paired):")
    bl_b, no_b, me_b, fu_b = bootstrap(data, args.bootstraps, args.seed)
    def stats(diff):
        lo, hi = np.percentile(diff, [2.5, 97.5])
        return f"mean {diff.mean():+.2f} pp  CI [{lo:+.2f}, {hi:+.2f}]  P>0 {float(np.mean(diff > 0)):.3f}"

    print(f"  no-rules vs blend    : {stats((no_b - bl_b) * 100)}")
    print(f"  meta-only vs blend   : {stats((me_b - bl_b) * 100)}")
    print(f"  full vs blend        : {stats((fu_b - bl_b) * 100)}")
    print(f"  meta-only vs no-rules: {stats((me_b - no_b) * 100)}")
    print(f"  full vs meta-only    : {stats((fu_b - me_b) * 100)}")
    print(f"  full vs no-rules     : {stats((fu_b - no_b) * 100)}")


if __name__ == "__main__":
    main()
