"""After SeedVL/Qwen35 v3 runs complete, regenerate stats and update paper text.

This script:
1. Loads anomaclaw_v3 results for any backbones whose run completed.
2. Computes macro AUROC + per-domain AUROC.
3. Computes paired bootstrap vs fusion (using existing fusion scores from agent
   files keyed by item_id) on the v3-completed items.
4. Prints a summary that can be pasted into the paper (Table 1 row, Table 2 row,
   Finding 3 paragraph).
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

R = Path("/hdd1/jiangxi/AD-Agent/benchmark/results")


def by_id(items):
    return {x["item_id"]: x for x in items if "item_id" in x}


def macro(by_dom):
    out = {}
    for d, (s, y) in by_dom.items():
        if len(set(y)) >= 2:
            out[d] = float(roc_auc_score(y, s))
    return float(np.mean(list(out.values()))) if out else 0.0, out


def fusion_scores(direct_items: dict, expert_items: dict, w=0.2):
    matched_exp = [float(expert_items[i].get("anomaly_score", 0))
                   for i in direct_items if i in expert_items]
    m = float(np.median(matched_exp)) if matched_exp else 0.0
    out = {}
    for iid, vlm_it in direct_items.items():
        sv = vlm_it.get("anomaly_score")
        if sv is None:
            continue
        if iid in expert_items:
            se = expert_items[iid].get("anomaly_score")
            if se is None:
                out[iid] = float(sv)
            else:
                sig = 1.0 / (1.0 + np.exp(-2.0 * (se - m) / max(m, 1e-6)))
                out[iid] = (1 - w) * float(sv) + w * float(sig)
        else:
            out[iid] = float(sv)
    return out


def stratified_paired_bootstrap(items_a, items_b, labels_by_id, doms_by_id, n=1000, seed=20260415):
    rng = np.random.default_rng(seed)
    common = sorted(set(items_a) & set(items_b) & set(labels_by_id) & set(doms_by_id))
    if not common:
        return None
    by_dom_idx = defaultdict(list)
    for i, iid in enumerate(common):
        by_dom_idx[doms_by_id[iid]].append(i)
    sa = np.array([items_a[i] for i in common])
    sb = np.array([items_b[i] for i in common])
    yy = np.array([labels_by_id[i] for i in common])

    def macro_idx(idx):
        a, b = [], []
        for dom, ids in by_dom_idx.items():
            sub = [j for j in idx if j in set(ids)]
            if not sub:
                continue
            ya = yy[sub]
            if len(set(ya.tolist())) < 2:
                continue
            a.append(roc_auc_score(ya, sa[sub]))
            b.append(roc_auc_score(ya, sb[sub]))
        return (float(np.mean(a)) if a else 0.0, float(np.mean(b)) if b else 0.0)

    pa, pb = macro_idx(list(range(len(common))))
    deltas = []
    for _ in range(n):
        idx = []
        for ids in by_dom_idx.values():
            idx.extend(rng.choice(ids, len(ids), replace=True).tolist())
        a, b = macro_idx(idx)
        deltas.append(a - b)
    deltas = np.array(deltas)
    lo, hi = np.percentile(deltas, 2.5), np.percentile(deltas, 97.5)
    return {"macro_a": pa, "macro_b": pb, "delta": pa - pb,
            "ci": [float(lo), float(hi)], "sig": (lo > 0) or (hi < 0)}


BK_FILES = {
    "seedvl": ("seedvl_v0_direct_test_all_v2.json", "anomaclaw_v3_seedvl_test.json"),
    "qwen35": ("qwen35_v0_direct_test_all_v2.json", "anomaclaw_v3_qwen35_test.json"),
}


def main():
    # SubspaceAD shared expert
    exp_items = by_id(json.load(open(R / "subspacead_test.json")))

    summary = {}
    for bk, (direct_f, v3_f) in BK_FILES.items():
        v3_path = R / v3_f
        if not v3_path.exists():
            print(f"[skip] {bk}: {v3_path} not found")
            continue
        v3 = json.load(open(v3_path))
        v3_ok = [x for x in v3 if x.get("anomaly_score") is not None
                 and not x.get("error")]
        if len(v3_ok) < 100:
            print(f"[skip] {bk}: only {len(v3_ok)} v3 items, need more")
            continue
        v3_dict = {x["item_id"]: float(x["anomaly_score"]) for x in v3_ok}

        direct_items = by_id(json.load(open(R / direct_f)))
        direct_dict = {iid: float(it.get("anomaly_score", 0))
                       for iid, it in direct_items.items()
                       if it.get("anomaly_score") is not None}
        fusion_dict = fusion_scores(direct_items, exp_items)

        labels = {iid: int(it["label_gt"]) for iid, it in direct_items.items()
                  if it.get("label_gt") is not None}
        doms = {iid: it["domain_code"] for iid, it in direct_items.items()
                if it.get("domain_code")}

        # Restrict labels/doms to v3 coverage
        common = set(v3_dict) & set(labels)
        # macro per system on common items
        def per_dom_macro(score_dict):
            by = defaultdict(lambda: ([], []))
            for iid in common:
                if iid in score_dict:
                    by[doms[iid]][0].append(score_dict[iid])
                    by[doms[iid]][1].append(labels[iid])
            return macro(by)

        m_v3, per_v3 = per_dom_macro(v3_dict)
        m_dir, per_dir = per_dom_macro(direct_dict)
        m_fus, per_fus = per_dom_macro(fusion_dict)

        # Bootstrap
        bs_v3_vs_fus = stratified_paired_bootstrap(v3_dict, fusion_dict, labels, doms)
        bs_v3_vs_dir = stratified_paired_bootstrap(v3_dict, direct_dict, labels, doms)

        summary[bk] = {
            "v3_items": len(v3_ok),
            "common_items": len(common),
            "macro_v3": m_v3, "macro_direct": m_dir, "macro_fusion": m_fus,
            "per_domain_v3": per_v3,
            "per_domain_fusion": per_fus,
            "bootstrap_v3_vs_fusion": bs_v3_vs_fus,
            "bootstrap_v3_vs_direct": bs_v3_vs_dir,
        }
        print(f"\n=== {bk} ===")
        print(f"  items: v3 ok={len(v3_ok)}, common with direct/labels={len(common)}")
        print(f"  macro AUROC: v3={m_v3:.4f}  fusion={m_fus:.4f}  direct={m_dir:.4f}")
        print(f"  per-domain v3:")
        for d in sorted(per_v3):
            print(f"    {d}: v3={per_v3[d]:.3f}  fus={per_fus.get(d, 0):.3f}")
        if bs_v3_vs_fus:
            print(f"  bootstrap v3-vs-fusion: Δ={bs_v3_vs_fus['delta']:+.4f} "
                  f"CI=[{bs_v3_vs_fus['ci'][0]:+.4f},{bs_v3_vs_fus['ci'][1]:+.4f}] "
                  f"{'✓' if bs_v3_vs_fus['sig'] else '—'}")
        if bs_v3_vs_dir:
            print(f"  bootstrap v3-vs-direct: Δ={bs_v3_vs_dir['delta']:+.4f} "
                  f"CI=[{bs_v3_vs_dir['ci'][0]:+.4f},{bs_v3_vs_dir['ci'][1]:+.4f}] "
                  f"{'✓' if bs_v3_vs_dir['sig'] else '—'}")

        # Strategy executed distribution
        sd = defaultdict(int)
        plan_by_dom = defaultdict(set)
        for x in v3_ok:
            s = x.get("plan", {}).get("strategy_executed")
            sd[s] += 1
            plan_by_dom[x["domain_code"]].add(x.get("plan", {}).get("strategy_planned"))
        print(f"  strategy executed: {dict(sd)}")
        print(f"  strategies planned per domain: { {d: list(s) for d, s in plan_by_dom.items()} }")

    out = Path("/hdd1/jiangxi/AD-Agent/refine-logs/V3_RESULTS_SUMMARY.json")
    with open(out, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
