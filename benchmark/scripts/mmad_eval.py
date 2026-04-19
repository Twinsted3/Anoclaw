"""MMAD benchmark evaluator for AnomalyClaw on Qwen3.5-VL.

MMAD is a 39,670-question industrial anomaly detection MCQ benchmark (Jiang
et al., ICLR 2025). We evaluate on the "Anomaly Detection" subset
(binary Yes/No per image; 8,297 images covering MVTec-AD, MVTec-LOCO,
VisA, GoodsAD) by running Direct VLM and the v6 agent on each query,
then mapping the anomaly score to A/B:

    score > 0.5  ->  A ("Yes, there's a defect")
    score <= 0.5 ->  B ("No defect")

Per image we use the first 4 normal `random_templates` from mmad.json as
references (consistent with MMAD protocol's few_shot=4 normal setup).

Usage:
    python benchmark/scripts/mmad_eval.py \
      --mmad_root MMAD/dataset/MMAD \
      --sample 1000 \
      --output benchmark/results/mmad_anomaly_qwen3.json \
      --max_workers 9 --max_turns 5
"""
from __future__ import annotations
import argparse
import json
import os
import random
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from infer import (  # noqa: E402
    call_llm, extract_json, get_client, get_model_name,
    img_msg, load_and_encode, text_msg,
)
import agent_v6 as v6_mod  # noqa: E402


def iter_mmad_ad_items(mmad_root: str, only_ad: bool = True):
    """Yield one item per image × AD-question from mmad.json.

    Each yielded dict:
        item_id (str unique),
        image (str absolute path),
        refs (list of str absolute paths; first 4 random_templates),
        class_name (e.g. "bottle"),
        dataset (e.g. "DS-MVTec"),
        label_gt (0 if 'good' in path, 1 otherwise),
        correct_answer (str A|B|C|D),
        question_type (str),
        question (str),
        options (dict).
    """
    mmad_json = json.load(open(os.path.join(mmad_root, "mmad.json")))
    for key, v in mmad_json.items():
        parts = key.split("/")
        dataset = parts[0]
        class_name = parts[1] if len(parts) >= 2 else "unknown"
        image_abs = os.path.join(mmad_root, key)
        refs = []
        for t in (v.get("random_templates") or [])[:4]:
            refs.append(os.path.join(mmad_root, t))
        # Yield each QA turn
        for idx, qa in enumerate(v.get("conversation", [])):
            if only_ad and qa.get("type") != "Anomaly Detection":
                continue
            # Binary AD label: anomalous (label=1) unless path contains 'good' or 'normal'
            label_gt = 0 if ("good" in key.lower() or "normal" in key.lower()) else 1
            yield {
                "item_id": f"{key}#q{idx}",
                "image": image_abs,
                "refs": refs,
                "class_name": class_name,
                "dataset": dataset,
                "label_gt": label_gt,
                "correct_answer": qa.get("Answer"),
                "question_type": qa.get("type"),
                "question": qa.get("Question"),
                "options": qa.get("Options", {}),
                "raw_key": key,
            }


def stratified_sample(items, n, seed=42):
    """Sample n items stratified by class_name (roughly proportional)."""
    rng = random.Random(seed)
    by_class: dict[str, list] = defaultdict(list)
    for x in items:
        by_class[f"{x['dataset']}/{x['class_name']}"].append(x)
    total = sum(len(v) for v in by_class.values())
    # Proportional alloc with min 5 per class
    alloc = {k: max(5, int(n * len(v) / total)) for k, v in by_class.items()}
    total_alloc = sum(alloc.values())
    if total_alloc > n:
        # Scale down proportionally
        scale = n / total_alloc
        alloc = {k: max(3, int(v * scale)) for k, v in alloc.items()}
    sample = []
    for k, cap in alloc.items():
        pool = by_class[k]
        rng.shuffle(pool)
        sample.extend(pool[:cap])
    rng.shuffle(sample)
    return sample


# --- Direct VLM scoring -------------------------------------------------

DIRECT_PROMPT = (
    "You are a visual anomaly detection expert. I will show you four NORMAL "
    "reference images of the same product, followed by one QUERY image. "
    "Decide whether the query shows a manufacturing defect, damage, or "
    "abnormal appearance.\n\n"
    "Return ONLY a JSON object: {\"thought\": \"<one sentence>\", "
    "\"score\": <float 0..1>, \"rationale\": \"<one sentence>\"}. "
    "score close to 0 = clearly normal, score close to 1 = clearly anomalous, "
    "0.5 = genuinely uncertain."
)


def direct_score(client, model, image_path: str, ref_paths: list[str]) -> dict:
    parts = [text_msg("NORMAL REFERENCE IMAGES:")]
    for rp in ref_paths[:4]:
        if os.path.exists(rp):
            parts.append(img_msg(load_and_encode(rp)))
    parts.append(text_msg("QUERY IMAGE:"))
    parts.append(img_msg(load_and_encode(image_path)))
    messages = [
        {"role": "system", "content": DIRECT_PROMPT},
        {"role": "user", "content": parts},
    ]
    try:
        text, _, _ = call_llm(client, model, messages,
                              max_tokens=200, temperature=0.0)
    except Exception as e:
        return {"score": 0.5, "error": f"call_llm: {e}"}
    parsed = extract_json(text)
    if not isinstance(parsed, dict) or "score" not in parsed:
        return {"score": 0.5, "error": "parse fail",
                "raw": (text or "")[:200]}
    try:
        s = float(parsed["score"])
        s = max(0.0, min(1.0, s))
    except (TypeError, ValueError):
        return {"score": 0.5, "error": "score not float"}
    return {"score": s,
            "thought": str(parsed.get("thought", ""))[:200],
            "rationale": str(parsed.get("rationale", ""))[:200]}


# --- v6 ReAct agent scoring ---------------------------------------------

def v6_agent_score(agent: v6_mod.ReActAgent, item: dict, split: str = "test") -> dict:
    """Run v6 agent and return score + rationale.

    We pass a synthetic split and item_id so cached-expert tools won't
    error (they'll just return missing-score errors that the agent learns
    to ignore).
    """
    try:
        r = agent.run(item_id=item["item_id"], query_path=item["image"],
                      ref_paths=item["refs"], split=split,
                      domain_code=None)
        return {"score": r.score,
                "n_turns": r.n_turns,
                "tools_used": r.tools_used,
                "rationale": (r.rationale or "")[:200],
                "error": r.error}
    except Exception as e:
        return {"score": 0.5, "error": f"{type(e).__name__}: {e}"}


def score_to_mcq(score: float, options: dict) -> str:
    """Map score to MCQ answer. AD questions usually have A=Yes B=No."""
    yes_letter = None
    no_letter = None
    for letter, text in options.items():
        t = text.lower()
        if "yes" in t or "there is" in t or "defect" in t:
            yes_letter = letter
        elif "no " in t or "no defect" in t or "not" in t:
            no_letter = letter
    yes_letter = yes_letter or "A"
    no_letter = no_letter or "B"
    return yes_letter if score > 0.5 else no_letter


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mmad_root",
                    default="MMAD/dataset/MMAD")
    ap.add_argument("--output",
                    default="benchmark/results/mmad_anomaly_qwen3.json")
    ap.add_argument("--sample", type=int, default=1000,
                    help="Stratified sample size (0 = all AD items)")
    ap.add_argument("--backend", default="qwen3")
    ap.add_argument("--max_workers", type=int, default=9)
    ap.add_argument("--max_turns", type=int, default=5)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--mode", choices=["direct", "agent", "both"], default="both",
                    help="direct only / agent only / both (for ensemble)")
    args = ap.parse_args()

    print(f"[mmad] loading from {args.mmad_root}/mmad.json ...", flush=True)
    all_items = list(iter_mmad_ad_items(args.mmad_root, only_ad=True))
    print(f"[mmad] {len(all_items)} Anomaly-Detection questions in full set", flush=True)

    if args.sample and args.sample < len(all_items):
        items = stratified_sample(all_items, args.sample, seed=args.seed)
        print(f"[mmad] stratified sample -> {len(items)} items "
              f"across {len({i['class_name'] for i in items})} classes", flush=True)
    else:
        items = all_items

    # Resume logic
    done_ids: set = set()
    prev: list = []
    if args.resume and os.path.exists(args.output):
        prev = json.load(open(args.output))
        done_ids = {r["item_id"] for r in prev if not r.get("error")}
        items = [x for x in items if x["item_id"] not in done_ids]
        print(f"[resume] {len(done_ids)} done; {len(items)} remaining", flush=True)

    client = get_client(args.backend)
    model = get_model_name(args.backend)
    agent = v6_mod.ReActAgent(vlm_client=client, vlm_model=model,
                              max_turns=args.max_turns)

    t0 = time.time()

    def _run(x):
        out = {
            "item_id": x["item_id"],
            "image": x["raw_key"],  # MMAD key (relative)
            "correct_answer": x["correct_answer"],
            "question_type": x["question_type"],
            "class_name": x["class_name"],
            "dataset": x["dataset"],
            "label_gt": x["label_gt"],
        }
        # Direct
        if args.mode in ("direct", "both"):
            dr = direct_score(client, model, x["image"], x["refs"])
            out["direct_score"] = dr.get("score")
            out["direct_rationale"] = dr.get("rationale", "")
            if dr.get("error"):
                out["direct_error"] = dr["error"]
        # Agent
        if args.mode in ("agent", "both"):
            ag = v6_agent_score(agent, x, split="test")
            out["agent_score"] = ag.get("score")
            out["agent_n_turns"] = ag.get("n_turns")
            out["agent_tools_used"] = ag.get("tools_used")
            out["agent_rationale"] = ag.get("rationale", "")
            if ag.get("error"):
                out["agent_error"] = ag["error"]
        # Ensemble
        if args.mode == "both":
            if out.get("direct_score") is not None and out.get("agent_score") is not None:
                out["ensemble_score"] = 0.5 * out["direct_score"] + 0.5 * out["agent_score"]
                out["ensemble_answer"] = score_to_mcq(out["ensemble_score"], x["options"])
            out["direct_answer"] = score_to_mcq(out.get("direct_score", 0.5), x["options"])
            out["agent_answer"] = score_to_mcq(out.get("agent_score", 0.5), x["options"])
        elif args.mode == "direct":
            out["direct_answer"] = score_to_mcq(out.get("direct_score", 0.5), x["options"])
        else:
            out["agent_answer"] = score_to_mcq(out.get("agent_score", 0.5), x["options"])
        return out

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    results = list(prev)
    with ThreadPoolExecutor(max_workers=args.max_workers) as ex:
        futs = [ex.submit(_run, x) for x in items]
        for i, f in enumerate(as_completed(futs)):
            try:
                results.append(f.result())
            except Exception as e:
                print(f"[err] worker raised: {type(e).__name__}: {e}", flush=True)
            if (i + 1) % 25 == 0:
                with open(args.output, "w") as ff:
                    json.dump(results, ff)
                print(f"[{i+1}/{len(items)}] t={time.time()-t0:.1f}s", flush=True)

    with open(args.output, "w") as f:
        json.dump(results, f)
    print(f"Wrote {len(results)} → {args.output}")

    # Quick accuracy report
    for field in ("direct_answer", "agent_answer", "ensemble_answer"):
        correct = sum(1 for r in results if r.get(field) == r.get("correct_answer"))
        total = sum(1 for r in results if r.get(field))
        if total:
            print(f"{field}: {correct}/{total} = {100*correct/total:.2f}%")


if __name__ == "__main__":
    main()
