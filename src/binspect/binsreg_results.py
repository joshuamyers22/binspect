"""Owned tabular results for binsreg's function estimand."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd

from .result_serialization import json_value

if TYPE_CHECKING:
    from matplotlib.axes import Axes


@dataclass(frozen=True)
class BinsregResult:
    """Function estimates in original x coordinates; no FWL slope/gap verdict.

    Public table/metadata accessors return copies. No raw input observations or
    upstream result object are retained. Confidence intervals have their own
    fitted centers, which need not equal the degree-0 dot estimates.
    """

    _dots: pd.DataFrame
    _intervals: pd.DataFrame
    _metadata: dict[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "_dots", self._dots.copy(deep=True))
        object.__setattr__(self, "_intervals", self._intervals.copy(deep=True))
        object.__setattr__(self, "_metadata", deepcopy(self._metadata))

    @property
    def dots(self) -> pd.DataFrame:
        return self._dots.copy(deep=True)

    @property
    def intervals(self) -> pd.DataFrame:
        return self._intervals.copy(deep=True)

    @property
    def metadata(self) -> dict[str, Any]:
        return deepcopy(self._metadata)

    def to_dict(self) -> dict[str, Any]:
        return {
            "metadata": self.metadata,
            "dots": [
                {k: json_value(v) for k, v in row.items()}
                for row in self._dots.to_dict(orient="records")
            ],
            "intervals": [
                {k: json_value(v) for k, v in row.items()}
                for row in self._intervals.to_dict(orient="records")
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
        import matplotlib.pyplot as plt

        if ax is None:
            _, ax = plt.subplots()
        ax.scatter(self._dots.x, self._dots.fit, label="Dot fit")
        ci = self._intervals
        if len(ci):
            center = ci["fit"].to_numpy()
            ax.errorbar(
                ci.x,
                center,
                yerr=np.vstack((center - ci.ci_lo, ci.ci_hi - center)),
                fmt="x",
                label="Interval fit",
            )
        ax.set_xlabel(self._metadata["x_name"])
        ax.set_ylabel(f"{self._metadata['y_name']} (function estimate)")
        ax.set_title(f"binsreg: {self._metadata['inference_status']}")
        ax.legend()
        return ax
