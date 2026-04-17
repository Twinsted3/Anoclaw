"""AnomalyClaw v6.1 — same ReAct loop as v6 but imports v6.1 prompt.

Only difference: prompt with confidence gating + expert warning.
All other behavior identical — same tools, same CLI flags.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Monkey-patch the prompt module used by agent_v6 BEFORE importing it
import agent_prompt_v6_1 as _p61

import agent_prompt_v6 as _p6
_p6.SYSTEM_PROMPT = _p61.SYSTEM_PROMPT
_p6.TOOL_CATALOG = _p61.TOOL_CATALOG
_p6.forced_final_prompt = _p61.forced_final_prompt
_p6.budget_warning_prompt = _p61.budget_warning_prompt

from agent_v6 import main  # noqa: E402

if __name__ == "__main__":
    main()
