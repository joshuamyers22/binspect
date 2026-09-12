"""Owned numeric storage shared by frozen result dataclasses."""

from __future__ import annotations

from dataclasses import Field, dataclass, fields
from typing import Any, ClassVar

import numpy as np


@dataclass(frozen=True, slots=True)
class _ArraySnapshot:
    """Immutable payload and metadata, with no retained caller array header."""

    data: bytes
    dtype: np.dtype[Any]
    shape: tuple[int, ...]

    def view(self) -> np.ndarray[Any, Any]:
        return np.frombuffer(self.data, dtype=self.dtype).reshape(self.shape)


class ArrayOwner:
    """Store array fields as snapshots; preserve their public ndarray interface.

    Subclasses must be frozen dataclasses with otherwise immutable fields.
    Each read gets a fresh header over immutable bytes, avoiding both value
    aliasing and shape/dtype mutation through a previously returned array.
    Construction copies each numeric buffer once; access does not copy values.
    """

    __slots__ = ()
    __dataclass_fields__: ClassVar[dict[str, Field[Any]]]

    def __post_init__(self) -> None:
        for field in fields(type(self)):
            value = object.__getattribute__(self, field.name)
            if isinstance(value, np.ndarray):
                if value.dtype.hasobject:
                    raise TypeError("Result arrays must not contain Python objects.")
                object.__setattr__(
                    self,
                    field.name,
                    _ArraySnapshot(value.tobytes(), value.dtype, value.shape),
                )

    def __getattribute__(self, name: str) -> Any:
        value = object.__getattribute__(self, name)
        return value.view() if isinstance(value, _ArraySnapshot) else value

    def __copy__(self) -> ArrayOwner:
        return self

    def __deepcopy__(self, memo: dict[int, Any]) -> ArrayOwner:
        return self

    def __reduce__(self) -> tuple[type[ArrayOwner], tuple[Any, ...]]:
        # Reconstruct through __init__/__post_init__, including after pickling;
        # NumPy's own pickle reconstruction would otherwise restore writable arrays.
        return type(self), tuple(getattr(self, f.name) for f in fields(type(self)))
