"""Stable grouped-result and presentation model."""

from __future__ import annotations

from collections.abc import Hashable, Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal

import numpy as np
import polars as pl

from .evidence import JsonExport
from .label_values import label_record
from .result_serialization import json_value
from .results import BinscatterResult
from .tabular import to_pandas

if TYPE_CHECKING:  # pragma: no cover
    import pandas as pd
    from matplotlib.figure import Figure


def _add_group_column(
    frame: pl.DataFrame, value: Hashable | None, dtype: pl.DataType
) -> pl.DataFrame:
    return frame.insert_column(
        0, pl.Series("group", [value] * frame.height, dtype=dtype)
    )


@dataclass(frozen=True, slots=True)
class BinscatterCollection(JsonExport):
    """Results from estimating binned scatterplots by group.

    Parameters
    ----------
    results : Mapping
        Immutable hashable group labels mapped to their immutable estimation
        results. The mapping is copied and exposed read-only; result values are
        safely shared. Tables and exports are independent editable projections.
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
    def table(self) -> pl.DataFrame:
        """Return occupied intervals by group, retaining original bin IDs/bounds.

        With common bins, equal IDs identify equal intervals across groups. With
        independent bins, IDs are local to each group's partition. Empty intervals
        have no row, so IDs need not be contiguous.
        """
        frames = [
            _add_group_column(result.table, group, self._group_dtype())
            for group, result in self.results.items()
        ]
        return pl.concat(frames, how="vertical_relaxed")

    def _group_dtype(self) -> pl.DataType:
        kinds = {label_record(group)["type"] for group in self.groups}
        if len(kinds) > 1 or "datetime64" in kinds:
            return pl.Object()
        try:
            return pl.Series("group", self.groups, strict=True).dtype
        except (TypeError, ValueError):
            return pl.Object()

    def summary_frame(self, *, include_pooled: bool = False) -> pl.DataFrame:
        """Return a Polars model/diagnostic summary by group."""
        frames = [
            _add_group_column(
                result.summary_frame(), group, self._group_dtype()
            ).insert_column(1, pl.Series("is_pooled", [False]))
            for group, result in self.results.items()
        ]
        if include_pooled:
            frames.append(
                _add_group_column(
                    self.pooled.summary_frame(), None, self._group_dtype()
                ).insert_column(1, pl.Series("is_pooled", [True]))
            )
        return pl.concat(frames, how="vertical_relaxed")

    def to_pandas(
        self,
        table: Literal["bins", "summary"] = "bins",
        *,
        include_pooled: bool = False,
    ) -> pd.DataFrame:
        """Return an editable pandas table or grouped summary."""
        if table == "bins":
            return to_pandas(self.table)
        if table == "summary":
            return to_pandas(self.summary_frame(include_pooled=include_pooled))
        raise ValueError("table must be bins or summary.")

    def to_dict(self) -> dict[str, Any]:
        """Return grouped estimation results using JSON-compatible values."""
        return {
            "group": self.group_name,
            "common_bins": self.common_bins,
            "schema_version": 1,
            "result_type": "collection",
            "sample": None
            if self.pooled.sample is None
            else self.pooled.sample.to_dict(self.pooled.n_obs),
            "pooled": self.pooled.to_dict(),
            "groups": [
                {
                    "value": json_value(group),
                    "label": label_record(group),
                    "result": result.to_dict(),
                }
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
        """Plot grouped results in a faceted figure."""
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
