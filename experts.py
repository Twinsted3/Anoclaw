"""
Extensible expert pool for AnomalyClaw anomaly detection.

Each expert takes a query image and reference images, runs a specialized
analysis using DINOv2 features, and returns a structured text report that
can be consumed by the VLM agent.

All DINOv2-based experts share a single lazily-loaded model instance.
"""

import math
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

import numpy as np
import torch
import torch.nn.functional as F

# ---------------------------------------------------------------------------
# Shared DINOv2 backbone (lazy singleton)
# ---------------------------------------------------------------------------

_dino_state: Dict = {}  # keys: "model", "transform", "device"


def _get_device() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"


def _get_dino(device: Optional[str] = None):
    """Return (model, transform) for DINOv2 ViT-S/14, loading on first call."""
    if "model" in _dino_state:
        return _dino_state["model"], _dino_state["transform"]

    import timm

    device = device or _get_device()
    model = timm.create_model(
        "vit_small_patch14_dinov2.lvd142m", pretrained=True, num_classes=0
    )
    model = model.to(device).eval()
    data_cfg = timm.data.resolve_data_config(model.pretrained_cfg)
    transform = timm.data.create_transform(**data_cfg, is_training=False)

    _dino_state["model"] = model
    _dino_state["transform"] = transform
    _dino_state["device"] = device
    return model, transform


# ---------------------------------------------------------------------------
# Feature extraction helpers
# ---------------------------------------------------------------------------

def _load_image_tensor(image_path: str, transform) -> torch.Tensor:
    from PIL import Image

    img = Image.open(image_path).convert("RGB")
    return transform(img).unsqueeze(0)


def _extract_patch_features(image_path: str) -> np.ndarray:
    """Return L2-normalised patch tokens [N_patches, D]."""
    model, transform = _get_dino()
    device = _dino_state["device"]
    tensor = _load_image_tensor(image_path, transform).to(device)
    with torch.no_grad():
        feats = model.forward_features(tensor)  # [1, 1+N, D]
        patches = F.normalize(feats[:, 1:, :], dim=-1)
    return patches.squeeze(0).cpu().numpy()


def _extract_cls_feature(image_path: str) -> np.ndarray:
    """Return L2-normalised CLS token [D]."""
    model, transform = _get_dino()
    device = _dino_state["device"]
    tensor = _load_image_tensor(image_path, transform).to(device)
    with torch.no_grad():
        feats = model.forward_features(tensor)
        cls = F.normalize(feats[:, 0, :], dim=-1)
    return cls.squeeze(0).cpu().numpy()


def _safe_extract(fn, path):
    """Call *fn(path)* and return None on any error."""
    if not os.path.exists(path):
        return None
    try:
        return fn(path)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------

class Expert(ABC):
    """Base class for an anomaly-detection expert."""

    name: str = "base"

    @abstractmethod
    def analyze(
        self,
        query_path: str,
        ref_paths: List[str],
        domain_code: str,
    ) -> str:
        """Return a structured text report."""


# ---------------------------------------------------------------------------
# PatchExpert
# ---------------------------------------------------------------------------

class PatchExpert(Expert):
    """PatchCore-style expert using DINOv2 patch-level nearest-neighbour distances.

    Calibration: sigmoid(20 * (raw_score - 0.18)) mapped to five qualitative
    levels (very similar / mostly normal / ambiguous / moderate anomaly /
    strong anomaly).
    """

    name = "patch"

    def __init__(self, max_refs: int = 8, top_fraction: float = 0.01):
        self.max_refs = max_refs
        self.top_fraction = top_fraction

    # -- internal ----------------------------------------------------------

    @staticmethod
    def _build_patch_bank(ref_paths: List[str], max_refs: int) -> np.ndarray:
        banks = []
        for p in ref_paths[:max_refs]:
            feat = _safe_extract(_extract_patch_features, p)
            if feat is not None:
                banks.append(feat)
        if not banks:
            return np.zeros((0, 384), dtype=np.float32)
        bank = np.concatenate(banks, axis=0)
        if bank.shape[0] > 20_000:
            rng = np.random.default_rng(42)
            idx = rng.choice(bank.shape[0], 20_000, replace=False)
            bank = bank[idx]
        return bank

    @staticmethod
    def _calibrate(raw: float) -> float:
        return 1.0 / (1.0 + math.exp(-20.0 * (raw - 0.18)))

    @staticmethod
    def _level(calibrated: float) -> str:
        if calibrated > 0.8:
            return "strong anomaly"
        if calibrated > 0.6:
            return "moderate anomaly"
        if calibrated > 0.4:
            return "ambiguous"
        if calibrated > 0.2:
            return "mostly normal"
        return "very similar to normal"

    # -- public API --------------------------------------------------------

    def analyze(self, query_path: str, ref_paths: List[str], domain_code: str) -> str:
        bank = self._build_patch_bank(ref_paths, self.max_refs)
        if bank.shape[0] == 0:
            return "PatchExpert: insufficient references (empty patch bank)."

        q_patches = _extract_patch_features(query_path)

        # Nearest-neighbour distances (batched for memory efficiency)
        batch_size = 512
        min_dists = []
        for i in range(0, q_patches.shape[0], batch_size):
            sims = q_patches[i : i + batch_size] @ bank.T
            min_dists.append(1.0 - sims.max(axis=1))
        min_dists = np.concatenate(min_dists)

        n_top = max(1, int(len(min_dists) * self.top_fraction))
        top_dists = np.sort(min_dists)[::-1][:n_top]
        raw_score = float(np.mean(top_dists))
        calibrated = self._calibrate(raw_score)

        # Global CLS similarity
        q_cls = _extract_cls_feature(query_path)
        ref_cls = [_safe_extract(_extract_cls_feature, p) for p in ref_paths[: self.max_refs]]
        ref_cls = [c for c in ref_cls if c is not None]
        if ref_cls:
            global_sim = float((q_cls @ np.stack(ref_cls).T).max())
        else:
            global_sim = float("nan")

        level = self._level(calibrated)
        return (
            f"PatchExpert report:\n"
            f"  Raw patch distance (top-{self.top_fraction:.0%}): {raw_score:.4f}\n"
            f"  Calibrated score: {calibrated:.4f}\n"
            f"  Global CLS similarity: {global_sim:.4f}\n"
            f"  Assessment: {level}"
        )


# ---------------------------------------------------------------------------
# RetrievalExpert
# ---------------------------------------------------------------------------

class RetrievalExpert(Expert):
    """Reports top-k CLS-token similarity between query and reference images."""

    name = "retrieval"

    def __init__(self, top_k: int = 4):
        self.top_k = top_k

    def analyze(self, query_path: str, ref_paths: List[str], domain_code: str) -> str:
        q_cls = _extract_cls_feature(query_path)
        sims: List[float] = []
        for p in ref_paths:
            feat = _safe_extract(_extract_cls_feature, p)
            if feat is not None:
                sims.append(float(q_cls @ feat))
        if not sims:
            return "RetrievalExpert: no valid reference images."

        sims_sorted = sorted(sims, reverse=True)[: self.top_k]
        top1 = sims_sorted[0]

        if top1 > 0.90:
            proximity = "visually close to"
        elif top1 > 0.75:
            proximity = "moderately similar to"
        else:
            proximity = "visually distant from"

        scores_str = ", ".join(f"{s:.3f}" for s in sims_sorted)
        return (
            f"RetrievalExpert report:\n"
            f"  Global similarity (top-{len(sims_sorted)}): {scores_str}\n"
            f"  Query is {proximity} references."
        )


# ---------------------------------------------------------------------------
# TextureExpert
# ---------------------------------------------------------------------------

class TextureExpert(Expert):
    """Lightweight texture consistency check via DINOv2 patch feature statistics.

    Compares mean and standard deviation of patch features between the query
    and the reference set and reports the divergence.
    """

    name = "texture"

    def __init__(self, max_refs: int = 8):
        self.max_refs = max_refs

    @staticmethod
    def _patch_stats(patches: np.ndarray):
        """Return (mean_vec, std_vec) over the patch dimension."""
        return patches.mean(axis=0), patches.std(axis=0)

    def analyze(self, query_path: str, ref_paths: List[str], domain_code: str) -> str:
        q_patches = _extract_patch_features(query_path)
        q_mean, q_std = self._patch_stats(q_patches)

        ref_means, ref_stds = [], []
        for p in ref_paths[: self.max_refs]:
            feat = _safe_extract(_extract_patch_features, p)
            if feat is not None:
                m, s = self._patch_stats(feat)
                ref_means.append(m)
                ref_stds.append(s)
        if not ref_means:
            return "TextureExpert: no valid reference images."

        ref_mean = np.mean(ref_means, axis=0)
        ref_std = np.mean(ref_stds, axis=0)

        mean_div = float(np.linalg.norm(q_mean - ref_mean))
        std_div = float(np.linalg.norm(q_std - ref_std))

        if mean_div < 0.10 and std_div < 0.06:
            verdict = "consistent"
        elif mean_div < 0.20 and std_div < 0.12:
            verdict = "mildly divergent"
        else:
            verdict = "divergent"

        return (
            f"TextureExpert report:\n"
            f"  Feature statistics: mean divergence {mean_div:.4f}, std divergence {std_div:.4f}\n"
            f"  Texture appears {verdict}."
        )


# ---------------------------------------------------------------------------
# SubspaceADExpert — PCA subspace of DINOv2 patch features
# ---------------------------------------------------------------------------

class SubspaceADExpert(Expert):
    """Training-free anomaly expert using PCA subspace of DINOv2 patch features.

    Inspired by SubspaceAD (Lendering et al., 2026): fit PCA on normal reference
    patch features, then measure reconstruction residual for query patches.
    """

    name = "subspace"

    def __init__(self, max_refs: int = 8, top_fraction: float = 0.01,
                 n_components: int = 50):
        self.max_refs = max_refs
        self.top_fraction = top_fraction
        self.n_components = n_components
        self._pca_cache: Dict[str, tuple] = {}  # key -> (mean, components)

    def _fit_pca(self, ref_paths: List[str], cache_key: str) -> tuple:
        """Fit PCA on normal reference patch features. Returns (mean, components)."""
        if cache_key in self._pca_cache:
            return self._pca_cache[cache_key]

        banks = []
        for p in ref_paths[:self.max_refs]:
            feat = _safe_extract(_extract_patch_features, p)
            if feat is not None:
                banks.append(feat)
        if not banks:
            return None, None

        bank = np.concatenate(banks, axis=0)  # [N_patches, D]
        # Subsample if too large
        if bank.shape[0] > 20_000:
            rng = np.random.default_rng(42)
            idx = rng.choice(bank.shape[0], 20_000, replace=False)
            bank = bank[idx]

        # PCA: center and compute SVD
        mean = bank.mean(axis=0)
        centered = bank - mean
        n_comp = min(self.n_components, bank.shape[0], bank.shape[1])
        U, S, Vt = np.linalg.svd(centered, full_matrices=False)
        components = Vt[:n_comp]  # [n_comp, D]
        total_var = (S ** 2).sum()
        explained_var = (S[:n_comp] ** 2).sum() / total_var if total_var > 0 else 0.0

        self._pca_cache[cache_key] = (mean, components, explained_var)
        return mean, components, explained_var

    @staticmethod
    def _calibrate(raw: float) -> float:
        """Sigmoid calibration tuned for subspace residual range."""
        return 1.0 / (1.0 + math.exp(-15.0 * (raw - 0.12)))

    @staticmethod
    def _level(calibrated: float) -> str:
        if calibrated > 0.8:
            return "strong anomaly"
        if calibrated > 0.6:
            return "moderate anomaly"
        if calibrated > 0.4:
            return "ambiguous"
        if calibrated > 0.2:
            return "mostly normal"
        return "very similar to normal"

    def analyze(self, query_path: str, ref_paths: List[str], domain_code: str) -> str:
        cache_key = f"{domain_code}_{hash(tuple(sorted(ref_paths[:self.max_refs])))}"
        result = self._fit_pca(ref_paths, cache_key)
        if result[0] is None:
            return "SubspaceADExpert: insufficient references for PCA."

        mean, components, explained_var = result
        q_patches = _extract_patch_features(query_path)  # [N, D]

        # Project query patches and compute residuals
        centered = q_patches - mean  # [N, D]
        projected = centered @ components.T @ components  # [N, D]
        residuals = np.linalg.norm(centered - projected, axis=1)  # [N]

        n_top = max(1, int(len(residuals) * self.top_fraction))
        top_residuals = np.sort(residuals)[::-1][:n_top]
        raw_score = float(np.mean(top_residuals))
        calibrated = self._calibrate(raw_score)
        level = self._level(calibrated)

        return (
            f"SubspaceADExpert report:\n"
            f"  PCA residual (top-{self.top_fraction:.0%}): {raw_score:.4f}\n"
            f"  Variance explained by normal subspace: {explained_var:.4f}\n"
            f"  Calibrated score: {calibrated:.4f}\n"
            f"  Assessment: {level}"
        )


# ---------------------------------------------------------------------------
# NormalCalibrationCache — per-category normal variation profiling
# ---------------------------------------------------------------------------

class NormalCalibrationCache:
    """Cache for per-category normal calibration evidence.

    Computes:
    1. Expert baseline scores (PatchExpert on ref-vs-ref) — pure GPU, no VLM
    2. Normal variation profile — requires one VLM call per category (amortized)
    """

    def __init__(self):
        self._cache: Dict[str, Dict] = {}

    def compute_expert_baseline(
        self, ref_paths: List[str], domain_code: str, max_refs: int = 8
    ) -> Dict:
        """Run PatchExpert on ref_i vs ref_others for each ref image.

        Returns statistics of normal-on-normal scores for calibration.
        """
        patch_expert = PatchExpert(max_refs=max_refs)
        scores = []
        refs = ref_paths[:max_refs]
        for i, ref_path in enumerate(refs):
            other_refs = [p for j, p in enumerate(refs) if j != i]
            if not other_refs:
                continue
            report = patch_expert.analyze(ref_path, other_refs, domain_code)
            # Parse calibrated score from report
            for line in report.split("\n"):
                if "Calibrated score:" in line:
                    try:
                        val = float(line.split(":")[-1].strip())
                        scores.append(val)
                    except ValueError:
                        pass

        if not scores:
            return {"mean": 0.15, "std": 0.05, "max": 0.25, "min": 0.05, "n": 0}

        return {
            "mean": float(np.mean(scores)),
            "std": float(np.std(scores)),
            "max": float(np.max(scores)),
            "min": float(np.min(scores)),
            "n": len(scores),
        }

    def get_cache_key(self, domain_code: str, category: str) -> str:
        return f"{domain_code}_{category}"

    def get(self, key: str) -> Optional[Dict]:
        return self._cache.get(key)

    def put(self, key: str, data: Dict) -> None:
        self._cache[key] = data

    def format_calibration_evidence(self, data: Dict) -> str:
        """Format cached calibration data as text for prompt injection."""
        parts = []

        baseline = data.get("expert_baseline", {})
        if baseline.get("n", 0) > 0:
            parts.append(
                f"Expert baseline on normal references (PatchExpert, n={baseline['n']}):\n"
                f"  Mean score: {baseline['mean']:.4f}, Std: {baseline['std']:.4f}\n"
                f"  Range: [{baseline['min']:.4f}, {baseline['max']:.4f}]\n"
                f"  Interpretation: scores within this range are NORMAL for this category."
            )

        profile = data.get("normal_variation_profile", {})
        if profile:
            parts.append("Normal variation profile (from confirmed normal images):")
            if isinstance(profile, dict):
                for k, v in profile.items():
                    parts.append(f"  {k}: {v}")
            else:
                parts.append(f"  {profile}")

        fp_flags = data.get("false_positive_flags", [])
        if fp_flags:
            parts.append("Known false positive patterns:")
            for fp in fp_flags:
                if isinstance(fp, dict):
                    parts.append(f"  - {fp.get('feature', '?')}: {fp.get('reason_not_anomalous', '?')}")
                else:
                    parts.append(f"  - {fp}")

        typical = data.get("typical_appearance", "")
        if typical:
            parts.append(f"Typical appearance: {typical}")

        return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# ExpertPool
# ---------------------------------------------------------------------------

# Registry of built-in expert classes keyed by name.
_EXPERT_CLASSES: Dict[str, type] = {
    "patch": PatchExpert,
    "retrieval": RetrievalExpert,
    "texture": TextureExpert,
    "subspace": SubspaceADExpert,
}


class ExpertPool:
    """Holds a collection of experts and dispatches analysis requests."""

    def __init__(self, experts: Optional[List[Expert]] = None):
        if experts is not None:
            self._experts = {e.name: e for e in experts}
        else:
            # Default: instantiate all built-in experts.
            self._experts = {name: cls() for name, cls in _EXPERT_CLASSES.items()}

    @property
    def available(self) -> List[str]:
        return list(self._experts.keys())

    def add(self, expert: Expert) -> None:
        self._experts[expert.name] = expert

    def run_selected(
        self,
        experts: List[str],
        query_path: str,
        ref_paths: List[str],
        domain_code: str,
    ) -> Dict[str, str]:
        """Run the named experts and return {name: text_report}."""
        results: Dict[str, str] = {}
        for name in experts:
            exp = self._experts.get(name)
            if exp is None:
                results[name] = f"Expert '{name}' not found. Available: {self.available}"
                continue
            try:
                results[name] = exp.analyze(query_path, ref_paths, domain_code)
            except Exception as exc:
                results[name] = f"Expert '{name}' failed: {exc}"
        return results

    def run_all(
        self,
        query_path: str,
        ref_paths: List[str],
        domain_code: str,
    ) -> Dict[str, str]:
        """Convenience: run every registered expert."""
        return self.run_selected(self.available, query_path, ref_paths, domain_code)
