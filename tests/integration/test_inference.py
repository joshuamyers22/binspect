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
        ci=None if adjusted else 0.95,
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
    """Public unadjusted inference and historical adjusted-primitive arithmetic."""
    from statsmodels.regression.linear_model import OLS, WLS

    from binspect.core.estimate import estimate_bins

    frame = sample().dropna()
    result = binspect.binscatter(
        frame,
        x="x",
        y="y",
        controls=["z", "category"] if adjusted else None,
        weights="w" if weighted else None,
        cluster="cluster" if clustered else None,
        bins=5,
        ci=None if adjusted else 0.95,
    )
    weights = frame["w"].to_numpy() if weighted else np.ones(len(frame))
    estimates = result.estimates
    if adjusted:
        assert np.isnan(estimates.se).all()
        # Retain reference arithmetic for the withdrawn primitive, without
        # presenting it as supported adjusted-bin uncertainty in the public API.
        estimates = estimate_bins(
            result.x,
            result.y,
            result.binning.assignment,
            result.n_bins,
            weights=weights if weighted else None,
            clusters=frame["cluster"].to_numpy() if clustered else None,
        )
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
            estimates.y_mean[index], reference.params[0], rtol=1e-9, atol=1e-11
        )
        np.testing.assert_allclose(
            estimates.se[index], expected_se, rtol=1e-9, atol=1e-11
        )
        assert estimates.ci_df[index] == pytest.approx(expected_df)
        expected_bounds = (
            reference.params[0]
            + np.array([-1, 1]) * stats.t.ppf(0.975, expected_df) * expected_se
        )
        np.testing.assert_allclose(
            [estimates.ci_lo[index], estimates.ci_hi[index]],
            expected_bounds,
            rtol=1e-9,
            atol=1e-11,
        )


@pytest.mark.parametrize("scale", [1e-12, 1.0, 1e12])
@pytest.mark.parametrize("weighted", [False, True])
@pytest.mark.parametrize("clustered", [False, True])
def test_redundant_rescaled_controls_match_equivalent_full_rank_model(
    scale, weighted, clustered
):
    from statsmodels.regression.linear_model import OLS, WLS

    rng = np.random.default_rng(61004)
    z, noise = rng.normal(size=(2, 300))
    x = 0.5 * z + noise
    y = 2 + 1.7 * x - 0.4 * z + rng.normal(size=300)
    weights = rng.uniform(0.5, 2, 300)
    weights[::10] = 0
    groups = np.repeat(np.arange(30), 10)
    controls = np.column_stack([z * scale, -2 * z * scale, np.zeros(300)])
    result = binspect.binscatter(
        x=x,
        y=y,
        controls=controls,
        weights=weights if weighted else None,
        cluster=groups if clustered else None,
        bins=5,
        ci=None,
    )
    keep = weights > 0 if weighted else np.ones(300, dtype=bool)
    # Equivalent span in ordinary units; redundant columns must not inflate CR1 df.
    design = np.column_stack([np.ones(300), z, x])[keep]
    model = WLS(y[keep], design, weights=weights[keep]) if weighted else OLS(y, design)
    reference = (
        model.fit(
            cov_type="cluster",
            cov_kwds={"groups": groups[keep], "use_correction": True},
            use_t=True,
        )
        if clustered
        else model.fit()
    )
    np.testing.assert_allclose(
        [result.fit.slope, result.fit.se_slope],
        [reference.params[-1], reference.bse[-1]],
        rtol=1e-9,
        atol=1e-11,
    )
    assert result.fit.df_resid == reference.df_resid == np.count_nonzero(keep) - 3
    expected_df = np.unique(groups[keep]).size - 1 if clustered else reference.df_resid
    assert result.fit.inference_df == expected_df


@pytest.mark.parametrize("sizes", [(100, 100), (160, 20, 20)])
@pytest.mark.parametrize("weighted", [False, True])
def test_few_unbalanced_cluster_slope_arithmetic(sizes, weighted):
    """A matched CR1 calculation is not a small-cluster coverage guarantee."""
    from statsmodels.regression.linear_model import OLS, WLS

    rng = np.random.default_rng(61005)
    groups = np.repeat(np.arange(len(sizes)), sizes)
    x = rng.normal(size=200)
    y = 1 + 2 * x + rng.normal(size=200) + rng.normal(size=len(sizes))[groups]
    weights = rng.uniform(0.5, 2, 200)
    result = binspect.binscatter(
        x=x, y=y, cluster=groups, weights=weights if weighted else None, bins=5
    )
    design = np.column_stack([np.ones(200), x])
    model = WLS(y, design, weights=weights) if weighted else OLS(y, design)
    reference = model.fit(
        cov_type="cluster",
        cov_kwds={"groups": groups, "use_correction": True},
        use_t=True,
    )
    np.testing.assert_allclose(
        [result.fit.slope, result.fit.se_slope],
        [reference.params[-1], reference.bse[-1]],
        rtol=1e-9,
        atol=1e-11,
    )
    assert result.fit.df_resid == reference.df_resid
    assert result.fit.inference_df == len(sizes) - 1
