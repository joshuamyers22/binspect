"""Grouped coordinates and interval identity must agree with caller data."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

import binspect
from binspect.exceptions import BinCountWarning, InvalidBinningError


@pytest.fixture
def shifted_controls() -> pd.DataFrame:
    rng = np.random.default_rng(0)
    group = np.repeat(["a", "b"], 100)
    control = rng.normal(size=200) + np.repeat([-3.0, 3.0], 100)
    x = 5 * control + rng.normal(size=200)
    y = x + control + rng.normal(size=200)
    return pd.DataFrame(
        {
            "x": x,
            "y": y,
            "group": group,
            "control": control,
            "weight": rng.uniform(0.5, 2.0, 200),
        }
    )


@pytest.mark.parametrize("weighted", [False, True])
def test_shared_adjusted_coordinates_are_explicitly_unsupported(
    shifted_controls, weighted
):
    with pytest.raises(InvalidBinningError, match="common_bins=False"):
        binspect.compare(
            shifted_controls,
            x="x",
            y="y",
            group="group",
            controls="control",
            weights="weight" if weighted else None,
            bins=5,
        )


@pytest.mark.parametrize("weighted", [False, True])
def test_independent_adjustment_preserves_group_fits_and_means(
    shifted_controls, weighted
):
    comparison = binspect.compare(
        shifted_controls,
        x="x",
        y="y",
        group="group",
        controls="control",
        weights="weight" if weighted else None,
        bins=5,
        common_bins=False,
        ci=None,
    )
    for result in [comparison.pooled, *comparison.results.values()]:
        assert result.table[["se", "ci_lo", "ci_hi"]].isna().all().all()
        assert result.estimates.ci_level is None
        assert np.isfinite(result.fit.se_slope)
    for label, result in comparison.results.items():
        sample = shifted_controls.loc[shifted_controls["group"] == label]
        weights = sample["weight"].to_numpy() if weighted else None
        design = np.column_stack([np.ones(len(sample)), sample["control"], sample["x"]])
        response = sample["y"].to_numpy()
        if weights is not None:
            design = design * np.sqrt(weights)[:, None]
            response = response * np.sqrt(weights)
        coefficients, *_ = np.linalg.lstsq(design, response, rcond=None)
        assert result.fit.slope == pytest.approx(coefficients[-1], rel=1e-11)
        assert np.average(result.x, weights=weights) == pytest.approx(
            np.average(sample["x"], weights=weights)
        )
        assert np.average(result.y, weights=weights) == pytest.approx(
            np.average(sample["y"], weights=weights)
        )


@pytest.mark.parametrize("zero_weight", ["retain", "drop"])
@pytest.mark.parametrize("partition", ["custom", "equal_width", "quantile"])
def test_shared_interval_ids_and_bounds_survive_empty_bins(partition, zero_weight):
    # Both groups have disjoint support and interior gaps. The custom partition
    # additionally has empty leading, trailing and globally empty interior bins.
    x = np.repeat([0.5, 2.0, 2.5, 4.5, 6.0, 6.5], 20)
    frame = pd.DataFrame(
        {
            "x": x,
            "y": x**2 + np.tile(np.linspace(-0.1, 0.1, 20), 6),
            "group": np.repeat(["a", "b"], 60),
            "weight": np.ones(120),
        }
    )
    frame.loc[0, "y"] = np.nan
    frame.loc[60, "group"] = None
    frame.loc[20:39, "weight"] = 0.0  # these rows drop or remain in descriptive counts
    # Give the bin containing these observations some positive weight when kept.
    frame.loc[39, "weight"] = 1.0
    custom_edges = np.arange(-1.0, 9.0)
    kwargs = (
        {"bins": custom_edges}
        if partition == "custom"
        else {
            "bins": 8,
            "binning": partition,
        }
    )
    with pytest.warns(BinCountWarning):
        comparison = binspect.compare(
            frame,
            x="x",
            y="y",
            group="group",
            weights="weight",
            zero_weight=zero_weight,
            **kwargs,
        )
    edges = comparison.pooled.binning.partition_edges
    if partition == "custom":
        np.testing.assert_array_equal(edges, custom_edges)
    pooled_bounds = comparison.pooled.table.set_index("bin")[["x_lo", "x_hi"]]
    for label, result in comparison.results.items():
        np.testing.assert_array_equal(result.binning.partition_edges, edges)
        sample = frame.loc[(frame["group"] == label) & frame["y"].notna()]
        if zero_weight == "drop":
            sample = sample.loc[sample["weight"] > 0]
        expected_ids = []
        for interval in range(len(edges) - 1):
            lower = (
                sample["x"] >= edges[interval]
                if interval == 0
                else sample["x"] > edges[interval]
            )
            members = sample.loc[lower & (sample["x"] <= edges[interval + 1])]
            if members.empty:
                continue
            expected_ids.append(interval)
            row = result.table.set_index("bin").loc[interval]
            assert row["n"] == len(members)
            assert row["x_lo"] == edges[interval]
            assert row["x_hi"] == edges[interval + 1]
            assert row["y_mean"] == pytest.approx(
                np.average(members["y"], weights=members["weight"])
            )
        assert result.table["bin"].tolist() == expected_ids
        np.testing.assert_array_equal(result.binning.interval_ids, expected_ids)
        # Estimation indices stay compact even though displayed IDs can have gaps.
        np.testing.assert_array_equal(
            np.unique(result.binning.assignment), np.arange(result.n_bins)
        )
        pd.testing.assert_frame_equal(
            result.table.set_index("bin")[["x_lo", "x_hi"]],
            pooled_bounds.loc[expected_ids],
        )
    payload = comparison.to_dict()
    json.dumps(payload, allow_nan=False)
    for entry in payload["groups"]:
        result = comparison.results[entry["value"]]
        assert entry["result"]["binning"]["partition_edges"] == edges.tolist()
        assert (
            entry["result"]["binning"]["interval_ids"] == result.table["bin"].tolist()
        )
        assert [row["bin"] for row in entry["result"]["bins"]] == result.table[
            "bin"
        ].tolist()
    assert comparison.table["bin"].tolist() == [
        interval
        for result in comparison.results.values()
        for interval in result.table["bin"]
    ]


def test_group_weight_failure_names_group_and_preserves_cause():
    x = np.tile(np.linspace(0, 1, 40), 2)
    weights = np.concatenate([np.ones(40), np.zeros(40)])
    with pytest.raises(ValueError, match=r"group 'empty'.*positive") as error:
        binspect.compare(
            x=x, y=x**2, group=np.repeat(["ok", "empty"], 40), weights=weights, bins=2
        )
    assert isinstance(error.value.__cause__, ValueError)


def test_group_binning_failure_names_group_and_preserves_cause(shifted_controls):
    with pytest.raises(InvalidBinningError, match=r"group 'a'.*cover") as error:
        binspect.compare(
            shifted_controls,
            x="x",
            y="y",
            group="group",
            controls="control",
            bins=[-10.0, -1.0, 1.0, 10.0],
            common_bins=False,
        )
    assert isinstance(error.value.__cause__, InvalidBinningError)


def test_missing_estimation_values_are_rejected_when_requested():
    x = np.tile(np.linspace(0, 1, 40), 2)
    y = x.copy()
    y[0] = np.nan
    with pytest.raises(ValueError, match="non-finite"):
        binspect.compare(
            x=x, y=y, group=np.repeat(["a", "b"], 40), bins=2, dropna=False
        )
