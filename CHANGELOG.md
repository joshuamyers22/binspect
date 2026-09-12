# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Diagnostic support excludes retained zero-weight rows and uses effective sample
  size for unequal weights. Signed SD and deviation-layer explanations now state
  the absolute-correlation identity and distinguish visual marks from squared gap.
- Control projection and numerical-rank checks normalize design columns, retaining
  identified slope/df behavior when control units change or columns are redundant.
  `x` in the numerical control span on positive-weight rows now raises
  `InsufficientDataError` instead of fitting a slope from numerical roundoff.
- Grouped tables and JSON retain original interval IDs and bounds when bins are
  empty, so groups with disjoint support no longer report renumbered or stretched
  intervals as matching bins. Group-specific binning and value errors now identify
  the group while preserving their exception type and cause.
- Plain `import binspect` and ordinary estimation defer Matplotlib initialization
  until a plotting export or method is requested, avoiding font-cache background
  work during non-plotting use. Public `THEMES` and `theme` imports remain available.
- `bins="dpi"` now uses binsreg's direct plug-in count instead of its regularized
  rule-of-thumb count, with explicit piecewise-constant model, requested spacing,
  and mass-point checks. Missing/invalid counts and numerical selection failures
  raise an actionable error without a silent fallback or count clipping.
- The missing-DPI-dependency message now names `binspect-regression[dpi]`.

### Changed
- `underpowered bins` is now `limited support`; no power calculation is implied.
  Constant outcomes and clustered results without an explicit cluster threshold
  return `not assessed` with an exported reason. Numerical estimates are unchanged.
- With controls, public bin SEs, confidence limits and reference df are unavailable
  (NaN / JSON null), with `ci_level=None` and explicit inference status, following
  failed population-coverage validation. Means, dispersion and slope SEs remain.
  Requesting adjusted intervals emits `AdjustedInferenceWarning`; `ci=None`
  requests descriptive adjusted bins without that warning.
- `compare(controls=..., common_bins=True)` now raises an explicit unsupported-
  combination error. Use `common_bins=False` for independently adjusted group
  fits; pooled and within-group adjustment do not share a common coordinate system.
- Table `bin` values identify the original partition interval and can contain gaps.
  Estimation arrays and `binning.assignment` keep compact indices. Consumers joining
  grouped rows should use IDs only when `common_bins=True`; use `x_lo`/`x_hi` for
  original bounds instead of compressed `binning.edges`.
- DPI selection now rejects `weights`, `controls`, and `cluster` until those
  integrations are validated. Previously these options were omitted from the
  upstream selector. Other bin rules remain available with these options.

### Added
- Optional `binspect.binsreg()` and `BinsregResult` delegate original-coordinate
  function inference to binsreg with joint control covariance, HC1 or clustered
  covariance, DPI/fixed counts and explicit fallback status. Copied dot/interval
  tables, JSON, summary and plotting keep this target separate from FWL diagnostics.
  Few-cluster constant-fit fallbacks carry `limited_support`, without a coverage
  guarantee. Matched backend references and prespecified development coverage
  join the required quality gate.
- Immutable `DiagnosticPolicy` for `binscatter` and `compare`, with configurable
  gap/effective-row/cluster thresholds and `None` to disable classification.
  Exports distinguish retained, positive-weight and effective rows, plus policy
  values, support minima and decision reasons.
- Locked binsreg method checks document control uncertainty, higher-degree
  function intervals and small-cluster warnings/fallbacks as independent references.
- A prespecified nonflat/DPI and few-cluster development coverage gate with a
  retained aggregate report and tested failure accounting. Uneven-cluster
  undercoverage remains explicit evidence for qualified review, not a passing
  production inference claim.
- A statistical analysis plan, locked Statsmodels reference checks and seeded
  coverage protocol, enforced by a separate `inference-validation` CI job.
- `result.inference` and JSON/summary metadata expose covariance, residual/reference
  degrees of freedom and interval limitations. Bin intervals are explicitly
  approximate and pointwise when available; selection uncertainty is omitted, and
  adjusted-bin uncertainty is withheld. HC1 remains unsupported by binscatter/compare.
- `binning.partition_edges` and `binning.interval_ids`, also included in JSON,
  preserve full partition boundaries and occupied interval identity. Legacy
  compressed edges and no-gap table behavior remain available.
- `bin_rule` on results and rule/source/fallback metadata on partitions; JSON and
  summary exports include selection provenance and requested/actual bin counts.
  Grouped estimates using pooled edges identify the pooled source rule.
- A required CI job tests DPI against the locked binsreg dependency, including
  equal-width spacing and discrete-input success/failure cases.

## [0.1.1] - 2026-09-09

### Added
- `cluster=` support in `binscatter()` and `compare()`, with CR1 cluster-robust
  standard errors for bin means and fitted slopes, cluster-based t intervals, and
  inference metadata in result exports and summaries.
- `zero_weight="retain" | "drop"` in both public estimators, allowing callers to
  choose whether zero-weight observations remain in binning and descriptive counts or
  are treated as omitted rows.

### Fixed
- Classical and CR1 slope degrees-of-freedom corrections now exclude zero-weight
  observations, including estimates adjusted for controls.
- Custom partitions with empty leading, trailing, or interior intervals now rebuild
  their retained boundaries so ``len(edges) == n_bins + 1`` and result tables remain
  constructible.

## [0.1.0] - 2026-08-25

### Added
- The installable distribution is named `binspect-regression` while retaining the
  concise `binspect` import package, avoiding a collision with an existing PyPI project.
- A release workflow builds and validates artifacts separately from its narrowly
  permissioned PyPI Trusted Publishing job.
- `compare()` and `BinscatterCollection` for grouped estimation, tidy combined tables,
  pooled results, and faceted plots with common bin edges by default.
- `summary_frame()` and JSON-compatible `to_dict()` exports for single and grouped
  results.
- `BinscatterResult.audit()` for a composed binscatter, marginal-distribution, and
  residual diagnostic figure.
- Numeric and categorical `controls=` using weighted Frisch--Waugh--Lovell
  residualization in single and grouped estimates.

### Changed
- Public docstrings now follow statsmodels-style numpydoc conventions and terminology.
- The text summary uses regression-results labels and numbered assumption notes.
- README prose now distinguishes descriptive diagnostics from formal inference more
  consistently. Plot annotations and layer labels are unchanged.
- Quantile, equal-width and custom binning with a documented tie convention
  (ties go to the lower bin).
- Per-bin means, within-bin SDs, standard errors and t-intervals, with weight support.
- OLS fit line and SD line, with the `slope = r * sd_slope` identity under test.
- Between/within variance decomposition, eta-squared, lack of fit, and a linearity
  verdict.
- `BinscatterResult` with `.table`, `.decomposition_table`, `.summary()` and `.plot()`.
- Eight composable plot layers and three scoped themes (`notebook`, `paper`, `deck`).

### Notes
- `gap` is defined as lack of fit, `SS_lof / SS_total`, **not** as
  `eta_sq - r_sq_linear`. The latter can be negative for coarse bins because a step
  function does not nest a straight line; see `binspect/core/decompose.py`.

### Fixed (pre-release, during initial build)
- Custom edges are preserved and must cover the observed x range; they are no longer
  silently replaced by the sample minimum and maximum.
- Multidimensional inputs and zero-weight bins now fail with actionable errors instead
  of reaching low-level NumPy failures or producing non-finite diagnostics.
- Public documentation no longer describes lack of fit as `eta_sq - r_sq_linear`.
- Matplotlib theme typing now passes the project's strict mypy configuration.
- Fit and SD lines now span the bin means rather than the full data range; a handful
  of tail observations previously stretched the axes past every bin.
- Rug, confidence bars and deviation shading each draw as a single collection instead
  of one artist per observation; the rug is added with `autolim=False` so context
  never drives autoscaling.
