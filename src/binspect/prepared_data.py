"""Validation and preparation of inputs for binned-scatter estimation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike

from .core.residualize import residualize
from .exceptions import InsufficientDataError
from .input_data import column, control_frame, encode_controls, labels
from .types import FloatArray, ZeroWeightPolicy


@dataclass(frozen=True, slots=True)
class PreparedData:
    x: FloatArray
    y: FloatArray
    weights: FloatArray | None
    clusters: np.ndarray[Any, np.dtype[Any]] | None
    x_name: str
    y_name: str
    controls: tuple[str, ...]
    cluster_name: str | None
    dof_resid: int | None


def prepare_data(
    data: pd.DataFrame | Mapping[str, Any] | None,
    y: str | ArrayLike | None,
    x: str | ArrayLike | None,
    *,
    weights: str | ArrayLike | None,
    zero_weight: ZeroWeightPolicy,
    controls: str | Sequence[str] | ArrayLike | None,
    cluster: str | ArrayLike | None,
    dropna: bool,
) -> PreparedData:
    """Normalize, filter, validate, and residualize estimator inputs."""
    y_arr, y_name = column(data, y, "y")
    x_arr, x_name = column(data, x, "x")

    if zero_weight not in ("retain", "drop"):
        raise ValueError(
            f"zero_weight must be either 'retain' or 'drop', got {zero_weight!r}."
        )
    if x_arr.shape != y_arr.shape:
        raise ValueError(
            f"x and y must have the same shape, got {x_arr.shape} and {y_arr.shape}."
        )

    w_arr: FloatArray | None = None
    if weights is not None:
        w_arr, _ = column(data, weights, "weights")
        if w_arr.shape != y_arr.shape:
            raise ValueError("weights must have the same shape as x and y.")
        if np.any(w_arr < 0):
            raise ValueError("weights must be non-negative.")

    controls_frame: pd.DataFrame | None = None
    control_names: tuple[str, ...] = ()
    if controls is not None:
        controls_frame, control_names = control_frame(data, controls, y_arr.size)

    cluster_arr: np.ndarray[Any, np.dtype[Any]] | None = None
    cluster_name: str | None = None
    if cluster is not None:
        cluster_arr, cluster_name = labels(data, cluster, "cluster")
        if cluster_arr.shape != y_arr.shape:
            raise ValueError("cluster must have the same shape as x and y.")

    finite = np.isfinite(x_arr) & np.isfinite(y_arr)
    if w_arr is not None:
        finite &= np.isfinite(w_arr)
    if controls_frame is not None:
        finite &= ~controls_frame.isna().any(axis=1).to_numpy()
        numeric_controls = controls_frame.select_dtypes(include="number")
        if numeric_controls.shape[1]:
            finite &= np.isfinite(numeric_controls.to_numpy(dtype=float)).all(axis=1)
    if cluster_arr is not None:
        finite &= np.asarray(pd.notna(cluster_arr), dtype=bool)

    if not finite.all():
        if not dropna:
            raise ValueError(
                f"{int((~finite).sum())} row(s) contain non-finite values; "
                "pass dropna=True to drop them."
            )
        x_arr, y_arr = x_arr[finite], y_arr[finite]
        if w_arr is not None:
            w_arr = w_arr[finite]
        if controls_frame is not None:
            controls_frame = controls_frame.loc[finite].reset_index(drop=True)
        if cluster_arr is not None:
            cluster_arr = cluster_arr[finite]

    if w_arr is not None and not np.any(w_arr > 0):
        raise ValueError("weights must contain at least one positive value.")
    if w_arr is not None and zero_weight == "drop":
        positive = w_arr > 0
        x_arr, y_arr, w_arr = x_arr[positive], y_arr[positive], w_arr[positive]
        if controls_frame is not None:
            controls_frame = controls_frame.loc[positive].reset_index(drop=True)
        if cluster_arr is not None:
            cluster_arr = cluster_arr[positive]

    if y_arr.size < 4:
        raise InsufficientDataError(
            f"need at least 4 usable observations, got {y_arr.size}."
        )

    cluster_active = np.ones(y_arr.size, dtype=bool) if w_arr is None else w_arr > 0
    if cluster_arr is not None and pd.unique(cluster_arr[cluster_active]).size < 2:
        raise InsufficientDataError(
            "cluster-robust inference requires at least 2 positive-weight clusters."
        )

    dof_resid: int | None = None
    if controls_frame is not None:
        control_matrix = encode_controls(controls_frame)
        if not np.isfinite(control_matrix).all():
            raise ValueError("controls contain non-finite numeric values.")
        full_design = np.column_stack((control_matrix, x_arr))
        if w_arr is not None:
            full_design = full_design * np.sqrt(w_arr)[:, None]
        effective_n = y_arr.size if w_arr is None else int(np.count_nonzero(w_arr > 0))
        dof_resid = effective_n - int(np.linalg.matrix_rank(full_design))
        if dof_resid < 1:
            raise InsufficientDataError(
                "controls leave no residual degrees of freedom."
            )
        x_arr = residualize(x_arr, control_matrix, weights=w_arr)
        y_arr = residualize(y_arr, control_matrix, weights=w_arr)

    return PreparedData(
        x_arr,
        y_arr,
        w_arr,
        cluster_arr,
        x_name,
        y_name,
        control_names,
        cluster_name,
        dof_resid,
    )
