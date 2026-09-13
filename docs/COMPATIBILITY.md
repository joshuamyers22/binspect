# Compatibility and migration policy

This proposed A3 policy describes the unreleased checkout based on A2 `9a6db9f`.
Maintainer acceptance and release qualification are pending. The package still
reports **0.1.1**; the changes below are allocated to **0.2.0**, not a 0.1.2 patch.
Use this guide with the [actual API inventory](API_INVENTORY.md),
[input/table/export contract](INPUT_OUTPUT_CONTRACT.md) and
[changelog](../CHANGELOG.md). Verification is recorded in [the A3 review](compatibility-policy-review.md).

## What compatibility covers

The supported application surface is the top-level `binspect` exports, result
attributes/methods listed in the inventory, `binspect.types` value containers and
aliases, and the composable `binspect.viz` exports. Re-exported names remain usable
at their documented paths. Result constructors are inventoried, but estimators
are the recommended construction path: direct construction cannot reconstruct
sample/design history and may export null metadata. Underscore-prefixed storage
and unlisted implementation helpers are internal.

`binspect.core` describes itself as estimation internals. Its existing exported
primitives are inventoried separately for auditability; they do not perform the
full public preparation/inference checks and are not an alternative supported
estimator. In particular, a low-level adjusted-bin variance formula is retained
for development evidence despite failed coverage. Its availability does not
override the public withdrawal of adjusted-bin uncertainty.

Compatibility includes accepted documented inputs, positional alignment, parameter
names/defaults, return types, table column meanings, result ownership, exception
and warning classes, and plotting composition. It does not promise exact summary
prose, exception wording, artist counts/pixels, internal layout, cross-version
pickle loading, or bit-identical floating-point estimates across dependencies and
platforms. Use structured tables/JSON and warning classes instead of parsing text.
No implicit pandas output switch is made for pandas inputs.

## Release and deprecation rules

During 0.x development, an intentional incompatible change goes in a minor release
and includes a changelog entry, before/after example, affected surface and release
allocation. A patch may correct implementation to the documented mathematical or
input contract, fix packaging, or clarify documentation while preserving the
supported interface. A numeric bug fix can change estimates: document the affected
method and evidence even when the signature stays the same. Additive capabilities
go in a minor release. After 1.0, intentional incompatibilities require a major
release; additive capabilities remain minor and compatible fixes remain patch.

For future planned removals or renames, prefer a working transition plus a
`DeprecationWarning` during at least one released minor version, naming the
replacement and earliest removal version. There is no deprecation warning/shim
for the current Polars table migration; 0.2.0's explicit pandas projection is its
migration path. Invalid statistics need not remain available through a warning
period: a correctness fix may withhold inference or reject an unsupported
combination immediately, with the reason, evidence and alternative documented.
An urgent patch withdrawal needs explicit maintainer review and release notes;
that exception does not permit unrelated default/type changes in a patch.

| Pending change since 0.1.1 | Compatibility impact | Release allocation |
|---|---|---|
| Polars required/default tables; pandas optional with explicit conversion | Return types and installation requirements change | 0.2.0 minor |
| Owned read-only arrays and immutable group mapping | Callers mutating stored arrays must copy/re-estimate | 0.2.0 minor |
| Positional named mapping controls, explicit category order and label/name validation | Fixes inconsistent alignment; previously ambiguous inputs may fail or change design | 0.2.0 minor, with migration examples |
| `limited support`/`not assessed` verdicts and configurable policy | Categorical outputs/default assessment change | 0.2.0 minor |
| Adjusted-bin uncertainty withheld; shared adjusted bins and unsupported DPI combinations rejected | Previously accepted calls/finite outputs can warn, fail or become unavailable | 0.2.0 minor; correctness withdrawal is explained explicitly |
| Actual DPI selection, stable grouped interval identity, normalized control-rank checks | Corrected counts/IDs/numerics; unidentified slopes now fail | 0.2.0 minor alongside affected migrations; not an invisible patch |
| Versioned JSON/evidence, sample/design metadata, separate binsreg function adapter | Additive API, schema and method capabilities | 0.2.0 minor |
| Deferred Matplotlib initialization, corrected installation hint and documentation | Compatible fixes eligible for a patch independently | Included in 0.2.0; no separate patch proposed |

The allocation is a release proposal, not a version bump or approval to publish.
Follow [release readiness](../checklists/RELEASE_READINESS.md) and
[maintainer release instructions](../RELEASING.md). C3 statistical acceptance,
dependency qualification and other release gates remain open.

JSON schema versions are independent of package versions. V1 permits new optional
fields; consumers should ignore unknown fields. Removal, renaming, type/meaning
changes or altered null/label encoding require a new schema and migration notes.
Unversioned legacy exports are not v1. There is no automatic legacy importer.
Undefined numbers become null, not zero; raw observations are omitted. See the
[full export contract](INPUT_OUTPUT_CONTRACT.md) for provenance and ordering.

## Supported estimation combinations

“Supported” below means implemented with the documented checks and limitations;
it is not a coverage guarantee. Every path requires sufficient sample support,
valid weights and an identified design. All three estimators accept eager Polars,
pandas, mapping and array inputs under the same positional contract. Collect
LazyFrames explicitly. Native `binscatter`/`compare` need no pandas installation.

| Option | `binscatter` | `compare` | `binsreg` (optional `[dpi]`) |
|---|---|---|---|
| Count/edges | Integer ≥2, `auto` (default), `sturges`, `iqr`, `dpi`, or custom edges | Same; pooled selection by default | `dpi` (default) or integer ≥2, no custom edges/other rules |
| Placement | `quantile` (default), `equal_width`; explicit edges give `custom` | Same | `quantile` (default), `equal_width` |
| Controls | Numeric/categorical FWL adjustment of x/y, restored sample weighted means | Requires `common_bins=False`; group and pooled adjustments are independent | Joint original-coordinate function fit; full-rank encoded design required |
| Weights | Nonnegative reliability weights; `zero_weight='retain'` default, `'drop'` optional | Same within each estimate | Nonnegative weights; zero rows always dropped, no `zero_weight` argument |
| Clusters | CR1 bin/slope covariance; local bin/global slope cluster counts | Same within each estimate | Upstream cluster covariance; normal reference, explicit fallback/status |
| DPI with controls/weights/clusters | Rejected if any supplied | Rejected if any supplied | Supported by adapter; inspect upstream issues/actual method |
| `ci` | 0.95 default; `None` disables limits | Same | 0.95 default; finite level strictly between 0 and 1 required, no `None` |
| Adjusted-bin uncertainty | SE/CI/df unavailable; `ci=None` avoids warning | Same | Different function estimand; intervals include coefficient/control covariance, not uncertainty in chosen `at` values |
| Covariance selection | Independent reliability bin SEs and classical slope SEs, or CR1 when `cluster` supplied; no `vce`/HC1 switch | Same | HC1 without clusters; cluster covariance with clusters; no public `vce` argument |
| Missing values | `dropna=True` joint filtering; `False` raises | Same, but missing group labels always excluded first | Joint filtering; `False` raises |
| Group partitions | One sample | `common_bins=True` default; `False` selects separately | No grouped adapter API |
| Diagnostic policy | `DiagnosticPolicy(0.02, 30.0, None)` default; `None` disables verdict | Same policy for pooled and groups | No slope/gap/verdict policy |
| Control evaluation `at` | Not applicable | Not applicable | `'mean'` default, `'zero'`, or finite vector in encoded-control order |

Custom edges must be one-dimensional, strictly increasing and cover observed x;
use `bins=edges` rather than requesting automatic `binning='custom'`. Ties at an
interior edge belong to the lower interval. `auto` targets about 100 rows per bin;
`auto`/`sturges`/`iqr` clip suggested counts to the current 5–40 range with a
sample-size ceiling. Ties/empty intervals can further reduce realized counts.
Inspect `bin_rule`, `requested_bins`, `n_bins` and partition metadata.

Unadjusted bin intervals are approximate pointwise intervals conditional on the
observed partition, with selection uncertainty omitted. No path promises uniform
bands or reliable few/uneven-cluster coverage. The adapter has a different target
from residualized diagnostic bins. Its fallback may change count, degree and
placement; unknown warnings/backend versions are unverified. See the
[analysis plan](STATISTICAL_ANALYSIS_PLAN.md) and [adapter evidence](binsreg-adapter-review.md).

## Plotting compatibility

`result.plot(ax=ax)` and `binspect.viz.plot(result, ax=ax)` return that exact Axes;
omitting `ax` creates one. Each standalone layer also returns the supplied Axes.
`BinsregResult.plot(ax=ax)` preserves identity but has no `theme`, `show` or
annotation arguments. `result.audit()` and collection `.plot()` create Figures
and have no caller-axes parameter. Collection layout supports only `'facets'`;
`ncols=None` uses up to three columns, with shared x/y axes by default.

Single-result plots use `theme='notebook'`, `annotate='minimal'`, no legend and
layers `deviation`, `rug`, `fit`, `ci`, `bins`. Audit uses `annotate='audit'`, both
companion panels and 30 histogram bins. `show=None` selects default layers;
`show=()` selects none. `annotate=None` omits captions. Layer draw order is fixed
regardless of `show` order; CI draws nothing if intervals are unavailable.
See [layer signatures and destinations for styling options](API_INVENTORY.md).

Themes `notebook`, `paper`, `deck` apply through scoped Matplotlib contexts.
`binspect.theme(name, **rc_overrides)` restores rcParams on normal exit and
exceptions. Rendering does not leak theme settings; created artists keep their
styles. A plot's explicit/default theme still applies inside an outer context;
use the desired `theme=` on the plot or an explicit custom `Theme` through
`binspect.viz.plot`. Standalone layers use theme style values but do not themselves
open an rcParams context. Facet figure creation uses the caller's current rcParams;
each panel applies its requested theme. The adapter uses caller rcParams.
Style dictionaries in `Theme.rc` and the theme/palette registries are mutable;
direct global mutation is not the scoped-context contract. No concurrent rendering
or pixel/accessibility qualification is implied by these compatibility guarantees.

## Warnings and exceptions

All names in the first five rows are importable from `binspect` and
`binspect.exceptions`. Warnings derive from `UserWarning`, not `BinspectError`.
Catch classes instead of depending on message wording. Standard validation errors
are not wrapped in `BinspectError`; catching it alone does not catch every bad input.

| Class | Trigger / caller action |
|---|---|
| `BinspectError` | Base of `InvalidBinningError`, `InsufficientDataError`, `BinsregError` |
| `InvalidBinningError` | Invalid rule/partition, unavailable or failed DPI selection, unsupported DPI options or shared adjusted bins; choose a documented combination |
| `InsufficientDataError` | Insufficient retained support, degenerate x, unidentified adjusted slope, or no nonmissing groups; check sample/design |
| `BinsregError` | Missing optional backend, failed upstream fit or unusable returned schema; inspect sample/design and install `[dpi]` when missing |
| `BinCountWarning`, `AdjustedInferenceWarning`, `BinsregWarning` | Reduced/sparse bins (current sparse threshold <10 retained rows); requested unavailable adjusted intervals; adapter limitations/fallback/unverified method respectively |
| `ValueError` | Shapes, missingness with `dropna=False`, weights, levels, ambiguous controls, policy/provenance, table selector or plotting options |
| `TypeError` | Unsupported input/label types (including LazyFrame), unexpected arguments or incompatible Matplotlib styling options |
| `KeyError` | Missing selected column or unknown named theme/palette |
| `ImportError` | Explicit pandas conversion without pandas installed; install `[pandas]` |

The list describes controlled public failure paths, not an exhaustive translation
of third-party failures. Group estimation adds group context while preserving
supported error types and causes. Bin-count warnings use raw counts and are
separate from the effective-row/cluster diagnostic policy. No new deprecation
warning class or runtime compatibility check is introduced by this policy.

## Migration examples from 0.1.1

Run these sequentially in the unreleased checkout with the `[pandas]` extra.
Synthetic inputs avoid retaining caller data. The optional function example also
needs `[dpi]`. These are application examples, not statistical assessment seeds.

### Keep pandas inputs; choose native or explicit pandas outputs

```python
import json
import numpy as np
import pandas as pd
import polars as pl
import binspect

rng = np.random.default_rng(321)
n = 600
x = rng.normal(size=n)
z = rng.normal(size=n)
frame = pd.DataFrame(
    {
        "x": x,
        "y": 0.7 * x + z + rng.normal(size=n),
        "z": z,
        "group": np.where(np.arange(n) % 2, "A", "B"),
    }
)
result = binspect.binscatter(frame, x="x", y="y", bins=6)
# Before: result.table.loc[result.table["n"] > 30, "y_mean"]
native = result.table.filter(pl.col("n") > 30).select("y_mean")
legacy = result.to_pandas().loc[lambda table: table["n"] > 30, "y_mean"]
np.testing.assert_allclose(native["y_mean"].to_numpy(), legacy.to_numpy())
assert isinstance(result.table, pl.DataFrame)
assert isinstance(result.to_pandas("summary"), pd.DataFrame)
assert isinstance(result.to_pandas("decomposition"), pd.DataFrame)

# Before: mutating result.x (or its input buffer) could alter stored data.
editable_x = result.x.copy()
editable_x[0] = 99
assert result.x[0] != 99  # re-estimate explicitly to change the fitted result
```

### Make alignment and inference choices explicit

```python
# Before: named control Series in mappings could align by pandas index while
# x/y remained positional. If index alignment is intended, do it before the call.
indexed_x = pd.Series(x, index=np.arange(n))
indexed_z = pd.Series(z, index=np.arange(n)[::-1])
aligned = pd.DataFrame({"x": indexed_x, "z": indexed_z}).reindex(indexed_x.index)
aligned["y"] = frame["y"]
adjusted = binspect.binscatter(
    aligned,
    x="x",
    y="y",
    controls="z",
    bins=6,
    ci=None,
)
assert adjusted.adjusted and adjusted.estimates.ci_level is None
assert np.isnan(adjusted.estimates.se).all()
# ci=None requests descriptive adjusted bins; it does not restore their intervals.
# Replace bins='dpi' with a supported fixed/auto rule when these diagnostics
# include controls, weights or clusters. Slope uncertainty remains available.

groups = binspect.compare(
    frame,
    x="x",
    y="y",
    group="group",
    controls="z",
    bins=6,
    common_bins=False,
    ci=None,
)
assert isinstance(groups.to_pandas("summary", include_pooled=True), pd.DataFrame)
# Independent group bin IDs are local. For shared original-coordinate bins:
shared = binspect.compare(frame, x="x", y="y", group="group", bins=6)
intervals = shared.table.select("group", "bin", "x_lo", "x_hi")
assert intervals.height == shared.table.height
# Join by bin only when common_bins=True; IDs may have gaps. Compact array index
# j maps to binning.interval_ids[j], not necessarily table bin j.

# Before: code might branch on 'underpowered bins' or parse summary text.
assert result.verdict in {"linear", "curvature", "limited support", "not assessed"}
assert "verdict_reason" in result.decomposition.as_dict()
payload = json.loads(adjusted.to_json())
assert payload["schema_version"] == 1 and payload["result_type"] == "binscatter"
assert payload["bins"][0]["se"] is None
# Legacy payloads without schema_version need an explicit legacy reader.
```

### Retain caller axes and scoped styling

```python
import copy
import matplotlib as mpl
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
before = copy.deepcopy(dict(mpl.rcParams))
assert result.plot(ax=ax, theme="paper", show=("bins", "fit")) is ax
assert dict(mpl.rcParams) == before
try:
    with binspect.theme("deck", **{"font.size": 42}):
        assert mpl.rcParams["font.size"] == 42
        raise RuntimeError("example failure")
except RuntimeError:
    pass
assert dict(mpl.rcParams) == before
plt.close(fig)
```

### Choose the separate function target when needed

```python
# This is a different target from adjusted FWL diagnostic bins above.
function = binspect.binsreg(frame, x="x", y="y", controls="z", bins="dpi")
assert isinstance(function.dots, pl.DataFrame)
assert isinstance(function.to_pandas("intervals"), pd.DataFrame)
assert function.metadata["estimand"] == "function_in_original_x_at_fixed_controls"
status = function.metadata["inference_status"]
issues = function.metadata["issues"]  # inspect actual method and support warnings
```

## Dependency and platform scope

The current manifest requires Python ≥3.10, NumPy ≥1.24, Polars ≥1.0, SciPy ≥1.10
and Matplotlib ≥3.7. Pandas ≥2.0 is optional via `[pandas]`; `[dpi]` installs binsreg
≥1.0 with its upstream pandas dependency. Those lower bounds are installation
constraints, not evidence that every admitted combination is qualified. CI is
configured for Python 3.10–3.13 on Linux/macOS; a configured matrix is not a claim
that this branch passed on each platform. P2 lower-bound/current dependency
qualification remains open. This policy adds no maximum-input-size or speed claim.

The [A2 evidence](export-input-contract-review.md) records the tested lock and
minimal installation without pandas. The adapter's reference backend is binsreg
3.2.1; other versions receive `unverified_method` status. Use the committed lock
for reproducing development evidence and qualify new dependency combinations
before expanding support claims.
