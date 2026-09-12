# binspect

**Binned scatterplots for linear specification diagnostics.**

`binspect` estimates binned conditional means and compares them with a linear fit to
the underlying observations. The bin means are the fitted values from the saturated
model `OLS(y ~ C(bin))`. Their weighted deviations from the line provide a descriptive
linear specification diagnostic.

![binspect](docs/hero.png)

```python
import binspect

bs = binspect.binscatter(df, y="sales", x="age", bins=20)

bs.table  # per-bin means, SDs, standard errors, intervals
bs.summary_frame()  # one-row model and diagnostic table
bs.to_dict()  # JSON-compatible structured results
print(bs.summary())
bs.plot(theme="paper")
bs.audit(theme="paper")  # plot plus marginal distributions and residuals
```

Adjust both variables for numeric or categorical controls with FWL residualization:

```python
adjusted = binspect.binscatter(
    df,
    y="sales",
    x="age",
    controls=["region", "tenure"],
    bins=20,
)
adjusted.fit.slope  # age coefficient from OLS(sales ~ age + region + tenure)
adjusted.plot()  # axes are explicitly labelled as adjusted
```

Residualized variables retain their original means, keeping the plot on a familiar
scale. Categorical controls are indicator-encoded and a constant is included
automatically. With `weights=`, the projection uses the same reliability weights.

Zero-weight observations are retained by default: they can affect bin boundaries,
unweighted bin counts, and stored descriptive arrays, but never point estimates or
degrees-of-freedom corrections. To make them fully equivalent to omitted rows, set
`zero_weight="drop"`:

```python
trimmed = binspect.binscatter(
    df, y="sales", x="age", weights="sample_weight", zero_weight="drop"
)
```

For comparisons across groups, pooled bin edges are used by default so facets refer
to the same intervals of `x`:

```python
comparison = binspect.compare(
    df,
    y="sales",
    x="age",
    group="region",
    bins=20,
)

comparison.table  # one row per group and bin
comparison.summary_frame()  # one row per group
comparison.plot(sharex=True, sharey=True)
```

Pass `common_bins=False` to select bins separately within each group. The pooled
estimate remains available as `comparison.pooled`.

When using `controls=`, set `common_bins=False`. Pooled and group fits adjust
separately and restore their own means, so their adjusted coordinates do not share
a common partition. Shared bins with controls raise an explicit error until a
common adjusted-coordinate contract is validated.

Tables include only occupied intervals. With shared bins, the `bin` ID and
`x_lo`/`x_hi` bounds refer to the same original interval across groups; IDs can
have gaps where a group has no observations. With independent bins, IDs are local
to each partition and should not be used to join groups as matching x ranges.
`binning.partition_edges` preserves the complete partition and
`binning.interval_ids` maps the compact estimation arrays to those intervals.
The older `binning.edges` remains a compressed partition that folds in empty
intervals; use the table or full partition for interval comparisons. JSON includes
the complete partition and interval IDs.

Use `cluster=` when observations share shocks within a firm, person, location, or
other sampling unit:

```python
clustered = binspect.binscatter(
    df,
    y="sales",
    x="age",
    controls=["region", "tenure"],
    cluster="firm_id",
    bins=20,
)
```

This applies CR1 cluster-robust standard errors to both the fitted slope and bin
means. Bin-mean intervals use a t reference distribution based on the number of
clusters represented in each bin. Bins containing fewer than two positive-weight
clusters have undefined intervals.

Bin intervals are **approximate, pointwise and conditional on the observed
partition and fitted adjustment**. They omit uncertainty from fitting controls
and choosing bins, and provide no simultaneous coverage guarantee. Adjusted-bin
intervals have no validated nominal population-coverage claim. Initial controlled
simulations found undercoverage; see the [inference evidence](docs/inference-contract-review.md).

`bs.inference` (also in JSON) reports covariance, degrees of freedom and these
limitations. Classical slope SEs require their variance model; with weights this
is inverse-variance WLS. Independent weighted bin SEs instead use reliability
variance and effective sample size. HC1 is not supported for returned estimates;
the DPI selector's internal covariance setting does not change that. See the
[statistical analysis plan](docs/STATISTICAL_ANALYSIS_PLAN.md) for the exact contracts.

## Related packages


`binsreg` (Cattaneo, Crump, Farrell, and Feng) provides formal binscatter inference.
`binspect` delegates optimal bin selection to it when requested. Use `binsreg` when
uniform confidence bands or formal shape-restriction tests are required.

## Choosing bins with DPI

Install `binspect-regression[dpi]` and use `bins="dpi"` for binsreg's direct
plug-in count for a piecewise-constant fit. Both quantile and equal-width spacing
are supported. Selection uses the full retained sample with mass-point checks.
It currently requires no `weights`, `controls`, or `cluster`; those combinations
raise an error rather than passing an incomplete specification to the selector.
Use an integer, custom edges, or `bins="auto"` for those estimates.

If DPI cannot produce a finite integer count between two and the retained sample
size, selection raises `InvalidBinningError`. There is no rule-of-thumb fallback
or silent count clipping. binspect constructs its own edges and may merge bins
for tied/discrete x; it does not promise identical knots or intervals to binsreg.

`bs.bin_rule`, `bs.binning.requested_bins`, and `bs.n_bins` distinguish the rule,
selected count, and realized count. JSON and summary exports include this metadata
and a `None` fallback. Groups sharing pooled edges report `bin_rule="pooled"` and
the originating rule in `bs.binning.source_rule`; the pooled result retains the
original selection count.

## What it draws

The default plot presents the estimates, uncertainty, linear fit, lack of fit, and
distribution of the exogenous variable as separate layers.

| Layer | What it shows | Default |
|---|---|---|
| `bins` | Bin means — the saturated-model fitted values | on |
| `ci` | Confidence bar per bin mean | on |
| `fit` | OLS line through the underlying data | on |
| `deviation` | Shading between bin means and the line — the lack of fit | on |
| `rug` | x-density, so quantile bins can't hide their own imbalance | on |
| `sd_line` | Slope σy/σx — the OLS line is this flattened by `r` | off |
| `smooth` | Local-linear smoother through the bin means | off |
| `raw` | Underlying observations at low alpha | off |

Three themes are included: `notebook` (default), `paper` (thin, serif, grayscale-safe),
and `deck` (larger marks and type). Themes are colorblind-safe and scoped; importing
`binspect` does not modify global `rcParams`.

Use `bs.audit()` for a composed diagnostic figure with the unchanged binscatter in
the central panel, marginal histograms, and OLS residuals against fitted values.
Either companion view can be omitted with `marginals=False` or `residuals=False`.
These panels describe the stored estimate; they do not add a formal specification
test.

## One thing to know about η²

The bin-indicator model does not nest the linear model. Consequently, η² can be below
the linear R² when bins are coarse, and their difference is not a valid curvature
measure. `binspect` reports normalized lack of fit,

```
SS_lof = Σⱼ nⱼ (ȳⱼ − ŷ(x̄ⱼ))²      gap = SS_lof / SS_total
```

which is nonnegative by construction and corresponds to the deviations shown in the
plot. This quantity is descriptive and is not a formal test of linearity.

## Status

Initial alpha release (`0.1.0`). The API may continue to evolve during the `0.x`
series. The distribution name is `binspect-regression`; the import remains `binspect`.

**Not yet implemented:** uniform confidence bands and quantile regression. Without
`cluster=`, standard errors are `sd/√n` within bin and assume independent
observations.

## Install

```bash
git clone https://github.com/joshuamyers22/binspect.git && cd binspect
pip install -e ".[dev]"
pytest
```

Install the published package with `pip install binspect-regression` and continue to
write `import binspect`.

For contributing, release checks, and development conventions, see
[CONTRIBUTING.md](CONTRIBUTING.md). Please report vulnerabilities privately as
described in [SECURITY.md](SECURITY.md).

Maintainer release instructions are in [RELEASING.md](RELEASING.md).

## License

MIT.

## Citation

The methodology this package leans on is Cattaneo, M. D., Crump, R. K., Farrell,
M. H., & Feng, Y. (2024). "On Binscatter." *American Economic Review*, 114(5),
1488–1514. If you use binned scatterplots for inference, cite that paper and consider
using `binsreg` directly.
