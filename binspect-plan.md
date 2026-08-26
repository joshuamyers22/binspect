# binspect — project plan

*Name settled. The implementation has reached the original v0.4 scope; the roadmap
below is retained as a record of the project's initial sequencing.*

> This is a living roadmap, not a statement that every listed module or feature is
> implemented. The README is the source of truth for current behavior.

A binned scatterplot library that produces figures you can publish without redrawing,
and diagnostics that tell you whether the regression underneath the figure is lying.

---

## 0. Naming

**`binspect`** — bin + inspect, which states the premise: binning as a way of
inspecting a model, not just a way of drawing points. The repository and import
package use `binspect`; the PyPI distribution uses `binspect-regression` because the
original distribution name belongs to an unrelated project.

Do before the first commit:

- [x] Verify `binspect` on PyPI (taken); select `binspect-regression` as the
  distribution name
- [x] Claim the GitHub repo (and the org/user namespace if you want one)
- [ ] Check the readthedocs slug even if docs go to GH Pages, to keep it from being squatted

Known friction to live with: it reads at a glance as a typo of Python's stdlib
`inspect`, so docs and the README should always render it in code style and spell out
the bin/inspect derivation once, up top.

Taken, do not use: `binsreg`, `binscatter`.

---

## 1. Positioning

Two packages already occupy this space:

- **`binsreg`** (Cattaneo, Crump, Farrell, Feng) — the authoritative implementation.
  Partition selection, LS/quantile/GLM binscatter, pointwise CIs, uniform bands,
  shape-restriction tests, covariate adjustment, clustering. Statistically definitive,
  API is a Stata port; users routinely wrap it just to get a readable DataFrame.
- **`binscatter`** (PyPI) — narwhals-backed multi-backend dataframes, plotly output,
  DPI bin selection. Pretty and modern; says nothing about your model.

**The gap:** neither treats the binscatter as a *regression diagnostic*. The bin means
are the saturated-dummy fit; the deviation of those means from the fitted line is
exactly the nonlinearity your linear model is eating. Nobody surfaces that.

**One-liner:** `binsreg` for inference, `binscatter` for a quick plot, `binspect` for
auditing a regression you're about to publish — in a figure that's already
presentation-ready.

**Non-goals for v1:** multi-backend dataframes (that's the other package's
differentiator), reimplementing binsreg's inference theory (depend on it, cite it),
interactive/web output.

---

## 2. Design principles

1. **Every audit quantity has a visual form.** If a diagnostic can only be communicated
   as a number in a corner, it does not go in the default plot. Normalized lack of fit
   becomes deviation marks. Bin uncertainty becomes CI bar length. Sample imbalance
   becomes the density rug.
2. **Estimation is usable without plotting.** `plot()` is a method on a result object,
   never the entry point. This is what makes the statistics testable in isolation.
3. **`ax` in, `ax` out.** Drops into an existing figure; never owns the figure unless
   explicitly asked.
4. **Never mutate global rcParams on import.** Themes are opt-in, scoped, and reversible.
5. **Layers are addressable.** Each visual layer callable standalone against an axes,
   so someone can put deviation shading over their own scatter.
6. **Defaults are honest.** Where a prettier option means something different from the
   rigorous one (shading to a smoother vs. to the OLS line), the rigorous one is the
   default and the pretty one is explicit.

---

## 3. Public API

```python
import binspect

bs = binspect.binscatter(
    data=df,
    y="sales",
    x="age",
    controls=["region", "tenure"],  # FWL-residualized before binning
    bins="dpi",  # int | "dpi" | "iqr" | array of edges
    binning="quantile",  # "quantile" | "equal_width" | "custom"
    weights=None,  # column name or array
    cluster="firm_id",  # for robust SEs
    ci=0.95,  # None disables CI computation
    bands="pointwise",  # None | "pointwise" | "uniform"
)
```

### Result object

```python
bs.table            # DataFrame: bin, n, x_lo, x_hi, x_mean, y_mean, y_sd, se, ci_lo, ci_hi
bs.decomposition    # DataFrame: ss_between, ss_within, ss_total, eta_sq, r_sq_linear, gap
bs.fit              # slope, intercept, se, r_sq of the linear fit (post-residualization)
bs.sd_line          # slope, intercept of the SD line (r-shrinkage reference)
bs.n_obs, bs.n_bins, bs.bin_rule

bs.summary()        # statsmodels-flavored text block
bs.summary_frame()  # one-row DataFrame of model and diagnostic statistics
bs.to_dict()        # JSON-compatible structured results
bs.verdict          # "linear" | "curvature" | "underpowered bins"

bs.plot(ax=None, theme="notebook", show=(...), annotate="minimal") -> Axes
bs.audit(theme="notebook") -> Figure       # multi-panel, v0.4
```

### Grouped comparison

```python
comparison = binspect.compare(
    data=df,
    y="sales",
    x="age",
    group="region",
    bins=20,
    common_bins=True,
)

comparison.results  # mapping of group label -> BinscatterResult
comparison.pooled  # pooled BinscatterResult
comparison.table  # group-by-bin DataFrame
comparison.summary_frame()  # one row per group
comparison.plot()  # faceted Figure with shared axes by default
```

### Plot layers

```python
show = ("bins", "ci", "fit", "sd_line", "deviation", "rug", "smooth", "raw")
```

| Layer | Draws | Default |
|---|---|---|
| `bins` | Bin-mean markers, optionally sized by n | on |
| `ci` | Vertical CI bars per bin | on when `ci` computed |
| `fit` | OLS line through the underlying data | on |
| `sd_line` | Slope σy/σx through the point of averages | off |
| `deviation` | Shading between bin means and the fit | on |
| `rug` | x-density strip beneath the axis | on |
| `smooth` | LOWESS/spline through the bin means | off |
| `raw` | Underlying scatter at low alpha | off |

Each is also importable standalone:

```python
from binspect.viz.layers import deviation_layer

deviation_layer(ax, bs, color="...", alpha=0.18)
```

### Themes

Three shipped, all colorblind-safe, all tested on light and dark backgrounds:

| Theme | For | Character |
|---|---|---|
| `notebook` | Default, exploratory | Balanced, matplotlib-native sizing |
| `paper` | Publication | Thin strokes, no fills, survives grayscale print |
| `deck` | Slides | Heavy marks, large type, one saturated accent |

Applied per-call (`bs.plot(theme="paper")`) or scoped
(`with binspect.theme("paper"): ...`). Never globally on import.

### Annotation levels

- `annotate=None` — nothing
- `annotate="minimal"` (**default**) — n, bin count
- `annotate="audit"` — adds R², η², gap, verdict

---

## 4. Repository structure

```
binspect/
├── src/
│   └── binspect/
│       ├── __init__.py             # public exports: binscatter, theme, __version__
│       ├── api.py                  # binscatter() entry point, arg validation, orchestration
│       ├── types.py                # TypedDicts, Literals, protocol for array-likes
│       ├── exceptions.py           # BinspectError, InsufficientDataError, BinCountWarning
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── binning.py          # partition rules -> bin edges + assignment
│       │   ├── selection.py        # bin-count selectors (dpi, iqr, sturges, fixed)
│       │   ├── residualize.py      # FWL projection of y and x on controls
│       │   ├── estimate.py         # bin means, SDs, weighted means, SEs
│       │   ├── variance.py         # homoskedastic / HC1 / cluster-robust variance
│       │   ├── decompose.py        # between/within SS, eta^2, linear R^2, gap
│       │   └── lines.py            # OLS fit line, SD line, optional smoother
│       │
│       ├── results.py              # BinscatterResult dataclass + summary()
│       │
│       ├── viz/
│       │   ├── __init__.py
│       │   ├── figure.py           # plot() and audit() composition
│       │   ├── layers.py           # one function per layer, all (ax, result) -> ax
│       │   ├── theme.py            # theme registry, context manager, rcParams scoping
│       │   ├── annotate.py         # caption block rendering
│       │   └── palette.py          # colorblind-safe ramps, light/dark variants
│       │
│       └── datasets/
│           ├── __init__.py         # load_gapminder(), load_wage(), load_synthetic()
│           └── data/               # small CSVs, < 100 KB each
│
├── tests/
│   ├── conftest.py                 # fixtures: linear DGP, concave DGP, heteroskedastic DGP
│   ├── test_binning.py             # partition properties
│   ├── test_selection.py           # selector behavior + monotonicity
│   ├── test_residualize.py         # FWL equivalence
│   ├── test_estimate.py            # bin means == saturated dummy OLS
│   ├── test_variance.py            # cluster SE vs statsmodels
│   ├── test_decompose.py           # SS identity, eta^2 >= R^2
│   ├── test_results.py             # table schema, summary snapshot
│   ├── test_api.py                 # end-to-end, arg validation, error messages
│   ├── test_properties.py          # hypothesis-based invariants
│   ├── test_themes.py              # no global rcParams leakage
│   ├── test_plot.py                # layer smoke tests, ax-in/ax-out contract
│   ├── test_baseline_images.py     # pytest-mpl, 4 baselines max
│   ├── baseline/                   # reference PNGs for pytest-mpl
│   └── external/
│       └── test_vs_binsreg.py      # non-blocking cross-check, marked "external"
│
├── docs/
│   ├── index.md                    # the one-liner + hero figure
│   ├── quickstart.md
│   ├── guide/
│   │   ├── what-is-a-binscatter.md
│   │   ├── auditing-a-regression.md   # the differentiator; lead with this
│   │   ├── controls-and-fwl.md
│   │   ├── choosing-bins.md
│   │   └── themes-and-styling.md
│   ├── reference/                  # mkdocstrings-generated API docs
│   ├── comparison.md               # honest table vs binsreg and binscatter
│   └── references.md               # Cattaneo et al. and related literature
│
├── examples/
│   ├── 01-quickstart.ipynb
│   ├── 02-auditing-a-published-regression.ipynb
│   ├── 03-controls-and-fwl.ipynb
│   └── 04-theme-gallery.ipynb
│
├── benchmarks/
│   └── bench_estimate.py           # asv or pytest-benchmark; 10M-row path
│
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                  # lint, type, test matrix
│   │   ├── docs.yml                # build + deploy to Pages on main
│   │   ├── external.yml            # weekly binsreg cross-check, non-blocking
│   │   └── release.yml             # tag-triggered PyPI trusted publishing
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.yml
│   │   └── feature_request.yml
│   └── PULL_REQUEST_TEMPLATE.md
│
├── .pre-commit-config.yaml
├── .gitignore
├── pyproject.toml
├── uv.lock
├── mkdocs.yml
├── CHANGELOG.md                    # Keep a Changelog format
├── CITATION.cff
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── LICENSE                         # MIT
└── README.md
```

---

## 5. Module responsibilities

| Module | Owns | Must not |
|---|---|---|
| `api.py` | Validation, orchestration, building the result | Contain statistical formulas |
| `core/binning.py` | Edges and integer bin assignment | Know about y |
| `core/selection.py` | Choosing bin count; wraps binsreg DPI if installed | Hard-depend on binsreg |
| `core/residualize.py` | FWL projection, categorical expansion of controls | Touch binning |
| `core/estimate.py` | Per-bin means, SDs, counts, weighted variants | Compute variance-covariance |
| `core/variance.py` | SEs: homoskedastic, HC1, cluster | Know about bins directly |
| `core/decompose.py` | SS decomposition, η², linear R², gap, verdict | Import matplotlib |
| `core/lines.py` | OLS line, SD line, smoother | Draw anything |
| `results.py` | Immutable container, table assembly, `summary()` | Do estimation |
| `viz/*` | All matplotlib | Do any statistics |

**Hard rule:** nothing under `core/` imports matplotlib; nothing under `viz/` computes
a statistic. Enforced by an import-linter contract in CI.

---

## 6. Statistical specification

Definitions the implementation must satisfy exactly, not approximately.

**Binning.** Quantile binning with J bins assigns observation i to bin
j = ceil(J · F̂(xᵢ)), clipped to [1, J]. Bin counts differ by at most one. Ties in x
go to the lower bin; document this, since it makes quantile bins uneven on discrete x.

**Bin means.** ȳⱼ = Σ_{i∈j} wᵢyᵢ / Σ_{i∈j} wᵢ. Equivalently, the fitted values of
`OLS(y ~ C(bin) - 1)`. This equivalence is a test, not a comment.

**Residualization (FWL).** With controls W, compute ỹ = M_W y and x̃ = M_W x where
M_W = I − W(W'W)⁻¹W'. Bin on x̃, plot ỹ. Add back the means of y and x so the axes
stay on the original scale. The slope through the bin means then equals the coefficient
on x from `OLS(y ~ x + W)`.

**Decomposition.**
```
SS_total   = Σ (yᵢ − ȳ)²
SS_between = Σⱼ nⱼ (ȳⱼ − ȳ)²
SS_within  = Σⱼ Σ_{i∈j} (yᵢ − ȳⱼ)²
SS_lof     = Σⱼ nⱼ (ȳⱼ − ŷ(x̄ⱼ))²
η²         = SS_between / SS_total
R²_linear  = from OLS(y ~ x)
gap        = SS_lof / SS_total ≥ 0
```

> **Correction (found during implementation).** An earlier draft of this plan defined
> `gap = η² − R²_linear` and claimed `η² ≥ R²_linear` always. That is false. A step
> function does not nest a straight line, so a coarse partition can explain *less*
> variance than a line: on a linear DGP with 3 bins, η² sits ~7.7 points *below* R².
> The gap is therefore defined as normalised **lack of fit**, which is non-negative by
> construction and is exactly what the deviation-shading layer draws — each shaded
> segment is one term's square root. η² is still reported; it just cannot be
> differenced against R². Note also that the classical lack-of-fit / pure-error split
> is exact only with replicated x; with binned x it is approximate, so `gap` is a
> descriptive magnitude, not an F-test numerator.

**Verdict thresholds** (fixed heuristics in v0.1; make configurable before calling the
API stable, and never present them as hypothesis tests):
- `gap < 0.02` → `"linear"`  *(gap = lack of fit, per the correction above)*
- `gap ≥ 0.02` and min bin count ≥ 30 → `"curvature"`
- min bin count < 30 → `"underpowered bins"` (dominates; η² is inflated here)

**SD line.** Slope sign(r)·σy/σx through (x̄, ȳ). The OLS slope is this shrunk by r.

**Warnings.** Emit `BinCountWarning` when J > n/30, when any bin has < 10
observations, or when x has fewer distinct values than J.

---

## 7. Testing strategy

The identities above give exact assertions rather than tolerance-fudging. This is
where credibility comes from.

### Equivalence tests (exact, to float tolerance)

| Test | Assertion |
|---|---|
| Saturated fit | Bin means == fitted values of `OLS(y ~ C(bin))` from statsmodels |
| Between estimator | Count-weighted OLS on bin means == between-variance estimator |
| SS identity | `ss_between + ss_within == ss_total` to machine precision |
| FWL | Slope through bin means (with controls) == `x` coefficient of full OLS |
| Bound | `gap ≥ 0` always; `gap == 0` iff the bin means lie on the line |
| Anti-bound | η² < R²_linear on a linear DGP with coarse bins — asserted, so nobody "fixes" it back |
| Shrinkage | `ols_slope == r * sd_line_slope` |
| Cluster SE | Matches `statsmodels` `cov_type="cluster"` on the saturated model |

### Property tests (hypothesis)

- Bin assignment is a partition: every row in exactly one bin, counts sum to n
- Quantile bin counts differ by at most one
- Results invariant to row permutation
- Slope equivariant under affine rescaling: `y → a·y + b`, `x → c·x + d`
- Weighted result with all-equal weights == unweighted result
- Adding a constant column to `controls` changes nothing

### Fixture DGPs (`conftest.py`)

Linear, concave, heteroskedastic, clustered, weighted, and a discrete-x edge case.
Fixed seeds; the concave one is the fixture that catches η²/gap regressions.

### Visual tests

`pytest-mpl` with **four** baselines maximum — default notebook plot, paper theme,
audit panel, deviation layer alone. Image tests rot; keep them few and regenerate
deliberately. Everything else is a smoke test asserting artist counts and that the
returned object is the axes that was passed in.

### Isolation tests

- Importing `binspect` leaves `matplotlib.rcParams` byte-identical
- `with binspect.theme(...)` restores rcParams on exit, including on exception
- `import-linter` contract: `core` has no matplotlib import path

### External (non-blocking)

Weekly workflow comparing bin means and CIs against `binsreg` on a fixed dataset.
Divergence opens an issue; it does not fail the build.

---

## 8. Tooling and CI

| Concern | Choice |
|---|---|
| Env/deps | Standard `venv`/pip locally; `uv` as the CI installer |
| Build backend | `hatchling` |
| Lint + format | `ruff` (replaces black, isort, flake8) |
| Types | `mypy --strict` on `src/` only |
| Tests | `pytest`, `pytest-cov`, `pytest-mpl`, `hypothesis` |
| Import boundaries | `import-linter` |
| Hooks | `pre-commit` |
| Docs | `mkdocs-material` + `mkdocstrings` |
| Versioning | SemVer, `0.x` until the API settles |
| Changelog | Keep a Changelog |

**Matrix:** Python 3.10–3.13 × {ubuntu-latest, macos-latest}. macOS is worth the runner
minutes — matplotlib backend behavior differs and you develop there.

**Coverage gate:** 85% overall. Prefer identity and behavior tests over line chasing;
plot tests should assert meaningful artist and axes contracts.

**Release:** tag-triggered workflow using PyPI trusted publishing (OIDC). No long-lived
token in repository secrets.

### Dependencies

```
Required:  numpy, pandas, scipy, matplotlib
Optional:
  [stats]  statsmodels          # richer SEs, formula interface
  [dpi]    binsreg              # DPI bin selection
  [polars] polars               # zero-copy input path
  [dev]    pytest, hypothesis, pytest-mpl, ruff, mypy, import-linter, pre-commit
  [docs]   mkdocs-material, mkdocstrings[python]
```

A stats package that pulls plotly and five dataframe backends on `pip install` is one
people vendor around. Keep the required set to four.

---

## 9. `pyproject.toml` skeleton

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "binspect"
dynamic = ["version"]
description = "Binned scatterplots that audit the regression behind them"
readme = "README.md"
requires-python = ">=3.10"
license = { file = "LICENSE" }
authors = [{ name = "..." }]
keywords = ["binscatter", "regression", "diagnostics", "visualization", "econometrics"]
classifiers = [
  "Development Status :: 3 - Alpha",
  "Intended Audience :: Science/Research",
  "License :: OSI Approved :: MIT License",
  "Topic :: Scientific/Engineering :: Visualization",
]
dependencies = ["numpy>=1.24", "pandas>=2.0", "scipy>=1.10", "matplotlib>=3.7"]

[project.optional-dependencies]
stats = ["statsmodels>=0.14"]
dpi = ["binsreg>=1.0"]
polars = ["polars>=0.20"]
dev = ["pytest", "pytest-cov", "pytest-mpl", "hypothesis", "ruff", "mypy",
       "import-linter", "pre-commit"]
docs = ["mkdocs-material", "mkdocstrings[python]"]

[project.urls]
Homepage = "https://github.com/<you>/binspect"
Documentation = "https://<you>.github.io/binspect"
Changelog = "https://github.com/<you>/binspect/blob/main/CHANGELOG.md"

[tool.ruff]
line-length = 88
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B", "SIM", "NPY", "PD"]

[tool.mypy]
strict = true
files = ["src/binspect"]

[tool.pytest.ini_options]
addopts = "--strict-markers --mpl"
markers = ["external: cross-checks against binsreg (not run in CI gate)"]

[tool.importlinter]
root_package = "binspect"

[[tool.importlinter.contracts]]
name = "core is plotting-free"
type = "forbidden"
source_modules = ["binspect.core"]
forbidden_modules = ["matplotlib"]
```

---

## 10. Roadmap

The original v0.1-v0.4 implementation scope is complete as of the `0.1.0` package
release. Version labels below describe the order in which capabilities were built,
not the final package versions in which they shipped. Cluster-robust standard errors,
uniform confidence bands, and quantile regression remain future work.

### v0.1 — it exists and it looks right
Quantile binning, bin means and SDs, `.table`, `notebook` theme, layers `bins` + `fit`
+ `sd_line`. No inference, no controls. Aesthetics are in scope from day one —
"we'll make it look good later" is how the incumbents ended up here.
*Ship early and let the API get criticized before it hardens.*

### v0.2 — the differentiator
Decomposition, η²/gap/verdict, deviation-shading layer, audit annotation block,
`paper` and `deck` themes, `summary()`.

### v0.3 — controls and inference
FWL residualization, weights, CIs, HC1 and cluster-robust SEs, density rug,
`bins="dpi"` via optional binsreg dependency.

### v0.4 — the audit panel
`bs.audit()` multi-panel figure (binscatter, residuals vs fitted, bin-count strip),
grouped/faceted comparison of two or more series.

### v0.5+ — candidates, unordered
Quantile-regression variant (median + IQR bands — the boxplot answer), uniform
confidence bands, polars fast path, `patsy`/formula interface, seaborn-style
`data=`+`hue=` API.

---

## 11. Open decisions

1. **Deviation shading target.** To the OLS line (honest audit) or to a smoother
   (prettier, means something different). *Leaning: line as default, smoother explicit.*
2. **Does `raw` scatter ship in v0.1?** Overlaying the underlying points undercuts the
   premise but is the first thing reviewers ask for.
3. **statsmodels: optional or required?** Optional keeps the dep set clean but means
   reimplementing cluster-robust variance, which is exactly the code most likely to be
   subtly wrong. *Leaning: required, and drop the `[stats]` extra.*
4. **Verdict strings in the default annotation?** A package that stamps
   "curvature" on someone's figure by default may read as presumptuous.
5. **Bin-count warning as `warnings.warn` or a field on the result?** Warnings are
   noisy in notebooks; a silent field gets ignored.

---

## 12. First week

1. Reserve `binspect` on PyPI and GitHub (§0 checklist).
2. `uv init`, repo skeleton, MIT license, pre-commit, CI green on an empty test.
3. `core/binning.py` + `core/estimate.py` with the saturated-fit equivalence test.
   This single test is the project's foundation — write it before anything else.
4. `core/decompose.py` with the SS identity test.
5. `results.py`, minimal `.table`.
6. `viz/layers.py`: bins + fit only, `notebook` theme, ax-in/ax-out contract test.
7. README with one hero figure generated from `examples/01`.

---

## References

- Cattaneo, M. D., Crump, R. K., Farrell, M. H., & Feng, Y. (2024). On Binscatter.
  *American Economic Review*, 114(5), 1488–1514.
- `binsreg` — https://nppackages.github.io/binsreg/
- Starmer, C. et al. — prior art review to complete before v0.1 announcement.
