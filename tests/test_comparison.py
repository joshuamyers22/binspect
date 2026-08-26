"""Grouped estimation and structured export contracts."""

from __future__ import annotations

import json
from datetime import date

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

import binspect
from binspect.exceptions import InsufficientDataError


@pytest.fixture
def grouped_frame() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    x = np.tile(np.linspace(-3.0, 3.0, 600), 2)
    group = np.repeat(["control", "treatment"], 600)
    y = np.where(group == "control", x, 0.5 * x + 0.4 * x**2)
    y = y + rng.normal(scale=0.5, size=x.size)
    return pd.DataFrame({"x": x, "y": y, "arm": group})


def test_compare_returns_group_and_pooled_results(grouped_frame):
    result = binspect.compare(grouped_frame, x="x", y="y", group="arm", bins=12)
    assert isinstance(result, binspect.BinscatterCollection)
    assert result.groups == ("control", "treatment")
    assert result.pooled.n_obs == len(grouped_frame)
    assert sum(item.n_obs for item in result.results.values()) == len(grouped_frame)


def test_common_bins_use_pooled_edges(grouped_frame):
    result = binspect.compare(grouped_frame, x="x", y="y", group="arm", bins=12)
    for grouped_result in result.results.values():
        np.testing.assert_allclose(
            grouped_result.binning.edges, result.pooled.binning.edges
        )


def test_independent_bins_can_differ():
    frame = pd.DataFrame(
        {
            "x": np.concatenate([np.linspace(0, 1, 500), np.linspace(10, 20, 500)]),
            "y": np.linspace(0, 1, 1_000),
            "group": np.repeat(["a", "b"], 500),
        }
    )
    result = binspect.compare(
        frame, x="x", y="y", group="group", bins=10, common_bins=False
    )
    assert not np.array_equal(
        result.results["a"].binning.edges, result.results["b"].binning.edges
    )


def test_group_tables_are_tidy(grouped_frame):
    result = binspect.compare(grouped_frame, x="x", y="y", group="arm", bins=12)
    assert result.group_name == "arm"
    assert result.table.columns[0] == "group"
    assert set(result.table["group"]) == {"control", "treatment"}

    summary = result.summary_frame(include_pooled=True)
    assert summary.columns[:2].tolist() == ["group", "is_pooled"]
    assert summary["group"].tolist() == ["control", "treatment", None]
    assert summary["is_pooled"].tolist() == [False, False, True]
    assert {"slope", "lack_of_fit", "verdict"} <= set(summary.columns)


def test_result_exports_are_json_serializable(grouped_frame):
    single = binspect.binscatter(grouped_frame, x="x", y="y", bins=12)
    grouped = binspect.compare(grouped_frame, x="x", y="y", group="arm", bins=12)
    json.dumps(single.to_dict(), allow_nan=False)
    json.dumps(grouped.to_dict(), allow_nan=False)


def test_non_json_group_labels_are_normalized():
    x = np.tile(np.linspace(0, 1, 100), 2)
    groups = np.repeat([date(2025, 1, 1), date(2026, 1, 1)], 100)
    result = binspect.compare(x=x, y=x, group=groups, bins=5)
    payload = result.to_dict()
    json.dumps(payload, allow_nan=False)
    assert payload["groups"][0]["value"] == "2025-01-01"


def test_group_name_cannot_collide_with_export_columns():
    x = np.tile(np.linspace(0, 1, 100), 2)
    frame = pd.DataFrame({"x": x, "y": x, "bin": np.repeat(["a", "b"], 100)})
    result = binspect.compare(frame, x="x", y="y", group="bin", bins=5)
    assert result.group_name == "bin"
    assert result.table.columns.tolist().count("bin") == 1
    assert result.table.columns[0] == "group"


def test_missing_group_labels_are_excluded(grouped_frame):
    frame = grouped_frame.copy()
    frame.loc[:9, "arm"] = None
    result = binspect.compare(frame, x="x", y="y", group="arm", bins=10)
    assert result.pooled.n_obs == len(frame) - 10


def test_too_small_group_names_the_group(grouped_frame):
    frame = grouped_frame.copy()
    frame.loc[:1, "arm"] = "tiny"
    with pytest.raises(InsufficientDataError, match="group 'tiny'"):
        binspect.compare(frame, x="x", y="y", group="arm", bins=10)


def test_faceted_plot_returns_one_axes_per_group(grouped_frame):
    result = binspect.compare(grouped_frame, x="x", y="y", group="arm", bins=12)
    figure = result.plot(annotate=None)
    assert len(figure.axes) == 2
    assert {ax.get_title() for ax in figure.axes} == {
        "arm = control",
        "arm = treatment",
    }
    plt.close(figure)


def test_invalid_facet_layout_is_refused(grouped_frame):
    result = binspect.compare(grouped_frame, x="x", y="y", group="arm", bins=12)
    with pytest.raises(ValueError, match="layout must be"):
        result.plot(layout="overlay")


def test_compare_applies_controls_to_pooled_and_group_results(grouped_frame):
    frame = grouped_frame.assign(control=np.sin(grouped_frame["x"]))
    result = binspect.compare(
        frame,
        x="x",
        y="y",
        group="arm",
        controls="control",
        bins=10,
        common_bins=False,
    )
    assert result.pooled.controls == ("control",)
    assert all(item.controls == ("control",) for item in result.results.values())


def test_compare_applies_clusters_to_pooled_and_group_results(grouped_frame):
    frame = grouped_frame.assign(firm=np.arange(len(grouped_frame)) // 5)
    result = binspect.compare(
        frame,
        x="x",
        y="y",
        group="arm",
        cluster="firm",
        bins=10,
    )
    assert result.pooled.cluster == "firm"
    assert result.pooled.fit.se_type == "cluster"
    assert all(item.cluster == "firm" for item in result.results.values())
