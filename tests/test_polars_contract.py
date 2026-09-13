"""Native dataframe behavior and pandas compatibility at the same boundary."""

import json
from datetime import date

import numpy as np
import pandas as pd
import polars as pl
import pytest
from polars.testing import assert_frame_equal

import binspect
from binspect.input_data import control_frame, encoded_controls
from binspect.tabular import to_pandas


def sample():
    rng = np.random.default_rng(421)
    n = 240
    x = rng.normal(size=n)
    return pl.DataFrame(
        {
            "x": x,
            "y": x**2 + rng.normal(size=n),
            "z": rng.normal(size=n),
            "category": ["b", "a", "c"] * 80,
            "w": rng.uniform(0.5, 2, n),
            "cluster": np.arange(n) % 12,
            "group": ["one", "two"] * 120,
        }
    )


@pytest.mark.parametrize("weighted", [False, True])
@pytest.mark.parametrize("clustered", [False, True])
@pytest.mark.parametrize("adjusted", [False, True])
@pytest.mark.parametrize("grouped", [False, True])
def test_native_and_pandas_produce_identical_results(
    weighted, clustered, adjusted, grouped
):
    native = sample()
    pandas = to_pandas(native)
    pandas.index = np.arange(len(pandas))[::-1]  # indexes must not participate
    kwargs = dict(
        x="x",
        y="y",
        bins=4,
        ci=None,
        controls=["z", "category"] if adjusted else None,
        weights="w" if weighted else None,
        cluster="cluster" if clustered else None,
    )
    if grouped:
        kwargs.update(group="group", common_bins=not adjusted)
    estimate = binspect.compare if grouped else binspect.binscatter
    left, right = estimate(native, **kwargs), estimate(pandas, **kwargs)
    assert isinstance(left.table, pl.DataFrame)
    assert isinstance(left.summary_frame(), pl.DataFrame)
    assert_frame_equal(left.table, right.table)
    assert left.to_json() == right.to_json()
    pd.testing.assert_frame_equal(left.to_pandas(), right.to_pandas())


def test_dataframe_and_series_mutations_do_not_change_owned_results():
    native = sample()
    result = binspect.binscatter(native, x="x", y="y", weights="w", bins=4)
    before = result.to_json()
    native[0, "x"] = 999
    table = result.table
    table[0, "y_mean"] = 999
    table.replace_column(0, pl.Series("bin", [99] * 4))
    summary = result.summary_frame()
    summary[0, "slope"] = 999
    assert result.to_json() == before
    returned = result.to_pandas()
    returned.loc[0, "y_mean"] = -999
    assert result.to_json() == before


def test_declared_categories_and_encoded_column_order_survive_filtering():
    native = sample().with_columns(
        pl.col("category").cast(pl.Enum(["c", "b", "a", "unused"]))
    )
    pandas = to_pandas(native)
    pandas["category"] = pd.Categorical(
        pandas["category"], categories=["c", "b", "a", "unused"]
    )
    for source in (native, pandas):
        controls, _ = control_frame(source, ["category", "z"], len(source))
        encoded, design = encoded_controls(controls)
        assert encoded.columns == ["z", "category_b", "category_a", "category_unused"]
        assert design.to_dict()["encoding"][0]["reference"] == {
            "type": "string",
            "value": "c",
        }
        assert encoded["category_unused"].sum() == 0
        expected = pd.get_dummies(
            pandas[["category", "z"]], drop_first=True, dtype=float
        )
        np.testing.assert_array_equal(encoded.to_numpy(), expected.to_numpy())


def test_named_series_controls_use_positions_instead_of_index_alignment():
    source = {
        "a": pd.Series([10.0, 20.0], index=[0, 1]),
        "b": pd.Series([30.0, 40.0], index=[1, 0]),
    }
    controls, _ = control_frame(source, ["a", "b"], 2)
    assert controls.frame.to_dict(as_series=False) == {
        "a": [10.0, 20.0],
        "b": [30.0, 40.0],
    }


@pytest.mark.parametrize("backend", ["polars", "pandas"])
def test_nullable_inputs_and_complete_case_counts(backend):
    frame = sample().with_columns(
        pl.when(pl.int_range(pl.len()) == 0)
        .then(None)
        .otherwise(pl.col("y"))
        .alias("y"),
        pl.when(pl.int_range(pl.len()) == 1)
        .then(float("inf"))
        .otherwise(pl.col("z"))
        .alias("z"),
        pl.when(pl.int_range(pl.len()) == 2)
        .then(0.0)
        .otherwise(pl.col("w"))
        .alias("w"),
        pl.when(pl.int_range(pl.len()) == 3)
        .then(None)
        .otherwise(pl.col("group"))
        .alias("group"),
    )
    source = frame if backend == "polars" else to_pandas(frame).astype({"y": "Float64"})
    result = binspect.compare(
        source,
        x="x",
        y="y",
        controls="z",
        weights="w",
        group="group",
        common_bins=False,
        zero_weight="drop",
        bins=4,
        ci=None,
    )
    counts = result.to_dict()["sample"]
    assert counts == {
        "n_input": 240,
        "n_obs": 236,
        "n_dropped": 4,
        "n_missing_group": 1,
        "n_missing": 2,
        "n_zero_weight_dropped": 1,
        "dropna": True,
        "alignment": "positional",
    }
    assert sum(r.sample.n_input for r in result.results.values()) == 239
    assert sum(r.n_obs for r in result.results.values()) == 236


@pytest.mark.parametrize(
    "label", [1, True, 2.5, "one", date(2026, 1, 1), np.datetime64("2026-01-01", "ns")]
)
def test_group_scalar_identity_is_exported_without_string_collisions(label):
    x = np.linspace(-1, 1, 100)
    groups = np.empty(100, dtype=object)
    groups[:] = [label] * 50 + ["other"] * 50
    result = binspect.compare(x=x, y=x**2, group=groups, bins=2, common_bins=False)
    entries = json.loads(result.to_json())["groups"]
    assert entries[0]["label"]["type"] != entries[1]["label"]["type"] or isinstance(
        label, str
    )
    assert result.table.height == 4
    assert result.summary_frame(include_pooled=True).height == 3


@pytest.mark.parametrize("kwargs", [{"x": "bad"}, {"weights": "bad"}])
def test_named_two_dimensional_inputs_are_rejected(kwargs):
    source = {"x": np.arange(8.0), "y": np.arange(8.0), "bad": np.ones((8, 2))}
    with pytest.raises(ValueError, match="one-dimensional"):
        binspect.binscatter(source, **({"x": "x", "y": "y"} | kwargs))


def test_lazy_inputs_and_encoded_name_collisions_fail_explicitly():
    with pytest.raises(TypeError, match="Collect LazyFrame"):
        binspect.binscatter(sample().lazy(), x="x", y="y")
    with pytest.raises(TypeError, match="Collect LazyFrame"):
        binspect.binscatter(sample(), x="x", y="y", controls=sample().lazy())
    frame = sample().with_columns(pl.lit(1.0).alias("category_b"))
    with pytest.raises(ValueError, match="encoded control columns must be unique"):
        binspect.binscatter(frame, x="x", y="y", controls=["category", "category_b"])


def test_polars_series_inputs_and_controls_match_named_columns():
    frame = sample()
    direct = binspect.binscatter(
        x=frame["x"],
        y=frame["y"],
        controls=frame["z"],
        weights=frame["w"],
        bins=4,
        ci=None,
    )
    named = binspect.binscatter(
        frame, x="x", y="y", controls="z", weights="w", bins=4, ci=None
    )
    assert direct.to_json() == named.to_json()


def test_mixed_numeric_control_values_and_typed_group_tables():
    controls, _ = control_frame({"z": [1, 2.5, None]}, "z", 3)
    assert controls.frame["z"].to_list() == [1.0, 2.5, None]
    x = np.arange(100.0)
    grouped = binspect.compare(
        x=x, y=x * x, group=[1] * 50 + [2.5] * 50, bins=2, common_bins=False
    )
    assert grouped.table.schema["group"] == pl.Object
    labels = grouped.table["group"].to_list()
    assert isinstance(labels[0], int) and isinstance(labels[-1], float)


def test_explicit_date_categories_keep_reference_coding():
    values = pd.Series(pd.Categorical([date(2026, 1, 1), date(2026, 1, 2)] * 2))
    controls, _ = control_frame(None, values, 4)
    encoded, design = encoded_controls(controls)
    assert encoded.to_series().to_list() == [0.0, 1.0, 0.0, 1.0]
    assert design.to_dict()["encoding"][0]["reference"] == {
        "type": "date",
        "value": "2026-01-01",
    }


@pytest.mark.parametrize("weighted", [False, True])
def test_large_integer_categories_preserve_design_and_adjusted_fit(weighted):
    rng = np.random.default_rng(421)
    indicator = np.tile([0.0, 1.0], 120)
    x = indicator + rng.normal(size=240)
    y = 0.7 * x + 4 * indicator + rng.normal(size=240)
    values = pd.Series(
        pd.Categorical([2**53, 2**53 + 1] * 120, categories=[2**53, 2**53 + 1]),
        name="category",
    )
    weights = rng.uniform(0.5, 2, 240) if weighted else None
    controls, _ = control_frame(None, values, 240)
    encoded, design = encoded_controls(controls)
    np.testing.assert_array_equal(encoded.to_numpy(), indicator[:, None])
    assert design.to_dict()["encoding"][0]["levels"] == [
        {"type": "integer", "value": 2**53},
        {"type": "integer", "value": 2**53 + 1},
    ]
    result = binspect.binscatter(
        x=x, y=y, controls=values, weights=weights, bins=4, ci=None
    )
    full_design = np.column_stack((np.ones(240), indicator, x))
    root_weights = np.ones(240) if weights is None else np.sqrt(weights)
    coefficients = np.linalg.lstsq(
        full_design * root_weights[:, None], y * root_weights, rcond=None
    )[0]
    assert result.fit.slope == pytest.approx(coefficients[-1], rel=1e-12, abs=1e-12)

    # The separate function adapter uses the same categorical boundary.
    from binspect.binsreg_inputs import prepare_binsreg

    prepared = prepare_binsreg(None, y, x, weights, values, None, True)
    np.testing.assert_array_equal(prepared.controls, indicator[:, None])
