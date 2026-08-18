"""The audit arithmetic.

Total variation in ``y`` splits into a between-bin and a within-bin part::

    SS_total   = sum_i (y_i - ybar)^2
    SS_between = sum_j n_j (ybar_j - ybar)^2
    SS_within  = sum_j sum_{i in j} (y_i - ybar_j)^2

``eta_sq = SS_between / SS_total`` is the R-squared of the saturated bin model.

A warning about eta-squared
---------------------------
It is tempting to write ``gap = eta_sq - r_sq_linear`` and call it curvature. That is
wrong, and the test suite proves it: **eta_sq is not an upper bound on the linear
R-squared.** A step function does not nest a straight line, so a coarse partition can
explain *less* of the variance than a line does. On a genuinely linear DGP with five
bins, ``eta_sq`` typically sits several points *below* ``r_sq_linear``; the bound only
emerges once bins are fine enough to approximate the line.

What is well defined is the **lack of fit** --- how far the bin means sit from the
fitted line, weighted by bin size::

    SS_lof = sum_j n_j (ybar_j - yhat(xbar_j))^2
    gap    = SS_lof / SS_total

This is non-negative by construction, it is exactly what the deviation-shading layer
draws (each shaded segment is one term's square root), and it is the quantity the
verdict keys off. ``eta_sq`` is still reported, because it says how much a saturated
model *could* explain --- it simply cannot be differenced against R-squared.

The classical lack-of-fit test splits residual variance into lack of fit and pure
error exactly when every observation in a group shares an identical ``x``. With
binned rather than replicated ``x``, the split is approximate, because ``x`` still
varies within a bin. So ``gap`` is a descriptive magnitude here, not the numerator of
an F test.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..types import FloatArray, IntArray, Line, Verdict

__all__ = ["GAP_THRESHOLD", "MIN_BIN_FOR_VERDICT", "Decomposition", "decompose"]

#: Lack of fit below this share of total variance is not worth acting on. A
#: heuristic for reading a picture, not a hypothesis test.
GAP_THRESHOLD = 0.02

#: Below this many observations in the smallest bin, bin means are noisy enough to
#: manufacture apparent curvature on their own.
MIN_BIN_FOR_VERDICT = 30


@dataclass(frozen=True, slots=True)
class Decomposition:
    """Variance split, lack of fit, and the diagnostics that fall out of them."""

    ss_between: float
    ss_within: float
    ss_total: float
    ss_lof: float
    eta_sq: float
    r_sq_linear: float
    gap: float
    verdict: Verdict
    min_bin_n: int

    def as_dict(self) -> dict[str, float | str | int]:
        return {
            "ss_between": self.ss_between,
            "ss_within": self.ss_within,
            "ss_total": self.ss_total,
            "ss_lof": self.ss_lof,
            "eta_sq": self.eta_sq,
            "r_sq_linear": self.r_sq_linear,
            "gap": self.gap,
            "verdict": self.verdict,
            "min_bin_n": self.min_bin_n,
        }


def _verdict(gap: float, min_bin_n: int) -> Verdict:
    if min_bin_n < MIN_BIN_FOR_VERDICT:
        return "underpowered bins"
    if gap < GAP_THRESHOLD:
        return "linear"
    return "curvature"


def decompose(
    y: FloatArray,
    x: FloatArray,
    assignment: IntArray,
    n_bins: int,
    fit: Line,
    r_sq_linear: float,
    *,
    weights: FloatArray | None = None,
) -> Decomposition:
    """Split the variation in ``y`` and measure the line's lack of fit.

    Parameters
    ----------
    y, x:
        Outcome and binning variable.
    assignment:
        Integer bin index per observation.
    n_bins:
        Number of bins.
    fit:
        The fitted line, supplied by :mod:`binspect.core.lines` so this module never
        has to estimate anything itself.
    r_sq_linear:
        R-squared of that line, likewise supplied rather than recomputed.
    weights:
        Non-negative reliability weights.

    Returns
    -------
    Decomposition

    Notes
    -----
    ``ss_between + ss_within == ss_total`` holds to machine precision and is asserted
    in the test suite. ``gap >= 0`` always. ``eta_sq - r_sq_linear`` may be negative
    and is deliberately not exposed as a diagnostic --- see the module docstring.
    """
    y = np.asarray(y, dtype=float)
    x = np.asarray(x, dtype=float)
    assignment = np.asarray(assignment, dtype=np.int64)
    w = np.ones_like(y) if weights is None else np.asarray(weights, dtype=float)

    sum_w = np.bincount(assignment, weights=w, minlength=n_bins).astype(float)
    sum_wy = np.bincount(assignment, weights=w * y, minlength=n_bins).astype(float)
    sum_wx = np.bincount(assignment, weights=w * x, minlength=n_bins).astype(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        bin_mean_y = sum_wy / sum_w
        bin_mean_x = sum_wx / sum_w

    grand_mean = float(np.sum(w * y) / np.sum(w))

    ss_total = float(np.sum(w * (y - grand_mean) ** 2))
    ss_between = float(np.sum(sum_w * (bin_mean_y - grand_mean) ** 2))
    ss_within = float(np.sum(w * (y - bin_mean_y[assignment]) ** 2))

    predicted = np.asarray(fit.predict(bin_mean_x), dtype=float)
    ss_lof = float(np.sum(sum_w * (bin_mean_y - predicted) ** 2))

    eta_sq = ss_between / ss_total if ss_total > 0 else 0.0
    gap = ss_lof / ss_total if ss_total > 0 else 0.0
    min_bin_n = int(np.bincount(assignment, minlength=n_bins).min())

    return Decomposition(
        ss_between=ss_between,
        ss_within=ss_within,
        ss_total=ss_total,
        ss_lof=ss_lof,
        eta_sq=float(eta_sq),
        r_sq_linear=float(r_sq_linear),
        gap=float(gap),
        verdict=_verdict(gap, min_bin_n),
        min_bin_n=min_bin_n,
    )
