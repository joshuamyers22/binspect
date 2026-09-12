"""Original-coordinate inputs for the optional binsreg method."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike

from .core.residualize import scaled_design
from .exceptions import InsufficientDataError
from .input_data import column, control_frame, labels
from .types import FloatArray


@dataclass(frozen=True)
class BinsregInputs:
    x: FloatArray
    y: FloatArray
    weights: FloatArray | None
    controls: FloatArray | None
    clusters: FloatArray | None
    x_name: str
    y_name: str
    control_columns: tuple[str, ...]
    n_input: int
    n_missing: int
    n_zero_weight: int


def prepare_binsreg(
    data: pd.DataFrame | Mapping[str, Any] | None,
    y: str | ArrayLike | None,
    x: str | ArrayLike | None,
    weights: str | ArrayLike | None,
    controls: str | Sequence[str] | ArrayLike | None,
    cluster: str | ArrayLike | None,
    dropna: bool,
) -> BinsregInputs:
    xa, xn = column(data, x, "x")
    ya, yn = column(data, y, "y")
    if xa.ndim != 1 or ya.ndim != 1 or xa.shape != ya.shape:
        raise ValueError("x and y must be matching one-dimensional arrays.")
    wa = None if weights is None else column(data, weights, "weights")[0]
    ca = None if cluster is None else labels(data, cluster, "cluster")[0]
    for value in (wa, ca):
        if value is not None and value.shape != ya.shape:
            raise ValueError("weights and cluster must match x and y.")
    if wa is not None and np.any(wa < 0):
        raise ValueError("weights must be nonnegative.")
    frame = None if controls is None else control_frame(data, controls, len(ya))[0]
    keep = np.isfinite(xa) & np.isfinite(ya)
    if wa is not None:
        keep &= np.isfinite(wa)
    if ca is not None:
        keep &= np.asarray(pd.notna(ca), dtype=bool)
    if frame is not None:
        keep &= ~frame.isna().any(axis=1).to_numpy()
        keep &= np.isfinite(frame.select_dtypes(include="number").to_numpy()).all(
            axis=1
        )
    missing = int(np.count_nonzero(~keep))
    if missing and not dropna:
        raise ValueError("inputs contain missing/nonfinite values; use dropna=True.")
    zero = 0 if wa is None else int(np.count_nonzero(keep & (wa == 0)))
    if wa is not None:
        keep &= wa > 0
    n_input = len(ya)
    xa, ya = xa[keep].copy(), ya[keep].copy()
    wa = None if wa is None else wa[keep].copy()
    if len(ya) < 4:
        raise InsufficientDataError("binsreg needs at least four positive-weight rows.")
    clusters = None
    if ca is not None:
        codes, unique = pd.factorize(ca[keep], sort=False)
        if len(unique) < 2:
            raise InsufficientDataError(
                "binsreg needs at least two positive-weight clusters."
            )
        clusters = codes.astype(float)
    design_controls = None
    columns: tuple[str, ...] = ()
    if frame is not None:
        encoded = pd.get_dummies(frame.loc[keep], drop_first=True, dtype=float)
        if not encoded.columns.is_unique:
            raise ValueError("encoded control columns must be unique.")
        columns = tuple(str(name) for name in encoded.columns)
        if columns:
            design_controls = encoded.to_numpy(dtype=float).copy()
            if not np.isfinite(design_controls).all():
                raise ValueError("encoded controls must be finite numeric values.")
    design = np.column_stack((np.ones(len(xa)), xa))
    if design_controls is not None:
        design = np.column_stack((design, design_controls))
    root = np.ones(len(xa)) if wa is None else np.sqrt(wa)
    rank = np.linalg.matrix_rank(scaled_design(design, root) * root[:, None])
    if rank != design.shape[1] or rank >= len(xa):
        raise InsufficientDataError(
            "binsreg requires an identified full-rank x/control design."
        )
    return BinsregInputs(
        xa, ya, wa, design_controls, clusters, xn, yn, columns, n_input, missing, zero
    )
