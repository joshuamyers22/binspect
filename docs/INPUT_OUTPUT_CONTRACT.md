# Input, table and evidence-export contracts

This is the 0.2.0 dataframe/input/export contract. The user-directed dataframe decision is in
[ADR-0002](decisions/0002-polars-native-dataframes.md); implementation evidence is
in [the A2 review](export-input-contract-review.md). Numerical conventions remain
those in the [statistical analysis plan](STATISTICAL_ANALYSIS_PLAN.md).
The [compatibility policy](COMPATIBILITY.md) records the 0.2.0 allocation,
supported option combinations and migration examples; the
[API inventory](API_INVENTORY.md) lists current signatures and attributes.

## Dataframe and input contract

Polars is the primary tabular engine and a required dependency. NumPy/SciPy perform
numerical calculations. Pandas is optional: install `binspect-regression[pandas]`
for compatibility tables. Existing pandas callers already have that dependency.
The `[dpi]` extra also installs pandas through upstream binsreg. Native import,
estimation, grouped controls, export and plotting run without pandas installed.

| Input | Supported contract |
|---|---|
| `data` | Eager Polars or pandas DataFrame, or a mapping of string column names to vectors. A string x/y/weight/group/cluster/control argument selects a column. LazyFrames must be explicitly `.collect()`ed. No implicit scans, collection or network I/O. |
| `x`, `y`, `weights` | One-dimensional, real numeric array-like or Polars/pandas Series, all with equal length. Lists, NumPy arrays and numeric strings convertible to float64 are accepted. No broadcasting, scalar, complex or two-dimensional columns. Selected duplicate dataframe columns fail dimensional validation. |
| Controls | One vector, a two-dimensional array, eager dataframe, or named column(s). Numeric and boolean controls stay numerical; string/categorical controls are reference-coded. Names must be unique, including after string conversion and dummy expansion. Unsupported nested/struct/object columns fail instead of being silently coerced. |
| Alignment | Strictly positional for every input, including mappings of Series and named controls. Pandas indexes are ignored. Every control has the same original row count as x/y; the library never joins indexes. |
| Missingness | Null/NA/NaN and infinite numeric estimation values are excluded jointly with `dropna=True`; `False` raises. Missing group labels are excluded first regardless of `dropna`, as before. Negative weights raise; at least one positive weight and positive weight in each occupied bin are required. |
| Zero weights | `retain` keeps rows in partition selection and descriptive counts; `drop` removes complete-case zero-weight rows before estimation. The binsreg adapter always drops zero-weight rows. Exclusion reasons are mutually exclusive in the order missing group → missing/nonfinite estimation inputs → dropped zero weights. |
| Group/cluster labels | Strings, booleans, finite numeric scalars, dates, datetimes and NumPy datetime64 scalars. Missing labels are handled by the policies above. Arbitrary custom objects and nonfinite nonmissing labels are rejected. Group order is first appearance. Python equality defines identity, so equal labels such as `1`, `1.0` and `True` identify one group. |

The native control matrix preserves the established numerical-first order: all
numeric/boolean controls in input order, then categorical dummy columns in input
column order. Ordinary strings and Polars Categorical use sorted **observed** levels
after filtering; the first is omitted. Declared pandas Categorical and Polars Enum
orders retain their reference and unused levels after filtering. These declared
levels can create redundant columns: binscatter permits redundancy when x remains
identified, while binsreg requires a full-rank design. Explicit `at=` vectors for
binsreg follow the exported encoded-control order.

The named-control mapping path previously let pandas align Series by index while
x/y remained positional. A2 corrects this inconsistency. Callers who intend index
alignment must perform their join/reindex explicitly before estimation.

## Tables and pandas migration

`BinscatterResult.table`, `.decomposition_table`, `.summary_frame()`, grouped
`.table`/`.summary_frame()`, and `BinsregResult.dots`/`.intervals` are Polars
DataFrames, regardless of the input backend. No inference or schema is selected
based on which input dataframe library the caller uses.

```python
import numpy as np
import polars as pl
import binspect

rng = np.random.default_rng(421)
frame = pl.DataFrame({"x": rng.normal(size=200), "y": rng.normal(size=200)})
result = binspect.binscatter(frame, x="x", y="y", bins=4)
native = result.table.filter(pl.col("n") > 10)
pandas_bins = result.to_pandas()
pandas_summary = result.to_pandas("summary")
pandas_decomposition = result.to_pandas("decomposition")
```

For collections use `collection.to_pandas()` or
`collection.to_pandas("summary", include_pooled=True)`. For the function adapter
use `function.to_pandas()` for dots and `function.to_pandas("intervals")`.
These explicit conversions need pandas but not PyArrow. Direct
[Polars `to_pandas`](https://docs.pola.rs/api/python/stable/reference/dataframe/api/polars.DataFrame.to_pandas.html)
has its own dependency/options contract; it is not needed for binspect's conversion.

Migrate pandas-specific operations by using the explicit conversion, or native
Polars operations (`table[0, "y_mean"]`, `series.to_list()`, `frame.filter(...)`).
Old result column names are retained. Numeric undefined estimates remain NaN in
tables and become null in JSON. Grouped summaries mark pooled rows using
`is_pooled=True`, with a null group value. Homogeneous labels use an inferred Polars
dtype; heterogeneous labels use Object to avoid coerced/colliding identities.
Use the tagged JSON encoding below for portable heterogeneous labels.

All returned tables and pandas conversions are independent editable projections.
Changing them does not update the estimate. Numeric observation/partition/estimate
arrays remain read-only under A1. Raw arrays are not part of JSON exports.

## Versioned result payloads

`to_dict()` produces a strict-JSON-compatible object; `to_json()` produces a
deterministic encoding using sorted object keys, compact separators, ASCII escapes
and `allow_nan=False`. Arrays and grouped records preserve their documented order.
Determinism means the same result and caller metadata yield the same text; it does
not promise identical numerical results across machines, library versions or row
permutations. Python integers are retained; consumers with limited integer precision
must account for that limitation.

All payloads carry integer `schema_version=1` and `result_type` equal to
`binscatter`, `collection` or `binsreg`. Previously unversioned payloads are legacy
and must not be interpreted as v1 merely because some keys match. Within v1, new
optional fields may be added; readers should ignore unknown fields. Removing or
renaming fields, changing their meaning/type, or changing null/label encoding needs
a new schema version and migration notes. Package and schema versions are separate.
No deserialization or cross-version pickle compatibility is promised.

| Payload component | v1 meaning |
|---|---|
| `sample` | Original `n_input`, retained `n_obs`, total `n_dropped`, `n_missing_group`, `n_missing`, `n_zero_weight_dropped`, `dropna`, and `alignment="positional"`. Original = retained + all three exclusion counts. Single results have zero missing-group exclusions. Group counts use each group's original pre-filter rows; collection/pooled counts use all original rows. Unknown accounting from direct result construction is null. Adapter accounting is in `metadata.sample`. |
| `design` | Binscatter intercept, ordered role/name descriptors for the full slope design, encoded control columns and per-variable coding/reference levels; `original` or `fwl_residuals_with_sample_weighted_means` coordinates, and unit/reliability weights. Encoded identity is not a hash of caller observations. Unknown direct-construction design is null. Grouped adjusted results retain independent group/pooled design identities. |
| `inference` and `fit` | Actual bin and slope covariance types, interval confidence level, per-bin df in compact occupied-bin order, slope residual/reference df and unchanged inference limitations. Adjusted bin uncertainty is unavailable. Disabled confidence intervals have null `ci_level`; applicable standard errors and df may still exist. Undefined numerics encode as null. |
| `binning` and `bins` | Method, count rule/source/fallback, requested/actual count, legacy edges, full partition and original occupied interval IDs. Bin rows preserve table column names and order. Raw assignments and observations are omitted. |
| `decomposition` | Existing sums, descriptive gap/verdict, raw/positive/effective support, optional cluster support, enabled status, policy thresholds and verdict reason. No new statistical acceptance is implied. |
| Collection `groups` | Ordered list of `{value, label, result}`. `value` retains the legacy scalar/ISO representation. `label` is a tagged `{type, value}` descriptor (boolean, integer, number, string, date, datetime; datetime64 also carries `unit`). Use `label`, not the legacy scalar alone, for portable identity. |
| Function adapter `metadata` | Original-coordinate function target; actual dot/interval degrees, selection method/fallback/status, control design/evaluation and weight interpretation. `bin_covariance` describes function covariance; `slope_covariance=null` because this result has no slope. The reference is normal with `reference_df=null`. Upstream warning/coverage limitations remain explicit. |

JSON null means unavailable/undefined, never zero. Metadata objects/arrays are
recursively normalized, and unsupported objects or non-string object keys raise
TypeError instead of being silently stringified. Tables and exports include caller
labels and aggregate estimates and are not anonymous; export and sharing remain
caller-controlled.

## Caller-controlled evidence

```python
evidence = result.to_evidence(
    provenance={
        "analysis_plan": {"uri": "analysis-plan.md"},
        "inputs": {"uri": "private://my-retained-input"},
        "software_lock": {"sha256": "a" * 64},
        "code": {"revision": "reviewed-source-revision"},
    },
    exported_at="2026-09-12T12:00:00Z",
)
```

The envelope has `schema_version=1`, `result_type="evidence"`, a deterministic
`payload={result, provenance}`, and optional `exported_at` outside the payload.
The timestamp is supplied by the caller and must include a timezone; no current
time is collected automatically. No timestamp enters `to_json()` result payloads.

Provenance admits only `analysis_plan`, `inputs`, `software_lock` and `code`.
Each supplied reference must contain a nonempty `uri`, a 64-hex-character `sha256`,
or a `revision` for code; SHA-256 text is normalized to lowercase. Omitted
references are null, not inferred from the machine. Unknown fields and malformed
references fail. URIs may be caller-owned local or private references; the library
does not read them, verify hashes, inspect Git, fetch links or fingerprint data.
There is no network/storage side effect and no implicit export of raw rows.

For consequential use, the caller must supply and retain the matching plan, input,
lock and code references and review the statistical limitations. The envelope
records their assertions; it neither authenticates them nor certifies reproducibility,
privacy or statistical validity. Data-derived fingerprints and retention remain
under caller control.
