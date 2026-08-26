"""Public functions for estimating binned scatterplots."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike

from .core.binning import compute_binning
from .core.decompose import decompose
from .core.estimate import estimate_bins
from .core.lines import fit_ols, fit_sd_line
from .core.residualize import residualize
from .core.selection import select_n_bins
from .exceptions import InsufficientDataError
from .results import BinscatterResult
from .types import BinningMethod, FloatArray, ZeroWeightPolicy

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


def _labels(
    source: Mapping[str, Any] | pd.DataFrame | None,
    value: Any,
    label: str,
) -> tuple[np.ndarray[Any, np.dtype[Any]], str]:
    """Return a nonnumeric one-dimensional label array."""
    if isinstance(value, str):
        if source is None:
            raise ValueError(
                f"{label}={value!r} is a column name, but no data= was given."
            )
        try:
            values = source[value]
        except KeyError:
            available = list(getattr(source, "columns", source.keys()))
            raise KeyError(
                f"column {value!r} not found; available: {available}"
            ) from None
        name = value
    else:
        values = value
        name = str(getattr(value, "name", None) or label)
    array = np.asarray(values, dtype=object)
    if array.ndim != 1:
        raise ValueError(f"{label} must be one-dimensional, got shape {array.shape}.")
    return array, name


def _control_frame(
    source: Mapping[str, Any] | pd.DataFrame | None,
    controls: str | Sequence[str] | ArrayLike,
    n_obs: int,
) -> tuple[pd.DataFrame, tuple[str, ...]]:
    """Return controls as an unencoded DataFrame and their display names."""
    if (
        isinstance(controls, Sequence)
        and not isinstance(controls, (str, bytes))
        and len(controls) == 0
    ):
        raise ValueError("controls must contain at least one variable.")
    names: tuple[str, ...]
    if isinstance(controls, str):
        names = (controls,)
    elif (
        source is not None
        and isinstance(controls, Sequence)
        and not isinstance(controls, (np.ndarray, pd.Series, pd.DataFrame))
        and all(isinstance(value, str) for value in controls)
    ):
        names = tuple(str(value) for value in controls)
    else:
        names = ()

    if names:
        if source is None:
            raise ValueError("named controls require data=.")
        if len(set(names)) != len(names):
            raise ValueError("control column names must be unique.")
        try:
            frame = pd.DataFrame({name: source[name] for name in names})
        except KeyError as exc:
            available = list(getattr(source, "columns", source.keys()))
            raise KeyError(
                f"control column {exc.args[0]!r} not found; available: {available}"
            ) from None
    elif isinstance(controls, pd.DataFrame):
        frame = controls.copy()
        names = tuple(str(name) for name in frame.columns)
    else:
        array = np.asarray(controls)
        if array.ndim == 1:
            frame = pd.DataFrame(
                {str(getattr(controls, "name", None) or "control"): array}
            )
        elif array.ndim == 2:
            frame = pd.DataFrame(
                array, columns=[f"control_{index}" for index in range(array.shape[1])]
            )
        else:
            raise ValueError(
                f"controls must be one- or two-dimensional, got shape {array.shape}."
            )
        names = tuple(str(name) for name in frame.columns)

    if frame.shape[1] == 0:
        raise ValueError("controls must contain at least one variable.")
    if not frame.columns.is_unique:
        raise ValueError("control column names must be unique.")
    if len(frame) != n_obs:
        raise ValueError("controls must have the same number of rows as x and y.")
    return frame.reset_index(drop=True), names


def _encode_controls(frame: pd.DataFrame) -> FloatArray:
    """Encode numeric and categorical controls as a full-rank projection matrix."""
    encoded = pd.get_dummies(frame, drop_first=True, dtype=float)
    try:
        values = encoded.to_numpy(dtype=float)
    except (TypeError, ValueError):
        raise ValueError("controls must be numeric, boolean, or categorical.") from None
    return np.column_stack((np.ones(len(frame), dtype=float), values))


def binscatter(
    data: pd.DataFrame | Mapping[str, Any] | None = None,
    y: str | ArrayLike | None = None,
    x: str | ArrayLike | None = None,
    *,
    bins: int | str | ArrayLike = "auto",
    binning: BinningMethod = "quantile",
    weights: str | ArrayLike | None = None,
    zero_weight: ZeroWeightPolicy = "retain",
    controls: str | Sequence[str] | ArrayLike | None = None,
    cluster: str | ArrayLike | None = None,
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
    zero_weight : {"retain", "drop"}, default "retain"
        Treatment of zero-weight observations. ``"retain"`` keeps them in bin
        selection, unweighted counts, and descriptive arrays while excluding them
        from estimation and inference. ``"drop"`` removes them before binning, making
        them equivalent to omitted rows. This option has no effect without weights.
    controls : str, sequence of str, or array_like, optional
        Variables partialled out of both ``x`` and ``y`` using Frisch--Waugh--Lovell
        residualization. String values select columns from ``data``. Categorical
        controls are indicator-encoded. A constant is included automatically.
    cluster : str or array_like, optional
        Cluster identifier used for CR1 cluster-robust bin-mean intervals and slope
        standard errors. At least two nonmissing clusters are required.
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

    When controls are supplied, ``x`` and ``y`` are residualized on a constant and
    the encoded control matrix, then shifted back to their original weighted means.
    The reported slope equals the coefficient on ``x`` from the corresponding full
    least-squares model.

    Confidence intervals assume independent observations unless ``cluster`` is
    supplied. Clustered inference uses cluster-level score sums, a CR1 finite-sample
    correction, and t critical values based on the clusters represented in each bin.

    See Also
    --------
    binspect.results.BinscatterResult
        Results container returned by this function.
    """
    y_arr, y_name = _column(data, y, "y")
    x_arr, x_name = _column(data, x, "x")

    if zero_weight not in ("retain", "drop"):
        raise ValueError(
            f"zero_weight must be either 'retain' or 'drop', got {zero_weight!r}."
        )

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

    control_frame: pd.DataFrame | None = None
    control_names: tuple[str, ...] = ()
    if controls is not None:
        control_frame, control_names = _control_frame(data, controls, y_arr.size)

    cluster_arr: np.ndarray[Any, np.dtype[Any]] | None = None
    cluster_name: str | None = None
    if cluster is not None:
        cluster_arr, cluster_name = _labels(data, cluster, "cluster")
        if cluster_arr.shape != y_arr.shape:
            raise ValueError("cluster must have the same shape as x and y.")

    finite = np.isfinite(x_arr) & np.isfinite(y_arr)
    if w_arr is not None:
        finite &= np.isfinite(w_arr)
    if control_frame is not None:
        finite &= ~control_frame.isna().any(axis=1).to_numpy()
        numeric_controls = control_frame.select_dtypes(include="number")
        if numeric_controls.shape[1]:
            finite &= np.isfinite(numeric_controls.to_numpy(dtype=float)).all(axis=1)
    if cluster_arr is not None:
        finite &= np.asarray(pd.notna(cluster_arr), dtype=bool)

    if not finite.all():
        if not dropna:
            raise ValueError(
                f"{int((~finite).sum())} row(s) contain non-finite values; "
                "pass dropna=True to drop them."
            )
        x_arr, y_arr = x_arr[finite], y_arr[finite]
        if w_arr is not None:
            w_arr = w_arr[finite]
        if control_frame is not None:
            control_frame = control_frame.loc[finite].reset_index(drop=True)
        if cluster_arr is not None:
            cluster_arr = cluster_arr[finite]

    if w_arr is not None and not np.any(w_arr > 0):
        raise ValueError("weights must contain at least one positive value.")
    if w_arr is not None and zero_weight == "drop":
        positive = w_arr > 0
        x_arr, y_arr, w_arr = x_arr[positive], y_arr[positive], w_arr[positive]
        if control_frame is not None:
            control_frame = control_frame.loc[positive].reset_index(drop=True)
        if cluster_arr is not None:
            cluster_arr = cluster_arr[positive]

    if y_arr.size < 4:
        raise InsufficientDataError(
            f"need at least 4 usable observations, got {y_arr.size}."
        )

    cluster_active = np.ones(y_arr.size, dtype=bool) if w_arr is None else w_arr > 0
    if cluster_arr is not None and pd.unique(cluster_arr[cluster_active]).size < 2:
        raise InsufficientDataError(
            "cluster-robust inference requires at least 2 positive-weight clusters."
        )

    dof_resid: int | None = None
    if control_frame is not None:
        control_matrix = _encode_controls(control_frame)
        if not np.isfinite(control_matrix).all():
            raise ValueError("controls contain non-finite numeric values.")
        full_design = np.column_stack((control_matrix, x_arr))
        if w_arr is not None:
            full_design = full_design * np.sqrt(w_arr)[:, None]
        effective_n = y_arr.size if w_arr is None else int(np.count_nonzero(w_arr > 0))
        dof_resid = effective_n - int(np.linalg.matrix_rank(full_design))
        if dof_resid < 1:
            raise InsufficientDataError(
                "controls leave no residual degrees of freedom."
            )
        x_arr = residualize(x_arr, control_matrix, weights=w_arr)
        y_arr = residualize(y_arr, control_matrix, weights=w_arr)

    if isinstance(bins, (str, int, np.integer)):
        bin_rule = int(bins) if isinstance(bins, np.integer) else bins
        n_bins = select_n_bins(x_arr, bin_rule, y=y_arr)
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
        clusters=cluster_arr,
        ci=ci,
    )
    fit = fit_ols(
        x_arr,
        y_arr,
        weights=w_arr,
        dof_resid=dof_resid,
        clusters=cluster_arr,
    )
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
        controls=control_names,
        cluster=cluster_name,
        zero_weight=zero_weight,
    )
