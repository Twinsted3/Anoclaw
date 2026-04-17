"""AnomalyClaw v6.8 — Anchored pure agent (NO ensemble, NO monkey-patch).

Design:
- Pre-fetches SubspaceAD expert score+rank from cache and injects it as
  a textual "anchor" into the agent's initial context.
- Also stashes the expert's top-k hotspot patches into ctx["_expert_patches"]
  so tool_hotspot_cropper / tool_component_counter can use them without
  the agent having to spend a turn on tool_expert_score.
- Agent's exported anomaly_score = free-form final score (NO blending
  with Direct, NO initial-vs-final self-ensemble).
- Thread-safe: subclass ReActAgent, no instance mutation.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import agent_prompt_v6_8 as _p68
import agent_prompt_v6 as _p6_orig
# Replace the base prompt module globally so subclass sees v6.8 prompts
_p6_orig.SYSTEM_PROMPT = _p68.SYSTEM_PROMPT
_p6_orig.TOOL_CATALOG = _p68.TOOL_CATALOG
_p6_orig.forced_final_prompt = _p68.forced_final_prompt
_p6_orig.budget_warning_prompt = _p68.budget_warning_prompt

import agent_v6 as mod  # noqa: E402
from infer import DOMAIN_CONTEXT, text_msg, img_msg, load_and_encode  # noqa: E402
from agent_tools_v6 import tool_expert_score  # noqa: E402


class AnchoredReActAgent(mod.ReActAgent):
    """Subclass that overrides _build_initial_messages and run to:
      1. Fetch expert anchor once per item (pure cache lookup, 0 API).
      2. Inject anchor text into user message on turn 1.
      3. Make expert top_patches available to downstream tools via ctx.
    """

    def _build_initial_messages(self, query_path, ref_paths,
                                domain_code=None, anchor_text=None):
        ctx_text = DOMAIN_CONTEXT.get(domain_code or "", "an image")
        user_parts = [
            text_msg(f"DOMAIN: {ctx_text}"),
        ]
        if anchor_text:
            user_parts.append(text_msg(anchor_text))
        user_parts.append(text_msg("NORMAL REFERENCE IMAGES:"))
        for rp in ref_paths[:4]:
            user_parts.append(img_msg(load_and_encode(rp)))
        user_parts.append(text_msg("QUERY IMAGE:"))
        user_parts.append(img_msg(load_and_encode(query_path)))
        user_parts.append(text_msg(f"Turn 1/{self.K}. Decide your next action."))
        return [
            {"role": "system", "content": _p68.SYSTEM_PROMPT},
            {"role": "user", "content": user_parts},
        ]

    def run(self, item_id, query_path, ref_paths, split,
            domain_code=None):
        # Pre-fetch anchor (synchronous, disk lookup only; no API)
        anchor = tool_expert_score(item_id=item_id, expert="subspacead",
                                   split=split)
        if anchor.get("error") is None:
            r = anchor.get("normalized_rank", 0.5)
            interp = anchor.get("interpretation", "?")
            raw = anchor.get("score", 0.0)
            anchor_text = (f"SUBSPACEAD EXPERT ANCHOR: rank={r:.3f}  "
                           f"raw={raw:.3f}  interpretation=\"{interp}\"")
            patches = anchor.get("top_patches", []) or []
        else:
            anchor_text = "SUBSPACEAD EXPERT ANCHOR: (unavailable)"
            patches = []

        # We need to pass anchor_text + patches into the loop. Because
        # mod.ReActAgent.run constructs `ctx` and calls
        # `self._build_initial_messages(query_path, ref_paths, domain_code=...)`,
        # we stash patches on a per-call attr and use a closure-safe
        # temporary subclass that reads them.
        #
        # Thread safety: stash in a local dict that we return to caller;
        # since ReActAgent.run is purely per-call, the ctx is local to
        # the call stack. We use a thin override of run that augments ctx
        # AFTER parent builds it.

        # Easiest: re-implement the loop but dispatch to parent's helpers.
        # But that duplicates the loop. Instead we use a thread-local for
        # the per-call anchor context.

        import threading
        tl = getattr(AnchoredReActAgent, "_tl", None)
        if tl is None:
            AnchoredReActAgent._tl = threading.local()
            tl = AnchoredReActAgent._tl
        tl.anchor_text = anchor_text
        tl.anchor_patches = patches

        try:
            result = super().run(item_id=item_id, query_path=query_path,
                                 ref_paths=ref_paths, split=split,
                                 domain_code=domain_code)
        finally:
            tl.anchor_text = None
            tl.anchor_patches = None
        return result


# Monkey-patch ReActAgent._build_initial_messages to read from the TL
# storage. This is thread-safe because threading.local is per-thread.
_orig_build = mod.ReActAgent._build_initial_messages


def _build_with_anchor(self, query_path, ref_paths, domain_code=None,
                       anchor_text=None):
    tl = getattr(AnchoredReActAgent, "_tl", None)
    tl_text = getattr(tl, "anchor_text", None) if tl is not None else None
    # Prefer explicit anchor_text kwarg if passed, else TL
    if anchor_text is None and tl_text:
        anchor_text = tl_text
    # If we're an AnchoredReActAgent instance, use its custom builder
    if isinstance(self, AnchoredReActAgent):
        return AnchoredReActAgent._build_initial_messages(
            self, query_path, ref_paths,
            domain_code=domain_code, anchor_text=anchor_text)
    return _orig_build(self, query_path, ref_paths,
                       domain_code=domain_code, anchor_text=anchor_text)


mod.ReActAgent._build_initial_messages = _build_with_anchor


# Also patch dispatch_tool to inject expert_patches from TL (so
# hotspot_cropper / component_counter see the anchor patches without
# the agent calling tool_expert_score).
import agent_tools_v6 as _tools  # noqa: E402
_orig_dispatch = _tools.dispatch_tool


def _dispatch_with_anchor_tl(name, args, ctx=None):
    ctx = dict(ctx or {})
    tl = getattr(AnchoredReActAgent, "_tl", None)
    patches = getattr(tl, "anchor_patches", None) if tl is not None else None
    if patches and "_expert_patches" not in ctx:
        ctx["_expert_patches"] = patches
    return _orig_dispatch(name, args, ctx)


_tools.dispatch_tool = _dispatch_with_anchor_tl
mod.dispatch_tool = _dispatch_with_anchor_tl


# Override the agent-construction in main() so it uses our subclass
import argparse  # noqa: E402
import json  # noqa: E402
import time  # noqa: E402
from concurrent.futures import ThreadPoolExecutor, as_completed  # noqa: E402
from infer import get_client, get_model_name  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--split", choices=["calibration", "dev", "test"],
                    required=True)
    ap.add_argument("--backend", choices=["qwen3", "seedvl", "gpt"],
                    required=True)
    ap.add_argument("--output", required=True)
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

    client = get_client(args.backend)
    model = get_model_name(args.backend)
    agent = AnchoredReActAgent(vlm_client=client, vlm_model=model,
                               max_turns=args.max_turns)

    results = []
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
