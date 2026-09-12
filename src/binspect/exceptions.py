"""Errors and warnings raised by binspect."""

from __future__ import annotations

__all__ = [
    "AdjustedInferenceWarning",
    "BinCountWarning",
    "BinspectError",
    "InsufficientDataError",
    "InvalidBinningError",
]


class BinspectError(Exception):
    """Base class for exceptions raised by binspect."""


class InsufficientDataError(BinspectError):
    """Exception raised when the data are insufficient for estimation."""


class InvalidBinningError(BinspectError):
    """Exception raised when a binning specification is invalid."""


class BinCountWarning(UserWarning):
    """Warning issued when a binning specification produces sparse or merged bins."""


class AdjustedInferenceWarning(UserWarning):
    """Requested adjusted-bin uncertainty is unavailable pending validation."""
