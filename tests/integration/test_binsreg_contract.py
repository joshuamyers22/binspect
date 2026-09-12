"""Locked binsreg behavior informs scope; differing estimands are not conflated."""

from __future__ import annotations

import warnings

import numpy as np
import pytest

pytestmark = pytest.mark.integration


def sample():
    rng = np.random.default_rng(92001)
    x = rng.uniform(-1, 1, 600)
    control = rng.normal(size=600)
    y = 2 + x + x * x + control + rng.normal(size=600)
    return x, y, control


@pytest.mark.parametrize("sizes", [(300, 300), (480, 60, 60)])
def test_few_clusters_warn_and_change_requested_fit(sizes):
    from binsreg import binsreg

    x, y, _ = sample()
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        result = binsreg(
            y,
            x,
            nbins=5,
            ci=True,
            noplot=True,
            cluster=np.repeat(np.arange(len(sizes)), sizes),
        )
    messages = [str(item.message) for item in captured]
    assert any("Too small effective sample size for ci" in item for item in messages)
    assert any("ci=(0,0) used" in item for item in messages)
    # Upstream retains fallback constant-fit intervals; it does not certify them.
    assert len(result.data_plot[0].ci) == len(sizes)
    assert np.isfinite(result.data_plot[0].ci[["ci_l", "ci_r"]]).all().all()


def test_default_adjusted_uncertainty_includes_control_coefficients():
    from binsreg import binsreg

    x, y, control = sample()
    with pytest.warns(UserWarning, match="IMSE-optimal"):
        full = binsreg(y, x, w=control, at=[2.0], nbins=5, ci=True, noplot=True)
    with pytest.warns(UserWarning, match="IMSE-optimal"):
        omitted = binsreg(
            y, x, w=control, at=[2.0], nbins=5, ci=True, noplot=True, asyvar=True
        )
    first = full.data_plot[0].ci
    second = omitted.data_plot[0].ci
    np.testing.assert_allclose(
        (first.ci_l + first.ci_r) / 2,
        (second.ci_l + second.ci_r) / 2,
        rtol=1e-9,
        atol=1e-11,
    )
    assert not np.allclose(first.ci_r - first.ci_l, second.ci_r - second.ci_l)


def test_dpi_function_intervals_use_higher_degree_than_dots():
    from binsreg import binsreg

    x, y, _ = sample()
    result = binsreg(y, x, ci=True, noplot=True)
    np.testing.assert_array_equal(result.options.dots, [[0, 0]])
    np.testing.assert_array_equal(result.options.ci, [[1, 1]])
    assert result.data_plot[0].ci is not None
