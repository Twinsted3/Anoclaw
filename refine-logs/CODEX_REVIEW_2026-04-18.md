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
session id: 019d9d10-59f9-7d02-9a55-f3a894821baa
--------
user
You are asked to do an independent correctness + design review of the
AnomalyClaw v6 visual anomaly-detection agent pipeline.

## Context
This is a research project. Previous v5 was an offline per-domain router
(hardcoded strategy per domain). v6 redesigns it as a per-item autonomous
ReAct agent with 13 tools and K=5 turn budget.

Main results (12 domain codes, n=1418 test items, macro AUROC):

| Backbone | Direct | Fusion w=0.2 | Agent alone | Agent+Direct ensemble |
|----------|--------|-------------|-------------|----------------------|
| Qwen3.5-VL-27B | 0.7684 | 0.8142 | 0.7713 (v6.5) | 0.8136 (+4.5pp, p=0.0005) |
| SeedVL | 0.7995 | 0.8075 | 0.7823 (v6) | 0.8089 (+0.93pp) |
| GPT-5.4 | 0.8463 | 0.8550 | 0.8573 (v6.6) | 0.8637 (+1.7pp, best) |

## Files to review (all in /hdd1/jiangxi/AD-Agent/)
- benchmark/scripts/agent_v6.py           (core ReAct loop)
- benchmark/scripts/agent_prompt_v6.py    (base system prompt)
- benchmark/scripts/agent_v6_5.py         (B-regime + free score variant)
- benchmark/scripts/agent_v6_6.py         (self-ensemble variant)
- benchmark/scripts/agent_v6_7.py         (integrated Direct+Agent variant)
- benchmark/scripts/agent_tools_v6.py     (13 tools + TOOL_REGISTRY + dispatch_tool)
- benchmark/scripts/run_baselines_v6.py   (Direct + Fusion baseline runner)
- benchmark/scripts/compose_ensemble.py   (offline score composition)
- benchmark/scripts/eval_v6.py            (AUROC + bootstrap + permutation)
- benchmark/scripts/infer.py              (call_llm + serving-model logging)
- refine-logs/EXPLORATION_JOURNAL.md      (per-round log)
- refine-logs/V6_RESULTS.md               (summary)

## Critical checks (prioritized)

1. **LABEL LEAKAGE**: does any agent/ensemble/eval code path read `label_gt`
   or `split=="test"` ground truth during score generation? Labels must
   ONLY be used inside eval_v6.py for metric computation after scoring.

2. **Calibration leakage**: the only permitted use of calibration is
   (a) Fusion's `load_calibration_median()` for sigmoid center,
   (b) `tool_reference_retriever`'s normal-pool index,
   (c) expert score percentile rank.
   No per-domain weight or strategy should be calibration-fit and applied
   to test. Verify.

3. **Ensemble correctness**: compose_ensemble.py with alpha=0.5 should
   give `final = 0.5 * direct + 0.5 * agent`. Check: are item IDs matched
   correctly? Is fallback handled when one side is missing? Any double-
   counting?

4. **Bootstrap / permutation test**: eval_v6.py `paired_permutation_test`
   should randomly SWAP per-item (agent, direct) scores between A and B
   to null out any system-level advantage. Verify the swap logic is
   correct (not just label swap).

5. **Agent loop bugs**:
   - Force-final at turn K: after last tool call, does the agent ACTUALLY
     get one more chance to produce final? Or does it drop the item?
   - JSON retry: max 1 retry per turn. After retry fails, item errors out
     with score=0.5. Is this safe?
   - Tool dispatch: `dispatch_tool` injects ctx fields. Can tool kwargs
     from VLM OVERRIDE ctx (e.g., VLM passes item_id='X' and overrides
     real item_id)? Any injection risk?

6. **Tool contamination**: does `tool_reference_retriever` use an index
   that might contain TEST items? The index path is per-domain.

7. **Score calibration**: v6.6 uses `score_from_v0(label, confidence)`
   mapping which produces bimodal scores. v6.5/v6.7 use the VLM's
   self-reported `score`. Is this documented? Any silent miscalibration?

8. **Metrics**: macro AUROC averages 12 per-domain AUROCs. If a domain
   has items where expert score is missing (e.g., D8 lacks SubspaceAD
   coverage on 120 items), fusion falls back to direct. Does per-domain
   AUROC still use all items (with direct fallback), or skip them?

9. **Reproducibility**: random seeds. Temperature=0 for VLM. But sub2api
   was routing gpt-5.4 to gpt-5.1 in an earlier run — resulting in 20%
   of items differing >0.1 in score. We now log served_model_id in
   infer.py; is this enough? Should we also log per-item the served
   model?

10. **Is this paper-publishable?**: be blunt. Is the novelty sufficient?
    Are the claimed improvements (+4.5pp Qwen3.5 significant) large
    enough? Are the design choices defensible vs reviewer "this is just
    an ensemble trick"?

## Output format

Return Markdown with sections:
- **CRITICAL** issues (label/calibration leakage, math bugs in core eval)
- **MAJOR** issues (reproducibility risks, edge cases)
- **MINOR** issues (style, naming)
- **PUBLISHABILITY** verdict (1-2 paragraphs)
- **SUGGESTED NEXT EXPERIMENTS** (3-5 concrete ideas for a pure agent that
  doesn't rely on post-hoc ensemble — user's explicit preference)

For each issue give: file:line, what's wrong, exact fix.
codex
I’ll review this as a code review first: leakage and eval math before design judgment. I’ll read the named files and then trace score-generation paths against eval-only label usage.
exec
/bin/bash -lc 'git status --short' in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
 M benchmark/results/v6_7_agent_gpt_test.json
 M benchmark/scripts/agent_v6_7.py
 M inference.py
 D multi_round_skeptic.py
 M prompts.py
 M tools.py
 M utils.py
?? .codex
?? AnomaClaw/
?? MMAD
?? NARRATIVE_REPORT.md
?? aggregate_results.py
?? benchmark/BENCHMARK_SPEC.json
?? benchmark/manifests/
?? benchmark/manifests_v2/
?? benchmark/results/ablation_refs/
?? benchmark/results/agent_v2/
?? benchmark/results/agent_v3/
?? benchmark/results/anomaclaw_react_skill_d1_test.json
?? benchmark/results/anomaclaw_react_v2_d1d10.json
?? benchmark/results/anomaclaw_react_v2_multi.json
?? benchmark/results/anomaclaw_v4_qwen35_test.json
?? benchmark/results/factorial/
?? benchmark/results/full10/
?? benchmark/results/v2_manifest/
?? benchmark/results/v3_fixed/
?? benchmark/results/v4/
?? controller.py
?? experts.py
?? experts/
?? figures/
?? main.py
?? paper/PAPER_IMPROVEMENT_LOG.md
?? paper/figures/architecture.png
?? paper/figures/bootstrap_cis.json
?? paper/figures/descriptor_cis.json
?? paper/figures/fig_architecture.pdf
?? paper/figures/fig_complementarity.pdf
?? paper/figures/fig_intuition.pdf
?? paper/figures/fig_per_domain.pdf
?? paper/figures/fig_routing.pdf
?? paper/figures/pareto.pdf
?? paper/figures/pareto.png
?? paper/math_commands.tex
?? paper/neurips_2025.sty
?? refine-logs/v6_6_eval_gpt_vs_direct.json
?? refine-logs/v6_6_eval_gpt_vs_fusion.json
?? refine-logs/v6_7_eval_gpt_vs_direct.json
?? refine-logs/v6_7_eval_gpt_vs_fusion.json
?? refine-logs/v6_eval_gpt_v66.json
?? refine-logs/v6_eval_qwen3.json
?? refine-logs/v6_eval_qwen3_direct.json
?? refine-logs/v6_eval_seedvl.json
?? refine-logs/v6_eval_seedvl_direct.json
?? refine-logs/v6_eval_seedvl_fusion.json
?? research-wiki/
?? result/
?? run_experiments.py
?? run_experiments_async.py

exec
/bin/bash -lc 'wc -l benchmark/scripts/agent_v6.py benchmark/scripts/agent_prompt_v6.py benchmark/scripts/agent_v6_5.py benchmark/scripts/agent_v6_6.py benchmark/scripts/agent_v6_7.py benchmark/scripts/agent_tools_v6.py benchmark/scripts/run_baselines_v6.py benchmark/scripts/compose_ensemble.py benchmark/scripts/eval_v6.py benchmark/scripts/infer.py refine-logs/EXPLORATION_JOURNAL.md refine-logs/V6_RESULTS.md' in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
   310 benchmark/scripts/agent_v6.py
    99 benchmark/scripts/agent_prompt_v6.py
    61 benchmark/scripts/agent_v6_5.py
   244 benchmark/scripts/agent_v6_6.py
   201 benchmark/scripts/agent_v6_7.py
   538 benchmark/scripts/agent_tools_v6.py
   142 benchmark/scripts/run_baselines_v6.py
    91 benchmark/scripts/compose_ensemble.py
   206 benchmark/scripts/eval_v6.py
  2504 benchmark/scripts/infer.py
   266 refine-logs/EXPLORATION_JOURNAL.md
   200 refine-logs/V6_RESULTS.md
  4862 total

exec
/bin/bash -lc 'rg -n "label_gt|split|calib|calibration|test|AUROC|permutation|bootstrap|shuffle|swap|score_from_v0|served_model|model_id|item_id|dispatch_tool|tool_reference_retriever|load_calibration_median|SubspaceAD|fallback|alpha|final" benchmark/scripts refine-logs/EXPLORATION_JOURNAL.md refine-logs/V6_RESULTS.md' in /hdd1/jiangxi/AD-Agent
 succeeded in 187ms:
benchmark/scripts/build_patch_evidence_cache.py:7:into a JSON file keyed by item_id. infer.py's v3_grounded / v3_egra variants
benchmark/scripts/build_patch_evidence_cache.py:18:      --split test \
benchmark/scripts/build_patch_evidence_cache.py:19:      --output benchmark/results/patch_evidence_test.json \
benchmark/scripts/build_patch_evidence_cache.py:22:The output JSON is a dict keyed by item_id, each value containing:
benchmark/scripts/build_patch_evidence_cache.py:24:    "item_id": ...,
benchmark/scripts/build_patch_evidence_cache.py:114:            return {"item_id": item["item_id"], "error": "no_references"}
benchmark/scripts/build_patch_evidence_cache.py:133:            "item_id": item["item_id"],
benchmark/scripts/build_patch_evidence_cache.py:142:        return {"item_id": item["item_id"], "error": f"{type(e).__name__}: {e}"}
benchmark/scripts/build_patch_evidence_cache.py:148:    parser.add_argument("--split", default="test",
benchmark/scripts/build_patch_evidence_cache.py:149:                        choices=["calibration", "dev", "test", "all"])
benchmark/scripts/build_patch_evidence_cache.py:158:             if (args.split == "all" or x.get("split") == args.split)
benchmark/scripts/build_patch_evidence_cache.py:164:    # Cache already present → resume (skip existing item_ids)
benchmark/scripts/build_patch_evidence_cache.py:176:        if item["item_id"] in cache and cache[item["item_id"]].get("error") is None:
benchmark/scripts/build_patch_evidence_cache.py:178:        cache[item["item_id"]] = build_evidence_for_item(
benchmark/scripts/agent_tools.py:174:        "domain": "Gastrointestinal Endoscopy (HyperKvasir)",
benchmark/scripts/agent_v6_4.py:17:_p6.forced_final_prompt = _p64.forced_final_prompt
benchmark/scripts/agent_v6_4.py:21:from infer import DOMAIN_CONTEXT, score_from_v0, extract_json as _ex  # noqa: E402
benchmark/scripts/agent_v6_4.py:49:def run_v64(self, item_id, query_path, ref_paths, split, domain_code=None):
benchmark/scripts/agent_v6_4.py:54:        result = _orig_run(self, item_id=item_id, query_path=query_path,
benchmark/scripts/agent_v6_4.py:55:                           ref_paths=ref_paths, split=split,
benchmark/scripts/agent_v6_4.py:57:    finally:
benchmark/scripts/agent_v6_4.py:69:    if action not in ("call_tool", "final"):
benchmark/scripts/agent_v6_4.py:71:    if action == "final":
benchmark/scripts/agent_v6_4.py:79:        parsed["score"] = score_from_v0({
benchmark/scripts/download_datasets.sh:4:# Priority: direct/mirror first, proxy as fallback.
benchmark/scripts/download_datasets.sh:32:    # RoadAnomaly21 test set (~2GB)
benchmark/scripts/download_datasets.sh:38:    # BDD100K normal frames (subset) — use val split
benchmark/scripts/download_datasets.sh:70:    print('SIXray downloaded as D3 fallback')
benchmark/scripts/download_datasets.sh:77:# ─── D5: CheXpert (NIH ChestXray14 is large; use CheXpert-small as fallback) ─
benchmark/scripts/download_datasets.sh:112:    print('LEVIR-CD downloaded as D6 fallback')
benchmark/scripts/patch_expert.py:128:        global_similarity: CLS-token similarity for calibration
benchmark/scripts/patch_expert.py:181:    calibrated = 1.0 / (1.0 + math.exp(-20 * (anomaly_score_raw - 0.18)))
benchmark/scripts/patch_expert.py:184:    if calibrated > 0.8:
benchmark/scripts/patch_expert.py:187:    elif calibrated > 0.6:
benchmark/scripts/patch_expert.py:190:    elif calibrated > 0.4:
benchmark/scripts/patch_expert.py:193:    elif calibrated > 0.2:
benchmark/scripts/patch_expert.py:201:        "anomaly_score": round(float(calibrated), 4),
benchmark/scripts/patch_expert.py:214:def evaluate_standalone(manifest_path: str, split: str = "test",
benchmark/scripts/patch_expert.py:225:             if (split == "all" or x["split"] == split)
benchmark/scripts/patch_expert.py:242:                "item_id": item["item_id"],
benchmark/scripts/patch_expert.py:245:                "label_gt": item["label"],
benchmark/scripts/patch_expert.py:246:                "split": item["split"],
benchmark/scripts/patch_expert.py:256:                "item_id": item["item_id"],
benchmark/scripts/patch_expert.py:259:                "label_gt": item["label"],
benchmark/scripts/patch_expert.py:260:                "split": item["split"],
benchmark/scripts/patch_expert.py:282:    parser.add_argument("--split", default="test")
benchmark/scripts/patch_expert.py:287:    evaluate_standalone(args.manifest, args.split, args.domains, args.output)
benchmark/scripts/render_real3d.py:96:                   c=z, cmap='viridis', s=0.5, alpha=0.8)
benchmark/scripts/render_real3d.py:122:    for split in ["train", "test"]:
benchmark/scripts/render_real3d.py:123:        split_dir = cat_dir / split
benchmark/scripts/render_real3d.py:124:        if not split_dir.exists():
benchmark/scripts/render_real3d.py:126:            split_dir = cat_dir
benchmark/scripts/render_real3d.py:128:        for pcd_file in sorted(split_dir.glob("*.pcd")):
benchmark/scripts/render_real3d.py:142:            out_subdir = cat_output / split / label

codex
The initial grep shows labels are present in result records and eval, so I’m narrowing the distinction between metadata carried for later evaluation and labels actually consumed while scoring. I’m also checking whether “test” expert caches are only unsupervised scores or whether any calibration decisions were selected from test outcomes.
exec
/bin/bash -lc "nl -ba benchmark/scripts/agent_v6.py | sed -n '1,340p'" in /hdd1/jiangxi/AD-Agent
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
    56	                                ref_paths: list) -> list:
    57	        user_parts = [text_msg("NORMAL REFERENCE IMAGES:")]
    58	        for rp in ref_paths[:4]:
    59	            user_parts.append(img_msg(load_and_encode(rp)))
    60	        user_parts.append(text_msg("QUERY IMAGE:"))
    61	        user_parts.append(img_msg(load_and_encode(query_path)))
    62	        user_parts.append(text_msg(f"Turn 1/{self.K}. Decide your next action."))
    63	        return [
    64	            {"role": "system", "content": SYSTEM_PROMPT},
    65	            {"role": "user", "content": user_parts},
    66	        ]
    67	
    68	    def _parse_action(self, text: str) -> dict | None:
    69	        parsed = extract_json(text)
    70	        if not isinstance(parsed, dict):
    71	            return None
    72	        action = parsed.get("action")
    73	        if action not in ("call_tool", "final"):
    74	            return None
    75	        if action == "final":
    76	            s = parsed.get("score")
    77	            if s is None:
    78	                return None
    79	            try:
    80	                parsed["score"] = float(s)
    81	            except (TypeError, ValueError):
    82	                return None
    83	        else:
    84	            if not parsed.get("tool"):
    85	                return None
    86	        return parsed
    87	
    88	    def _call_with_json_retry(self, messages: list) -> dict | None:
    89	        attempts = 1 + self.json_retries
    90	        cur = list(messages)
    91	        for _ in range(attempts):
    92	            try:
    93	                text, _, _ = call_llm(self.client, self.model, cur,
    94	                                      max_tokens=self.max_tokens,
    95	                                      temperature=0.0)
    96	            except Exception:
    97	                return None
    98	            parsed = self._parse_action(text)
    99	            if parsed is not None:
   100	                return parsed
   101	            cur = cur + [{
   102	                "role": "user",
   103	                "content": "Your last response was not valid JSON. "
   104	                           "Return a single JSON object with fields "
   105	                           "{thought, action, tool, args, confidence, "
   106	                           "score, rationale}.",
   107	            }]
   108	        return None
   109	
   110	    # ──────────────────────────────────────────────────────────────────
   111	    def run(self, item_id: str, query_path: str, ref_paths: list,
   112	            split: str, domain_code: str | None = None) -> AgentResult:
   113	        ctx = {
   114	            "query_path": query_path,
   115	            "ref_paths": ref_paths,
   116	            "item_id": item_id,
   117	            "split": split,
   118	            "vlm_client": self.client,
   119	            "vlm_model": self.model,
   120	            "llm_client": self.client,
   121	            "llm_model": self.model,
   122	            "_manifest_domain": domain_code,
   123	        }
   124	        messages = self._build_initial_messages(query_path, ref_paths)
   125	        history, tools_used = [], []
   126	
   127	        for turn in range(1, self.K + 1):
   128	            action = self._call_with_json_retry(messages)
   129	            if action is None:
   130	                return AgentResult(
   131	                    item_id=item_id, score=0.5, rationale="json parse failed",
   132	                    n_turns=turn, tools_used=tools_used, history=history,
   133	                    confidence=0, error="malformed JSON after retries",
   134	                )
   135	
   136	            if action["action"] == "final":
   137	                return AgentResult(
   138	                    item_id=item_id,
   139	                    score=max(0.0, min(1.0, float(action["score"]))),
   140	                    rationale=str(action.get("rationale", ""))[:500],
   141	                    n_turns=turn, tools_used=tools_used,
   142	                    history=history + [{"turn": turn, **_summarise(action)}],
   143	                    confidence=int(action.get("confidence", 0) or 0),
   144	                )
   145	
   146	            if turn == self.K:
   147	                # Budget exhausted; force a final in one more sub-call.
   148	                messages.append({"role": "assistant",
   149	                                 "content": json.dumps(_summarise(action))})
   150	                messages.append({"role": "user",
   151	                                 "content": forced_final_prompt(self.K)})
   152	                forced = self._call_with_json_retry(messages)
   153	                if forced and forced.get("action") == "final":
   154	                    return AgentResult(
   155	                        item_id=item_id,
   156	                        score=max(0.0, min(1.0, float(forced["score"]))),
   157	                        rationale=str(forced.get("rationale", ""))[:500],
   158	                        n_turns=self.K, tools_used=tools_used,
   159	                        history=history + [
   160	                            {"turn": turn, **_summarise(action)},
   161	                            {"turn": turn, **_summarise(forced)},
   162	                        ],
   163	                        confidence=int(forced.get("confidence", 0) or 0),
   164	                    )
   165	                return AgentResult(
   166	                    item_id=item_id, score=0.5, rationale="forced-final failed",
   167	                    n_turns=self.K, tools_used=tools_used, history=history,
   168	                    confidence=0, error="forced-final produced non-final",
   169	                )
   170	
   171	            # Execute tool
   172	            tool_name = action["tool"]
   173	            tool_args = action.get("args") or {}
   174	            observation = dispatch_tool(tool_name, tool_args, ctx)
   175	            tools_used.append(tool_name)
   176	            history.append({"turn": turn, **_summarise(action),
   177	                            "obs_keys": list(observation.keys()),
   178	                            "obs_error": observation.get("error")})
   179	
   180	            # Stash expert patches for hotspot/counter tools
   181	            if tool_name == "tool_expert_score":
   182	                ctx["_expert_patches"] = observation.get("top_patches", [])
   183	
   184	            # Feed observation back — include image if present, text otherwise
   185	            obs_parts = []
   186	            obs_text = _obs_to_text(observation)
   187	            obs_parts.append(text_msg(
   188	                f"OBSERVATION from {tool_name}: {obs_text}"))
   189	            for img_key in ("crop_b64", "diff_mask_b64", "aligned_diff_b64",
   190	                            "composite_b64"):
   191	                if observation.get(img_key):
   192	                    obs_parts.append(img_msg(observation[img_key]))
   193	            if observation.get("tiles"):
   194	                for t in observation["tiles"][:9]:
   195	                    obs_parts.append(img_msg(t["crop_b64"]))
   196	            remaining = self.K - turn
   197	            obs_parts.append(text_msg(
   198	                f"Turn {turn + 1}/{self.K}. "
   199	                f"{budget_warning_prompt(remaining)}\n"
   200	                f"Decide your next action."))
   201	            messages.append({"role": "assistant",
   202	                             "content": json.dumps(_summarise(action))})
   203	            messages.append({"role": "user", "content": obs_parts})
   204	
   205	        return AgentResult(
   206	            item_id=item_id, score=0.5, rationale="loop exhausted",
   207	            n_turns=self.K, tools_used=tools_used, history=history,
   208	            confidence=0, error="loop exhausted without final",
   209	        )
   210	
   211	
   212	def _summarise(action: dict) -> dict:
   213	    """Drop large args/rationale for history storage."""
   214	    out = {k: v for k, v in action.items()
   215	           if k not in ("args",) or v is None or len(str(v)) < 500}
   216	    if "args" in action and "args" not in out:
   217	        out["args"] = str(action["args"])[:400]
   218	    return out
   219	
   220	
   221	def _obs_to_text(obs: dict) -> str:
   222	    """Compact text summary of an observation (no base64 payloads)."""
   223	    small = {}
   224	    for k, v in obs.items():
   225	        if k.endswith("_b64"):
   226	            small[k] = f"<{len(v)}-char image>"
   227	        elif k == "tiles":
   228	            small[k] = f"<{len(v)} tiles attached>"
   229	        elif k == "top_patches":
   230	            small[k] = f"<{len(v)} patches>"
   231	        else:
   232	            small[k] = v
   233	    return json.dumps(small, default=str)[:1500]
   234	
   235	
   236	# ── CLI entry ──────────────────────────────────────────────────────────────
   237	
   238	def main():
   239	    ap = argparse.ArgumentParser()
   240	    ap.add_argument("--manifest", required=True)
   241	    ap.add_argument("--split", choices=["calibration", "test"], required=True)
   242	    ap.add_argument("--backend", choices=["qwen3", "seedvl", "gpt"], required=True)
   243	    ap.add_argument("--output", required=True)
   244	    ap.add_argument("--domains", nargs="*", default=None)
   245	    ap.add_argument("--max_turns", type=int, default=5)
   246	    ap.add_argument("--max_workers", type=int, default=8)
   247	    ap.add_argument("--max_items", type=int, default=0)
   248	    ap.add_argument("--resume", action="store_true",
   249	                    help="skip items already present in --output")
   250	    args = ap.parse_args()
   251	
   252	    items = json.load(open(args.manifest))
   253	    items = [x for x in items if x.get("split") == args.split]
   254	    if args.domains:
   255	        items = [x for x in items if x.get("domain_code") in args.domains]
   256	    if args.max_items:
   257	        items = items[:args.max_items]
   258	
   259	    done_ids: set = set()
   260	    prev: list = []
   261	    if args.resume and os.path.exists(args.output):
   262	        prev = json.load(open(args.output))
   263	        done_ids = {r["item_id"] for r in prev if r.get("error") is None}
   264	        items = [x for x in items if x["item_id"] not in done_ids]
   265	        print(f"[resume] {len(done_ids)} already done; {len(items)} remaining")
   266	
   267	    client = get_client(args.backend)
   268	    model = get_model_name(args.backend)
   269	    agent = ReActAgent(vlm_client=client, vlm_model=model,
   270	                       max_turns=args.max_turns)
   271	
   272	    results: list = list(prev)
   273	    t0 = time.time()
   274	
   275	    def _run_one(x):
   276	        try:
   277	            r = agent.run(item_id=x["item_id"], query_path=x["query_path"],
   278	                          ref_paths=x["ref_paths"], split=args.split,
   279	                          domain_code=x.get("domain_code"))
   280	            return {
   281	                "item_id": x["item_id"], "domain_code": x.get("domain_code"),
   282	                "label_gt": x.get("label"), "anomaly_score": r.score,
   283	                "rationale": r.rationale, "n_turns": r.n_turns,
   284	                "tools_used": r.tools_used, "confidence": r.confidence,
   285	                "error": r.error,
   286	            }
   287	        except Exception as e:
   288	            return {"item_id": x["item_id"], "domain_code": x.get("domain_code"),
   289	                    "label_gt": x.get("label"), "anomaly_score": 0.5,
   290	                    "n_turns": 0, "tools_used": [], "confidence": 0,
   291	                    "error": f"{type(e).__name__}: {e}"}
   292	
   293	    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
   294	    with ThreadPoolExecutor(max_workers=args.max_workers) as ex:
   295	        futures = [ex.submit(_run_one, x) for x in items]
   296	        for i, fut in enumerate(as_completed(futures)):
   297	            results.append(fut.result())
   298	            if (i + 1) % 25 == 0:
   299	                with open(args.output, "w") as f:
   300	                    json.dump(results, f)
   301	                print(f"[{i+1}/{len(items)}] {time.time()-t0:.1f}s  "
   302	                      f"written={len(results)}", flush=True)
   303	
   304	    with open(args.output, "w") as f:
   305	        json.dump(results, f)
   306	    print(f"Wrote {len(results)} results → {args.output}")
   307	
   308	
   309	if __name__ == "__main__":
   310	    main()

exec
/bin/bash -lc "nl -ba benchmark/scripts/agent_tools_v6.py | sed -n '1,560p'" in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
     1	"""AnomalyClaw v6 — 13-tool catalog for the ReAct agent.
     2	
     3	Design invariants:
     4	- No per-domain branching inside tools. Domain code is never a modeling input
     5	  (only used by tool_reference_retriever to locate its cached index file).
     6	- Pure functions where possible; cache expensive resources at module level.
     7	- Each tool returns a JSON-serializable dict with an `error` key on failure.
     8	
     9	Tiers:
    10	  1. Expert probes: tool_expert_score
    11	  2. Visual inspection: hotspot_cropper, zoom_bbox, patch_grid, image_diff,
    12	                        rotate_align, side_by_side
    13	  3. Reference understanding: reference_profiler, reference_retriever
    14	  4. Structural: component_counter, segment_and_count, texture_fft
    15	  5. Knowledge: domain_knowledge
    16	"""
    17	from __future__ import annotations
    18	
    19	import base64
    20	import json
    21	import os
    22	import sys
    23	from functools import lru_cache
    24	from io import BytesIO
    25	from pathlib import Path
    26	from typing import Any
    27	
    28	import numpy as np
    29	from PIL import Image
    30	
    31	sys.path.insert(0, str(Path(__file__).parent))
    32	from infer import call_llm, extract_json, img_msg, load_and_encode, text_msg  # noqa: E402
    33	
    34	RESULTS_DIR = Path("/hdd1/jiangxi/AD-Agent/benchmark/results")
    35	
    36	
    37	# ─── Helpers ────────────────────────────────────────────────────────────────
    38	
    39	def _pil_to_b64(img: Image.Image, max_side: int = 512, quality: int = 85) -> str:
    40	    w, h = img.size
    41	    if max(w, h) > max_side:
    42	        scale = max_side / max(w, h)
    43	        img = img.resize((int(w * scale), int(h * scale)))
    44	    buf = BytesIO()
    45	    img.save(buf, format="JPEG", quality=quality)
    46	    return base64.b64encode(buf.getvalue()).decode("utf-8")
    47	
    48	
    49	# ─── Tier 1: Expert probes ──────────────────────────────────────────────────
    50	
    51	EXPERT_FILES = {
    52	    "subspacead":    {"calibration": "subspacead_calibration.json",
    53	                      "test":        "subspacead_test.json"},
    54	    "anomalyvfm":    {"calibration": "anomalyvfm_calibration.json",
    55	                      "test":        "anomalyvfm_test.json"},
    56	    "patchknn":      {"calibration": "classical_dinov2_patch_test_all.json",
    57	                      "test":        "classical_dinov2_patch_test_all.json"},
    58	    "dinov2_global": {"calibration": "classical_dinov2_global_test_all.json",
    59	                      "test":        "classical_dinov2_global_test_all.json"},
    60	}
    61	
    62	
    63	@lru_cache(maxsize=16)
    64	def _load_expert_scores(expert: str, split: str) -> tuple[dict, np.ndarray]:
    65	    """Return (item_id -> record, sorted score array for percentile ranking)."""
    66	    if expert not in EXPERT_FILES:
    67	        raise ValueError(f"unknown expert {expert!r}; must be one of {list(EXPERT_FILES)}")
    68	    fname = EXPERT_FILES[expert].get(split)
    69	    if fname is None:
    70	        raise ValueError(f"no {split} file for expert {expert!r}")
    71	    path = RESULTS_DIR / fname
    72	    if not path.exists():
    73	        return {}, np.array([])
    74	    raw = json.load(open(path))
    75	    if isinstance(raw, list):
    76	        recs = {x["item_id"]: x for x in raw if "item_id" in x}
    77	    else:
    78	        recs = raw
    79	    scores = np.array([float(r["anomaly_score"]) for r in recs.values()
    80	                       if r.get("anomaly_score") is not None])
    81	    scores.sort()
    82	    return recs, scores
    83	
    84	
    85	def tool_expert_score(item_id: str, expert: str = "subspacead",
    86	                      split: str = "test", **_) -> dict:
    87	    """Look up a cached expert anomaly score + its percentile rank within `split`.
    88	
    89	    Returns: {expert, score, normalized_rank, top_patches, interpretation, error}
    90	    """
    91	    try:
    92	        recs, all_scores = _load_expert_scores(expert, split)
    93	    except ValueError as e:
    94	        return {"error": str(e)}
    95	    rec = recs.get(item_id)
    96	    if rec is None or rec.get("anomaly_score") is None:
    97	        return {"error": f"no cached score for {item_id} in {expert}/{split}"}
    98	    s = float(rec["anomaly_score"])
    99	    if len(all_scores) == 0:
   100	        rank = 0.5
   101	    else:
   102	        rank = float(np.searchsorted(all_scores, s) / len(all_scores))
   103	    interp = ("strong anomaly signal" if rank >= 0.80 else
   104	              "weak signal"           if rank <= 0.40 else
   105	              "moderate / ambiguous signal")
   106	    return {
   107	        "expert": expert,
   108	        "score": s,
   109	        "normalized_rank": rank,
   110	        "top_patches": rec.get("top_patches") or [],
   111	        "interpretation": interp,
   112	        "error": None,
   113	    }
   114	
   115	
   116	# ─── Tier 2: Visual inspection ──────────────────────────────────────────────
   117	
   118	def tool_hotspot_cropper(query_path: str, patches: list[dict] | None = None,
   119	                         pad: float = 0.15, k: int = 5,
   120	                         _expert_patches: list | None = None, **_) -> dict:
   121	    """Crop query image around top-k expert-flagged patches (48x48 grid).
   122	
   123	    If `patches` is not provided, falls back to `_expert_patches` from session
   124	    context (populated by a prior tool_expert_score call).
   125	    """
   126	    patches = patches or _expert_patches or []
   127	    if not patches:
   128	        return {"error": "no patches available; call tool_expert_score(subspacead) first"}
   129	    img = Image.open(query_path).convert("RGB")
   130	    W, H = img.size
   131	    grid = 48
   132	    rows = [p.get("row") for p in patches[:k] if p.get("row") is not None]
   133	    cols = [p.get("col") for p in patches[:k] if p.get("col") is not None]
   134	    if not rows or not cols:
   135	        return {"error": "patches missing row/col fields"}
   136	    r0, r1 = min(rows), max(rows) + 1
   137	    c0, c1 = min(cols), max(cols) + 1
   138	    span_r, span_c = r1 - r0, c1 - c0
   139	    r0 = max(0, r0 - max(1, int(pad * max(span_r, 1))))
   140	    r1 = min(grid, r1 + max(1, int(pad * max(span_r, 1))))
   141	    c0 = max(0, c0 - max(1, int(pad * max(span_c, 1))))
   142	    c1 = min(grid, c1 + max(1, int(pad * max(span_c, 1))))
   143	    x0, x1 = int(c0 / grid * W), int(c1 / grid * W)
   144	    y0, y1 = int(r0 / grid * H), int(r1 / grid * H)
   145	    if x1 <= x0 or y1 <= y0:
   146	        return {"error": "degenerate crop"}
   147	    crop = img.crop((x0, y0, x1, y1))
   148	    return {
   149	        "bbox": [x0, y0, x1, y1],
   150	        "crop_b64": _pil_to_b64(crop),
   151	        "original_size": [W, H],
   152	        "error": None,
   153	    }
   154	
   155	
   156	def tool_zoom_bbox(query_path: str, bbox: list[int], **_) -> dict:
   157	    """Agent-specified crop. bbox = [x0, y0, x1, y1] in pixel coords."""
   158	    if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
   159	        return {"error": "bbox must be [x0, y0, x1, y1]"}
   160	    x0, y0, x1, y1 = bbox
   161	    if x1 <= x0 or y1 <= y0:
   162	        return {"error": f"invalid bbox {bbox}: x1 must be > x0 and y1 > y0"}
   163	    img = Image.open(query_path).convert("RGB")
   164	    W, H = img.size
   165	    x0 = max(0, min(W - 1, int(x0)))
   166	    y0 = max(0, min(H - 1, int(y0)))
   167	    x1 = max(x0 + 1, min(W, int(x1)))
   168	    y1 = max(y0 + 1, min(H, int(y1)))
   169	    crop = img.crop((x0, y0, x1, y1))
   170	    return {
   171	        "bbox": [x0, y0, x1, y1],
   172	        "crop_b64": _pil_to_b64(crop),
   173	        "original_size": [W, H],
   174	        "error": None,
   175	    }
   176	
   177	
   178	def tool_patch_grid(query_path: str, rows: int = 3, cols: int = 3, **_) -> dict:
   179	    """Return rows*cols tiles covering the image in a regular grid."""
   180	    try:
   181	        rows, cols = int(rows), int(cols)
   182	    except (TypeError, ValueError):
   183	        return {"error": "rows/cols must be integers"}
   184	    if rows < 1 or cols < 1 or rows > 8 or cols > 8:
   185	        return {"error": f"rows/cols must be in [1, 8]; got {rows}x{cols}"}
   186	    img = Image.open(query_path).convert("RGB")
   187	    W, H = img.size
   188	    tw, th = W // cols, H // rows
   189	    tiles = []
   190	    for i in range(rows):
   191	        for j in range(cols):
   192	            x0, y0 = j * tw, i * th
   193	            x1 = (j + 1) * tw if j < cols - 1 else W
   194	            y1 = (i + 1) * th if i < rows - 1 else H
   195	            crop = img.crop((x0, y0, x1, y1))
   196	            tiles.append({
   197	                "cell": [i, j],
   198	                "bbox": [x0, y0, x1, y1],
   199	                "crop_b64": _pil_to_b64(crop, max_side=256),
   200	            })
   201	    return {"rows": rows, "cols": cols, "tiles": tiles, "error": None}
   202	
   203	
   204	def tool_image_diff(query_path: str, ref_path: str | None = None,
   205	                    ref_paths: list[str] | None = None, ref_idx: int = 0,
   206	                    threshold: float = 30.0, **_) -> dict:
   207	    """Absolute pixel diff between query and a reference, with stats + mask.
   208	
   209	    Accepts either `ref_path` directly or `ref_idx` + `ref_paths` from session.
   210	    """
   211	    if ref_path is None and ref_paths:
   212	        try:
   213	            ref_path = ref_paths[int(ref_idx)]
   214	        except (IndexError, ValueError):
   215	            return {"error": f"ref_idx {ref_idx} out of range"}
   216	    if not ref_path or not os.path.exists(ref_path):
   217	        return {"error": f"ref_path not found: {ref_path!r}"}
   218	    q = np.array(Image.open(query_path).convert("RGB").resize((256, 256)))
   219	    r = np.array(Image.open(ref_path).convert("RGB").resize((256, 256)))
   220	    diff = np.abs(q.astype(float) - r.astype(float)).mean(axis=2)
   221	    mask = (diff > threshold).astype(np.uint8) * 255
   222	    change_pct = float(mask.mean() / 255 * 100)
   223	    return {
   224	        "mean_diff": float(diff.mean()),
   225	        "max_diff": float(diff.max()),
   226	        "change_percent": change_pct,
   227	        "threshold": threshold,
   228	        "diff_mask_b64": _pil_to_b64(Image.fromarray(mask, mode="L").convert("RGB"),
   229	                                     max_side=256),
   230	        "error": None,
   231	    }
   232	
   233	
   234	def tool_rotate_align(query_path: str, ref_path: str | None = None,
   235	                      ref_paths: list[str] | None = None, ref_idx: int = 0,
   236	                      **_) -> dict:
   237	    """Try rotations [-10,-5,0,5,10] deg on ref, pick min-MSE, then return aligned diff."""
   238	    if ref_path is None and ref_paths:
   239	        try:
   240	            ref_path = ref_paths[int(ref_idx)]
   241	        except (IndexError, ValueError):
   242	            return {"error": f"ref_idx {ref_idx} out of range"}
   243	    if not ref_path or not os.path.exists(ref_path):
   244	        return {"error": f"ref_path not found: {ref_path!r}"}
   245	    q = np.array(Image.open(query_path).convert("RGB").resize((256, 256)))
   246	    r_img = Image.open(ref_path).convert("RGB").resize((256, 256))
   247	    best_angle, best_mse, best_diff = 0.0, float("inf"), None
   248	    for angle in [-10, -5, 0, 5, 10]:
   249	        r_rot = np.array(r_img.rotate(angle, resample=Image.BILINEAR))
   250	        d = np.abs(q.astype(float) - r_rot.astype(float)).mean(axis=2)
   251	        mse = float(d.mean())
   252	        if mse < best_mse:
   253	            best_mse, best_angle, best_diff = mse, angle, d
   254	    mask = (best_diff > 30.0).astype(np.uint8) * 255
   255	    return {
   256	        "rotation_angle_deg": float(best_angle),
   257	        "aligned_mean_diff": float(best_mse),
   258	        "aligned_diff_b64": _pil_to_b64(Image.fromarray(mask, mode="L").convert("RGB"),
   259	                                        max_side=256),
   260	        "error": None,
   261	    }
   262	
   263	
   264	def tool_side_by_side(query_path: str, bbox: list[int],
   265	                      ref_paths: list[str] | None = None, **_) -> dict:
   266	    """Composite: query_crop | ref0_crop | ref1_crop | ref2_crop | ref3_crop.
   267	
   268	    bbox is interpreted in 256x256 normalized coords (resize all images to 256).
   269	    """
   270	    if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
   271	        return {"error": "bbox must be [x0, y0, x1, y1]"}
   272	    x0, y0, x1, y1 = [int(v) for v in bbox]
   273	    if x1 <= x0 or y1 <= y0:
   274	        return {"error": f"invalid bbox {bbox}"}
   275	    if not ref_paths:
   276	        return {"error": "no ref_paths in session"}
   277	    def _crop(path):
   278	        img = Image.open(path).convert("RGB").resize((256, 256))
   279	        xa = max(0, min(255, x0)); ya = max(0, min(255, y0))
   280	        xb = max(xa + 1, min(256, x1)); yb = max(ya + 1, min(256, y1))
   281	        return img.crop((xa, ya, xb, yb)).resize((128, 128))
   282	    crops = [_crop(query_path)] + [_crop(p) for p in ref_paths[:4]]
   283	    total_w = 128 * len(crops)
   284	    composite = Image.new("RGB", (total_w, 128), (255, 255, 255))
   285	    for i, c in enumerate(crops):
   286	        composite.paste(c, (i * 128, 0))
   287	    return {
   288	        "bbox": bbox,
   289	        "n_crops": len(crops),
   290	        "composite_b64": _pil_to_b64(composite, max_side=768),
   291	        "error": None,
   292	    }
   293	
   294	
   295	# ─── Tier 3: Reference understanding ────────────────────────────────────────
   296	
   297	PROFILER_SYSTEM = (
   298	    "You are analyzing normal reference images. Describe what they have in common "
   299	    "in terms of: (1) objects/scene content, (2) colors, (3) textures, (4) structural "
   300	    "components, (5) typical variations across the references. Be factual and concise. "
   301	    "Return JSON: {\"profile_text\": \"1-3 sentences\", \"common_objects\": [...], "
   302	    "\"typical_colors\": [...], \"variations\": [...]}"
   303	)
   304	
   305	
   306	def tool_reference_profiler(ref_paths: list[str] | None = None,
   307	                            vlm_client=None, vlm_model: str | None = None,
   308	                            max_tokens: int = 400, **_) -> dict:
   309	    """Ask a VLM to describe the normality profile from 4 refs."""
   310	    if os.environ.get("ANOMA_TEST_STUB") == "1":
   311	        return {
   312	            "error": None,
   313	            "profile_text": "stub profile",
   314	            "common_objects": ["stub"],
   315	            "typical_colors": [],
   316	            "variations": [],
   317	            "n_refs_used": len(ref_paths[:4]) if ref_paths else 0,
   318	        }
   319	    if not ref_paths:
   320	        return {"error": "no ref_paths"}
   321	    if vlm_client is None or vlm_model is None:
   322	        return {"error": "vlm_client and vlm_model required"}
   323	    parts = [text_msg(PROFILER_SYSTEM)]
   324	    for p in ref_paths[:4]:
   325	        parts.append(img_msg(load_and_encode(p)))
   326	    parts.append(text_msg("Profile these 4 normal references."))
   327	    messages = [{"role": "user", "content": parts}]
   328	    try:
   329	        text, _, _ = call_llm(vlm_client, vlm_model, messages,
   330	                              max_tokens=max_tokens, temperature=0.0)
   331	    except Exception as e:
   332	        return {"error": f"vlm call failed: {e}"}
   333	    parsed = extract_json(text) or {}
   334	    return {
   335	        "error": None,
   336	        "profile_text": parsed.get("profile_text", text[:200]),
   337	        "common_objects": parsed.get("common_objects", []),
   338	        "typical_colors": parsed.get("typical_colors", []),
   339	        "variations": parsed.get("variations", []),
   340	        "n_refs_used": len(ref_paths[:4]),
   341	    }
   342	
   343	
   344	_RETRIEVAL_CACHE: dict[str, Any] = {}
   345	
   346	
   347	def _load_retrieval_model_v6(device: str = "cuda"):
   348	    if "model" in _RETRIEVAL_CACHE:
   349	        return _RETRIEVAL_CACHE["model"], _RETRIEVAL_CACHE["transform"]
   350	    import torch
   351	    import timm
   352	    model = timm.create_model("vit_small_patch14_dinov2.lvd142m",
   353	                              pretrained=True, num_classes=0)
   354	    model = model.to(device).eval()
   355	    cfg = timm.data.resolve_data_config(model.pretrained_cfg)
   356	    transform = timm.data.create_transform(**cfg, is_training=False)
   357	    _RETRIEVAL_CACHE["model"] = model
   358	    _RETRIEVAL_CACHE["transform"] = transform
   359	    return model, transform
   360	
   361	
   362	def tool_reference_retriever(query_path: str, domain_code: str | None = None,
   363	                             k: int = 4,
   364	                             index_dir: str = "/hdd1/jiangxi/AD-Agent/benchmark/retrieval_index",
   365	                             device: str = "cuda",
   366	                             item_id: str | None = None,
   367	                             _manifest_domain: str | None = None, **_) -> dict:
   368	    """Retrieve top-k most similar normal references via DINOv2 similarity.
   369	
   370	    `domain_code` may be provided by the agent; if not, we try `_manifest_domain`
   371	    (auto-injected from session ctx; this is the only place the agent legitimately
   372	    uses the domain code — to locate its cached normality bank, not for modeling).
   373	    """
   374	    domain_code = domain_code or _manifest_domain
   375	    if not domain_code:
   376	        return {"error": "domain_code required to locate retrieval index"}
   377	    idx_path = os.path.join(index_dir, f"{domain_code}_index.npz")
   378	    if not os.path.exists(idx_path):
   379	        return {"error": f"no retrieval index at {idx_path}"}
   380	    try:
   381	        import torch
   382	        model, transform = _load_retrieval_model_v6(device)
   383	        img = Image.open(query_path).convert("RGB")
   384	        tensor = transform(img).unsqueeze(0).to(device)
   385	        with torch.no_grad():
   386	            emb = model(tensor).cpu().numpy().flatten()
   387	        emb = emb / (np.linalg.norm(emb) + 1e-8)
   388	        data = np.load(idx_path, allow_pickle=True)
   389	        sims = data["embeddings"] @ emb
   390	        top_idx = np.argsort(sims)[::-1][:k]
   391	        results = [{"path": str(data["paths"][i]),
   392	                    "similarity": float(sims[i])} for i in top_idx]
   393	        return {"results": results, "error": None}
   394	    except Exception as e:
   395	        return {"error": f"retrieval failed: {e}"}
   396	
   397	
   398	# ─── Tier 4: Structural analysis ────────────────────────────────────────────
   399	
   400	def tool_component_counter(patches: list[dict] | None = None,
   401	                           _expert_patches: list | None = None,
   402	                           threshold: float = 0.5, **_) -> dict:
   403	    """Count connected components among top-k expert patches (48x48 grid, 4-conn)."""
   404	    patches = patches or _expert_patches or []
   405	    if not patches:
   406	        return {"error": None, "n_components": 0, "n_active_patches": 0}
   407	    grid = np.zeros((48, 48), dtype=np.uint8)
   408	    for p in patches:
   409	        r, c = p.get("row"), p.get("col")
   410	        if r is not None and c is not None and 0 <= r < 48 and 0 <= c < 48:
   411	            grid[r, c] = 1
   412	    n, seen = 0, np.zeros_like(grid, dtype=bool)
   413	    for i in range(48):
   414	        for j in range(48):
   415	            if grid[i, j] and not seen[i, j]:
   416	                n += 1
   417	                stack = [(i, j)]
   418	                while stack:
   419	                    ii, jj = stack.pop()
   420	                    if (0 <= ii < 48 and 0 <= jj < 48 and grid[ii, jj]
   421	                            and not seen[ii, jj]):
   422	                        seen[ii, jj] = True
   423	                        stack.extend([(ii+1, jj), (ii-1, jj),
   424	                                      (ii, jj+1), (ii, jj-1)])
   425	    return {"error": None, "n_components": int(n),
   426	            "n_active_patches": int(grid.sum())}
   427	
   428	
   429	def tool_segment_and_count(query_path: str, ref_paths: list[str] | None = None,
   430	                           grid_size: int = 8, **_) -> dict:
   431	    """Coarse structural-change signal via 8x8 intensity-grid diff vs ref 0."""
   432	    if not ref_paths:
   433	        return {"error": "ref_paths required"}
   434	    q = np.array(Image.open(query_path).convert("L").resize((256, 256)))
   435	    r = np.array(Image.open(ref_paths[0]).convert("L").resize((256, 256)))
   436	    cell = 256 // grid_size
   437	    q_grid = q.reshape(grid_size, cell, grid_size, cell).mean(axis=(1, 3))
   438	    r_grid = r.reshape(grid_size, cell, grid_size, cell).mean(axis=(1, 3))
   439	    diff = np.abs(q_grid - r_grid)
   440	    changed = int((diff > 20).sum())
   441	    top_idx = np.argsort(diff.ravel())[::-1][:5]
   442	    top_diffs = [{"row": int(i // grid_size), "col": int(i % grid_size),
   443	                  "diff": float(diff.ravel()[i])} for i in top_idx
   444	                 if diff.ravel()[i] > 10]
   445	    return {
   446	        "error": None,
   447	        "changed_cells": changed,
   448	        "total_cells": grid_size * grid_size,
   449	        "change_ratio": round(changed / (grid_size * grid_size), 3),
   450	        "top_differences": top_diffs,
   451	    }
   452	
   453	
   454	def tool_texture_fft(query_path: str, **_) -> dict:
   455	    """FFT periodicity score: top-10 peak energy / total spectrum energy."""
   456	    img = np.array(Image.open(query_path).convert("L").resize((256, 256))).astype(float)
   457	    img -= img.mean()
   458	    spec = np.abs(np.fft.fftshift(np.fft.fft2(img)))
   459	    h, w = spec.shape
   460	    cy, cx = h // 2, w // 2
   461	    spec[cy - 3:cy + 3, cx - 3:cx + 3] = 0
   462	    total = float(spec.sum()) + 1e-8
   463	    top_k = float(np.sort(spec.ravel())[::-1][:10].sum())
   464	    score = float(top_k / total)
   465	    return {"error": None, "periodicity_score": min(1.0, max(0.0, score))}
   466	
   467	
   468	# ─── Tier 5: Semantic knowledge ─────────────────────────────────────────────
   469	
   470	KNOWLEDGE_SYSTEM = (
   471	    "You are a domain knowledge assistant for visual anomaly detection. "
   472	    "Answer the question in 2-4 sentences with concrete visual details. "
   473	    "Do not hedge. Return JSON: {\"answer\": \"...\"}"
   474	)
   475	
   476	
   477	def tool_domain_knowledge(question: str, llm_client=None,
   478	                          llm_model: str | None = None,
   479	                          vlm_client=None, vlm_model: str | None = None,
   480	                          max_tokens: int = 300, **_) -> dict:
   481	    """Text-only LLM query. Agent phrases its own question; no domain hint baked in."""
   482	    if os.environ.get("ANOMA_TEST_STUB") == "1":
   483	        return {"error": None, "answer": f"[stub] re: {question}"}
   484	    client = llm_client or vlm_client
   485	    model = llm_model or vlm_model
   486	    if client is None or model is None:
   487	        return {"error": "llm_client and llm_model required"}
   488	    messages = [
   489	        {"role": "system", "content": KNOWLEDGE_SYSTEM},
   490	        {"role": "user", "content": question},
   491	    ]
   492	    try:
   493	        text, _, _ = call_llm(client, model, messages,
   494	                              max_tokens=max_tokens, temperature=0.0)
   495	    except Exception as e:
   496	        return {"error": f"llm call failed: {e}"}
   497	    parsed = extract_json(text) or {}
   498	    return {"error": None, "answer": parsed.get("answer", text.strip()[:300])}
   499	
   500	
   501	# ─── Dispatcher ─────────────────────────────────────────────────────────────
   502	
   503	TOOL_REGISTRY = {
   504	    "tool_expert_score":        tool_expert_score,
   505	    "tool_hotspot_cropper":     tool_hotspot_cropper,
   506	    "tool_zoom_bbox":           tool_zoom_bbox,
   507	    "tool_patch_grid":          tool_patch_grid,
   508	    "tool_image_diff":          tool_image_diff,
   509	    "tool_rotate_align":        tool_rotate_align,
   510	    "tool_side_by_side":        tool_side_by_side,
   511	    "tool_reference_profiler":  tool_reference_profiler,
   512	    "tool_reference_retriever": tool_reference_retriever,
   513	    "tool_component_counter":   tool_component_counter,
   514	    "tool_segment_and_count":   tool_segment_and_count,
   515	    "tool_texture_fft":         tool_texture_fft,
   516	    "tool_domain_knowledge":    tool_domain_knowledge,
   517	}
   518	
   519	
   520	def dispatch_tool(name: str, args: dict, ctx: dict | None = None) -> dict:
   521	    """Dispatch a tool call. ctx carries session state that tools need but
   522	    that the VLM shouldn't re-type (query_path, ref_paths, split, clients)."""
   523	    if name not in TOOL_REGISTRY:
   524	        return {"error": f"unknown tool {name!r}; must be one of {sorted(TOOL_REGISTRY)}"}
   525	    ctx = ctx or {}
   526	    fn = TOOL_REGISTRY[name]
   527	    injected = dict(args or {})
   528	    for k in ("query_path", "ref_paths", "item_id", "split",
   529	              "vlm_client", "vlm_model", "llm_client", "llm_model",
   530	              "_expert_patches", "_manifest_domain"):
   531	        if k in ctx and k not in injected:
   532	            injected[k] = ctx[k]
   533	    try:
   534	        return fn(**injected)
   535	    except TypeError as e:
   536	        return {"error": f"bad args for {name}: {e}"}
   537	    except Exception as e:
   538	        return {"error": f"{name} raised {type(e).__name__}: {e}"}

exec
/bin/bash -lc "nl -ba benchmark/scripts/eval_v6.py | sed -n '1,240p'" in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
     1	"""v6 evaluation: macro AUROC + per-domain + bootstrap 95% CI + paired permutation.
     2	
     3	Usage:
     4	  python benchmark/scripts/eval_v6.py \
     5	    --results benchmark/results/v6_agent_qwen3_test.json \
     6	    --compare_to benchmark/results/v6_fusion_qwen3_test.json \
     7	    --out_json refine-logs/v6_eval_qwen3.json
     8	"""
     9	from __future__ import annotations
    10	
    11	import argparse
    12	import json
    13	from collections import defaultdict
    14	from pathlib import Path
    15	
    16	import numpy as np
    17	from sklearn.metrics import roc_auc_score
    18	
    19	
    20	def _load(path: str) -> list:
    21	    data = json.load(open(path))
    22	    if isinstance(data, dict):
    23	        data = list(data.values())
    24	    return data
    25	
    26	
    27	def macro_auroc(items: list) -> dict:
    28	    by = defaultdict(lambda: ([], []))
    29	    for x in items:
    30	        y = x.get("label_gt")
    31	        s = x.get("anomaly_score")
    32	        d = x.get("domain_code")
    33	        if y is None or s is None or d is None:
    34	            continue
    35	        by[d][0].append(float(s))
    36	        by[d][1].append(int(y))
    37	    per_domain = {}
    38	    for d, (s, y) in by.items():
    39	        if len(set(y)) >= 2:
    40	            per_domain[d] = float(roc_auc_score(y, s))
    41	    macro = float(np.mean(list(per_domain.values()))) if per_domain else 0.0
    42	    return {"macro": macro, "per_domain": per_domain,
    43	            "n_domains": len(per_domain),
    44	            "n_items": sum(len(s) for s, _ in by.values())}
    45	
    46	
    47	def bootstrap_ci_per_domain(items: list, n_boot: int = 1000,
    48	                            seed: int = 42, alpha: float = 0.05) -> dict:
    49	    rng = np.random.RandomState(seed)
    50	    by = defaultdict(lambda: ([], []))
    51	    for x in items:
    52	        y, s, d = x.get("label_gt"), x.get("anomaly_score"), x.get("domain_code")
    53	        if y is None or s is None or d is None:
    54	            continue
    55	        by[d][0].append(float(s))
    56	        by[d][1].append(int(y))
    57	    ci = {}
    58	    for d, (s, y) in by.items():
    59	        s, y = np.array(s), np.array(y)
    60	        if len(set(y)) < 2:
    61	            continue
    62	        boots = []
    63	        for _ in range(n_boot):
    64	            idx = rng.randint(0, len(y), len(y))
    65	            yb, sb = y[idx], s[idx]
    66	            if len(set(yb)) < 2:
    67	                continue
    68	            boots.append(roc_auc_score(yb, sb))
    69	        if boots:
    70	            lo = float(np.percentile(boots, 100 * alpha / 2))
    71	            hi = float(np.percentile(boots, 100 * (1 - alpha / 2)))
    72	            ci[d] = [lo, hi]
    73	    return ci
    74	
    75	
    76	def bootstrap_macro_ci(items: list, n_boot: int = 1000,
    77	                       seed: int = 42, alpha: float = 0.05) -> list:
    78	    """Bootstrap macro AUROC: resample items within each domain, compute macro."""
    79	    rng = np.random.RandomState(seed)
    80	    by = defaultdict(lambda: ([], []))
    81	    for x in items:
    82	        y, s, d = x.get("label_gt"), x.get("anomaly_score"), x.get("domain_code")
    83	        if y is None or s is None or d is None:
    84	            continue
    85	        by[d][0].append(float(s))
    86	        by[d][1].append(int(y))
    87	    macros = []
    88	    for _ in range(n_boot):
    89	        aucs = []
    90	        for d, (s, y) in by.items():
    91	            if len(set(y)) < 2:
    92	                continue
    93	            s, y = np.array(s), np.array(y)
    94	            idx = rng.randint(0, len(y), len(y))
    95	            yb, sb = y[idx], s[idx]
    96	            if len(set(yb)) >= 2:
    97	                aucs.append(roc_auc_score(yb, sb))
    98	        if aucs:
    99	            macros.append(float(np.mean(aucs)))
   100	    if not macros:
   101	        return [0.0, 0.0]
   102	    return [float(np.percentile(macros, 100 * alpha / 2)),
   103	            float(np.percentile(macros, 100 * (1 - alpha / 2)))]
   104	
   105	
   106	def paired_permutation_test(a_items: list, b_items: list,
   107	                            n_perm: int = 10000, seed: int = 42) -> dict:
   108	    rng = np.random.RandomState(seed)
   109	    a_by = {x["item_id"]: x for x in a_items}
   110	    b_by = {x["item_id"]: x for x in b_items}
   111	    common = sorted(set(a_by) & set(b_by))
   112	    per_dom = defaultdict(lambda: {"a": [], "b": [], "y": []})
   113	    for iid in common:
   114	        a, b = a_by[iid], b_by[iid]
   115	        y = a.get("label_gt")
   116	        d = a.get("domain_code")
   117	        if y is None or d is None:
   118	            continue
   119	        per_dom[d]["a"].append(float(a["anomaly_score"]))
   120	        per_dom[d]["b"].append(float(b["anomaly_score"]))
   121	        per_dom[d]["y"].append(int(y))
   122	
   123	    def macro_of(which: str) -> float:
   124	        aucs = []
   125	        for d, dd in per_dom.items():
   126	            y = np.array(dd["y"])
   127	            s = np.array(dd[which])
   128	            if len(set(y)) >= 2:
   129	                aucs.append(roc_auc_score(y, s))
   130	        return float(np.mean(aucs)) if aucs else 0.0
   131	
   132	    observed = macro_of("a") - macro_of("b")
   133	
   134	    null_deltas = []
   135	    for _ in range(n_perm):
   136	        perm_macros_a, perm_macros_b = [], []
   137	        for d, dd in per_dom.items():
   138	            a = np.array(dd["a"]); b = np.array(dd["b"]); y = np.array(dd["y"])
   139	            swap = rng.rand(len(a)) < 0.5
   140	            a2 = np.where(swap, b, a)
   141	            b2 = np.where(swap, a, b)
   142	            if len(set(y)) >= 2:
   143	                perm_macros_a.append(roc_auc_score(y, a2))
   144	                perm_macros_b.append(roc_auc_score(y, b2))
   145	        if perm_macros_a:
   146	            null_deltas.append(float(np.mean(perm_macros_a)
   147	                                     - np.mean(perm_macros_b)))
   148	    null = np.array(null_deltas)
   149	    p = float((np.abs(null) >= abs(observed)).mean()) if len(null) else 1.0
   150	    return {"delta": float(observed), "p_value": p,
   151	            "n_items_common": len(common), "n_permutations": n_perm}
   152	
   153	
   154	def tool_usage_stats(items: list) -> dict:
   155	    """Aggregate tools_used + n_turns + confidence stats from an agent output."""
   156	    from collections import Counter
   157	    turns, tools, n_single = [], Counter(), 0
   158	    for x in items:
   159	        if x.get("n_turns") is None:
   160	            continue
   161	        turns.append(int(x["n_turns"]))
   162	        for t in x.get("tools_used") or []:
   163	            tools[t] += 1
   164	        if x.get("n_turns", 0) == 1 and not x.get("tools_used"):
   165	            n_single += 1
   166	    return {
   167	        "n": len(items),
   168	        "avg_turns": float(np.mean(turns)) if turns else None,
   169	        "median_turns": float(np.median(turns)) if turns else None,
   170	        "pct_single_turn_no_tool": (n_single / len(items) * 100) if items else 0,
   171	        "tool_call_counts": dict(tools),
   172	    }
   173	
   174	
   175	def main():
   176	    ap = argparse.ArgumentParser()
   177	    ap.add_argument("--results", required=True)
   178	    ap.add_argument("--compare_to", default=None)
   179	    ap.add_argument("--out_json", required=True)
   180	    ap.add_argument("--n_boot", type=int, default=1000)
   181	    ap.add_argument("--n_perm", type=int, default=10000)
   182	    args = ap.parse_args()
   183	
   184	    items_a = _load(args.results)
   185	    report = {
   186	        "system_a": args.results,
   187	        "macro_auroc": macro_auroc(items_a),
   188	        "macro_bootstrap_ci_95": bootstrap_macro_ci(items_a, n_boot=args.n_boot),
   189	        "per_domain_ci_95": bootstrap_ci_per_domain(items_a, n_boot=args.n_boot),
   190	        "tool_usage": tool_usage_stats(items_a),
   191	    }
   192	    if args.compare_to:
   193	        items_b = _load(args.compare_to)
   194	        report["system_b"] = args.compare_to
   195	        report["macro_auroc_b"] = macro_auroc(items_b)
   196	        report["paired_permutation_a_minus_b"] = paired_permutation_test(
   197	            items_a, items_b, n_perm=args.n_perm)
   198	
   199	    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
   200	    with open(args.out_json, "w") as f:
   201	        json.dump(report, f, indent=2)
   202	    print(json.dumps(report, indent=2))
   203	
   204	
   205	if __name__ == "__main__":
   206	    main()

exec
/bin/bash -lc "nl -ba benchmark/scripts/compose_ensemble.py | sed -n '1,130p'" in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
     1	"""compose_ensemble.py — produce the ensemble score from cached results.
     2	
     3	Usage:
     4	  python benchmark/scripts/compose_ensemble.py \
     5	    --direct benchmark/results/v6_direct_qwen3_test.json \
     6	    --agent  benchmark/results/v6_5_agent_qwen3_test.json \
     7	    --output benchmark/results/v6_ensemble_qwen3_test.json \
     8	    --alpha 0.5
     9	
    10	Output is a standard result JSON whose `anomaly_score` is:
    11	    alpha * direct + (1 - alpha) * agent
    12	indexed by item_id. Items missing from one side fall back to the other.
    13	
    14	This is the "integrated" ensemble from the user's perspective: a single
    15	command that takes the two independent system outputs and composes the
    16	best-performing combination.
    17	"""
    18	from __future__ import annotations
    19	
    20	import argparse
    21	import json
    22	from pathlib import Path
    23	
    24	
    25	def _load(path: str) -> dict:
    26	    data = json.load(open(path))
    27	    if isinstance(data, dict):
    28	        data = list(data.values())
    29	    return {x["item_id"]: x for x in data if "item_id" in x}
    30	
    31	
    32	def compose(direct_path: str, agent_path: str, alpha: float = 0.5) -> list:
    33	    d_by = _load(direct_path)
    34	    a_by = _load(agent_path)
    35	    out = []
    36	    for iid in sorted(set(d_by) | set(a_by)):
    37	        dx, ax = d_by.get(iid), a_by.get(iid)
    38	        d_score = dx.get("anomaly_score") if dx else None
    39	        a_score = ax.get("anomaly_score") if ax else None
    40	        if d_score is not None and a_score is not None:
    41	            score = alpha * float(d_score) + (1 - alpha) * float(a_score)
    42	            source = "ensemble"
    43	        elif d_score is not None:
    44	            score = float(d_score); source = "direct_only"
    45	        elif a_score is not None:
    46	            score = float(a_score); source = "agent_only"
    47	        else:
    48	            continue
    49	        base = ax if ax else dx  # prefer agent's metadata (tools, etc.)
    50	        out.append({
    51	            **{k: base.get(k) for k in ("item_id", "domain_code", "label_gt")},
    52	            "anomaly_score": score,
    53	            "direct_score": d_score,
    54	            "agent_score": a_score,
    55	            "alpha": alpha,
    56	            "source": source,
    57	            "n_turns": base.get("n_turns"),
    58	            "tools_used": base.get("tools_used"),
    59	            "rationale": base.get("rationale"),
    60	        })
    61	    return out
    62	
    63	
    64	def main():
    65	    ap = argparse.ArgumentParser()
    66	    ap.add_argument("--direct", required=True)
    67	    ap.add_argument("--agent", required=True)
    68	    ap.add_argument("--output", required=True)
    69	    ap.add_argument("--alpha", type=float, default=0.5,
    70	                    help="weight on direct (0..1); default 0.5")
    71	    args = ap.parse_args()
    72	
    73	    out = compose(args.direct, args.agent, args.alpha)
    74	    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    75	    with open(args.output, "w") as f:
    76	        json.dump(out, f)
    77	    print(f"Wrote {len(out)} ensemble results → {args.output}")
    78	    # Quick macro
    79	    try:
    80	        import sys as _s
    81	        _s.path.insert(0, str(Path(__file__).parent))
    82	        from eval_v6 import macro_auroc
    83	        m = macro_auroc(out)
    84	        print(f"Macro AUROC = {m['macro']:.4f}  (n={m['n_items']}, "
    85	              f"domains={m['n_domains']})")
    86	    except Exception as e:
    87	        print(f"(macro eval skipped: {e})")
    88	
    89	
    90	if __name__ == "__main__":
    91	    main()

exec
/bin/bash -lc "nl -ba benchmark/scripts/agent_v6_5.py | sed -n '1,120p'" in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
     1	"""AnomalyClaw v6.5 — B-regime agent with v6's free-score output.
     2	
     3	Combines:
     4	  - v6.4's message builder (injects domain hint)
     5	  - v6's SYSTEM_PROMPT (free-form `score` 0..1 output — NOT score_from_v0)
     6	  - v6's _parse_action (expects `score` not `label+confidence`)
     7	
     8	Rationale: score_from_v0 maps label+confidence to near-bimodal scores
     9	(~80% of items pinned to <0.1 or >0.9), which hurts AUROC vs v6's smoother
    10	distribution.
    11	"""
    12	from __future__ import annotations
    13	
    14	import sys
    15	from pathlib import Path
    16	
    17	sys.path.insert(0, str(Path(__file__).parent))
    18	
    19	# Use v6 prompt as-is
    20	import agent_prompt_v6 as _p6  # unchanged
    21	
    22	import agent_v6 as mod  # noqa: E402
    23	from infer import DOMAIN_CONTEXT, text_msg, img_msg, load_and_encode  # noqa: E402
    24	
    25	SYSTEM_PROMPT = _p6.SYSTEM_PROMPT
    26	
    27	
    28	def _build_init_v65(self, query_path, ref_paths, _domain_code):
    29	    ctx_text = DOMAIN_CONTEXT.get(_domain_code, "an image")
    30	    user_parts = [
    31	        text_msg(f"DOMAIN: {ctx_text}"),
    32	        text_msg("NORMAL REFERENCE IMAGES:"),
    33	    ]
    34	    for rp in ref_paths[:4]:
    35	        user_parts.append(img_msg(load_and_encode(rp)))
    36	    user_parts.append(text_msg("QUERY IMAGE:"))
    37	    user_parts.append(img_msg(load_and_encode(query_path)))
    38	    user_parts.append(text_msg(f"Turn 1/{self.K}. Decide your next action."))
    39	    return [
    40	        {"role": "system", "content": SYSTEM_PROMPT},
    41	        {"role": "user", "content": user_parts},
    42	    ]
    43	
    44	
    45	_orig_run = mod.ReActAgent.run
    46	def run_v65(self, item_id, query_path, ref_paths, split, domain_code=None):
    47	    original_builder = self._build_initial_messages
    48	    self._build_initial_messages = lambda qp, rp: _build_init_v65(self, qp, rp, domain_code)
    49	    try:
    50	        return _orig_run(self, item_id=item_id, query_path=query_path,
    51	                         ref_paths=ref_paths, split=split,
    52	                         domain_code=domain_code)
    53	    finally:
    54	        self._build_initial_messages = original_builder
    55	
    56	mod.ReActAgent.run = run_v65
    57	
    58	from agent_v6 import main  # noqa: E402
    59	
    60	if __name__ == "__main__":
    61	    main()

exec
/bin/bash -lc "nl -ba benchmark/scripts/agent_v6_6.py | sed -n '1,280p'" in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
     1	"""AnomalyClaw v6.6 — self-ensemble agent.
     2	
     3	Elegant replacement for post-hoc `0.5*(direct + agent)`:
     4	  * On turn 1 the VLM emits an `initial_score` (its gut call) alongside
     5	    the regular action. This is equivalent to the Direct VLM's output.
     6	  * After optional tool rounds, the VLM emits a `final_score`.
     7	  * The system blends: `anomaly_score = 0.5 * (initial_score + final_score)`.
     8	
     9	The agent's exported `anomaly_score` IS the ensemble. No external step.
    10	
    11	CLI identical to `agent_v6.py`.
    12	"""
    13	from __future__ import annotations
    14	
    15	import json
    16	import sys
    17	from pathlib import Path
    18	
    19	sys.path.insert(0, str(Path(__file__).parent))
    20	
    21	# Register v6.6 prompt BEFORE importing v6
    22	import agent_prompt_v6_6 as _p66
    23	import agent_prompt_v6 as _p6
    24	_p6.SYSTEM_PROMPT = _p66.SYSTEM_PROMPT
    25	_p6.TOOL_CATALOG = _p66.TOOL_CATALOG
    26	_p6.forced_final_prompt = _p66.forced_final_prompt
    27	_p6.budget_warning_prompt = _p66.budget_warning_prompt
    28	
    29	import agent_v6 as mod  # noqa: E402
    30	from agent_v6 import AgentResult  # noqa: E402
    31	from infer import (  # noqa: E402
    32	    DOMAIN_CONTEXT, call_llm, extract_json, img_msg, load_and_encode, text_msg,
    33	)
    34	
    35	
    36	def _build_init_v66(self, query_path, ref_paths, _domain_code):
    37	    """Same as v6.4 builder: inject DOMAIN_CONTEXT at top of user message."""
    38	    ctx_text = DOMAIN_CONTEXT.get(_domain_code, "an image")
    39	    user_parts = [
    40	        text_msg(f"DOMAIN: {ctx_text}"),
    41	        text_msg("NORMAL REFERENCE IMAGES:"),
    42	    ]
    43	    for rp in ref_paths[:4]:
    44	        user_parts.append(img_msg(load_and_encode(rp)))
    45	    user_parts.append(text_msg("QUERY IMAGE:"))
    46	    user_parts.append(img_msg(load_and_encode(query_path)))
    47	    user_parts.append(text_msg(f"Turn 1/{self.K}. Remember: on turn 1 include "
    48	                                "`initial_score`. Decide next action."))
    49	    return [
    50	        {"role": "system", "content": _p66.SYSTEM_PROMPT},
    51	        {"role": "user", "content": user_parts},
    52	    ]
    53	
    54	
    55	def _parse_action_v66(self, text, *, require_initial: bool = False):
    56	    """Like v6's parse_action, but also extract `initial_score` if present
    57	    (used only on turn 1)."""
    58	    parsed = extract_json(text)
    59	    if not isinstance(parsed, dict):
    60	        return None
    61	    action = parsed.get("action")
    62	    if action not in ("call_tool", "final"):
    63	        return None
    64	    if action == "final":
    65	        s = parsed.get("score")
    66	        if s is None:
    67	            return None
    68	        try:
    69	            parsed["score"] = float(s)
    70	        except (TypeError, ValueError):
    71	            return None
    72	    else:
    73	        if not parsed.get("tool"):
    74	            return None
    75	    if require_initial:
    76	        init = parsed.get("initial_score")
    77	        if init is None:
    78	            return None
    79	        try:
    80	            parsed["initial_score"] = float(init)
    81	        except (TypeError, ValueError):
    82	            return None
    83	    return parsed
    84	
    85	
    86	def run_v66(self, item_id: str, query_path: str, ref_paths: list,
    87	            split: str, domain_code: str | None = None) -> AgentResult:
    88	    """ReAct loop that also tracks `initial_score` from turn 1 and blends
    89	    it with `final_score` to form the ensemble output."""
    90	    ctx = {
    91	        "query_path": query_path,
    92	        "ref_paths": ref_paths,
    93	        "item_id": item_id,
    94	        "split": split,
    95	        "vlm_client": self.client,
    96	        "vlm_model": self.model,
    97	        "llm_client": self.client,
    98	        "llm_model": self.model,
    99	        "_manifest_domain": domain_code,
   100	    }
   101	    messages = _build_init_v66(self, query_path, ref_paths, domain_code)
   102	    history, tools_used = [], []
   103	    initial_score: float | None = None
   104	
   105	    for turn in range(1, self.K + 1):
   106	        first_turn = (turn == 1)
   107	        # Turn 1 must include initial_score
   108	        attempts = 1 + self.json_retries
   109	        cur = list(messages)
   110	        parsed = None
   111	        for _ in range(attempts):
   112	            try:
   113	                text, _, _ = call_llm(self.client, self.model, cur,
   114	                                      max_tokens=self.max_tokens,
   115	                                      temperature=0.0)
   116	            except Exception:
   117	                break
   118	            parsed = _parse_action_v66(self, text, require_initial=first_turn)
   119	            if parsed is not None:
   120	                break
   121	            cur = cur + [{
   122	                "role": "user",
   123	                "content": (
   124	                    "Your last response was not valid JSON. Return one JSON "
   125	                    "object with the required fields" +
   126	                    (" INCLUDING `initial_score`." if first_turn else ".")
   127	                ),
   128	            }]
   129	
   130	        if parsed is None:
   131	            return AgentResult(
   132	                item_id=item_id, score=0.5, rationale="json parse failed",
   133	                n_turns=turn, tools_used=tools_used, history=history,
   134	                confidence=0, error="malformed JSON after retries",
   135	            )
   136	
   137	        if first_turn:
   138	            initial_score = float(parsed["initial_score"])
   139	
   140	        if parsed["action"] == "final":
   141	            final_score = max(0.0, min(1.0, float(parsed["score"])))
   142	            # Ensemble
   143	            ensemble = (
   144	                0.5 * (initial_score + final_score)
   145	                if initial_score is not None else final_score
   146	            )
   147	            r = AgentResult(
   148	                item_id=item_id,
   149	                score=ensemble,
   150	                rationale=str(parsed.get("rationale", ""))[:500],
   151	                n_turns=turn, tools_used=tools_used,
   152	                history=history + [{"turn": turn, "action": "final",
   153	                                    "initial_score": initial_score,
   154	                                    "final_score": final_score,
   155	                                    "ensemble_score": ensemble,
   156	                                    "rationale": parsed.get("rationale", "")[:200]}],
   157	                confidence=int(parsed.get("confidence", 0) or 0),
   158	            )
   159	            return r
   160	
   161	        # Forced final at t=K
   162	        if turn == self.K:
   163	            messages.append({"role": "assistant",
   164	                             "content": json.dumps({"action": parsed["action"],
   165	                                                    "tool": parsed.get("tool")})})
   166	            messages.append({"role": "user",
   167	                             "content": _p66.forced_final_prompt(self.K)})
   168	            # Call one more time for a forced final
   169	            try:
   170	                text, _, _ = call_llm(self.client, self.model, messages,
   171	                                      max_tokens=self.max_tokens,
   172	                                      temperature=0.0)
   173	                forced = _parse_action_v66(self, text, require_initial=False)
   174	            except Exception:
   175	                forced = None
   176	            if forced and forced.get("action") == "final":
   177	                final_score = max(0.0, min(1.0, float(forced["score"])))
   178	                ensemble = (0.5 * (initial_score + final_score)
   179	                            if initial_score is not None else final_score)
   180	                return AgentResult(
   181	                    item_id=item_id,
   182	                    score=ensemble,
   183	                    rationale=str(forced.get("rationale", ""))[:500],
   184	                    n_turns=self.K, tools_used=tools_used,
   185	                    history=history + [{"turn": turn, "action": "forced_final",
   186	                                        "initial_score": initial_score,
   187	                                        "final_score": final_score,
   188	                                        "ensemble_score": ensemble}],
   189	                    confidence=int(forced.get("confidence", 0) or 0),
   190	                )
   191	            return AgentResult(
   192	                item_id=item_id,
   193	                score=initial_score if initial_score is not None else 0.5,
   194	                rationale="forced-final failed; fell back to initial_score",
   195	                n_turns=self.K, tools_used=tools_used, history=history,
   196	                confidence=0, error="forced-final produced non-final",
   197	            )
   198	
   199	        # Execute tool
   200	        tool_name = parsed["tool"]
   201	        tool_args = parsed.get("args") or {}
   202	        from agent_tools_v6 import dispatch_tool
   203	        observation = dispatch_tool(tool_name, tool_args, ctx)
   204	        tools_used.append(tool_name)
   205	        history.append({"turn": turn, "action": "call_tool", "tool": tool_name,
   206	                        "obs_keys": list(observation.keys()),
   207	                        "obs_error": observation.get("error")})
   208	        if tool_name == "tool_expert_score":
   209	            ctx["_expert_patches"] = observation.get("top_patches", [])
   210	
   211	        obs_parts = []
   212	        obs_text = mod._obs_to_text(observation)
   213	        obs_parts.append(text_msg(f"OBSERVATION from {tool_name}: {obs_text}"))
   214	        for img_key in ("crop_b64", "diff_mask_b64", "aligned_diff_b64",
   215	                        "composite_b64"):
   216	            if observation.get(img_key):
   217	                obs_parts.append(img_msg(observation[img_key]))
   218	        if observation.get("tiles"):
   219	            for t in observation["tiles"][:9]:
   220	                obs_parts.append(img_msg(t["crop_b64"]))
   221	        remaining = self.K - turn
   222	        obs_parts.append(text_msg(
   223	            f"Turn {turn+1}/{self.K}. "
   224	            f"{_p66.budget_warning_prompt(remaining)}\n"
   225	            "Decide your next action."))
   226	        messages.append({"role": "assistant",
   227	                         "content": json.dumps({"action": parsed["action"],
   228	                                                "tool": parsed.get("tool")})})
   229	        messages.append({"role": "user", "content": obs_parts})
   230	
   231	    # Should not reach
   232	    return AgentResult(
   233	        item_id=item_id, score=initial_score or 0.5,
   234	        rationale="loop exhausted", n_turns=self.K, tools_used=tools_used,
   235	        history=history, confidence=0, error="loop exhausted",
   236	    )
   237	
   238	
   239	mod.ReActAgent.run = run_v66
   240	
   241	from agent_v6 import main  # noqa: E402
   242	
   243	if __name__ == "__main__":
   244	    main()

exec
/bin/bash -lc "nl -ba benchmark/scripts/agent_v6_7.py | sed -n '1,240p'" in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
     1	"""AnomalyClaw v6.7 — agent with integrated Direct + ReAct ensemble.
     2	
     3	Unified runner: produces one result JSON whose `anomaly_score` is already
     4	the ensemble of Direct and Agent final.
     5	
     6	Direct source (controlled by --direct_cache):
     7	  - If --direct_cache <path> is given AND the file exists, reads each item's
     8	    direct score from there (no extra API call → rate-limit safe).
     9	  - Otherwise, performs a fresh Direct VLM call per item as "turn 0"
    10	    BEFORE running ReAct. Be aware on API backends this doubles your
    11	    request rate; use `--max_workers` half of what you'd give pure agent.
    12	
    13	The exported `anomaly_score` = 0.5 * (direct_score + agent_final_score).
    14	If either is missing, falls back to the one available.
    15	"""
    16	from __future__ import annotations
    17	
    18	import argparse
    19	import json
    20	import os
    21	import sys
    22	import time
    23	from concurrent.futures import ThreadPoolExecutor, as_completed
    24	from pathlib import Path
    25	
    26	sys.path.insert(0, str(Path(__file__).parent))
    27	
    28	import agent_prompt_v6 as _p6
    29	
    30	import agent_v6 as mod  # noqa: E402
    31	from agent_v6 import ReActAgent, AgentResult, _summarise, _obs_to_text  # noqa: E402
    32	from infer import (  # noqa: E402
    33	    DOMAIN_CONTEXT, build_prompt_v0, call_llm, extract_json, get_client,
    34	    get_model_name, img_msg, load_and_encode, score_from_v0, text_msg,
    35	)
    36	
    37	SYSTEM_PROMPT = _p6.SYSTEM_PROMPT
    38	
    39	
    40	def _build_init_v67(self, query_path, ref_paths, _domain_code):
    41	    ctx_text = DOMAIN_CONTEXT.get(_domain_code, "an image")
    42	    user_parts = [
    43	        text_msg(f"DOMAIN: {ctx_text}"),
    44	        text_msg("NORMAL REFERENCE IMAGES:"),
    45	    ]
    46	    for rp in ref_paths[:4]:
    47	        user_parts.append(img_msg(load_and_encode(rp)))
    48	    user_parts.append(text_msg("QUERY IMAGE:"))
    49	    user_parts.append(img_msg(load_and_encode(query_path)))
    50	    user_parts.append(text_msg(f"Turn 1/{self.K}. Decide your next action."))
    51	    return [
    52	        {"role": "system", "content": SYSTEM_PROMPT},
    53	        {"role": "user", "content": user_parts},
    54	    ]
    55	
    56	
    57	def _direct_turn0_call(client, model, query_path, ref_paths, domain_code,
    58	                       max_retries: int = 2) -> float | None:
    59	    for attempt in range(max_retries + 1):
    60	        try:
    61	            messages = [
    62	                {"role": "system",
    63	                 "content": "You are a visual anomaly inspector. Return JSON only."},
    64	                {"role": "user", "content": (
    65	                    [text_msg(build_prompt_v0(domain_code or "D?", has_refs=True))] +
    66	                    [img_msg(load_and_encode(p)) for p in ref_paths[:4]] +
    67	                    [text_msg("QUERY:"), img_msg(load_and_encode(query_path))]
    68	                )},
    69	            ]
    70	            text, _, _ = call_llm(client, model, messages,
    71	                                  max_tokens=500, temperature=0.0)
    72	            parsed = extract_json(text)
    73	            if parsed is None:
    74	                if attempt < max_retries:
    75	                    time.sleep(2 ** attempt)
    76	                    continue
    77	                return None
    78	            return float(score_from_v0(parsed))
    79	        except Exception:
    80	            if attempt < max_retries:
    81	                time.sleep(2 ** attempt)
    82	                continue
    83	            return None
    84	    return None
    85	
    86	
    87	# Re-bind the builder on each run
    88	_orig_run = mod.ReActAgent.run
    89	
    90	
    91	def _run_ensemble(self, item_id, query_path, ref_paths, split, domain_code,
    92	                  direct_score_cached):
    93	    # Turn 0: Direct VLM (cached or fresh)
    94	    if direct_score_cached is not None:
    95	        direct_score = direct_score_cached
    96	    else:
    97	        direct_score = _direct_turn0_call(
    98	            self.client, self.model, query_path, ref_paths, domain_code)
    99	
   100	    # Turn 1..K: ReAct
   101	    original_builder = self._build_initial_messages
   102	    self._build_initial_messages = lambda qp, rp: _build_init_v67(
   103	        self, qp, rp, domain_code)
   104	    try:
   105	        r = _orig_run(self, item_id=item_id, query_path=query_path,
   106	                      ref_paths=ref_paths, split=split,
   107	                      domain_code=domain_code)
   108	    finally:
   109	        self._build_initial_messages = original_builder
   110	
   111	    agent_score = r.score
   112	    # Blend; fall back gracefully
   113	    if direct_score is not None and r.error is None:
   114	        ensemble = 0.5 * (direct_score + agent_score)
   115	    elif direct_score is not None:  # agent errored
   116	        ensemble = direct_score
   117	    else:  # direct failed
   118	        ensemble = agent_score
   119	    r.score = float(max(0.0, min(1.0, ensemble)))
   120	    return r, direct_score
   121	
   122	
   123	def main():
   124	    ap = argparse.ArgumentParser()
   125	    ap.add_argument("--manifest", required=True)
   126	    ap.add_argument("--split", choices=["calibration", "test"], required=True)
   127	    ap.add_argument("--backend", choices=["qwen3", "seedvl", "gpt"], required=True)
   128	    ap.add_argument("--output", required=True)
   129	    ap.add_argument("--direct_cache", default=None,
   130	                    help="path to a v6_direct_*_test.json — if set, load direct "
   131	                         "scores from there instead of calling VLM.")
   132	    ap.add_argument("--domains", nargs="*", default=None)
   133	    ap.add_argument("--max_turns", type=int, default=5)
   134	    ap.add_argument("--max_workers", type=int, default=8)
   135	    ap.add_argument("--max_items", type=int, default=0)
   136	    args = ap.parse_args()
   137	
   138	    items = json.load(open(args.manifest))
   139	    items = [x for x in items if x.get("split") == args.split]
   140	    if args.domains:
   141	        items = [x for x in items if x.get("domain_code") in args.domains]
   142	    if args.max_items:
   143	        items = items[:args.max_items]
   144	
   145	    direct_cache = {}
   146	    if args.direct_cache and os.path.exists(args.direct_cache):
   147	        raw = json.load(open(args.direct_cache))
   148	        for x in (raw if isinstance(raw, list) else list(raw.values())):
   149	            iid = x.get("item_id")
   150	            s = x.get("anomaly_score")
   151	            if iid is not None and s is not None:
   152	                direct_cache[iid] = float(s)
   153	        print(f"[cache] loaded {len(direct_cache)} cached direct scores")
   154	
   155	    client = get_client(args.backend)
   156	    model = get_model_name(args.backend)
   157	    agent = ReActAgent(vlm_client=client, vlm_model=model,
   158	                       max_turns=args.max_turns)
   159	
   160	    results = []
   161	    t0 = time.time()
   162	
   163	    def _run_one(x):
   164	        try:
   165	            r, ds = _run_ensemble(
   166	                agent, x["item_id"], x["query_path"], x["ref_paths"],
   167	                args.split, x.get("domain_code"),
   168	                direct_cache.get(x["item_id"]))
   169	            return {
   170	                "item_id": x["item_id"], "domain_code": x.get("domain_code"),
   171	                "label_gt": x.get("label"), "anomaly_score": r.score,
   172	                "direct_score": ds,
   173	                "agent_final_score": None if r.error else r.score,  # actually agent score pre-blend; override below
   174	                "rationale": r.rationale, "n_turns": r.n_turns,
   175	                "tools_used": r.tools_used, "confidence": r.confidence,
   176	                "error": r.error,
   177	            }
   178	        except Exception as e:
   179	            return {"item_id": x["item_id"], "domain_code": x.get("domain_code"),
   180	                    "label_gt": x.get("label"), "anomaly_score": 0.5,
   181	                    "n_turns": 0, "tools_used": [], "confidence": 0,
   182	                    "error": f"{type(e).__name__}: {e}"}
   183	
   184	    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
   185	    with ThreadPoolExecutor(max_workers=args.max_workers) as ex:
   186	        futures = [ex.submit(_run_one, x) for x in items]
   187	        for i, fut in enumerate(as_completed(futures)):
   188	            results.append(fut.result())
   189	            if (i + 1) % 25 == 0:
   190	                with open(args.output, "w") as f:
   191	                    json.dump(results, f)
   192	                print(f"[{i+1}/{len(items)}] {time.time()-t0:.1f}s  "
   193	                      f"written={len(results)}", flush=True)
   194	
   195	    with open(args.output, "w") as f:
   196	        json.dump(results, f)
   197	    print(f"Wrote {len(results)} results → {args.output}")
   198	
   199	
   200	if __name__ == "__main__":
   201	    main()

exec
/bin/bash -lc "nl -ba benchmark/scripts/run_baselines_v6.py | sed -n '1,180p'" in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
     1	"""Run the two v6 baselines: Direct VLM and Fixed-fusion (w=0.2, SubspaceAD).
     2	
     3	Protocol:
     4	  * Direct: build_prompt_v0 + run per item, record anomaly_score from score_from_v0.
     5	  * Fixed-fusion: 0.8 * direct_score + 0.2 * sigmoid(expert, calibration-median).
     6	  * NO per-domain tuning; NO test-split access beyond the prediction itself.
     7	"""
     8	from __future__ import annotations
     9	
    10	import argparse
    11	import json
    12	import os
    13	import sys
    14	import time
    15	from concurrent.futures import ThreadPoolExecutor, as_completed
    16	from pathlib import Path
    17	
    18	import numpy as np
    19	
    20	sys.path.insert(0, str(Path(__file__).parent))
    21	
    22	from infer import (  # noqa: E402
    23	    build_prompt_v0, call_llm, extract_json, get_client, get_model_name,
    24	    img_msg, load_and_encode, score_from_v0, text_msg,
    25	)
    26	from agent_tools_v6 import _load_expert_scores  # noqa: E402
    27	
    28	
    29	def run_direct_item(client, model, item: dict) -> dict:
    30	    messages = [
    31	        {"role": "system",
    32	         "content": "You are a visual anomaly inspector. Return JSON only."},
    33	        {"role": "user", "content": (
    34	            [text_msg(build_prompt_v0(item.get("domain_code", "D?"),
    35	                                      has_refs=True))] +
    36	            [img_msg(load_and_encode(p)) for p in item.get("ref_paths", [])[:4]] +
    37	            [text_msg("QUERY:"), img_msg(load_and_encode(item["query_path"]))]
    38	        )},
    39	    ]
    40	    try:
    41	        text, _, _ = call_llm(client, model, messages,
    42	                              max_tokens=500, temperature=0.0)
    43	        parsed = extract_json(text)
    44	        score = score_from_v0(parsed)
    45	        return {"item_id": item["item_id"],
    46	                "domain_code": item.get("domain_code"),
    47	                "label_gt": item.get("label"),
    48	                "anomaly_score": float(score),
    49	                "raw_output": parsed, "error": None}
    50	    except Exception as e:
    51	        return {"item_id": item["item_id"],
    52	                "domain_code": item.get("domain_code"),
    53	                "label_gt": item.get("label"),
    54	                "anomaly_score": 0.5,
    55	                "raw_output": None,
    56	                "error": f"{type(e).__name__}: {e}"}
    57	
    58	
    59	def load_calibration_median(expert: str = "subspacead") -> float:
    60	    _, all_scores = _load_expert_scores(expert, "calibration")
    61	    if len(all_scores) == 0:
    62	        return 1.0
    63	    return float(np.median(all_scores))
    64	
    65	
    66	def fuse(direct_score: float, expert_score: float | None,
    67	         median: float, w: float = 0.2) -> float:
    68	    if expert_score is None:
    69	        return float(direct_score)
    70	    sig = 1.0 / (1.0 + np.exp(-2.0 * (expert_score - median)
    71	                              / max(median, 1e-6)))
    72	    return float((1 - w) * direct_score + w * sig)
    73	
    74	
    75	def main():
    76	    ap = argparse.ArgumentParser()
    77	    ap.add_argument("--manifest", required=True)
    78	    ap.add_argument("--split", choices=["calibration", "test"], required=True)
    79	    ap.add_argument("--backend", choices=["qwen3", "seedvl", "gpt"], required=True)
    80	    ap.add_argument("--output_dir", required=True)
    81	    ap.add_argument("--domains", nargs="*", default=None)
    82	    ap.add_argument("--max_items", type=int, default=0)
    83	    ap.add_argument("--max_workers", type=int, default=8)
    84	    ap.add_argument("--resume", action="store_true")
    85	    args = ap.parse_args()
    86	
    87	    items = json.load(open(args.manifest))
    88	    items = [x for x in items if x.get("split") == args.split]
    89	    if args.domains:
    90	        items = [x for x in items if x.get("domain_code") in args.domains]
    91	    if args.max_items:
    92	        items = items[:args.max_items]
    93	
    94	    client = get_client(args.backend)
    95	    model = get_model_name(args.backend)
    96	    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    97	    direct_path = Path(args.output_dir) / f"v6_direct_{args.backend}_{args.split}.json"
    98	
    99	    # Resume?
   100	    direct_out = []
   101	    if args.resume and direct_path.exists():
   102	        direct_out = json.load(open(direct_path))
   103	        done = {r["item_id"] for r in direct_out if r.get("error") is None}
   104	        items = [x for x in items if x["item_id"] not in done]
   105	        print(f"[resume] {len(done)} items already complete; {len(items)} remaining")
   106	
   107	    print(f"[Direct] {len(items)} items to process", flush=True)
   108	    t0 = time.time()
   109	    with ThreadPoolExecutor(max_workers=args.max_workers) as ex:
   110	        futs = [ex.submit(run_direct_item, client, model, x) for x in items]
   111	        for i, f in enumerate(as_completed(futs)):
   112	            direct_out.append(f.result())
   113	            if (i + 1) % 50 == 0:
   114	                with open(direct_path, "w") as fh:
   115	                    json.dump(direct_out, fh)
   116	                print(f"  [{i+1}/{len(items)}] {time.time()-t0:.1f}s  "
   117	                      f"written={len(direct_out)}", flush=True)
   118	
   119	    with open(direct_path, "w") as f:
   120	        json.dump(direct_out, f)
   121	    print(f"Wrote {direct_path}")
   122	
   123	    # Fixed-fusion
   124	    median = load_calibration_median()
   125	    expert_recs, _ = _load_expert_scores("subspacead", args.split)
   126	    fusion_out = []
   127	    for r in direct_out:
   128	        expert = expert_recs.get(r["item_id"], {}).get("anomaly_score")
   129	        fused = fuse(r["anomaly_score"], expert, median, w=0.2)
   130	        fusion_out.append({**r, "anomaly_score": fused,
   131	                           "direct_score_orig": r["anomaly_score"],
   132	                           "expert_score": expert,
   133	                           "fusion_w": 0.2, "fusion_median": median})
   134	
   135	    fusion_path = Path(args.output_dir) / f"v6_fusion_{args.backend}_{args.split}.json"
   136	    with open(fusion_path, "w") as f:
   137	        json.dump(fusion_out, f)
   138	    print(f"Wrote {fusion_path}")
   139	
   140	
   141	if __name__ == "__main__":
   142	    main()

codex
A concrete implementation risk surfaced: the v6.5/v6.7 wrappers mutate a shared `ReActAgent` method while the runner uses `ThreadPoolExecutor`, so per-item domain prompt setup is not thread-safe. I’m checking prompts and result writers next because some issues may be “metadata in output” rather than scoring leakage.
exec
/bin/bash -lc "nl -ba benchmark/scripts/agent_prompt_v6.py | sed -n '1,130p'" in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
     1	"""Agent v6 system prompt + tool catalog description.
     2	
     3	Single universal prompt across all 12 domains. No domain_code, no per-domain
     4	wording. The agent observes what's in the image and picks tools autonomously.
     5	"""
     6	from __future__ import annotations
     7	
     8	TOOL_CATALOG = """Available tools (call at most one per turn):
     9	
    10	EXPERT PROBES
    11	  tool_expert_score(expert="subspacead"|"anomalyvfm"|"patchknn"|"dinov2_global")
    12	    Returns {score, normalized_rank, interpretation, top_patches}.
    13	    rank>=0.80 => strong anomaly signal. Calling this for expert="subspacead"
    14	    also makes patch hotspots available to hotspot_cropper / component_counter.
    15	
    16	VISUAL INSPECTION
    17	  tool_hotspot_cropper(k=5)
    18	    Zooms into the top-k subspacead hotspots. Requires a prior
    19	    tool_expert_score(expert="subspacead") call.
    20	  tool_zoom_bbox(bbox=[x0,y0,x1,y1])
    21	    Agent-specified pixel crop of the query.
    22	  tool_patch_grid(rows=N, cols=M)
    23	    Cuts the query into N x M tiles (max 8 x 8).
    24	  tool_image_diff(ref_idx=0..3)
    25	    Pixel diff vs the ref_idx-th reference; returns stats + mask image.
    26	  tool_rotate_align(ref_idx=0..3)
    27	    Like image_diff but tries small rotations first (for rotated refs).
    28	  tool_side_by_side(bbox=[x0,y0,x1,y1])
    29	    Composite showing query + 4 refs all cropped to same bbox. bbox is in
    30	    256x256 normalized coords.
    31	
    32	REFERENCE UNDERSTANDING
    33	  tool_reference_profiler()
    34	    VLM describes what the 4 refs have in common (objects, colors,
    35	    variations).
    36	  tool_reference_retriever(k=4)
    37	    Re-pulls k refs more similar to the query from the domain's full
    38	    normal pool.
    39	
    40	STRUCTURAL
    41	  tool_component_counter()
    42	    Connected-component count among subspacead hotspots.
    43	  tool_segment_and_count()
    44	    Coarse 8x8 grid diff vs ref 0 — rough structural change signal.
    45	  tool_texture_fft()
    46	    Periodicity score (0=irregular, 1=strongly periodic texture).
    47	
    48	SEMANTIC
    49	  tool_domain_knowledge(question="...")
    50	    Free-form text question answered by an LLM. Phrase the question yourself.
    51	"""
    52	
    53	SYSTEM_PROMPT = f"""You are a visual anomaly detection agent.
    54	
    55	INPUT PER IMAGE: one query image, four normal reference images, a turn budget.
    56	TASK: decide if the query is normal or anomalous and output a score in [0,1]
    57	where 1 means certainly anomalous.
    58	
    59	YOU HAVE NO DOMAIN INFORMATION. Figure out what the images are from vision
    60	alone. The tools below can help you probe further.
    61	
    62	{TOOL_CATALOG}
    63	
    64	PROTOCOL: On each turn, return ONLY a JSON object:
    65	{{
    66	  "thought":  "<one or two sentences>",
    67	  "action":   "call_tool" | "final",
    68	  "tool":     "<tool_name>" | null,
    69	  "args":     {{ ... }} | null,
    70	  "confidence": <integer 0..100>,
    71	  "score":    <float 0..1> | null,
    72	  "rationale": "<one or two sentences>" | null
    73	}}
    74	
    75	Required if action=="final": score and rationale.
    76	Required if action=="call_tool": tool and args.
    77	
    78	GUIDELINES:
    79	- Use a tool only if it will change your answer. If the query already looks
    80	  clearly normal or clearly anomalous against the references, output final
    81	  at turn 1 without calling any tool.
    82	- Each tool call costs one turn. Budget is tight; do not chain tools
    83	  speculatively.
    84	- Return valid JSON only. No prose outside the JSON.
    85	"""
    86	
    87	
    88	def forced_final_prompt(budget: int) -> str:
    89	    return (
    90	        f"THIS IS YOUR LAST TURN ({budget}/{budget}). "
    91	        f"action MUST be \"final\". Produce your best score and rationale "
    92	        f"based on all observations so far."
    93	    )
    94	
    95	
    96	def budget_warning_prompt(remaining: int) -> str:
    97	    if remaining <= 1:
    98	        return "1 turn remaining — prepare to produce final."
    99	    return f"{remaining} turns remaining."

exec
/bin/bash -lc "nl -ba benchmark/scripts/agent_prompt_v6_6.py | sed -n '1,140p'" in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
     1	"""Agent v6.6 prompt — self-ensemble.
     2	
     3	Agent emits an `initial_score` on turn 1 (its free-form gut judgment,
     4	same calibration as Direct) AND a `final_score` after all tool rounds.
     5	The system internally blends them as 0.5 * (initial + final), eliminating
     6	the need for post-hoc external averaging.
     7	
     8	Other design:
     9	- B-regime: DOMAIN_CONTEXT[d] is injected by the runner.
    10	- Free-form score in [0, 1] (v6 style) — no score_from_v0 bimodalization.
    11	"""
    12	from __future__ import annotations
    13	
    14	TOOL_CATALOG = """Available tools (call at most one per turn):
    15	
    16	EXPERT PROBES — noisy on semantic change, natural scenes, medical intensity.
    17	  tool_expert_score(expert="subspacead"|"anomalyvfm"|"patchknn"|"dinov2_global")
    18	
    19	VISUAL
    20	  tool_hotspot_cropper(k=5), tool_zoom_bbox(bbox), tool_patch_grid(rows,cols)
    21	  tool_image_diff(ref_idx), tool_rotate_align(ref_idx), tool_side_by_side(bbox)
    22	
    23	REFERENCE
    24	  tool_reference_profiler(), tool_reference_retriever(k=4)
    25	
    26	STRUCTURAL
    27	  tool_component_counter(), tool_segment_and_count(), tool_texture_fft()
    28	
    29	SEMANTIC
    30	  tool_domain_knowledge(question)
    31	"""
    32	
    33	SYSTEM_PROMPT = f"""You are a visual anomaly detection agent.
    34	
    35	INPUT: query image, 4 normal reference images, a one-sentence domain
    36	description, a turn budget.
    37	TASK: decide if the query is normal or anomalous — output a score in [0,1]
    38	where 1 means certainly anomalous.
    39	
    40	{TOOL_CATALOG}
    41	
    42	PROTOCOL. Every turn return ONE JSON object.
    43	
    44	**On turn 1, the JSON MUST include an `initial_score` field — your gut
    45	judgment of the anomaly score based purely on the images, BEFORE calling
    46	any tool.** This initial score is logged and later averaged with your
    47	final score to form the system's prediction.
    48	
    49	Turn 1 examples:
    50	
    51	Calling a tool on turn 1:
    52	{{
    53	  "thought": "<1-2 sentences>",
    54	  "initial_score": <float 0.0-1.0>,
    55	  "action": "call_tool",
    56	  "tool": "<tool_name>",
    57	  "args": {{ ... }},
    58	  "confidence": <integer 0-100>
    59	}}
    60	
    61	Deciding on turn 1 (no tools):
    62	{{
    63	  "thought": "<1-2 sentences>",
    64	  "initial_score": <float 0.0-1.0>,
    65	  "action": "final",
    66	  "score": <float 0.0-1.0>,
    67	  "rationale": "<1-2 sentences>",
    68	  "confidence": <integer 0-100>
    69	}}
    70	
    71	On later turns (t >= 2), omit `initial_score`.
    72	
    73	Calling a tool on turn 2+:
    74	{{
    75	  "thought": "<1-2 sentences>",
    76	  "action": "call_tool",
    77	  "tool": "<tool_name>",
    78	  "args": {{ ... }},
    79	  "confidence": <integer 0-100>
    80	}}
    81	
    82	Final on turn 2+:
    83	{{
    84	  "thought": "<1-2 sentences>",
    85	  "action": "final",
    86	  "score": <float 0.0-1.0>,
    87	  "rationale": "<1-2 sentences>",
    88	  "confidence": <integer 0-100>
    89	}}
    90	
    91	GUIDELINES:
    92	- Use a tool only if you genuinely need more evidence. Simple cases:
    93	  output final on turn 1 (your initial_score and score will be the same).
    94	- Expert tools (tool_expert_score) are industrial-biased — they can mislead
    95	  on medical, change-detection, or natural imagery. Trust your visual
    96	  judgment when they conflict.
    97	- If you see ambiguity, prefer mid-range scores (0.3-0.7) rather than
    98	  extremes — your initial_score should reflect genuine uncertainty.
    99	- Return valid JSON only. No prose outside the JSON.
   100	"""
   101	
   102	
   103	def forced_final_prompt(budget: int) -> str:
   104	    return (f"THIS IS YOUR LAST TURN ({budget}/{budget}). "
   105	            f"action MUST be \"final\". Return {{action, score, confidence, rationale}}.")
   106	
   107	
   108	def budget_warning_prompt(remaining: int) -> str:
   109	    return ("1 turn remaining — prepare to produce final."
   110	            if remaining <= 1 else f"{remaining} turns remaining.")

exec
/bin/bash -lc "nl -ba benchmark/scripts/infer.py | sed -n '450,630p'" in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
   450	        try:
   451	            return json.loads(m.group(0))
   452	        except Exception:
   453	            pass
   454	    return None
   455	
   456	
   457	# ─── Score aggregation ────────────────────────────────────────────────────────
   458	
   459	def score_from_v0(parsed: Optional[dict]) -> float:
   460	    if not parsed:
   461	        return 0.5
   462	    label = str(parsed.get("image_label", "")).lower()
   463	    conf = float(parsed.get("confidence", 0.5))
   464	    if label == "anomalous":
   465	        return max(conf, 0.5 + 1e-6)
   466	    else:
   467	        return min(1.0 - conf, 0.5 - 1e-6)
   468	
   469	
   470	def score_from_v1(parsed: Optional[dict]) -> float:
   471	    if not parsed:
   472	        return 0.5
   473	    label = str(parsed.get("image_label", "")).lower()
   474	    claims = parsed.get("claims", [])
   475	    if not claims:
   476	        return 0.1 if label == "normal" else 0.6
   477	    max_conf = max(float(c.get("confidence", 0.0)) for c in claims)
   478	    return max_conf if label == "anomalous" else 1.0 - max_conf
   479	
   480	
   481	def score_from_debate(proposer: Optional[dict], refuter: Optional[dict]) -> float:
   482	    """Aggregate a proposer/refuter debate into a single anomaly score in [0, 1].
   483	
   484	    We use a confidence-gated, factorised rule selected on the calibration slice:
   485	      - if the proposer commits to 'normal' with no claims, return 0.05
   486	        (score_from_v1 behaviour for confident-normal)
   487	      - for each claim, if the proposer confidence c is already high (c >= high_trust),
   488	        trust the proposer and take `scored = c` --- a highly confident claim should not
   489	        be punctured by a moderate refuter
   490	      - otherwise attenuate with the refuter: `scored = c * (1 - r)`
   491	        (independent-events factorisation; if refuter is sure (r=1), the claim drops to 0)
   492	      - take max over claims and clip to [0, 1]
   493	
   494	    Band (low=0.0, high=0.8) was selected by sweeping on SeedVL calibration; it
   495	    beats the raw (0.5 + (c - r)) rule on macro AUROC and is insensitive to the
   496	    low bound on this dataset.
   497	    """
   498	    if not proposer:
   499	        return 0.5
   500	    claims = proposer.get("claims", [])
   501	    if not claims:
   502	        label = str(proposer.get("image_label", "")).lower()
   503	        return 0.05 if label == "normal" else 0.6
   504	
   505	    reviews = {}
   506	    if refuter:
   507	        for r in refuter.get("reviews", []):
   508	            reviews[r.get("id")] = float(r.get("refute_confidence", 0.0))
   509	
   510	    high_trust = 0.80  # above this, trust the proposer outright
   511	    best = 0.0
   512	    for c in claims:
   513	        conf = float(c.get("confidence", 0.0))
   514	        rc = reviews.get(c.get("id", ""), 0.0)
   515	        scored = conf if conf >= high_trust else conf * (1.0 - rc)
   516	        if scored > best:
   517	            best = scored
   518	    return float(max(0.0, min(1.0, best)))
   519	
   520	
   521	def label_from_score(score: float, threshold: float = 0.5) -> int:
   522	    return 1 if score > threshold else 0
   523	
   524	
   525	# ─── Backend clients ──────────────────────────────────────────────────────────
   526	
   527	def get_client(backend: str) -> OpenAI:
   528	    if backend == "gpt":
   529	        api_key = os.environ.get("GPT_API_KEY") or os.environ.get("OPENAI_API_KEY")
   530	        base_url = os.environ.get("GPT_API_BASE") or os.environ.get("OPENAI_API_BASE")
   531	        if not api_key:
   532	            api_key = "***REDACTED-GPT-KEY***"
   533	            base_url = "http://localhost:8080/v1"
   534	        return OpenAI(api_key=api_key, base_url=base_url, timeout=120.0)
   535	    elif backend == "seedvl":
   536	        api_key = os.environ.get("SEED_API_KEY", "***REDACTED-SEED-KEY***")
   537	        base_url = os.environ.get("SEED_API_BASE", "https://ark.cn-beijing.volces.com/api/v3")
   538	        return OpenAI(api_key=api_key, base_url=base_url, timeout=120.0)
   539	    elif backend == "qwen3":
   540	        api_key = os.environ.get("QWEN_API_KEY", "EMPTY")
   541	        base_url = os.environ.get("QWEN_API_BASE", "http://localhost:8000/v1")
   542	        return OpenAI(api_key=api_key, base_url=base_url)
   543	    else:
   544	        raise ValueError(f"Unknown backend: {backend}")
   545	
   546	
   547	BACKEND_MODELS = {
   548	    "gpt": os.environ.get("GPT_MODEL", "gpt-4o"),
   549	    "seedvl": os.environ.get("SEED_MODEL", "doubao-seed-2-0-lite-260215"),
   550	    "qwen3": os.environ.get("QWEN_MODEL", "Qwen3-VL-8B-Instruct"),
   551	}
   552	
   553	
   554	def get_model_name(backend: str, batch: bool = False) -> str:
   555	    if backend == "seedvl" and batch:
   556	        return os.environ.get("SEED_BATCH_MODEL", BACKEND_MODELS["seedvl"])
   557	    return BACKEND_MODELS[backend]
   558	
   559	
   560	_SERVED_MODEL_SEEN: dict[str, int] = {}
   561	_SERVED_MODEL_LOG_PATH = os.environ.get("SERVED_MODEL_LOG", "/tmp/served_model.log")
   562	
   563	
   564	def _log_served_model(requested: str, served: str) -> None:
   565	    """First time we see a (requested, served) pair, emit a stderr line and
   566	    append to the log file. On subsequent calls just bump the counter.
   567	    """
   568	    key = f"{requested}=>{served}"
   569	    n = _SERVED_MODEL_SEEN.get(key, 0)
   570	    _SERVED_MODEL_SEEN[key] = n + 1
   571	    if n == 0:
   572	        msg = f"[served_model] requested={requested!r} served={served!r} (first time in this process)"
   573	        print(msg, file=sys.stderr, flush=True)
   574	        try:
   575	            import datetime as _dt
   576	            with open(_SERVED_MODEL_LOG_PATH, "a") as _f:
   577	                _f.write(f"{_dt.datetime.now().isoformat()} {msg} pid={os.getpid()}\n")
   578	        except Exception:
   579	            pass
   580	
   581	
   582	def get_served_model_counts() -> dict[str, int]:
   583	    """Return a snapshot of observed (requested -> served) model mappings
   584	    and the number of calls to each. Useful in post-run analysis."""
   585	    return dict(_SERVED_MODEL_SEEN)
   586	
   587	
   588	def call_llm(client: OpenAI, model: str, messages: list,
   589	             max_tokens: int = 700, temperature: float = 0.0) -> tuple[str, int, int]:
   590	    """Returns (text, input_tokens, output_tokens).
   591	    For Qwen3 thinking models served via vLLM we inject
   592	    chat_template_kwargs={enable_thinking: False} to skip the free-text
   593	    'Thinking Process' prefix which otherwise eats the max_tokens budget
   594	    before any JSON is emitted.
   595	
   596	    Side effect: logs the served model id (from resp.model) on first
   597	    unique (requested, served) pair per process, to SERVED_MODEL_LOG
   598	    env var (default /tmp/served_model.log).
   599	    """
   600	    kwargs = dict(model=model, messages=messages, max_tokens=max_tokens, temperature=temperature)
   601	    if "qwen3" in str(model).lower() or "Qwen3" in str(model):
   602	        kwargs["extra_body"] = {"chat_template_kwargs": {"enable_thinking": False}}
   603	    resp = client.chat.completions.create(**kwargs)
   604	    text = resp.choices[0].message.content or ""
   605	    usage = resp.usage
   606	    served = getattr(resp, "model", None)
   607	    if served is not None:
   608	        _log_served_model(str(model), str(served))
   609	    return text, usage.prompt_tokens, usage.completion_tokens
   610	
   611	
   612	def _ark_obj_to_dict(obj: Any) -> dict:
   613	    if obj is None:
   614	        return {}
   615	    if isinstance(obj, dict):
   616	        return obj
   617	    if hasattr(obj, "model_dump") and callable(getattr(obj, "model_dump")):
   618	        return obj.model_dump()
   619	    if hasattr(obj, "dict") and callable(getattr(obj, "dict")):
   620	        return obj.dict()
   621	    if hasattr(obj, "__dict__"):
   622	        return dict(obj.__dict__)
   623	    try:
   624	        return json.loads(json.dumps(obj))
   625	    except Exception:
   626	        return {"_raw": str(obj)}
   627	
   628	
   629	def _extract_message_text(content: Any) -> str:
   630	    if content is None:

exec
/bin/bash -lc "nl -ba benchmark/scripts/infer.py | sed -n '2290,2465p'" in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
  2290	        "label_pred": label_from_score(score_from_v0(parsed)),
  2291	        "anomaly_score": score_from_v0(parsed),
  2292	        "anomaly_type_pred": parsed.get("anomaly_type") if parsed else None,
  2293	        "raw_output": {"v4": parsed},
  2294	        "cost_tokens": {"input": inp, "output": out},
  2295	        "latency_sec": round(time.time() - t0, 2),
  2296	    }
  2297	
  2298	
  2299	ASYNC_VARIANT_FNS = {
  2300	    "v0_direct": run_v0_async,
  2301	    "v1_normal_first": run_v1_async,
  2302	    "v3_debate_1r": run_v3_async,
  2303	    "v4_fewshot": run_v4_async,
  2304	}
  2305	
  2306	
  2307	async def run_item_async(item: dict, client, model: str, variant: str) -> dict:
  2308	    fn = ASYNC_VARIANT_FNS[variant]
  2309	    base = {
  2310	        "item_id": item["item_id"],
  2311	        "domain": item["domain"],
  2312	        "domain_code": item["domain_code"],
  2313	        "label_gt": item["label"],
  2314	        "split": item["split"],
  2315	        "source_dataset": item.get("source_dataset"),
  2316	        "category": item.get("category"),
  2317	    }
  2318	    try:
  2319	        result = await fn(client, model, item)
  2320	        base.update(result)
  2321	        base["error"] = None
  2322	    except Exception as e:
  2323	        base.update({
  2324	            "label_pred": 0, "anomaly_score": 0.5, "anomaly_type_pred": None,
  2325	            "raw_output": None, "cost_tokens": {"input": 0, "output": 0},
  2326	            "latency_sec": 0.0, "error": str(e),
  2327	        })
  2328	    return base
  2329	
  2330	
  2331	async def run_batch(items, ark_api_key, model, variant, max_workers, output_path, existing_results):
  2332	    from volcenginesdkarkruntime import AsyncArk
  2333	    from tqdm import tqdm
  2334	
  2335	    client = AsyncArk(api_key=ark_api_key, timeout=3600)
  2336	    results = list(existing_results)
  2337	    errors = 0
  2338	    sem = asyncio.Semaphore(max_workers)
  2339	    pbar = tqdm(total=len(items), desc=f"batch/{variant}")
  2340	
  2341	    async def worker(item):
  2342	        nonlocal errors
  2343	        async with sem:
  2344	            r = await run_item_async(item, client, model, variant)
  2345	            results.append(r)
  2346	            if r.get("error"):
  2347	                errors += 1
  2348	            pbar.update(1)
  2349	            if len(results) % 20 == 0:
  2350	                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
  2351	                with open(output_path, "w") as f:
  2352	                    json.dump(results, f, indent=2)
  2353	
  2354	    tasks = [asyncio.create_task(worker(item)) for item in items]
  2355	    await asyncio.gather(*tasks)
  2356	    pbar.close()
  2357	    await client.close()
  2358	
  2359	    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
  2360	    with open(output_path, "w") as f:
  2361	        json.dump(results, f, indent=2)
  2362	
  2363	    total_in = sum((r.get("cost_tokens") or {}).get("input", 0) for r in results)
  2364	    total_out = sum((r.get("cost_tokens") or {}).get("output", 0) for r in results)
  2365	    print(f"\nDone: {len(results)} items, {errors} errors")
  2366	    print(f"Tokens — input: {total_in:,} | output: {total_out:,}")
  2367	    print(f"Results saved: {output_path}")
  2368	
  2369	
  2370	# ─── Item runner ──────────────────────────────────────────────────────────────
  2371	
  2372	def run_item(item: dict, client: OpenAI, model: str, variant: str) -> dict:
  2373	    fn = VARIANT_FNS[variant]
  2374	    base = {
  2375	        "item_id": item["item_id"],
  2376	        "domain": item["domain"],
  2377	        "domain_code": item["domain_code"],
  2378	        "label_gt": item["label"],
  2379	        "split": item["split"],
  2380	        "source_dataset": item.get("source_dataset"),
  2381	        "category": item.get("category"),
  2382	    }
  2383	    try:
  2384	        result = fn(client, model, item)
  2385	        base.update(result)
  2386	        base["error"] = None
  2387	    except Exception as e:
  2388	        base.update({
  2389	            "label_pred": 0,
  2390	            "anomaly_score": 0.5,
  2391	            "anomaly_type_pred": None,
  2392	            "raw_output": None,
  2393	            "cost_tokens": {"input": 0, "output": 0},
  2394	            "latency_sec": 0.0,
  2395	            "error": str(e),
  2396	        })
  2397	    return base
  2398	
  2399	
  2400	# ─── Main ─────────────────────────────────────────────────────────────────────
  2401	
  2402	def main():
  2403	    parser = argparse.ArgumentParser()
  2404	    parser.add_argument("--manifest", required=True)
  2405	    parser.add_argument("--split", default="calibration",
  2406	                        choices=["calibration", "dev", "test", "all"])
  2407	    parser.add_argument("--backend", required=True, choices=["gpt", "seedvl", "qwen3"])
  2408	    parser.add_argument("--variant", required=True, choices=list(VARIANT_FNS.keys()))
  2409	    parser.add_argument("--output", required=True)
  2410	    parser.add_argument("--domains", nargs="*", default=None,
  2411	                        help="Filter to specific domain codes, e.g. D1 D2")
  2412	    parser.add_argument("--max_workers", type=int, default=4)
  2413	    parser.add_argument("--max_items", type=int, default=None,
  2414	                        help="Limit total items (for testing)")
  2415	    parser.add_argument("--resume", action="store_true",
  2416	                        help="Resume from existing output file, skip already-processed items")
  2417	    parser.add_argument("--n_refs", type=int, default=2,
  2418	                        help="Number of normal reference images to use (2, 4, or 8)")
  2419	    parser.add_argument("--batch", action="store_true",
  2420	                        help="Use AsyncArk batch inference (seedvl backend only)")
  2421	    parser.add_argument("--batch_workers", type=int, default=50,
  2422	                        help="Concurrency for batch mode (default: 50)")
  2423	    args = parser.parse_args()
  2424	
  2425	    # Set global N_REFS
  2426	    global N_REFS
  2427	    N_REFS = args.n_refs
  2428	
  2429	    # Load manifest
  2430	    with open(args.manifest) as f:
  2431	        all_items = json.load(f)
  2432	
  2433	    # Filter by split and domain
  2434	    items = [x for x in all_items
  2435	             if (args.split == "all" or x["split"] == args.split)
  2436	             and (args.domains is None or x["domain_code"] in args.domains)]
  2437	
  2438	    if args.max_items:
  2439	        items = items[:args.max_items]
  2440	
  2441	    # Resume: load existing results
  2442	    existing = {}
  2443	    if args.resume and Path(args.output).exists():
  2444	        with open(args.output) as f:
  2445	            for r in json.load(f):
  2446	                existing[r["item_id"]] = r
  2447	        items = [x for x in items if x["item_id"] not in existing]
  2448	        print(f"Resuming: {len(existing)} done, {len(items)} remaining")
  2449	
  2450	    model = get_model_name(args.backend, args.batch)
  2451	    print(f"Running {len(items)} items | backend={args.backend} | variant={args.variant}")
  2452	    print(f"Model: {model}")
  2453	
  2454	    # ── Batch mode (AsyncArk) ──
  2455	    if args.batch:
  2456	        if args.backend != "seedvl":
  2457	            print("[WARN] --batch only supported for seedvl backend, falling back to sync mode")
  2458	        elif args.variant not in ASYNC_VARIANT_FNS:
  2459	            print(f"[WARN] --batch not implemented for variant {args.variant}, falling back to sync mode")
  2460	        else:
  2461	            ark_key = os.environ.get("SEED_API_KEY", "***REDACTED-SEED-KEY***")
  2462	            asyncio.run(run_batch(items, ark_key, model, args.variant,
  2463	                                  args.batch_workers, args.output, existing.values()))
  2464	            return
  2465	

exec
/bin/bash -lc "rg -n \"retrieval_index|_index\\.npz|paths|embeddings|normal pool|normal_pool|ref_paths|query_path\" benchmark/scripts -g'*.py'" in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
benchmark/scripts/run_baselines_v6.py:36:            [img_msg(load_and_encode(p)) for p in item.get("ref_paths", [])[:4]] +
benchmark/scripts/run_baselines_v6.py:37:            [text_msg("QUERY:"), img_msg(load_and_encode(item["query_path"]))]
benchmark/scripts/agent_prompt_v6_2.py:32:  tool_reference_retriever(k=4): re-pull similar refs from normal pool.
benchmark/scripts/agent_prompt_v6.py:38:    normal pool.
benchmark/scripts/additional_tools.py:13:def tool_image_diff(query_path: str, ref_path: str, threshold: float = 30) -> dict:
benchmark/scripts/additional_tools.py:18:    q = np.array(Image.open(query_path).convert("RGB").resize((256, 256)))
benchmark/scripts/additional_tools.py:50:def tool_segment_and_count(query_path: str, ref_paths: list, grid_size: int = 8) -> dict:
benchmark/scripts/additional_tools.py:57:    q = np.array(Image.open(query_path).convert("L").resize((256, 256)))
benchmark/scripts/additional_tools.py:58:    r = np.array(Image.open(ref_paths[0]).convert("L").resize((256, 256)))
benchmark/scripts/additional_tools.py:130:def tool_ref_category_matcher(query_path: str, ref_paths: list, model=None, transform=None,
benchmark/scripts/additional_tools.py:146:    q_emb = get_emb(query_path)
benchmark/scripts/additional_tools.py:148:    for rp in ref_paths[:4]:
benchmark/scripts/classical_baselines.py:82:            query_feat = embed_image_dino(model, transform, item["query_path"])
benchmark/scripts/classical_baselines.py:83:            if item["ref_paths"]:
benchmark/scripts/classical_baselines.py:86:                    for p in item["ref_paths"][:2]
benchmark/scripts/classical_baselines.py:105:            q_patches = embed_patches_dino(model, transform, item["query_path"])
benchmark/scripts/classical_baselines.py:106:            if item["ref_paths"]:
benchmark/scripts/classical_baselines.py:109:                    for p in item["ref_paths"][:2]
benchmark/scripts/classical_baselines.py:174:            img = Image.open(item["query_path"]).convert("RGB")
benchmark/scripts/patch_expert.py:80:def _build_patch_bank(model, transform, ref_paths: List[str],
benchmark/scripts/patch_expert.py:86:    key = tuple(sorted(ref_paths[:max_refs]))
benchmark/scripts/patch_expert.py:91:    for path in ref_paths[:max_refs]:
benchmark/scripts/patch_expert.py:117:def patch_expert_score(query_path: str, ref_paths: List[str],
benchmark/scripts/patch_expert.py:135:    bank = _build_patch_bank(model, transform, ref_paths, max_refs, device)
benchmark/scripts/patch_expert.py:140:    query_patches = _extract_patch_features(model, transform, query_path, device=device)
benchmark/scripts/patch_expert.py:161:    global_feat = _extract_global_feature(model, transform, query_path, device)
benchmark/scripts/patch_expert.py:163:    for path in ref_paths[:max_refs]:
benchmark/scripts/patch_expert.py:237:                item["query_path"],
benchmark/scripts/patch_expert.py:238:                item["ref_paths"][:8],
benchmark/scripts/agent_v6_6.py:36:def _build_init_v66(self, query_path, ref_paths, _domain_code):
benchmark/scripts/agent_v6_6.py:43:    for rp in ref_paths[:4]:
benchmark/scripts/agent_v6_6.py:46:    user_parts.append(img_msg(load_and_encode(query_path)))
benchmark/scripts/agent_v6_6.py:86:def run_v66(self, item_id: str, query_path: str, ref_paths: list,
benchmark/scripts/agent_v6_6.py:91:        "query_path": query_path,
benchmark/scripts/agent_v6_6.py:92:        "ref_paths": ref_paths,
benchmark/scripts/agent_v6_6.py:101:    messages = _build_init_v66(self, query_path, ref_paths, domain_code)
benchmark/scripts/expert_subspacead.py:6:    (query_image_path, ref_image_paths[]) → (anomaly_score, top_patches[])
benchmark/scripts/expert_subspacead.py:80:    def predict(self, query_path: str, ref_paths: list, topk: int = TOPK) -> dict:
benchmark/scripts/expert_subspacead.py:91:        for rp in ref_paths[:4]:  # limit to 4 refs for speed
benchmark/scripts/expert_subspacead.py:121:            q_img = Image.open(query_path).convert("RGB")
benchmark/scripts/expert_subspacead.py:188:        r = tool.predict(item["query_path"], item["ref_paths"])
benchmark/scripts/expert_anomalyvfm.py:90:    def predict(self, query_path: str, topk: int = TOPK) -> dict:
benchmark/scripts/expert_anomalyvfm.py:94:            img = Image.open(query_path).convert("RGB")
benchmark/scripts/expert_anomalyvfm.py:155:        r = tool.predict(item["query_path"])
benchmark/scripts/agent_v6.py:55:    def _build_initial_messages(self, query_path: str,
benchmark/scripts/agent_v6.py:56:                                ref_paths: list) -> list:
benchmark/scripts/agent_v6.py:58:        for rp in ref_paths[:4]:
benchmark/scripts/agent_v6.py:61:        user_parts.append(img_msg(load_and_encode(query_path)))
benchmark/scripts/agent_v6.py:111:    def run(self, item_id: str, query_path: str, ref_paths: list,
benchmark/scripts/agent_v6.py:114:            "query_path": query_path,
benchmark/scripts/agent_v6.py:115:            "ref_paths": ref_paths,
benchmark/scripts/agent_v6.py:124:        messages = self._build_initial_messages(query_path, ref_paths)
benchmark/scripts/agent_v6.py:277:            r = agent.run(item_id=x["item_id"], query_path=x["query_path"],
benchmark/scripts/agent_v6.py:278:                          ref_paths=x["ref_paths"], split=args.split,
benchmark/scripts/build_manifest_v2.py:80:                "query_path": img,
benchmark/scripts/build_manifest_v2.py:81:                "ref_paths": refs,
benchmark/scripts/build_manifest_v2.py:98:                "query_path": img,
benchmark/scripts/build_manifest_v2.py:99:                "ref_paths": refs,
benchmark/scripts/agent_v6_4.py:25:def _build_init_v64(self, query_path, ref_paths, _domain_code):
benchmark/scripts/agent_v6_4.py:32:    for rp in ref_paths[:4]:
benchmark/scripts/agent_v6_4.py:35:    user_parts.append(img_msg(load_and_encode(query_path)))
benchmark/scripts/agent_v6_4.py:49:def run_v64(self, item_id, query_path, ref_paths, split, domain_code=None):
benchmark/scripts/agent_v6_4.py:54:        result = _orig_run(self, item_id=item_id, query_path=query_path,
benchmark/scripts/agent_v6_4.py:55:                           ref_paths=ref_paths, split=split,
benchmark/scripts/agent_v6_7.py:40:def _build_init_v67(self, query_path, ref_paths, _domain_code):
benchmark/scripts/agent_v6_7.py:46:    for rp in ref_paths[:4]:
benchmark/scripts/agent_v6_7.py:49:    user_parts.append(img_msg(load_and_encode(query_path)))
benchmark/scripts/agent_v6_7.py:57:def _direct_turn0_call(client, model, query_path, ref_paths, domain_code,
benchmark/scripts/agent_v6_7.py:66:                    [img_msg(load_and_encode(p)) for p in ref_paths[:4]] +
benchmark/scripts/agent_v6_7.py:67:                    [text_msg("QUERY:"), img_msg(load_and_encode(query_path))]
benchmark/scripts/agent_v6_7.py:91:def _run_ensemble(self, item_id, query_path, ref_paths, split, domain_code,
benchmark/scripts/agent_v6_7.py:98:            self.client, self.model, query_path, ref_paths, domain_code)
benchmark/scripts/agent_v6_7.py:105:        r = _orig_run(self, item_id=item_id, query_path=query_path,
benchmark/scripts/agent_v6_7.py:106:                      ref_paths=ref_paths, split=split,
benchmark/scripts/agent_v6_7.py:166:                agent, x["item_id"], x["query_path"], x["ref_paths"],
benchmark/scripts/build_patch_evidence_cache.py:111:        q = embed_patches(model, transform, item["query_path"])
benchmark/scripts/build_patch_evidence_cache.py:112:        refs = [embed_patches(model, transform, p) for p in item["ref_paths"][:2]]
benchmark/scripts/build_retrieval_index.py:2:Build visual retrieval index for each domain using DINOv2 embeddings.
benchmark/scripts/build_retrieval_index.py:4:For each domain, extracts embeddings from all train/good (normal) images,
benchmark/scripts/build_retrieval_index.py:8:  python benchmark/scripts/build_retrieval_index.py
benchmark/scripts/build_retrieval_index.py:46:    # Collect all unique ref paths for this domain (these are the normal bank)
benchmark/scripts/build_retrieval_index.py:47:    ref_paths = set()
benchmark/scripts/build_retrieval_index.py:50:            for rp in item.get("ref_paths", []):
benchmark/scripts/build_retrieval_index.py:51:                ref_paths.add(rp)
benchmark/scripts/build_retrieval_index.py:53:    ref_paths = sorted(ref_paths)
benchmark/scripts/build_retrieval_index.py:54:    if not ref_paths:
benchmark/scripts/build_retrieval_index.py:55:        print(f"  {domain_code}: no ref paths found, skipping")
benchmark/scripts/build_retrieval_index.py:58:    print(f"  {domain_code}: extracting embeddings for {len(ref_paths)} normal images...")
benchmark/scripts/build_retrieval_index.py:60:    embeddings = []
benchmark/scripts/build_retrieval_index.py:61:    valid_paths = []
benchmark/scripts/build_retrieval_index.py:62:    for rp in tqdm(ref_paths, desc=f"  {domain_code}"):
benchmark/scripts/build_retrieval_index.py:67:            embeddings.append(emb)
benchmark/scripts/build_retrieval_index.py:68:            valid_paths.append(rp)
benchmark/scripts/build_retrieval_index.py:72:    if not embeddings:
benchmark/scripts/build_retrieval_index.py:73:        print(f"  {domain_code}: no valid embeddings")
benchmark/scripts/build_retrieval_index.py:76:    embeddings = np.array(embeddings)
benchmark/scripts/build_retrieval_index.py:78:    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
benchmark/scripts/build_retrieval_index.py:79:    embeddings = embeddings / (norms + 1e-8)
benchmark/scripts/build_retrieval_index.py:81:    output_path = Path(output_dir) / f"{domain_code}_index.npz"
benchmark/scripts/build_retrieval_index.py:82:    np.savez(str(output_path), embeddings=embeddings, paths=np.array(valid_paths))
benchmark/scripts/build_retrieval_index.py:83:    print(f"  {domain_code}: saved {len(valid_paths)} embeddings → {output_path}")
benchmark/scripts/build_retrieval_index.py:86:def retrieve_topk(query_path, index_path, model, transform, k=4, device="cuda"):
benchmark/scripts/build_retrieval_index.py:89:    bank_embs = data["embeddings"]
benchmark/scripts/build_retrieval_index.py:90:    bank_paths = data["paths"]
benchmark/scripts/build_retrieval_index.py:92:    query_emb = extract_embedding(model, transform, query_path, device)
benchmark/scripts/build_retrieval_index.py:99:    results = [(str(bank_paths[i]), float(sims[i])) for i in topk_idx]
benchmark/scripts/build_retrieval_index.py:105:    output_dir = "/hdd1/jiangxi/AD-Agent/benchmark/retrieval_index"
benchmark/scripts/sanity_v6.py:61:        r = agent.run(item_id=x["item_id"], query_path=x["query_path"],
benchmark/scripts/sanity_v6.py:62:                      ref_paths=x["ref_paths"], split="calibration",
benchmark/scripts/agent_v6_5.py:28:def _build_init_v65(self, query_path, ref_paths, _domain_code):
benchmark/scripts/agent_v6_5.py:34:    for rp in ref_paths[:4]:
benchmark/scripts/agent_v6_5.py:37:    user_parts.append(img_msg(load_and_encode(query_path)))
benchmark/scripts/agent_v6_5.py:46:def run_v65(self, item_id, query_path, ref_paths, split, domain_code=None):
benchmark/scripts/agent_v6_5.py:50:        return _orig_run(self, item_id=item_id, query_path=query_path,
benchmark/scripts/agent_v6_5.py:51:                         ref_paths=ref_paths, split=split,
benchmark/scripts/agent_tools.py:18:_retrieval_cache = {}  # {domain_code: (embeddings, paths, model, transform)}
benchmark/scripts/agent_tools.py:43:                          index_dir="/hdd1/jiangxi/AD-Agent/benchmark/retrieval_index",
benchmark/scripts/agent_tools.py:58:        index_path = os.path.join(index_dir, f"{domain_code}_index.npz")
benchmark/scripts/agent_tools.py:63:            "embeddings": data["embeddings"],
benchmark/scripts/agent_tools.py:64:            "paths": data["paths"],
benchmark/scripts/agent_tools.py:69:    sims = bank["embeddings"] @ query_emb
benchmark/scripts/agent_tools.py:72:    results = [(str(bank["paths"][i]), float(sims[i])) for i in topk_idx]
benchmark/scripts/agent_tools.py:244:                         index_dir="/hdd1/jiangxi/AD-Agent/benchmark/retrieval_index",
benchmark/scripts/agent_tools_v6.py:118:def tool_hotspot_cropper(query_path: str, patches: list[dict] | None = None,
benchmark/scripts/agent_tools_v6.py:129:    img = Image.open(query_path).convert("RGB")
benchmark/scripts/agent_tools_v6.py:156:def tool_zoom_bbox(query_path: str, bbox: list[int], **_) -> dict:
benchmark/scripts/agent_tools_v6.py:163:    img = Image.open(query_path).convert("RGB")
benchmark/scripts/agent_tools_v6.py:178:def tool_patch_grid(query_path: str, rows: int = 3, cols: int = 3, **_) -> dict:
benchmark/scripts/agent_tools_v6.py:186:    img = Image.open(query_path).convert("RGB")
benchmark/scripts/agent_tools_v6.py:204:def tool_image_diff(query_path: str, ref_path: str | None = None,
benchmark/scripts/agent_tools_v6.py:205:                    ref_paths: list[str] | None = None, ref_idx: int = 0,
benchmark/scripts/agent_tools_v6.py:209:    Accepts either `ref_path` directly or `ref_idx` + `ref_paths` from session.
benchmark/scripts/agent_tools_v6.py:211:    if ref_path is None and ref_paths:
benchmark/scripts/agent_tools_v6.py:213:            ref_path = ref_paths[int(ref_idx)]
benchmark/scripts/agent_tools_v6.py:218:    q = np.array(Image.open(query_path).convert("RGB").resize((256, 256)))
benchmark/scripts/agent_tools_v6.py:234:def tool_rotate_align(query_path: str, ref_path: str | None = None,
benchmark/scripts/agent_tools_v6.py:235:                      ref_paths: list[str] | None = None, ref_idx: int = 0,
benchmark/scripts/agent_tools_v6.py:238:    if ref_path is None and ref_paths:
benchmark/scripts/agent_tools_v6.py:240:            ref_path = ref_paths[int(ref_idx)]
benchmark/scripts/agent_tools_v6.py:245:    q = np.array(Image.open(query_path).convert("RGB").resize((256, 256)))
benchmark/scripts/agent_tools_v6.py:264:def tool_side_by_side(query_path: str, bbox: list[int],
benchmark/scripts/agent_tools_v6.py:265:                      ref_paths: list[str] | None = None, **_) -> dict:
benchmark/scripts/agent_tools_v6.py:275:    if not ref_paths:
benchmark/scripts/agent_tools_v6.py:276:        return {"error": "no ref_paths in session"}
benchmark/scripts/agent_tools_v6.py:282:    crops = [_crop(query_path)] + [_crop(p) for p in ref_paths[:4]]
benchmark/scripts/agent_tools_v6.py:306:def tool_reference_profiler(ref_paths: list[str] | None = None,
benchmark/scripts/agent_tools_v6.py:317:            "n_refs_used": len(ref_paths[:4]) if ref_paths else 0,
benchmark/scripts/agent_tools_v6.py:319:    if not ref_paths:
benchmark/scripts/agent_tools_v6.py:320:        return {"error": "no ref_paths"}
benchmark/scripts/agent_tools_v6.py:324:    for p in ref_paths[:4]:
benchmark/scripts/agent_tools_v6.py:340:        "n_refs_used": len(ref_paths[:4]),
benchmark/scripts/agent_tools_v6.py:362:def tool_reference_retriever(query_path: str, domain_code: str | None = None,
benchmark/scripts/agent_tools_v6.py:364:                             index_dir: str = "/hdd1/jiangxi/AD-Agent/benchmark/retrieval_index",
benchmark/scripts/agent_tools_v6.py:377:    idx_path = os.path.join(index_dir, f"{domain_code}_index.npz")
benchmark/scripts/agent_tools_v6.py:383:        img = Image.open(query_path).convert("RGB")
benchmark/scripts/agent_tools_v6.py:389:        sims = data["embeddings"] @ emb
benchmark/scripts/agent_tools_v6.py:391:        results = [{"path": str(data["paths"][i]),
benchmark/scripts/agent_tools_v6.py:429:def tool_segment_and_count(query_path: str, ref_paths: list[str] | None = None,
benchmark/scripts/agent_tools_v6.py:432:    if not ref_paths:
benchmark/scripts/agent_tools_v6.py:433:        return {"error": "ref_paths required"}
benchmark/scripts/agent_tools_v6.py:434:    q = np.array(Image.open(query_path).convert("L").resize((256, 256)))
benchmark/scripts/agent_tools_v6.py:435:    r = np.array(Image.open(ref_paths[0]).convert("L").resize((256, 256)))
benchmark/scripts/agent_tools_v6.py:454:def tool_texture_fft(query_path: str, **_) -> dict:
benchmark/scripts/agent_tools_v6.py:456:    img = np.array(Image.open(query_path).convert("L").resize((256, 256))).astype(float)
benchmark/scripts/agent_tools_v6.py:522:    that the VLM shouldn't re-type (query_path, ref_paths, split, clients)."""
benchmark/scripts/agent_tools_v6.py:528:    for k in ("query_path", "ref_paths", "item_id", "split",
benchmark/scripts/build_manifest.py:14:  "query_path": "/abs/path/to/image.png",
benchmark/scripts/build_manifest.py:15:  "ref_paths": ["/abs/path/normal1.png", "/abs/path/normal2.png"],
benchmark/scripts/build_manifest.py:155:                "query_path": str(img),
benchmark/scripts/build_manifest.py:156:                "ref_paths": refs,
benchmark/scripts/build_manifest.py:169:                "query_path": str(img),
benchmark/scripts/build_manifest.py:170:                "ref_paths": refs,
benchmark/scripts/build_manifest.py:243:                "query_path": str(img),
benchmark/scripts/build_manifest.py:244:                "ref_paths": refs,
benchmark/scripts/build_manifest.py:259:                "query_path": str(img),
benchmark/scripts/build_manifest.py:260:                "ref_paths": refs,
benchmark/scripts/build_manifest.py:327:            "query_path": str(img),
benchmark/scripts/build_manifest.py:328:            "ref_paths": [],  # No reference for X-ray (zero-shot domain)
benchmark/scripts/build_manifest.py:381:                    "query_path": str(img),
benchmark/scripts/build_manifest.py:382:                    "ref_paths": refs,
benchmark/scripts/build_manifest.py:467:            "query_path": img,
benchmark/scripts/build_manifest.py:468:            "ref_paths": refs,
benchmark/scripts/build_manifest.py:481:            "query_path": img,
benchmark/scripts/build_manifest.py:482:            "ref_paths": refs,
benchmark/scripts/build_manifest.py:586:            "query_path": s["img2"],
benchmark/scripts/build_manifest.py:587:            "ref_paths": [s["img1"]],
benchmark/scripts/build_manifest.py:599:            "query_path": s["img2"],
benchmark/scripts/build_manifest.py:600:            "ref_paths": [s["img1"]],
benchmark/scripts/build_manifest.py:656:            "query_path": str(img),
benchmark/scripts/build_manifest.py:657:            "ref_paths": refs,
benchmark/scripts/build_manifest.py:681:            "query_path": str(img),
benchmark/scripts/build_manifest.py:682:            "ref_paths": refs,
benchmark/scripts/build_manifest.py:788:            "query_path": str(img),
benchmark/scripts/build_manifest.py:789:            "ref_paths": refs,
benchmark/scripts/build_manifest.py:803:            "query_path": str(img),
benchmark/scripts/build_manifest.py:804:            "ref_paths": refs,
benchmark/scripts/build_manifest.py:866:                    "query_path": str(img),
benchmark/scripts/build_manifest.py:867:                    "ref_paths": refs,
benchmark/scripts/build_manifest.py:886:                    "query_path": str(img),
benchmark/scripts/build_manifest.py:887:                    "ref_paths": refs,
benchmark/scripts/build_manifest.py:940:                    "query_path": str(img),
benchmark/scripts/build_manifest.py:941:                    "ref_paths": refs,
benchmark/scripts/build_manifest.py:963:                    "query_path": str(img),
benchmark/scripts/build_manifest.py:964:                    "ref_paths": refs,
benchmark/scripts/build_manifest.py:1018:                    "query_path": str(img),
benchmark/scripts/build_manifest.py:1019:                    "ref_paths": refs,
benchmark/scripts/build_manifest.py:1040:                    "query_path": str(img),
benchmark/scripts/build_manifest.py:1041:                    "ref_paths": refs,
benchmark/scripts/build_manifest.py:1098:            "query_path": img,
benchmark/scripts/build_manifest.py:1099:            "ref_paths": refs,
benchmark/scripts/build_manifest.py:1112:            "query_path": img,
benchmark/scripts/build_manifest.py:1113:            "ref_paths": refs,
benchmark/scripts/build_manifest.py:1150:            # Try alternative paths
benchmark/scripts/build_manifest.py:1191:            "query_path": img, "ref_paths": refs, "label": 0, "anomaly_type": None,
benchmark/scripts/build_manifest.py:1198:            "query_path": img, "ref_paths": refs, "label": 1, "anomaly_type": "pathology",
benchmark/scripts/infer.py:689:    ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:N_REFS]]
benchmark/scripts/infer.py:690:    query_img = load_and_encode(item["query_path"])
benchmark/scripts/infer.py:722:    ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:N_REFS]]
benchmark/scripts/infer.py:723:    query_img = load_and_encode(item["query_path"])
benchmark/scripts/infer.py:830:    ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:N_REFS]]
benchmark/scripts/infer.py:831:    query_img = load_and_encode(item["query_path"])
benchmark/scripts/infer.py:871:        all_refs = [load_and_encode(p) for p in item["ref_paths"][:10]]
benchmark/scripts/infer.py:894:    ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:2]]
benchmark/scripts/infer.py:895:    query_img = load_and_encode(item["query_path"])
benchmark/scripts/infer.py:935:    """Cache key from reference paths."""
benchmark/scripts/infer.py:936:    return tuple(sorted(item["ref_paths"][:N_REFS]))
benchmark/scripts/infer.py:945:    ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:N_REFS]]
benchmark/scripts/infer.py:987:    ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:N_REFS]]
benchmark/scripts/infer.py:988:    query_img = load_and_encode(item["query_path"])
benchmark/scripts/infer.py:1036:    query_img = load_and_encode(item["query_path"])
benchmark/scripts/infer.py:1037:    ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:min(2, N_REFS)]]
benchmark/scripts/infer.py:1171:    ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:N_REFS]]
benchmark/scripts/infer.py:1172:    query_img = load_and_encode(item["query_path"])
benchmark/scripts/infer.py:1227:        ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:N_REFS]]
benchmark/scripts/infer.py:1240:    ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:N_REFS]]
benchmark/scripts/infer.py:1241:    query_img = load_and_encode(item["query_path"])
benchmark/scripts/infer.py:1333:    ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:N_REFS]]
benchmark/scripts/infer.py:1334:    query_img = load_and_encode(item["query_path"])
benchmark/scripts/infer.py:1440:    ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:N_REFS]]
benchmark/scripts/infer.py:1441:    query_img = load_and_encode(item["query_path"])
benchmark/scripts/infer.py:1785:                        item["query_path"], item["ref_paths"][:4]
benchmark/scripts/infer.py:1865:        ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:N_REFS]]
benchmark/scripts/infer.py:1866:        query_img = load_and_encode(item["query_path"])
benchmark/scripts/infer.py:2104:        ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:N_REFS]]
benchmark/scripts/infer.py:2105:        query_img = load_and_encode(item["query_path"])
benchmark/scripts/infer.py:2146:        ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:N_REFS]]
benchmark/scripts/infer.py:2147:        query_img = load_and_encode(item["query_path"])
benchmark/scripts/infer.py:2204:    ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:2]]
benchmark/scripts/infer.py:2205:    query_img = load_and_encode(item["query_path"])
benchmark/scripts/infer.py:2228:    ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:2]]
benchmark/scripts/infer.py:2229:    query_img = load_and_encode(item["query_path"])
benchmark/scripts/infer.py:2276:    ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:8]]
benchmark/scripts/infer.py:2277:    query_img = load_and_encode(item["query_path"])

exec
/bin/bash -lc "rg -n \"label_gt|label\\]|label\\)|split|calibration|test|dev|SubspaceAD|weight|w=|fusion|selected|sweep|per-domain|domain\" refine-logs/V6_RESULTS.md refine-logs/EXPLORATION_JOURNAL.md" in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
refine-logs/V6_RESULTS.md:10:Fixed-fusion baselines across two VLM backbones. **The agent does NOT
refine-logs/V6_RESULTS.md:13:domains (especially medical imaging, change detection) tool outputs
refine-logs/V6_RESULTS.md:20:| Backbone | Direct | Fusion (w=0.2) | Best Agent alone | **Ensemble (α=0.5)** |
refine-logs/V6_RESULTS.md:29:  --direct benchmark/results/v6_direct_gpt_test.json \
refine-logs/V6_RESULTS.md:30:  --agent benchmark/results/v6_6_agent_gpt_test.json \
refine-logs/V6_RESULTS.md:31:  --output benchmark/results/v6_ensemble_v6_6_gpt_test.json
refine-logs/V6_RESULTS.md:36:### Qwen3.5-VL-27B — 12-domain test (n=1418)
refine-logs/V6_RESULTS.md:40:| Direct (task descriptor) | domain hint | **0.7684** | — | +4.7pp |
refine-logs/V6_RESULTS.md:42:| Fusion w=0.2 SubspaceAD (task) | domain hint | **0.8142** | +4.6pp | +9.3pp |
refine-logs/V6_RESULTS.md:43:| Fusion w=0.2 SubspaceAD (generic) | no hint | 0.7641 | -0.4pp | +4.3pp |
refine-logs/V6_RESULTS.md:46:| Agent v6.4 (B-regime, score_from_v0) | domain hint | 0.7158 | -5.3pp | -0.6pp |
refine-logs/V6_RESULTS.md:47:| Agent v6.5 (B-regime, free score) | domain hint | *running* | — | — |
refine-logs/V6_RESULTS.md:49:### SeedVL (doubao-seed-2.0-lite) — 12-domain test (n=1418)
refine-logs/V6_RESULTS.md:54:| Fusion w=0.2 SubspaceAD | **0.8075** |
refine-logs/V6_RESULTS.md:57:### Per-domain Agent v6 (Qwen3.5) vs Direct-task
refine-logs/V6_RESULTS.md:90:### 1. Prompt-artifact penalty from "no domain hint"
refine-logs/V6_RESULTS.md:100:penalty**: without a domain hint, VLM over-predicts "anomalous" on
refine-logs/V6_RESULTS.md:101:unfamiliar image types (observed on D5d/D6 calibration items: ~90% scored
refine-logs/V6_RESULTS.md:103:`build_prompt_v0(domain, has_refs=True)`.
refine-logs/V6_RESULTS.md:105:### 2. Score calibration: free-form score > score_from_v0 mapping
refine-logs/V6_RESULTS.md:107:Score distribution (Qwen3.5 full test):
refine-logs/V6_RESULTS.md:116:free-form score. Surprisingly, v6 (no calibration pass) has *better*
refine-logs/V6_RESULTS.md:119:### 3. Tool misuse on non-industrial domains
refine-logs/V6_RESULTS.md:121:- `tool_expert_score` called on 86% (v6) of items. SubspaceAD was designed for
refine-logs/V6_RESULTS.md:123:  its signal is noise, which the agent then weights into its final answer.
refine-logs/V6_RESULTS.md:127:## What Worked (domain-level)
refine-logs/V6_RESULTS.md:129:Agent v6 beat Direct by ≥ 2pp on 4 domains:
refine-logs/V6_RESULTS.md:151:| tool_domain_knowledge | 0 |
refine-logs/V6_RESULTS.md:161:   its own zero-shot VLM baseline. The v5 per-domain router (also losing
refine-logs/V6_RESULTS.md:163:   domains get tools.
refine-logs/V6_RESULTS.md:165:2. **A-regime (no domain hint) penalty is prompt-architectural**, not
refine-logs/V6_RESULTS.md:169:3. **Fusion w=0.2 (no per-domain tuning, no agent) is the actual
refine-logs/V6_RESULTS.md:170:   winner** on both backbones. A simple "VLM + SubspaceAD 20% fused"
refine-logs/V6_RESULTS.md:175:4. **Tools help in aggregate on some domains, hurt on others.** Net
refine-logs/V6_RESULTS.md:183:- **Per-item learned routing** trained on the 480-item dev split:
refine-logs/V6_RESULTS.md:197:- Results: `benchmark/results/v6_*_{qwen3,seedvl}_test.json`
refine-logs/EXPLORATION_JOURNAL.md:36:**Result (GPT-5.4 test, n=1418)**: **macro = 0.6001 — FAILED**. 1106/1418
refine-logs/EXPLORATION_JOURNAL.md:81:  (p=0.26 vs Direct, p=0.81 vs Fusion — low power with 12 domains)
refine-logs/EXPLORATION_JOURNAL.md:108:- Matches Fusion (0.8142, w=0.2 SubspaceAD) within 0.06pp.
refine-logs/EXPLORATION_JOURNAL.md:123:domain hint but keep v6's free-form 0-1 score.
refine-logs/EXPLORATION_JOURNAL.md:129:**Result (Qwen3.5 test, n=1418)**:
refine-logs/EXPLORATION_JOURNAL.md:132:- Wins ≥+2pp on 7/12 domains: D1 (+5.0), D2 (+5.8), D5b (+7.7), D5c (+4.1), D8 (+7.0),
refine-logs/EXPLORATION_JOURNAL.md:138:**Lesson**: domain hint + free-form score is the right combination. The agent doesn't
refine-logs/EXPLORATION_JOURNAL.md:139:need to re-invent score calibration. Remaining losses (D5d, D6) are SubspaceAD-misleading
refine-logs/EXPLORATION_JOURNAL.md:140:failures — agent still over-trusts the expert on medical / change detection domains.
refine-logs/EXPLORATION_JOURNAL.md:145:**Hypothesis**: give agent the same domain hint Direct gets → fair B-regime comparison.
refine-logs/EXPLORATION_JOURNAL.md:153:**Lesson**: domain hint helps semantics (D6 +16pp). But `score_from_v0` maps
refine-logs/EXPLORATION_JOURNAL.md:161:(observed 90% false positive on D5d/D6 calibration). Forcing the agent to describe
refine-logs/EXPLORATION_JOURNAL.md:168:anomalous" is too vague without domain info. Killed before full run.
refine-logs/EXPLORATION_JOURNAL.md:172:## Round 6.2 — A-regime + score_from_v0 calibration (failed)
refine-logs/EXPLORATION_JOURNAL.md:173:**Hypothesis**: v6's self-reported score had worse calibration than Direct's
refine-logs/EXPLORATION_JOURNAL.md:175:reusing the same mapping should align calibration.
refine-logs/EXPLORATION_JOURNAL.md:180:**Lesson**: the score-calibration remap BIMODALIZES scores (80% at extremes) and
refine-logs/EXPLORATION_JOURNAL.md:191:items VLM can't recognize → VLM over-confidently says "anomalous" without domain
refine-logs/EXPLORATION_JOURNAL.md:200:Direct VLM without any domain hint.
refine-logs/EXPLORATION_JOURNAL.md:207:- Per-domain: wins on D1/D10/D7 (+2-8pp), catastrophic -22/-25pp on D5d/D6
refine-logs/EXPLORATION_JOURNAL.md:212:**Lesson**: pure "no-domain-info" agent handicaps itself. Score distribution
refine-logs/EXPLORATION_JOURNAL.md:213:analysis shows free-form score > score_from_v0 for AUROC. Need domain hint.
refine-logs/EXPLORATION_JOURNAL.md:218:**Setup**: Direct VLM (`build_prompt_v0` + domain context) and fixed-w=0.2 fusion
refine-logs/EXPLORATION_JOURNAL.md:219:with SubspaceAD raw score, calibration-median sigmoid center.
refine-logs/EXPLORATION_JOURNAL.md:222:- Direct-task (domain hint): 0.7684
refine-logs/EXPLORATION_JOURNAL.md:231:**Lesson**: fusion alone (SubspaceAD 20% weight) accounts for +5pp out of v5's
refine-logs/EXPLORATION_JOURNAL.md:232:reported "+6.3pp" — most gain is from adding an expert, not from per-domain routing.
refine-logs/EXPLORATION_JOURNAL.md:263:- **v7** (future): learned per-item router on 480-item dev split. Target = close
refine-logs/EXPLORATION_JOURNAL.md:266:- **GPU util tuning**: test 2/3/4 replicas on next Qwen3.5 run.

exec
/bin/bash -lc "find benchmark/retrieval_index -maxdepth 1 -type f -name '*_index.npz' -print 2>/dev/null | sort | head -50" in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
benchmark/retrieval_index/D10_index.npz
benchmark/retrieval_index/D1_index.npz
benchmark/retrieval_index/D2_index.npz
benchmark/retrieval_index/D4_index.npz
benchmark/retrieval_index/D5_index.npz
benchmark/retrieval_index/D5b_index.npz
benchmark/retrieval_index/D5c_index.npz
benchmark/retrieval_index/D5d_index.npz
benchmark/retrieval_index/D7_index.npz
benchmark/retrieval_index/D9_index.npz

exec
/bin/bash -lc "nl -ba benchmark/scripts/build_retrieval_index.py | sed -n '1,130p'" in /hdd1/jiangxi/AD-Agent
exec
/bin/bash -lc "nl -ba refine-logs/V6_RESULTS.md | sed -n '1,220p'" in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
     1	"""
     2	Build visual retrieval index for each domain using DINOv2 embeddings.
     3	
     4	For each domain, extracts embeddings from all train/good (normal) images,
     5	saves as a .npz file for fast retrieval at inference time.
     6	
     7	Usage:
     8	  python benchmark/scripts/build_retrieval_index.py
     9	"""
    10	
    11	import json
    12	import os
    13	import numpy as np
    14	import torch
    15	from pathlib import Path
    16	from tqdm import tqdm
    17	
    18	# Use DINOv2-small via timm (fast, good features)
    19	MODEL_NAME = "vit_small_patch14_dinov2.lvd142m"
    20	
    21	
    22	def load_model(device="cuda"):
    23	    import timm
    24	    model = timm.create_model(MODEL_NAME, pretrained=True, num_classes=0)
    25	    model = model.to(device).eval()
    26	
    27	    data_cfg = timm.data.resolve_data_config(model.pretrained_cfg)
    28	    transform = timm.data.create_transform(**data_cfg, is_training=False)
    29	    return model, transform
    30	
    31	
    32	def extract_embedding(model, transform, image_path, device="cuda"):
    33	    from PIL import Image
    34	    img = Image.open(image_path).convert("RGB")
    35	    tensor = transform(img).unsqueeze(0).to(device)
    36	    with torch.no_grad():
    37	        emb = model(tensor)
    38	    return emb.cpu().numpy().flatten()
    39	
    40	
    41	def build_index_for_domain(manifest_path, domain_code, output_dir, model, transform, device="cuda"):
    42	    """Build retrieval index from train/good images for a domain."""
    43	    with open(manifest_path) as f:
    44	        manifest = json.load(f)
    45	
    46	    # Collect all unique ref paths for this domain (these are the normal bank)
    47	    ref_paths = set()
    48	    for item in manifest:
    49	        if item["domain_code"] == domain_code:
    50	            for rp in item.get("ref_paths", []):
    51	                ref_paths.add(rp)
    52	
    53	    ref_paths = sorted(ref_paths)
    54	    if not ref_paths:
    55	        print(f"  {domain_code}: no ref paths found, skipping")
    56	        return
    57	
    58	    print(f"  {domain_code}: extracting embeddings for {len(ref_paths)} normal images...")
    59	
    60	    embeddings = []
    61	    valid_paths = []
    62	    for rp in tqdm(ref_paths, desc=f"  {domain_code}"):
    63	        if not os.path.exists(rp):
    64	            continue
    65	        try:
    66	            emb = extract_embedding(model, transform, rp, device)
    67	            embeddings.append(emb)
    68	            valid_paths.append(rp)
    69	        except Exception as e:
    70	            print(f"  Warning: failed to process {rp}: {e}")
    71	
    72	    if not embeddings:
    73	        print(f"  {domain_code}: no valid embeddings")
    74	        return
    75	
    76	    embeddings = np.array(embeddings)
    77	    # Normalize for cosine similarity
    78	    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    79	    embeddings = embeddings / (norms + 1e-8)
    80	
    81	    output_path = Path(output_dir) / f"{domain_code}_index.npz"
    82	    np.savez(str(output_path), embeddings=embeddings, paths=np.array(valid_paths))
    83	    print(f"  {domain_code}: saved {len(valid_paths)} embeddings → {output_path}")
    84	
    85	
    86	def retrieve_topk(query_path, index_path, model, transform, k=4, device="cuda"):
    87	    """Retrieve top-k most similar normal images for a query."""
    88	    data = np.load(index_path, allow_pickle=True)
    89	    bank_embs = data["embeddings"]
    90	    bank_paths = data["paths"]
    91	
    92	    query_emb = extract_embedding(model, transform, query_path, device)
    93	    query_emb = query_emb / (np.linalg.norm(query_emb) + 1e-8)
    94	
    95	    # Cosine similarity
    96	    sims = bank_embs @ query_emb
    97	    topk_idx = np.argsort(sims)[::-1][:k]
    98	
    99	    results = [(str(bank_paths[i]), float(sims[i])) for i in topk_idx]
   100	    return results
   101	
   102	
   103	if __name__ == "__main__":
   104	    manifest_path = "/hdd1/jiangxi/AD-Agent/benchmark/manifests/full_manifest.json"
   105	    output_dir = "/hdd1/jiangxi/AD-Agent/benchmark/retrieval_index"
   106	    os.makedirs(output_dir, exist_ok=True)
   107	
   108	    device = "cuda" if torch.cuda.is_available() else "cpu"
   109	    print(f"Loading {MODEL_NAME} on {device}...")
   110	    model, transform = load_model(device)
   111	
   112	    domains = ["D1", "D2", "D4", "D5", "D5b", "D5c", "D5d", "D7", "D9", "D10"]
   113	    for dc in domains:
   114	        build_index_for_domain(manifest_path, dc, output_dir, model, transform, device)
   115	
   116	    print("\nDone! Retrieval indices saved to:", output_dir)

 succeeded in 0ms:
     1	# AnomalyClaw v6 Real Agent — Experimental Results
     2	
     3	**Date**: 2026-04-17
     4	**Status**: All Qwen3.5 + SeedVL variants complete. v6.5 in progress.
     5	
     6	## Executive Summary
     7	
     8	We re-implemented AnomalyClaw as a per-item autonomous ReAct agent (v6)
     9	with 16 tools and K=5 turn budget, and compared against fair Direct and
    10	Fixed-fusion baselines across two VLM backbones. **The agent does NOT
    11	beat Direct VLM in any of the prompt variants we tried.** The ReAct
    12	architecture's tool overhead outweighs its contribution because on many
    13	domains (especially medical imaging, change detection) tool outputs
    14	mislead rather than help the VLM.
    15	
    16	## TL;DR — BEST RESULT
    17	
    18	**Best method = Ensemble(Direct, Agent_v6.5 or v6.6) via `compose_ensemble.py`**
    19	
    20	| Backbone | Direct | Fusion (w=0.2) | Best Agent alone | **Ensemble (α=0.5)** |
    21	|----------|--------|----------------|------------------|----------------------|
    22	| Qwen3.5-VL-27B | 0.7684 | 0.8142 | v6.5: 0.7713 | **0.8136** (v6.5+D, +4.53pp p=0.0005) |
    23	| SeedVL         | 0.7995 | 0.8075 | v6: 0.7823 | 0.8089 (v6+D, +0.93pp p=0.29) |
    24	| GPT-5.4        | 0.8463 | 0.8550 | v6.6: 0.8573 | **0.8637** (v6.6+D, +1.74pp) |
    25	
    26	Ensemble is built offline from cached Direct + Agent result files:
    27	```
    28	python benchmark/scripts/compose_ensemble.py \
    29	  --direct benchmark/results/v6_direct_gpt_test.json \
    30	  --agent benchmark/results/v6_6_agent_gpt_test.json \
    31	  --output benchmark/results/v6_ensemble_v6_6_gpt_test.json
    32	```
    33	
    34	## Main Results
    35	
    36	### Qwen3.5-VL-27B — 12-domain test (n=1418)
    37	
    38	| System | Descriptor | Macro AUROC | vs Direct-task | vs Direct-generic |
    39	|--------|------------|-------------|----------------|-------------------|
    40	| Direct (task descriptor) | domain hint | **0.7684** | — | +4.7pp |
    41	| Direct (generic)         | no hint     | 0.7215 | -4.7pp | — |
    42	| Fusion w=0.2 SubspaceAD (task) | domain hint | **0.8142** | +4.6pp | +9.3pp |
    43	| Fusion w=0.2 SubspaceAD (generic) | no hint | 0.7641 | -0.4pp | +4.3pp |
    44	| **Agent v6** (A-regime, free score) | no hint | 0.7253 | -4.3pp | **+0.4pp** ≈ tie |
    45	| Agent v6.2 (A-regime, score_from_v0) | no hint | 0.6916 | -7.7pp | -3.0pp |
    46	| Agent v6.4 (B-regime, score_from_v0) | domain hint | 0.7158 | -5.3pp | -0.6pp |
    47	| Agent v6.5 (B-regime, free score) | domain hint | *running* | — | — |
    48	
    49	### SeedVL (doubao-seed-2.0-lite) — 12-domain test (n=1418)
    50	
    51	| System | Macro AUROC |
    52	|--------|-------------|
    53	| Direct (task descriptor) | **0.7995** |
    54	| Fusion w=0.2 SubspaceAD | **0.8075** |
    55	| Agent v6 | 0.7823 (−1.7pp vs Direct) |
    56	
    57	### Per-domain Agent v6 (Qwen3.5) vs Direct-task
    58	
    59	| Domain | Direct-task | Agent v6 | Δ |
    60	|--------|------------|----------|---|
    61	| D1 (MVTec-AD industrial) | 0.919 | 0.947 | +2.8 ✓ |
    62	| D2 (GoodsAD retail)       | 0.725 | 0.600 | **−12.5** ✗ |
    63	| D4 (SDNET infra cracks)   | 0.794 | 0.761 | −3.3 |
    64	| D5 (Dermoscopy)           | 0.701 | 0.639 | −6.2 |
    65	| D5b (Brain MRI)           | 0.855 | 0.876 | +2.1 ✓ |
    66	| D5c (Liver CT)            | 0.624 | 0.643 | +1.9 ≈ |
    67	| D5d (GI endoscopy)        | 0.905 | 0.654 | **−25.1** ✗ |
    68	| D6 (LEVIR change det.)    | 0.792 | 0.570 | **−22.2** ✗ |
    69	| D7 (Road BDD100K)         | 0.923 | 0.961 | +3.8 ✓ |
    70	| D8 (Avenue surveillance)  | 0.616 | 0.585 | −3.1 |
    71	| D9 (MVTec-LOCO logical)   | 0.564 | 0.586 | +2.2 ≈ |
    72	| D10 (VisA industrial)     | 0.801 | 0.882 | +8.1 ✓ |
    73	
    74	**Wins (≥+2pp)**: D1, D5b, D7, D10 (4)
    75	**Losses (≥−2pp)**: D2, D4, D5, D5d, D6, D8 (6)
    76	**Ties**: D5c, D9 (2)
    77	
    78	## Success Criteria Check (from spec §7)
    79	
    80	- Minimal (Agent > Direct by ≥ 2pp on ≥ 2/3 backbones): **FAIL**
    81	  - Qwen3.5 B-regime: Agent 0.7158 vs Direct 0.7684 → −5.3pp
    82	  - Qwen3.5 A-regime (fair): Agent 0.7253 vs Direct 0.7215 → **+0.4pp** (tied)
    83	  - SeedVL: Agent 0.7823 vs Direct 0.7995 → −1.7pp
    84	
    85	- Solid (≥ 3pp on all 3): **FAIL**
    86	- Strong (Agent > Fusion on ≥ 1): **FAIL** (agent loses to Fusion on both backbones)
    87	
    88	## Why Agent Fails — Diagnostic Findings
    89	
    90	### 1. Prompt-artifact penalty from "no domain hint"
    91	
    92	Sub-analysis of v6 (Qwen3.5):
    93	
    94	| Subset | n | Agent macro | Direct-task macro on same items | Δ |
    95	|--------|---|-------------|----------------------------------|---|
    96	| Agent decided at turn 1 without tools | 318 | 0.6115 | 0.8358 | **−22.4** |
    97	| Agent called ≥ 1 tool | 1100 | 0.6889 | 0.7355 | −4.7 |
    98	
    99	The −22.4pp hit on "agent answers turn 1 without tools" is **pure prompt
   100	penalty**: without a domain hint, VLM over-predicts "anomalous" on
   101	unfamiliar image types (observed on D5d/D6 calibration items: ~90% scored
   102	0.95 when GT=0). The agent's prompt is structurally handicapped vs
   103	`build_prompt_v0(domain, has_refs=True)`.
   104	
   105	### 2. Score calibration: free-form score > score_from_v0 mapping
   106	
   107	Score distribution (Qwen3.5 full test):
   108	
   109	| System | %<0.1 | %<0.5 | %>0.5 | %>0.9 |
   110	|--------|-------|-------|-------|-------|
   111	| v6 (free 0–1 score) | 7.3% | 46.1% | 53.9% | 37.0% |
   112	| v6.4 (score_from_v0) | 39.5% | 55.8% | 44.2% | 39.7% |
   113	
   114	`score_from_v0(label, confidence)` pushes 80% of items into extremes
   115	(<0.1 or >0.9), hurting AUROC's rank-ordering vs the VLM's continuous
   116	free-form score. Surprisingly, v6 (no calibration pass) has *better*
   117	distribution than v6.2/v6.4.
   118	
   119	### 3. Tool misuse on non-industrial domains
   120	
   121	- `tool_expert_score` called on 86% (v6) of items. SubspaceAD was designed for
   122	  industrial surface defects; on D6 (change detection) and D5d (endoscopy)
   123	  its signal is noise, which the agent then weights into its final answer.
   124	- `tool_image_diff` on D6 helps find building changes but the agent can't
   125	  tell "change direction" (building added vs removed) → many false positives.
   126	
   127	## What Worked (domain-level)
   128	
   129	Agent v6 beat Direct by ≥ 2pp on 4 domains:
   130	- **D1 (+2.8pp)**: hotspot_cropper + expert_score work well on MVTec-AD textures
   131	- **D5b (+2.1pp)**: Brain MRI — expert helps highlight lesions
   132	- **D7 (+3.8pp)**: Road scenes benefit from reference_profiler
   133	- **D10 (+8.1pp)**: VisA industrial — same story as D1 (biggest win)
   134	
   135	## Tool Usage Distribution (Qwen3.5 v6)
   136	
   137	| Tool | Call count |
   138	|------|------------|
   139	| tool_expert_score | 1222 (86% of items) |
   140	| tool_hotspot_cropper | 556 |
   141	| tool_side_by_side | 399 |
   142	| tool_reference_profiler | 398 |
   143	| tool_image_diff | 291 |
   144	| tool_component_counter | 15 |
   145	| tool_zoom_bbox | 11 |
   146	| tool_rotate_align | 8 |
   147	| tool_patch_grid | 8 |
   148	| tool_segment_and_count | 4 |
   149	| tool_texture_fft | 3 |
   150	| tool_reference_retriever | 0 |
   151	| tool_domain_knowledge | 0 |
   152	
   153	Agent does not use 3 of the 13 tools. Zoom/patch_grid/rotate_align
   154	barely used. SeedVL uses tools more sparingly (avg 1.68 turns vs
   155	Qwen3.5's 3.06).
   156	
   157	## Honest Assessment
   158	
   159	1. **The "real agent" framing is harder than expected.** Even with 13
   160	   tools and autonomous tool selection, a zero-shot ReAct VLM loses to
   161	   its own zero-shot VLM baseline. The v5 per-domain router (also losing
   162	   to fair baselines in truth) at least avoided this by hardcoding which
   163	   domains get tools.
   164	
   165	2. **A-regime (no domain hint) penalty is prompt-architectural**, not
   166	   agent-architectural. The VLM just performs worse when told nothing
   167	   about what it's inspecting.
   168	
   169	3. **Fusion w=0.2 (no per-domain tuning, no agent) is the actual
   170	   winner** on both backbones. A simple "VLM + SubspaceAD 20% fused"
   171	   beats Direct by +4.6pp on Qwen3.5 and +0.8pp on SeedVL — with zero
   172	   agent overhead. This is what the paper's main contribution should be,
   173	   honestly.
   174	
   175	4. **Tools help in aggregate on some domains, hurt on others.** Net
   176	   effect is negative because catastrophic losses on D5d/D6 (−25, −22pp)
   177	   outweigh +8pp gains on D10.
   178	
   179	## What a Future v7 Would Need
   180	
   181	If we want an agent that actually beats Direct:
   182	
   183	- **Per-item learned routing** trained on the 480-item dev split:
   184	  input = (VLM initial judgment, expert rank, image features) → output =
   185	  which tools to call.
   186	- **Tool-quality estimation**: agent should predict whether a tool's
   187	  output will be reliable before trusting it. E.g. texture_fft on a
   188	  medical MRI returns a periodicity score, but that signal is irrelevant
   189	  for MRI pathology detection.
   190	- **Soft ensemble with initial VLM**: final score = α · VLM_turn1 + (1−α)
   191	  · agent_final, where α is learned.
   192	
   193	## Files
   194	
   195	- Spec: `docs/superpowers/specs/2026-04-16-real-ad-agent-design.md`
   196	- Plan: `docs/superpowers/plans/2026-04-16-real-ad-agent.md`
   197	- Results: `benchmark/results/v6_*_{qwen3,seedvl}_test.json`
   198	- Eval: `refine-logs/v6_eval_*.json`
   199	- Code: `benchmark/scripts/agent_v6*.py`, `agent_tools_v6.py`, `eval_v6.py`,
   200	  `run_baselines_v6.py`

exec
/bin/bash -lc "nl -ba refine-logs/EXPLORATION_JOURNAL.md | sed -n '1,285p'" in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
     1	# AnomalyClaw v6 — Exploration Journal
     2	
     3	Per-round log of hypothesis → change → result → lesson. Newest entries at top.
     4	Append a new block for every experiment iteration.
     5	
     6	---
     7	
     8	## Round 6.8 — Offline compose_ensemble (the actual elegant integration)
     9	**Hypothesis**: True elegance is "one command in, one result out" — but
    10	adding API calls inside the agent runner risks rate-limits (v6.7's issue).
    11	The cleanest design is to separate CONCERNS: Direct and Agent are two
    12	independent passes, then a pure-data composition step.
    13	**Change**: `benchmark/scripts/compose_ensemble.py` — takes two result
    14	JSON files and outputs the ensemble. No VLM calls, no concurrency,
    15	fully deterministic. `anomaly_score = α*direct + (1-α)*agent`. Default
    16	α=0.5.
    17	**Result**: reproduces every ensemble number we had, in ~1 second:
    18	- Qwen3.5 v6.5+D: 0.8136
    19	- Qwen3.5 v6.6+D: 0.8036
    20	- SeedVL v6+D:    0.8089
    21	- GPT-5.4 v6.6+D: **0.8637** (best overall)
    22	**Lesson**: "integrated" doesn't require a single Python call chain when
    23	you can separate compute (Direct pass, Agent pass) from composition
    24	(average scores). The paper method is cleanly described in 3 lines.
    25	
    26	---
    27	
    28	## Round 6.7 — Integrated Direct-turn0 + ReAct (implementation bug, not reusable)
    29	**Hypothesis**: Data from v6.6 shows post-hoc ensemble (agent + separate
    30	Direct call) > self-ensemble (initial_score + final inside one prompt).
    31	But user wants the ensemble INSIDE the agent, not external.
    32	**Change**: Agent runner now performs a Direct VLM call (`build_prompt_v0`)
    33	on "turn 0" before starting the ReAct loop. Agent's exported
    34	`anomaly_score = 0.5 * (direct_score + agent_final_score)`. Single CLI,
    35	single output file, invisible to caller.
    36	**Result (GPT-5.4 test, n=1418)**: **macro = 0.6001 — FAILED**. 1106/1418
    37	items errored with "malformed JSON after retries" during the ReAct loop
    38	(which succeeded perfectly in v6.6 on the same items). Only items where
    39	the agent decided "final" on turn 1 survived.
    40	**Root cause (diagnosed)**: running direct_turn0 BEFORE the agent loop
    41	DOUBLES the outbound-request rate to sub2api per item. With 6 workers,
    42	effective concurrency was ~12 simultaneous GPT-5.4 requests, which
    43	exceeded the proxy's tolerance and many ReAct follow-up calls returned
    44	rate-limit error payloads that weren't JSON.
    45	**Lesson**: integrating the ensemble by adding API calls PER ITEM
    46	amplifies rate-limit exposure on shared infrastructure. Practical solution
    47	is either:
    48	  (a) run direct + agent as two SEPARATE passes over the dataset with
    49	      proper pacing between them (== current post-hoc approach), or
    50	  (b) add retry/backoff on the direct_turn0 call and cap concurrency to
    51	      half of what pure agent uses (3 workers, not 6).
    52	Keeping v6.7 archived; **v6.6 + Direct post-hoc ensemble (0.8637) remains
    53	the best GPT-5.4 method**. For the paper we describe the method as
    54	"run Direct and Agent in parallel, average" — it IS a single well-defined
    55	procedure even if not in one Python function.
    56	
    57	---
    58	
    59	## Round 6.6-ENS — Post-hoc ensemble of v6.6 + Direct (NEW best on GPT-5.4)
    60	**Hypothesis**: v6.6 alone beat Direct by +1.1pp on GPT-5.4. Does adding
    61	post-hoc average with Direct give even more?
    62	**Change**: `final_score = 0.5 * (v6.6_score + direct_score)` per item.
    63	**Result (GPT-5.4, n=1418)**:
    64	- v6.6 alone: 0.8573
    65	- v6.6 + Direct post-hoc: **0.8637** — **+1.74pp vs Direct, +0.87pp vs Fusion**
    66	- Best single-system result we've achieved.
    67	- Qwen3.5 parallel: v6.6+post-hoc = 0.8036 (vs v6.5+post-hoc 0.8136 → still best)
    68	
    69	**Lesson**: self-ensemble (v6.6) and post-hoc ensemble can STACK on strong
    70	VLMs. GPT-5.4's initial_score is high quality → self-ensemble helps.
    71	Then adding a separate Direct call further de-correlates errors.
    72	
    73	## Round 6.6 — Self-ensemble inside a single prompt (mixed result)
    74	**Hypothesis**: Have agent emit `initial_score` (gut judgment, pre-tool)
    75	alongside its action on turn 1, and `final_score` on the last turn. System
    76	outputs `0.5 * (initial_score + final_score)`. Eliminates external ensemble.
    77	**Change**: v6.6 prompt adds `initial_score` requirement on turn 1.
    78	`agent_v6_6.py` captures both scores and computes the blend internally.
    79	**Result**:
    80	- GPT-5.4: macro = **0.8573** — beats Direct (+1.1pp), beats Fusion (+0.2pp)
    81	  (p=0.26 vs Direct, p=0.81 vs Fusion — low power with 12 domains)
    82	  avg turns = 1.26 (GPT uses tools 26% of items)
    83	- Qwen3.5: macro = **0.7412** — WORSE than v6.5's 0.7713
    84	  avg turns = 1.58
    85	**Why the asymmetry**: GPT-5.4's initial_score is high-quality (it's a
    86	competent zero-shot scorer). Qwen3.5's initial_score, when it has to SHARE
    87	prompt space with action/tool selection, gets degraded — Qwen3.5 can't do
    88	both well at once. Averaging a weak initial with a better final drags the
    89	better one down.
    90	**Comparison**:
    91	- GPT-5.4: v6.6 alone = 0.8573, v6.6 + post-hoc ensemble with Direct = **0.8637**
    92	- Qwen3.5: v6.6 alone = 0.7412, v6.6 + post-hoc ensemble = 0.8036
    93	  vs v6.5 + post-hoc = 0.8136 (still best)
    94	**Lesson**: when asking the VLM to multitask within a turn (judge + route
    95	+ rank), weaker VLMs get confused. Separate the judging call from the
    96	routing call — v6.7 integrates this.
    97	
    98	---
    99	
   100	## Round 6.5-ENS — Post-hoc average ensemble of v6.5 agent + Direct
   101	**Hypothesis**: v6.5's and Direct's errors are on different items → their average should
   102	outperform either alone.
   103	**Change**: `final = 0.5 * v6_5_score + 0.5 * direct_score` per item (external).
   104	**Result (Qwen3.5, n=1418)**:
   105	- Ensemble macro = **0.8136**  [95% CI 0.7918, 0.8347]
   106	- Direct macro = 0.7684
   107	- Delta **+4.53pp, p=0.0005** (paired permutation, 2 000 perms)
   108	- Matches Fusion (0.8142, w=0.2 SubspaceAD) within 0.06pp.
   109	
   110	**SeedVL check**:
   111	- Ensemble = 0.8089, Direct = 0.7995 → +0.93pp, p=0.29 (not significant)
   112	- Gain is Qwen3.5-specific; SeedVL's agent & direct are more correlated.
   113	
   114	**Lesson**: complementarity of agent + direct is model-dependent. Qwen3.5 has high
   115	variance between direct vs agent paths → ensemble exploits disagreement.
   116	User feedback: ensemble as external step is inelegant → needs integration into
   117	agent (v6.6 plan).
   118	
   119	---
   120	
   121	## Round 6.5 — B-regime + free score (WINNER single-system)
   122	**Hypothesis**: v6.4 underperformed because `score_from_v0` bimodalized scores; use v6.4's
   123	domain hint but keep v6's free-form 0-1 score.
   124	**Change**:
   125	- Inherit v6's SYSTEM_PROMPT and `{"action":"final","score":0.0-1.0}` schema.
   126	- Override `_build_initial_messages` to inject `DOMAIN_CONTEXT[d]` text (same hint
   127	  Direct gets).
   128	- No `score_from_v0` remapping.
   129	**Result (Qwen3.5 test, n=1418)**:
   130	- Macro = **0.7713** (v6 was 0.7253, Direct-task was 0.7684 → v6.5 beats Direct by +0.3pp
   131	  but p=0.86 not significant as single system)
   132	- Wins ≥+2pp on 7/12 domains: D1 (+5.0), D2 (+5.8), D5b (+7.7), D5c (+4.1), D8 (+7.0),
   133	  D9 (+5.1), D10 (+9.9)
   134	- Losses on 3: D4 (-4.2), D5d (-25.8), D6 (-11.2)
   135	- Avg turns = 3.22; top tools: expert_score (81%), hotspot_cropper (43%),
   136	  side_by_side (35%), reference_profiler (32%), image_diff (21%)
   137	
   138	**Lesson**: domain hint + free-form score is the right combination. The agent doesn't
   139	need to re-invent score calibration. Remaining losses (D5d, D6) are SubspaceAD-misleading
   140	failures — agent still over-trusts the expert on medical / change detection domains.
   141	
   142	---
   143	
   144	## Round 6.4 — B-regime + score_from_v0 (failed via score mapping)
   145	**Hypothesis**: give agent the same domain hint Direct gets → fair B-regime comparison.
   146	**Change**: v6.2 prompt + `DOMAIN_CONTEXT[d]` injection in user message.
   147	**Result (Qwen3.5)**:
   148	- Macro = 0.7158  (vs v6's 0.7253, Direct-task 0.7684)
   149	- D6 AUROC jumped from 0.57 (v6) to 0.73 (v6.4) — **big win on change detection**
   150	- D5d still at 0.54 (worse)
   151	- Score distribution 80% concentrated at <0.1 or >0.9 — bimodal from `score_from_v0`.
   152	
   153	**Lesson**: domain hint helps semantics (D6 +16pp). But `score_from_v0` maps
   154	`{label, confidence}` to bimodal scores which hurts AUROC's rank ordering vs
   155	the VLM's native continuous score.
   156	
   157	---
   158	
   159	## Round 6.3 — Forced reference description + "unfamiliar ≠ anomalous" hint
   160	**Hypothesis**: v6's turn-1 agent defaults to "anomalous" on unfamiliar image types
   161	(observed 90% false positive on D5d/D6 calibration). Forcing the agent to describe
   162	what the refs show first should fix this.
   163	**Change**: SYSTEM_PROMPT requires turn-1 `thought` start with "The reference images
   164	show ..." + anti-false-positive rule + conservative bias.
   165	**Result (D5d/D6 sanity, n=20)**: D6 AUROC = 0.265 (**worse than random!**, inverted).
   166	Confidence gating + "describe first" actively made the VLM worse on change detection.
   167	**Lesson**: over-specifying VLM behavior via prompt can hurt. "Unfamiliar is not
   168	anomalous" is too vague without domain info. Killed before full run.
   169	
   170	---
   171	
   172	## Round 6.2 — A-regime + score_from_v0 calibration (failed)
   173	**Hypothesis**: v6's self-reported score had worse calibration than Direct's
   174	`score_from_v0(label, confidence)`. Making agent output `{label, confidence}` and
   175	reusing the same mapping should align calibration.
   176	**Change**: prompt asks for `{action:"final", label, confidence, rationale}` instead
   177	of `score`. `_parse_action` computes `score = score_from_v0({label, confidence})`.
   178	**Result (Qwen3.5 full, n=1418)**: Macro = **0.6916** — worse than v6's 0.7253 by
   179	-3.4pp. D2 dropped to 0.52, D5c to 0.44.
   180	**Lesson**: the score-calibration remap BIMODALIZES scores (80% at extremes) and
   181	destroys AUROC rank ordering. Don't replace v6's free-form score.
   182	
   183	---
   184	
   185	## Round 6.1 — Confidence-gated tool use (failed catastrophically)
   186	**Hypothesis**: If agent's initial confidence ≥ 75, skip tools (avoids tool noise).
   187	**Change**: prompt adds rule "if initial_confidence ≥ 75, MUST output final
   188	without calling any tool".
   189	**Result (D5d/D6 sanity, n=10)**: On 10 GT=normal items, agent scored 0.92-0.98
   190	with confidence 95 → rule locked in wrong high-confidence predictions. Domain
   191	items VLM can't recognize → VLM over-confidently says "anomalous" without domain
   192	hint → rule traps this error.
   193	**Lesson**: Self-reported confidence is not trustworthy; making it the early-exit
   194	gate amplifies the VLM's overconfidence failure mode. Killed before full run.
   195	
   196	---
   197	
   198	## Round 6.0 — Initial A-regime ReAct (baseline agent)
   199	**Hypothesis**: zero-shot ReAct agent with 13 tools and K=5 turn budget can match
   200	Direct VLM without any domain hint.
   201	**Change**: full implementation per spec §4 — agent sees only `query + 4 refs`,
   202	decides tool vs final on each turn, 13 tools via TOOL_REGISTRY.
   203	**Result (Qwen3.5 full, n=1418)**:
   204	- Macro = 0.7253 (vs Direct-task 0.7684, Direct-generic 0.7215, Fusion 0.8142)
   205	- A-regime fair comparison (vs Direct-generic): **+0.4pp tied**
   206	- B-regime unfair (vs Direct-task): -4.3pp
   207	- Per-domain: wins on D1/D10/D7 (+2-8pp), catastrophic -22/-25pp on D5d/D6
   208	- 22.4% of items solved at turn 1 with no tools (but these had macro 0.61 vs
   209	  Direct's 0.84 on same items — prompt handicap penalty)
   210	
   211	**SeedVL parallel**: Agent 0.7823 vs Direct 0.7995 (-1.7pp). Same pattern.
   212	**Lesson**: pure "no-domain-info" agent handicaps itself. Score distribution
   213	analysis shows free-form score > score_from_v0 for AUROC. Need domain hint.
   214	
   215	---
   216	
   217	## Baselines — Before any agent iteration
   218	**Setup**: Direct VLM (`build_prompt_v0` + domain context) and fixed-w=0.2 fusion
   219	with SubspaceAD raw score, calibration-median sigmoid center.
   220	
   221	**Qwen3.5 (n=1418)**:
   222	- Direct-task (domain hint): 0.7684
   223	- Direct-generic (no hint, `DESCRIPTOR_MODE=generic`): 0.7215
   224	- Fusion-task: 0.8142  (+4.6pp, p=0.0005 vs Direct-task)
   225	- Fusion-generic: 0.7641
   226	
   227	**SeedVL (n=1418)**:
   228	- Direct: 0.7995
   229	- Fusion: 0.8075
   230	
   231	**Lesson**: fusion alone (SubspaceAD 20% weight) accounts for +5pp out of v5's
   232	reported "+6.3pp" — most gain is from adding an expert, not from per-domain routing.
   233	
   234	---
   235	
   236	## Infrastructure Findings
   237	
   238	- **vLLM TP > 1 broken** on this machine (NCCL/P2P issue, see
   239	  `/hdd1/models/MULTI_GPU_ISSUES.md`). Use TP=1 replicas + round-robin LB.
   240	- **Replica count sweet spot = 2 replicas × 16 workers** (not 4×24 as
   241	  initially tried):
   242	  - 4 replicas × 24 workers: 0.31 items/sec for v6.5 agent
   243	  - 2 replicas × 16 workers: 0.50 items/sec for v6.6 agent (60% faster!)
   244	  - At 4 replicas, KV-cache contention and thread oversubscription hurt
   245	    throughput. GPU util was 100% on one replica but only 60% on others.
   246	  - At 2 replicas, GPUs hover at 55-70% util — headroom exists but adding
   247	    workers hits the "multi-turn sessions compete for same shard" limit.
   248	- **Release GPUs when idle**: each replica holds ~41GB VRAM. After each
   249	  benchmark, `pkill -f Qwen3.5` and `pkill -f vllm_lb` immediately frees
   250	  GPU 0-3 for other users.
   251	- **Agent adds ~4x VLM calls per item** (avg 3.22 turn × 1 call + retries).
   252	- **SeedVL JSON compliance**: ~2% items fail JSON parse after retries; masked to
   253	  score 0.5.
   254	- **Manifest**: must use `benchmark/manifests/full_manifest.json` (v1 codes,
   255	  D1/D2/D4/D5/D5b/c/d/D6/D7/D8/D9/D10) because expert caches align with v1, not v2.
   256	
   257	---
   258	
   259	## Open directions
   260	
   261	- **v6.6** (planned): self-ensemble integrated into agent (turn-1 initial score +
   262	  final score, internal blend). Eliminates external averaging step.
   263	- **v7** (future): learned per-item router on 480-item dev split. Target = close
   264	  oracle gap (0.8259 vs 0.8136, +1.2pp headroom).
   265	- **GPT-5.4** (queued): full direct + agent + ensemble benchmark. sub2api fixed.
   266	- **GPU util tuning**: test 2/3/4 replicas on next Qwen3.5 run.

exec
/bin/bash -lc "python - <<'PY'
import json, os
for p in ['benchmark/results/v6_7_agent_gpt_test.json','benchmark/results/v6_6_agent_gpt_test.json']:
    if os.path.exists(p):
        data=json.load(open(p)); vals=list(data.values()) if isinstance(data,dict) else data
        print(p, len(vals))
        for x in vals[:3]: print({k:x.get(k) for k in ['item_id','anomaly_score','direct_score','agent_final_score','error']})
PY" in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
benchmark/results/v6_7_agent_gpt_test.json 425
{'item_id': 'D1_0077', 'anomaly_score': 0.08999999999999997, 'direct_score': 0.08999999999999997, 'agent_final_score': None, 'error': 'malformed JSON after retries'}
{'item_id': 'D1_0085', 'anomaly_score': 0.050000000000000044, 'direct_score': 0.050000000000000044, 'agent_final_score': None, 'error': 'malformed JSON after retries'}
{'item_id': 'D1_0051', 'anomaly_score': 0.050000000000000044, 'direct_score': 0.050000000000000044, 'agent_final_score': None, 'error': 'malformed JSON after retries'}
benchmark/results/v6_6_agent_gpt_test.json 1418
{'item_id': 'D1_0077', 'anomaly_score': 0.1, 'direct_score': None, 'agent_final_score': None, 'error': None}
{'item_id': 'D1_0063', 'anomaly_score': 0.1, 'direct_score': None, 'agent_final_score': None, 'error': None}
{'item_id': 'D1_0051', 'anomaly_score': 0.09, 'direct_score': None, 'agent_final_score': None, 'error': None}

exec
/bin/bash -lc "python - <<'PY'
import json, glob, os
paths=['benchmark/results/v6_direct_qwen3_test.json','benchmark/results/v6_5_agent_qwen3_test.json','benchmark/results/v6_6_agent_gpt_test.json','benchmark/results/v6_direct_gpt_test.json','benchmark/results/v6_fusion_qwen3_test.json','benchmark/results/subspacead_test.json']
for p in paths:
    if not os.path.exists(p):
        print('MISSING',p); continue
    data=json.load(open(p)); vals=list(data.values()) if isinstance(data,dict) else data
    print(p, len(vals), 'ids', len({x.get('item_id') for x in vals}), 'errs', sum(1 for x in vals if x.get('error')))
    print(' first keys', sorted(vals[0].keys()) if vals else [])
# D8 fusion missing expert fallback count
p='benchmark/results/v6_fusion_qwen3_test.json'
if os.path.exists(p):
    vals=json.load(open(p))
    from collections import Counter
    miss=Counter(x.get('domain_code') for x in vals if x.get('expert_score') is None)
    total=Counter(x.get('domain_code') for x in vals)
    print('fusion missing expert by domain', miss)
    print('fusion total by domain', total)
# ensemble matching check if file exists
for p in glob.glob('benchmark/results/v6_ensemble*_test.json'):
    vals=json.load(open(p)); print('ensemble',p,len(vals), Counter(x.get('source') for x in vals))
PY" in /hdd1/jiangxi/AD-Agent
exec
/bin/bash -lc "python - <<'PY'
import numpy as np, os, json, glob
manifest='benchmark/manifests/full_manifest.json'
if os.path.exists(manifest):
    m=json.load(open(manifest))
    query_by_path={x['query_path']:x for x in m}
    for idx in sorted(glob.glob('benchmark/retrieval_index/*_index.npz')):
        data=np.load(idx, allow_pickle=True)
        paths=[str(p) for p in data['paths']]
        hits=[query_by_path[p]['item_id'] for p in paths if p in query_by_path]
        print(os.path.basename(idx), 'n_paths',len(paths),'paths_that_are_queries',len(hits), hits[:5])
PY" in /hdd1/jiangxi/AD-Agent
 succeeded in 195ms:
benchmark/results/v6_direct_qwen3_test.json 1418 ids 1418 errs 0
 first keys ['anomaly_score', 'domain_code', 'error', 'item_id', 'label_gt', 'raw_output']
benchmark/results/v6_5_agent_qwen3_test.json 1418 ids 1418 errs 6
 first keys ['anomaly_score', 'confidence', 'domain_code', 'error', 'item_id', 'label_gt', 'n_turns', 'rationale', 'tools_used']
benchmark/results/v6_6_agent_gpt_test.json 1418 ids 1418 errs 0
 first keys ['anomaly_score', 'confidence', 'domain_code', 'error', 'item_id', 'label_gt', 'n_turns', 'rationale', 'tools_used']
benchmark/results/v6_direct_gpt_test.json 1418 ids 1418 errs 0
 first keys ['anomaly_score', 'domain_code', 'error', 'item_id', 'label_gt', 'raw_output']
benchmark/results/v6_fusion_qwen3_test.json 1418 ids 1418 errs 0
 first keys ['anomaly_score', 'direct_score_orig', 'domain_code', 'error', 'expert_score', 'fusion_median', 'fusion_w', 'item_id', 'label_gt', 'raw_output']
benchmark/results/subspacead_test.json 1298 ids 1298 errs 0
 first keys ['anomaly_score', 'anomaly_score_norm', 'domain', 'domain_code', 'error', 'item_id', 'label_gt', 'label_pred', 'split', 'top_patches']
fusion missing expert by domain Counter({'D8': 120})
fusion total by domain Counter({'D1': 120, 'D2': 120, 'D4': 120, 'D5': 120, 'D7': 120, 'D8': 120, 'D9': 120, 'D10': 120, 'D5b': 120, 'D5c': 120, 'D5d': 120, 'D6': 98})
ensemble benchmark/results/v6_ensemble_v6_6_gpt_test.json 1418 Counter({'ensemble': 1418})
ensemble benchmark/results/v6_ensemble_v6_6_qwen3_test.json 1418 Counter({'ensemble': 1418})
ensemble benchmark/results/v6_ensemble_seedvl_test.json 1418 Counter({None: 1418})
ensemble benchmark/results/v6_ensemble_v6_seedvl_test.json 1418 Counter({'ensemble': 1418})
ensemble benchmark/results/v6_ensemble_v6_5_qwen3_test.json 1418 Counter({'ensemble': 1418})

 succeeded in 388ms:
D10_index.npz n_paths 120 paths_that_are_queries 0 []
D1_index.npz n_paths 150 paths_that_are_queries 0 []
D2_index.npz n_paths 909 paths_that_are_queries 0 []
D4_index.npz n_paths 60 paths_that_are_queries 0 []
D5_index.npz n_paths 20 paths_that_are_queries 20 ['D5_0003', 'D5_0011', 'D5_0017', 'D5_0018', 'D5_0005']
D5b_index.npz n_paths 1595 paths_that_are_queries 0 []
D5c_index.npz n_paths 1076 paths_that_are_queries 0 []
D5d_index.npz n_paths 20 paths_that_are_queries 20 ['D5d_0002', 'D5d_0006', 'D5d_0017', 'D5d_0003', 'D5d_0012']
D7_index.npz n_paths 90 paths_that_are_queries 90 ['D7_0071', 'D7_0057', 'D7_0016', 'D7_0077', 'D7_0030']
D9_index.npz n_paths 50 paths_that_are_queries 0 []

exec
/bin/bash -lc "python - <<'PY'
import json, numpy as np, os, glob
m=json.load(open('benchmark/manifests/full_manifest.json'))
query_by_path={x['query_path']:x for x in m}
from collections import Counter,defaultdict
for idx in sorted(glob.glob('benchmark/retrieval_index/*_index.npz')):
    data=np.load(idx, allow_pickle=True)
    hits=[query_by_path[str(p)] for p in data['paths'] if str(p) in query_by_path]
    if hits:
        print(os.path.basename(idx), len(hits), 'splits', Counter(h['split'] for h in hits), 'labels', Counter(h['label'] for h in hits), 'first', [(h['item_id'],h['split'],h['label']) for h in hits[:10]])
PY" in /hdd1/jiangxi/AD-Agent
 succeeded in 185ms:
D5_index.npz 20 splits Counter({'test': 12, 'dev': 6, 'calibration': 2}) labels Counter({0: 20}) first [('D5_0003', 'test', 0), ('D5_0011', 'dev', 0), ('D5_0017', 'dev', 0), ('D5_0018', 'test', 0), ('D5_0005', 'test', 0), ('D5_0010', 'calibration', 0), ('D5_0009', 'calibration', 0), ('D5_0015', 'dev', 0), ('D5_0001', 'test', 0), ('D5_0019', 'test', 0)]
D5d_index.npz 20 splits Counter({'test': 14, 'calibration': 3, 'dev': 3}) labels Counter({0: 20}) first [('D5d_0002', 'test', 0), ('D5d_0006', 'calibration', 0), ('D5d_0017', 'dev', 0), ('D5d_0003', 'test', 0), ('D5d_0012', 'test', 0), ('D5d_0016', 'calibration', 0), ('D5d_0018', 'test', 0), ('D5d_0011', 'test', 0), ('D5d_0000', 'test', 0), ('D5d_0001', 'test', 0)]
D7_index.npz 90 splits Counter({'test': 60, 'dev': 20, 'calibration': 10}) labels Counter({0: 90}) first [('D7_0071', 'test', 0), ('D7_0057', 'test', 0), ('D7_0016', 'test', 0), ('D7_0077', 'test', 0), ('D7_0030', 'dev', 0), ('D7_0020', 'test', 0), ('D7_0048', 'test', 0), ('D7_0026', 'test', 0), ('D7_0088', 'calibration', 0), ('D7_0070', 'test', 0)]

exec
/bin/bash -lc "python - <<'PY'
import json, os
from collections import Counter
for p in ['benchmark/results/v6_5_agent_qwen3_test.json','benchmark/results/v6_6_agent_qwen3_test.json','benchmark/results/v6_6_agent_gpt_test.json','benchmark/results/v6_agent_qwen3_test.json','benchmark/results/v6_agent_seedvl_test.json']:
    if os.path.exists(p):
        data=json.load(open(p)); c=Counter()
        for x in data:
            for t in x.get('tools_used') or []: c[t]+=1
        print(p, c.get('tool_reference_retriever',0), c.most_common(5))
PY" in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
benchmark/results/v6_5_agent_qwen3_test.json 0 [('tool_expert_score', 1155), ('tool_hotspot_cropper', 609), ('tool_side_by_side', 502), ('tool_reference_profiler', 459), ('tool_image_diff', 297)]
benchmark/results/v6_6_agent_qwen3_test.json 0 [('tool_side_by_side', 230), ('tool_expert_score', 182), ('tool_image_diff', 151), ('tool_zoom_bbox', 86), ('tool_hotspot_cropper', 75)]
benchmark/results/v6_6_agent_gpt_test.json 1 [('tool_expert_score', 135), ('tool_hotspot_cropper', 66), ('tool_domain_knowledge', 58), ('tool_image_diff', 50), ('tool_component_counter', 14)]
benchmark/results/v6_agent_qwen3_test.json 0 [('tool_expert_score', 1222), ('tool_hotspot_cropper', 556), ('tool_side_by_side', 399), ('tool_reference_profiler', 398), ('tool_image_diff', 291)]
benchmark/results/v6_agent_seedvl_test.json 0 [('tool_expert_score', 573), ('tool_hotspot_cropper', 188), ('tool_reference_profiler', 76), ('tool_zoom_bbox', 46), ('tool_side_by_side', 27)]

exec
/bin/bash -lc "python - <<'PY'
import json
p='benchmark/results/v6_6_agent_gpt_test.json'
data=json.load(open(p))
for x in data:
    if 'tool_reference_retriever' in (x.get('tools_used') or []): print(x)
PY" in /hdd1/jiangxi/AD-Agent
 succeeded in 0ms:
{'item_id': 'D5b_0078', 'domain_code': 'D5b', 'label_gt': 0, 'anomaly_score': 0.19, 'rationale': 'No convincing focal lesion or asymmetric mass effect is visible. The main difference is global brightness/contrast rather than localized abnormality, so this looks likely normal.', 'n_turns': 2, 'tools_used': ['tool_reference_retriever'], 'confidence': 72, 'error': None}

exec
/bin/bash -lc "python - <<'PY'
import json, os, sys
sys.path.insert(0,'benchmark/scripts')
from eval_v6 import macro_auroc
pairs=[('benchmark/results/v6_direct_qwen3_test.json','benchmark/results/v6_5_agent_qwen3_test.json')]
for dpath,apath in pairs:
    if not os.path.exists(dpath) or not os.path.exists(apath): continue
    d={x['item_id']:x for x in json.load(open(dpath))}
    a={x['item_id']:x for x in json.load(open(apath))}
    out_old=[]; out_new=[]; changed=[]
    for iid in sorted(set(d)|set(a)):
        dx, ax=d.get(iid), a.get(iid)
        ds=dx.get('anomaly_score') if dx and not dx.get('error') else None
        as_=ax.get('anomaly_score') if ax and not ax.get('error') else None
        # old compose ignores error
        ods=dx.get('anomaly_score') if dx else None; oas=ax.get('anomaly_score') if ax else None
        base=ax or dx
        if ods is not None and oas is not None: oscore=0.5*ods+0.5*oas
        elif ods is not None: oscore=ods
        elif oas is not None: oscore=oas
        else: continue
        if ds is not None and as_ is not None: nscore=0.5*ds+0.5*as_
        elif ds is not None: nscore=ds
        elif as_ is not None: nscore=as_
        else: continue
        rec={k:base.get(k) for k in ['item_id','domain_code','label_gt']}
        out_old.append({**rec,'anomaly_score':oscore})
        out_new.append({**rec,'anomaly_score':nscore})
        if abs(oscore-nscore)>1e-12: changed.append((iid, oscore,nscore, ax.get('error') if ax else None))
    print('old', macro_auroc(out_old)['macro'], 'new', macro_auroc(out_new)['macro'], 'changed', len(changed), changed[:10])
PY" in /hdd1/jiangxi/AD-Agent
 succeeded in 1077ms:
old 0.8136473566183842 new 0.8128137918999799 changed 6 [('D5_0159', 0.275, 0.050000000000000044, 'malformed JSON after retries'), ('D6_0066', 0.275, 0.050000000000000044, 'malformed JSON after retries'), ('D6_0126', 0.74, 0.98, 'malformed JSON after retries'), ('D7_0071', 0.275, 0.050000000000000044, 'malformed JSON after retries'), ('D8_0143', 0.725, 0.95, 'malformed JSON after retries'), ('D9_0143', 0.255, 0.010000000000000009, 'malformed JSON after retries')]

codex
**CRITICAL**

- [refine-logs/EXPLORATION_JOURNAL.md](/hdd1/jiangxi/AD-Agent/refine-logs/EXPLORATION_JOURNAL.md:8), [refine-logs/EXPLORATION_JOURNAL.md](/hdd1/jiangxi/AD-Agent/refine-logs/EXPLORATION_JOURNAL.md:59), [refine-logs/EXPLORATION_JOURNAL.md](/hdd1/jiangxi/AD-Agent/refine-logs/EXPLORATION_JOURNAL.md:100): the final “best” method is selected after repeated test-set evaluations. This is not code-level `label_gt` leakage during scoring, but it is experimental leakage: the reported p-values and “best” claims are no longer confirmatory.
  Exact fix: freeze one method using calibration/dev only, then run once on a truly held-out test set. Report current numbers as exploratory only, or use nested validation / a new test split.

- [benchmark/scripts/build_retrieval_index.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/build_retrieval_index.py:46), [benchmark/scripts/build_retrieval_index.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/build_retrieval_index.py:103), [benchmark/scripts/agent_tools_v6.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_tools_v6.py:388): `tool_reference_retriever` can use retrieval indices built from all manifest `ref_paths`, not split-clean train-only normal banks. I verified current artifacts contain test-query normal images in `D5_index.npz`, `D5d_index.npz`, and `D7_index.npz`; normal test items can self-match with similarity near 1.0. That is test contamination if this tool is used.
  Exact fix: rebuild indices from a dedicated train/calibration normal pool only; exclude every `query_path` from calibration/dev/test; store split/source metadata in the index; at retrieval time filter `path != query_path`.

- [benchmark/scripts/agent_tools_v6.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_tools_v6.py:527): `dispatch_tool` lets model-supplied kwargs override protected context because it starts with `args` and only injects ctx keys if absent. A tool call can override `item_id`, `split`, `query_path`, `ref_paths`, `domain_code`, or `index_dir`, which can accidentally query the wrong cache/split or wrong file.
  Exact fix: reject protected keys in model args, or always overwrite them from `ctx`. Use an allowlist per tool signature for model-controllable args.

- [benchmark/scripts/compose_ensemble.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/compose_ensemble.py:38): ensemble fallback only handles missing scores, not errored records. Agent JSON failures still carry `anomaly_score=0.5`, so `compose_ensemble.py` averages Direct with synthetic 0.5 instead of falling back to Direct. In current Qwen v6.5+D this changes 6 items and slightly changes macro AUROC.
  Exact fix: treat `record["error"] is not None` as missing for that side. Optionally emit `source="direct_only_due_agent_error"`.

- [benchmark/scripts/eval_v6.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/eval_v6.py:139): permutation logic is correct. It swaps per-item A/B scores, not labels, then recomputes macro AUROC. No core math bug found there. Minor fix: report `(count+1)/(n_perm+1)` to avoid zero p-values and disclose method-selection multiplicity.

**MAJOR**

- [benchmark/scripts/agent_v6_5.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_v6_5.py:47), [benchmark/scripts/agent_v6.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_v6.py:269), [benchmark/scripts/agent_v6.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_v6.py:294): v6.5 mutates `self._build_initial_messages` on a shared `ReActAgent` while running multiple threads. Domain hints can race across items. v6.7 has the same pattern at [agent_v6_7.py:101](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_v6_7.py:101).
  Exact fix: do not monkey-patch instance methods. Pass `domain_code` into a thread-safe builder, or instantiate one agent per worker/item.

- [benchmark/scripts/agent_tools_v6.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_tools_v6.py:92), [benchmark/scripts/agent_tools_v6.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_tools_v6.py:102): expert percentile rank is computed against the whole active split. On `split="test"`, that is a transductive use of the full test score distribution. It is label-free, but not a per-item online agent.
  Exact fix: compute percentile ranks against calibration/train expert-score distributions, while looking up only the current item’s raw expert score from the active split.

- [benchmark/scripts/agent_v6_6.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_v6_6.py:169): v6.6 forced-final path does not use the JSON retry helper; one malformed final response falls back or errors, unlike v6 at [agent_v6.py:152](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_v6.py:152).
  Exact fix: factor `_call_with_json_retry(require_initial=False)` into v6.6 and use it for forced-final too.

- [benchmark/scripts/infer.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/infer.py:596), [benchmark/scripts/infer.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/infer.py:607): served-model logging is not enough. It logs only the first unique requested→served pair per process and has no `item_id`, turn, tool, response id, or per-result field. It cannot diagnose the reported 20% per-item drift.
  Exact fix: return `served_model_id` from `call_llm` or add a structured callback, and write per item/per turn `{item_id, phase, turn, requested_model, served_model, response_id, timestamp}` into result JSON or a sidecar JSONL.

- [benchmark/scripts/agent_prompt_v6_6.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_prompt_v6_6.py:3), [benchmark/scripts/agent_v6_6.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_v6_6.py:137), [benchmark/scripts/infer.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/infer.py:459): score calibration documentation is internally inconsistent. v6.6 does not use `score_from_v0`; it averages free-form `initial_score` and free-form final `score`. Direct uses `score_from_v0`. v6.7’s Direct turn uses `score_from_v0`, while its ReAct final uses free score.
  Exact fix: document each score source explicitly in result files: `direct_score_from="score_from_v0"`, `agent_score_from="free_score"`, `initial_score_from="free_score"`.

- [benchmark/scripts/agent_v6_7.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_v6_7.py:111), [benchmark/scripts/agent_v6_7.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_v6_7.py:173): `agent_final_score` is wrong in v6.7 output. `r.score` is overwritten with the ensemble, then recorded as `agent_final_score`.
  Exact fix: save `agent_score = r.score` before blending, record that field, then write ensemble separately.

**MINOR**

- [benchmark/scripts/infer.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/infer.py:532), [benchmark/scripts/infer.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/infer.py:536): hard-coded API keys/base URLs are in source. This is a security and reproducibility problem.
  Exact fix: remove defaults; require env vars or a local ignored config file.

- [refine-logs/V6_RESULTS.md](/hdd1/jiangxi/AD-Agent/refine-logs/V6_RESULTS.md:8), [benchmark/scripts/agent_tools_v6.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_tools_v6.py:503): docs say 16 tools, registry has 13.
  Exact fix: update the result doc or registry count.

- [benchmark/scripts/agent_tools_v6.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_tools_v6.py:4), [benchmark/scripts/agent_v6_5.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_v6_5.py:31): tool docs say domain code is never a modeling input, but v6.5/v6.6/v6.7 inject domain text into the prompt.
  Exact fix: rename A-regime/B-regime clearly and update invariants.

**PUBLISHABILITY**

As a paper about a pure autonomous visual anomaly-detection agent, this is not publishable yet. The cleanest result is not the agent: fixed Direct+SubspaceAD fusion matches or beats most claimed gains, and the strongest reported Qwen improvement is an offline ensemble selected after many test-set iterations. Reviewers will reasonably say the contribution is an ensemble/complementarity trick, not an agentic detection algorithm.

A publishable angle is possible if the paper is reframed honestly: “tool-augmented VLM agents are brittle; simple fusion is a strong baseline; agents help only under identifiable reliability conditions.” For a positive agent paper, you need a frozen dev-selected method, a clean held-out test, no contaminated retrieval bank, and evidence that tool use causally improves rank ordering beyond Direct and fixed fusion.

**SUGGESTED NEXT EXPERIMENTS**

1. Build a pure-agent reliability gate: before calling any expert tool, the agent must predict whether the tool is applicable from visual/domain cues, then either abstain or call one tool. Tune the gate prompt/rules on dev only.

2. Run one-tool causal ablations: Direct-style visual judgment, then exactly one allowed tool family, then final free score. Compare `expert_score`, `reference_profiler`, `image_diff`, and `retriever` under the same K and prompt budget.

3. Fix and use the retrieval tool as a pure visual reference augmenter: clean train-only normal bank, return retrieved images to the VLM, and test whether better references improve agent-alone AUROC without score averaging.

4. Add a self-critique final step instead of post-hoc ensemble: the agent outputs final score plus a tool-reliability assessment, and must downweight any tool it labels unreliable. No external Direct averaging.

5. Create a dev-only routing policy from non-label features available at inference: domain descriptor, first-turn uncertainty, expert raw/rank, and tool observation metadata. Freeze it, then evaluate once on held-out test as a pure agent controller.
tokens used
129,184
**CRITICAL**

- [refine-logs/EXPLORATION_JOURNAL.md](/hdd1/jiangxi/AD-Agent/refine-logs/EXPLORATION_JOURNAL.md:8), [refine-logs/EXPLORATION_JOURNAL.md](/hdd1/jiangxi/AD-Agent/refine-logs/EXPLORATION_JOURNAL.md:59), [refine-logs/EXPLORATION_JOURNAL.md](/hdd1/jiangxi/AD-Agent/refine-logs/EXPLORATION_JOURNAL.md:100): the final “best” method is selected after repeated test-set evaluations. This is not code-level `label_gt` leakage during scoring, but it is experimental leakage: the reported p-values and “best” claims are no longer confirmatory.
  Exact fix: freeze one method using calibration/dev only, then run once on a truly held-out test set. Report current numbers as exploratory only, or use nested validation / a new test split.

- [benchmark/scripts/build_retrieval_index.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/build_retrieval_index.py:46), [benchmark/scripts/build_retrieval_index.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/build_retrieval_index.py:103), [benchmark/scripts/agent_tools_v6.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_tools_v6.py:388): `tool_reference_retriever` can use retrieval indices built from all manifest `ref_paths`, not split-clean train-only normal banks. I verified current artifacts contain test-query normal images in `D5_index.npz`, `D5d_index.npz`, and `D7_index.npz`; normal test items can self-match with similarity near 1.0. That is test contamination if this tool is used.
  Exact fix: rebuild indices from a dedicated train/calibration normal pool only; exclude every `query_path` from calibration/dev/test; store split/source metadata in the index; at retrieval time filter `path != query_path`.

- [benchmark/scripts/agent_tools_v6.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_tools_v6.py:527): `dispatch_tool` lets model-supplied kwargs override protected context because it starts with `args` and only injects ctx keys if absent. A tool call can override `item_id`, `split`, `query_path`, `ref_paths`, `domain_code`, or `index_dir`, which can accidentally query the wrong cache/split or wrong file.
  Exact fix: reject protected keys in model args, or always overwrite them from `ctx`. Use an allowlist per tool signature for model-controllable args.

- [benchmark/scripts/compose_ensemble.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/compose_ensemble.py:38): ensemble fallback only handles missing scores, not errored records. Agent JSON failures still carry `anomaly_score=0.5`, so `compose_ensemble.py` averages Direct with synthetic 0.5 instead of falling back to Direct. In current Qwen v6.5+D this changes 6 items and slightly changes macro AUROC.
  Exact fix: treat `record["error"] is not None` as missing for that side. Optionally emit `source="direct_only_due_agent_error"`.

- [benchmark/scripts/eval_v6.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/eval_v6.py:139): permutation logic is correct. It swaps per-item A/B scores, not labels, then recomputes macro AUROC. No core math bug found there. Minor fix: report `(count+1)/(n_perm+1)` to avoid zero p-values and disclose method-selection multiplicity.

**MAJOR**

- [benchmark/scripts/agent_v6_5.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_v6_5.py:47), [benchmark/scripts/agent_v6.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_v6.py:269), [benchmark/scripts/agent_v6.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_v6.py:294): v6.5 mutates `self._build_initial_messages` on a shared `ReActAgent` while running multiple threads. Domain hints can race across items. v6.7 has the same pattern at [agent_v6_7.py:101](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_v6_7.py:101).
  Exact fix: do not monkey-patch instance methods. Pass `domain_code` into a thread-safe builder, or instantiate one agent per worker/item.

- [benchmark/scripts/agent_tools_v6.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_tools_v6.py:92), [benchmark/scripts/agent_tools_v6.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_tools_v6.py:102): expert percentile rank is computed against the whole active split. On `split="test"`, that is a transductive use of the full test score distribution. It is label-free, but not a per-item online agent.
  Exact fix: compute percentile ranks against calibration/train expert-score distributions, while looking up only the current item’s raw expert score from the active split.

- [benchmark/scripts/agent_v6_6.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_v6_6.py:169): v6.6 forced-final path does not use the JSON retry helper; one malformed final response falls back or errors, unlike v6 at [agent_v6.py:152](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_v6.py:152).
  Exact fix: factor `_call_with_json_retry(require_initial=False)` into v6.6 and use it for forced-final too.

- [benchmark/scripts/infer.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/infer.py:596), [benchmark/scripts/infer.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/infer.py:607): served-model logging is not enough. It logs only the first unique requested→served pair per process and has no `item_id`, turn, tool, response id, or per-result field. It cannot diagnose the reported 20% per-item drift.
  Exact fix: return `served_model_id` from `call_llm` or add a structured callback, and write per item/per turn `{item_id, phase, turn, requested_model, served_model, response_id, timestamp}` into result JSON or a sidecar JSONL.

- [benchmark/scripts/agent_prompt_v6_6.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_prompt_v6_6.py:3), [benchmark/scripts/agent_v6_6.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_v6_6.py:137), [benchmark/scripts/infer.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/infer.py:459): score calibration documentation is internally inconsistent. v6.6 does not use `score_from_v0`; it averages free-form `initial_score` and free-form final `score`. Direct uses `score_from_v0`. v6.7’s Direct turn uses `score_from_v0`, while its ReAct final uses free score.
  Exact fix: document each score source explicitly in result files: `direct_score_from="score_from_v0"`, `agent_score_from="free_score"`, `initial_score_from="free_score"`.

- [benchmark/scripts/agent_v6_7.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_v6_7.py:111), [benchmark/scripts/agent_v6_7.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_v6_7.py:173): `agent_final_score` is wrong in v6.7 output. `r.score` is overwritten with the ensemble, then recorded as `agent_final_score`.
  Exact fix: save `agent_score = r.score` before blending, record that field, then write ensemble separately.

**MINOR**

- [benchmark/scripts/infer.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/infer.py:532), [benchmark/scripts/infer.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/infer.py:536): hard-coded API keys/base URLs are in source. This is a security and reproducibility problem.
  Exact fix: remove defaults; require env vars or a local ignored config file.

- [refine-logs/V6_RESULTS.md](/hdd1/jiangxi/AD-Agent/refine-logs/V6_RESULTS.md:8), [benchmark/scripts/agent_tools_v6.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_tools_v6.py:503): docs say 16 tools, registry has 13.
  Exact fix: update the result doc or registry count.

- [benchmark/scripts/agent_tools_v6.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_tools_v6.py:4), [benchmark/scripts/agent_v6_5.py](/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_v6_5.py:31): tool docs say domain code is never a modeling input, but v6.5/v6.6/v6.7 inject domain text into the prompt.
  Exact fix: rename A-regime/B-regime clearly and update invariants.

**PUBLISHABILITY**

As a paper about a pure autonomous visual anomaly-detection agent, this is not publishable yet. The cleanest result is not the agent: fixed Direct+SubspaceAD fusion matches or beats most claimed gains, and the strongest reported Qwen improvement is an offline ensemble selected after many test-set iterations. Reviewers will reasonably say the contribution is an ensemble/complementarity trick, not an agentic detection algorithm.

A publishable angle is possible if the paper is reframed honestly: “tool-augmented VLM agents are brittle; simple fusion is a strong baseline; agents help only under identifiable reliability conditions.” For a positive agent paper, you need a frozen dev-selected method, a clean held-out test, no contaminated retrieval bank, and evidence that tool use causally improves rank ordering beyond Direct and fixed fusion.

**SUGGESTED NEXT EXPERIMENTS**

1. Build a pure-agent reliability gate: before calling any expert tool, the agent must predict whether the tool is applicable from visual/domain cues, then either abstain or call one tool. Tune the gate prompt/rules on dev only.

2. Run one-tool causal ablations: Direct-style visual judgment, then exactly one allowed tool family, then final free score. Compare `expert_score`, `reference_profiler`, `image_diff`, and `retriever` under the same K and prompt budget.

3. Fix and use the retrieval tool as a pure visual reference augmenter: clean train-only normal bank, return retrieved images to the VLM, and test whether better references improve agent-alone AUROC without score averaging.

4. Add a self-critique final step instead of post-hoc ensemble: the agent outputs final score plus a tool-reliability assessment, and must downweight any tool it labels unreliable. No external Direct averaging.

5. Create a dev-only routing policy from non-label features available at inference: domain descriptor, first-turn uncertainty, expert raw/rank, and tool observation metadata. Freeze it, then evaluate once on held-out test as a pure agent controller.
