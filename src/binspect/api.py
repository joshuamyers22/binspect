"""Public functions for estimating binned scatterplots."""

from __future__ import annotations

import warnings
from collections.abc import Mapping, Sequence
from dataclasses import replace
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike

from .core.binning import compute_binning
from .core.decompose import decompose
from .core.diagnostics import DEFAULT_DIAGNOSTIC_POLICY, DiagnosticPolicy
from .core.estimate import estimate_bins
from .core.lines import fit_ols, fit_sd_line
from .core.selection import select_n_bins
from .exceptions import AdjustedInferenceWarning, InvalidBinningError
from .prepared_data import prepare_data
from .results import BinscatterResult
from .types import BinningMethod, ZeroWeightPolicy

__all__ = ["binscatter"]


def binscatter(
    data: pd.DataFrame | Mapping[str, Any] | None = None,
    y: str | ArrayLike | None = None,
    x: str | ArrayLike | None = None,
    *,
    bins: int | str | ArrayLike = "auto",
    binning: BinningMethod = "quantile",
    weights: str | ArrayLike | None = None,
    zero_weight: ZeroWeightPolicy = "retain",
    controls: str | Sequence[str] | ArrayLike | None = None,
    cluster: str | ArrayLike | None = None,
    ci: float | None = 0.95,
    dropna: bool = True,
    diagnostic_policy: DiagnosticPolicy | None = DEFAULT_DIAGNOSTIC_POLICY,
) -> BinscatterResult:
    """Estimate a binned scatterplot and linear specification diagnostic.

    Parameters
    ----------
    data : pandas.DataFrame or Mapping, optional
        Data containing the variables. Not required when ``x``, ``y``, and
        ``weights`` are array-like.
    y : str or array_like
        Endogenous (response) variable. A string is interpreted as a column in
        ``data``.
    x : str or array_like
        Exogenous (regressor) variable used for binning. A string is interpreted as
        a column in ``data``.
    bins : int, {"auto", "sturges", "iqr", "dpi"}, or array_like, default "auto"
        Number of bins, bin-selection rule, or custom bin edges. Custom edges must
        be strictly increasing and cover the observed range of ``x``.
        ``"dpi"`` requires the optional binsreg dependency and currently supports
        only estimates without weights, controls, or clusters. Failed DPI selection
        raises ``InvalidBinningError`` without falling back to another rule.
    binning : {"quantile", "equal_width"}, default "quantile"
        Partition method. Ignored when custom edges are supplied in ``bins``.
    weights : str or array_like, optional
        Nonnegative reliability weights. At least one weight, and the total weight
        in each bin, must be positive.
    zero_weight : {"retain", "drop"}, default "retain"
        Treatment of zero-weight observations. ``"retain"`` keeps them in bin
        selection, unweighted counts, and descriptive arrays while excluding them
        from estimation and inference. ``"drop"`` removes them before binning, making
        them equivalent to omitted rows. This option has no effect without weights.
    controls : str, sequence of str, or array_like, optional
        Variables partialled out of both ``x`` and ``y`` using Frisch--Waugh--Lovell
        residualization. String values select columns from ``data``. Categorical
        controls are indicator-encoded. A constant is included automatically.
    cluster : str or array_like, optional
        Cluster identifier used for CR1 cluster-robust bin-mean intervals and slope
        standard errors. At least two nonmissing clusters are required.
    ci : float or None, default 0.95
        Two-sided confidence level for bin means. Set to ``None`` to omit confidence
        intervals. With controls, bin SEs and intervals are always unavailable;
        requesting intervals emits ``AdjustedInferenceWarning``. Set ``ci=None``
        for descriptive adjusted bins without that warning.
    dropna : bool, default True
        If True, remove observations with nonfinite values in any input. If False,
        raise a ``ValueError`` when nonfinite values are present.
    diagnostic_policy : DiagnosticPolicy or None, optional
        Descriptive gap/support thresholds. Defaults to gap 0.02 and at least 30
        effective rows per bin. Clustered verdicts require an explicit minimum
        cluster count in the policy; no default count guarantees reliability.
        ``None`` disables classification while retaining estimates and decomposition.

    Returns
    -------
    BinscatterResult
        Estimation results and plotting methods.

    Examples
    --------
    >>> import numpy as np, binspect
    >>> rng = np.random.default_rng(0)
    >>> x = rng.normal(size=5_000)
    >>> y = np.tanh(x) + rng.normal(scale=0.5, size=5_000)
    >>> bs = binspect.binscatter(x=x, y=y, bins=20)
    >>> bs.decomposition.gap > 0.05   # bin means depart from the line
    True

    Notes
    -----
    The bin means are the fitted values from a saturated indicator regression,
    ``OLS(y ~ C(bin))``. The reported lack-of-fit measure is descriptive. It is not
    a hypothesis test for linearity.

    When controls are supplied, ``x`` and ``y`` are residualized on a constant and
    the encoded control matrix, then shifted back to their original weighted means.
    The reported slope equals the coefficient on ``x`` from the corresponding full
    least-squares model. If ``x`` adds no numerical rank beyond the controls on
    positive-weight observations, ``InsufficientDataError`` is raised.

    Confidence intervals assume independent observations unless ``cluster`` is
    supplied. Unadjusted bin intervals are approximate, pointwise and conditional
    on the partition; they omit selection uncertainty. Adjusted-bin SEs, confidence
    limits and reference df are NaN, with ``ci_level=None``, until fitted-control
    uncertainty is validated. Descriptive bins and slope inference remain available.
    See ``result.inference`` for covariance, degrees of freedom and limitations.
    Clustered inference uses cluster-level score sums, a CR1 finite-sample
    correction, and t critical values based on the clusters represented in each bin.

    See Also
    --------
    binspect.results.BinscatterResult
        Results container returned by this function.
    """
    if isinstance(bins, str) and bins == "dpi":
        unsupported = [
            name
            for name, value in (
                ("weights", weights),
                ("controls", controls),
                ("cluster", cluster),
            )
            if value is not None
        ]
        if unsupported:
            raise InvalidBinningError(
                f"DPI selection does not yet support {', '.join(unsupported)}; "
                "use an explicit integer, custom edges, or bins='auto'."
            )
    prepared = prepare_data(
        data,
        y,
        x,
        weights=weights,
        zero_weight=zero_weight,
        controls=controls,
        cluster=cluster,
        dropna=dropna,
    )
    x_arr = prepared.x
    y_arr = prepared.y
    w_arr = prepared.weights
    cluster_arr = prepared.clusters

    if isinstance(bins, (str, int, np.integer)):
        bin_rule = int(bins) if isinstance(bins, np.integer) else bins
        n_bins = select_n_bins(x_arr, bin_rule, y=y_arr, method=binning)
        binning_obj = replace(
            compute_binning(x_arr, n_bins, method=binning),
            rule=bin_rule if isinstance(bin_rule, str) else "fixed",
        )
    else:
        binning_obj = compute_binning(
            x_arr, method="custom", edges=np.asarray(bins, dtype=float)
        )

    estimates = estimate_bins(
        x_arr,
        y_arr,
        binning_obj.assignment,
        binning_obj.n_bins,
        weights=w_arr,
        clusters=cluster_arr,
        ci=ci,
    )
    if prepared.controls:
        if ci is not None:
            warnings.warn(
                "adjusted-bin uncertainty is unavailable: fitted-control uncertainty "
                "is not validated. Bin means and slope inference remain available; "
                "pass ci=None for descriptive adjusted bins without this warning.",
                AdjustedInferenceWarning,
                stacklevel=2,
            )
        estimates = replace(
            estimates,
            se=np.full(estimates.n_bins, np.nan),
            ci_lo=np.full(estimates.n_bins, np.nan),
            ci_hi=np.full(estimates.n_bins, np.nan),
            ci_df=np.full(estimates.n_bins, np.nan),
            ci_level=None,
            se_type="unavailable",
        )
    fit = fit_ols(
        x_arr,
        y_arr,
        weights=w_arr,
        dof_resid=prepared.dof_resid,
        clusters=cluster_arr,
    )
    sd_line = fit_sd_line(x_arr, y_arr, weights=w_arr)
    decomposition = decompose(
        y_arr,
        x_arr,
        binning_obj.assignment,
        binning_obj.n_bins,
        fit,
        fit.r_sq,
        weights=w_arr,
        bin_clusters=estimates.n_clusters,
        diagnostic_policy=diagnostic_policy,
    )

    return BinscatterResult(
        binning=binning_obj,
        estimates=estimates,
        fit=fit,
        sd_line=sd_line,
        decomposition=decomposition,
        x=x_arr,
        y=y_arr,
        weights=w_arr,
        x_name=prepared.x_name,
        y_name=prepared.y_name,
        controls=prepared.controls,
        cluster=prepared.cluster_name,
        zero_weight=zero_weight,
    )
