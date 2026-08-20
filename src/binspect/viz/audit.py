"""Composed diagnostic figures for binned scatterplot results."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from matplotlib.figure import Figure

from .theme import Theme, get_theme
from .theme import theme as theme_context

if TYPE_CHECKING:  # pragma: no cover
    from matplotlib.axes import Axes

    from ..results import BinscatterResult

__all__ = ["audit"]


def audit(
    result: BinscatterResult,
    *,
    theme: str | Theme = "notebook",
    show: Sequence[str] | None = None,
    annotate: str | None = "audit",
    marginals: bool = True,
    residuals: bool = True,
    hist_bins: int = 30,
    layer_kwargs: dict[str, dict[str, Any]] | None = None,
) -> Figure:
    """Plot a binned scatterplot with distribution and residual diagnostics.

    Parameters
    ----------
    result : BinscatterResult
        Estimation results.
    theme : {"notebook", "paper", "deck"} or Theme, default "notebook"
        Visual theme.
    show : sequence of str, optional
        Layers to draw in the central binned scatterplot.
    annotate : {"minimal", "audit"} or None, default "audit"
        Annotation level for the central plot. Set to None to omit annotations.
    marginals : bool, default True
        If True, include marginal histograms for the observed variables.
    residuals : bool, default True
        If True, include raw residuals against fitted values from the linear model.
    hist_bins : int, default 30
        Number of bins in each marginal histogram.
    layer_kwargs : dict, optional
        Keyword arguments by central-plot layer.

    Returns
    -------
    matplotlib.figure.Figure
        Figure containing the requested diagnostic panels.

    Notes
    -----
    The residual panel is descriptive. It uses the same fitted linear model stored
    on ``result`` and does not perform an additional specification test.
    """
    import matplotlib.pyplot as plt

    if isinstance(hist_bins, bool) or not isinstance(hist_bins, int) or hist_bins < 1:
        raise ValueError("hist_bins must be a positive integer")

    th = get_theme(theme)
    with theme_context(th):
        figure = plt.figure(
            figsize=_figure_size(th, marginals, residuals), layout="constrained"
        )
        axes = _make_axes(figure, marginals=marginals, residuals=residuals)

        from .figure import plot

        plot(
            result,
            ax=axes["main"],
            theme=th,
            show=show,
            annotate=annotate,
            layer_kwargs=layer_kwargs,
        )
        if marginals:
            _draw_marginals(
                axes["x_marginal"], axes["y_marginal"], result, th, hist_bins
            )
        if residuals:
            _draw_residuals(axes["residuals"], result, th)

    return figure


def _figure_size(theme: Theme, marginals: bool, residuals: bool) -> tuple[float, float]:
    width, height = theme.rc.get("figure.figsize", (7.2, 4.6))
    return (
        float(width) * (1.2 if marginals else 1.0),
        float(height) * (1.4 if residuals else 1.0),
    )


def _make_axes(figure: Figure, *, marginals: bool, residuals: bool) -> dict[str, Axes]:
    top_rows = 2 if marginals else 1
    rows = top_rows + int(residuals)
    columns = 2 if marginals else 1
    height_ratios = ([0.28, 1.0] if marginals else [1.0]) + (
        [0.55] if residuals else []
    )
    width_ratios = [1.0, 0.28] if marginals else [1.0]
    grid = figure.add_gridspec(
        rows,
        columns,
        height_ratios=height_ratios,
        width_ratios=width_ratios,
        hspace=0.14,
        wspace=0.12,
    )
    main_row = 1 if marginals else 0
    axes: dict[str, Axes] = {"main": figure.add_subplot(grid[main_row, 0])}

    if marginals:
        axes["x_marginal"] = figure.add_subplot(grid[0, 0], sharex=axes["main"])
        axes["y_marginal"] = figure.add_subplot(grid[main_row, 1], sharey=axes["main"])
    if residuals:
        axes["residuals"] = figure.add_subplot(grid[rows - 1, 0])
    return axes


def _draw_marginals(
    x_axis: Axes,
    y_axis: Axes,
    result: BinscatterResult,
    theme: Theme,
    hist_bins: int,
) -> None:
    label = "Weighted count" if result.weights is not None else "Count"
    x_axis.hist(
        result.x,
        bins=hist_bins,
        weights=result.weights,
        color=theme.palette.neutral,
        alpha=0.45,
        edgecolor="none",
    )
    y_axis.hist(
        result.y,
        bins=hist_bins,
        weights=result.weights,
        color=theme.palette.neutral,
        alpha=0.45,
        edgecolor="none",
        orientation="horizontal",
    )
    x_axis.set_ylabel(label)
    y_axis.set_xlabel(label)
    x_axis.tick_params(axis="x", labelbottom=False)
    y_axis.tick_params(axis="y", labelleft=False)


def _draw_residuals(axis: Axes, result: BinscatterResult, theme: Theme) -> None:
    fitted = result.fit.predict(result.x)
    residual = result.y - fitted
    axis.scatter(
        fitted,
        residual,
        s=theme.raw_size,
        alpha=theme.raw_alpha,
        color=theme.palette.raw,
        edgecolors="none",
        rasterized=result.n_obs > 2_000,
    )
    axis.axhline(0.0, color=theme.palette.neutral, linewidth=theme.sd_width)
    axis.set_xlabel("Fitted values")
    axis.set_ylabel("Residuals")
