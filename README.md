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

## Related packages


`binsreg` (Cattaneo, Crump, Farrell, and Feng) provides formal binscatter inference.
`binspect` delegates optimal bin selection to it when requested. Use `binsreg` when
uniform confidence bands or formal shape-restriction tests are required.

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
