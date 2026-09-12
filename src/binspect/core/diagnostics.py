"""Explicit descriptive screening policy; never a statistical power calculation."""

from __future__ import annotations

import math
from dataclasses import dataclass
from numbers import Integral, Real

from ..types import Verdict


@dataclass(frozen=True, slots=True)
class DiagnosticPolicy:
    """Thresholds for descriptive verdicts, with no inference-validity guarantee.

    Clustered results require an explicit ``min_bin_clusters`` to classify.
    ``None`` leaves their verdict unassessed. Defaults retain the historical
    unweighted gap/count cutoffs, applying effective rather than retained rows.
    """

    gap_threshold: float = 0.02
    min_bin_effective_n: float = 30.0
    min_bin_clusters: int | None = None

    def __post_init__(self) -> None:
        for name, minimum in (("gap_threshold", 0), ("min_bin_effective_n", 1)):
            value = getattr(self, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, Real)
                or not math.isfinite(value)
                or value < minimum
            ):
                raise ValueError(f"{name} must be finite and at least {minimum}.")
            object.__setattr__(self, name, float(value))
        count = self.min_bin_clusters
        if count is not None:
            if isinstance(count, bool) or not isinstance(count, Integral) or count < 2:
                raise ValueError(
                    "min_bin_clusters must be an integer at least 2 or None."
                )
            object.__setattr__(self, "min_bin_clusters", int(count))


DEFAULT_DIAGNOSTIC_POLICY = DiagnosticPolicy()


def classify(
    gap: float,
    ss_total: float,
    min_effective_n: float,
    min_clusters: int | None,
    policy: DiagnosticPolicy | None,
) -> tuple[Verdict, str]:
    if policy is None:
        return "not assessed", "disabled"
    if not isinstance(policy, DiagnosticPolicy):
        raise TypeError("diagnostic_policy must be a DiagnosticPolicy or None.")
    if ss_total <= 0:
        return "not assessed", "constant outcome"
    if min_clusters is not None and policy.min_bin_clusters is None:
        return "not assessed", "cluster policy required"
    if min_effective_n < policy.min_bin_effective_n:
        return "limited support", "effective rows below threshold"
    if (
        min_clusters is not None
        and policy.min_bin_clusters is not None
        and min_clusters < policy.min_bin_clusters
    ):
        return "limited support", "clusters below threshold"
    if gap < policy.gap_threshold:
        return "linear", "gap below threshold"
    return "curvature", "gap at or above threshold"
