"""Independent target and failure-accounting checks for adapter coverage."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

SPEC = importlib.util.spec_from_file_location(
    "binsreg_coverage",
    Path(__file__).resolve().parents[1] / "validation" / "binsreg_coverage.py",
)
assert SPEC is not None and SPEC.loader is not None
protocol = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(protocol)


def test_function_target_at_nearest_interval_and_failures_remain_misses(monkeypatch):
    calls = 0

    def fit(**kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise protocol.BinspectError("private failure detail")
        # At x=.25 the target is 3.375; at x=-.25 it is 2.875. The first
        # equidistant interval is chosen, and this interval misses a bin-average
        # target. A broad interval on a more distant x cannot rescue the result.
        return SimpleNamespace(
            metadata={
                "inference_status": "limited_support",
                "issues": ["constant_interval_fallback"],
                "actual_bins": 3,
                "actual_intervals": [0, 0],
            },
            intervals=pd.DataFrame(
                {
                    "x": [0.25, -0.25, 0.9],
                    "ci_lo": [3.37, 0, 0],
                    "ci_hi": [3.38, 0.1, 100],
                }
            ),
        )

    monkeypatch.setattr(protocol.binspect, "binsreg", fit)
    report = protocol.simulate(protocol.SCENARIOS[2], 93002, repetitions=3)
    assert (report["hits"], report["valid"], report["failed"]) == (2, 2, 1)
    assert report["coverage"] == 2 / 3
    assert report["mean_width_valid"] == pytest.approx(0.01)
    assert report["errors"] == {"BinspectError": 1}
    assert report["issue_counts"] == {"constant_interval_fallback": 2}
    assert not protocol.gate([report])
    assert "private" not in json.dumps(report, allow_nan=False)


def test_cluster_failures_are_diagnostic_but_iid_and_invalid_runs_block():
    row = {"failed": 0, "required_coverage": False, "within_nominal_band": False}
    assert protocol.gate([row])
    assert not protocol.gate([row | {"required_coverage": True}])
    assert not protocol.gate([row | {"failed": 1}])
    assert not protocol.gate([])


def test_unexpected_programming_errors_abort(monkeypatch):
    def fail(**kwargs):
        raise RuntimeError("unexpected defect")

    monkeypatch.setattr(protocol.binspect, "binsreg", fail)
    with pytest.raises(RuntimeError, match="unexpected defect"):
        protocol.simulate(protocol.SCENARIOS[0], 93003, repetitions=1)
