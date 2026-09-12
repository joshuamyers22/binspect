"""Behavioral regressions for result ownership, including AR9."""

import json
import pickle
import warnings
from copy import copy, deepcopy
from dataclasses import fields, replace

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

import binspect
from binspect.binsreg_results import BinsregResult
from binspect.core.binning import Binning


def sample():
    rng = np.random.default_rng(421)
    x = np.linspace(-2, 2, 400)
    return pd.DataFrame(
        {
            "x": x,
            "y": x**2 + rng.normal(size=x.size),
            "w": rng.uniform(0.5, 2, size=x.size),
            "z": rng.normal(size=x.size),
            "cluster": np.tile(np.arange(20), 20),
            "group": np.tile(["a", "b"], 200),
        }
    )


def arrays(result):
    for owner in (result, result.binning, result.estimates):
        for field in fields(owner):
            value = getattr(owner, field.name)
            if isinstance(value, np.ndarray):
                yield owner, field.name, value
    yield result.binning, "partition_edges", result.binning.partition_edges
    yield result.binning, "interval_ids", result.binning.interval_ids


@pytest.mark.parametrize("adjusted", [False, True])
@pytest.mark.parametrize("filtered", [False, True])
def test_caller_dataframe_mutation_preserves_estimation_and_plots(adjusted, filtered):
    frame = sample()
    if filtered:
        frame.loc[0, "y"] = np.nan
        frame.loc[1, "w"] = 0
    result = binspect.binscatter(
        frame,
        x="x",
        y="y",
        weights="w",
        cluster="cluster",
        bins=4,
        controls="z" if adjusted else None,
        ci=None,
        zero_weight="drop" if filtered else "retain",
    )
    expected = result.to_dict()
    expected_arrays = [(name, value.copy()) for _, name, value in arrays(result)]
    figure = result.audit(show=["raw", "bins", "fit"], annotate=None)
    figure.canvas.draw()
    pixels = np.asarray(figure.canvas.buffer_rgba()).copy()
    plt.close(figure)
    frame.loc[:, ["x", "y", "w", "z", "cluster"]] = 0
    assert result.to_dict() == expected
    for (_, name, value), (expected_name, before) in zip(
        arrays(result), expected_arrays, strict=True
    ):
        assert name == expected_name
        np.testing.assert_array_equal(value, before)
    figure = result.audit(show=["raw", "bins", "fit"], annotate=None)
    figure.canvas.draw()
    np.testing.assert_array_equal(np.asarray(figure.canvas.buffer_rgba()), pixels)
    plt.close(figure)


def test_strided_input_views_and_custom_edges_are_owned():
    source = np.arange(800.0)
    x = source[::2]
    y = source[1::2]
    weights = np.linspace(0.5, 2, x.size)
    edges = np.linspace(-1, 800, 5)
    result = binspect.binscatter(x=x, y=y, weights=weights, bins=edges)
    expected = result.to_dict()
    assert source.flags.writeable and edges.flags.writeable
    assert not np.shares_memory(result.x, source)
    assert not np.shares_memory(result.weights, weights)
    source[:] = -100
    weights[:] = 100
    edges[:] = 0
    assert result.to_dict() == expected
    np.testing.assert_array_equal(result.x, np.arange(0, 800, 2))


@pytest.mark.parametrize("clustered", [False, True])
def test_every_nested_array_resists_writes_and_header_mutations(clustered):
    result = binspect.binscatter(
        sample(),
        x="x",
        y="y",
        weights="w",
        bins=4,
        cluster="cluster" if clustered else None,
    )
    expected = result.to_dict()
    for owner, name, value in arrays(result):
        before = value.copy()
        with pytest.raises(ValueError):
            value.flat[0] = 0
        with pytest.raises(ValueError):
            value.setflags(write=True)
        # Every ndarray in the exposed base chain must also be read-only.
        base = value.base
        while isinstance(base, np.ndarray):
            with pytest.raises(ValueError):
                base.setflags(write=True)
            base = base.base
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            value.shape = (1, value.size)
            value.dtype = np.uint8
        np.testing.assert_array_equal(getattr(owner, name), before)
        editable = getattr(owner, name).copy()
        editable[:] = 0
        np.testing.assert_array_equal(getattr(owner, name), before)
    assert result.to_dict() == expected


def test_direct_construction_and_replacement_own_all_array_arguments():
    result = binspect.binscatter(sample(), x="x", y="y", bins=4)
    for owner in (result, result.binning, result.estimates):
        supplied = {
            f.name: getattr(owner, f.name).copy()
            for f in fields(owner)
            if isinstance(getattr(owner, f.name), np.ndarray)
        }
        constructed = replace(owner, **supplied)
        for name, value in supplied.items():
            before = value.copy()
            value[:] = 0
            np.testing.assert_array_equal(getattr(constructed, name), before)
    controls = ["z"]
    adjusted = replace(result, controls=controls)
    controls.append("other")
    assert adjusted.controls == ("z",)
    legacy = Binning(np.array([0.0, 1.0, 2.0]), np.array([0, 1]), 2, "custom", 2)
    legacy.interval_ids[:] = 100  # A fresh derived array, not stored data.
    np.testing.assert_array_equal(legacy.interval_ids, [0, 1])
    with pytest.raises(TypeError, match="Python objects"):
        replace(result, x=np.array([object()], dtype=object))


@pytest.mark.parametrize(
    "clone", [copy, deepcopy, lambda r: pickle.loads(pickle.dumps(r))]
)
def test_copied_results_keep_ownership(clone):
    result = binspect.binscatter(sample(), x="x", y="y", weights="w", bins=4)
    cloned = clone(result)
    assert cloned.to_dict() == result.to_dict()
    for _, _, value in arrays(cloned):
        with pytest.raises(ValueError):
            value.setflags(write=True)


def test_single_tables_metadata_and_derived_arrays_are_editable_projections():
    result = binspect.binscatter(sample(), x="x", y="y", weights="w", bins=4)
    before = result.to_dict()
    for frame in (result.table, result.decomposition_table, result.summary_frame()):
        for column in frame.select_dtypes(include="number"):
            frame.loc[:, column] = 0
    exported = result.to_dict()
    exported["bins"][0]["y_mean"] = 999
    exported["binning"]["edges"].clear()
    result.inference.clear()
    result.residuals_from_fit()[:] = 0
    result.binning.counts()[:] = 0
    result.fit.predict(result.x)[:] = 0
    assert result.to_dict() == before


@pytest.mark.parametrize("common_bins", [False, True])
def test_group_mapping_pooled_results_and_exports_are_isolated(common_bins):
    frame = sample()
    grouped = binspect.compare(
        frame, x="x", y="y", group="group", weights="w", bins=4, common_bins=common_bins
    )
    expected = json.dumps(grouped.to_dict(), allow_nan=False)
    mapping = dict(grouped.results)
    collection = replace(grouped, results=mapping)
    mapping.clear()
    with pytest.raises(TypeError):
        collection.results["a"] = grouped.pooled
    frame.loc[:, ["x", "y", "w"]] = 0
    for result in (*collection.results.values(), collection.pooled):
        for _, _, value in arrays(result):
            with pytest.raises(ValueError):
                value.flat[0] = 0
        table = result.table
        table.loc[:, "y_mean"] = 999
    table = collection.table
    table.loc[:, "y_mean"] = 0
    summary = collection.summary_frame(include_pooled=True)
    summary.loc[:, "slope"] = 0
    collection.to_dict()["groups"].clear()
    assert json.dumps(collection.to_dict(), allow_nan=False) == expected


def test_adapter_tables_and_nested_metadata_remain_owned():
    dots = pd.DataFrame({"x": [0.0, 1.0], "fit": [1.0, 2.0]})
    intervals = pd.DataFrame({"x": [0.0, 1.0], "ci_l": [0.0, 1.0], "ci_r": [2.0, 3.0]})
    metadata = {"issues": [], "nested": {"values": [1, 2]}}
    result = BinsregResult(dots, intervals, metadata)
    expected = result.to_dict()
    dots.loc[:, "fit"] = 0
    intervals.loc[:, "ci_l"] = 0
    metadata["nested"]["values"].clear()
    returned_dots = result.dots
    returned_intervals = result.intervals
    returned_dots.loc[:, "fit"] = 0
    returned_intervals.loc[:, "ci_r"] = 0
    result.metadata["nested"]["values"].clear()
    result.to_dict()["metadata"]["issues"].append("changed")
    assert result.to_dict() == expected
