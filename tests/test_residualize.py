"""Frisch--Waugh--Lovell projection contracts."""

from __future__ import annotations

import numpy as np

from binspect.core.residualize import residualize


def test_residualization_retains_the_original_mean():
    control = np.linspace(-2.0, 2.0, 100)
    values = 4.0 + 3.0 * control + np.sin(control)
    design = np.column_stack((np.ones(control.size), control))
    adjusted = residualize(values, design)
    np.testing.assert_allclose(adjusted.mean(), values.mean(), rtol=1e-14)


def test_weighted_residuals_are_orthogonal_to_controls():
    control = np.linspace(-1.0, 1.0, 80)
    values = control**2 + 2.0 * control
    weights = np.linspace(0.2, 3.0, control.size)
    design = np.column_stack((np.ones(control.size), control))
    adjusted = residualize(values, design, weights=weights)
    residual = adjusted - np.average(values, weights=weights)
    np.testing.assert_allclose(design.T @ (weights * residual), 0.0, atol=1e-12)


def test_redundant_constant_is_harmless():
    values = np.linspace(-3.0, 4.0, 50) ** 2
    one_constant = np.ones((values.size, 1))
    two_constants = np.ones((values.size, 2))
    np.testing.assert_allclose(
        residualize(values, one_constant),
        residualize(values, two_constants),
        rtol=1e-14,
        atol=1e-14,
    )
