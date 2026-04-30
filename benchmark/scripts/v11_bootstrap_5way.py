"""Five-way paired stratified bootstrap: v10 blend vs four v11 variants,
including a shuffled-rules negative control.

Regimes:
  blend:    0.5 * v9 + 0.5 * direct (v10)
  no-rules: Controller, empty rulebook
  shuffled: Controller, wrong-domain rulebook (D1↔D7, D2↔D8, ..., D6↔D12)
  meta:     Controller, routing rules only
  full:     Controller, routing + domain rules

All frozen replays share identical v9+Direct outputs from the full run.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from sklearn.metrics import roc_auc_score


def load5(full_dir, meta_dir, nor_dir, shuf_dir):
    out = {}
    for p in sorted(Path(full_dir).glob("D*.json")):
        d = p.stem
        full_rows = json.load(open(p))
        refs = {
            "meta": Path(meta_dir) / f"{d}.json",
            "nor":  Path(nor_dir)  / f"{d}.json",
            "shuf": Path(shuf_dir) / f"{d}.json",
        }
        if not all(r.exists() for r in refs.values()):
            continue
        idx_meta = {x["item_id"]: x for x in json.load(open(refs["meta"]))}
        idx_nor  = {x["item_id"]: x for x in json.load(open(refs["nor"]))}
        idx_shuf = {x["item_id"]: x for x in json.load(open(refs["shuf"]))}
        rows = []
        for x in full_rows:
            ki = x["item_id"]
            if ki not in idx_meta or ki not in idx_nor or ki not in idx_shuf:
                continue
            gt = x.get("label_gt")
            v9 = x.get("v9_score"); dv = x.get("direct_score")
            if gt is None or v9 is None or dv is None:
                continue
            blend = 0.5 * v9 + 0.5 * dv
            rows.append((
                int(gt), float(blend),
                float(idx_nor[ki].get("anomaly_score", blend)),
                float(idx_shuf[ki].get("anomaly_score", blend)),
                float(idx_meta[ki].get("anomaly_score", blend)),
                float(x.get("anomaly_score", blend)),
            ))
        if rows:
            out[d] = np.array(rows)
    return out


def macro(data, col):
    aucs = []
    for d, arr in data.items():
        gts = arr[:, 0].astype(int)
        if len(np.unique(gts)) < 2:
            continue
        aucs.append(roc_auc_score(gts, arr[:, col]))
    return float(np.mean(aucs))


def bootstrap(data, B=1000, seed=0):
    rng = np.random.default_rng(seed)
    cols = [[], [], [], [], []]  # blend, noR, shuf, meta, full
    for b in range(B):
        acc = [[] for _ in range(5)]
        for d, arr in data.items():
            n = len(arr)
            idx = rng.integers(0, n, size=n)
            sub = arr[idx]
            gts = sub[:, 0].astype(int)
            if len(np.unique(gts)) < 2:
                continue
            for ci in range(5):
                acc[ci].append(roc_auc_score(gts, sub[:, 1+ci]))
        if acc[0]:
            for ci in range(5):
                cols[ci].append(np.mean(acc[ci]))
    return [np.array(c) for c in cols]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", default="benchmark/results/verbalized/v11_eval_test")
    ap.add_argument("--meta", default="benchmark/results/verbalized/v11_frozen_meta_only")
    ap.add_argument("--nor",  default="benchmark/results/verbalized/v11_frozen_no_rules")
    ap.add_argument("--shuf", default="benchmark/results/verbalized/v11_frozen_shuffled")
    ap.add_argument("--bootstraps", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    data = load5(args.full, args.meta, args.nor, args.shuf)
    total = sum(len(v) for v in data.values())
    print(f"Loaded {total} matched items across {len(data)} domains.\n")

    print(f"{'D':<4}{'n':>4}{'blend':>8}{'noR':>8}{'shuf':>8}{'meta':>8}{'full':>8}  "
          f"{'ΔnoR':>7}{'Δshuf':>7}{'Δmeta':>7}{'Δfull':>7}")
    print('-' * 92)
    for d in sorted(data.keys(), key=lambda s: int(s[1:])):
        arr = data[d]
        gts = arr[:, 0].astype(int)
        if len(np.unique(gts)) < 2:
            continue
        ab = roc_auc_score(gts, arr[:, 1])
        an = roc_auc_score(gts, arr[:, 2])
        ash = roc_auc_score(gts, arr[:, 3])
        am = roc_auc_score(gts, arr[:, 4])
        af = roc_auc_score(gts, arr[:, 5])
        print(f"{d:<4}{len(arr):>4}{ab:>8.3f}{an:>8.3f}{ash:>8.3f}{am:>8.3f}{af:>8.3f}  "
              f"{(an-ab)*100:>+6.2f} {(ash-ab)*100:>+6.2f} {(am-ab)*100:>+6.2f} {(af-ab)*100:>+6.2f}")

    labels = ["blend", "no-rules", "shuffled", "meta-only", "full (meta+domain)"]
    macros = [macro(data, 1+i) for i in range(5)]
    print(f"\nMacro AUROC (point estimate):")
    for label, m in zip(labels, macros):
        dlt = f"  Δ vs blend {(m - macros[0])*100:+.2f} pp" if label != "blend" else ""
        print(f"  {label:<22} = {m:.4f}{dlt}")

    print(f"\nBootstrap ({args.bootstraps} paired stratified resamples):")
    series = bootstrap(data, args.bootstraps, args.seed)
    def stats(diff):
        lo, hi = np.percentile(diff, [2.5, 97.5])
        return f"mean {diff.mean():+.2f} pp  CI [{lo:+.2f},{hi:+.2f}]  P>0 {float(np.mean(diff>0)):.3f}"
    bl, no, sh, me, fu = series
    print(f"  no-rules vs blend : {stats((no - bl) * 100)}")
    print(f"  shuffled vs blend : {stats((sh - bl) * 100)}")
    print(f"  meta-only vs blend: {stats((me - bl) * 100)}")
    print(f"  full vs blend     : {stats((fu - bl) * 100)}")
    print(f"  shuffled vs noR   : {stats((sh - no) * 100)}")
    print(f"  meta vs shuffled  : {stats((me - sh) * 100)}")
    print(f"  full vs shuffled  : {stats((fu - sh) * 100)}")
    print(f"  full vs meta      : {stats((fu - me) * 100)}")


if __name__ == "__main__":
    main()
