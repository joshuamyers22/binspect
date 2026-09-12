"""Matched independent references; optional imports fail only in integration runs."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from scipy import stats

import binspect

pytestmark = pytest.mark.integration


def sample():
    rng = np.random.default_rng(31001)
    n = 600
    z = rng.normal(size=n)
    category = np.where(np.arange(n) % 3 == 0, "b", "a")
    x = 0.5 * z + rng.normal(size=n)
    cluster = np.arange(n) // 10
    y = 1 + 1.7 * x - 0.4 * z + (category == "b") + rng.normal(size=n)
    y += rng.normal(size=60)[cluster]
    w = rng.uniform(0.5, 2.0, n)
    w[::20] = 0
    w[-10:] = 0  # an entire cluster disappears from positive-weight inference
    y[5] = np.nan
    return pd.DataFrame(
        {"x": x, "y": y, "z": z, "category": category, "w": w, "cluster": cluster}
    )


@pytest.mark.parametrize("weighted", [False, True])
@pytest.mark.parametrize("adjusted", [False, True])
@pytest.mark.parametrize("clustered", [False, True])
@pytest.mark.parametrize("zero_weight", ["retain", "drop"])
def test_slope_matches_full_design_statsmodels(
    weighted, adjusted, clustered, zero_weight
):
    from statsmodels.regression.linear_model import OLS, WLS

    frame = sample()
    result = binspect.binscatter(
        frame,
        x="x",
        y="y",
        controls=["z", "category"] if adjusted else None,
        weights="w" if weighted else None,
        cluster="cluster" if clustered else None,
        zero_weight=zero_weight,
        bins=5,
    )
    reference_sample = frame.dropna()
    if weighted:
        reference_sample = reference_sample.loc[reference_sample["w"] > 0]
    columns = [np.ones(len(reference_sample))]
    if adjusted:
        columns.extend([reference_sample["z"], reference_sample["category"] == "b"])
    columns.append(reference_sample["x"])
    design = np.column_stack(columns)
    assert np.linalg.matrix_rank(design) == design.shape[1]
    model = (
        WLS(reference_sample["y"], design, weights=reference_sample["w"])
        if weighted
        else OLS(reference_sample["y"], design)
    )
    reference = (
        model.fit(
            cov_type="cluster",
            cov_kwds={
                "groups": reference_sample["cluster"],
                "use_correction": True,
                "df_correction": True,
            },
            use_t=True,
        )
        if clustered
        else model.fit()
    )
    np.testing.assert_allclose(
        result.fit.slope, reference.params.iloc[-1], rtol=1e-9, atol=1e-11
    )
    np.testing.assert_allclose(
        result.fit.se_slope, reference.bse.iloc[-1], rtol=1e-9, atol=1e-11
    )
    assert result.fit.df_resid == reference.df_resid
    expected_df = (
        reference_sample["cluster"].nunique() - 1 if clustered else reference.df_resid
    )
    assert result.fit.inference_df == expected_df


@pytest.mark.parametrize("weighted", [False, True])
@pytest.mark.parametrize("adjusted", [False, True])
@pytest.mark.parametrize("clustered", [False, True])
def test_bin_uncertainty_matches_local_reference(weighted, adjusted, clustered):
    from statsmodels.regression.linear_model import OLS, WLS

    frame = sample().dropna()
    result = binspect.binscatter(
        frame,
        x="x",
        y="y",
        controls=["z", "category"] if adjusted else None,
        weights="w" if weighted else None,
        cluster="cluster" if clustered else None,
        bins=5,
    )
    weights = frame["w"].to_numpy() if weighted else np.ones(len(frame))
    for index in range(result.n_bins):
        keep = (result.binning.assignment == index) & (weights > 0)
        y = result.y[keep]
        w = weights[keep]
        model = (
            WLS(y, np.ones((len(y), 1)), weights=w)
            if weighted
            else OLS(y, np.ones((len(y), 1)))
        )
        if clustered:
            groups = frame["cluster"].to_numpy()[keep]
            reference = model.fit(
                cov_type="cluster",
                cov_kwds={"groups": groups, "use_correction": True},
                use_t=True,
            )
            expected_se = reference.bse[0]
            expected_df = np.unique(groups).size - 1
        elif weighted:
            # A reliability-weight mean is not classical inverse-variance WLS.
            expected_se = np.sqrt(
                np.cov(y, aweights=w, ddof=1) * np.sum(w**2) / np.sum(w) ** 2
            )
            expected_df = max(np.sum(w) ** 2 / np.sum(w**2) - 1, 1)
            reference = model.fit()
        else:
            reference = model.fit()
            expected_se = reference.bse[0]
            expected_df = len(y) - 1
        np.testing.assert_allclose(
            result.estimates.y_mean[index], reference.params[0], rtol=1e-9, atol=1e-11
        )
        np.testing.assert_allclose(
            result.estimates.se[index], expected_se, rtol=1e-9, atol=1e-11
        )
        assert result.estimates.ci_df[index] == pytest.approx(expected_df)
        expected_bounds = (
            reference.params[0]
            + np.array([-1, 1]) * stats.t.ppf(0.975, expected_df) * expected_se
        )
        np.testing.assert_allclose(
            [result.estimates.ci_lo[index], result.estimates.ci_hi[index]],
            expected_bounds,
            rtol=1e-9,
            atol=1e-11,
        )
