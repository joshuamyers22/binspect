"""Fixtures.

Six data-generating processes, all seeded. The concave one is the fixture that
catches regressions in the eta-squared/gap machinery: if the audit arithmetic breaks,
the linear DGP often still looks fine and only this one goes wrong.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

N = 4_000
SEED = 20260818


@pytest.fixture(scope="session")
def rng() -> np.random.Generator:
    return np.random.default_rng(SEED)


@pytest.fixture(scope="session")
def linear() -> pd.DataFrame:
    """E[y|x] is exactly linear. Here eta^2 and R^2 should nearly coincide."""
    rng = np.random.default_rng(SEED)
    x = rng.normal(size=N)
    y = 1.5 + 0.8 * x + rng.normal(scale=1.0, size=N)
    return pd.DataFrame({"x": x, "y": y})


@pytest.fixture(scope="session")
def concave() -> pd.DataFrame:
    """A pronounced bend. The gap should be large and the verdict 'curvature'."""
    rng = np.random.default_rng(SEED + 1)
    x = rng.normal(size=N)
    y = 2.0 * np.tanh(1.5 * x) + rng.normal(scale=0.4, size=N)
    return pd.DataFrame({"x": x, "y": y})


@pytest.fixture(scope="session")
def heteroskedastic() -> pd.DataFrame:
    """Fanning residual spread; bin SDs should rise monotonically with x."""
    rng = np.random.default_rng(SEED + 2)
    x = rng.uniform(0.0, 10.0, size=N)
    y = 0.5 * x + rng.normal(scale=0.3 + 0.4 * x, size=N)
    return pd.DataFrame({"x": x, "y": y})


@pytest.fixture(scope="session")
def negative() -> pd.DataFrame:
    """Negative correlation, to keep sign conventions honest."""
    rng = np.random.default_rng(SEED + 3)
    x = rng.normal(size=N)
    y = -1.2 * x + rng.normal(scale=1.5, size=N)
    return pd.DataFrame({"x": x, "y": y})


@pytest.fixture(scope="session")
def weighted() -> pd.DataFrame:
    """Carries a non-degenerate weight column."""
    rng = np.random.default_rng(SEED + 4)
    x = rng.normal(size=N)
    y = 0.6 * x + rng.normal(scale=1.0, size=N)
    w = rng.uniform(0.2, 3.0, size=N)
    return pd.DataFrame({"x": x, "y": y, "w": w})


@pytest.fixture(scope="session")
def discrete() -> pd.DataFrame:
    """Only seven distinct x values --- the quantile-binning edge case."""
    rng = np.random.default_rng(SEED + 5)
    x = rng.integers(0, 7, size=N).astype(float)
    y = 0.4 * x + rng.normal(scale=1.0, size=N)
    return pd.DataFrame({"x": x, "y": y})


@pytest.fixture(scope="session")
def tiny() -> pd.DataFrame:
    """Small enough to trigger sparse-bin warnings."""
    rng = np.random.default_rng(SEED + 6)
    x = rng.normal(size=40)
    y = x + rng.normal(size=40)
    return pd.DataFrame({"x": x, "y": y})


def saturated_fitted_values(y: np.ndarray, assignment: np.ndarray, n_bins: int):
    """Fitted values of OLS(y ~ C(bin)) computed independently, via lstsq.

    Deliberately built from a dummy matrix rather than from group means, so the
    equivalence test is not comparing an implementation against itself.
    """
    design = np.zeros((y.size, n_bins), dtype=float)
    design[np.arange(y.size), assignment] = 1.0
    coefs, *_ = np.linalg.lstsq(design, y, rcond=None)
    return coefs
