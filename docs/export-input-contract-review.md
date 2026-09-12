# A2 — export and input contracts

- Owner: Josh Myers; implementer: Codex; maintainer review/integration pending.
- Date / baseline: 2026-09-12 / `1da64c0`, stacked on A1 PR #16.
- Task: A2 in [the production plan](../binspect-plan.md).
- Status: implemented and locally verified on `feat/export-input-contracts`;
  maintainer review/integration pending. No independent statistical acceptance claimed.

## Contract before iteration

User direction during A2 supersedes the proposed pandas baseline: make the library
Polars-native while retaining pandas compatibility. Polars owns tabular preparation
and result tables; pandas inputs convert at an explicit compatibility boundary.
NumPy/SciPy continue numerical estimation, and the optional binsreg backend keeps
its required upstream pandas boundary. Native use must run without importing or
installing pandas. Verify equivalent pandas/Polars inputs, category coding and
missingness, plus native/pandas table projections. This is an explicit user need;
no speedup or zero-copy claim is inferred from the backend change.

Define one positional input contract for arrays, dataframe columns and mappings.
Reject malformed named columns and ambiguous encoded control names. Record
complete-case and zero-weight exclusions, including missing group labels, without
retaining row identities in exports. Preserve numeric methods, uncertainty
withdrawals, partition identities and descriptive policies. Describe the exact
ordered encoded controls and categorical reference levels, adjustment coordinates,
interval level/df and both covariance types. Public results remain owned under A1.

Introduce schema-versioned strict JSON for all three result types, preserving
existing result keys where possible. Add deterministic JSON and a separate evidence
envelope with optional caller-supplied analysis-plan/input/software-lock/code
references. Never implicitly read/hash input files, collect raw rows or fetch
references. Caller-supplied export timestamps live outside deterministic payloads.
Group labels have explicit supported scalar types and a tagged encoding; do not
silently stringify arbitrary objects. Document schema migration and failure paths.

Safety net: existing API/group/inference/adapter/ownership and independent numerical
reference tests. Add behavioral regressions for named shape errors, index mismatch,
filter accounting, category design identity, strict JSON in degenerate/clustered/
grouped cases, typed labels and deterministic/isolated evidence exports.
Required checks: frozen all-extras sync, focused tests, full `make check`, executed
documentation examples, link/format checks and final diff review.

Blocking High findings: silent row misalignment, incorrect counts/design/inference
metadata, mutation regression, implicit private-data collection, or numerical gate
failure. Missing schema/compatibility documentation is Medium and must be resolved.
Maximum four evidence-changing passes / 120 minutes, local compute only. Stop when
checks pass; if the ceiling is reached, document unresolved criteria for the owner.
Do not relax reference tolerances, consume reserved assessment seeds, merge or
publish a release. Maintainer acceptance remains separate from implementation.

## Evidence ledger

| Pass | Evidence | Result / disposition |
|---|---|---|
| Baseline | Two named control Series with reversed indexes | `b=[30,40]` silently becomes `[40,30]`, while x/y conversion remains positional. Named 2-D x bypasses `column` shape validation. |
| 1 | User-directed Polars preparation and result tables, explicit pandas conversions, optional dependency boundary | Preserved numerical assertions through pandas projections. Initial compatibility checks exposed a shared upstream pandas buffer and pandas null conversion differences; explicit copying and object-column conversion corrected them. Core cluster factorization no longer imports pandas. |
| 2 | Native/pandas parity, strict evidence, filter/design and ownership regressions; minimal native installation | 16 estimation parity combinations and native mutation tests pass. Declared category order matches explicit pandas dummy matrices. New datetime-label evidence exposed NumPy scalar broadcasting in group selection; selecting factorized group codes fixes it. Native estimation, grouped controls, JSON and plots pass with no pandas installed. |
| 3 | Final type/identity review, heterogeneous numeric groups, mixed numeric controls, date categories, direct Polars binsreg references | Mixed numeric control lists explicitly promote numerically; heterogeneous group labels use Object instead of coercing identity. Date category reference coding and both backend input paths pass. No statistical formulas or reference tolerances changed. |
| Final gate | `uv sync --frozen --all-extras`, `make check`, executed contract examples and diff/link checks | 402 unit tests; 34 required DPI/binsreg integrations; 40 Statsmodels references; 94.56% coverage. Ruff/format, strict mypy (38 source files), four import contracts, isolated native journey, all three development coverage gates and wheel/sdist builds pass. Both contract code examples execute. |

The first full run passed software gates but sandbox DNS blocked Hatchling at build;
an authorized `uv build` retry succeeded. A subsequent full gate after the final
input/identity corrections completed successfully, including build. Dependency-lock
and editable-install refreshes also required authorized network retries. These were
environment-resolution failures, not numerical failures or waived checks.

## Implementation and compatibility evidence

The [input/output contract](INPUT_OUTPUT_CONTRACT.md) is the public schema and
migration reference. [ADR-0002](decisions/0002-polars-native-dataframes.md) records
the user's explicit choice of Polars-native operation/default tables and pandas
compatibility, superseding only the dataframe portion of the earlier proposed ADR.

Polars is required; pandas is optional through `[pandas]`, the development environment,
or upstream binsreg. `tabular.py` owns lazy pandas conversion, copying upstream
numeric buffers and producing independent pandas projections without PyArrow.
Polars control preparation preserves positional rows, explicit category references,
numeric-first design order and occupied partition identity. NumPy/SciPy continue
numerical estimation. The adapter still uses binsreg's upstream pandas internals;
native binscatter/compare do not install or import pandas.

New evidence is in [Polars/pandas regressions](../tests/test_polars_contract.py),
[strict export regressions](../tests/test_evidence_export.py),
[matched upstream references](../tests/integration/test_binsreg_adapter.py) and
[the native journey](../validation/native_smoke.py). Historical pandas assertions
remain through explicit `.to_pandas()` projections, preserving their original
expectations/tolerances; separate tests assert native table types, operations and
mutation isolation. The binsreg coverage harness changes only table access; its
target, nearest-point tie rule, seeds, failure accounting and tolerances are unchanged.

Verification environment: macOS arm64, Python 3.12.14, Polars 1.44.2, pandas 3.0.5,
NumPy 2.5.2, SciPy 1.18.1, binsreg 3.2.1 and Statsmodels 0.15.0. Lock SHA-256:
`bf45cbccfb726789465f61eb99b1dff5d1cb5b6237c9f30bc167f86952fc2ea3`.
The final local gate log is ignored `.work/a2-final-check.log`; development coverage
reports remain in their existing ignored locations. Reports identify the baseline
revision plus a dirty working tree; no clean-commit CI result is claimed here.

Result schema v1 includes exclusion accounting, encoded design/reference levels,
coordinate identity, actual covariance/df, partition-selection provenance and
existing diagnostic policies. Direct constructors with unknown sample/design
history export null rather than fabricate it. `to_evidence()` only records caller
references; no input/plan/lock/Git inspection, automatic fingerprints or raw-row
export was added. Optional timestamps are outside the deterministic payload.

## Review disposition

Local implementation review has no unresolved High finding in the supported tested
paths. The positional-control defect, ownership regression found during conversion,
datetime group selection and heterogeneous-label coercion are corrected with
behavioral evidence. The table-type change is documented for a future minor 0.x
release; package version remains 0.1.1 and nothing is published.

Maintainer review/integration of this A1-dependent change remains open. Local
verification uses the locked Python 3.12 environment; the configured CI matrix and
P2 lower-bound/upstream dependency qualification remain separate. No measured
speedup, workload ceiling or zero-copy pipeline is claimed. C3 final assessment,
qualified statistical acceptance, governance and release gates remain open;
uneven-cluster diagnostic coverage failures remain explicit. Reserved assessment
seeds were not run. Next implementation task is A3 compatibility policy.
