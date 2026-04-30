"""MMAD evaluator — Implementation 1: logit-add ensemble.

Architecture per item:
  1) Direct logit  (mcq_logit_call → letter_logits_D)
  2) Agent v12_mmad trajectory (existing multi-turn ReAct + tools)
  3) Agent logit follow-up: append a "Answer with one letter" question
     to the agent's message history and extract first-token letter logits
     (letter_logits_A).
  4) Ensemble = softmax(D) + softmax(A); argmax → ensemble_logit_answer.

Both AD (binary A/B) and non-AD (4-option A/B/C/D) items use the same
logit pipeline — letter set is taken from `options.keys()`.

Output schema preserves the v10 fields (direct_answer, agent_answer,
ensemble_answer) for backward-comparison and adds:
  direct_logit_answer, direct_logits, direct_logit_scores
  agent_logit_answer, agent_logits, agent_logit_scores
  ensemble_logit_answer, ensemble_logit_scores
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from infer import get_client, get_model_name, img_msg, text_msg, call_llm  # noqa: E402
import agent_v12_mmad as v12_mmad_mod  # noqa: E402
from mcq_logit import mcq_logit_call, ensemble_logits, _argmax_softmax  # noqa: E402

from mmad_eval_v9 import (  # noqa: E402
    QTYPES_ALL,
    iter_mmad_items,
    stratified_sample_images,
)
from mmad_eval_v12_mmad import MMAD_DATASET_TO_DCODE  # noqa: E402


# Letter follow-up question used to extract logits from agent's history.
_AGENT_LOGIT_FOLLOWUP = (
    "Based on your reasoning above, output your final answer to the "
    "multiple-choice question. Reply with EXACTLY one letter (one of "
    "{letters}) and nothing else. Do not write JSON, do not write "
    "explanations — only the letter."
)


def _agent_logit_followup(client, model, history_messages, letters):
    """Append a final letter question to the agent's history and extract logit."""
    msgs = list(history_messages) + [{
        "role": "user",
        "content": _AGENT_LOGIT_FOLLOWUP.format(letters="/".join(letters))
    }]
    kwargs = dict(
        model=model, messages=msgs,
        max_tokens=2, temperature=0.0,
        logprobs=True, top_logprobs=20,
    )
    if "qwen3" in str(model).lower() or "Qwen3" in str(model):
        kwargs["extra_body"] = {
            "chat_template_kwargs": {"enable_thinking": False}}
    try:
        resp = client.chat.completions.create(**kwargs)
    except Exception as e:
        return {"answer": None, "logits": None, "scores": None,
                "error": f"call: {type(e).__name__}: {e}"}

    text = resp.choices[0].message.content or ""
    lp = resp.choices[0].logprobs
    if lp is None or not lp.content:
        first_letter = next((c for c in text.upper() if c in letters), None)
        return {"answer": first_letter, "logits": None, "scores": None,
                "error": "no_logprobs", "raw_text": text}

    first = lp.content[0]
    out = {L: None for L in letters}
    for entry in first.top_logprobs:
        tok = entry.token.strip().strip(".)").upper()
        if tok in out:
            cur = out[tok]
            if cur is None or entry.logprob > cur:
                out[tok] = entry.logprob
    if all(v is None for v in out.values()):
        first_letter = next((c for c in text.upper() if c in letters), None)
        return {"answer": first_letter, "logits": None, "scores": None,
                "error": "letters_not_in_topk",
                "raw_text": text}
    fallback = -30.0
    full = {L: out[L] if out[L] is not None else fallback for L in letters}
    ans, scores = _argmax_softmax(full, letters)
    return {"answer": ans, "logits": full, "scores": scores,
            "error": None, "raw_text": text}


def _run_agent_with_history(client, model, item, split, max_turns,
                             question, options, use_dataset_dcode):
    """Run v12_mmad trajectory and return both result + final message history."""
    if use_dataset_dcode:
        domain_code = MMAD_DATASET_TO_DCODE.get(
            item.get("dataset"), item["class_name"])
    else:
        domain_code = item["class_name"]
    agent_item = {
        "item_id": item["item_id"],
        "query_path": item["image"],
        "ref_paths": item["refs"],
        "domain_code": domain_code,
    }
    # Re-implement minimal trajectory recorder. We can't easily extract
    # the full message list from agent_v12_mmad without modifying it,
    # so we patch into _run_v9_agent_v12 by capturing via wrapper.
    # Simplest: run the agent + then reconstruct an abbreviated history
    # from item context for the logit follow-up.
    try:
        r = v12_mmad_mod._run_v9_agent_v12(
            client, model, agent_item, split, max_turns,
            question=question, options=options)
        # Reconstruct minimal history: system + user(query+refs+question)
        # + assistant(rationale).
        import agent_prompt_v12_mmad as _p
        from infer import load_and_encode
        # Build a lightweight context that captures the agent's reasoning
        # well enough for the final letter logit.
        user_parts = []
        for rp in item["refs"][:4]:
            try:
                user_parts.append(text_msg("Normal reference:"))
                user_parts.append(img_msg(load_and_encode(rp)))
            except Exception:
                continue
        user_parts.append(text_msg("Query image:"))
        user_parts.append(img_msg(load_and_encode(item["image"])))
        opts_lines = "\n".join(f"  {k}: {v}" for k, v in options.items())
        user_parts.append(text_msg(
            f"QUESTION: {question}\nOPTIONS:\n{opts_lines}"))
        # Inject the agent's own reasoning summary as the assistant turn.
        agent_reasoning = (
            f"My reasoning: {r.rationale or ''}\n"
            f"Tools used: {', '.join(r.tools_used or []) or 'none'}\n"
            f"Mode: {r.mode}\n"
            f"My initial pick: {r.mcq_answer or 'none'}\n"
            f"My option scores: {r.option_scores or 'none'}"
        )
        history = [
            {"role": "system", "content": _p.SYSTEM_PROMPT},
            {"role": "user", "content": user_parts},
            {"role": "assistant", "content": agent_reasoning},
        ]
        return r, history
    except Exception as e:
        return None, None


def _run_one(client, model, item, split, max_turns, use_dataset_dcode):
    is_ad = (item["question_type"] == "Anomaly Detection")
    out = {
        "item_id": item["item_id"], "image": item["raw_key"],
        "correct_answer": item["correct_answer"],
        "question_type": item["question_type"],
        "question": item["question"], "options": item["options"],
        "class_name": item["class_name"], "dataset": item["dataset"],
        "label_gt": item["label_gt"],
    }
    letters = sorted(item["options"].keys())

    # --- 1. Direct logit ---
    dlogit = mcq_logit_call(client, model, item["image"], item["refs"],
                            item["question"], item["options"])
    out["direct_logit_answer"] = dlogit.get("answer")
    out["direct_logits"] = dlogit.get("logits")
    out["direct_logit_scores"] = dlogit.get("scores")
    if dlogit.get("error"):
        out["direct_logit_error"] = dlogit["error"]

    # --- 2. Agent v12_mmad trajectory ---
    r, history = _run_agent_with_history(
        client, model, item, split, max_turns,
        item["question"], item["options"], use_dataset_dcode)
    if r is not None:
        out["agent_answer"] = r.mcq_answer
        out["agent_option_scores"] = r.option_scores
        out["agent_mode"] = r.mode
        out["agent_n_turns"] = r.n_turns
        out["agent_tools_used"] = r.tools_used
        out["agent_rationale"] = (r.rationale or "")[:200]
        if r.error:
            out["agent_error"] = r.error
    else:
        out["agent_answer"] = None
        out["agent_error"] = "agent_failed"

    # --- 3. Agent logit follow-up ---
    if history is not None:
        alogit = _agent_logit_followup(client, model, history, letters)
        out["agent_logit_answer"] = alogit.get("answer")
        out["agent_logits"] = alogit.get("logits")
        out["agent_logit_scores"] = alogit.get("scores")
        if alogit.get("error"):
            out["agent_logit_error"] = alogit["error"]
    else:
        out["agent_logit_answer"] = None

    # --- 4. Ensemble ---
    ans, scores = ensemble_logits(out.get("direct_logits"),
                                  out.get("agent_logits"), letters)
    out["ensemble_logit_answer"] = ans
    out["ensemble_logit_scores"] = scores
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mmad_root", default="MMAD/dataset/MMAD")
    ap.add_argument("--output", required=True)
    ap.add_argument("--sample", type=int, default=500)
    ap.add_argument("--only_types", default=None)
    ap.add_argument("--backend", default="qwen3")
    ap.add_argument("--max_workers", type=int, default=16)
    ap.add_argument("--max_turns", type=int, default=5)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--use_dataset_dcode", action="store_true", default=True)
    args = ap.parse_args()

    if args.sample and args.sample > 0:
        items = stratified_sample_images(args.mmad_root, args.sample,
                                         seed=args.seed)
    else:
        items = list(iter_mmad_items(args.mmad_root))
    if args.only_types:
        keep = set(t.strip() for t in args.only_types.split(","))
        items = [x for x in items if x["question_type"] in keep]
    print(f"[mmad_logit] {len(items)} QA items", flush=True)

    prev = []; done_ids = set()
    if args.resume and os.path.exists(args.output):
        prev = json.load(open(args.output))
        done_ids = {r["item_id"] for r in prev if r.get("direct_logit_answer")}
        items = [x for x in items if x["item_id"] not in done_ids]
        print(f"[resume] {len(done_ids)} done; {len(items)} remaining",
              flush=True)

    client = get_client(args.backend)
    model = get_model_name(args.backend)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    results = list(prev)
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.max_workers) as ex:
        futs = [ex.submit(_run_one, client, model, x, "test",
                           args.max_turns, args.use_dataset_dcode)
                for x in items]
        for i, f in enumerate(as_completed(futs)):
            try:
                results.append(f.result())
            except Exception as e:
                print(f"[err] worker: {type(e).__name__}: {e}", flush=True)
            if (i + 1) % 10 == 0:
                with open(args.output, "w") as ff:
                    json.dump(results, ff)
                dt = time.time() - t0
                rate = (i + 1) / dt if dt > 0 else 0
                eta = (len(items) - (i + 1)) / rate if rate > 0 else 0
                print(f"[{i+1}/{len(items)}] t={dt:.1f}s rate={rate:.2f}/s "
                      f"eta={eta:.0f}s", flush=True)

    with open(args.output, "w") as f:
        json.dump(results, f)
    print(f"Wrote {len(results)} → {args.output}")

    # Accuracy report
    print("\n=== Per-type letter accuracy (logit) ===", flush=True)
    by_type = defaultdict(list)
    for r in results:
        by_type[r.get("question_type")].append(r)
    for qt in QTYPES_ALL:
        subset = by_type.get(qt) or []
        if not subset:
            continue
        for fld in ("direct_logit_answer", "agent_logit_answer",
                    "ensemble_logit_answer"):
            corr = sum(1 for r in subset
                       if r.get(fld) and r.get(fld) == r["correct_answer"])
            tot = sum(1 for r in subset if r.get(fld))
            if tot:
                print(f"  {qt:25s} {fld:25s} {corr:3d}/{tot:<4d} "
                      f"{100*corr/tot:5.2f}%")


if __name__ == "__main__":
    main()
