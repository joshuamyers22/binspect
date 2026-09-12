"""Interpretation and actual covariance degrees of freedom survive presentation."""

from __future__ import annotations

import json

import numpy as np
import pytest

import binspect
from binspect.exceptions import BinCountWarning


@pytest.mark.parametrize("adjusted", [False, True])
@pytest.mark.parametrize("weighted", [False, True])
@pytest.mark.parametrize("clustered", [False, True])
def test_uncertainty_limits_and_df_are_exposed(adjusted, weighted, clustered):
    rng = np.random.default_rng(71)
    x = rng.normal(size=400)
    result = binspect.binscatter(
        x=x,
        y=x + rng.normal(size=400),
        bins=5,
        controls=rng.normal(size=400) if adjusted else None,
        weights=np.linspace(0.5, 2, 400) if weighted else None,
        cluster=np.repeat(np.arange(40), 10) if clustered else None,
    )
    metadata = result.inference
    assert metadata["interval_scope"] == (
        "unavailable_after_adjustment"
        if adjusted
        else "approximate_pointwise_conditional"
    )
    assert metadata["slope_df_resid"] == 400 - (3 if adjusted else 2)
    assert metadata["slope_reference_df"] == (
        39 if clustered else metadata["slope_df_resid"]
    )
    assert metadata["hc1_supported"] is False
    assert metadata["selection_uncertainty_included"] is False
    assert metadata["adjustment_uncertainty_included"] is (False if adjusted else None)
    assert any("fitted-control" in note for note in metadata["limitations"]) == adjusted
    assert any("reliability" in note for note in metadata["limitations"]) == (
        weighted and not adjusted
    )
    assert ("unavailable" if adjusted else "pointwise") in result.summary()
    assert result.summary_frame().loc[0, "slope_se_type"] == result.fit.se_type
    payload = result.to_dict()
    assert payload["inference"] == metadata
    assert payload["fit"]["df_resid"] == metadata["slope_df_resid"]
    json.dumps(payload, allow_nan=False)


def test_undefined_cluster_bin_df_serializes_as_null():
    with pytest.warns(BinCountWarning):
        result = binspect.binscatter(
            x=np.arange(8.0),
            y=np.arange(8.0) ** 2,
            bins=2,
            cluster=np.repeat([0, 1], 4),
        )
    assert result.inference["bin_reference_df"] == [None, None]
    json.dumps(result.to_dict(), allow_nan=False)


def test_disabled_intervals_retain_covariance_metadata():
    x = np.linspace(-1, 1, 100)
    result = binspect.binscatter(x=x, y=x**2, bins=5, ci=None)
    assert result.inference["ci_level"] is None
    assert len(result.inference["bin_reference_df"]) == result.n_bins
