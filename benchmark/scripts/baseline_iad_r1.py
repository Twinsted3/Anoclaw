"""
IAD-R1 baseline runner over manifests_v2 test split.

IAD-R1 (Li et al., arXiv 2508.09178) is a GRPO post-trained Qwen2.5-VL
that emits `<think>...</think><answer>Yes/No</answer>`. We score with a
continuous P(Yes) by:

  1. generate() freely up to max_new_tokens with output_scores=True;
  2. locate the position immediately after `<answer>` in the generated
     sequence;
  3. take softmax over (Yes, No) logits at that position.

If the model fails to emit `<answer>` (parse failure), we fall back to
scanning the whole output and counting yes/no, defaulting to 0.5.
"""
import argparse
import json
import os
import sys
import time
import re
from pathlib import Path

import torch
from PIL import Image
from tqdm import tqdm
from transformers import AutoModelForImageTextToText, AutoProcessor

DEFAULT_PROMPT = (
    "The first image is a normal reference. The second image is the test image. "
    "Are there any defects, anomalies, or unusual patterns in the test image?\n"
    "Output your reasoning between <think>...</think> and your final answer "
    "between <answer>Yes</answer> or <answer>No</answer>."
)


def load_image(path, max_edge=512):
    img = Image.open(path).convert("RGB")
    if max_edge > 0:
        img.thumbnail((max_edge, max_edge), Image.Resampling.LANCZOS)
    return img


def build_inputs(processor, ref_path, query_path, prompt, device, max_edge):
    """If ref_path is None, build a zero-shot prompt with only the query image
    (matches IAD-R1's native --few_shot_model 0 protocol)."""
    q_img = load_image(query_path, max_edge)
    if ref_path is None:
        content = [
            {"type": "image", "image": q_img},
            {"type": "text", "text": prompt},
        ]
        images = [q_img]
    else:
        ref_img = load_image(ref_path, max_edge)
        content = [
            {"type": "image", "image": ref_img},
            {"type": "image", "image": q_img},
            {"type": "text", "text": prompt},
        ]
        images = [ref_img, q_img]
    messages = [{"role": "user", "content": content}]
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    try:
        from qwen_vl_utils import process_vision_info
        image_inputs, _ = process_vision_info(messages)
    except ImportError:
        image_inputs = images
    inputs = processor(text=[text], images=image_inputs,
                       padding=True, return_tensors="pt").to(device)
    return inputs


_ANSWER_TOK = 9217  # 'answer' subword in Qwen2.5 BPE vocab
_LT_OPEN = {27, 1784}  # '<' (standalone) or '><' (merged from previous tag close)
_LT_CLOSE = 522        # '</'
_GT = 29               # '>'
_GT_NO = 41157         # '>No'  (BPE-merged shortcut for the No answer)


def find_answer_idx(new_tokens):
    """Return the index of the `answer` token (9217) in the OPENING
    `<answer>` tag, or None if not found. Robust to the BPE quirk where
    `<` after a closing tag like `</think>` is fused into a single token
    1784 (`><`)."""
    nt = new_tokens.tolist() if hasattr(new_tokens, "tolist") else list(new_tokens)
    for i in range(1, len(nt)):
        if nt[i] == _ANSWER_TOK and nt[i-1] in _LT_OPEN:
            return i
    return None


@torch.inference_mode()
def score_iad_r1(model, processor, ref_path, query_path, prompt, device,
                 max_edge, max_new_tokens):
    inputs = build_inputs(processor, ref_path, query_path, prompt, device, max_edge)
    out = model.generate(
        **inputs, max_new_tokens=max_new_tokens, do_sample=False,
        output_scores=True, return_dict_in_generate=True,
    )
    seq = out.sequences[0]
    n_input = inputs.input_ids.shape[1]
    new_tokens = seq[n_input:]
    text = processor.tokenizer.decode(new_tokens, skip_special_tokens=False)

    ans_idx = find_answer_idx(new_tokens)
    pos = (ans_idx + 1) if ans_idx is not None else None
    # `pos` is the index where the model decides the post-`<answer` token,
    # which is either `41157` (`>No`, merged) for the No path or `29` (`>`)
    # for the Yes path (since `>Yes` is NOT BPE-merged in this vocab).
    if pos is not None and pos < len(out.scores):
        L = out.scores[pos][0]
        yes_path = L[_GT].item()       # `>` opens the Yes path (>Yes follows)
        no_path = L[_GT_NO].item()     # `>No` is the direct No-shortcut
        m = max(yes_path, no_path)
        py = pow(2.71828182846, yes_path - m)
        pn = pow(2.71828182846, no_path - m)
        score = py / (py + pn)
        return float(score), text, "logits"

    # fallback: parse <answer>X</answer> from full decoded text
    m = re.search(r"<answer>\s*(yes|no)", text, re.IGNORECASE)
    if m:
        ans = m.group(1).lower()
        return (0.95 if ans == "yes" else 0.05), text, "parsed"
    return 0.5, text, "none"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--split", default="test")
    ap.add_argument("--output", required=True)
    ap.add_argument("--model_path", required=True,
                    help="path to IAD-R1 checkpoint dir")
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--max_edge", type=int, default=512)
    ap.add_argument("--prompt", default=DEFAULT_PROMPT)
    ap.add_argument("--n_refs", type=int, default=1)
    ap.add_argument("--max_new_tokens", type=int, default=200)
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

    print(f"Loading IAD-R1 from {args.model_path} on {args.device}")
    try:
        import flash_attn  # noqa: F401
        attn_impl = "flash_attention_2"
    except ImportError:
        attn_impl = "sdpa"

    processor = AutoProcessor.from_pretrained(
        args.model_path, min_pixels=64*28*28, max_pixels=1280*28*28,
        trust_remote_code=True,
    )
    model = AutoModelForImageTextToText.from_pretrained(
        args.model_path, torch_dtype=torch.bfloat16,
        attn_implementation=attn_impl, device_map=args.device,
        trust_remote_code=True,
    ).eval()

    print(f"using BPE-aware <answer> opener search (yes_path=tok 29, no_path=tok 41157)")

    results = list(done.values())
    pending = [it for it in items if it["item_id"] not in done]
    print(f"Manifest items={len(items)}, pending={len(pending)}, n_refs={args.n_refs}")

    t0 = time.time()
    for it in tqdm(pending, desc="IAD-R1"):
        try:
            if args.n_refs <= 0:
                # zero-shot: query only, matches IAD-R1's native --few_shot_model 0
                refs = [None]
            else:
                refs = (it.get("ref_paths") or [it["query_path"]])[:args.n_refs]
            ps, srcs, texts = [], [], []
            for ref_path in refs:
                s, t, src = score_iad_r1(
                    model, processor, ref_path, it["query_path"],
                    args.prompt, args.device, args.max_edge,
                    args.max_new_tokens,
                )
                ps.append(s); srcs.append(src); texts.append(t[:300])
            mean_s = float(sum(ps) / len(ps))
            results.append({
                "item_id": it["item_id"],
                "domain_code": it.get("domain_code"),
                "split": it.get("split"),
                "label": it.get("label"),
                "anomaly_score": mean_s,
                "per_ref_scores": ps,
                "label_pred": int(mean_s > 0.5),
                "score_source": srcs,
                "n_refs": len(refs) if args.n_refs > 0 else 0,
                "raw_texts": texts,
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
