"""The audit arithmetic: the sum-of-squares identity and the eta-squared bound."""

from __future__ import annotations

import numpy as np
import pytest

from binspect.core.binning import compute_binning
from binspect.core.decompose import decompose
from binspect.core.lines import fit_ols


def _decompose(frame, n_bins=20):
    x, y = frame["x"].to_numpy(), frame["y"].to_numpy()
    b = compute_binning(x, n_bins)
    fit = fit_ols(x, y)
    return decompose(y, x, b.assignment, b.n_bins, fit, fit.r_sq)


def test_sum_of_squares_identity(linear, concave, heteroskedastic):
    for frame in (linear, concave, heteroskedastic):
        d = _decompose(frame)
        assert d.ss_between + d.ss_within == pytest.approx(d.ss_total, rel=1e-12)


def test_lack_of_fit_is_never_negative(linear, concave, negative, heteroskedastic):
    for frame in (linear, concave, negative, heteroskedastic):
        for n_bins in (3, 5, 10, 40, 100):
            assert _decompose(frame, n_bins=n_bins).gap >= 0.0


def test_eta_squared_does_not_bound_linear_r_squared(linear):
    """The bound people assume, and the reason `gap` is lack-of-fit instead.

    A coarse step function does not nest a straight line, so on a linear DGP it
    explains strictly less variance. If this test ever starts failing, someone has
    quietly redefined eta_sq --- not fixed a bug.
    """
    coarse = _decompose(linear, n_bins=3)
    assert coarse.eta_sq < coarse.r_sq_linear
    assert coarse.gap >= 0.0


def test_eta_squared_is_a_proportion(concave):
    d = _decompose(concave)
    assert 0.0 <= d.eta_sq <= 1.0


def test_linear_dgp_has_a_negligible_gap(linear):
    d = _decompose(linear)
    assert d.gap < 0.02
    assert d.verdict == "linear"


def test_curved_dgp_has_a_large_gap(concave):
    d = _decompose(concave)
    assert d.gap > 0.05
    assert d.verdict == "curvature"


def test_sparse_bins_dominate_the_verdict(concave):
    # 200 bins over 4,000 rows leaves 20 per bin: too few to call curvature.
    d = _decompose(concave, n_bins=200)
    assert d.min_bin_n < 30
    assert d.verdict == "underpowered bins"


def test_eta_squared_rises_mechanically_with_bin_count(linear):
    coarse = _decompose(linear, n_bins=5)
    fine = _decompose(linear, n_bins=200)
    # Same data, same underlying relationship: the increase is noise being fitted.
    assert fine.eta_sq > coarse.eta_sq


def test_gap_equals_weighted_squared_deviation_of_bin_means(concave):
    """gap is exactly the ink in the deviation layer, normalised by total variance."""
    x, y = concave["x"].to_numpy(), concave["y"].to_numpy()
    b = compute_binning(x, 20)
    fit = fit_ols(x, y)
    d = decompose(y, x, b.assignment, b.n_bins, fit, fit.r_sq)

    counts = np.bincount(b.assignment, minlength=b.n_bins).astype(float)
    x_mean = np.bincount(b.assignment, weights=x, minlength=b.n_bins) / counts
    y_mean = np.bincount(b.assignment, weights=y, minlength=b.n_bins) / counts
    expected = float(np.sum(counts * (y_mean - fit.predict(x_mean)) ** 2))

    assert d.ss_lof == pytest.approx(expected, rel=1e-12)
    assert d.gap == pytest.approx(expected / d.ss_total, rel=1e-12)


def test_saturated_binning_explains_everything():
    # One observation per bin: eta^2 must be exactly 1 and nothing is left within.
    y = np.arange(10.0)
    x = np.arange(10.0)
    fit = fit_ols(x, y)
    d = decompose(y, x, np.arange(10), 10, fit, fit.r_sq)
    assert d.eta_sq == pytest.approx(1.0)
    assert d.ss_within == pytest.approx(0.0)


def test_perfectly_linear_data_has_no_lack_of_fit():
    x = np.linspace(0.0, 10.0, 1_000)
    y = 3.0 + 2.0 * x
    b = compute_binning(x, 10)
    fit = fit_ols(x, y)
    d = decompose(y, x, b.assignment, b.n_bins, fit, fit.r_sq)
    assert d.gap == pytest.approx(0.0, abs=1e-20)
    assert d.verdict == "linear"


def test_single_bin_explains_nothing():
    x = np.array([1.0, 2.0, 3.0, 4.0])
    y = np.array([1.0, 2.0, 3.0, 4.0])
    fit = fit_ols(x, y)
    d = decompose(y, x, np.zeros(4, dtype=int), 1, fit, fit.r_sq)
    assert d.eta_sq == pytest.approx(0.0)
    assert d.ss_between == pytest.approx(0.0)


def test_equal_weights_reproduce_the_unweighted_decomposition(linear):
    x, y = linear["x"].to_numpy(), linear["y"].to_numpy()
    b = compute_binning(x, 15)
    fit = fit_ols(x, y)
    plain = decompose(y, x, b.assignment, b.n_bins, fit, fit.r_sq)
    weighted = decompose(
        y, x, b.assignment, b.n_bins, fit, fit.r_sq, weights=np.full(y.size, 4.0)
    )
    assert weighted.eta_sq == pytest.approx(plain.eta_sq, rel=1e-12)
