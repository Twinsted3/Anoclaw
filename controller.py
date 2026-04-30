"""
Autonomous Controller for AnomalyClaw.

Responsibilities:
  1. Expert selection based on domain and initial similarity
  2. Debate depth control based on domain and initial confidence
  3. Verdict production from claim decisions
"""

from typing import Dict, List, Optional


DOMAIN_CONFIG = {
    "D1": {"name": "Industrial Mfg.", "type": "industrial", "experts": ["patch", "retrieval", "subspace"]},
    "D2": {"name": "Retail", "type": "industrial", "experts": ["patch", "retrieval", "subspace"]},
    "D3": {"name": "Complex Industrial", "type": "industrial", "experts": ["patch", "retrieval", "texture", "subspace"]},
    "D4": {"name": "Infrastructure", "type": "industrial", "experts": ["patch", "retrieval", "subspace"]},
    "D5": {"name": "Logical Anomaly", "type": "logical", "experts": ["patch", "retrieval", "texture"]},
    "D6": {"name": "3D Industrial", "type": "industrial", "experts": ["patch", "retrieval", "subspace"]},
    "D7": {"name": "Remote Sensing", "type": "remote_sensing", "experts": ["patch", "retrieval"]},
    "D8": {"name": "Dermatology", "type": "medical", "experts": ["patch", "retrieval"]},
    "D9": {"name": "Brain MRI", "type": "medical", "experts": ["patch", "retrieval"]},
    "D10": {"name": "Liver CT", "type": "medical", "experts": ["patch", "retrieval"]},
    "D11": {"name": "GI Endoscopy", "type": "medical", "experts": ["patch", "retrieval"]},
    "D12": {"name": "Road Safety", "type": "scene", "experts": ["retrieval"]},
}


class AutonomousController:
    """
    Controls expert selection, debate depth, and verdict aggregation
    for the AnomalyClaw multi-agent anomaly detection system.
    """

    def __init__(self):
        self.domain_config = DOMAIN_CONFIG

    def select_experts(
        self,
        domain_code: str,
        initial_similarity: Optional[float] = None,
    ) -> List[str]:
        """Select which expert modules to activate for a given domain.

        Args:
            domain_code: Domain identifier (e.g. "D1", "D3", "D8").
            initial_similarity: Optional similarity score from an initial
                quick check. If > 0.95 the image is clearly normal and
                the heavier patch expert is skipped.

        Returns:
            List of expert names to run.
        """
        config = self.domain_config.get(domain_code)
        domain_type = config["type"] if config else "unknown"
        domain_experts = list(config["experts"]) if config else []

        experts: List[str] = []

        # Retrieval is always included (lightweight)
        if "retrieval" not in experts:
            experts.append("retrieval")

        # Include patch unless the image is clearly normal
        skip_patch = initial_similarity is not None and initial_similarity > 0.95
        if not skip_patch and "patch" in domain_experts:
            experts.append("patch")

        # Include texture for industrial domains
        if domain_type == "industrial" and "texture" in domain_experts:
            experts.append("texture")

        # Logical anomaly domains also get texture
        if domain_type == "logical" and "texture" in domain_experts:
            experts.append("texture")

        # Include subspace (PCA-based) for domains that list it
        if "subspace" in domain_experts:
            experts.append("subspace")

        return experts

    def get_max_depth(
        self,
        domain_code: str,
        initial_confidence: Optional[float] = None,
    ) -> int:
        """Determine the maximum debate depth for a given domain.

        Args:
            domain_code: Domain identifier.
            initial_confidence: Optional confidence from an initial assessment.
                Values near 0 or 1 indicate a clear-cut case.

        Returns:
            Maximum number of debate rounds (D_max).
        """
        config = self.domain_config.get(domain_code)
        domain_type = config["type"] if config else "unknown"

        # Very clear initial assessment: one round suffices
        if initial_confidence is not None:
            if initial_confidence > 0.8 or initial_confidence < 0.2:
                return 1

        # Medical domains need extra verification
        if domain_type == "medical":
            return 3

        # Default
        return 2

    def produce_verdict(self, decisions: Dict[str, str]) -> str:
        """Aggregate per-claim decisions into a final verdict.

        Args:
            decisions: Mapping from claim id to decision string
                ("Valid", "Invalid", or "TBD").

        Returns:
            "anomaly" if any claim is Valid,
            "normal" if all claims are Invalid or there are no claims,
            "uncertain" if TBD claims remain.
        """
        if not decisions:
            return "normal"

        values = set(decisions.values())

        if "Valid" in values:
            return "anomaly"

        if values <= {"Invalid"}:
            return "normal"

        # TBD claims remain
        return "uncertain"
