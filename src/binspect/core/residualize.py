"""Frisch--Waugh--Lovell residualization."""

from __future__ import annotations

import numpy as np

from ..types import FloatArray

__all__ = ["residualize"]


def residualize(
    values: FloatArray,
    controls: FloatArray,
    *,
    weights: FloatArray | None = None,
) -> FloatArray:
    """Residualize a variable on controls while retaining its original mean.

    Parameters
    ----------
    values : array_like
        Variable to residualize.
    controls : array_like
        Two-dimensional control matrix. Include a constant column when an
        intercept is required.
    weights : array_like, optional
        Nonnegative reliability weights used in the projection and mean.

    Returns
    -------
    ndarray
        Projection residuals shifted to the original weighted mean.

    Notes
    -----
    The least-squares solution is well-defined for rank-deficient control matrices.
    Consequently, explicitly including a constant in ``controls`` has no effect when
    the matrix already contains one.
    """
    y = np.asarray(values, dtype=float)
    design = np.asarray(controls, dtype=float)
    if y.ndim != 1:
        raise ValueError("values must be one-dimensional.")
    if design.ndim != 2 or design.shape[0] != y.size:
        raise ValueError("controls must be two-dimensional with one row per value.")

    if weights is None:
        root_weight = np.ones_like(y)
        mean = float(np.mean(y))
    else:
        weight = np.asarray(weights, dtype=float)
        root_weight = np.sqrt(weight)
        mean = float(np.average(y, weights=weight))

    weighted_design = design * root_weight[:, None]
    coefficient, *_ = np.linalg.lstsq(weighted_design, y * root_weight, rcond=None)
    return np.asarray(y - design @ coefficient + mean, dtype=float)
