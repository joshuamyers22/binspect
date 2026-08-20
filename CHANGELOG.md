# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- The installable distribution is named `binspect-regression` while retaining the
  concise `binspect` import package, avoiding a collision with an existing PyPI project.
- A release workflow builds and validates artifacts separately from its narrowly
  permissioned PyPI Trusted Publishing job.
- `compare()` and `BinscatterCollection` for grouped estimation, tidy combined tables,
  pooled results, and faceted plots with common bin edges by default.
- `summary_frame()` and JSON-compatible `to_dict()` exports for single and grouped
  results.

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
