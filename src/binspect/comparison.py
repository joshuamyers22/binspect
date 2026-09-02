"""Grouped binned scatterplot estimation and results."""

from __future__ import annotations

from collections.abc import Hashable, Mapping, Sequence
from dataclasses import replace
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike

from .api import binscatter
from .comparison_results import BinscatterCollection as BinscatterCollection
from .exceptions import InsufficientDataError
from .input_data import column as _column
from .input_data import control_frame as _control_frame
from .input_data import labels as _labels
from .results import BinscatterResult
from .types import BinningMethod, FloatArray, ZeroWeightPolicy

__all__ = ["BinscatterCollection", "compare"]


def _group_values(
    data: pd.DataFrame | Mapping[str, Any] | None,
    group: str | Sequence[Any],
) -> tuple[np.ndarray[Any, np.dtype[np.object_]], str]:
    if isinstance(group, str):
        if data is None:
            raise ValueError(
                f"group={group!r} is a column name, but no data= was given."
            )
        try:
            values = data[group]
        except KeyError:
            available = list(getattr(data, "columns", data.keys()))
            raise KeyError(
                f"column {group!r} not found; available: {available}"
            ) from None
        name = group
    else:
        values = group
        name = str(getattr(group, "name", None) or "group")

    array = np.asarray(values, dtype=object)
    if array.ndim != 1:
        raise ValueError(f"group must be one-dimensional, got shape {array.shape}.")
    return array, name


def compare(
    data: pd.DataFrame | Mapping[str, Any] | None = None,
    y: str | ArrayLike | None = None,
    x: str | ArrayLike | None = None,
    *,
    group: str | Sequence[Any],
    bins: int | str | ArrayLike = "auto",
    binning: BinningMethod = "quantile",
    weights: str | ArrayLike | None = None,
    zero_weight: ZeroWeightPolicy = "retain",
    controls: str | Sequence[str] | ArrayLike | None = None,
    cluster: str | ArrayLike | None = None,
    ci: float | None = 0.95,
    dropna: bool = True,
    common_bins: bool = True,
) -> BinscatterCollection:
    """Estimate binned scatterplots across groups.

    Parameters
    ----------
    data : pandas.DataFrame or Mapping, optional
        Data containing the variables. Not required when all variables are
        array-like.
    y : str or array_like
        Endogenous (response) variable.
    x : str or array_like
        Exogenous (regressor) variable used for binning.
    group : str or array_like
        Grouping variable. Missing group labels are excluded.
    bins : int, {"auto", "sturges", "iqr", "dpi"}, or array_like, default "auto"
        Number of bins, bin-selection rule, or custom bin edges.
    binning : {"quantile", "equal_width"}, default "quantile"
        Partition method.
    weights : str or array_like, optional
        Nonnegative reliability weights.
    zero_weight : {"retain", "drop"}, default "retain"
        Whether zero-weight observations remain in binning and descriptive counts or
        are removed before estimation. Passed to every pooled and grouped estimate.
    controls : str, sequence of str, or array_like, optional
        Variables partialled out of ``x`` and ``y`` within the pooled sample and
        each group. String values select columns from ``data``.
    cluster : str or array_like, optional
        Cluster identifier used for CR1 cluster-robust uncertainty in the pooled and
        group-specific estimates.
    ci : float or None, default 0.95
        Two-sided confidence level for bin means. Set to None to omit intervals.
    dropna : bool, default True
        If True, remove observations with nonfinite estimation inputs. If False,
        raise a ``ValueError`` when nonfinite values are present.
    common_bins : bool, default True
        If True, select bin edges from the pooled sample and use those edges for
        every group. If False, select bins independently within each group.

    Returns
    -------
    BinscatterCollection
        Pooled and group-specific estimation results.

    Notes
    -----
    Common edges support comparisons at the same values of ``x``. Empty intervals
    can still be merged within a group, so the number of nonempty bins may differ.

    See Also
    --------
    binspect.binscatter
        Estimate a single binned scatterplot.
    """
    y_values, y_name = _column(data, y, "y")
    x_values, x_name = _column(data, x, "x")
    group_values, group_name = _group_values(data, group)
    if x_values.shape != y_values.shape or group_values.shape != y_values.shape:
        raise ValueError("x, y, and group must have the same shape.")

    weight_values: FloatArray | None
    if weights is None:
        weight_values = None
    else:
        weight_values, _ = _column(data, weights, "weights")
        if weight_values.shape != y_values.shape:
            raise ValueError("weights must have the same shape as x, y, and group.")

    control_frame: pd.DataFrame | None = None
    if controls is not None:
        control_frame, _ = _control_frame(data, controls, y_values.size)

    cluster_values: np.ndarray[Any, np.dtype[Any]] | None = None
    cluster_name: str | None = None
    if cluster is not None:
        cluster_values, cluster_name = _labels(data, cluster, "cluster")
        if cluster_values.shape != y_values.shape:
            raise ValueError("cluster must have the same shape as x, y, and group.")

    group_ok = np.asarray(pd.notna(group_values), dtype=bool)
    if not group_ok.any():
        raise InsufficientDataError("group has no nonmissing values.")

    pooled = binscatter(
        x=x_values[group_ok],
        y=y_values[group_ok],
        bins=bins,
        binning=binning,
        weights=None if weight_values is None else weight_values[group_ok],
        zero_weight=zero_weight,
        controls=None if control_frame is None else control_frame.loc[group_ok],
        cluster=None if cluster_values is None else cluster_values[group_ok],
        ci=ci,
        dropna=dropna,
    )
    pooled = replace(pooled, x_name=x_name, y_name=y_name, cluster=cluster_name)
    group_bins: int | str | ArrayLike
    group_bins = pooled.binning.edges if common_bins else bins

    labels = pd.unique(group_values[group_ok])
    results: dict[Hashable, BinscatterResult] = {}
    for label in labels:
        if not isinstance(label, Hashable):
            raise TypeError(f"group labels must be hashable, got {label!r}.")
        selected = group_ok & (group_values == label)
        try:
            result = binscatter(
                x=x_values[selected],
                y=y_values[selected],
                bins=group_bins,
                binning=binning,
                weights=(None if weight_values is None else weight_values[selected]),
                zero_weight=zero_weight,
                controls=(
                    None if control_frame is None else control_frame.loc[selected]
                ),
                cluster=(None if cluster_values is None else cluster_values[selected]),
                ci=ci,
                dropna=dropna,
            )
        except InsufficientDataError as exc:
            raise InsufficientDataError(f"group {label!r}: {exc}") from exc
        results[label] = replace(
            result, x_name=x_name, y_name=y_name, cluster=cluster_name
        )

    return BinscatterCollection(
        results=results,
        pooled=pooled,
        group_name=group_name,
        common_bins=common_bins,
    )
