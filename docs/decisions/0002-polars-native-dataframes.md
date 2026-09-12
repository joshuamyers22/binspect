# ADR-0002: Polars-native dataframes with pandas compatibility

- Date: 2026-09-12. Owner: Josh Myers.
- Decision authority: explicit user direction during A2: “i want this to be polars
  native but still functional with pandas”, followed by “Polars tables by default,
  explicit pandas conversion”. This authorizes the tabular direction; implementation
  review/integration and statistical/release acceptance remain separate.
- Supersedes: only the pandas-first dataframe portion of proposed
  [ADR-0001](0001-existing-library-baseline.md). Other baseline decisions remain
  proposed for their existing review gates.

## Decision

Polars is the required dataframe dependency. Named columns and controls normalize
positionally; control filtering and categorical encoding use Polars. Result tables,
grouped summaries and binsreg dot/interval projections return Polars dataframes.
NumPy/SciPy remain responsible for numerical estimation, with owned arrays under A1.

Pandas dataframes/Series remain accepted at the input boundary. Their indexes never
align rows. Explicit `result.to_pandas()` conversions provide independent pandas
tables without requiring PyArrow; pandas becomes an optional `[pandas]` extra.
Pandas categorical order is carried into the native preparation contract, matching
declared Polars Enum order. Plain string controls use sorted observed categories.

The optional upstream binsreg library still uses pandas internally. Its returned
tables convert once at the adapter boundary; this does not make binsreg itself
Polars-native. Core factorization and native estimation/import/plot journeys do not
depend on pandas. LazyFrame inputs must be collected explicitly by the caller.

## Consequences and validation

Changing the default table type requires a compatibility migration and an eventual
minor 0.x release; this change does not publish or bump package 0.1.1. The
[input/export contract](../INPUT_OUTPUT_CONTRACT.md) gives exact types, missingness,
categorical coding, conversions and schema rules.

Native and pandas parity tests, preserved numerical/reference assertions,
ownership tests and a minimal environment without pandas verify the implementation.
CI and `make check` include that native journey. No speedup, zero-copy pipeline or
capacity claim follows from changing dataframe libraries; P1 still owns benchmarks.
See [A2 implementation evidence](../export-input-contract-review.md).
