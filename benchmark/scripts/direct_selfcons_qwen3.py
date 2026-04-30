#!/usr/bin/env python3
"""Direct@N=3 self-consistency baseline for the budget-matched control.

For each test item, calls Direct (run_v0) N=3 times at temperature T, parses
the score from each call, and saves the mean. Skip-on-error per call (we
report the average over the calls that did parse).

Output schema mirrors v0_direct_generic_*_test.json, with extra fields
`scores_per_call` and `n_successful_calls` for inspection.

Run: python direct_selfcons_qwen3.py --backend qwen3 --split test \
       --output benchmark/results/v2/v0_directN3_test_qwen3.json --n_calls 3 --temperature 0.5
"""
import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "benchmark/scripts"))

from infer import (
    N_REFS, build_prompt_v0, call_llm, extract_json, get_client,
    get_model_name, img_msg, label_from_score, load_and_encode,
    score_from_v0, text_msg
)


def run_v0_t(client, model, item, temperature, max_tokens=700):
    ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:N_REFS]]
    query_img = load_and_encode(item["query_path"])
    domain_code = item["domain_code"]
    prompt = build_prompt_v0(domain_code, bool(ref_imgs))
    content = []
    for b64 in ref_imgs:
        content.append(text_msg("Normal reference:"))
        content.append(img_msg(b64))
    content.append(text_msg("Query image:"))
    content.append(img_msg(query_img))
    content.append(text_msg(prompt))
    t0 = time.time()
    text, inp, out = call_llm(
        client, model, [{"role": "user", "content": content}],
        max_tokens=max_tokens, temperature=temperature)
    parsed = extract_json(text)
    score = score_from_v0(parsed) if parsed else None
    return {
        "score": score,
        "anomaly_type": (parsed or {}).get("anomaly_type") if parsed else None,
        "raw": parsed,
        "tokens": (inp, out),
        "latency": round(time.time() - t0, 2),
    }


def run_one(client, model, item, n_calls, temperature):
    scores = []
    raws = []
    errors = []
    inp_total = 0
    out_total = 0
    for i in range(n_calls):
        try:
            res = run_v0_t(client, model, item, temperature=temperature)
            if res["score"] is not None:
                scores.append(res["score"])
                raws.append(res["raw"])
            inp_total += res["tokens"][0]
            out_total += res["tokens"][1]
        except Exception as e:
            errors.append(f"{type(e).__name__}: {e}")
    if not scores:
        avg = None
    else:
        avg = sum(scores) / len(scores)
    return {
        "item_id": item.get("item_id"),
        "domain": item.get("domain"),
        "domain_code": item.get("domain_code"),
        "label_gt": item.get("label"),
        "split": item.get("split"),
        "source_dataset": item.get("source_dataset"),
        "category": item.get("category"),
        "label_pred": label_from_score(avg) if avg is not None else None,
        "anomaly_score": avg,
        "scores_per_call": scores,
        "n_successful_calls": len(scores),
        "n_calls": n_calls,
        "temperature": temperature,
        "raw_outputs": raws,
        "cost_tokens": {"input": inp_total, "output": out_total},
        "errors": errors,
        "error": ";".join(errors) if (not scores) else None,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--split", default="test")
    ap.add_argument("--backend", choices=["gpt", "seedvl", "qwen3"], required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--n_calls", type=int, default=3)
    ap.add_argument("--temperature", type=float, default=0.5)
    ap.add_argument("--max_workers", type=int, default=32)
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    items = json.load(open(args.manifest))
    if isinstance(items, dict) and "items" in items:
        items = items["items"]
    items = [it for it in items if it.get("split") == args.split]
    print(f"loaded {len(items)} items for split={args.split}")

    out_path = Path(args.output)
    existing = {}
    if args.resume and out_path.exists():
        for r in json.load(open(out_path)):
            if r.get("anomaly_score") is not None:
                existing[r["item_id"]] = r
    print(f"resume: {len(existing)} existing successful items")
    todo = [it for it in items if it["item_id"] not in existing]
    print(f"running {len(todo)} new items at T={args.temperature} N={args.n_calls}")

    client = get_client(args.backend)
    model = get_model_name(args.backend)

    results = list(existing.values())
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.max_workers) as pool:
        futures = {pool.submit(run_one, client, model, it, args.n_calls, args.temperature): it for it in todo}
        done = 0
        for fut in as_completed(futures):
            r = fut.result()
            results.append(r)
            done += 1
            if done % 50 == 0:
                el = time.time() - t0
                rate = done / el
                eta = (len(todo) - done) / max(rate, 0.001)
                print(f"  {done}/{len(todo)}  rate={rate:.2f}/s  eta={eta/60:.1f}min  errs={sum(1 for r in results if r.get('error'))}")
                # incremental save
                json.dump(results, open(out_path, "w"))

    json.dump(results, open(out_path, "w"))
    n_err = sum(1 for r in results if r.get("error"))
    print(f"done. n={len(results)} errors={n_err} elapsed={(time.time()-t0)/60:.1f}min")
    print(f"saved -> {out_path}")


if __name__ == "__main__":
    main()
