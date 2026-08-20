"""Binned scatterplot composition functions."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from matplotlib.figure import Figure

from . import layers as _layers
from .annotate import annotate_layer
from .theme import Theme, get_theme
from .theme import theme as theme_context

if TYPE_CHECKING:  # pragma: no cover
    from matplotlib.axes import Axes

    from ..results import BinscatterResult

__all__ = ["DEFAULT_LAYERS", "LAYER_ORDER", "plot"]

#: Draw order: context underneath, estimates on top. Not caller-configurable ---
#: reordering these produces a misleading plot, not a stylistic variant.
LAYER_ORDER: tuple[str, ...] = (
    "raw",
    "deviation",
    "rug",
    "fit",
    "sd_line",
    "smooth",
    "ci",
    "bins",
)

DEFAULT_LAYERS: tuple[str, ...] = ("deviation", "rug", "fit", "ci", "bins")

_DISPATCH = {
    "raw": _layers.raw_layer,
    "deviation": _layers.deviation_layer,
    "rug": _layers.rug_layer,
    "fit": _layers.fit_layer,
    "sd_line": _layers.sd_line_layer,
    "smooth": _layers.smooth_layer,
    "ci": _layers.ci_layer,
    "bins": _layers.bins_layer,
}


def plot(
    result: BinscatterResult,
    ax: Axes | None = None,
    *,
    theme: str | Theme = "notebook",
    show: Sequence[str] | None = None,
    annotate: str | None = "minimal",
    legend: bool = False,
    title: str | None = None,
    layer_kwargs: dict[str, dict[str, Any]] | None = None,
) -> Axes:
    """Plot binned scatterplot results.

    Parameters
    ----------
    result : BinscatterResult
        Estimation results.
    ax : matplotlib.axes.Axes, optional
        Axes on which to draw. A new figure and axes are created if omitted.
    theme : {"notebook", "paper", "deck"} or Theme, default "notebook"
        Visual theme.
    show : sequence of str, optional
        Layer names to draw. Defaults to ``DEFAULT_LAYERS``. Order is ignored;
        layers always draw in ``LAYER_ORDER``.
    annotate : {"minimal", "audit"} or None, default "minimal"
        Plot annotation level. Set to None to omit annotations.
    legend : bool, default False
        If True, draw a legend.
    title : str, optional
        Axes title.
    layer_kwargs : dict, optional
        Keyword arguments by layer, for example
        ``{"bins": {"size_by_n": True}}``.

    Returns
    -------
    Axes
        Axes containing the plot. If ``ax`` is provided, the same object is returned.
    """
    import matplotlib.pyplot as plt

    th = get_theme(theme)
    requested = tuple(DEFAULT_LAYERS if show is None else show)

    unknown = set(requested) - set(_DISPATCH)
    if unknown:
        raise ValueError(
            f"unknown layer(s) {sorted(unknown)}; available: {sorted(_DISPATCH)}"
        )

    layer_kwargs = layer_kwargs or {}
    owns_figure = ax is None

    with theme_context(th):
        if ax is None:
            _, ax = plt.subplots()

        for name in LAYER_ORDER:
            if name in requested:
                _DISPATCH[name](ax, result, theme=th, **layer_kwargs.get(name, {}))

        if annotate is not None:
            annotate_layer(
                ax, result, theme=th, level=annotate, **layer_kwargs.get("annotate", {})
            )

        ax.set_xlabel(result.x_label)
        ax.set_ylabel(result.y_label)
        if title is not None:
            ax.set_title(title)
        if legend:
            ax.legend(loc="best")
        if owns_figure:
            fig = ax.get_figure()
            if isinstance(fig, Figure):
                fig.set_size_inches(*th.rc.get("figure.figsize", (7.2, 4.6)))

    return ax
