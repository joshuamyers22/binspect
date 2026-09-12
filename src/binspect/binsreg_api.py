"""Explicit optional delegation of function inference to binsreg."""

from __future__ import annotations

import contextlib
import importlib.metadata
import io
import warnings
from collections.abc import Callable
from numbers import Integral, Real
from typing import Any

import numpy as np
import polars as pl
from numpy.typing import ArrayLike

from .binsreg_inputs import prepare_binsreg
from .binsreg_results import BinsregResult
from .exceptions import BinsregError, BinsregWarning
from .tabular import ControlInput, DataSource, numeric_table


def _load_backend() -> tuple[Callable[..., Any], str]:
    try:
        from binsreg import binsreg as backend

        return backend, importlib.metadata.version("binsreg")
    except (ImportError, importlib.metadata.PackageNotFoundError):
        raise BinsregError(
            "Install binspect-regression[dpi] to use binspect.binsreg."
        ) from None


def _issue(message: str) -> str:
    for fragment, code in (
        ("Too small effective sample size", "small_effective_sample"),
        ("ci=(0,0) used", "constant_interval_fallback"),
        ("dots=c(0,0) used", "constant_dots_fallback"),
        ("DPI selection fails. ROT choice used", "dpi_to_rot_fallback"),
        ("Confidence intervals/bands are valid when nbins", "fixed_count_bias_warning"),
        ("Repeated knots", "repeated_knots"),
        ("too few distinct values", "insufficient_local_mass_points"),
        ("some X-based variables dropped", "rank_drop"),
    ):
        if fragment in message:
            return code
    return "unclassified_upstream_warning"


def _table(value: Any, *, intervals: bool) -> pl.DataFrame:
    columns = ["x", "bin", "ci_l", "ci_r"] if intervals else ["x", "bin", "fit"]
    if value is None and intervals:
        return pl.DataFrame(
            schema={name: pl.Float64 for name in ["x", "bin", "fit", "ci_lo", "ci_hi"]}
        )
    try:
        table = numeric_table(value).select(columns).cast(pl.Float64)
    except (TypeError, ValueError, pl.exceptions.PolarsError):
        raise BinsregError("binsreg returned an unsupported result schema.") from None
    numbers = table.to_numpy()
    if not len(table) or not np.isfinite(numbers).all():
        raise BinsregError("binsreg returned empty or nonfinite estimates.")
    ids = table["bin"].to_numpy()
    if np.any(ids < 1) or np.any(ids % 1 != 0):
        raise BinsregError("binsreg returned invalid interval identifiers.")
    table = table.with_columns(pl.col("bin").cast(pl.Int64))
    if intervals:
        table = table.rename({"ci_l": "ci_lo", "ci_r": "ci_hi"})
        if (table["ci_lo"] > table["ci_hi"]).any():
            raise BinsregError("binsreg returned reversed confidence limits.")
        table = table.with_columns(
            (pl.col("ci_lo") / 2 + pl.col("ci_hi") / 2).alias("fit")
        )
    return table


def binsreg(
    data: DataSource = None,
    y: str | ArrayLike | None = None,
    x: str | ArrayLike | None = None,
    *,
    controls: ControlInput | None = None,
    weights: str | ArrayLike | None = None,
    cluster: str | ArrayLike | None = None,
    bins: int | str = "dpi",
    binning: str = "quantile",
    at: str | ArrayLike = "mean",
    ci: float = 0.95,
    dropna: bool = True,
) -> BinsregResult:
    """Fit binsreg's function in original x coordinates with full control covariance.

    Requires the optional ``dpi`` extra. Numeric/categorical controls enter the
    upstream design jointly; ``at`` is 'mean', 'zero', or a finite vector in the
    exported encoded-control order. Zero weights are always dropped. ``bins`` is
    'dpi' or an integer >=2; ``binning`` is 'quantile' or 'equal_width'.

    Requests degree-0 dots and degree-1 pointwise intervals, asyvar=False, HC1 or
    cluster covariance, and upstream sample-size/mass-point safeguards. Returned
    intervals follow any upstream fallback, with explicit warnings/status; this
    supplies no general few-cluster guarantee. Does not return an FWL slope/gap.
    """
    if (
        isinstance(ci, bool)
        or not isinstance(ci, Real)
        or not np.isfinite(ci)
        or not 0 < ci < 1
    ):
        raise ValueError(
            "ci must be a finite confidence level strictly between 0 and 1."
        )
    if binning not in ("quantile", "equal_width"):
        raise ValueError("binning must be quantile or equal_width.")
    if not (isinstance(bins, str) and bins == "dpi") and (
        isinstance(bins, bool) or not isinstance(bins, Integral) or bins < 2
    ):
        raise ValueError("bins must be 'dpi' or an integer at least 2.")
    prepared = prepare_binsreg(data, y, x, weights, controls, cluster, dropna)
    n = len(prepared.y)
    if isinstance(bins, Integral) and bins > n:
        raise ValueError("requested bins cannot exceed positive-weight rows.")
    k = len(prepared.control_columns)
    if isinstance(at, str):
        if at not in ("mean", "zero"):
            raise ValueError("at must be mean, zero or an encoded-control vector.")
        evaluation = (
            np.average(prepared.controls, axis=0, weights=prepared.weights)
            if at == "mean" and k
            else np.zeros(k)
        )
    else:
        evaluation = np.asarray(at, dtype=float)
        if evaluation.shape != (k,) or not np.isfinite(evaluation).all():
            raise ValueError("at must contain one finite value per encoded control.")
    backend, version = _load_backend()
    # The optional backend can emit progress text; never export unstructured data.
    with (
        warnings.catch_warnings(record=True) as captured,
        contextlib.redirect_stdout(io.StringIO()),
        contextlib.redirect_stderr(io.StringIO()),
    ):
        warnings.simplefilter("always")
        try:
            result = backend(
                y=prepared.y,
                x=prepared.x,
                w=prepared.controls,
                weights=prepared.weights,
                cluster=prepared.clusters,
                at=evaluation.copy() if k else None,
                nbins=None if bins == "dpi" else int(bins),
                binspos="qs" if binning == "quantile" else "es",
                binsmethod="dpi",
                dots=(0, 0),
                ci=True,
                asyvar=False,
                vce="HC1",
                level=float(ci) * 100,
                noplot=True,
                randcut=1,
                dfcheck=(20, 30),
                masspoints="on",
            )
        except Exception:
            raise BinsregError(
                "binsreg could not fit the requested function; "
                "check sample support and design."
            ) from None
    issues = sorted({_issue(str(item.message)) for item in captured})
    if version != "3.2.1":
        issues.append("unverified_backend_version")
    try:
        dots = _table(result.data_plot[0].dots, intervals=False)
        intervals = _table(result.data_plot[0].ci, intervals=True)
        actual = int(result.options.nbins_by[0])
        if (
            actual != result.options.nbins_by[0]
            or actual != dots["bin"].n_unique()
            or actual < 1
        ):
            raise ValueError("inconsistent bins")
        if len(intervals) and not set(intervals["bin"]) <= set(dots["bin"]):
            raise ValueError("inconsistent intervals")
        dot_degree = [int(v) for v in result.options.dots[0]]
        ci_degree = [int(v) for v in result.options.ci[0]]
        for degree, raw in (
            (dot_degree, result.options.dots[0]),
            (ci_degree, result.options.ci[0]),
        ):
            if len(degree) != 2 or not np.array_equal(degree, raw) or min(degree) < 0:
                raise ValueError("invalid degree")
    except (AttributeError, IndexError, TypeError, ValueError, OverflowError):
        raise BinsregError("binsreg returned an unsupported result schema.") from None
    if "constant_interval_fallback" in issues:
        ci_degree = [0, 0]
    if "constant_dots_fallback" in issues:
        dot_degree = [0, 0]
    if (
        dot_degree != [0, 0]
        or (ci_degree != [1, 1] and "constant_interval_fallback" not in issues)
        or (
            isinstance(bins, Integral)
            and actual != bins
            and not any(
                code in issues for code in ("small_effective_sample", "repeated_knots")
            )
        )
    ):
        issues.append("unverified_method_change")
    if not len(intervals):
        issues.append("intervals_unavailable")
    limited = any(
        code in issues
        for code in (
            "small_effective_sample",
            "constant_interval_fallback",
            "insufficient_local_mass_points",
            "rank_drop",
        )
    )
    status = "limited_support" if limited else "approximate_pointwise"
    if (
        "unclassified_upstream_warning" in issues
        or "unverified_backend_version" in issues
        or "unverified_method_change" in issues
    ):
        status = "unverified_method"
        dot_degree = ci_degree = None
    if not len(intervals):
        status = "unavailable"
    metadata = {
        "method": "binsreg",
        "backend_version": version,
        "estimand": "function_in_original_x_at_fixed_controls",
        "x_name": prepared.x_name,
        "y_name": prepared.y_name,
        "control_columns": list(prepared.control_columns),
        "control_design": prepared.control_design.to_dict(),
        "sample": prepared.sample.to_dict(n),
        "coordinates": "original_x_at_fixed_controls",
        "weight_interpretation": "reliability"
        if prepared.weights is not None
        else "unit",
        "bin_covariance": "HC1" if prepared.clusters is None else "cluster",
        "slope_covariance": None,
        "reference_df": None,
        "at": np.asarray(evaluation).tolist(),
        "asyvar": False,
        "control_evaluation_uncertainty_included": False,
        "covariance": "HC1" if prepared.clusters is None else "cluster",
        "reference_distribution": "normal",
        "ci_level": float(ci),
        "n_input": prepared.n_input,
        "n_obs": n,
        "n_missing": prepared.n_missing,
        "n_zero_weight": prepared.n_zero_weight,
        "zero_weight": "drop",
        "n_clusters": None
        if prepared.clusters is None
        else int(np.unique(prepared.clusters).size),
        "requested_bins": bins if isinstance(bins, str) else int(bins),
        "actual_bins": actual,
        "selection_method": "unverified"
        if status == "unverified_method"
        else "rot"
        if "dpi_to_rot_fallback" in issues
        else "effective_sample_fallback"
        if "small_effective_sample" in issues
        else "dpi"
        if bins == "dpi"
        else "fixed_count",
        "requested_binning": binning,
        # Upstream's fallback can replace equal-width placement with quantiles
        # or mass-point categories while retaining the requested options label.
        "actual_binning": None
        if status == "unverified_method" or "constant_dots_fallback" in issues
        else binning,
        "requested_dots": [0, 0],
        "requested_intervals": [1, 1],
        "actual_dots": dot_degree,
        "actual_intervals": ci_degree,
        "inference_status": status,
        "issues": issues,
        "fallback": any("fallback" in issue for issue in issues),
        "few_cluster_coverage_guaranteed": False,
    }
    if issues:
        warnings.warn(
            f"binsreg status {status}: {', '.join(issues)}. See result.metadata.",
            BinsregWarning,
            stacklevel=2,
        )
    return BinsregResult(dots, intervals, metadata)
