import sys
from pathlib import Path
import numpy as np
from PIL import Image
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "benchmark" / "scripts"))
from agent_tools_v6 import (  # noqa: E402
    tool_component_counter, tool_segment_and_count, tool_texture_fft,
)


@pytest.fixture
def synthetic_image(tmp_path):
    arr = np.zeros((256, 256, 3), dtype=np.uint8)
    arr[10:50, 10:50] = 255
    arr[100:150, 100:150] = 255
    p = str(tmp_path / "q.png")
    Image.fromarray(arr).save(p)
    return p


def test_component_counter_counts(synthetic_image):
    # 4-connectivity: diagonals not counted. Two clusters of 4-adjacent patches.
    patches = [{"row": 5, "col": 5}, {"row": 5, "col": 6},
               {"row": 20, "col": 20}, {"row": 21, "col": 20}]
    out = tool_component_counter(patches=patches, threshold=0.5)
    assert out["error"] is None
    assert out["n_components"] == 2


def test_segment_and_count_works(synthetic_image):
    out = tool_segment_and_count(query_path=synthetic_image,
                                 ref_paths=[synthetic_image])
    assert out["error"] is None
    assert "changed_cells" in out


def test_texture_fft_score(synthetic_image):
    out = tool_texture_fft(query_path=synthetic_image)
    assert out["error"] is None
    assert 0.0 <= out["periodicity_score"] <= 1.0
