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


def test_summary_mentions_the_verdict(concave):
    bs = binspect.binscatter(concave, y="y", x="x", bins=20)
    text = bs.summary()
    assert bs.verdict in text
    assert "Eta-squared" in text


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
