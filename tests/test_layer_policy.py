from __future__ import annotations

import numpy as np
import pytest

from binspect.viz.layer_policy import deviation_baseline, rug_positions


def test_fit_deviation_baseline_uses_supplied_model() -> None:
    x = np.array([1.0, 2.0, 3.0])
    y = np.array([4.0, 6.0, 8.0])

    baseline = deviation_baseline(x, y, "fit", lambda values: 2.0 * values)

    assert np.array_equal(baseline, np.array([2.0, 4.0, 6.0]))


def test_smooth_deviation_baseline_does_not_consult_fit() -> None:
    x = np.array([1.0, 2.0, 3.0])
    y = np.array([4.0, 6.0, 8.0])

    def unexpected_fit(_values):
        raise AssertionError("smooth target consulted the fitted model")

    baseline = deviation_baseline(x, y, "smooth", unexpected_fit)

    assert baseline.shape == y.shape


def test_unknown_deviation_baseline_is_rejected() -> None:
    values = np.array([1.0, 2.0, 3.0])
    with pytest.raises(ValueError, match="target must be"):
        deviation_baseline(values, values, "vibes", lambda x: x)


def test_rug_positions_are_bounded_deterministic_and_unique() -> None:
    observations = np.arange(5_000.0)

    first = rug_positions(observations, 200)
    second = rug_positions(observations, 200)

    assert np.array_equal(first, second)
    assert first.size == 200
    assert np.unique(first).size == first.size


def test_small_rug_preserves_every_observation() -> None:
    observations = np.array([3.0, 1.0, 2.0])

    assert np.array_equal(rug_positions(observations, 10), observations)
