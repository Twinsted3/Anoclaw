"""AnomalyClaw v6.7 — agent with integrated Direct "turn 0" pass.

Data insight from v6.6: post-hoc ensemble of agent + Direct VLM beats
self-ensemble where agent emits both `initial_score` and `final_score`
inside a single prompt. The initial_score in v6.6 had to share prompt
space with the action/tool selection, which degraded its calibration
(especially on Qwen3.5).

v6.7 runs a proper Direct VLM call (`build_prompt_v0`) on turn 0 FIRST,
then runs the full v6.5 ReAct loop (domain hint, free-form score).
The agent's exported `anomaly_score` = 0.5 * (direct_score + agent_final_score).

From the user's perspective this is a single self-contained agent — the
ensemble is invisible.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Use v6 prompt (same as v6.5)
import agent_prompt_v6 as _p6

import agent_v6 as mod  # noqa: E402
from agent_v6 import AgentResult  # noqa: E402
from infer import (  # noqa: E402
    DOMAIN_CONTEXT, build_prompt_v0, call_llm, extract_json, img_msg,
    load_and_encode, score_from_v0, text_msg,
)

SYSTEM_PROMPT = _p6.SYSTEM_PROMPT


def _build_init_v67(self, query_path, ref_paths, _domain_code):
    """Same as v6.5: inject DOMAIN_CONTEXT hint; reuse v6 system prompt."""
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


def _direct_turn0(self, query_path, ref_paths, domain_code) -> float | None:
    """A dedicated Direct VLM call with `build_prompt_v0` — same as the
    Direct baseline. Produces a calibrated anomaly score independent of
    the agent's ReAct context.
    """
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
        text, _, _ = call_llm(self.client, self.model, messages,
                              max_tokens=500, temperature=0.0)
        parsed = extract_json(text)
        return float(score_from_v0(parsed))
    except Exception:
        return None


# Save original v6.5-style run
_orig_run = mod.ReActAgent.run


def run_v67(self, item_id: str, query_path: str, ref_paths: list,
            split: str, domain_code: str | None = None) -> AgentResult:
    # Turn 0: Direct VLM call (calibrated anomaly score)
    direct_score = _direct_turn0(self, query_path, ref_paths, domain_code)

    # Turn 1..K: ReAct agent (v6.5 style)
    original_builder = self._build_initial_messages
    self._build_initial_messages = lambda qp, rp: _build_init_v67(self, qp, rp, domain_code)
    try:
        agent_result = _orig_run(self, item_id=item_id, query_path=query_path,
                                  ref_paths=ref_paths, split=split,
                                  domain_code=domain_code)
    finally:
        self._build_initial_messages = original_builder

    agent_score = agent_result.score
    # Ensemble
    if direct_score is not None:
        ensemble = 0.5 * (direct_score + agent_score)
    else:
        ensemble = agent_score
    agent_result.score = ensemble
    # Log both for analysis
    agent_result.history = [{"turn": 0, "action": "direct_turn0",
                             "direct_score": direct_score}] + agent_result.history
    agent_result.history.append({
        "ensemble": {"direct_score": direct_score,
                     "agent_score": agent_score,
                     "final": ensemble},
    })
    return agent_result


mod.ReActAgent.run = run_v67

from agent_v6 import main  # noqa: E402

if __name__ == "__main__":
    main()
