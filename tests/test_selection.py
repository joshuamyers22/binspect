"""DPI adapter behavior without importing the optional backend."""

from __future__ import annotations

import json
import sys
from types import SimpleNamespace

import numpy as np
import pytest

import binspect
from binspect.core.selection import select_n_bins
from binspect.exceptions import BinCountWarning, InvalidBinningError


@pytest.fixture
def selection_data():
    x = np.linspace(-2, 2, 400)
    return x, np.sin(x)


@pytest.fixture
def backend(monkeypatch):
    calls = []
    output = SimpleNamespace(nbinsrot_regul=5, nbinsdpi=17)

    def select(**kwargs):
        calls.append(kwargs)
        return output

    monkeypatch.setitem(sys.modules, "binsreg", SimpleNamespace(binsregselect=select))
    return output, calls


def test_dpi_uses_dpi_not_rot(selection_data, backend):
    x, y = selection_data
    assert select_n_bins(x, "dpi", y=y) == 17


@pytest.mark.parametrize("method,spacing", [("quantile", "qs"), ("equal_width", "es")])
def test_dpi_passes_the_model_and_spacing(selection_data, backend, method, spacing):
    x, y = selection_data
    binspect.binscatter(x=x, y=y, bins="dpi", binning=method)
    _, calls = backend
    assert len(calls) == 1
    call = calls[0]
    np.testing.assert_array_equal(call.pop("x"), x)
    np.testing.assert_array_equal(call.pop("y"), y)
    assert call == {
        "bins": (0, 0),
        "binsmethod": "dpi",
        "binspos": spacing,
        "masspoints": "on",
        "vce": "HC1",
        "randcut": None,
    }


@pytest.mark.parametrize(
    "value",
    [None, np.nan, np.inf, -np.inf, 0, 1, -3, 2.5, 401, "17", True, [17]],
)
def test_invalid_dpi_never_falls_back_to_rot(selection_data, backend, value):
    x, y = selection_data
    output, _ = backend
    output.nbinsdpi = value
    with pytest.raises(InvalidBinningError, match=r"DPI.*explicit integer"):
        select_n_bins(x, "dpi", y=y)


def test_missing_dpi_result_never_falls_back(selection_data, backend):
    x, y = selection_data
    del backend[0].nbinsdpi
    with pytest.raises(InvalidBinningError, match="DPI"):
        select_n_bins(x, "dpi", y=y)


@pytest.mark.parametrize("value", [17, 17.0, np.int64(17), np.float64(17)])
def test_integer_valued_scalar_counts_are_accepted(selection_data, backend, value):
    x, y = selection_data
    backend[0].nbinsdpi = value
    assert select_n_bins(x, "dpi", y=y) == 17


def test_missing_dependency_names_the_distribution(selection_data, monkeypatch):
    x, y = selection_data
    monkeypatch.setitem(sys.modules, "binsreg", None)
    with pytest.raises(InvalidBinningError, match=r"binspect-regression\[dpi\]"):
        select_n_bins(x, "dpi", y=y)


@pytest.mark.parametrize(
    "error", [ValueError, np.linalg.LinAlgError, ZeroDivisionError]
)
def test_backend_numerical_failure_is_actionable(selection_data, monkeypatch, error):
    x, y = selection_data

    def fail(**kwargs):
        raise error("numerical failure")

    monkeypatch.setitem(sys.modules, "binsreg", SimpleNamespace(binsregselect=fail))
    with pytest.raises(InvalidBinningError, match=r"DPI.*explicit integer") as exc:
        select_n_bins(x, "dpi", y=y)
    assert isinstance(exc.value.__cause__, error)


def test_dpi_needs_y(selection_data):
    with pytest.raises(InvalidBinningError, match="needs y"):
        select_n_bins(selection_data[0], "dpi")


@pytest.mark.parametrize(
    "x,y",
    [
        (np.arange(3.0), np.arange(3.0)),
        (np.ones(5), np.arange(5.0)),
        (np.arange(5.0), np.ones((5, 1))),
        (np.ones((5, 1)), np.arange(5.0)),
        (np.arange(5.0), np.full(5, np.nan)),
        (np.full(5, np.inf), np.arange(5.0)),
    ],
)
def test_invalid_dpi_sample_is_rejected_before_backend(x, y, backend):
    with pytest.raises(InvalidBinningError, match="DPI"):
        select_n_bins(x, "dpi", y=y)
    assert backend[1] == []


def test_valid_dpi_count_is_not_clipped_to_heuristic_limits(selection_data, backend):
    x, y = selection_data
    backend[0].nbinsdpi = 65
    assert select_n_bins(x, "dpi", y=y) == 65


def test_dpi_refuses_custom_spacing_before_backend(selection_data, backend):
    x, y = selection_data
    with pytest.raises(InvalidBinningError, match=r"quantile.*equal_width"):
        select_n_bins(x, "dpi", y=y, method="custom")
    assert backend[1] == []


@pytest.mark.parametrize("option", ["weights", "controls", "cluster"])
@pytest.mark.parametrize("grouped", [False, True])
def test_unsupported_dpi_options_are_not_silently_ignored(
    selection_data, backend, option, grouped
):
    x, y = selection_data
    options = {option: np.ones(x.size)}
    if grouped:
        options["group"] = np.repeat(["a", "b"], x.size // 2)
    estimate = binspect.compare if grouped else binspect.binscatter
    with pytest.raises(InvalidBinningError, match=f"DPI.*{option}"):
        estimate(x=x, y=y, bins="dpi", **options)
    assert backend[1] == []


def test_dpi_uses_the_retained_sample(selection_data, backend):
    x, y = selection_data
    y = y.copy()
    y[0] = np.nan
    result = binspect.binscatter(x=x, y=y, bins="dpi")
    assert result.n_obs == 399
    np.testing.assert_array_equal(backend[1][0]["x"], x[1:])


def test_result_records_rule_counts_and_no_fallback(selection_data, backend):
    x, y = selection_data
    result = binspect.binscatter(x=x, y=y, bins="dpi")
    assert result.bin_rule == "dpi"
    payload = result.to_dict()
    assert payload["binning"]["rule"] == "dpi"
    assert payload["binning"]["requested_bins"] == 17
    assert payload["binning"]["n_bins"] == 17
    assert payload["binning"]["fallback"] is None
    frame = result.summary_frame().iloc[0]
    assert frame["bin_rule"] == "dpi"
    assert frame["requested_bins"] == 17
    assert "dpi" in result.summary()
    json.dumps(payload, allow_nan=False)


def test_discrete_partition_preserves_selected_count(backend):
    backend[0].nbinsdpi = 20
    x = np.repeat(np.arange(7.0), 60)
    with pytest.warns(BinCountWarning, match="merged"):
        result = binspect.binscatter(x=x, y=x**2, bins="dpi")
    assert result.binning.requested_bins == 20
    assert result.n_bins < 20
    assert result.binning.fallback is None
    assert result.bin_rule == "dpi"


@pytest.mark.parametrize("common", [True, False])
def test_grouped_selection_provenance(selection_data, backend, common):
    x, y = selection_data
    group = np.tile(["a", "b"], x.size // 2)
    result = binspect.compare(x=x, y=y, group=group, bins="dpi", common_bins=common)
    assert result.pooled.bin_rule == "dpi"
    assert len(backend[1]) == (1 if common else 3)
    for item in result.results.values():
        assert item.bin_rule == ("pooled" if common else "dpi")
        assert item.binning.source_rule == ("dpi" if common else None)
    json.dumps(result.to_dict(), allow_nan=False)


@pytest.mark.parametrize(
    "bins,rule",
    [
        (10, "fixed"),
        ("auto", "auto"),
        ("iqr", "iqr"),
        ("sturges", "sturges"),
        ([-2, 0, 2], "custom"),
    ],
)
def test_other_rules_do_not_call_optional_backend(selection_data, backend, bins, rule):
    x, y = selection_data
    result = binspect.binscatter(x=x, y=y, bins=bins)
    assert result.bin_rule == rule
    assert backend[1] == []
