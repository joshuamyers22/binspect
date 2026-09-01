"""Input normalization independent of estimation and presentation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike

from .types import FloatArray


def column(
    source: Mapping[str, Any] | pd.DataFrame | None,
    value: Any,
    label: str,
) -> tuple[FloatArray, str]:
    """Return a data column as a one-dimensional floating-point array."""
    if value is None:
        raise ValueError(f"{label} is required.")
    if isinstance(value, str):
        if source is None:
            raise ValueError(
                f"{label}={value!r} is a column name, but no data= was given."
            )
        try:
            selected = source[value]
        except KeyError:
            available = list(getattr(source, "columns", source.keys()))
            raise KeyError(
                f"column {value!r} not found; available: {available}"
            ) from None
        return np.asarray(selected, dtype=float), value
    array = np.asarray(value, dtype=float)
    if array.ndim != 1:
        raise ValueError(f"{label} must be one-dimensional, got shape {array.shape}.")
    name = getattr(value, "name", None) or label
    return array, str(name)


def labels(
    source: Mapping[str, Any] | pd.DataFrame | None,
    value: Any,
    label: str,
) -> tuple[np.ndarray[Any, np.dtype[Any]], str]:
    """Return a nonnumeric one-dimensional label array."""
    if isinstance(value, str):
        if source is None:
            raise ValueError(
                f"{label}={value!r} is a column name, but no data= was given."
            )
        try:
            values = source[value]
        except KeyError:
            available = list(getattr(source, "columns", source.keys()))
            raise KeyError(
                f"column {value!r} not found; available: {available}"
            ) from None
        name = value
    else:
        values = value
        name = str(getattr(value, "name", None) or label)
    array = np.asarray(values, dtype=object)
    if array.ndim != 1:
        raise ValueError(f"{label} must be one-dimensional, got shape {array.shape}.")
    return array, name


def control_frame(
    source: Mapping[str, Any] | pd.DataFrame | None,
    controls: str | Sequence[str] | ArrayLike,
    n_obs: int,
) -> tuple[pd.DataFrame, tuple[str, ...]]:
    """Return controls as an unencoded DataFrame and their display names."""
    if (
        isinstance(controls, Sequence)
        and not isinstance(controls, (str, bytes))
        and len(controls) == 0
    ):
        raise ValueError("controls must contain at least one variable.")
    names: tuple[str, ...]
    if isinstance(controls, str):
        names = (controls,)
    elif (
        source is not None
        and isinstance(controls, Sequence)
        and not isinstance(controls, (np.ndarray, pd.Series, pd.DataFrame))
        and all(isinstance(value, str) for value in controls)
    ):
        names = tuple(str(value) for value in controls)
    else:
        names = ()

    if names:
        if source is None:
            raise ValueError("named controls require data=.")
        if len(set(names)) != len(names):
            raise ValueError("control column names must be unique.")
        try:
            frame = pd.DataFrame({name: source[name] for name in names})
        except KeyError as exc:
            available = list(getattr(source, "columns", source.keys()))
            raise KeyError(
                f"control column {exc.args[0]!r} not found; available: {available}"
            ) from None
    elif isinstance(controls, pd.DataFrame):
        frame = controls.copy()
        names = tuple(str(name) for name in frame.columns)
    else:
        array = np.asarray(controls)
        if array.ndim == 1:
            frame = pd.DataFrame(
                {str(getattr(controls, "name", None) or "control"): array}
            )
        elif array.ndim == 2:
            frame = pd.DataFrame(
                array, columns=[f"control_{index}" for index in range(array.shape[1])]
            )
        else:
            raise ValueError(
                f"controls must be one- or two-dimensional, got shape {array.shape}."
            )
        names = tuple(str(name) for name in frame.columns)

    if frame.shape[1] == 0:
        raise ValueError("controls must contain at least one variable.")
    if not frame.columns.is_unique:
        raise ValueError("control column names must be unique.")
    if len(frame) != n_obs:
        raise ValueError("controls must have the same number of rows as x and y.")
    return frame.reset_index(drop=True), names


def encode_controls(frame: pd.DataFrame) -> FloatArray:
    """Encode numeric and categorical controls as a full-rank projection matrix."""
    encoded = pd.get_dummies(frame, drop_first=True, dtype=float)
    try:
        values = encoded.to_numpy(dtype=float)
    except (TypeError, ValueError):
        raise ValueError("controls must be numeric, boolean, or categorical.") from None
    return np.column_stack((np.ones(len(frame), dtype=float), values))
