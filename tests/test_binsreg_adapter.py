"""Adapter boundary checks without requiring the optional backend."""

from __future__ import annotations

import json
import sys
import warnings
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

import binspect
import binspect.binsreg_api as adapter


def output():
    return SimpleNamespace(
        data_plot=[
            SimpleNamespace(
                dots=pd.DataFrame({"x": [-0.5, 0.5], "bin": [1, 2], "fit": [2.0, 3.0]}),
                ci=pd.DataFrame(
                    {
                        "x": [-0.5, 0.5],
                        "bin": [1, 2],
                        "ci_l": [1.0, 2.0],
                        "ci_r": [2.0, 3.0],
                    }
                ),
            )
        ],
        options=SimpleNamespace(nbins_by=[2], dots=[[0, 0]], ci=[[1, 1]]),
    )


@pytest.fixture
def backend(monkeypatch):
    calls = []

    def fake(**kwargs):
        calls.append(kwargs)
        return output()

    monkeypatch.setattr(adapter, "_load_backend", lambda: (fake, "3.2.1"))
    return calls


def sample():
    x = np.linspace(-1, 1, 100)
    return {"x": x, "y": x * x, "bins": 2}


def test_original_coordinates_filtering_and_full_control_covariance(backend):
    rng = np.random.default_rng(93001)
    frame = pd.DataFrame(
        {
            "x": rng.normal(size=100),
            "y": rng.normal(size=100),
            "z": rng.normal(size=100),
            "w": np.ones(100),
            "group": np.tile(["a", "b"], 50),
        }
    )
    frame.loc[0, "y"] = np.nan
    frame.loc[1, "w"] = 0
    original = frame.copy(deep=True)
    result = binspect.binsreg(
        frame, x="x", y="y", controls="z", weights="w", cluster="group"
    )
    call = backend[0]
    np.testing.assert_array_equal(call["x"], frame.x.to_numpy()[2:])
    assert call["asyvar"] is False
    assert call["randcut"] == 1
    assert call["dfcheck"] == (20, 30)
    np.testing.assert_allclose(call["at"], [frame.z.iloc[2:].mean()])
    assert result.metadata["control_columns"] == ["z"]
    assert result.metadata["n_input"] == 100
    assert result.metadata["n_obs"] == 98
    assert result.metadata["n_missing"] == result.metadata["n_zero_weight"] == 1
    call["x"][:] = 999
    pd.testing.assert_frame_equal(frame, original)


def test_categorical_encoding_and_explicit_evaluation(backend):
    args = sample()
    args["controls"] = pd.DataFrame({"category": np.tile(["a", "b"], 50)})
    result = binspect.binsreg(**args, at=[0.25])
    assert result.metadata["control_columns"] == ["category_b"]
    assert result.metadata["at"] == [0.25]
    assert backend[0]["w"].shape == (100, 1)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"ci": 0},
        {"ci": np.nan},
        {"ci": True},
        {"bins": True},
        {"bins": 1},
        {"bins": "auto"},
        {"bins": 101},
        {"binning": "custom"},
        {"at": [1]},
        {"at": "median"},
        {"weights": -np.ones(100)},
        {"weights": np.ones(99)},
        {"controls": np.ones(100)},
        {"cluster": np.zeros(100)},
        {"x": np.ones((10, 10))},
        {"y": np.ones(4)},
        {"weights": np.zeros(100)},
        {"y": np.full(100, np.nan), "dropna": False},
    ],
)
def test_invalid_inputs_fail_before_backend(backend, kwargs):
    args = sample() | kwargs
    with pytest.raises((ValueError, binspect.InsufficientDataError)):
        binspect.binsreg(**args)
    assert not backend


def test_warning_status_and_actual_fallback_are_explicit(monkeypatch):
    def fallback(**kwargs):
        warnings.warn("Too small effective sample size for ci.", stacklevel=2)
        warnings.warn("ci=(0,0) used.", stacklevel=2)
        return output()

    monkeypatch.setattr(adapter, "_load_backend", lambda: (fallback, "3.2.1"))
    with pytest.warns(binspect.BinsregWarning, match="limited_support"):
        result = binspect.binsreg(**sample())
    assert result.metadata["actual_intervals"] == [0, 0]
    assert result.metadata["fallback"]
    assert not result.metadata["few_cluster_coverage_guaranteed"]
    assert "limited_support" in result.summary()


def test_unknown_warning_does_not_leak_or_claim_verified_method(monkeypatch, capsys):
    def changed(**kwargs):
        print("private upstream output")
        warnings.warn("private warning payload", stacklevel=2)
        return output()

    monkeypatch.setattr(adapter, "_load_backend", lambda: (changed, "3.2.1"))
    with pytest.warns(binspect.BinsregWarning, match="unverified_method"):
        result = binspect.binsreg(**sample())
    assert "private" not in json.dumps(result.to_dict())
    assert not capsys.readouterr().out
    assert result.metadata["actual_intervals"] is None


@pytest.mark.parametrize(
    "kind", ["nan", "reverse", "schema", "bad_count", "fractional_degree"]
)
def test_malformed_upstream_result_is_rejected(monkeypatch, kind):
    result = output()
    if kind == "nan":
        result.data_plot[0].ci.loc[0, "ci_l"] = np.nan
    if kind == "reverse":
        result.data_plot[0].ci.loc[0, "ci_l"] = 100
    if kind == "schema":
        result.data_plot[0].dots = {}
    if kind == "bad_count":
        result.options.nbins_by = [2.5]
    if kind == "fractional_degree":
        result.options.ci = [[1.5, 1]]
    monkeypatch.setattr(
        adapter, "_load_backend", lambda: (lambda **kwargs: result, "3.2.1")
    )
    with pytest.raises(binspect.BinsregError):
        binspect.binsreg(**sample())


def test_unavailable_intervals_have_explicit_status(monkeypatch):
    raw = output()
    raw.data_plot[0].ci = None
    monkeypatch.setattr(adapter, "_load_backend", lambda: (lambda **kw: raw, "3.2.1"))
    with pytest.warns(binspect.BinsregWarning, match="unavailable"):
        result = binspect.binsreg(**sample())
    assert result.intervals.empty
    json.dumps(result.to_dict(), allow_nan=False)


def test_outputs_are_copied_and_plot_uses_interval_centers(backend):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    result = binspect.binsreg(**sample())
    before = result.to_dict()
    dots, intervals = result.dots, result.intervals
    dots.loc[0, "fit"] = 999
    intervals.loc[0, "ci_lo"] = 999
    result.metadata["issues"].append("changed")
    assert result.to_dict() == before
    json.dumps(before, allow_nan=False)
    fig, ax = plt.subplots()
    result.plot(ax=ax)
    np.testing.assert_allclose(ax.lines[0].get_ydata(), [1.5, 2.5])
    plt.close(fig)


def test_upstream_exception_is_sanitized(monkeypatch):
    def fail(**kwargs):
        raise ValueError("private inputs")

    monkeypatch.setattr(adapter, "_load_backend", lambda: (fail, "3.2.1"))
    with pytest.raises(binspect.BinsregError, match="could not fit") as error:
        binspect.binsreg(**sample())
    assert "private" not in str(error.value)


def test_missing_optional_backend_has_install_hint(monkeypatch):
    monkeypatch.setitem(sys.modules, "binsreg", None)
    with pytest.raises(binspect.BinsregError, match=r"binspect-regression\[dpi\]"):
        binspect.binsreg(**sample())


@pytest.mark.parametrize("change", ["version", "degree", "count"])
def test_unverified_backend_changes_are_explicit(monkeypatch, change):
    raw = output()
    if change == "degree":
        raw.options.ci = [[0, 0]]
    version = "4.0.0" if change == "version" else "3.2.1"
    monkeypatch.setattr(adapter, "_load_backend", lambda: (lambda **kw: raw, version))
    args = sample() | ({"bins": 3} if change == "count" else {})
    with pytest.warns(binspect.BinsregWarning, match="unverified_method"):
        result = binspect.binsreg(**args)
    assert result.metadata["actual_intervals"] is None
    assert result.metadata["selection_method"] == "unverified"


def test_rot_fallback_is_exposed(monkeypatch):
    def fallback(**kwargs):
        warnings.warn("DPI selection fails. ROT choice used.", stacklevel=2)
        return output()

    monkeypatch.setattr(adapter, "_load_backend", lambda: (fallback, "3.2.1"))
    with pytest.warns(binspect.BinsregWarning, match="dpi_to_rot_fallback"):
        result = binspect.binsreg(**(sample() | {"bins": "dpi"}), at="zero")
    assert result.metadata["selection_method"] == "rot"
    assert result.metadata["fallback"]
