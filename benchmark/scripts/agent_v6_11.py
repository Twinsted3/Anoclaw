"""AnomalyClaw v6.11 — Direct-prompt first, ReAct escalation only on uncertainty.

Core insight from v6.8/v6.9 dev results: agents that rewrite the prompt
suffer a ~5-10pp "prompt structure penalty" on Qwen3.5 compared to
Direct's build_prompt_v0. Tools can't recover that gap.

v6.11 fixes this by using Direct's EXACT schema on turn 1:
  - Turn 1 calls build_prompt_v0 (same as Direct baseline).
  - Parse → image_label, confidence, evidence. Score via score_from_v0.
  - If confidence >= high_threshold (default 0.85) → return score, done.
  - Else → escalate to ReAct loop (turn 2..K) with v6 prompt, agent can
    call tools. Final free-form score.

This keeps Direct's calibration for confident items (80%+ of dataset)
and only "pays" for ReAct on uncertain ones. A pure agent, no ensemble.
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

import agent_prompt_v6 as _p6
# use the v6 base ReAct prompt for escalation
import agent_v6 as mod  # noqa: E402
from infer import (  # noqa: E402
    DOMAIN_CONTEXT, build_prompt_v0, call_llm, extract_json, get_client,
    get_model_name, img_msg, load_and_encode, score_from_v0, text_msg,
)


def _direct_turn1(client, model, item):
    """Exact Direct baseline call: returns (score, parsed, text)."""
    messages = [
        {"role": "system",
         "content": "You are a visual anomaly inspector. Return JSON only."},
        {"role": "user", "content": (
            [text_msg(build_prompt_v0(item.get("domain_code", "D?"),
                                      has_refs=True))] +
            [img_msg(load_and_encode(p)) for p in item.get("ref_paths", [])[:4]] +
            [text_msg("QUERY:"), img_msg(load_and_encode(item["query_path"]))]
        )},
    ]
    try:
        text, _, _ = call_llm(client, model, messages, max_tokens=500,
                              temperature=0.0)
        parsed = extract_json(text)
        score = float(score_from_v0(parsed))
        conf = float((parsed or {}).get("confidence", 0.0))
        return score, parsed, conf, None
    except Exception as e:
        return 0.5, None, 0.0, f"{type(e).__name__}: {e}"


def _escalate_react(client, model, item, direct_score, direct_parsed, K=5):
    """Continue with v6.5-style ReAct loop, informed by turn-1 Direct."""
    from agent_v6_5 import SYSTEM_PROMPT as V65_PROMPT  # reuse v6 prompt
    # Inject the turn-1 direct judgment into context so agent can build on it
    evidence = (direct_parsed or {}).get("evidence", "")[:200]
    anchor = (f"TURN 1 DIRECT JUDGMENT: score={direct_score:.3f}  "
              f"evidence={evidence!r}\n"
              f"Inspect the images more carefully; decide whether this "
              f"matches (then just confirm the score) or whether tools will "
              f"change your mind.")
    ctx = DOMAIN_CONTEXT.get(item.get("domain_code") or "", "an image")
    user_parts = [
        text_msg(f"DOMAIN: {ctx}"),
        text_msg(anchor),
        text_msg("NORMAL REFERENCE IMAGES:"),
    ]
    for rp in item.get("ref_paths", [])[:4]:
        user_parts.append(img_msg(load_and_encode(rp)))
    user_parts.append(text_msg("QUERY IMAGE:"))
    user_parts.append(img_msg(load_and_encode(item["query_path"])))
    user_parts.append(text_msg(f"Turn 2/{K+1}. Decide your next action."))
    messages = [
        {"role": "system", "content": V65_PROMPT},
        {"role": "user", "content": user_parts},
    ]
    # Manual loop (simplified v6 semantics)
    tools_used = []
    from agent_tools_v6 import dispatch_tool  # noqa: F401
    item_ctx = {
        "query_path": item["query_path"],
        "ref_paths": item["ref_paths"],
        "item_id": item["item_id"],
        "split": item.get("split"),
        "vlm_client": client, "vlm_model": model,
        "llm_client": client, "llm_model": model,
        "_manifest_domain": item.get("domain_code"),
    }
    for t in range(2, K + 1):
        try:
            text, _, _ = call_llm(client, model, messages, max_tokens=600,
                                  temperature=0.0)
            parsed = extract_json(text)
        except Exception as e:
            return direct_score, tools_used, t - 1, f"{type(e).__name__}: {e}"
        if not isinstance(parsed, dict):
            return direct_score, tools_used, t - 1, "malformed JSON"
        action = parsed.get("action")
        if action == "final":
            s = parsed.get("score")
            if s is not None:
                try:
                    return float(s), tools_used, t, None
                except (TypeError, ValueError):
                    return direct_score, tools_used, t, "bad score"
            return direct_score, tools_used, t, "no score"
        if action == "call_tool":
            tool_name = parsed.get("tool")
            if not tool_name:
                return direct_score, tools_used, t, "no tool"
            tool_args = parsed.get("args") or {}
            obs = dispatch_tool(tool_name, tool_args, item_ctx)
            tools_used.append(tool_name)
            messages.append({"role": "assistant",
                             "content": json.dumps(parsed)})
            messages.append({"role": "user",
                             "content": f"OBSERVATION: {json.dumps(obs, default=str)[:1500]}\n"
                                        f"Turn {t+1}/{K+1}. Decide."})
        else:
            return direct_score, tools_used, t, f"bad action {action}"
    return direct_score, tools_used, K, "loop exhausted"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--split", choices=["calibration", "dev", "test"],
                    required=True)
    ap.add_argument("--backend", choices=["qwen3", "seedvl", "gpt"],
                    required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--domains", nargs="*", default=None)
    ap.add_argument("--conf_threshold", type=float, default=0.85,
                    help="if direct confidence >= this, skip ReAct escalation")
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
    for it in items:
        it["split"] = args.split

    client = get_client(args.backend)
    model = get_model_name(args.backend)

    results = []
    t0 = time.time()

    def _run_one(x):
        d_score, d_parsed, d_conf, d_err = _direct_turn1(client, model, x)
        if d_err is not None:
            return {"item_id": x["item_id"], "domain_code": x.get("domain_code"),
                    "label_gt": x.get("label"), "anomaly_score": 0.5,
                    "escalated": False, "direct_score": None,
                    "direct_confidence": None,
                    "error": f"turn1_direct: {d_err}"}
        if d_conf >= args.conf_threshold:
            return {"item_id": x["item_id"], "domain_code": x.get("domain_code"),
                    "label_gt": x.get("label"), "anomaly_score": d_score,
                    "direct_score": d_score, "direct_confidence": d_conf,
                    "escalated": False, "tools_used": [], "n_turns": 1,
                    "error": None}
        # Escalate
        score, tools, nturns, err = _escalate_react(
            client, model, x, d_score, d_parsed, K=args.max_turns)
        return {"item_id": x["item_id"], "domain_code": x.get("domain_code"),
                "label_gt": x.get("label"), "anomaly_score": score,
                "direct_score": d_score, "direct_confidence": d_conf,
                "escalated": True, "tools_used": tools, "n_turns": nturns,
                "error": err}

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
    # Quick stats
    escalated = sum(1 for r in results if r.get("escalated"))
    print(f"Escalated: {escalated}/{len(results)} ({100*escalated/len(results):.1f}%)")


if __name__ == "__main__":
    main()
