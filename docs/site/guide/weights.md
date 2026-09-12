# Weights, clusters and missingness

All inputs align by row position. Pandas indexes do not trigger joins or reindexing,
including named control Series in mappings. Join explicitly before estimation if
index alignment is intended. x/y/weights must be one-dimensional and equally long;
controls must have the same row count. Collect LazyFrames explicitly.

## Complete cases and zero weights

`dropna=True` jointly excludes missing/nonfinite estimation inputs; `False` raises.
Negative weights raise. With `zero_weight='retain'` (default), zero rows can affect
partitions and raw counts, but not point estimates, df or diagnostic support.
Use `'drop'` to omit them before partitioning. Every occupied bin needs positive
weight. The separate binsreg adapter always drops zero-weight rows.

```python
import numpy as np
import polars as pl
import binspect

rng = np.random.default_rng(53)
n = 1200
x = rng.normal(size=n)
y = x + rng.normal(size=n)
y[0] = np.nan
w = np.ones(n)
w[1] = 0
frame = pl.DataFrame({"x": x, "y": y, "w": w, "firm": np.arange(n) // 20})
weighted = binspect.binscatter(
    frame,
    x="x",
    y="y",
    weights="w",
    zero_weight="drop",
    bins=8,
)
counts = weighted.to_dict()["sample"]
assert counts["n_input"] == n
assert counts["n_missing"] == 1 and counts["n_zero_weight_dropped"] == 1
assert counts["n_obs"] == n - 2
assert counts["n_input"] == counts["n_obs"] + counts["n_dropped"]
```

Exclusions are mutually exclusive: missing groups first (for `compare`), then
missing/nonfinite estimation inputs, then dropped zero weights. Missing group
labels are excluded even with `dropna=False`. `n_obs`/bin `n` count retained rows;
`n_positive` counts positive-weight rows, and `n_effective` is Kish effective size.

## Different variance conventions

Independent weighted bin SEs use reliability variance and effective sample size.
Classical weighted slope SEs instead use the inverse-variance WLS model. These
are distinct assumptions despite sharing point-estimation weights. Frequency,
survey-design and inverse-probability variance interpretations are not supplied.
`binscatter`/`compare` have no HC1 or `vce` argument.

```python
clustered = binspect.binscatter(
    frame,
    x="x",
    y="y",
    weights="w",
    zero_weight="drop",
    cluster="firm",
    bins=8,
)
assert clustered.fit.se_type == "cluster"
assert clustered.estimates.se_type == "cluster"
assert clustered.fit.inference_df == clustered.fit.n_clusters - 1
assert clustered.verdict == "not assessed"
```

CR1 bin covariance uses positive-weight clusters represented **in each bin** and
a t reference with local cluster count minus one. A bin with fewer than two such
clusters has undefined intervals. Slope covariance uses the full design and
global cluster count. Controls still withhold bin uncertainty even with clusters.

Few or highly uneven clusters can under-cover severely: the prespecified case
with cluster sizes 480/60/60 gave 78.2% bin coverage at nominal 95%. Arithmetic
agreement does not establish a safe cluster threshold. Unadjusted intervals remain
approximate, pointwise and conditional on the partition; selection uncertainty
and simultaneous coverage are omitted. Read the
[statistical contract](https://github.com/joshuamyers22/binspect/blob/main/docs/STATISTICAL_ANALYSIS_PLAN.md)
and [coverage evidence](https://github.com/joshuamyers22/binspect/blob/main/docs/expanded-coverage-review.md).
