"""Pandas table projections for binscatter results."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd

if TYPE_CHECKING:
    from .results import BinscatterResult


def bin_table(result: BinscatterResult) -> pd.DataFrame:
    """Return occupied intervals with original IDs and bounds as a DataFrame."""
    estimates = result.estimates
    edges = result.binning.partition_edges
    interval_ids = result.binning.interval_ids
    columns: dict[str, Any] = {
        "bin": interval_ids,
        "n": estimates.n,
        "x_lo": edges[interval_ids],
        "x_hi": edges[interval_ids + 1],
        "x_mean": estimates.x_mean,
        "y_mean": estimates.y_mean,
        "y_sd": estimates.y_sd,
        "se": estimates.se,
        "ci_lo": estimates.ci_lo,
        "ci_hi": estimates.ci_hi,
    }
    if estimates.n_clusters is not None:
        columns["n_clusters"] = estimates.n_clusters
    if estimates.n_positive is not None:
        columns["n_positive"] = estimates.n_positive
    if estimates.n_effective is not None:
        columns["n_effective"] = estimates.n_effective
    return pd.DataFrame(columns, copy=True)


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
                "slope_se_type": result.fit.se_type,
                "slope_df_resid": result.fit.df_resid,
                "slope_reference_df": result.fit.inference_df,
                "interval_scope": result.inference["interval_scope"],
                "n_clusters": result.fit.n_clusters,
                "zero_weight": result.zero_weight,
                "n_obs": result.n_obs,
                "n_positive": result.n_positive,
                "n_effective": result.n_effective,
                "n_bins": result.n_bins,
                "binning": result.binning.method,
                "bin_rule": result.bin_rule,
                "bin_source_rule": result.binning.source_rule,
                "bin_fallback": result.binning.fallback,
                "requested_bins": result.binning.requested_bins,
                "slope": result.fit.slope,
                "slope_se": result.fit.se_slope,
                "intercept": result.fit.intercept,
                "correlation": result.fit.r,
                "r_squared": decomposition.r_sq_linear,
                "eta_squared": decomposition.eta_sq,
                "lack_of_fit": decomposition.gap,
                "min_bin_n": decomposition.min_bin_n,
                "verdict": decomposition.verdict,
                **{
                    key: value
                    for key, value in decomposition.as_dict().items()
                    if key
                    in {
                        "min_bin_positive_n",
                        "min_bin_effective_n",
                        "min_bin_clusters",
                        "verdict_reason",
                        "diagnostics_enabled",
                        "gap_threshold",
                        "min_bin_effective_n_threshold",
                        "min_bin_clusters_threshold",
                    }
                },
            }
        ]
    )
