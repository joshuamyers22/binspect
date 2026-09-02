"""Deterministic numerical policy for visualization layers."""

from collections.abc import Callable

import numpy as np

from ..types import FloatArray, IntArray


def deviation_baseline(
    x: FloatArray,
    y: FloatArray,
    target: str,
    predict_fit: Callable[[FloatArray], FloatArray | float],
) -> FloatArray:
    """Return the comparison baseline for deviation rendering."""
    if target == "fit":
        return np.asarray(predict_fit(x), dtype=float)
    if target == "smooth":
        return smooth(x, y)
    raise ValueError(f"target must be 'fit' or 'smooth', got {target!r}.")


def rug_positions(
    observations: FloatArray, max_ticks: int, *, seed: int = 0
) -> FloatArray:
    """Return a deterministic bounded sample of rug positions."""
    x = np.asarray(observations, dtype=float)
    if x.size <= max_ticks:
        return x
    rng = np.random.default_rng(seed)
    return np.asarray(rng.choice(x, size=max_ticks, replace=False), dtype=float)


def line_span(bin_means: FloatArray, observations: FloatArray, span: str) -> FloatArray:
    """Return the x-domain for a fitted line without consulting a renderer."""
    if span == "bins":
        lo = float(np.min(bin_means))
        hi = float(np.max(bin_means))
        pad = 0.04 * (hi - lo)
        return np.array([lo - pad, hi + pad])
    if span == "data":
        return np.array([float(np.min(observations)), float(np.max(observations))])
    raise ValueError(f"span must be 'bins' or 'data', got {span!r}.")


def marker_sizes(counts: FloatArray | IntArray, base_size: float) -> FloatArray:
    """Scale marker area by bin count while retaining a visible minimum."""
    values = np.asarray(counts, dtype=float)
    scale = values / values.max() if values.max() > 0 else np.ones_like(values)
    return base_size * (0.45 + 0.9 * scale)


def smooth(x: FloatArray, y: FloatArray, frac: float = 0.6) -> FloatArray:
    """Return a tricube-weighted local linear smooth over bin means."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n = x.size
    if n < 3:
        return y.copy()

    span = max(int(np.ceil(frac * n)), 3)
    out = np.empty(n, dtype=float)
    for i in range(n):
        distance = np.abs(x - x[i])
        cutoff = np.sort(distance)[span - 1]
        if cutoff <= 0:
            out[i] = y[i]
            continue
        weights = np.clip(1.0 - (distance / cutoff) ** 3, 0.0, None) ** 3
        weight_sum = weights.sum()
        if weight_sum <= 0:
            out[i] = y[i]
            continue
        x_mean = np.sum(weights * x) / weight_sum
        y_mean = np.sum(weights * y) / weight_sum
        variance = np.sum(weights * (x - x_mean) ** 2)
        covariance = np.sum(weights * (x - x_mean) * (y - y_mean))
        slope = covariance / variance if variance > 0 else 0.0
        out[i] = y_mean + slope * (x[i] - x_mean)
    return out
