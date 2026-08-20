"""Grouped binned scatterplot estimation and results."""

from __future__ import annotations

from collections.abc import Hashable, Mapping, Sequence
from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, cast

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike

from .api import _column, _control_frame, binscatter
from .exceptions import InsufficientDataError
from .results import BinscatterResult, _json_value
from .types import BinningMethod, FloatArray

if TYPE_CHECKING:  # pragma: no cover
    from matplotlib.figure import Figure

__all__ = ["BinscatterCollection", "compare"]


@dataclass(frozen=True, slots=True)
class BinscatterCollection:
    """Results from estimating binned scatterplots by group.

    Parameters
    ----------
    results : Mapping
        Group labels mapped to their estimation results.
    pooled : BinscatterResult
        Results estimated from all observations with nonmissing group labels.
    group_name : str
        Display name of the grouping variable.
    common_bins : bool
        Whether group estimates use edges selected from the pooled sample.
    """

    results: Mapping[Hashable, BinscatterResult]
    pooled: BinscatterResult
    group_name: str
    common_bins: bool

    def __post_init__(self) -> None:
        if not self.results:
            raise ValueError("results must contain at least one group.")
        object.__setattr__(self, "results", MappingProxyType(dict(self.results)))

    @property
    def groups(self) -> tuple[Hashable, ...]:
        """Return group labels in estimation order."""
        return tuple(self.results)

    @property
    def table(self) -> pd.DataFrame:
        """Return per-bin estimates for all groups as a DataFrame.

        The ``group`` column contains group labels. The original variable name is
        available in :attr:`group_name`.
        """
        return pd.concat(
            [
                _add_group_column(result.table, "group", group)
                for group, result in self.results.items()
            ],
            ignore_index=True,
        ).loc[:, ["group", *self.pooled.table.columns]]

    def summary_frame(self, *, include_pooled: bool = False) -> pd.DataFrame:
        """Return model and diagnostic statistics by group.

        Parameters
        ----------
        include_pooled : bool, default False
            If True, append the pooled-sample results. Pooled rows have
            ``is_pooled=True`` and a missing ``group`` value.
        """
        frames = [
            _add_summary_group(result.summary_frame(), group, is_pooled=False)
            for group, result in self.results.items()
        ]
        if include_pooled:
            frames.append(_add_summary_group(self.pooled.summary_frame(), None, True))
        summary = pd.concat(frames, ignore_index=True)
        return summary.loc[
            :, ["group", "is_pooled", *self.pooled.summary_frame().columns]
        ]

    def to_dict(self) -> dict[str, Any]:
        """Return grouped estimation results using JSON-compatible values."""
        return {
            "group": self.group_name,
            "common_bins": self.common_bins,
            "pooled": self.pooled.to_dict(),
            "groups": [
                {"value": _json_value(group), "result": result.to_dict()}
                for group, result in self.results.items()
            ],
        }

    def plot(
        self,
        *,
        layout: str = "facets",
        ncols: int | None = None,
        sharex: bool = True,
        sharey: bool = True,
        theme: str = "notebook",
        show: Sequence[str] | None = None,
        annotate: str | None = "minimal",
        legend: bool = False,
        layer_kwargs: dict[str, dict[str, Any]] | None = None,
    ) -> Figure:
        """Plot grouped results in a faceted figure.

        Parameters
        ----------
        layout : {"facets"}, default "facets"
            Plot layout. Additional layouts may be added in future releases.
        ncols : int, optional
            Number of facet columns. Defaults to at most three.
        sharex, sharey : bool, default True
            Whether facets share their x- and y-axis limits.
        theme : {"notebook", "paper", "deck"}, default "notebook"
            Visual theme applied to each facet.
        show : sequence of str, optional
            Plot layers to draw.
        annotate : {"minimal", "audit"} or None, default "minimal"
            Plot annotation level.
        legend : bool, default False
            If True, draw a legend in each facet.
        layer_kwargs : dict, optional
            Keyword arguments by plot layer.

        Returns
        -------
        matplotlib.figure.Figure
            Figure containing one facet per group.
        """
        if layout != "facets":
            raise ValueError(f"layout must be 'facets', got {layout!r}.")

        import matplotlib.pyplot as plt

        count = len(self.results)
        columns = min(3, count) if ncols is None else ncols
        if columns < 1:
            raise ValueError(f"ncols must be positive, got {columns}.")
        rows = int(np.ceil(count / columns))
        figure, axes = plt.subplots(
            rows,
            columns,
            squeeze=False,
            sharex=sharex,
            sharey=sharey,
        )
        flat_axes = axes.reshape(-1)
        for ax, (group, result) in zip(flat_axes, self.results.items(), strict=False):
            result.plot(
                ax=ax,
                theme=theme,
                show=show,
                annotate=annotate,
                legend=legend,
                title=f"{self.group_name} = {group}",
                layer_kwargs=layer_kwargs,
            )
        for ax in flat_axes[count:]:
            ax.remove()
        figure.tight_layout()
        return figure


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


def _add_group_column(frame: pd.DataFrame, name: str, value: Hashable) -> pd.DataFrame:
    result = frame.copy()
    result.insert(0, name, cast(Any, value))
    return result


def _add_summary_group(
    frame: pd.DataFrame, value: Hashable | None, is_pooled: bool
) -> pd.DataFrame:
    result = _add_group_column(frame, "group", value)
    result.insert(1, "is_pooled", is_pooled)
    return result


def compare(
    data: pd.DataFrame | Mapping[str, Any] | None = None,
    y: str | ArrayLike | None = None,
    x: str | ArrayLike | None = None,
    *,
    group: str | Sequence[Any],
    bins: int | str | ArrayLike = "auto",
    binning: BinningMethod = "quantile",
    weights: str | ArrayLike | None = None,
    controls: str | Sequence[str] | ArrayLike | None = None,
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
    controls : str, sequence of str, or array_like, optional
        Variables partialled out of ``x`` and ``y`` within the pooled sample and
        each group. String values select columns from ``data``.
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

    group_ok = np.asarray(pd.notna(group_values), dtype=bool)
    if not group_ok.any():
        raise InsufficientDataError("group has no nonmissing values.")

    pooled = binscatter(
        x=x_values[group_ok],
        y=y_values[group_ok],
        bins=bins,
        binning=binning,
        weights=None if weight_values is None else weight_values[group_ok],
        controls=None if control_frame is None else control_frame.loc[group_ok],
        ci=ci,
        dropna=dropna,
    )
    pooled = replace(pooled, x_name=x_name, y_name=y_name)
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
                controls=(
                    None if control_frame is None else control_frame.loc[selected]
                ),
                ci=ci,
                dropna=dropna,
            )
        except InsufficientDataError as exc:
            raise InsufficientDataError(f"group {label!r}: {exc}") from exc
        results[label] = replace(result, x_name=x_name, y_name=y_name)

    return BinscatterCollection(
        results=results,
        pooled=pooled,
        group_name=group_name,
        common_bins=common_bins,
    )
