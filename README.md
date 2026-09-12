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
    ci=None,  # adjusted bins are descriptive; slope uncertainty remains available
)
adjusted.fit.slope  # age coefficient from OLS(sales ~ age + region + tenure)
adjusted.plot()  # axes are explicitly labelled as adjusted
```

Residualized variables retain their original means, keeping the plot on a familiar
scale. Categorical controls are indicator-encoded and a constant is included
automatically. With `weights=`, the projection uses the same reliability weights.
FWL preserves the coefficient fitted to observation-level residuals. A regression
on the displayed bin means generally has a different slope.

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

Few or highly uneven clusters can produce severe undercoverage even when CR1
arithmetic is correct. In a controlled development case with three clusters sized
480/60/60, nominal 95% bin intervals covered the population target only 78.2% of
the time. Cluster count alone is not a reliability guarantee; see the
[expanded coverage evidence](docs/expanded-coverage-review.md).

Unadjusted bin intervals are **approximate, pointwise and conditional on the
observed partition**. They omit uncertainty from choosing bins and provide no
simultaneous coverage guarantee.

With `controls=`, bin standard errors and confidence limits are unavailable
(NaN in tables, null in JSON) because fitted-control uncertainty is not validated.
Bin means, dispersion and slope uncertainty remain available. Requesting intervals
issues `AdjustedInferenceWarning`; pass `ci=None` for descriptive adjusted bins
without that warning. Controlled simulations found 87.4% coverage at nominal 95%;
see the [withdrawal decision](docs/adjusted-inference-boundary-review.md). An `x`
that adds no numerical rank beyond the controls on positive-weight observations
raises `InsufficientDataError`.

`bs.inference` (also in JSON) reports covariance, degrees of freedom and these
limitations. Classical slope SEs require their variance model; with weights this
is inverse-variance WLS. Independent weighted bin SEs instead use reliability
variance and effective sample size. HC1 is not supported by `binscatter`/`compare`;
the DPI selector's internal covariance setting does not change that. See the
[statistical analysis plan](docs/STATISTICAL_ANALYSIS_PLAN.md) for the exact contracts.

## Related packages


`binsreg` (Cattaneo, Crump, Farrell, and Feng) provides formal binscatter inference.
`binspect` delegates optimal bin selection and, through the separate adapter below,
pointwise function inference to it when requested. Use `binsreg` directly when
uniform confidence bands or formal shape-restriction tests are required.

## Adjusted function inference with binsreg

The unreleased optional adapter fits binsreg's function in the original x
coordinates, jointly with numeric or categorical controls:

```python
# Install this checkout with: pip install -e ".[dpi]"
function = binspect.binsreg(
    df, y="sales", x="age", controls=["region", "tenure"], bins="dpi"
)
function.dots  # degree-0 dot estimates
function.intervals  # pointwise limits and their own fitted centers
function.metadata  # target, control evaluation, covariance, actual method, issues
print(function.summary())
function.plot()
```

Controls are evaluated at positive-weight sample means by default. Use `at="zero"`
or an explicit vector in `metadata["control_columns"]` order to choose fixed
encoded-control values. The full coefficient covariance includes estimated-control
uncertainty (`asyvar=False`); uncertainty in the chosen evaluation values themselves
is omitted. The normal path uses degree-1 intervals and HC1 covariance. `weights=`
and `cluster=` pass through to binsreg after consistent complete-case filtering;
zero-weight rows are always dropped and counts are exported.

Use an integer `bins=` for a fixed count and `binning="equal_width"` for equal-width
spacing. Fixed counts can leave approximation bias; upstream warnings are exposed
as `BinsregWarning` and controlled issue codes. With few clusters, binsreg may
reduce bins and return constant-fit intervals. These have `limited_support`
status, explicit actual settings and **no few-cluster coverage guarantee**.
Fallback may also change knot placement; `actual_binning=None` reports that the
requested spacing is not certified in that path.
Unrecognized warnings or an unvalidated backend version give `unverified_method`.
The locked reference version is binsreg 3.2.1. See the
[adapter protocol](docs/BINSREG_ADAPTER_PLAN.md) for the target and coverage scope.
Prespecified development coverage at nominal 95% was 93.6% for adjusted iid DPI,
94.3% with 60 balanced clusters and 42.4% for the three-uneven-cluster fallback.
See the [results and limitations](docs/binsreg-adapter-review.md).

`BinsregResult` has separate copied dot/interval tables, metadata and strict-JSON
`to_dict()` output. It supplies function estimates without an FWL slope or gap
verdict. Its intervals do not apply to the residualized bins from `binscatter`.

## Result ownership

Results own snapshots of their numeric data. Changing input arrays, dataframe
columns, weights or custom edges after estimation does not change the result.
`result.x`, `result.y`, `result.weights`, and arrays in `binning` and `estimates`
are read-only. Use `result.x.copy()` when you need an editable array; to change
an estimate, run estimation again with the changed inputs. Array access shares
immutable numeric storage but returns a fresh array header, so changing a
returned array's shape or dtype also leaves the result intact.

Grouped results own a read-only copy of the group mapping and share immutable
single-result objects. Use immutable hashable group labels, such as strings,
numbers or dates; mutable custom label objects are outside this contract.
Tables, summaries, inference dictionaries and `to_dict()` exports are independent
editable projections. The binsreg adapter similarly returns copied dot/interval
tables and nested metadata. Public result access does not expose writable stored
numeric data; deliberate private-attribute or native-memory tampering is outside
this API contract.

Snapshot construction copies the retained numeric buffers once per container;
reading an array does not copy its values. This trades memory for stable results.
See the [ownership verification and memory measurements](docs/result-ownership-review.md).

## Choosing bins with DPI

For `binscatter`/`compare`, install `binspect-regression[dpi]` and use `bins="dpi"` for binsreg's direct
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

## Diagnostic policy

Verdicts are configurable descriptive heuristics. The defaults use a gap threshold
of 0.02 and require at least 30 effective rows in every bin. `linear` means the gap
falls below that chosen cutoff; it is not evidence from a specification test.
`limited support` replaces the former `underpowered bins` label. Constant outcomes
and clustered results without an explicit cluster threshold are `not assessed`.

```python
policy = binspect.DiagnosticPolicy(gap_threshold=0.05, min_bin_effective_n=40)
screened = binspect.binscatter(df, y="sales", x="age", diagnostic_policy=policy)
descriptive = binspect.binscatter(df, y="sales", x="age", diagnostic_policy=None)
```

`compare` applies the same policy to pooled and group results. An explicit
`min_bin_clusters` enables clustered classification using both cluster and effective
row thresholds; it does not validate confidence coverage. Policy values, support
minima and decision reasons are exported in decomposition/summary records.
`n_obs` and bin `n` count retained rows; `n_positive` and `n_effective` separately
report positive-weight and Kish effective rows. Cluster counts remain separate.
Retained zero-weight rows cannot supply diagnostic support.

The signed SD reference obeys `OLS slope = abs(correlation) * SD slope`, including
negative relationships. At exactly zero covariance its orientation is positive;
constant y gives zero slope. Deviation marks show signed departures; displayed
area or length does not equal the weighted squared gap.

## Status

Initial alpha release (`0.1.0`). The API may continue to evolve during the `0.x`
series. The distribution name is `binspect-regression`; the import remains `binspect`.

**Not yet implemented:** uniform confidence bands and quantile regression.
Without controls, weights or clusters, bin standard errors are `sd/√n` and assume
independent observations. Weighted/clustered conventions and the adjusted-bin
uncertainty restriction are described above.

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
