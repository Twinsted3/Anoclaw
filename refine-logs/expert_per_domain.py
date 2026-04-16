"""Compare experts (SubspaceAD vs AnomalyVFM vs DINOv2-patch) per domain on
calibration. Produces per-domain best expert assignment (data-driven, frozen).

Output: refine-logs/PER_DOMAIN_EXPERT.json
"""
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

R = Path("/hdd1/jiangxi/AD-Agent/benchmark/results")


def load_dict(p):
    if not p.exists():
        return {}
    d = json.load(open(p))
    if isinstance(d, list):
        d = {x.get("item_id"): x for x in d if "item_id" in x}
    return d


def per_dom(items_by_id, score_key="anomaly_score"):
    by = defaultdict(lambda: ([], []))
    for iid, x in items_by_id.items():
        s = x.get(score_key)
        y = x.get("label_gt")
        d = x.get("domain_code")
        if s is None or y is None or d is None:
            continue
        by[d][0].append(float(s))
        by[d][1].append(int(y))
    out = {}
    for dom, (s, y) in by.items():
        if len(set(y)) >= 2:
            out[dom] = float(roc_auc_score(y, s))
    return out


def main():
    sources = {
        "subspacead": load_dict(R / "subspacead_calibration.json"),
        "anomalyvfm": load_dict(R / "anomalyvfm_calibration.json"),
    }
    # DINOv2-patch only has test-split data; we approximate calib AUROC by
    # restricting test items to per-domain and reporting test AUROC. Honest
    # cross-split comparison.
    dn_patch_test = load_dict(R / "classical_dinov2_patch_test_all.json")
    dn_global_test = load_dict(R / "classical_dinov2_global_test_all.json")

    print("=== Per-domain calibration AUROC ===")
    per = {}
    for name, items in sources.items():
        per[name] = per_dom(items)
        print(f"  {name}:")
        for d in sorted(per[name]):
            print(f"    {d}: {per[name][d]:.4f}  (n={sum(1 for x in items.values() if x.get('domain_code')==d)})")

    # Per-domain best expert (calibration only, between subspacead & anomalyvfm)
    all_doms = set()
    for v in per.values():
        all_doms.update(v.keys())
    best = {}
    for d in sorted(all_doms):
        scores = [(per[name].get(d, 0.0), name) for name in per]
        scores.sort(reverse=True)
        best[d] = {"expert": scores[0][1], "calib_auroc": scores[0][0],
                   "all_calib": {n: per[n].get(d, None) for n in per}}
    print("\n=== Best expert per domain (calibration argmax) ===")
    for d in sorted(best):
        v = best[d]
        print(f"  {d}: {v['expert']}  ({v['calib_auroc']:.4f})  "
              f"all={v['all_calib']}")

    # Sanity: per-domain test AUROC for each expert (where available)
    print("\n=== Per-domain TEST AUROC (sanity) ===")
    per_test = {
        "subspacead": per_dom(load_dict(R / "subspacead_test.json")),
        "dinov2_patch": per_dom(dn_patch_test),
        "dinov2_global": per_dom(dn_global_test),
    }
    if (R / "anomalyvfm_test.json").exists():
        per_test["anomalyvfm"] = per_dom(load_dict(R / "anomalyvfm_test.json"))
    for name, v in per_test.items():
        print(f"  {name}: " + "  ".join(f"{d}={v.get(d, 0):.3f}" for d in sorted(v)))

    out_path = Path("/hdd1/jiangxi/AD-Agent/refine-logs/PER_DOMAIN_EXPERT.json")
    with open(out_path, "w") as f:
        json.dump({"per_domain_calib": per, "best_expert": best,
                   "per_domain_test": per_test}, f, indent=2)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
