"""JSON-compatible serialization for estimation results."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:  # pragma: no cover
    from .results import BinscatterResult


def serialize_result(result: BinscatterResult) -> dict[str, Any]:
    """Return the stable external representation of an estimation result."""
    return {
        "x": result.x_name,
        "y": result.y_name,
        "controls": list(result.controls),
        "cluster": result.cluster,
        "se_type": result.estimates.se_type,
        "n_clusters": result.fit.n_clusters,
        "zero_weight": result.zero_weight,
        "n_obs": result.n_obs,
        "binning": {
            "method": result.binning.method,
            "requested_bins": result.binning.requested_bins,
            "n_bins": result.n_bins,
            "edges": [json_value(value) for value in result.binning.edges],
        },
        "fit": {
            "slope": json_value(result.fit.slope),
            "intercept": json_value(result.fit.intercept),
            "slope_se": json_value(result.fit.se_slope),
            "correlation": json_value(result.fit.r),
            "r_squared": json_value(result.fit.r_sq),
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
            for row in result.table.to_dict(orient="records")
        ],
    }


def json_value(value: Any) -> Any:
    """Normalize NumPy, date, and nonfinite scalar values for strict JSON."""
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not np.isfinite(value):
        return None
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)
