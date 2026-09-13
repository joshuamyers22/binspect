# binspect project memory

A retrieval index, not a transcript, task history, or source of truth. Verify
each entry before use; update stable keys in place and remove stale claims.
No caller data, private logs, secrets, or hidden reasoning belong here.

## Verified constraints and current state

| Key | Fact / limitation | Evidence | Verified |
|---|---|---|---|
| `package-identity` | Distribution `binspect-regression`, import `binspect`, existing MIT license. | [manifest](pyproject.toml), [license](LICENSE) | 2026-09-12 |
| `library-scope` | In-process descriptive diagnostics; no hosted service or runtime telemetry. User-directed Polars-native preparation/tables retain optional pandas compatibility; remaining numerical/tooling baseline decisions are proposed. | [brief](PROJECT_BRIEF.md), [ADR-0002](docs/decisions/0002-polars-native-dataframes.md) | 2026-09-12 |
| `quality-gate` | `make check` includes native use without pandas, frozen numerical references, all development coverage protocols, executable docs/strict MkDocs and four guarded figure baselines. Full render qualification uses CPython 3.12 plus the recorded renderer/fonts; portable unit exports run on the wider CI matrix. Default pytest omits integration/external tests. | [Makefile](Makefile), [CI](.github/workflows/ci.yml), [renderer](tests/baseline/manifest.json) | 2026-09-12 |
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
| `polars-contract` | A2 makes Polars the default table type regardless of input; `.to_pandas()` explicitly converts. Inputs align by position, including named Series controls. Explicit categorical orders survive filtering; ordinary string categories sort observed levels. Native use does not install/import pandas; upstream binsreg still uses pandas internally. Review/integration pending. | [Contract](docs/INPUT_OUTPUT_CONTRACT.md), [parity tests](tests/test_polars_contract.py), [native gate](validation/native_smoke.py) | 2026-09-12 |
| `evidence-export` | Schema v1 exports include exclusion counts/design identity and typed group labels; `to_json()` is deterministic. `to_evidence()` only records caller-supplied plan/input/lock/code references, with timestamp outside payload; no implicit fingerprints, reads, raw rows or provenance verification. | [Contract](docs/INPUT_OUTPUT_CONTRACT.md), [regressions](tests/test_evidence_export.py) | 2026-09-12 |
| `compatibility-policy` | A3 inventories actual API/defaults and supported combinations, with executed migrations. Pending incompatible changes are allocated to proposed 0.2.0, not a patch; package remains 0.1.1. Axes identity/scoped themes remain intact. Policy acceptance/integration pending; availability does not establish statistical or dependency qualification. | [Policy](docs/COMPATIBILITY.md), [inventory](docs/API_INVENTORY.md), [verification](docs/compatibility-policy-review.md) | 2026-09-12 |
| `executable-docs` | `docs/site` has source-generated mkdocstrings API and strict local links/anchors; D3 adds nine gallery blocks to the prior 29 plus quickstart. Each page runs in a fresh process/temp directory. Root `/site/` alone is ignored; quickstart output defaults to `.work/quickstart.png`. No hosting/deployment added; publication/review pending. | [Guide](docs/site/index.md), [runner](validation/documentation.py), [D1 evidence](docs/user-guide-review.md), [D3 evidence](docs/example-gallery-review.md) | 2026-09-12 |
| `figure-qualification` | D2 adds four initial PNG baselines (RMS limit 0.5/255; local rerender 0.0), PNG/PDF/SVG structure/text/geometry tests and vision/background sheets. Existing presets lose labels/context on dark backgrounds; general accessibility and vector pixel equivalence are unqualified. Baselines never auto-update; renderer mismatch fails. Maintainer visual acceptance pending. | [Guide/review](docs/site/guide/figure-exports.md), [evidence](docs/figure-export-review.md), [baseline policy](tests/baseline/README.md) | 2026-09-12 |
| `synthetic-gallery` | D3 has seven Polars-native cases with PCG64 seeds 120101–120107, separate from assessment seeds. Markdown is the executable source; the checkout launcher retains figures and source/lock/version/input/result hashes under `.work/gallery` by default. Discrete-bin merging and sparse grouped tails intentionally retain warnings. No coverage qualification is implied. | [Gallery](docs/site/guide/gallery.md), [launcher](examples/gallery.py), [manifest](docs/site/assets/gallery/manifest.json), [verification](docs/example-gallery-review.md) | 2026-09-12 |
| `workload-limits` | P1 replaces dense bin-by-cluster score/count storage with occupied-pair aggregation, preserving CR1. The separate benchmark measures 10k–1M Polars rows with 2 GiB/120-second child guards and proposed host-specific budgets; pending acceptance cannot pass budget enforcement. Existing default rugs cap at 2,000 marks. Control matrices remain dense; 10M/general capacity are unqualified. | [Scope](docs/site/guide/performance.md), [evidence](docs/performance-review.md), [storage regressions](tests/test_cluster_storage.py), [budget checker](validation/performance_check.py) | 2026-09-12 |
| `dependency-configurations` | P2 tests ten fresh installed configurations: minimal Python 3.10–3.13, DPI, locked all extras, runtime/pandas/DPI direct floors and current compatible packages. Binsreg 1.0 rejects the adapter CI request; minimum is now 3.2.1 with locked versions unchanged. Standalone pandas 2.0 passes; DPI resolves newer pandas transitively. Native/default tables remain Polars. Matrix journeys are not full inference or all-version qualification. | [Scope](docs/site/guide/dependencies.md), [evidence](docs/dependency-review.md), [floor regressions](tests/test_dependency_floors.py), [CI](.github/workflows/ci.yml) | 2026-09-12 |
| `supply-chain-gate` | P3 adds an isolated online gate for all locked versions, license metadata, full available history/tracked/artifact secret scans and validated artifact-linked CycloneDX. Build/audit tools and workflow actions are pinned. Six license reviews (binsreg, certifi, docutils, fqdn, hypothesis, pathspec) remain pending and block the gate; no waiver/release acceptance is supplied. Three historical source-hash scanner false positives have exact value/path exclusions verified against historical source. | [Scope/decisions](docs/SUPPLY_CHAIN.md), [verification](docs/supply-chain-review.md), [regressions](tests/test_supply_chain.py), [exception registry](validation/supply-chain-exceptions.json) | 2026-09-12 |

## Open work

The [plan](binspect-plan.md) owns ordering and task status. PRs #6–#14 were
merged into main on 2026-09-12 at `e206e0c`, explicitly authorized by the user;
[PR #14](https://github.com/joshuamyers22/binspect/pull/14) completed the stack.
C1/C2/C4 corrections, C3 inference boundaries/development evidence, and the binsreg
adapter are integrated. A1 ownership/mutation isolation is locally implemented
and verified on `fix/result-ownership`, pending maintainer review/integration.
A2 adds the user-directed Polars-native boundary and versioned input/evidence
contracts on `feat/export-input-contracts`, stacked on A1; review/integration pending.
A3 documents compatibility/release allocation on `docs/compatibility-policy`,
stacked on A2; policy acceptance/integration pending. D1 guide/reference and CI
checks are implemented on `docs/executable-user-guide`, stacked on A3, with
maintainer review/integration and hosting/publication pending. D2 export/baseline
checks are implemented on `test/figure-exports`, stacked on D1, with visual
acceptance/integration pending. D3 reproducible examples are implemented on
`docs/reproducible-gallery`, stacked on D2, with maintainer review/integration
pending. P1 occupied-cluster aggregation and workload/budget tooling are implemented
on `perf/cluster-workloads`, stacked on D3; baseline/controlled-runner acceptance
and integration remain pending. P2 dependency configurations and the binsreg minimum
correction are implemented on `test/dependency-configurations`, stacked on P1;
maintainer review/integration remains pending. P3 supply-chain tooling is implemented
on `security/supply-chain-checks`, stacked on P2; six license reviews block its
gate/acceptance, and maintainer review/integration remains pending. Next implementation:
R1 artifact/workflow qualification without publishing.
M2 maintainer acceptance remains open.
Few-cluster coverage remains unsupported. C3 qualified acceptance/final assessment,
proposed baseline decisions and governance/security/release gates remain open;
merge authorization is not an independent statistical approval or a release.

Owner for these retrieval pointers: Josh Myers. Review before the next affected
task and at each release; remote observations must be rechecked before use.
