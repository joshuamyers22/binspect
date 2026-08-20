"""Results classes for binned scatterplot estimation."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from textwrap import wrap
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd

from .core.binning import Binning
from .core.decompose import Decomposition
from .core.estimate import BinEstimates
from .types import FloatArray, Line, LineFit

if TYPE_CHECKING:  # pragma: no cover
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

__all__ = ["BinscatterResult"]


@dataclass(frozen=True, slots=True)
class BinscatterResult:
    """Results from binned scatterplot estimation.

    Parameters
    ----------
    binning : Binning
        Bin edges, assignments, and partition metadata.
    estimates : BinEstimates
        Per-bin location, dispersion, and uncertainty estimates.
    fit : LineFit
        Weighted least-squares fit of ``y`` on ``x``.
    sd_line : Line
        Standard-deviation reference line.
    decomposition : Decomposition
        Variance decomposition and lack-of-fit diagnostic.
    x, y : ndarray
        Observations retained after missing-value handling. When controls are
        present, these are the mean-shifted residualized variables used in estimation.
    weights : ndarray or None
        Reliability weights, or None for an unweighted estimate.
    x_name, y_name : str
        Display names for the exogenous and endogenous variables.
    controls : tuple of str
        Variables partialled out of ``x`` and ``y``. Empty for an unadjusted
        estimate.

    Attributes
    ----------
    n_obs : int
        Number of observations used in estimation.
    n_bins : int
        Number of nonempty bins.
    verdict : str
        Descriptive interpretation of the lack-of-fit measure.
    table : pandas.DataFrame
        Per-bin estimates.
    decomposition_table : pandas.DataFrame
        Variance decomposition as a one-row table.
    """

    binning: Binning
    estimates: BinEstimates
    fit: LineFit
    sd_line: Line
    decomposition: Decomposition
    x: FloatArray
    y: FloatArray
    weights: FloatArray | None
    x_name: str
    y_name: str
    controls: tuple[str, ...] = ()

    # -- convenience accessors -------------------------------------------------

    @property
    def n_obs(self) -> int:
        return int(self.y.size)

    @property
    def n_bins(self) -> int:
        return self.binning.n_bins

    @property
    def verdict(self) -> str:
        return self.decomposition.verdict

    @property
    def adjusted(self) -> bool:
        """Whether the estimate is adjusted for control variables."""
        return bool(self.controls)

    @property
    def x_label(self) -> str:
        """Return the display label for the exogenous variable."""
        return f"{self.x_name} (adjusted)" if self.adjusted else self.x_name

    @property
    def y_label(self) -> str:
        """Return the display label for the endogenous variable."""
        return f"{self.y_name} (adjusted)" if self.adjusted else self.y_name

    @property
    def table(self) -> pd.DataFrame:
        """Return per-bin estimates as a DataFrame."""
        e = self.estimates
        edges = self.binning.edges
        return pd.DataFrame(
            {
                "bin": np.arange(self.n_bins, dtype=int),
                "n": e.n,
                "x_lo": edges[:-1],
                "x_hi": edges[1:],
                "x_mean": e.x_mean,
                "y_mean": e.y_mean,
                "y_sd": e.y_sd,
                "se": e.se,
                "ci_lo": e.ci_lo,
                "ci_hi": e.ci_hi,
            }
        )

    @property
    def decomposition_table(self) -> pd.DataFrame:
        """Return the variance decomposition as a one-row DataFrame."""
        return pd.DataFrame([self.decomposition.as_dict()])

    def summary_frame(self) -> pd.DataFrame:
        """Return model and diagnostic statistics as a one-row DataFrame."""
        d = self.decomposition
        return pd.DataFrame(
            [
                {
                    "x": self.x_name,
                    "y": self.y_name,
                    "controls": ", ".join(self.controls) or None,
                    "n_obs": self.n_obs,
                    "n_bins": self.n_bins,
                    "binning": self.binning.method,
                    "slope": self.fit.slope,
                    "slope_se": self.fit.se_slope,
                    "intercept": self.fit.intercept,
                    "correlation": self.fit.r,
                    "r_squared": d.r_sq_linear,
                    "eta_squared": d.eta_sq,
                    "lack_of_fit": d.gap,
                    "min_bin_n": d.min_bin_n,
                    "verdict": d.verdict,
                }
            ]
        )

    def to_dict(self) -> dict[str, Any]:
        """Return estimation results using JSON-compatible Python values."""
        return {
            "x": self.x_name,
            "y": self.y_name,
            "controls": list(self.controls),
            "n_obs": self.n_obs,
            "binning": {
                "method": self.binning.method,
                "requested_bins": self.binning.requested_bins,
                "n_bins": self.n_bins,
                "edges": [_json_value(value) for value in self.binning.edges],
            },
            "fit": {
                "slope": _json_value(self.fit.slope),
                "intercept": _json_value(self.fit.intercept),
                "slope_se": _json_value(self.fit.se_slope),
                "correlation": _json_value(self.fit.r),
                "r_squared": _json_value(self.fit.r_sq),
            },
            "sd_line": {
                "slope": _json_value(self.sd_line.slope),
                "intercept": _json_value(self.sd_line.intercept),
            },
            "decomposition": {
                key: _json_value(value)
                for key, value in self.decomposition.as_dict().items()
            },
            "bins": [
                {key: _json_value(value) for key, value in row.items()}
                for row in self.table.to_dict(orient="records")
            ],
        }

    def residuals_from_fit(self) -> FloatArray:
        """Return deviations of the bin means from the fitted linear model."""
        return self.estimates.y_mean - self.fit.predict(self.estimates.x_mean)

    # -- description -----------------------------------------------------------

    def summary(self) -> str:
        """Summarize the binned scatterplot results.

        Returns
        -------
        str
            Plain-text summary of the model, partition, and diagnostic measures.

        Notes
        -----
        ``Lack of fit`` is a descriptive measure and ``Verdict`` is a heuristic.
        Neither is a formal specification test.
        """
        d = self.decomposition
        f = self.fit
        width = 68
        rule = "=" * width
        thin = "-" * width
        lines = [
            rule,
            "Binscatter Results".center(width),
            rule,
            f"{'Dep. Variable:':<20}{self.y_name:>14}"
            f"{'No. Observations:':>22}{self.n_obs:>12,}",
            f"{'Exog:':<20}{self.x_name:>14}{'No. Bins:':>22}{self.n_bins:>12}",
            f"{'Binning:':<20}{self.binning.method:>14}"
            f"{'Min. Bin Size:':>22}{d.min_bin_n:>12,}",
            *(
                [f"{'Controls:':<20}{_controls_label(self.controls):>48}"]
                if self.controls
                else []
            ),
            thin,
            f"{'':<18}{'coef':>13}{'std err':>13}",
            thin,
            f"{'const':<18}{f.intercept:>13.6g}{'--':>13}",
            f"{self.x_name:<18}{f.slope:>13.6g}{f.se_slope:>13.6g}",
            thin,
            f"{'R-squared:':<20}{d.r_sq_linear:>14.4f}"
            f"{'Eta-squared:':>22}{d.eta_sq:>12.4f}",
            f"{'Lack of fit:':<20}{d.gap:>14.4f}"
            f"{'SD line slope:':>22}{self.sd_line.slope:>12.6g}",
            f"{'Correlation:':<20}{f.r:>14.4f}{'Verdict:':>22}{d.verdict:>12}",
            rule,
            "Notes:",
            *_summary_notes(d, width, self.controls),
            rule,
        ]
        return "\n".join(lines)

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return (
            f"<BinscatterResult {self.y_name}~{self.x_name} "
            f"n={self.n_obs:,} bins={self.n_bins} "
            f"slope={self.fit.slope:.4g} gap={self.decomposition.gap:.3f} "
            f"verdict={self.verdict!r}>"
        )

    # -- drawing ---------------------------------------------------------------

    def plot(
        self,
        ax: Axes | None = None,
        *,
        theme: str = "notebook",
        show: Sequence[str] | None = None,
        annotate: str | None = "minimal",
        **kwargs: Any,
    ) -> Axes:
        """Plot the binned scatterplot results.

        Parameters
        ----------
        ax : matplotlib.axes.Axes, optional
            Axes on which to draw. A new figure and axes are created if omitted.
        theme : {"notebook", "paper", "deck"}, default "notebook"
            Visual theme.
        show : sequence of str, optional
            Layers to draw. See :mod:`binspect.viz.layers` for available layers.
        annotate : {"minimal", "audit"} or None, default "minimal"
            Plot annotation level. Set to None to suppress annotations.
        **kwargs
            Additional keyword arguments passed to :func:`binspect.viz.figure.plot`.

        Returns
        -------
        matplotlib.axes.Axes
            Axes containing the plot.
        """
        from .viz.figure import plot as _plot

        return _plot(self, ax=ax, theme=theme, show=show, annotate=annotate, **kwargs)

    def audit(
        self,
        *,
        theme: str = "notebook",
        show: Sequence[str] | None = None,
        annotate: str | None = "audit",
        marginals: bool = True,
        residuals: bool = True,
        hist_bins: int = 30,
        **kwargs: Any,
    ) -> Figure:
        """Plot the estimate with marginal and residual diagnostics.

        Parameters
        ----------
        theme : {"notebook", "paper", "deck"}, default "notebook"
            Visual theme.
        show : sequence of str, optional
            Layers to draw in the central binned scatterplot.
        annotate : {"minimal", "audit"} or None, default "audit"
            Annotation level for the central plot.
        marginals : bool, default True
            If True, include marginal histograms for ``x`` and ``y``.
        residuals : bool, default True
            If True, include raw residuals against fitted values.
        hist_bins : int, default 30
            Number of bins in each marginal histogram.
        **kwargs
            Additional keyword arguments passed to :func:`binspect.viz.audit.audit`.

        Returns
        -------
        matplotlib.figure.Figure
            Figure containing the requested diagnostic panels.
        """
        from .viz.audit import audit as _audit

        return _audit(
            self,
            theme=theme,
            show=show,
            annotate=annotate,
            marginals=marginals,
            residuals=residuals,
            hist_bins=hist_bins,
            **kwargs,
        )


def _verdict_note(d: Decomposition) -> str:
    if d.verdict == "underpowered bins":
        return (
            f"The smallest bin has {d.min_bin_n} observations; sampling variation "
            "may dominate the lack-of-fit measure."
        )
    if d.verdict == "curvature":
        return (
            f"Bin-mean deviations account for {d.gap:.1%} of total variation, "
            "which may indicate a nonlinear conditional mean."
        )
    return "The bin means do not show substantial departure from the fitted line."


def _controls_label(controls: tuple[str, ...]) -> str:
    label = ", ".join(controls)
    return f"{label[:45]}..." if len(label) > 48 else label


def _summary_notes(
    d: Decomposition, width: int, controls: tuple[str, ...]
) -> list[str]:
    notes = [
        "Confidence intervals assume independent observations.",
        "Lack of fit is descriptive; the verdict is not a formal test.",
        _verdict_note(d),
    ]
    if controls:
        notes.append(
            "The displayed variables were residualized on the listed controls "
            "using Frisch-Waugh-Lovell projection."
        )
    lines: list[str] = []
    for index, note in enumerate(notes, start=1):
        prefix = f"[{index}] "
        lines.extend(
            wrap(
                note,
                width=width,
                initial_indent=prefix,
                subsequent_indent=" " * len(prefix),
            )
        )
    return lines


def _json_value(value: Any) -> Any:
    """Convert NumPy and nonfinite scalar values to JSON-compatible values."""
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not np.isfinite(value):
        return None
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)
