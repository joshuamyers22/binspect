"""Pandas table projections for binscatter results."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from .results import BinscatterResult


def bin_table(result: BinscatterResult) -> pd.DataFrame:
    """Return per-bin estimates as a DataFrame."""
    estimates = result.estimates
    edges = result.binning.edges
    columns: dict[str, Any] = {
        "bin": np.arange(result.n_bins, dtype=int),
        "n": estimates.n,
        "x_lo": edges[:-1],
        "x_hi": edges[1:],
        "x_mean": estimates.x_mean,
        "y_mean": estimates.y_mean,
        "y_sd": estimates.y_sd,
        "se": estimates.se,
        "ci_lo": estimates.ci_lo,
        "ci_hi": estimates.ci_hi,
    }
    if estimates.n_clusters is not None:
        columns["n_clusters"] = estimates.n_clusters
    return pd.DataFrame(columns)


def decomposition_table(result: BinscatterResult) -> pd.DataFrame:
    """Return the variance decomposition as a one-row DataFrame."""
    return pd.DataFrame([result.decomposition.as_dict()])


def summary_frame(result: BinscatterResult) -> pd.DataFrame:
    """Return model and diagnostic statistics as a one-row DataFrame."""
    decomposition = result.decomposition
    return pd.DataFrame(
        [
            {
                "x": result.x_name,
                "y": result.y_name,
                "controls": ", ".join(result.controls) or None,
                "cluster": result.cluster,
                "se_type": result.estimates.se_type,
                "n_clusters": result.fit.n_clusters,
                "zero_weight": result.zero_weight,
                "n_obs": result.n_obs,
                "n_bins": result.n_bins,
                "binning": result.binning.method,
                "slope": result.fit.slope,
                "slope_se": result.fit.se_slope,
                "intercept": result.fit.intercept,
                "correlation": result.fit.r,
                "r_squared": decomposition.r_sq_linear,
                "eta_squared": decomposition.eta_sq,
                "lack_of_fit": decomposition.gap,
                "min_bin_n": decomposition.min_bin_n,
                "verdict": decomposition.verdict,
            }
        ]
    )
