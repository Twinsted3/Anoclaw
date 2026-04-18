"""Slice a single-tool audit result by multiple axes, find niches where the
tool beats Direct, emit a tool_card.md.

Slices:
  - domain (per-domain AUROC)
  - direct_margin bucket (uncertain / confident)
  - expert_score bucket (subspacead rank: low/mid/high)
  - tool_used True/False
  - n_turns bucket (1 / 2-3)

Niche = slice with n >= threshold AND Δ_AUROC > 0 AND bootstrap 95% CI
lower-bound > 0.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

N_BOOT = 1000
RNG = np.random.default_rng(42)


def _safe_auroc(y, s):
    y, s = np.asarray(y), np.asarray(s)
    if len(y) < 5 or len(set(y)) < 2:
        return np.nan
    return float(roc_auc_score(y, s))


def macro_auroc_from_results(items, min_n_per_domain: int = 3):
    by_d: dict[str, list] = {}
    for x in items:
        if x.get("label_gt") is None:
            continue
        by_d.setdefault(x.get("domain_code"), []).append(x)
    aurocs = []
    for d, arr in by_d.items():
        if len(arr) < min_n_per_domain:
            continue
        y = [i["label_gt"] for i in arr]
        s = [i["anomaly_score"] for i in arr]
        auc = _safe_auroc(y, s)
        if not np.isnan(auc):
            aurocs.append(auc)
    return float(np.mean(aurocs)) if aurocs else np.nan


def slice_macro_delta(pairs: list[tuple[dict, dict]], slice_fn, slice_name: str):
    """Return {'slice', 'n', 'auroc_tool', 'auroc_direct', 'delta',
    'delta_ci'} for the subset where slice_fn(tool_item, direct_item) is True.

    AUROC is macro over domains represented in the subset, falling back to
    pooled AUROC when too few per-domain samples.
    """
    subset = [(t, d) for t, d in pairs if slice_fn(t, d)]
    if len(subset) < 5:
        return None
    tools = [t for t, _ in subset]
    drs = [d for _, d in subset]

    # Check label diversity
    y = [t["label_gt"] for t in tools]
    if len(set(y)) < 2:
        return None

    # Try macro; fall back to pooled if not enough domains
    a_tool = macro_auroc_from_results(tools)
    a_direct = macro_auroc_from_results(drs)
    if np.isnan(a_tool) or np.isnan(a_direct):
        # pooled
        s_t = [t["anomaly_score"] for t in tools]
        s_d = [d["anomaly_score"] for d in drs]
        a_tool = _safe_auroc(y, s_t)
        a_direct = _safe_auroc(y, s_d)
        if np.isnan(a_tool) or np.isnan(a_direct):
            return None

    # Bootstrap paired delta (pooled AUROC basis)
    s_t_arr = np.asarray([t["anomaly_score"] for t in tools])
    s_d_arr = np.asarray([d["anomaly_score"] for d in drs])
    y_arr = np.asarray(y)
    n = len(y_arr)
    deltas = []
    for _ in range(N_BOOT):
        idx = RNG.integers(0, n, n)
        if len(set(y_arr[idx])) < 2:
            continue
        try:
            dt = (roc_auc_score(y_arr[idx], s_t_arr[idx])
                  - roc_auc_score(y_arr[idx], s_d_arr[idx]))
            deltas.append(dt)
        except Exception:
            continue
    if not deltas:
        return None
    return {
        "slice": slice_name,
        "n": n,
        "auroc_tool": float(a_tool),
        "auroc_direct": float(a_direct),
        "delta": float(a_tool - a_direct),
        "delta_ci": [float(np.percentile(deltas, 2.5)),
                     float(np.percentile(deltas, 97.5))],
    }


def _load_expert_rank_map(split: str):
    """Return item_id -> subspacead normalized_rank for direct_margin / expert
    slicing. Uses the same method as tool_expert_score."""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from agent_tools_v7 import _load_expert_scores
        recs, all_scores = _load_expert_scores("subspacead", split)
        if len(all_scores) == 0:
            return {}
        rank_map = {}
        for iid, rec in recs.items():
            if rec.get("anomaly_score") is None:
                continue
            s = float(rec["anomaly_score"])
            rank_map[iid] = float(np.searchsorted(all_scores, s) / len(all_scores))
        return rank_map
    except Exception:
        return {}


def build_slices(direct_results: list, split: str):
    rank_map = _load_expert_rank_map(split)
    domains = sorted({x.get("domain_code") for x in direct_results
                      if x.get("domain_code") is not None})
    slices: list[tuple[str, callable]] = []
    for d in domains:
        slices.append((f"domain={d}",
                       lambda t, _d, d=d: t.get("domain_code") == d))
    slices.append(("direct_margin<0.15 (uncertain)",
                   lambda t, d: abs(d.get("anomaly_score", 0.5) - 0.5) < 0.15))
    slices.append(("direct_margin>=0.30 (confident)",
                   lambda t, d: abs(d.get("anomaly_score", 0.5) - 0.5) >= 0.30))
    slices.append(("tool_used=True",
                   lambda t, d: bool(t.get("used_tool"))))
    slices.append(("tool_used=False",
                   lambda t, d: not bool(t.get("used_tool"))))
    if rank_map:
        slices.append(("subspacead_rank<=0.4 (weak expert)",
                       lambda t, d, rm=rank_map:
                       rm.get(t.get("item_id"), 0.5) <= 0.4))
        slices.append(("subspacead_rank in [0.4,0.8) (moderate expert)",
                       lambda t, d, rm=rank_map:
                       0.4 < rm.get(t.get("item_id"), 0.5) < 0.8))
        slices.append(("subspacead_rank>=0.8 (strong expert)",
                       lambda t, d, rm=rank_map:
                       rm.get(t.get("item_id"), 0.5) >= 0.8))
    slices.append(("n_turns=1 (no tool, tool-offered)",
                   lambda t, d: t.get("n_turns") == 1))
    slices.append(("n_turns>=2 (actually explored)",
                   lambda t, d: t.get("n_turns") is not None and t.get("n_turns") >= 2))
    return slices


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tool_file", required=True)
    ap.add_argument("--direct_file", required=True)
    ap.add_argument("--out_md", required=True)
    ap.add_argument("--split", default="dev")
    ap.add_argument("--threshold_n", type=int, default=10)
    args = ap.parse_args()

    tool_results = json.load(open(args.tool_file))
    direct_results = json.load(open(args.direct_file))
    tool_name = Path(args.tool_file).stem

    direct_by_id = {x["item_id"]: x for x in direct_results}
    pairs = [(t, direct_by_id[t["item_id"]]) for t in tool_results
             if t.get("item_id") in direct_by_id
             and t.get("label_gt") is not None]

    overall = {
        "tool": tool_name,
        "n_total": len(pairs),
        "n_called": sum(1 for t, _ in pairs if t.get("used_tool")),
        "n_errors": sum(1 for t, _ in pairs if t.get("error")),
        "full_tool_macro": macro_auroc_from_results([t for t, _ in pairs]),
        "full_direct_macro": macro_auroc_from_results([d for _, d in pairs]),
    }
    overall["full_delta"] = (overall["full_tool_macro"]
                             - overall["full_direct_macro"])
    overall["call_rate"] = (overall["n_called"] / overall["n_total"] * 100
                            if overall["n_total"] else 0)

    slices = build_slices(direct_results, args.split)
    findings = []
    for name, fn in slices:
        res = slice_macro_delta(pairs, fn, name)
        if res and res["n"] >= args.threshold_n:
            findings.append(res)
    findings.sort(key=lambda x: -x["delta"])

    positive_niches = [f for f in findings
                       if f["delta"] > 0 and f["delta_ci"][0] > 0]
    anti = [f for f in findings
            if f["delta"] < 0 and f["delta_ci"][1] < 0]
    verdict = "KEEP" if positive_niches else "DROP"

    lines: list[str] = [
        f"# Tool Card: {tool_name}",
        "",
        f"**Verdict:** {verdict}  ",
        f"**Overall (dev n={overall['n_total']})**: tool={overall['full_tool_macro']:.4f}  "
        f"direct={overall['full_direct_macro']:.4f}  Δ={overall['full_delta']:+.4f}  ",
        f"**Calls**: {overall['n_called']}/{overall['n_total']} "
        f"({overall['call_rate']:.1f}%)  ",
        f"**Errors**: {overall['n_errors']}  ",
        "",
        "## Positive niches (n≥{}, Δ>0, 95% CI lower > 0)".format(args.threshold_n),
        "",
    ]
    if not positive_niches:
        lines += ["_None found. Tool has no demonstrated niche on dev._", ""]
    else:
        lines.append("| slice | n | tool AUROC | direct AUROC | Δ | 95% CI |")
        lines.append("|---|---|---|---|---|---|")
        for f in positive_niches:
            lines.append(f"| {f['slice']} | {f['n']} | {f['auroc_tool']:.3f} | "
                         f"{f['auroc_direct']:.3f} | {f['delta']:+.3f} | "
                         f"[{f['delta_ci'][0]:+.3f}, {f['delta_ci'][1]:+.3f}] |")
        lines.append("")

    lines += ["## Anti-niches (Δ<0, 95% CI upper < 0)", ""]
    if not anti:
        lines += ["_None flagged._", ""]
    else:
        lines.append("| slice | n | tool AUROC | direct AUROC | Δ | 95% CI |")
        lines.append("|---|---|---|---|---|---|")
        for f in anti:
            lines.append(f"| {f['slice']} | {f['n']} | {f['auroc_tool']:.3f} | "
                         f"{f['auroc_direct']:.3f} | {f['delta']:+.3f} | "
                         f"[{f['delta_ci'][0]:+.3f}, {f['delta_ci'][1]:+.3f}] |")
        lines.append("")

    lines += ["## All slices (audit)", ""]
    lines.append("| slice | n | tool | direct | Δ | 95% CI |")
    lines.append("|---|---|---|---|---|---|")
    for f in findings:
        lines.append(f"| {f['slice']} | {f['n']} | {f['auroc_tool']:.3f} | "
                     f"{f['auroc_direct']:.3f} | {f['delta']:+.3f} | "
                     f"[{f['delta_ci'][0]:+.3f}, {f['delta_ci'][1]:+.3f}] |")
    lines.append("")

    lines += ["## Agent hint (injected into agent_v7 prompt if KEEP)", ""]
    if positive_niches:
        best = positive_niches[0]
        lines.append(f"**When to use {tool_name}:** especially helpful on "
                     f"`{best['slice']}` (Δ={best['delta']:+.3f} on n={best['n']}).")
    else:
        lines.append(f"**When to use {tool_name}:** no documented positive niche "
                     f"on dev. DROPPED.")
    if anti:
        worst = min(anti, key=lambda x: x["delta"])
        lines.append(f"**Avoid {tool_name} on:** `{worst['slice']}` "
                     f"(Δ={worst['delta']:+.3f} on n={worst['n']}).")
    lines.append("")

    Path(args.out_md).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out_md, "w") as f:
        f.write("\n".join(lines))
    print(f"wrote {args.out_md}  verdict={verdict}  "
          f"pos={len(positive_niches)} anti={len(anti)}")


if __name__ == "__main__":
    main()
