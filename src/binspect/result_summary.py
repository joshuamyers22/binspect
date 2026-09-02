"""Plain-text presentation policy for estimation results."""

from __future__ import annotations

from textwrap import wrap
from typing import TYPE_CHECKING

from .core.decompose import Decomposition

if TYPE_CHECKING:  # pragma: no cover
    from .results import BinscatterResult


def plot_caption(result: BinscatterResult, level: str = "minimal") -> str:
    """Build the compact result caption used by visualization adapters."""
    if level == "minimal":
        return f"n = {result.n_obs:,}   ·   {result.n_bins} bins"
    if level == "audit":
        decomposition = result.decomposition
        return (
            f"R² {decomposition.r_sq_linear:.2f}   ·   η² {decomposition.eta_sq:.2f}\n"
            f"lack of fit {decomposition.gap:.2f}, {decomposition.verdict}\n"
            f"n = {result.n_obs:,}   ·   {result.n_bins} bins"
        )
    raise ValueError(f"annotate must be None, 'minimal' or 'audit', got {level!r}.")


def summarize(result: BinscatterResult) -> str:
    """Render a stable, plain-text model and diagnostics report."""
    decomposition = result.decomposition
    fit = result.fit
    width = 68
    rule = "=" * width
    thin = "-" * width
    lines = [
        rule,
        "Binscatter Results".center(width),
        rule,
        f"{'Dep. Variable:':<20}{result.y_name:>14}"
        f"{'No. Observations:':>22}{result.n_obs:>12,}",
        f"{'Exog:':<20}{result.x_name:>14}{'No. Bins:':>22}{result.n_bins:>12}",
        f"{'Binning:':<20}{result.binning.method:>14}"
        f"{'Min. Bin Size:':>22}{decomposition.min_bin_n:>12,}",
        *(
            [f"{'Controls:':<20}{_controls_label(result.controls):>48}"]
            if result.controls
            else []
        ),
        *(
            [f"{'Cluster:':<20}{result.cluster!s:>48}"]
            if result.cluster is not None
            else []
        ),
        thin,
        f"{'':<18}{'coef':>13}{'std err':>13}",
        thin,
        f"{'const':<18}{fit.intercept:>13.6g}{'--':>13}",
        f"{result.x_name:<18}{fit.slope:>13.6g}{fit.se_slope:>13.6g}",
        thin,
        f"{'R-squared:':<20}{decomposition.r_sq_linear:>14.4f}"
        f"{'Eta-squared:':>22}{decomposition.eta_sq:>12.4f}",
        f"{'Lack of fit:':<20}{decomposition.gap:>14.4f}"
        f"{'SD line slope:':>22}{result.sd_line.slope:>12.6g}",
        f"{'Correlation:':<20}{fit.r:>14.4f}"
        f"{'Verdict:':>22}{decomposition.verdict:>12}",
        rule,
        "Notes:",
        *_summary_notes(decomposition, width, result.controls, result.cluster),
        rule,
    ]
    return "\n".join(lines)


def _verdict_note(decomposition: Decomposition) -> str:
    if decomposition.verdict == "underpowered bins":
        return (
            f"The smallest bin has {decomposition.min_bin_n} observations; sampling "
            "variation may dominate the lack-of-fit measure."
        )
    if decomposition.verdict == "curvature":
        return (
            "Bin-mean deviations account for "
            f"{decomposition.gap:.1%} of total variation, "
            "which may indicate a nonlinear conditional mean."
        )
    return "The bin means do not show substantial departure from the fitted line."


def _controls_label(controls: tuple[str, ...]) -> str:
    label = ", ".join(controls)
    return f"{label[:45]}..." if len(label) > 48 else label


def _summary_notes(
    decomposition: Decomposition,
    width: int,
    controls: tuple[str, ...],
    cluster: str | None,
) -> list[str]:
    uncertainty_note = (
        "Standard errors and confidence intervals use CR1 cluster-robust inference."
        if cluster is not None
        else "Confidence intervals assume independent observations."
    )
    notes = [
        uncertainty_note,
        "Lack of fit is descriptive; the verdict is not a formal test.",
        _verdict_note(decomposition),
    ]
    if controls:
        notes.append(
            "The displayed variables were residualized on the listed controls "
            "using Frisch-Waugh-Lovell projection."
        )
    lines: list[str] = []
    for index, note in enumerate(notes, start=1):
        prefix = f"[{index}] "
        lines.extend(
            wrap(
                note,
                width=width,
                initial_indent=prefix,
                subsequent_indent=" " * len(prefix),
            )
        )
    return lines
