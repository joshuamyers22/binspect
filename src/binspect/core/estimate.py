"""Per-bin summaries.

The identity that anchors this module: the bin means computed here are exactly the
fitted values of ``OLS(y ~ C(bin))`` --- the saturated dummy regression. Every
downstream claim about auditing a linear model rests on that, so it is asserted as
an equality test rather than described in a docstring alone.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats

from ..types import FloatArray, IntArray

__all__ = ["BinEstimates", "estimate_bins"]


@dataclass(frozen=True, slots=True)
class BinEstimates:
    """Per-bin summary statistics, all arrays of length ``n_bins``."""

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


def _group_sum(values: FloatArray, assignment: IntArray, n_bins: int) -> FloatArray:
    return np.bincount(assignment, weights=values, minlength=n_bins).astype(float)


def estimate_bins(
    x: FloatArray,
    y: FloatArray,
    assignment: IntArray,
    n_bins: int,
    *,
    weights: FloatArray | None = None,
    ci: float | None = 0.95,
) -> BinEstimates:
    """Compute per-bin means, dispersion and standard errors.

    Parameters
    ----------
    x, y:
        Finite arrays of equal length.
    assignment:
        Integer bin index per observation, as produced by ``compute_binning``.
    n_bins:
        Number of bins.
    weights:
        Non-negative reliability weights. ``None`` means equal weights.
    ci:
        Two-sided confidence level for the per-bin mean, or ``None`` to skip.

    Returns
    -------
    BinEstimates

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
