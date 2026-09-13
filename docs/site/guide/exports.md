# Tables and evidence

All result tables are Polars, regardless of input backend. Single results expose
`.table`, `.decomposition_table` and `.summary_frame()`; collections expose `.table`
and `.summary_frame(include_pooled=...)`. The separate adapter exposes `.dots` and
`.intervals`. Tables and metadata are editable projections, so editing them does
not update the stored estimate.

## Explicit pandas compatibility and owned arrays

```python
import json
import numpy as np
import pandas as pd
import polars as pl
import binspect

rng = np.random.default_rng(97)
frame = pd.DataFrame({"x": rng.normal(size=600), "y": rng.normal(size=600)})
result = binspect.binscatter(frame, x="x", y="y", bins=6)
assert isinstance(result.table, pl.DataFrame)
native = result.table.filter(pl.col("n") > 30)
pandas_bins = result.to_pandas()
assert isinstance(pandas_bins, pd.DataFrame)
np.testing.assert_allclose(
    native["y_mean"].to_numpy(), pandas_bins["y_mean"].to_numpy()
)
assert isinstance(result.to_pandas("summary"), pd.DataFrame)
assert isinstance(result.to_pandas("decomposition"), pd.DataFrame)

editable = result.x.copy()
editable[0] = 99
assert result.x[0] != 99
assert not result.x.flags.writeable
```

`to_pandas()` needs pandas but does not need PyArrow. For collections use the
`'bins'`/`'summary'` selectors; `include_pooled=True` applies only to summaries.
For the adapter use `'dots'`/`'intervals'`. Numeric observations, weights,
partitions and estimates are read-only snapshots. Copy to edit, and re-estimate
explicitly to change results. Inputs can be mutated after fitting safely.

## Deterministic, versioned exports

```python
payload = json.loads(result.to_json())
assert payload["schema_version"] == 1
assert payload["result_type"] == "binscatter"
assert payload["sample"]["alignment"] == "positional"
assert payload["x"] == "x" and payload["y"] == "y"  # names, not raw vectors
assert "assignment" not in payload["binning"]
assert result.to_json() == result.to_json()

evidence = result.to_evidence(
    provenance={"analysis_plan": {"uri": "https://example.org/my-analysis-plan"}},
    exported_at="2026-09-12T12:00:00+00:00",
)
assert evidence["result_type"] == "evidence"
assert evidence["payload"]["result"] == payload
assert evidence["exported_at"] == "2026-09-12T12:00:00+00:00"
```

JSON exports omit raw observations and convert undefined numeric values to null,
never zero. They carry sample exclusions, encoded design identity, coordinates,
both covariance conventions/df, partition provenance and diagnostic settings.
Direct construction with unknown sample/design history can export null metadata.
Typed group labels disambiguate portable representations; mixed Polars label
columns may use Object to retain identity.

Evidence references are supplied by the caller. The library does not fetch URLs,
read or hash files, discover Git state, verify provenance, or add the current time.
The optional caller timestamp sits outside the deterministic payload. Determinism
does not promise identical numerics across dependencies, machines or row order.

V1 allows new optional fields; ignore unknown fields when reading. Removing or
changing fields/meaning/null encoding requires a new schema and migration notes.
Legacy unversioned payloads are not v1, and no cross-version pickle loading or
deserializer is promised. See the complete
[input/export contract](https://github.com/joshuamyers22/binspect/blob/main/docs/INPUT_OUTPUT_CONTRACT.md)
and [0.1.1 migration policy](https://github.com/joshuamyers22/binspect/blob/main/docs/COMPATIBILITY.md).
