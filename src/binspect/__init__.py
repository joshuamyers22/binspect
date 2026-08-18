"""binspect --- binned scatterplots that audit the regression behind them.

Bin ``x``, average ``y`` within each bin, and you have the fitted values of the
saturated model ``OLS(y ~ C(bin))``. The weighted distance between those bin means
and a straight-line fit exposes structure the linear specification may be discarding.
binspect draws that lack of fit instead of leaving it implicit.

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
from .exceptions import (
    BinCountWarning,
    BinspectError,
    InsufficientDataError,
    InvalidBinningError,
)
from .results import BinscatterResult
from .viz.theme import THEMES, theme

__version__ = "0.1.0.dev0"

__all__ = [
    "THEMES",
    "BinCountWarning",
    "BinscatterResult",
    "BinspectError",
    "InsufficientDataError",
    "InvalidBinningError",
    "__version__",
    "binscatter",
    "theme",
]
