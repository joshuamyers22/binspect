"""Estimation of within-bin summary statistics."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats

from ..types import FloatArray, IntArray

__all__ = ["BinEstimates", "estimate_bins"]


@dataclass(frozen=True, slots=True)
class BinEstimates:
    """Within-bin summary statistics.

    Parameters
    ----------
    x_mean, y_mean : ndarray
        Weighted means of the exogenous and endogenous variables.
    y_sd : ndarray
        Weighted standard deviation of the endogenous variable.
    n : ndarray
        Unweighted observation counts.
    sum_w : ndarray
        Sum of weights.
    se : ndarray
        Standard errors of the endogenous-variable means.
    ci_lo, ci_hi : ndarray
        Lower and upper confidence limits.
    ci_level : float or None
        Confidence level, or None when intervals were not estimated.
    """

    x_mean: FloatArray
    y_mean: FloatArray
    y_sd: FloatArray
    n: IntArray
    sum_w: FloatArray
    se: FloatArray
    ci_lo: FloatArray
    ci_hi: FloatArray
    ci_level: float | None

    @property
    def n_bins(self) -> int:
        return int(self.y_mean.size)


def _group_sum(
    values: FloatArray | IntArray, assignment: IntArray, n_bins: int
) -> FloatArray:
    """Sum numeric values by bin and normalize the result to floating point."""
    numeric_values = np.asarray(values, dtype=float)
    totals = np.bincount(assignment, weights=numeric_values, minlength=n_bins)
    return totals.astype(float)


def estimate_bins(
    x: FloatArray,
    y: FloatArray,
    assignment: IntArray,
    n_bins: int,
    *,
    weights: FloatArray | None = None,
    ci: float | None = 0.95,
) -> BinEstimates:
    """Estimate means, dispersion, and standard errors by bin.

    Parameters
    ----------
    x, y : array_like
        Finite exogenous and endogenous variables of equal length.
    assignment : array_like
        Integer bin index per observation, as produced by ``compute_binning``.
    n_bins : int
        Number of bins.
    weights : array_like, optional
        Nonnegative reliability weights. Equal weights are used if omitted.
    ci : float or None, default 0.95
        Two-sided confidence level for the bin means. Set to None to omit intervals.

    Returns
    -------
    BinEstimates
        Per-bin estimates.

    Notes
    -----
    The within-bin SD uses a denominator of ``n - 1`` (``NaN`` for singleton bins).
    Standard errors are the within-bin ``sd / sqrt(n)``: correct under independence,
    and *not* cluster-robust. Clustered variance arrives in a later release; until
    then, treat these intervals as descriptive when the data are grouped.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    assignment = np.asarray(assignment, dtype=np.int64)

    if weights is None:
        w = np.ones_like(y, dtype=float)
    else:
        w = np.asarray(weights, dtype=float)
        if np.any(w < 0):
            raise ValueError("weights must be non-negative.")

    counts = np.bincount(assignment, minlength=n_bins).astype(np.int64)
    sum_w = _group_sum(w, assignment, n_bins)
    if np.any(sum_w <= 0):
        empty = np.flatnonzero(sum_w <= 0).tolist()
        raise ValueError(
            f"each bin must have positive total weight; zero-weight bin(s): {empty}."
        )

    with np.errstate(invalid="ignore", divide="ignore"):
        x_mean = _group_sum(w * x, assignment, n_bins) / sum_w
        y_mean = _group_sum(w * y, assignment, n_bins) / sum_w

    # Weighted within-bin variance with a reliability-weight (frequency-free)
    # correction: sum(w) - sum(w^2) / sum(w) reduces to n - 1 when all w are equal.
    resid_sq = w * (y - y_mean[assignment]) ** 2
    ss_w = _group_sum(resid_sq, assignment, n_bins)
    sum_w2 = _group_sum(w**2, assignment, n_bins)
    with np.errstate(invalid="ignore", divide="ignore"):
        denom = sum_w - sum_w2 / sum_w
        variance = np.where(denom > 0, ss_w / denom, np.nan)
    y_sd = np.sqrt(variance)

    with np.errstate(invalid="ignore", divide="ignore"):
        eff_n = np.where(sum_w2 > 0, sum_w**2 / sum_w2, np.nan)
        se = y_sd / np.sqrt(eff_n)

    if ci is None:
        ci_lo = np.full(n_bins, np.nan)
        ci_hi = np.full(n_bins, np.nan)
    else:
        if not 0.0 < ci < 1.0:
            raise ValueError(f"ci must lie strictly between 0 and 1, got {ci}.")
        df = np.maximum(eff_n - 1.0, 1.0)
        crit = stats.t.ppf(0.5 + ci / 2.0, df)
        ci_lo = y_mean - crit * se
        ci_hi = y_mean + crit * se

    return BinEstimates(
        x_mean=x_mean,
        y_mean=y_mean,
        y_sd=y_sd,
        n=counts,
        sum_w=sum_w,
        se=se,
        ci_lo=ci_lo,
        ci_hi=ci_hi,
        ci_level=ci,
    )
