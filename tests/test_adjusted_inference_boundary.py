"""Unvalidated bin uncertainty and unidentified slopes must not escape the API."""

from __future__ import annotations

import json

import numpy as np
import pytest

import binspect
from binspect.exceptions import InsufficientDataError


@pytest.mark.parametrize("weighted", [False, True])
@pytest.mark.parametrize("clustered", [False, True])
def test_adjusted_bins_withhold_uncertainty_but_keep_slope(weighted, clustered):
    rng = np.random.default_rng(61001)
    z = rng.normal(size=300)
    x = 0.5 * z + rng.normal(size=300)
    with pytest.warns(
        binspect.AdjustedInferenceWarning, match="adjusted-bin uncertainty"
    ):
        result = binspect.binscatter(
            x=x,
            y=2 * x + z + rng.normal(size=300),
            controls=z,
            bins=5,
            weights=rng.uniform(0.5, 2, 300) if weighted else None,
            cluster=np.repeat(np.arange(30), 10) if clustered else None,
        )
    assert np.isfinite(result.estimates.y_mean).all()
    assert np.isfinite(result.estimates.y_sd).all()
    assert np.isfinite(result.fit.se_slope)
    assert result.estimates.ci_level is None
    assert result.table[["se", "ci_lo", "ci_hi"]].isna().all().all()
    assert result.inference["bin_inference_status"] == "unavailable_after_adjustment"
    assert all(value is None for value in result.inference["bin_reference_df"])
    assert "unavailable" in result.summary()
    assert all(row["se"] is None for row in result.to_dict()["bins"])
    json.dumps(result.to_dict(), allow_nan=False)


@pytest.mark.parametrize("scale", [1.0, 1e-12, 1e12])
@pytest.mark.parametrize("weighted", [False, True])
def test_x_in_control_span_is_explicitly_rejected(scale, weighted):
    rng = np.random.default_rng(61002)
    z = rng.normal(size=100)
    with pytest.raises(InsufficientDataError, match="not identified"):
        binspect.binscatter(
            x=5 + 2 * z,
            y=rng.normal(size=100),
            controls=z * scale,
            bins=5,
            ci=None,
            weights=rng.uniform(0.5, 2, 100) if weighted else None,
        )


def test_zero_weight_rows_cannot_identify_controlled_x():
    z = np.linspace(-1, 1, 100)
    x = z.copy()
    x[-10:] += 1
    with pytest.raises(InsufficientDataError, match="not identified"):
        binspect.binscatter(
            x=x,
            y=z**2,
            controls=z,
            weights=np.r_[np.ones(90), np.zeros(10)],
            bins=5,
            ci=None,
        )


def test_numerically_unresolved_controlled_x_is_rejected():
    rng = np.random.default_rng(61006)
    z = rng.normal(size=100)
    with pytest.raises(InsufficientDataError, match="not identified"):
        binspect.binscatter(
            x=z + 1e-15 * rng.normal(size=100),
            y=rng.normal(size=100),
            controls=z,
            ci=None,
        )


def test_descriptive_adjustment_omits_warning_and_confidence_artists():
    import warnings

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rng = np.random.default_rng(61003)
    x, z = rng.normal(size=(2, 300))
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        result = binspect.binscatter(x=x, y=x + z, controls=z, bins=5, ci=None)
    assert not any("adjusted-bin uncertainty" in str(item.message) for item in captured)
    assert result.table["se"].isna().all()
    figure, ax = plt.subplots()
    result.plot(ax=ax, show=["ci"], annotate=None)
    assert not ax.collections
    plt.close(figure)
