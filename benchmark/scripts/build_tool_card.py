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


def _macro_auroc_bootstrap_sample(items, rng):
    """One paired-bootstrap macro-AUROC sample: resample items within domain,
    recompute per-domain AUROC, average. Returns np.nan if any domain is
    unlabeled-constant after resampling."""
    by_d: dict[str, list] = {}
    for x in items:
        by_d.setdefault(x.get("domain_code"), []).append(x)
    aurocs = []
    for d, arr in by_d.items():
        if len(arr) < 3:
            continue
        idx = rng.integers(0, len(arr), len(arr))
        y = [arr[i]["label_gt"] for i in idx]
        if len(set(y)) < 2:
            continue
        s = [arr[i]["anomaly_score"] for i in idx]
        try:
            aurocs.append(roc_auc_score(y, s))
        except Exception:
            continue
    return float(np.mean(aurocs)) if aurocs else float("nan")


def slice_delta(pairs: list[tuple[dict, dict]], slice_fn, slice_name: str):
    """Return {'slice', 'n', 'auroc_tool', 'auroc_direct', 'delta',
    'delta_ci', 'metric'}. The same metric is used for point estimate
    AND bootstrap CI to avoid mislabelled claims (codex review 2026-04-18 C3).

    metric='macro' if the slice has >=2 domains each with n>=3, else 'pooled'.
    """
    subset = [(t, d) for t, d in pairs if slice_fn(t, d)]
    if len(subset) < 5:
        return None
    tools = [t for t, _ in subset]
    drs = [d for _, d in subset]
    y = [t["label_gt"] for t in tools]
    if len(set(y)) < 2:
        return None

    # Decide metric based on slice composition
    by_d: dict[str, int] = {}
    for t in tools:
        by_d[t.get("domain_code")] = by_d.get(t.get("domain_code"), 0) + 1
    viable_domains = [d for d, n in by_d.items() if n >= 3]
    use_macro = len(viable_domains) >= 2

    if use_macro:
        a_tool = macro_auroc_from_results(tools)
        a_direct = macro_auroc_from_results(drs)
        if np.isnan(a_tool) or np.isnan(a_direct):
            use_macro = False
    if not use_macro:
        a_tool = _safe_auroc(y, [t["anomaly_score"] for t in tools])
        a_direct = _safe_auroc(y, [d["anomaly_score"] for d in drs])
        if np.isnan(a_tool) or np.isnan(a_direct):
            return None

    # Bootstrap paired delta with the SAME metric used for the point estimate
    n = len(tools)
    deltas = []
    if use_macro:
        for _ in range(N_BOOT):
            a = _macro_auroc_bootstrap_sample(tools, RNG)
            b = _macro_auroc_bootstrap_sample(drs, RNG)
            if not (np.isnan(a) or np.isnan(b)):
                deltas.append(a - b)
    else:
        s_t_arr = np.asarray([t["anomaly_score"] for t in tools])
        s_d_arr = np.asarray([d["anomaly_score"] for d in drs])
        y_arr = np.asarray(y)
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
        "metric": "macro" if use_macro else "pooled",
    }


# Backwards-compatible alias
slice_macro_delta = slice_delta


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


SLICE_TYPE_DIAG = "diagnostic"        # useful for analysis, not injectable as niche
SLICE_TYPE_PRE = "actionable_pre_call"  # observable BEFORE any tool call
SLICE_TYPE_POST_EXPERT = "actionable_after_expert_score"  # only available once expert_score called


def build_slices(direct_results: list, split: str):
    """Return list of (name, predicate, slice_type) tuples.

    Slice type classification matters for actionability:
    - diagnostic slices (domain, tool_used, n_turns) characterize WHERE the
      tool helps in an oracle sense, but the agent can't use them as a trigger
      at inference time (the agent has no domain hint and tool_used/n_turns
      are post-treatment).
    - actionable_pre_call slices (direct_margin) are observable BEFORE the
      agent chooses any tool, so their niche can be injected as a trigger
      hint WHEN paired with an external Direct prior.
    - actionable_after_expert_score slices (subspacead_rank) become available
      AFTER the agent calls tool_expert_score, so they only trigger secondary
      tools in a multi-step plan.
    """
    rank_map = _load_expert_rank_map(split)
    domains = sorted({x.get("domain_code") for x in direct_results
                      if x.get("domain_code") is not None})
    slices: list[tuple[str, callable, str]] = []
    for d in domains:
        slices.append((f"domain={d}",
                       lambda t, _d, d=d: t.get("domain_code") == d,
                       SLICE_TYPE_DIAG))
    slices.append(("direct_margin<0.15 (uncertain)",
                   lambda t, d: abs(d.get("anomaly_score", 0.5) - 0.5) < 0.15,
                   SLICE_TYPE_PRE))
    slices.append(("direct_margin>=0.30 (confident)",
                   lambda t, d: abs(d.get("anomaly_score", 0.5) - 0.5) >= 0.30,
                   SLICE_TYPE_PRE))
    slices.append(("tool_used=True",
                   lambda t, d: bool(t.get("used_tool")),
                   SLICE_TYPE_DIAG))
    slices.append(("tool_used=False",
                   lambda t, d: not bool(t.get("used_tool")),
                   SLICE_TYPE_DIAG))
    if rank_map:
        slices.append(("subspacead_rank<=0.4 (weak expert)",
                       lambda t, d, rm=rank_map:
                       rm.get(t.get("item_id"), 0.5) <= 0.4,
                       SLICE_TYPE_POST_EXPERT))
        slices.append(("subspacead_rank in [0.4,0.8) (moderate expert)",
                       lambda t, d, rm=rank_map:
                       0.4 < rm.get(t.get("item_id"), 0.5) < 0.8,
                       SLICE_TYPE_POST_EXPERT))
        slices.append(("subspacead_rank>=0.8 (strong expert)",
                       lambda t, d, rm=rank_map:
                       rm.get(t.get("item_id"), 0.5) >= 0.8,
                       SLICE_TYPE_POST_EXPERT))
    slices.append(("n_turns=1 (no tool, tool-offered)",
                   lambda t, d: t.get("n_turns") == 1,
                   SLICE_TYPE_DIAG))
    slices.append(("n_turns>=2 (actually explored)",
                   lambda t, d: t.get("n_turns") is not None and t.get("n_turns") >= 2,
                   SLICE_TYPE_DIAG))
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
    for name, fn, stype in slices:
        res = slice_delta(pairs, fn, name)
        if res and res["n"] >= args.threshold_n:
            res["slice_type"] = stype
            findings.append(res)
    findings.sort(key=lambda x: -x["delta"])

    positive_niches = [f for f in findings
                       if f["delta"] > 0 and f["delta_ci"][0] > 0]
    # ACTIONABLE positive niches are the subset that can actually be used
    # as a trigger in the agent prompt. Diagnostic-only positives still go
    # into the KEEP consideration (they prove the tool has *some* value)
    # but the agent hint should only cite actionable ones.
    actionable_positive = [f for f in positive_niches
                           if f["slice_type"] != SLICE_TYPE_DIAG]
    anti = [f for f in findings
            if f["delta"] < 0 and f["delta_ci"][1] < 0]
    # KEEP requires at least one ACTIONABLE positive niche. A tool with only
    # diagnostic-domain niches has no defensible trigger and is dropped.
    verdict = "KEEP" if actionable_positive else "DROP"
    verdict_note = ""
    if positive_niches and not actionable_positive:
        verdict_note = (" (diagnostic-only positives exist but are not "
                        "prompt-actionable — see discussion)")

    # Multiple-testing note: ~N_slices ≈ 20; a 95% two-sided CI has ~2.5%
    # per-slice false-positive rate. Expected FPs per tool ≈ 0.5. Report
    # this in the card so consumers understand the statistic is uncorrected.
    n_slices_tested = len(findings)
    fdr_note = (f"Tested {n_slices_tested} slices at α=0.05 (two-sided); "
                f"expected false positive niches ≈ {0.025 * n_slices_tested:.2f}. "
                f"CI uncorrected for multiple testing — dev-derived hints "
                f"should be revalidated.")

    def _fmt_slice(f):
        mm = f.get("metric", "?")
        st = f.get("slice_type", "?")
        return (f"| {f['slice']} [{st}, {mm}] | {f['n']} | "
                f"{f['auroc_tool']:.3f} | {f['auroc_direct']:.3f} | "
                f"{f['delta']:+.3f} | [{f['delta_ci'][0]:+.3f}, "
                f"{f['delta_ci'][1]:+.3f}] |")

    lines: list[str] = [
        f"# Tool Card: {tool_name}",
        "",
        f"**Verdict:** {verdict}{verdict_note}  ",
        f"**Overall (dev n={overall['n_total']})**: tool={overall['full_tool_macro']:.4f}  "
        f"direct={overall['full_direct_macro']:.4f}  Δ={overall['full_delta']:+.4f}  ",
        f"**Calls**: {overall['n_called']}/{overall['n_total']} "
        f"({overall['call_rate']:.1f}%)  ",
        f"**Errors**: {overall['n_errors']}  ",
        f"**Multiple testing**: {fdr_note}  ",
        "",
        f"## Positive niches (n≥{args.threshold_n}, Δ>0, 95% CI lower > 0)",
        "",
    ]
    if not positive_niches:
        lines += ["_None found. Tool has no demonstrated niche on dev._", ""]
    else:
        lines.append("| slice [type, metric] | n | tool AUROC | direct AUROC | Δ | 95% CI |")
        lines.append("|---|---|---|---|---|---|")
        for f in positive_niches:
            lines.append(_fmt_slice(f))
        lines.append("")
        if actionable_positive:
            lines.append(f"**Actionable positives** ({len(actionable_positive)}): "
                         f"these can be used as a trigger in the agent prompt.")
        else:
            lines.append("**Actionable positives**: none — all positives are "
                         "diagnostic-only slices (e.g. domain labels the agent "
                         "cannot observe).")
        lines.append("")

    lines += ["## Anti-niches (Δ<0, 95% CI upper < 0)", ""]
    if not anti:
        lines += ["_None flagged._", ""]
    else:
        lines.append("| slice [type, metric] | n | tool AUROC | direct AUROC | Δ | 95% CI |")
        lines.append("|---|---|---|---|---|---|")
        for f in anti:
            lines.append(_fmt_slice(f))
        lines.append("")

    lines += ["## All slices (audit)", ""]
    lines.append("| slice [type, metric] | n | tool | direct | Δ | 95% CI |")
    lines.append("|---|---|---|---|---|---|")
    for f in findings:
        lines.append(_fmt_slice(f))
    lines.append("")

    lines += ["## Agent hint (injected into agent_v7 prompt if KEEP)", ""]
    if actionable_positive:
        best = actionable_positive[0]
        lines.append(f"**When to use {tool_name}:** especially helpful on "
                     f"`{best['slice']}` (Δ={best['delta']:+.3f} on n={best['n']}, "
                     f"metric={best.get('metric', '?')}).")
    elif positive_niches:
        lines.append(f"**{tool_name} has diagnostic-only positives** — DROP "
                     f"because no prompt-actionable trigger is available.")
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
