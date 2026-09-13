"""Polars-native input normalization with positional pandas compatibility."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from numbers import Real
from typing import Any

import numpy as np
import polars as pl

from .input_metadata import ControlDesign
from .label_values import is_missing, label_record
from .tabular import DataSource, is_pandas
from .types import FloatArray


def _select(source: DataSource, value: Any, label: str) -> tuple[Any, str]:
    if isinstance(source, pl.LazyFrame) or isinstance(value, pl.LazyFrame):
        raise TypeError("Collect LazyFrame inputs explicitly before estimation.")
    if value is None:
        raise ValueError(f"{label} is required.")
    if isinstance(value, str):
        if source is None:
            raise ValueError(
                f"{label}={value!r} is a column name, but no data= was given."
            )
        try:
            return source[value], value
        except (KeyError, pl.exceptions.ColumnNotFoundError):
            available = (
                list(source.columns) if hasattr(source, "columns") else list(source)
            )
            raise KeyError(
                f"column {value!r} not found; available: {available}"
            ) from None
    return value, str(getattr(value, "name", None) or label)


def column(source: DataSource, value: Any, label: str) -> tuple[FloatArray, str]:
    """Return one numeric vector; indexes never align rows."""
    selected, name = _select(source, value, label)
    if np.iscomplexobj(selected):
        raise ValueError(f"{label} must contain real numeric values.")
    if isinstance(selected, pl.Series):
        array = selected.cast(pl.Float64, strict=True).to_numpy()
    elif is_pandas(selected) and selected.ndim == 1:
        array = selected.to_numpy(dtype=float, na_value=np.nan)
    else:
        array = np.asarray(selected, dtype=float)
    if array.ndim != 1:
        raise ValueError(f"{label} must be one-dimensional, got shape {array.shape}.")
    return np.asarray(array, dtype=float), name


def labels(
    source: DataSource, value: Any, label: str
) -> tuple[np.ndarray[Any, Any], str]:
    selected, name = _select(source, value, label)
    if isinstance(selected, pl.Series):
        values = selected.to_list()
    elif is_pandas(selected):
        if selected.ndim != 1:
            raise ValueError(f"{label} must be one-dimensional.")
        values = selected.to_list()
    else:
        raw = np.asarray(selected)
        if raw.ndim != 1:
            raise ValueError(f"{label} must be one-dimensional, got shape {raw.shape}.")
        # Iteration preserves NumPy datetime units and mixed scalar label types.
        values = list(selected)
    array = np.empty(len(values), dtype=object)
    for index, item in enumerate(values):
        if is_missing(item):
            array[index] = None
        else:
            label_record(item)
            array[index] = (
                item.item()
                if isinstance(item, np.generic) and not isinstance(item, np.datetime64)
                else item
            )
    return array, name


@dataclass(frozen=True)
class ControlFrame:
    frame: pl.DataFrame
    # Declared category order survives filtering, including unused levels.
    categories: tuple[tuple[str, tuple[Any, ...]], ...] = ()

    def filter(self, mask: np.ndarray[Any, Any]) -> ControlFrame:
        return ControlFrame(self.frame.filter(pl.Series(mask)), self.categories)

    def valid_rows(self) -> np.ndarray[Any, Any]:
        checks = [
            pl.col(name).is_not_null() & pl.col(name).is_finite()
            if dtype.is_numeric()
            else pl.col(name).is_not_null()
            for name, dtype in self.frame.schema.items()
        ]
        return np.asarray(
            self.frame.select(pl.all_horizontal(checks))
            .to_series()
            .fill_null(False)
            .to_numpy(),
            dtype=bool,
        )


def control_frame(
    source: DataSource, controls: Any, n_obs: int
) -> tuple[ControlFrame, tuple[str, ...]]:
    if (
        isinstance(controls, Sequence)
        and not isinstance(controls, (str, bytes))
        and len(controls) == 0
    ):
        raise ValueError("controls must contain at least one variable.")
    if isinstance(controls, ControlFrame):
        return controls, tuple(controls.frame.columns)
    if isinstance(controls, pl.LazyFrame):
        raise TypeError("Collect LazyFrame controls explicitly before estimation.")
    names: tuple[str, ...] = ()
    if isinstance(controls, str):
        names = (controls,)
    elif (
        source is not None
        and isinstance(controls, Sequence)
        and not isinstance(controls, (np.ndarray, str, bytes))
        and all(isinstance(item, str) for item in controls)
    ):
        names = tuple(controls)
    series: list[pl.Series] = []
    categories: list[tuple[str, tuple[Any, ...]]] = []
    if names:
        selected = [(name, _select(source, name, "controls")[0]) for name in names]
    elif isinstance(controls, pl.DataFrame) or (
        is_pandas(controls) and controls.ndim == 2
    ):
        selected = [(str(name), controls[name]) for name in controls.columns]
    elif isinstance(controls, pl.Series) or (
        is_pandas(controls) and controls.ndim == 1
    ):
        selected = [(str(getattr(controls, "name", None) or "control"), controls)]
    else:
        array = np.asarray(controls)
        if array.ndim == 1:
            selected = [("control", array)]
        elif array.ndim == 2:
            selected = [(f"control_{i}", array[:, i]) for i in range(array.shape[1])]
        else:
            raise ValueError(
                f"controls must be one- or two-dimensional, got shape {array.shape}."
            )
    if not selected:
        raise ValueError("controls must contain at least one variable.")
    if len({name for name, _ in selected}) != len(selected):
        raise ValueError("control column names must be unique.")
    for name, values in selected:
        if isinstance(values, pl.Series):
            item = values.rename(name)
            if isinstance(item.dtype, pl.Enum):
                categories.append((name, tuple(item.dtype.categories.to_list())))
        else:
            if np.ndim(values) != 1:
                raise ValueError("Each named control must be one-dimensional.")
            if is_pandas(values):
                if str(values.dtype) == "category":
                    categories.append((name, tuple(values.cat.categories)))
                raw = values.to_list()
            else:
                raw = list(values)
            cleaned = [None if is_missing(v) else v for v in raw]
            numeric = all(v is None or isinstance(v, Real) for v in cleaned)
            boolean = all(v is None or isinstance(v, (bool, np.bool_)) for v in cleaned)
            item = (
                pl.Series(
                    name,
                    [None if v is None else float(v) for v in cleaned],
                    dtype=pl.Float64,
                )
                # Declared numeric categories are identities, not measurements;
                # float conversion can collapse distinct large integer labels.
                if numeric and not boolean and name not in dict(categories)
                else pl.Series(name, cleaned, strict=True)
            )
        if len(item) != n_obs:
            raise ValueError("controls must have the same number of rows as x and y.")
        if not (
            item.dtype.is_numeric()
            or item.dtype in (pl.Boolean, pl.String, pl.Categorical, pl.Enum, pl.Null)
            or (name in dict(categories) and item.dtype in (pl.Date, pl.Datetime))
        ):
            raise ValueError(
                "controls must be numeric, boolean, or categorical strings."
            )
        series.append(item)
    frame = pl.DataFrame(series)
    return ControlFrame(frame, tuple(categories)), tuple(frame.columns)


def encoded_controls(controls: ControlFrame) -> tuple[pl.DataFrame, ControlDesign]:
    """Reference coding in numerical-first order, matching the existing design."""
    frame = controls.frame
    declared = dict(controls.categories)
    numeric: list[pl.Series] = []
    categorical: list[pl.Series] = []
    metadata: list[dict[str, Any]] = []
    for name, dtype in frame.schema.items():
        if name not in declared and (dtype.is_numeric() or dtype == pl.Boolean):
            numeric.append(frame[name].cast(pl.Float64))
            metadata.append({"name": name, "kind": "numeric"})
        else:
            levels = declared.get(
                name, tuple(sorted(frame[name].drop_nulls().unique().to_list()))
            )
            metadata.append(
                {
                    "name": name,
                    "kind": "categorical",
                    "levels": [label_record(v) for v in levels],
                    "reference": None if not levels else label_record(levels[0]),
                }
            )
            for level in levels[1:]:
                categorical.append(
                    (frame[name] == level).cast(pl.Float64).rename(f"{name}_{level}")
                )
    columns = numeric + categorical
    names = tuple(item.name for item in columns)
    if len(set(names)) != len(names):
        raise ValueError("encoded control columns must be unique.")
    return pl.DataFrame(columns), ControlDesign(
        names, json.dumps(metadata, allow_nan=False)
    )
