"""AnomalyClaw v6.6 — self-ensemble agent.

Elegant replacement for post-hoc `0.5*(direct + agent)`:
  * On turn 1 the VLM emits an `initial_score` (its gut call) alongside
    the regular action. This is equivalent to the Direct VLM's output.
  * After optional tool rounds, the VLM emits a `final_score`.
  * The system blends: `anomaly_score = 0.5 * (initial_score + final_score)`.

The agent's exported `anomaly_score` IS the ensemble. No external step.

CLI identical to `agent_v6.py`.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Register v6.6 prompt BEFORE importing v6
import agent_prompt_v6_6 as _p66
import agent_prompt_v6 as _p6
_p6.SYSTEM_PROMPT = _p66.SYSTEM_PROMPT
_p6.TOOL_CATALOG = _p66.TOOL_CATALOG
_p6.forced_final_prompt = _p66.forced_final_prompt
_p6.budget_warning_prompt = _p66.budget_warning_prompt

import agent_v6 as mod  # noqa: E402
from agent_v6 import AgentResult  # noqa: E402
from infer import (  # noqa: E402
    DOMAIN_CONTEXT, call_llm, extract_json, img_msg, load_and_encode, text_msg,
)


def _build_init_v66(self, query_path, ref_paths, _domain_code):
    """Same as v6.4 builder: inject DOMAIN_CONTEXT at top of user message."""
    ctx_text = DOMAIN_CONTEXT.get(_domain_code, "an image")
    user_parts = [
        text_msg(f"DOMAIN: {ctx_text}"),
        text_msg("NORMAL REFERENCE IMAGES:"),
    ]
    for rp in ref_paths[:4]:
        user_parts.append(img_msg(load_and_encode(rp)))
    user_parts.append(text_msg("QUERY IMAGE:"))
    user_parts.append(img_msg(load_and_encode(query_path)))
    user_parts.append(text_msg(f"Turn 1/{self.K}. Remember: on turn 1 include "
                                "`initial_score`. Decide next action."))
    return [
        {"role": "system", "content": _p66.SYSTEM_PROMPT},
        {"role": "user", "content": user_parts},
    ]


def _parse_action_v66(self, text, *, require_initial: bool = False):
    """Like v6's parse_action, but also extract `initial_score` if present
    (used only on turn 1)."""
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
    if require_initial:
        init = parsed.get("initial_score")
        if init is None:
            return None
        try:
            parsed["initial_score"] = float(init)
        except (TypeError, ValueError):
            return None
    return parsed


def run_v66(self, item_id: str, query_path: str, ref_paths: list,
            split: str, domain_code: str | None = None) -> AgentResult:
    """ReAct loop that also tracks `initial_score` from turn 1 and blends
    it with `final_score` to form the ensemble output."""
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
    messages = _build_init_v66(self, query_path, ref_paths, domain_code)
    history, tools_used = [], []
    initial_score: float | None = None

    for turn in range(1, self.K + 1):
        first_turn = (turn == 1)
        # Turn 1 must include initial_score
        attempts = 1 + self.json_retries
        cur = list(messages)
        parsed = None
        for _ in range(attempts):
            try:
                text, _, _ = call_llm(self.client, self.model, cur,
                                      max_tokens=self.max_tokens,
                                      temperature=0.0)
            except Exception:
                break
            parsed = _parse_action_v66(self, text, require_initial=first_turn)
            if parsed is not None:
                break
            cur = cur + [{
                "role": "user",
                "content": (
                    "Your last response was not valid JSON. Return one JSON "
                    "object with the required fields" +
                    (" INCLUDING `initial_score`." if first_turn else ".")
                ),
            }]

        if parsed is None:
            return AgentResult(
                item_id=item_id, score=0.5, rationale="json parse failed",
                n_turns=turn, tools_used=tools_used, history=history,
                confidence=0, error="malformed JSON after retries",
            )

        if first_turn:
            initial_score = float(parsed["initial_score"])

        if parsed["action"] == "final":
            final_score = max(0.0, min(1.0, float(parsed["score"])))
            # Ensemble
            ensemble = (
                0.5 * (initial_score + final_score)
                if initial_score is not None else final_score
            )
            r = AgentResult(
                item_id=item_id,
                score=ensemble,
                rationale=str(parsed.get("rationale", ""))[:500],
                n_turns=turn, tools_used=tools_used,
                history=history + [{"turn": turn, "action": "final",
                                    "initial_score": initial_score,
                                    "final_score": final_score,
                                    "ensemble_score": ensemble,
                                    "rationale": parsed.get("rationale", "")[:200]}],
                confidence=int(parsed.get("confidence", 0) or 0),
            )
            return r

        # Forced final at t=K
        if turn == self.K:
            messages.append({"role": "assistant",
                             "content": json.dumps({"action": parsed["action"],
                                                    "tool": parsed.get("tool")})})
            messages.append({"role": "user",
                             "content": _p66.forced_final_prompt(self.K)})
            # Call one more time for a forced final
            try:
                text, _, _ = call_llm(self.client, self.model, messages,
                                      max_tokens=self.max_tokens,
                                      temperature=0.0)
                forced = _parse_action_v66(self, text, require_initial=False)
            except Exception:
                forced = None
            if forced and forced.get("action") == "final":
                final_score = max(0.0, min(1.0, float(forced["score"])))
                ensemble = (0.5 * (initial_score + final_score)
                            if initial_score is not None else final_score)
                return AgentResult(
                    item_id=item_id,
                    score=ensemble,
                    rationale=str(forced.get("rationale", ""))[:500],
                    n_turns=self.K, tools_used=tools_used,
                    history=history + [{"turn": turn, "action": "forced_final",
                                        "initial_score": initial_score,
                                        "final_score": final_score,
                                        "ensemble_score": ensemble}],
                    confidence=int(forced.get("confidence", 0) or 0),
                )
            return AgentResult(
                item_id=item_id,
                score=initial_score if initial_score is not None else 0.5,
                rationale="forced-final failed; fell back to initial_score",
                n_turns=self.K, tools_used=tools_used, history=history,
                confidence=0, error="forced-final produced non-final",
            )

        # Execute tool
        tool_name = parsed["tool"]
        tool_args = parsed.get("args") or {}
        from agent_tools_v6 import dispatch_tool
        observation = dispatch_tool(tool_name, tool_args, ctx)
        tools_used.append(tool_name)
        history.append({"turn": turn, "action": "call_tool", "tool": tool_name,
                        "obs_keys": list(observation.keys()),
                        "obs_error": observation.get("error")})
        if tool_name == "tool_expert_score":
            ctx["_expert_patches"] = observation.get("top_patches", [])

        obs_parts = []
        obs_text = mod._obs_to_text(observation)
        obs_parts.append(text_msg(f"OBSERVATION from {tool_name}: {obs_text}"))
        for img_key in ("crop_b64", "diff_mask_b64", "aligned_diff_b64",
                        "composite_b64"):
            if observation.get(img_key):
                obs_parts.append(img_msg(observation[img_key]))
        if observation.get("tiles"):
            for t in observation["tiles"][:9]:
                obs_parts.append(img_msg(t["crop_b64"]))
        remaining = self.K - turn
        obs_parts.append(text_msg(
            f"Turn {turn+1}/{self.K}. "
            f"{_p66.budget_warning_prompt(remaining)}\n"
            "Decide your next action."))
        messages.append({"role": "assistant",
                         "content": json.dumps({"action": parsed["action"],
                                                "tool": parsed.get("tool")})})
        messages.append({"role": "user", "content": obs_parts})

    # Should not reach
    return AgentResult(
        item_id=item_id, score=initial_score or 0.5,
        rationale="loop exhausted", n_turns=self.K, tools_used=tools_used,
        history=history, confidence=0, error="loop exhausted",
    )


mod.ReActAgent.run = run_v66

from agent_v6 import main  # noqa: E402

if __name__ == "__main__":
    main()
