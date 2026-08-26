"""Binning is a partition, and the tie rule is the documented one."""

from __future__ import annotations

import numpy as np
import pytest

from binspect.core.binning import compute_binning
from binspect.exceptions import (
    BinCountWarning,
    InsufficientDataError,
    InvalidBinningError,
)


def test_assignment_is_a_partition(linear):
    b = compute_binning(linear["x"].to_numpy(), 20)
    assert b.assignment.shape == linear["x"].shape
    assert b.assignment.min() >= 0
    assert b.assignment.max() == b.n_bins - 1
    assert b.counts().sum() == len(linear)


def test_quantile_counts_differ_by_at_most_one(linear):
    b = compute_binning(linear["x"].to_numpy(), 20)
    counts = b.counts()
    assert counts.max() - counts.min() <= 1


def test_edges_are_increasing_and_span_the_data(linear):
    x = linear["x"].to_numpy()
    b = compute_binning(x, 15)
    assert np.all(np.diff(b.edges) > 0)
    assert b.edges[0] == pytest.approx(x.min())
    assert b.edges[-1] == pytest.approx(x.max())
    assert b.edges.size == b.n_bins + 1


def test_ties_go_to_the_lower_bin():
    # Edge at 2.0; the value 2.0 itself must land in the bin below it.
    x = np.array([1.0, 2.0, 3.0, 4.0])
    with pytest.warns(BinCountWarning):  # 2 observations per bin, expected here
        b = compute_binning(x, method="custom", edges=np.array([1.0, 2.0, 4.0]))
    assert b.assignment.tolist() == [0, 0, 1, 1]


def test_equal_width_bins_have_equal_spans(linear):
    b = compute_binning(linear["x"].to_numpy(), 10, method="equal_width")
    widths = np.diff(b.edges)
    assert np.allclose(widths, widths[0])


def test_permutation_invariance(linear):
    x = linear["x"].to_numpy()
    b1 = compute_binning(x, 12)
    order = np.random.default_rng(0).permutation(x.size)
    b2 = compute_binning(x[order], 12)
    assert np.allclose(b1.edges, b2.edges)
    assert np.array_equal(b1.assignment[order], b2.assignment)


def test_discrete_x_merges_bins_and_warns(discrete):
    with pytest.warns(BinCountWarning, match="merged"):
        b = compute_binning(discrete["x"].to_numpy(), 20)
    assert b.n_bins <= 7
    assert b.was_reduced


def test_sparse_bins_warn(tiny):
    with pytest.warns(BinCountWarning, match="observations"):
        compute_binning(tiny["x"].to_numpy(), 20)


def test_constant_x_is_refused():
    with pytest.raises(InsufficientDataError):
        compute_binning(np.ones(100), 5)


def test_non_finite_x_is_refused():
    x = np.array([1.0, 2.0, np.nan, 4.0])
    with pytest.raises(InvalidBinningError, match="non-finite"):
        compute_binning(x, 2)


def test_custom_edges_must_increase():
    with pytest.raises(InvalidBinningError, match="increasing"):
        compute_binning(
            np.arange(10.0), method="custom", edges=np.array([0.0, 5.0, 3.0])
        )


def test_custom_edges_are_preserved_and_must_cover_data():
    x = np.linspace(0.0, 1.0, 100)
    b = compute_binning(x, method="custom", edges=np.array([-1.0, 0.5, 2.0]))
    np.testing.assert_array_equal(b.edges, [-1.0, 0.5, 2.0])

    with pytest.raises(InvalidBinningError, match="cover"):
        compute_binning(x, method="custom", edges=np.array([0.1, 0.5, 1.0]))


@pytest.mark.parametrize(
    ("x", "edges", "expected_edges"),
    [
        ([1.5, 1.6, 2.5, 2.6], [0.0, 1.0, 2.0, 3.0], [0.0, 2.0, 3.0]),
        ([0.5, 0.6, 1.5, 1.6], [0.0, 1.0, 2.0, 3.0], [0.0, 1.0, 3.0]),
        ([0.5, 0.6, 2.5, 2.6], [0.0, 1.0, 2.0, 3.0], [0.0, 2.0, 3.0]),
        (
            [0.5, 0.6, 3.5, 3.6],
            [0.0, 1.0, 2.0, 3.0, 4.0],
            [0.0, 3.0, 4.0],
        ),
    ],
    ids=["leading", "trailing", "interior", "consecutive-interior"],
)
def test_custom_edges_rebuild_around_occupied_bins(x, edges, expected_edges):
    values = np.asarray(x)
    with pytest.warns(BinCountWarning) as warnings:
        result = compute_binning(values, method="custom", edges=np.asarray(edges))
    assert any("merged" in str(item.message) for item in warnings)
    np.testing.assert_array_equal(result.edges, expected_edges)
    assert result.edges.size == result.n_bins + 1
    expected_assignment = np.searchsorted(result.edges[1:-1], values, side="left")
    np.testing.assert_array_equal(result.assignment, expected_assignment)


def test_too_few_bins_is_refused(linear):
    with pytest.raises(InvalidBinningError, match="at least 2"):
        compute_binning(linear["x"].to_numpy(), 1)
