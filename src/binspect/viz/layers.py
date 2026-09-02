"""One function per visual layer.

Every layer takes an axes and a result, draws, and returns the axes. They are public
and independently usable --- someone who wants only the deviation shading over their
own scatter should be able to import that one function and get it.

Layer order matters and is fixed in :mod:`binspect.viz.figure`: context first
(raw, deviation, rug), then lines, then the estimates on top.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
from matplotlib.collections import LineCollection

from ..types import FloatArray
from .layer_policy import line_span as _line_span
from .layer_policy import marker_sizes as _marker_sizes
from .layer_policy import smooth as _smooth
from .theme import Theme, get_theme

if TYPE_CHECKING:  # pragma: no cover
    from matplotlib.axes import Axes

    from ..results import BinscatterResult

__all__ = [
    "bins_layer",
    "ci_layer",
    "deviation_layer",
    "fit_layer",
    "raw_layer",
    "rug_layer",
    "sd_line_layer",
    "smooth_layer",
]


def _theme(t: str | Theme) -> Theme:
    return get_theme(t)


def raw_layer(
    ax: Axes,
    result: BinscatterResult,
    *,
    theme: str | Theme = "notebook",
    **kwargs: Any,
) -> Axes:
    """The underlying observations at low alpha.

    Off by default: showing every point undercuts the reason to bin. Useful when a
    reviewer wants to see that the bins are not hiding a bimodal cloud.
    """
    th = _theme(theme)
    opts: dict[str, Any] = {
        "s": th.raw_size,
        "color": th.palette.raw,
        "alpha": th.raw_alpha,
        "linewidths": 0,
        "zorder": 1,
    }
    opts.update(kwargs)
    ax.scatter(result.x, result.y, **opts)
    return ax


def deviation_layer(
    ax: Axes,
    result: BinscatterResult,
    *,
    theme: str | Theme = "notebook",
    target: str = "fit",
    **kwargs: Any,
) -> Axes:
    """Shading between each bin mean and the line it is being compared against.

    This is the package's whole thesis rendered as ink: the visible area is the
    lack of fit measured by ``SS_lof / SS_total``. It is descriptive rather than a
    formal test of curvature.

    Parameters
    ----------
    target:
        ``"fit"`` (default) shades to the OLS line, which is the honest audit.
        ``"smooth"`` shades to a smoother through the bin means --- prettier, and a
        different claim. Opt in deliberately.
    """
    th = _theme(theme)
    x = result.estimates.x_mean
    y = result.estimates.y_mean

    if target == "fit":
        base = np.asarray(result.fit.predict(x), dtype=float)
    elif target == "smooth":
        base = _smooth(x, y)
    else:
        raise ValueError(f"target must be 'fit' or 'smooth', got {target!r}.")

    opts: dict[str, Any] = {
        "colors": th.palette.deviation,
        "alpha": th.deviation_alpha,
        "linewidth": th.deviation_width,
        "zorder": 2,
    }
    opts.update(kwargs)
    ax.vlines(x, base, y, **opts)
    return ax


def rug_layer(
    ax: Axes,
    result: BinscatterResult,
    *,
    theme: str | Theme = "notebook",
    max_ticks: int = 2000,
    **kwargs: Any,
) -> Axes:
    """A density strip under the axis, showing where the observations actually are.

    Quantile bins hide their own imbalance: every bin holds the same count, so wide
    bins in sparse regions look identical to narrow ones. The rug puts that back.
    """
    th = _theme(theme)
    x = np.asarray(result.x, dtype=float)
    if x.size > max_ticks:
        rng = np.random.default_rng(0)
        x = rng.choice(x, size=max_ticks, replace=False)

    opts: dict[str, Any] = {
        "colors": th.palette.neutral,
        "alpha": th.rug_alpha,
        "linewidth": 0.5,
        "zorder": 1,
    }
    opts.update(kwargs)

    # One LineCollection, not one artist per observation -- and added with
    # autolim=False so the rug never drives autoscaling. It is context: a few
    # observations far out in the tail should not stretch the axes past the bins.
    segments = [[(xi, 0.0), (xi, th.rug_height)] for xi in x]
    collection = LineCollection(segments, transform=ax.get_xaxis_transform(), **opts)
    ax.add_collection(collection, autolim=False)
    return ax


def _span(result: BinscatterResult, span: str) -> FloatArray:
    """The x-interval a line is drawn across.

    ``"bins"`` (default) spans the bin means. ``"data"`` spans every observation,
    which on a normal-ish x means a handful of tail points stretch the axes far past
    where any bin mean lives --- honest about the fit's domain, useless as a picture.
    """
    return _line_span(result.estimates.x_mean, result.x, span)


def fit_layer(
    ax: Axes,
    result: BinscatterResult,
    *,
    theme: str | Theme = "notebook",
    span: str = "bins",
    label: str | None = "OLS fit",
    **kwargs: Any,
) -> Axes:
    """The least-squares line through the underlying observations.

    Note that this is fitted to the raw data, not to the bin means. Fitting to bin
    means would give a similar slope and a wildly inflated R-squared, because
    averaging deletes the within-bin noise the model has to explain.
    """
    th = _theme(theme)
    xs = _span(result, span)
    opts: dict[str, Any] = {
        "color": th.palette.accent,
        "linewidth": th.fit_width,
        "zorder": 3,
        "label": label,
    }
    opts.update(kwargs)
    ax.plot(xs, result.fit.predict(xs), **opts)
    return ax


def sd_line_layer(
    ax: Axes,
    result: BinscatterResult,
    *,
    theme: str | Theme = "notebook",
    span: str = "bins",
    label: str | None = "SD line",
    **kwargs: Any,
) -> Axes:
    """The SD line, always at least as steep as the fit.

    Drawn dashed and neutral so the plot still distinguishes it in greyscale. The
    visible gap between the two lines is the shrinkage factor ``r``.
    """
    th = _theme(theme)
    xs = _span(result, span)
    opts: dict[str, Any] = {
        "color": th.palette.neutral,
        "linewidth": th.sd_width,
        "dashes": list(th.sd_dashes),
        "zorder": 3,
        "label": label,
    }
    opts.update(kwargs)
    ax.plot(xs, result.sd_line.predict(xs), **opts)
    return ax


def ci_layer(
    ax: Axes,
    result: BinscatterResult,
    *,
    theme: str | Theme = "notebook",
    **kwargs: Any,
) -> Axes:
    """Per-bin confidence bars for the bin mean.

    These are intervals for the *mean*, not the spread of the observations. The
    within-bin SD lives in ``result.table['y_sd']`` and is deliberately not drawn by
    default: at typical bin sizes it dwarfs everything else and flattens the plot.
    """
    th = _theme(theme)
    e = result.estimates
    if e.ci_level is None or not np.any(np.isfinite(e.ci_lo)):
        return ax
    opts: dict[str, Any] = {
        "colors": th.palette.accent,
        "alpha": th.ci_alpha,
        "linewidth": th.ci_width,
        "zorder": 4,
    }
    opts.update(kwargs)
    ok = np.isfinite(e.ci_lo) & np.isfinite(e.ci_hi)
    ax.vlines(e.x_mean[ok], e.ci_lo[ok], e.ci_hi[ok], **opts)
    return ax


def bins_layer(
    ax: Axes,
    result: BinscatterResult,
    *,
    theme: str | Theme = "notebook",
    size_by_n: bool = False,
    label: str | None = "Bin mean",
    **kwargs: Any,
) -> Axes:
    """The bin means themselves --- the saturated-model fitted values.

    Parameters
    ----------
    size_by_n:
        Scale marker area with bin count. Off by default because quantile bins hold
        equal counts, making it pure noise; useful for equal-width bins.
    """
    th = _theme(theme)
    e = result.estimates
    size = _marker_sizes(e.n, th.marker_size) if size_by_n else th.marker_size

    opts: dict[str, Any] = {
        "s": size,
        "color": th.palette.accent,
        "zorder": 5,
        "linewidths": th.marker_edge,
        "label": label,
    }
    opts.update(kwargs)
    ax.scatter(e.x_mean, e.y_mean, **opts)
    return ax


def smooth_layer(
    ax: Axes,
    result: BinscatterResult,
    *,
    theme: str | Theme = "notebook",
    label: str | None = None,
    **kwargs: Any,
) -> Axes:
    """A smoother through the bin means. Off by default.

    Useful for reading the shape of the conditional mean; not a fitted model, and
    not something to quote a slope from.
    """
    th = _theme(theme)
    e = result.estimates
    opts: dict[str, Any] = {
        "color": th.palette.neutral,
        "linewidth": th.fit_width * 0.8,
        "alpha": 0.8,
        "zorder": 3,
        "label": label,
    }
    opts.update(kwargs)
    ax.plot(e.x_mean, _smooth(e.x_mean, e.y_mean), **opts)
    return ax
