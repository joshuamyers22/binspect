"""Budget enforcement must fail closed on unaccepted or incomparable evidence."""

from __future__ import annotations

import copy
import runpy
from pathlib import Path

import pytest

CHECKS = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "validation/performance_check.py")
)


def evidence():
    return {
        "identity": dict.fromkeys(CHECKS["IDENTITY_KEYS"], "fixture"),
        "workloads": [
            {
                "spec": {"name": "example", "n": 10_000},
                "status": "pass",
                "numerical": [1.0, None],
                "trials": [
                    {
                        "timings": {"estimate_first_s": 1.0},
                        "estimate_peak_rss_bytes": 100,
                        "process_peak_rss_bytes": 200,
                    }
                    for _ in range(3)
                ],
            }
        ],
    }


def test_budget_requires_explicit_acceptance():
    report = evidence()
    budget = CHECKS["propose"](report)
    with pytest.raises(ValueError, match="acceptance is pending"):
        CHECKS["enforce"](budget, report)


@pytest.mark.parametrize(
    "defect", ["host", "missing", "incomplete", "time", "memory", "spec"]
)
def test_budget_detects_regression_or_unqualified_run(defect):
    original = evidence()
    budget = CHECKS["propose"](original)
    # Synthetic acceptance exercises mechanics only; no actual baseline is accepted.
    budget["acceptance"] = {
        "status": "accepted",
        "reviewer": "test fixture",
        "date": "2000-01-01",
    }
    CHECKS["enforce"](budget, original)
    report = copy.deepcopy(original)
    entry = report["workloads"][0]
    if defect == "host":
        report["identity"]["host"] = "different"
    elif defect == "missing":
        report["workloads"] = []
    elif defect == "incomplete":
        entry["status"] = "rss_limit"
    elif defect == "time":
        entry["trials"][0]["timings"]["estimate_first_s"] = 2
    elif defect == "memory":
        entry["trials"][0]["process_peak_rss_bytes"] = 300
    else:
        entry["spec"]["n"] = 100_000
    with pytest.raises(ValueError):
        CHECKS["enforce"](budget, report)


def test_reference_detects_numerical_drift_and_reports_unmeasured_cases():
    original = evidence()
    candidate = copy.deepcopy(original)
    candidate["workloads"][0]["numerical"][0] = 1.1
    with pytest.raises(AssertionError):
        CHECKS["compare"]([original], candidate)
    candidate["workloads"][0]["status"] = "rss_limit"
    result = CHECKS["compare"]([original], candidate)
    assert not result["numerically_equivalent"]
    assert result["not_compared"][0]["after"] == "rss_limit"
