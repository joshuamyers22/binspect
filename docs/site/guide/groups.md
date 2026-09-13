# Comparing groups

`compare` produces group results and a pooled estimate. Group order is first
appearance, with supported immutable scalar labels. Missing group labels are
excluded first, even with `dropna=False`; other estimation inputs follow joint
complete-case filtering. Python equality defines identity (`1`, `1.0`, `True`
identify the same group). Typed JSON preserves portable label descriptions.

## Shared partitions and occupied support

```python
import numpy as np
import polars as pl
import binspect

rng = np.random.default_rng(75)
n = 1200
x = rng.uniform(-3, 3, n)
z = rng.normal(size=n)
frame = pl.DataFrame(
    {
        "x": x,
        "y": x + z + rng.normal(size=n),
        "z": z,
        "group": np.where(x < 0, "left", "right"),
    }
)
shared = binspect.compare(frame, x="x", y="y", group="group", bins=6)
assert shared.common_bins
assert shared.pooled.n_obs == n
table = shared.table.select("group", "bin", "x_lo", "x_hi", "n")
left_ids = set(shared.results["left"].table["bin"])
right_ids = set(shared.results["right"].table["bin"])
assert len(left_ids & right_ids) < min(len(left_ids), len(right_ids))
assert shared.summary_frame(include_pooled=True).height == 3
```

With `common_bins=True` (default), edges come from the pooled sample. A shared
`bin` ID identifies the same original interval in every group, even if empty
intervals produce gaps in one group's table. There is no estimated row for empty
support; do not invent a zero mean or connect disjoint regions as shared evidence.
The pooled result remains available as `.pooled` and is not included in `.table`.
Use `is_pooled` in a pooled summary to distinguish its null group value.

## Independent adjusted coordinates

```python
adjusted = binspect.compare(
    frame,
    x="x",
    y="y",
    group="group",
    controls="z",
    common_bins=False,
    bins=6,
    ci=None,
)
assert not adjusted.common_bins
assert all(result.adjusted for result in adjusted.results.values())
assert all(result.estimates.ci_level is None for result in adjusted.results.values())
```

Controls require `common_bins=False`: pooled and group fits residualize separately
and restore their own means, so they do not share adjusted coordinates. Equal IDs
under independent binning are local labels, not matching x intervals. This option
also selects counts/edges separately for unadjusted groups.

Grouped estimation requires sufficient support within each group. Failures include
group context rather than silently omitting invalid groups. The same descriptive
policy applies to every estimate. Use `.plot()` for facets, or individual results
with caller axes as shown in [plot composition](plotting.md).
