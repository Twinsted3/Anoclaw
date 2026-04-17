"""AnomalyClaw v6.7 — agent with integrated Direct + ReAct ensemble.

Unified runner: produces one result JSON whose `anomaly_score` is already
the ensemble of Direct and Agent final.

Direct source (controlled by --direct_cache):
  - If --direct_cache <path> is given AND the file exists, reads each item's
    direct score from there (no extra API call → rate-limit safe).
  - Otherwise, performs a fresh Direct VLM call per item as "turn 0"
    BEFORE running ReAct. Be aware on API backends this doubles your
    request rate; use `--max_workers` half of what you'd give pure agent.

The exported `anomaly_score` = 0.5 * (direct_score + agent_final_score).
If either is missing, falls back to the one available.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import agent_prompt_v6 as _p6

import agent_v6 as mod  # noqa: E402
from agent_v6 import ReActAgent, AgentResult, _summarise, _obs_to_text  # noqa: E402
from infer import (  # noqa: E402
    DOMAIN_CONTEXT, build_prompt_v0, call_llm, extract_json, get_client,
    get_model_name, img_msg, load_and_encode, score_from_v0, text_msg,
)

SYSTEM_PROMPT = _p6.SYSTEM_PROMPT


def _build_init_v67(self, query_path, ref_paths, _domain_code):
    ctx_text = DOMAIN_CONTEXT.get(_domain_code, "an image")
    user_parts = [
        text_msg(f"DOMAIN: {ctx_text}"),
        text_msg("NORMAL REFERENCE IMAGES:"),
    ]
    for rp in ref_paths[:4]:
        user_parts.append(img_msg(load_and_encode(rp)))
    user_parts.append(text_msg("QUERY IMAGE:"))
    user_parts.append(img_msg(load_and_encode(query_path)))
    user_parts.append(text_msg(f"Turn 1/{self.K}. Decide your next action."))
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_parts},
    ]


def _direct_turn0_call(client, model, query_path, ref_paths, domain_code,
                       max_retries: int = 2) -> float | None:
    for attempt in range(max_retries + 1):
        try:
            messages = [
                {"role": "system",
                 "content": "You are a visual anomaly inspector. Return JSON only."},
                {"role": "user", "content": (
                    [text_msg(build_prompt_v0(domain_code or "D?", has_refs=True))] +
                    [img_msg(load_and_encode(p)) for p in ref_paths[:4]] +
                    [text_msg("QUERY:"), img_msg(load_and_encode(query_path))]
                )},
            ]
            text, _, _ = call_llm(client, model, messages,
                                  max_tokens=500, temperature=0.0)
            parsed = extract_json(text)
            if parsed is None:
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                    continue
                return None
            return float(score_from_v0(parsed))
        except Exception:
            if attempt < max_retries:
                time.sleep(2 ** attempt)
                continue
            return None
    return None


# Re-bind the builder on each run
_orig_run = mod.ReActAgent.run


def _run_ensemble(self, item_id, query_path, ref_paths, split, domain_code,
                  direct_score_cached):
    # Turn 0: Direct VLM (cached or fresh)
    if direct_score_cached is not None:
        direct_score = direct_score_cached
    else:
        direct_score = _direct_turn0_call(
            self.client, self.model, query_path, ref_paths, domain_code)

    # Turn 1..K: ReAct
    original_builder = self._build_initial_messages
    self._build_initial_messages = lambda qp, rp, **_kw: _build_init_v67(
        self, qp, rp, domain_code)
    try:
        r = _orig_run(self, item_id=item_id, query_path=query_path,
                      ref_paths=ref_paths, split=split,
                      domain_code=domain_code)
    finally:
        self._build_initial_messages = original_builder

    agent_score = r.score
    # Blend; fall back gracefully
    if direct_score is not None and r.error is None:
        ensemble = 0.5 * (direct_score + agent_score)
    elif direct_score is not None:  # agent errored
        ensemble = direct_score
    else:  # direct failed
        ensemble = agent_score
    r.score = float(max(0.0, min(1.0, ensemble)))
    return r, direct_score


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--split", choices=["calibration", "test"], required=True)
    ap.add_argument("--backend", choices=["qwen3", "seedvl", "gpt"], required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--direct_cache", default=None,
                    help="path to a v6_direct_*_test.json — if set, load direct "
                         "scores from there instead of calling VLM.")
    ap.add_argument("--domains", nargs="*", default=None)
    ap.add_argument("--max_turns", type=int, default=5)
    ap.add_argument("--max_workers", type=int, default=8)
    ap.add_argument("--max_items", type=int, default=0)
    args = ap.parse_args()

    items = json.load(open(args.manifest))
    items = [x for x in items if x.get("split") == args.split]
    if args.domains:
        items = [x for x in items if x.get("domain_code") in args.domains]
    if args.max_items:
        items = items[:args.max_items]

    direct_cache = {}
    if args.direct_cache and os.path.exists(args.direct_cache):
        raw = json.load(open(args.direct_cache))
        for x in (raw if isinstance(raw, list) else list(raw.values())):
            iid = x.get("item_id")
            s = x.get("anomaly_score")
            if iid is not None and s is not None:
                direct_cache[iid] = float(s)
        print(f"[cache] loaded {len(direct_cache)} cached direct scores")

    client = get_client(args.backend)
    model = get_model_name(args.backend)
    agent = ReActAgent(vlm_client=client, vlm_model=model,
                       max_turns=args.max_turns)

    results = []
    t0 = time.time()

    def _run_one(x):
        try:
            r, ds = _run_ensemble(
                agent, x["item_id"], x["query_path"], x["ref_paths"],
                args.split, x.get("domain_code"),
                direct_cache.get(x["item_id"]))
            return {
                "item_id": x["item_id"], "domain_code": x.get("domain_code"),
                "label_gt": x.get("label"), "anomaly_score": r.score,
                "direct_score": ds,
                "agent_final_score": None if r.error else r.score,  # actually agent score pre-blend; override below
                "rationale": r.rationale, "n_turns": r.n_turns,
                "tools_used": r.tools_used, "confidence": r.confidence,
                "error": r.error,
            }
        except Exception as e:
            return {"item_id": x["item_id"], "domain_code": x.get("domain_code"),
                    "label_gt": x.get("label"), "anomaly_score": 0.5,
                    "n_turns": 0, "tools_used": [], "confidence": 0,
                    "error": f"{type(e).__name__}: {e}"}

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=args.max_workers) as ex:
        futures = [ex.submit(_run_one, x) for x in items]
        for i, fut in enumerate(as_completed(futures)):
            results.append(fut.result())
            if (i + 1) % 25 == 0:
                with open(args.output, "w") as f:
                    json.dump(results, f)
                print(f"[{i+1}/{len(items)}] {time.time()-t0:.1f}s  "
                      f"written={len(results)}", flush=True)

    with open(args.output, "w") as f:
        json.dump(results, f)
    print(f"Wrote {len(results)} results → {args.output}")


if __name__ == "__main__":
    main()
