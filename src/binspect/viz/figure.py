"""Composition.

The contract, tested rather than described: pass an axes, get *that* axes back. A
figure is created only when none is supplied. This is what lets a binscatter drop
into somebody's existing multi-panel layout instead of hijacking it.
"""

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
    """Draw a binscatter.

    Parameters
    ----------
    result:
        A :class:`~binspect.results.BinscatterResult`.
    ax:
        Existing axes to draw on. When ``None``, a themed figure is created.
    theme:
        ``"notebook"``, ``"paper"``, ``"deck"``, or a :class:`Theme`.
    show:
        Layer names to draw. Defaults to ``DEFAULT_LAYERS``. Order is ignored ---
        layers always draw in ``LAYER_ORDER``.
    annotate:
        ``None``, ``"minimal"`` (default) or ``"audit"``.
    legend:
        Draw a legend. Off by default; with three layers it costs more space than it
        explains.
    title:
        Axes title. ``None`` leaves it unset.
    layer_kwargs:
        Per-layer keyword overrides, e.g. ``{"bins": {"size_by_n": True}}``.

    Returns
    -------
    Axes
        The axes that was drawn on --- the same object passed in, when one was.
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

        ax.set_xlabel(result.x_name)
        ax.set_ylabel(result.y_name)
        if title is not None:
            ax.set_title(title)
        if legend:
            ax.legend(loc="best")
        if owns_figure:
            fig = ax.get_figure()
            if isinstance(fig, Figure):
                fig.set_size_inches(*th.rc.get("figure.figsize", (7.2, 4.6)))

    return ax
