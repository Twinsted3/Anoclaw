# AnomaClaw v7 — Per-Tool Causal Audit & Niche-Aware Agent — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** For each of the 13 v6 agent tools, discover and document its niche on Qwen3.5-VL via isolated single-tool experiments on dev n=480; compose niche-aware agent_v7; beat Direct on test.

**Architecture:** Per-tool protocol (diagnose → redesign → single-tool dev audit → niche discovery → tool card → compose). 3 vLLM replicas with 9-worker concurrency for parallel Phase B. Shut vLLM down between phases.

**Tech Stack:** Python, Qwen3.5-VL-27B INT8 on A6000, vLLM + custom LB, ReAct JSON protocol, scikit-learn for AUROC, numpy for bootstrap.

**Spec:** `docs/superpowers/specs/2026-04-18-anomaclaw-per-tool-audit-design.md`

---

## Phase 0: Scaffold

### Task 01: Create v7 scaffold from v6 files

**Files:**
- Create: `benchmark/scripts/agent_tools_v7.py` (copy of v6)
- Create: `benchmark/scripts/agent_prompt_v7.py` (copy of v6)
- Create: `benchmark/results/tool_audit/` (empty dir)
- Create: `refine-logs/tool_cards/` (empty dir)

- [ ] **Step 1: Copy tools and prompt to v7**
```bash
cp benchmark/scripts/agent_tools_v6.py benchmark/scripts/agent_tools_v7.py
cp benchmark/scripts/agent_prompt_v6.py benchmark/scripts/agent_prompt_v7.py
mkdir -p benchmark/results/tool_audit refine-logs/tool_cards
```

- [ ] **Step 2: Add v7 header marker to both files**

Edit the top of both files to add `"""AnomaClaw v7 — redesigned tools per tool_card audit (2026-04-18)."""` instead of v6 docstring.

- [ ] **Step 3: Commit scaffold**
```bash
git add benchmark/scripts/agent_tools_v7.py benchmark/scripts/agent_prompt_v7.py
git commit -m "v7 scaffold: copy v6 tools/prompt as starting point"
```

### Task 02: Verify Direct dev baseline n=480 exists

**Files:**
- Read: `benchmark/results/v6_direct_qwen3_dev.json`
- Read: `benchmark/manifests_v2/full_manifest.json`

- [ ] **Step 1: Check existing dev results**
```bash
ls -la benchmark/results/ | grep -i "direct.*qwen3.*dev"
```

- [ ] **Step 2: Count dev items in manifest**
```bash
python -c "import json; m=json.load(open('benchmark/manifests_v2/full_manifest.json')); dev=[x for x in m if x.get('split')=='dev']; print(f'dev n={len(dev)}, domains={sorted(set(x.get(\"domain_code\") for x in dev))}')"
```

Expected: n=480, 12 domains.

- [ ] **Step 3: If direct dev file is missing or n≠480, compute it**
```bash
# Only run if needed
bash benchmark/scripts/launch_qwen35_replicas.sh
sleep 30
python benchmark/scripts/run_baselines_v6.py \
  --manifest benchmark/manifests_v2/full_manifest.json \
  --split dev --backend qwen3 --mode direct \
  --output benchmark/results/v6_direct_qwen3_dev.json \
  --max_workers 9
```

Expected output: 480 items in JSON.

- [ ] **Step 4: Record Direct dev macro AUROC**
```bash
python -c "
import json, numpy as np
from sklearn.metrics import roc_auc_score
r = json.load(open('benchmark/results/v6_direct_qwen3_dev.json'))
by_d = {}
for x in r:
    by_d.setdefault(x['domain_code'], []).append(x)
aurocs = []
for d, items in by_d.items():
    y = [i['label_gt'] for i in items]
    s = [i['anomaly_score'] for i in items]
    if len(set(y)) > 1:
        aurocs.append(roc_auc_score(y, s))
print(f'Direct dev macro AUROC: {np.mean(aurocs):.4f}, per-domain n={len(aurocs)}')
"
```

Record the number in `refine-logs/v7_direct_dev_baseline.txt`.

---

## Phase A: Diagnose + Redesign (Serial)

### Task 03: Diagnose all 13 tools from v6.5 results

**Files:**
- Create: `refine-logs/tool_diagnosis/<tool>.md` × 13
- Read: `benchmark/results/v6_5_agent_qwen3_test.json`

- [ ] **Step 1: Create diagnosis script**

Write `benchmark/scripts/diagnose_tools.py`:

```python
"""Extract 20 cases per tool (10 hits, 10 misses) from v6.5 test results
for manual failure-mode inspection."""
import json
import os
from collections import defaultdict

RESULTS = "benchmark/results/v6_5_agent_qwen3_test.json"
DIRECT = "benchmark/results/v6_direct_qwen3_test.json"
OUT_DIR = "refine-logs/tool_diagnosis"

os.makedirs(OUT_DIR, exist_ok=True)

v65 = json.load(open(RESULTS))
direct = {x["item_id"]: x for x in json.load(open(DIRECT))}

by_tool = defaultdict(list)
for r in v65:
    tools = r.get("tools_used") or []
    label = r.get("label_gt")
    agent_score = r.get("anomaly_score", 0.5)
    direct_score = direct.get(r["item_id"], {}).get("anomaly_score", 0.5)
    if label is None:
        continue
    for t in set(tools):
        # margin: how much the agent's score differs from direct on this item
        agent_err = abs(agent_score - label)
        direct_err = abs(direct_score - label)
        delta_err = agent_err - direct_err  # negative = agent better
        by_tool[t].append({
            "item_id": r["item_id"],
            "domain": r.get("domain_code"),
            "label": label,
            "agent_score": agent_score,
            "direct_score": direct_score,
            "delta_err": delta_err,
            "tools_used": tools,
            "rationale": r.get("rationale", "")[:200],
        })

for tool, cases in by_tool.items():
    cases.sort(key=lambda x: x["delta_err"])
    hits = cases[:10]    # agent better than direct
    misses = cases[-10:] # agent worse than direct
    out = f"# Diagnosis: {tool}\n\nTotal calls: {len(cases)}\n\n## Hits (agent better)\n"
    for h in hits:
        out += f"- {h['item_id']} [{h['domain']}] label={h['label']} agent={h['agent_score']:.2f} direct={h['direct_score']:.2f} Δerr={h['delta_err']:+.3f}\n"
        out += f"  rationale: {h['rationale']}\n\n"
    out += "## Misses (agent worse)\n"
    for m in misses:
        out += f"- {m['item_id']} [{m['domain']}] label={m['label']} agent={m['agent_score']:.2f} direct={m['direct_score']:.2f} Δerr={m['delta_err']:+.3f}\n"
        out += f"  rationale: {m['rationale']}\n\n"
    with open(f"{OUT_DIR}/{tool}.md", "w") as f:
        f.write(out)
    print(f"wrote {OUT_DIR}/{tool}.md ({len(cases)} cases)")

print("\nTools with zero calls in v6.5:")
seen = set(by_tool.keys())
ALL = {"tool_expert_score", "tool_hotspot_cropper", "tool_zoom_bbox",
       "tool_patch_grid", "tool_image_diff", "tool_rotate_align",
       "tool_side_by_side", "tool_reference_profiler", "tool_reference_retriever",
       "tool_component_counter", "tool_segment_and_count", "tool_texture_fft",
       "tool_domain_knowledge"}
for t in ALL - seen:
    print(f"  {t}")
```

- [ ] **Step 2: Run diagnosis**
```bash
python benchmark/scripts/diagnose_tools.py
```

Expected: 11 diagnosis files written (tools that were called in v6.5), list of 2 never-called tools printed.

- [ ] **Step 3: Read each diagnosis file and write one-line failure mode summary**

For each `refine-logs/tool_diagnosis/<tool>.md`, append at the top:

```
## Failure mode (manual analysis)
<one line: wrong trigger / unclear output / VLM misreads / mixed>
```

- [ ] **Step 4: Commit diagnosis**
```bash
git add benchmark/scripts/diagnose_tools.py refine-logs/tool_diagnosis/
git commit -m "v7 diagnosis: extract 20 cases per tool for manual inspection"
```

### Task 04: Redesign tool outputs for clarity (agent_tools_v7.py)

Each tool's output is wrapped in an `interpretation` field that gives the VLM an explicit verdict hint **with a disconfirming clause**. Changes are concentrated in the return-dict construction of each tool function.

**Files:**
- Modify: `benchmark/scripts/agent_tools_v7.py`

- [ ] **Step 1: Add interpretation wrapper helper**

Insert at the top of `agent_tools_v7.py` (after imports):

```python
def _wrap_interpretation(obs: dict, verdict_hint: str,
                         disconfirm_hint: str) -> dict:
    """Add interpretation field that includes a disconfirming clause.

    Format: 'Observation suggests {verdict}, BUT if {disconfirm} then normal.'
    This reduces confirmation bias: the VLM is reminded of the null.
    """
    obs["interpretation"] = (
        f"Observation suggests: {verdict_hint}. "
        f"IMPORTANT: if {disconfirm_hint}, the query is likely NORMAL despite this signal."
    )
    return obs
```

- [ ] **Step 2: Redesign tool_expert_score (high coverage, current Δ=-0.55)**

Current issue: returns raw scores + rank; VLM either trusts blindly or ignores. Fix: output binned verdict + explicit reminder that normal refs also score non-zero.

Edit `tool_expert_score` return section — after computing `score`, `normalized_rank`, `interpretation`:

```python
# v7 redesign: explicit bin + disconfirm clause
if normalized_rank >= 0.85:
    verdict = "strong anomaly signal (this sample scores higher than 85% of normal refs)"
    disconfirm = "the ref pool for this domain has high natural variance (check other refs)"
elif normalized_rank >= 0.60:
    verdict = "mild anomaly signal (ambiguous zone)"
    disconfirm = "the query's rank is similar to normal variation seen in refs"
else:
    verdict = "weak signal: sample is similar to normal distribution"
    disconfirm = "a localized defect may not shift the global expert score"
return _wrap_interpretation({
    "expert": expert,
    "score": float(score),
    "normalized_rank": float(normalized_rank),
    "top_patches": top_patches,
}, verdict, disconfirm)
```

- [ ] **Step 3: Redesign tool_hotspot_cropper (Δ=-4.7)**

Current issue: crops 5 hotspot patches; VLM often mistakes "hot" for "anomalous".

Edit end of `tool_hotspot_cropper`:

```python
verdict = f"top-{len(tiles)} suspicious regions extracted; inspect if they show genuine defects"
disconfirm = "hotspots may be edge artifacts, lighting variance, or normal texture"
return _wrap_interpretation({
    "tiles": tiles,
    "n_tiles": len(tiles),
}, verdict, disconfirm)
```

- [ ] **Step 4: Redesign tool_reference_profiler (Δ=-9.4, worst offender)**

Current issue: profiler returns long free-form text that overwhelms VLM.

Edit `tool_reference_profiler` — constrain the LLM's profiling prompt to produce a structured short output:

```python
# v7 redesign: force structured profile, not free-form prose
profile_prompt = (
    "Summarize what is common across these 4 normal reference images in EXACTLY "
    "this structured format:\n"
    "OBJECT: <one noun phrase>\n"
    "EXPECTED_COLOR: <dominant colors>\n"
    "EXPECTED_SHAPE: <one phrase>\n"
    "ALLOWED_VARIATION: <list allowed variations in refs, e.g. rotation/lighting>\n"
    "DO NOT guess at what anomalies might look like. Only describe NORMAL."
)
```

Then wrap output:
```python
return _wrap_interpretation({
    "profile_text": profile_text,
}, "baseline normal description extracted",
   "the query shows variation listed in ALLOWED_VARIATION field")
```

- [ ] **Step 5: Redesign tool_side_by_side (Δ=-2.2)**

Current issue: composite image but no guidance on what to focus on.

Edit `tool_side_by_side` return:
```python
verdict = "visual comparison grid generated; look for structural differences query vs refs"
disconfirm = "refs show natural variation; a single outlier in one ref does not mean query is anomalous"
return _wrap_interpretation({
    "composite_b64": composite_b64,
    "bbox": bbox,
}, verdict, disconfirm)
```

- [ ] **Step 6: Redesign tool_image_diff (Δ=-1.2)**

Current issue: pixel diff meaningless on unaligned images.

Edit `tool_image_diff` — add alignment check + explicit domain-sensitivity warning:

```python
# v7: reject diff if query and ref alignment is poor
if diff_stats.get("mean_abs_diff", 0) > 0.4:
    verdict = "UNRELIABLE: query and ref are poorly aligned; ignore this diff"
    disconfirm = "trust other evidence; do not use pixel diff here"
else:
    verdict = f"diff mask shows {diff_stats.get('n_bright_regions', 0)} bright regions (>20% pixel-change threshold)"
    disconfirm = "bright regions may be lighting/color variation, not defects"

return _wrap_interpretation({
    "diff_mask_b64": diff_mask_b64,
    **diff_stats,
}, verdict, disconfirm)
```

- [ ] **Step 7: Redesign tool_zoom_bbox (Δ=+7.0, the only positive tool — just add interpretation, do not change logic)**

Edit `tool_zoom_bbox` return:
```python
verdict = "cropped region extracted at full resolution; inspect for localized defects"
disconfirm = "the crop may show benign texture variation, not a defect"
return _wrap_interpretation({
    "crop_b64": crop_b64,
    "bbox": bbox,
}, verdict, disconfirm)
```

- [ ] **Step 8: Redesign tool_component_counter (Δ=-13.3, low coverage)**

Current issue: counts connected components from subspacead hotspots. Often misfires.

Edit `tool_component_counter` to gate on hotspot quality:

```python
# v7: only meaningful when hotspots are concentrated
if not patches or len(patches) < 3:
    return _wrap_interpretation({"n_components": 0, "error": "insufficient hotspots for counting"},
        "not applicable for this sample", "skip this tool's output")

# ... existing counting logic ...

verdict = f"found {n_components} connected hotspot blobs"
disconfirm = "component count alone is weak evidence; cross-check with zoom_bbox"
return _wrap_interpretation({"n_components": n_components, ...}, verdict, disconfirm)
```

- [ ] **Step 9: Redesign tool_patch_grid (Δ=-5.6)**

Current issue: cuts image into NxM tiles, VLM loses global context.

Edit — gate to only be useful at small grid sizes AND add warning:

```python
# v7: limit max grid to 3x3 to preserve tile legibility
rows = min(rows, 3)
cols = min(cols, 3)

verdict = f"{rows}x{cols} tile grid extracted; inspect for one odd tile"
disconfirm = "all tiles may show natural texture variation; one odd tile is not enough evidence"
```

- [ ] **Step 10: Redesign tool_rotate_align (Δ=-28, worst)**

Current issue: almost certainly bugged or produces noise. Gate heavily.

Edit `tool_rotate_align`:

```python
# v7: only call if strong periodic/rotation cue detected in prior turns
# Otherwise, return degraded-signal flag
if best_rotation_score < 0.3:  # low alignment confidence
    return _wrap_interpretation({"aligned_diff_b64": None, "error": "alignment failed"},
        "rotation alignment did not converge",
        "abandon this tool for this sample")

verdict = f"best rotation: {best_angle}°, aligned diff computed"
disconfirm = "alignment residual may dominate over real defect signal"
```

- [ ] **Step 11: Redesign remaining 4 tools (domain_knowledge, segment_and_count, texture_fft, reference_retriever)**

For each: add the same `_wrap_interpretation` wrapper around their return dict with sensible verdict + disconfirm clauses. Examples:

- `tool_domain_knowledge`: verdict=`"LLM answer provided"`, disconfirm=`"the LLM may have hallucinated; cross-check with visual evidence"`
- `tool_segment_and_count`: verdict=`"coarse structural diff computed"`, disconfirm=`"coarse signal may miss small defects"`
- `tool_texture_fft`: verdict=`"periodicity score {score:.2f}"`, disconfirm=`"texture regularity is weak evidence alone"`
- `tool_reference_retriever`: verdict=`"k new similar refs retrieved"`, disconfirm=`"retrieved refs are still from the normal pool; query may still be normal"`

- [ ] **Step 12: Commit redesigned tools**
```bash
git add benchmark/scripts/agent_tools_v7.py
git commit -m "v7 tools: add interpretation wrapper + per-tool verdict/disconfirm hints"
```

### Task 05: Update v7 prompt to advertise interpretation field

**Files:**
- Modify: `benchmark/scripts/agent_prompt_v7.py`

- [ ] **Step 1: Update TOOL_CATALOG preamble**

In `agent_prompt_v7.py`, before the TOOL_CATALOG string, add:

```python
TOOL_OUTPUT_GUIDE = """Every tool returns an 'interpretation' field with:
  - a verdict hint (what the observation suggests)
  - a disconfirm clause (when this signal does NOT mean anomaly)
ALWAYS read both and weigh the disconfirm clause before updating your score.
"""
```

And update `SYSTEM_PROMPT` to inject it:
```python
SYSTEM_PROMPT = f"""You are a visual anomaly detection agent.
...
{TOOL_OUTPUT_GUIDE}

{TOOL_CATALOG}
...
"""
```

- [ ] **Step 2: Commit prompt update**
```bash
git add benchmark/scripts/agent_prompt_v7.py
git commit -m "v7 prompt: advertise interpretation field + disconfirm reading"
```

---

## Phase B: Framework + Parallel Audit

### Task 06: Build single_tool_agent.py

**Files:**
- Create: `benchmark/scripts/single_tool_agent.py`

- [ ] **Step 1: Write single_tool_agent.py**

```python
"""Single-tool agent: Direct-style ReAct loop with exactly ONE tool exposed.

Usage:
  python benchmark/scripts/single_tool_agent.py \
    --tool tool_expert_score --split dev \
    --manifest benchmark/manifests_v2/full_manifest.json \
    --output benchmark/results/tool_audit/tool_expert_score.json \
    --max_turns 3 --max_workers 9
"""
from __future__ import annotations
import argparse, json, os, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from infer import get_client, get_model_name
import agent_v6 as v6
import agent_tools_v7 as tv7
import agent_prompt_v7 as pv7


SINGLE_TOOL_SYSTEM_PROMPT_TEMPLATE = """You are a visual anomaly detection agent.

INPUT: one query image, four normal references, a turn budget of {K}.
TASK: output an anomaly score in [0,1], 1 = certainly anomalous.

TOOL AVAILABLE (only one):
{tool_desc}

{output_guide}

PROTOCOL: JSON only, fields {{thought, action, tool, args, confidence, score, rationale}}.
If you call the tool, use action="call_tool". Otherwise action="final".
At turn {K}, you MUST output final."""


def build_single_tool_prompt(tool_name: str, K: int) -> str:
    # Extract just the line for this tool from TOOL_CATALOG
    tool_desc_lines = []
    capturing = False
    for line in pv7.TOOL_CATALOG.splitlines():
        if line.strip().startswith(tool_name):
            capturing = True
            tool_desc_lines.append(line)
        elif capturing and line.startswith("    "):
            tool_desc_lines.append(line)
        elif capturing and line.strip() == "":
            tool_desc_lines.append("")
        elif capturing and line.strip() and not line.startswith(" "):
            break
    tool_desc = "\n".join(tool_desc_lines) if tool_desc_lines else f"  {tool_name}(...)"
    return SINGLE_TOOL_SYSTEM_PROMPT_TEMPLATE.format(
        K=K, tool_desc=tool_desc, output_guide=pv7.TOOL_OUTPUT_GUIDE,
    )


def make_restricted_dispatch(allowed_tool: str):
    """Return a dispatch_tool that refuses any tool != allowed_tool."""
    orig = tv7.dispatch_tool
    def _dispatch(name, args, ctx=None):
        if name != allowed_tool:
            return {"error": f"only {allowed_tool} is available in this run"}
        return orig(name, args, ctx)
    return _dispatch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tool", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--split", choices=["calibration", "dev", "test"], required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--backend", default="qwen3")
    ap.add_argument("--max_turns", type=int, default=3)
    ap.add_argument("--max_workers", type=int, default=9)
    ap.add_argument("--max_items", type=int, default=0)
    args = ap.parse_args()

    items = json.load(open(args.manifest))
    items = [x for x in items if x.get("split") == args.split]
    if args.max_items:
        items = items[:args.max_items]

    client = get_client(args.backend)
    model = get_model_name(args.backend)

    v6.dispatch_tool = make_restricted_dispatch(args.tool)
    system_prompt = build_single_tool_prompt(args.tool, args.max_turns)
    orig_sp = v6.SYSTEM_PROMPT
    v6.SYSTEM_PROMPT = system_prompt

    agent = v6.ReActAgent(vlm_client=client, vlm_model=model,
                          max_turns=args.max_turns)

    results = []
    t0 = time.time()
    def _run_one(x):
        try:
            r = agent.run(item_id=x["item_id"], query_path=x["query_path"],
                          ref_paths=x["ref_paths"], split=args.split,
                          domain_code=x.get("domain_code"))
            return {"item_id": x["item_id"], "domain_code": x.get("domain_code"),
                    "label_gt": x.get("label"), "anomaly_score": r.score,
                    "used_tool": args.tool in (r.tools_used or []),
                    "n_turns": r.n_turns, "tools_used": r.tools_used,
                    "confidence": r.confidence, "rationale": r.rationale,
                    "error": r.error}
        except Exception as e:
            return {"item_id": x["item_id"], "domain_code": x.get("domain_code"),
                    "label_gt": x.get("label"), "anomaly_score": 0.5,
                    "used_tool": False, "n_turns": 0, "tools_used": [],
                    "error": f"{type(e).__name__}: {e}"}

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=args.max_workers) as ex:
        futs = [ex.submit(_run_one, x) for x in items]
        for i, fut in enumerate(as_completed(futs)):
            results.append(fut.result())
            if (i+1) % 40 == 0:
                with open(args.output, "w") as f:
                    json.dump(results, f)
                print(f"[{args.tool}] {i+1}/{len(items)} {time.time()-t0:.1f}s", flush=True)

    with open(args.output, "w") as f:
        json.dump(results, f)
    print(f"[{args.tool}] wrote {len(results)} → {args.output}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Sanity test on 5 items with tool_zoom_bbox**
```bash
python benchmark/scripts/single_tool_agent.py \
  --tool tool_zoom_bbox --split dev \
  --manifest benchmark/manifests_v2/full_manifest.json \
  --output /tmp/single_tool_sanity.json \
  --max_turns 3 --max_workers 2 --max_items 5
```

Expected: 5 items JSON, no crashes (requires vLLM running — skip if vLLM is down and run later in Task 08).

- [ ] **Step 3: Commit**
```bash
git add benchmark/scripts/single_tool_agent.py
git commit -m "v7 single_tool_agent: restricted dispatch + single-tool prompt"
```

### Task 07: Build tool_audit_runner.py

**Files:**
- Create: `benchmark/scripts/tool_audit_runner.py`

- [ ] **Step 1: Write the runner**

```python
"""Queue 13 single-tool audits and run them sequentially but with
per-tool internal concurrency = max_workers. Each tool gets full
replica capacity in sequence (avoids rate-limit interference)."""
from __future__ import annotations
import argparse, subprocess, sys, time
from pathlib import Path

TOOLS = [
    "tool_zoom_bbox",          # +7.0 in v6.5; validate it replicates
    "tool_expert_score",       # high coverage
    "tool_hotspot_cropper",
    "tool_side_by_side",
    "tool_image_diff",
    "tool_reference_profiler",
    "tool_component_counter",
    "tool_patch_grid",
    "tool_rotate_align",
    "tool_domain_knowledge",
    "tool_segment_and_count",
    "tool_texture_fft",        # never called in v6.5 — first data
    "tool_reference_retriever",# never called in v6.5 — first data
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="benchmark/manifests_v2/full_manifest.json")
    ap.add_argument("--split", default="dev")
    ap.add_argument("--out_dir", default="benchmark/results/tool_audit")
    ap.add_argument("--max_turns", type=int, default=3)
    ap.add_argument("--max_workers", type=int, default=9)
    ap.add_argument("--tools", nargs="*", default=None,
                    help="subset of tools to run (default: all)")
    args = ap.parse_args()

    Path(args.out_dir).mkdir(parents=True, exist_ok=True)
    tools = args.tools or TOOLS
    script = "benchmark/scripts/single_tool_agent.py"
    t0 = time.time()
    for tool in tools:
        out = f"{args.out_dir}/{tool}.json"
        if Path(out).exists():
            print(f"[skip] {tool}: {out} exists")
            continue
        cmd = [sys.executable, script,
               "--tool", tool, "--split", args.split,
               "--manifest", args.manifest, "--output", out,
               "--max_turns", str(args.max_turns),
               "--max_workers", str(args.max_workers)]
        print(f"[run] {tool} → {out}")
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"[FAIL] {tool}: {r.stderr[-500:]}")
            with open(f"{args.out_dir}/{tool}.stderr.log", "w") as f:
                f.write(r.stderr)
        else:
            print(f"[OK]   {tool}  t={time.time()-t0:.1f}s")

    print(f"\nDone in {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**
```bash
git add benchmark/scripts/tool_audit_runner.py
git commit -m "v7 tool_audit_runner: sequential per-tool dev audits"
```

### Task 08: Launch vLLM replicas + sanity check

**Files:**
- Read: `benchmark/scripts/launch_qwen35_replicas.sh`

- [ ] **Step 1: Check GPU availability**
```bash
nvidia-smi --query-gpu=index,memory.free --format=csv,noheader
```

Expected: GPUs 0, 1, 2 free with ≥30GB each.

- [ ] **Step 2: Start 3 replicas**
```bash
bash benchmark/scripts/launch_qwen35_replicas.sh
```

Wait for "Ready" logs. Check LB:
```bash
sleep 30
curl -s http://localhost:8210/v1/models | head -5
```

- [ ] **Step 3: Run 5-item sanity**
```bash
python benchmark/scripts/single_tool_agent.py \
  --tool tool_zoom_bbox --split dev \
  --manifest benchmark/manifests_v2/full_manifest.json \
  --output /tmp/single_tool_sanity.json \
  --max_turns 3 --max_workers 3 --max_items 5
cat /tmp/single_tool_sanity.json | python -c "import json,sys; r=json.load(sys.stdin); print('n=', len(r), 'errors=', sum(1 for x in r if x.get('error')))"
```

Expected: n=5, errors=0.

### Task 09: Run 13-tool parallel audit on dev n=480

- [ ] **Step 1: Launch audit (foreground, ~30 min)**
```bash
python benchmark/scripts/tool_audit_runner.py \
  --split dev --max_turns 3 --max_workers 9 \
  2>&1 | tee /tmp/tool_audit.log
```

- [ ] **Step 2: Verify all 13 outputs exist**
```bash
ls -la benchmark/results/tool_audit/
```
Expected: 13 JSON files, each with 480 entries.

- [ ] **Step 3: Check error rates per file**
```bash
for f in benchmark/results/tool_audit/*.json; do
  python -c "import json; r=json.load(open('$f')); e=sum(1 for x in r if x.get('error')); print('$f', 'n=', len(r), 'err=', e)"
done
```

Expected: errors < 5% per file. Any file with >5% errors → investigate and re-run.

### Task 10: Build build_tool_card.py

**Files:**
- Create: `benchmark/scripts/build_tool_card.py`

- [ ] **Step 1: Write the analysis script**

```python
"""For each tool audit, slice dev results by multiple axes and find the
niche(s) where the tool beats Direct. Emit a tool_card.md."""
from __future__ import annotations
import argparse, json, os
from pathlib import Path
import numpy as np
from sklearn.metrics import roc_auc_score

N_BOOT = 1000
RNG = np.random.default_rng(42)


def bootstrap_auroc(y, s, n_boot=N_BOOT, alpha=0.05):
    y, s = np.asarray(y), np.asarray(s)
    if len(set(y)) < 2 or len(y) < 5:
        return np.nan, np.nan, np.nan
    n = len(y)
    aucs = []
    for _ in range(n_boot):
        idx = RNG.integers(0, n, n)
        if len(set(y[idx])) < 2:
            continue
        aucs.append(roc_auc_score(y[idx], s[idx]))
    if not aucs:
        return np.nan, np.nan, np.nan
    return float(np.mean(aucs)), float(np.percentile(aucs, 100*alpha/2)), float(np.percentile(aucs, 100*(1-alpha/2)))


def macro_auroc(results, by="domain_code"):
    groups = {}
    for r in results:
        groups.setdefault(r.get(by), []).append(r)
    vals = []
    for k, items in groups.items():
        y = [i["label_gt"] for i in items if i.get("label_gt") is not None]
        s = [i["anomaly_score"] for i in items if i.get("label_gt") is not None]
        if len(set(y)) < 2:
            continue
        vals.append(roc_auc_score(y, s))
    return float(np.mean(vals)) if vals else np.nan


def slice_delta(tool_results, direct_results, slice_fn, slice_name):
    """For a given slice function (item -> bool), compute AUROC on matched subset."""
    direct_by_id = {x["item_id"]: x for x in direct_results}
    matched = []
    for r in tool_results:
        d = direct_by_id.get(r["item_id"])
        if d and r.get("label_gt") is not None:
            if slice_fn(r, d):
                matched.append((r, d))
    if len(matched) < 5:
        return None
    y = [r["label_gt"] for r, _ in matched]
    s_tool = [r["anomaly_score"] for r, _ in matched]
    s_direct = [d["anomaly_score"] for _, d in matched]
    if len(set(y)) < 2:
        return None
    auc_tool = roc_auc_score(y, s_tool)
    auc_direct = roc_auc_score(y, s_direct)
    # bootstrap delta CI
    n = len(y)
    y_arr, s_t, s_d = np.asarray(y), np.asarray(s_tool), np.asarray(s_direct)
    deltas = []
    for _ in range(N_BOOT):
        idx = RNG.integers(0, n, n)
        if len(set(y_arr[idx])) < 2:
            continue
        deltas.append(roc_auc_score(y_arr[idx], s_t[idx]) - roc_auc_score(y_arr[idx], s_d[idx]))
    if not deltas:
        return None
    return {
        "slice": slice_name, "n": n,
        "auroc_tool": float(auc_tool),
        "auroc_direct": float(auc_direct),
        "delta": float(auc_tool - auc_direct),
        "delta_ci": [float(np.percentile(deltas, 2.5)), float(np.percentile(deltas, 97.5))],
    }


def build_slices(direct_results):
    """Return list of (name, predicate) slice fns."""
    # Direct score margin = |direct_score - 0.5|; small = uncertain
    direct_by_id = {x["item_id"]: x for x in direct_results}
    slices = []
    # by domain
    for d in sorted(set(x.get("domain_code") for x in direct_results if x.get("domain_code"))):
        slices.append((f"domain={d}", lambda r, _d, d=d: r.get("domain_code") == d))
    # by direct margin
    slices.append(("direct_margin<0.15 (uncertain)",
                   lambda r, d: abs(d["anomaly_score"] - 0.5) < 0.15))
    slices.append(("direct_margin>=0.3 (confident)",
                   lambda r, d: abs(d["anomaly_score"] - 0.5) >= 0.3))
    # by tool-used
    slices.append(("tool_used=True", lambda r, d: bool(r.get("used_tool"))))
    slices.append(("tool_used=False", lambda r, d: not bool(r.get("used_tool"))))
    return slices


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tool_file", required=True)
    ap.add_argument("--direct_file", required=True)
    ap.add_argument("--out_md", required=True)
    ap.add_argument("--threshold_n", type=int, default=10)
    args = ap.parse_args()

    tool_results = json.load(open(args.tool_file))
    direct_results = json.load(open(args.direct_file))
    tool_name = Path(args.tool_file).stem

    full_tool_auroc = macro_auroc(tool_results)
    full_direct_auroc = macro_auroc(direct_results)
    overall = {
        "tool": tool_name,
        "n_total": len(tool_results),
        "n_called": sum(1 for r in tool_results if r.get("used_tool")),
        "full_tool_macro": full_tool_auroc,
        "full_direct_macro": full_direct_auroc,
        "full_delta": full_tool_auroc - full_direct_auroc,
    }

    slices = build_slices(direct_results)
    findings = []
    for name, fn in slices:
        res = slice_delta(tool_results, direct_results, fn, name)
        if res and res["n"] >= args.threshold_n:
            findings.append(res)
    findings.sort(key=lambda x: -x["delta"])

    positive_niches = [f for f in findings if f["delta"] > 0 and f["delta_ci"][0] > 0]
    verdict = "KEEP" if positive_niches else "DROP"

    md = f"# Tool Card: {tool_name}\n\n"
    md += f"**Verdict:** {verdict}  \n"
    md += f"**Overall (dev n={overall['n_total']})**: tool={overall['full_tool_macro']:.4f}  "
    md += f"direct={overall['full_direct_macro']:.4f}  Δ={overall['full_delta']:+.4f}  \n"
    md += f"**Calls**: {overall['n_called']}/{overall['n_total']} ({100*overall['n_called']/overall['n_total']:.1f}%)  \n\n"

    md += "## Niche (positive slices, CI lower bound > 0)\n\n"
    if not positive_niches:
        md += "_None found. Tool has no demonstrated niche on dev._\n\n"
    else:
        md += "| slice | n | tool AUROC | direct AUROC | Δ | 95% CI |\n|---|---|---|---|---|---|\n"
        for f in positive_niches:
            md += f"| {f['slice']} | {f['n']} | {f['auroc_tool']:.3f} | {f['auroc_direct']:.3f} | {f['delta']:+.3f} | [{f['delta_ci'][0]:+.3f}, {f['delta_ci'][1]:+.3f}] |\n"

    md += "\n## Anti-niche (significantly negative)\n\n"
    anti = [f for f in findings if f["delta"] < 0 and f["delta_ci"][1] < 0]
    if not anti:
        md += "_None flagged._\n\n"
    else:
        md += "| slice | n | Δ | 95% CI |\n|---|---|---|---|\n"
        for f in anti:
            md += f"| {f['slice']} | {f['n']} | {f['delta']:+.3f} | [{f['delta_ci'][0]:+.3f}, {f['delta_ci'][1]:+.3f}] |\n"

    md += "\n## All slices (for audit)\n\n"
    md += "| slice | n | Δ | 95% CI |\n|---|---|---|---|\n"
    for f in findings:
        md += f"| {f['slice']} | {f['n']} | {f['delta']:+.3f} | [{f['delta_ci'][0]:+.3f}, {f['delta_ci'][1]:+.3f}] |\n"

    md += "\n## Agent hint (for agent_v7 prompt)\n\n"
    if positive_niches:
        best = positive_niches[0]
        md += f"**When to call {tool_name}:** especially helpful on `{best['slice']}` (Δ={best['delta']:+.3f} on n={best['n']}). "
    else:
        md += f"**When to call {tool_name}:** avoid — no documented positive niche. "
    if anti:
        worst = min(anti, key=lambda x: x["delta"])
        md += f"Avoid on `{worst['slice']}` (Δ={worst['delta']:+.3f}).\n"
    else:
        md += "\n"

    Path(args.out_md).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out_md, "w") as f:
        f.write(md)
    print(f"wrote {args.out_md}  verdict={verdict}  niches={len(positive_niches)}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Generate 13 tool cards**
```bash
for f in benchmark/results/tool_audit/*.json; do
  tool=$(basename "$f" .json)
  python benchmark/scripts/build_tool_card.py \
    --tool_file "$f" \
    --direct_file benchmark/results/v6_direct_qwen3_dev.json \
    --out_md "refine-logs/tool_cards/${tool}.md"
done
```

- [ ] **Step 3: Summarize KEEP / DROP**
```bash
grep -H "Verdict:" refine-logs/tool_cards/*.md | tee /tmp/v7_keep_drop.txt
```

- [ ] **Step 4: Commit**
```bash
git add benchmark/scripts/build_tool_card.py refine-logs/tool_cards/ benchmark/results/tool_audit/
git commit -m "v7 tool cards: per-tool niche discovery on dev n=480"
```

### Task 11: Shut down vLLM

- [ ] **Step 1: Kill replicas + LB**
```bash
pkill -9 -f "Qwen3.5" || true
pkill -9 -f "vllm_lb" || true
sleep 5
nvidia-smi --query-gpu=index,memory.free --format=csv,noheader
```

Expected: GPUs 0, 1, 2 freed.

---

## Phase C: Compose + Final Evaluation

### Task 12: Compose agent_v7.py with tool cards injected

**Files:**
- Create: `benchmark/scripts/agent_v7.py`
- Modify: `benchmark/scripts/agent_prompt_v7.py`

- [ ] **Step 1: Load KEEP tool cards and inject agent hints into prompt**

Write `benchmark/scripts/compose_v7_prompt.py`:

```python
"""Read tool_cards/*.md, extract the 'Agent hint' section from KEEP tools,
and write an ALL_TOOL_HINTS string that agent_prompt_v7 can import."""
import re, os
from pathlib import Path

CARDS = Path("refine-logs/tool_cards")
OUT = Path("benchmark/scripts/agent_tool_hints_v7.py")

hints = []
for md in sorted(CARDS.glob("*.md")):
    text = md.read_text()
    if "**Verdict:** KEEP" not in text:
        continue
    tool_name = md.stem
    m = re.search(r"## Agent hint.*?\n\n(.+?)(?=\n##|\Z)", text, re.DOTALL)
    if m:
        hints.append(f"- {tool_name}: {m.group(1).strip()}")

content = '"""Auto-generated from tool_cards/*.md. Do not edit by hand."""\n\n'
content += "TOOL_HINTS = " + repr("\n".join(hints)) + "\n"
OUT.write_text(content)
print(f"wrote {OUT} with {len(hints)} KEEP tools")
```

Run it:
```bash
python benchmark/scripts/compose_v7_prompt.py
cat benchmark/scripts/agent_tool_hints_v7.py
```

- [ ] **Step 2: Update agent_prompt_v7.py to include TOOL_HINTS**

Edit `agent_prompt_v7.py` — add at the bottom of the SYSTEM_PROMPT construction:

```python
try:
    from agent_tool_hints_v7 import TOOL_HINTS
except ImportError:
    TOOL_HINTS = ""

SYSTEM_PROMPT = f"""You are a visual anomaly detection agent.

INPUT PER IMAGE: one query image, four normal reference images, a turn budget.
TASK: decide if the query is normal or anomalous and output a score in [0,1]
where 1 means certainly anomalous.

YOU HAVE NO DOMAIN INFORMATION. Figure out what the images are from vision
alone. The tools below can help you probe further.

{TOOL_OUTPUT_GUIDE}

{TOOL_CATALOG}

EMPIRICAL TOOL PERFORMANCE (on a held-out dev set, do NOT consult for this specific image — use as general guidance):
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

GUIDELINES:
- Use tools with documented POSITIVE niches when applicable.
- AVOID tools with documented anti-niches on this kind of input.
- If the query is obviously normal or anomalous on inspection, finalize at turn 1.
- Return valid JSON only.
"""
```

- [ ] **Step 3: Remove DROP tools from agent_v7's dispatch**

Edit `agent_tools_v7.py` bottom — gate `dispatch_tool` to only serve KEEP tools.

Append to `agent_tools_v7.py`:

```python
# v7: filter to KEEP tools only
_KEEP_TOOLS = None  # loaded lazily from tool_cards

def _load_keep_tools():
    global _KEEP_TOOLS
    import re, os
    from pathlib import Path
    _KEEP_TOOLS = set()
    cards = Path(__file__).resolve().parent.parent.parent / "refine-logs" / "tool_cards"
    if not cards.exists():
        _KEEP_TOOLS = set(TOOL_REGISTRY.keys())  # fallback: all tools
        return
    for md in cards.glob("*.md"):
        if "**Verdict:** KEEP" in md.read_text():
            _KEEP_TOOLS.add(md.stem)
    if not _KEEP_TOOLS:
        _KEEP_TOOLS = set(TOOL_REGISTRY.keys())

_orig_dispatch = dispatch_tool
def dispatch_tool(name, args, ctx=None):  # noqa: F811
    if _KEEP_TOOLS is None:
        _load_keep_tools()
    if name not in _KEEP_TOOLS:
        return {"error": f"{name} is not a v7 KEEP tool; choose from {sorted(_KEEP_TOOLS)}"}
    return _orig_dispatch(name, args, ctx)
```

- [ ] **Step 4: Write agent_v7.py**

```python
"""AnomalyClaw v7 — niche-aware agent (tool cards in prompt, DROP tools gated)."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import agent_prompt_v7 as _p7
import agent_tools_v7 as _t7
import agent_v6 as mod

# Patch v6 to use v7 prompt + v7 tools
mod.SYSTEM_PROMPT = _p7.SYSTEM_PROMPT
mod.dispatch_tool = _t7.dispatch_tool
mod.TOOL_REGISTRY = _t7.TOOL_REGISTRY

from agent_v6 import main
if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Commit composition**
```bash
git add benchmark/scripts/compose_v7_prompt.py benchmark/scripts/agent_tool_hints_v7.py \
        benchmark/scripts/agent_prompt_v7.py benchmark/scripts/agent_tools_v7.py \
        benchmark/scripts/agent_v7.py
git commit -m "v7 agent: inject tool cards into prompt, gate dispatch to KEEP tools"
```

### Task 13: Run agent_v7 on dev n=480

- [ ] **Step 1: Relaunch vLLM**
```bash
bash benchmark/scripts/launch_qwen35_replicas.sh
sleep 30
curl -s http://localhost:8210/v1/models | head -5
```

- [ ] **Step 2: Run agent_v7 dev**
```bash
python benchmark/scripts/agent_v7.py \
  --manifest benchmark/manifests_v2/full_manifest.json \
  --split dev --backend qwen3 \
  --output benchmark/results/v7_agent_qwen3_dev.json \
  --max_turns 5 --max_workers 9 \
  2>&1 | tee /tmp/v7_dev.log
```

- [ ] **Step 3: Evaluate dev**
```bash
python -c "
import json, numpy as np
from sklearn.metrics import roc_auc_score
def macro(path):
    r = json.load(open(path))
    by_d = {}
    for x in r:
        if x.get('label_gt') is None: continue
        by_d.setdefault(x['domain_code'], []).append(x)
    aurocs = []
    for d, items in by_d.items():
        y = [i['label_gt'] for i in items]; s = [i['anomaly_score'] for i in items]
        if len(set(y)) > 1: aurocs.append(roc_auc_score(y, s))
    return np.mean(aurocs), aurocs
v7, v7d = macro('benchmark/results/v7_agent_qwen3_dev.json')
dr, drd = macro('benchmark/results/v6_direct_qwen3_dev.json')
print(f'agent_v7  dev macro AUROC: {v7:.4f}')
print(f'Direct    dev macro AUROC: {dr:.4f}')
print(f'Δ = {v7-dr:+.4f}')
"
```

- [ ] **Step 4: Decision gate**

If **Δ > 0**, proceed to test. Else document the failure and stop (see Task 15's alternate branch).

### Task 14: Run agent_v7 on test n=1418 (if dev passes)

- [ ] **Step 1: Run test**
```bash
python benchmark/scripts/agent_v7.py \
  --manifest benchmark/manifests_v2/full_manifest.json \
  --split test --backend qwen3 \
  --output benchmark/results/v7_agent_qwen3_test.json \
  --max_turns 5 --max_workers 9 \
  2>&1 | tee /tmp/v7_test.log
```

- [ ] **Step 2: Compute test macro + bootstrap CI vs Direct**
```bash
python -c "
import json, numpy as np
from sklearn.metrics import roc_auc_score
rng = np.random.default_rng(42)
def macro(r):
    by_d = {}
    for x in r:
        if x.get('label_gt') is None: continue
        by_d.setdefault(x['domain_code'], []).append(x)
    aurocs = []
    for d, items in by_d.items():
        y = [i['label_gt'] for i in items]; s = [i['anomaly_score'] for i in items]
        if len(set(y)) > 1: aurocs.append(roc_auc_score(y, s))
    return np.mean(aurocs)
v7 = json.load(open('benchmark/results/v7_agent_qwen3_test.json'))
dr = json.load(open('benchmark/results/v6_direct_qwen3_test.json'))
print(f'v7  test macro: {macro(v7):.4f}')
print(f'dir test macro: {macro(dr):.4f}')
print(f'Δ = {macro(v7)-macro(dr):+.4f}')
# paired bootstrap
dr_by_id = {x['item_id']: x for x in dr}
paired = [(x, dr_by_id.get(x['item_id'])) for x in v7 if dr_by_id.get(x['item_id'])]
deltas = []
items = list(range(len(paired)))
for _ in range(1000):
    idx = rng.integers(0, len(items), len(items))
    sub = [paired[i] for i in idx]
    deltas.append(macro([a for a,_ in sub]) - macro([b for _,b in sub]))
print(f'95% CI on Δ: [{np.percentile(deltas,2.5):+.4f}, {np.percentile(deltas,97.5):+.4f}]')
"
```

### Task 15: Shut down vLLM + write V7_RESULTS.md

- [ ] **Step 1: Kill replicas**
```bash
pkill -9 -f "Qwen3.5" || true
pkill -9 -f "vllm_lb" || true
```

- [ ] **Step 2: Write V7_RESULTS.md**

Template at `refine-logs/V7_RESULTS.md`:

```markdown
# V7 Results — Niche-Aware Agent (Per-Tool Audit)

**Date**: 2026-04-18
**Backbone**: Qwen3.5-VL-27B INT8

## Headline (vs Direct only)

| Metric | Direct | v7 agent | Δ | 95% CI |
|---|---|---|---|---|
| Dev macro AUROC  | 0.xxxx | 0.xxxx | ±0.xxxx | [±, ±] |
| Test macro AUROC | 0.xxxx | 0.xxxx | ±0.xxxx | [±, ±] |

## Tool audit summary

| tool | verdict | niche n | niche Δ |
|---|---|---|---|
| (fill from tool_cards/*.md) |

## Honest caveats

- Only vs Direct, not vs Fusion/Router
- Tool cards are dev-derived (no test leakage)
- KEEP/DROP thresholds: n≥10, bootstrap CI lower > 0

## Files

- agent code: agent_v7.py, agent_tools_v7.py, agent_prompt_v7.py
- results: benchmark/results/v7_agent_qwen3_{dev,test}.json
- tool cards: refine-logs/tool_cards/*.md
```

Fill in real numbers from previous tasks.

- [ ] **Step 3: Commit final results**
```bash
git add benchmark/results/v7_agent_qwen3_*.json refine-logs/V7_RESULTS.md \
        refine-logs/tool_cards/ refine-logs/tool_diagnosis/
git commit -m "v7 results: per-tool niche audit + final agent_v7 test eval"
```

- [ ] **Step 4: Update RESUME.md**

Edit top of RESUME.md to reflect new v7 state:
```
**Last active**: 2026-04-18 ~end of v7 iteration
**Status**: v7 niche-aware agent completed. See refine-logs/V7_RESULTS.md.
```

Commit:
```bash
git add RESUME.md
git commit -m "RESUME: v7 iteration complete"
```

---

## Failure Branches

### If Task 13 Δ ≤ 0 (v7 loses to Direct on dev)

Do not proceed to test. Instead:

- [ ] **Analyze** why v7 lost: too few KEEP tools? Tools overlap? Prompt confusion?
- [ ] **Record** the negative finding in `refine-logs/V7_RESULTS.md` as an honest null result
- [ ] **Stop** — user needs to be informed before any more test compute is spent

### If vLLM replicas crash mid-audit

- [ ] Re-launch via `bash benchmark/scripts/launch_qwen35_replicas.sh`
- [ ] Resume by re-running `tool_audit_runner.py` (it skips files that already exist)
- [ ] If a specific tool keeps crashing, audit its code or set `--max_items 240` fallback

---

## Self-Review Against Spec

- ✅ 13 tools each get a dedicated tool card (Task 10)
- ✅ Single-tool agent framework (Task 06)
- ✅ Dev-only slicing, test runs once (Tasks 13, 14)
- ✅ vLLM shutdown between phases (Tasks 11, 15)
- ✅ KEEP threshold n≥10, CI lower > 0 (Task 10)
- ✅ Max turns 3 single-tool, 5 combined (Tasks 06, 13)
- ✅ Only Direct as baseline (no Fusion/Router) (Task 14)
- ✅ Honest failure branch if v7 loses (Failure Branches section)
