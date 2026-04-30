"""Generate paper/figures/v2_main_results_v12.json.

Computes per-backbone per-domain AUROC for v12-passive (blend of the parallel
Direct + v9-with-v8-tools-and-v10-prompt agent) and compares to v10, both
on the CrossDomainVAD-12 test split. Produces:
  - macro AUROC: direct, v9, v10_blend, v12_blend
  - per-domain AUROC for the same four scores
  - 95% stratified paired bootstrap CI on macro (v12 - v10), per backbone,
    matching the existing table-1 bootstrap protocol (n=1000 resamples,
    per-domain stratification, item_id alignment).

Only Qwen3.5 and SeedVL are populated at this point; GPT retries were
blocked on sub2api outage at 2026-04-24.
"""
from __future__ import annotations

import collections
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score


ROOT = Path("/hdd1/jiangxi/AD-Agent")
OUT_PATH = ROOT / "paper" / "figures" / "v2_main_results_v12.json"


def load_dir(p):
    rows = []
    for f in sorted(Path(p).glob("D*.json"), key=lambda x: int(x.stem[1:])):
        rows.extend(json.load(open(f)))
    return rows


def load_file(p):
    return json.load(open(p))


def filter_ok(rows):
    return [
        x for x in rows
        if x.get("mode") == "anomaly_detection"
        and x.get("direct_score") is not None
        and x.get("v9_score") is not None
        and not x.get("error")
        and x.get("label_gt") is not None
    ]


def macro_auroc(rows, score_key=None, scorer=None):
    """Macro AUROC: equally weighted mean over domains."""
    by_dom = collections.defaultdict(list)
    for x in rows:
        by_dom[x["domain_code"]].append(x)
    aurocs = []
    for dc, items in by_dom.items():
        y = np.array([x["label_gt"] for x in items])
        if len(set(y)) < 2:
            continue
        if scorer is not None:
            s = np.array([scorer(x) for x in items])
        else:
            s = np.array([x[score_key] for x in items])
        aurocs.append(roc_auc_score(y, s))
    return float(np.mean(aurocs))


def per_domain_auroc(rows, scorer):
    out = {}
    by_dom = collections.defaultdict(list)
    for x in rows:
        by_dom[x["domain_code"]].append(x)
    for dc, items in by_dom.items():
        y = np.array([x["label_gt"] for x in items])
        s = np.array([scorer(x) for x in items])
        au = float(roc_auc_score(y, s)) if len(set(y)) == 2 else float("nan")
        out[dc] = {"auroc": au, "n": len(items)}
    return out


def paired_bootstrap_delta(rows_v10, rows_v12, scorer_v10, scorer_v12,
                           n_resamples=1000, seed=42):
    """Stratified paired bootstrap over common item_ids.

    For each resample: within each domain, sample items with replacement;
    compute macro AUROC for each method using the SAME resampled set;
    record the macro delta.

    Returns (mean_delta_pp, lo_pp, hi_pp, p_delta_positive).
    """
    rng = np.random.default_rng(seed)
    # Index by item_id for paired lookup
    by_id_v10 = {x["item_id"]: x for x in rows_v10}
    by_id_v12 = {x["item_id"]: x for x in rows_v12}
    common_ids = sorted(set(by_id_v10) & set(by_id_v12))

    # Group common ids by domain for stratification
    dom_to_ids = collections.defaultdict(list)
    for iid in common_ids:
        dom_to_ids[by_id_v12[iid]["domain_code"]].append(iid)
    domains = sorted(dom_to_ids)

    deltas = []
    for _ in range(n_resamples):
        # Per-domain, sample w/ replacement, same indices for both methods
        au_v10 = []
        au_v12 = []
        for dc in domains:
            ids = dom_to_ids[dc]
            idx = rng.integers(0, len(ids), size=len(ids))
            sampled = [ids[i] for i in idx]
            y = np.array([by_id_v12[iid]["label_gt"] for iid in sampled])
            if len(set(y)) < 2:
                continue
            s10 = np.array([scorer_v10(by_id_v10[iid]) for iid in sampled])
            s12 = np.array([scorer_v12(by_id_v12[iid]) for iid in sampled])
            au_v10.append(roc_auc_score(y, s10))
            au_v12.append(roc_auc_score(y, s12))
        if not au_v10:
            continue
        deltas.append(float(np.mean(au_v12) - np.mean(au_v10)))
    deltas = np.array(deltas)
    mean_pp = float(deltas.mean() * 100)
    lo_pp = float(np.percentile(deltas, 2.5) * 100)
    hi_pp = float(np.percentile(deltas, 97.5) * 100)
    p_pos = float((deltas > 0).mean())
    return {
        "mean_delta_pp": round(mean_pp, 3),
        "ci95_lo_pp": round(lo_pp, 3),
        "ci95_hi_pp": round(hi_pp, 3),
        "p_delta_positive": round(p_pos, 3),
        "n_resamples": n_resamples,
        "n_common_items": len(common_ids),
    }


BACKBONES = {
    "qwen3":  {"v12": ROOT / "benchmark/results/v2/v12_passive_test",
               "v10": ROOT / "benchmark/results/v2/v10_agent_qwen3_test.json",
               "label": "Qwen3.5-VL-27B"},
    "seedvl": {"v12": ROOT / "benchmark/results/v2/v12_passive_test_seedvl",
               "v10": ROOT / "benchmark/results/v2/v10_agent_seedvl_test.json",
               "label": "SeedVL"},
    "gpt":    {"v12": ROOT / "benchmark/results/v2/v12_passive_test_gpt",
               "v10": ROOT / "benchmark/results/v2/v10_agent_gpt_test.json",
               "label": "GPT-5.4"},
}


def blend(x):
    return 0.5 * x["direct_score"] + 0.5 * x["v9_score"]


def main():
    out = {}
    for bk, cfg in BACKBONES.items():
        v10_all = load_file(cfg["v10"])
        v12_all = load_dir(cfg["v12"])
        v10_ok = filter_ok(v10_all)
        v12_ok = filter_ok(v12_all)
        v10_err = sum(1 for r in v10_all if r.get("error"))
        v12_err = sum(1 for r in v12_all if r.get("error"))

        # Skip GPT if too few valid items (retry blocked)
        if len(v12_ok) < 500:
            out[bk] = {
                "label": cfg["label"],
                "status": "pending_retry",
                "v10_n": len(v10_ok),
                "v12_n": len(v12_ok),
                "v12_err": v12_err,
                "note": "sub2api outage blocked full v12 run; GPT rows pending retry"
            }
            continue

        # Macro AUROC for each score family
        macro = {
            "direct":    macro_auroc(v12_ok, score_key="direct_score"),
            "v9":        macro_auroc(v12_ok, score_key="v9_score"),
            "v12_blend": macro_auroc(v12_ok, scorer=blend),
            "v10_blend": macro_auroc(v10_ok, scorer=blend),
        }

        # Per-domain (v12 blend)
        pd_v12 = per_domain_auroc(v12_ok, scorer=blend)
        pd_v10 = per_domain_auroc(v10_ok, scorer=blend)

        # Stratified paired bootstrap on the common item-id pool
        boot = paired_bootstrap_delta(
            v10_ok, v12_ok,
            scorer_v10=blend, scorer_v12=blend,
            n_resamples=1000, seed=42,
        )

        out[bk] = {
            "label": cfg["label"],
            "status": "complete",
            "v10_n": len(v10_ok), "v12_n": len(v12_ok),
            "v10_err": v10_err, "v12_err": v12_err,
            "macro": {k: round(v, 4) for k, v in macro.items()},
            "per_domain_v12": {d: {"auroc": round(v["auroc"], 4), "n": v["n"]}
                               for d, v in pd_v12.items()},
            "per_domain_v10": {d: {"auroc": round(v["auroc"], 4), "n": v["n"]}
                               for d, v in pd_v10.items()},
            "bootstrap_v12_minus_v10": boot,
        }

        print(f"=== {cfg['label']} ===")
        print(f"  v10 n={len(v10_ok)} err={v10_err}  v12 n={len(v12_ok)} err={v12_err}")
        print(f"  macro: direct={macro['direct']:.4f}  v9={macro['v9']:.4f}  "
              f"v10={macro['v10_blend']:.4f}  v12={macro['v12_blend']:.4f}")
        print(f"  bootstrap v12-v10: Δ={boot['mean_delta_pp']:+.2f} pp  "
              f"CI [{boot['ci95_lo_pp']:+.2f}, {boot['ci95_hi_pp']:+.2f}]  "
              f"P(Δ>0)={boot['p_delta_positive']:.3f}")
        print()

    with open(OUT_PATH, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
