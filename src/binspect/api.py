"""Public functions for estimating binned scatterplots."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd

from .core.binning import compute_binning
from .core.decompose import decompose
from .core.estimate import estimate_bins
from .core.lines import fit_ols, fit_sd_line
from .core.selection import select_n_bins
from .exceptions import InsufficientDataError
from .results import BinscatterResult
from .types import BinningMethod, FloatArray

__all__ = ["binscatter"]


def _column(
    source: Mapping[str, Any] | pd.DataFrame | None,
    value: Any,
    label: str,
) -> tuple[FloatArray, str]:
    """Return a data column as a one-dimensional floating-point array."""
    if value is None:
        raise ValueError(f"{label} is required.")

    if isinstance(value, str):
        if source is None:
            raise ValueError(
                f"{label}={value!r} is a column name, but no data= was given."
            )
        try:
            column = source[value]
        except KeyError:
            available = list(getattr(source, "columns", source.keys()))
            raise KeyError(
                f"column {value!r} not found; available: {available}"
            ) from None
        return np.asarray(column, dtype=float), value

    array = np.asarray(value, dtype=float)
    if array.ndim != 1:
        raise ValueError(f"{label} must be one-dimensional, got shape {array.shape}.")
    name = getattr(value, "name", None) or label
    return array, str(name)


def binscatter(
    data: pd.DataFrame | Mapping[str, Any] | None = None,
    y: str | Sequence[float] | None = None,
    x: str | Sequence[float] | None = None,
    *,
    bins: int | str | Sequence[float] = "auto",
    binning: BinningMethod = "quantile",
    weights: str | Sequence[float] | None = None,
    ci: float | None = 0.95,
    dropna: bool = True,
) -> BinscatterResult:
    """Estimate a binned scatterplot and linear specification diagnostic.

    Parameters
    ----------
    data : pandas.DataFrame or Mapping, optional
        Data containing the variables. Not required when ``x``, ``y``, and
        ``weights`` are array-like.
    y : str or array_like
        Endogenous (response) variable. A string is interpreted as a column in
        ``data``.
    x : str or array_like
        Exogenous (regressor) variable used for binning. A string is interpreted as
        a column in ``data``.
    bins : int, {"auto", "sturges", "iqr", "dpi"}, or array_like, default "auto"
        Number of bins, bin-selection rule, or custom bin edges. Custom edges must
        be strictly increasing and cover the observed range of ``x``.
    binning : {"quantile", "equal_width"}, default "quantile"
        Partition method. Ignored when custom edges are supplied in ``bins``.
    weights : str or array_like, optional
        Nonnegative reliability weights. At least one weight, and the total weight
        in each bin, must be positive.
    ci : float or None, default 0.95
        Two-sided confidence level for bin means. Set to ``None`` to omit confidence
        intervals.
    dropna : bool, default True
        If True, remove observations with nonfinite values in any input. If False,
        raise a ``ValueError`` when nonfinite values are present.

    Returns
    -------
    BinscatterResult
        Estimation results and plotting methods.

    Examples
    --------
    >>> import numpy as np, binspect
    >>> rng = np.random.default_rng(0)
    >>> x = rng.normal(size=5_000)
    >>> y = np.tanh(x) + rng.normal(scale=0.5, size=5_000)
    >>> bs = binspect.binscatter(x=x, y=y, bins=20)
    >>> bs.decomposition.gap > 0.05   # bin means depart from the line
    True

    Notes
    -----
    The bin means are the fitted values from a saturated indicator regression,
    ``OLS(y ~ C(bin))``. The reported lack-of-fit measure is descriptive. It is not
    a hypothesis test for linearity.

    Confidence intervals use within-bin standard errors and assume independent
    observations. They are not heteroskedasticity- or cluster-robust.

    See Also
    --------
    binspect.results.BinscatterResult
        Results container returned by this function.
    """
    y_arr, y_name = _column(data, y, "y")
    x_arr, x_name = _column(data, x, "x")

    if x_arr.shape != y_arr.shape:
        raise ValueError(
            f"x and y must have the same shape, got {x_arr.shape} and {y_arr.shape}."
        )

    if weights is None:
        w_arr: FloatArray | None = None
    else:
        w_arr, _ = _column(data, weights, "weights")
        if w_arr.shape != y_arr.shape:
            raise ValueError("weights must have the same shape as x and y.")
        if np.any(w_arr < 0):
            raise ValueError("weights must be non-negative.")

    finite = np.isfinite(x_arr) & np.isfinite(y_arr)
    if w_arr is not None:
        finite &= np.isfinite(w_arr)

    if not finite.all():
        if not dropna:
            raise ValueError(
                f"{int((~finite).sum())} row(s) contain non-finite values; "
                "pass dropna=True to drop them."
            )
        x_arr, y_arr = x_arr[finite], y_arr[finite]
        if w_arr is not None:
            w_arr = w_arr[finite]

    if y_arr.size < 4:
        raise InsufficientDataError(
            f"need at least 4 usable observations, got {y_arr.size}."
        )

    if w_arr is not None and not np.any(w_arr > 0):
        raise ValueError("weights must contain at least one positive value.")

    if isinstance(bins, (str, int, np.integer)):
        n_bins = select_n_bins(x_arr, bins, y=y_arr)
        binning_obj = compute_binning(x_arr, n_bins, method=binning)
    else:
        binning_obj = compute_binning(
            x_arr, method="custom", edges=np.asarray(bins, dtype=float)
        )

    estimates = estimate_bins(
        x_arr,
        y_arr,
        binning_obj.assignment,
        binning_obj.n_bins,
        weights=w_arr,
        ci=ci,
    )
    fit = fit_ols(x_arr, y_arr, weights=w_arr)
    sd_line = fit_sd_line(x_arr, y_arr, weights=w_arr)
    decomposition = decompose(
        y_arr,
        x_arr,
        binning_obj.assignment,
        binning_obj.n_bins,
        fit,
        fit.r_sq,
        weights=w_arr,
    )

    return BinscatterResult(
        binning=binning_obj,
        estimates=estimates,
        fit=fit,
        sd_line=sd_line,
        decomposition=decomposition,
        x=x_arr,
        y=y_arr,
        weights=w_arr,
        x_name=x_name,
        y_name=y_name,
    )
