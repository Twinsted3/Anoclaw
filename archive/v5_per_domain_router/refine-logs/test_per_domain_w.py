"""Apply per-domain calibration-tuned w to test split and report macro AUROC."""
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

R = Path("/hdd1/jiangxi/AD-Agent/benchmark/results")
PERDOM = json.load(open("/hdd1/jiangxi/AD-Agent/refine-logs/PER_DOMAIN_W.json"))


def load_dict(p):
    if not p.exists():
        return {}
    d = json.load(open(p))
    if isinstance(d, list):
        d = {x.get("item_id"): x for x in d if "item_id" in x}
    return d


def main():
    subs = load_dict(R / "subspacead_test.json")
    files = {
        "gpt54": "gpt54_v0_direct_test_all_v2.json",
        "seedvl": "seedvl_v0_direct_test_all_v2.json",
        "qwen35": "qwen35_v0_direct_test_all_v2.json",
    }
    # Use TEST-level expert median (matches paper convention)
    m_test = float(np.median([x["anomaly_score"] for x in subs.values()
                              if "anomaly_score" in x and x["anomaly_score"] is not None]))
    # Also use calibration-level median (more honest)
    m_calib = PERDOM["global_expert_median"]

    for bk, fname in files.items():
        direct = load_dict(R / fname)
        per_w = PERDOM["per_backbone"].get(bk, {})

        for m_label, m_val in [("test_med", m_test), ("calib_med", m_calib)]:
            # per-domain w (from calibration), per-domain median
            by_dom_perw = defaultdict(lambda: ([], []))
            by_dom_global = defaultdict(lambda: ([], []))  # global w=0.2 baseline
            by_dom_direct = defaultdict(lambda: ([], []))
            for iid, vlm_it in direct.items():
                sv = vlm_it.get("anomaly_score")
                y = vlm_it.get("label_gt")
                dom = vlm_it.get("domain_code")
                if sv is None or y is None or dom is None:
                    continue
                if iid in subs and subs[iid].get("anomaly_score") is not None:
                    se = float(subs[iid]["anomaly_score"])
                    sig = 1.0 / (1.0 + np.exp(-2.0 * (se - m_val) / max(m_val, 1e-6)))
                    w = per_w.get(dom, {}).get("w", 0.2)
                    fused_perw = (1 - w) * float(sv) + w * sig
                    fused_g02 = 0.8 * float(sv) + 0.2 * sig
                else:
                    fused_perw = float(sv)
                    fused_g02 = float(sv)
                by_dom_perw[dom][0].append(fused_perw)
                by_dom_perw[dom][1].append(int(y))
                by_dom_global[dom][0].append(fused_g02)
                by_dom_global[dom][1].append(int(y))
                by_dom_direct[dom][0].append(float(sv))
                by_dom_direct[dom][1].append(int(y))

            def macro(d):
                aucs = []
                per = {}
                for dom, (s, y) in d.items():
                    if len(set(y)) >= 2:
                        a = roc_auc_score(y, s)
                        aucs.append(a)
                        per[dom] = a
                return float(np.mean(aucs)) if aucs else 0.0, per

            m_pw, per_pw = macro(by_dom_perw)
            m_g, per_g = macro(by_dom_global)
            m_d, per_d = macro(by_dom_direct)
            print(f"\n=== {bk} ({m_label}) ===")
            print(f"  direct:           {m_d:.4f}")
            print(f"  fusion (w=0.2):   {m_g:.4f}")
            print(f"  fusion (per-domain w from calib): {m_pw:.4f}  Δ vs fusion={m_pw-m_g:+.4f}  Δ vs direct={m_pw-m_d:+.4f}")
            for dom in sorted(per_pw):
                w = per_w.get(dom, {}).get("w", 0.2)
                pw_v = per_pw.get(dom, 0)
                g_v = per_g.get(dom, 0)
                print(f"    {dom}: w={w:.2f}  perw={pw_v:.3f}  fusion={g_v:.3f}  Δ={pw_v-g_v:+.3f}")
            break  # only show one m_label


if __name__ == "__main__":
    main()
