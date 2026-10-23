"""Scale-independent Procrustes distance between corresponding landmark points."""

import numpy as np
from skimage import transform


def landmark_distance(left: np.ndarray, right: np.ndarray) -> float:
    """Compare two corresponding (N, 2) point arrays, without reflections.

    Returns full Procrustes distance in [0, 1], up to floating-point precision.
    Translation, rotation and uniform scale are removed. Inputs must have
    nonzero spread; meaningful shape comparison requires more than two points.
    """
    left = np.asarray(left, dtype=np.float64)
    right = np.asarray(right, dtype=np.float64)
    left = left - left.mean(axis=0)
    right = right - right.mean(axis=0)
    left /= np.linalg.norm(left)
    right /= np.linalg.norm(right)

    alignment = transform.SimilarityTransform.from_estimate(right, left)
    return float(np.linalg.norm(left - alignment(right)))
