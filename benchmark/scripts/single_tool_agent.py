"""Single-tool agent: Direct-style ReAct loop with exactly ONE tool exposed.

Builds on top of agent_v6.ReActAgent but:
  - Swaps SYSTEM_PROMPT for a single-tool variant describing only `--tool`
  - Restricts dispatch_tool to reject any tool != --tool
  - Outputs {item_id, anomaly_score, used_tool, n_turns, tools_used,
             confidence, rationale, error} per item

Usage:
  python benchmark/scripts/single_tool_agent.py \
    --tool tool_expert_score --split dev \
    --manifest benchmark/manifests/full_manifest.json \
    --output benchmark/results/tool_audit/tool_expert_score.json \
    --max_turns 3 --max_workers 9
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from infer import get_client, get_model_name  # noqa: E402
import agent_v6 as v6  # noqa: E402
import agent_tools_v7 as tv7  # noqa: E402
import agent_prompt_v7 as pv7  # noqa: E402


SINGLE_TOOL_SYSTEM_PROMPT = """You are a visual anomaly detection agent.

INPUT PER IMAGE: one query image, four normal reference images, a turn budget.
TASK: decide if the query is normal or anomalous and output a score in [0,1]
where 1 means certainly anomalous.

You have NO domain information and can observe only what's in the images.
On each turn you have exactly ONE tool available.

{output_guide}

THE ONE TOOL AVAILABLE TO YOU:
{tool_desc}

PROTOCOL: Return ONLY a JSON object:
{{
  "thought":  "<one or two sentences>",
  "action":   "call_tool" | "final",
  "tool":     "<tool_name>" | null,
  "args":     {{ ... }} | null,
  "confidence": <integer 0..100>,
  "score":    <float 0..1> | null,
  "rationale": "<one or two sentences>" | null
}}

GUIDELINES:
- Call the tool ONLY if you think it will help on THIS image. Otherwise output
  `final` at turn 1 without calling it.
- If the tool returns an `unreliable_alignment: true` or `not_applicable: true`
  flag, IGNORE its output and reason from the raw images.
- Read the disconfirm clause of the tool output before updating your score.
- Return valid JSON only.
"""


def _extract_tool_desc(tool_name: str) -> str:
    """Extract the docstring block for `tool_name` from agent_prompt_v7.TOOL_CATALOG."""
    catalog = pv7.TOOL_CATALOG
    lines = catalog.splitlines()
    out: list[str] = []
    capturing = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(tool_name):
            capturing = True
            out.append(line)
            continue
        if capturing:
            if line.startswith("    ") or not stripped:
                out.append(line)
                continue
            # next tool or section header → stop
            break
    if not out:
        return f"  {tool_name}(...)  (no description found in catalog)"
    return "\n".join(out).rstrip()


def make_restricted_dispatch(allowed_tool: str):
    """Return a dispatch_tool that routes only `allowed_tool`, else returns error."""
    original = tv7.dispatch_tool

    def _dispatch(name: str, args: dict, ctx: dict | None = None) -> dict:
        if name != allowed_tool:
            return {"error": (f"only {allowed_tool} is available in this single-tool "
                              f"run; you called {name}")}
        return original(name, args, ctx)

    return _dispatch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tool", required=True)
    ap.add_argument("--manifest", default="benchmark/manifests/full_manifest.json")
    ap.add_argument("--split", choices=["calibration", "dev", "test"], default="dev")
    ap.add_argument("--output", required=True)
    ap.add_argument("--backend", default="qwen3")
    ap.add_argument("--max_turns", type=int, default=3)
    ap.add_argument("--max_workers", type=int, default=9)
    ap.add_argument("--max_items", type=int, default=0)
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    if args.tool not in tv7.TOOL_REGISTRY:
        raise SystemExit(f"unknown tool {args.tool!r}; choices: "
                         f"{sorted(tv7.TOOL_REGISTRY)}")

    items = json.load(open(args.manifest))
    items = [x for x in items if x.get("split") == args.split]
    if args.max_items:
        items = items[:args.max_items]

    prev: list = []
    done_ids: set = set()
    if args.resume and os.path.exists(args.output):
        prev = json.load(open(args.output))
        done_ids = {r["item_id"] for r in prev if r.get("error") is None}
        items = [x for x in items if x["item_id"] not in done_ids]
        print(f"[resume] {len(done_ids)} done; {len(items)} remaining", flush=True)

    client = get_client(args.backend)
    model = get_model_name(args.backend)

    # Patch: single-tool prompt and restricted dispatch
    tool_desc = _extract_tool_desc(args.tool)
    sp = SINGLE_TOOL_SYSTEM_PROMPT.format(
        output_guide=pv7.TOOL_OUTPUT_GUIDE, tool_desc=tool_desc)

    v6.SYSTEM_PROMPT = sp
    v6.dispatch_tool = make_restricted_dispatch(args.tool)

    agent = v6.ReActAgent(vlm_client=client, vlm_model=model,
                          max_turns=args.max_turns)

    results: list = list(prev)
    t0 = time.time()

    def _run_one(x):
        try:
            r = agent.run(item_id=x["item_id"], query_path=x["query_path"],
                          ref_paths=x["ref_paths"], split=args.split,
                          domain_code=x.get("domain_code"))
            used = args.tool in (r.tools_used or [])
            return {
                "item_id": x["item_id"],
                "domain_code": x.get("domain_code"),
                "label_gt": x.get("label"),
                "anomaly_score": r.score,
                "used_tool": used,
                "n_turns": r.n_turns,
                "tools_used": r.tools_used,
                "confidence": r.confidence,
                "rationale": r.rationale,
                "error": r.error,
            }
        except Exception as e:
            return {"item_id": x["item_id"], "domain_code": x.get("domain_code"),
                    "label_gt": x.get("label"), "anomaly_score": 0.5,
                    "used_tool": False, "n_turns": 0, "tools_used": [],
                    "confidence": 0, "rationale": None,
                    "error": f"{type(e).__name__}: {e}"}

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=args.max_workers) as ex:
        futs = [ex.submit(_run_one, x) for x in items]
        for i, fut in enumerate(as_completed(futs)):
            results.append(fut.result())
            if (i + 1) % 40 == 0:
                with open(args.output, "w") as f:
                    json.dump(results, f)
                print(f"[{args.tool}] {i+1}/{len(items)} "
                      f"t={time.time()-t0:.1f}s", flush=True)

    with open(args.output, "w") as f:
        json.dump(results, f)
    used_n = sum(1 for r in results if r.get("used_tool"))
    err_n = sum(1 for r in results if r.get("error"))
    print(f"[{args.tool}] n={len(results)} used={used_n} err={err_n} "
          f"→ {args.output}")


if __name__ == "__main__":
    main()
