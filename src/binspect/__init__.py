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

from typing import TYPE_CHECKING, Any

from .api import binscatter
from .comparison import BinscatterCollection, compare
from .core.diagnostics import DiagnosticPolicy
from .exceptions import (
    AdjustedInferenceWarning,
    BinCountWarning,
    BinspectError,
    InsufficientDataError,
    InvalidBinningError,
)
from .results import BinscatterResult

if TYPE_CHECKING:
    from .viz.theme import THEMES, theme


def __getattr__(name: str) -> Any:
    """Load plotting exports only when requested, preserving plain import isolation."""
    if name in {"THEMES", "theme"}:
        from .viz.theme import THEMES, theme

        globals().update(THEMES=THEMES, theme=theme)
        return globals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | {"THEMES", "theme"})


__version__ = "0.1.1"

__all__ = [
    "THEMES",
    "AdjustedInferenceWarning",
    "BinCountWarning",
    "BinscatterCollection",
    "BinscatterResult",
    "BinspectError",
    "DiagnosticPolicy",
    "InsufficientDataError",
    "InvalidBinningError",
    "__version__",
    "binscatter",
    "compare",
    "theme",
]
