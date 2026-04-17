"""AnomalyClaw v6.4 — B-regime: agent gets the same one-sentence domain
hint that Direct gets (DOMAIN_CONTEXT[domain_code]).

Rebuilds initial messages to inject the hint.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import agent_prompt_v6_4 as _p64
import agent_prompt_v6 as _p6
_p6.SYSTEM_PROMPT = _p64.SYSTEM_PROMPT
_p6.TOOL_CATALOG = _p64.TOOL_CATALOG
_p6.forced_final_prompt = _p64.forced_final_prompt
_p6.budget_warning_prompt = _p64.budget_warning_prompt

import agent_v6 as mod  # noqa: E402
from infer import DOMAIN_CONTEXT, score_from_v0, extract_json as _ex  # noqa: E402
from infer import text_msg, img_msg, load_and_encode  # noqa: E402


def _build_init_v64(self, query_path, ref_paths, _domain_code):
    """Override: include domain hint as text."""
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
        {"role": "system", "content": _p6.SYSTEM_PROMPT},
        {"role": "user", "content": user_parts},
    ]


# Monkey-patch: run() needs domain_code so it can pass to _build_init.
# The existing v6 run() accepts domain_code kwarg, so we just need to change
# _build_initial_messages to accept domain_code. Easiest: wrap run().

_orig_run = mod.ReActAgent.run

def run_v64(self, item_id, query_path, ref_paths, split, domain_code=None):
    # Override the builder for this run
    original_builder = self._build_initial_messages
    self._build_initial_messages = lambda qp, rp: _build_init_v64(self, qp, rp, domain_code)
    try:
        result = _orig_run(self, item_id=item_id, query_path=query_path,
                           ref_paths=ref_paths, split=split,
                           domain_code=domain_code)
    finally:
        self._build_initial_messages = original_builder
    return result

mod.ReActAgent.run = run_v64


def _parse_action_v64(self, text):
    parsed = _ex(text)
    if not isinstance(parsed, dict):
        return None
    action = parsed.get("action")
    if action not in ("call_tool", "final"):
        return None
    if action == "final":
        lbl = str(parsed.get("label", "")).lower()
        if lbl not in ("normal", "anomalous"):
            return None
        try:
            conf = float(parsed.get("confidence", 0))
        except (TypeError, ValueError):
            return None
        parsed["score"] = score_from_v0({
            "image_label": lbl, "confidence": conf,
        })
    else:
        if not parsed.get("tool"):
            return None
    return parsed

mod.ReActAgent._parse_action = _parse_action_v64

from agent_v6 import main  # noqa: E402

if __name__ == "__main__":
    main()
