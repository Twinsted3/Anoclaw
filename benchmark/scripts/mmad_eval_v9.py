"""MMAD full-type evaluator for v9 unified agent.

Extends mmad_eval.py to all 9 MMAD question types (not just AD).

For each (image, question) pair:
  - Agent v9 runs with (image, refs, question, options) → mcq_answer or score
  - Direct VLM: MCQ-aware prompt → per-option softmax → argmax
  - AD only: ensemble via 0.5*s_direct + 0.5*s_agent → threshold→letter.

Output JSON per item: {type, letter_gt, direct_letter, agent_letter,
  ensemble_letter(AD only), scores, ...}.

Usage:
  python benchmark/scripts/mmad_eval_v9.py \
    --mmad_root MMAD/dataset/MMAD \
    --sample 1000 --output benchmark/results/mmad_v9_dev989.json \
    --max_workers 9 --max_turns 5 \
    --backend qwen3
"""
from __future__ import annotations
import argparse
import json
import os
import random
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from infer import (  # noqa: E402
    call_llm, extract_json, get_client, get_model_name,
    img_msg, load_and_encode, text_msg,
)
import agent_v9 as v9_mod  # noqa: E402


# -------------------------- Data loading --------------------------

QTYPES_ALL = (
    "Anomaly Detection",
    "Defect Classification",
    "Defect Localization",
    "Defect Description",
    "Defect Analysis",
    "Object Classification",
    "Object Analysis",
    "Object Structure",
    "Object Details",
)


def iter_mmad_items(mmad_root: str, qtypes=QTYPES_ALL):
    mmad_json = json.load(open(os.path.join(mmad_root, "mmad.json")))
    for key, v in mmad_json.items():
        parts = key.split("/")
        dataset = parts[0]
        class_name = parts[1] if len(parts) >= 2 else "unknown"
        image_abs = os.path.join(mmad_root, key)
        refs = []
        for t in (v.get("random_templates") or [])[:4]:
            refs.append(os.path.join(mmad_root, t))
        for idx, qa in enumerate(v.get("conversation", [])):
            qt = qa.get("type")
            if qt not in qtypes:
                continue
            label_gt = 0 if ("good" in key.lower() or "normal" in key.lower()) \
                else 1
            yield {
                "item_id": f"{key}#q{idx}",
                "image": image_abs,
                "refs": refs,
                "class_name": class_name,
                "dataset": dataset,
                "label_gt": label_gt,
                "correct_answer": qa.get("Answer"),
                "question_type": qt,
                "question": qa.get("Question"),
                "options": qa.get("Options", {}) or {},
                "raw_key": key,
            }


def stratified_sample_images(mmad_root, n_images, seed=42):
    """Sample n_images images stratified by dataset/class, then expand to
    all questions on those images."""
    by_img = defaultdict(list)
    for item in iter_mmad_items(mmad_root):
        by_img[item["raw_key"]].append(item)
    by_class = defaultdict(list)
    for k, v in by_img.items():
        cls = f"{v[0]['dataset']}/{v[0]['class_name']}"
        by_class[cls].append(k)
    rng = random.Random(seed)
    total_imgs = sum(len(v) for v in by_class.values())
    n_classes = len(by_class)
    # Scale floor with sample size. For very small n (sanity), allow 1 per class.
    floor = 1 if n_images < n_classes * 3 else (3 if n_images < n_classes * 8
                                                else 5)
    alloc = {k: max(floor, int(n_images * len(v) / total_imgs))
             for k, v in by_class.items()}
    total_alloc = sum(alloc.values())
    if total_alloc > n_images:
        scale = n_images / total_alloc
        alloc = {k: max(1, int(v * scale)) for k, v in alloc.items()}
    keys = []
    for cls, cap in alloc.items():
        pool = by_class[cls]
        rng.shuffle(pool)
        keys.extend(pool[:cap])
    rng.shuffle(keys)
    # Hard cap at n_images
    keys = keys[:n_images]
    # Expand to all questions on selected images
    all_items = []
    for k in keys:
        all_items.extend(by_img[k])
    return all_items


# -------------------------- Direct VLM MCQ baseline --------------------------

DIRECT_AD_PROMPT = (
    "You are a visual anomaly detection expert. I will show you NORMAL "
    "reference images followed by a QUERY image. Decide whether the query "
    "shows a defect, damage, or abnormal appearance.\n\n"
    "Return ONLY JSON: {\"thought\": \"<one sentence>\", \"score\": "
    "<float 0..1>, \"rationale\": \"<one sentence>\"}. "
    "score > 0.5 = anomalous."
)

DIRECT_MCQ_PROMPT = (
    "You are an industrial-inspection visual expert. I will show you NORMAL "
    "reference images followed by a QUERY image, then ask a multiple-choice "
    "question. Read the question and options carefully and choose the single "
    "best letter. Ground your answer in what you see.\n\n"
    "Return ONLY JSON: {\"thought\": \"<one sentence>\", \"answer\": "
    "\"A|B|C|D\", \"option_scores\": {\"A\":<float 0..1>, \"B\":<float 0..1>,"
    " \"C\":<float 0..1>, \"D\":<float 0..1>}, "
    "\"rationale\": \"<one sentence>\"}."
)


def direct_ad_score(client, model, image_path, ref_paths):
    parts = [text_msg("NORMAL REFERENCE IMAGES:")]
    for rp in ref_paths[:4]:
        if os.path.exists(rp):
            parts.append(img_msg(load_and_encode(rp)))
    parts.append(text_msg("QUERY IMAGE:"))
    parts.append(img_msg(load_and_encode(image_path)))
    msgs = [{"role": "system", "content": DIRECT_AD_PROMPT},
            {"role": "user", "content": parts}]
    try:
        text, _, _ = call_llm(client, model, msgs, max_tokens=180,
                              temperature=0.0)
    except Exception as e:
        return {"score": 0.5, "error": f"call: {e}"}
    parsed = extract_json(text)
    if not isinstance(parsed, dict) or "score" not in parsed:
        return {"score": 0.5, "error": "parse"}
    try:
        s = max(0.0, min(1.0, float(parsed["score"])))
    except (TypeError, ValueError):
        return {"score": 0.5, "error": "score_nan"}
    return {"score": s, "rationale": str(parsed.get("rationale", ""))[:200]}


def direct_mcq_answer(client, model, image_path, ref_paths, question,
                      options):
    parts = [text_msg("NORMAL REFERENCE IMAGES:")]
    for rp in ref_paths[:4]:
        if os.path.exists(rp):
            parts.append(img_msg(load_and_encode(rp)))
    parts.append(text_msg("QUERY IMAGE:"))
    parts.append(img_msg(load_and_encode(image_path)))
    opts_lines = "\n".join(f"  {k}: {v}" for k, v in options.items())
    parts.append(text_msg(f"QUESTION: {question}\nOPTIONS:\n{opts_lines}"))
    msgs = [{"role": "system", "content": DIRECT_MCQ_PROMPT},
            {"role": "user", "content": parts}]
    try:
        text, _, _ = call_llm(client, model, msgs, max_tokens=220,
                              temperature=0.0)
    except Exception as e:
        return {"answer": None, "error": f"call: {e}"}
    parsed = extract_json(text)
    if not isinstance(parsed, dict):
        return {"answer": None, "error": "parse"}
    ans = parsed.get("answer")
    if ans not in ("A", "B", "C", "D"):
        # try option_scores argmax
        opt = parsed.get("option_scores") or {}
        if opt:
            try:
                ans = max(opt.items(), key=lambda kv: float(kv[1]))[0]
            except Exception:
                ans = None
    return {"answer": ans if ans in ("A", "B", "C", "D") else None,
            "option_scores": parsed.get("option_scores"),
            "rationale": str(parsed.get("rationale", ""))[:200]}


# -------------------------- Agent wrapper --------------------------

def v9_agent_run(client, model, item, split, max_turns):
    """Run v9 agent on one MMAD item."""
    agent_item = {
        "item_id": item["item_id"],
        "query_path": item["image"],
        "ref_paths": item["refs"],
        "domain_code": item["class_name"],
    }
    try:
        r = v9_mod.run_v9_item(client, model, agent_item, split, max_turns,
                               question=item["question"],
                               options=item["options"])
        return {
            "score": r.score,
            "mcq_answer": r.mcq_answer,
            "free_text": r.free_text,
            "option_scores": r.option_scores,
            "mode": r.mode,
            "rationale": (r.rationale or "")[:200],
            "n_turns": r.n_turns, "tools_used": r.tools_used,
            "error": r.error,
        }
    except Exception as e:
        return {"score": 0.5, "mcq_answer": None, "error":
                f"{type(e).__name__}: {e}"}


# -------------------------- MCQ letter utilities --------------------------

def ad_score_to_letter(score, options):
    """Map AD score to Yes/No letter. Yes-letter = option containing
    'yes|defect|there is|anomal'."""
    yes_letter = None
    no_letter = None
    for letter, txt in options.items():
        t = str(txt).lower()
        if any(k in t for k in ("yes", "defect", "there is", "anomal")):
            yes_letter = letter
        elif any(k in t for k in ("no ", "no,", "no defect", "not ",
                                  "normal")):
            no_letter = letter
    yes_letter = yes_letter or "A"
    no_letter = no_letter or "B"
    return yes_letter if score > 0.5 else no_letter


# -------------------------- Main loop --------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mmad_root", default="MMAD/dataset/MMAD")
    ap.add_argument("--output", required=True)
    ap.add_argument("--sample", type=int, default=1000,
                    help="Sample size in IMAGES; expanded to all questions "
                         "on those images. 0 = all images.")
    ap.add_argument("--only_types", default=None,
                    help="Comma-separated question types to keep.")
    ap.add_argument("--backend", default="qwen3")
    ap.add_argument("--max_workers", type=int, default=9)
    ap.add_argument("--max_turns", type=int, default=5)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--mode", choices=["agent", "direct", "both"],
                    default="both")
    args = ap.parse_args()

    if args.sample and args.sample > 0:
        print(f"[mmad_v9] stratified sampling {args.sample} images",
              flush=True)
        items = stratified_sample_images(args.mmad_root, args.sample,
                                         seed=args.seed)
    else:
        items = list(iter_mmad_items(args.mmad_root))
    if args.only_types:
        keep = set(t.strip() for t in args.only_types.split(","))
        items = [x for x in items if x["question_type"] in keep]
    print(f"[mmad_v9] {len(items)} QA items "
          f"across {len({i['class_name'] for i in items})} classes",
          flush=True)

    # Resume
    prev: list = []
    done_ids: set = set()
    if args.resume and os.path.exists(args.output):
        prev = json.load(open(args.output))
        done_ids = {r["item_id"] for r in prev if not r.get("fatal_error")}
        items = [x for x in items if x["item_id"] not in done_ids]
        print(f"[resume] {len(done_ids)} done; {len(items)} remaining",
              flush=True)

    client = get_client(args.backend)
    model = get_model_name(args.backend)
    t0 = time.time()

    def _run(x):
        out = {
            "item_id": x["item_id"], "image": x["raw_key"],
            "correct_answer": x["correct_answer"],
            "question_type": x["question_type"],
            "question": x["question"], "options": x["options"],
            "class_name": x["class_name"], "dataset": x["dataset"],
            "label_gt": x["label_gt"],
        }
        is_ad = (x["question_type"] == "Anomaly Detection")
        # Direct
        if args.mode in ("direct", "both"):
            if is_ad:
                dr = direct_ad_score(client, model, x["image"], x["refs"])
                out["direct_score"] = dr.get("score")
                out["direct_rationale"] = dr.get("rationale", "")
                out["direct_answer"] = ad_score_to_letter(
                    dr.get("score", 0.5), x["options"])
                if dr.get("error"):
                    out["direct_error"] = dr["error"]
            else:
                dm = direct_mcq_answer(client, model, x["image"], x["refs"],
                                       x["question"], x["options"])
                out["direct_answer"] = dm.get("answer")
                out["direct_option_scores"] = dm.get("option_scores")
                out["direct_rationale"] = dm.get("rationale", "")
                if dm.get("error"):
                    out["direct_error"] = dm["error"]
        # Agent
        if args.mode in ("agent", "both"):
            ag = v9_agent_run(client, model, x, "test", args.max_turns)
            out["agent_score"] = ag.get("score")
            out["agent_option_scores"] = ag.get("option_scores")
            out["agent_mode"] = ag.get("mode")
            out["agent_n_turns"] = ag.get("n_turns")
            out["agent_tools_used"] = ag.get("tools_used")
            out["agent_rationale"] = ag.get("rationale", "")
            if is_ad:
                out["agent_answer"] = ad_score_to_letter(
                    ag.get("score", 0.5), x["options"])
            else:
                out["agent_answer"] = ag.get("mcq_answer")
            if ag.get("error"):
                out["agent_error"] = ag["error"]
        # Ensemble (AD only)
        if args.mode == "both" and is_ad:
            if (out.get("direct_score") is not None
                    and out.get("agent_score") is not None):
                ens = 0.5 * out["direct_score"] + 0.5 * out["agent_score"]
                out["ensemble_score"] = ens
                out["ensemble_answer"] = ad_score_to_letter(
                    ens, x["options"])
        return out

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    results = list(prev)
    with ThreadPoolExecutor(max_workers=args.max_workers) as ex:
        futs = [ex.submit(_run, x) for x in items]
        for i, f in enumerate(as_completed(futs)):
            try:
                results.append(f.result())
            except Exception as e:
                print(f"[err] worker: {type(e).__name__}: {e}", flush=True)
            if (i + 1) % 10 == 0:
                with open(args.output, "w") as ff:
                    json.dump(results, ff)
                dt = time.time() - t0
                rate = (i + 1) / dt if dt > 0 else 0.0
                eta = (len(items) - (i + 1)) / rate if rate > 0 else 0
                print(f"[{i+1}/{len(items)}] t={dt:.1f}s "
                      f"rate={rate:.2f}/s eta={eta:.0f}s", flush=True)

    with open(args.output, "w") as f:
        json.dump(results, f)
    print(f"Wrote {len(results)} → {args.output}")

    # Accuracy report by type
    print("\n=== Per-type MCQ accuracy ===", flush=True)
    for qt in QTYPES_ALL:
        subset = [r for r in results if r.get("question_type") == qt]
        if not subset:
            continue
        for field in ("direct_answer", "agent_answer", "ensemble_answer"):
            correct = sum(1 for r in subset if r.get(field)
                          and r.get(field) == r.get("correct_answer"))
            total = sum(1 for r in subset if r.get(field))
            if total:
                print(f"  {qt:25s} {field:16s} {correct}/{total} = "
                      f"{100*correct/total:5.2f}%")


if __name__ == "__main__":
    main()
