"""Per-(backbone, domain) optimal fusion weight w from calibration AUROC sweep.

For each (backbone, domain), sweeps w in {0.0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.7, 1.0}
on the calibration split and picks the w that maximises calibration AUROC.

Output: refine-logs/PER_DOMAIN_W.json — used by the v4 agent's strategy_fusion.
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


def main():
    direct_files = {
        "gpt54": "gpt54_v0_direct_calibration_egra.json",
        "seedvl": "seedvl_v0_direct_calibration_egra.json",
        "qwen35": "qwen35_v0_direct_calibration_egra.json",
    }
    subs = load_dict(R / "subspacead_calibration.json")
    # global median for sigmoid centring
    m_subs = float(np.median([x["anomaly_score"] for x in subs.values()
                              if "anomaly_score" in x and x["anomaly_score"] is not None]))
    grid = [0.0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.7, 1.0]

    out = {}
    for bk, fname in direct_files.items():
        p = R / fname
        if not p.exists():
            print(f"[skip] {bk}: no calibration file {fname}")
            continue
        direct = load_dict(p)
        # group by domain
        by_dom = defaultdict(lambda: {"sv": [], "se": [], "y": []})
        for iid, vlm_it in direct.items():
            if iid not in subs:
                continue
            sv = vlm_it.get("anomaly_score")
            y = vlm_it.get("label_gt")
            dom = vlm_it.get("domain_code")
            se = subs[iid].get("anomaly_score")
            if sv is None or y is None or dom is None or se is None:
                continue
            by_dom[dom]["sv"].append(float(sv))
            by_dom[dom]["se"].append(float(se))
            by_dom[dom]["y"].append(int(y))

        per_dom_w = {}
        for dom, d in by_dom.items():
            if len(set(d["y"])) < 2:
                continue
            sv = np.array(d["sv"])
            se = np.array(d["se"])
            y = np.array(d["y"])
            sig = 1.0 / (1.0 + np.exp(-2.0 * (se - m_subs) / max(m_subs, 1e-6)))
            best_w, best_auc = 0.0, 0.0
            for w in grid:
                fused = (1 - w) * sv + w * sig
                auc = roc_auc_score(y, fused)
                if auc > best_auc + 1e-6:
                    best_auc = auc
                    best_w = w
            per_dom_w[dom] = {"w": best_w, "calib_auroc": best_auc, "n": len(y)}
        out[bk] = per_dom_w
        print(f"\n=== {bk} per-domain optimal w (calibration) ===")
        for d in sorted(per_dom_w):
            v = per_dom_w[d]
            print(f"  {d}: w={v['w']:.2f}  calib_auroc={v['calib_auroc']:.4f}  n={v['n']}")

    out_path = Path("/hdd1/jiangxi/AD-Agent/refine-logs/PER_DOMAIN_W.json")
    with open(out_path, "w") as f:
        json.dump({"global_expert_median": m_subs, "per_backbone": out}, f, indent=2)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
