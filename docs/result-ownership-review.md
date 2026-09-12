# A1 — result ownership and mutation isolation

- Owner: Josh Myers. Implementer: Codex. Maintainer review pending; no independent
  statistical acceptance is claimed or required for this storage-only change.
- Date / baseline: 2026-09-12 / `25bf68c`.
- Task: A1 in [the production plan](../binspect-plan.md).
- Status: implemented and locally verified on `fix/result-ownership`; maintainer
  review/integration pending. Package version remains 0.1.1; unreleased.

## Contract before iteration

Own numeric result data at construction, including direct construction of nested
`Binning` and `BinEstimates` objects. Caller arrays must remain writable and must
not alias stored values. Expose read-only arrays over immutable bytes with fresh
array headers on access: changing a returned array's shape/dtype must not change
the stored result, and `setflags(write=True)` must fail. Explicit `.copy()` gives
the caller an editable array. Nested scalar dataclasses/policies remain frozen.
Group mappings own their entries and share immutable result values; group labels
must be immutable hashable values. Tables, inference metadata and exports are
independent editable projections. The binsreg adapter retains its copied public
table/metadata contract; private-attribute tampering is outside the contract.

Invariants: coefficients, partition semantics, estimates, uncertainty boundaries,
exports and plot coordinates remain numerically unchanged. No new estimator,
export schema, concurrency guarantee, release or governance acceptance. Existing
AR9 reproduction and numerical/plot tests are the safety net. Add mutation tests
for arrays/views, custom edges, nested fields, grouped mapping/pooled results,
tables/exports, and adapter projections. Measure ownership allocation and retained
numeric payload on synthetic single/grouped workloads; P1 capacity claims remain
separate.

Required checks: frozen all-extras sync, focused regressions, `make check`, a
reproducible memory probe, documentation links and final diff review. Any supported
mutation corrupting a result, changed numerical behavior or failed quality gate
blocks readiness (High); missing compatibility/memory documentation is Medium
and must be resolved. Maximum four evidence-changing passes / 90 minutes; no paid
compute. Stop when checks pass; at the ceiling record remaining failures for the
maintainer. Do not relax tolerances or use reserved assessment seeds. Maintainer
review/integration remains separate from implementation verification.

## Evidence ledger

| Pass | Evidence | Result / disposition |
|---|---|---|
| Baseline | Synthetic 100-row array input; mutate x after estimation | Stored x changes while slope stays fixed; nested estimate arrays are writable. AR9 reproduced. |
| 1 | Immutable numeric snapshots, fresh array headers, explicit table copies; [15 mutation regressions](../tests/test_result_ownership.py) | All 15 pass, including input/view/custom-edge mutation, nested fields, direct construction, replacement, copy/deepcopy/pickle, grouped maps/pooled results, tables/metadata, and exact rendered pixels after caller mutation. Strict mypy passes after declaring the dataclass protocol on the shared storage mixin. |
| 2 | [Allocation probe](../validation/result_ownership.py) against baseline source, then full required gate | All eight synthetic exports match baseline exactly. 349 unit tests, 32 binsreg/DPI integrations and 40 Statsmodels references pass; coverage 93.75%. Ruff, formatting, strict mypy and all import contracts pass. All three development coverage gates pass their required criteria; existing uneven-cluster diagnostic failures remain visible. |
| Build retry | `make check` reached build, where sandbox DNS blocked Hatchling resolution | Authorized `uv build` retry outside the sandbox built wheel and sdist successfully. All gate components passed; the initial compound command exited at the network failure. No release or upload. |

## Ownership decision and memory evidence

The small internal [storage mixin](../src/binspect/_ownership.py) snapshots numeric
dataclass fields as bytes plus dtype/shape, and reconstructs array views on access.
Keeping only a read-only owning ndarray would permit callers to re-enable writes;
returning the same array header would still allow shape/dtype changes. Immutable
bytes and fresh headers close both paths without copying values on every read.
Construction preserves caller write permissions. Object-dtype arrays are rejected
by these numeric containers. The immutable scalar result objects can be shared;
`controls` is normalized to a tuple. Copy/deepcopy can share the immutable object;
pickle reconstruction runs through construction to restore the same ownership.
This verifies a same-version round trip, not a versioned persistence schema (A2).

The existing grouped mapping proxy already copies entries. With nested result
arrays protected, sharing its result values is safe. Labels must be immutable
hashable values; this does not add general support for mutable custom label types.
The adapter retains its numeric dataframe and deep-copied metadata projections.
No new mapping or table schema is introduced.

Measurements below use 20 bins, four interleaved groups, seeded synthetic inputs,
one warmup and three measured repetitions per case. Hardware environment:
macOS 15.1 arm64, Python 3.12.14, NumPy 2.5.2, pandas 3.0.5. Lock SHA-256:
`e80f8124b8bcd0051f60b9beef7742434333c78f3e63d8ac7ed1de30deafed90`.
Baseline source was extracted from `25bf68c`; edited source supplied the A1 run.
All eight complete synthetic exports compare exactly, without changed tolerances.

Numbers are median decimal MB from tracemalloc (input creation and warmup excluded),
with baseline → A1. They measure tracked allocations, not whole-process RSS or
all native-library memory. Numeric payload includes x/y/optional weights,
assignments and the small per-bin arrays. The original single result aliases
caller columns, explaining its smaller newly allocated retained memory. Grouped
preparation already copies those arrays, so retained memory changes little.

| Rows | Result | Weights | Retained MB | Peak MB | Elapsed ms |
|---|---|---|---|---|---|
| 10,000 | Single | No | 0.089 → 0.249 | 0.409 → 0.412 | 2.86 → 3.05 |
| 10,000 | Single | Yes | 0.089 → 0.330 | 0.329 → 0.332 | 2.90 → 3.15 |
| 10,000 | Four groups + pooled | No | 0.512 → 0.517 | 0.692 → 0.740 | 8.87 → 9.84 |
| 10,000 | Four groups + pooled | Yes | 0.673 → 0.678 | 0.833 → 0.901 | 9.29 → 10.43 |
| 100,000 | Single | No | 0.809 → 2.409 | 3.310 → 4.012 | 15.49 → 16.21 |
| 100,000 | Single | Yes | 0.809 → 3.210 | 2.510 → 3.212 | 15.66 → 16.30 |
| 100,000 | Four groups + pooled | No | 4.832 → 4.837 | 6.632 → 7.040 | 38.09 → 41.40 |
| 100,000 | Four groups + pooled | Yes | 6.433 → 6.438 | 8.033 → 8.642 | 40.04 → 42.07 |

For 100,000 rows, numeric payload is 2,402,256 bytes unweighted and 3,202,256
weighted for a single result; four groups plus pooled retain 4,811,280 and
6,411,280 bytes respectively. The main single-result copy cost is 16 bytes per
row for x/y, or 24 with weights. Replacing a numeric container copies its buffers
again during construction; table/export allocation and grouped intermediates add
temporary memory. These bounded observations justify the A1 ownership tradeoff;
they do not set P1 workload limits, regression budgets or zero-copy pipeline claims.

Reproduce after `uv sync --frozen --all-extras`:

```bash
mkdir -p .work/ownership-baseline
git archive 25bf68c src | tar -x -C .work/ownership-baseline
PYTHONPATH=.work/ownership-baseline/src uv run python validation/result_ownership.py --label baseline-25bf68c --output .work/ownership-baseline.json
uv run python validation/result_ownership.py --label A1 --output .work/ownership-after.json
```

Reports retain each repetition and the synthetic exports in ignored `.work/`.
No raw caller data is collected. The commands are a local allocation comparison,
not a statistical assessment; reserved assessment seeds remain unrun.

## Review disposition

Implementation self-review found no remaining supported mutation path in the
tested public numeric fields/projections. The High AR9 aliasing finding is fixed;
the compatibility change and measured copy cost are recorded in the
[README](../README.md#result-ownership) and [changelog](../CHANGELOG.md).
Documentation links and `git diff --check` pass. Local checks apply to the edited
tree on the recorded baseline; no clean-commit CI or independent approval is
claimed. Maintainer review/integration remains open, and C3 statistical acceptance,
A2 schema compatibility, P1 capacity and release gates remain separate.
