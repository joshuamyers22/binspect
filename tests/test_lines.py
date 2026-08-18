"""The OLS line is the SD line flattened by r. That is an identity, so it is
tested as an equality, not a tolerance."""

from __future__ import annotations

import numpy as np
import pytest

from binspect.core.lines import fit_ols, fit_sd_line


def test_ols_slope_is_sd_slope_shrunk_by_r(linear):
    x, y = linear["x"].to_numpy(), linear["y"].to_numpy()
    fit = fit_ols(x, y)
    sd = fit_sd_line(x, y)
    assert fit.slope == pytest.approx(fit.r * sd.slope, rel=1e-12)


def test_sd_line_is_steeper(linear, concave, negative):
    for frame in (linear, concave, negative):
        x, y = frame["x"].to_numpy(), frame["y"].to_numpy()
        fit = fit_ols(x, y)
        sd = fit_sd_line(x, y)
        assert abs(sd.slope) >= abs(fit.slope)


def test_both_lines_pass_through_the_point_of_averages(linear):
    x, y = linear["x"].to_numpy(), linear["y"].to_numpy()
    x_bar, y_bar = x.mean(), y.mean()
    assert fit_ols(x, y).predict(x_bar) == pytest.approx(y_bar)
    assert fit_sd_line(x, y).predict(x_bar) == pytest.approx(y_bar)


def test_sd_line_is_the_geometric_mean_of_the_two_regressions(linear):
    x, y = linear["x"].to_numpy(), linear["y"].to_numpy()
    slope_y_on_x = fit_ols(x, y).slope
    slope_x_on_y = fit_ols(y, x).slope  # dy/dx implied is 1 / this
    geometric_mean = np.sqrt(slope_y_on_x / slope_x_on_y)
    assert fit_sd_line(x, y).slope == pytest.approx(geometric_mean, rel=1e-10)


def test_signs_follow_the_correlation(negative):
    x, y = negative["x"].to_numpy(), negative["y"].to_numpy()
    fit = fit_ols(x, y)
    sd = fit_sd_line(x, y)
    assert fit.slope < 0
    assert sd.slope < 0


def test_slope_matches_lstsq(linear):
    x, y = linear["x"].to_numpy(), linear["y"].to_numpy()
    design = np.column_stack([np.ones_like(x), x])
    coefs, *_ = np.linalg.lstsq(design, y, rcond=None)
    fit = fit_ols(x, y)
    assert fit.intercept == pytest.approx(coefs[0], rel=1e-10)
    assert fit.slope == pytest.approx(coefs[1], rel=1e-10)


def test_r_squared_is_r_squared(linear):
    x, y = linear["x"].to_numpy(), linear["y"].to_numpy()
    fit = fit_ols(x, y)
    assert fit.r_sq == pytest.approx(np.corrcoef(x, y)[0, 1] ** 2, rel=1e-12)


def test_affine_equivariance(linear):
    x, y = linear["x"].to_numpy(), linear["y"].to_numpy()
    base = fit_ols(x, y)
    scaled = fit_ols(3.0 * x + 7.0, 2.0 * y - 4.0)
    assert scaled.slope == pytest.approx(base.slope * 2.0 / 3.0, rel=1e-10)
    assert scaled.r_sq == pytest.approx(base.r_sq, rel=1e-10)


def test_zero_variance_x_is_refused():
    with pytest.raises(ValueError, match="zero variance"):
        fit_ols(np.ones(50), np.arange(50.0))
