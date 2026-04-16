"""Compute per-domain best strategy from Qwen3.5 calibration.

Strategies considered: direct, fusion (w=0.2 with SubspaceAD), fusion_perdomainw,
zoom_fusion (executed on calib in anomaclaw_v4_qwen35_calib.json).
"""
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

R = Path("/hdd1/jiangxi/AD-Agent/benchmark/results")
M = json.load(open("/hdd1/jiangxi/AD-Agent/benchmark/manifests/full_manifest.json"))
LABELS = {x["item_id"]: x.get("label") for x in M if x["split"] == "calibration"}


def load_dict(p):
    if not p.exists():
        return {}
    d = json.load(open(p))
    if isinstance(d, list):
        d = {x.get("item_id"): x for x in d if "item_id" in x}
    return d


def per_dom_macro(items_score):
    by = defaultdict(lambda: ([], []))
    for iid, (s, dom) in items_score.items():
        y = LABELS.get(iid)
        if y is None:
            continue
        by[dom][0].append(float(s))
        by[dom][1].append(int(y))
    out = {}
    for d, (s, y) in by.items():
        if len(set(y)) >= 2:
            out[d] = float(roc_auc_score(y, s))
    return out


def main():
    # Direct (Qwen3.5)
    direct = load_dict(R / "qwen35_v0_direct_calibration_egra.json")
    direct_scores = {iid: (x.get("anomaly_score"), x.get("domain_code"))
                     for iid, x in direct.items()
                     if x.get("anomaly_score") is not None and x.get("domain_code")}

    subs = load_dict(R / "subspacead_calibration.json")
    m_subs = float(np.median([x["anomaly_score"] for x in subs.values()
                              if x.get("anomaly_score") is not None]))

    # Fusion w=0.2
    fusion_scores = {}
    for iid, (sv, dom) in direct_scores.items():
        if iid in subs and subs[iid].get("anomaly_score") is not None:
            se = float(subs[iid]["anomaly_score"])
            sig = 1.0 / (1.0 + np.exp(-2.0 * (se - m_subs) / max(m_subs, 1e-6)))
            fusion_scores[iid] = (0.8 * float(sv) + 0.2 * sig, dom)
        else:
            fusion_scores[iid] = (float(sv), dom)

    # AnomalyVFM expert
    avfm = load_dict(R / "anomalyvfm_calibration.json")
    avfm_scores = {iid: (x.get("anomaly_score"), x.get("domain_code"))
                   for iid, x in avfm.items()
                   if x.get("anomaly_score") is not None and x.get("domain_code")}

    # Fusion with AnomalyVFM expert
    m_avfm = float(np.median([x for x in [v[0] for v in avfm_scores.values()] if x is not None]))
    fusion_avfm_scores = {}
    for iid, (sv, dom) in direct_scores.items():
        if iid in avfm_scores and avfm_scores[iid][0] is not None:
            se = float(avfm_scores[iid][0])
            sig = 1.0 / (1.0 + np.exp(-2.0 * (se - m_avfm) / max(m_avfm, 1e-6)))
            fusion_avfm_scores[iid] = (0.8 * float(sv) + 0.2 * sig, dom)
        else:
            fusion_avfm_scores[iid] = (float(sv), dom)

    # zoom_fusion (from real run)
    zf_path = R / "anomaclaw_v4_qwen35_calib.json"
    zf = load_dict(zf_path) if zf_path.exists() else {}
    zoom_scores = {iid: (x.get("anomaly_score"), x.get("domain_code"))
                   for iid, x in zf.items()
                   if x.get("anomaly_score") is not None and x.get("domain_code")}

    strategies = {
        "direct": direct_scores,
        "fusion_subs": fusion_scores,
        "fusion_avfm": fusion_avfm_scores,
        "subspacead_only": {iid: (x.get("anomaly_score"), x.get("domain_code"))
                            for iid, x in subs.items()
                            if x.get("anomaly_score") is not None and x.get("domain_code")},
        "anomalyvfm_only": avfm_scores,
        "zoom_fusion": zoom_scores,
    }

    print("=== Per-domain calibration AUROC per strategy (Qwen3.5) ===")
    per_strat = {name: per_dom_macro(s) for name, s in strategies.items()}
    domains = sorted({d for s in per_strat.values() for d in s})
    print(f"{'domain':6s}  " + "  ".join(f"{n:14s}" for n in per_strat))
    for d in domains:
        print(f"{d:6s}  " + "  ".join(f"{per_strat[n].get(d, 0):.3f}{'':10s}" for n in per_strat))
    print()
    for name, p in per_strat.items():
        macro = float(np.mean(list(p.values()))) if p else 0.0
        print(f"  {name}: macro={macro:.4f}")

    # per-domain argmax
    print("\n=== Per-domain best strategy (calibration argmax) ===")
    best = {}
    for d in domains:
        scores = [(per_strat[n].get(d, 0), n) for n in per_strat]
        scores.sort(reverse=True)
        best[d] = {"strategy": scores[0][1], "calib_auroc": scores[0][0]}
        print(f"  {d}: {scores[0][1]:18s} ({scores[0][0]:.4f})")

    # If we APPLY the per-domain best on test data (using existing test scores), what would we get?
    print("\n=== Estimated TEST macro if we use per-domain calibration best ===")
    test_strats = {
        "direct": load_dict(R / "qwen35_v0_direct_test_all_v2.json"),
        "subspacead_only": load_dict(R / "subspacead_test.json"),
        "anomalyvfm_only": load_dict(R / "anomalyvfm_test.json"),
    }
    test_subs_med = float(np.median([x["anomaly_score"] for x in test_strats["subspacead_only"].values()
                                    if x.get("anomaly_score") is not None]))
    test_avfm_med = float(np.median([x["anomaly_score"] for x in test_strats["anomalyvfm_only"].values()
                                    if x.get("anomaly_score") is not None]))

    test_labels = {x["item_id"]: x.get("label") for x in M if x["split"] == "test"}
    direct_test = test_strats["direct"]
    fusion_subs_test, fusion_avfm_test = {}, {}
    for iid, x in direct_test.items():
        sv = x.get("anomaly_score"); dom = x.get("domain_code")
        if sv is None or dom is None: continue
        # subs fusion
        sub = test_strats["subspacead_only"].get(iid)
        if sub and sub.get("anomaly_score") is not None:
            se = float(sub["anomaly_score"])
            sig = 1.0/(1.0+np.exp(-2.0*(se-test_subs_med)/max(test_subs_med,1e-6)))
            fusion_subs_test[iid] = (0.8*float(sv)+0.2*sig, dom)
        else:
            fusion_subs_test[iid] = (float(sv), dom)
        # avfm fusion
        a = test_strats["anomalyvfm_only"].get(iid)
        if a and a.get("anomaly_score") is not None:
            se = float(a["anomaly_score"])
            sig = 1.0/(1.0+np.exp(-2.0*(se-test_avfm_med)/max(test_avfm_med,1e-6)))
            fusion_avfm_test[iid] = (0.8*float(sv)+0.2*sig, dom)
        else:
            fusion_avfm_test[iid] = (float(sv), dom)

    test_scores = {
        "direct": {iid: (x.get("anomaly_score"), x.get("domain_code"))
                   for iid, x in direct_test.items() if x.get("anomaly_score") is not None and x.get("domain_code")},
        "fusion_subs": fusion_subs_test,
        "fusion_avfm": fusion_avfm_test,
        "subspacead_only": {iid: (x.get("anomaly_score"), x.get("domain_code"))
                            for iid, x in test_strats["subspacead_only"].items() if x.get("anomaly_score") is not None and x.get("domain_code")},
        "anomalyvfm_only": {iid: (x.get("anomaly_score"), x.get("domain_code"))
                            for iid, x in test_strats["anomalyvfm_only"].items() if x.get("anomaly_score") is not None and x.get("domain_code")},
    }
    # Simulated agent: per-domain best strategy (where available in test_scores; zoom_fusion not in test)
    print("\nSimulated AGENT (per-domain calib argmax, executed via test scores):")
    by_dom = defaultdict(lambda: ([], []))
    for d, info in best.items():
        strat = info["strategy"]
        if strat == "zoom_fusion":
            # zoom_fusion not in test; fall back to fusion_subs
            strat = "fusion_subs"
        if strat not in test_scores:
            continue
        for iid, (s, dom) in test_scores[strat].items():
            if dom != d: continue
            y = test_labels.get(iid)
            if y is None: continue
            by_dom[d][0].append(float(s))
            by_dom[d][1].append(int(y))
    aurocs = {d: roc_auc_score(y, s) for d, (s, y) in by_dom.items() if len(set(y)) >= 2}
    macro_agent = float(np.mean(list(aurocs.values()))) if aurocs else 0.0
    print(f"  agent macro test: {macro_agent:.4f}")

    # baselines on test
    for name, s in test_scores.items():
        per_t = per_dom_macro({iid: v for iid, v in s.items()}) if False else None
        by = defaultdict(lambda: ([], []))
        for iid, (sc, dom) in s.items():
            y = test_labels.get(iid)
            if y is None: continue
            by[dom][0].append(float(sc))
            by[dom][1].append(int(y))
        a = [roc_auc_score(y, sc) for sc, y in by.values() if len(set(y)) >= 2]
        m = float(np.mean(a)) if a else 0.0
        print(f"  {name} macro test: {m:.4f}")

    print(f"\nAGENT vs DIRECT on test: {(macro_agent - 0.776)*100:+.1f} pp")


if __name__ == "__main__":
    main()
