"""
AnomaClaw Agent V3: Tool-augmented agent with dynamic tool dispatch.

Main Agent decides which tools to call based on its reasoning:
  - Always: DINOv2 retrieval for refs
  - Always: Normality Profile (build normal understanding)
  - Agent decides: call Scout+Judge for uncertain cases, or direct judgment for clear cases

Modes:
  baseline    — random refs, direct judgment (V0)
  retrieval   — DINOv2 refs, direct judgment
  agent       — DINOv2 refs + profile + agent-dispatched scout/judge
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

sys.path.insert(0, str(Path(__file__).parent))
from agent_tools import tool_visual_retrieval, tool_expert_ad_score

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

def call_llm(client, model, content, max_tokens=700):
    resp = client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": content}],
        max_tokens=max_tokens, temperature=0.0)
    text = resp.choices[0].message.content or ""
    return text, resp.usage.prompt_tokens, resp.usage.completion_tokens

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

def score_from_response(parsed):
    if not parsed: return 0.5
    label = str(parsed.get("label", parsed.get("image_label", parsed.get("final_label", "")))).lower()
    conf = float(parsed.get("confidence", parsed.get("final_confidence", 0.5)))
    if "anomal" in label:
        return max(conf, 0.5 + 1e-6)
    elif "normal" in label:
        return min(1.0 - conf, 0.5 - 1e-6)
    return 0.5

OUTPUT_SCHEMA = """{
  "image_label": "normal" or "anomalous",
  "anomaly_type": "type or null",
  "evidence": "brief description",
  "confidence": float 0-1
}"""

# ─── Tool: Normality Profile ────────────────────────────────────────────────

_profile_cache = {}

PROFILE_SCHEMA = """{
  "normal_patterns": [
    {"pattern": "visual characteristic shared across references", "evidence_refs": [1, 2]}
  ],
  "benign_variations": [
    {"variation": "variation that is still normal", "evidence_refs": [2, 4]}
  ]
}"""


def tool_normality_profile(client, model, ref_paths, domain_code):
    """Build normality profile from reference images. Cached per ref set."""
    key = tuple(sorted(ref_paths))
    if key in _profile_cache:
        return _profile_cache[key]

    ref_imgs = [load_and_encode(p) for p in ref_paths]
    ctx = DOMAIN_CONTEXT.get(domain_code, "image")

    content = []
    for i, b64 in enumerate(ref_imgs):
        content.append(text_msg(f"Normal reference {i+1}/{len(ref_imgs)}:"))
        content.append(img_msg(b64))
    content.append(text_msg(
        f"You are analyzing {len(ref_imgs)} NORMAL reference images of a {ctx} domain.\n"
        f"Build a normality profile: what do these references have in common, "
        f"and what variations between them are still normal.\n"
        f"Each item must cite which reference images support it (1-indexed).\n"
        f"Return JSON only:\n{PROFILE_SCHEMA}"
    ))

    text, inp, out = call_llm(client, model, content, max_tokens=800)
    parsed = extract_json(text)
    profile_json = json.dumps(parsed, indent=2) if parsed else text

    result = {"json": profile_json, "parsed": parsed, "cost": (inp, out)}
    _profile_cache[key] = result
    return result


# ─── Tool: Scout (find anomaly candidates) ───────────────────────────────────

SCOUT_SCHEMA = """{
  "candidates": [
    {"id": "C1", "description": "concrete deviation found", "location": "where", "confidence": float 0-1}
  ],
  "no_difference_conf": float 0-1
}"""


def tool_scout(client, model, ref_paths, query_path, domain_code):
    """High-recall anomaly candidate finder. Calls expert model first, then VLM analysis."""
    # Sub-tool: expert AD score
    expert = tool_expert_ad_score(query_path, domain_code)

    ref_imgs = [load_and_encode(p) for p in ref_paths]
    query_img = load_and_encode(query_path)
    ctx = DOMAIN_CONTEXT.get(domain_code, "image")

    expert_info = (
        f"\n--- Expert Model Signal ---\n"
        f"DINOv2 few-shot AD score: {expert['anomaly_score']} "
        f"(top1_sim={expert['top1_similarity']}, {expert['interpretation']})\n"
        f"Use this as a reference signal, but make your own visual judgment.\n"
    )

    content = []
    for i, b64 in enumerate(ref_imgs):
        content.append(text_msg(f"Normal reference {i+1}:"))
        content.append(img_msg(b64))
    content.append(text_msg("QUERY image:"))
    content.append(img_msg(query_img))
    content.append(text_msg(
        f"You are a discrepancy scout examining a {ctx}.\n"
        f"{expert_info}\n"
        f"Find ALL concrete deviations in the query that are absent from the references.\n"
        f"Do NOT decide normal/anomalous. Just list what you find.\n"
        f"Missing a real deviation is worse than over-reporting.\n"
        f"Return JSON only:\n{SCOUT_SCHEMA}"
    ))

    text, inp, out = call_llm(client, model, content, max_tokens=600)
    parsed = extract_json(text)
    return {"parsed": parsed, "expert": expert, "cost": (inp, out)}


# ─── Tool: Judge (evaluate candidates with profile) ─────────────────────────

JUDGE_SCHEMA = """{
  "per_candidate": [
    {"id": "C1", "is_anomaly": true or false, "reasoning": "why"}
  ],
  "final_label": "normal" or "anomalous",
  "final_confidence": float 0-1
}"""


def tool_judge(client, model, ref_paths, query_path, profile_json, scout_json, domain_code):
    """Evaluate scout candidates using normality profile for grounding."""
    ref_imgs = [load_and_encode(p) for p in ref_paths[:2]]  # only 2 refs to save tokens
    query_img = load_and_encode(query_path)

    content = []
    for i, b64 in enumerate(ref_imgs):
        content.append(text_msg(f"Reference {i+1}:"))
        content.append(img_msg(b64))
    content.append(text_msg("Query:"))
    content.append(img_msg(query_img))
    content.append(text_msg(
        f"You are the anomaly judge.\n\n"
        f"Normality profile (what is normal in this domain):\n{profile_json}\n\n"
        f"Scout report (candidate deviations found):\n{scout_json}\n\n"
        f"For each candidate, decide if it is a genuine anomaly or explainable "
        f"by normal_patterns/benign_variations in the profile.\n"
        f"Return JSON only:\n{JUDGE_SCHEMA}"
    ))

    text, inp, out = call_llm(client, model, content, max_tokens=600)
    parsed = extract_json(text)
    return {"parsed": parsed, "cost": (inp, out)}


# ─── Mode: Baseline ─────────────────────────────────────────────────────────

def run_baseline(client, model, item, n_refs=4):
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
    text, inp, out = call_llm(client, model, content)
    parsed = extract_json(text)
    return {
        "anomaly_score": score_from_response(parsed),
        "raw_output": {"method": "baseline", "response": parsed},
        "cost_tokens": {"input": inp, "output": out},
        "latency_sec": round(time.time() - t0, 2),
    }


# ─── Mode: Retrieval ────────────────────────────────────────────────────────

def run_retrieval(client, model, item, n_refs=4):
    retrieved = tool_visual_retrieval(item["query_path"], item["domain_code"], k=n_refs)
    if not retrieved:
        return run_baseline(client, model, item, n_refs)

    ref_paths = [p for p, s in retrieved]
    ref_imgs = [load_and_encode(p) for p in ref_paths]
    query_img = load_and_encode(item["query_path"])
    ctx = DOMAIN_CONTEXT.get(item["domain_code"], "image")

    content = []
    for i, b64 in enumerate(ref_imgs):
        content.append(text_msg(f"Normal reference {i+1}:"))
        content.append(img_msg(b64))
    content.append(text_msg("Query image:"))
    content.append(img_msg(query_img))
    content.append(text_msg(
        f"You are inspecting a {ctx}. The reference images are the most visually "
        f"similar normal samples.\n"
        f"Decide whether the query image is normal or anomalous.\n"
        f"Return JSON only:\n{OUTPUT_SCHEMA}"
    ))

    t0 = time.time()
    text, inp, out = call_llm(client, model, content)
    parsed = extract_json(text)
    return {
        "anomaly_score": score_from_response(parsed),
        "raw_output": {"method": "retrieval", "retrieved": [(p, round(s,3)) for p,s in retrieved], "response": parsed},
        "cost_tokens": {"input": inp, "output": out},
        "latency_sec": round(time.time() - t0, 2),
    }


# ─── Mode: Agent (main agent dispatches tools) ──────────────────────────────

AGENT_DISPATCH_SCHEMA = """{
  "initial_assessment": "normal" or "anomalous" or "uncertain",
  "confidence": float 0-1,
  "needs_detailed_inspection": true or false,
  "reasoning": "why you need or don't need detailed inspection"
}"""


def run_agent(client, model, item, n_refs=4):
    """Agent V3: retrieval + profile + agent-dispatched scout/judge."""
    t0 = time.time()
    domain_code = item["domain_code"]
    ctx = DOMAIN_CONTEXT.get(domain_code, "image")
    inp_total, out_total = 0, 0

    # Step 1: Retrieval (always)
    retrieved = tool_visual_retrieval(item["query_path"], domain_code, k=n_refs)
    if retrieved:
        ref_paths = [p for p, s in retrieved]
        sims = [s for _, s in retrieved]
    else:
        ref_paths = item["ref_paths"][:n_refs]
        sims = []

    # Step 2: Normality Profile (always, cached)
    profile = tool_normality_profile(client, model, ref_paths, domain_code)
    p_inp, p_out = profile["cost"]
    # Amortize profile cost
    inp_total += p_inp // 20
    out_total += p_out // 20

    # Step 3: Main Agent — initial assessment with profile context
    ref_imgs = [load_and_encode(p) for p in ref_paths]
    query_img = load_and_encode(item["query_path"])

    content = []
    for i, b64 in enumerate(ref_imgs):
        content.append(text_msg(f"Normal reference {i+1}:"))
        content.append(img_msg(b64))
    content.append(text_msg("Query image:"))
    content.append(img_msg(query_img))
    content.append(text_msg(
        f"You are an anomaly detection agent inspecting a {ctx}.\n\n"
        f"Normality profile (what normal looks like):\n{profile['json']}\n\n"
        f"Make an initial assessment. If you are confident (>0.85), give your final answer.\n"
        f"If uncertain, set needs_detailed_inspection=true and I will run Scout+Judge tools.\n\n"
        f"Return JSON only:\n{AGENT_DISPATCH_SCHEMA}"
    ))

    text, inp, out = call_llm(client, model, content, max_tokens=400)
    inp_total += inp; out_total += out
    dispatch = extract_json(text)

    initial = str((dispatch or {}).get("initial_assessment", "uncertain")).lower()
    conf = float((dispatch or {}).get("confidence", 0.5))
    needs_detail = (dispatch or {}).get("needs_detailed_inspection", True)

    # If agent is confident, return directly
    if not needs_detail and conf >= 0.8:
        score = score_from_response({"image_label": initial, "confidence": conf})
        return {
            "anomaly_score": score,
            "raw_output": {
                "method": "agent", "path": "direct",
                "dispatch": dispatch, "n_tools": 1,
                "retrieval_sims": [round(s,3) for s in sims],
            },
            "cost_tokens": {"input": inp_total, "output": out_total},
            "latency_sec": round(time.time() - t0, 2),
        }

    # Step 4: Scout (high recall, no profile)
    scout = tool_scout(client, model, ref_paths, item["query_path"], domain_code)
    s_inp, s_out = scout["cost"]
    inp_total += s_inp; out_total += s_out
    scout_parsed = scout["parsed"]

    candidates = (scout_parsed or {}).get("candidates", [])
    no_diff = float((scout_parsed or {}).get("no_difference_conf", 0.5))

    # If scout found nothing, trust that
    if not candidates and no_diff > 0.7:
        return {
            "anomaly_score": min(1.0 - no_diff, 0.5 - 1e-6),
            "raw_output": {
                "method": "agent", "path": "scout_clear",
                "dispatch": dispatch, "scout": scout_parsed, "n_tools": 2,
                "retrieval_sims": [round(s,3) for s in sims],
            },
            "cost_tokens": {"input": inp_total, "output": out_total},
            "latency_sec": round(time.time() - t0, 2),
        }

    # Step 5: Judge (with profile, evaluates scout candidates)
    scout_json = json.dumps(scout_parsed, indent=2) if scout_parsed else "{}"
    judge = tool_judge(client, model, ref_paths, item["query_path"],
                       profile["json"], scout_json, domain_code)
    j_inp, j_out = judge["cost"]
    inp_total += j_inp; out_total += j_out
    judge_parsed = judge["parsed"]

    score = score_from_response(judge_parsed)

    return {
        "anomaly_score": score,
        "raw_output": {
            "method": "agent", "path": "full_pipeline",
            "dispatch": dispatch, "scout": scout_parsed, "judge": judge_parsed,
            "n_tools": 3,
            "retrieval_sims": [round(s,3) for s in sims],
        },
        "cost_tokens": {"input": inp_total, "output": out_total},
        "latency_sec": round(time.time() - t0, 2),
    }


# ─── Runner ──────────────────────────────────────────────────────────────────

MODE_FNS = {"baseline": run_baseline, "retrieval": run_retrieval, "agent": run_agent}


def run_item(item, client, model, mode, n_refs):
    fn = MODE_FNS[mode]
    base = {
        "item_id": item["item_id"], "domain": item["domain"],
        "domain_code": item["domain_code"], "label_gt": item["label"],
        "split": item["split"], "source_dataset": item.get("source_dataset"),
        "category": item.get("category"),
    }
    try:
        result = fn(client, model, item, n_refs)
        base["label_pred"] = 1 if result["anomaly_score"] > 0.5 else 0
        base.update(result)
        base["error"] = None
    except Exception as e:
        base.update({"label_pred": 0, "anomaly_score": 0.5, "raw_output": None,
                      "cost_tokens": {"input": 0, "output": 0}, "latency_sec": 0.0, "error": str(e)})
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

    api_key = os.environ.get("GPT_API_KEY")
    base_url = os.environ.get("GPT_API_BASE")
    if not api_key:
        api_key = "***REDACTED-GPT-KEY***"
        base_url = "http://localhost:8080/v1"
    model = os.environ.get("GPT_MODEL", "gpt-5.4")
    client = OpenAI(api_key=api_key, base_url=base_url, timeout=120.0)

    print(f"Running {len(items)} items | mode={args.mode} | model={model}")

    results = list(existing.values())
    from tqdm import tqdm

    with ThreadPoolExecutor(max_workers=args.max_workers) as pool:
        futures = {pool.submit(run_item, item, client, model, args.mode, args.n_refs): item for item in items}
        for fut in tqdm(as_completed(futures), total=len(futures), desc=args.mode):
            r = fut.result()
            results.append(r)
            if len(results) % 20 == 0:
                Path(args.output).parent.mkdir(parents=True, exist_ok=True)
                with open(args.output, "w") as f:
                    json.dump(results, f, indent=2)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)

    errors = sum(1 for r in results if r.get("error"))
    print(f"\nDone: {len(results)} items, {errors} errors")
    print(f"Results saved: {args.output}")


if __name__ == "__main__":
    main()
