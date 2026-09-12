"""Immutable input accounting and encoded-control identity."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class SampleCounts:
    n_input: int
    n_missing: int
    n_zero_weight_dropped: int
    dropna: bool
    n_missing_group: int = 0

    def to_dict(self, n_obs: int) -> dict[str, Any]:
        return {
            "n_input": self.n_input,
            "n_obs": n_obs,
            "n_dropped": self.n_input - n_obs,
            "n_missing_group": self.n_missing_group,
            "n_missing": self.n_missing,
            "n_zero_weight_dropped": self.n_zero_weight_dropped,
            "dropna": self.dropna,
            "alignment": "positional",
        }


@dataclass(frozen=True, slots=True)
class ControlDesign:
    columns: tuple[str, ...] = ()
    encoding_json: str = "[]"

    def to_dict(self) -> dict[str, Any]:
        return {
            "control_columns": list(self.columns),
            "encoding": json.loads(self.encoding_json),
        }
