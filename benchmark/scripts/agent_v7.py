"""AnomalyClaw v7 — niche-aware agent.

Wires:
  - agent_prompt_v7.SYSTEM_PROMPT (which imports TOOL_HINTS from the
    auto-generated agent_tool_hints_v7.py)
  - agent_tools_v7.dispatch_tool_keep_only (which gates tools to the KEEP
    set loaded from refine-logs/tool_cards/*.md)

Startup assertions:
  - If refine-logs/tool_cards/*.md does not exist, the script warns but
    still runs with all tools enabled (pre-audit behavior).
  - If it exists but zero KEEP, the script exits with a clear error
    rather than running an "all-tools-open" v7 by accident.

Usage:
  python benchmark/scripts/agent_v7.py \
    --manifest benchmark/manifests/full_manifest.json \
    --split dev --backend qwen3 \
    --output benchmark/results/v7_agent_qwen3_dev.json \
    --max_turns 5 --max_workers 9
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import agent_prompt_v7 as _p7  # noqa: E402
import agent_tools_v7 as _t7  # noqa: E402
import agent_v6 as mod  # noqa: E402


def _startup_assertions():
    cards = (Path(__file__).resolve().parent.parent.parent
             / "refine-logs" / "tool_cards")
    if not cards.exists() or not any(cards.glob("*.md")):
        print("[v7 warn] no tool cards found; running with all tools "
              "enabled (pre-audit behavior). Run Phase B first for v7.",
              file=sys.stderr, flush=True)
        return

    keep = _t7._load_keep_tools()
    if not keep:
        print("[v7 FATAL] tool cards exist but ZERO tools are KEEP. "
              "Refusing to run — this would silently re-enable all tools.",
              file=sys.stderr, flush=True)
        print(f"[v7 FATAL] Cards checked: {sorted(cards.glob('*.md'))}",
              file=sys.stderr, flush=True)
        sys.exit(2)

    print(f"[v7] KEEP tools: {sorted(keep)}", flush=True)

    hints = getattr(_p7, "TOOL_HINTS", "")
    if "not yet generated" in hints:
        print("[v7 warn] TOOL_HINTS is the fallback placeholder. "
              "Run compose_v7_prompt.py after Phase B to inject "
              "empirical tool cards into the prompt.",
              file=sys.stderr, flush=True)


# Patch v6 module to use v7 prompt + v7 keep-gated dispatch
mod.SYSTEM_PROMPT = _p7.SYSTEM_PROMPT
mod.dispatch_tool = _t7.dispatch_tool_keep_only
mod.TOOL_REGISTRY = _t7.TOOL_REGISTRY
mod.budget_warning_prompt = _p7.budget_warning_prompt
mod.forced_final_prompt = _p7.forced_final_prompt


def main():
    _startup_assertions()
    # Delegate to agent_v6.main() which has the full CLI + runner
    from agent_v6 import main as _main
    _main()


if __name__ == "__main__":
    main()
