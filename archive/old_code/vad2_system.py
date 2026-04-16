"""
AnomalyClaw: Adversarial VLM Debate with Expert Grounding.

DualVADAgentSystem (v2): Proposer/Advocate debate with expert evidence integration.
- Extensible expert pool provides quantitative grounding
- Autonomous controller selects experts and controls debate depth
- Each round: 2 model calls (Proposer + Advocate)
- Rule-based claim aggregation (no 3rd oracle model)
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from agents import Agent, Runner, SQLiteSession, RunConfig

from utils import VisualContext, encode_image
from vad2_prompts import (
    PROPOSER_SYSTEM,
    ADVOCATE_SYSTEM,
    MMAD_ANSWERER_SYSTEM,
    proposer_cold,
    proposer_iterative,
    advocate_prompt,
    mmad_answerer_prompt,
    PROPOSER_COLD,  # backward compat
)


def _stateless_session_input_callback(_history_items, new_input_items):
    """Force stateless conversation: only send current input, avoid token growth."""
    if isinstance(new_input_items, list):
        return new_input_items
    return [{"role": "user", "content": new_input_items}]


def _extract_json(text: str) -> Dict[str, Any]:
    """Extract JSON object from model output with fallback parsing."""
    text = (text or "").strip()
    if not text:
        raise ValueError("empty model output")

    # 1) Direct parse
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    # 2) Strip code fence
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if fence:
        inner = fence.group(1).strip()
        try:
            obj = json.loads(inner)
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass

    # 3) Extract first {...} block
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        obj = json.loads(candidate)
        if isinstance(obj, dict):
            return obj

    raise ValueError("Cannot parse JSON from output")


def _vision_messages(
    visual_ctx: VisualContext,
    *,
    prompt_text: str,
    max_query_frames: int = 1,
    max_normal_frames: int = 1,
) -> List[Dict[str, Any]]:
    """Build multi-modal messages in Agents SDK format."""
    messages: List[Dict[str, Any]] = []

    # Normal reference images (few-shot)
    normal_frames = visual_ctx.few_shot_frames or []
    for i, f in enumerate(normal_frames[:max_normal_frames]):
        b64 = encode_image(f)
        messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_image",
                        "detail": "auto",
                        "image_url": f"data:image/jpeg;base64,{b64}",
                    }
                ],
            }
        )
        messages.append({"role": "user", "content": f"Normal sample {i+1}."})

    # Query image(s)
    query_frames = visual_ctx.full_frames or []
    for i, f in enumerate(query_frames[:max_query_frames]):
        b64 = encode_image(f)
        messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_image",
                        "detail": "auto",
                        "image_url": f"data:image/jpeg;base64,{b64}",
                    }
                ],
            }
        )
        messages.append({"role": "user", "content": f"Query image {i+1}."})

    if normal_frames[:max_normal_frames]:
        messages.append(
            {
                "role": "user",
                "content": f"The first {min(len(normal_frames), max_normal_frames)} image(s) are normal sample(s). "
                f"The last {min(len(query_frames), max_query_frames)} image(s) are query image(s).",
            }
        )

    messages.append({"role": "user", "content": prompt_text})
    return messages


@dataclass
class DualVADConfig:
    model: str = "doubao-seed-1-6-vision-250815"
    temperature: float = 0.0
    max_tokens: int = 600
    depth_quota: int = 2
    max_query_frames: int = 1
    max_normal_frames: int = 1
    # Expert integration
    use_experts: bool = True
    domain_code: str = ""
    domain_knowledge: str = ""


class DualVADAgentSystem:
    """
    AnomalyClaw: Adversarial debate with expert grounding.

    Two agents (Proposer/Advocate) + rule-based aggregation.
    - Expert evidence injected as text context into Proposer prompt
    - Autonomous controller manages expert selection and debate depth
    - Each round: exactly 2 model calls
    - Only TBD claims proceed to next round
    """

    def __init__(self, session: Optional[SQLiteSession] = None, config: Optional[DualVADConfig] = None):
        self.config = config or DualVADConfig()
        self.session = session or SQLiteSession("vad2_user")

        self.proposer = Agent(
            name="AnomalyClaw_Proposer",
            instructions=PROPOSER_SYSTEM,
            tools=[],
        )
        self.advocate = Agent(
            name="AnomalyClaw_Advocate",
            instructions=ADVOCATE_SYSTEM,
            tools=[],
        )
        self.mmad_answerer = Agent(
            name="AnomalyClaw_MMAD",
            instructions=MMAD_ANSWERER_SYSTEM,
            tools=[],
        )

        self.run_config = RunConfig(
            session_input_callback=_stateless_session_input_callback,
            trace_include_sensitive_data=False,
            model=self.config.model,
        )

        # Expert pool (lazy loaded)
        self._expert_pool = None
        # Autonomous controller (lazy loaded)
        self._controller = None

    @property
    def expert_pool(self):
        if self._expert_pool is None:
            try:
                from experts import ExpertPool
                self._expert_pool = ExpertPool()
            except ImportError:
                self._expert_pool = None
        return self._expert_pool

    @property
    def controller(self):
        if self._controller is None:
            try:
                from controller import AutonomousController
                self._controller = AutonomousController()
            except ImportError:
                self._controller = None
        return self._controller

    def _collect_expert_evidence(
        self,
        query_path: str,
        ref_paths: List[str],
        domain_code: str = "",
    ) -> str:
        """Run selected experts and combine their text reports."""
        if not self.config.use_experts or not self.expert_pool:
            return ""

        # Use controller to select experts, or run all available
        if self.controller:
            expert_names = self.controller.select_experts(domain_code)
        else:
            expert_names = ["patch", "retrieval"]

        try:
            reports = self.expert_pool.run_selected(
                expert_names, query_path, ref_paths, domain_code
            )
            if not reports:
                return ""

            parts = []
            for name, report in reports.items():
                parts.append(f"[{name.upper()} EXPERT]\n{report}")
            return "\n\n".join(parts)
        except Exception as e:
            print(f"  [WARN] Expert evidence collection failed: {e}")
            return ""

    def _get_debate_depth(self, domain_code: str = "") -> int:
        """Get max debate depth from controller or config."""
        if self.controller:
            return self.controller.get_max_depth(domain_code)
        return self.config.depth_quota

    def _aggregate(
        self,
        claims: List[Dict[str, Any]],
        reviews: List[Dict[str, Any]],
    ) -> Tuple[Dict[str, str], List[str]]:
        """Rule-based claim resolution: no 3rd model call needed."""
        review_map = {r.get("id"): r for r in (reviews or [])}
        decisions: Dict[str, str] = {}
        tbd_ids: List[str] = []

        for c in claims:
            cid = c.get("id")
            if not cid:
                continue
            conf = float(c.get("confidence", 0.0) or 0.0)
            r = review_map.get(cid, {})
            ref = float(r.get("refute_confidence", 0.0) or 0.0)

            if ref >= 0.6:
                decisions[cid] = "Invalid"
            elif conf >= 0.6 and ref <= 0.4:
                decisions[cid] = "Valid"
            else:
                decisions[cid] = "TBD"
                tbd_ids.append(cid)

        return decisions, tbd_ids

    def _compact_report_for_qa(
        self,
        *,
        verdict: str,
        normal_profile: Optional[Dict[str, Any]],
        final_claims: Dict[str, Dict[str, Any]],
        final_reviews: Dict[str, Dict[str, Any]],
        final_decisions: Dict[str, str],
    ) -> str:
        """Compact report for MMAD answerer."""
        claims_out: List[Dict[str, Any]] = []
        for cid, c in final_claims.items():
            claims_out.append(
                {
                    "id": cid,
                    "decision": final_decisions.get(cid, "TBD"),
                    "category": c.get("category"),
                    "location": c.get("location"),
                    "appearance": c.get("appearance"),
                    "evidence": c.get("evidence"),
                    "analysis": c.get("analysis"),
                    "confidence": c.get("confidence"),
                    "severity": c.get("severity"),
                    "refute": final_reviews.get(cid),
                }
            )
        report = {
            "verdict": verdict,
            "normal_profile": normal_profile,
            "anomalies": claims_out,
        }
        return json.dumps(report, ensure_ascii=False)

    def run(
        self,
        visual_ctx: VisualContext,
        *,
        mmad_questions_text: Optional[str] = None,
        query_path: Optional[str] = None,
        ref_paths: Optional[List[str]] = None,
        domain_code: Optional[str] = None,
        domain_knowledge: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run the adversarial debate.

        Args:
            visual_ctx: Image context (query + reference frames)
            mmad_questions_text: Optional MMAD VQA questions
            query_path: Path to query image (for expert evidence)
            ref_paths: Paths to reference images (for expert evidence)
            domain_code: Domain identifier (e.g., "D1") for controller
            domain_knowledge: Domain-specific knowledge text
        """
        history_rounds: List[Dict[str, Any]] = []
        final_claims: Dict[str, Dict[str, Any]] = {}
        final_reviews: Dict[str, Dict[str, Any]] = {}
        final_decisions: Dict[str, str] = {}
        normal_profile: Optional[Dict[str, Any]] = None
        mmad_answers: Optional[List[str]] = None
        tbd_ids: Optional[List[str]] = None

        _domain_code = domain_code or self.config.domain_code or ""
        _domain_knowledge = domain_knowledge or self.config.domain_knowledge or ""

        # Collect expert evidence
        expert_evidence = ""
        if query_path and ref_paths:
            expert_evidence = self._collect_expert_evidence(
                query_path, ref_paths, _domain_code
            )

        # Get debate depth from controller
        max_depth = self._get_debate_depth(_domain_code)

        for round_idx in range(max_depth):
            # 1) Proposer: cold start (round 0) or TBD refinement
            if round_idx == 0 or not tbd_ids:
                prop_prompt = proposer_cold(
                    expert_reports=expert_evidence,
                    domain_knowledge=_domain_knowledge,
                )
            else:
                tbd_claims = [final_claims[cid] for cid in tbd_ids if cid in final_claims]
                iterative_payload: Dict[str, Any] = {"claims": tbd_claims}
                if isinstance(normal_profile, dict):
                    iterative_payload["normal_profile"] = normal_profile
                prop_prompt = proposer_iterative(
                    json.dumps(iterative_payload, ensure_ascii=False),
                    expert_reports=expert_evidence,
                )

            proposer_input = _vision_messages(
                visual_ctx,
                prompt_text=prop_prompt,
                max_query_frames=self.config.max_query_frames,
                max_normal_frames=self.config.max_normal_frames,
            )
            proposer_result = Runner.run_sync(
                self.proposer,
                input=proposer_input,
                session=self.session,
                run_config=self.run_config,
            )
            proposer_text = proposer_result.final_output if hasattr(proposer_result, "final_output") else str(proposer_result)
            proposer_json = _extract_json(proposer_text)
            claims = proposer_json.get("claims", []) or []
            if isinstance(proposer_json.get("normal_profile"), dict):
                normal_profile = proposer_json.get("normal_profile")

            # Update claims (overwrite same id)
            for c in claims:
                cid = c.get("id")
                if cid:
                    final_claims[cid] = c

            # 2) Advocate: review claims (all in round 0, TBD only after)
            if round_idx == 0:
                focus_claims = list(final_claims.values())
            else:
                focus_claims = [final_claims[cid] for cid in (tbd_ids or []) if cid in final_claims]
                if not focus_claims:
                    break

            advocate_input = _vision_messages(
                visual_ctx,
                prompt_text=advocate_prompt(json.dumps({"claims": focus_claims}, ensure_ascii=False)),
                max_query_frames=self.config.max_query_frames,
                max_normal_frames=self.config.max_normal_frames,
            )
            advocate_result = Runner.run_sync(
                self.advocate,
                input=advocate_input,
                session=self.session,
                run_config=self.run_config,
            )
            advocate_text = advocate_result.final_output if hasattr(advocate_result, "final_output") else str(advocate_result)
            advocate_json = _extract_json(advocate_text)
            reviews = advocate_json.get("reviews", []) or []

            for r in reviews:
                rid = r.get("id")
                if rid:
                    final_reviews[rid] = r

            # 3) Aggregate: update decisions for this round's focus claims
            decisions, tbd_ids = self._aggregate(focus_claims, reviews)
            final_decisions.update(decisions)

            history_rounds.append(
                {
                    "round": round_idx,
                    "focus_ids": [c.get("id") for c in focus_claims if c.get("id")],
                    "decisions": decisions,
                    "tbd_ids_next": list(tbd_ids),
                }
            )

            if not tbd_ids:
                break

        # Compute verdict
        valid = sum(1 for v in final_decisions.values() if v == "Valid")
        invalid = sum(1 for v in final_decisions.values() if v == "Invalid")
        tbd = sum(1 for v in final_decisions.values() if v == "TBD")
        total = len(final_decisions)

        if self.controller:
            verdict = self.controller.produce_verdict(final_decisions)
        else:
            verdict = "uncertain"
            if valid > 0:
                verdict = "anomaly"
            elif total > 0 and tbd == 0 and invalid == total:
                verdict = "normal"
            elif total == 0:
                verdict = "normal"

        # MMAD QA (separate call after debate)
        if mmad_questions_text:
            qa_report_json = self._compact_report_for_qa(
                verdict=verdict,
                normal_profile=normal_profile,
                final_claims=final_claims,
                final_reviews=final_reviews,
                final_decisions=final_decisions,
            )
            qa_prompt = mmad_answerer_prompt(mmad_questions_text, qa_report_json)
            qa_input = _vision_messages(
                visual_ctx,
                prompt_text=qa_prompt,
                max_query_frames=self.config.max_query_frames,
                max_normal_frames=self.config.max_normal_frames,
            )
            qa_result = Runner.run_sync(
                self.mmad_answerer,
                input=qa_input,
                session=self.session,
                run_config=self.run_config,
            )
            qa_text = qa_result.final_output if hasattr(qa_result, "final_output") else str(qa_result)
            qa_json = _extract_json(qa_text)
            if isinstance(qa_json.get("mmad_answers"), list):
                mmad_answers = qa_json.get("mmad_answers")

        return {
            "summary": {"valid": valid, "invalid": invalid, "TBD": tbd, "total": total},
            "verdict": verdict,
            "normal_profile": normal_profile,
            "mmad_answers": mmad_answers,
            "decisions": final_decisions,
            "claims": final_claims,
            "reviews": final_reviews,
            "rounds": history_rounds,
            "expert_evidence": expert_evidence if expert_evidence else None,
            "debate_depth": len(history_rounds),
        }
