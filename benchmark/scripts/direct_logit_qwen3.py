#!/usr/bin/env python3
"""Direct@logit baseline.

For each test item: ask a binary yes/no question with `logprobs=True,
top_logprobs=20`, extract the first-token logprob of the tokens
matching " yes" / " no" (case-insensitive, with optional leading space),
and compute score = softmax([logit_yes, logit_no])[0].

This gives a continuous anomaly probability from a single call, without
relying on the model's self-reported confidence.
"""
import argparse
import json
import math
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "benchmark/scripts"))

from infer import (
    N_REFS, get_client, get_model_name, img_msg, label_from_score,
    load_and_encode, text_msg
)


PROMPT = (
    "You are a visual anomaly inspector. The first image(s) show normal "
    "reference state, the last image is the query.\n"
    "Question: Is the query image anomalous compared to the references?\n"
    "Answer with exactly one word: yes or no."
)


def call_logit(client, model, item, max_tokens=2):
    ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:N_REFS]]
    query_img = load_and_encode(item["query_path"])
    content = []
    for b64 in ref_imgs:
        content.append(text_msg("Normal reference:"))
        content.append(img_msg(b64))
    content.append(text_msg("Query image:"))
    content.append(img_msg(query_img))
    content.append(text_msg(PROMPT))

    kwargs = dict(
        model=model,
        messages=[{"role": "user", "content": content}],
        max_tokens=max_tokens,
        temperature=0.0,
        logprobs=True,
        top_logprobs=20,
    )
    if "qwen3" in str(model).lower() or "Qwen3" in str(model):
        kwargs["extra_body"] = {"chat_template_kwargs": {"enable_thinking": False}}

    resp = client.chat.completions.create(**kwargs)
    text = resp.choices[0].message.content or ""
    # Extract first-token top_logprobs
    lp_struct = resp.choices[0].logprobs
    if lp_struct is None or not lp_struct.content:
        return {"score": 0.5, "raw_text": text, "logits": None, "first_top": None}

    first_token = lp_struct.content[0]
    top = first_token.top_logprobs  # list of {token, logprob}
    # Find logit for tokens matching yes/no (case-insensitive, with optional leading whitespace)
    logit_yes = None
    logit_no = None
    for entry in top:
        tok = entry.token.strip().lower()
        if tok in ("yes",):
            if logit_yes is None or entry.logprob > logit_yes:
                logit_yes = entry.logprob
        elif tok in ("no",):
            if logit_no is None or entry.logprob > logit_no:
                logit_no = entry.logprob

    # If only one of yes/no was in top-20, use a fallback (very low logprob for the missing one)
    if logit_yes is None and logit_no is None:
        # neither in top-20: fallback to text parse
        s = 1.0 if text.strip().lower().startswith("yes") else 0.0
        return {"score": s, "raw_text": text, "logits": None, "first_top": [(e.token, e.logprob) for e in top[:8]]}
    if logit_yes is None:
        score = 1.0 / (1.0 + math.exp(logit_no - (-30.0)))  # min logprob ≈ -30
        logit_yes = -30.0
    elif logit_no is None:
        score = 1.0 / (1.0 + math.exp(-30.0 - logit_yes))
        logit_no = -30.0
    else:
        # softmax of [logit_yes, logit_no]
        m = max(logit_yes, logit_no)
        ey = math.exp(logit_yes - m)
        en = math.exp(logit_no - m)
        score = ey / (ey + en)

    return {
        "score": float(score),
        "raw_text": text,
        "logit_yes": logit_yes,
        "logit_no": logit_no,
        "first_top": [(e.token, e.logprob) for e in top[:8]],
    }


def run_one(client, model, item):
    try:
        r = call_logit(client, model, item)
        return {
            "item_id": item.get("item_id"),
            "domain": item.get("domain"),
            "domain_code": item.get("domain_code"),
            "label_gt": item.get("label"),
            "split": item.get("split"),
            "label_pred": label_from_score(r["score"]) if r["score"] is not None else None,
            "anomaly_score": r["score"],
            "raw_text": r["raw_text"],
            "logit_yes": r.get("logit_yes"),
            "logit_no": r.get("logit_no"),
            "first_top": r.get("first_top"),
            "error": None,
        }
    except Exception as e:
        return {
            "item_id": item.get("item_id"),
            "domain_code": item.get("domain_code"),
            "label_gt": item.get("label"),
            "anomaly_score": None,
            "error": f"{type(e).__name__}: {e}",
        }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--split", default="test")
    ap.add_argument("--backend", choices=["gpt", "seedvl", "qwen3"], required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--max_workers", type=int, default=24)
    args = ap.parse_args()

    items = json.load(open(args.manifest))
    if isinstance(items, dict) and "items" in items:
        items = items["items"]
    items = [it for it in items if it.get("split") == args.split]
    print(f"loaded {len(items)} items split={args.split}")

    client = get_client(args.backend)
    model = get_model_name(args.backend)
    out_path = Path(args.output)
    results = []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.max_workers) as pool:
        futs = {pool.submit(run_one, client, model, it): it for it in items}
        done = 0
        for f in as_completed(futs):
            results.append(f.result())
            done += 1
            if done % 50 == 0:
                rate = done / (time.time() - t0)
                eta = (len(items) - done) / max(rate, 0.001)
                errs = sum(1 for r in results if r.get("error"))
                print(f"  {done}/{len(items)}  rate={rate:.2f}/s  eta={eta/60:.1f}min  errs={errs}")
                json.dump(results, open(out_path, "w"))
    json.dump(results, open(out_path, "w"))
    n_err = sum(1 for r in results if r.get("error"))
    print(f"done. n={len(results)}  errors={n_err}  elapsed={(time.time()-t0)/60:.1f}min")
    print(f"saved -> {out_path}")


if __name__ == "__main__":
    main()
