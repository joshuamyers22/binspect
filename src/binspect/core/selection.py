"""Choosing how many bins to use.

The IMSE-optimal ``"dpi"`` selector belongs to ``binsreg`` (Cattaneo, Crump, Farrell
and Feng); we delegate to it when it is installed rather than reimplement it. The
rules here are the pragmatic defaults for the exploratory path.
"""

from __future__ import annotations

import numpy as np

from ..exceptions import InvalidBinningError
from ..types import FloatArray

__all__ = ["DEFAULT_MAX_BINS", "DEFAULT_MIN_BINS", "select_n_bins"]

DEFAULT_MIN_BINS = 5
DEFAULT_MAX_BINS = 40

#: Target observations per bin for the ``"auto"`` rule. Below roughly this many, a
#: bin mean carries enough sampling error to bend the visible curve on its own.
TARGET_PER_BIN = 100


def _clip(n_bins: int, n_obs: int) -> int:
    ceiling = max(DEFAULT_MIN_BINS, min(DEFAULT_MAX_BINS, n_obs // 2))
    return int(np.clip(n_bins, DEFAULT_MIN_BINS, ceiling))


def select_n_bins(
    x: FloatArray,
    rule: int | str = "auto",
    *,
    y: FloatArray | None = None,
) -> int:
    """Resolve a bin-count request to a concrete integer.

    Parameters
    ----------
    x:
        The binning variable.
    rule:
        An explicit integer, or one of ``"auto"``, ``"sturges"``, ``"iqr"``,
        ``"dpi"``.
    y:
        Outcome variable, required only by ``"dpi"``.

    Returns
    -------
    int
        A bin count, clipped to a sane range for the sample size.
    """
    x = np.asarray(x, dtype=float)
    n_obs = int(x.size)

    if isinstance(rule, (int, np.integer)):
        if rule < 2:
            raise InvalidBinningError(f"bins must be at least 2, got {int(rule)}.")
        return int(rule)

    if rule == "auto":
        return _clip(int(np.ceil(n_obs / TARGET_PER_BIN)), n_obs)

    if rule == "sturges":
        return _clip(int(np.ceil(np.log2(max(n_obs, 2)) + 1)), n_obs)

    if rule == "iqr":
        # Freedman-Diaconis width, converted to a bin count over the observed range.
        q75, q25 = np.percentile(x, [75, 25])
        iqr = float(q75 - q25)
        span = float(np.max(x) - np.min(x))
        if iqr <= 0 or span <= 0:
            return _clip(DEFAULT_MIN_BINS, n_obs)
        width = 2.0 * iqr / np.cbrt(n_obs)
        return _clip(int(np.ceil(span / width)), n_obs)

    if rule == "dpi":
        return _select_dpi(x, y)

    raise InvalidBinningError(
        f"unknown bin rule {rule!r}; expected an int or one of "
        "'auto', 'sturges', 'iqr', 'dpi'."
    )


def _select_dpi(x: FloatArray, y: FloatArray | None) -> int:
    """Delegate IMSE-optimal selection to binsreg, if it is installed."""
    if y is None:
        raise InvalidBinningError("bins='dpi' needs y as well as x.")
    try:
        import binsreg
    except ImportError as exc:  # pragma: no cover - depends on the environment
        raise InvalidBinningError(
            "bins='dpi' requires the optional binsreg dependency: "
            "pip install 'binspect[dpi]'."
        ) from exc

    import pandas as pd  # local import: only needed on this path

    out = binsreg.binsregselect(  # pragma: no cover - exercised in external tests
        y=pd.Series(np.asarray(y, dtype=float)),
        x=pd.Series(np.asarray(x, dtype=float)),
    )
    return int(out.nbinsrot_regul)
