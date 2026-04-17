"""Compute Fusion(direct, subspacead, w=0.2) on dev and save as a standard
result file for the dev-frozen router."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from agent_tools_v6 import _load_expert_scores  # noqa: E402


def main():
    direct = json.load(open("benchmark/results/v6_direct_qwen3_dev.json"))
    d_by = {x["item_id"]: x for x in direct}

    # Load dev subspacead
    raw = json.load(open("benchmark/results/subspacead_dev.json"))
    if isinstance(raw, list):
        subs_by = {x["item_id"]: x for x in raw if "item_id" in x}
    else:
        subs_by = raw

    # Get calibration median for sigmoid center (same as the test-time Fusion)
    _, calib_scores = _load_expert_scores("subspacead", "calibration")
    median = float(np.median(calib_scores)) if len(calib_scores) else 1.0

    fused = []
    for iid, dx in d_by.items():
        ds = dx.get("anomaly_score")
        if ds is None:
            continue
        subs = subs_by.get(iid)
        if subs and subs.get("anomaly_score") is not None:
            se = float(subs["anomaly_score"])
            sig = 1.0 / (1.0 + np.exp(-2.0 * (se - median) / max(median, 1e-6)))
            s = 0.8 * float(ds) + 0.2 * sig
        else:
            s = float(ds)
        fused.append({
            **{k: dx.get(k) for k in ("item_id", "domain_code", "label_gt")},
            "anomaly_score": s,
            "direct_score_orig": ds,
            "expert_score": subs.get("anomaly_score") if subs else None,
            "fusion_w": 0.2,
        })

    out = "benchmark/results/v6_fusion_qwen3_dev.json"
    with open(out, "w") as f:
        json.dump(fused, f)
    print(f"Wrote {out}: {len(fused)} items")

    import sys as _s
    _s.path.insert(0, "benchmark/scripts")
    from eval_v6 import macro_auroc
    m = macro_auroc(fused)
    print(f"Fusion DEV macro: {m['macro']:.4f} (n={m['n_items']})")


if __name__ == "__main__":
    main()
