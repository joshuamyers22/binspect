"""Versioned strict JSON and opt-in provenance without implicit data collection."""

import json
from dataclasses import replace

import numpy as np
import polars as pl
import pytest

import binspect
from binspect.binsreg_results import BinsregResult
from binspect.evidence import canonical_json
from binspect.result_serialization import json_value


def result():
    x = np.linspace(-1, 1, 100)
    return binspect.binscatter(x=x, y=x * x, bins=4, ci=np.float32(0.95))


@pytest.mark.parametrize("kind", ["single", "grouped", "adapter"])
def test_result_json_is_deterministic_and_evidence_separates_timestamps(kind):
    r = result()
    if kind == "grouped":
        r = binspect.compare(x=r.x, y=r.y, group=["a", "b"] * 50, bins=4)
    elif kind == "adapter":
        r = BinsregResult(
            pl.DataFrame({"x": [0.0], "fit": [1.0]}),
            pl.DataFrame({"ci_lo": [float("nan")], "ci_hi": [float("inf")]}),
            {"nested": [np.float64(np.nan)], "issues": []},
        )
    payload = json.loads(r.to_json())
    assert payload["schema_version"] == 1
    assert r.to_json() == canonical_json(payload)
    references = {
        "inputs": {"uri": "private://caller-owned-input", "sha256": "A" * 64},
        "analysis_plan": {"uri": "plan.md"},
        "software_lock": {"sha256": "b" * 64},
        "code": {"revision": "caller-revision"},
    }
    first = r.to_evidence(provenance=references, exported_at="2026-09-12T10:00:00Z")
    second = r.to_evidence(
        provenance=dict(reversed(list(references.items()))),
        exported_at="2026-09-12T11:00:00+00:00",
    )
    assert canonical_json(first["payload"]) == canonical_json(second["payload"])
    assert first["exported_at"] != second["exported_at"]
    assert first["payload"]["provenance"]["inputs"]["sha256"] == "a" * 64
    references["inputs"]["uri"] = "changed"
    first["payload"]["result"].clear()
    assert r.to_dict() == payload
    assert (
        second["payload"]["provenance"]["inputs"]["uri"]
        == "private://caller-owned-input"
    )


def test_absent_provenance_is_unknown_and_raw_observations_are_not_exported():
    r = result()
    evidence = r.to_evidence()
    assert evidence["exported_at"] is None
    assert evidence["payload"]["provenance"] == dict.fromkeys(
        ["analysis_plan", "inputs", "software_lock", "code"]
    )
    payload = evidence["payload"]["result"]
    assert payload["x"] == "x" and payload["y"] == "y"
    assert "assignment" not in payload["binning"]
    assert len(payload["bins"]) == 4
    constructed = replace(r, sample=None, control_design=None)
    assert constructed.to_dict()["sample"] is None
    assert constructed.to_dict()["design"]["column_order"] is None


@pytest.mark.parametrize(
    "provenance",
    [
        {"unexpected": {"uri": "x"}},
        {"inputs": {}},
        {"inputs": {"uri": ""}},
        {"inputs": {"sha256": "not-a-digest"}},
        {"inputs": {"revision": "x"}},
        {"code": {"raw_rows": "x"}},
        {"inputs": {"uri": [1, 2]}},
    ],
)
def test_malformed_provenance_is_rejected(provenance):
    with pytest.raises(ValueError):
        result().to_evidence(provenance=provenance)


@pytest.mark.parametrize(
    "timestamp", ["yesterday", "2026-09-12", "2026-09-12T10:00:00", 123]
)
def test_timestamp_requires_explicit_timezone(timestamp):
    with pytest.raises(ValueError):
        result().to_evidence(exported_at=timestamp)


@pytest.mark.parametrize("adjusted", [False, True])
@pytest.mark.parametrize("clustered", [False, True])
def test_degenerate_inference_is_strict_json_with_actual_covariance(
    adjusted, clustered
):
    x = np.arange(100.0)
    r = binspect.binscatter(
        x=x,
        y=np.ones(100),
        controls=np.sin(x) if adjusted else None,
        cluster=np.repeat([0, 1], 50) if clustered else None,
        ci=None,
        bins=2,
    )
    payload = json.loads(r.to_json())
    assert payload["inference"]["ci_level"] is None
    assert payload["inference"]["slope_covariance"] == (
        "cluster" if clustered else "classical"
    )
    assert payload["inference"]["bin_covariance"] == (
        "unavailable" if adjusted else "cluster" if clustered else "independent"
    )
    assert all(row["ci_lo"] is None and row["ci_hi"] is None for row in payload["bins"])
    if adjusted or clustered:
        assert payload["inference"]["bin_reference_df"] == [None, None]


def test_unknown_objects_and_nonstring_keys_are_not_silently_stringified():
    with pytest.raises(TypeError, match="Unsupported"):
        json_value(object())
    with pytest.raises(TypeError, match="keys"):
        json_value({1: "one"})
