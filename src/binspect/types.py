"""Type definitions and linear-result containers."""

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
    "ZeroWeightPolicy",
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
ZeroWeightPolicy = Literal["retain", "drop"]


@dataclass(frozen=True, slots=True)
class Line:
    """Linear function represented by a slope and intercept.

    Parameters
    ----------
    slope : float
        Slope coefficient.
    intercept : float
        Constant term.
    """

    slope: float
    intercept: float

    def predict(self, x: FloatArray | float) -> FloatArray | float:
        """Return fitted values at ``x``.

        Parameters
        ----------
        x : array_like or float
            Values of the exogenous variable.

        Returns
        -------
        ndarray or float
            Fitted values.
        """
        return self.intercept + self.slope * np.asarray(x, dtype=float)


@dataclass(frozen=True, slots=True)
class LineFit(Line):
    """Results from fitting a linear model.

    Parameters
    ----------
    slope : float
        Slope coefficient.
    intercept : float
        Constant term.
    se_slope : float
        Standard error of the slope coefficient.
    r : float
        Correlation coefficient.
    r_sq : float
        Coefficient of determination.
    n_obs : int
        Number of observations.
    se_type : {"classical", "cluster"}
        Covariance estimator used for ``se_slope``.
    n_clusters : int or None
        Number of clusters used by cluster-robust inference.
    """

    se_slope: float
    r: float
    r_sq: float
    n_obs: int
    se_type: Literal["classical", "cluster"] = "classical"
    n_clusters: int | None = None
