"""AnomalyClaw v8 — Dialectic (Competing Hypothesis Testing) agent.

Wires agent_prompt_v8.SYSTEM_PROMPT into the v6 ReAct loop, with
agent_tools_v7 (interpretation wrappers preserved).

Captures the refutation schema (candidate_features, refutation_verdict,
remaining_candidate_features, updated_score) plus full turn history
into the output for downstream audit.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import agent_prompt_v8 as _p8  # noqa: E402
import agent_tools_v7 as _t7  # noqa: E402
from infer import (  # noqa: E402
    call_llm, extract_json, get_client, get_model_name,
    img_msg, load_and_encode, text_msg,
)


@dataclass
class V8Result:
    item_id: str
    score: float
    rationale: str
    n_turns: int
    tools_used: list
    history: list
    initial_score: float | None
    candidate_features: list | None
    remaining_features: list | None
    refutation_verdicts: list
    updated_score: float | None
    confidence: int
    error: str | None = None


def _build_initial_messages(query_path, ref_paths, max_turns):
    user_parts = [
        text_msg("NORMAL REFERENCE IMAGES:"),
    ]
    for rp in ref_paths[:4]:
        user_parts.append(img_msg(load_and_encode(rp)))
    user_parts.append(text_msg("QUERY IMAGE:"))
    user_parts.append(img_msg(load_and_encode(query_path)))
    user_parts.append(text_msg(
        f"Turn 1/{max_turns}. Output initial_score, candidate_features "
        f"(up to 3), refutation_target, then action."
    ))
    return [
        {"role": "system", "content": _p8.SYSTEM_PROMPT},
        {"role": "user", "content": user_parts},
    ]


def _parse_v8_action(text):
    parsed = extract_json(text)
    if not isinstance(parsed, dict):
        return None
    action = parsed.get("action")
    if action not in ("call_tool", "final"):
        return None
    if action == "final":
        score = parsed.get("score")
        if score is None:
            score = (parsed.get("updated_score")
                     or parsed.get("initial_score"))
        if score is None:
            return None
        try:
            parsed["score"] = float(score)
        except (TypeError, ValueError):
            return None
    else:
        if not parsed.get("tool"):
            return None
    return parsed


def _call_with_retry(client, model, messages, max_tokens=700, retries=1):
    cur = list(messages)
    for _ in range(1 + retries):
        try:
            text, _, _ = call_llm(client, model, cur,
                                  max_tokens=max_tokens, temperature=0.0)
        except Exception:
            return None
        parsed = _parse_v8_action(text)
        if parsed is not None:
            return parsed
        cur = cur + [{
            "role": "user",
            "content": "Your last response was not valid JSON matching the "
                       "schema. Return ONLY a JSON object with the required "
                       "fields for this turn type."
        }]
    return None


def _obs_to_text(obs):
    """Compact text summary; put interpretation first so disconfirm is visible."""
    small = {}
    if "interpretation" in obs:
        small["interpretation"] = obs["interpretation"]
    for k, v in obs.items():
        if k == "interpretation":
            continue
        if k.endswith("_b64"):
            small[k] = f"<{len(v)}-char image>"
        elif k == "tiles":
            small[k] = f"<{len(v)} tiles attached>"
        elif k == "top_patches":
            small[k] = f"<{len(v)} patches>"
        else:
            small[k] = v
    return json.dumps(small, default=str)[:1800]


def _summarise_action(action):
    """For message history — drop bulky args/stories."""
    keep_keys = {"action", "tool", "thought", "initial_score",
                 "candidate_features", "refutation_target",
                 "refutation_verdict", "feature_status_update",
                 "remaining_candidate_features", "updated_score",
                 "evidence_strength", "confidence", "score"}
    out = {k: v for k, v in action.items() if k in keep_keys and v is not None}
    if "args" in action:
        out["args"] = str(action["args"])[:300]
    return out


def run_v8_item(client, model, item, split, max_turns):
    item_id = item["item_id"]
    query_path = item["query_path"]
    ref_paths = item["ref_paths"]
    domain_code = item.get("domain_code")

    ctx = {
        "query_path": query_path,
        "ref_paths": ref_paths,
        "item_id": item_id,
        "split": split,
        "vlm_client": client,
        "vlm_model": model,
        "llm_client": client,
        "llm_model": model,
        "_manifest_domain": domain_code,
    }

    messages = _build_initial_messages(query_path, ref_paths, max_turns)
    history = []
    tools_used = []
    initial_score = None
    candidate_features = None
    remaining_features = None
    updated_score = None
    refutation_verdicts: list = []

    for turn in range(1, max_turns + 1):
        action = _call_with_retry(client, model, messages)
        if action is None:
            return V8Result(
                item_id=item_id, score=0.5, rationale="json parse failed",
                n_turns=turn, tools_used=tools_used, history=history,
                initial_score=initial_score, candidate_features=candidate_features,
                remaining_features=remaining_features,
                refutation_verdicts=refutation_verdicts,
                updated_score=updated_score,
                confidence=0, error="malformed JSON after retries",
            )

        # Capture turn-1 fields
        if turn == 1:
            initial_score = action.get("initial_score")
            candidate_features = action.get("candidate_features")
            remaining_features = candidate_features

        # Capture refutation state
        if action.get("refutation_verdict"):
            refutation_verdicts.append({
                "turn": turn,
                "verdict": action.get("refutation_verdict"),
                "status": action.get("feature_status_update"),
            })
        if action.get("remaining_candidate_features") is not None:
            remaining_features = action.get("remaining_candidate_features")
        if action.get("updated_score") is not None:
            try:
                updated_score = float(action["updated_score"])
            except (TypeError, ValueError):
                pass

        if action["action"] == "final":
            score = max(0.0, min(1.0, float(action["score"])))
            return V8Result(
                item_id=item_id, score=score,
                rationale=str(action.get("rationale", ""))[:500],
                n_turns=turn, tools_used=tools_used,
                history=history + [{"turn": turn, **_summarise_action(action)}],
                initial_score=initial_score, candidate_features=candidate_features,
                remaining_features=remaining_features,
                refutation_verdicts=refutation_verdicts,
                updated_score=updated_score,
                confidence=int(action.get("confidence", 0) or 0),
            )

        # Budget exhausted: force final
        if turn == max_turns:
            messages.append({"role": "assistant",
                             "content": json.dumps(_summarise_action(action))})
            messages.append({"role": "user",
                             "content": _p8.forced_final_prompt(max_turns)})
            forced = _call_with_retry(client, model, messages)
            if forced and forced.get("action") == "final":
                score = max(0.0, min(1.0, float(forced["score"])))
                return V8Result(
                    item_id=item_id, score=score,
                    rationale=str(forced.get("rationale", ""))[:500],
                    n_turns=max_turns, tools_used=tools_used,
                    history=history + [
                        {"turn": turn, **_summarise_action(action)},
                        {"turn": turn, **_summarise_action(forced)},
                    ],
                    initial_score=initial_score, candidate_features=candidate_features,
                    remaining_features=remaining_features,
                    refutation_verdicts=refutation_verdicts,
                    updated_score=updated_score,
                    confidence=int(forced.get("confidence", 0) or 0),
                )
            return V8Result(
                item_id=item_id, score=0.5, rationale="forced-final failed",
                n_turns=max_turns, tools_used=tools_used, history=history,
                initial_score=initial_score, candidate_features=candidate_features,
                remaining_features=remaining_features,
                refutation_verdicts=refutation_verdicts,
                updated_score=updated_score,
                confidence=0, error="forced-final produced non-final",
            )

        # Execute tool
        tool_name = action["tool"]
        tool_args = action.get("args") or {}
        observation = _t7.dispatch_tool(tool_name, tool_args, ctx)
        tools_used.append(tool_name)
        history.append({"turn": turn, **_summarise_action(action),
                        "obs_keys": list(observation.keys()),
                        "obs_error": observation.get("error")})

        if tool_name == "tool_expert_score":
            ctx["_expert_patches"] = observation.get("top_patches", [])

        obs_parts = []
        obs_parts.append(text_msg(
            f"OBSERVATION from {tool_name}: {_obs_to_text(observation)}"))
        for img_key in ("crop_b64", "diff_mask_b64", "aligned_diff_b64",
                        "composite_b64"):
            if observation.get(img_key):
                obs_parts.append(img_msg(observation[img_key]))
        if observation.get("tiles"):
            for t in observation["tiles"][:9]:
                obs_parts.append(img_msg(t["crop_b64"]))
        remaining = max_turns - turn
        obs_parts.append(text_msg(
            f"Turn {turn + 1}/{max_turns}. "
            f"{_p8.budget_warning_prompt(remaining)}\n"
            f"Refute the current refutation_target against this evidence. "
            f"Update remaining_candidate_features and updated_score. "
            f"Continue or finalise."))
        messages.append({"role": "assistant",
                         "content": json.dumps(_summarise_action(action))})
        messages.append({"role": "user", "content": obs_parts})

    return V8Result(
        item_id=item_id, score=0.5, rationale="loop exhausted",
        n_turns=max_turns, tools_used=tools_used, history=history,
        initial_score=initial_score, candidate_features=candidate_features,
        remaining_features=remaining_features,
        refutation_verdicts=refutation_verdicts,
        updated_score=updated_score,
        confidence=0, error="loop exhausted without final",
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--split", choices=["calibration", "dev", "test"], required=True)
    ap.add_argument("--backend", choices=["gpt", "seedvl", "qwen3"], required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--max_turns", type=int, default=5)
    ap.add_argument("--max_workers", type=int, default=9)
    ap.add_argument("--max_items", type=int, default=0)
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    items = json.load(open(args.manifest))
    items = [x for x in items if x.get("split") == args.split]
    if args.max_items:
        items = items[:args.max_items]

    prev = []
    done_ids = set()
    if args.resume and os.path.exists(args.output):
        prev = json.load(open(args.output))
        done_ids = {r["item_id"] for r in prev if r.get("error") is None}
        items = [x for x in items if x["item_id"] not in done_ids]
        print(f"[resume] {len(done_ids)} done; {len(items)} remaining")

    client = get_client(args.backend)
    model = get_model_name(args.backend)

    results = list(prev)
    t0 = time.time()

    def _run(x):
        try:
            r = run_v8_item(client, model, x, args.split, args.max_turns)
            return {
                "item_id": r.item_id, "domain_code": x.get("domain_code"),
                "label_gt": x.get("label"), "anomaly_score": r.score,
                "rationale": r.rationale, "n_turns": r.n_turns,
                "tools_used": r.tools_used, "confidence": r.confidence,
                "initial_score": r.initial_score,
                "candidate_features": r.candidate_features,
                "remaining_features": r.remaining_features,
                "refutation_verdicts": r.refutation_verdicts,
                "updated_score": r.updated_score,
                "history": r.history,  # codex r1 feedback: expose full trace
                "error": r.error,
            }
        except Exception as e:
            return {"item_id": x["item_id"], "domain_code": x.get("domain_code"),
                    "label_gt": x.get("label"), "anomaly_score": 0.5,
                    "n_turns": 0, "tools_used": [], "confidence": 0,
                    "error": f"{type(e).__name__}: {e}"}

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=args.max_workers) as ex:
        futs = [ex.submit(_run, x) for x in items]
        for i, f in enumerate(as_completed(futs)):
            results.append(f.result())
            if (i+1) % 25 == 0:
                with open(args.output, "w") as ff:
                    json.dump(results, ff)
                print(f"[{i+1}/{len(items)}] t={time.time()-t0:.1f}s", flush=True)

    with open(args.output, "w") as f:
        json.dump(results, f)
    print(f"Wrote {len(results)} → {args.output}")


if __name__ == "__main__":
    main()
