"""Matched real-backend delegation, including its small-cluster fallback."""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import pytest

import binspect

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("adjusted", [False, True])
@pytest.mark.parametrize("weighted", [False, True])
@pytest.mark.parametrize("clustered", [False, True])
@pytest.mark.parametrize("spacing", ["quantile", "equal_width"])
def test_matches_direct_binsreg(adjusted, weighted, clustered, spacing):
    from binsreg import binsreg

    rng = np.random.default_rng(93000)
    x = rng.uniform(-1, 1, 600)
    z = rng.normal(size=600)
    y = 2 + x + 2 * x * x + z + rng.normal(size=600)
    w = rng.uniform(0.5, 2, 600) if weighted else None
    groups = np.repeat(np.arange(60), 10) if clustered else None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        result = binspect.binsreg(
            x=x,
            y=y,
            controls=z if adjusted else None,
            weights=w,
            cluster=groups,
            bins=5,
            binning=spacing,
            at=[1.0] if adjusted else "mean",
        )
        expected = binsreg(
            y=y,
            x=x,
            w=z[:, None] if adjusted else None,
            weights=w,
            cluster=groups,
            nbins=5,
            binspos="qs" if spacing == "quantile" else "es",
            at=[1.0] if adjusted else None,
            ci=True,
            dots=(0, 0),
            asyvar=False,
            vce="HC1",
            randcut=1,
            noplot=True,
            dfcheck=(20, 30),
            masspoints="on",
        )
    np.testing.assert_allclose(
        result.dots[["x", "fit"]],
        expected.data_plot[0].dots[["x", "fit"]],
        rtol=1e-9,
        atol=1e-11,
    )
    np.testing.assert_allclose(
        result.intervals[["x", "ci_lo", "ci_hi"]],
        expected.data_plot[0].ci[["x", "ci_l", "ci_r"]],
        rtol=1e-9,
        atol=1e-11,
    )
    assert result.metadata["actual_intervals"] == [1, 1]


@pytest.mark.parametrize("sizes", [(300, 300), (480, 60, 60)])
def test_adjusted_few_cluster_fallback_matches_upstream(sizes):
    from binsreg import binsreg

    rng = np.random.default_rng(93000)
    x, z = rng.normal(size=(2, 600))
    y = x * x + z + rng.normal(size=600)
    groups = np.repeat(np.arange(len(sizes)), sizes)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        result = binspect.binsreg(
            x=x, y=y, controls=z, cluster=groups, bins=5, at=[1.0]
        )
        expected = binsreg(
            y, x, w=z, cluster=groups, nbins=5, at=[1.0], ci=True, noplot=True
        )
    assert result.metadata["inference_status"] == "limited_support"
    assert result.metadata["actual_intervals"] == [0, 0]
    assert result.metadata["actual_bins"] == len(sizes)
    np.testing.assert_allclose(
        result.intervals[["ci_lo", "ci_hi"]],
        expected.data_plot[0].ci[["ci_l", "ci_r"]],
        rtol=1e-9,
        atol=1e-11,
    )


@pytest.mark.parametrize("count", ["dpi", 5])
def test_filtered_categorical_weighted_target_matches_upstream(count):
    from binsreg import binsreg

    rng = np.random.default_rng(93000)
    frame = pd.DataFrame(
        {
            "x": rng.uniform(-1, 1, 600),
            "z": rng.normal(size=600),
            "category": np.tile(["a", "b"], 300),
            "weight": rng.uniform(0.5, 2, 600),
        }
    )
    frame["y"] = 2 + frame.x + 2 * frame.x**2 + frame.z + rng.normal(size=600)
    frame.loc[0, "z"] = np.nan
    frame.loc[1, "weight"] = 0
    kept = frame.iloc[2:]
    encoded = pd.get_dummies(kept[["z", "category"]], drop_first=True, dtype=float)
    at = np.average(encoded, axis=0, weights=kept.weight)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        result = binspect.binsreg(
            frame,
            x="x",
            y="y",
            controls=["z", "category"],
            weights="weight",
            bins=count,
            ci=0.90,
        )
        expected = binsreg(
            y=kept.y.to_numpy(),
            x=kept.x.to_numpy(),
            w=encoded.to_numpy(),
            weights=kept.weight.to_numpy(),
            at=at,
            nbins=None if count == "dpi" else count,
            binsmethod="dpi",
            ci=True,
            dots=(0, 0),
            asyvar=False,
            vce="HC1",
            level=90,
            randcut=1,
            noplot=True,
            dfcheck=(20, 30),
            masspoints="on",
        )
    assert result.metadata["control_columns"] == ["z", "category_b"]
    assert result.metadata["n_obs"] == 598
    assert result.metadata["actual_bins"] == expected.options.nbins_by[0]
    assert result.metadata["selection_method"] == (
        "dpi" if count == "dpi" else "fixed_count"
    )
    np.testing.assert_allclose(result.metadata["at"], at, rtol=1e-9, atol=1e-11)
    np.testing.assert_allclose(
        result.dots[["x", "fit"]],
        expected.data_plot[0].dots[["x", "fit"]],
        rtol=1e-9,
        atol=1e-11,
    )
    np.testing.assert_allclose(
        result.intervals[["x", "ci_lo", "ci_hi"]],
        expected.data_plot[0].ci[["x", "ci_l", "ci_r"]],
        rtol=1e-9,
        atol=1e-11,
    )
