"""Linear fit and standard-deviation reference estimators."""

from __future__ import annotations

from typing import Any, Literal

import numpy as np

from ..types import FloatArray, Line, LineFit

__all__ = ["fit_ols", "fit_sd_line"]


def _moments(
    x: FloatArray, y: FloatArray, w: FloatArray
) -> tuple[float, float, float, float, float]:
    sw = float(np.sum(w))
    x_bar = float(np.sum(w * x) / sw)
    y_bar = float(np.sum(w * y) / sw)
    var_x = float(np.sum(w * (x - x_bar) ** 2) / sw)
    var_y = float(np.sum(w * (y - y_bar) ** 2) / sw)
    cov = float(np.sum(w * (x - x_bar) * (y - y_bar)) / sw)
    return x_bar, y_bar, var_x, var_y, cov


def _weights(y: FloatArray, weights: FloatArray | None) -> FloatArray:
    if weights is None:
        return np.ones_like(y, dtype=float)
    return np.asarray(weights, dtype=float)


def fit_ols(
    x: FloatArray,
    y: FloatArray,
    *,
    weights: FloatArray | None = None,
    dof_resid: int | None = None,
    clusters: np.ndarray[Any, np.dtype[Any]] | None = None,
) -> LineFit:
    """Fit a linear model by weighted least squares.

    Parameters
    ----------
    x, y : array_like
        Exogenous and endogenous variables.
    weights : array_like, optional
        Nonnegative reliability weights. Equal weights are used if omitted.
    dof_resid : int, optional
        Residual degrees of freedom. Defaults to ``n_obs - 2``. Adjusted models
        supply the degrees of freedom from the full design matrix.
    clusters : array_like, optional
        Cluster label per observation. When supplied, the slope standard error uses
        a CR1 cluster-robust sandwich estimator.

    Returns
    -------
    LineFit
        Parameter estimates and fit statistics.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    w = _weights(y, weights)

    x_bar, y_bar, var_x, var_y, cov = _moments(x, y, w)
    if var_x <= 0:
        raise ValueError("x has zero variance; a slope is not identified.")

    slope = cov / var_x
    intercept = y_bar - slope * x_bar
    r = cov / np.sqrt(var_x * var_y) if var_y > 0 else 0.0
    r_sq = float(r**2)

    n = int(y.size)
    effective_n = n if weights is None else int(np.count_nonzero(w > 0))
    resid = y - (intercept + slope * x)
    dof = max(effective_n - 2, 1) if dof_resid is None else dof_resid
    if dof < 1:
        raise ValueError("dof_resid must be positive.")
    n_clusters: int | None = None
    se_type: Literal["classical", "cluster"] = "classical"
    if clusters is None:
        sigma_sq = float(np.sum(w * resid**2) / (np.sum(w) / n) / dof) / n
        se_slope = float(np.sqrt(sigma_sq / var_x))
    else:
        cluster_values = np.asarray(clusters, dtype=object)
        if cluster_values.ndim != 1 or cluster_values.shape != y.shape:
            raise ValueError("clusters must be one-dimensional and match x and y.")
        import pandas as pd

        active = w > 0
        codes, uniques = pd.factorize(cluster_values[active], sort=False)
        if np.any(codes < 0):
            raise ValueError("clusters must not contain missing values.")
        n_clusters = int(uniques.size)
        if n_clusters < 2:
            raise ValueError("cluster-robust inference requires at least 2 clusters.")
        centered_x = x - x_bar
        cluster_scores = np.bincount(
            codes,
            weights=w[active] * centered_x[active] * resid[active],
            minlength=n_clusters,
        )
        bread = float(np.sum(w * centered_x**2))
        correction = (n_clusters / (n_clusters - 1.0)) * ((effective_n - 1.0) / dof)
        se_slope = float(np.sqrt(correction * np.sum(cluster_scores**2) / bread**2))
        se_type = "cluster"

    return LineFit(
        slope=float(slope),
        intercept=float(intercept),
        se_slope=se_slope,
        r=float(r),
        r_sq=r_sq,
        n_obs=n,
        se_type=se_type,
        n_clusters=n_clusters,
    )


def fit_sd_line(
    x: FloatArray, y: FloatArray, *, weights: FloatArray | None = None
) -> Line:
    """Estimate the standard-deviation reference line.

    Parameters
    ----------
    x, y : array_like
        Exogenous and endogenous variables.
    weights : array_like, optional
        Nonnegative reliability weights. Equal weights are used if omitted.

    Returns
    -------
    Line
        Standard-deviation reference line.

    Notes
    -----
    The slope is ``sign(r) * sd_y / sd_x`` and the line passes through the weighted
    means of ``x`` and ``y``. The weighted least-squares slope equals this slope
    multiplied by the correlation coefficient.

    The reference is descriptive and is not an additional fitted model.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    w = _weights(y, weights)

    x_bar, y_bar, var_x, var_y, cov = _moments(x, y, w)
    if var_x <= 0:
        raise ValueError("x has zero variance; an SD line is not defined.")

    sign = 1.0 if cov >= 0 else -1.0
    slope = sign * float(np.sqrt(var_y / var_x))
    return Line(slope=slope, intercept=float(y_bar - slope * x_bar))
