"""Errors and warnings raised by binspect."""

from __future__ import annotations

__all__ = [
    "BinCountWarning",
    "BinspectError",
    "InsufficientDataError",
    "InvalidBinningError",
]


class BinspectError(Exception):
    """Base class for every error raised by binspect."""


class InsufficientDataError(BinspectError):
    """Raised when there are too few usable observations to bin at all."""


class InvalidBinningError(BinspectError):
    """Raised when a binning request cannot be satisfied (bad edges, bad rule)."""


class BinCountWarning(UserWarning):
    """Warned when the requested bin count is unwise for the data at hand.

    Emitted for sparse bins, more bins than distinct x values, or a bin count
    high enough that eta-squared is inflated by noise rather than signal.
    """
