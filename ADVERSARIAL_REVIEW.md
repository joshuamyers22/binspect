# Adversarial review

Status: resolved on `main` after the review.

Scope: the repository was clean at `ecd24d7` (`main`), so this review covers the
checked-out tree rather than an uncommitted diff.

## Findings

### P1 — Custom edges with empty outer bins corrupt the `Binning` invariant

`src/binspect/core/binning.py:170-190` removes empty bins and renumbers their
assignments, but chooses retained interior edges using the original bin numbers and
always preserves both original outer edges. If the custom range extends past the
observed data and a leading or trailing interval is empty, `n_bins` is reduced while
`edges` can remain at its original length. This violates the documented invariant
`len(edges) == n_bins + 1` and makes the public `result.table` property fail.

Reproduction:

```python
import numpy as np
import binspect

r = binspect.binscatter(
    x=np.array([1.5, 1.6, 2.5, 2.6]),
    y=np.arange(4.0),
    bins=[0, 1, 2, 3],
)

assert r.n_bins == 2
assert len(r.binning.edges) == 4  # should be 3
r.table  # ValueError: All arrays must be of the same length
```

These edges satisfy the public contract: they are strictly increasing and cover the
full observed range. Empty outer intervals should either be retained consistently or
collapsed while rebuilding exactly one boundary around each resulting occupied bin.
A regression test should cover empty leading, trailing, and interior intervals.

Resolution: empty intervals are collapsed by retaining one original boundary before
each occupied bin after the first, while preserving custom outer bounds. Regression
tests cover leading, trailing, interior, and consecutive interior empty intervals,
including reconstruction of assignments from the returned edges and construction of
the public result table.

### P1 — Zero-weight observations change slope standard errors

`src/binspect/core/lines.py:73-81` uses the total array length to calculate residual
degrees of freedom and the classical variance normalization even though zero-weight
rows contribute nothing to the fit. The clustered CR1 factor at line 103 has the
same issue. With controls, `src/binspect/api.py:313-316` also counts zero-weight rows
in `dof_resid`. Consequently, appending observations with weight zero leaves the
coefficients unchanged but changes both classical and cluster-robust slope standard
errors. A zero-weight observation should be equivalent to omitting it.

Reproduction:

```python
import numpy as np
from binspect.core.lines import fit_ols

rng = np.random.default_rng(1)
x = rng.normal(size=20)
y = 2 * x + rng.normal(size=20)
w = np.r_[np.ones(16), np.zeros(4)]

weighted = fit_ols(x, y, weights=w)
dropped = fit_ols(x[:16], y[:16])

assert weighted.slope == dropped.slope
assert weighted.se_slope == dropped.se_slope  # fails: 0.4451 != 0.5047
```

The effective row count for degrees-of-freedom corrections should exclude rows with
zero weight throughout both the unadjusted and controlled paths. Add invariance tests
for classical, cluster-robust, and controlled fits.

Resolution: inferential degrees of freedom now count only positive-weight
observations. The public `zero_weight=` policy lets users choose whether zero-weight
rows remain in bin selection and descriptive counts (`"retain"`, the default) or are
removed before binning (`"drop"`). Classical, cluster-robust, controlled, grouped,
and omission-equivalence cases are covered by regression tests.

## Verification

Both reproductions now pass, and the expanded suite covers the reported cases.
