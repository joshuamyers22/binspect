"""CR1 arithmetic and storage must depend on represented bin/cluster pairs."""

from __future__ import annotations

import numpy as np
import pytest
from scipy import stats

from binspect.core.estimate import estimate_bins


@pytest.mark.parametrize("pattern", ["crossed", "nested", "unique"])
@pytest.mark.parametrize("weighted", [False, True])
@pytest.mark.parametrize("shuffle", [False, True])
def test_cluster_scores_match_direct_reference(pattern, weighted, shuffle):
    rng = np.random.default_rng(130201)
    n, bins = 240, 8
    assignment = np.arange(n) % bins
    x, y = rng.normal(size=(2, n))
    codes = {
        "crossed": np.arange(n) % 17,
        "nested": assignment * 3 + np.arange(n) // 80,
        "unique": np.arange(n),
    }[pattern]
    # Mixed label types preserve the first-observed, nonsorting public contract.
    labels = np.array([str(c) if c % 2 else int(c) for c in codes], dtype=object)
    weights = rng.uniform(0.1, 2, n) if weighted else np.ones(n)
    if weighted:
        weights[::5] = 0
    if shuffle:
        order = rng.permutation(n)
        x, y, assignment, labels, weights = (
            array[order] for array in (x, y, assignment, labels, weights)
        )
    result = estimate_bins(x, y, assignment, bins, weights=weights, clusters=labels)
    expected_se, expected_clusters = [], []
    for index in range(bins):
        active = (assignment == index) & (weights > 0)
        center = np.average(y[active], weights=weights[active])
        scores = {}
        for label, weight, value in zip(
            labels[active], weights[active], y[active], strict=True
        ):
            scores[label] = scores.get(label, 0.0) + weight * (value - center)
        count = len(scores)
        expected_clusters.append(count)
        expected_se.append(
            np.sqrt(count / (count - 1) * sum(v**2 for v in scores.values()))
            / weights[active].sum()
        )
    np.testing.assert_array_equal(result.n_clusters, expected_clusters)
    np.testing.assert_allclose(result.se, expected_se, rtol=1e-12, atol=1e-12)
    degrees = np.array(expected_clusters) - 1
    np.testing.assert_array_equal(result.ci_df, degrees)
    np.testing.assert_allclose(
        result.ci_hi,
        result.y_mean + stats.t.ppf(0.975, degrees) * expected_se,
        rtol=1e-12,
        atol=1e-12,
    )


def test_zero_scores_still_count_clusters_but_zero_weight_labels_do_not():
    result = estimate_bins(
        np.arange(8.0),
        np.array([2, 2, 2, 9, 4, 4, 4, 9.0]),
        np.repeat([0, 1], 4),
        2,
        weights=np.array([1, 1, 1, 0, 1, 1, 1, 0.0]),
        clusters=np.array(["a", "b", "a", "zero", "c", "c", "c", "zero"]),
    )
    np.testing.assert_array_equal(result.n_clusters, [2, 1])
    assert result.se[0] == 0 and result.ci_lo[0] == 2
    assert np.isnan(result.se[1]) and np.isnan(result.ci_df[1])


def test_near_row_count_clusters_do_not_allocate_cartesian_product(monkeypatch):
    original = np.bincount
    n, bins = 10_000, 100

    def bounded(values, weights=None, minlength=0):
        # A bincount allocates through max(values), even without minlength.
        needed = max(minlength, int(np.max(values, initial=-1)) + 1)
        assert needed <= n, "attempted dense bin-by-cluster allocation"
        return original(values, weights=weights, minlength=minlength)

    monkeypatch.setattr(np, "bincount", bounded)
    x = np.arange(n, dtype=float)
    result = estimate_bins(
        x, np.sin(x), np.arange(n) % bins, bins, clusters=np.arange(n)
    )
    np.testing.assert_array_equal(result.n_clusters, np.full(bins, n // bins))
    np.testing.assert_allclose(result.se, result.y_sd / np.sqrt(result.n), rtol=1e-12)
