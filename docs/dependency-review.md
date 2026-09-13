# P2 — dependency configurations and Python support

- Owner: Josh Myers; implementer: Codex; maintainer review/integration pending.
- Date / baseline: 2026-09-12 / `79fb59f`, stacked on P1 PR #22.
- Status: implemented and locally verified on `test/dependency-configurations`;
  maintainer review/integration pending.
- Task: P2 in [the production plan](../binspect-plan.md).

## Contract before iteration

Verify fresh noneditable installs for minimal runtime (without pandas/binsreg),
locked DPI, locked development dependencies, exact declared direct lower bounds,
and current compatible dependencies in separate CI jobs. Include explicit pandas
input/output compatibility. Execute estimation, weighted/clustered/adjusted and
grouped contracts, JSON/ownership and headless plots, plus real optional methods
where installed. Missing extras must identify `binspect-regression[pandas]` or
`binspect-regression[dpi]`. Package installation is not inference qualification.

Keep Polars native defaults and explicit pandas conversion, numerical conventions,
reserved seeds, plotting baselines and package version unchanged. Use synthetic
PCG64 seed 140101 for new checks. Retain Python 3.10–3.13 as the reviewed scope;
do not add 3.14+ or promise all future Python versions merely because metadata
admits them. Test direct floors on Python 3.10 where their wheels exist, and test
current compatible dependencies on 3.13. Current resolution is dated evidence,
not a lock. Do not silently upgrade a floor to conceal a failing configuration.

Inspect actual failures and make the smallest supported compatibility correction
or evidence-backed bound change. Preserve failed probes in this record. Exact
floor constraints must agree with published metadata; resolution must fail if
they cannot coexist. Avoid pulling pandas through test dependencies into the
minimal check. Installed-code smoke tests run outside the source directory and
with Python isolation; record versions and source/lock/configuration identity.

Existing locked unit/optional/reference tests and native smoke are the safety net.
Run full `make check` after source/workflow/metadata changes. Add meaningful
regressions for discovered behavior and matrix configuration, not duplicate tests
of arbitrary implementation details. CI failures must not be skipped or allowed
to continue. Remote configuration is not a claim that remote jobs have passed.

Maximum four evidence-changing phases / 90 minutes / local compute and necessary
dependency downloads: initial floor probes; bounded corrections and isolated
journeys; CI/Python matrix verification; full gate/docs/review. Block High errors:
incorrect outputs, unsupported Python/dependency claims, accidental optional
imports, false installed-code checks, or floor drift hidden by resolution.
Missing matrix/evidence coverage is Medium. At the ceiling retain actual results
and identify unresolved gates; never weaken statistical tolerances or invent
acceptance. Supply-chain audits, release artifact qualification and publication
remain P3/R1/R2 work.

## Evidence ledger

| Phase | Evidence | Actual result / next action |
|---|---|---|
| Baseline | Existing locked CI, metadata and optional import messages inspected | Python 3.10–3.13 locked jobs and a native journey exist. No exact-floor/current-resolution jobs. Original floors were NumPy 1.24, Polars 1.0, SciPy 1.10, Matplotlib 3.7, pandas 2.0 and binsreg 1.0. |
| Initial probes | Python 3.10.21, exact original runtime and pandas floors | Runtime and pandas journeys passed. Original DPI 1.0 installed and selected bins, but the function adapter failed. A direct synthetic upstream call reproduced `TypeError: object of type 'bool' has no len()` in binsreg 1.0's CI validation. |
| Bounded correction | Raise only binsreg minimum to 3.2.1, the existing reference backend | Corrected DPI journey passes with exact runtime floors. Lock diff changes only project requirement metadata; no locked package version changes. No runtime algorithm or statistical tolerance changes. |
| Extra interaction | Resolver dry run with all six exact floors after the correction | No solution: binsreg 3.2.1 requires plotnine ≥0.13, whose admitted versions require pandas ≥2.1. Standalone pandas 2.0 remains functional. `lower-pandas` checks that direct floor; `lower-dpi` checks runtime/binsreg direct floors and resolves pandas transitively (2.3.3 locally). Do not represent all optional floors as a single compatible install. |
| Matrix | Ten isolated noneditable installs, including minimal Python 3.10–3.13, locked DPI/all extras, three floor jobs and fresh current resolution | All ten final journeys passed locally on macOS arm64 with source hashes guarded before/after each check. CI adds distinct jobs with fail-fast disabled; existing Linux/macOS full locked jobs remain. |
| Full gate | `make check` | Passed: 458 unit tests, 34 DPI/adapter and 40 Statsmodels reference tests, 94.65% coverage, strict mypy (38 files), all four import contracts, native no-pandas journey, all development coverage protocols, 38 documentation blocks plus quickstart, strict MkDocs, four figure baselines at RMS 0.0, and sdist/wheel builds. Final launcher hash-guard edit also passed Ruff/format; it is independently exercised by every final matrix run. |

## Retained local configurations

[Machine-readable results](dependency-results.json) retain every installed
distribution version and common source/configuration hashes. Checks completed on
2026-09-12 local time (2026-09-13 UTC). All rows below passed; `—` means the optional
package was absent and its error/import boundary was exercised.

| Profile | Python | NumPy | Polars | SciPy | Matplotlib | pandas | binsreg |
|---|---|---|---|---|---|---|---|
| minimal | 3.10.21 | 2.2.6 | 1.44.2 | 1.15.3 | 3.10.9 | — | — |
| minimal | 3.11.16 | 2.4.6 | 1.44.2 | 1.17.1 | 3.11.1 | — | — |
| minimal | 3.12.11 | 2.5.2 | 1.44.2 | 1.18.1 | 3.11.1 | — | — |
| minimal | 3.13.15 | 2.5.2 | 1.44.2 | 1.18.1 | 3.11.1 | — | — |
| dpi | 3.12.11 | 2.5.2 | 1.44.2 | 1.18.1 | 3.11.1 | 3.0.5 | 3.2.1 |
| locked | 3.12.11 | 2.5.2 | 1.44.2 | 1.18.1 | 3.11.1 | 3.0.5 | 3.2.1 |
| lower | 3.10.21 | 1.24.0 | 1.0.0 | 1.10.0 | 3.7.0 | — | — |
| lower-pandas | 3.10.21 | 1.24.0 | 1.0.0 | 1.10.0 | 3.7.0 | 2.0.0 | — |
| lower-dpi | 3.10.21 | 1.24.0 | 1.0.0 | 1.10.0 | 3.7.0 | 2.3.3 | 3.2.1 |
| current | 3.13.15 | 2.5.3 | 1.44.2 | 1.18.1 | 3.11.2 | 3.0.5 | 3.2.1 |

The floor/metadata checker has four regression tests: matching direct floors,
rejection of an upgraded floor, rejection of missing/changed metadata constraints,
and distinguishing DPI's transitive pandas from the standalone direct pandas
floor. All four passed. Missing-extra messages already named the correct
distribution and needed no source change.

The first package build and lock refresh hit sandbox DNS failures for build
dependencies. Authorized network retries succeeded; these were not dependency
compatibility failures. Python 3.10.21 and 3.11.16 were installed for the local
matrix; existing interpreters supply 3.12.11 and 3.13.15. The full gate uses the
existing CPython 3.12.14 renderer environment. No Python support version is added.

## Reproduction and limits

See the [configuration guide](site/guide/dependencies.md) and
[launcher](../validation/dependencies.py). Run each profile with
`make dependencies DEPENDENCY_PROFILE=<profile> DEPENDENCY_PYTHON=<version>`.
CI invokes the standard-library launcher directly with its selected interpreter;
the minimal child never installs pytest or pandas through development extras.
Every run uses a temporary environment, checks installed dependencies, executes
with `-I` outside the checkout, and requires a noneditable installed package.
The old output record is removed before execution; failure cannot retain a stale
pass. Hashes are checked before and after execution to reject source changes
during a run. CI prints the full version/provenance record in job logs.

The retained matrix record contains synthetic-check metadata and package versions,
not caller inputs, local environment paths, or raw logs. Its Git revision is the
parent commit because local verification precedes committing this change; hashes
identify the tested library, launcher, smoke script, floor file, metadata and lock.
Passing these installed journeys does not qualify all allowed cross-products,
all upstream methods, pixel equivalence across versions, or statistical coverage.
The original backend failure is resolved by the bound correction, not by weakening
or skipping the adapter check. Arbitrary newer backends retain unverified status.

## Disposition

Local implementation and verification are complete within the four-phase ceiling.
No unresolved High/Medium implementation finding remains from these probes.
Maintainer review/integration and actual remote CI remain separate gates. No new
supported Python version, release or independent inference acceptance is implied.
P3 supply-chain and secret checks are the next implementation item.
