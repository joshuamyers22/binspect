"""The caption block.

Three levels, and the default is the quiet one. A package that stamps "curvature" on
someone's figure by default reads as presumptuous --- and the diagnostics that matter
are already drawn as shading and bar length, so the text is a convenience, not the
delivery mechanism.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..result_summary import plot_caption as caption_text
from .theme import Theme, get_theme

if TYPE_CHECKING:  # pragma: no cover
    from matplotlib.axes import Axes

    from ..results import BinscatterResult

__all__ = ["annotate_layer", "caption_text"]

_CORNERS = {
    "upper left": (0.025, 0.975, "left", "top"),
    "upper right": (0.975, 0.975, "right", "top"),
    "lower left": (0.025, 0.025, "left", "bottom"),
    "lower right": (0.975, 0.025, "right", "bottom"),
}


def annotate_layer(
    ax: Axes,
    result: BinscatterResult,
    *,
    theme: str | Theme = "notebook",
    level: str = "minimal",
    loc: str = "upper left",
    **kwargs: Any,
) -> Axes:
    """Draw the caption block in a corner of the axes.

    Placement is not automatic: ``"upper left"`` suits the usual upward-sloping fit,
    and callers with a downward slope should pass ``loc="upper right"``. Guessing
    from the slope sign was tried and is wrong often enough to be worse than a
    documented default.
    """
    th = get_theme(theme)
    text = caption_text(result, level)

    if loc not in _CORNERS:
        raise ValueError(f"loc must be one of {sorted(_CORNERS)}, got {loc!r}.")
    x, y, ha, va = _CORNERS[loc]

    bbox = None
    if th.annotate_alpha > 0:
        bbox = {
            "boxstyle": "round,pad=0.45",
            "facecolor": th.palette.neutral,
            "edgecolor": "none",
            "alpha": th.annotate_alpha,
        }

    opts: dict[str, Any] = {
        "transform": ax.transAxes,
        "ha": ha,
        "va": va,
        "color": th.palette.text,
        "linespacing": 1.5,
        "zorder": 6,
        "bbox": bbox,
    }
    opts.update(kwargs)
    ax.text(x, y, text, **opts)
    return ax
