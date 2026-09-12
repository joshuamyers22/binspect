# Choosing bins

`binscatter`/`compare` default to `bins='auto'` and `binning='quantile'`.
`auto` targets about 100 retained rows per bin; `sturges` and `iqr` are alternative
descriptive rules. Suggested counts are clipped to the current 5–40 range with
a sample-size ceiling. An integer ≥2 requests a count; ties and empty intervals
can reduce the realized count. Quantile bins can have unequal counts for discrete x.

```python
import numpy as np
import binspect

rng = np.random.default_rng(64)
x = rng.normal(size=1200)
y = np.sin(x) + rng.normal(size=x.size)
quantiles = binspect.binscatter(x=x, y=y, bins=10)
equal = binspect.binscatter(x=x, y=y, bins=10, binning="equal_width")
assert quantiles.binning.method == "quantile"
assert equal.binning.method == "equal_width"

edges = np.linspace(x.min(), x.max(), 9)
custom = binspect.binscatter(x=x, y=y, bins=edges)
assert custom.bin_rule == "custom"
assert np.array_equal(custom.binning.partition_edges, edges)
```

Custom edges must be strictly increasing and cover observed x. Ties exactly on
interior boundaries go to the lower interval. Supply edges via `bins=edges`;
`binning='custom'` alone cannot choose them. Inspect `bin_rule`,
`binning.requested_bins` and `n_bins` rather than assuming the requested count
equals the occupied count. Sparse/merged partitions can emit `BinCountWarning`.

`binning.assignment` uses compact indices for estimation arrays. Table `bin` values
are original interval IDs and can have gaps. `binning.interval_ids` maps compact
indices to full `partition_edges`; legacy `binning.edges` compresses empty
intervals. Use full bounds for [group comparisons](groups.md).

## DPI selection is explicit

```python
# Requires the optional [dpi] extra.
dpi = binspect.binscatter(x=x, y=y, bins="dpi")
assert dpi.bin_rule == "dpi"
assert dpi.binning.fallback is None
```

This selects binsreg's actual direct plug-in count for a piecewise-constant model,
then builds binspect's partition. Quantile and equal-width spacing are supported.
It rejects weights, controls and clusters rather than passing an incomplete
specification to the selector. Use an integer, custom edges or another rule for
those diagnostic fits. Missing/invalid counts or selection failures raise
`InvalidBinningError`; no silent ROT fallback or clipping is applied.

The separate [function adapter](adjustment.md#a-separate-original-coordinate-function-target)
does accept DPI with weights/controls/clusters, but has a different estimand and
reports upstream fallbacks. Selecting DPI does not change binspect's bin/slope
covariance convention or validate population coverage.
