"""MMAD evaluator — fair single-letter baseline.

Pipeline per item:
  1) Direct (single-letter): one VLM call with prompt "Reply with EXACTLY
     one letter and nothing else." Parse first letter from raw text.
     NO JSON, NO logit constraint to A/B/C/D — pure text parse.
  2) Agent v12_mmad full multi-turn trajectory (unchanged).
  3) Agent single-letter followup: append "Final answer: one letter." to
     the agent's history (system + user(question) + assistant(rationale))
     and parse first letter from raw text.

This is the apples-to-apples comparison the previous logit run could not
provide — both Direct and Agent output a free-form letter without
artificial A/B/C/D constraint.

Output is aligned to MMAD's official 4 datasets × 7 subtasks reporting:
  Subtasks: Anomaly Detection / Defect Classification / Defect
            Localization / Defect Description / Defect Analysis /
            Object Classification / Object Analysis (= our Object
            Analysis + Object Structure + Object Details merged).
  Datasets: DS-MVTec / MVTec-LOCO / VisA / GoodsAD.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from infer import (  # noqa: E402
    get_client, get_model_name, img_msg, load_and_encode, text_msg,
)
import agent_v12_mmad as v12_mmad_mod  # noqa: E402

from mmad_eval_v9 import (  # noqa: E402
    QTYPES_ALL,
    iter_mmad_items,
    stratified_sample_images,
)
from mmad_eval_v12_mmad import MMAD_DATASET_TO_DCODE  # noqa: E402


_DIRECT_LETTER_PROMPT = (
    "You are an industrial-inspection visual expert. I will show you "
    "NORMAL reference images followed by a QUERY image, then ask a "
    "multiple-choice question. Pick the single best option that fits "
    "what you see in the query image.\n\n"
    "Reply with EXACTLY one letter and nothing else. Do not write "
    "JSON, do not write a rationale — only the letter."
)

_AGENT_LETTER_FOLLOWUP = (
    "Based on your reasoning above, output your final answer to the "
    "multiple-choice question. Reply with EXACTLY one letter "
    "(one of {letters}) and nothing else."
)


def _parse_first_letter(text: str, letters):
    """Parse the first valid candidate letter from a free-text response."""
    if not text:
        return None
    # Look for whole-token A/B/C/D, optionally followed by punctuation
    m = re.search(r"\b([A-D])\b", text.upper())
    if m and m.group(1) in letters:
        return m.group(1)
    # Last-resort: first uppercase letter that's a candidate
    for c in text.upper():
        if c in letters:
            return c
    return None


def _direct_letter_call(client, model, image_path, ref_paths, question,
                        options):
    """Single-letter Direct call — NO JSON, NO logit constraint."""
    parts = [text_msg("NORMAL REFERENCE IMAGES:")]
    for rp in (ref_paths or [])[:4]:
        try:
            parts.append(img_msg(load_and_encode(rp)))
        except Exception:
            continue
    parts.append(text_msg("QUERY IMAGE:"))
    try:
        parts.append(img_msg(load_and_encode(image_path)))
    except Exception as e:
        return {"answer": None, "raw_text": "",
                "error": f"image: {e}"}
    opts_lines = "\n".join(f"  {k}: {v}" for k, v in options.items())
    parts.append(text_msg(f"QUESTION: {question}\nOPTIONS:\n{opts_lines}"))

    msgs = [{"role": "system", "content": _DIRECT_LETTER_PROMPT},
            {"role": "user", "content": parts}]
    kwargs = dict(model=model, messages=msgs, max_tokens=4, temperature=0.0)
    if "qwen3" in str(model).lower() or "Qwen3" in str(model):
        kwargs["extra_body"] = {
            "chat_template_kwargs": {"enable_thinking": False}}
    try:
        resp = client.chat.completions.create(**kwargs)
    except Exception as e:
        return {"answer": None, "raw_text": "",
                "error": f"call: {type(e).__name__}: {e}"}
    text = resp.choices[0].message.content or ""
    letters = sorted(options.keys())
    return {"answer": _parse_first_letter(text, letters),
            "raw_text": text, "error": None}


def _agent_letter_followup(client, model, image_path, ref_paths, question,
                           options, agent_result):
    """Single-letter agent followup using a slim history."""
    user_parts = []
    for rp in (ref_paths or [])[:4]:
        try:
            user_parts.append(text_msg("Normal reference:"))
            user_parts.append(img_msg(load_and_encode(rp)))
        except Exception:
            continue
    user_parts.append(text_msg("Query image:"))
    try:
        user_parts.append(img_msg(load_and_encode(image_path)))
    except Exception:
        pass
    opts_lines = "\n".join(f"  {k}: {v}" for k, v in options.items())
    user_parts.append(text_msg(
        f"QUESTION: {question}\nOPTIONS:\n{opts_lines}"))

    rationale = (agent_result.rationale or "")[:300] if agent_result else ""
    tools = (agent_result.tools_used if agent_result else None) or []
    initial_pick = (agent_result.mcq_answer if agent_result else None) or "?"
    summary = (
        f"My reasoning: {rationale}\n"
        f"Tools used: {', '.join(tools) or 'none'}\n"
        f"My initial pick: {initial_pick}"
    )
    letters = sorted(options.keys())
    msgs = [
        {"role": "system", "content": _DIRECT_LETTER_PROMPT},
        {"role": "user", "content": user_parts},
        {"role": "assistant", "content": summary},
        {"role": "user",
         "content": _AGENT_LETTER_FOLLOWUP.format(
             letters="/".join(letters))},
    ]
    kwargs = dict(model=model, messages=msgs, max_tokens=4, temperature=0.0)
    if "qwen3" in str(model).lower() or "Qwen3" in str(model):
        kwargs["extra_body"] = {
            "chat_template_kwargs": {"enable_thinking": False}}
    try:
        resp = client.chat.completions.create(**kwargs)
    except Exception as e:
        return {"answer": None, "raw_text": "",
                "error": f"call: {type(e).__name__}: {e}"}
    text = resp.choices[0].message.content or ""
    return {"answer": _parse_first_letter(text, letters),
            "raw_text": text, "error": None}


def _run_one(client, model, item, split, max_turns, use_dataset_dcode):
    out = {
        "item_id": item["item_id"], "image": item["raw_key"],
        "correct_answer": item["correct_answer"],
        "question_type": item["question_type"],
        "question": item["question"], "options": item["options"],
        "class_name": item["class_name"], "dataset": item["dataset"],
        "label_gt": item["label_gt"],
    }

    # --- 1. Direct single-letter ---
    dr = _direct_letter_call(client, model, item["image"], item["refs"],
                             item["question"], item["options"])
    out["direct_answer"] = dr.get("answer")
    out["direct_raw_text"] = dr.get("raw_text", "")[:50]
    if dr.get("error"):
        out["direct_error"] = dr["error"]

    # --- 2. Agent v12_mmad trajectory ---
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
    try:
        r = v12_mmad_mod._run_v9_agent_v12(
            client, model, agent_item, split, max_turns,
            question=item["question"], options=item["options"])
        out["agent_initial_answer"] = r.mcq_answer
        out["agent_option_scores"] = r.option_scores
        out["agent_mode"] = r.mode
        out["agent_n_turns"] = r.n_turns
        out["agent_tools_used"] = r.tools_used
        out["agent_rationale"] = (r.rationale or "")[:200]
        if r.error:
            out["agent_error"] = r.error
    except Exception as e:
        r = None
        out["agent_initial_answer"] = None
        out["agent_error"] = f"{type(e).__name__}: {e}"

    # --- 3. Agent single-letter followup ---
    af = _agent_letter_followup(client, model, item["image"], item["refs"],
                                item["question"], item["options"], r)
    out["agent_answer"] = af.get("answer")
    out["agent_raw_text"] = af.get("raw_text", "")[:50]
    if af.get("error"):
        out["agent_followup_error"] = af["error"]

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
    print(f"[mmad_letter] {len(items)} QA items", flush=True)

    prev = []; done_ids = set()
    if args.resume and os.path.exists(args.output):
        prev = json.load(open(args.output))
        done_ids = {r["item_id"] for r in prev if r.get("direct_answer")}
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

    # MMAD-aligned 4×7 table.
    print("\n=== MMAD 4 datasets × 7 subtasks (single-letter) ===",
          flush=True)
    OBJ_ANALYSIS_MERGE = {"Object Analysis", "Object Structure",
                          "Object Details"}
    SUBTASK_DEF = (
        ("Anomaly Detection", {"Anomaly Detection"}),
        ("Defect Classification", {"Defect Classification"}),
        ("Defect Localization", {"Defect Localization"}),
        ("Defect Description", {"Defect Description"}),
        ("Defect Analysis", {"Defect Analysis"}),
        ("Object Classification", {"Object Classification"}),
        ("Object Analysis", OBJ_ANALYSIS_MERGE),
    )
    DATASETS = ("DS-MVTec", "MVTec-LOCO", "VisA", "GoodsAD")

    def acc(items, fld):
        n = sum(1 for r in items if r.get(fld))
        if n == 0:
            return float('nan')
        c = sum(1 for r in items if r.get(fld) == r["correct_answer"])
        return c / n * 100

    for fld_label, fld in (("Direct", "direct_answer"),
                            ("Agent ", "agent_answer")):
        print(f"\n--- {fld_label} ---")
        header = f"{'Dataset':12s} | " + " ".join(
            f"{nm:>9s}" for nm, _ in SUBTASK_DEF) + f" | {'Avg':>6s}"
        print(header)
        for ds in DATASETS:
            row_items = [r for r in results if r["dataset"] == ds]
            if not row_items:
                continue
            cells = []
            avg_vals = []
            for nm, qts in SUBTASK_DEF:
                sub = [r for r in row_items
                       if r["question_type"] in qts]
                if sub:
                    a = acc(sub, fld)
                    cells.append(f"{a:8.2f}%")
                    avg_vals.append(a)
                else:
                    cells.append(f"{'--':>9s}")
            avg = sum(avg_vals) / len(avg_vals) if avg_vals else float('nan')
            print(f"{ds:12s} | " + " ".join(cells) + f" | {avg:5.2f}%")


if __name__ == "__main__":
    main()
