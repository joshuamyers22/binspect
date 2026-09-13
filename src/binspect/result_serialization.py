"""JSON-compatible serialization for estimation results."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:  # pragma: no cover
    from .results import BinscatterResult


def serialize_result(result: BinscatterResult) -> dict[str, Any]:
    """Return the stable external representation of an estimation result."""
    return {
        "schema_version": 1,
        "result_type": "binscatter",
        "sample": None
        if result.sample is None
        else result.sample.to_dict(result.n_obs),
        "design": {
            "intercept": True,
            "column_order": None
            if result.control_design is None
            else [
                {"role": "intercept"},
                *[
                    {"role": "control", "name": name}
                    for name in result.control_design.columns
                ],
                {"role": "x", "name": result.x_name},
            ],
            "controls": None
            if result.control_design is None
            else result.control_design.to_dict(),
            "coordinates": "fwl_residuals_with_sample_weighted_means"
            if result.adjusted
            else "original",
            "weight_interpretation": "unit"
            if result.weights is None
            else "reliability",
        },
        "x": result.x_name,
        "y": result.y_name,
        "controls": list(result.controls),
        "cluster": result.cluster,
        "se_type": result.estimates.se_type,
        "n_clusters": result.fit.n_clusters,
        "zero_weight": result.zero_weight,
        "inference": result.inference,
        "n_obs": result.n_obs,
        "n_positive": result.n_positive,
        "n_effective": json_value(result.n_effective),
        "binning": {
            "method": result.binning.method,
            "rule": result.bin_rule,
            "source_rule": result.binning.source_rule,
            "fallback": result.binning.fallback,
            "requested_bins": result.binning.requested_bins,
            "n_bins": result.n_bins,
            "edges": [json_value(value) for value in result.binning.edges],
            "partition_edges": [
                json_value(value) for value in result.binning.partition_edges
            ],
            "interval_ids": [
                json_value(value) for value in result.binning.interval_ids
            ],
        },
        "fit": {
            "slope": json_value(result.fit.slope),
            "intercept": json_value(result.fit.intercept),
            "slope_se": json_value(result.fit.se_slope),
            "correlation": json_value(result.fit.r),
            "r_squared": json_value(result.fit.r_sq),
            "se_type": result.fit.se_type,
            "df_resid": result.fit.df_resid,
            "inference_df": result.fit.inference_df,
        },
        "sd_line": {
            "slope": json_value(result.sd_line.slope),
            "intercept": json_value(result.sd_line.intercept),
        },
        "decomposition": {
            key: json_value(value)
            for key, value in result.decomposition.as_dict().items()
        },
        "bins": [
            {key: json_value(value) for key, value in row.items()}
            for row in result.table.to_dicts()
        ],
    }


def json_value(value: Any) -> Any:
    """Normalize NumPy, date, and nonfinite scalar values for strict JSON."""
    if isinstance(value, np.datetime64):
        return None if np.isnat(value) else str(value)
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not np.isfinite(value):
        return None
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise TypeError("JSON object keys must be strings.")
        return {key: json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(item) for item in value]
    raise TypeError("Unsupported value in JSON export.")
