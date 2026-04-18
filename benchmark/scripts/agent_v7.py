"""AnomalyClaw v7 — niche-aware agent.

Wires:
  - agent_prompt_v7.SYSTEM_PROMPT (with TOOL_OUTPUT_GUIDE + TOOL_HINTS)
  - agent_tools_v7.dispatch_tool (all tools) OR
    agent_tools_v7.dispatch_tool_keep_only (KEEP subset) depending on env

Modes (set via ANOMA_V7_MODE env var):
  - "keep" (default): gate to KEEP tools from refine-logs/tool_cards/*.md
  - "all":  enable all 13 tools regardless of cards (useful when the
            audit found zero KEEP and we still want to test the v7
            prompt's effect on free selection)

Startup assertions for "keep" mode:
  - If no cards exist, warn and fall back to all tools.
  - If cards exist but zero KEEP, EXIT with error (to prevent silent
    re-enabling of all tools). Use mode=all to override.

Usage:
  # KEEP-gated (default, requires successful Phase B)
  python benchmark/scripts/agent_v7.py \
    --manifest benchmark/manifests/full_manifest.json \
    --split dev --backend qwen3 \
    --output benchmark/results/v7_agent_qwen3_dev.json \
    --max_turns 5 --max_workers 9

  # All-tools (for ablation)
  ANOMA_V7_MODE=all python benchmark/scripts/agent_v7.py ...
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import agent_prompt_v7 as _p7  # noqa: E402
import agent_tools_v7 as _t7  # noqa: E402
import agent_v6 as mod  # noqa: E402

MODE = os.environ.get("ANOMA_V7_MODE", "keep").lower()


def _startup_assertions():
    cards = (Path(__file__).resolve().parent.parent.parent
             / "refine-logs" / "tool_cards")
    if MODE == "all":
        print("[v7 mode=all] running with ALL 13 tools (KEEP gate disabled). "
              "Useful for ablation vs keep-gated or for pre-audit runs.",
              flush=True)
        return
    if not cards.exists() or not any(cards.glob("*.md")):
        print("[v7 warn] no tool cards found; running with all tools "
              "enabled (pre-audit behavior). Run Phase B first for v7.",
              file=sys.stderr, flush=True)
        return

    keep = _t7._load_keep_tools()
    if not keep:
        print("[v7 FATAL] tool cards exist but ZERO tools are KEEP. "
              "Refusing to run — this would silently re-enable all tools. "
              "Set ANOMA_V7_MODE=all to override explicitly.",
              file=sys.stderr, flush=True)
        sys.exit(2)

    print(f"[v7 mode=keep] KEEP tools: {sorted(keep)}", flush=True)

    hints = getattr(_p7, "TOOL_HINTS", "")
    if "not yet generated" in hints:
        print("[v7 warn] TOOL_HINTS is the fallback placeholder. "
              "Run compose_v7_prompt.py after Phase B to inject "
              "empirical tool cards into the prompt.",
              file=sys.stderr, flush=True)


# Patch v6 module to use v7 prompt + chosen dispatch
mod.SYSTEM_PROMPT = _p7.SYSTEM_PROMPT
if MODE == "all":
    mod.dispatch_tool = _t7.dispatch_tool  # unrestricted
else:
    mod.dispatch_tool = _t7.dispatch_tool_keep_only
mod.TOOL_REGISTRY = _t7.TOOL_REGISTRY
mod.budget_warning_prompt = _p7.budget_warning_prompt
mod.forced_final_prompt = _p7.forced_final_prompt


def main():
    _startup_assertions()
    from agent_v6 import main as _main
    _main()


if __name__ == "__main__":
    main()
