"""Estimation internals.

Nothing in this subpackage may import matplotlib. The boundary is enforced by an
import-linter contract in CI, and it is what keeps the statistics testable without
a display.
"""

from __future__ import annotations

from .binning import Binning, compute_binning
from .decompose import Decomposition, decompose
from .estimate import BinEstimates, estimate_bins
from .lines import fit_ols, fit_sd_line
from .selection import select_n_bins

__all__ = [
    "BinEstimates",
    "Binning",
    "Decomposition",
    "compute_binning",
    "decompose",
    "estimate_bins",
    "fit_ols",
    "fit_sd_line",
    "select_n_bins",
]
