"""Everything that touches matplotlib.

Nothing in this subpackage computes a statistic; it consumes a
:class:`~binspect.results.BinscatterResult` and renders it.
"""

from __future__ import annotations

from .annotate import annotate_layer, caption_text
from .figure import DEFAULT_LAYERS, LAYER_ORDER, plot
from .layers import (
    bins_layer,
    ci_layer,
    deviation_layer,
    fit_layer,
    raw_layer,
    rug_layer,
    sd_line_layer,
    smooth_layer,
)
from .palette import PALETTES, Palette, get_palette
from .theme import THEMES, Theme, get_theme, theme

__all__ = [
    "DEFAULT_LAYERS",
    "LAYER_ORDER",
    "PALETTES",
    "THEMES",
    "Palette",
    "Theme",
    "annotate_layer",
    "bins_layer",
    "caption_text",
    "ci_layer",
    "deviation_layer",
    "fit_layer",
    "get_palette",
    "get_theme",
    "plot",
    "raw_layer",
    "rug_layer",
    "sd_line_layer",
    "smooth_layer",
    "theme",
]
