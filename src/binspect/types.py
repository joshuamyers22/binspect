"""Shared types and small immutable containers.

Nothing in here imports matplotlib. Nothing in here computes a statistic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias

import numpy as np
from numpy.typing import NDArray

__all__ = [
    "AnnotateLevel",
    "BinRule",
    "BinningMethod",
    "FloatArray",
    "IntArray",
    "Layer",
    "Line",
    "LineFit",
    "Verdict",
]

FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]

BinningMethod = Literal["quantile", "equal_width", "custom"]
BinRule: TypeAlias = (
    int | Literal["auto", "sturges", "iqr", "dpi"] | NDArray[np.float64]
)

Layer = Literal["raw", "deviation", "rug", "fit", "sd_line", "ci", "bins", "smooth"]
AnnotateLevel = Literal["minimal", "audit"]
Verdict = Literal["linear", "curvature", "underpowered bins"]


@dataclass(frozen=True, slots=True)
class Line:
    """A straight line in the (x, y) plane, parameterised by slope and intercept."""

    slope: float
    intercept: float

    def predict(self, x: FloatArray | float) -> FloatArray | float:
        """Evaluate the line at ``x``."""
        return self.intercept + self.slope * np.asarray(x, dtype=float)


@dataclass(frozen=True, slots=True)
class LineFit(Line):
    """An estimated regression line, with the fit diagnostics that come with it."""

    se_slope: float
    r: float
    r_sq: float
    n_obs: int
