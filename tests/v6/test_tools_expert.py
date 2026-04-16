import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "benchmark" / "scripts"))
from agent_tools_v6 import tool_expert_score  # noqa: E402


def test_expert_score_returns_dict_with_score():
    out = tool_expert_score(item_id="D1_0079", expert="subspacead", split="calibration")
    # If cached file exists, we should get a valid score
    if out.get("error") is None:
        assert "score" in out
        assert isinstance(out["score"], float)
        assert "normalized_rank" in out
        assert 0.0 <= out["normalized_rank"] <= 1.0
        assert "top_patches" in out
        assert "interpretation" in out
    else:
        assert isinstance(out["error"], str)


def test_expert_score_unknown_expert_errors():
    out = tool_expert_score(item_id="D1_0079", expert="bogus", split="calibration")
    assert out.get("error") is not None


def test_expert_score_unknown_item_errors():
    out = tool_expert_score(item_id="DOES_NOT_EXIST", expert="subspacead",
                            split="calibration")
    assert out.get("error") is not None
