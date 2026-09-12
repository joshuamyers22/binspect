# Interpreting diagnostics

The bin means form a saturated bin-indicator fit. The straight line is fitted to
all retained observations, with the requested weights and control adjustment.
Changing the number of bins changes the step fit and its diagnostics; it does not
turn the displayed bin means into the data used for the linear slope.

## Gap and R-squared answer different questions

`eta_sq` is the share of outcome variation explained by bin indicators.
`r_sq_linear` is the observation-level linear R-squared. The bin-indicator model
does not nest the straight line, so their difference can be negative. It is not
the reported gap.

The descriptive gap is `SS_lof / SS_total`, where `SS_lof` sums
`sum_w[j] * (y_mean[j] - fit.predict(x_mean[j]))**2` across bins.
Without weights, `sum_w[j]` equals the bin count. Deviation marks show signed
departures, but their lengths or areas do not equal this weighted squared gap.

```python
import numpy as np
import binspect

rng = np.random.default_rng(31)
x = rng.uniform(-3, 3, 1200)
y = x + 0.6 * x**2 + rng.normal(size=x.size)
result = binspect.binscatter(x=x, y=y, bins=12)
e = result.estimates
ss_lof = np.sum(e.sum_w * (e.y_mean - result.fit.predict(e.x_mean)) ** 2)
assert np.isclose(result.decomposition.gap, ss_lof / result.decomposition.ss_total)
assert result.decomposition.gap >= 0

# The SD reference is signed, including a negative relationship.
negative = binspect.binscatter(x=x, y=-2 * x + rng.normal(size=x.size), bins=12)
assert np.isclose(negative.fit.slope, abs(negative.fit.r) * negative.sd_line.slope)
```

The signed SD line passes through the weighted means. Its slope has magnitude
`sd(y)/sd(x)` with correlation's sign; at zero covariance its orientation is
positive, and constant y gives zero slope. The identity uses **abs(r)**.

## Verdicts are configurable descriptions

The default `DiagnosticPolicy` uses gap threshold 0.02 and at least 30 effective
rows per bin. A gap below that chosen threshold yields `linear` once support
checks pass. It is not a specification test, p-value or power calculation.
`limited support` replaces the former `underpowered bins` wording.

```python
policy = binspect.DiagnosticPolicy(gap_threshold=0.05, min_bin_effective_n=40)
screened = binspect.binscatter(x=x, y=y, bins=12, diagnostic_policy=policy)
disabled = binspect.binscatter(x=x, y=y, bins=12, diagnostic_policy=None)
assert disabled.verdict == "not assessed"
assert screened.decomposition.diagnostic_policy == policy
assert screened.decomposition.verdict_reason
```

Constant outcomes are not assessed. Clustered results are not assessed unless a
cluster threshold is explicitly supplied; that threshold does not validate
interval coverage. Unequal weights affect effective support, and retained
zero-weight rows cannot supply it. Read [weights and clusters](weights.md) before
interpreting uncertainty, and use [structured results](exports.md) rather than
parsing summary prose.
