"""Public description of the uncertainty actually computed by the library."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .results import BinscatterResult


def inference_metadata(result: BinscatterResult) -> dict[str, Any]:
    limitations = [
        "Bin intervals are approximate, pointwise and conditional on "
        "the observed partition.",
        "Partition-selection uncertainty and simultaneous coverage are not provided.",
    ]
    if result.adjusted:
        limitations.append(
            "Bin uncertainty does not propagate fitted-control uncertainty."
        )
        limitations.append(
            "Adjusted bin intervals have no validated nominal "
            "population-coverage claim."
        )
    if result.weights is not None:
        limitations.append(
            "Independent weighted bin SEs use reliability variance and "
            "effective sample size; "
            "they are not classical inverse-variance WLS SEs."
        )
    if result.fit.se_type == "classical":
        limitations.append(
            "Classical slope SEs require the specified variance model and are not "
            "heteroskedasticity robust; HC1 is unsupported."
        )
    else:
        limitations.append(
            "CR1 assumes independent clusters; few-cluster coverage is limited."
        )
    degrees = result.estimates.ci_df
    return {
        "interval_scope": "approximate_pointwise_conditional",
        "ci_level": result.estimates.ci_level,
        "slope_covariance": result.fit.se_type,
        "slope_df_resid": result.fit.df_resid,
        "slope_reference_df": result.fit.inference_df,
        "bin_covariance": result.estimates.se_type,
        "bin_reference_df": None
        if degrees is None
        else [float(value) if math.isfinite(value) else None for value in degrees],
        "hc1_supported": False,
        "adjustment_uncertainty_included": False if result.adjusted else None,
        "selection_uncertainty_included": False,
        "limitations": limitations,
    }
