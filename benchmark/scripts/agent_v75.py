"""AnomalyClaw v7.5 — conflict-triggered agent.

Wires agent_prompt_v75 + a restricted dispatch that only exposes the
primary + secondary tools named in the v7.5 protocol.

Usage:
  python benchmark/scripts/agent_v75.py \
    --manifest benchmark/manifests/full_manifest.json \
    --split dev --backend qwen3 \
    --output benchmark/results/v75_agent_qwen3_dev.json \
    --max_turns 4 --max_workers 9
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import agent_prompt_v75 as _p75  # noqa: E402
import agent_tools_v7 as _t7  # noqa: E402
import agent_v6 as mod  # noqa: E402

# Tools cited in v7.5 domain rules
ALLOWED = {
    "tool_zoom_bbox",
    "tool_image_diff",
    "tool_patch_grid",
    "tool_reference_profiler",
    "tool_reference_retriever",
    "tool_texture_fft",
    "tool_hotspot_cropper",
    "tool_side_by_side",
    "tool_expert_score",  # agent may still probe rank
}


def _dispatch_v75(name: str, args: dict, ctx: dict | None = None) -> dict:
    if name not in ALLOWED:
        return {"error": (f"v7.5 protocol does not allow {name}; allowed: "
                          f"{sorted(ALLOWED)}")}
    return _t7.dispatch_tool(name, args, ctx)


mod.SYSTEM_PROMPT = _p75.SYSTEM_PROMPT
mod.dispatch_tool = _dispatch_v75
mod.TOOL_REGISTRY = _t7.TOOL_REGISTRY
mod.budget_warning_prompt = _p75.budget_warning_prompt
mod.forced_final_prompt = _p75.forced_final_prompt


def main():
    from agent_v6 import main as _main
    _main()


if __name__ == "__main__":
    main()
