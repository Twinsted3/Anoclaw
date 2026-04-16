"""
Render Real3D-AD point clouds (.pcd) to 2D RGB images for VLM-based anomaly detection.

Usage:
    python render_real3d.py --data_root /hdd3/ljq/3dad_demo_more_pcd --output_dir /hdd1/jiangxi/AD-Agent/benchmark/data/Real3D-AD-RGB
"""

import argparse
import os
import numpy as np
from pathlib import Path


def render_pcd_to_image(pcd_path: str, output_path: str, width: int = 512, height: int = 512) -> bool:
    """Render a point cloud to a 2D image using Open3D offscreen rendering."""
    import open3d as o3d

    try:
        pcd = o3d.io.read_point_cloud(pcd_path)
        if len(pcd.points) == 0:
            return False

        # Compute colors if not present
        if not pcd.has_colors():
            # Color by height (z-coordinate)
            points = np.asarray(pcd.points)
            z = points[:, 2]
            z_norm = (z - z.min()) / (z.max() - z.min() + 1e-8)
            # Use a colormap: blue (low) -> green -> red (high)
            colors = np.zeros((len(points), 3))
            colors[:, 0] = z_norm  # R
            colors[:, 1] = 1 - np.abs(z_norm - 0.5) * 2  # G
            colors[:, 2] = 1 - z_norm  # B
            pcd.colors = o3d.utility.Vector3dVector(colors)

        # Compute normals for better visualization
        if not pcd.has_normals():
            pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30))

        # Set up offscreen renderer
        renderer = o3d.visualization.rendering.OffscreenRenderer(width, height)
        renderer.scene.set_background([1.0, 1.0, 1.0, 1.0])  # White background

        # Material
        mat = o3d.visualization.rendering.MaterialRecord()
        mat.shader = "defaultUnlit"
        mat.point_size = 3.0

        renderer.scene.add_geometry("pcd", pcd, mat)

        # Compute camera parameters to view the full point cloud
        bounds = pcd.get_axis_aligned_bounding_box()
        center = bounds.get_center()
        extent = bounds.get_max_extent()

        # Camera looking from front-top angle
        eye = center + np.array([extent * 0.8, -extent * 0.8, extent * 0.6])
        up = np.array([0.0, 0.0, 1.0])
        renderer.setup_camera(60.0, center, eye, up)

        # Render
        img = renderer.render_to_image()
        o3d.io.write_image(output_path, img)
        return True

    except Exception as e:
        print(f"  [WARN] Failed to render {pcd_path}: {e}")
        return False


def render_pcd_matplotlib(pcd_path: str, output_path: str, figsize: int = 6, dpi: int = 100) -> bool:
    """Fallback renderer using matplotlib (works without GPU/display)."""
    import open3d as o3d
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D

    try:
        pcd = o3d.io.read_point_cloud(pcd_path)
        if len(pcd.points) == 0:
            return False

        points = np.asarray(pcd.points)
        # Subsample if too many points
        if len(points) > 10000:
            idx = np.random.choice(len(points), 10000, replace=False)
            points = points[idx]

        fig = plt.figure(figsize=(figsize, figsize))
        ax = fig.add_subplot(111, projection='3d')

        # Color by height
        z = points[:, 2]
        ax.scatter(points[:, 0], points[:, 1], points[:, 2],
                   c=z, cmap='viridis', s=0.5, alpha=0.8)

        ax.set_xlim(points[:, 0].min(), points[:, 0].max())
        ax.set_ylim(points[:, 1].min(), points[:, 1].max())
        ax.set_zlim(points[:, 2].min(), points[:, 2].max())
        ax.view_init(elev=30, azim=45)
        ax.axis('off')

        plt.tight_layout()
        plt.savefig(output_path, dpi=dpi, bbox_inches='tight', pad_inches=0)
        plt.close()
        return True

    except Exception as e:
        print(f"  [WARN] Failed to render {pcd_path}: {e}")
        return False


def process_category(cat_dir: Path, output_dir: Path, renderer="matplotlib"):
    """Render all PCD files in a category directory."""
    cat_name = cat_dir.name
    cat_output = output_dir / cat_name
    render_fn = render_pcd_matplotlib if renderer == "matplotlib" else render_pcd_to_image

    results = {"normal": [], "anomaly": [], "template": []}

    for split in ["train", "test"]:
        split_dir = cat_dir / split
        if not split_dir.exists():
            # Flat structure: files directly in category dir
            split_dir = cat_dir

        for pcd_file in sorted(split_dir.glob("*.pcd")):
            stem = pcd_file.stem
            # Skip _cut versions (use full point clouds)
            if stem.endswith("_cut"):
                continue

            # Determine label from filename
            if "template" in stem:
                label = "template"
            elif "good" in stem:
                label = "normal"
            else:
                label = "anomaly"

            out_subdir = cat_output / split / label
            out_subdir.mkdir(parents=True, exist_ok=True)
            out_path = str(out_subdir / f"{stem}.png")

            if os.path.exists(out_path):
                results[label].append(out_path)
                continue

            success = render_fn(str(pcd_file), out_path)
            if success:
                results[label].append(out_path)

    return results


def main():
    parser = argparse.ArgumentParser(description="Render Real3D-AD point clouds to images")
    parser.add_argument("--data_root", default="/hdd3/ljq/3dad_demo_more_pcd")
    parser.add_argument("--output_dir", default="/hdd1/jiangxi/AD-Agent/benchmark/data/Real3D-AD-RGB")
    parser.add_argument("--renderer", default="matplotlib", choices=["matplotlib", "open3d"])
    args = parser.parse_args()

    data_root = Path(args.data_root)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Skip categories with too few files
    skip = {"gemstone_registration", "gyro"}

    categories = sorted([d for d in data_root.iterdir()
                         if d.is_dir() and d.name not in skip])

    print(f"Rendering {len(categories)} categories from {data_root}")
    print(f"Output: {output_dir}")
    print(f"Renderer: {args.renderer}")

    total_stats = {"normal": 0, "anomaly": 0, "template": 0}
    for cat in categories:
        print(f"\n  Processing {cat.name}...")
        results = process_category(cat, output_dir, args.renderer)
        for k, v in results.items():
            total_stats[k] += len(v)
            print(f"    {k}: {len(v)} images")

    print(f"\n=== Total: {total_stats['normal']} normal, {total_stats['anomaly']} anomaly, {total_stats['template']} template ===")


if __name__ == "__main__":
    main()
