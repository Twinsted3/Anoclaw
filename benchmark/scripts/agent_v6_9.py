"""AnomalyClaw v6.9 — minimal pure agent (zoom_bbox only).

Strips the toolbox to the single tool that had a net positive AUROC
delta in v6.5 analysis: tool_zoom_bbox. Agent chooses whether to zoom or
answer directly; no expert, no reference profiler, no patch grid.

Thread-safe subclass (no monkey-patch on instance).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import agent_prompt_v6_9 as _p69
import agent_prompt_v6 as _p6
_p6.SYSTEM_PROMPT = _p69.SYSTEM_PROMPT
_p6.TOOL_CATALOG = _p69.TOOL_CATALOG
_p6.forced_final_prompt = _p69.forced_final_prompt
_p6.budget_warning_prompt = _p69.budget_warning_prompt

import agent_v6 as mod  # noqa: E402
from infer import (  # noqa: E402
    DOMAIN_CONTEXT, get_client, get_model_name, img_msg, load_and_encode,
    text_msg,
)

# Restrict TOOL_REGISTRY to just zoom_bbox so dispatch_tool rejects others
import agent_tools_v6 as _tools  # noqa: E402
_ALLOWED = {"tool_zoom_bbox"}
_orig_registry = _tools.TOOL_REGISTRY
_tools.TOOL_REGISTRY = {k: v for k, v in _orig_registry.items()
                        if k in _ALLOWED}
mod.TOOL_REGISTRY = _tools.TOOL_REGISTRY


class MinimalReActAgent(mod.ReActAgent):
    def _build_initial_messages(self, query_path, ref_paths,
                                domain_code=None, anchor_text=None):
        ctx_text = DOMAIN_CONTEXT.get(domain_code or "", "an image")
        user_parts = [
            text_msg(f"DOMAIN: {ctx_text}"),
            text_msg("NORMAL REFERENCE IMAGES:"),
        ]
        for rp in ref_paths[:4]:
            user_parts.append(img_msg(load_and_encode(rp)))
        user_parts.append(text_msg("QUERY IMAGE:"))
        user_parts.append(img_msg(load_and_encode(query_path)))
        user_parts.append(text_msg(f"Turn 1/{self.K}. Decide your next action."))
        return [
            {"role": "system", "content": _p69.SYSTEM_PROMPT},
            {"role": "user", "content": user_parts},
        ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--split", choices=["calibration", "dev", "test"],
                    required=True)
    ap.add_argument("--backend", choices=["qwen3", "seedvl", "gpt"],
                    required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--domains", nargs="*", default=None)
    ap.add_argument("--max_turns", type=int, default=5)
    ap.add_argument("--max_workers", type=int, default=8)
    ap.add_argument("--max_items", type=int, default=0)
    args = ap.parse_args()

    items = json.load(open(args.manifest))
    items = [x for x in items if x.get("split") == args.split]
    if args.domains:
        items = [x for x in items if x.get("domain_code") in args.domains]
    if args.max_items:
        items = items[:args.max_items]

    client = get_client(args.backend)
    model = get_model_name(args.backend)
    agent = MinimalReActAgent(vlm_client=client, vlm_model=model,
                              max_turns=args.max_turns)

    results = []
    t0 = time.time()

    def _run_one(x):
        try:
            r = agent.run(item_id=x["item_id"], query_path=x["query_path"],
                          ref_paths=x["ref_paths"], split=args.split,
                          domain_code=x.get("domain_code"))
            return {
                "item_id": x["item_id"], "domain_code": x.get("domain_code"),
                "label_gt": x.get("label"), "anomaly_score": r.score,
                "rationale": r.rationale, "n_turns": r.n_turns,
                "tools_used": r.tools_used, "confidence": r.confidence,
                "error": r.error,
            }
        except Exception as e:
            return {"item_id": x["item_id"], "domain_code": x.get("domain_code"),
                    "label_gt": x.get("label"), "anomaly_score": 0.5,
                    "n_turns": 0, "tools_used": [], "confidence": 0,
                    "error": f"{type(e).__name__}: {e}"}

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=args.max_workers) as ex:
        futures = [ex.submit(_run_one, x) for x in items]
        for i, fut in enumerate(as_completed(futures)):
            results.append(fut.result())
            if (i + 1) % 25 == 0:
                with open(args.output, "w") as f:
                    json.dump(results, f)
                print(f"[{i+1}/{len(items)}] {time.time()-t0:.1f}s  "
                      f"written={len(results)}", flush=True)

    with open(args.output, "w") as f:
        json.dump(results, f)
    print(f"Wrote {len(results)} results → {args.output}")


if __name__ == "__main__":
    main()
