"""Scalar label handling shared by input and numerical boundaries."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import numpy as np

from .types import IntArray


def is_missing(value: Any) -> bool:
    if value is None or (
        type(value).__module__.startswith("pandas.")
        and type(value).__name__ in {"NAType", "NaTType"}
    ):
        return True
    if isinstance(value, (float, np.floating)):
        return bool(np.isnan(value))
    if isinstance(value, (np.datetime64, np.timedelta64)):
        return bool(np.isnat(value))
    return False


def label_record(value: Any) -> dict[str, Any]:
    """Encode supported nonmissing labels without arbitrary repr/string fallback."""
    if isinstance(value, np.datetime64):
        if np.isnat(value):
            raise ValueError("A group label cannot be missing.")
        return {
            "type": "datetime64",
            "value": str(value),
            "unit": np.datetime_data(value.dtype)[0],
        }
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, datetime):
        return {"type": "datetime", "value": value.isoformat()}
    if isinstance(value, date):
        return {"type": "date", "value": value.isoformat()}
    for kind, typ in (
        ("boolean", bool),
        ("integer", int),
        ("number", float),
        ("string", str),
    ):
        if isinstance(value, typ):
            if isinstance(value, float) and not np.isfinite(value):
                raise ValueError("Numeric labels must be finite.")
            return {"type": kind, "value": value}
    raise TypeError(
        "Labels must be strings, finite numbers, booleans, dates or datetimes."
    )


def factorize_labels(
    values: np.ndarray[Any, Any],
) -> tuple[IntArray, np.ndarray[Any, Any]]:
    """First-observed factorization with Python equality; no sorting or pandas."""
    lookup: dict[Any, int] = {}
    unique: list[Any] = []
    codes = np.empty(len(values), dtype=np.int64)
    for index, value in enumerate(values):
        if is_missing(value):
            codes[index] = -1
            continue
        label_record(value)
        if value not in lookup:
            lookup[value] = len(unique)
            unique.append(value)
        codes[index] = lookup[value]
    result = np.empty(len(unique), dtype=object)
    result[:] = unique
    return codes, result
