"""AnomalyClaw v6.5 — B-regime agent with v6's free-score output.

Combines:
  - v6.4's message builder (injects domain hint)
  - v6's SYSTEM_PROMPT (free-form `score` 0..1 output — NOT score_from_v0)
  - v6's _parse_action (expects `score` not `label+confidence`)

Rationale: score_from_v0 maps label+confidence to near-bimodal scores
(~80% of items pinned to <0.1 or >0.9), which hurts AUROC vs v6's smoother
distribution.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Use v6 prompt as-is
import agent_prompt_v6 as _p6  # unchanged

import agent_v6 as mod  # noqa: E402
from infer import DOMAIN_CONTEXT, text_msg, img_msg, load_and_encode  # noqa: E402

SYSTEM_PROMPT = _p6.SYSTEM_PROMPT


def _build_init_v65(self, query_path, ref_paths, _domain_code):
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


_orig_run = mod.ReActAgent.run
def run_v65(self, item_id, query_path, ref_paths, split, domain_code=None):
    original_builder = self._build_initial_messages
    self._build_initial_messages = lambda qp, rp, **_kw: _build_init_v65(self, qp, rp, domain_code)
    try:
        return _orig_run(self, item_id=item_id, query_path=query_path,
                         ref_paths=ref_paths, split=split,
                         domain_code=domain_code)
    finally:
        self._build_initial_messages = original_builder

mod.ReActAgent.run = run_v65

from agent_v6 import main  # noqa: E402

if __name__ == "__main__":
    main()
