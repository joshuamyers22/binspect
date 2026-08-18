"""Themes.

Importing binspect must leave ``matplotlib.rcParams`` byte-identical --- a library
that restyles someone's whole notebook on import gets uninstalled. So themes are
applied through :func:`matplotlib.rc_context`, scoped to a single ``with`` block or
a single ``plot()`` call, and always restored, including when an exception unwinds.
That property is asserted in the test suite rather than promised here.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, cast

import matplotlib as mpl

from .palette import Palette, get_palette

__all__ = ["THEMES", "Theme", "get_theme", "theme"]


@dataclass(frozen=True, slots=True)
class Theme:
    """A named look: rcParams plus the geometry of each layer."""

    name: str
    palette: Palette
    rc: dict[str, Any] = field(default_factory=dict)

    marker_size: float = 34.0
    marker_edge: float = 0.0
    fit_width: float = 2.0
    sd_width: float = 1.4
    sd_dashes: tuple[float, float] = (6.0, 4.0)
    ci_width: float = 1.5
    ci_alpha: float = 0.55
    deviation_width: float = 7.0
    deviation_alpha: float = 0.28
    rug_alpha: float = 0.45
    rug_height: float = 0.022
    raw_alpha: float = 0.16
    raw_size: float = 5.0
    annotate_alpha: float = 0.06


_BASE_RC: dict[str, Any] = {
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linewidth": 0.6,
    "axes.axisbelow": True,
    "legend.frameon": False,
    "figure.autolayout": True,
}


THEMES: dict[str, Theme] = {
    "notebook": Theme(
        name="notebook",
        palette=get_palette("notebook"),
        rc={
            **_BASE_RC,
            "figure.figsize": (7.2, 4.6),
            "font.size": 10.0,
            "axes.labelsize": 11.0,
            "axes.titlesize": 12.0,
            "axes.edgecolor": "#6E6E6E",
            "grid.color": "#6E6E6E",
            "text.color": "#2B2B2B",
            "axes.labelcolor": "#2B2B2B",
            "xtick.color": "#6E6E6E",
            "ytick.color": "#6E6E6E",
        },
    ),
    "paper": Theme(
        name="paper",
        palette=get_palette("paper"),
        rc={
            **_BASE_RC,
            "figure.figsize": (5.5, 3.6),
            "font.size": 9.0,
            "font.family": "serif",
            "axes.labelsize": 9.5,
            "axes.titlesize": 10.0,
            "axes.edgecolor": "#1A1A1A",
            "axes.linewidth": 0.6,
            "grid.color": "#8A8A8A",
            "grid.alpha": 0.18,
            "savefig.format": "pdf",
            "savefig.bbox": "tight",
        },
        marker_size=26.0,
        fit_width=1.3,
        sd_width=1.0,
        ci_width=1.0,
        deviation_width=5.0,
        deviation_alpha=0.22,
        annotate_alpha=0.0,
    ),
    "deck": Theme(
        name="deck",
        palette=get_palette("deck"),
        rc={
            **_BASE_RC,
            "figure.figsize": (10.0, 6.0),
            "font.size": 15.0,
            "axes.labelsize": 17.0,
            "axes.titlesize": 20.0,
            "axes.linewidth": 1.4,
            "axes.edgecolor": "#7A7A7A",
            "grid.color": "#7A7A7A",
            "grid.alpha": 0.2,
            "xtick.major.size": 6.0,
            "ytick.major.size": 6.0,
        },
        marker_size=110.0,
        fit_width=3.4,
        sd_width=2.4,
        sd_dashes=(8.0, 5.0),
        ci_width=2.6,
        deviation_width=14.0,
        deviation_alpha=0.30,
        raw_size=9.0,
        annotate_alpha=0.08,
    ),
}


def get_theme(name: str | Theme) -> Theme:
    """Resolve a theme name (or pass a ``Theme`` straight through)."""
    if isinstance(name, Theme):
        return name
    try:
        return THEMES[name]
    except KeyError:
        raise KeyError(f"unknown theme {name!r}; available: {sorted(THEMES)}") from None


@contextmanager
def theme(name: str | Theme, **overrides: Any) -> Iterator[Theme]:
    """Apply a theme's rcParams for the duration of a block.

    Examples
    --------
    >>> import binspect
    >>> with binspect.theme("paper"):          # doctest: +SKIP
    ...     result.plot()

    Any extra keyword arguments are treated as rcParams overrides layered on top of
    the theme. Everything is restored on exit.
    """
    resolved = get_theme(name)
    rc = {**resolved.rc, **overrides}
    # Matplotlib's stubs enumerate every valid rcParam key. User-provided overrides
    # are intentionally dynamic and are validated by Matplotlib at runtime.
    with mpl.rc_context(cast(Any, rc)):
        yield resolved
