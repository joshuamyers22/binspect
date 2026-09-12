"""Descriptive decisions must use actual estimation support."""

from __future__ import annotations

import json

import numpy as np
import pytest

import binspect
from binspect.core.diagnostics import classify


def test_zero_weight_rows_do_not_supply_diagnostic_support():
    x = np.r_[np.linspace(-1, -0.1, 50), np.linspace(0.1, 1, 50)]
    w = np.tile(np.r_[np.ones(5), np.zeros(45)], 2)
    result = binspect.binscatter(x=x, y=x**2, weights=w, bins=[-1, 0, 1])
    assert result.decomposition.min_bin_n == 50
    assert result.verdict == "limited support"
    assert result.n_obs == 100
    assert result.n_positive == result.n_effective == 10
    np.testing.assert_allclose(result.table["n_positive"], 5)
    np.testing.assert_allclose(result.table["n_effective"], 5)
    assert result.decomposition.min_bin_positive_n == 5
    assert result.decomposition.min_bin_effective_n == 5


def test_concentrated_weights_do_not_supply_diagnostic_support():
    x = np.linspace(-1, 1, 100)
    w = np.ones(100)
    w[[0, 99]] = 1000
    result = binspect.binscatter(x=x, y=x**2, weights=w, bins=[-1, 0, 1])
    assert result.verdict == "limited support"


@pytest.mark.parametrize("weighted", [False, True])
def test_constant_outcome_is_not_evidence_for_linearity(weighted):
    y = np.ones(100)
    weights = np.tile([1.0, 0.0], 50) if weighted else None
    if weighted:
        y[1::2] = 100
    result = binspect.binscatter(x=np.arange(100.0), y=y, weights=weights, bins=2)
    assert result.decomposition.gap == result.decomposition.eta_sq == 0
    assert result.verdict == "not assessed"
    assert result.sd_line.slope == result.fit.slope == 0


@pytest.mark.parametrize(
    "gap,expected", [(0.019, "linear"), (0.02, "curvature"), (0.021, "curvature")]
)
def test_gap_boundary(gap, expected):
    policy = binspect.DiagnosticPolicy()
    assert classify(gap, 1, 30, None, policy)[0] == expected


@pytest.mark.parametrize(
    "support,expected",
    [(29.9, "limited support"), (30, "curvature"), (30.1, "curvature")],
)
def test_effective_support_boundary(support, expected):
    assert classify(0.03, 1, support, None, binspect.DiagnosticPolicy())[0] == expected


@pytest.mark.parametrize(
    "count,expected", [(2, "limited support"), (3, "curvature"), (4, "curvature")]
)
def test_explicit_cluster_policy_boundary(count, expected):
    policy = binspect.DiagnosticPolicy(min_bin_clusters=3)
    assert classify(0.03, 1, 30, count, policy)[0] == expected


@pytest.mark.parametrize(
    "kwargs",
    [
        {"gap_threshold": -1},
        {"gap_threshold": np.nan},
        {"gap_threshold": np.inf},
        {"gap_threshold": True},
        {"gap_threshold": "0.02"},
        {"min_bin_effective_n": 0},
        {"min_bin_effective_n": False},
        {"min_bin_clusters": 1},
        {"min_bin_clusters": 2.5},
        {"min_bin_clusters": True},
    ],
)
def test_invalid_policy_is_rejected(kwargs):
    with pytest.raises(ValueError):
        binspect.DiagnosticPolicy(**kwargs)


@pytest.mark.parametrize("scale", [1e-9, 1.0, 1e9])
def test_weight_rescaling_preserves_support_and_policy(scale):
    x = np.linspace(-1, 1, 100)
    result = binspect.binscatter(
        x=x,
        y=x * x,
        weights=np.full(100, scale),
        bins=2,
        diagnostic_policy=binspect.DiagnosticPolicy(min_bin_effective_n=50),
    )
    assert result.decomposition.min_bin_effective_n == 50
    assert result.verdict != "limited support"


def test_opt_out_preserves_estimates_and_group_policy_exports():
    x = np.linspace(-1, 1, 200)
    y = x * x + np.sin(10 * x)
    plain = binspect.binscatter(x=x, y=y, bins=3)
    disabled = binspect.binscatter(x=x, y=y, bins=3, diagnostic_policy=None)
    assert disabled.verdict == "not assessed"
    assert disabled.decomposition.verdict_reason == "disabled"
    assert disabled.fit == plain.fit
    assert disabled.decomposition.gap == plain.decomposition.gap
    np.testing.assert_allclose(disabled.table, plain.table)
    assert "classification is disabled" in disabled.summary()
    from binspect.result_summary import plot_caption

    assert "not assessed" in plot_caption(disabled, "audit")
    policy = binspect.DiagnosticPolicy(
        gap_threshold=0.1, min_bin_effective_n=20, min_bin_clusters=4
    )
    comparison = binspect.compare(
        x=x, y=y, group=np.tile([0, 1], 100), bins=3, diagnostic_policy=policy
    )
    for result in [comparison.pooled, *comparison.results.values()]:
        exported = result.to_dict()["decomposition"]
        assert exported["gap_threshold"] == 0.1
        assert exported["min_bin_effective_n_threshold"] == 20
        assert exported["min_bin_clusters_threshold"] == 4
        assert result.summary_frame()["gap_threshold"].iloc[0] == 0.1
    json.dumps(comparison.to_dict(), allow_nan=False)
    json.dumps(disabled.to_dict(), allow_nan=False)
    disabled_groups = binspect.compare(
        x=x, y=y, group=np.tile([0, 1], 100), bins=3, diagnostic_policy=None
    )
    assert all(
        result.decomposition.verdict_reason == "disabled"
        for result in [disabled_groups.pooled, *disabled_groups.results.values()]
    )


def test_cluster_support_ignores_zero_weight_only_labels():
    x = np.linspace(-1, 1, 200)
    weights = np.tile([1.0, 1.0, 0.0, 0.0], 50)
    clusters = np.tile([0, 1, 2, 3], 50)
    policy = binspect.DiagnosticPolicy(min_bin_effective_n=10, min_bin_clusters=3)
    result = binspect.binscatter(
        x=x,
        y=x * x,
        weights=weights,
        cluster=clusters,
        bins=2,
        diagnostic_policy=policy,
    )
    assert result.decomposition.min_bin_clusters == 2
    assert result.verdict == "limited support"
    assert result.decomposition.verdict_reason == "clusters below threshold"


def test_clusters_do_not_receive_an_implicit_reliability_threshold():
    x = np.linspace(-1, 1, 600)
    result = binspect.binscatter(x=x, y=x**2, cluster=np.tile([0, 1, 2], 200), bins=5)
    assert result.verdict == "not assessed"
