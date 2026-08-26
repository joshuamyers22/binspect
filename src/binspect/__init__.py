"""Binned scatterplots for linear specification diagnostics.

``binspect`` estimates within-bin means and compares them with a linear fit to the
underlying observations. The bin means are the fitted values of the saturated model
``OLS(y ~ C(bin))``. Their weighted deviations from the line provide a descriptive
measure of linear lack of fit.

Quick start
-----------
>>> import numpy as np, binspect
>>> rng = np.random.default_rng(0)
>>> x = rng.normal(size=5_000)
>>> y = np.tanh(x) + rng.normal(scale=0.5, size=5_000)
>>> bs = binspect.binscatter(x=x, y=y, bins=20)
>>> print(bs.summary())                      # doctest: +SKIP
>>> bs.plot(theme="paper")                   # doctest: +SKIP
"""

from __future__ import annotations

from .api import binscatter
from .comparison import BinscatterCollection, compare
from .exceptions import (
    BinCountWarning,
    BinspectError,
    InsufficientDataError,
    InvalidBinningError,
)
from .results import BinscatterResult
from .viz.theme import THEMES, theme

__version__ = "0.1.0"

__all__ = [
    "THEMES",
    "BinCountWarning",
    "BinscatterCollection",
    "BinscatterResult",
    "BinspectError",
    "InsufficientDataError",
    "InvalidBinningError",
    "__version__",
    "binscatter",
    "compare",
    "theme",
]
