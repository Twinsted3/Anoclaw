"""Stratified paired bootstrap for router vs. single-strategy baselines."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from sklearn.metrics import roc_auc_score

from .router import (
    load_strategy_scores,
    per_item_scores,
    oracle_assignment,
    calibration_assignment,
    descriptor_assignment,
)
from .registry import DOMAIN_FAMILY

RNG = np.random.default_rng(20260415)


def paired_series(per_strat, assignment_a, assignment_b, domains):
    """For each item, return the score under assignment A and assignment B. Items are
    aligned by (item_id, domain) and scored under the strategy each assignment selects
    for that item's domain."""
    # Build item_id -> (score_a, score_b, y, dom)
    # Strategy_a is fixed to assignment_a[dom] for each dom; similarly b.
    item_scores_a = {}
    item_scores_b = {}
    item_labels = {}
    item_domains = {}

    # Need all items; for each item, compute score under assignment_a[dom] and _b[dom].
    # For each strategy s in per_strat, iterate items.
    dom_to_strat_a = assignment_a
    dom_to_strat_b = assignment_b

    # Collect all item_ids present across all strategies needed
    needed_strats = set(assignment_a.values()) | set(assignment_b.values())
    present = defaultdict(set)
    for s in needed_strats:
        if s in per_strat:
            for iid, (_, _, dom) in per_strat[s].items():
                present[iid].add(s)

    for iid, strats in present.items():
        # Need the item's domain
        any_strat = next(iter(strats))
        _, y, dom = per_strat[any_strat][iid]
        strat_a = dom_to_strat_a.get(dom)
        strat_b = dom_to_strat_b.get(dom)
        if strat_a is None or strat_b is None:
            continue
        if iid not in per_strat.get(strat_a, {}) or iid not in per_strat.get(strat_b, {}):
            continue
        sa, _, _ = per_strat[strat_a][iid]
        sb, _, _ = per_strat[strat_b][iid]
        item_scores_a[iid] = sa
        item_scores_b[iid] = sb
        item_labels[iid] = y
        item_domains[iid] = dom
    return item_scores_a, item_scores_b, item_labels, item_domains


def stratified_bootstrap_delta(item_scores_a, item_scores_b, item_labels, item_domains,
                                n_resamples: int = 1000):
    # Index items by domain
    by_dom = defaultdict(list)
    for iid in item_labels:
        by_dom[item_domains[iid]].append(iid)
    # Point estimate
    ids = list(item_labels.keys())
    labels = np.array([item_labels[i] for i in ids])
    sa = np.array([item_scores_a[i] for i in ids])
    sb = np.array([item_scores_b[i] for i in ids])
    id_idx = {iid: i for i, iid in enumerate(ids)}

    def compute_macro(sub_idx):
        # compute per-domain AUROC on indices, then macro-average
        dom_ys = defaultdict(list)
        dom_sa = defaultdict(list)
        dom_sb = defaultdict(list)
        for j in sub_idx:
            iid = ids[j]
            dom = item_domains[iid]
            dom_ys[dom].append(labels[j])
            dom_sa[dom].append(sa[j])
            dom_sb[dom].append(sb[j])
        auc_a, auc_b = [], []
        for dom in dom_ys:
            if len(set(dom_ys[dom])) < 2:
                continue
            auc_a.append(roc_auc_score(dom_ys[dom], dom_sa[dom]))
            auc_b.append(roc_auc_score(dom_ys[dom], dom_sb[dom]))
        return float(np.mean(auc_a)) if auc_a else 0.0, float(np.mean(auc_b)) if auc_b else 0.0

    point_a, point_b = compute_macro(range(len(ids)))
    deltas = []
    for _ in range(n_resamples):
        resampled = []
        for dom, iids in by_dom.items():
            idx = [id_idx[iid] for iid in iids]
            idx = RNG.choice(idx, size=len(idx), replace=True)
            resampled.extend(idx.tolist())
        a, b = compute_macro(resampled)
        deltas.append(a - b)
    deltas = np.array(deltas)
    lo, hi = float(np.percentile(deltas, 2.5)), float(np.percentile(deltas, 97.5))
    sig = (lo > 0) or (hi < 0)
    return point_a, point_b, point_a - point_b, (lo, hi), sig


def main():
    bs, exp = load_strategy_scores()
    all_bk = {}
    for bk in ["gpt54", "seedvl", "qwen35"]:
        per_strat = per_item_scores(bs, exp, bk)
        domains = sorted({d for s in per_strat.values() for (_, _, d) in s.values()})
        oracle = oracle_assignment(per_strat)
        calib = calibration_assignment(bk)
        desc = descriptor_assignment(domains, DOMAIN_FAMILY)
        fusion_all = {d: "fusion" for d in domains}
        direct_all = {d: "direct" for d in domains}

        comparisons = [
            ("descriptor_vs_fusion", desc, fusion_all),
            ("descriptor_vs_direct", desc, direct_all),
            ("calibration_vs_fusion", calib, fusion_all),
            ("calibration_vs_direct", calib, direct_all),
            ("calibration_vs_descriptor", calib, desc),
            ("oracle_vs_fusion", oracle, fusion_all),
            ("oracle_vs_calibration", oracle, calib),
        ]
        out = {}
        for name, a, b in comparisons:
            sa, sb, yy, dd = paired_series(per_strat, a, b, domains)
            if not yy:
                continue
            pa, pb, d, ci, sig = stratified_bootstrap_delta(sa, sb, yy, dd, n_resamples=1000)
            out[name] = {
                "macro_a": pa,
                "macro_b": pb,
                "delta": d,
                "ci": list(ci),
                "significant_p05": sig,
                "n": len(yy),
            }
            print(f"  {bk:7s} {name:30s} dA={pa:.4f} dB={pb:.4f} Δ={d:+.4f} CI=[{ci[0]:+.4f},{ci[1]:+.4f}] {'✓' if sig else '—'}")
        all_bk[bk] = out
    out_path = Path("/hdd1/jiangxi/AD-Agent/refine-logs/ROUTER_BOOTSTRAP.json")
    with open(out_path, "w") as f:
        json.dump(all_bk, f, indent=2)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
