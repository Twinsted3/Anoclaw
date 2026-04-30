"""Generate LOO sensitivity numbers for fusion vs v0.

Output: prints the LOO macro-AUROC gap for each (backbone, held-out domain) combination.
"""
import json
import numpy as np
from collections import defaultdict
from sklearn.metrics import roc_auc_score

RESULTS = "/hdd1/jiangxi/AD-Agent/benchmark/results"

DOMAIN_MAP = {
    "D1":  "D01 Industrial", "D2":  "D02 Retail",
    "D4":  "D03 Infrastr.",  "D5":  "D04 Dermo.",
    "D5b": "D05 Brain MRI",  "D5c": "D06 Liver CT",
    "D5d": "D07 Endoscopy",  "D6":  "D08 Change",
    "D7":  "D09 Road",       "D9":  "D10 Logical",
    "D10": "D11 VisA",
}

BACKBONES = {
    "GPT-5.4":  "gpt54_agent_v1_test.json",
    "SeedVL":   "seedvl_agent_v1_test.json",
    "Qwen3.5":  "qwen35_agent_v1_test.json",
}


def load(agent_file):
    subs = {x["item_id"]: float(x["anomaly_score"])
            for x in json.load(open(f"{RESULTS}/subspacead_test.json"))
            if x.get("anomaly_score") is not None}
    d = json.load(open(f"{RESULTS}/{agent_file}"))
    per = defaultdict(lambda: {"y": [], "v0": [], "exp": []})
    all_exp = []
    for it in d:
        dc = it.get("domain_code")
        if dc not in DOMAIN_MAP:
            continue
        key = DOMAIN_MAP[dc]
        es = subs.get(it["item_id"])
        if es is None:
            continue
        all_exp.append(es)
        per[key]["y"].append(int(it["label_gt"]))
        per[key]["v0"].append(float((it.get("raw_output") or {}).get("v0_score",
                                                                      it["anomaly_score"])))
        per[key]["exp"].append(es)
    global_median = float(np.median(all_exp))
    # compute per-domain v0 and fusion
    auroc_v0 = {}
    auroc_fusion = {}
    for k, v in per.items():
        y = np.array(v["y"])
        v0 = np.array(v["v0"])
        exp = np.array(v["exp"])
        fus = 0.8 * v0 + 0.2 * (1.0 / (1.0 + np.exp(-2.0 * (exp - global_median) / (global_median + 1e-9))))
        auroc_v0[k] = roc_auc_score(y, v0)
        auroc_fusion[k] = roc_auc_score(y, fus)
    return auroc_v0, auroc_fusion


def loo_deltas(auroc_v0, auroc_fusion):
    keys = sorted(auroc_v0.keys())
    full_v0 = float(np.mean([auroc_v0[k] for k in keys]))
    full_fus = float(np.mean([auroc_fusion[k] for k in keys]))
    out = []
    for drop in keys:
        rest = [k for k in keys if k != drop]
        m_v0 = float(np.mean([auroc_v0[k] for k in rest]))
        m_fus = float(np.mean([auroc_fusion[k] for k in rest]))
        out.append((drop, m_fus - m_v0))
    return full_fus - full_v0, out


for bb, f in BACKBONES.items():
    v0, fus = load(f)
    full, deltas = loo_deltas(v0, fus)
    vals = [d for _, d in deltas]
    print(f"\n{bb}: full Δ={full*100:+.2f}pp")
    print(f"  LOO min  = {min(vals)*100:+.2f}pp (drop {min(deltas, key=lambda x: x[1])[0]})")
    print(f"  LOO max  = {max(vals)*100:+.2f}pp (drop {max(deltas, key=lambda x: x[1])[0]})")
    print(f"  LOO std  = {np.std(vals)*100:.3f}pp")
    print(f"  positive on {sum(1 for v in vals if v>0)}/{len(vals)} splits")
