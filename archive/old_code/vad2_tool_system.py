import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from utils import VisualContext
from vad2_tools_mm import propose_anomalies_mm, refute_anomalies_mm


def _extract_json(text: str) -> Dict[str, Any]:
    text = (text or "").strip()
    if not text:
        raise ValueError("empty model output")

    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if fence:
        inner = fence.group(1).strip()
        obj = json.loads(inner)
        if isinstance(obj, dict):
            return obj

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        obj = json.loads(text[start : end + 1])
        if isinstance(obj, dict):
            return obj

    raise ValueError("无法从输出中解析 JSON")


@dataclass
class DualVADToolConfig:
    model: str = "doubao-seed-1-6-vision-250815"
    temperature: float = 0.0
    max_tokens: int = 600
    depth_quota: int = 2
    max_query_frames: int = 1
    max_normal_frames: int = 1


class DualVADToolSystem:
    """
    以“两个多模态 tool 直连模型”的方式运行：
    - 每轮固定 2 次 API：propose 一次 + refute 一次
    - 规则聚合，无需额外总结模型
    - 仅对 TBD 进入下一轮
    """

    def __init__(self, config: Optional[DualVADToolConfig] = None):
        self.config = config or DualVADToolConfig()

    def _aggregate(
        self,
        claims: List[Dict[str, Any]],
        reviews: List[Dict[str, Any]],
    ) -> Tuple[Dict[str, str], List[str]]:
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

    def run(self, visual_ctx: VisualContext) -> Dict[str, Any]:
        history_rounds: List[Dict[str, Any]] = []
        final_claims: Dict[str, Dict[str, Any]] = {}
        final_reviews: Dict[str, Dict[str, Any]] = {}
        final_decisions: Dict[str, str] = {}

        tbd_ids: Optional[List[str]] = None

        for round_idx in range(self.config.depth_quota):
            # 1) proposer：首轮全量；后续仅 TBD 精炼
            tbd_claims_json: Optional[str] = None
            if round_idx > 0 and tbd_ids:
                tbd_claims = [final_claims[cid] for cid in tbd_ids if cid in final_claims]
                tbd_claims_json = json.dumps({"claims": tbd_claims}, ensure_ascii=False)

            proposer_text = propose_anomalies_mm(
                visual_ctx,
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                max_query_frames=self.config.max_query_frames,
                max_normal_frames=self.config.max_normal_frames,
                tbd_claims_json=tbd_claims_json,
            )
            proposer_json = _extract_json(proposer_text)
            claims = proposer_json.get("claims", []) or []

            for c in claims:
                cid = c.get("id")
                if cid:
                    final_claims[cid] = c

            # 2) refuter：首轮评审全量；后续只评审 TBD
            if round_idx == 0:
                focus_claims = list(final_claims.values())
            else:
                focus_claims = [final_claims[cid] for cid in (tbd_ids or []) if cid in final_claims]
                if not focus_claims:
                    break

            refuter_text = refute_anomalies_mm(
                visual_ctx,
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                max_query_frames=self.config.max_query_frames,
                max_normal_frames=self.config.max_normal_frames,
                claims_json=json.dumps({"claims": focus_claims}, ensure_ascii=False),
            )
            refuter_json = _extract_json(refuter_text)
            reviews = refuter_json.get("reviews", []) or []

            for r in reviews:
                rid = r.get("id")
                if rid:
                    final_reviews[rid] = r

            decisions, tbd_ids = self._aggregate(focus_claims, reviews)
            final_decisions.update(decisions)

            history_rounds.append(
                {
                    "round": round_idx,
                    "focus_ids": [c.get("id") for c in focus_claims if c.get("id")],
                    "decisions": decisions,
                }
            )

            if not tbd_ids:
                break

        valid = sum(1 for v in final_decisions.values() if v == "Valid")
        invalid = sum(1 for v in final_decisions.values() if v == "Invalid")
        tbd = sum(1 for v in final_decisions.values() if v == "TBD")
        total = len(final_decisions)

        return {
            "summary": {"valid": valid, "invalid": invalid, "TBD": tbd, "total": total},
            "decisions": final_decisions,
            "claims": final_claims,
            "reviews": final_reviews,
            "rounds": history_rounds,
        }


