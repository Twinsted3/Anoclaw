"""Additional tools for AnomalyClaw agent — beyond the basic set.

New tools:
1. image_diff: pixel difference between query and nearest ref (for change detection)
2. segment_and_count: segment objects and count (for logical anomalies)
3. anomaly_heatmap_text: describe expert's anomaly pattern in text
4. ref_category_matcher: check if query matches ref category
"""
import numpy as np
from PIL import Image


def tool_image_diff(query_path: str, ref_path: str, threshold: float = 30) -> dict:
    """Compute absolute pixel difference between query and nearest ref.
    Returns change stats and a text description of where differences are.
    Useful for change detection (D6 LEVIR) and temporal comparison.
    """
    q = np.array(Image.open(query_path).convert("RGB").resize((256, 256)))
    r = np.array(Image.open(ref_path).convert("RGB").resize((256, 256)))
    diff = np.abs(q.astype(float) - r.astype(float)).mean(axis=2)

    # Threshold binary change mask
    changed = diff > threshold
    change_pct = changed.mean() * 100

    # Find change regions (quadrants)
    h, w = changed.shape
    regions = {
        "top-left": changed[:h // 2, :w // 2].mean(),
        "top-right": changed[:h // 2, w // 2:].mean(),
        "bottom-left": changed[h // 2:, :w // 2].mean(),
        "bottom-right": changed[h // 2:, w // 2:].mean(),
    }
    main_region = max(regions, key=regions.get)

    return {
        "change_percent": round(change_pct, 1),
        "mean_diff": round(diff.mean(), 1),
        "max_diff": round(diff.max(), 1),
        "main_change_region": main_region,
        "region_change_pcts": {k: round(v * 100, 1) for k, v in regions.items()},
        "description": (
            f"{change_pct:.0f}% of pixels changed (threshold={threshold}). "
            f"Main change region: {main_region} ({regions[main_region] * 100:.0f}%). "
            f"Mean pixel difference: {diff.mean():.1f}, max: {diff.max():.0f}."
        ),
    }


def tool_segment_and_count(query_path: str, ref_paths: list, grid_size: int = 8) -> dict:
    """Simple grid-based object counting via intensity clustering.
    Counts distinct intensity clusters in a grid overlay, comparing query vs refs.
    For logical anomalies: detects missing/extra/moved components.

    This is a rough structural tool — not pixel-perfect segmentation.
    """
    q = np.array(Image.open(query_path).convert("L").resize((256, 256)))
    r = np.array(Image.open(ref_paths[0]).convert("L").resize((256, 256)))

    # Grid-level comparison
    cell_h, cell_w = 256 // grid_size, 256 // grid_size
    q_grid = np.zeros((grid_size, grid_size))
    r_grid = np.zeros((grid_size, grid_size))
    for i in range(grid_size):
        for j in range(grid_size):
            q_cell = q[i * cell_h:(i + 1) * cell_h, j * cell_w:(j + 1) * cell_w]
            r_cell = r[i * cell_h:(i + 1) * cell_h, j * cell_w:(j + 1) * cell_w]
            q_grid[i, j] = q_cell.mean()
            r_grid[i, j] = r_cell.mean()

    # Difference
    diff_grid = np.abs(q_grid - r_grid)
    changed_cells = (diff_grid > 20).sum()
    total_cells = grid_size * grid_size

    # Find which cells differ most
    flat_idx = np.argsort(diff_grid.ravel())[::-1][:5]
    top_diffs = []
    for idx in flat_idx:
        i, j = idx // grid_size, idx % grid_size
        if diff_grid[i, j] > 10:
            top_diffs.append({"row": int(i), "col": int(j),
                             "diff": float(diff_grid[i, j])})

    return {
        "changed_cells": int(changed_cells),
        "total_cells": total_cells,
        "change_ratio": round(changed_cells / total_cells, 2),
        "top_differences": top_diffs,
        "description": (
            f"{changed_cells}/{total_cells} grid cells differ significantly. "
            f"Change ratio: {changed_cells / total_cells:.0%}. "
            + (f"Top changes at: {[(d['row'], d['col']) for d in top_diffs[:3]]}" if top_diffs else "No significant changes.")
        ),
    }


def tool_anomaly_heatmap_text(expert_info: dict) -> str:
    """Describe the expert's anomaly pattern as structured text.
    Tells the VLM WHERE the expert sees anomalies without showing an image.
    """
    patches = expert_info.get("subspacead_top_patches") or []
    if not patches:
        return "Expert did not flag any specific regions."

    # Cluster patches into regions
    regions = {}
    for p in patches[:10]:
        r = p.get("region", "unknown")
        regions[r] = regions.get(r, 0) + 1

    top_region = max(regions, key=regions.get) if regions else "unknown"
    score_range = (patches[0].get("score", 0), patches[-1].get("score", 0)) if len(patches) > 1 else (0, 0)

    concentration = patches[0].get("score", 0) / max(np.mean([p.get("score", 0) for p in patches[:5]]), 1e-6) if patches else 1.0

    desc = (
        f"Expert anomaly pattern: {len(patches)} hotspot patches detected. "
        f"Primary region: {top_region} ({regions.get(top_region, 0)} patches). "
        f"Score range: {score_range[0]:.1f} (strongest) to {score_range[1]:.1f} (weakest). "
    )
    if concentration > 1.3:
        desc += "Signal is CONCENTRATED in a small area → likely a localized defect."
    else:
        desc += "Signal is DISPERSED across multiple regions → could be overall degradation or normal variation."

    return desc


def tool_ref_category_matcher(query_path: str, ref_paths: list, model=None, transform=None,
                               device="cuda") -> dict:
    """Check whether query and refs are from the same visual category.
    Uses DINOv2 CLS similarity. Low similarity suggests category mismatch
    → the VLM should request better refs via reference_retriever.
    """
    import torch

    def get_emb(path):
        img = Image.open(path).convert("RGB")
        tensor = transform(img).unsqueeze(0).to(device)
        with torch.no_grad():
            emb = model(tensor)
        emb = emb.cpu().numpy().flatten()
        return emb / (np.linalg.norm(emb) + 1e-8)

    q_emb = get_emb(query_path)
    ref_sims = []
    for rp in ref_paths[:4]:
        r_emb = get_emb(rp)
        sim = float(q_emb @ r_emb)
        ref_sims.append(sim)

    avg_sim = np.mean(ref_sims)
    max_sim = max(ref_sims)

    if avg_sim > 0.85:
        match = "GOOD — refs match query category"
    elif avg_sim > 0.70:
        match = "MODERATE — refs are similar but not identical category"
    else:
        match = "POOR — refs may be a different product type. Consider using reference_retriever."

    return {
        "avg_similarity": round(avg_sim, 3),
        "max_similarity": round(max_sim, 3),
        "match_quality": match,
    }
