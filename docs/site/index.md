# Binned diagnostics you can inspect

`binspect` compares within-bin means with a linear fit to the observations. Its
tables and figures help describe departures from linearity; they do not establish
causality or certify a model. Polars is the native table engine, pandas inputs
remain supported, and pandas output requires an explicit conversion.

!!! note "Development documentation"
    This guide describes the unreleased checkout. The package still reports
    **0.1.1**, while Polars tables, versioned exports and the function adapter are
    proposed for **0.2.0**. A published 0.1.1 installation does not provide this
    whole interface. Review and release qualification remain open.

## Install this checkout

From the repository root, install the base package for native Polars workflows:

```sh
python -m pip install -e .
```

Use `python -m pip install -e ".[pandas]"` for explicit pandas conversion, or
`python -m pip install -e ".[dpi]"` for optional binsreg selection/function inference.
The DPI extra brings upstream pandas. NumPy/SciPy perform the numerical work;
native estimation, exports and plots do not need pandas. Python ≥3.10 is required;
dependency lower-bound qualification is still open. For the exact development
environment and all examples below, use `uv sync --frozen --all-extras`.

The published distribution is installed with `python -m pip install binspect-regression`;
the import name is always `binspect`. See [development and releases](development.md)
for the distinction between a checkout, a built site and a published release.

## Estimate, inspect and plot

This complete example uses synthetic data. Every Python block in the user guide
is executed by `make docs`; blocks on a page share variables, while each page runs
in a fresh process. Figure output goes to temporary storage during that check.

```python
import json
import numpy as np
import polars as pl
import matplotlib.pyplot as plt
import binspect

rng = np.random.default_rng(11)
x = rng.gamma(shape=2, scale=2, size=2000)
frame = pl.DataFrame({"x": x, "y": 8 * np.log1p(x) + rng.normal(0, 3, x.size)})
result = binspect.binscatter(frame, x="x", y="y", bins=12)
table = result.table.select("bin", "n", "x_mean", "y_mean", "se")
assert isinstance(table, pl.DataFrame) and table.height == result.n_bins
assert result.n_obs == frame.height
assert json.loads(result.to_json())["schema_version"] == 1

fig, ax = plt.subplots()
assert result.plot(ax=ax, theme="paper") is ax
fig.savefig("quickstart.png", dpi=120)
plt.close(fig)
```

`result.table` contains occupied-bin summaries. `result.fit` describes the linear
model fitted to observations; it is not a regression on bin means.
`result.summary_frame()` is a Polars model/diagnostic summary, and
`result.to_pandas()` explicitly returns pandas when its extra is installed.

Unadjusted intervals are approximate, pointwise and conditional on the observed
partition. They omit bin-selection uncertainty. With controls, bin uncertainty is
withheld. Start with [interpreting diagnostics](guide/interpretation.md), then
[controls](guide/adjustment.md) or [weights and clusters](guide/weights.md).

## Find the right operation

| Need | Guide / API |
|---|---|
| Understand gap, R-squared and verdicts | [Interpretation](guide/interpretation.md) |
| Adjust x and y for covariates | [Controls and distinct estimands](guide/adjustment.md) |
| Handle weights, missing rows or dependent observations | [Weights and clusters](guide/weights.md) |
| Select a partition or inspect gaps in IDs | [Binning](guide/binning.md) |
| Compare groups with overlapping or disjoint support | [Groups](guide/groups.md) |
| Reuse axes, layers or an audit figure | [Plot composition](guide/plotting.md) |
| Convert tables or export deterministic evidence | [Tables and evidence](guide/exports.md) |
| Check parameters, attributes and defaults | [Estimation](reference/estimation.md), [results](reference/results.md), [plotting](reference/plotting.md) |
