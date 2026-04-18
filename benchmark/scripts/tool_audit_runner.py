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
    ap.add_argument("--overwrite", action="store_true",
                    help="re-run tools even if output file exists "
                         "(default: skip existing)")
    args = ap.parse_args()

    Path(args.out_dir).mkdir(parents=True, exist_ok=True)
    tools = args.tools or TOOLS
    script = "benchmark/scripts/single_tool_agent.py"

    t0 = time.time()
    for i, tool in enumerate(tools, 1):
        out = f"{args.out_dir}/{tool}.json"
        if not args.overwrite and Path(out).exists():
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
