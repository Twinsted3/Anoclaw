"""Fast stratified paired bootstrap using vectorized AUROC via numpy."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

from .router import (
    load_strategy_scores,
    per_item_scores,
    oracle_assignment,
    calibration_assignment,
    descriptor_assignment,
)
from .registry import DOMAIN_FAMILY


def fast_auroc(scores: np.ndarray, labels: np.ndarray) -> float:
    """Vectorised AUROC via Mann-Whitney U / rank sum."""
    if len(scores) == 0:
        return float("nan")
    pos = labels == 1
    neg = ~pos
    n_pos = pos.sum()
    n_neg = neg.sum()
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty_like(order, dtype=np.float64)
    # Fractional ranks for ties
    sorted_scores = scores[order]
    _, inv, counts = np.unique(sorted_scores, return_inverse=True, return_counts=True)
    # Assign average rank
    cumcount = np.concatenate(([0], np.cumsum(counts)))
    avg = (cumcount[inv] + cumcount[inv + 1] + 1) / 2.0
    ranks[order] = avg
    r_pos = ranks[pos].sum()
    U = r_pos - n_pos * (n_pos + 1) / 2.0
    return U / (n_pos * n_neg)


def build_arrays(per_strat, assignment):
    """Return {dom -> (scores, labels, idx_in_global)} for items scored via assignment."""
    out = {}
    for dom, strat in assignment.items():
        items = per_strat.get(strat, {})
        rows = [(iid, sc, y) for iid, (sc, y, d) in items.items() if d == dom]
        if not rows:
            continue
        iids = [r[0] for r in rows]
        scores = np.array([r[1] for r in rows], dtype=np.float64)
        labels = np.array([r[2] for r in rows], dtype=np.int64)
        out[dom] = (iids, scores, labels)
    return out


def paired_delta_bootstrap(per_strat, assign_a, assign_b, n_resamples=1000, rng=None):
    rng = rng or np.random.default_rng(20260415)
    # Build common items: intersect domain-wise by item_id
    ba = build_arrays(per_strat, assign_a)
    bb = build_arrays(per_strat, assign_b)
    common = {}
    for dom in set(ba) & set(bb):
        ids_a, sa, ya = ba[dom]
        ids_b, sb, yb = bb[dom]
        # align by iid
        a_map = {iid: (s, y) for iid, s, y in zip(ids_a, sa, ya)}
        b_map = {iid: (s, y) for iid, s, y in zip(ids_b, sb, yb)}
        shared = [iid for iid in ids_a if iid in b_map]
        if not shared:
            continue
        s_a = np.array([a_map[iid][0] for iid in shared])
        s_b = np.array([b_map[iid][0] for iid in shared])
        y = np.array([a_map[iid][1] for iid in shared], dtype=np.int64)
        common[dom] = (s_a, s_b, y)

    def macro(resample_idx=None):
        aa, bb_ = [], []
        for dom, (s_a, s_b, y) in common.items():
            if resample_idx is None:
                idx = np.arange(len(y))
            else:
                idx = resample_idx[dom]
            if len(set(y[idx].tolist())) < 2:
                continue
            aa.append(fast_auroc(s_a[idx], y[idx]))
            bb_.append(fast_auroc(s_b[idx], y[idx]))
        return (float(np.mean(aa)) if aa else 0.0,
                float(np.mean(bb_)) if bb_ else 0.0)

    point_a, point_b = macro()
    deltas = np.empty(n_resamples, dtype=np.float64)
    for r in range(n_resamples):
        idxs = {dom: rng.integers(0, len(v[2]), len(v[2])) for dom, v in common.items()}
        a, b = macro(idxs)
        deltas[r] = a - b
    lo = float(np.percentile(deltas, 2.5))
    hi = float(np.percentile(deltas, 97.5))
    return {
        "macro_a": point_a,
        "macro_b": point_b,
        "delta": point_a - point_b,
        "ci": [lo, hi],
        "significant_p05": (lo > 0) or (hi < 0),
        "n_items": int(sum(len(v[2]) for v in common.values())),
    }


def main():
    bs, exp = load_strategy_scores()
    out = {}
    n_res = 1000
    for bk in ["gpt54", "seedvl", "qwen35"]:
        per_strat = per_item_scores(bs, exp, bk)
        domains = sorted({d for s in per_strat.values() for (_, _, d) in s.values()})
        oracle = oracle_assignment(per_strat)
        calib = calibration_assignment(bk)
        desc = descriptor_assignment(domains, DOMAIN_FAMILY)
        fusion_all = {d: "fusion" for d in domains}
        direct_all = {d: "direct" for d in domains}

        comps = [
            ("descriptor_vs_fusion", desc, fusion_all),
            ("descriptor_vs_direct", desc, direct_all),
            ("calibration_vs_fusion", calib, fusion_all),
            ("calibration_vs_direct", calib, direct_all),
            ("calibration_vs_descriptor", calib, desc),
            ("oracle_vs_fusion", oracle, fusion_all),
            ("oracle_vs_calibration", oracle, calib),
            ("fusion_vs_direct", fusion_all, direct_all),
        ]
        out[bk] = {}
        for name, a, b in comps:
            res = paired_delta_bootstrap(per_strat, a, b, n_resamples=n_res)
            out[bk][name] = res
            sig = "✓" if res["significant_p05"] else "—"
            print(f"  {bk:7s} {name:30s} dA={res['macro_a']:.4f} dB={res['macro_b']:.4f} "
                  f"Δ={res['delta']:+.4f} CI=[{res['ci'][0]:+.4f},{res['ci'][1]:+.4f}] {sig}",
                  flush=True)
    out_path = Path("/hdd1/jiangxi/AD-Agent/refine-logs/ROUTER_BOOTSTRAP.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
