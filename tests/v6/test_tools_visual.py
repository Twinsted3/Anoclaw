import sys
from pathlib import Path
import numpy as np
from PIL import Image
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "benchmark" / "scripts"))
from agent_tools_v6 import (  # noqa: E402
    tool_hotspot_cropper, tool_zoom_bbox, tool_patch_grid,
    tool_image_diff, tool_rotate_align, tool_side_by_side,
)


@pytest.fixture
def synthetic_image(tmp_path):
    arr = (np.random.rand(200, 200, 3) * 255).astype(np.uint8)
    p = tmp_path / "q.png"
    Image.fromarray(arr).save(p)
    return str(p)


def test_hotspot_cropper_returns_crop(synthetic_image):
    patches = [{"row": 10, "col": 10, "score": 2.1},
               {"row": 11, "col": 11, "score": 1.9},
               {"row": 12, "col": 10, "score": 1.5}]
    out = tool_hotspot_cropper(query_path=synthetic_image, patches=patches, k=3)
    assert out["error"] is None
    assert "crop_b64" in out
    assert out["bbox"][0] < out["bbox"][2]


def test_hotspot_cropper_empty_patches(synthetic_image):
    out = tool_hotspot_cropper(query_path=synthetic_image, patches=[], k=5)
    assert out["error"] is not None


def test_zoom_bbox_crops(synthetic_image):
    out = tool_zoom_bbox(query_path=synthetic_image, bbox=[10, 20, 100, 120])
    assert out["error"] is None
    assert out["bbox"] == [10, 20, 100, 120]
    assert "crop_b64" in out


def test_zoom_bbox_invalid(synthetic_image):
    out = tool_zoom_bbox(query_path=synthetic_image, bbox=[100, 100, 50, 50])
    assert out["error"] is not None


def test_patch_grid_returns_tiles(synthetic_image):
    out = tool_patch_grid(query_path=synthetic_image, rows=3, cols=3)
    assert out["error"] is None
    assert len(out["tiles"]) == 9


def test_patch_grid_invalid(synthetic_image):
    out = tool_patch_grid(query_path=synthetic_image, rows=0, cols=3)
    assert out["error"] is not None


def test_image_diff_returns_stats(synthetic_image, tmp_path):
    arr = (np.random.rand(200, 200, 3) * 255).astype(np.uint8)
    ref_path = str(tmp_path / "r.png")
    Image.fromarray(arr).save(ref_path)
    out = tool_image_diff(query_path=synthetic_image, ref_path=ref_path)
    assert out["error"] is None
    assert "diff_mask_b64" in out


def test_image_diff_missing_ref(synthetic_image):
    out = tool_image_diff(query_path=synthetic_image, ref_path="/nonexistent/x.png")
    assert out["error"] is not None


def test_rotate_align_returns_diff(synthetic_image, tmp_path):
    arr = (np.random.rand(200, 200, 3) * 255).astype(np.uint8)
    ref_path = str(tmp_path / "r.png")
    Image.fromarray(arr).save(ref_path)
    out = tool_rotate_align(query_path=synthetic_image, ref_path=ref_path)
    assert out["error"] is None
    assert "rotation_angle_deg" in out
    assert "aligned_diff_b64" in out


def test_side_by_side_returns_composite(synthetic_image, tmp_path):
    refs = []
    for i in range(4):
        arr = (np.random.rand(200, 200, 3) * 255).astype(np.uint8)
        p = str(tmp_path / f"r{i}.png")
        Image.fromarray(arr).save(p)
        refs.append(p)
    out = tool_side_by_side(query_path=synthetic_image, ref_paths=refs,
                            bbox=[10, 10, 100, 100])
    assert out["error"] is None
    assert "composite_b64" in out
