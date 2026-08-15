"""AnomalyClaw v12_mmad — experimental v12 fork that unblocks tool
use on MMAD non-AD question types (Defect Localization, Object
Classification, etc.).

Diff vs agent_v12.py:
  - imports agent_prompt_v12_mmad instead of agent_prompt_v10. The
    fork's prompt rewrites mode 2 / mode 3 protocols to ENCOURAGE
    targeted tool use for spatial / classification / fine-grained
    sub-types.
  - The hardcoded `mode_hint == "object_analysis" → force final` block
    in the main turn loop is REMOVED. Tools are now allowed in
    object_analysis mode (governed by the prompt's softer rules).
  - All other behaviour (controller, refutation trace, MCQ coercion,
    forced-final) inherited from agent_v9 / agent_v11 unchanged.

Validation: must beat v10 letter accuracy on MMAD dev500 non-AD
pooled to be promoted to v15.

Original v12 docstring follows.
---
AnomalyClaw v12 — v11 architecture wired to the v8 tool catalog
+ v10 specialty-ladder prompt.

Delta vs v11:
- v9 refutation agent now reads agent_prompt_v10.py (specialty-matched
  tool descriptions + refutation ladder) and dispatches to
  agent_tools_v8.py (expert heatmap + suggested_bbox, blob-layout viz,
  change heatmap viz, FFT spectrum viz, reference_retriever images,
  image_diff/rotate_align domain guards).
- Observation rendering is extended: any tool output key ending in _b64
  (and any retrieved_images_b64 list) is attached to the next-turn
  observation as an image message, so scalar-only tools can now
  contribute visual evidence.
- Controller arbitration layer and learning_enabled flag unchanged from
  v11; passing learning_enabled=False reproduces the v10 (Passive)
  baseline with the new tool catalog.

CLI mirrors agent_v11.py. The v8 prompt classifier and all MCQ mode
handling are inherited from agent_v9 via a thin wrapper.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import agent_prompt_v12_mmad as _p10  # noqa: E402  (fork of v10 prompt)
import agent_tools_v8 as _t8     # noqa: E402
import agent_v9 as _v9           # noqa: E402 — reuse its helpers & V9Result dataclass
from agent_v11 import (  # noqa: E402
    CONTROLLER_SYSTEM, CONTROLLER_USER_TEMPLATE,
    _controller_arbitrate, _direct_blocking, _direct_rationale,
    _retrieve_rules_cached,
)
from infer import (  # noqa: E402
    call_llm, extract_json, get_client, get_model_name,
    img_msg, load_and_encode, run_v0, text_msg,
)

N_REFS = 2


# Image keys that can appear in tool observations and that should be
# attached to the next-turn user message as image_msg payloads. v8 adds
# heatmap_b64, blob_layout_b64, change_heatmap_b64, spectrum_b64 on top
# of the v7 set (crop_b64, diff_mask_b64, aligned_diff_b64, composite_b64).
_OBS_IMAGE_KEYS = (
    "crop_b64", "diff_mask_b64", "aligned_diff_b64", "composite_b64",
    "heatmap_b64", "blob_layout_b64", "change_heatmap_b64", "spectrum_b64",
)


def _run_v9_agent_v12(client, model, item, split, max_turns,
                      question=None, options=None, rulebook=None,
                      prior_hint=None):
    """Run the v9 refutation loop using agent_prompt_v10 + agent_tools_v8.

    Adapted from agent_v9.run_v9_item, changes limited to:
      - _build_initial_messages swapped to use _p10 (v10 prompt)
      - dispatch_tool routed through _t8
      - observation image-attach loop extended to the v8 key set.
    All other logic (mode handling, refutation trace, forced-final,
    MCQ coercion) is inherited from agent_v9.
    """
    item_id = item["item_id"]
    query_path = item["query_path"]
    ref_paths = item.get("ref_paths", []) or []
    domain_code = item.get("domain_code")

    ctx = {
        "query_path": query_path,
        "ref_paths": ref_paths,
        "item_id": item_id,
        "split": split,
        "vlm_client": client,
        "vlm_model": model,
        "llm_client": client,
        "llm_model": model,
        "_manifest_domain": domain_code,
    }

    # Build initial messages using v10 SYSTEM_PROMPT. We can reuse v9's
    # _build_initial_messages by monkey-patching its _p9 reference, but
    # the cleaner path is to duplicate the tiny initial-messages block
    # and swap _p9 -> _p10. We use the v9 helper to preserve hybrid
    # routing logic (object/defect/ad) and just replace SYSTEM_PROMPT.
    messages, mode_hint = _v9._build_initial_messages(
        query_path, ref_paths, question, options, max_turns,
        rulebook=rulebook)
    messages[0]["content"] = _p10.SYSTEM_PROMPT  # override prompt v9->v10

    # Inject per-domain tool guidance as the first user-side text msg.
    # This is the single most effective lever on tool diversity: the
    # generic ladder is preserved in the system prompt, but the agent
    # now sees a domain-specific "which tool belongs here" hint on
    # turn 1.
    hint = _p10.format_domain_hint(domain_code)
    if hint and isinstance(messages[1].get("content"), list):
        messages[1]["content"] = [text_msg(hint)] + list(messages[1]["content"])

    # v12_mmad addition: optional prior hint injection (Direct-as-prior).
    # Caller passes a single text block summarising another model's
    # initial guess; we prepend it after the domain hint so the agent
    # sees "this is what model X thinks" before its own analysis.
    if prior_hint and isinstance(messages[1].get("content"), list):
        messages[1]["content"] = (
            [text_msg(prior_hint)] + list(messages[1]["content"]))

    history = []
    tools_used = []
    initial_score = None
    candidate_features = None
    remaining_features = None
    updated_score = None
    refutation_verdicts: list = []

    for turn in range(1, max_turns + 1):
        action = _v9._call_with_retry(client, model, messages, mode_hint)
        # NOTE (v12_mmad): the v12 hardcoded "object_analysis →
        # force final" coercion is intentionally REMOVED here. Tool
        # calls in object_analysis are now governed by the prompt's
        # softer rules (zoom_bbox permitted for fine-grained
        # questions). If empirical regression returns, restore the
        # block but keyed on a sub-type detector rather than blanket
        # mode coercion.
        if action is None:
            return _v9.V9Result(
                item_id=item_id, mode=mode_hint, score=0.5,
                mcq_answer=None, free_text=None, option_scores=None,
                rationale="json parse failed",
                n_turns=turn, tools_used=tools_used, history=history,
                initial_score=initial_score,
                candidate_features=candidate_features,
                remaining_features=remaining_features,
                refutation_verdicts=refutation_verdicts,
                updated_score=updated_score,
                confidence=0, error="malformed JSON after retries",
            )

        if turn == 1:
            rt = action.get("refutation_trace") or {}
            initial_score = (action.get("initial_score")
                             or rt.get("initial_score"))
            candidate_features = (action.get("candidate_features")
                                  or rt.get("candidate_features"))
            remaining_features = candidate_features

        if action.get("refutation_verdict"):
            refutation_verdicts.append({
                "turn": turn,
                "verdict": action.get("refutation_verdict"),
                "status": action.get("feature_status_update"),
            })
        if action.get("remaining_candidate_features") is not None:
            remaining_features = action.get("remaining_candidate_features")
        if action.get("updated_score") is not None:
            try:
                updated_score = float(action["updated_score"])
            except (TypeError, ValueError):
                pass

        if action["action"] == "final":
            score = float(action.get("anomaly_score", 0.5))
            score = max(0.0, min(1.0, score))
            return _v9.V9Result(
                item_id=item_id,
                mode=action.get("mode") or mode_hint,
                score=score,
                mcq_answer=action.get("mcq_answer"),
                free_text=action.get("free_text"),
                option_scores=action.get("option_scores"),
                rationale=str(action.get("rationale", ""))[:500],
                n_turns=turn, tools_used=tools_used,
                history=history + [
                    {"turn": turn, **_v9._summarise_action(action)}],
                initial_score=initial_score,
                candidate_features=candidate_features,
                remaining_features=remaining_features,
                refutation_verdicts=refutation_verdicts,
                updated_score=updated_score,
                confidence=int(action.get("confidence", 0) or 0),
            )

        if turn == max_turns:
            messages.append({"role": "assistant",
                             "content": json.dumps(_v9._summarise_action(action))})
            messages.append({"role": "user",
                             "content": _p10.forced_final_prompt(max_turns)})
            forced = _v9._call_with_retry(client, model, messages, mode_hint)
            if forced and forced.get("action") == "final":
                score = float(forced.get("anomaly_score", 0.5))
                score = max(0.0, min(1.0, score))
                return _v9.V9Result(
                    item_id=item_id,
                    mode=forced.get("mode") or mode_hint,
                    score=score,
                    mcq_answer=forced.get("mcq_answer"),
                    free_text=forced.get("free_text"),
                    option_scores=forced.get("option_scores"),
                    rationale=str(forced.get("rationale", ""))[:500],
                    n_turns=max_turns, tools_used=tools_used,
                    history=history + [
                        {"turn": turn, **_v9._summarise_action(action)},
                        {"turn": turn, **_v9._summarise_action(forced)},
                    ],
                    initial_score=initial_score,
                    candidate_features=candidate_features,
                    remaining_features=remaining_features,
                    refutation_verdicts=refutation_verdicts,
                    updated_score=updated_score,
                    confidence=int(forced.get("confidence", 0) or 0),
                )
            return _v9.V9Result(
                item_id=item_id, mode=mode_hint, score=0.5,
                mcq_answer=None, free_text=None, option_scores=None,
                rationale="forced-final failed",
                n_turns=max_turns, tools_used=tools_used, history=history,
                initial_score=initial_score,
                candidate_features=candidate_features,
                remaining_features=remaining_features,
                refutation_verdicts=refutation_verdicts,
                updated_score=updated_score,
                confidence=0, error="forced-final produced non-final",
            )

        # Execute tool via v8 dispatcher
        tool_name = action["tool"]
        tool_args = action.get("args") or {}
        observation = _t8.dispatch_tool(tool_name, tool_args, ctx)
        tools_used.append(tool_name)
        history.append({"turn": turn, **_v9._summarise_action(action),
                        "obs_keys": list(observation.keys()),
                        "obs_error": observation.get("error")})

        if tool_name == "tool_expert_score":
            ctx["_expert_patches"] = observation.get("top_patches", [])

        obs_parts = [text_msg(
            f"OBSERVATION from {tool_name}: {_v9._obs_to_text(observation)}")]
        # Attach single-image keys
        for img_key in _OBS_IMAGE_KEYS:
            b64 = observation.get(img_key)
            if isinstance(b64, str) and b64:
                obs_parts.append(img_msg(b64))
        # Attach patch_grid tiles
        if observation.get("tiles"):
            for t in observation["tiles"][:9]:
                if t.get("crop_b64"):
                    obs_parts.append(img_msg(t["crop_b64"]))
        # Attach retrieved_images_b64 (list)
        retrieved = observation.get("retrieved_images_b64")
        if isinstance(retrieved, list):
            for rb in retrieved[:4]:
                if isinstance(rb, str) and rb:
                    obs_parts.append(img_msg(rb))

        remaining = max_turns - turn
        obs_parts.append(text_msg(
            f"Turn {turn + 1}/{max_turns}. "
            f"{_p10.budget_warning_prompt(remaining)}\n"
            f"Incorporate this evidence, update your fields, continue or "
            f"finalise."))
        messages.append({"role": "assistant",
                         "content": json.dumps(_v9._summarise_action(action))})
        messages.append({"role": "user", "content": obs_parts})

    return _v9.V9Result(
        item_id=item_id, mode=mode_hint, score=0.5,
        mcq_answer=None, free_text=None, option_scores=None,
        rationale="loop exhausted",
        n_turns=max_turns, tools_used=tools_used, history=history,
        initial_score=initial_score, candidate_features=candidate_features,
        remaining_features=remaining_features,
        refutation_verdicts=refutation_verdicts,
        updated_score=updated_score,
        confidence=0, error="loop exhausted without final",
    )


def run_v12_item(client, model, item, split, max_turns,
                 question=None, options=None,
                 w_direct=0.5, w_v9=0.5,
                 learning_enabled=False, rulebook_dir=None,
                 controller_max_tokens=400,
                 controller_client=None, controller_model=None):
    """v12 item runner — parallel Direct + v9-agent-with-v8-tools + optional
    controller arbitration.
    """
    is_ad_expected = (question is None or options is None)

    direct_holder = {"result": None, "error": None}
    direct_thread = None
    if is_ad_expected:
        direct_thread = threading.Thread(
            target=_direct_blocking,
            args=(client, model, item, direct_holder),
            daemon=True,
        )
        direct_thread.start()

    try:
        v9 = _run_v9_agent_v12(client, model, item, split, max_turns,
                               question=question, options=options)
        v9_error = v9.error
    except Exception as e:
        v9 = None
        v9_error = f"{type(e).__name__}: {e}"

    if direct_thread is not None:
        direct_thread.join()
    direct_result = direct_holder["result"]
    direct_error = direct_holder["error"]

    base = {
        "item_id": item.get("item_id"),
        "domain_code": item.get("domain_code"),
        "label_gt": item.get("label"),
        "mode": None,
        "anomaly_score": None,
        "direct_score": None,
        "v9_score": None,
        "v9_initial_score": None,
        "v9_updated_score": None,
        "mcq_answer": None,
        "free_text": None,
        "option_scores": None,
        "rationale": "",
        "n_turns": 0,
        "tools_used": [],
        "confidence": 0,
        "candidate_features": None,
        "remaining_features": None,
        "refutation_verdicts": [],
        "history": [],
        "w_direct": w_direct,
        "w_v9": w_v9,
        "learning_enabled": bool(learning_enabled),
        "controller": None,
        "error": v9_error,
        "direct_error": direct_error,
    }

    if v9 is None:
        fallback_score = (direct_result or {}).get("anomaly_score")
        base["mode"] = "anomaly_detection" if is_ad_expected else "unknown"
        base["anomaly_score"] = fallback_score
        base["direct_score"] = fallback_score
        base["rationale"] = ("v9 agent failed; reporting Direct-only score"
                             if fallback_score is not None
                             else "v9 agent failed, no fallback")
        base["error"] = f"v9_failed: {v9_error}"
        return base

    base.update({
        "mode": v9.mode,
        "v9_score": v9.score,
        "v9_initial_score": v9.initial_score,
        "v9_updated_score": v9.updated_score,
        "mcq_answer": v9.mcq_answer,
        "free_text": v9.free_text,
        "option_scores": v9.option_scores,
        "rationale": v9.rationale,
        "n_turns": v9.n_turns,
        "tools_used": v9.tools_used,
        "confidence": v9.confidence,
        "candidate_features": v9.candidate_features,
        "remaining_features": v9.remaining_features,
        "refutation_verdicts": v9.refutation_verdicts,
        "history": v9.history,
    })

    agent_decided_ad = (v9.mode == "anomaly_detection")
    direct_score = (direct_result or {}).get("anomaly_score")
    base["direct_score"] = direct_score if agent_decided_ad else None
    if direct_result is not None and agent_decided_ad:
        base["direct_rationale"] = _direct_rationale(direct_result)
    else:
        base["direct_rationale"] = ""

    if agent_decided_ad and direct_score is not None and v9.score is not None:
        blend_score = max(0.0, min(1.0, w_direct * direct_score + w_v9 * v9.score))
    elif v9.score is not None:
        blend_score = v9.score
    else:
        blend_score = direct_score

    if (not learning_enabled) or (not agent_decided_ad) \
       or (direct_score is None) or (v9.score is None):
        base["anomaly_score"] = blend_score
        if learning_enabled and agent_decided_ad and \
           (direct_score is None or v9.score is None):
            base["controller"] = {"skipped": "missing_branch"}
        return base

    rules_text = _retrieve_rules_cached(
        rulebook_dir or "",
        item.get("domain_code", "") or "",
        item.get("category") or "",
        max_meta=3, max_domain=4,
    )
    ctrl_client = controller_client or client
    ctrl_model = controller_model or model
    ctrl_score, ctrl_meta = _controller_arbitrate(
        ctrl_client, ctrl_model, item,
        v9_score=v9.score, v9_rationale=v9.rationale,
        direct_score=direct_score,
        direct_rationale=_direct_rationale(direct_result),
        rules_text=rules_text,
        max_tokens=controller_max_tokens,
    )
    if ctrl_score is None:
        base["anomaly_score"] = blend_score
        base["controller"] = {**(ctrl_meta or {}), "fallback": "blend"}
    else:
        base["anomaly_score"] = ctrl_score
        base["controller"] = ctrl_meta
    return base


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--split", choices=["calibration", "dev", "test"],
                    required=True)
    ap.add_argument("--backend", choices=["gpt", "seedvl", "qwen3"],
                    required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--max_turns", type=int, default=4)
    ap.add_argument("--max_workers", type=int, default=9)
    ap.add_argument("--max_items", type=int, default=0)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--w_direct", type=float, default=0.5)
    ap.add_argument("--w_v9", type=float, default=0.5)
    ap.add_argument("--learning_enabled", action="store_true")
    ap.add_argument("--rulebook_dir", default="")
    ap.add_argument("--controller_max_tokens", type=int, default=400)
    args = ap.parse_args()

    items = json.load(open(args.manifest))
    items = [x for x in items if x.get("split") == args.split]
    if args.max_items:
        items = items[:args.max_items]

    prev = []
    done_ids = set()
    if args.resume and os.path.exists(args.output):
        prev = json.load(open(args.output))
        done_ids = {r["item_id"] for r in prev if r.get("error") is None}
        items = [x for x in items if x["item_id"] not in done_ids]

    client = get_client(args.backend)
    model = get_model_name(args.backend)

    def _run(x):
        try:
            return run_v12_item(
                client, model, x, args.split, args.max_turns,
                w_direct=args.w_direct, w_v9=args.w_v9,
                learning_enabled=args.learning_enabled,
                rulebook_dir=args.rulebook_dir,
                controller_max_tokens=args.controller_max_tokens,
            )
        except Exception as e:
            return {"item_id": x["item_id"], "anomaly_score": 0.5,
                    "error": f"{type(e).__name__}: {e}"}

    results_by_id = {x["item_id"]: x for x in prev}
    t0 = time.time()
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=args.max_workers) as ex:
        futs = [ex.submit(_run, x) for x in items]
        for i, f in enumerate(as_completed(futs)):
            r = f.result()
            results_by_id[r["item_id"]] = r
            if (i + 1) % 20 == 0:
                with open(args.output, "w") as ff:
                    json.dump(list(results_by_id.values()), ff)
                print(f"[{i+1}/{len(items)}] t={time.time()-t0:.1f}s",
                      flush=True)

    with open(args.output, "w") as f:
        json.dump(list(results_by_id.values()), f)
    print(f"Wrote {len(results_by_id)} → {args.output}")


if __name__ == "__main__":
    main()
