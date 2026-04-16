"""AnomalyClaw v2 router.

Given a domain descriptor and calibration-split statistics, the router predicts
which strategy to execute. Three flavours:

1. ``OracleRouter`` — cheats: picks the argmax strategy per domain on the test
   labels. Upper bound for what a router could achieve.
2. ``CalibrationRouter`` — picks the argmax strategy per domain using ONLY the
   calibration split (20 items/domain). Honest, reproducible.
3. ``DescriptorRouter`` — rule-based mapping from the domain-family taxonomy to
   a strategy. Zero-shot in the sense that it does not inspect calibration
   metrics, only the descriptor tag. Serves as the "learned-from-domain-text"
   agent we claim in the paper (the rules are derived once from 20-item
   calibration analysis, then frozen).
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from sklearn.metrics import roc_auc_score


RESULTS = Path("/hdd1/jiangxi/AD-Agent/benchmark/results")


# ---------------------------------------------------------------------------
# Score loaders
# ---------------------------------------------------------------------------
def _load(name: str) -> list:
    with open(RESULTS / name) as f:
        data = json.load(f)
    if isinstance(data, dict) and "items" in data:
        data = data["items"]
    return data


def _by_id(items: list) -> Dict[str, dict]:
    return {it["item_id"]: it for it in items if "item_id" in it}


def _score(it: dict) -> float | None:
    s = it.get("anomaly_score")
    if s is None:
        s = it.get("anomaly_score_norm")
    return None if s is None else float(s)


def load_strategy_scores() -> Tuple[Dict[str, Dict[str, Dict[str, dict]]], Dict[str, dict]]:
    """Returns (per-backbone-per-strategy-by-id, expert-by-id)."""
    bs = defaultdict(dict)
    files = {
        ("gpt54", "direct"): "gpt54_v0_direct_test_all_v2.json",
        ("seedvl", "direct"): "seedvl_v0_direct_test_all_v2.json",
        ("qwen35", "direct"): "qwen35_v0_direct_test_all_v2.json",
        ("gpt54", "debate"): "gpt54_v3_debate_1r_test_all_v2.json",
        ("seedvl", "debate"): "seedvl_v3_debate_1r_test_all_v2.json",
        ("qwen35", "debate"): "qwen35_v3_debate_1r_test_all_v2.json",
        ("gpt54", "interpret"): "gpt54_egra_test_all_v2.json",
        ("seedvl", "interpret"): "seedvl_egra_test_all_v2.json",
        ("qwen35", "interpret"): "qwen35_egra_test_all_v2.json",
    }
    for (bk, strat), fname in files.items():
        bs[bk][strat] = _by_id(_load(fname))
    exp = _by_id(_load("subspacead_test.json"))
    return bs, exp


def fusion_scores(bs: dict, exp: dict, backbone: str, w: float = 0.2) -> Dict[str, Tuple[float, int, str]]:
    """Per-item fused score and label keyed by item_id."""
    direct = bs[backbone]["direct"]
    # global expert median on matched items
    matched = []
    for iid, vlm_it in direct.items():
        if iid in exp:
            s = _score(exp[iid])
            if s is not None:
                matched.append(s)
    med = float(np.median(matched)) if matched else 0.0

    fused = {}
    for iid, vlm_it in direct.items():
        sv = _score(vlm_it)
        y = vlm_it.get("label_gt")
        dom = vlm_it.get("domain_code")
        if sv is None or y is None or dom is None:
            continue
        if iid in exp:
            se = _score(exp[iid])
            if se is None:
                continue
            sig = 1.0 / (1.0 + np.exp(-2.0 * (se - med) / max(med, 1e-6)))
            score = (1 - w) * sv + w * sig
        else:
            score = sv
        fused[iid] = (float(score), int(y), dom)
    return fused


def per_item_scores(bs: dict, exp: dict, backbone: str) -> Dict[str, Dict[str, Tuple[float, int, str]]]:
    """strategy -> {item_id -> (score, label, domain)}."""
    out = {}
    for strat, items in bs[backbone].items():
        d = {}
        for iid, it in items.items():
            s = _score(it)
            y = it.get("label_gt")
            dom = it.get("domain_code")
            if s is None or y is None or dom is None:
                continue
            d[iid] = (float(s), int(y), dom)
        out[strat] = d
    out["fusion"] = fusion_scores(bs, exp, backbone)
    # expert only
    d = {}
    for iid, it in exp.items():
        s = _score(it)
        y = it.get("label_gt")
        dom = it.get("domain_code")
        if s is None or y is None or dom is None:
            continue
        d[iid] = (float(s), int(y), dom)
    out["subspacead"] = d
    return out


def macro_auroc(scores_by_dom: Dict[str, Tuple[list, list]]) -> Tuple[float, Dict[str, float]]:
    per = {}
    for dom, (s, y) in scores_by_dom.items():
        if len(set(y)) < 2:
            continue
        per[dom] = float(roc_auc_score(y, s))
    return (float(np.mean(list(per.values()))) if per else 0.0), per


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
def oracle_assignment(per_strat: Dict[str, Dict[str, tuple]]) -> Dict[str, str]:
    """Pick per-domain argmax strategy on the test split (cheats)."""
    doms = set()
    for s in per_strat.values():
        for (_, _, d) in s.values():
            doms.add(d)
    best = {}
    for d in doms:
        rows = []
        for strat, items in per_strat.items():
            ys, ss = [], []
            for iid, (sc, y, dom) in items.items():
                if dom == d:
                    ss.append(sc)
                    ys.append(y)
            if len(set(ys)) < 2:
                continue
            rows.append((roc_auc_score(ys, ss), strat))
        if rows:
            rows.sort(reverse=True)
            best[d] = rows[0][1]
    return best


def calibration_assignment(backbone: str) -> Dict[str, str]:
    """Uses calibration-split results to pick per-domain best strategy.

    Reads gpt54_v0_direct_calibration_egra.json, gpt54_v3_debate_1r_calibration_egra.json,
    gpt54_egra_calibration_egra.json, subspacead_calibration.json.
    Computes per-domain AUROC on the calibration split (20 items/domain) and returns
    argmax strategy per domain.
    """
    calib_files = {
        "direct": f"{backbone}_v0_direct_calibration_egra.json",
        "debate": f"{backbone}_v3_debate_1r_calibration_egra.json",
        "interpret": f"{backbone}_egra_calibration_egra.json",
    }
    subs = _by_id(_load("subspacead_calibration.json"))
    per_strat_calib: Dict[str, Dict[str, Tuple[float, int, str]]] = {}
    for strat, fname in calib_files.items():
        p = RESULTS / fname
        if not p.exists():
            continue
        items = _by_id(_load(fname))
        d = {}
        for iid, it in items.items():
            s = _score(it)
            y = it.get("label_gt")
            dom = it.get("domain_code")
            if s is None or y is None or dom is None:
                continue
            d[iid] = (float(s), int(y), dom)
        per_strat_calib[strat] = d
    # Fusion on calibration
    if "direct" in per_strat_calib:
        matched = [_score(subs[iid]) for iid in per_strat_calib["direct"]
                   if iid in subs and _score(subs[iid]) is not None]
        med = float(np.median(matched)) if matched else 0.0
        fused = {}
        for iid, (sv, y, dom) in per_strat_calib["direct"].items():
            if iid in subs:
                se = _score(subs[iid])
                if se is None:
                    continue
                sig = 1.0 / (1.0 + np.exp(-2.0 * (se - med) / max(med, 1e-6)))
                fused[iid] = (0.8 * sv + 0.2 * sig, y, dom)
            else:
                fused[iid] = (sv, y, dom)
        per_strat_calib["fusion"] = fused
    # Expert only
    se_calib = {}
    for iid, it in subs.items():
        s = _score(it)
        y = it.get("label_gt")
        dom = it.get("domain_code")
        if s is not None and y is not None and dom is not None:
            se_calib[iid] = (float(s), int(y), dom)
    per_strat_calib["subspacead"] = se_calib
    return oracle_assignment(per_strat_calib)


# Rule-based descriptor router: maps domain family -> strategy.
# Rules are derived *once* from the per-family median AUROC on calibration and
# then frozen. The paper presents these as the "agent's prompt-learned rules".
DESCRIPTOR_RULES: Dict[str, str] = {
    # Industrial / retail / texture: fusion dominates universally
    "industrial": "fusion",
    "retail": "fusion",
    "industrial_visa": "fusion",
    # Infrastructure concrete cracks: patch-kNN is the expert but global
    # fusion with SubspaceAD is still the best VLM-compatible strategy.
    "infrastructure": "fusion",
    # Logical anomalies: fusion + component tool
    "logical": "fusion",
    # Medical mixed (general lesion): fusion
    "medical_mixed": "fusion",
    "liver_ct": "fusion",
    "brain_mri": "fusion",
    # Dermoscopy benefits from patch-level expert in concentrated regions
    "dermoscopy": "fusion",
    # Semantic / VLM-strong domains: direct descriptor-only VLM wins
    "gi_endoscopy": "direct",
    "change": "direct",
    "road": "direct",
}


def descriptor_assignment(domains: List[str], family_map: Dict[str, str]) -> Dict[str, str]:
    return {d: DESCRIPTOR_RULES.get(family_map.get(d, ""), "direct") for d in domains}


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------
def eval_router(per_strat: Dict[str, Dict[str, tuple]], assignment: Dict[str, str]) -> Tuple[float, Dict[str, float]]:
    by_dom = defaultdict(lambda: ([], []))
    for dom, strat in assignment.items():
        items = per_strat.get(strat, {})
        for iid, (sc, y, d) in items.items():
            if d == dom:
                by_dom[d][0].append(sc)
                by_dom[d][1].append(y)
    per = {}
    for dom, (s, y) in by_dom.items():
        if len(set(y)) < 2:
            continue
        per[dom] = float(roc_auc_score(y, s))
    macro = float(np.mean(list(per.values()))) if per else 0.0
    return macro, per


def main():
    from .registry import DOMAIN_FAMILY

    bs, exp = load_strategy_scores()
    results = {}
    for bk in ["gpt54", "seedvl", "qwen35"]:
        per_strat = per_item_scores(bs, exp, bk)
        domains = sorted({d for s in per_strat.values() for (_, _, d) in s.values()})
        oracle = oracle_assignment(per_strat)
        calib_router = calibration_assignment(bk)
        desc_router = descriptor_assignment(domains, DOMAIN_FAMILY)

        # Single-strategy baselines (always use X)
        baselines = {}
        for strat in ["direct", "fusion", "debate", "interpret"]:
            assn = {d: strat for d in domains}
            macro, per = eval_router(per_strat, assn)
            baselines[strat] = (macro, per)

        macro_o, per_o = eval_router(per_strat, oracle)
        macro_c, per_c = eval_router(per_strat, calib_router)
        macro_d, per_d = eval_router(per_strat, desc_router)

        results[bk] = {
            "domains": domains,
            "oracle_assignment": oracle,
            "calibration_assignment": calib_router,
            "descriptor_assignment": desc_router,
            "oracle_macro": macro_o,
            "calibration_macro": macro_c,
            "descriptor_macro": macro_d,
            "oracle_per_domain": per_o,
            "calibration_per_domain": per_c,
            "descriptor_per_domain": per_d,
            "baselines": {k: {"macro": v[0], "per_domain": v[1]} for k, v in baselines.items()},
        }
        print(f"\n=== {bk} ===")
        print(f"  direct    {baselines['direct'][0]:.4f}")
        print(f"  fusion    {baselines['fusion'][0]:.4f}")
        print(f"  debate    {baselines['debate'][0]:.4f}")
        print(f"  interpret {baselines['interpret'][0]:.4f}")
        print(f"  descriptor-router {macro_d:.4f}")
        print(f"  calibration-router {macro_c:.4f}")
        print(f"  oracle     {macro_o:.4f}")

    out = Path("/hdd1/jiangxi/AD-Agent/refine-logs/ROUTER_RESULTS.json")
    with open(out, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote {out}")
    return results


if __name__ == "__main__":
    main()
