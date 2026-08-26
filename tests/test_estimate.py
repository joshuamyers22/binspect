"""The foundational test: bin means ARE the saturated dummy regression.

If this fails, nothing downstream means what the documentation says it means.
"""

from __future__ import annotations

import numpy as np
import pytest

from binspect.core.binning import compute_binning
from binspect.core.estimate import estimate_bins
from conftest import saturated_fitted_values


def test_bin_means_equal_saturated_ols_coefficients(linear):
    x, y = linear["x"].to_numpy(), linear["y"].to_numpy()
    b = compute_binning(x, 20)
    e = estimate_bins(x, y, b.assignment, b.n_bins)

    expected = saturated_fitted_values(y, b.assignment, b.n_bins)
    np.testing.assert_allclose(e.y_mean, expected, rtol=0, atol=1e-10)


def test_bin_means_equal_saturated_ols_on_a_curved_dgp(concave):
    x, y = concave["x"].to_numpy(), concave["y"].to_numpy()
    b = compute_binning(x, 25)
    e = estimate_bins(x, y, b.assignment, b.n_bins)

    expected = saturated_fitted_values(y, b.assignment, b.n_bins)
    np.testing.assert_allclose(e.y_mean, expected, rtol=0, atol=1e-10)


def test_within_bin_sd_matches_pandas(linear):
    x, y = linear["x"].to_numpy(), linear["y"].to_numpy()
    b = compute_binning(x, 12)
    e = estimate_bins(x, y, b.assignment, b.n_bins)

    import pandas as pd

    expected = pd.Series(y).groupby(b.assignment).std(ddof=1).to_numpy()
    np.testing.assert_allclose(e.y_sd, expected, rtol=1e-12)


def test_equal_weights_reproduce_the_unweighted_result(linear):
    x, y = linear["x"].to_numpy(), linear["y"].to_numpy()
    b = compute_binning(x, 15)
    plain = estimate_bins(x, y, b.assignment, b.n_bins)
    weighted = estimate_bins(x, y, b.assignment, b.n_bins, weights=np.full(y.size, 2.5))
    np.testing.assert_allclose(plain.y_mean, weighted.y_mean, rtol=1e-12)
    np.testing.assert_allclose(plain.y_sd, weighted.y_sd, rtol=1e-10)
    np.testing.assert_allclose(plain.se, weighted.se, rtol=1e-10)


def test_standard_error_is_sd_over_root_n(linear):
    x, y = linear["x"].to_numpy(), linear["y"].to_numpy()
    b = compute_binning(x, 10)
    e = estimate_bins(x, y, b.assignment, b.n_bins)
    np.testing.assert_allclose(e.se, e.y_sd / np.sqrt(e.n), rtol=1e-12)


def test_clustered_bin_standard_errors_match_score_formula(linear):
    x, y = linear["x"].to_numpy(), linear["y"].to_numpy()
    clusters = np.arange(y.size) // 8
    b = compute_binning(x, 10)
    e = estimate_bins(x, y, b.assignment, b.n_bins, clusters=clusters)

    expected = []
    expected_counts = []
    for bin_index in range(b.n_bins):
        selected = b.assignment == bin_index
        labels = np.unique(clusters[selected])
        scores = np.array(
            [
                np.sum(y[selected & (clusters == label)] - e.y_mean[bin_index])
                for label in labels
            ]
        )
        count = labels.size
        expected_counts.append(count)
        expected.append(
            np.sqrt((count / (count - 1.0)) * np.sum(scores**2) / selected.sum() ** 2)
        )

    np.testing.assert_allclose(e.se, expected, rtol=1e-12)
    np.testing.assert_array_equal(e.n_clusters, expected_counts)
    assert e.se_type == "cluster"


def test_clustered_bin_with_one_cluster_has_undefined_interval():
    x = np.arange(8.0)
    y = x + np.array([0.0, 1.0, -1.0, 0.0, 0.5, -0.5, 1.0, -1.0])
    assignment = np.repeat([0, 1], 4)
    clusters = np.array(["a"] * 4 + ["b", "c", "b", "c"])
    result = estimate_bins(x, y, assignment, 2, clusters=clusters)
    assert np.isnan(result.se[0]) and np.isnan(result.ci_lo[0])
    assert np.isfinite(result.se[1])


def test_confidence_interval_brackets_the_mean(linear):
    x, y = linear["x"].to_numpy(), linear["y"].to_numpy()
    b = compute_binning(x, 10)
    e = estimate_bins(x, y, b.assignment, b.n_bins, ci=0.95)
    assert np.all(e.ci_lo < e.y_mean)
    assert np.all(e.y_mean < e.ci_hi)


def test_wider_level_gives_wider_intervals(linear):
    x, y = linear["x"].to_numpy(), linear["y"].to_numpy()
    b = compute_binning(x, 10)
    narrow = estimate_bins(x, y, b.assignment, b.n_bins, ci=0.80)
    wide = estimate_bins(x, y, b.assignment, b.n_bins, ci=0.99)
    assert np.all((wide.ci_hi - wide.ci_lo) > (narrow.ci_hi - narrow.ci_lo))


def test_ci_none_skips_intervals(linear):
    x, y = linear["x"].to_numpy(), linear["y"].to_numpy()
    b = compute_binning(x, 10)
    e = estimate_bins(x, y, b.assignment, b.n_bins, ci=None)
    assert e.ci_level is None
    assert np.all(np.isnan(e.ci_lo))


def test_bin_sds_rise_with_x_under_heteroskedasticity(heteroskedastic):
    x, y = heteroskedastic["x"].to_numpy(), heteroskedastic["y"].to_numpy()
    b = compute_binning(x, 10)
    e = estimate_bins(x, y, b.assignment, b.n_bins)
    # Not strictly monotone in a finite sample, but the trend must be unmistakable.
    assert e.y_sd[-1] > 2.0 * e.y_sd[0]
    assert np.corrcoef(e.x_mean, e.y_sd)[0, 1] > 0.9


def test_negative_weights_are_refused(linear):
    x, y = linear["x"].to_numpy(), linear["y"].to_numpy()
    b = compute_binning(x, 5)
    w = np.ones_like(y)
    w[0] = -1.0
    with pytest.raises(ValueError, match="non-negative"):
        estimate_bins(x, y, b.assignment, b.n_bins, weights=w)


def test_invalid_ci_level_is_refused(linear):
    x, y = linear["x"].to_numpy(), linear["y"].to_numpy()
    b = compute_binning(x, 5)
    with pytest.raises(ValueError, match="strictly between"):
        estimate_bins(x, y, b.assignment, b.n_bins, ci=1.5)
