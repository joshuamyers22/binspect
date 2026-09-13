# Public API inventory

Snapshot of unreleased A2 `9a6db9f`, inspected on 2026-09-12 for A3. This is the
current callable/attribute inventory, not a new API or a release announcement.
See [compatibility, supported combinations and migrations](COMPATIBILITY.md) and
[table/JSON meanings](INPUT_OUTPUT_CONTRACT.md). Implementation sources are
[top-level exports](../src/binspect/__init__.py), [types](../src/binspect/types.py),
[results](../src/binspect/results.py), [collections](../src/binspect/comparison_results.py),
[adapter results](../src/binspect/binsreg_results.py) and
[visualization exports](../src/binspect/viz/__init__.py).

Signatures below retain parameter names, order, positional/keyword boundaries,
defaults and return annotations from `inspect.signature`; parameter annotations
are omitted for readability. `<factory>` means a fresh dataclass default (the
Theme rc dictionary). They are declarations, not executable examples. Result
properties and dataclass fields come from inspection, including inherited methods.
Regenerate/recheck against runtime signatures when the public surface changes.

## Top-level exports

`THEMES`, `AdjustedInferenceWarning`, `BinCountWarning`, `BinscatterCollection`, `BinscatterResult`, `BinspectError`, `BinsregError`, `BinsregResult`, `BinsregWarning`, `DiagnosticPolicy`, `InsufficientDataError`, `InvalidBinningError`, `__version__`, `binscatter`, `binsreg`, `compare`, `theme`.

`__version__` currently equals `"0.1.1"`; `THEMES` is lazily loaded.

```text
binscatter(
    data=None,
    y=None,
    x=None,
    *,
    bins='auto',
    binning='quantile',
    weights=None,
    zero_weight='retain',
    controls=None,
    cluster=None,
    ci=0.95,
    dropna=True,
    diagnostic_policy=DiagnosticPolicy(gap_threshold=0.02, min_bin_effective_n=30.0, min_bin_clusters=None),
) -> BinscatterResult
compare(
    data=None,
    y=None,
    x=None,
    *,
    group,
    bins='auto',
    binning='quantile',
    weights=None,
    zero_weight='retain',
    controls=None,
    cluster=None,
    ci=0.95,
    dropna=True,
    common_bins=True,
    diagnostic_policy=DiagnosticPolicy(gap_threshold=0.02, min_bin_effective_n=30.0, min_bin_clusters=None),
) -> BinscatterCollection
binsreg(
    data=None,
    y=None,
    x=None,
    *,
    controls=None,
    weights=None,
    cluster=None,
    bins='dpi',
    binning='quantile',
    at='mean',
    ci=0.95,
    dropna=True,
) -> BinsregResult
theme(name, **overrides) -> Iterator[Theme]
```

`data`, x/y, controls, weights and labels follow the positional
[input contract](INPUT_OUTPUT_CONTRACT.md). `DiagnosticPolicy` thresholds must be
finite, with gap at least zero and effective rows at least one; the optional
cluster threshold is an integer at least two.
`None` disables classification. Clustered verdicts need an explicit threshold.

### `DiagnosticPolicy`

Constructor:

```text
DiagnosticPolicy(gap_threshold=0.02, min_bin_effective_n=30.0, min_bin_clusters=None) -> None
```

Stored public fields: `gap_threshold`, `min_bin_effective_n`, `min_bin_clusters`.

## Results

All single/grouped summary and estimate tables are Polars DataFrames. Explicit
`to_pandas` calls return independent pandas DataFrames. `summary()` returns text;
`to_dict()`/`to_evidence()` return independent JSON-compatible dictionaries and
`to_json()` returns strict JSON text. There is no universal `.table` or
`.summary_frame()` on the function adapter, or `.summary()` on collections.

Stored numeric arrays are read-only owned snapshots. `x`/`y` hold retained data
in original or mean-restored FWL coordinates; `weights` may be None. `controls`
and `cluster` are names, not raw control/cluster observations. `sample` and
`control_design` may be None for direct construction. Counts distinguish retained,
positive-weight and effective observations. `inference` describes actual covariance,
reference df and availability; `x_label`/`y_label` expose adjusted-axis labels.
`residuals_from_fit()` returns editable observation residuals.

Collection `results` is a copied read-only mapping with immutable result values;
`pooled` is a separate single result and `groups` preserves first appearance.
Collection `include_pooled` applies to summary conversions only, not bin tables.
Adapter `dots`/`intervals` and nested `metadata` are independent projections.
The adapter constructor's underscore-prefixed storage is inventoried but internal.

### `BinscatterResult`

Constructor:

```text
BinscatterResult(
    binning,
    estimates,
    fit,
    sd_line,
    decomposition,
    x,
    y,
    weights,
    x_name,
    y_name,
    controls=(),
    cluster=None,
    zero_weight='retain',
    sample=None,
    control_design=None,
) -> None
```

Stored public fields: `binning`, `estimates`, `fit`, `sd_line`, `decomposition`, `x`, `y`, `weights`, `x_name`, `y_name`, `controls`, `cluster`, `zero_weight`, `sample`, `control_design`.

Properties: `adjusted`, `bin_rule`, `decomposition_table`, `inference`, `n_bins`, `n_effective`, `n_obs`, `n_positive`, `table`, `verdict`, `x_label`, `y_label`.

```text
audit(
    self,
    *,
    theme='notebook',
    show=None,
    annotate='audit',
    marginals=True,
    residuals=True,
    hist_bins=30,
    **kwargs,
) -> Figure
plot(self, ax=None, *, theme='notebook', show=None, annotate='minimal', **kwargs) -> Axes
residuals_from_fit(self) -> FloatArray
summary(self) -> str
summary_frame(self) -> pl.DataFrame
to_dict(self) -> dict[str, Any]
to_evidence(self, *, provenance=None, exported_at=None) -> dict[str, Any]
to_json(self) -> str
to_pandas(self, table='bins') -> pd.DataFrame
```

### `BinscatterCollection`

Constructor:

```text
BinscatterCollection(results, pooled, group_name, common_bins) -> None
```

Stored public fields: `results`, `pooled`, `group_name`, `common_bins`.

Properties: `groups`, `table`.

```text
plot(
    self,
    *,
    layout='facets',
    ncols=None,
    sharex=True,
    sharey=True,
    theme='notebook',
    show=None,
    annotate='minimal',
    legend=False,
    layer_kwargs=None,
) -> Figure
summary_frame(self, *, include_pooled=False) -> pl.DataFrame
to_dict(self) -> dict[str, Any]
to_evidence(self, *, provenance=None, exported_at=None) -> dict[str, Any]
to_json(self) -> str
to_pandas(self, table='bins', *, include_pooled=False) -> pd.DataFrame
```

### `BinsregResult`

Constructor:

```text
BinsregResult(_dots, _intervals, _metadata) -> None
```

Properties: `dots`, `intervals`, `metadata`.

```text
plot(self, ax=None) -> Axes
summary(self) -> str
to_dict(self) -> dict[str, Any]
to_evidence(self, *, provenance=None, exported_at=None) -> dict[str, Any]
to_json(self) -> str
to_pandas(self, table='dots') -> pd.DataFrame
```

## Nested result values and public types

These fields are available through returned results; computing them independently
requires the numerical preconditions documented in the source. `LineFit` inherits
`Line.predict`. Binning arrays use compact estimation indices; `interval_ids` maps
them to original intervals in `partition_edges`. Legacy `edges` compresses empty
intervals. Bin estimates follow compact order; unavailable numeric values are NaN.
Decomposition reports descriptive sums, gap, support and policy, not a test result.
`SampleCounts.to_dict(n_obs)` requires the retained count from its owning result.

### `Line`

Constructor:

```text
Line(slope, intercept) -> None
```

Stored public fields: `slope`, `intercept`.

```text
predict(self, x) -> FloatArray | float
```

### `LineFit`

Constructor:

```text
LineFit(
    slope,
    intercept,
    se_slope,
    r,
    r_sq,
    n_obs,
    se_type='classical',
    n_clusters=None,
    df_resid=None,
    inference_df=None,
) -> None
```

Stored public fields: `slope`, `intercept`, `se_slope`, `r`, `r_sq`, `n_obs`, `se_type`, `n_clusters`, `df_resid`, `inference_df`.

```text
predict(self, x) -> FloatArray | float
```

### `Binning`

Constructor:

```text
Binning(
    edges,
    assignment,
    n_bins,
    method,
    requested_bins,
    rule='fixed',
    source_rule=None,
    fallback=None,
    _partition_edges=None,
    _interval_ids=None,
) -> None
```

Stored public fields: `edges`, `assignment`, `n_bins`, `method`, `requested_bins`, `rule`, `source_rule`, `fallback`.

Properties: `interval_ids`, `partition_edges`, `was_reduced`.

```text
counts(self) -> IntArray
```

### `BinEstimates`

Constructor:

```text
BinEstimates(
    x_mean,
    y_mean,
    y_sd,
    n,
    sum_w,
    se,
    ci_lo,
    ci_hi,
    ci_level,
    se_type='independent',
    n_clusters=None,
    ci_df=None,
    n_positive=None,
    n_effective=None,
) -> None
```

Stored public fields: `x_mean`, `y_mean`, `y_sd`, `n`, `sum_w`, `se`, `ci_lo`, `ci_hi`, `ci_level`, `se_type`, `n_clusters`, `ci_df`, `n_positive`, `n_effective`.

Properties: `n_bins`.

### `Decomposition`

Constructor:

```text
Decomposition(
    ss_between,
    ss_within,
    ss_total,
    ss_lof,
    eta_sq,
    r_sq_linear,
    gap,
    verdict,
    min_bin_n,
    min_bin_positive_n=None,
    min_bin_effective_n=None,
    min_bin_clusters=None,
    verdict_reason='legacy result',
    diagnostic_policy=DiagnosticPolicy(gap_threshold=0.02, min_bin_effective_n=30.0, min_bin_clusters=None),
) -> None
```

Stored public fields: `ss_between`, `ss_within`, `ss_total`, `ss_lof`, `eta_sq`, `r_sq_linear`, `gap`, `verdict`, `min_bin_n`, `min_bin_positive_n`, `min_bin_effective_n`, `min_bin_clusters`, `verdict_reason`, `diagnostic_policy`.

```text
as_dict(self) -> dict[str, float | str | int | bool | None]
```

### `SampleCounts`

Constructor:

```text
SampleCounts(n_input, n_missing, n_zero_weight_dropped, dropna, n_missing_group=0) -> None
```

Stored public fields: `n_input`, `n_missing`, `n_zero_weight_dropped`, `dropna`, `n_missing_group`.

```text
to_dict(self, n_obs) -> dict[str, Any]
```

### `ControlDesign`

Constructor:

```text
ControlDesign(columns=(), encoding_json='[]') -> None
```

Stored public fields: `columns`, `encoding_json`.

```text
to_dict(self) -> dict[str, Any]
```

### Type aliases from `binspect.types`

- `AnnotateLevel = typing.Literal['minimal', 'audit']`
- `BinRule = typing.Union[int, typing.Literal['auto', 'sturges', 'iqr', 'dpi'], NDArray[numpy.float64]]`
- `BinningMethod = typing.Literal['quantile', 'equal_width', 'custom']`
- `FloatArray = NDArray[numpy.float64]`
- `IntArray = NDArray[numpy.int64]`
- `Layer = typing.Literal['raw', 'deviation', 'rug', 'fit', 'sd_line', 'ci', 'bins', 'smooth']`
- `Verdict = typing.Literal['linear', 'curvature', 'limited support', 'not assessed']`
- `ZeroWeightPolicy = typing.Literal['retain', 'drop']`

## Plot composition and standalone layers

Every layer below takes `(ax, result, *, theme='notebook', ...)`, renders a
`BinscatterResult` and returns the same Axes. `**kwargs` forward artist styling
options; they do not add statistical options. The following table lists those
Matplotlib destinations. Unknown style options follow Matplotlib validation.

| Layer | Display / additional controls | Styling destination |
|---|---|---|
| `raw_layer` | Retained observation points | `Axes.scatter` |
| `deviation_layer` | Signed departure to `target='fit'` or `'smooth'`; not squared gap/area | `Axes.vlines` |
| `rug_layer` | Up to `max_ticks=2000`, deterministic sampling; does not drive autoscaling | `LineCollection` |
| `fit_layer` | Observation-level OLS/WLS; `span='bins'` or `'data'` | `Axes.plot` |
| `sd_line_layer` | Signed SD reference; fit slope = abs(r) × SD slope; same span options | `Axes.plot` |
| `smooth_layer` | Descriptive local-linear smooth of bin means; no public bandwidth option | `Axes.plot` |
| `ci_layer` | Available pointwise mean limits; no drawing when unavailable | `Axes.vlines` |
| `bins_layer` | Bin means; `size_by_n=False`, optionally scale by retained raw counts | `Axes.scatter` |
| `annotate_layer` | `level='minimal'` or `'audit'`; four `upper/lower left/right` corners | `Axes.text` |

`plot` accepts per-layer options in `layer_kwargs`, including an `annotate` entry.
Only requested layers consume their entries. Unknown `show` names raise; unused
`layer_kwargs` entries are currently ignored, not additional supported layers.
`caption_text` uses the same two caption levels. `annotate=None` is supported by
composition methods, not by standalone `caption_text`/`annotate_layer`.
Fit/SD lines span the bin means with 4% padding by default; `'data'` spans all
retained observations. The default fit legend label remains `'OLS fit'` even for
weighted fits; callers can set a more specific label through `layer_kwargs`.

Public viz exports: `DEFAULT_LAYERS`, `LAYER_ORDER`, `PALETTES`, `THEMES`, `Palette`, `Theme`, `annotate_layer`, `audit`, `bins_layer`, `caption_text`, `ci_layer`, `deviation_layer`, `fit_layer`, `get_palette`, `get_theme`, `plot`, `raw_layer`, `rug_layer`, `sd_line_layer`, `smooth_layer`, `theme`.

`DEFAULT_LAYERS = ('deviation', 'rug', 'fit', 'ci', 'bins')`

`LAYER_ORDER = ('raw', 'deviation', 'rug', 'fit', 'sd_line', 'smooth', 'ci', 'bins')`

```text
annotate_layer(ax, result, *, theme='notebook', level='minimal', loc='upper left', **kwargs) -> Axes
audit(
    result,
    *,
    theme='notebook',
    show=None,
    annotate='audit',
    marginals=True,
    residuals=True,
    hist_bins=30,
    layer_kwargs=None,
) -> Figure
bins_layer(ax, result, *, theme='notebook', size_by_n=False, label='Bin mean', **kwargs) -> Axes
caption_text(result, level='minimal') -> str
ci_layer(ax, result, *, theme='notebook', **kwargs) -> Axes
deviation_layer(ax, result, *, theme='notebook', target='fit', **kwargs) -> Axes
fit_layer(ax, result, *, theme='notebook', span='bins', label='OLS fit', **kwargs) -> Axes
get_palette(name) -> Palette
get_theme(name) -> Theme
plot(
    result,
    ax=None,
    *,
    theme='notebook',
    show=None,
    annotate='minimal',
    legend=False,
    title=None,
    layer_kwargs=None,
) -> Axes
raw_layer(ax, result, *, theme='notebook', **kwargs) -> Axes
rug_layer(ax, result, *, theme='notebook', max_ticks=2000, **kwargs) -> Axes
sd_line_layer(ax, result, *, theme='notebook', span='bins', label='SD line', **kwargs) -> Axes
smooth_layer(ax, result, *, theme='notebook', label=None, **kwargs) -> Axes
theme(name, **overrides) -> Iterator[Theme]
```

## Themes and palettes

`THEMES` and `PALETTES` each have `notebook`, `paper`, `deck` keys.
`get_theme` accepts a name or Theme; `get_palette` accepts a name.
`theme(name, **overrides)` yields the resolved Theme inside an rcParams context;
overrides are Matplotlib rc keys. Constructor defaults below describe custom
Theme construction, not every named preset. Named presets override sizes, fonts,
colors and other styles; see the [preset definitions](../src/binspect/viz/theme.py)
and [palette values](../src/binspect/viz/palette.py). Frozen Theme/Palette dataclasses
do not make Theme.rc or the registries deeply immutable.

### `Theme`

Constructor:

```text
Theme(
    name,
    palette,
    rc=<factory>,
    marker_size=34.0,
    marker_edge=0.0,
    fit_width=2.0,
    sd_width=1.4,
    sd_dashes=(6.0, 4.0),
    ci_width=1.5,
    ci_alpha=0.55,
    deviation_width=7.0,
    deviation_alpha=0.28,
    rug_alpha=0.45,
    rug_height=0.022,
    raw_alpha=0.16,
    raw_size=5.0,
    annotate_alpha=0.06,
) -> None
```

Stored public fields: `name`, `palette`, `rc`, `marker_size`, `marker_edge`, `fit_width`, `sd_width`, `sd_dashes`, `ci_width`, `ci_alpha`, `deviation_width`, `deviation_alpha`, `rug_alpha`, `rug_height`, `raw_alpha`, `raw_size`, `annotate_alpha`.

### `Palette`

Constructor:

```text
Palette(accent, neutral, deviation, text, raw) -> None
```

Stored public fields: `accent`, `neutral`, `deviation`, `text`, `raw`.

## Exception and warning hierarchy

```text
AdjustedInferenceWarning(UserWarning)
BinCountWarning(UserWarning)
BinspectError(Exception)
BinsregError(BinspectError)
BinsregWarning(UserWarning)
InsufficientDataError(BinspectError)
InvalidBinningError(BinspectError)
```

Triggers and handling are in the [compatibility policy](COMPATIBILITY.md).

## Exported core primitives (internal estimation surface)

These existing `binspect.core.__all__` functions are recorded to avoid confusing
importability with the supported application estimator. The public API boundary
adds input handling, inference withdrawal, metadata and owned result composition.
No new stability or population-inference promise is conferred on these primitives.
The returned core value attributes are inventoried above because application
results expose them.

```text
compute_binning(x, n_bins=None, *, method='quantile', edges=None) -> Binning
decompose(
    y,
    x,
    assignment,
    n_bins,
    fit,
    r_sq_linear,
    *,
    weights=None,
    bin_clusters=None,
    diagnostic_policy=DiagnosticPolicy(gap_threshold=0.02, min_bin_effective_n=30.0, min_bin_clusters=None),
) -> Decomposition
estimate_bins(x, y, assignment, n_bins, *, weights=None, clusters=None, ci=0.95) -> BinEstimates
fit_ols(x, y, *, weights=None, dof_resid=None, clusters=None) -> LineFit
fit_sd_line(x, y, *, weights=None) -> Line
residualize(values, controls, *, weights=None) -> FloatArray
select_n_bins(x, rule='auto', *, y=None, method='quantile') -> int
```

Exported legacy module constants: `binspect.core.selection.DEFAULT_MAX_BINS = 40`, `binspect.core.selection.DEFAULT_MIN_BINS = 5`, `binspect.core.decompose.GAP_THRESHOLD = 0.02`, `binspect.core.decompose.MIN_BIN_FOR_VERDICT = 30`.
