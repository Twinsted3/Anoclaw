"""AnomalyClaw v9 — Unified Task-Aware Agent runner.

Extends v8 refutation with task-aware output (MCQ + open-ended). The LLM
infers the mode inside turn 1 based on the task preamble built from
(question, options). Tool set is unchanged (agent_tools_v7).

Use run_v9_item(..., question=None, options=None) to cover all 4 modes.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import agent_prompt_v9 as _p9  # noqa: E402
import agent_tools_v7 as _t7  # noqa: E402
from infer import (  # noqa: E402
    call_llm, extract_json, get_client, get_model_name,
    img_msg, load_and_encode, text_msg,
)


@dataclass
class V9Result:
    item_id: str
    mode: str
    score: float                    # anomaly_score
    mcq_answer: str | None
    free_text: str | None
    option_scores: dict | None
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


def _build_initial_messages(query_path, ref_paths, question, options,
                            max_turns, fewshot_context=None):
    user_parts = []
    if ref_paths:
        user_parts.append(text_msg("NORMAL REFERENCE IMAGES:"))
        for rp in ref_paths[:4]:
            user_parts.append(img_msg(load_and_encode(rp)))
    user_parts.append(text_msg("QUERY IMAGE:"))
    user_parts.append(img_msg(load_and_encode(query_path)))
    preamble = _p9.format_task_preamble(question, options)
    preamble_text = preamble["text"]
    if fewshot_context:
        # Compact injection — no rationale, no similarity — to avoid
        # confusing the strict JSON schema of the refutation prompt.
        n_anom = sum(1 for f in fewshot_context if f.get("label") == 1)
        n_norm = len(fewshot_context) - n_anom
        preamble_text = (
            preamble_text
            + f"\n\nDomain prior (from {len(fewshot_context)} recent"
              f" labelled neighbours of this query): {n_anom} were"
              f" ANOMALOUS, {n_norm} were NORMAL. Use this as a weak prior"
              f" on what an anomaly in this domain typically looks like."
        )
    user_parts.append(text_msg(preamble_text))
    user_parts.append(text_msg(
        f"Turn 1/{max_turns}. Produce the turn-1 JSON for this mode. "
        f"mode='{preamble['mode_hint']}' (you may override if confident)."
    ))
    return [
        {"role": "system", "content": _p9.SYSTEM_PROMPT},
        {"role": "user", "content": user_parts},
    ], preamble["mode_hint"]


def _parse_v9_action(text, mode_hint):
    parsed = extract_json(text)
    if not isinstance(parsed, dict):
        return None
    action = parsed.get("action")
    if action not in ("call_tool", "final"):
        return None
    if action == "final":
        # Required: anomaly_score or mcq_answer or free_text depending on mode
        mode = parsed.get("mode") or mode_hint
        # Always require anomaly_score (fallback sources)
        score = parsed.get("anomaly_score")
        if score is None:
            score = parsed.get("score")  # backward-compat
        if score is None:
            score = (parsed.get("updated_score")
                     or parsed.get("initial_score"))
        if score is None:
            score = 0.5
        try:
            parsed["anomaly_score"] = float(score)
        except (TypeError, ValueError):
            parsed["anomaly_score"] = 0.5

        if mode in ("mcq_binary", "mcq_choice"):
            letter = parsed.get("mcq_answer")
            if letter not in ("A", "B", "C", "D"):
                # Fallback 1: argmax of option_scores
                if mode == "mcq_choice":
                    opt = parsed.get("option_scores") or {}
                    if opt:
                        try:
                            letter = max(opt.items(),
                                         key=lambda kv: float(kv[1]))[0]
                        except Exception:
                            letter = None
                # Fallback 2: regex parse of rationale / thought / free_text
                if letter not in ("A", "B", "C", "D"):
                    import re
                    blob = " ".join(str(parsed.get(k, "")) for k in
                                    ("rationale", "thought", "free_text"))
                    m = re.search(r"\boption\s*([A-D])\b", blob,
                                  re.IGNORECASE)
                    if not m:
                        m = re.search(r"\b(?:answer|choice)\s*(?:is|=)?\s*"
                                      r"([A-D])\b", blob, re.IGNORECASE)
                    if not m:
                        m = re.search(r"\b([A-D])\)", blob)
                    if m:
                        letter = m.group(1).upper()
                parsed["mcq_answer"] = (letter
                                        if letter in ("A", "B", "C", "D")
                                        else None)
            else:
                parsed["mcq_answer"] = letter
        parsed["mode"] = mode
    else:
        if not parsed.get("tool"):
            return None
    return parsed


def _call_with_retry(client, model, messages, mode_hint, max_tokens=700,
                     retries=1):
    cur = list(messages)
    for _ in range(1 + retries):
        try:
            text, _, _ = call_llm(client, model, cur,
                                  max_tokens=max_tokens, temperature=0.0)
        except Exception:
            return None
        parsed = _parse_v9_action(text, mode_hint)
        if parsed is not None:
            return parsed
        cur = cur + [{
            "role": "user",
            "content": ("Your last response was not valid JSON. Return ONLY "
                        "a JSON object matching the schema for this mode.")
        }]
    return None


def _obs_to_text(obs):
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
    keep_keys = {"action", "tool", "thought", "mode",
                 "anomaly_score", "mcq_answer", "free_text",
                 "visual_evidence", "option_scores",
                 "initial_score", "candidate_features", "refutation_target",
                 "refutation_verdict", "feature_status_update",
                 "remaining_candidate_features", "updated_score",
                 "confidence"}
    out = {k: v for k, v in action.items() if k in keep_keys and v is not None}
    if "args" in action:
        out["args"] = str(action["args"])[:300]
    return out


def run_v9_item(client, model, item, split, max_turns,
                question=None, options=None, fewshot_context=None):
    item_id = item["item_id"]
    query_path = item["query_path"]
    ref_paths = item.get("ref_paths", []) or []
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

    messages, mode_hint = _build_initial_messages(
        query_path, ref_paths, question, options, max_turns,
        fewshot_context=fewshot_context)
    history = []
    tools_used = []
    initial_score = None
    candidate_features = None
    remaining_features = None
    updated_score = None
    refutation_verdicts: list = []
    final_mode = mode_hint
    final_mcq = None
    final_free = None
    final_opt_scores = None

    for turn in range(1, max_turns + 1):
        action = _call_with_retry(client, model, messages, mode_hint)
        if action is None:
            return V9Result(
                item_id=item_id, mode=mode_hint, score=0.5,
                mcq_answer=None, free_text=None, option_scores=None,
                rationale="json parse failed",
                n_turns=turn, tools_used=tools_used, history=history,
                initial_score=initial_score, candidate_features=candidate_features,
                remaining_features=remaining_features,
                refutation_verdicts=refutation_verdicts,
                updated_score=updated_score,
                confidence=0, error="malformed JSON after retries",
            )

        if turn == 1:
            rt = action.get("refutation_trace") or {}
            initial_score = (action.get("initial_score")
                             or rt.get("initial_score"))
            candidate_features = (action.get("candidate_features")
                                  or rt.get("candidate_features"))
            remaining_features = candidate_features

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
            score = float(action.get("anomaly_score", 0.5))
            score = max(0.0, min(1.0, score))
            final_mode = action.get("mode") or mode_hint
            final_mcq = action.get("mcq_answer")
            final_free = action.get("free_text")
            final_opt_scores = action.get("option_scores")
            return V9Result(
                item_id=item_id, mode=final_mode, score=score,
                mcq_answer=final_mcq, free_text=final_free,
                option_scores=final_opt_scores,
                rationale=str(action.get("rationale", ""))[:500],
                n_turns=turn, tools_used=tools_used,
                history=history + [{"turn": turn, **_summarise_action(action)}],
                initial_score=initial_score,
                candidate_features=candidate_features,
                remaining_features=remaining_features,
                refutation_verdicts=refutation_verdicts,
                updated_score=updated_score,
                confidence=int(action.get("confidence", 0) or 0),
            )

        if turn == max_turns:
            messages.append({"role": "assistant",
                             "content": json.dumps(_summarise_action(action))})
            messages.append({"role": "user",
                             "content": _p9.forced_final_prompt(max_turns)})
            forced = _call_with_retry(client, model, messages, mode_hint)
            if forced and forced.get("action") == "final":
                score = float(forced.get("anomaly_score", 0.5))
                score = max(0.0, min(1.0, score))
                return V9Result(
                    item_id=item_id,
                    mode=forced.get("mode") or mode_hint,
                    score=score,
                    mcq_answer=forced.get("mcq_answer"),
                    free_text=forced.get("free_text"),
                    option_scores=forced.get("option_scores"),
                    rationale=str(forced.get("rationale", ""))[:500],
                    n_turns=max_turns, tools_used=tools_used,
                    history=history + [
                        {"turn": turn, **_summarise_action(action)},
                        {"turn": turn, **_summarise_action(forced)},
                    ],
                    initial_score=initial_score,
                    candidate_features=candidate_features,
                    remaining_features=remaining_features,
                    refutation_verdicts=refutation_verdicts,
                    updated_score=updated_score,
                    confidence=int(forced.get("confidence", 0) or 0),
                )
            return V9Result(
                item_id=item_id, mode=mode_hint, score=0.5,
                mcq_answer=None, free_text=None, option_scores=None,
                rationale="forced-final failed",
                n_turns=max_turns, tools_used=tools_used, history=history,
                initial_score=initial_score,
                candidate_features=candidate_features,
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
            f"{_p9.budget_warning_prompt(remaining)}\n"
            f"Incorporate this evidence, update your fields, continue or "
            f"finalise."))
        messages.append({"role": "assistant",
                         "content": json.dumps(_summarise_action(action))})
        messages.append({"role": "user", "content": obs_parts})

    return V9Result(
        item_id=item_id, mode=mode_hint, score=0.5,
        mcq_answer=None, free_text=None, option_scores=None,
        rationale="loop exhausted",
        n_turns=max_turns, tools_used=tools_used, history=history,
        initial_score=initial_score, candidate_features=candidate_features,
        remaining_features=remaining_features,
        refutation_verdicts=refutation_verdicts,
        updated_score=updated_score,
        confidence=0, error="loop exhausted without final",
    )


def main():
    """CLI for regression-testing v9 on CrossDomainVAD manifests (no MCQ)."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--split", choices=["calibration", "dev", "test"],
                    required=True)
    ap.add_argument("--backend", choices=["gpt", "seedvl", "qwen3"],
                    required=True)
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

    client = get_client(args.backend)
    model = get_model_name(args.backend)

    def _run(x):
        try:
            r = run_v9_item(client, model, x, args.split, args.max_turns)
            return {
                "item_id": r.item_id, "domain_code": x.get("domain_code"),
                "label_gt": x.get("label"), "mode": r.mode,
                "anomaly_score": r.score,
                "rationale": r.rationale, "n_turns": r.n_turns,
                "tools_used": r.tools_used, "confidence": r.confidence,
                "initial_score": r.initial_score,
                "candidate_features": r.candidate_features,
                "remaining_features": r.remaining_features,
                "refutation_verdicts": r.refutation_verdicts,
                "updated_score": r.updated_score,
                "history": r.history,
                "error": r.error,
            }
        except Exception as e:
            return {"item_id": x["item_id"], "anomaly_score": 0.5,
                    "error": f"{type(e).__name__}: {e}"}

    results = list(prev)
    t0 = time.time()
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=args.max_workers) as ex:
        futs = [ex.submit(_run, x) for x in items]
        for i, f in enumerate(as_completed(futs)):
            results.append(f.result())
            if (i + 1) % 25 == 0:
                with open(args.output, "w") as ff:
                    json.dump(results, ff)
                print(f"[{i+1}/{len(items)}] t={time.time()-t0:.1f}s",
                      flush=True)

    with open(args.output, "w") as f:
        json.dump(results, f)
    print(f"Wrote {len(results)} → {args.output}")


if __name__ == "__main__":
    main()
