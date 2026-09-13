"""Owned tabular results for binsreg's function estimand."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

import polars as pl

from .evidence import JsonExport
from .result_serialization import json_value
from .tabular import numeric_table, to_pandas

if TYPE_CHECKING:
    import pandas as pd
    from matplotlib.axes import Axes


@dataclass(frozen=True)
class BinsregResult(JsonExport):
    """Function estimates in original x coordinates; no FWL slope/gap verdict.

    Public table/metadata accessors return copies. No raw input observations or
    upstream result object are retained. Confidence intervals have their own
    fitted centers, which need not equal the degree-0 dot estimates.
    """

    _dots: pl.DataFrame
    _intervals: pl.DataFrame
    _metadata: dict[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "_dots", numeric_table(self._dots))
        object.__setattr__(self, "_intervals", numeric_table(self._intervals))
        object.__setattr__(self, "_metadata", deepcopy(self._metadata))

    @property
    def dots(self) -> pl.DataFrame:
        return self._dots.clone()

    @property
    def intervals(self) -> pl.DataFrame:
        return self._intervals.clone()

    @property
    def metadata(self) -> dict[str, Any]:
        return deepcopy(self._metadata)

    def to_pandas(self, table: Literal["dots", "intervals"] = "dots") -> pd.DataFrame:
        """Return an independent pandas projection."""
        if table == "dots":
            return to_pandas(self.dots)
        if table == "intervals":
            return to_pandas(self.intervals)
        raise ValueError("table must be dots or intervals.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "result_type": "binsreg",
            "metadata": json_value(self.metadata),
            "dots": [
                {k: json_value(v) for k, v in row.items()}
                for row in self._dots.to_dicts()
            ],
            "intervals": [
                {k: json_value(v) for k, v in row.items()}
                for row in self._intervals.to_dicts()
            ],
        }

    def summary(self) -> str:
        meta = self._metadata
        return (
            f"binsreg {meta['backend_version']}: "
            "original-coordinate function estimate\n"
            f"Rows: {meta['n_obs']} / {meta['n_input']}; bins: {meta['actual_bins']}\n"
            f"Covariance: {meta['covariance']}; status: {meta['inference_status']}\n"
            f"Issues: {', '.join(meta['issues']) or 'none'}\n"
            "Pointwise function intervals; no general few-cluster or simultaneous "
            "coverage guarantee. Control evaluation values are treated as fixed."
        )

    def plot(self, ax: Axes | None = None) -> Axes:
        """Draw dots and intervals around their own fitted centers."""
        from .viz.binsreg import plot

        return plot(self, ax=ax)
