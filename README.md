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
print(bs.summary())
bs.plot(theme="paper")
```

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

Pre-release (`0.1.0.dev0`). Both APIs may change before the first stable release. The
distribution name is `binspect-regression`; the import remains `binspect`.

**Not yet implemented:** covariate adjustment via FWL residualization, cluster-robust
standard errors, uniform confidence bands, and quantile regression. Standard errors are
currently `sd/√n` within bin and assume independent observations.

## Install

```bash
git clone https://github.com/joshuamyers22/binspect.git && cd binspect
pip install -e ".[dev]"
pytest
```

Once published, users will install the package with
`pip install binspect-regression` and continue to write `import binspect`.

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
