import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "benchmark" / "scripts"))
from agent_tools_v6 import tool_domain_knowledge, TOOL_REGISTRY  # noqa: E402


def test_knowledge_stub():
    os.environ["ANOMA_TEST_STUB"] = "1"
    try:
        out = tool_domain_knowledge(question="what is normal industrial?")
    finally:
        del os.environ["ANOMA_TEST_STUB"]
    assert out["error"] is None
    assert "answer" in out


def test_tool_registry_has_13_tools():
    expected = {
        "tool_expert_score", "tool_hotspot_cropper", "tool_zoom_bbox",
        "tool_patch_grid", "tool_image_diff", "tool_rotate_align",
        "tool_side_by_side", "tool_reference_profiler",
        "tool_reference_retriever", "tool_component_counter",
        "tool_segment_and_count", "tool_texture_fft", "tool_domain_knowledge",
    }
    assert expected == set(TOOL_REGISTRY.keys())
