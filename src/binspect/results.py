"""Results classes for binned scatterplot estimation."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd

from .core.binning import Binning
from .core.decompose import Decomposition
from .core.estimate import BinEstimates
from .result_serialization import serialize_result
from .result_summary import summarize
from .types import FloatArray, Line, LineFit, ZeroWeightPolicy

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
    cluster : str or None
        Cluster variable display name, or None for independent-observation standard
        errors.
    zero_weight : {"retain", "drop"}
        Policy applied to zero-weight observations.

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
    cluster: str | None = None
    zero_weight: ZeroWeightPolicy = "retain"

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
        columns: dict[str, Any] = {
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
        if e.n_clusters is not None:
            columns["n_clusters"] = e.n_clusters
        return pd.DataFrame(columns)

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
                    "cluster": self.cluster,
                    "se_type": self.estimates.se_type,
                    "n_clusters": self.fit.n_clusters,
                    "zero_weight": self.zero_weight,
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
        return serialize_result(self)

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
        return summarize(self)

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
