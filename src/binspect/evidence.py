"""Deterministic, caller-controlled evidence exports with no implicit I/O."""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from collections.abc import Mapping
from datetime import datetime
from typing import Any


def canonical_json(value: Any) -> str:
    """Stable strict JSON for a given payload; no timestamp or file fingerprint."""
    return json.dumps(
        value, allow_nan=False, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    )


def evidence_export(
    result: dict[str, Any],
    provenance: Mapping[str, Mapping[str, str]] | None,
    exported_at: str | None,
) -> dict[str, Any]:
    references: dict[str, Any] = dict.fromkeys(
        ("analysis_plan", "inputs", "software_lock", "code")
    )
    for name, reference in ({} if provenance is None else provenance).items():
        if name not in references:
            raise ValueError(
                "Provenance keys must be analysis_plan, inputs, software_lock or code."
            )
        if not isinstance(reference, Mapping) or not reference:
            raise ValueError(
                "Each provenance reference needs a URI, SHA-256 or code revision."
            )
        copied = {}
        for key, value in reference.items():
            if key not in {"uri", "sha256", "revision"} or (
                key == "revision" and name != "code"
            ):
                raise ValueError(
                    "Reference fields must be uri, sha256, or revision for code."
                )
            if not isinstance(value, str) or not value.strip():
                raise ValueError("Reference values must be nonempty strings.")
            if key == "sha256" and re.fullmatch(r"[0-9a-fA-F]{64}", value) is None:
                raise ValueError(
                    "sha256 must contain exactly 64 hexadecimal characters."
                )
            copied[key] = value.lower() if key == "sha256" else value
        references[name] = copied
    if exported_at is not None:
        try:
            stamp = datetime.fromisoformat(exported_at.replace("Z", "+00:00"))
        except (TypeError, ValueError, AttributeError):
            raise ValueError(
                "exported_at must be an ISO-8601 timestamp with a timezone."
            ) from None
        if stamp.tzinfo is None:
            raise ValueError("exported_at must include a timezone.")
    envelope = {
        "schema_version": 1,
        "result_type": "evidence",
        "payload": {"result": result, "provenance": references},
        "exported_at": exported_at,
    }
    canonical_json(envelope)
    return envelope


class JsonExport(ABC):
    __slots__ = ()

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Return a schema-versioned strict-JSON payload."""

    def to_json(self) -> str:
        """Return deterministic strict JSON, without raw observations."""
        return canonical_json(self.to_dict())

    def to_evidence(
        self,
        *,
        provenance: Mapping[str, Mapping[str, str]] | None = None,
        exported_at: str | None = None,
    ) -> dict[str, Any]:
        """Attach caller-owned references; no references are read or verified."""
        return evidence_export(self.to_dict(), provenance, exported_at)
