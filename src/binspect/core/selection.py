"""Bin-count selection methods."""

from __future__ import annotations

import numpy as np

from ..exceptions import InvalidBinningError
from ..types import BinningMethod, FloatArray

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
    method: BinningMethod = "quantile",
) -> int:
    """Select the number of bins.

    Parameters
    ----------
    x : array_like
        Exogenous variable used for binning.
    rule : int or {"auto", "sturges", "iqr", "dpi"}, default "auto"
        An explicit integer, or one of ``"auto"``, ``"sturges"``, ``"iqr"``,
        ``"dpi"``.
    y : array_like, optional
        Endogenous variable. Required when ``rule="dpi"``.
    method : {"quantile", "equal_width"}, default "quantile"
        Partition spacing passed to DPI selection. Other rules are unchanged.

    Returns
    -------
    int
        Selected bin count.
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
        return _select_dpi(x, y, method)

    raise InvalidBinningError(
        f"unknown bin rule {rule!r}; expected an int or one of "
        "'auto', 'sturges', 'iqr', 'dpi'."
    )


def _select_dpi(x: FloatArray, y: FloatArray | None, method: BinningMethod) -> int:
    """Select the piecewise-constant DPI count before our own knot reduction."""
    if y is None:
        raise InvalidBinningError("bins='dpi' needs y as well as x.")
    if method not in ("quantile", "equal_width"):
        raise InvalidBinningError("DPI requires quantile or equal_width binning.")

    failure = (
        "DPI selection did not produce a usable bin count; choose an explicit "
        "integer or bins='auto', or check sample size and distinct x values. "
        "No ROT fallback was applied."
    )
    y = np.asarray(y, dtype=float)
    if (
        x.ndim != 1
        or y.shape != x.shape
        or x.size < 4
        or not np.isfinite(x).all()
        or not np.isfinite(y).all()
        or np.unique(x).size < 2
    ):
        raise InvalidBinningError(failure)
    try:
        import binsreg
    except ImportError as exc:
        raise InvalidBinningError(
            "bins='dpi' requires the optional binsreg dependency: "
            "pip install 'binspect-regression[dpi]'."
        ) from exc

    try:
        out = binsreg.binsregselect(
            y=y,
            x=x,
            bins=(0, 0),
            binsmethod="dpi",
            binspos="qs" if method == "quantile" else "es",
            masspoints="on",
            vce="HC1",
            randcut=None,
        )
    except (ValueError, ArithmeticError, np.linalg.LinAlgError) as exc:
        raise InvalidBinningError(failure) from exc

    count = getattr(out, "nbinsdpi", None)
    if isinstance(count, (bool, np.bool_)) or not isinstance(
        count, (int, float, np.integer, np.floating)
    ):
        raise InvalidBinningError(failure)
    # Check the upper bound before float conversion, including huge Python ints.
    if not 2 <= count <= x.size or not float(count).is_integer():
        raise InvalidBinningError(failure)
    return int(count)
