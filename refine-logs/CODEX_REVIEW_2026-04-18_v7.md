Reading additional input from stdin...
OpenAI Codex v0.120.0 (research preview)
--------
workdir: /hdd1/jiangxi/AD-Agent
model: gpt-5.4
provider: openai
approval: never
sandbox: workspace-write [workdir, /tmp, $TMPDIR, /home/jiangxi/.codex/memories]
reasoning effort: high
reasoning summaries: none
session id: 019da06c-5954-7023-a3f7-8694a36c726a
--------
user
You are doing an independent correctness + design review of AnomalyClaw v7, a per-item ReAct agent for visual anomaly detection on 12 domains using Qwen3.5-VL-27B.

## Context

v6.5 agent showed that 10 of 11 tools are NET-NEGATIVE on the subsets where they are called (only `tool_zoom_bbox` is net-positive at +7.0pp). v7 hypothesis: per-tool confirmation bias. Fix: every tool now returns an `interpretation` field that pairs a verdict hint with a disconfirming clause ("IF X then query is likely NORMAL despite this signal"). Plan is to audit each tool independently on dev n=480 via `single_tool_agent.py` (ReAct with ONE tool exposed), slice results, find each tool's niche, inject those niches into `agent_v7` prompt.

Only Direct is the baseline (0.7599 dev, 0.7684 test). Per user instruction, Fusion and Router are not in scope.

## Claim being reviewed (pre-deployment)

The framework (tool redesigns + single_tool_agent + tool_audit_runner + build_tool_card) will produce per-tool niches on dev n=480 that are (a) statistically valid (bootstrap 95% CI lower bound > 0, n≥10) and (b) actionable (composable into agent_v7 prompt).

## Files to inspect (paths relative to /hdd1/jiangxi/AD-Agent/)

- `benchmark/scripts/agent_tools_v7.py` — 13 tool functions with new `_wrap_interpretation()` helper + `dispatch_tool_keep_only()` gate; copy of v6 tools with modifications
- `benchmark/scripts/agent_prompt_v7.py` — system prompt + tool catalog, imports `TOOL_HINTS` from auto-generated `agent_tool_hints_v7.py` (does not yet exist)
- `benchmark/scripts/single_tool_agent.py` — ReAct runner restricted to ONE tool; monkeypatches `agent_v6.SYSTEM_PROMPT` and `agent_v6.dispatch_tool` BEFORE starting ThreadPoolExecutor
- `benchmark/scripts/tool_audit_runner.py` — sequential wrapper that spawns single_tool_agent as a subprocess per tool
- `benchmark/scripts/build_tool_card.py` — slices tool-audit JSON by 9 axes, computes Δ_AUROC vs Direct baseline with paired bootstrap CI, emits tool_card.md with KEEP/DROP verdict
- `benchmark/scripts/agent_v6.py` (context: ReActAgent class that single_tool_agent patches)
- `benchmark/scripts/agent_prompt_v6.py` (reference: original prompt agent_v6 imports)

## Critical checks (prioritized by likely impact)

1. **MONKEYPATCH SAFETY**: `single_tool_agent.py:main()` sets `v6.SYSTEM_PROMPT = sp` and `v6.dispatch_tool = make_restricted_dispatch(...)` then launches `ThreadPoolExecutor(max_workers=9)`. Does `agent_v6.ReActAgent.run()` reference `SYSTEM_PROMPT` / `dispatch_tool` as module globals (thus picking up the patch) or as closure locals (thus NOT picking it up)? If the former, do concurrent threads race on any other module state? If the latter, we silently ran v6 with v6's tools, defeating the purpose.

2. **RESTRICTED DISPATCH CORRECTNESS**: `make_restricted_dispatch` returns `{"error": "only X is available ... you called Y"}` when the LLM calls a wrong tool. Does agent_v6's turn loop handle this gracefully (keep looping) or does it crash / finalize with score=0.5? If it crashes, many items will be noise.

3. **CTX INJECTION STILL WORKS**: `tv7.dispatch_tool` populates PROTECTED_CTX_KEYS from `ctx` (query_path, ref_paths, vlm_client, etc). When we wrap it with `make_restricted_dispatch`, does ctx still reach the underlying tool function? Trace the call chain and confirm.

4. **TOOL INTERPRETATION WRAPPER**: `_wrap_interpretation(obs, verdict, disconfirm)` mutates `obs` in place by assigning `obs["interpretation"] = ...`. Is this actually transmitted to the VLM? Check `agent_v6._obs_to_text()` — does it include the `interpretation` field in its JSON dump? If the summary truncates at 1500 chars and interpretation is at the end of a large dict, it may be dropped.

5. **DEV/TEST CONTAMINATION FOR EXPERT LOOKUP**: `tool_expert_score` calls `_load_expert_scores(expert, split)` with `split` from ctx. When single_tool_agent runs on `split="dev"`, does it correctly look up dev cached scores (subspacead_dev.json) — NOT test scores? Confirm via the EXPERT_FILES mapping in agent_tools_v7.py.

6. **BUILD_TOOL_CARD METRIC CORRECTNESS**: The script computes macro AUROC via `macro_auroc_from_results` for slice-level `auroc_tool` / `auroc_direct`, but the bootstrap delta CI uses POOLED AUROC via `roc_auc_score(y_arr[idx], s_t_arr[idx])`. These are different quantities — is the 95% CI actually a CI on the macro delta, or on the pooled delta? Mislabeled CI = misleading niche claims.

7. **NICHE STATISTICAL VALIDITY**: Niche threshold is n≥10, Δ>0, bootstrap CI lower > 0. With 8+ slices and n=480 dev, how many slices would we expect to flag positive by chance alone under a null model where the tool is neutral? (multiple-testing / snooping concern). Is there any correction, or is the 0.05 CI naively applied per slice?

8. **SELECTION ON DEV**: The final `agent_v7` prompt will incorporate per-tool cards derived from dev. When we later run agent_v7 on test, does the test evaluation honestly reflect the cost of this selection? The spec says "Test runs exactly once" — but the niche decisions themselves are a form of dev selection. Acknowledge vs. overstate?

9. **KEEP-GATE FALLBACK**: `dispatch_tool_keep_only` falls back to all tools when no tool cards exist. Good for audit phase. But if the Phase B audit DROPs every tool (all slices non-significant), the fallback would re-enable all tools — exactly the failure mode we wanted to prevent. Is this behavior what we want?

10. **DIAGNOSIS OUTPUT UNUSED**: `diagnose_tools.py` writes `refine-logs/tool_diagnosis/*.md` with "fill in failure mode" placeholders that the engineer never actually filled in. Is this an inert artifact (harmless) or does something downstream silently depend on it?

## Output format

- **CRITICAL issues** (file:line, exact fix, why it matters)
- **MAJOR issues** (reproducibility, statistical validity, edge cases)
- **MINOR issues** (style, comments)
- **PUBLISHABILITY verdict** (blunt): is this a real research contribution if Phase B+C succeed? or merely hyperparameter tuning on dev dressed up as "niche discovery"?
- **SUGGESTED NEXT EXPERIMENTS** (3-5 concrete ideas, no platitudes)

Be a skeptic. The engineer has a strong prior that the framework is correct; find what they missed.
codex
I’ll review this as a code/design audit, not implement changes. I’ll inspect the named files first, then trace the ReAct call paths and the metric code before giving a severity-ranked review.
exec
/bin/bash -lc "sed -n '1,260p' benchmark/scripts/single_tool_agent.py" in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
"""Single-tool agent: Direct-style ReAct loop with exactly ONE tool exposed.

Builds on top of agent_v6.ReActAgent but:
  - Swaps SYSTEM_PROMPT for a single-tool variant describing only `--tool`
  - Restricts dispatch_tool to reject any tool != --tool
  - Outputs {item_id, anomaly_score, used_tool, n_turns, tools_used,
             confidence, rationale, error} per item

Usage:
  python benchmark/scripts/single_tool_agent.py \
    --tool tool_expert_score --split dev \
    --manifest benchmark/manifests/full_manifest.json \
    --output benchmark/results/tool_audit/tool_expert_score.json \
    --max_turns 3 --max_workers 9
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from infer import get_client, get_model_name  # noqa: E402
import agent_v6 as v6  # noqa: E402
import agent_tools_v7 as tv7  # noqa: E402
import agent_prompt_v7 as pv7  # noqa: E402


SINGLE_TOOL_SYSTEM_PROMPT = """You are a visual anomaly detection agent.

INPUT PER IMAGE: one query image, four normal reference images, a turn budget.
TASK: decide if the query is normal or anomalous and output a score in [0,1]
where 1 means certainly anomalous.

You have NO domain information and can observe only what's in the images.
On each turn you have exactly ONE tool available.

{output_guide}

THE ONE TOOL AVAILABLE TO YOU:
{tool_desc}

PROTOCOL: Return ONLY a JSON object:
{{
  "thought":  "<one or two sentences>",
  "action":   "call_tool" | "final",
  "tool":     "<tool_name>" | null,
  "args":     {{ ... }} | null,
  "confidence": <integer 0..100>,
  "score":    <float 0..1> | null,
  "rationale": "<one or two sentences>" | null
}}

GUIDELINES:
- Call the tool ONLY if you think it will help on THIS image. Otherwise output
  `final` at turn 1 without calling it.
- If the tool returns an `unreliable_alignment: true` or `not_applicable: true`
  flag, IGNORE its output and reason from the raw images.
- Read the disconfirm clause of the tool output before updating your score.
- Return valid JSON only.
"""


def _extract_tool_desc(tool_name: str) -> str:
    """Extract the docstring block for `tool_name` from agent_prompt_v7.TOOL_CATALOG."""
    catalog = pv7.TOOL_CATALOG
    lines = catalog.splitlines()
    out: list[str] = []
    capturing = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(tool_name):
            capturing = True
            out.append(line)
            continue
        if capturing:
            if line.startswith("    ") or not stripped:
                out.append(line)
                continue
            # next tool or section header → stop
            break
    if not out:
        return f"  {tool_name}(...)  (no description found in catalog)"
    return "\n".join(out).rstrip()


def make_restricted_dispatch(allowed_tool: str):
    """Return a dispatch_tool that routes only `allowed_tool`, else returns error."""
    original = tv7.dispatch_tool

    def _dispatch(name: str, args: dict, ctx: dict | None = None) -> dict:
        if name != allowed_tool:
            return {"error": (f"only {allowed_tool} is available in this single-tool "
                              f"run; you called {name}")}
        return original(name, args, ctx)

    return _dispatch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tool", required=True)
    ap.add_argument("--manifest", default="benchmark/manifests/full_manifest.json")
    ap.add_argument("--split", choices=["calibration", "dev", "test"], default="dev")
    ap.add_argument("--output", required=True)
    ap.add_argument("--backend", default="qwen3")
    ap.add_argument("--max_turns", type=int, default=3)
    ap.add_argument("--max_workers", type=int, default=9)
    ap.add_argument("--max_items", type=int, default=0)
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    if args.tool not in tv7.TOOL_REGISTRY:
        raise SystemExit(f"unknown tool {args.tool!r}; choices: "
                         f"{sorted(tv7.TOOL_REGISTRY)}")

    items = json.load(open(args.manifest))
    items = [x for x in items if x.get("split") == args.split]
    if args.max_items:
        items = items[:args.max_items]

    prev: list = []
    done_ids: set = set()
    if args.resume and os.path.exists(args.output):
        prev = json.load(open(args.output))
        done_ids = {r["item_id"] for r in prev if r.get("error") is None}
        items = [x for x in items if x["item_id"] not in done_ids]
        print(f"[resume] {len(done_ids)} done; {len(items)} remaining", flush=True)

    client = get_client(args.backend)
    model = get_model_name(args.backend)

    # Patch: single-tool prompt and restricted dispatch
    tool_desc = _extract_tool_desc(args.tool)
    sp = SINGLE_TOOL_SYSTEM_PROMPT.format(
        output_guide=pv7.TOOL_OUTPUT_GUIDE, tool_desc=tool_desc)

    v6.SYSTEM_PROMPT = sp
    v6.dispatch_tool = make_restricted_dispatch(args.tool)

    agent = v6.ReActAgent(vlm_client=client, vlm_model=model,
                          max_turns=args.max_turns)

    results: list = list(prev)
    t0 = time.time()

    def _run_one(x):
        try:
            r = agent.run(item_id=x["item_id"], query_path=x["query_path"],
                          ref_paths=x["ref_paths"], split=args.split,
                          domain_code=x.get("domain_code"))
            used = args.tool in (r.tools_used or [])
            return {
                "item_id": x["item_id"],
                "domain_code": x.get("domain_code"),
                "label_gt": x.get("label"),
                "anomaly_score": r.score,
                "used_tool": used,
                "n_turns": r.n_turns,
                "tools_used": r.tools_used,
                "confidence": r.confidence,
                "rationale": r.rationale,
                "error": r.error,
            }
        except Exception as e:
            return {"item_id": x["item_id"], "domain_code": x.get("domain_code"),
                    "label_gt": x.get("label"), "anomaly_score": 0.5,
                    "used_tool": False, "n_turns": 0, "tools_used": [],
                    "confidence": 0, "rationale": None,
                    "error": f"{type(e).__name__}: {e}"}

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=args.max_workers) as ex:
        futs = [ex.submit(_run_one, x) for x in items]
        for i, fut in enumerate(as_completed(futs)):
            results.append(fut.result())
            if (i + 1) % 40 == 0:
                with open(args.output, "w") as f:
                    json.dump(results, f)
                print(f"[{args.tool}] {i+1}/{len(items)} "
                      f"t={time.time()-t0:.1f}s", flush=True)

    with open(args.output, "w") as f:
        json.dump(results, f)
    used_n = sum(1 for r in results if r.get("used_tool"))
    err_n = sum(1 for r in results if r.get("error"))
    print(f"[{args.tool}] n={len(results)} used={used_n} err={err_n} "
          f"→ {args.output}")


if __name__ == "__main__":
    main()

exec
/bin/bash -lc "sed -n '1,320p' benchmark/scripts/agent_v6.py" in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
"""AnomalyClaw v6 — per-item autonomous ReAct agent.

Usage:
  python benchmark/scripts/agent_v6.py \
    --manifest benchmark/manifests_v2/full_manifest.json \
    --split test --backend qwen3 \
    --output benchmark/results/v6_agent_qwen3_test.json \
    --max_turns 5 --max_workers 8
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from infer import (  # noqa: E402
    call_llm, extract_json, get_client, get_model_name,
    img_msg, load_and_encode, text_msg,
)
from agent_prompt_v6 import (  # noqa: E402
    SYSTEM_PROMPT, budget_warning_prompt, forced_final_prompt,
)
from agent_tools_v6 import dispatch_tool, TOOL_REGISTRY  # noqa: E402


@dataclass
class AgentResult:
    item_id: str
    score: float
    rationale: str
    n_turns: int
    tools_used: list
    history: list
    confidence: int
    error: str | None = None


class ReActAgent:
    def __init__(self, vlm_client, vlm_model: str, max_turns: int = 5,
                 json_retries: int = 1, max_tokens: int = 600):
        self.client = vlm_client
        self.model = vlm_model
        self.K = max_turns
        self.json_retries = json_retries
        self.max_tokens = max_tokens

    # ──────────────────────────────────────────────────────────────────
    def _build_initial_messages(self, query_path: str,
                                ref_paths: list,
                                domain_code: str | None = None,
                                anchor_text: str | None = None) -> list:
        """Builder is called with per-item kwargs; no instance mutation.
        Subclasses override by subclassing, not by monkey-patching.

        Args:
            domain_code: forwarded for variants that want to inject
                DOMAIN_CONTEXT[d] at call time.
            anchor_text: free-form extra preamble (used by anchored
                variants to pass precomputed expert signals).
        """
        user_parts = []
        if anchor_text:
            user_parts.append(text_msg(anchor_text))
        user_parts.append(text_msg("NORMAL REFERENCE IMAGES:"))
        for rp in ref_paths[:4]:
            user_parts.append(img_msg(load_and_encode(rp)))
        user_parts.append(text_msg("QUERY IMAGE:"))
        user_parts.append(img_msg(load_and_encode(query_path)))
        user_parts.append(text_msg(f"Turn 1/{self.K}. Decide your next action."))
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_parts},
        ]

    def _parse_action(self, text: str) -> dict | None:
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
        return parsed

    def _call_with_json_retry(self, messages: list) -> dict | None:
        attempts = 1 + self.json_retries
        cur = list(messages)
        for _ in range(attempts):
            try:
                text, _, _ = call_llm(self.client, self.model, cur,
                                      max_tokens=self.max_tokens,
                                      temperature=0.0)
            except Exception:
                return None
            parsed = self._parse_action(text)
            if parsed is not None:
                return parsed
            cur = cur + [{
                "role": "user",
                "content": "Your last response was not valid JSON. "
                           "Return a single JSON object with fields "
                           "{thought, action, tool, args, confidence, "
                           "score, rationale}.",
            }]
        return None

    # ──────────────────────────────────────────────────────────────────
    def run(self, item_id: str, query_path: str, ref_paths: list,
            split: str, domain_code: str | None = None) -> AgentResult:
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
        messages = self._build_initial_messages(query_path, ref_paths,
                                                domain_code=domain_code)
        history, tools_used = [], []

        for turn in range(1, self.K + 1):
            action = self._call_with_json_retry(messages)
            if action is None:
                return AgentResult(
                    item_id=item_id, score=0.5, rationale="json parse failed",
                    n_turns=turn, tools_used=tools_used, history=history,
                    confidence=0, error="malformed JSON after retries",
                )

            if action["action"] == "final":
                return AgentResult(
                    item_id=item_id,
                    score=max(0.0, min(1.0, float(action["score"]))),
                    rationale=str(action.get("rationale", ""))[:500],
                    n_turns=turn, tools_used=tools_used,
                    history=history + [{"turn": turn, **_summarise(action)}],
                    confidence=int(action.get("confidence", 0) or 0),
                )

            if turn == self.K:
                # Budget exhausted; force a final in one more sub-call.
                messages.append({"role": "assistant",
                                 "content": json.dumps(_summarise(action))})
                messages.append({"role": "user",
                                 "content": forced_final_prompt(self.K)})
                forced = self._call_with_json_retry(messages)
                if forced and forced.get("action") == "final":
                    return AgentResult(
                        item_id=item_id,
                        score=max(0.0, min(1.0, float(forced["score"]))),
                        rationale=str(forced.get("rationale", ""))[:500],
                        n_turns=self.K, tools_used=tools_used,
                        history=history + [
                            {"turn": turn, **_summarise(action)},
                            {"turn": turn, **_summarise(forced)},
                        ],
                        confidence=int(forced.get("confidence", 0) or 0),
                    )
                return AgentResult(
                    item_id=item_id, score=0.5, rationale="forced-final failed",
                    n_turns=self.K, tools_used=tools_used, history=history,
                    confidence=0, error="forced-final produced non-final",
                )

            # Execute tool
            tool_name = action["tool"]
            tool_args = action.get("args") or {}
            observation = dispatch_tool(tool_name, tool_args, ctx)
            tools_used.append(tool_name)
            history.append({"turn": turn, **_summarise(action),
                            "obs_keys": list(observation.keys()),
                            "obs_error": observation.get("error")})

            # Stash expert patches for hotspot/counter tools
            if tool_name == "tool_expert_score":
                ctx["_expert_patches"] = observation.get("top_patches", [])

            # Feed observation back — include image if present, text otherwise
            obs_parts = []
            obs_text = _obs_to_text(observation)
            obs_parts.append(text_msg(
                f"OBSERVATION from {tool_name}: {obs_text}"))
            for img_key in ("crop_b64", "diff_mask_b64", "aligned_diff_b64",
                            "composite_b64"):
                if observation.get(img_key):
                    obs_parts.append(img_msg(observation[img_key]))
            if observation.get("tiles"):
                for t in observation["tiles"][:9]:
                    obs_parts.append(img_msg(t["crop_b64"]))
            remaining = self.K - turn
            obs_parts.append(text_msg(
                f"Turn {turn + 1}/{self.K}. "
                f"{budget_warning_prompt(remaining)}\n"
                f"Decide your next action."))
            messages.append({"role": "assistant",
                             "content": json.dumps(_summarise(action))})
            messages.append({"role": "user", "content": obs_parts})

        return AgentResult(
            item_id=item_id, score=0.5, rationale="loop exhausted",
            n_turns=self.K, tools_used=tools_used, history=history,
            confidence=0, error="loop exhausted without final",
        )


def _summarise(action: dict) -> dict:
    """Drop large args/rationale for history storage."""
    out = {k: v for k, v in action.items()
           if k not in ("args",) or v is None or len(str(v)) < 500}
    if "args" in action and "args" not in out:
        out["args"] = str(action["args"])[:400]
    return out


def _obs_to_text(obs: dict) -> str:
    """Compact text summary of an observation (no base64 payloads)."""
    small = {}
    for k, v in obs.items():
        if k.endswith("_b64"):
            small[k] = f"<{len(v)}-char image>"
        elif k == "tiles":
            small[k] = f"<{len(v)} tiles attached>"
        elif k == "top_patches":
            small[k] = f"<{len(v)} patches>"
        else:
            small[k] = v
    return json.dumps(small, default=str)[:1500]


# ── CLI entry ──────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--split", choices=["calibration", "dev", "test"], required=True)
    ap.add_argument("--backend", choices=["qwen3", "seedvl", "gpt"], required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--domains", nargs="*", default=None)
    ap.add_argument("--max_turns", type=int, default=5)
    ap.add_argument("--max_workers", type=int, default=8)
    ap.add_argument("--max_items", type=int, default=0)
    ap.add_argument("--resume", action="store_true",
                    help="skip items already present in --output")
    args = ap.parse_args()

    items = json.load(open(args.manifest))
    items = [x for x in items if x.get("split") == args.split]
    if args.domains:
        items = [x for x in items if x.get("domain_code") in args.domains]
    if args.max_items:
        items = items[:args.max_items]

    done_ids: set = set()
    prev: list = []
    if args.resume and os.path.exists(args.output):
        prev = json.load(open(args.output))
        done_ids = {r["item_id"] for r in prev if r.get("error") is None}
        items = [x for x in items if x["item_id"] not in done_ids]
        print(f"[resume] {len(done_ids)} already done; {len(items)} remaining")

    client = get_client(args.backend)
    model = get_model_name(args.backend)
    agent = ReActAgent(vlm_client=client, vlm_model=model,
                       max_turns=args.max_turns)

    results: list = list(prev)
    t0 = time.time()

    def _run_one(x):
        try:
            r = agent.run(item_id=x["item_id"], query_path=x["query_path"],
                          ref_paths=x["ref_paths"], split=args.split,
                          domain_code=x.get("domain_code"))
            return {
                "item_id": x["item_id"], "domain_code": x.get("domain_code"),
                "label_gt": x.get("label"), "anomaly_score": r.score,
                "rationale": r.rationale, "n_turns": r.n_turns,
                "tools_used": r.tools_used, "confidence": r.confidence,
                "error": r.error,
            }
        except Exception as e:
            return {"item_id": x["item_id"], "domain_code": x.get("domain_code"),
                    "label_gt": x.get("label"), "anomaly_score": 0.5,
                    "n_turns": 0, "tools_used": [], "confidence": 0,
                    "error": f"{type(e).__name__}: {e}"}

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=args.max_workers) as ex:
        futures = [ex.submit(_run_one, x) for x in items]
        for i, fut in enumerate(as_completed(futures)):
            results.append(fut.result())
            if (i + 1) % 25 == 0:
                with open(args.output, "w") as f:
                    json.dump(results, f)
                print(f"[{i+1}/{len(items)}] {time.time()-t0:.1f}s  "
                      f"written={len(results)}", flush=True)

    with open(args.output, "w") as f:
        json.dump(results, f)

exec
/bin/bash -lc "sed -n '1,360p' benchmark/scripts/agent_tools_v7.py" in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
"""AnomalyClaw v7 — 13-tool catalog with interpretation + disconfirm hints.

Changes from v6:
- Every tool's return dict includes an `interpretation` field built via
  `_wrap_interpretation(obs, verdict, disconfirm)`: a verdict hint
  ("observation suggests X") paired with a disconfirming clause
  ("IF Y then the query is likely NORMAL"). Reduces confirmation bias.
- Alignment-sensitive tools (image_diff, rotate_align) now return an
  UNRELIABLE flag when their internal confidence is low.
- dispatch_tool is gated to a KEEP set (loaded lazily from
  refine-logs/tool_cards/*.md) during v7 runs; audit runs use the
  un-gated dispatch via the single_tool_agent.

Original v6 header follows:

Design invariants:
- No per-domain branching inside tools. Domain code is never a modeling input
  (only used by tool_reference_retriever to locate its cached index file).
- Pure functions where possible; cache expensive resources at module level.
- Each tool returns a JSON-serializable dict with an `error` key on failure.

Tiers:
  1. Expert probes: tool_expert_score
  2. Visual inspection: hotspot_cropper, zoom_bbox, patch_grid, image_diff,
                        rotate_align, side_by_side
  3. Reference understanding: reference_profiler, reference_retriever
  4. Structural: component_counter, segment_and_count, texture_fft
  5. Knowledge: domain_knowledge
"""
from __future__ import annotations

import base64
import json
import os
import sys
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from infer import call_llm, extract_json, img_msg, load_and_encode, text_msg  # noqa: E402

RESULTS_DIR = Path("/hdd1/jiangxi/AD-Agent/benchmark/results")


# ─── Helpers ────────────────────────────────────────────────────────────────

def _pil_to_b64(img: Image.Image, max_side: int = 512, quality: int = 85) -> str:
    w, h = img.size
    if max(w, h) > max_side:
        scale = max_side / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _wrap_interpretation(obs: dict, verdict: str, disconfirm: str) -> dict:
    """Attach a verdict + disconfirming clause to a tool observation.

    Format: "Observation suggests: <verdict>. IMPORTANT: if <disconfirm>,
    the query is likely NORMAL despite this signal."

    Intent: force the VLM to consider the null hypothesis before updating
    its score. Many v6 failures came from confirmation bias where a tool's
    signal (e.g. 'strong anomaly') was treated as proof rather than evidence.
    """
    obs["interpretation"] = (
        f"Observation suggests: {verdict}. "
        f"IMPORTANT: if {disconfirm}, the query is likely NORMAL despite this signal."
    )
    return obs


# ─── Tier 1: Expert probes ──────────────────────────────────────────────────

EXPERT_FILES = {
    "subspacead":    {"calibration": "subspacead_calibration.json",
                      "dev":         "subspacead_dev.json",
                      "test":        "subspacead_test.json"},
    "anomalyvfm":    {"calibration": "anomalyvfm_calibration.json",
                      "dev":         "anomalyvfm_dev.json",  # may not exist
                      "test":        "anomalyvfm_test.json"},
    "patchknn":      {"calibration": "classical_dinov2_patch_test_all.json",
                      "dev":         "classical_dinov2_patch_test_all.json",
                      "test":        "classical_dinov2_patch_test_all.json"},
    "dinov2_global": {"calibration": "classical_dinov2_global_test_all.json",
                      "dev":         "classical_dinov2_global_test_all.json",
                      "test":        "classical_dinov2_global_test_all.json"},
}


@lru_cache(maxsize=16)
def _load_expert_scores(expert: str, split: str) -> tuple[dict, np.ndarray]:
    """Return (item_id -> record, sorted score array for percentile ranking)."""
    if expert not in EXPERT_FILES:
        raise ValueError(f"unknown expert {expert!r}; must be one of {list(EXPERT_FILES)}")
    fname = EXPERT_FILES[expert].get(split)
    if fname is None:
        raise ValueError(f"no {split} file for expert {expert!r}")
    path = RESULTS_DIR / fname
    if not path.exists():
        return {}, np.array([])
    raw = json.load(open(path))
    if isinstance(raw, list):
        recs = {x["item_id"]: x for x in raw if "item_id" in x}
    else:
        recs = raw
    scores = np.array([float(r["anomaly_score"]) for r in recs.values()
                       if r.get("anomaly_score") is not None])
    scores.sort()
    return recs, scores


def tool_expert_score(item_id: str, expert: str = "subspacead",
                      split: str = "test", **_) -> dict:
    """Look up a cached expert anomaly score + its percentile rank within `split`.

    Returns: {expert, score, normalized_rank, top_patches, interpretation, error}
    """
    try:
        recs, all_scores = _load_expert_scores(expert, split)
    except ValueError as e:
        return {"error": str(e)}
    rec = recs.get(item_id)
    if rec is None or rec.get("anomaly_score") is None:
        return {"error": f"no cached score for {item_id} in {expert}/{split}"}
    s = float(rec["anomaly_score"])
    if len(all_scores) == 0:
        rank = 0.5
    else:
        rank = float(np.searchsorted(all_scores, s) / len(all_scores))
    # v7: binned verdict + disconfirm
    if rank >= 0.85:
        verdict = (f"strong anomaly signal (rank {rank:.2f}: the query's {expert} "
                   f"score is higher than 85% of samples in this split)")
        disconfirm = (f"the {expert} expert is known to over-flag this domain's "
                      f"natural texture variation, OR the refs happen to be outliers")
    elif rank >= 0.60:
        verdict = (f"moderate/ambiguous anomaly signal (rank {rank:.2f}: mild "
                   f"deviation, but within normal variation for many images)")
        disconfirm = (f"the refs show comparable variation, or the score reflects "
                      f"benign domain texture not a defect")
    else:
        verdict = (f"weak signal (rank {rank:.2f}: the query looks like normal "
                   f"samples in this split)")
        disconfirm = (f"a small localised defect may not shift the global {expert} "
                      f"score; do not rule out anomaly if a suspicious region is visible")
    out = {
        "expert": expert,
        "score": s,
        "normalized_rank": rank,
        "top_patches": rec.get("top_patches") or [],
        "error": None,
    }
    return _wrap_interpretation(out, verdict, disconfirm)


# ─── Tier 2: Visual inspection ──────────────────────────────────────────────

def tool_hotspot_cropper(query_path: str, patches: list[dict] | None = None,
                         pad: float = 0.15, k: int = 5,
                         _expert_patches: list | None = None, **_) -> dict:
    """Crop query image around top-k expert-flagged patches (48x48 grid).

    If `patches` is not provided, falls back to `_expert_patches` from session
    context (populated by a prior tool_expert_score call).
    """
    patches = patches or _expert_patches or []
    if not patches:
        return {"error": "no patches available; call tool_expert_score(subspacead) first"}
    img = Image.open(query_path).convert("RGB")
    W, H = img.size
    grid = 48
    rows = [p.get("row") for p in patches[:k] if p.get("row") is not None]
    cols = [p.get("col") for p in patches[:k] if p.get("col") is not None]
    if not rows or not cols:
        return {"error": "patches missing row/col fields"}
    r0, r1 = min(rows), max(rows) + 1
    c0, c1 = min(cols), max(cols) + 1
    span_r, span_c = r1 - r0, c1 - c0
    r0 = max(0, r0 - max(1, int(pad * max(span_r, 1))))
    r1 = min(grid, r1 + max(1, int(pad * max(span_r, 1))))
    c0 = max(0, c0 - max(1, int(pad * max(span_c, 1))))
    c1 = min(grid, c1 + max(1, int(pad * max(span_c, 1))))
    x0, x1 = int(c0 / grid * W), int(c1 / grid * W)
    y0, y1 = int(r0 / grid * H), int(r1 / grid * H)
    if x1 <= x0 or y1 <= y0:
        return {"error": "degenerate crop"}
    crop = img.crop((x0, y0, x1, y1))
    out = {
        "bbox": [x0, y0, x1, y1],
        "crop_b64": _pil_to_b64(crop),
        "original_size": [W, H],
        "n_patches_used": len(patches[:k]),
        "error": None,
    }
    verdict = (f"high-expert-attention region extracted from {out['n_patches_used']} "
               f"hotspot patches; inspect crop for a genuine defect")
    disconfirm = ("the attention region shows normal texture, a lighting artifact, "
                  "or a benign edge — in that case treat as normal")
    return _wrap_interpretation(out, verdict, disconfirm)


def tool_zoom_bbox(query_path: str, bbox: list[int], **_) -> dict:
    """Agent-specified crop. bbox = [x0, y0, x1, y1] in pixel coords."""
    if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        return {"error": "bbox must be [x0, y0, x1, y1]"}
    x0, y0, x1, y1 = bbox
    if x1 <= x0 or y1 <= y0:
        return {"error": f"invalid bbox {bbox}: x1 must be > x0 and y1 > y0"}
    img = Image.open(query_path).convert("RGB")
    W, H = img.size
    x0 = max(0, min(W - 1, int(x0)))
    y0 = max(0, min(H - 1, int(y0)))
    x1 = max(x0 + 1, min(W, int(x1)))
    y1 = max(y0 + 1, min(H, int(y1)))
    crop = img.crop((x0, y0, x1, y1))
    out = {
        "bbox": [x0, y0, x1, y1],
        "crop_b64": _pil_to_b64(crop),
        "original_size": [W, H],
        "error": None,
    }
    verdict = ("agent-requested region returned at higher resolution; "
               "inspect closely for localised defect not visible at overview scale")
    disconfirm = ("the crop shows normal surface texture or a benign visual cue "
                  "(lighting, joint, shadow) — in that case treat as normal")
    return _wrap_interpretation(out, verdict, disconfirm)


def tool_patch_grid(query_path: str, rows: int = 3, cols: int = 3, **_) -> dict:
    """Return rows*cols tiles covering the image in a regular grid."""
    try:
        rows, cols = int(rows), int(cols)
    except (TypeError, ValueError):
        return {"error": "rows/cols must be integers"}
    if rows < 1 or cols < 1:
        return {"error": f"rows/cols must be >= 1; got {rows}x{cols}"}
    # v7: cap at 3x3 to keep tiles readable and VLM context manageable
    rows = min(rows, 3)
    cols = min(cols, 3)
    img = Image.open(query_path).convert("RGB")
    W, H = img.size
    tw, th = W // cols, H // rows
    tiles = []
    for i in range(rows):
        for j in range(cols):
            x0, y0 = j * tw, i * th
            x1 = (j + 1) * tw if j < cols - 1 else W
            y1 = (i + 1) * th if i < rows - 1 else H
            crop = img.crop((x0, y0, x1, y1))
            tiles.append({
                "cell": [i, j],
                "bbox": [x0, y0, x1, y1],
                "crop_b64": _pil_to_b64(crop, max_side=256),
            })
    out = {"rows": rows, "cols": cols, "tiles": tiles, "error": None}
    verdict = (f"image split into {rows}x{cols} tiles; look for a single tile "
               f"that differs clearly from the others in texture/content")
    disconfirm = ("all tiles vary naturally (texture, lighting gradient), no "
                  "single tile stands out — in that case treat as normal")
    return _wrap_interpretation(out, verdict, disconfirm)


def tool_image_diff(query_path: str, ref_path: str | None = None,
                    ref_paths: list[str] | None = None, ref_idx: int = 0,
                    threshold: float = 30.0, **_) -> dict:
    """Absolute pixel diff between query and a reference, with stats + mask.

    Accepts either `ref_path` directly or `ref_idx` + `ref_paths` from session.
    """
    if ref_path is None and ref_paths:
        try:
            ref_path = ref_paths[int(ref_idx)]
        except (IndexError, ValueError):
            return {"error": f"ref_idx {ref_idx} out of range"}
    if not ref_path or not os.path.exists(ref_path):
        return {"error": f"ref_path not found: {ref_path!r}"}
    q = np.array(Image.open(query_path).convert("RGB").resize((256, 256)))
    r = np.array(Image.open(ref_path).convert("RGB").resize((256, 256)))
    diff = np.abs(q.astype(float) - r.astype(float)).mean(axis=2)
    mask = (diff > threshold).astype(np.uint8) * 255
    change_pct = float(mask.mean() / 255 * 100)
    mean_diff = float(diff.mean())
    # v7: detect unreliable diff when query/ref alignment is poor
    unreliable = (mean_diff > 40.0) or (change_pct > 45.0)
    out = {
        "mean_diff": mean_diff,
        "max_diff": float(diff.max()),
        "change_percent": change_pct,
        "threshold": threshold,
        "unreliable_alignment": unreliable,
        "diff_mask_b64": _pil_to_b64(Image.fromarray(mask, mode="L").convert("RGB"),
                                     max_side=256),
        "error": None,
    }
    if unreliable:
        verdict = (f"UNRELIABLE: query and reference are not aligned "
                   f"(mean_diff={mean_diff:.1f}, change={change_pct:.1f}%); "
                   f"the diff mask reflects alignment noise, not defects")
        disconfirm = ("alignment noise ALWAYS looks like many bright regions; "
                      "do NOT use this tool's output as evidence for this sample")
    else:
        verdict = (f"pixel diff computed; {change_pct:.1f}% of pixels changed "
                   f"above the {threshold}-intensity threshold")
        disconfirm = ("changed regions may be benign lighting/color variation, "
                      "not a true defect — cross-check with zoom_bbox on bright regions")
    return _wrap_interpretation(out, verdict, disconfirm)


def tool_rotate_align(query_path: str, ref_path: str | None = None,
                      ref_paths: list[str] | None = None, ref_idx: int = 0,
                      **_) -> dict:
    """Try rotations [-10,-5,0,5,10] deg on ref, pick min-MSE, then return aligned diff."""
    if ref_path is None and ref_paths:
        try:
            ref_path = ref_paths[int(ref_idx)]
        except (IndexError, ValueError):
            return {"error": f"ref_idx {ref_idx} out of range"}
    if not ref_path or not os.path.exists(ref_path):
        return {"error": f"ref_path not found: {ref_path!r}"}
    q = np.array(Image.open(query_path).convert("RGB").resize((256, 256)))
    r_img = Image.open(ref_path).convert("RGB").resize((256, 256))
    best_angle, best_mse, best_diff = 0.0, float("inf"), None
    for angle in [-10, -5, 0, 5, 10]:
        r_rot = np.array(r_img.rotate(angle, resample=Image.BILINEAR))
        d = np.abs(q.astype(float) - r_rot.astype(float)).mean(axis=2)
        mse = float(d.mean())
        if mse < best_mse:
            best_mse, best_angle, best_diff = mse, angle, d
    mask = (best_diff > 30.0).astype(np.uint8) * 255
    unreliable = best_mse > 40.0
    out = {
        "rotation_angle_deg": float(best_angle),
        "aligned_mean_diff": float(best_mse),
        "unreliable_alignment": unreliable,
        "aligned_diff_b64": _pil_to_b64(Image.fromarray(mask, mode="L").convert("RGB"),
                                        max_side=256),
        "error": None,
    }
    if unreliable:
        verdict = (f"UNRELIABLE: even the best rotation ({best_angle}°) yields "
                   f"mean diff {best_mse:.1f} — query and ref cannot be aligned; "
                   f"do NOT use this tool's output")
        disconfirm = ("treat as no evidence; rely on other tools or direct inspection")
    else:
        verdict = (f"best rotation {best_angle}°, post-alignment mean diff "
                   f"{best_mse:.1f}; diff mask shows residual change")
        disconfirm = ("post-alignment residual may still be lighting/color variation; "
                      "confirm with zoom_bbox on suspicious bright regions")
    return _wrap_interpretation(out, verdict, disconfirm)


def tool_side_by_side(query_path: str, bbox: list[int],
                      ref_paths: list[str] | None = None, **_) -> dict:

exec
/bin/bash -lc "sed -n '1,300p' benchmark/scripts/build_tool_card.py" in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
"""Slice a single-tool audit result by multiple axes, find niches where the
tool beats Direct, emit a tool_card.md.

Slices:
  - domain (per-domain AUROC)
  - direct_margin bucket (uncertain / confident)
  - expert_score bucket (subspacead rank: low/mid/high)
  - tool_used True/False
  - n_turns bucket (1 / 2-3)

Niche = slice with n >= threshold AND Δ_AUROC > 0 AND bootstrap 95% CI
lower-bound > 0.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

N_BOOT = 1000
RNG = np.random.default_rng(42)


def _safe_auroc(y, s):
    y, s = np.asarray(y), np.asarray(s)
    if len(y) < 5 or len(set(y)) < 2:
        return np.nan
    return float(roc_auc_score(y, s))


def macro_auroc_from_results(items, min_n_per_domain: int = 3):
    by_d: dict[str, list] = {}
    for x in items:
        if x.get("label_gt") is None:
            continue
        by_d.setdefault(x.get("domain_code"), []).append(x)
    aurocs = []
    for d, arr in by_d.items():
        if len(arr) < min_n_per_domain:
            continue
        y = [i["label_gt"] for i in arr]
        s = [i["anomaly_score"] for i in arr]
        auc = _safe_auroc(y, s)
        if not np.isnan(auc):
            aurocs.append(auc)
    return float(np.mean(aurocs)) if aurocs else np.nan


def slice_macro_delta(pairs: list[tuple[dict, dict]], slice_fn, slice_name: str):
    """Return {'slice', 'n', 'auroc_tool', 'auroc_direct', 'delta',
    'delta_ci'} for the subset where slice_fn(tool_item, direct_item) is True.

    AUROC is macro over domains represented in the subset, falling back to
    pooled AUROC when too few per-domain samples.
    """
    subset = [(t, d) for t, d in pairs if slice_fn(t, d)]
    if len(subset) < 5:
        return None
    tools = [t for t, _ in subset]
    drs = [d for _, d in subset]

    # Check label diversity
    y = [t["label_gt"] for t in tools]
    if len(set(y)) < 2:
        return None

    # Try macro; fall back to pooled if not enough domains
    a_tool = macro_auroc_from_results(tools)
    a_direct = macro_auroc_from_results(drs)
    if np.isnan(a_tool) or np.isnan(a_direct):
        # pooled
        s_t = [t["anomaly_score"] for t in tools]
        s_d = [d["anomaly_score"] for d in drs]
        a_tool = _safe_auroc(y, s_t)
        a_direct = _safe_auroc(y, s_d)
        if np.isnan(a_tool) or np.isnan(a_direct):
            return None

    # Bootstrap paired delta (pooled AUROC basis)
    s_t_arr = np.asarray([t["anomaly_score"] for t in tools])
    s_d_arr = np.asarray([d["anomaly_score"] for d in drs])
    y_arr = np.asarray(y)
    n = len(y_arr)
    deltas = []
    for _ in range(N_BOOT):
        idx = RNG.integers(0, n, n)
        if len(set(y_arr[idx])) < 2:
            continue
        try:
            dt = (roc_auc_score(y_arr[idx], s_t_arr[idx])
                  - roc_auc_score(y_arr[idx], s_d_arr[idx]))
            deltas.append(dt)
        except Exception:
            continue
    if not deltas:
        return None
    return {
        "slice": slice_name,
        "n": n,
        "auroc_tool": float(a_tool),
        "auroc_direct": float(a_direct),
        "delta": float(a_tool - a_direct),
        "delta_ci": [float(np.percentile(deltas, 2.5)),
                     float(np.percentile(deltas, 97.5))],
    }


def _load_expert_rank_map(split: str):
    """Return item_id -> subspacead normalized_rank for direct_margin / expert
    slicing. Uses the same method as tool_expert_score."""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from agent_tools_v7 import _load_expert_scores
        recs, all_scores = _load_expert_scores("subspacead", split)
        if len(all_scores) == 0:
            return {}
        rank_map = {}
        for iid, rec in recs.items():
            if rec.get("anomaly_score") is None:
                continue
            s = float(rec["anomaly_score"])
            rank_map[iid] = float(np.searchsorted(all_scores, s) / len(all_scores))
        return rank_map
    except Exception:
        return {}


def build_slices(direct_results: list, split: str):
    rank_map = _load_expert_rank_map(split)
    domains = sorted({x.get("domain_code") for x in direct_results
                      if x.get("domain_code") is not None})
    slices: list[tuple[str, callable]] = []
    for d in domains:
        slices.append((f"domain={d}",
                       lambda t, _d, d=d: t.get("domain_code") == d))
    slices.append(("direct_margin<0.15 (uncertain)",
                   lambda t, d: abs(d.get("anomaly_score", 0.5) - 0.5) < 0.15))
    slices.append(("direct_margin>=0.30 (confident)",
                   lambda t, d: abs(d.get("anomaly_score", 0.5) - 0.5) >= 0.30))
    slices.append(("tool_used=True",
                   lambda t, d: bool(t.get("used_tool"))))
    slices.append(("tool_used=False",
                   lambda t, d: not bool(t.get("used_tool"))))
    if rank_map:
        slices.append(("subspacead_rank<=0.4 (weak expert)",
                       lambda t, d, rm=rank_map:
                       rm.get(t.get("item_id"), 0.5) <= 0.4))
        slices.append(("subspacead_rank in [0.4,0.8) (moderate expert)",
                       lambda t, d, rm=rank_map:
                       0.4 < rm.get(t.get("item_id"), 0.5) < 0.8))
        slices.append(("subspacead_rank>=0.8 (strong expert)",
                       lambda t, d, rm=rank_map:
                       rm.get(t.get("item_id"), 0.5) >= 0.8))
    slices.append(("n_turns=1 (no tool, tool-offered)",
                   lambda t, d: t.get("n_turns") == 1))
    slices.append(("n_turns>=2 (actually explored)",
                   lambda t, d: t.get("n_turns") is not None and t.get("n_turns") >= 2))
    return slices


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tool_file", required=True)
    ap.add_argument("--direct_file", required=True)
    ap.add_argument("--out_md", required=True)
    ap.add_argument("--split", default="dev")
    ap.add_argument("--threshold_n", type=int, default=10)
    args = ap.parse_args()

    tool_results = json.load(open(args.tool_file))
    direct_results = json.load(open(args.direct_file))
    tool_name = Path(args.tool_file).stem

    direct_by_id = {x["item_id"]: x for x in direct_results}
    pairs = [(t, direct_by_id[t["item_id"]]) for t in tool_results
             if t.get("item_id") in direct_by_id
             and t.get("label_gt") is not None]

    overall = {
        "tool": tool_name,
        "n_total": len(pairs),
        "n_called": sum(1 for t, _ in pairs if t.get("used_tool")),
        "n_errors": sum(1 for t, _ in pairs if t.get("error")),
        "full_tool_macro": macro_auroc_from_results([t for t, _ in pairs]),
        "full_direct_macro": macro_auroc_from_results([d for _, d in pairs]),
    }
    overall["full_delta"] = (overall["full_tool_macro"]
                             - overall["full_direct_macro"])
    overall["call_rate"] = (overall["n_called"] / overall["n_total"] * 100
                            if overall["n_total"] else 0)

    slices = build_slices(direct_results, args.split)
    findings = []
    for name, fn in slices:
        res = slice_macro_delta(pairs, fn, name)
        if res and res["n"] >= args.threshold_n:
            findings.append(res)
    findings.sort(key=lambda x: -x["delta"])

    positive_niches = [f for f in findings
                       if f["delta"] > 0 and f["delta_ci"][0] > 0]
    anti = [f for f in findings
            if f["delta"] < 0 and f["delta_ci"][1] < 0]
    verdict = "KEEP" if positive_niches else "DROP"

    lines: list[str] = [
        f"# Tool Card: {tool_name}",
        "",
        f"**Verdict:** {verdict}  ",
        f"**Overall (dev n={overall['n_total']})**: tool={overall['full_tool_macro']:.4f}  "
        f"direct={overall['full_direct_macro']:.4f}  Δ={overall['full_delta']:+.4f}  ",
        f"**Calls**: {overall['n_called']}/{overall['n_total']} "
        f"({overall['call_rate']:.1f}%)  ",
        f"**Errors**: {overall['n_errors']}  ",
        "",
        "## Positive niches (n≥{}, Δ>0, 95% CI lower > 0)".format(args.threshold_n),
        "",
    ]
    if not positive_niches:
        lines += ["_None found. Tool has no demonstrated niche on dev._", ""]
    else:
        lines.append("| slice | n | tool AUROC | direct AUROC | Δ | 95% CI |")
        lines.append("|---|---|---|---|---|---|")
        for f in positive_niches:
            lines.append(f"| {f['slice']} | {f['n']} | {f['auroc_tool']:.3f} | "
                         f"{f['auroc_direct']:.3f} | {f['delta']:+.3f} | "
                         f"[{f['delta_ci'][0]:+.3f}, {f['delta_ci'][1]:+.3f}] |")
        lines.append("")

    lines += ["## Anti-niches (Δ<0, 95% CI upper < 0)", ""]
    if not anti:
        lines += ["_None flagged._", ""]
    else:
        lines.append("| slice | n | tool AUROC | direct AUROC | Δ | 95% CI |")
        lines.append("|---|---|---|---|---|---|")
        for f in anti:
            lines.append(f"| {f['slice']} | {f['n']} | {f['auroc_tool']:.3f} | "
                         f"{f['auroc_direct']:.3f} | {f['delta']:+.3f} | "
                         f"[{f['delta_ci'][0]:+.3f}, {f['delta_ci'][1]:+.3f}] |")
        lines.append("")

    lines += ["## All slices (audit)", ""]
    lines.append("| slice | n | tool | direct | Δ | 95% CI |")
    lines.append("|---|---|---|---|---|---|")
    for f in findings:
        lines.append(f"| {f['slice']} | {f['n']} | {f['auroc_tool']:.3f} | "
                     f"{f['auroc_direct']:.3f} | {f['delta']:+.3f} | "
                     f"[{f['delta_ci'][0]:+.3f}, {f['delta_ci'][1]:+.3f}] |")
    lines.append("")

    lines += ["## Agent hint (injected into agent_v7 prompt if KEEP)", ""]
    if positive_niches:
        best = positive_niches[0]
        lines.append(f"**When to use {tool_name}:** especially helpful on "
                     f"`{best['slice']}` (Δ={best['delta']:+.3f} on n={best['n']}).")
    else:
        lines.append(f"**When to use {tool_name}:** no documented positive niche "
                     f"on dev. DROPPED.")
    if anti:
        worst = min(anti, key=lambda x: x["delta"])
        lines.append(f"**Avoid {tool_name} on:** `{worst['slice']}` "
                     f"(Δ={worst['delta']:+.3f} on n={worst['n']}).")
    lines.append("")

    Path(args.out_md).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out_md, "w") as f:
        f.write("\n".join(lines))
    print(f"wrote {args.out_md}  verdict={verdict}  "
          f"pos={len(positive_niches)} anti={len(anti)}")


if __name__ == "__main__":
    main()

codex
The monkeypatch itself is visible now: `ReActAgent` reads `SYSTEM_PROMPT` and `dispatch_tool` as `agent_v6` module globals at call time, so the patch is picked up. I’m checking the less obvious failure modes next: context propagation, prompt import side effects, keep-gate behavior, and the slice statistics.
exec
/bin/bash -lc "sed -n '360,920p' benchmark/scripts/agent_tools_v7.py" in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
                      ref_paths: list[str] | None = None, **_) -> dict:
    """Composite: query_crop | ref0_crop | ref1_crop | ref2_crop | ref3_crop.

    bbox is interpreted in 256x256 normalized coords (resize all images to 256).
    """
    if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        return {"error": "bbox must be [x0, y0, x1, y1]"}
    x0, y0, x1, y1 = [int(v) for v in bbox]
    if x1 <= x0 or y1 <= y0:
        return {"error": f"invalid bbox {bbox}"}
    if not ref_paths:
        return {"error": "no ref_paths in session"}
    def _crop(path):
        img = Image.open(path).convert("RGB").resize((256, 256))
        xa = max(0, min(255, x0)); ya = max(0, min(255, y0))
        xb = max(xa + 1, min(256, x1)); yb = max(ya + 1, min(256, y1))
        return img.crop((xa, ya, xb, yb)).resize((128, 128))
    crops = [_crop(query_path)] + [_crop(p) for p in ref_paths[:4]]
    total_w = 128 * len(crops)
    composite = Image.new("RGB", (total_w, 128), (255, 255, 255))
    for i, c in enumerate(crops):
        composite.paste(c, (i * 128, 0))
    out = {
        "bbox": bbox,
        "n_crops": len(crops),
        "composite_b64": _pil_to_b64(composite, max_side=768),
        "error": None,
    }
    verdict = ("side-by-side composite (query | ref0 | ref1 | ref2 | ref3); "
               "look for a structural/textural feature present ONLY in query")
    disconfirm = ("refs themselves show natural variation; a feature that is "
                  "slightly different in degree but present across samples is NORMAL")
    return _wrap_interpretation(out, verdict, disconfirm)


# ─── Tier 3: Reference understanding ────────────────────────────────────────

PROFILER_SYSTEM = (
    "You are describing NORMAL reference images for anomaly detection. Output ONLY "
    "what normal looks like — do NOT speculate about anomalies. Return JSON with "
    "these EXACT fields, each a single short phrase:\n"
    "  object: the main object/scene content (one noun phrase)\n"
    "  expected_color: 2-3 dominant colors\n"
    "  expected_shape: overall geometric/structural pattern (one phrase)\n"
    "  allowed_variation: list 2-4 variations that are NORMAL across refs "
    "(e.g. 'minor rotation', 'lighting shift', 'minor texture variation')\n"
    "Do NOT include anomaly hypotheses. JSON format: "
    "{\"object\": \"...\", \"expected_color\": \"...\", \"expected_shape\": \"...\", "
    "\"allowed_variation\": [\"...\", \"...\"]}"
)


def tool_reference_profiler(ref_paths: list[str] | None = None,
                            vlm_client=None, vlm_model: str | None = None,
                            max_tokens: int = 400, **_) -> dict:
    """Ask a VLM to describe the normality profile from 4 refs."""
    if os.environ.get("ANOMA_TEST_STUB") == "1":
        return {
            "error": None,
            "profile_text": "stub profile",
            "common_objects": ["stub"],
            "typical_colors": [],
            "variations": [],
            "n_refs_used": len(ref_paths[:4]) if ref_paths else 0,
        }
    if not ref_paths:
        return {"error": "no ref_paths"}
    if vlm_client is None or vlm_model is None:
        return {"error": "vlm_client and vlm_model required"}
    parts = [text_msg(PROFILER_SYSTEM)]
    for p in ref_paths[:4]:
        parts.append(img_msg(load_and_encode(p)))
    parts.append(text_msg("Profile these 4 normal references using ONLY the 4 fields listed."))
    messages = [{"role": "user", "content": parts}]
    try:
        text, _, _ = call_llm(vlm_client, vlm_model, messages,
                              max_tokens=max_tokens, temperature=0.0)
    except Exception as e:
        return {"error": f"vlm call failed: {e}"}
    parsed = extract_json(text) or {}
    out = {
        "error": None,
        "object": parsed.get("object", ""),
        "expected_color": parsed.get("expected_color", ""),
        "expected_shape": parsed.get("expected_shape", ""),
        "allowed_variation": parsed.get("allowed_variation", []),
        "n_refs_used": len(ref_paths[:4]),
    }
    verdict = (f"normal-baseline profile extracted: object='{out['object']}', "
               f"shape='{out['expected_shape']}', allowed variations: "
               f"{out['allowed_variation']}")
    disconfirm = ("the query exhibits a variation LISTED in allowed_variation — in "
                  "that case it is NORMAL, not anomalous. Also: profiler only describes "
                  "what refs have in common; it cannot detect anomalies by itself")
    return _wrap_interpretation(out, verdict, disconfirm)


_RETRIEVAL_CACHE: dict[str, Any] = {}


def _load_retrieval_model_v6(device: str = "cuda"):
    if "model" in _RETRIEVAL_CACHE:
        return _RETRIEVAL_CACHE["model"], _RETRIEVAL_CACHE["transform"]
    import torch
    import timm
    model = timm.create_model("vit_small_patch14_dinov2.lvd142m",
                              pretrained=True, num_classes=0)
    model = model.to(device).eval()
    cfg = timm.data.resolve_data_config(model.pretrained_cfg)
    transform = timm.data.create_transform(**cfg, is_training=False)
    _RETRIEVAL_CACHE["model"] = model
    _RETRIEVAL_CACHE["transform"] = transform
    return model, transform


def tool_reference_retriever(query_path: str, domain_code: str | None = None,
                             k: int = 4,
                             index_dir: str = "/hdd1/jiangxi/AD-Agent/benchmark/retrieval_index",
                             device: str = "cuda",
                             item_id: str | None = None,
                             _manifest_domain: str | None = None, **_) -> dict:
    """Retrieve top-k most similar normal references via DINOv2 similarity.

    `domain_code` may be provided by the agent; if not, we try `_manifest_domain`
    (auto-injected from session ctx; this is the only place the agent legitimately
    uses the domain code — to locate its cached normality bank, not for modeling).
    """
    domain_code = domain_code or _manifest_domain
    if not domain_code:
        return {"error": "domain_code required to locate retrieval index"}
    idx_path = os.path.join(index_dir, f"{domain_code}_index.npz")
    if not os.path.exists(idx_path):
        return {"error": f"no retrieval index at {idx_path}"}
    try:
        import torch
        model, transform = _load_retrieval_model_v6(device)
        img = Image.open(query_path).convert("RGB")
        tensor = transform(img).unsqueeze(0).to(device)
        with torch.no_grad():
            emb = model(tensor).cpu().numpy().flatten()
        emb = emb / (np.linalg.norm(emb) + 1e-8)
        data = np.load(idx_path, allow_pickle=True)
        sims = data["embeddings"] @ emb
        top_idx = np.argsort(sims)[::-1][:k]
        results = [{"path": str(data["paths"][i]),
                    "similarity": float(sims[i])} for i in top_idx]
        out = {"results": results, "error": None,
               "top_similarity": float(sims[top_idx[0]]) if len(top_idx) else 0.0}
        verdict = (f"top-{k} most similar NORMAL refs retrieved "
                   f"(top_similarity={out['top_similarity']:.3f})")
        disconfirm = ("high top_similarity means the query matches a normal cluster "
                      "well → likely NORMAL. Low similarity alone does NOT prove anomaly "
                      "— the query may just be in a less-represented normal subtype")
        return _wrap_interpretation(out, verdict, disconfirm)
    except Exception as e:
        return {"error": f"retrieval failed: {e}"}


# ─── Tier 4: Structural analysis ────────────────────────────────────────────

def tool_component_counter(patches: list[dict] | None = None,
                           _expert_patches: list | None = None,
                           threshold: float = 0.5, **_) -> dict:
    """Count connected components among top-k expert patches (48x48 grid, 4-conn)."""
    patches = patches or _expert_patches or []
    # v7: require at least 3 hotspot patches for component count to be meaningful
    if len(patches) < 3:
        out = {"error": None, "n_components": 0, "n_active_patches": len(patches),
               "not_applicable": True}
        verdict = (f"not applicable: only {len(patches)} expert patch(es) available; "
                   f"component counting needs >=3 patches to be meaningful")
        disconfirm = "ignore this tool's output for this sample"
        return _wrap_interpretation(out, verdict, disconfirm)
    grid = np.zeros((48, 48), dtype=np.uint8)
    for p in patches:
        r, c = p.get("row"), p.get("col")
        if r is not None and c is not None and 0 <= r < 48 and 0 <= c < 48:
            grid[r, c] = 1
    n, seen = 0, np.zeros_like(grid, dtype=bool)
    for i in range(48):
        for j in range(48):
            if grid[i, j] and not seen[i, j]:
                n += 1
                stack = [(i, j)]
                while stack:
                    ii, jj = stack.pop()
                    if (0 <= ii < 48 and 0 <= jj < 48 and grid[ii, jj]
                            and not seen[ii, jj]):
                        seen[ii, jj] = True
                        stack.extend([(ii+1, jj), (ii-1, jj),
                                      (ii, jj+1), (ii, jj-1)])
    n_active = int(grid.sum())
    out = {"error": None, "n_components": int(n),
           "n_active_patches": n_active, "not_applicable": False}
    verdict = (f"{n} connected hotspot blob(s) across {n_active} active patches; "
               f"many small blobs = diffuse anomaly, one large blob = localised defect")
    disconfirm = ("expert hotspots may be spread across normal high-variance regions "
                  "without a true defect; cross-check with zoom_bbox")
    return _wrap_interpretation(out, verdict, disconfirm)


def tool_segment_and_count(query_path: str, ref_paths: list[str] | None = None,
                           grid_size: int = 8, **_) -> dict:
    """Coarse structural-change signal via 8x8 intensity-grid diff vs ref 0."""
    if not ref_paths:
        return {"error": "ref_paths required"}
    q = np.array(Image.open(query_path).convert("L").resize((256, 256)))
    r = np.array(Image.open(ref_paths[0]).convert("L").resize((256, 256)))
    cell = 256 // grid_size
    q_grid = q.reshape(grid_size, cell, grid_size, cell).mean(axis=(1, 3))
    r_grid = r.reshape(grid_size, cell, grid_size, cell).mean(axis=(1, 3))
    diff = np.abs(q_grid - r_grid)
    changed = int((diff > 20).sum())
    top_idx = np.argsort(diff.ravel())[::-1][:5]
    top_diffs = [{"row": int(i // grid_size), "col": int(i % grid_size),
                  "diff": float(diff.ravel()[i])} for i in top_idx
                 if diff.ravel()[i] > 10]
    out = {
        "error": None,
        "changed_cells": changed,
        "total_cells": grid_size * grid_size,
        "change_ratio": round(changed / (grid_size * grid_size), 3),
        "top_differences": top_diffs,
    }
    verdict = (f"{changed}/{out['total_cells']} coarse cells changed > threshold "
               f"(ratio {out['change_ratio']})")
    disconfirm = ("coarse diff is sensitive to global intensity shift (lighting, "
                  "exposure, dye/contrast); not conclusive evidence of a defect")
    return _wrap_interpretation(out, verdict, disconfirm)


def tool_texture_fft(query_path: str, **_) -> dict:
    """FFT periodicity score: top-10 peak energy / total spectrum energy."""
    img = np.array(Image.open(query_path).convert("L").resize((256, 256))).astype(float)
    img -= img.mean()
    spec = np.abs(np.fft.fftshift(np.fft.fft2(img)))
    h, w = spec.shape
    cy, cx = h // 2, w // 2
    spec[cy - 3:cy + 3, cx - 3:cx + 3] = 0
    total = float(spec.sum()) + 1e-8
    top_k = float(np.sort(spec.ravel())[::-1][:10].sum())
    score = float(top_k / total)
    periodicity = min(1.0, max(0.0, score))
    out = {"error": None, "periodicity_score": periodicity}
    if periodicity > 0.15:
        verdict = (f"periodic texture detected (score {periodicity:.3f}); a regular "
                   f"repeating pattern is present")
        disconfirm = ("periodicity alone does not indicate defect — many normal "
                      "textures (fabric, grid, lattice) are highly periodic")
    else:
        verdict = (f"low periodicity (score {periodicity:.3f}); texture is irregular")
        disconfirm = ("irregular texture is normal for many domains (natural scenes, "
                      "tissue); do NOT use this alone to flag anomaly")
    return _wrap_interpretation(out, verdict, disconfirm)


# ─── Tier 5: Semantic knowledge ─────────────────────────────────────────────

KNOWLEDGE_SYSTEM = (
    "You are a domain knowledge assistant for visual anomaly detection. "
    "Answer the question in 2-4 sentences with concrete visual details. "
    "Do not hedge. Return JSON: {\"answer\": \"...\"}"
)


def tool_domain_knowledge(question: str, llm_client=None,
                          llm_model: str | None = None,
                          vlm_client=None, vlm_model: str | None = None,
                          max_tokens: int = 300, **_) -> dict:
    """Text-only LLM query. Agent phrases its own question; no domain hint baked in."""
    if os.environ.get("ANOMA_TEST_STUB") == "1":
        return {"error": None, "answer": f"[stub] re: {question}"}
    client = llm_client or vlm_client
    model = llm_model or vlm_model
    if client is None or model is None:
        return {"error": "llm_client and llm_model required"}
    messages = [
        {"role": "system", "content": KNOWLEDGE_SYSTEM},
        {"role": "user", "content": question},
    ]
    try:
        text, _, _ = call_llm(client, model, messages,
                              max_tokens=max_tokens, temperature=0.0)
    except Exception as e:
        return {"error": f"llm call failed: {e}"}
    parsed = extract_json(text) or {}
    out = {"error": None, "answer": parsed.get("answer", text.strip()[:300])}
    verdict = "text-only LLM answer returned"
    disconfirm = ("the LLM may hallucinate or give generic advice that doesn't match "
                  "this specific image; always cross-check against the visual evidence "
                  "before updating your score")
    return _wrap_interpretation(out, verdict, disconfirm)


# ─── Dispatcher ─────────────────────────────────────────────────────────────

TOOL_REGISTRY = {
    "tool_expert_score":        tool_expert_score,
    "tool_hotspot_cropper":     tool_hotspot_cropper,
    "tool_zoom_bbox":           tool_zoom_bbox,
    "tool_patch_grid":          tool_patch_grid,
    "tool_image_diff":          tool_image_diff,
    "tool_rotate_align":        tool_rotate_align,
    "tool_side_by_side":        tool_side_by_side,
    "tool_reference_profiler":  tool_reference_profiler,
    "tool_reference_retriever": tool_reference_retriever,
    "tool_component_counter":   tool_component_counter,
    "tool_segment_and_count":   tool_segment_and_count,
    "tool_texture_fft":         tool_texture_fft,
    "tool_domain_knowledge":    tool_domain_knowledge,
}


PROTECTED_CTX_KEYS = (
    "query_path", "ref_paths", "item_id", "split",
    "vlm_client", "vlm_model", "llm_client", "llm_model",
    "_expert_patches", "_manifest_domain", "index_dir",
)


def dispatch_tool(name: str, args: dict, ctx: dict | None = None) -> dict:
    """Dispatch a tool call. ctx carries session state that tools need but
    that the VLM shouldn't re-type (query_path, ref_paths, split, clients).

    PROTECTED_CTX_KEYS are ALWAYS taken from ctx — model-supplied args for
    those keys are dropped (prevents VLM from redirecting a tool to
    different item/split by crafting malicious args).
    """
    if name not in TOOL_REGISTRY:
        return {"error": f"unknown tool {name!r}; must be one of {sorted(TOOL_REGISTRY)}"}
    ctx = ctx or {}
    fn = TOOL_REGISTRY[name]
    # Start from sanitized model args: drop protected keys
    injected = {k: v for k, v in (args or {}).items() if k not in PROTECTED_CTX_KEYS}
    # Overlay ctx (ctx wins over model args for protected fields)
    for k in PROTECTED_CTX_KEYS:
        if k in ctx:
            injected[k] = ctx[k]
    try:
        return fn(**injected)
    except TypeError as e:
        return {"error": f"bad args for {name}: {e}"}
    except Exception as e:
        return {"error": f"{name} raised {type(e).__name__}: {e}"}


# ─── KEEP-gated dispatch (used by agent_v7 after audit is complete) ─────────

_KEEP_TOOLS: set[str] | None = None


def _load_keep_tools() -> set[str]:
    """Load KEEP set from refine-logs/tool_cards/*.md.

    Fallback: if no cards exist or none are KEEP, return all registered tools
    (single-tool audit runs BEFORE tool cards exist, so they must not be gated).
    """
    global _KEEP_TOOLS
    cards = Path(__file__).resolve().parent.parent.parent / "refine-logs" / "tool_cards"
    keep: set[str] = set()
    if cards.exists():
        for md in cards.glob("*.md"):
            try:
                text = md.read_text()
            except OSError:
                continue
            if "**Verdict:** KEEP" in text:
                keep.add(md.stem)
    if not keep:
        keep = set(TOOL_REGISTRY.keys())
    _KEEP_TOOLS = keep
    return keep


def dispatch_tool_keep_only(name: str, args: dict, ctx: dict | None = None) -> dict:
    """Same as dispatch_tool but refuses tools not in the KEEP set.

    agent_v7 uses this; audit runs use the un-gated dispatch_tool.
    """
    global _KEEP_TOOLS
    if _KEEP_TOOLS is None:
        _load_keep_tools()
    if name not in (_KEEP_TOOLS or set()):
        return {"error": (f"{name} is not a v7 KEEP tool; allowed set: "
                          f"{sorted(_KEEP_TOOLS or [])}")}
    return dispatch_tool(name, args, ctx)

exec
/bin/bash -lc "sed -n '1,320p' benchmark/scripts/agent_prompt_v7.py" in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
"""Agent v7 system prompt + tool catalog + empirical tool hints.

Changes from v6:
- Introduces TOOL_OUTPUT_GUIDE that advertises the interpretation/disconfirm
  format from agent_tools_v7.
- Imports TOOL_HINTS from agent_tool_hints_v7 (auto-generated from
  refine-logs/tool_cards/*.md) so the agent sees which tools have
  documented positive niches and which have anti-niches.
"""
from __future__ import annotations

TOOL_OUTPUT_GUIDE = """Every tool returns an `interpretation` field with two parts:
  1. VERDICT HINT — what the observation is suggesting.
  2. DISCONFIRM CLAUSE — when the signal does NOT mean anomaly.
ALWAYS read BOTH parts before updating your score. A strong-looking signal that
also satisfies the disconfirm clause is NOT evidence of anomaly. Tools that
return `unreliable_alignment: true` or `not_applicable: true` should be
ignored for the current sample."""


TOOL_CATALOG = """Available tools (call at most one per turn):

EXPERT PROBES
  tool_expert_score(expert="subspacead"|"anomalyvfm"|"patchknn"|"dinov2_global")
    Returns {score, normalized_rank, interpretation, top_patches}.
    rank>=0.85 => strong. rank<=0.6 weak. Moderate in between. Calling this with
    expert="subspacead" also makes patch hotspots available to hotspot_cropper /
    component_counter.

VISUAL INSPECTION
  tool_hotspot_cropper(k=5)
    Zooms into the top-k subspacead hotspots. Requires a prior
    tool_expert_score(expert="subspacead") call.
  tool_zoom_bbox(bbox=[x0,y0,x1,y1])
    Agent-specified pixel crop of the query. Use for localised-defect hypothesis.
  tool_patch_grid(rows=N, cols=M)
    Cuts the query into N x M tiles (capped at 3x3).
  tool_image_diff(ref_idx=0..3)
    Pixel diff vs the ref_idx-th reference; returns stats + mask + unreliable flag.
    AVOID when images are not spatially aligned (natural scenes, medical slices,
    rotated industrial parts).
  tool_rotate_align(ref_idx=0..3)
    Like image_diff but tries small rotations first. Still unreliable on
    non-rigid images.
  tool_side_by_side(bbox=[x0,y0,x1,y1])
    Composite showing query + 4 refs all cropped to same bbox. bbox is in
    256x256 normalized coords.

REFERENCE UNDERSTANDING
  tool_reference_profiler()
    VLM describes the NORMAL baseline in 4 fields (object / expected_color /
    expected_shape / allowed_variation). Use when you need to know what
    variation IS allowed in refs before judging the query.
  tool_reference_retriever(k=4)
    Re-pulls k refs more similar to the query from the domain's full
    normal pool.

STRUCTURAL
  tool_component_counter()
    Connected-component count among subspacead hotspots. Needs >=3 hotspot
    patches to be meaningful.
  tool_segment_and_count()
    Coarse 8x8 grid diff vs ref 0 — rough structural change signal.
  tool_texture_fft()
    Periodicity score (0=irregular, 1=strongly periodic texture).

SEMANTIC
  tool_domain_knowledge(question="...")
    Free-form text question answered by an LLM. LLM may hallucinate —
    always cross-check with visual evidence.
"""


try:
    from agent_tool_hints_v7 import TOOL_HINTS  # auto-generated by compose_v7_prompt.py
except ImportError:
    TOOL_HINTS = "(tool hints not yet generated — running un-hinted)"


SYSTEM_PROMPT = f"""You are a visual anomaly detection agent.

INPUT PER IMAGE: one query image, four normal reference images, a turn budget.
TASK: decide if the query is normal or anomalous and output a score in [0,1]
where 1 means certainly anomalous.

YOU HAVE NO DOMAIN INFORMATION. Figure out what the images are from vision
alone. The tools below can help you probe further.

{TOOL_OUTPUT_GUIDE}

{TOOL_CATALOG}

EMPIRICAL TOOL PERFORMANCE (observed on a held-out dev set; use as general
guidance, not as a decision for this specific image):
{TOOL_HINTS}

PROTOCOL: On each turn, return ONLY a JSON object:
{{
  "thought":  "<one or two sentences>",
  "action":   "call_tool" | "final",
  "tool":     "<tool_name>" | null,
  "args":     {{ ... }} | null,
  "confidence": <integer 0..100>,
  "score":    <float 0..1> | null,
  "rationale": "<one or two sentences>" | null
}}

Required if action=="final": score and rationale.
Required if action=="call_tool": tool and args.

GUIDELINES:
- Use a tool only if it will change your answer. If the query looks clearly
  normal or anomalous at turn 1, output final without calling any tool.
- READ the disconfirm clause of every tool output. A positive-looking signal
  that satisfies the disconfirm clause is NOT evidence of anomaly.
- Prefer tools with documented positive niches on this kind of input.
- Avoid tools on inputs that match their anti-niche.
- Each tool call costs one turn. Budget is tight.
- Return valid JSON only. No prose outside the JSON.
"""


def forced_final_prompt(budget: int) -> str:
    return (
        f"THIS IS YOUR LAST TURN ({budget}/{budget}). "
        f"action MUST be \"final\". Produce your best score and rationale "
        f"based on all observations so far."
    )


def budget_warning_prompt(remaining: int) -> str:
    if remaining <= 1:
        return "1 turn remaining — prepare to produce final."
    return f"{remaining} turns remaining."

exec
/bin/bash -lc "sed -n '1,260p' benchmark/scripts/tool_audit_runner.py" in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
"""Queue 13 single-tool audits sequentially; each uses max_workers concurrency
internally. Sequential across tools avoids rate-limit bleed between audits.
"""
from __future__ import annotations
import argparse
import subprocess
import sys
import time
from pathlib import Path

TOOLS = [
    "tool_zoom_bbox",           # +7pp in v6.5 (only positive tool); validate
    "tool_expert_score",        # 76% coverage; largest lever
    "tool_hotspot_cropper",
    "tool_side_by_side",
    "tool_image_diff",
    "tool_reference_profiler",  # worst offender -9.4pp
    "tool_component_counter",
    "tool_patch_grid",
    "tool_rotate_align",         # -28pp in v6.5 — gate aggressively
    "tool_domain_knowledge",
    "tool_segment_and_count",
    "tool_texture_fft",          # never called in v6.5
    "tool_reference_retriever",  # never called in v6.5
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest",
                    default="benchmark/manifests/full_manifest.json")
    ap.add_argument("--split", default="dev")
    ap.add_argument("--out_dir", default="benchmark/results/tool_audit")
    ap.add_argument("--max_turns", type=int, default=3)
    ap.add_argument("--max_workers", type=int, default=9)
    ap.add_argument("--tools", nargs="*", default=None,
                    help="subset of tools (default: all)")
    ap.add_argument("--skip_existing", action="store_true", default=True)
    args = ap.parse_args()

    Path(args.out_dir).mkdir(parents=True, exist_ok=True)
    tools = args.tools or TOOLS
    script = "benchmark/scripts/single_tool_agent.py"

    t0 = time.time()
    for i, tool in enumerate(tools, 1):
        out = f"{args.out_dir}/{tool}.json"
        if args.skip_existing and Path(out).exists():
            print(f"[{i}/{len(tools)}] skip {tool}: {out} exists", flush=True)
            continue
        cmd = [sys.executable, script,
               "--tool", tool, "--split", args.split,
               "--manifest", args.manifest, "--output", out,
               "--max_turns", str(args.max_turns),
               "--max_workers", str(args.max_workers)]
        t_tool = time.time()
        print(f"[{i}/{len(tools)}] running {tool} ...", flush=True)
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"[{i}/{len(tools)}] FAIL {tool}: rc={r.returncode}\n"
                  f"stderr tail:\n{r.stderr[-800:]}", flush=True)
            with open(f"{args.out_dir}/{tool}.stderr.log", "w") as f:
                f.write(r.stderr)
        else:
            print(f"[{i}/{len(tools)}] OK   {tool}  "
                  f"t_tool={time.time()-t_tool:.1f}s  "
                  f"t_total={time.time()-t0:.1f}s", flush=True)
            # echo last line of child stdout
            last = r.stdout.strip().splitlines()
            if last:
                print(f"          {last[-1]}", flush=True)

    print(f"\ntool_audit_runner done in {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()

exec
/bin/bash -lc 'rg -n "dispatch_tool_keep_only|def dispatch_tool|PROTECTED_CTX_KEYS|TOOL_REGISTRY|agent_tool_hints|diagnose_tools|tool_diagnosis|TOOL_HINTS" benchmark/scripts -S' in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
benchmark/scripts/agent_v6_9.py:33:# Restrict TOOL_REGISTRY to just zoom_bbox so dispatch_tool rejects others
benchmark/scripts/agent_v6_9.py:36:_orig_registry = _tools.TOOL_REGISTRY
benchmark/scripts/agent_v6_9.py:37:_tools.TOOL_REGISTRY = {k: v for k, v in _orig_registry.items()
benchmark/scripts/agent_v6_9.py:39:mod.TOOL_REGISTRY = _tools.TOOL_REGISTRY
benchmark/scripts/single_tool_agent.py:117:    if args.tool not in tv7.TOOL_REGISTRY:
benchmark/scripts/single_tool_agent.py:119:                         f"{sorted(tv7.TOOL_REGISTRY)}")
benchmark/scripts/agent_tools_v7.py:656:TOOL_REGISTRY = {
benchmark/scripts/agent_tools_v7.py:673:PROTECTED_CTX_KEYS = (
benchmark/scripts/agent_tools_v7.py:680:def dispatch_tool(name: str, args: dict, ctx: dict | None = None) -> dict:
benchmark/scripts/agent_tools_v7.py:684:    PROTECTED_CTX_KEYS are ALWAYS taken from ctx — model-supplied args for
benchmark/scripts/agent_tools_v7.py:688:    if name not in TOOL_REGISTRY:
benchmark/scripts/agent_tools_v7.py:689:        return {"error": f"unknown tool {name!r}; must be one of {sorted(TOOL_REGISTRY)}"}
benchmark/scripts/agent_tools_v7.py:691:    fn = TOOL_REGISTRY[name]
benchmark/scripts/agent_tools_v7.py:693:    injected = {k: v for k, v in (args or {}).items() if k not in PROTECTED_CTX_KEYS}
benchmark/scripts/agent_tools_v7.py:695:    for k in PROTECTED_CTX_KEYS:
benchmark/scripts/agent_tools_v7.py:729:        keep = set(TOOL_REGISTRY.keys())
benchmark/scripts/agent_tools_v7.py:734:def dispatch_tool_keep_only(name: str, args: dict, ctx: dict | None = None) -> dict:
benchmark/scripts/agent_v6.py:30:from agent_tools_v6 import dispatch_tool, TOOL_REGISTRY  # noqa: E402
benchmark/scripts/agent_prompt_v7.py:6:- Imports TOOL_HINTS from agent_tool_hints_v7 (auto-generated from
benchmark/scripts/agent_prompt_v7.py:75:    from agent_tool_hints_v7 import TOOL_HINTS  # auto-generated by compose_v7_prompt.py
benchmark/scripts/agent_prompt_v7.py:77:    TOOL_HINTS = "(tool hints not yet generated — running un-hinted)"
benchmark/scripts/agent_prompt_v7.py:95:{TOOL_HINTS}
benchmark/scripts/diagnose_tools.py:14:OUT_DIR = "refine-logs/tool_diagnosis"
benchmark/scripts/agent_tools_v6.py:507:TOOL_REGISTRY = {
benchmark/scripts/agent_tools_v6.py:524:PROTECTED_CTX_KEYS = (
benchmark/scripts/agent_tools_v6.py:531:def dispatch_tool(name: str, args: dict, ctx: dict | None = None) -> dict:
benchmark/scripts/agent_tools_v6.py:535:    PROTECTED_CTX_KEYS are ALWAYS taken from ctx — model-supplied args for
benchmark/scripts/agent_tools_v6.py:539:    if name not in TOOL_REGISTRY:
benchmark/scripts/agent_tools_v6.py:540:        return {"error": f"unknown tool {name!r}; must be one of {sorted(TOOL_REGISTRY)}"}
benchmark/scripts/agent_tools_v6.py:542:    fn = TOOL_REGISTRY[name]
benchmark/scripts/agent_tools_v6.py:544:    injected = {k: v for k, v in (args or {}).items() if k not in PROTECTED_CTX_KEYS}
benchmark/scripts/agent_tools_v6.py:546:    for k in PROTECTED_CTX_KEYS:

exec
/bin/bash -lc "rg -n \"agent_prompt_v7|dispatch_tool_keep_only|dispatch_tool|SYSTEM_PROMPT|ReActAgent\" benchmark/scripts/agent_v7.py benchmark/scripts -g 'agent_v7.py' -S" in /hdd1/jiangxi/AD-Agent
 exited 2 in 0ms:
rg: benchmark/scripts/agent_v7.py: No such file or directory (os error 2)

exec
/bin/bash -lc "sed -n '1,220p' benchmark/scripts/agent_v7.py" in /hdd1/jiangxi/AD-Agent
 exited 2 in 0ms:
sed: can't read benchmark/scripts/agent_v7.py: No such file or directory

exec
/bin/bash -lc "sed -n '1,220p' benchmark/scripts/diagnose_tools.py" in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
"""Extract 20 cases per tool (10 wins, 10 losses) from v6.5 test results
for manual failure-mode inspection.

A "win" = tool call correlated with lower error than Direct on same item.
A "loss" = tool call correlated with higher error than Direct.
"""
from __future__ import annotations
import json
import os
from collections import defaultdict

RESULTS = "benchmark/results/v6_5_agent_qwen3_test.json"
DIRECT = "benchmark/results/v6_direct_qwen3_test.json"
OUT_DIR = "refine-logs/tool_diagnosis"

os.makedirs(OUT_DIR, exist_ok=True)

v65 = json.load(open(RESULTS))
direct = {x["item_id"]: x for x in json.load(open(DIRECT))}

by_tool: dict[str, list[dict]] = defaultdict(list)
for r in v65:
    tools = r.get("tools_used") or []
    label = r.get("label_gt")
    if label is None:
        continue
    agent_score = r.get("anomaly_score", 0.5)
    direct_score = direct.get(r["item_id"], {}).get("anomaly_score", 0.5)
    agent_err = abs(agent_score - label)
    direct_err = abs(direct_score - label)
    delta_err = agent_err - direct_err  # negative = agent better
    for t in set(tools):
        by_tool[t].append({
            "item_id": r["item_id"],
            "domain": r.get("domain_code"),
            "label": label,
            "agent_score": agent_score,
            "direct_score": direct_score,
            "delta_err": delta_err,
            "tools_used": tools,
            "rationale": (r.get("rationale") or "")[:240],
        })

for tool, cases in sorted(by_tool.items()):
    cases.sort(key=lambda x: x["delta_err"])
    wins = cases[:10]   # agent better
    losses = cases[-10:]  # agent worse
    out = [
        f"# Diagnosis: {tool}",
        "",
        f"Total calls: {len(cases)}",
        "",
        "## Failure mode (manual analysis — fill in)",
        "",
        "_TBD: wrong trigger / unclear output / VLM misreads / mixed_",
        "",
        "## Wins (agent better than Direct)",
        "",
    ]
    for h in wins:
        out.append(f"- `{h['item_id']}` [{h['domain']}] label={h['label']} agent={h['agent_score']:.2f} direct={h['direct_score']:.2f} Δerr={h['delta_err']:+.3f}")
        out.append(f"  > {h['rationale']}")
        out.append("")
    out += ["## Losses (agent worse than Direct)", ""]
    for m in losses:
        out.append(f"- `{m['item_id']}` [{m['domain']}] label={m['label']} agent={m['agent_score']:.2f} direct={m['direct_score']:.2f} Δerr={m['delta_err']:+.3f}")
        out.append(f"  > {m['rationale']}")
        out.append("")
    with open(f"{OUT_DIR}/{tool}.md", "w") as f:
        f.write("\n".join(out))
    print(f"wrote {OUT_DIR}/{tool}.md  (n_calls={len(cases)})")

print("\nTools with zero calls in v6.5:")
seen = set(by_tool.keys())
ALL = {
    "tool_expert_score", "tool_hotspot_cropper", "tool_zoom_bbox",
    "tool_patch_grid", "tool_image_diff", "tool_rotate_align",
    "tool_side_by_side", "tool_reference_profiler", "tool_reference_retriever",
    "tool_component_counter", "tool_segment_and_count", "tool_texture_fft",
    "tool_domain_knowledge",
}
for t in sorted(ALL - seen):
    print(f"  {t}")

exec
/bin/bash -lc 'rg -n "tool_cards|agent_tool_hints_v7|compose_v7|diagnosis|tool_diagnosis|TOOL_HINTS" -S .' in /hdd1/jiangxi/AD-Agent
 succeeded in 5029ms:
./docs/superpowers/specs/2026-04-18-anomaclaw-per-tool-audit-design.md:73:- Write `refine-logs/tool_cards/<tool>.md`
./docs/superpowers/specs/2026-04-18-anomaclaw-per-tool-audit-design.md:106:- `refine-logs/tool_cards/<tool>.md` × 11
./docs/superpowers/specs/2026-04-18-anomaclaw-per-tool-audit-design.md:124:| Redesigned output confuses VLM differently | Step 1 diagnosis re-audits after single-tool run |
./docs/superpowers/specs/2026-04-18-anomaclaw-per-tool-audit-design.md:130:- Phase A (diagnosis + redesign, serial): ~2-3 hours depending on how many tools survive audit
./docs/superpowers/plans/2026-04-18-anomaclaw-per-tool-audit.md:23:- Create: `refine-logs/tool_cards/` (empty dir)
./docs/superpowers/plans/2026-04-18-anomaclaw-per-tool-audit.md:29:mkdir -p benchmark/results/tool_audit refine-logs/tool_cards
./docs/superpowers/plans/2026-04-18-anomaclaw-per-tool-audit.md:102:- Create: `refine-logs/tool_diagnosis/<tool>.md` × 13
./docs/superpowers/plans/2026-04-18-anomaclaw-per-tool-audit.md:105:- [ ] **Step 1: Create diagnosis script**
./docs/superpowers/plans/2026-04-18-anomaclaw-per-tool-audit.md:118:OUT_DIR = "refine-logs/tool_diagnosis"
./docs/superpowers/plans/2026-04-18-anomaclaw-per-tool-audit.md:176:- [ ] **Step 2: Run diagnosis**
./docs/superpowers/plans/2026-04-18-anomaclaw-per-tool-audit.md:181:Expected: 11 diagnosis files written (tools that were called in v6.5), list of 2 never-called tools printed.
./docs/superpowers/plans/2026-04-18-anomaclaw-per-tool-audit.md:183:- [ ] **Step 3: Read each diagnosis file and write one-line failure mode summary**
./docs/superpowers/plans/2026-04-18-anomaclaw-per-tool-audit.md:185:For each `refine-logs/tool_diagnosis/<tool>.md`, append at the top:
./docs/superpowers/plans/2026-04-18-anomaclaw-per-tool-audit.md:192:- [ ] **Step 4: Commit diagnosis**
./docs/superpowers/plans/2026-04-18-anomaclaw-per-tool-audit.md:194:git add benchmark/scripts/diagnose_tools.py refine-logs/tool_diagnosis/
./docs/superpowers/plans/2026-04-18-anomaclaw-per-tool-audit.md:195:git commit -m "v7 diagnosis: extract 20 cases per tool for manual inspection"
./docs/superpowers/plans/2026-04-18-anomaclaw-per-tool-audit.md:937:    --out_md "refine-logs/tool_cards/${tool}.md"
./docs/superpowers/plans/2026-04-18-anomaclaw-per-tool-audit.md:943:grep -H "Verdict:" refine-logs/tool_cards/*.md | tee /tmp/v7_keep_drop.txt
./docs/superpowers/plans/2026-04-18-anomaclaw-per-tool-audit.md:948:git add benchmark/scripts/build_tool_card.py refine-logs/tool_cards/ benchmark/results/tool_audit/
./docs/superpowers/plans/2026-04-18-anomaclaw-per-tool-audit.md:976:Write `benchmark/scripts/compose_v7_prompt.py`:
./docs/superpowers/plans/2026-04-18-anomaclaw-per-tool-audit.md:979:"""Read tool_cards/*.md, extract the 'Agent hint' section from KEEP tools,
./docs/superpowers/plans/2026-04-18-anomaclaw-per-tool-audit.md:980:and write an ALL_TOOL_HINTS string that agent_prompt_v7 can import."""
./docs/superpowers/plans/2026-04-18-anomaclaw-per-tool-audit.md:984:CARDS = Path("refine-logs/tool_cards")
./docs/superpowers/plans/2026-04-18-anomaclaw-per-tool-audit.md:985:OUT = Path("benchmark/scripts/agent_tool_hints_v7.py")
./docs/superpowers/plans/2026-04-18-anomaclaw-per-tool-audit.md:997:content = '"""Auto-generated from tool_cards/*.md. Do not edit by hand."""\n\n'
./docs/superpowers/plans/2026-04-18-anomaclaw-per-tool-audit.md:998:content += "TOOL_HINTS = " + repr("\n".join(hints)) + "\n"
./docs/superpowers/plans/2026-04-18-anomaclaw-per-tool-audit.md:1005:python benchmark/scripts/compose_v7_prompt.py
./docs/superpowers/plans/2026-04-18-anomaclaw-per-tool-audit.md:1006:cat benchmark/scripts/agent_tool_hints_v7.py
./docs/superpowers/plans/2026-04-18-anomaclaw-per-tool-audit.md:1009:- [ ] **Step 2: Update agent_prompt_v7.py to include TOOL_HINTS**
./docs/superpowers/plans/2026-04-18-anomaclaw-per-tool-audit.md:1015:    from agent_tool_hints_v7 import TOOL_HINTS
./docs/superpowers/plans/2026-04-18-anomaclaw-per-tool-audit.md:1017:    TOOL_HINTS = ""
./docs/superpowers/plans/2026-04-18-anomaclaw-per-tool-audit.md:1033:{TOOL_HINTS}
./docs/superpowers/plans/2026-04-18-anomaclaw-per-tool-audit.md:1062:_KEEP_TOOLS = None  # loaded lazily from tool_cards
./docs/superpowers/plans/2026-04-18-anomaclaw-per-tool-audit.md:1069:    cards = Path(__file__).resolve().parent.parent.parent / "refine-logs" / "tool_cards"
./docs/superpowers/plans/2026-04-18-anomaclaw-per-tool-audit.md:1113:git add benchmark/scripts/compose_v7_prompt.py benchmark/scripts/agent_tool_hints_v7.py \
./docs/superpowers/plans/2026-04-18-anomaclaw-per-tool-audit.md:1241:| (fill from tool_cards/*.md) |
./docs/superpowers/plans/2026-04-18-anomaclaw-per-tool-audit.md:1253:- tool cards: refine-logs/tool_cards/*.md
./docs/superpowers/plans/2026-04-18-anomaclaw-per-tool-audit.md:1261:        refine-logs/tool_cards/ refine-logs/tool_diagnosis/
./AnomaClaw/refine-logs/auto-review-round-1-2026-04-05.md:85:### 6. Weak-domain diagnosis is incomplete
./AnomaClaw/refine-logs/auto-review-round-2-2026-04-05.md:133:3. **Weak-domain diagnosis**: still incomplete.
./AnomaClaw/refine-logs/auto-review-round-3-2026-04-05.md:133:1. **Weak-domain diagnosis**
./archive/old_docs/AUTO_REVIEW.md:235:6. Weak-domain diagnosis is not yet paper-ready.

exec
/bin/bash -lc "nl -ba benchmark/scripts/single_tool_agent.py | sed -n '1,210p'" in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
     1	"""Single-tool agent: Direct-style ReAct loop with exactly ONE tool exposed.
     2	
     3	Builds on top of agent_v6.ReActAgent but:
     4	  - Swaps SYSTEM_PROMPT for a single-tool variant describing only `--tool`
     5	  - Restricts dispatch_tool to reject any tool != --tool
     6	  - Outputs {item_id, anomaly_score, used_tool, n_turns, tools_used,
     7	             confidence, rationale, error} per item
     8	
     9	Usage:
    10	  python benchmark/scripts/single_tool_agent.py \
    11	    --tool tool_expert_score --split dev \
    12	    --manifest benchmark/manifests/full_manifest.json \
    13	    --output benchmark/results/tool_audit/tool_expert_score.json \
    14	    --max_turns 3 --max_workers 9
    15	"""
    16	from __future__ import annotations
    17	import argparse
    18	import json
    19	import os
    20	import sys
    21	import time
    22	from concurrent.futures import ThreadPoolExecutor, as_completed
    23	from pathlib import Path
    24	
    25	sys.path.insert(0, str(Path(__file__).parent))
    26	
    27	from infer import get_client, get_model_name  # noqa: E402
    28	import agent_v6 as v6  # noqa: E402
    29	import agent_tools_v7 as tv7  # noqa: E402
    30	import agent_prompt_v7 as pv7  # noqa: E402
    31	
    32	
    33	SINGLE_TOOL_SYSTEM_PROMPT = """You are a visual anomaly detection agent.
    34	
    35	INPUT PER IMAGE: one query image, four normal reference images, a turn budget.
    36	TASK: decide if the query is normal or anomalous and output a score in [0,1]
    37	where 1 means certainly anomalous.
    38	
    39	You have NO domain information and can observe only what's in the images.
    40	On each turn you have exactly ONE tool available.
    41	
    42	{output_guide}
    43	
    44	THE ONE TOOL AVAILABLE TO YOU:
    45	{tool_desc}
    46	
    47	PROTOCOL: Return ONLY a JSON object:
    48	{{
    49	  "thought":  "<one or two sentences>",
    50	  "action":   "call_tool" | "final",
    51	  "tool":     "<tool_name>" | null,
    52	  "args":     {{ ... }} | null,
    53	  "confidence": <integer 0..100>,
    54	  "score":    <float 0..1> | null,
    55	  "rationale": "<one or two sentences>" | null
    56	}}
    57	
    58	GUIDELINES:
    59	- Call the tool ONLY if you think it will help on THIS image. Otherwise output
    60	  `final` at turn 1 without calling it.
    61	- If the tool returns an `unreliable_alignment: true` or `not_applicable: true`
    62	  flag, IGNORE its output and reason from the raw images.
    63	- Read the disconfirm clause of the tool output before updating your score.
    64	- Return valid JSON only.
    65	"""
    66	
    67	
    68	def _extract_tool_desc(tool_name: str) -> str:
    69	    """Extract the docstring block for `tool_name` from agent_prompt_v7.TOOL_CATALOG."""
    70	    catalog = pv7.TOOL_CATALOG
    71	    lines = catalog.splitlines()
    72	    out: list[str] = []
    73	    capturing = False
    74	    for i, line in enumerate(lines):
    75	        stripped = line.strip()
    76	        if stripped.startswith(tool_name):
    77	            capturing = True
    78	            out.append(line)
    79	            continue
    80	        if capturing:
    81	            if line.startswith("    ") or not stripped:
    82	                out.append(line)
    83	                continue
    84	            # next tool or section header → stop
    85	            break
    86	    if not out:
    87	        return f"  {tool_name}(...)  (no description found in catalog)"
    88	    return "\n".join(out).rstrip()
    89	
    90	
    91	def make_restricted_dispatch(allowed_tool: str):
    92	    """Return a dispatch_tool that routes only `allowed_tool`, else returns error."""
    93	    original = tv7.dispatch_tool
    94	
    95	    def _dispatch(name: str, args: dict, ctx: dict | None = None) -> dict:
    96	        if name != allowed_tool:
    97	            return {"error": (f"only {allowed_tool} is available in this single-tool "
    98	                              f"run; you called {name}")}
    99	        return original(name, args, ctx)
   100	
   101	    return _dispatch
   102	
   103	
   104	def main():
   105	    ap = argparse.ArgumentParser()
   106	    ap.add_argument("--tool", required=True)
   107	    ap.add_argument("--manifest", default="benchmark/manifests/full_manifest.json")
   108	    ap.add_argument("--split", choices=["calibration", "dev", "test"], default="dev")
   109	    ap.add_argument("--output", required=True)
   110	    ap.add_argument("--backend", default="qwen3")
   111	    ap.add_argument("--max_turns", type=int, default=3)
   112	    ap.add_argument("--max_workers", type=int, default=9)
   113	    ap.add_argument("--max_items", type=int, default=0)
   114	    ap.add_argument("--resume", action="store_true")
   115	    args = ap.parse_args()
   116	
   117	    if args.tool not in tv7.TOOL_REGISTRY:
   118	        raise SystemExit(f"unknown tool {args.tool!r}; choices: "
   119	                         f"{sorted(tv7.TOOL_REGISTRY)}")
   120	
   121	    items = json.load(open(args.manifest))
   122	    items = [x for x in items if x.get("split") == args.split]
   123	    if args.max_items:
   124	        items = items[:args.max_items]
   125	
   126	    prev: list = []
   127	    done_ids: set = set()
   128	    if args.resume and os.path.exists(args.output):
   129	        prev = json.load(open(args.output))
   130	        done_ids = {r["item_id"] for r in prev if r.get("error") is None}
   131	        items = [x for x in items if x["item_id"] not in done_ids]
   132	        print(f"[resume] {len(done_ids)} done; {len(items)} remaining", flush=True)
   133	
   134	    client = get_client(args.backend)
   135	    model = get_model_name(args.backend)
   136	
   137	    # Patch: single-tool prompt and restricted dispatch
   138	    tool_desc = _extract_tool_desc(args.tool)
   139	    sp = SINGLE_TOOL_SYSTEM_PROMPT.format(
   140	        output_guide=pv7.TOOL_OUTPUT_GUIDE, tool_desc=tool_desc)
   141	
   142	    v6.SYSTEM_PROMPT = sp
   143	    v6.dispatch_tool = make_restricted_dispatch(args.tool)
   144	
   145	    agent = v6.ReActAgent(vlm_client=client, vlm_model=model,
   146	                          max_turns=args.max_turns)
   147	
   148	    results: list = list(prev)
   149	    t0 = time.time()
   150	
   151	    def _run_one(x):
   152	        try:
   153	            r = agent.run(item_id=x["item_id"], query_path=x["query_path"],
   154	                          ref_paths=x["ref_paths"], split=args.split,
   155	                          domain_code=x.get("domain_code"))
   156	            used = args.tool in (r.tools_used or [])
   157	            return {
   158	                "item_id": x["item_id"],
   159	                "domain_code": x.get("domain_code"),
   160	                "label_gt": x.get("label"),
   161	                "anomaly_score": r.score,
   162	                "used_tool": used,
   163	                "n_turns": r.n_turns,
   164	                "tools_used": r.tools_used,
   165	                "confidence": r.confidence,
   166	                "rationale": r.rationale,
   167	                "error": r.error,
   168	            }
   169	        except Exception as e:
   170	            return {"item_id": x["item_id"], "domain_code": x.get("domain_code"),
   171	                    "label_gt": x.get("label"), "anomaly_score": 0.5,
   172	                    "used_tool": False, "n_turns": 0, "tools_used": [],
   173	                    "confidence": 0, "rationale": None,
   174	                    "error": f"{type(e).__name__}: {e}"}
   175	
   176	    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
   177	    with ThreadPoolExecutor(max_workers=args.max_workers) as ex:
   178	        futs = [ex.submit(_run_one, x) for x in items]
   179	        for i, fut in enumerate(as_completed(futs)):
   180	            results.append(fut.result())
   181	            if (i + 1) % 40 == 0:
   182	                with open(args.output, "w") as f:
   183	                    json.dump(results, f)
   184	                print(f"[{args.tool}] {i+1}/{len(items)} "
   185	                      f"t={time.time()-t0:.1f}s", flush=True)
   186	
   187	    with open(args.output, "w") as f:
   188	        json.dump(results, f)
   189	    used_n = sum(1 for r in results if r.get("used_tool"))
   190	    err_n = sum(1 for r in results if r.get("error"))
   191	    print(f"[{args.tool}] n={len(results)} used={used_n} err={err_n} "
   192	          f"→ {args.output}")
   193	
   194	
   195	if __name__ == "__main__":
   196	    main()

exec
/bin/bash -lc "nl -ba benchmark/scripts/agent_v6.py | sed -n '1,240p'" in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
     1	"""AnomalyClaw v6 — per-item autonomous ReAct agent.
     2	
     3	Usage:
     4	  python benchmark/scripts/agent_v6.py \
     5	    --manifest benchmark/manifests_v2/full_manifest.json \
     6	    --split test --backend qwen3 \
     7	    --output benchmark/results/v6_agent_qwen3_test.json \
     8	    --max_turns 5 --max_workers 8
     9	"""
    10	from __future__ import annotations
    11	
    12	import argparse
    13	import json
    14	import os
    15	import sys
    16	import time
    17	from concurrent.futures import ThreadPoolExecutor, as_completed
    18	from dataclasses import dataclass
    19	from pathlib import Path
    20	
    21	sys.path.insert(0, str(Path(__file__).parent))
    22	
    23	from infer import (  # noqa: E402
    24	    call_llm, extract_json, get_client, get_model_name,
    25	    img_msg, load_and_encode, text_msg,
    26	)
    27	from agent_prompt_v6 import (  # noqa: E402
    28	    SYSTEM_PROMPT, budget_warning_prompt, forced_final_prompt,
    29	)
    30	from agent_tools_v6 import dispatch_tool, TOOL_REGISTRY  # noqa: E402
    31	
    32	
    33	@dataclass
    34	class AgentResult:
    35	    item_id: str
    36	    score: float
    37	    rationale: str
    38	    n_turns: int
    39	    tools_used: list
    40	    history: list
    41	    confidence: int
    42	    error: str | None = None
    43	
    44	
    45	class ReActAgent:
    46	    def __init__(self, vlm_client, vlm_model: str, max_turns: int = 5,
    47	                 json_retries: int = 1, max_tokens: int = 600):
    48	        self.client = vlm_client
    49	        self.model = vlm_model
    50	        self.K = max_turns
    51	        self.json_retries = json_retries
    52	        self.max_tokens = max_tokens
    53	
    54	    # ──────────────────────────────────────────────────────────────────
    55	    def _build_initial_messages(self, query_path: str,
    56	                                ref_paths: list,
    57	                                domain_code: str | None = None,
    58	                                anchor_text: str | None = None) -> list:
    59	        """Builder is called with per-item kwargs; no instance mutation.
    60	        Subclasses override by subclassing, not by monkey-patching.
    61	
    62	        Args:
    63	            domain_code: forwarded for variants that want to inject
    64	                DOMAIN_CONTEXT[d] at call time.
    65	            anchor_text: free-form extra preamble (used by anchored
    66	                variants to pass precomputed expert signals).
    67	        """
    68	        user_parts = []
    69	        if anchor_text:
    70	            user_parts.append(text_msg(anchor_text))
    71	        user_parts.append(text_msg("NORMAL REFERENCE IMAGES:"))
    72	        for rp in ref_paths[:4]:
    73	            user_parts.append(img_msg(load_and_encode(rp)))
    74	        user_parts.append(text_msg("QUERY IMAGE:"))
    75	        user_parts.append(img_msg(load_and_encode(query_path)))
    76	        user_parts.append(text_msg(f"Turn 1/{self.K}. Decide your next action."))
    77	        return [
    78	            {"role": "system", "content": SYSTEM_PROMPT},
    79	            {"role": "user", "content": user_parts},
    80	        ]
    81	
    82	    def _parse_action(self, text: str) -> dict | None:
    83	        parsed = extract_json(text)
    84	        if not isinstance(parsed, dict):
    85	            return None
    86	        action = parsed.get("action")
    87	        if action not in ("call_tool", "final"):
    88	            return None
    89	        if action == "final":
    90	            s = parsed.get("score")
    91	            if s is None:
    92	                return None
    93	            try:
    94	                parsed["score"] = float(s)
    95	            except (TypeError, ValueError):
    96	                return None
    97	        else:
    98	            if not parsed.get("tool"):
    99	                return None
   100	        return parsed
   101	
   102	    def _call_with_json_retry(self, messages: list) -> dict | None:
   103	        attempts = 1 + self.json_retries
   104	        cur = list(messages)
   105	        for _ in range(attempts):
   106	            try:
   107	                text, _, _ = call_llm(self.client, self.model, cur,
   108	                                      max_tokens=self.max_tokens,
   109	                                      temperature=0.0)
   110	            except Exception:
   111	                return None
   112	            parsed = self._parse_action(text)
   113	            if parsed is not None:
   114	                return parsed
   115	            cur = cur + [{
   116	                "role": "user",
   117	                "content": "Your last response was not valid JSON. "
   118	                           "Return a single JSON object with fields "
   119	                           "{thought, action, tool, args, confidence, "
   120	                           "score, rationale}.",
   121	            }]
   122	        return None
   123	
   124	    # ──────────────────────────────────────────────────────────────────
   125	    def run(self, item_id: str, query_path: str, ref_paths: list,
   126	            split: str, domain_code: str | None = None) -> AgentResult:
   127	        ctx = {
   128	            "query_path": query_path,
   129	            "ref_paths": ref_paths,
   130	            "item_id": item_id,
   131	            "split": split,
   132	            "vlm_client": self.client,
   133	            "vlm_model": self.model,
   134	            "llm_client": self.client,
   135	            "llm_model": self.model,
   136	            "_manifest_domain": domain_code,
   137	        }
   138	        messages = self._build_initial_messages(query_path, ref_paths,
   139	                                                domain_code=domain_code)
   140	        history, tools_used = [], []
   141	
   142	        for turn in range(1, self.K + 1):
   143	            action = self._call_with_json_retry(messages)
   144	            if action is None:
   145	                return AgentResult(
   146	                    item_id=item_id, score=0.5, rationale="json parse failed",
   147	                    n_turns=turn, tools_used=tools_used, history=history,
   148	                    confidence=0, error="malformed JSON after retries",
   149	                )
   150	
   151	            if action["action"] == "final":
   152	                return AgentResult(
   153	                    item_id=item_id,
   154	                    score=max(0.0, min(1.0, float(action["score"]))),
   155	                    rationale=str(action.get("rationale", ""))[:500],
   156	                    n_turns=turn, tools_used=tools_used,
   157	                    history=history + [{"turn": turn, **_summarise(action)}],
   158	                    confidence=int(action.get("confidence", 0) or 0),
   159	                )
   160	
   161	            if turn == self.K:
   162	                # Budget exhausted; force a final in one more sub-call.
   163	                messages.append({"role": "assistant",
   164	                                 "content": json.dumps(_summarise(action))})
   165	                messages.append({"role": "user",
   166	                                 "content": forced_final_prompt(self.K)})
   167	                forced = self._call_with_json_retry(messages)
   168	                if forced and forced.get("action") == "final":
   169	                    return AgentResult(
   170	                        item_id=item_id,
   171	                        score=max(0.0, min(1.0, float(forced["score"]))),
   172	                        rationale=str(forced.get("rationale", ""))[:500],
   173	                        n_turns=self.K, tools_used=tools_used,
   174	                        history=history + [
   175	                            {"turn": turn, **_summarise(action)},
   176	                            {"turn": turn, **_summarise(forced)},
   177	                        ],
   178	                        confidence=int(forced.get("confidence", 0) or 0),
   179	                    )
   180	                return AgentResult(
   181	                    item_id=item_id, score=0.5, rationale="forced-final failed",
   182	                    n_turns=self.K, tools_used=tools_used, history=history,
   183	                    confidence=0, error="forced-final produced non-final",
   184	                )
   185	
   186	            # Execute tool
   187	            tool_name = action["tool"]
   188	            tool_args = action.get("args") or {}
   189	            observation = dispatch_tool(tool_name, tool_args, ctx)
   190	            tools_used.append(tool_name)
   191	            history.append({"turn": turn, **_summarise(action),
   192	                            "obs_keys": list(observation.keys()),
   193	                            "obs_error": observation.get("error")})
   194	
   195	            # Stash expert patches for hotspot/counter tools
   196	            if tool_name == "tool_expert_score":
   197	                ctx["_expert_patches"] = observation.get("top_patches", [])
   198	
   199	            # Feed observation back — include image if present, text otherwise
   200	            obs_parts = []
   201	            obs_text = _obs_to_text(observation)
   202	            obs_parts.append(text_msg(
   203	                f"OBSERVATION from {tool_name}: {obs_text}"))
   204	            for img_key in ("crop_b64", "diff_mask_b64", "aligned_diff_b64",
   205	                            "composite_b64"):
   206	                if observation.get(img_key):
   207	                    obs_parts.append(img_msg(observation[img_key]))
   208	            if observation.get("tiles"):
   209	                for t in observation["tiles"][:9]:
   210	                    obs_parts.append(img_msg(t["crop_b64"]))
   211	            remaining = self.K - turn
   212	            obs_parts.append(text_msg(
   213	                f"Turn {turn + 1}/{self.K}. "
   214	                f"{budget_warning_prompt(remaining)}\n"
   215	                f"Decide your next action."))
   216	            messages.append({"role": "assistant",
   217	                             "content": json.dumps(_summarise(action))})
   218	            messages.append({"role": "user", "content": obs_parts})
   219	
   220	        return AgentResult(
   221	            item_id=item_id, score=0.5, rationale="loop exhausted",
   222	            n_turns=self.K, tools_used=tools_used, history=history,
   223	            confidence=0, error="loop exhausted without final",
   224	        )
   225	
   226	
   227	def _summarise(action: dict) -> dict:
   228	    """Drop large args/rationale for history storage."""
   229	    out = {k: v for k, v in action.items()
   230	           if k not in ("args",) or v is None or len(str(v)) < 500}
   231	    if "args" in action and "args" not in out:
   232	        out["args"] = str(action["args"])[:400]
   233	    return out
   234	
   235	
   236	def _obs_to_text(obs: dict) -> str:
   237	    """Compact text summary of an observation (no base64 payloads)."""
   238	    small = {}
   239	    for k, v in obs.items():
   240	        if k.endswith("_b64"):

exec
/bin/bash -lc "nl -ba benchmark/scripts/agent_tools_v7.py | sed -n '35,145p;650,745p'" in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
    35	import sys
    36	from functools import lru_cache
    37	from io import BytesIO
    38	from pathlib import Path
    39	from typing import Any
    40	
    41	import numpy as np
    42	from PIL import Image
    43	
    44	sys.path.insert(0, str(Path(__file__).parent))
    45	from infer import call_llm, extract_json, img_msg, load_and_encode, text_msg  # noqa: E402
    46	
    47	RESULTS_DIR = Path("/hdd1/jiangxi/AD-Agent/benchmark/results")
    48	
    49	
    50	# ─── Helpers ────────────────────────────────────────────────────────────────
    51	
    52	def _pil_to_b64(img: Image.Image, max_side: int = 512, quality: int = 85) -> str:
    53	    w, h = img.size
    54	    if max(w, h) > max_side:
    55	        scale = max_side / max(w, h)
    56	        img = img.resize((int(w * scale), int(h * scale)))
    57	    buf = BytesIO()
    58	    img.save(buf, format="JPEG", quality=quality)
    59	    return base64.b64encode(buf.getvalue()).decode("utf-8")
    60	
    61	
    62	def _wrap_interpretation(obs: dict, verdict: str, disconfirm: str) -> dict:
    63	    """Attach a verdict + disconfirming clause to a tool observation.
    64	
    65	    Format: "Observation suggests: <verdict>. IMPORTANT: if <disconfirm>,
    66	    the query is likely NORMAL despite this signal."
    67	
    68	    Intent: force the VLM to consider the null hypothesis before updating
    69	    its score. Many v6 failures came from confirmation bias where a tool's
    70	    signal (e.g. 'strong anomaly') was treated as proof rather than evidence.
    71	    """
    72	    obs["interpretation"] = (
    73	        f"Observation suggests: {verdict}. "
    74	        f"IMPORTANT: if {disconfirm}, the query is likely NORMAL despite this signal."
    75	    )
    76	    return obs
    77	
    78	
    79	# ─── Tier 1: Expert probes ──────────────────────────────────────────────────
    80	
    81	EXPERT_FILES = {
    82	    "subspacead":    {"calibration": "subspacead_calibration.json",
    83	                      "dev":         "subspacead_dev.json",
    84	                      "test":        "subspacead_test.json"},
    85	    "anomalyvfm":    {"calibration": "anomalyvfm_calibration.json",
    86	                      "dev":         "anomalyvfm_dev.json",  # may not exist
    87	                      "test":        "anomalyvfm_test.json"},
    88	    "patchknn":      {"calibration": "classical_dinov2_patch_test_all.json",
    89	                      "dev":         "classical_dinov2_patch_test_all.json",
    90	                      "test":        "classical_dinov2_patch_test_all.json"},
    91	    "dinov2_global": {"calibration": "classical_dinov2_global_test_all.json",
    92	                      "dev":         "classical_dinov2_global_test_all.json",
    93	                      "test":        "classical_dinov2_global_test_all.json"},
    94	}
    95	
    96	
    97	@lru_cache(maxsize=16)
    98	def _load_expert_scores(expert: str, split: str) -> tuple[dict, np.ndarray]:
    99	    """Return (item_id -> record, sorted score array for percentile ranking)."""
   100	    if expert not in EXPERT_FILES:
   101	        raise ValueError(f"unknown expert {expert!r}; must be one of {list(EXPERT_FILES)}")
   102	    fname = EXPERT_FILES[expert].get(split)
   103	    if fname is None:
   104	        raise ValueError(f"no {split} file for expert {expert!r}")
   105	    path = RESULTS_DIR / fname
   106	    if not path.exists():
   107	        return {}, np.array([])
   108	    raw = json.load(open(path))
   109	    if isinstance(raw, list):
   110	        recs = {x["item_id"]: x for x in raw if "item_id" in x}
   111	    else:
   112	        recs = raw
   113	    scores = np.array([float(r["anomaly_score"]) for r in recs.values()
   114	                       if r.get("anomaly_score") is not None])
   115	    scores.sort()
   116	    return recs, scores
   117	
   118	
   119	def tool_expert_score(item_id: str, expert: str = "subspacead",
   120	                      split: str = "test", **_) -> dict:
   121	    """Look up a cached expert anomaly score + its percentile rank within `split`.
   122	
   123	    Returns: {expert, score, normalized_rank, top_patches, interpretation, error}
   124	    """
   125	    try:
   126	        recs, all_scores = _load_expert_scores(expert, split)
   127	    except ValueError as e:
   128	        return {"error": str(e)}
   129	    rec = recs.get(item_id)
   130	    if rec is None or rec.get("anomaly_score") is None:
   131	        return {"error": f"no cached score for {item_id} in {expert}/{split}"}
   132	    s = float(rec["anomaly_score"])
   133	    if len(all_scores) == 0:
   134	        rank = 0.5
   135	    else:
   136	        rank = float(np.searchsorted(all_scores, s) / len(all_scores))
   137	    # v7: binned verdict + disconfirm
   138	    if rank >= 0.85:
   139	        verdict = (f"strong anomaly signal (rank {rank:.2f}: the query's {expert} "
   140	                   f"score is higher than 85% of samples in this split)")
   141	        disconfirm = (f"the {expert} expert is known to over-flag this domain's "
   142	                      f"natural texture variation, OR the refs happen to be outliers")
   143	    elif rank >= 0.60:
   144	        verdict = (f"moderate/ambiguous anomaly signal (rank {rank:.2f}: mild "
   145	                   f"deviation, but within normal variation for many images)")
   650	                  "before updating your score")
   651	    return _wrap_interpretation(out, verdict, disconfirm)
   652	
   653	
   654	# ─── Dispatcher ─────────────────────────────────────────────────────────────
   655	
   656	TOOL_REGISTRY = {
   657	    "tool_expert_score":        tool_expert_score,
   658	    "tool_hotspot_cropper":     tool_hotspot_cropper,
   659	    "tool_zoom_bbox":           tool_zoom_bbox,
   660	    "tool_patch_grid":          tool_patch_grid,
   661	    "tool_image_diff":          tool_image_diff,
   662	    "tool_rotate_align":        tool_rotate_align,
   663	    "tool_side_by_side":        tool_side_by_side,
   664	    "tool_reference_profiler":  tool_reference_profiler,
   665	    "tool_reference_retriever": tool_reference_retriever,
   666	    "tool_component_counter":   tool_component_counter,
   667	    "tool_segment_and_count":   tool_segment_and_count,
   668	    "tool_texture_fft":         tool_texture_fft,
   669	    "tool_domain_knowledge":    tool_domain_knowledge,
   670	}
   671	
   672	
   673	PROTECTED_CTX_KEYS = (
   674	    "query_path", "ref_paths", "item_id", "split",
   675	    "vlm_client", "vlm_model", "llm_client", "llm_model",
   676	    "_expert_patches", "_manifest_domain", "index_dir",
   677	)
   678	
   679	
   680	def dispatch_tool(name: str, args: dict, ctx: dict | None = None) -> dict:
   681	    """Dispatch a tool call. ctx carries session state that tools need but
   682	    that the VLM shouldn't re-type (query_path, ref_paths, split, clients).
   683	
   684	    PROTECTED_CTX_KEYS are ALWAYS taken from ctx — model-supplied args for
   685	    those keys are dropped (prevents VLM from redirecting a tool to
   686	    different item/split by crafting malicious args).
   687	    """
   688	    if name not in TOOL_REGISTRY:
   689	        return {"error": f"unknown tool {name!r}; must be one of {sorted(TOOL_REGISTRY)}"}
   690	    ctx = ctx or {}
   691	    fn = TOOL_REGISTRY[name]
   692	    # Start from sanitized model args: drop protected keys
   693	    injected = {k: v for k, v in (args or {}).items() if k not in PROTECTED_CTX_KEYS}
   694	    # Overlay ctx (ctx wins over model args for protected fields)
   695	    for k in PROTECTED_CTX_KEYS:
   696	        if k in ctx:
   697	            injected[k] = ctx[k]
   698	    try:
   699	        return fn(**injected)
   700	    except TypeError as e:
   701	        return {"error": f"bad args for {name}: {e}"}
   702	    except Exception as e:
   703	        return {"error": f"{name} raised {type(e).__name__}: {e}"}
   704	
   705	
   706	# ─── KEEP-gated dispatch (used by agent_v7 after audit is complete) ─────────
   707	
   708	_KEEP_TOOLS: set[str] | None = None
   709	
   710	
   711	def _load_keep_tools() -> set[str]:
   712	    """Load KEEP set from refine-logs/tool_cards/*.md.
   713	
   714	    Fallback: if no cards exist or none are KEEP, return all registered tools
   715	    (single-tool audit runs BEFORE tool cards exist, so they must not be gated).
   716	    """
   717	    global _KEEP_TOOLS
   718	    cards = Path(__file__).resolve().parent.parent.parent / "refine-logs" / "tool_cards"
   719	    keep: set[str] = set()
   720	    if cards.exists():
   721	        for md in cards.glob("*.md"):
   722	            try:
   723	                text = md.read_text()
   724	            except OSError:
   725	                continue
   726	            if "**Verdict:** KEEP" in text:
   727	                keep.add(md.stem)
   728	    if not keep:
   729	        keep = set(TOOL_REGISTRY.keys())
   730	    _KEEP_TOOLS = keep
   731	    return keep
   732	
   733	
   734	def dispatch_tool_keep_only(name: str, args: dict, ctx: dict | None = None) -> dict:
   735	    """Same as dispatch_tool but refuses tools not in the KEEP set.
   736	
   737	    agent_v7 uses this; audit runs use the un-gated dispatch_tool.
   738	    """
   739	    global _KEEP_TOOLS
   740	    if _KEEP_TOOLS is None:
   741	        _load_keep_tools()
   742	    if name not in (_KEEP_TOOLS or set()):
   743	        return {"error": (f"{name} is not a v7 KEEP tool; allowed set: "
   744	                          f"{sorted(_KEEP_TOOLS or [])}")}
   745	    return dispatch_tool(name, args, ctx)

exec
/bin/bash -lc "nl -ba benchmark/scripts/build_tool_card.py | sed -n '1,260p'" in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
     1	"""Slice a single-tool audit result by multiple axes, find niches where the
     2	tool beats Direct, emit a tool_card.md.
     3	
     4	Slices:
     5	  - domain (per-domain AUROC)
     6	  - direct_margin bucket (uncertain / confident)
     7	  - expert_score bucket (subspacead rank: low/mid/high)
     8	  - tool_used True/False
     9	  - n_turns bucket (1 / 2-3)
    10	
    11	Niche = slice with n >= threshold AND Δ_AUROC > 0 AND bootstrap 95% CI
    12	lower-bound > 0.
    13	"""
    14	from __future__ import annotations
    15	import argparse
    16	import json
    17	import os
    18	from pathlib import Path
    19	
    20	import numpy as np
    21	from sklearn.metrics import roc_auc_score
    22	
    23	N_BOOT = 1000
    24	RNG = np.random.default_rng(42)
    25	
    26	
    27	def _safe_auroc(y, s):
    28	    y, s = np.asarray(y), np.asarray(s)
    29	    if len(y) < 5 or len(set(y)) < 2:
    30	        return np.nan
    31	    return float(roc_auc_score(y, s))
    32	
    33	
    34	def macro_auroc_from_results(items, min_n_per_domain: int = 3):
    35	    by_d: dict[str, list] = {}
    36	    for x in items:
    37	        if x.get("label_gt") is None:
    38	            continue
    39	        by_d.setdefault(x.get("domain_code"), []).append(x)
    40	    aurocs = []
    41	    for d, arr in by_d.items():
    42	        if len(arr) < min_n_per_domain:
    43	            continue
    44	        y = [i["label_gt"] for i in arr]
    45	        s = [i["anomaly_score"] for i in arr]
    46	        auc = _safe_auroc(y, s)
    47	        if not np.isnan(auc):
    48	            aurocs.append(auc)
    49	    return float(np.mean(aurocs)) if aurocs else np.nan
    50	
    51	
    52	def slice_macro_delta(pairs: list[tuple[dict, dict]], slice_fn, slice_name: str):
    53	    """Return {'slice', 'n', 'auroc_tool', 'auroc_direct', 'delta',
    54	    'delta_ci'} for the subset where slice_fn(tool_item, direct_item) is True.
    55	
    56	    AUROC is macro over domains represented in the subset, falling back to
    57	    pooled AUROC when too few per-domain samples.
    58	    """
    59	    subset = [(t, d) for t, d in pairs if slice_fn(t, d)]
    60	    if len(subset) < 5:
    61	        return None
    62	    tools = [t for t, _ in subset]
    63	    drs = [d for _, d in subset]
    64	
    65	    # Check label diversity
    66	    y = [t["label_gt"] for t in tools]
    67	    if len(set(y)) < 2:
    68	        return None
    69	
    70	    # Try macro; fall back to pooled if not enough domains
    71	    a_tool = macro_auroc_from_results(tools)
    72	    a_direct = macro_auroc_from_results(drs)
    73	    if np.isnan(a_tool) or np.isnan(a_direct):
    74	        # pooled
    75	        s_t = [t["anomaly_score"] for t in tools]
    76	        s_d = [d["anomaly_score"] for d in drs]
    77	        a_tool = _safe_auroc(y, s_t)
    78	        a_direct = _safe_auroc(y, s_d)
    79	        if np.isnan(a_tool) or np.isnan(a_direct):
    80	            return None
    81	
    82	    # Bootstrap paired delta (pooled AUROC basis)
    83	    s_t_arr = np.asarray([t["anomaly_score"] for t in tools])
    84	    s_d_arr = np.asarray([d["anomaly_score"] for d in drs])
    85	    y_arr = np.asarray(y)
    86	    n = len(y_arr)
    87	    deltas = []
    88	    for _ in range(N_BOOT):
    89	        idx = RNG.integers(0, n, n)
    90	        if len(set(y_arr[idx])) < 2:
    91	            continue
    92	        try:
    93	            dt = (roc_auc_score(y_arr[idx], s_t_arr[idx])
    94	                  - roc_auc_score(y_arr[idx], s_d_arr[idx]))
    95	            deltas.append(dt)
    96	        except Exception:
    97	            continue
    98	    if not deltas:
    99	        return None
   100	    return {
   101	        "slice": slice_name,
   102	        "n": n,
   103	        "auroc_tool": float(a_tool),
   104	        "auroc_direct": float(a_direct),
   105	        "delta": float(a_tool - a_direct),
   106	        "delta_ci": [float(np.percentile(deltas, 2.5)),
   107	                     float(np.percentile(deltas, 97.5))],
   108	    }
   109	
   110	
   111	def _load_expert_rank_map(split: str):
   112	    """Return item_id -> subspacead normalized_rank for direct_margin / expert
   113	    slicing. Uses the same method as tool_expert_score."""
   114	    try:
   115	        import sys
   116	        sys.path.insert(0, str(Path(__file__).resolve().parent))
   117	        from agent_tools_v7 import _load_expert_scores
   118	        recs, all_scores = _load_expert_scores("subspacead", split)
   119	        if len(all_scores) == 0:
   120	            return {}
   121	        rank_map = {}
   122	        for iid, rec in recs.items():
   123	            if rec.get("anomaly_score") is None:
   124	                continue
   125	            s = float(rec["anomaly_score"])
   126	            rank_map[iid] = float(np.searchsorted(all_scores, s) / len(all_scores))
   127	        return rank_map
   128	    except Exception:
   129	        return {}
   130	
   131	
   132	def build_slices(direct_results: list, split: str):
   133	    rank_map = _load_expert_rank_map(split)
   134	    domains = sorted({x.get("domain_code") for x in direct_results
   135	                      if x.get("domain_code") is not None})
   136	    slices: list[tuple[str, callable]] = []
   137	    for d in domains:
   138	        slices.append((f"domain={d}",
   139	                       lambda t, _d, d=d: t.get("domain_code") == d))
   140	    slices.append(("direct_margin<0.15 (uncertain)",
   141	                   lambda t, d: abs(d.get("anomaly_score", 0.5) - 0.5) < 0.15))
   142	    slices.append(("direct_margin>=0.30 (confident)",
   143	                   lambda t, d: abs(d.get("anomaly_score", 0.5) - 0.5) >= 0.30))
   144	    slices.append(("tool_used=True",
   145	                   lambda t, d: bool(t.get("used_tool"))))
   146	    slices.append(("tool_used=False",
   147	                   lambda t, d: not bool(t.get("used_tool"))))
   148	    if rank_map:
   149	        slices.append(("subspacead_rank<=0.4 (weak expert)",
   150	                       lambda t, d, rm=rank_map:
   151	                       rm.get(t.get("item_id"), 0.5) <= 0.4))
   152	        slices.append(("subspacead_rank in [0.4,0.8) (moderate expert)",
   153	                       lambda t, d, rm=rank_map:
   154	                       0.4 < rm.get(t.get("item_id"), 0.5) < 0.8))
   155	        slices.append(("subspacead_rank>=0.8 (strong expert)",
   156	                       lambda t, d, rm=rank_map:
   157	                       rm.get(t.get("item_id"), 0.5) >= 0.8))
   158	    slices.append(("n_turns=1 (no tool, tool-offered)",
   159	                   lambda t, d: t.get("n_turns") == 1))
   160	    slices.append(("n_turns>=2 (actually explored)",
   161	                   lambda t, d: t.get("n_turns") is not None and t.get("n_turns") >= 2))
   162	    return slices
   163	
   164	
   165	def main():
   166	    ap = argparse.ArgumentParser()
   167	    ap.add_argument("--tool_file", required=True)
   168	    ap.add_argument("--direct_file", required=True)
   169	    ap.add_argument("--out_md", required=True)
   170	    ap.add_argument("--split", default="dev")
   171	    ap.add_argument("--threshold_n", type=int, default=10)
   172	    args = ap.parse_args()
   173	
   174	    tool_results = json.load(open(args.tool_file))
   175	    direct_results = json.load(open(args.direct_file))
   176	    tool_name = Path(args.tool_file).stem
   177	
   178	    direct_by_id = {x["item_id"]: x for x in direct_results}
   179	    pairs = [(t, direct_by_id[t["item_id"]]) for t in tool_results
   180	             if t.get("item_id") in direct_by_id
   181	             and t.get("label_gt") is not None]
   182	
   183	    overall = {
   184	        "tool": tool_name,
   185	        "n_total": len(pairs),
   186	        "n_called": sum(1 for t, _ in pairs if t.get("used_tool")),
   187	        "n_errors": sum(1 for t, _ in pairs if t.get("error")),
   188	        "full_tool_macro": macro_auroc_from_results([t for t, _ in pairs]),
   189	        "full_direct_macro": macro_auroc_from_results([d for _, d in pairs]),
   190	    }
   191	    overall["full_delta"] = (overall["full_tool_macro"]
   192	                             - overall["full_direct_macro"])
   193	    overall["call_rate"] = (overall["n_called"] / overall["n_total"] * 100
   194	                            if overall["n_total"] else 0)
   195	
   196	    slices = build_slices(direct_results, args.split)
   197	    findings = []
   198	    for name, fn in slices:
   199	        res = slice_macro_delta(pairs, fn, name)
   200	        if res and res["n"] >= args.threshold_n:
   201	            findings.append(res)
   202	    findings.sort(key=lambda x: -x["delta"])
   203	
   204	    positive_niches = [f for f in findings
   205	                       if f["delta"] > 0 and f["delta_ci"][0] > 0]
   206	    anti = [f for f in findings
   207	            if f["delta"] < 0 and f["delta_ci"][1] < 0]
   208	    verdict = "KEEP" if positive_niches else "DROP"
   209	
   210	    lines: list[str] = [
   211	        f"# Tool Card: {tool_name}",
   212	        "",
   213	        f"**Verdict:** {verdict}  ",
   214	        f"**Overall (dev n={overall['n_total']})**: tool={overall['full_tool_macro']:.4f}  "
   215	        f"direct={overall['full_direct_macro']:.4f}  Δ={overall['full_delta']:+.4f}  ",
   216	        f"**Calls**: {overall['n_called']}/{overall['n_total']} "
   217	        f"({overall['call_rate']:.1f}%)  ",
   218	        f"**Errors**: {overall['n_errors']}  ",
   219	        "",
   220	        "## Positive niches (n≥{}, Δ>0, 95% CI lower > 0)".format(args.threshold_n),
   221	        "",
   222	    ]
   223	    if not positive_niches:
   224	        lines += ["_None found. Tool has no demonstrated niche on dev._", ""]
   225	    else:
   226	        lines.append("| slice | n | tool AUROC | direct AUROC | Δ | 95% CI |")
   227	        lines.append("|---|---|---|---|---|---|")
   228	        for f in positive_niches:
   229	            lines.append(f"| {f['slice']} | {f['n']} | {f['auroc_tool']:.3f} | "
   230	                         f"{f['auroc_direct']:.3f} | {f['delta']:+.3f} | "
   231	                         f"[{f['delta_ci'][0]:+.3f}, {f['delta_ci'][1]:+.3f}] |")
   232	        lines.append("")
   233	
   234	    lines += ["## Anti-niches (Δ<0, 95% CI upper < 0)", ""]
   235	    if not anti:
   236	        lines += ["_None flagged._", ""]
   237	    else:
   238	        lines.append("| slice | n | tool AUROC | direct AUROC | Δ | 95% CI |")
   239	        lines.append("|---|---|---|---|---|---|")
   240	        for f in anti:
   241	            lines.append(f"| {f['slice']} | {f['n']} | {f['auroc_tool']:.3f} | "
   242	                         f"{f['auroc_direct']:.3f} | {f['delta']:+.3f} | "
   243	                         f"[{f['delta_ci'][0]:+.3f}, {f['delta_ci'][1]:+.3f}] |")
   244	        lines.append("")
   245	
   246	    lines += ["## All slices (audit)", ""]
   247	    lines.append("| slice | n | tool | direct | Δ | 95% CI |")
   248	    lines.append("|---|---|---|---|---|---|")
   249	    for f in findings:
   250	        lines.append(f"| {f['slice']} | {f['n']} | {f['auroc_tool']:.3f} | "
   251	                     f"{f['auroc_direct']:.3f} | {f['delta']:+.3f} | "
   252	                     f"[{f['delta_ci'][0]:+.3f}, {f['delta_ci'][1]:+.3f}] |")
   253	    lines.append("")
   254	
   255	    lines += ["## Agent hint (injected into agent_v7 prompt if KEEP)", ""]
   256	    if positive_niches:
   257	        best = positive_niches[0]
   258	        lines.append(f"**When to use {tool_name}:** especially helpful on "
   259	                     f"`{best['slice']}` (Δ={best['delta']:+.3f} on n={best['n']}).")
   260	    else:

exec
/bin/bash -lc "nl -ba benchmark/scripts/agent_v6.py | sed -n '236,260p' && nl -ba benchmark/scripts/build_tool_card.py | sed -n '255,290p' && nl -ba benchmark/scripts/tool_audit_runner.py | sed -n '1,130p' && nl -ba benchmark/scripts/agent_prompt_v7.py | sed -n '70,115p' && nl -ba benchmark/scripts/diagnose_tools.py | sed -n '1,90p'" in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
   236	def _obs_to_text(obs: dict) -> str:
   237	    """Compact text summary of an observation (no base64 payloads)."""
   238	    small = {}
   239	    for k, v in obs.items():
   240	        if k.endswith("_b64"):
   241	            small[k] = f"<{len(v)}-char image>"
   242	        elif k == "tiles":
   243	            small[k] = f"<{len(v)} tiles attached>"
   244	        elif k == "top_patches":
   245	            small[k] = f"<{len(v)} patches>"
   246	        else:
   247	            small[k] = v
   248	    return json.dumps(small, default=str)[:1500]
   249	
   250	
   251	# ── CLI entry ──────────────────────────────────────────────────────────────
   252	
   253	def main():
   254	    ap = argparse.ArgumentParser()
   255	    ap.add_argument("--manifest", required=True)
   256	    ap.add_argument("--split", choices=["calibration", "dev", "test"], required=True)
   257	    ap.add_argument("--backend", choices=["qwen3", "seedvl", "gpt"], required=True)
   258	    ap.add_argument("--output", required=True)
   259	    ap.add_argument("--domains", nargs="*", default=None)
   260	    ap.add_argument("--max_turns", type=int, default=5)
   255	    lines += ["## Agent hint (injected into agent_v7 prompt if KEEP)", ""]
   256	    if positive_niches:
   257	        best = positive_niches[0]
   258	        lines.append(f"**When to use {tool_name}:** especially helpful on "
   259	                     f"`{best['slice']}` (Δ={best['delta']:+.3f} on n={best['n']}).")
   260	    else:
   261	        lines.append(f"**When to use {tool_name}:** no documented positive niche "
   262	                     f"on dev. DROPPED.")
   263	    if anti:
   264	        worst = min(anti, key=lambda x: x["delta"])
   265	        lines.append(f"**Avoid {tool_name} on:** `{worst['slice']}` "
   266	                     f"(Δ={worst['delta']:+.3f} on n={worst['n']}).")
   267	    lines.append("")
   268	
   269	    Path(args.out_md).parent.mkdir(parents=True, exist_ok=True)
   270	    with open(args.out_md, "w") as f:
   271	        f.write("\n".join(lines))
   272	    print(f"wrote {args.out_md}  verdict={verdict}  "
   273	          f"pos={len(positive_niches)} anti={len(anti)}")
   274	
   275	
   276	if __name__ == "__main__":
   277	    main()
     1	"""Queue 13 single-tool audits sequentially; each uses max_workers concurrency
     2	internally. Sequential across tools avoids rate-limit bleed between audits.
     3	"""
     4	from __future__ import annotations
     5	import argparse
     6	import subprocess
     7	import sys
     8	import time
     9	from pathlib import Path
    10	
    11	TOOLS = [
    12	    "tool_zoom_bbox",           # +7pp in v6.5 (only positive tool); validate
    13	    "tool_expert_score",        # 76% coverage; largest lever
    14	    "tool_hotspot_cropper",
    15	    "tool_side_by_side",
    16	    "tool_image_diff",
    17	    "tool_reference_profiler",  # worst offender -9.4pp
    18	    "tool_component_counter",
    19	    "tool_patch_grid",
    20	    "tool_rotate_align",         # -28pp in v6.5 — gate aggressively
    21	    "tool_domain_knowledge",
    22	    "tool_segment_and_count",
    23	    "tool_texture_fft",          # never called in v6.5
    24	    "tool_reference_retriever",  # never called in v6.5
    25	]
    26	
    27	
    28	def main():
    29	    ap = argparse.ArgumentParser()
    30	    ap.add_argument("--manifest",
    31	                    default="benchmark/manifests/full_manifest.json")
    32	    ap.add_argument("--split", default="dev")
    33	    ap.add_argument("--out_dir", default="benchmark/results/tool_audit")
    34	    ap.add_argument("--max_turns", type=int, default=3)
    35	    ap.add_argument("--max_workers", type=int, default=9)
    36	    ap.add_argument("--tools", nargs="*", default=None,
    37	                    help="subset of tools (default: all)")
    38	    ap.add_argument("--skip_existing", action="store_true", default=True)
    39	    args = ap.parse_args()
    40	
    41	    Path(args.out_dir).mkdir(parents=True, exist_ok=True)
    42	    tools = args.tools or TOOLS
    43	    script = "benchmark/scripts/single_tool_agent.py"
    44	
    45	    t0 = time.time()
    46	    for i, tool in enumerate(tools, 1):
    47	        out = f"{args.out_dir}/{tool}.json"
    48	        if args.skip_existing and Path(out).exists():
    49	            print(f"[{i}/{len(tools)}] skip {tool}: {out} exists", flush=True)
    50	            continue
    51	        cmd = [sys.executable, script,
    52	               "--tool", tool, "--split", args.split,
    53	               "--manifest", args.manifest, "--output", out,
    54	               "--max_turns", str(args.max_turns),
    55	               "--max_workers", str(args.max_workers)]
    56	        t_tool = time.time()
    57	        print(f"[{i}/{len(tools)}] running {tool} ...", flush=True)
    58	        r = subprocess.run(cmd, capture_output=True, text=True)
    59	        if r.returncode != 0:
    60	            print(f"[{i}/{len(tools)}] FAIL {tool}: rc={r.returncode}\n"
    61	                  f"stderr tail:\n{r.stderr[-800:]}", flush=True)
    62	            with open(f"{args.out_dir}/{tool}.stderr.log", "w") as f:
    63	                f.write(r.stderr)
    64	        else:
    65	            print(f"[{i}/{len(tools)}] OK   {tool}  "
    66	                  f"t_tool={time.time()-t_tool:.1f}s  "
    67	                  f"t_total={time.time()-t0:.1f}s", flush=True)
    68	            # echo last line of child stdout
    69	            last = r.stdout.strip().splitlines()
    70	            if last:
    71	                print(f"          {last[-1]}", flush=True)
    72	
    73	    print(f"\ntool_audit_runner done in {time.time()-t0:.1f}s")
    74	
    75	
    76	if __name__ == "__main__":
    77	    main()
    70	    always cross-check with visual evidence.
    71	"""
    72	
    73	
    74	try:
    75	    from agent_tool_hints_v7 import TOOL_HINTS  # auto-generated by compose_v7_prompt.py
    76	except ImportError:
    77	    TOOL_HINTS = "(tool hints not yet generated — running un-hinted)"
    78	
    79	
    80	SYSTEM_PROMPT = f"""You are a visual anomaly detection agent.
    81	
    82	INPUT PER IMAGE: one query image, four normal reference images, a turn budget.
    83	TASK: decide if the query is normal or anomalous and output a score in [0,1]
    84	where 1 means certainly anomalous.
    85	
    86	YOU HAVE NO DOMAIN INFORMATION. Figure out what the images are from vision
    87	alone. The tools below can help you probe further.
    88	
    89	{TOOL_OUTPUT_GUIDE}
    90	
    91	{TOOL_CATALOG}
    92	
    93	EMPIRICAL TOOL PERFORMANCE (observed on a held-out dev set; use as general
    94	guidance, not as a decision for this specific image):
    95	{TOOL_HINTS}
    96	
    97	PROTOCOL: On each turn, return ONLY a JSON object:
    98	{{
    99	  "thought":  "<one or two sentences>",
   100	  "action":   "call_tool" | "final",
   101	  "tool":     "<tool_name>" | null,
   102	  "args":     {{ ... }} | null,
   103	  "confidence": <integer 0..100>,
   104	  "score":    <float 0..1> | null,
   105	  "rationale": "<one or two sentences>" | null
   106	}}
   107	
   108	Required if action=="final": score and rationale.
   109	Required if action=="call_tool": tool and args.
   110	
   111	GUIDELINES:
   112	- Use a tool only if it will change your answer. If the query looks clearly
   113	  normal or anomalous at turn 1, output final without calling any tool.
   114	- READ the disconfirm clause of every tool output. A positive-looking signal
   115	  that satisfies the disconfirm clause is NOT evidence of anomaly.
     1	"""Extract 20 cases per tool (10 wins, 10 losses) from v6.5 test results
     2	for manual failure-mode inspection.
     3	
     4	A "win" = tool call correlated with lower error than Direct on same item.
     5	A "loss" = tool call correlated with higher error than Direct.
     6	"""
     7	from __future__ import annotations
     8	import json
     9	import os
    10	from collections import defaultdict
    11	
    12	RESULTS = "benchmark/results/v6_5_agent_qwen3_test.json"
    13	DIRECT = "benchmark/results/v6_direct_qwen3_test.json"
    14	OUT_DIR = "refine-logs/tool_diagnosis"
    15	
    16	os.makedirs(OUT_DIR, exist_ok=True)
    17	
    18	v65 = json.load(open(RESULTS))
    19	direct = {x["item_id"]: x for x in json.load(open(DIRECT))}
    20	
    21	by_tool: dict[str, list[dict]] = defaultdict(list)
    22	for r in v65:
    23	    tools = r.get("tools_used") or []
    24	    label = r.get("label_gt")
    25	    if label is None:
    26	        continue
    27	    agent_score = r.get("anomaly_score", 0.5)
    28	    direct_score = direct.get(r["item_id"], {}).get("anomaly_score", 0.5)
    29	    agent_err = abs(agent_score - label)
    30	    direct_err = abs(direct_score - label)
    31	    delta_err = agent_err - direct_err  # negative = agent better
    32	    for t in set(tools):
    33	        by_tool[t].append({
    34	            "item_id": r["item_id"],
    35	            "domain": r.get("domain_code"),
    36	            "label": label,
    37	            "agent_score": agent_score,
    38	            "direct_score": direct_score,
    39	            "delta_err": delta_err,
    40	            "tools_used": tools,
    41	            "rationale": (r.get("rationale") or "")[:240],
    42	        })
    43	
    44	for tool, cases in sorted(by_tool.items()):
    45	    cases.sort(key=lambda x: x["delta_err"])
    46	    wins = cases[:10]   # agent better
    47	    losses = cases[-10:]  # agent worse
    48	    out = [
    49	        f"# Diagnosis: {tool}",
    50	        "",
    51	        f"Total calls: {len(cases)}",
    52	        "",
    53	        "## Failure mode (manual analysis — fill in)",
    54	        "",
    55	        "_TBD: wrong trigger / unclear output / VLM misreads / mixed_",
    56	        "",
    57	        "## Wins (agent better than Direct)",
    58	        "",
    59	    ]
    60	    for h in wins:
    61	        out.append(f"- `{h['item_id']}` [{h['domain']}] label={h['label']} agent={h['agent_score']:.2f} direct={h['direct_score']:.2f} Δerr={h['delta_err']:+.3f}")
    62	        out.append(f"  > {h['rationale']}")
    63	        out.append("")
    64	    out += ["## Losses (agent worse than Direct)", ""]
    65	    for m in losses:
    66	        out.append(f"- `{m['item_id']}` [{m['domain']}] label={m['label']} agent={m['agent_score']:.2f} direct={m['direct_score']:.2f} Δerr={m['delta_err']:+.3f}")
    67	        out.append(f"  > {m['rationale']}")
    68	        out.append("")
    69	    with open(f"{OUT_DIR}/{tool}.md", "w") as f:
    70	        f.write("\n".join(out))
    71	    print(f"wrote {OUT_DIR}/{tool}.md  (n_calls={len(cases)})")
    72	
    73	print("\nTools with zero calls in v6.5:")
    74	seen = set(by_tool.keys())
    75	ALL = {
    76	    "tool_expert_score", "tool_hotspot_cropper", "tool_zoom_bbox",
    77	    "tool_patch_grid", "tool_image_diff", "tool_rotate_align",
    78	    "tool_side_by_side", "tool_reference_profiler", "tool_reference_retriever",
    79	    "tool_component_counter", "tool_segment_and_count", "tool_texture_fft",
    80	    "tool_domain_knowledge",
    81	}
    82	for t in sorted(ALL - seen):
    83	    print(f"  {t}")

exec
/bin/bash -lc "nl -ba benchmark/scripts/agent_tools_v7.py | sed -n '145,235p;505,575p'" in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
   145	                   f"deviation, but within normal variation for many images)")
   146	        disconfirm = (f"the refs show comparable variation, or the score reflects "
   147	                      f"benign domain texture not a defect")
   148	    else:
   149	        verdict = (f"weak signal (rank {rank:.2f}: the query looks like normal "
   150	                   f"samples in this split)")
   151	        disconfirm = (f"a small localised defect may not shift the global {expert} "
   152	                      f"score; do not rule out anomaly if a suspicious region is visible")
   153	    out = {
   154	        "expert": expert,
   155	        "score": s,
   156	        "normalized_rank": rank,
   157	        "top_patches": rec.get("top_patches") or [],
   158	        "error": None,
   159	    }
   160	    return _wrap_interpretation(out, verdict, disconfirm)
   161	
   162	
   163	# ─── Tier 2: Visual inspection ──────────────────────────────────────────────
   164	
   165	def tool_hotspot_cropper(query_path: str, patches: list[dict] | None = None,
   166	                         pad: float = 0.15, k: int = 5,
   167	                         _expert_patches: list | None = None, **_) -> dict:
   168	    """Crop query image around top-k expert-flagged patches (48x48 grid).
   169	
   170	    If `patches` is not provided, falls back to `_expert_patches` from session
   171	    context (populated by a prior tool_expert_score call).
   172	    """
   173	    patches = patches or _expert_patches or []
   174	    if not patches:
   175	        return {"error": "no patches available; call tool_expert_score(subspacead) first"}
   176	    img = Image.open(query_path).convert("RGB")
   177	    W, H = img.size
   178	    grid = 48
   179	    rows = [p.get("row") for p in patches[:k] if p.get("row") is not None]
   180	    cols = [p.get("col") for p in patches[:k] if p.get("col") is not None]
   181	    if not rows or not cols:
   182	        return {"error": "patches missing row/col fields"}
   183	    r0, r1 = min(rows), max(rows) + 1
   184	    c0, c1 = min(cols), max(cols) + 1
   185	    span_r, span_c = r1 - r0, c1 - c0
   186	    r0 = max(0, r0 - max(1, int(pad * max(span_r, 1))))
   187	    r1 = min(grid, r1 + max(1, int(pad * max(span_r, 1))))
   188	    c0 = max(0, c0 - max(1, int(pad * max(span_c, 1))))
   189	    c1 = min(grid, c1 + max(1, int(pad * max(span_c, 1))))
   190	    x0, x1 = int(c0 / grid * W), int(c1 / grid * W)
   191	    y0, y1 = int(r0 / grid * H), int(r1 / grid * H)
   192	    if x1 <= x0 or y1 <= y0:
   193	        return {"error": "degenerate crop"}
   194	    crop = img.crop((x0, y0, x1, y1))
   195	    out = {
   196	        "bbox": [x0, y0, x1, y1],
   197	        "crop_b64": _pil_to_b64(crop),
   198	        "original_size": [W, H],
   199	        "n_patches_used": len(patches[:k]),
   200	        "error": None,
   201	    }
   202	    verdict = (f"high-expert-attention region extracted from {out['n_patches_used']} "
   203	               f"hotspot patches; inspect crop for a genuine defect")
   204	    disconfirm = ("the attention region shows normal texture, a lighting artifact, "
   205	                  "or a benign edge — in that case treat as normal")
   206	    return _wrap_interpretation(out, verdict, disconfirm)
   207	
   208	
   209	def tool_zoom_bbox(query_path: str, bbox: list[int], **_) -> dict:
   210	    """Agent-specified crop. bbox = [x0, y0, x1, y1] in pixel coords."""
   211	    if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
   212	        return {"error": "bbox must be [x0, y0, x1, y1]"}
   213	    x0, y0, x1, y1 = bbox
   214	    if x1 <= x0 or y1 <= y0:
   215	        return {"error": f"invalid bbox {bbox}: x1 must be > x0 and y1 > y0"}
   216	    img = Image.open(query_path).convert("RGB")
   217	    W, H = img.size
   218	    x0 = max(0, min(W - 1, int(x0)))
   219	    y0 = max(0, min(H - 1, int(y0)))
   220	    x1 = max(x0 + 1, min(W, int(x1)))
   221	    y1 = max(y0 + 1, min(H, int(y1)))
   222	    crop = img.crop((x0, y0, x1, y1))
   223	    out = {
   224	        "bbox": [x0, y0, x1, y1],
   225	        "crop_b64": _pil_to_b64(crop),
   226	        "original_size": [W, H],
   227	        "error": None,
   228	    }
   229	    verdict = ("agent-requested region returned at higher resolution; "
   230	               "inspect closely for localised defect not visible at overview scale")
   231	    disconfirm = ("the crop shows normal surface texture or a benign visual cue "
   232	                  "(lighting, joint, shadow) — in that case treat as normal")
   233	    return _wrap_interpretation(out, verdict, disconfirm)
   234	
   235	
   505	                    "similarity": float(sims[i])} for i in top_idx]
   506	        out = {"results": results, "error": None,
   507	               "top_similarity": float(sims[top_idx[0]]) if len(top_idx) else 0.0}
   508	        verdict = (f"top-{k} most similar NORMAL refs retrieved "
   509	                   f"(top_similarity={out['top_similarity']:.3f})")
   510	        disconfirm = ("high top_similarity means the query matches a normal cluster "
   511	                      "well → likely NORMAL. Low similarity alone does NOT prove anomaly "
   512	                      "— the query may just be in a less-represented normal subtype")
   513	        return _wrap_interpretation(out, verdict, disconfirm)
   514	    except Exception as e:
   515	        return {"error": f"retrieval failed: {e}"}
   516	
   517	
   518	# ─── Tier 4: Structural analysis ────────────────────────────────────────────
   519	
   520	def tool_component_counter(patches: list[dict] | None = None,
   521	                           _expert_patches: list | None = None,
   522	                           threshold: float = 0.5, **_) -> dict:
   523	    """Count connected components among top-k expert patches (48x48 grid, 4-conn)."""
   524	    patches = patches or _expert_patches or []
   525	    # v7: require at least 3 hotspot patches for component count to be meaningful
   526	    if len(patches) < 3:
   527	        out = {"error": None, "n_components": 0, "n_active_patches": len(patches),
   528	               "not_applicable": True}
   529	        verdict = (f"not applicable: only {len(patches)} expert patch(es) available; "
   530	                   f"component counting needs >=3 patches to be meaningful")
   531	        disconfirm = "ignore this tool's output for this sample"
   532	        return _wrap_interpretation(out, verdict, disconfirm)
   533	    grid = np.zeros((48, 48), dtype=np.uint8)
   534	    for p in patches:
   535	        r, c = p.get("row"), p.get("col")
   536	        if r is not None and c is not None and 0 <= r < 48 and 0 <= c < 48:
   537	            grid[r, c] = 1
   538	    n, seen = 0, np.zeros_like(grid, dtype=bool)
   539	    for i in range(48):
   540	        for j in range(48):
   541	            if grid[i, j] and not seen[i, j]:
   542	                n += 1
   543	                stack = [(i, j)]
   544	                while stack:
   545	                    ii, jj = stack.pop()
   546	                    if (0 <= ii < 48 and 0 <= jj < 48 and grid[ii, jj]
   547	                            and not seen[ii, jj]):
   548	                        seen[ii, jj] = True
   549	                        stack.extend([(ii+1, jj), (ii-1, jj),
   550	                                      (ii, jj+1), (ii, jj-1)])
   551	    n_active = int(grid.sum())
   552	    out = {"error": None, "n_components": int(n),
   553	           "n_active_patches": n_active, "not_applicable": False}
   554	    verdict = (f"{n} connected hotspot blob(s) across {n_active} active patches; "
   555	               f"many small blobs = diffuse anomaly, one large blob = localised defect")
   556	    disconfirm = ("expert hotspots may be spread across normal high-variance regions "
   557	                  "without a true defect; cross-check with zoom_bbox")
   558	    return _wrap_interpretation(out, verdict, disconfirm)
   559	
   560	
   561	def tool_segment_and_count(query_path: str, ref_paths: list[str] | None = None,
   562	                           grid_size: int = 8, **_) -> dict:
   563	    """Coarse structural-change signal via 8x8 intensity-grid diff vs ref 0."""
   564	    if not ref_paths:
   565	        return {"error": "ref_paths required"}
   566	    q = np.array(Image.open(query_path).convert("L").resize((256, 256)))
   567	    r = np.array(Image.open(ref_paths[0]).convert("L").resize((256, 256)))
   568	    cell = 256 // grid_size
   569	    q_grid = q.reshape(grid_size, cell, grid_size, cell).mean(axis=(1, 3))
   570	    r_grid = r.reshape(grid_size, cell, grid_size, cell).mean(axis=(1, 3))
   571	    diff = np.abs(q_grid - r_grid)
   572	    changed = int((diff > 20).sum())
   573	    top_idx = np.argsort(diff.ravel())[::-1][:5]
   574	    top_diffs = [{"row": int(i // grid_size), "col": int(i % grid_size),
   575	                  "diff": float(diff.ravel()[i])} for i in top_idx

exec
/bin/bash -lc "find refine-logs -maxdepth 3 -type f | sort | sed -n '1,120p'" in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
refine-logs/CODEX_REVIEW_2026-04-18.md
refine-logs/EXPERIMENT_LOG_20260415.md
refine-logs/EXPLORATION_JOURNAL.md
refine-logs/OPTIMIZATION_LOG.md
refine-logs/RESEARCH_IDEA.md
refine-logs/V6_RESULTS.md
refine-logs/anomaclaw_v2/__init__.py
refine-logs/anomaclaw_v2/bootstrap.py
refine-logs/anomaclaw_v2/bootstrap_fast.py
refine-logs/anomaclaw_v2/registry.py
refine-logs/anomaclaw_v2/router.py
refine-logs/case_studies_v6_5_qwen3.md
refine-logs/eval_anomaclaw_v3.py
refine-logs/expert_strategy_qwen3.md
refine-logs/finalize_v3_paper.sh
refine-logs/router_dev_vs_direct.json
refine-logs/router_fusion_v65_vs_direct.json
refine-logs/router_fusion_v65_vs_fusion.json
refine-logs/router_gpt_vs_direct.json
refine-logs/router_gpt_vs_fusion.json
refine-logs/router_v65only_vs_direct.json
refine-logs/tool_diagnosis/tool_component_counter.md
refine-logs/tool_diagnosis/tool_domain_knowledge.md
refine-logs/tool_diagnosis/tool_expert_score.md
refine-logs/tool_diagnosis/tool_hotspot_cropper.md
refine-logs/tool_diagnosis/tool_image_diff.md
refine-logs/tool_diagnosis/tool_patch_grid.md
refine-logs/tool_diagnosis/tool_reference_profiler.md
refine-logs/tool_diagnosis/tool_rotate_align.md
refine-logs/tool_diagnosis/tool_segment_and_count.md
refine-logs/tool_diagnosis/tool_side_by_side.md
refine-logs/tool_diagnosis/tool_zoom_bbox.md
refine-logs/tool_effects_qwen3_v6_5.md
refine-logs/update_paper_with_v3.py
refine-logs/v6_6_eval_gpt_vs_direct.json
refine-logs/v6_6_eval_gpt_vs_fusion.json
refine-logs/v6_7_eval_gpt_vs_direct.json
refine-logs/v6_7_eval_gpt_vs_fusion.json
refine-logs/v6_eval_gpt_v66.json
refine-logs/v6_eval_qwen3.json
refine-logs/v6_eval_qwen3_direct.json
refine-logs/v6_eval_qwen3_fusion.log
refine-logs/v6_eval_seedvl.json
refine-logs/v6_eval_seedvl_direct.json
refine-logs/v6_eval_seedvl_fusion.json
refine-logs/v7_direct_dev_baseline.txt

exec
/bin/bash -lc "nl -ba benchmark/scripts/agent_prompt_v7.py | sed -n '18,70p'" in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
    18	ignored for the current sample."""
    19	
    20	
    21	TOOL_CATALOG = """Available tools (call at most one per turn):
    22	
    23	EXPERT PROBES
    24	  tool_expert_score(expert="subspacead"|"anomalyvfm"|"patchknn"|"dinov2_global")
    25	    Returns {score, normalized_rank, interpretation, top_patches}.
    26	    rank>=0.85 => strong. rank<=0.6 weak. Moderate in between. Calling this with
    27	    expert="subspacead" also makes patch hotspots available to hotspot_cropper /
    28	    component_counter.
    29	
    30	VISUAL INSPECTION
    31	  tool_hotspot_cropper(k=5)
    32	    Zooms into the top-k subspacead hotspots. Requires a prior
    33	    tool_expert_score(expert="subspacead") call.
    34	  tool_zoom_bbox(bbox=[x0,y0,x1,y1])
    35	    Agent-specified pixel crop of the query. Use for localised-defect hypothesis.
    36	  tool_patch_grid(rows=N, cols=M)
    37	    Cuts the query into N x M tiles (capped at 3x3).
    38	  tool_image_diff(ref_idx=0..3)
    39	    Pixel diff vs the ref_idx-th reference; returns stats + mask + unreliable flag.
    40	    AVOID when images are not spatially aligned (natural scenes, medical slices,
    41	    rotated industrial parts).
    42	  tool_rotate_align(ref_idx=0..3)
    43	    Like image_diff but tries small rotations first. Still unreliable on
    44	    non-rigid images.
    45	  tool_side_by_side(bbox=[x0,y0,x1,y1])
    46	    Composite showing query + 4 refs all cropped to same bbox. bbox is in
    47	    256x256 normalized coords.
    48	
    49	REFERENCE UNDERSTANDING
    50	  tool_reference_profiler()
    51	    VLM describes the NORMAL baseline in 4 fields (object / expected_color /
    52	    expected_shape / allowed_variation). Use when you need to know what
    53	    variation IS allowed in refs before judging the query.
    54	  tool_reference_retriever(k=4)
    55	    Re-pulls k refs more similar to the query from the domain's full
    56	    normal pool.
    57	
    58	STRUCTURAL
    59	  tool_component_counter()
    60	    Connected-component count among subspacead hotspots. Needs >=3 hotspot
    61	    patches to be meaningful.
    62	  tool_segment_and_count()
    63	    Coarse 8x8 grid diff vs ref 0 — rough structural change signal.
    64	  tool_texture_fft()
    65	    Periodicity score (0=irregular, 1=strongly periodic texture).
    66	
    67	SEMANTIC
    68	  tool_domain_knowledge(question="...")
    69	    Free-form text question answered by an LLM. LLM may hallucinate —
    70	    always cross-check with visual evidence.

exec
/bin/bash -lc "rg -n '\"split\": \"dev\"|domain_code|label' benchmark/manifests/full_manifest.json | head" in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
5:    "domain_code": "D1",
19:    "label": 0,
28:    "domain_code": "D1",
42:    "label": 0,
51:    "domain_code": "D1",
65:    "label": 0,
74:    "domain_code": "D1",
88:    "label": 0,
97:    "domain_code": "D1",
111:    "label": 0,

exec
/bin/bash -lc 'rg -n "TBD|Failure mode|manual analysis" refine-logs/tool_diagnosis benchmark/scripts -S' in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
refine-logs/tool_diagnosis/tool_image_diff.md:5:## Failure mode (manual analysis — fill in)
refine-logs/tool_diagnosis/tool_image_diff.md:7:_TBD: wrong trigger / unclear output / VLM misreads / mixed_
refine-logs/tool_diagnosis/tool_reference_profiler.md:5:## Failure mode (manual analysis — fill in)
refine-logs/tool_diagnosis/tool_reference_profiler.md:7:_TBD: wrong trigger / unclear output / VLM misreads / mixed_
refine-logs/tool_diagnosis/tool_patch_grid.md:5:## Failure mode (manual analysis — fill in)
refine-logs/tool_diagnosis/tool_patch_grid.md:7:_TBD: wrong trigger / unclear output / VLM misreads / mixed_
refine-logs/tool_diagnosis/tool_hotspot_cropper.md:5:## Failure mode (manual analysis — fill in)
refine-logs/tool_diagnosis/tool_hotspot_cropper.md:7:_TBD: wrong trigger / unclear output / VLM misreads / mixed_
refine-logs/tool_diagnosis/tool_zoom_bbox.md:5:## Failure mode (manual analysis — fill in)
refine-logs/tool_diagnosis/tool_zoom_bbox.md:7:_TBD: wrong trigger / unclear output / VLM misreads / mixed_
refine-logs/tool_diagnosis/tool_side_by_side.md:5:## Failure mode (manual analysis — fill in)
refine-logs/tool_diagnosis/tool_side_by_side.md:7:_TBD: wrong trigger / unclear output / VLM misreads / mixed_
refine-logs/tool_diagnosis/tool_rotate_align.md:5:## Failure mode (manual analysis — fill in)
refine-logs/tool_diagnosis/tool_rotate_align.md:7:_TBD: wrong trigger / unclear output / VLM misreads / mixed_
refine-logs/tool_diagnosis/tool_segment_and_count.md:5:## Failure mode (manual analysis — fill in)
refine-logs/tool_diagnosis/tool_segment_and_count.md:7:_TBD: wrong trigger / unclear output / VLM misreads / mixed_
refine-logs/tool_diagnosis/tool_domain_knowledge.md:5:## Failure mode (manual analysis — fill in)
refine-logs/tool_diagnosis/tool_domain_knowledge.md:7:_TBD: wrong trigger / unclear output / VLM misreads / mixed_
refine-logs/tool_diagnosis/tool_component_counter.md:5:## Failure mode (manual analysis — fill in)
refine-logs/tool_diagnosis/tool_component_counter.md:7:_TBD: wrong trigger / unclear output / VLM misreads / mixed_
refine-logs/tool_diagnosis/tool_expert_score.md:5:## Failure mode (manual analysis — fill in)
refine-logs/tool_diagnosis/tool_expert_score.md:7:_TBD: wrong trigger / unclear output / VLM misreads / mixed_
benchmark/scripts/diagnose_tools.py:53:        "## Failure mode (manual analysis — fill in)",
benchmark/scripts/diagnose_tools.py:55:        "_TBD: wrong trigger / unclear output / VLM misreads / mixed_",

codex
One design issue is not in the original checklist but matters: two “single tools” are not actually standalone. `hotspot_cropper` and `component_counter` depend on prior expert patches, so their single-tool audits measure missing-prerequisite behavior unless the runner seeds that context.
exec
/bin/bash -lc "ls -lh benchmark/results | sed -n '1,120p'" in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
total 90M
drwxrwxr-x 2 jiangxi jiangxi 4.0K Mar 31 21:13 ablation_refs
-rw-rw-r-- 1 jiangxi jiangxi   62 Apr 13 11:00 agent_domain_selection.json
drwxrwxr-x 2 jiangxi jiangxi 4.0K Apr  4 16:09 agent_v2
drwxrwxr-x 2 jiangxi jiangxi 4.0K Apr  4 21:25 agent_v3
-rw-rw-r-- 1 jiangxi jiangxi 1.1M Apr 16 14:10 anomaclaw_react_asym_multi_test.json
-rw-rw-r-- 1 jiangxi jiangxi 218K Apr 16 14:17 anomaclaw_react_d5c.json
-rw-rw-r-- 1 jiangxi jiangxi 249K Apr 16 14:17 anomaclaw_react_d9_nocount.json
-rw-rw-r-- 1 jiangxi jiangxi 338K Apr 16 12:41 anomaclaw_react_qwen35_calib.json
-rw-rw-r-- 1 jiangxi jiangxi  15K Apr 16 12:37 anomaclaw_react_qwen35_smoke.json
-rw-rw-r-- 1 jiangxi jiangxi 212K Apr 16 12:51 anomaclaw_react_skill_d1_test.json
-rw-rw-r-- 1 jiangxi jiangxi 1.1M Apr 16 13:26 anomaclaw_react_skill_multi_test.json
-rw-rw-r-- 1 jiangxi jiangxi 390K Apr 16 14:41 anomaclaw_react_v2_d1d10.json
-rw-rw-r-- 1 jiangxi jiangxi 808K Apr 16 14:32 anomaclaw_react_v2_multi.json
-rw-rw-r-- 1 jiangxi jiangxi  12K Apr 15 21:45 anomaclaw_v3_qwen35_test_plans.json
-rw-rw-r-- 1 jiangxi jiangxi  49K Apr 15 13:36 anomaclaw_v3_seedvl_smoke.json
-rw-rw-r-- 1 jiangxi jiangxi 1.2K Apr 15 13:33 anomaclaw_v3_seedvl_smoke_plans.json
-rw-rw-r-- 1 jiangxi jiangxi 263K Apr 15 21:51 anomaclaw_v3_seedvl_test.json
-rw-rw-r-- 1 jiangxi jiangxi 335K Apr 15 22:06 anomaclaw_v4_qwen35_calib.json
-rw-rw-r-- 1 jiangxi jiangxi  49K Apr 15 22:02 anomaclaw_v4_qwen35_smoke.json
-rw-rw-r-- 1 jiangxi jiangxi 1.9M Apr 15 22:31 anomaclaw_v4_qwen35_test.json
-rw-rw-r-- 1 jiangxi jiangxi 243K Apr 16 12:26 anomaclaw_v4_seedvl_test.json
-rw-rw-r-- 1 jiangxi jiangxi 400K Apr 16 12:37 anomaclaw_v5_qwen35_calib.json
-rw-rw-r-- 1 jiangxi jiangxi 193K Apr 13 02:24 anomalyvfm_calibration.json
-rw-rw-r-- 1 jiangxi jiangxi 1.2M Apr 15 22:07 anomalyvfm_test.json
-rw-rw-r-- 1 jiangxi jiangxi  497 Apr 14 12:26 bootstrap_ci_results.json
-rw-rw-r-- 1 jiangxi jiangxi  242 Apr 14 12:27 budget_baselines.json
-rw-rw-r-- 1 jiangxi jiangxi 578K Apr 12 02:19 classical_dinov2_global_test_all.json
-rw-rw-r-- 1 jiangxi jiangxi 8.7K Apr 12 02:36 classical_dinov2_global_test_all_metrics.json
-rw-rw-r-- 1 jiangxi jiangxi 577K Apr 12 02:24 classical_dinov2_patch_test_all.json
-rw-rw-r-- 1 jiangxi jiangxi 8.8K Apr 12 02:36 classical_dinov2_patch_test_all_metrics.json
-rw-rw-r-- 1 jiangxi jiangxi 1.2K Apr 14 12:26 complementarity_matrix.json
drwxrwxr-x 2 jiangxi jiangxi 4.0K Apr  1 23:22 factorial
drwxrwxr-x 2 jiangxi jiangxi 4.0K Apr  2 16:33 full10
-rw-rw-r-- 1 jiangxi jiangxi 543K Apr 13 03:00 gpt54_agent_v1_calibration.json
-rw-rw-r-- 1 jiangxi jiangxi 3.1M Apr 13 05:20 gpt54_agent_v1_test.json
-rw-rw-r-- 1 jiangxi jiangxi 9.2K Apr 13 05:21 gpt54_agent_v1_test_metrics.json
-rw-rw-r-- 1 jiangxi jiangxi 2.9M Apr 13 11:53 gpt54_agent_v2_test.json
-rw-rw-r-- 1 jiangxi jiangxi 1.5M Apr 13 18:25 gpt54_agent_v3_test.json
-rw-rw-r-- 1 jiangxi jiangxi 264K Apr 12 08:30 gpt54_egra_calibration_egra.json
-rw-rw-r-- 1 jiangxi jiangxi 8.6K Apr 12 08:31 gpt54_egra_calibration_egra_metrics.json
-rw-rw-r-- 1 jiangxi jiangxi 1.6M Apr 12 13:39 gpt54_egra_test_all_v2.json
-rw-rw-r-- 1 jiangxi jiangxi 9.2K Apr 12 13:40 gpt54_egra_test_all_v2_metrics.json
-rw-rw-r-- 1 jiangxi jiangxi 192K Apr 12 07:20 gpt54_v0_direct_calibration_egra.json
-rw-rw-r-- 1 jiangxi jiangxi 8.6K Apr 12 07:20 gpt54_v0_direct_calibration_egra_metrics.json
-rw-rw-r-- 1 jiangxi jiangxi 1.1M Apr 12 02:34 gpt54_v0_direct_test_all.json
-rw-rw-r-- 1 jiangxi jiangxi 9.2K Apr 12 02:35 gpt54_v0_direct_test_all_metrics.json
-rw-rw-r-- 1 jiangxi jiangxi 1.1M Apr 12 09:27 gpt54_v0_direct_test_all_v2.json
-rw-rw-r-- 1 jiangxi jiangxi 9.2K Apr 12 10:02 gpt54_v0_direct_test_all_v2_metrics.json
-rw-rw-r-- 1 jiangxi jiangxi 395K Apr 12 07:33 gpt54_v1_normal_first_calibration_egra.json
-rw-rw-r-- 1 jiangxi jiangxi 8.7K Apr 12 07:34 gpt54_v1_normal_first_calibration_egra_metrics.json
-rw-rw-r-- 1 jiangxi jiangxi 2.3M Apr 12 03:14 gpt54_v1_normal_first_test_all.json
-rw-rw-r-- 1 jiangxi jiangxi 9.2K Apr 12 03:34 gpt54_v1_normal_first_test_all_metrics.json
-rw-rw-r-- 1 jiangxi jiangxi 707K Apr 12 07:58 gpt54_v2_self_refine_calibration_egra.json
-rw-rw-r-- 1 jiangxi jiangxi 8.7K Apr 12 07:59 gpt54_v2_self_refine_calibration_egra_metrics.json
-rw-rw-r-- 1 jiangxi jiangxi 525K Apr 12 08:18 gpt54_v3_debate_1r_calibration_egra.json
-rw-rw-r-- 1 jiangxi jiangxi 8.6K Apr 12 08:18 gpt54_v3_debate_1r_calibration_egra_metrics.json
-rw-rw-r-- 1 jiangxi jiangxi 1.5M Apr 12 03:38 gpt54_v3_debate_1r_test_all.json
-rw-rw-r-- 1 jiangxi jiangxi 3.1M Apr 12 13:35 gpt54_v3_debate_1r_test_all_v2.json
-rw-rw-r-- 1 jiangxi jiangxi 9.2K Apr 12 13:39 gpt54_v3_debate_1r_test_all_v2_metrics.json
-rw-rw-r-- 1 jiangxi jiangxi 995K Apr 12 09:08 gpt54_v3_egra_calibration_egra.json
-rw-rw-r-- 1 jiangxi jiangxi 8.7K Apr 12 09:09 gpt54_v3_egra_calibration_egra_metrics.json
-rw-rw-r-- 1 jiangxi jiangxi 940K Apr 12 08:42 gpt54_v3_grounded_calibration_egra.json
-rw-rw-r-- 1 jiangxi jiangxi 8.7K Apr 12 08:42 gpt54_v3_grounded_calibration_egra_metrics.json
-rw-rw-r-- 1 jiangxi jiangxi 3.0M Apr 12 14:29 gpt54_v3_grounded_test_all_v2.json
-rw-rw-r-- 1 jiangxi jiangxi 5.4K Apr 12 14:29 gpt54_v3_grounded_test_all_v2_metrics.json
-rw-rw-r-- 1 jiangxi jiangxi  81K Mar 31 15:37 gpt_v0_direct_calib_d4d5d6d7d8.json
-rw-rw-r-- 1 jiangxi jiangxi 4.4K Mar 31 15:51 gpt_v0_direct_calib_d4d5d6d7d8_metrics.json
-rw-rw-r-- 1 jiangxi jiangxi  33K Mar 31 15:30 gpt_v0_direct_calibration.json
-rw-rw-r-- 1 jiangxi jiangxi 2.5K Mar 31 15:35 gpt_v0_direct_calibration_metrics.json
-rw-rw-r-- 1 jiangxi jiangxi 650K Mar 31 16:07 gpt_v0_direct_test_all.json
-rw-rw-r-- 1 jiangxi jiangxi 5.9K Mar 31 18:48 gpt_v0_direct_test_all_metrics.json
-rw-rw-r-- 1 jiangxi jiangxi 235K Mar 31 15:41 gpt_v3_debate_1r_calib_d4d5d6d7d8.json
-rw-rw-r-- 1 jiangxi jiangxi 4.4K Mar 31 15:51 gpt_v3_debate_1r_calib_d4d5d6d7d8_metrics.json
-rw-rw-r-- 1 jiangxi jiangxi  88K Mar 31 15:31 gpt_v3_debate_1r_calibration.json
-rw-rw-r-- 1 jiangxi jiangxi 2.5K Mar 31 15:35 gpt_v3_debate_1r_calibration_metrics.json
-rw-rw-r-- 1 jiangxi jiangxi 1.9M Mar 31 16:39 gpt_v3_debate_1r_test_all.json
-rw-rw-r-- 1 jiangxi jiangxi 5.9K Mar 31 18:48 gpt_v3_debate_1r_test_all_metrics.json
-rw-rw-r-- 1 jiangxi jiangxi 111K Mar 31 18:12 gpt_v4_fewshot_calibration.json
-rw-rw-r-- 1 jiangxi jiangxi 5.6K Mar 31 18:14 gpt_v4_fewshot_calibration_metrics.json
-rw-rw-r-- 1 jiangxi jiangxi 540K Mar 31 18:14 gpt_v5_agent_calibration.json
-rw-rw-r-- 1 jiangxi jiangxi 5.6K Mar 31 18:14 gpt_v5_agent_calibration_metrics.json
-rw-rw-r-- 1 jiangxi jiangxi 150K Apr 12 02:37 patch_evidence_calibration.json
-rw-rw-r-- 1 jiangxi jiangxi 882K Apr 12 02:36 patch_evidence_test.json
-rw-rw-r-- 1 jiangxi jiangxi 282K Apr 12 03:36 qwen35_27b_v0_direct_test_all.json
-rw-rw-r-- 1 jiangxi jiangxi 3.0M Apr 13 23:53 qwen35_agent_v1_test.json
-rw-rw-r-- 1 jiangxi jiangxi 252K Apr 12 08:30 qwen35_egra_calibration_egra.json
-rw-rw-r-- 1 jiangxi jiangxi 8.6K Apr 12 08:30 qwen35_egra_calibration_egra_metrics.json
-rw-rw-r-- 1 jiangxi jiangxi 1.5M Apr 12 13:43 qwen35_egra_test_all_v2.json
-rw-rw-r-- 1 jiangxi jiangxi 9.2K Apr 12 13:44 qwen35_egra_test_all_v2_metrics.json
-rw-rw-r-- 1 jiangxi jiangxi 209K Apr 12 05:32 qwen35_v0_direct_calibration_egra.json
-rw-rw-r-- 1 jiangxi jiangxi 8.5K Apr 12 05:32 qwen35_v0_direct_calibration_egra_metrics.json
-rw-rw-r-- 1 jiangxi jiangxi 1.2M Apr 14 23:32 qwen35_v0_direct_generic_test.json
-rw-rw-r-- 1 jiangxi jiangxi 1.2M Apr 12 10:10 qwen35_v0_direct_test_all_v2.json
-rw-rw-r-- 1 jiangxi jiangxi 9.3K Apr 12 10:39 qwen35_v0_direct_test_all_v2_metrics.json
-rw-rw-r-- 1 jiangxi jiangxi  16K Apr 14 22:19 qwen35_v0_generic_smoke.json
-rw-rw-r-- 1 jiangxi jiangxi 354K Apr 12 05:55 qwen35_v1_normal_first_calibration_egra.json
-rw-rw-r-- 1 jiangxi jiangxi 8.6K Apr 12 05:55 qwen35_v1_normal_first_calibration_egra_metrics.json
-rw-rw-r-- 1 jiangxi jiangxi 630K Apr 12 06:39 qwen35_v2_self_refine_calibration_egra.json
-rw-rw-r-- 1 jiangxi jiangxi 8.7K Apr 12 06:40 qwen35_v2_self_refine_calibration_egra_metrics.json
-rw-rw-r-- 1 jiangxi jiangxi 513K Apr 12 07:15 qwen35_v3_debate_1r_calibration_egra.json
-rw-rw-r-- 1 jiangxi jiangxi 8.7K Apr 12 07:15 qwen35_v3_debate_1r_calibration_egra_metrics.json
-rw-rw-r-- 1 jiangxi jiangxi 3.1M Apr 12 13:41 qwen35_v3_debate_1r_test_all_v2.json
-rw-rw-r-- 1 jiangxi jiangxi 9.0K Apr 12 13:43 qwen35_v3_debate_1r_test_all_v2_metrics.json
-rw-rw-r-- 1 jiangxi jiangxi 819K Apr 12 08:48 qwen35_v3_egra_calibration_egra.json
-rw-rw-r-- 1 jiangxi jiangxi 8.7K Apr 12 08:49 qwen35_v3_egra_calibration_egra_metrics.json
-rw-rw-r-- 1 jiangxi jiangxi 795K Apr 12 08:00 qwen35_v3_grounded_calibration_egra.json
-rw-rw-r-- 1 jiangxi jiangxi 8.7K Apr 12 08:01 qwen35_v3_grounded_calibration_egra_metrics.json
-rw-rw-r-- 1 jiangxi jiangxi 166K Apr 18 06:16 router_dev_frozen_qwen3_test.json
-rw-rw-r-- 1 jiangxi jiangxi 171K Apr 18 07:35 router_fusion_v65_gpt_test.json
-rw-rw-r-- 1 jiangxi jiangxi 180K Apr 18 06:57 router_fusion_v65_qwen3_test.json
-rw-rw-r-- 1 jiangxi jiangxi 164K Apr 18 06:19 router_v65only_qwen3_test.json
-rw-rw-r-- 1 jiangxi jiangxi 2.1K Mar 31 15:28 sanity_gpt_v0.json
-rw-rw-r-- 1 jiangxi jiangxi 7.7K Mar 31 11:19 sanity_seedvl_v1.json
-rw-rw-r-- 1 jiangxi jiangxi 544K Apr 13 03:08 seedvl_agent_v1_calibration.json
-rw-rw-r-- 1 jiangxi jiangxi 3.1M Apr 13 07:15 seedvl_agent_v1_test.json
-rw-rw-r-- 1 jiangxi jiangxi 9.3K Apr 13 07:15 seedvl_agent_v1_test_metrics.json
-rw-rw-r-- 1 jiangxi jiangxi 270K Apr 12 07:01 seedvl_egra_calibration_egra.json
-rw-rw-r-- 1 jiangxi jiangxi 8.7K Apr 12 07:02 seedvl_egra_calibration_egra_metrics.json
-rw-rw-r-- 1 jiangxi jiangxi 871K Apr 12 06:57 seedvl_egra_test_all.json

exec
/bin/bash -lc "python - <<'PY'
import json, os
from pathlib import Path
for f in ['subspacead_dev.json','subspacead_test.json','classical_dinov2_patch_test_all.json','classical_dinov2_global_test_all.json','anomalyvfm_dev.json','anomalyvfm_test.json']:
 p=Path('benchmark/results')/f
 if not p.exists():
  print(f, 'MISSING')
  continue
 data=json.load(open(p))
 vals=list(data.values()) if isinstance(data,dict) else data
 print(f, 'n=', len(vals), 'keys=', sorted(vals[0].keys())[:12] if vals else [])
 print(' first item', vals[0].get('item_id') if vals else None, 'split', vals[0].get('split') if vals else None)
PY" in /hdd1/jiangxi/AD-Agent
 succeeded in 113ms:
subspacead_dev.json n= 440 keys= ['anomaly_score', 'anomaly_score_norm', 'domain', 'domain_code', 'error', 'item_id', 'label_gt', 'label_pred', 'split', 'top_patches']
 first item D1_0044 split dev
subspacead_test.json n= 1298 keys= ['anomaly_score', 'anomaly_score_norm', 'domain', 'domain_code', 'error', 'item_id', 'label_gt', 'label_pred', 'split', 'top_patches']
 first item D1_0063 split test
classical_dinov2_patch_test_all.json n= 1418 keys= ['anomaly_score', 'anomaly_type_pred', 'category', 'cost_tokens', 'domain', 'domain_code', 'error', 'item_id', 'label_gt', 'label_pred', 'latency_sec', 'raw_output']
 first item D1_0063 split test
classical_dinov2_global_test_all.json n= 1418 keys= ['anomaly_score', 'anomaly_type_pred', 'category', 'cost_tokens', 'domain', 'domain_code', 'error', 'item_id', 'label_gt', 'label_pred', 'latency_sec', 'raw_output']
 first item D1_0063 split test
anomalyvfm_dev.json MISSING
anomalyvfm_test.json n= 1298 keys= ['anomaly_score', 'domain', 'domain_code', 'error', 'item_id', 'label_gt', 'label_pred', 'split', 'top_patches']
 first item D1_0063 split test

exec
/bin/bash -lc "python - <<'PY'
import json, collections
man=json.load(open('benchmark/manifests/full_manifest.json'))
print(collections.Counter(x.get('split') for x in man))
print(collections.Counter(x.get('domain_code') for x in man if x.get('split')=='dev'))
for f in ['classical_dinov2_patch_test_all.json','classical_dinov2_global_test_all.json']:
 data=json.load(open('benchmark/results/'+f))
 vals=list(data.values()) if isinstance(data,dict) else data
 print(f, collections.Counter(x.get('split') for x in vals))
PY" in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
Counter({'test': 1418, 'dev': 480, 'calibration': 240})
Counter({'D1': 40, 'D2': 40, 'D4': 40, 'D5': 40, 'D6': 40, 'D7': 40, 'D8': 40, 'D9': 40, 'D10': 40, 'D5b': 40, 'D5c': 40, 'D5d': 40})
classical_dinov2_patch_test_all.json Counter({'test': 1418})
classical_dinov2_global_test_all.json Counter({'test': 1418})

codex
**CRITICAL Issues**

1. [benchmark/scripts/agent_v6.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_v6.py:27) still imports v6 prompt/tools, and there is no `benchmark/scripts/agent_v7.py`.

`agent_prompt_v7.py` and `dispatch_tool_keep_only()` are not wired into a production v7 runner. `single_tool_agent.py` patches `agent_v6` for audit only, but Phase C can easily run plain v6 unless a v7 entrypoint exists.

Exact fix: create `agent_v7.py` that imports `SYSTEM_PROMPT`, `budget_warning_prompt`, `forced_final_prompt` from `agent_prompt_v7`, and `dispatch_tool_keep_only` from `agent_tools_v7`; or refactor `ReActAgent` to accept prompt/dispatch as constructor dependencies. Add a startup assertion that `TOOL_HINTS` is not the fallback string and that the allowed tool set matches the cards.

Why it matters: without this, the v7 framework may pass audits and then deploy/evaluate v6 behavior.

2. [benchmark/scripts/agent_tools_v7.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_tools_v7.py:165) and [benchmark/scripts/agent_tools_v7.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_tools_v7.py:520): two audited “single tools” are not standalone.

`tool_hotspot_cropper` requires prior `tool_expert_score` patches and otherwise returns `"no patches available"`; `tool_component_counter` needs the same patch context and otherwise returns `not_applicable`. But `single_tool_agent.py` exposes exactly one tool, so these audits mostly test missing-prerequisite behavior, not the tool niche.

Exact fix: either make these tools composite for audit, e.g. internally load `subspacead` patches from `item_id/split`, or add an audit mode that seeds `ctx["_expert_patches"]` before running these tools. Alternatively classify them as second-stage tools and audit tool chains, not single tools.

Why it matters: any KEEP/DROP conclusion for these tools is invalid as evidence about their intended use.

3. [benchmark/scripts/build_tool_card.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/build_tool_card.py:70): the reported delta and the CI are for different estimands.

`auroc_tool`, `auroc_direct`, and `delta` use macro AUROC when available, but the bootstrap CI uses pooled AUROC over resampled items. So a card can claim “macro Δ has CI lower > 0” when the CI is actually for pooled Δ.

Exact fix: bootstrap the same metric you report. Resample paired items within domain, recompute per-domain AUROC, then average domains. If a slice falls back to pooled AUROC, label it explicitly as pooled and use pooled for both point estimate and CI.

Why it matters: the headline validity criterion, “bootstrap 95% CI lower bound > 0,” is currently mislabeled and can select false niches.

4. [benchmark/scripts/build_tool_card.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/build_tool_card.py:132): most slices are not actionable pre-call niches.

Domain slices produce labels like `domain=D5c`, but the v7 prompt explicitly says the agent has no domain information. `direct_margin` requires knowing a separate Direct model score. `tool_used=True`, `tool_used=False`, and `n_turns>=2` are post-treatment behavioral slices, not input conditions. `subspacead_rank` is only known after calling `tool_expert_score`.

Exact fix: split slices into `actionable_pre_call`, `actionable_after_tool_X`, and `diagnostic_only`. Only inject pre-call or correctly staged hints. Domain-code niches must be converted to visual/domain descriptors or withheld from the prompt.

Why it matters: the framework may “discover” niches that cannot be used by `agent_v7` without oracle information or circular logic.

5. [benchmark/scripts/agent_tools_v7.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_tools_v7.py:711): KEEP-gate fallback re-enables all tools when all cards DROP.

`_load_keep_tools()` returns all registered tools if `keep` is empty. That is acceptable before cards exist, but catastrophic after Phase B produces all DROP cards.

Exact fix: distinguish “no cards directory/files yet” from “cards exist but zero KEEP.” If cards exist and zero KEEP, return an empty set. Also write a sentinel like `refine-logs/tool_cards/_COMPLETE` after audit/card generation.

Why it matters: the exact failure mode v7 is supposed to prevent gets restored silently.

**MAJOR Issues**

1. [benchmark/scripts/single_tool_agent.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/single_tool_agent.py:95): wrong-tool calls do not crash, but they poison the audit silently.

`make_restricted_dispatch()` returns an error dict. `agent_v6.run()` feeds that observation back and continues, so the loop is graceful. But the output does not record observation errors; it only records top-level agent errors. `build_tool_card.py` counts `r["error"]`, not tool observation errors, so a run with many rejected/wrong tool calls can report `Errors: 0`.

Exact fix: include `history` or at least `tool_obs_errors`, `wrong_tool_calls`, and `valid_allowed_tool_calls` in `single_tool_agent.py` output. Exclude or separately analyze samples where the first call was the wrong tool.

2. [benchmark/scripts/agent_v6.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_v6.py:78) and [benchmark/scripts/agent_v6.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_v6.py:189): monkeypatch safety is mostly okay.

`SYSTEM_PROMPT` and `dispatch_tool` are module globals, so the patch in `single_tool_agent.py` is picked up. Per-item `ctx`, `messages`, and `history` are local. The main shared risks are the VLM client thread-safety and tool-level caches. `_RETRIEVAL_CACHE` in `agent_tools_v7.py` is not locked, so `tool_reference_retriever` can race model loading/CUDA use under `max_workers=9`.

Exact fix: instantiate per-worker clients or confirm the client is thread-safe; protect retrieval model loading with a lock or force `max_workers=1` for retrieval audit.

3. [benchmark/scripts/agent_v6.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_v6.py:236): interpretation usually reaches the VLM, but it is fragile.

`_obs_to_text()` dumps all non-image fields, so `interpretation` is included. However `_wrap_interpretation()` appends it last, and `_obs_to_text()` truncates the JSON to 1500 chars. For outputs with long `results`, paths, or text answers, the disconfirm clause can be truncated.

Exact fix: make `_obs_to_text()` always emit `interpretation` first and reserve space for it before other fields.

4. [benchmark/scripts/agent_tools_v7.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_tools_v7.py:81): expert split handling is only correct for `subspacead`.

`subspacead` maps dev to `subspacead_dev.json`, so the default path is not test-contaminated. But `anomalyvfm_dev.json` is missing locally, and `patchknn` / `dinov2_global` map dev to `*_test_all.json`, whose records are test-only. On dev, these experts will mostly return missing-score errors, not valid dev expert signals.

Exact fix: either restrict `tool_expert_score` to `subspacead` during dev audit or generate true dev caches for every advertised expert. Do not advertise unavailable experts in the prompt.

5. [benchmark/scripts/build_tool_card.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/build_tool_card.py:196): multiple testing is naive.

The script tests roughly 21 slices per tool: 12 domains plus margin/tool-used/rank/turn slices. With CI lower > 0 from a two-sided 95% bootstrap, the positive-side null false-positive rate is about 2.5% per valid slice. Expected false positive niches are about `21 * 0.025 = 0.53` per tool, or `13 * 21 * 0.025 = 6.8` across 13 tools. Probability of at least one false positive across all tools is effectively near certain under independence; correlations reduce or reshape this, but do not solve snooping.

Exact fix: use held-out dev2 validation for selected niches, or apply FDR/Holm correction over all tested slices, or pre-register a small set of actionable slices before looking.

6. [benchmark/scripts/tool_audit_runner.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/tool_audit_runner.py:38): `--skip_existing` is always true.

`action="store_true", default=True` means existing audit files are skipped and there is no CLI way to force recomputation. This is dangerous after changing tool code or prompts.

Exact fix: replace with `--skip_existing/--overwrite` or default it to false.

7. [benchmark/scripts/build_tool_card.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/build_tool_card.py:255): the generated “Agent hint” is too thin.

It injects only the best positive slice and worst anti-slice. If the best slice is non-actionable, circular, or a multiple-testing artifact, the prompt inherits that directly.

Exact fix: emit structured JSON alongside Markdown, with slice type, preconditions, CI metric type, correction status, and whether the slice is prompt-actionable.

8. Selection on dev must be stated honestly.

A single final test run is fine only if all prompt/tool-card decisions are frozen after dev. But niche selection itself is hyperparameter/model selection on dev. Test reflects the selected v7 system, not independent confirmation of each discovered niche.

Exact fix: write the claim as “dev-selected tool policy evaluated once on test,” not “statistically validated niches generalize.”

**MINOR Issues**

1. [benchmark/scripts/diagnose_tools.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/diagnose_tools.py:53): diagnosis files are inert placeholders.

Search shows only `diagnose_tools.py` writes them; no downstream code consumes `refine-logs/tool_diagnosis/*.md`. Harmless operationally, but misleading as evidence of manual failure-mode analysis.

2. [benchmark/scripts/build_tool_card.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/build_tool_card.py:17): unused `os` import.

3. Tool docs say “Every tool returns interpretation,” but many error paths return only `{"error": ...}`. Either soften the prompt wording or wrap errors with a standard interpretation like “tool failed; treat as no evidence.”

**PUBLISHABILITY Verdict**

Bluntly: as written, this is not yet a real research contribution. It is a dev-set tool-selection and prompt-tuning framework with weak statistical controls, non-actionable discovered slices, and missing deployment wiring. If Phase B+C succeed after fixing the above, the contribution could become publishable as an empirical study of tool-use calibration for VLM anomaly agents. The current claim, “statistically valid and actionable per-tool niches,” is overstated.

The strongest possible paper angle is not “we discovered niches,” but “most ReAct tools harm anomaly detection unless tool outputs are calibrated and tool availability is gated by pre-registered, validated conditions.” That requires clean selection accounting and a final frozen test.

**SUGGESTED NEXT EXPERIMENTS**

1. Run a two-stage dev protocol: use dev-A to discover niches, dev-B to validate them with corrected macro-AUROC CIs, then freeze and run test once.

2. Add a “valid tool call” audit report: call rate, wrong-tool rate, observation-error rate, malformed JSON rate, and first-call-vs-later-call performance for every tool.

3. Re-audit dependent tools as chains: `expert_score -> hotspot_cropper`, `expert_score -> component_counter`, and compare against `expert_score` alone.

4. Replace non-actionable slice hints with observable triggers: self-estimated uncertainty, visible alignment quality, local defect hypothesis, texture periodicity, and reference variation consistency.

5. Run an ablation matrix on test only after freezing: Direct, v7 prompt with no tools, v7 tools without hints, v7 hints without KEEP gate, and full v7. This separates prompt effects from actual tool utility.
tokens used
190,207
**CRITICAL Issues**

1. [benchmark/scripts/agent_v6.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_v6.py:27) still imports v6 prompt/tools, and there is no `benchmark/scripts/agent_v7.py`.

`agent_prompt_v7.py` and `dispatch_tool_keep_only()` are not wired into a production v7 runner. `single_tool_agent.py` patches `agent_v6` for audit only, but Phase C can easily run plain v6 unless a v7 entrypoint exists.

Exact fix: create `agent_v7.py` that imports `SYSTEM_PROMPT`, `budget_warning_prompt`, `forced_final_prompt` from `agent_prompt_v7`, and `dispatch_tool_keep_only` from `agent_tools_v7`; or refactor `ReActAgent` to accept prompt/dispatch as constructor dependencies. Add a startup assertion that `TOOL_HINTS` is not the fallback string and that the allowed tool set matches the cards.

Why it matters: without this, the v7 framework may pass audits and then deploy/evaluate v6 behavior.

2. [benchmark/scripts/agent_tools_v7.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_tools_v7.py:165) and [benchmark/scripts/agent_tools_v7.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_tools_v7.py:520): two audited “single tools” are not standalone.

`tool_hotspot_cropper` requires prior `tool_expert_score` patches and otherwise returns `"no patches available"`; `tool_component_counter` needs the same patch context and otherwise returns `not_applicable`. But `single_tool_agent.py` exposes exactly one tool, so these audits mostly test missing-prerequisite behavior, not the tool niche.

Exact fix: either make these tools composite for audit, e.g. internally load `subspacead` patches from `item_id/split`, or add an audit mode that seeds `ctx["_expert_patches"]` before running these tools. Alternatively classify them as second-stage tools and audit tool chains, not single tools.

Why it matters: any KEEP/DROP conclusion for these tools is invalid as evidence about their intended use.

3. [benchmark/scripts/build_tool_card.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/build_tool_card.py:70): the reported delta and the CI are for different estimands.

`auroc_tool`, `auroc_direct`, and `delta` use macro AUROC when available, but the bootstrap CI uses pooled AUROC over resampled items. So a card can claim “macro Δ has CI lower > 0” when the CI is actually for pooled Δ.

Exact fix: bootstrap the same metric you report. Resample paired items within domain, recompute per-domain AUROC, then average domains. If a slice falls back to pooled AUROC, label it explicitly as pooled and use pooled for both point estimate and CI.

Why it matters: the headline validity criterion, “bootstrap 95% CI lower bound > 0,” is currently mislabeled and can select false niches.

4. [benchmark/scripts/build_tool_card.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/build_tool_card.py:132): most slices are not actionable pre-call niches.

Domain slices produce labels like `domain=D5c`, but the v7 prompt explicitly says the agent has no domain information. `direct_margin` requires knowing a separate Direct model score. `tool_used=True`, `tool_used=False`, and `n_turns>=2` are post-treatment behavioral slices, not input conditions. `subspacead_rank` is only known after calling `tool_expert_score`.

Exact fix: split slices into `actionable_pre_call`, `actionable_after_tool_X`, and `diagnostic_only`. Only inject pre-call or correctly staged hints. Domain-code niches must be converted to visual/domain descriptors or withheld from the prompt.

Why it matters: the framework may “discover” niches that cannot be used by `agent_v7` without oracle information or circular logic.

5. [benchmark/scripts/agent_tools_v7.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_tools_v7.py:711): KEEP-gate fallback re-enables all tools when all cards DROP.

`_load_keep_tools()` returns all registered tools if `keep` is empty. That is acceptable before cards exist, but catastrophic after Phase B produces all DROP cards.

Exact fix: distinguish “no cards directory/files yet” from “cards exist but zero KEEP.” If cards exist and zero KEEP, return an empty set. Also write a sentinel like `refine-logs/tool_cards/_COMPLETE` after audit/card generation.

Why it matters: the exact failure mode v7 is supposed to prevent gets restored silently.

**MAJOR Issues**

1. [benchmark/scripts/single_tool_agent.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/single_tool_agent.py:95): wrong-tool calls do not crash, but they poison the audit silently.

`make_restricted_dispatch()` returns an error dict. `agent_v6.run()` feeds that observation back and continues, so the loop is graceful. But the output does not record observation errors; it only records top-level agent errors. `build_tool_card.py` counts `r["error"]`, not tool observation errors, so a run with many rejected/wrong tool calls can report `Errors: 0`.

Exact fix: include `history` or at least `tool_obs_errors`, `wrong_tool_calls`, and `valid_allowed_tool_calls` in `single_tool_agent.py` output. Exclude or separately analyze samples where the first call was the wrong tool.

2. [benchmark/scripts/agent_v6.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_v6.py:78) and [benchmark/scripts/agent_v6.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_v6.py:189): monkeypatch safety is mostly okay.

`SYSTEM_PROMPT` and `dispatch_tool` are module globals, so the patch in `single_tool_agent.py` is picked up. Per-item `ctx`, `messages`, and `history` are local. The main shared risks are the VLM client thread-safety and tool-level caches. `_RETRIEVAL_CACHE` in `agent_tools_v7.py` is not locked, so `tool_reference_retriever` can race model loading/CUDA use under `max_workers=9`.

Exact fix: instantiate per-worker clients or confirm the client is thread-safe; protect retrieval model loading with a lock or force `max_workers=1` for retrieval audit.

3. [benchmark/scripts/agent_v6.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_v6.py:236): interpretation usually reaches the VLM, but it is fragile.

`_obs_to_text()` dumps all non-image fields, so `interpretation` is included. However `_wrap_interpretation()` appends it last, and `_obs_to_text()` truncates the JSON to 1500 chars. For outputs with long `results`, paths, or text answers, the disconfirm clause can be truncated.

Exact fix: make `_obs_to_text()` always emit `interpretation` first and reserve space for it before other fields.

4. [benchmark/scripts/agent_tools_v7.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_tools_v7.py:81): expert split handling is only correct for `subspacead`.

`subspacead` maps dev to `subspacead_dev.json`, so the default path is not test-contaminated. But `anomalyvfm_dev.json` is missing locally, and `patchknn` / `dinov2_global` map dev to `*_test_all.json`, whose records are test-only. On dev, these experts will mostly return missing-score errors, not valid dev expert signals.

Exact fix: either restrict `tool_expert_score` to `subspacead` during dev audit or generate true dev caches for every advertised expert. Do not advertise unavailable experts in the prompt.

5. [benchmark/scripts/build_tool_card.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/build_tool_card.py:196): multiple testing is naive.

The script tests roughly 21 slices per tool: 12 domains plus margin/tool-used/rank/turn slices. With CI lower > 0 from a two-sided 95% bootstrap, the positive-side null false-positive rate is about 2.5% per valid slice. Expected false positive niches are about `21 * 0.025 = 0.53` per tool, or `13 * 21 * 0.025 = 6.8` across 13 tools. Probability of at least one false positive across all tools is effectively near certain under independence; correlations reduce or reshape this, but do not solve snooping.

Exact fix: use held-out dev2 validation for selected niches, or apply FDR/Holm correction over all tested slices, or pre-register a small set of actionable slices before looking.

6. [benchmark/scripts/tool_audit_runner.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/tool_audit_runner.py:38): `--skip_existing` is always true.

`action="store_true", default=True` means existing audit files are skipped and there is no CLI way to force recomputation. This is dangerous after changing tool code or prompts.

Exact fix: replace with `--skip_existing/--overwrite` or default it to false.

7. [benchmark/scripts/build_tool_card.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/build_tool_card.py:255): the generated “Agent hint” is too thin.

It injects only the best positive slice and worst anti-slice. If the best slice is non-actionable, circular, or a multiple-testing artifact, the prompt inherits that directly.

Exact fix: emit structured JSON alongside Markdown, with slice type, preconditions, CI metric type, correction status, and whether the slice is prompt-actionable.

8. Selection on dev must be stated honestly.

A single final test run is fine only if all prompt/tool-card decisions are frozen after dev. But niche selection itself is hyperparameter/model selection on dev. Test reflects the selected v7 system, not independent confirmation of each discovered niche.

Exact fix: write the claim as “dev-selected tool policy evaluated once on test,” not “statistically validated niches generalize.”

**MINOR Issues**

1. [benchmark/scripts/diagnose_tools.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/diagnose_tools.py:53): diagnosis files are inert placeholders.

Search shows only `diagnose_tools.py` writes them; no downstream code consumes `refine-logs/tool_diagnosis/*.md`. Harmless operationally, but misleading as evidence of manual failure-mode analysis.

2. [benchmark/scripts/build_tool_card.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/build_tool_card.py:17): unused `os` import.

3. Tool docs say “Every tool returns interpretation,” but many error paths return only `{"error": ...}`. Either soften the prompt wording or wrap errors with a standard interpretation like “tool failed; treat as no evidence.”

**PUBLISHABILITY Verdict**

Bluntly: as written, this is not yet a real research contribution. It is a dev-set tool-selection and prompt-tuning framework with weak statistical controls, non-actionable discovered slices, and missing deployment wiring. If Phase B+C succeed after fixing the above, the contribution could become publishable as an empirical study of tool-use calibration for VLM anomaly agents. The current claim, “statistically valid and actionable per-tool niches,” is overstated.

The strongest possible paper angle is not “we discovered niches,” but “most ReAct tools harm anomaly detection unless tool outputs are calibrated and tool availability is gated by pre-registered, validated conditions.” That requires clean selection accounting and a final frozen test.

**SUGGESTED NEXT EXPERIMENTS**

1. Run a two-stage dev protocol: use dev-A to discover niches, dev-B to validate them with corrected macro-AUROC CIs, then freeze and run test once.

2. Add a “valid tool call” audit report: call rate, wrong-tool rate, observation-error rate, malformed JSON rate, and first-call-vs-later-call performance for every tool.

3. Re-audit dependent tools as chains: `expert_score -> hotspot_cropper`, `expert_score -> component_counter`, and compare against `expert_score` alone.

4. Replace non-actionable slice hints with observable triggers: self-estimated uncertainty, visible alignment quality, local defect hypothesis, texture periodicity, and reference variation consistency.

5. Run an ablation matrix on test only after freezing: Direct, v7 prompt with no tools, v7 tools without hints, v7 hints without KEEP gate, and full v7. This separates prompt effects from actual tool utility.
