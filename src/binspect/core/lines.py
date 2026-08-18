"""The two straight lines drawn over a binscatter.

The OLS line has slope ``r * sd_y / sd_x``. The SD line has slope ``sign(r) * sd_y /
sd_x``. The regression line is therefore the SD line flattened by ``r`` --- the
regression-to-the-mean effect, visible directly on the plot. That relationship is
asserted as an exact test.
"""

from __future__ import annotations

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
    x: FloatArray, y: FloatArray, *, weights: FloatArray | None = None
) -> LineFit:
    """Fit ``y ~ x`` by (weighted) least squares.

    Returns
    -------
    LineFit
        Slope, intercept, slope standard error, correlation and R-squared.
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
    resid = y - (intercept + slope * x)
    dof = max(n - 2, 1)
    sigma_sq = float(np.sum(w * resid**2) / (np.sum(w) / n) / dof) / n
    se_slope = float(np.sqrt(sigma_sq / var_x)) if var_x > 0 else np.nan

    return LineFit(
        slope=float(slope),
        intercept=float(intercept),
        se_slope=se_slope,
        r=float(r),
        r_sq=r_sq,
        n_obs=n,
    )


def fit_sd_line(
    x: FloatArray, y: FloatArray, *, weights: FloatArray | None = None
) -> Line:
    """The SD line: slope ``sign(r) * sd_y / sd_x`` through the point of averages.

    This is the line the eye draws through an elliptical cloud, and it is always at
    least as steep as the OLS line. It is also the geometric mean of the ``y on x``
    and ``x on y`` regression slopes.
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
