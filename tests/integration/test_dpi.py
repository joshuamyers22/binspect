"""Required checks against the binsreg version in the committed lockfile.

Import the optional dependency inside each test so the unit suite can collect
without it. Explicit integration runs fail (never skip) if it is unavailable.
"""

from __future__ import annotations

import json

import numpy as np
import pytest

import binspect
from binspect.exceptions import InvalidBinningError

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("method,spacing", [("quantile", "qs"), ("equal_width", "es")])
@pytest.mark.parametrize("discrete", [False, True])
def test_dpi_count_matches_real_selector(method, spacing, discrete):
    from binsreg import binsregselect

    rng = np.random.default_rng(7)
    x = rng.uniform(-2, 2, size=4000)
    if discrete:
        x = np.round(x, 2)
    y = np.sin(x) + rng.normal(scale=0.4, size=x.size)
    reference = binsregselect(
        x=x,
        y=y,
        bins=(0, 0),
        binsmethod="dpi",
        binspos=spacing,
        masspoints="on",
        vce="HC1",
        randcut=None,
    )
    assert np.isfinite(reference.nbinsdpi)
    assert reference.nbinsdpi != reference.nbinsrot_regul
    result = binspect.binscatter(x=x, y=y, bins="dpi", binning=method)
    assert result.binning.requested_bins == reference.nbinsdpi
    assert result.n_bins <= result.binning.requested_bins
    assert result.table["n"].sum() == len(x)
    assert result.bin_rule == "dpi"
    json.dumps(result.to_dict(), allow_nan=False)


def test_original_rot_regression():
    from binsreg import binsregselect

    rng = np.random.default_rng(7)
    x = rng.normal(size=4000)
    y = np.sin(x) + rng.normal(scale=0.4, size=x.size)
    reference = binsregselect(x=x, y=y, bins=(0, 0), binsmethod="dpi")
    result = binspect.binscatter(x=x, y=y, bins="dpi")
    assert reference.nbinsdpi != reference.nbinsrot_regul
    assert result.binning.requested_bins == reference.nbinsdpi


def test_too_few_mass_points_raise_instead_of_using_rot():
    # Import is deliberately required even though binspect imports it lazily.
    from binsreg import binsregselect

    rng = np.random.default_rng(8)
    x = np.repeat(np.arange(7.0), 100)
    y = x + rng.normal(size=x.size)
    with pytest.warns(UserWarning):
        reference = binsregselect(x=x, y=y)
    assert not np.isfinite(reference.nbinsdpi)
    with (
        pytest.warns(UserWarning),
        pytest.raises(InvalidBinningError, match="No ROT fallback"),
    ):
        binspect.binscatter(x=x, y=y, bins="dpi")
