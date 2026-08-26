"""Binning methods and partition results.

Tie convention
--------------
An observation whose ``x`` falls exactly on an interior edge is assigned to the
*lower* bin. Bin ``j`` therefore covers the half-open interval ``(e[j], e[j + 1]]``,
with the leftmost bin closed on both ends. This makes quantile bins uneven when
``x`` is discrete, which is the honest outcome: the alternative silently splits
identical x values across different bins.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np

from ..exceptions import BinCountWarning, InsufficientDataError, InvalidBinningError
from ..types import BinningMethod, FloatArray, IntArray

__all__ = ["Binning", "compute_binning"]

#: Below this many observations in a bin, the bin mean is mostly noise.
SPARSE_BIN_THRESHOLD = 10


@dataclass(frozen=True, slots=True)
class Binning:
    """Results from partitioning an exogenous variable.

    Attributes
    ----------
    edges : ndarray
        Bin boundaries, length ``n_bins + 1``, strictly increasing.
    assignment : ndarray
        Integer bin index in ``[0, n_bins)`` for every observation, same order and
        length as the input ``x``.
    n_bins : int
        Number of bins actually produced, which may be fewer than requested when
        ``x`` has too few distinct values.
    method : {"quantile", "equal_width", "custom"}
        The partition rule that produced this binning.
    requested_bins : int
        What the caller asked for, retained so the result can explain a reduction.
    """

    edges: FloatArray
    assignment: IntArray
    n_bins: int
    method: BinningMethod
    requested_bins: int

    @property
    def was_reduced(self) -> bool:
        """Return whether fewer bins were produced than requested."""
        return self.n_bins < self.requested_bins

    def counts(self) -> IntArray:
        """Return the number of observations in each bin."""
        return np.bincount(self.assignment, minlength=self.n_bins).astype(np.int64)


def _assign(x: FloatArray, interior: FloatArray) -> IntArray:
    """Assign each x to a bin given interior edges, ties going to the lower bin.

    ``side="left"`` counts the interior edges strictly below each value, so a value
    sitting exactly on edge ``k`` lands in bin ``k`` --- the bin below it.
    """
    return np.searchsorted(interior, x, side="left").astype(np.int64)


def _quantile_edges(x: FloatArray, n_bins: int) -> FloatArray:
    probs = np.linspace(0.0, 1.0, n_bins + 1)
    edges = np.quantile(x, probs)
    edges[0] = float(np.min(x))
    edges[-1] = float(np.max(x))
    return edges.astype(np.float64, copy=False)


def _equal_width_edges(x: FloatArray, n_bins: int) -> FloatArray:
    return np.linspace(float(np.min(x)), float(np.max(x)), n_bins + 1, dtype=np.float64)


def compute_binning(
    x: FloatArray,
    n_bins: int | None = None,
    *,
    method: BinningMethod = "quantile",
    edges: FloatArray | None = None,
) -> Binning:
    """Partition an exogenous variable into bins.

    Parameters
    ----------
    x : array_like
        Finite, one-dimensional exogenous variable.
    n_bins : int, optional
        Requested number of bins. Ignored when ``edges`` is provided.
    method : {"quantile", "equal_width", "custom"}, default "quantile"
        ``"quantile"`` for equal-count bins, ``"equal_width"`` for equal-span bins,
        or ``"custom"`` when supplying ``edges`` directly.
    edges : array_like, optional
        Explicit, strictly increasing bin boundaries that cover ``x``. Required for
        custom binning.

    Returns
    -------
    Binning
        Partition results.

    Raises
    ------
    InsufficientDataError
        If fewer than two distinct x values are present.
    InvalidBinningError
        If the request is self-contradictory, or custom edges are not increasing.

    Warns
    -----
    BinCountWarning
        If bins had to be merged, or any bin holds fewer than ten observations.
    """
    x = np.asarray(x, dtype=float)
    if x.ndim != 1:
        raise InvalidBinningError(f"x must be one-dimensional, got shape {x.shape}.")
    if not np.all(np.isfinite(x)):
        raise InvalidBinningError("x contains non-finite values; drop them first.")

    n_distinct = int(np.unique(x).size)
    if n_distinct < 2:
        raise InsufficientDataError(
            f"x has {n_distinct} distinct value(s); at least 2 are needed to bin."
        )

    if method == "custom" or edges is not None:
        if edges is None:
            raise InvalidBinningError("method='custom' requires explicit edges.")
        all_edges = np.asarray(edges, dtype=float)
        if all_edges.ndim != 1 or all_edges.size < 2:
            raise InvalidBinningError("edges must be a 1-D array of length >= 2.")
        if not np.all(np.diff(all_edges) > 0):
            raise InvalidBinningError("edges must be strictly increasing.")
        if all_edges[0] > np.min(x) or all_edges[-1] < np.max(x):
            raise InvalidBinningError(
                "custom edges must cover the full range of x "
                f"[{float(np.min(x))}, {float(np.max(x))}]."
            )
        requested = int(all_edges.size - 1)
        method = "custom"
    else:
        if n_bins is None:
            raise InvalidBinningError("n_bins is required unless edges are supplied.")
        if n_bins < 2:
            raise InvalidBinningError(f"n_bins must be at least 2, got {n_bins}.")
        requested = int(n_bins)
        if method == "quantile":
            all_edges = _quantile_edges(x, requested)
        elif method == "equal_width":
            all_edges = _equal_width_edges(x, requested)
        else:  # pragma: no cover - guarded by the Literal type
            raise InvalidBinningError(f"unknown binning method {method!r}.")

    interior = np.unique(all_edges[1:-1])
    interior = interior[(interior > all_edges[0]) & (interior < all_edges[-1])]

    outer_edges = (
        (float(all_edges[0]), float(all_edges[-1]))
        if method == "custom"
        else (float(np.min(x)), float(np.max(x)))
    )
    partition_edges = np.concatenate(
        [[outer_edges[0]], interior, [outer_edges[1]]]
    ).astype(float)

    assignment = _assign(x, interior)
    n_bins_actual = int(interior.size + 1)

    # Drop bins that ended up empty (possible with discrete x or custom edges) and
    # renumber so assignments stay contiguous from zero.
    occupied = np.unique(assignment)
    if occupied.size < n_bins_actual:
        remap = np.full(n_bins_actual, -1, dtype=np.int64)
        remap[occupied] = np.arange(occupied.size, dtype=np.int64)
        assignment = remap[assignment]
        # Preserve one boundary before every occupied bin after the first. This
        # folds empty leading/trailing intervals into the nearest occupied bin and
        # spans empty interior intervals without changing any observation's group.
        interior = partition_edges[occupied[1:]].astype(float, copy=True)
        n_bins_actual = int(occupied.size)

    final_edges = np.concatenate([[outer_edges[0]], interior, [outer_edges[1]]]).astype(
        float
    )

    if n_bins_actual < requested:
        warnings.warn(
            f"requested {requested} bins but x supports only {n_bins_actual} "
            f"({n_distinct} distinct values); bins were merged.",
            BinCountWarning,
            stacklevel=2,
        )

    binning = Binning(
        edges=final_edges,
        assignment=assignment,
        n_bins=n_bins_actual,
        method=method,
        requested_bins=requested,
    )

    counts = binning.counts()
    if counts.min() < SPARSE_BIN_THRESHOLD:
        warnings.warn(
            f"smallest bin holds {int(counts.min())} observations "
            f"(< {SPARSE_BIN_THRESHOLD}); bin means and eta-squared will be noisy.",
            BinCountWarning,
            stacklevel=2,
        )

    return binning
