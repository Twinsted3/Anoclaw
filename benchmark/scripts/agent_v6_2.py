"""AnomalyClaw v6.2 — v6 ReAct loop but:
  1. Final output uses {label, confidence} not self-reported score.
  2. Score computed via score_from_v0 (same as Direct baseline).
  3. v6.2 prompt (expert-noise warning, no confidence gating).

Guarantees calibration consistency across systems.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import agent_prompt_v6_2 as _p62
import agent_prompt_v6 as _p6
_p6.SYSTEM_PROMPT = _p62.SYSTEM_PROMPT
_p6.TOOL_CATALOG = _p62.TOOL_CATALOG
_p6.forced_final_prompt = _p62.forced_final_prompt
_p6.budget_warning_prompt = _p62.budget_warning_prompt

import agent_v6 as mod  # noqa: E402
from infer import score_from_v0  # noqa: E402


# Patch the parse_action / final-score computation to use score_from_v0
_orig_parse = mod.ReActAgent._parse_action

def _parse_action_v62(self, text):
    import json as _json
    from infer import extract_json as _ex
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
        # Score via shared mapping so agent and Direct are comparable
        parsed["score"] = score_from_v0({
            "image_label": lbl,
            "confidence": conf,
        })
    else:
        if not parsed.get("tool"):
            return None
    return parsed

mod.ReActAgent._parse_action = _parse_action_v62


from agent_v6 import main  # noqa: E402

if __name__ == "__main__":
    main()
