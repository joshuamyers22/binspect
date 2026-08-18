"""The object a ``binscatter()`` call returns.

Deliberately inert: it holds estimates and knows how to describe or draw itself, but
it does no estimation. ``plot()`` is a method here rather than the entry point,
which is what lets every statistic be tested without a figure ever being created.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd

from .core.binning import Binning
from .core.decompose import Decomposition
from .core.estimate import BinEstimates
from .types import FloatArray, Line, LineFit

if TYPE_CHECKING:  # pragma: no cover
    from matplotlib.axes import Axes

__all__ = ["BinscatterResult"]


@dataclass(frozen=True, slots=True)
class BinscatterResult:
    """Everything a binscatter knows about itself.

    Attributes
    ----------
    binning:
        Edges, assignment and bin count.
    estimates:
        Per-bin means, dispersion, standard errors and intervals.
    fit:
        The straight-line fit through the underlying observations.
    sd_line:
        The SD line, for the ``r``-shrinkage reference.
    decomposition:
        Between/within split, eta-squared, linear R-squared and the gap.
    x, y:
        The underlying data, retained so the raw layer and re-binning stay possible.
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
    def table(self) -> pd.DataFrame:
        """Per-bin estimates as a tidy frame, one row per bin."""
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
        """The variance decomposition as a one-row frame."""
        return pd.DataFrame([self.decomposition.as_dict()])

    def residuals_from_fit(self) -> FloatArray:
        """Bin-mean deviations from the fitted line --- what the shading draws."""
        return self.estimates.y_mean - self.fit.predict(self.estimates.x_mean)

    # -- description -----------------------------------------------------------

    def summary(self) -> str:
        """A text block in the spirit of a regression summary."""
        d = self.decomposition
        f = self.fit
        width = 68
        rule = "=" * width
        thin = "-" * width
        lines = [
            rule,
            f"binscatter: {self.y_name} on {self.x_name}".center(width),
            rule,
            f"{'Observations:':<24}{self.n_obs:>12,}{'Bins:':>20}{self.n_bins:>12}",
            f"{'Binning:':<24}{self.binning.method:>12}"
            f"{'Smallest bin:':>20}{d.min_bin_n:>12,}",
            thin,
            f"{'Slope (OLS):':<24}{f.slope:>12.6g}"
            f"{'Std. error:':>20}{f.se_slope:>12.6g}",
            f"{'Intercept:':<24}{f.intercept:>12.6g}{'Correlation r:':>20}{f.r:>12.4f}",
            f"{'SD line slope:':<24}{self.sd_line.slope:>12.6g}"
            f"{'Shrinkage (r):':>20}{f.r:>12.4f}",
            thin,
            f"{'R-squared (linear):':<24}{d.r_sq_linear:>12.4f}"
            f"{'Eta-squared (bins):':>20}{d.eta_sq:>12.4f}",
            f"{'Lack of fit:':<24}{d.gap:>12.4f}{'Verdict:':>20}{d.verdict:>12}",
            rule,
            _verdict_note(d),
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
        """Draw the binscatter. Imported lazily so ``core`` stays display-free."""
        from .viz.figure import plot as _plot

        return _plot(self, ax=ax, theme=theme, show=show, annotate=annotate, **kwargs)


def _verdict_note(d: Decomposition) -> str:
    if d.verdict == "underpowered bins":
        return (
            f"Smallest bin has {d.min_bin_n} observations. Eta-squared is inflated by\n"
            "sampling noise at this bin size; do not read the gap as curvature."
        )
    if d.verdict == "curvature":
        return (
            f"Bin means depart from the fitted line by {d.gap:.1%} of total variance.\n"
            "The linear slope is a variance-weighted average of local slopes."
        )
    return (
        "Bin means track the fitted line. The linear specification is not\n"
        "discarding visible structure in the conditional mean."
    )
