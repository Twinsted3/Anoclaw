"""Extract 20 cases per tool (10 wins, 10 losses) from v6.5 test results
for manual failure-mode inspection.

A "win" = tool call correlated with lower error than Direct on same item.
A "loss" = tool call correlated with higher error than Direct.
"""
from __future__ import annotations
import json
import os
from collections import defaultdict

RESULTS = "benchmark/results/v6_5_agent_qwen3_test.json"
DIRECT = "benchmark/results/v6_direct_qwen3_test.json"
OUT_DIR = "refine-logs/tool_diagnosis"

os.makedirs(OUT_DIR, exist_ok=True)

v65 = json.load(open(RESULTS))
direct = {x["item_id"]: x for x in json.load(open(DIRECT))}

by_tool: dict[str, list[dict]] = defaultdict(list)
for r in v65:
    tools = r.get("tools_used") or []
    label = r.get("label_gt")
    if label is None:
        continue
    agent_score = r.get("anomaly_score", 0.5)
    direct_score = direct.get(r["item_id"], {}).get("anomaly_score", 0.5)
    agent_err = abs(agent_score - label)
    direct_err = abs(direct_score - label)
    delta_err = agent_err - direct_err  # negative = agent better
    for t in set(tools):
        by_tool[t].append({
            "item_id": r["item_id"],
            "domain": r.get("domain_code"),
            "label": label,
            "agent_score": agent_score,
            "direct_score": direct_score,
            "delta_err": delta_err,
            "tools_used": tools,
            "rationale": (r.get("rationale") or "")[:240],
        })

for tool, cases in sorted(by_tool.items()):
    cases.sort(key=lambda x: x["delta_err"])
    wins = cases[:10]   # agent better
    losses = cases[-10:]  # agent worse
    out = [
        f"# Diagnosis: {tool}",
        "",
        f"Total calls: {len(cases)}",
        "",
        "## Failure mode (manual analysis — fill in)",
        "",
        "_TBD: wrong trigger / unclear output / VLM misreads / mixed_",
        "",
        "## Wins (agent better than Direct)",
        "",
    ]
    for h in wins:
        out.append(f"- `{h['item_id']}` [{h['domain']}] label={h['label']} agent={h['agent_score']:.2f} direct={h['direct_score']:.2f} Δerr={h['delta_err']:+.3f}")
        out.append(f"  > {h['rationale']}")
        out.append("")
    out += ["## Losses (agent worse than Direct)", ""]
    for m in losses:
        out.append(f"- `{m['item_id']}` [{m['domain']}] label={m['label']} agent={m['agent_score']:.2f} direct={m['direct_score']:.2f} Δerr={m['delta_err']:+.3f}")
        out.append(f"  > {m['rationale']}")
        out.append("")
    with open(f"{OUT_DIR}/{tool}.md", "w") as f:
        f.write("\n".join(out))
    print(f"wrote {OUT_DIR}/{tool}.md  (n_calls={len(cases)})")

print("\nTools with zero calls in v6.5:")
seen = set(by_tool.keys())
ALL = {
    "tool_expert_score", "tool_hotspot_cropper", "tool_zoom_bbox",
    "tool_patch_grid", "tool_image_diff", "tool_rotate_align",
    "tool_side_by_side", "tool_reference_profiler", "tool_reference_retriever",
    "tool_component_counter", "tool_segment_and_count", "tool_texture_fft",
    "tool_domain_knowledge",
}
for t in sorted(ALL - seen):
    print(f"  {t}")
