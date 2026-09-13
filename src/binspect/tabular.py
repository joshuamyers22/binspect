"""Polars tables and explicit, optional pandas compatibility boundaries."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, TypeAlias

import polars as pl
from numpy.typing import ArrayLike

if TYPE_CHECKING:
    import pandas as pd

    from .input_data import ControlFrame

DataSource: TypeAlias = "pl.DataFrame | pd.DataFrame | Mapping[str, Any] | None"
ControlInput: TypeAlias = (
    "str | Sequence[str] | ArrayLike | pl.DataFrame | pl.Series | "
    "pd.DataFrame | pd.Series | ControlFrame"
)


def is_pandas(value: Any) -> bool:
    """Recognize pandas objects/subclasses without importing pandas on native use."""
    return any(cls.__module__.startswith("pandas.") for cls in type(value).__mro__)


def to_pandas(frame: pl.DataFrame) -> pd.DataFrame:
    """Return an independent pandas table without requiring PyArrow."""
    try:
        import pandas as pd
    except ImportError:
        raise ImportError(
            "Install binspect-regression[pandas] for pandas table conversion."
        ) from None
    return pd.DataFrame(
        {
            name: pd.Series(values, dtype=object)
            if frame.schema[name] in (pl.String, pl.Null, pl.Object)
            else values
            for name, values in frame.to_dict(as_series=False).items()
        }
    )


def numeric_table(value: Any) -> pl.DataFrame:
    """Own a numeric Polars table, accepting upstream pandas at this boundary."""
    if isinstance(value, pl.DataFrame):
        return value.clone()
    if is_pandas(value) and value.ndim == 2:
        return pl.DataFrame(
            {str(name): value[name].to_numpy().copy() for name in value}
        )
    raise TypeError("Expected a Polars or pandas DataFrame.")
