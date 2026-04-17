"""AnomalyClaw v6.3 — v6 loop + v6.3 prompt (describe refs on turn 1,
anti-false-positive bias) + v6.2 score calibration via score_from_v0.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import agent_prompt_v6_3 as _p63
import agent_prompt_v6 as _p6
_p6.SYSTEM_PROMPT = _p63.SYSTEM_PROMPT
_p6.TOOL_CATALOG = _p63.TOOL_CATALOG
_p6.forced_final_prompt = _p63.forced_final_prompt
_p6.budget_warning_prompt = _p63.budget_warning_prompt

import agent_v6 as mod  # noqa: E402
from infer import score_from_v0  # noqa: E402
from infer import extract_json as _ex  # noqa: E402


def _parse_action_v63(self, text):
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

mod.ReActAgent._parse_action = _parse_action_v63

from agent_v6 import main  # noqa: E402

if __name__ == "__main__":
    main()
