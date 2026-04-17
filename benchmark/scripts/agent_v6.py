"""AnomalyClaw v6 — per-item autonomous ReAct agent.

Usage:
  python benchmark/scripts/agent_v6.py \
    --manifest benchmark/manifests_v2/full_manifest.json \
    --split test --backend qwen3 \
    --output benchmark/results/v6_agent_qwen3_test.json \
    --max_turns 5 --max_workers 8
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from infer import (  # noqa: E402
    call_llm, extract_json, get_client, get_model_name,
    img_msg, load_and_encode, text_msg,
)
from agent_prompt_v6 import (  # noqa: E402
    SYSTEM_PROMPT, budget_warning_prompt, forced_final_prompt,
)
from agent_tools_v6 import dispatch_tool, TOOL_REGISTRY  # noqa: E402


@dataclass
class AgentResult:
    item_id: str
    score: float
    rationale: str
    n_turns: int
    tools_used: list
    history: list
    confidence: int
    error: str | None = None


class ReActAgent:
    def __init__(self, vlm_client, vlm_model: str, max_turns: int = 5,
                 json_retries: int = 1, max_tokens: int = 600):
        self.client = vlm_client
        self.model = vlm_model
        self.K = max_turns
        self.json_retries = json_retries
        self.max_tokens = max_tokens

    # ──────────────────────────────────────────────────────────────────
    def _build_initial_messages(self, query_path: str,
                                ref_paths: list,
                                domain_code: str | None = None,
                                anchor_text: str | None = None) -> list:
        """Builder is called with per-item kwargs; no instance mutation.
        Subclasses override by subclassing, not by monkey-patching.

        Args:
            domain_code: forwarded for variants that want to inject
                DOMAIN_CONTEXT[d] at call time.
            anchor_text: free-form extra preamble (used by anchored
                variants to pass precomputed expert signals).
        """
        user_parts = []
        if anchor_text:
            user_parts.append(text_msg(anchor_text))
        user_parts.append(text_msg("NORMAL REFERENCE IMAGES:"))
        for rp in ref_paths[:4]:
            user_parts.append(img_msg(load_and_encode(rp)))
        user_parts.append(text_msg("QUERY IMAGE:"))
        user_parts.append(img_msg(load_and_encode(query_path)))
        user_parts.append(text_msg(f"Turn 1/{self.K}. Decide your next action."))
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_parts},
        ]

    def _parse_action(self, text: str) -> dict | None:
        parsed = extract_json(text)
        if not isinstance(parsed, dict):
            return None
        action = parsed.get("action")
        if action not in ("call_tool", "final"):
            return None
        if action == "final":
            s = parsed.get("score")
            if s is None:
                return None
            try:
                parsed["score"] = float(s)
            except (TypeError, ValueError):
                return None
        else:
            if not parsed.get("tool"):
                return None
        return parsed

    def _call_with_json_retry(self, messages: list) -> dict | None:
        attempts = 1 + self.json_retries
        cur = list(messages)
        for _ in range(attempts):
            try:
                text, _, _ = call_llm(self.client, self.model, cur,
                                      max_tokens=self.max_tokens,
                                      temperature=0.0)
            except Exception:
                return None
            parsed = self._parse_action(text)
            if parsed is not None:
                return parsed
            cur = cur + [{
                "role": "user",
                "content": "Your last response was not valid JSON. "
                           "Return a single JSON object with fields "
                           "{thought, action, tool, args, confidence, "
                           "score, rationale}.",
            }]
        return None

    # ──────────────────────────────────────────────────────────────────
    def run(self, item_id: str, query_path: str, ref_paths: list,
            split: str, domain_code: str | None = None) -> AgentResult:
        ctx = {
            "query_path": query_path,
            "ref_paths": ref_paths,
            "item_id": item_id,
            "split": split,
            "vlm_client": self.client,
            "vlm_model": self.model,
            "llm_client": self.client,
            "llm_model": self.model,
            "_manifest_domain": domain_code,
        }
        messages = self._build_initial_messages(query_path, ref_paths,
                                                domain_code=domain_code)
        history, tools_used = [], []

        for turn in range(1, self.K + 1):
            action = self._call_with_json_retry(messages)
            if action is None:
                return AgentResult(
                    item_id=item_id, score=0.5, rationale="json parse failed",
                    n_turns=turn, tools_used=tools_used, history=history,
                    confidence=0, error="malformed JSON after retries",
                )

            if action["action"] == "final":
                return AgentResult(
                    item_id=item_id,
                    score=max(0.0, min(1.0, float(action["score"]))),
                    rationale=str(action.get("rationale", ""))[:500],
                    n_turns=turn, tools_used=tools_used,
                    history=history + [{"turn": turn, **_summarise(action)}],
                    confidence=int(action.get("confidence", 0) or 0),
                )

            if turn == self.K:
                # Budget exhausted; force a final in one more sub-call.
                messages.append({"role": "assistant",
                                 "content": json.dumps(_summarise(action))})
                messages.append({"role": "user",
                                 "content": forced_final_prompt(self.K)})
                forced = self._call_with_json_retry(messages)
                if forced and forced.get("action") == "final":
                    return AgentResult(
                        item_id=item_id,
                        score=max(0.0, min(1.0, float(forced["score"]))),
                        rationale=str(forced.get("rationale", ""))[:500],
                        n_turns=self.K, tools_used=tools_used,
                        history=history + [
                            {"turn": turn, **_summarise(action)},
                            {"turn": turn, **_summarise(forced)},
                        ],
                        confidence=int(forced.get("confidence", 0) or 0),
                    )
                return AgentResult(
                    item_id=item_id, score=0.5, rationale="forced-final failed",
                    n_turns=self.K, tools_used=tools_used, history=history,
                    confidence=0, error="forced-final produced non-final",
                )

            # Execute tool
            tool_name = action["tool"]
            tool_args = action.get("args") or {}
            observation = dispatch_tool(tool_name, tool_args, ctx)
            tools_used.append(tool_name)
            history.append({"turn": turn, **_summarise(action),
                            "obs_keys": list(observation.keys()),
                            "obs_error": observation.get("error")})

            # Stash expert patches for hotspot/counter tools
            if tool_name == "tool_expert_score":
                ctx["_expert_patches"] = observation.get("top_patches", [])

            # Feed observation back — include image if present, text otherwise
            obs_parts = []
            obs_text = _obs_to_text(observation)
            obs_parts.append(text_msg(
                f"OBSERVATION from {tool_name}: {obs_text}"))
            for img_key in ("crop_b64", "diff_mask_b64", "aligned_diff_b64",
                            "composite_b64"):
                if observation.get(img_key):
                    obs_parts.append(img_msg(observation[img_key]))
            if observation.get("tiles"):
                for t in observation["tiles"][:9]:
                    obs_parts.append(img_msg(t["crop_b64"]))
            remaining = self.K - turn
            obs_parts.append(text_msg(
                f"Turn {turn + 1}/{self.K}. "
                f"{budget_warning_prompt(remaining)}\n"
                f"Decide your next action."))
            messages.append({"role": "assistant",
                             "content": json.dumps(_summarise(action))})
            messages.append({"role": "user", "content": obs_parts})

        return AgentResult(
            item_id=item_id, score=0.5, rationale="loop exhausted",
            n_turns=self.K, tools_used=tools_used, history=history,
            confidence=0, error="loop exhausted without final",
        )


def _summarise(action: dict) -> dict:
    """Drop large args/rationale for history storage."""
    out = {k: v for k, v in action.items()
           if k not in ("args",) or v is None or len(str(v)) < 500}
    if "args" in action and "args" not in out:
        out["args"] = str(action["args"])[:400]
    return out


def _obs_to_text(obs: dict) -> str:
    """Compact text summary of an observation (no base64 payloads)."""
    small = {}
    for k, v in obs.items():
        if k.endswith("_b64"):
            small[k] = f"<{len(v)}-char image>"
        elif k == "tiles":
            small[k] = f"<{len(v)} tiles attached>"
        elif k == "top_patches":
            small[k] = f"<{len(v)} patches>"
        else:
            small[k] = v
    return json.dumps(small, default=str)[:1500]


# ── CLI entry ──────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--split", choices=["calibration", "test"], required=True)
    ap.add_argument("--backend", choices=["qwen3", "seedvl", "gpt"], required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--domains", nargs="*", default=None)
    ap.add_argument("--max_turns", type=int, default=5)
    ap.add_argument("--max_workers", type=int, default=8)
    ap.add_argument("--max_items", type=int, default=0)
    ap.add_argument("--resume", action="store_true",
                    help="skip items already present in --output")
    args = ap.parse_args()

    items = json.load(open(args.manifest))
    items = [x for x in items if x.get("split") == args.split]
    if args.domains:
        items = [x for x in items if x.get("domain_code") in args.domains]
    if args.max_items:
        items = items[:args.max_items]

    done_ids: set = set()
    prev: list = []
    if args.resume and os.path.exists(args.output):
        prev = json.load(open(args.output))
        done_ids = {r["item_id"] for r in prev if r.get("error") is None}
        items = [x for x in items if x["item_id"] not in done_ids]
        print(f"[resume] {len(done_ids)} already done; {len(items)} remaining")

    client = get_client(args.backend)
    model = get_model_name(args.backend)
    agent = ReActAgent(vlm_client=client, vlm_model=model,
                       max_turns=args.max_turns)

    results: list = list(prev)
    t0 = time.time()

    def _run_one(x):
        try:
            r = agent.run(item_id=x["item_id"], query_path=x["query_path"],
                          ref_paths=x["ref_paths"], split=args.split,
                          domain_code=x.get("domain_code"))
            return {
                "item_id": x["item_id"], "domain_code": x.get("domain_code"),
                "label_gt": x.get("label"), "anomaly_score": r.score,
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
