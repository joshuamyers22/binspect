"""Oracles and failure accounting for the development coverage harness."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest
from scipy.integrate import quad

SPEC = importlib.util.spec_from_file_location(
    "expanded_coverage",
    Path(__file__).resolve().parents[1] / "validation" / "expanded_coverage.py",
)
assert SPEC is not None and SPEC.loader is not None
protocol = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(protocol)


@pytest.mark.parametrize("quadratic", [False, True])
@pytest.mark.parametrize("bounds", [(-0.2, 0.2), (-0.7, 0.4), (0.0, 0.9)])
def test_population_target_matches_independent_quadrature(bounds, quadratic):
    lower, upper = bounds
    mean_function = (
        (lambda x: 2 + x + 2 * x**2) if quadratic else (lambda x: 2 + 1.5 * x)
    )
    integral, _ = quad(mean_function, lower, upper)
    assert protocol.population_mean(lower, upper, quadratic=quadratic) == pytest.approx(
        integral / (upper - lower), rel=1e-12, abs=1e-12
    )


def test_anchor_uses_original_interval_identity_and_right_side_at_zero():
    partition = np.array([-1, -0.5, 0, 0.5, 1])
    assert protocol.anchor_index(partition, np.array([0, 2, 3])) == 1
    with pytest.raises(ValueError, match="absent"):
        protocol.anchor_index(partition, np.array([0, 3]))
    with pytest.raises(ValueError, match="outside"):
        protocol.anchor_index(np.array([0.2, 0.5, 1]), np.array([0, 1]))


def test_undefined_intervals_are_misses_and_never_shrink_denominator():
    metric = protocol.Metric()
    metric.record(0, 2, 1)
    metric.record(0, 2, 3)
    metric.record(np.nan, np.nan, 1)
    report = metric.report(3, required=False)
    assert report["coverage"] == 1 / 3
    assert (report["hits"], report["valid"], report["failed"]) == (1, 2, 1)
    assert report["mean_width_valid"] == 2
    assert not protocol.gate([{"metrics": {"bin": report}}])
    json.dumps(report, allow_nan=False)


def test_coverage_deviations_block_required_cases_but_remain_diagnostics():
    metric = protocol.Metric()
    metric.record(0, 1, 2)
    diagnostic = metric.report(1, required=False)
    required = metric.report(1, required=True)
    assert not diagnostic["within_nominal_band"]
    assert protocol.gate([{"metrics": {"bin": diagnostic}}])
    assert not protocol.gate([{"metrics": {"bin": required}}])


def test_selection_failures_count_for_both_metrics_without_leaking_messages(
    monkeypatch,
):
    def fail(**kwargs):
        raise protocol.BinspectError("synthetic private message")

    monkeypatch.setattr(protocol.binspect, "binscatter", fail)
    report = protocol.simulate(protocol.SCENARIOS[3], 91000, repetitions=3)
    for metric in report["metrics"].values():
        assert metric["failed"] == 3
        assert metric["coverage"] == 0
        assert metric["errors"] == {"BinspectError": 3}
    assert "synthetic private message" not in json.dumps(report, allow_nan=False)


def test_unexpected_errors_abort_instead_of_becoming_diagnostics(monkeypatch):
    def fail(**kwargs):
        raise RuntimeError("unexpected implementation defect")

    monkeypatch.setattr(protocol.binspect, "binscatter", fail)
    with pytest.raises(RuntimeError, match="unexpected"):
        protocol.simulate(protocol.SCENARIOS[0], 91001, repetitions=1)
