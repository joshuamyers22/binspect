# binspect project memory

A retrieval index, not a transcript, task history, or source of truth. Verify
each entry before use; update stable keys in place and remove stale claims.
No caller data, private logs, secrets, or hidden reasoning belong here.

## Verified constraints and current state

| Key | Fact / limitation | Evidence | Verified |
|---|---|---|---|
| `package-identity` | Distribution `binspect-regression`, import `binspect`, existing MIT license. | [manifest](pyproject.toml), [license](LICENSE) | 2026-09-12 |
| `library-scope` | In-process descriptive diagnostics; no hosted service or runtime telemetry. Existing stack exceptions remain proposed for review. | [brief](PROJECT_BRIEF.md), [ADR-0001](docs/decisions/0001-existing-library-baseline.md) | 2026-09-12 |
| `quality-gate` | `make check` includes frozen DPI/Statsmodels/adapter references, original coverage, expanded nonflat/DPI/few-cluster simulations and separate binsreg function coverage; default pytest omits integration/external tests. | [Makefile](Makefile), [CI](.github/workflows/ci.yml) | 2026-09-12 |
| `dpi-correction` | C1 is integrated through PR #7: actual DPI count, explicit spacing, no silent fallback; weights/controls/clusters rejected. Not yet released. | [C1 record](docs/dpi-selection-review.md), [PR #7](https://github.com/joshuamyers22/binspect/pull/7) | 2026-09-12 |
| `remote-controls` | Main is unprotected; PyPI environment has a reviewer; security-update automation and private vulnerability reporting are disabled. This is a dated observation, not a protection guarantee. | [API evidence](docs/GOVERNANCE.md) | 2026-09-12 |
| `import-isolation` | Plain import and ordinary estimation defer plotting initialization; requesting theme/plotting exports may initialize Matplotlib caches. Native numerical workers and optional DPI are outside this test's scope. | [Runtime regression](tests/test_runtime_boundaries.py), [public plotting exports](tests/test_plot.py) | 2026-09-12 |

## Verified traps

| Key | Failure / implication | Evidence | Verified |
|---|---|---|---|
| `grouped-adjustment` | Shared bins with controls are explicitly rejected; independent group adjustment remains supported. Tables preserve original interval IDs/bounds while estimation indices stay compact. Do not join independent partitions by ID or enable shared adjusted coordinates by widening edges. | [C2 contract and evidence](docs/grouped-interval-review.md), [regressions](tests/test_grouped_intervals.py) | 2026-09-12 |
| `frozen-arrays` | A1 locally protects observations/weights and nested numeric arrays with immutable bytes and fresh array headers. Use `.copy()` for editable arrays; tables/exports stay editable projections. Group mappings share immutable results; labels must be immutable hashable values. Single-result ownership adds about 16 bytes/row, or 24 with weights, versus caller aliasing. Review/integration pending. | [Ownership contract and measurements](docs/result-ownership-review.md), [mutation regressions](tests/test_result_ownership.py) | 2026-09-12 |
| `inference-evidence` | Adjusted-bin locked-assessment coverage is 87.4% at nominal 95% (89.2% development). Public adjusted-bin SEs/CIs are now unavailable; descriptive bins and slope SEs remain. Use ci=None to omit the warning. Consumed assessment seeds must not be reused for tuning; the failed primitive remains a development diagnostic. | [C3 analysis plan](docs/STATISTICAL_ANALYSIS_PLAN.md), [withdrawal](docs/adjusted-inference-boundary-review.md) | 2026-09-12 |
| `control-identification` | Weighted design columns are normalized for projection and numerical rank. Redundant controls are allowed if x adds rank; x in the numerical control span on positive-weight rows raises InsufficientDataError. This is not a near-singular accuracy guarantee. | [API regressions](tests/test_adjusted_inference_boundary.py), [independent references](tests/integration/test_inference.py) | 2026-09-12 |
| `uneven-cluster-coverage` | Expanded development finds 78.2% bin coverage at nominal 95% with three clusters sized 480/60/60 (80.7% weighted); unweighted slope coverage is 91.7%. Arithmetic agreement and passing balanced cases do not establish a safe cluster threshold. Seeds 81000–81007 remain reserved and unrun. | [Prespecification](docs/EXPANDED_COVERAGE_PLAN.md), [results](docs/expanded-coverage-review.md) | 2026-09-12 |
| `binsreg-reference` | Requested upstream review confirms a different adjusted function target with full control covariance by default, higher-degree DPI function intervals, and warnings/fallbacks for few clusters. It supplies no safe cluster-count guarantee or author endorsement of binspect. | [Source review and locked tests](docs/binsreg-reference-review.md) | 2026-09-12 |
| `binsreg-adapter` | User-requested `binspect.binsreg` adds original-coordinate function inference with full coefficient covariance and copied tables. Backend 3.2.1 references and full gate pass; unknown warnings/versions are unverified. Development coverage is 93.6% iid DPI, 94.3% with 60 clusters, 42.4% with three uneven clusters at nominal 95%. Few-cluster degree-0 fallback remains limited support. Assessment seeds 95000–95002 are reserved and unrun. | [Prespecified contract](docs/BINSREG_ADAPTER_PLAN.md), [clean evidence and review](docs/binsreg-adapter-review.md) | 2026-09-12 |
| `diagnostic-policy` | DiagnosticPolicy uses effective rows, not retained zeros; None opts out. Constant outcomes and clustered estimates without explicit cluster thresholds are not assessed. Limited support replaces the power-implying label. Policies, reasons and distinct counts are exported. | [C4 contract](docs/diagnostic-policy-review.md), [tests](tests/test_diagnostic_policy.py) | 2026-09-12 |

## Open work

The [plan](binspect-plan.md) owns ordering and task status. PRs #6–#14 were
merged into main on 2026-09-12 at `e206e0c`, explicitly authorized by the user;
[PR #14](https://github.com/joshuamyers22/binspect/pull/14) completed the stack.
C1/C2/C4 corrections, C3 inference boundaries/development evidence, and the binsreg
adapter are integrated. A1 ownership/mutation isolation is locally implemented
and verified on `fix/result-ownership`, pending maintainer review/integration.
Next implementation: A2 export and input contracts.
Few-cluster coverage remains unsupported. C3 qualified acceptance/final assessment,
proposed baseline decisions and governance/security/release gates remain open;
merge authorization is not an independent statistical approval or a release.

Owner for these retrieval pointers: Josh Myers. Review before the next affected
task and at each release; remote observations must be rechecked before use.
