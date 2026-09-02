"""Stable grouped-result and presentation model."""

from __future__ import annotations

from collections.abc import Hashable, Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, cast

import numpy as np
import pandas as pd

from .result_serialization import json_value
from .results import BinscatterResult

if TYPE_CHECKING:  # pragma: no cover
    from matplotlib.figure import Figure


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
        """Return per-bin estimates for all groups as a DataFrame."""
        return pd.concat(
            [
                _add_group_column(result.table, "group", group)
                for group, result in self.results.items()
            ],
            ignore_index=True,
        ).loc[:, ["group", *self.pooled.table.columns]]

    def summary_frame(self, *, include_pooled: bool = False) -> pd.DataFrame:
        """Return model and diagnostic statistics by group."""
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
                {"value": json_value(group), "result": result.to_dict()}
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
