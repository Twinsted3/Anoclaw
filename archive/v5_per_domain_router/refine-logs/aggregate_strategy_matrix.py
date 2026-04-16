#!/usr/bin/env python3
"""Aggregate per-(backbone, domain, strategy) AUROC from result JSONs.

Output: /hdd1/jiangxi/AD-Agent/refine-logs/PER_DOMAIN_STRATEGY_MATRIX.json
"""
import json
import os
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

RESULTS_DIR = Path("/hdd1/jiangxi/AD-Agent/benchmark/results")
OUT_JSON = Path("/hdd1/jiangxi/AD-Agent/refine-logs/PER_DOMAIN_STRATEGY_MATRIX.json")
OUT_MD = Path("/hdd1/jiangxi/AD-Agent/refine-logs/PER_DOMAIN_STRATEGY_MATRIX.md")

# File -> (backbone, strategy)
FILE_MAP = {
    "gpt54_v0_direct_test_all_v2.json": ("gpt54", "direct"),
    "seedvl_v0_direct_test_all_v2.json": ("seedvl", "direct"),
    "qwen35_v0_direct_test_all_v2.json": ("qwen35", "direct"),
    "gpt54_v3_debate_1r_test_all_v2.json": ("gpt54", "debate"),
    "seedvl_v3_debate_1r_test_all_v2.json": ("seedvl", "debate"),
    "qwen35_v3_debate_1r_test_all_v2.json": ("qwen35", "debate"),
    "gpt54_egra_test_all_v2.json": ("gpt54", "interpret"),
    "seedvl_egra_test_all_v2.json": ("seedvl", "interpret"),
    "qwen35_egra_test_all_v2.json": ("qwen35", "interpret"),
    "gpt54_v3_grounded_test_all_v2.json": ("gpt54", "grounded"),
    "qwen35_v3_grounded_test_all_v2.json": ("qwen35", "grounded"),
    "subspacead_test.json": ("expert", "subspacead"),
    "classical_dinov2_patch_test_all.json": ("expert", "patchknn"),
    "classical_dinov2_global_test_all.json": ("expert", "global"),
    # patch_evidence_test.json is keyed by item id, not a list — skip

}


def load_items(path: Path):
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, dict) and "items" in data:
        data = data["items"]
    return data


def items_by_id(items):
    out = {}
    for it in items:
        iid = it.get("item_id")
        if iid is None:
            continue
        out[iid] = it
    return out


def compute_auroc(scores, labels):
    if len(scores) == 0 or len(set(labels)) < 2:
        return None
    try:
        return float(roc_auc_score(labels, scores))
    except Exception:
        return None


def score_from_item(it):
    s = it.get("anomaly_score")
    if s is None:
        s = it.get("anomaly_score_norm")
    if s is None:
        return None
    return float(s)


def per_domain_auroc(items):
    by_dom = defaultdict(lambda: {"scores": [], "labels": []})
    for it in items:
        dom = it.get("domain_code")
        if dom is None:
            continue
        s = score_from_item(it)
        y = it.get("label_gt")
        if s is None or y is None:
            continue
        by_dom[dom]["scores"].append(s)
        by_dom[dom]["labels"].append(int(y))
    out = {}
    for dom, d in by_dom.items():
        out[dom] = {
            "n": len(d["labels"]),
            "auroc": compute_auroc(d["scores"], d["labels"]),
        }
    return out


def simple_fusion(scores_vlm, scores_exp, labels, w=0.2):
    # sigmoid on expert around global median
    exp = np.array(scores_exp, dtype=float)
    med = float(np.median(exp))
    sig = 1.0 / (1.0 + np.exp(-2.0 * (exp - med) / max(med, 1e-6)))
    vlm = np.array(scores_vlm, dtype=float)
    fused = (1 - w) * vlm + w * sig
    return compute_auroc(fused, labels), fused


def main():
    # Load all files we have
    loaded = {}
    for fname, (bk, strat) in FILE_MAP.items():
        p = RESULTS_DIR / fname
        if not p.exists():
            continue
        items = load_items(p)
        loaded[(bk, strat)] = items
        print(f"  loaded {fname}: {len(items)} items, backbone={bk}, strategy={strat}")

    # Compute per-domain AUROC for each (backbone, strategy)
    matrix = {}  # (backbone, strategy) -> {domain: {n, auroc}}
    overall = {}  # (backbone, strategy) -> {n, macro_auroc, micro_auroc}
    for key, items in loaded.items():
        per = per_domain_auroc(items)
        matrix[key] = per
        aurocs = [v["auroc"] for v in per.values() if v["auroc"] is not None]
        scores, labels = [], []
        for it in items:
            s = score_from_item(it)
            y = it.get("label_gt")
            if s is not None and y is not None:
                scores.append(s)
                labels.append(int(y))
        overall[key] = {
            "n": sum(v["n"] for v in per.values()),
            "macro_auroc": float(np.mean(aurocs)) if aurocs else None,
            "micro_auroc": compute_auroc(scores, labels),
            "n_domains": len(aurocs),
        }

    # Compute FUSION strategy (VLM direct + SubspaceAD) per backbone via inner join
    fusion_out = {}
    if ("expert", "subspacead") in loaded:
        exp_items = items_by_id(loaded[("expert", "subspacead")])
        for bk in ["gpt54", "seedvl", "qwen35"]:
            if (bk, "direct") not in loaded:
                continue
            vlm_items = loaded[(bk, "direct")]
            by_dom = defaultdict(lambda: {"vlm": [], "exp": [], "labels": []})
            matched = 0
            for it in vlm_items:
                iid = it["item_id"]
                dom = it["domain_code"]
                y = it.get("label_gt")
                if iid not in exp_items or y is None:
                    continue
                sv = score_from_item(it)
                se = score_from_item(exp_items[iid])
                if sv is None or se is None:
                    continue
                by_dom[dom]["vlm"].append(sv)
                by_dom[dom]["exp"].append(se)
                by_dom[dom]["labels"].append(int(y))
                matched += 1
            # global median on matched set
            all_exp = []
            for d in by_dom.values():
                all_exp.extend(d["exp"])
            med = float(np.median(all_exp)) if all_exp else 0.0
            per = {}
            all_fused, all_labels = [], []
            for dom, d in by_dom.items():
                exp = np.array(d["exp"])
                sig = 1.0 / (1.0 + np.exp(-2.0 * (exp - med) / max(med, 1e-6)))
                vlm = np.array(d["vlm"])
                fused = 0.8 * vlm + 0.2 * sig
                per[dom] = {"n": len(d["labels"]), "auroc": compute_auroc(fused, d["labels"])}
                all_fused.extend(fused.tolist())
                all_labels.extend(d["labels"])
            fusion_out[bk] = per
            aurocs = [v["auroc"] for v in per.values() if v["auroc"] is not None]
            overall[(bk, "fusion_v0_subspace")] = {
                "n": len(all_labels),
                "macro_auroc": float(np.mean(aurocs)) if aurocs else None,
                "micro_auroc": compute_auroc(all_fused, all_labels),
                "n_domains": len(aurocs),
            }
            matrix[(bk, "fusion_v0_subspace")] = per
            print(f"  fusion {bk}: matched {matched}, macro {overall[(bk,'fusion_v0_subspace')]['macro_auroc']:.4f}")

    # --- Per-domain BEST strategy per backbone (oracle) ---
    # Canonical domain list
    domains = sorted({d for per in matrix.values() for d in per.keys()})
    oracle_per_backbone = {}
    for bk in ["gpt54", "seedvl", "qwen35"]:
        per_dom_best = {}
        for d in domains:
            candidates = []
            for (bk2, strat), per in matrix.items():
                if bk2 != bk and bk2 != "expert":
                    continue
                if d in per and per[d]["auroc"] is not None:
                    candidates.append((per[d]["auroc"], strat, bk2))
            if not candidates:
                continue
            candidates.sort(reverse=True)
            best = candidates[0]
            per_dom_best[d] = {
                "strategy": f"{best[2]}:{best[1]}",
                "auroc": best[0],
                "candidates": [{"strategy": f"{c[2]}:{c[1]}", "auroc": c[0]} for c in candidates[:5]],
            }
        aurocs = [v["auroc"] for v in per_dom_best.values()]
        oracle_per_backbone[bk] = {
            "per_domain": per_dom_best,
            "macro_auroc": float(np.mean(aurocs)) if aurocs else None,
        }

    # --- Serialise ---
    def tuple_key(t):
        return "|".join(t) if isinstance(t, tuple) else t

    out = {
        "matrix": {tuple_key(k): v for k, v in matrix.items()},
        "overall": {tuple_key(k): v for k, v in overall.items()},
        "oracle_per_backbone": oracle_per_backbone,
        "domains": domains,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nWrote {OUT_JSON}")

    # --- Markdown summary ---
    md = ["# Per-Domain × Strategy Matrix\n"]
    md.append("## Macro AUROC summary (test split)\n")
    md.append("| Backbone | Strategy | Macro AUROC | n domains | n items |")
    md.append("|----------|----------|-------------|-----------|---------|")
    for (bk, strat), v in sorted(overall.items()):
        if v["macro_auroc"] is None:
            continue
        md.append(f"| {bk} | {strat} | {v['macro_auroc']:.4f} | {v['n_domains']} | {v['n']} |")
    md.append("")

    md.append("## Per-domain AUROC per strategy\n")
    # for each backbone, produce a table domain x strategy
    strategies = ["direct", "fusion_v0_subspace", "debate", "interpret", "grounded"]
    for bk in ["gpt54", "seedvl", "qwen35"]:
        md.append(f"### {bk}\n")
        header = "| Domain | " + " | ".join(strategies) + " | ExpertSubspace | Oracle |"
        sep = "|--------|" + "---|" * (len(strategies) + 2)
        md.append(header)
        md.append(sep)
        for d in domains:
            row = [d]
            for strat in strategies:
                key = (bk, strat)
                if key in matrix and d in matrix[key] and matrix[key][d]["auroc"] is not None:
                    row.append(f"{matrix[key][d]['auroc']:.3f}")
                else:
                    row.append("—")
            # expert
            key = ("expert", "subspacead")
            if key in matrix and d in matrix[key] and matrix[key][d]["auroc"] is not None:
                row.append(f"{matrix[key][d]['auroc']:.3f}")
            else:
                row.append("—")
            # oracle
            orc = oracle_per_backbone.get(bk, {}).get("per_domain", {}).get(d)
            if orc:
                row.append(f"{orc['auroc']:.3f} ({orc['strategy']})")
            else:
                row.append("—")
            md.append("| " + " | ".join(row) + " |")
        orc_macro = oracle_per_backbone.get(bk, {}).get("macro_auroc")
        if orc_macro is not None:
            md.append(f"\n**Oracle macro AUROC ({bk})**: {orc_macro:.4f}\n")
    with open(OUT_MD, "w") as f:
        f.write("\n".join(md))
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
