"""Compute macro/per-domain AUROC for an anomaclaw_v3 result file and compare
to v0 / fusion / debate / interpret strategies on the same items."""
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

RESULTS = Path("/hdd1/jiangxi/AD-Agent/benchmark/results")


def per_dom(items, score_key="anomaly_score"):
    by = defaultdict(lambda: ([], []))
    for x in items:
        s = x.get(score_key)
        y = x.get("label_gt")
        d = x.get("domain_code")
        if s is None or y is None or d is None:
            continue
        by[d][0].append(float(s))
        by[d][1].append(int(y))
    out = {}
    for d, (s, y) in by.items():
        if len(set(y)) >= 2:
            out[d] = roc_auc_score(y, s)
    macro = float(np.mean(list(out.values()))) if out else 0.0
    return macro, out


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "anomaclaw_v3_seedvl_test.json"
    backbone = sys.argv[2] if len(sys.argv) > 2 else "seedvl"
    bk_files = {
        "seedvl": ["seedvl_v0_direct_test_all_v2.json",
                   "seedvl_v3_debate_1r_test_all_v2.json",
                   "seedvl_egra_test_all_v2.json"],
        "gpt54": ["gpt54_v0_direct_test_all_v2.json",
                  "gpt54_v3_debate_1r_test_all_v2.json",
                  "gpt54_egra_test_all_v2.json"],
        "qwen35": ["qwen35_v0_direct_test_all_v2.json",
                   "qwen35_v3_debate_1r_test_all_v2.json",
                   "qwen35_egra_test_all_v2.json"],
    }
    p = RESULTS / target
    print(f"Loading {p}")
    new = json.load(open(p))
    new_ok = [x for x in new if x.get("anomaly_score") is not None and not x.get("error")]
    print(f"items={len(new)} ok={len(new_ok)}")

    macro, per = per_dom(new_ok)
    print(f"\n=== AnomalyClaw v3 ({backbone}) ===")
    print(f"  macro AUROC: {macro:.4f}  ({len(per)} domains)")
    for d in sorted(per):
        print(f"    {d}: {per[d]:.4f}")

    # Strategy distribution
    sd = defaultdict(int)
    for x in new_ok:
        s = x.get("plan", {}).get("strategy_executed", "?")
        sd[s] += 1
    print(f"  strategy executed: {dict(sd)}")

    # Per-strategy planned by domain
    plan_by_dom = defaultdict(set)
    for x in new_ok:
        plan_by_dom[x["domain_code"]].add(x.get("plan", {}).get("strategy_planned"))
    print(f"  strategies planned per domain: { {d: list(s) for d, s in plan_by_dom.items()} }")

    # Comparison vs baselines on the same items
    item_ids = {x["item_id"] for x in new_ok}
    print(f"\n=== Baselines on the same {len(item_ids)} items ===")
    for fname in bk_files.get(backbone, []):
        try:
            d = json.load(open(RESULTS / fname))
        except Exception:
            continue
        sub = [x for x in d if x["item_id"] in item_ids]
        m, _ = per_dom(sub)
        print(f"  {fname}: macro={m:.4f} ({len(sub)} items)")


if __name__ == "__main__":
    main()
