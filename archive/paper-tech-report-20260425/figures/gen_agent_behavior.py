"""Generate fig_agent_behavior.pdf — 4-panel empirical analysis of v9's
multi-turn / tool / refutation / candidate behaviour across 3 backbones
on CrossDomainVAD-12 test (extracted from v10 output files).

Produces a 2x2 figure:
  (a) n_turns distribution per backbone
  (b) tool invocation frequency (top 6 tools, per backbone)
  (c) refutation verdict distribution per backbone
  (d) candidate_features count per item

Also writes the aggregated stats to paper/figures/v2_agent_behavior_stats.json
for the in-paper table.
"""
from __future__ import annotations

import json
import collections
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 8.5,
    "axes.titlesize": 9.5,
    "axes.labelsize": 9,
    "legend.fontsize": 8,
    "pdf.fonttype": 42,
})

HERE = Path(__file__).parent
RESULTS = Path("/hdd1/jiangxi/AD-Agent/benchmark/results/v2")
BACKBONES = [("gpt", "GPT-5.4"), ("seedvl", "SeedVL"), ("qwen3", "Qwen3.5-VL-27B")]
COLOURS = {"gpt": "#4C72B0", "seedvl": "#DD8452", "qwen3": "#55A868"}


def parse_tools(t):
    if isinstance(t, list):
        return t
    if isinstance(t, str):
        try:
            return eval(t)
        except Exception:
            return [t] if t else []
    return []


def aggregate(items):
    """Return counters for one backbone's ad_ok items."""
    n = len(items)
    turns = collections.Counter(x.get("n_turns", 0) for x in items)
    tool_items = collections.Counter()  # tool -> #items invoking it
    for x in items:
        for t in set(parse_tools(x.get("tools_used"))):
            tool_items[t] += 1
    verdicts = collections.Counter()
    for x in items:
        for v in x.get("refutation_verdicts") or []:
            if isinstance(v, dict):
                verdicts[v.get("verdict") or "none"] += 1
    cands = collections.Counter()
    for x in items:
        cf = x.get("candidate_features") or []
        if isinstance(cf, list):
            cands[len(cf)] += 1
        elif isinstance(cf, str):
            try:
                cands[len(eval(cf))] += 1
            except Exception:
                cands[-1] += 1
    return {"n": n, "turns": turns, "tools": tool_items,
            "verdicts": verdicts, "cands": cands}


def load_backbone(bkey):
    d = json.load(open(RESULTS / f"v10_agent_{bkey}_test.json"))
    ok = [x for x in d if x.get("mode") == "anomaly_detection"
          and x.get("v9_score") is not None
          and x.get("direct_score") is not None
          and not x.get("error")]
    return aggregate(ok)


STATS = {bkey: load_backbone(bkey) for bkey, _ in BACKBONES}

# Dump JSON for in-paper table reference (rounded percentages)
out_json = {}
for bkey, blabel in BACKBONES:
    s = STATS[bkey]
    n = s["n"]
    out_json[bkey] = {
        "label": blabel,
        "ad_ok": n,
        "pct_n_turns": {str(k): round(v / n * 100, 1) for k, v in sorted(s["turns"].items())},
        "pct_tools_top5": {t: round(c / n * 100, 1) for t, c in s["tools"].most_common(5)},
        "n_verdicts": dict(s["verdicts"]),
        "pct_cand_count": {str(k): round(v / n * 100, 1) for k, v in sorted(s["cands"].items())},
        "mean_candidates": round(sum(k * v for k, v in s["cands"].items()) / n, 2),
    }
json.dump(out_json, open(HERE / "v2_agent_behavior_stats.json", "w"), indent=2)

# ─── figure ───
fig, axes = plt.subplots(2, 2, figsize=(11, 7))

# Panel (a) n_turns distribution — grouped bar per backbone
ax = axes[0, 0]
turn_keys = [1, 2, 3, 4, 5]
x = np.arange(len(turn_keys))
width = 0.27
for i, (bkey, blabel) in enumerate(BACKBONES):
    s = STATS[bkey]
    vals = [s["turns"].get(k, 0) / s["n"] * 100 for k in turn_keys]
    ax.bar(x + (i - 1) * width, vals, width, label=blabel,
           color=COLOURS[bkey], edgecolor="black", linewidth=0.3)
ax.set_xticks(x)
ax.set_xticklabels([f"{k} turn{'s' if k > 1 else ''}" for k in turn_keys])
ax.set_ylabel("% of items")
ax.set_title("(a) n_turns distribution")
ax.grid(axis="y", linewidth=0.3, alpha=0.5)
ax.legend(loc="upper right", frameon=False)
ax.set_ylim(0, 100)

# Panel (b) tool usage — top tools
ax = axes[0, 1]
all_tools = collections.Counter()
for bkey, _ in BACKBONES:
    for t, c in STATS[bkey]["tools"].items():
        all_tools[t] += c
top_tools = [t for t, _ in all_tools.most_common(6)]
# Rename for display
def short(t):
    return t.replace("tool_", "").replace("_", " ")
x = np.arange(len(top_tools))
width = 0.27
for i, (bkey, blabel) in enumerate(BACKBONES):
    s = STATS[bkey]
    vals = [s["tools"].get(t, 0) / s["n"] * 100 for t in top_tools]
    ax.bar(x + (i - 1) * width, vals, width, label=blabel,
           color=COLOURS[bkey], edgecolor="black", linewidth=0.3)
ax.set_xticks(x)
ax.set_xticklabels([short(t) for t in top_tools], rotation=20, ha="right")
ax.set_ylabel("% of items invoking tool")
ax.set_title("(b) Tool invocation frequency")
ax.grid(axis="y", linewidth=0.3, alpha=0.5)
ax.legend(loc="upper right", frameon=False)

# Panel (c) refutation verdict distribution
ax = axes[1, 0]
verdict_keys = ["found_in_ref", "not_found", "inconclusive"]
verdict_colours = {
    "found_in_ref": "#4E79A7",
    "not_found": "#E15759",
    "inconclusive": "#BAB0AC",
}
x = np.arange(len(BACKBONES))
bottoms = np.zeros(len(BACKBONES))
for vk in verdict_keys:
    vals = []
    for bkey, _ in BACKBONES:
        s = STATS[bkey]
        total_v = sum(s["verdicts"].values()) or 1
        vals.append(s["verdicts"].get(vk, 0) / total_v * 100)
    ax.bar(x, vals, bottom=bottoms, width=0.55,
           color=verdict_colours[vk], edgecolor="black", linewidth=0.3,
           label=vk)
    bottoms += vals
ax.set_xticks(x)
ax.set_xticklabels([b for _, b in BACKBONES])
ax.set_ylabel("% of verdicts")
ax.set_title("(c) Refutation verdict distribution")
ax.set_ylim(0, 102)
ax.legend(loc="center left", bbox_to_anchor=(1.0, 0.5), frameon=False)

# Panel (d) candidate_features count per item — grouped bars
ax = axes[1, 1]
cand_keys = [0, 1, 2, 3]
x = np.arange(len(cand_keys))
width = 0.27
for i, (bkey, blabel) in enumerate(BACKBONES):
    s = STATS[bkey]
    vals = [s["cands"].get(k, 0) / s["n"] * 100 for k in cand_keys]
    ax.bar(x + (i - 1) * width, vals, width, label=blabel,
           color=COLOURS[bkey], edgecolor="black", linewidth=0.3)
ax.set_xticks(x)
ax.set_xticklabels([f"{k}" for k in cand_keys])
ax.set_xlabel("# candidate_features")
ax.set_ylabel("% of items")
ax.set_title("(d) candidate_features count per item")
ax.grid(axis="y", linewidth=0.3, alpha=0.5)
ax.legend(loc="upper right", frameon=False)

plt.tight_layout()
out = HERE / "fig_agent_behavior.pdf"
plt.savefig(out, bbox_inches="tight")
print(f"Wrote {out}")
print(f"Wrote {HERE / 'v2_agent_behavior_stats.json'}")
