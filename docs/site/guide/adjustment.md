# Adjusting for controls

`binscatter(controls=...)` residualizes both x and y against an intercept and the
encoded controls, using the same weights as estimation. It restores each sample's
weighted means for display. The observation-level FWL slope equals the x
coefficient in the corresponding full linear design. Regression on the displayed
bin means generally gives a different answer.

## Descriptive bins in adjusted coordinates

```python
import numpy as np
import polars as pl
import binspect

rng = np.random.default_rng(42)
n = 1500
z = rng.normal(size=n)
x = 0.3 * z + rng.normal(size=n)
y = 0.7 * x + 2 * z + rng.normal(size=n)
frame = pl.DataFrame({"x": x, "y": y, "z": z})
adjusted = binspect.binscatter(frame, x="x", y="y", controls="z", bins=10, ci=None)
full_slope = np.linalg.lstsq(np.column_stack([np.ones(n), z, x]), y, rcond=None)[0][-1]
assert np.isclose(adjusted.fit.slope, full_slope)
assert adjusted.adjusted
assert np.isnan(adjusted.estimates.se).all()
assert adjusted.estimates.ci_level is None
assert "adjusted" in adjusted.x_label.lower()
```

Adjusted-bin SEs, confidence limits and reference df are unavailable because
population-coverage validation failed. Means, dispersion and slope uncertainty
remain available. Asking for intervals emits `AdjustedInferenceWarning`;
`ci=None` requests descriptive bins without that warning. An x in the numerical
control span raises `InsufficientDataError`. Redundant controls are permitted when
x remains identified; this is not a near-singular accuracy guarantee.

Numeric/boolean controls stay numeric. String/categorical controls use reference
coding, with numeric columns first. Ordinary strings/Polars Categorical sort
observed levels after filtering. Declared Polars Enum/pandas Categorical levels
retain their order and unused levels. Inspect `control_design.to_dict()` or the
exported design, especially when building explicit evaluation vectors.

## A separate original-coordinate function target

The optional `binsreg` adapter jointly fits a function of original x and controls.
Its intervals do **not** apply to the residualized bins above. It requires `[dpi]`,
a full-rank encoded design, and sufficient support.

```python
function = binspect.binsreg(frame, x="x", y="y", controls="z", bins="dpi")
assert isinstance(function.dots, pl.DataFrame)
assert function.metadata["coordinates"] == "original_x_at_fixed_controls"
assert function.metadata["asyvar"] is False
assert function.metadata["control_evaluation_uncertainty_included"] is False
status = function.metadata["inference_status"]
issues = function.metadata["issues"]
```

Controls are evaluated at positive-weight sample means by default. `at='zero'`
or a vector in `metadata['control_columns']` order selects fixed encoded values.
Full coefficient covariance includes fitted-control uncertainty; uncertainty in
the chosen evaluation values is omitted. Normal paths request degree-0 dots and
degree-1 pointwise intervals with HC1 or clustered covariance and a normal reference.

Inspect `status`, `issues` and actual method metadata: upstream fallbacks can
change count, degree and placement. Unknown warnings or backend versions are
unverified. Three uneven clusters produced 42.4% development coverage at nominal
95% for the function fallback; there is no few-cluster guarantee. See the
[adapter evidence](https://github.com/joshuamyers22/binspect/blob/main/docs/binsreg-adapter-review.md)
and [public estimators](../reference/estimation.md).
