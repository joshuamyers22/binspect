"""Colour choices.

One accent hue carries the estimate; everything contextual is neutral. Two rules
this obeys: the accent must survive conversion to greyscale as a distinctly darker
value than the neutrals, and no information is ever carried by hue alone --- the SD
line is dashed, the fit is solid, so the plot still reads in monochrome.

Accents are drawn from Okabe-Ito, which is colourblind-safe by construction.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["PALETTES", "Palette", "get_palette"]


@dataclass(frozen=True, slots=True)
class Palette:
    """The colours a single theme uses."""

    accent: str  # bin means, CI bars, the fitted line
    neutral: str  # SD line, rug, axis furniture
    deviation: str  # shading between bin means and the fit
    text: str
    raw: str  # underlying scatter, when shown


PALETTES: dict[str, Palette] = {
    # Okabe-Ito blue on warm grey. Reads on white and on the usual notebook greys.
    "notebook": Palette(
        accent="#0072B2",
        neutral="#6E6E6E",
        deviation="#0072B2",
        text="#2B2B2B",
        raw="#9A9A9A",
    ),
    # Near-black accent: prints cleanly, survives a photocopier, no colour budget.
    "paper": Palette(
        accent="#1A1A1A",
        neutral="#8A8A8A",
        deviation="#4A4A4A",
        text="#1A1A1A",
        raw="#B5B5B5",
    ),
    # Okabe-Ito vermillion: high chroma, legible from the back of a room.
    "deck": Palette(
        accent="#D55E00",
        neutral="#7A7A7A",
        deviation="#D55E00",
        text="#1A1A1A",
        raw="#BFBFBF",
    ),
}


def get_palette(name: str) -> Palette:
    """Look up a palette by theme name."""
    try:
        return PALETTES[name]
    except KeyError:
        raise KeyError(
            f"unknown palette {name!r}; available: {sorted(PALETTES)}"
        ) from None
