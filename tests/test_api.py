"""End-to-end behaviour of binscatter(), including the invariants a user can rely on."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import binspect
from binspect.exceptions import InsufficientDataError

EXPECTED_COLUMNS = [
    "bin",
    "n",
    "x_lo",
    "x_hi",
    "x_mean",
    "y_mean",
    "y_sd",
    "se",
    "ci_lo",
    "ci_hi",
]


def test_dataframe_interface(linear):
    bs = binspect.binscatter(linear, y="y", x="x", bins=20)
    assert bs.n_bins == 20
    assert bs.n_obs == len(linear)
    assert bs.x_name == "x" and bs.y_name == "y"


def test_array_interface_needs_no_dataframe(linear):
    bs = binspect.binscatter(
        x=linear["x"].to_numpy(), y=linear["y"].to_numpy(), bins=10
    )
    assert bs.n_bins == 10


def test_table_schema_and_shape(linear):
    table = binspect.binscatter(linear, y="y", x="x", bins=12).table
    assert list(table.columns) == EXPECTED_COLUMNS
    assert len(table) == 12
    assert table["n"].sum() == len(linear)
    assert table["x_mean"].is_monotonic_increasing


def test_decomposition_table_is_one_row(concave):
    d = binspect.binscatter(concave, y="y", x="x", bins=20).decomposition_table
    assert len(d) == 1
    assert d.loc[0, "eta_sq"] >= d.loc[0, "r_sq_linear"]


def test_summary_frame_is_one_row(linear):
    summary = binspect.binscatter(linear, y="y", x="x", bins=20).summary_frame()
    assert len(summary) == 1
    assert {"slope", "slope_se", "lack_of_fit", "verdict"} <= set(summary.columns)


def test_summary_mentions_the_verdict(concave):
    bs = binspect.binscatter(concave, y="y", x="x", bins=20)
    text = bs.summary()
    assert bs.verdict in text
    assert "Eta-squared" in text


def test_summary_uses_regression_results_conventions(linear):
    text = binspect.binscatter(linear, y="y", x="x", bins=20).summary()
    assert "Binscatter Results" in text
    assert "Dep. Variable:" in text
    assert "No. Observations:" in text
    assert "coef" in text and "std err" in text
    assert "Notes:" in text
    assert max(map(len, text.splitlines())) <= 68


def test_results_are_permutation_invariant(linear):
    order = np.random.default_rng(1).permutation(len(linear))
    a = binspect.binscatter(linear, y="y", x="x", bins=15)
    b = binspect.binscatter(linear.iloc[order], y="y", x="x", bins=15)
    np.testing.assert_allclose(a.table["y_mean"], b.table["y_mean"], rtol=1e-12)
    assert a.fit.slope == pytest.approx(b.fit.slope, rel=1e-12)


def test_affine_rescaling_is_equivariant(linear):
    base = binspect.binscatter(linear, y="y", x="x", bins=15)
    scaled_frame = pd.DataFrame(
        {"x": 3.0 * linear["x"] + 7.0, "y": 2.0 * linear["y"] - 4.0}
    )
    scaled = binspect.binscatter(scaled_frame, y="y", x="x", bins=15)
    assert scaled.fit.slope == pytest.approx(base.fit.slope * 2.0 / 3.0, rel=1e-10)
    assert scaled.decomposition.eta_sq == pytest.approx(
        base.decomposition.eta_sq, rel=1e-10
    )


def test_binning_to_bin_means_reproduces_the_saturated_fit(concave):
    bs = binspect.binscatter(concave, y="y", x="x", bins=20)
    grouped = pd.Series(bs.y).groupby(bs.binning.assignment).mean().to_numpy()
    np.testing.assert_allclose(bs.table["y_mean"], grouped, rtol=1e-12)


def test_weighted_run_differs_from_unweighted(weighted):
    plain = binspect.binscatter(weighted, y="y", x="x", bins=15)
    wtd = binspect.binscatter(weighted, y="y", x="x", bins=15, weights="w")
    assert wtd.fit.slope != pytest.approx(plain.fit.slope, rel=1e-6)


def test_constant_weights_match_unweighted(linear):
    frame = linear.assign(w=1.0)
    plain = binspect.binscatter(frame, y="y", x="x", bins=15)
    wtd = binspect.binscatter(frame, y="y", x="x", bins=15, weights="w")
    np.testing.assert_allclose(plain.table["y_mean"], wtd.table["y_mean"], rtol=1e-12)


def test_clustered_inference_is_exposed_in_results(linear):
    frame = linear.assign(firm=np.arange(len(linear)) // 10)
    result = binspect.binscatter(frame, y="y", x="x", bins=10, cluster="firm")
    assert result.cluster == "firm"
    assert result.fit.se_type == "cluster"
    assert result.fit.n_clusters == frame["firm"].nunique()
    assert result.estimates.se_type == "cluster"
    assert "n_clusters" in result.table
    assert result.summary_frame().loc[0, "se_type"] == "cluster"
    assert result.to_dict()["cluster"] == "firm"
    assert "CR1 cluster-robust" in result.summary()


def test_missing_cluster_rows_follow_dropna_policy(linear):
    cluster = pd.Series(np.arange(len(linear)) // 5, dtype="Int64")
    cluster.iloc[:7] = pd.NA
    result = binspect.binscatter(linear, x="x", y="y", cluster=cluster, bins=10)
    assert result.n_obs == len(linear) - 7
    with pytest.raises(ValueError, match="non-finite"):
        binspect.binscatter(linear, x="x", y="y", cluster=cluster, dropna=False)


def test_clustered_slope_with_controls_matches_full_model_sandwich():
    rng = np.random.default_rng(8128)
    n = 1_200
    clusters = np.arange(n) // 6
    control = rng.normal(size=n)
    x = control + rng.normal(size=n)
    cluster_shock = rng.normal(size=clusters.max() + 1)[clusters]
    y = 2.0 * x - control + cluster_shock + rng.normal(scale=0.3, size=n)
    result = binspect.binscatter(x=x, y=y, controls=control, cluster=clusters, bins=12)

    design = np.column_stack((np.ones(n), control, x))
    beta = np.linalg.lstsq(design, y, rcond=None)[0]
    residual = y - design @ beta
    bread = np.linalg.inv(design.T @ design)
    meat = np.zeros((3, 3))
    for label in np.unique(clusters):
        score = design[clusters == label].T @ residual[clusters == label]
        meat += np.outer(score, score)
    count = np.unique(clusters).size
    correction = (count / (count - 1.0)) * ((n - 1.0) / (n - design.shape[1]))
    covariance = correction * bread @ meat @ bread
    assert result.fit.se_slope == pytest.approx(np.sqrt(covariance[2, 2]), rel=1e-12)


def test_zero_weight_clusters_do_not_count(linear):
    clusters = np.zeros(len(linear), dtype=int)
    clusters[-10:] = 1
    weights = np.ones(len(linear))
    weights[-10:] = 0.0
    with pytest.raises(InsufficientDataError, match="positive-weight clusters"):
        binspect.binscatter(
            linear,
            x="x",
            y="y",
            weights=weights,
            cluster=clusters,
            bins=10,
        )


def test_zero_weight_drop_is_equivalent_to_omitting_rows(linear):
    frame = linear.iloc[:100].copy().assign(weight=1.0)
    frame.loc[frame.index[-20:], "weight"] = 0.0
    dropped = binspect.binscatter(
        frame,
        x="x",
        y="y",
        weights="weight",
        zero_weight="drop",
        bins=8,
    )
    omitted_frame = frame.loc[frame["weight"] > 0]
    omitted = binspect.binscatter(omitted_frame, x="x", y="y", weights="weight", bins=8)
    assert dropped.n_obs == len(omitted_frame)
    assert dropped.zero_weight == "drop"
    np.testing.assert_allclose(dropped.table, omitted.table, rtol=1e-12)
    assert dropped.fit.se_slope == pytest.approx(omitted.fit.se_slope, rel=1e-12)


def test_zero_weight_retain_keeps_descriptive_rows(linear):
    frame = linear.iloc[:100].copy().assign(weight=1.0)
    frame.loc[frame.index[-20:], "weight"] = 0.0
    result = binspect.binscatter(
        frame,
        x="x",
        y="y",
        weights="weight",
        zero_weight="retain",
        bins=8,
    )
    assert result.n_obs == len(frame)
    assert result.table["n"].sum() == len(frame)
    assert result.summary_frame().loc[0, "zero_weight"] == "retain"
    assert result.to_dict()["zero_weight"] == "retain"


def test_invalid_zero_weight_policy_is_refused(linear):
    with pytest.raises(ValueError, match="zero_weight must be"):
        binspect.binscatter(
            linear,
            x="x",
            y="y",
            weights=np.ones(len(linear)),
            zero_weight="ignore",  # type: ignore[arg-type]
        )


def test_zero_weight_controlled_se_matches_omitted_rows():
    rng = np.random.default_rng(103)
    n = 120
    control = rng.normal(size=n)
    x = control + rng.normal(size=n)
    y = 2.0 * x - control + rng.normal(size=n)
    weights = np.r_[np.ones(100), np.zeros(20)]
    weighted = binspect.binscatter(
        x=x,
        y=y,
        controls=control,
        weights=weights,
        zero_weight="retain",
        bins=8,
    )
    omitted = binspect.binscatter(
        x=x[:100],
        y=y[:100],
        controls=control[:100],
        weights=weights[:100],
        bins=8,
    )
    assert weighted.fit.se_slope == pytest.approx(omitted.fit.se_slope, rel=1e-12)


def test_bin_rules_resolve_to_sensible_counts(linear):
    for rule in ("auto", "sturges", "iqr"):
        bs = binspect.binscatter(linear, y="y", x="x", bins=rule)
        assert 5 <= bs.n_bins <= 40


def test_custom_edges_are_honoured(linear):
    edges = np.array([-4.0, -1.0, 0.0, 1.0, 4.0])
    bs = binspect.binscatter(linear, y="y", x="x", bins=edges)
    assert bs.n_bins == 4
    assert bs.binning.method == "custom"


def test_nan_rows_are_dropped(linear):
    frame = linear.copy()
    frame.loc[frame.index[:50], "y"] = np.nan
    bs = binspect.binscatter(frame, y="y", x="x", bins=10)
    assert bs.n_obs == len(frame) - 50


def test_dropna_false_raises_on_nan(linear):
    frame = linear.copy()
    frame.loc[frame.index[0], "y"] = np.nan
    with pytest.raises(ValueError, match="non-finite"):
        binspect.binscatter(frame, y="y", x="x", bins=10, dropna=False)


def test_missing_column_names_the_alternatives(linear):
    with pytest.raises(KeyError, match="available"):
        binspect.binscatter(linear, y="nope", x="x")


def test_mismatched_lengths_are_refused():
    with pytest.raises(ValueError, match="same shape"):
        binspect.binscatter(x=np.arange(10.0), y=np.arange(9.0))


def test_multidimensional_input_is_refused():
    with pytest.raises(ValueError, match="one-dimensional"):
        binspect.binscatter(x=np.ones((4, 2)), y=np.ones((4, 2)))


def test_too_few_observations_are_refused():
    with pytest.raises(InsufficientDataError):
        binspect.binscatter(x=np.arange(3.0), y=np.arange(3.0))


def test_all_zero_weights_are_refused(linear):
    with pytest.raises(ValueError, match="at least one positive"):
        binspect.binscatter(
            linear,
            x="x",
            y="y",
            bins=10,
            weights=np.zeros(len(linear)),
        )


def test_bin_with_zero_total_weight_is_refused():
    x = np.arange(100.0)
    weights = np.ones(100)
    weights[:50] = 0.0
    with pytest.raises(ValueError, match="positive total weight"):
        binspect.binscatter(x=x, y=x, bins=2, weights=weights)


def test_residuals_from_fit_sum_to_about_zero(linear):
    bs = binspect.binscatter(linear, y="y", x="x", bins=20)
    resid = bs.residuals_from_fit()
    assert abs(resid.mean()) < 0.05 * bs.y.std()


def test_controls_match_the_full_ols_coefficient():
    rng = np.random.default_rng(2718)
    control = rng.normal(size=2_000)
    x = 1.5 * control + rng.normal(size=control.size)
    y = 4.0 * x - 2.0 * control + rng.normal(scale=0.3, size=control.size)
    frame = pd.DataFrame({"x": x, "y": y, "control": control})

    result = binspect.binscatter(frame, x="x", y="y", controls="control", bins=15)
    design = np.column_stack((np.ones(x.size), x, control))
    expected = np.linalg.lstsq(design, y, rcond=None)[0][1]
    coefficient = np.linalg.lstsq(design, y, rcond=None)[0]
    residual = y - design @ coefficient
    covariance = np.linalg.inv(design.T @ design) * (
        residual @ residual / (x.size - np.linalg.matrix_rank(design))
    )

    assert result.fit.slope == pytest.approx(expected, rel=1e-12)
    assert result.fit.se_slope == pytest.approx(np.sqrt(covariance[1, 1]), rel=1e-12)
    assert result.controls == ("control",)
    assert result.adjusted
    assert result.x.mean() == pytest.approx(x.mean(), rel=1e-12)
    assert result.y.mean() == pytest.approx(y.mean(), rel=1e-12)


def test_categorical_controls_match_explicit_indicators():
    rng = np.random.default_rng(314)
    group = np.resize(np.array(["a", "b", "c"]), 900)
    effect = pd.Series(group).map({"a": -2.0, "b": 1.0, "c": 4.0}).to_numpy()
    x = effect + rng.normal(size=group.size)
    y = 2.5 * x + effect + rng.normal(scale=0.4, size=group.size)
    frame = pd.DataFrame({"x": x, "y": y, "group": group})
    indicators = pd.get_dummies(frame["group"], drop_first=True, dtype=float)

    categorical = binspect.binscatter(frame, x="x", y="y", controls="group")
    explicit = binspect.binscatter(x=x, y=y, controls=indicators)

    assert categorical.fit.slope == pytest.approx(explicit.fit.slope, rel=1e-12)


def test_missing_control_rows_follow_dropna_policy(linear):
    frame = linear.assign(control=np.arange(len(linear), dtype=float))
    frame.loc[frame.index[:7], "control"] = np.nan
    result = binspect.binscatter(frame, x="x", y="y", controls="control")
    assert result.n_obs == len(frame) - 7
    with pytest.raises(ValueError, match="non-finite"):
        binspect.binscatter(frame, x="x", y="y", controls="control", dropna=False)


def test_control_metadata_is_exported_and_labels_are_explicit(linear):
    frame = linear.assign(control=np.linspace(-1.0, 1.0, len(linear)))
    result = binspect.binscatter(frame, x="x", y="y", controls=["control"])
    assert result.summary_frame().loc[0, "controls"] == "control"
    assert result.to_dict()["controls"] == ["control"]
    axis = result.plot(annotate=None)
    assert axis.get_xlabel() == "x (adjusted)"
    assert axis.get_ylabel() == "y (adjusted)"
    summary = result.summary()
    assert "Controls:" in summary and "Frisch-Waugh-Lovell" in summary
    assert max(map(len, summary.splitlines())) <= 68


def test_weighted_controls_match_full_wls():
    rng = np.random.default_rng(1618)
    control = rng.normal(size=1_200)
    x = control + rng.normal(size=control.size)
    y = 1.8 * x - control + rng.normal(size=control.size)
    weights = rng.uniform(0.2, 3.0, size=control.size)
    result = binspect.binscatter(x=x, y=y, controls=control, weights=weights, bins=12)
    design = np.column_stack((np.ones(x.size), x, control))
    root_weight = np.sqrt(weights)
    expected = np.linalg.lstsq(
        design * root_weight[:, None], y * root_weight, rcond=None
    )[0][1]
    assert result.fit.slope == pytest.approx(expected, rel=1e-12)


def test_nonfinite_numeric_controls_follow_dropna_policy(linear):
    controls = np.linspace(-1.0, 1.0, len(linear))
    controls[:5] = np.inf
    result = binspect.binscatter(linear, x="x", y="y", controls=controls, bins=10)
    assert result.n_obs == len(linear) - 5
    with pytest.raises(ValueError, match="non-finite"):
        binspect.binscatter(linear, x="x", y="y", controls=controls, dropna=False)


@pytest.mark.parametrize("controls", [[], np.empty((4_000, 0))])
def test_empty_controls_are_refused(linear, controls):
    with pytest.raises(ValueError, match="at least one"):
        binspect.binscatter(linear, x="x", y="y", controls=controls)


def test_duplicate_named_controls_are_refused(linear):
    with pytest.raises(ValueError, match="unique"):
        binspect.binscatter(linear.assign(z=1.0), x="x", y="y", controls=["z", "z"])
