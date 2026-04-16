"""
Agent-based inference for AnomaClaw V2.

The main agent dynamically decides which tools to call based on its reasoning.
This is NOT a fixed pipeline — the agent loop adapts per-item.

Usage:
  # V0 baseline (no tools)
  python benchmark/scripts/agent_infer.py --mode baseline --domains D1 D2 ...

  # Retrieval only (V0 + retrieval tool)
  python benchmark/scripts/agent_infer.py --mode retrieval --domains D1 D2 ...

  # Full agent (retrieval + knowledge + multi-round)
  python benchmark/scripts/agent_infer.py --mode agent --domains D1 D2 ...
"""

import argparse
import base64
import json
import os
import sys
import time
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

import cv2
import numpy as np
from openai import OpenAI

# Import tools
sys.path.insert(0, str(Path(__file__).parent))
from agent_tools import tool_visual_retrieval, tool_domain_knowledge

# ─── Image utils ──────────────────────────────────────────────────────────────

def load_and_encode(path: str, max_side: int = 512) -> str:
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(f"Cannot read: {path}")
    h, w = img.shape[:2]
    if max(h, w) > max_side:
        scale = max_side / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)))
    _, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return base64.b64encode(buf).decode("utf-8")


def img_msg(b64): return {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "high"}}
def text_msg(t): return {"type": "text", "text": t}


def extract_json(text):
    if not text: return None
    text = text.strip()
    try: return json.loads(text)
    except: pass
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if m:
        try: return json.loads(m.group(1).strip())
        except: pass
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try: return json.loads(m.group(0))
        except: pass
    return None


# ─── Domain context ──────────────────────────────────────────────────────────

DOMAIN_CONTEXT = {
    "D1": "industrial manufacturing product",
    "D2": "retail product or shelf item",
    "D4": "concrete or infrastructure surface",
    "D5": "dermoscopic image of a skin lesion",
    "D5b": "brain MRI slice",
    "D5c": "liver CT slice",
    "D5d": "gastrointestinal endoscopy image",
    "D7": "road or traffic scene",
    "D9": "assembled product with multiple components (check logical correctness)",
    "D10": "industrial product (PCB, capsule, candle, etc.)",
}

# ─── Scoring ─────────────────────────────────────────────────────────────────

def score_from_response(parsed: Optional[dict]) -> float:
    if not parsed: return 0.5
    label = str(parsed.get("label", parsed.get("image_label", ""))).lower()
    conf = float(parsed.get("confidence", parsed.get("final_confidence", 0.5)))
    if "anomal" in label:
        return max(conf, 0.5 + 1e-6)
    elif "normal" in label:
        return min(1.0 - conf, 0.5 - 1e-6)
    return 0.5


# ─── Mode: Baseline (V0, no tools) ──────────────────────────────────────────

OUTPUT_SCHEMA = """{
  "image_label": "normal" or "anomalous",
  "anomaly_type": "type or null",
  "evidence": "brief description",
  "confidence": float 0-1
}"""


def run_baseline(client, model, item, n_refs=4):
    """V0: Direct comparison, no tools."""
    ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:n_refs]]
    query_img = load_and_encode(item["query_path"])
    ctx = DOMAIN_CONTEXT.get(item["domain_code"], "image")

    content = []
    for b64 in ref_imgs:
        content.append(text_msg("Normal reference:"))
        content.append(img_msg(b64))
    content.append(text_msg("Query image:"))
    content.append(img_msg(query_img))
    content.append(text_msg(
        f"You are inspecting a {ctx}. The reference images show the normal state.\n"
        f"Decide whether the query image is normal or anomalous.\n"
        f"Return JSON only:\n{OUTPUT_SCHEMA}"
    ))

    t0 = time.time()
    resp = client.chat.completions.create(model=model, messages=[{"role": "user", "content": content}],
                                           max_tokens=500, temperature=0.0)
    text = resp.choices[0].message.content or ""
    latency = time.time() - t0
    parsed = extract_json(text)

    return {
        "anomaly_score": score_from_response(parsed),
        "raw_output": {"method": "baseline", "response": parsed},
        "cost_tokens": {"input": resp.usage.prompt_tokens, "output": resp.usage.completion_tokens},
        "latency_sec": round(latency, 2),
    }


# ─── Mode: Retrieval (V0 + visual retrieval tool) ───────────────────────────

def run_retrieval(client, model, item, n_refs=4):
    """V0 + retrieval: use DINOv2 to find best refs, then direct comparison."""
    # Tool call: visual retrieval
    retrieved = tool_visual_retrieval(item["query_path"], item["domain_code"], k=n_refs)
    if not retrieved:
        # Fallback to manifest refs
        return run_baseline(client, model, item, n_refs)

    ref_paths = [path for path, sim in retrieved]
    ref_imgs = [load_and_encode(p) for p in ref_paths]
    query_img = load_and_encode(item["query_path"])
    ctx = DOMAIN_CONTEXT.get(item["domain_code"], "image")

    content = []
    for i, b64 in enumerate(ref_imgs):
        content.append(text_msg(f"Normal reference {i+1} (retrieved by visual similarity):"))
        content.append(img_msg(b64))
    content.append(text_msg("Query image:"))
    content.append(img_msg(query_img))
    content.append(text_msg(
        f"You are inspecting a {ctx}. The reference images are the most visually "
        f"similar normal samples to the query.\n"
        f"Decide whether the query image is normal or anomalous.\n"
        f"Return JSON only:\n{OUTPUT_SCHEMA}"
    ))

    t0 = time.time()
    resp = client.chat.completions.create(model=model, messages=[{"role": "user", "content": content}],
                                           max_tokens=500, temperature=0.0)
    text = resp.choices[0].message.content or ""
    latency = time.time() - t0
    parsed = extract_json(text)

    return {
        "anomaly_score": score_from_response(parsed),
        "raw_output": {
            "method": "retrieval",
            "retrieved_refs": [(p, round(s, 3)) for p, s in retrieved],
            "response": parsed,
        },
        "cost_tokens": {"input": resp.usage.prompt_tokens, "output": resp.usage.completion_tokens},
        "latency_sec": round(latency, 2),
    }


# ─── Mode: Full Agent (retrieval + knowledge + multi-round) ─────────────────

AGENT_SYSTEM_PROMPT = """You are an anomaly detection agent. You have access to tools and domain knowledge.

Your task: determine if the query image is normal or anomalous.

You will receive:
1. Retrieved reference images (most similar normal samples)
2. Domain-specific knowledge (what anomalies look like in this domain)

Reasoning process:
1. Study the reference images to understand what NORMAL looks like
2. Compare the query image to the references
3. Use domain knowledge to distinguish genuine anomalies from normal variation
4. Make your final judgment

Return JSON only:
{
  "reasoning": "step-by-step reasoning",
  "image_label": "normal" or "anomalous",
  "anomaly_type": "type or null",
  "evidence": "specific visual evidence for your decision",
  "confidence": float 0-1
}"""


def _build_knowledge_text(knowledge):
    if not knowledge:
        return ""
    text = f"\n--- Domain Knowledge: {knowledge.get('domain', '')} ---\n"
    text += f"Normal: {knowledge.get('normal', '')}\n"
    text += "Anomaly criteria:\n"
    for c in knowledge.get("anomaly_criteria", []):
        text += f"  - {c}\n"
    text += "Common false positives (do NOT flag these):\n"
    for fp in knowledge.get("common_false_positives", []):
        text += f"  - {fp}\n"
    return text


def _adaptive_k(sims, base_k=4):
    """Decide how many refs to use based on retrieval similarity."""
    if not sims:
        return base_k
    top1 = sims[0]
    if top1 > 0.95:
        return 2   # very good match, 2 refs enough
    elif top1 > 0.85:
        return 3
    else:
        return base_k  # need all k refs


def run_agent(client, model, item, n_refs=4):
    """Full agent: adaptive retrieval + knowledge + multi-round reasoning."""
    domain_code = item["domain_code"]
    ctx = DOMAIN_CONTEXT.get(domain_code, "image")

    # Tool 1: Visual retrieval (always retrieve, let similarity guide k)
    retrieved = tool_visual_retrieval(item["query_path"], domain_code, k=n_refs)
    sims = [s for _, s in retrieved] if retrieved else []
    k_actual = _adaptive_k(sims, n_refs)

    if retrieved:
        ref_paths = [path for path, sim in retrieved[:k_actual]]
    else:
        ref_paths = item["ref_paths"][:n_refs]
        sims = []

    # Tool 2: Domain knowledge
    knowledge = tool_domain_knowledge(domain_code)
    knowledge_text = _build_knowledge_text(knowledge)

    # Build retrieval context for the agent
    retrieval_info = ""
    if sims:
        retrieval_info = (
            f"\n--- Retrieval Info ---\n"
            f"Top-{k_actual} refs retrieved (DINOv2 cosine similarity):\n"
        )
        for i, (p, s) in enumerate(retrieved[:k_actual]):
            retrieval_info += f"  ref{i+1}: similarity={s:.3f}\n"
        avg_sim = np.mean(sims[:k_actual])
        retrieval_info += (
            f"Average similarity: {avg_sim:.3f}\n"
            f"Interpretation: {'refs match query well' if avg_sim > 0.9 else 'refs are moderately similar' if avg_sim > 0.75 else 'refs may not match query well — be cautious'}\n"
        )

    # Build message
    ref_imgs = [load_and_encode(p) for p in ref_paths]
    query_img = load_and_encode(item["query_path"])

    content = []
    for i, b64 in enumerate(ref_imgs):
        content.append(text_msg(f"Normal reference {i+1}:"))
        content.append(img_msg(b64))
    content.append(text_msg("Query image (classify this):"))
    content.append(img_msg(query_img))
    content.append(text_msg(
        f"You are an anomaly detection agent inspecting a {ctx}.\n"
        f"{retrieval_info}"
        f"{knowledge_text}\n"
        f"{AGENT_SYSTEM_PROMPT}"
    ))

    t0 = time.time()
    resp = client.chat.completions.create(model=model, messages=[{"role": "user", "content": content}],
                                           max_tokens=800, temperature=0.0)
    text = resp.choices[0].message.content or ""
    latency = time.time() - t0
    parsed = extract_json(text)
    score = score_from_response(parsed)
    inp_total = resp.usage.prompt_tokens
    out_total = resp.usage.completion_tokens
    n_rounds = 1

    # Round 2: if refs didn't match well, try alternative refs
    if sims and np.mean(sims[:k_actual]) < 0.75:
        # Low similarity — refs may not be representative, retry with manifest refs
        alt_paths = item["ref_paths"][:n_refs]
        alt_imgs = [load_and_encode(p) for p in alt_paths]

        content2 = []
        for i, b64 in enumerate(alt_imgs):
            content2.append(text_msg(f"Alternative reference {i+1} (random from training set):"))
            content2.append(img_msg(b64))
        content2.append(text_msg("Same query image:"))
        content2.append(img_msg(query_img))
        content2.append(text_msg(
            f"The retrieved references had low similarity ({np.mean(sims[:k_actual]):.2f}). "
            f"Here are random references from the training set for a second opinion.\n"
            f"{knowledge_text}\n"
            f"Make your final judgment.\n"
            f"Return JSON only:\n{OUTPUT_SCHEMA}"
        ))

        resp2 = client.chat.completions.create(model=model, messages=[{"role": "user", "content": content2}],
                                                 max_tokens=500, temperature=0.0)
        text2 = resp2.choices[0].message.content or ""
        parsed2 = extract_json(text2)
        score2 = score_from_response(parsed2)
        inp_total += resp2.usage.prompt_tokens
        out_total += resp2.usage.completion_tokens
        latency = time.time() - t0
        n_rounds = 2

        # Average both rounds
        score = (score + score2) / 2
        parsed = {"round1": parsed, "round2": parsed2, "final_score": score}

    return {
        "anomaly_score": score,
        "raw_output": {
            "method": "agent",
            "k_actual": k_actual,
            "retrieval_sims": [round(s, 3) for s in sims[:k_actual]],
            "n_rounds": n_rounds,
            "knowledge_used": bool(knowledge),
            "response": parsed,
        },
        "cost_tokens": {"input": inp_total, "output": out_total},
        "latency_sec": round(latency, 2),
    }


# ─── Runner ──────────────────────────────────────────────────────────────────

MODE_FNS = {
    "baseline": run_baseline,
    "retrieval": run_retrieval,
    "agent": run_agent,
}


def run_item(item, client, model, mode, n_refs):
    fn = MODE_FNS[mode]
    base = {
        "item_id": item["item_id"],
        "domain": item["domain"],
        "domain_code": item["domain_code"],
        "label_gt": item["label"],
        "split": item["split"],
        "source_dataset": item.get("source_dataset"),
        "category": item.get("category"),
    }
    try:
        result = fn(client, model, item, n_refs)
        base["label_pred"] = 1 if result["anomaly_score"] > 0.5 else 0
        base.update(result)
        base["error"] = None
    except Exception as e:
        base.update({
            "label_pred": 0, "anomaly_score": 0.5, "anomaly_type_pred": None,
            "raw_output": None, "cost_tokens": {"input": 0, "output": 0},
            "latency_sec": 0.0, "error": str(e),
        })
    return base


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="/hdd1/jiangxi/AD-Agent/benchmark/manifests/full_manifest.json")
    parser.add_argument("--split", default="test")
    parser.add_argument("--mode", required=True, choices=list(MODE_FNS.keys()))
    parser.add_argument("--output", required=True)
    parser.add_argument("--domains", nargs="*", default=None)
    parser.add_argument("--n_refs", type=int, default=4)
    parser.add_argument("--max_workers", type=int, default=4)
    parser.add_argument("--max_items", type=int, default=None)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    with open(args.manifest) as f:
        all_items = json.load(f)

    items = [x for x in all_items
             if (args.split == "all" or x["split"] == args.split)
             and (args.domains is None or x["domain_code"] in args.domains)]

    if args.max_items:
        items = items[:args.max_items]

    existing = {}
    if args.resume and Path(args.output).exists():
        with open(args.output) as f:
            for r in json.load(f):
                existing[r["item_id"]] = r
        items = [x for x in items if x["item_id"] not in existing]
        print(f"Resuming: {len(existing)} done, {len(items)} remaining")

    # Setup client
    api_key = os.environ.get("GPT_API_KEY")
    base_url = os.environ.get("GPT_API_BASE")
    if not api_key:
        api_key = "***REDACTED-GPT-KEY***"
        base_url = "http://localhost:8080/v1"
    model = os.environ.get("GPT_MODEL", "gpt-5.4")
    client = OpenAI(api_key=api_key, base_url=base_url, timeout=120.0)

    print(f"Running {len(items)} items | mode={args.mode} | model={model} | n_refs={args.n_refs}")

    results = list(existing.values())
    errors = 0

    from tqdm import tqdm

    def process(item):
        return run_item(item, client, model, args.mode, args.n_refs)

    with ThreadPoolExecutor(max_workers=args.max_workers) as pool:
        futures = {pool.submit(process, item): item for item in items}
        for fut in tqdm(as_completed(futures), total=len(futures), desc=f"{args.mode}"):
            r = fut.result()
            results.append(r)
            if r.get("error"):
                errors += 1
            if len(results) % 20 == 0:
                Path(args.output).parent.mkdir(parents=True, exist_ok=True)
                with open(args.output, "w") as f:
                    json.dump(results, f, indent=2)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)

    total_in = sum((r.get("cost_tokens") or {}).get("input", 0) for r in results)
    total_out = sum((r.get("cost_tokens") or {}).get("output", 0) for r in results)
    print(f"\nDone: {len(results)} items, {errors} errors")
    print(f"Tokens — input: {total_in:,} | output: {total_out:,}")
    print(f"Results saved: {args.output}")


if __name__ == "__main__":
    main()
