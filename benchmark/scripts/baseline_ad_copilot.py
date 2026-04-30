"""
AD-Copilot baseline runner over manifests_v2 test split.

AD-Copilot (Jiang et al., arXiv 2603.13779) is a Qwen2.5-VL-7B that has
been fine-tuned for industrial anomaly detection with a dedicated
comparison encoder. We feed it (1 reference, query) and ask a yes/no
question; the anomaly score is the softmax probability of "Yes" over
{"Yes","No"} taken from the logits at the first generated token.

This converts AD-Copilot's text output into a continuous score so it
can be evaluated with the same AUROC metric as the other baselines.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

import torch
from PIL import Image
from tqdm import tqdm
from transformers import AutoModelForImageTextToText, AutoProcessor

DEFAULT_PROMPT = (
    "The first image is a normal reference. The second image is the test image. "
    "Looking carefully at the test image and comparing to the reference, is there an anomaly, "
    "defect, or unusual pattern in the test image? Answer with a single word: Yes or No."
)


def load_image(path, max_edge=512):
    img = Image.open(path).convert("RGB")
    if max_edge > 0:
        img.thumbnail((max_edge, max_edge), Image.Resampling.LANCZOS)
    return img


def build_inputs(processor, ref_path, query_path, prompt, device, max_edge):
    ref_img = load_image(ref_path, max_edge)
    q_img = load_image(query_path, max_edge)
    messages = [{
        "role": "user",
        "content": [
            {"type": "image", "image": ref_img},
            {"type": "image", "image": q_img},
            {"type": "text", "text": prompt},
        ],
    }]
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    try:
        from qwen_vl_utils import process_vision_info
        image_inputs, video_inputs = process_vision_info(messages)
    except ImportError:
        image_inputs, video_inputs = [ref_img, q_img], None
    inputs = processor(text=[text], images=image_inputs, videos=video_inputs,
                       padding=True, return_tensors="pt").to(device)
    return inputs


@torch.inference_mode()
def score_yes_no(model, processor, ref_path, query_path, prompt, device, max_edge,
                 yes_id, no_id):
    inputs = build_inputs(processor, ref_path, query_path, prompt, device, max_edge)
    out = model.generate(
        **inputs, max_new_tokens=1, do_sample=False,
        output_scores=True, return_dict_in_generate=True,
    )
    logits = out.scores[0][0]  # [vocab]
    pair = torch.stack([logits[yes_id], logits[no_id]])
    p = torch.softmax(pair, dim=-1)
    return float(p[0].item()), int(out.sequences[0, -1].item())


def find_token_id(processor, candidates):
    """Return id of the first candidate that tokenizes to a single token."""
    tok = processor.tokenizer
    for cand in candidates:
        ids = tok.encode(cand, add_special_tokens=False)
        if len(ids) == 1:
            return ids[0], cand
    # fall back to first candidate's leading id
    cand = candidates[0]
    return tok.encode(cand, add_special_tokens=False)[0], cand


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--split", default="test")
    ap.add_argument("--output", required=True)
    ap.add_argument("--model_path", default="/hdd1/jiangxi/AD-Copilot/AD-Copilot")
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--max_edge", type=int, default=512)
    ap.add_argument("--prompt", default=DEFAULT_PROMPT)
    ap.add_argument("--n_refs", type=int, default=1,
                    help="how many ref images to use; n>1 runs n (ref_i,query) "
                         "passes and averages P(Yes) — AD-Copilot was trained on "
                         "single-pair comparison so we ensemble at the score level.")
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    items = json.load(open(args.manifest))
    if args.split:
        items = [x for x in items if x.get("split") == args.split]

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = {}
    if args.resume and out_path.exists():
        try:
            done = {r["item_id"]: r for r in json.load(open(out_path))}
            print(f"[resume] {len(done)} already done")
        except Exception:
            done = {}

    print(f"Loading AD-Copilot from {args.model_path} on {args.device}")
    try:
        import flash_attn  # noqa: F401
        attn_impl = "flash_attention_2"
    except ImportError:
        attn_impl = "sdpa"
    print(f"attn_impl={attn_impl}")

    processor = AutoProcessor.from_pretrained(
        args.model_path, min_pixels=64*28*28, max_pixels=1280*28*28,
        trust_remote_code=True,
    )
    model = AutoModelForImageTextToText.from_pretrained(
        args.model_path, torch_dtype=torch.bfloat16,
        attn_implementation=attn_impl, device_map=args.device,
        trust_remote_code=True,
    ).eval()

    yes_id, yes_tok = find_token_id(processor, [" Yes", "Yes", " yes", "yes"])
    no_id, no_tok = find_token_id(processor, [" No", "No", " no", "no"])
    print(f"Yes token id={yes_id} ({yes_tok!r}), No token id={no_id} ({no_tok!r})")

    results = list(done.values())
    pending = [it for it in items if it["item_id"] not in done]
    print(f"Manifest items={len(items)}, pending={len(pending)}")

    t0 = time.time()
    for it in tqdm(pending, desc="AD-Copilot"):
        try:
            refs = it.get("ref_paths") or [it["query_path"]]
            refs = refs[:max(1, args.n_refs)]
            ps, gens = [], []
            for ref_path in refs:
                s, gen_id = score_yes_no(
                    model, processor, ref_path, it["query_path"],
                    args.prompt, args.device, args.max_edge, yes_id, no_id,
                )
                ps.append(s); gens.append(gen_id)
            mean_s = float(sum(ps) / len(ps))
            results.append({
                "item_id": it["item_id"],
                "domain_code": it.get("domain_code"),
                "split": it.get("split"),
                "label": it.get("label"),
                "anomaly_score": mean_s,
                "per_ref_scores": ps,
                "label_pred": int(mean_s > 0.5),
                "gen_token_ids": gens,
                "n_refs": len(refs),
                "error": None,
            })
        except Exception as e:
            results.append({
                "item_id": it["item_id"],
                "domain_code": it.get("domain_code"),
                "split": it.get("split"),
                "label": it.get("label"),
                "anomaly_score": None,
                "label_pred": None,
                "error": f"{type(e).__name__}: {e}",
            })
        if len(results) % 25 == 0:
            json.dump(results, open(out_path, "w"))

    json.dump(results, open(out_path, "w"))
    print(f"[done] wrote {len(results)} items in {time.time()-t0:.1f}s -> {out_path}")


if __name__ == "__main__":
    main()
