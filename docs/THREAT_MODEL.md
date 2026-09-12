# binspect library threat model

Date: 2026-09-12. Scope: 0.1.1 plus the C1/C2 corrections and import isolation;
see the [plan's completion evidence](../binspect-plan.md).
Owner: Josh Myers. Prepared by Codex for maintainer review in G2.
Review before affected API/resource/security changes and before each release.
No residual-risk acceptance or production qualification is implied.

## Assets, actors, and trust boundaries

| Asset | Need | Boundary |
|---|---|---|
| Caller arrays, columns, weights, controls and labels | Confidentiality and integrity | Caller input to validation/conversion; callers may pass sensitive or adversarial data. |
| Estimates, uncertainty, exported tables/figures | Statistical integrity and appropriate disclosure | Core to result/export/rendering; summaries are not anonymization. |
| Caller process and memory | Availability and explicit side effects | Allocations, native numerical dependencies, Matplotlib and optional binsreg. |
| Source, lockfile, CI credentials and release identity | Supply-chain integrity | Contributors/dependencies to Actions artifacts and PyPI OIDC publishing. |
| Review/memory/issue records | Confidentiality and accurate evidence | Local investigation to public Git/PRs; no unrestricted input or raw error dumps. |

Actors include ordinary callers, users of applications embedding the library,
contributors, compromised upstream dependencies, and maintainers with repository
or publishing privileges. Arbitrary Python objects can execute their own
conversion/string methods; binspect is not a sandbox for untrusted Python code.

Data flows from caller validation/preparation to numerical estimation, immutable
container fields (but currently mutable nested arrays), then caller-requested
tables/JSON/figures. The library has no HTTP listener, authentication system,
background service, usage collector, or owned data store. Plain import and ordinary
estimation now defer Matplotlib initialization. Explicit plotting/theme access and
optional dependencies may read their normal configuration, start native numerical
workers or maintain caches; those paths are outside the ordinary-estimation
isolation test. This is distinct from binspect creating an application
configuration or telemetry system.

## Existing limits and failure behavior

Validated constraints include matching shapes, finite-value filtering or explicit
failure via `dropna=False`, nonnegative weights with positive totals, at least
four usable observations, identified x, valid custom edges, and degrees-of-freedom
checks for controls. See [input preparation](../src/binspect/prepared_data.py),
[binning](../src/binspect/core/binning.py), and
[API tests](../tests/test_api.py). This is evidence of specific checks, not a proof
that every dtype/shape/degenerate path is safe.

DPI additionally limits a selected count to [2, retained sample size] and rejects
unvalidated option combinations; [selection tests](../tests/test_selection.py)
cover it. Explicit bin counts, categorical control width, group count, cluster
cardinality, and render sizes do **not** yet have a validated global resource cap.
Per-bin cluster aggregation allocates dense bin-by-cluster arrays. Callers
embedding binspect at a hostile boundary must impose workload limits and process
isolation; P1 must establish supported budgets rather than promise exhaustion
resistance from vectorization.

## Threats, evidence, and residual work

All open risks are owned by Josh Myers and reviewed before their due gate. “Open”
does not mean accepted. No exploit or secret is included in this record.

| ID | Abuse/failure and consequence | Existing control/evidence | Residual work / due gate |
|---|---|---|---|
| T1 | Malformed shape, null/nonfinite data, degenerate weights/design silently alter the sample or estimate. | API/preparation/binning checks and error-path tests; C1 verifies invalid DPI inputs. | A2/C3 broaden type, index, rank/conditioning and sample-count contracts. |
| T2 | Huge bins, categorical expansion, many groups/clusters or rendering allocations exhaust caller resources. | Small-sample checks and DPI bound only; no general cap. Dense allocation identified in AR10. | P1 measured budgets, early rejection/bounded aggregation and hostile-size cases before capacity claims. |
| T3 | Input/result aliasing corrupts stored fit/table/plot consistency. | Frozen outer dataclasses; AR9 demonstrates nested mutation. | A1 ownership/copy/read-only contract and tests. |
| T4 | Unsupported covariance or mixed group coordinates produce credible but misleading output. | C1 explicit scope; C2 rejects shared adjusted coordinates and preserves interval identity; C3 [withholds adjusted-bin uncertainty](adjusted-inference-boundary-review.md) after undercoverage and rejects numerically unidentified controlled x. | Shared adjustment and adjusted-bin uncertainty remain unsupported. C3 expanded coverage and qualified review remain open; C4 accurate diagnostics. |
| T5 | Labels, ranges, small bins, exports or exception messages disclose sensitive inputs. | No automatic telemetry/export; outputs are explicitly requested. Existing errors intentionally expose column names/ranges. | A2/G2 caller redaction contract; P3 scans retained evidence/artifacts. Do not promise redacted exceptions or anonymous aggregates. |
| T6 | Import/estimation adds network connections, subprocesses, workers, or root logging configuration. | [Runtime-boundary tests](../tests/test_runtime_boundaries.py) exercise a fresh process with forbidden operations; existing theme tests cover scoped rcParams. | Preserve these regression contracts; they do not audit arbitrary dependencies/custom caller objects or every optional path. |
| T7 | Modified dependency/action/build tooling substitutes a malicious artifact. | Frozen developer/CI lock and mostly pinned actions; publisher still uses mutable ref and release tools are unpinned. | P3 audits/licenses/secrets/pins/SBOM; R1 locked builds; R2 provenance and artifact verification. |
| T8 | Privileged/bypassed changes reach release without required checks or correct identity. | PyPI reviewer gate exists; [main is unprotected](GOVERNANCE.md). | G1/R1 concrete reviewed controls; R2 exact-commit qualification. OIDC is not an authorization policy by itself. |
| T9 | Security reports are lost or sensitive reports become public. | Existing security policy asks for private reports; public private-reporting feature is currently disabled. | G1/R1 maintainer enables reporting or supplies a verified private route before release. Never redirect vulnerability details to public issues. |
| T10 | Public investigation/memory/CI records retain sensitive data or false acceptance claims. | [Agent agreement](../AGENTS.md), [notes policy](../notes/README.md), sanitized evidence convention. | Human review, P3 secret checks, owned review/delete dates and correction of stale memory. |

## Support and operational boundary

Preserve the existing security support scope: until stable release, only the latest
development version receives security fixes. No response-time SLA is asserted.
[SECURITY.md](../SECURITY.md) explains the currently unavailable private-reporting
route; the maintainer must resolve that gap before release.

No hosted authentication, tenancy, health endpoint, network retry policy, queue,
backup, or RPO/RTO is applicable to the library alone. An embedding application
owns authorization, request limits, redaction, isolation, data retention and
recovery. If binspect later owns such a service or persistent dataset, revise
this model and the project brief before relying on these exclusions.

## Acceptance and incident handling

G2 delivers a reviewed model, explicit limits, tests and owned residual work; it
does not close P1/P3/A1/C2/C3 implementation gaps. The maintainer records accepted,
rejected or deferred risks with rationale and expiry in a PR/ADR. Known correctness,
security or integrity gaps affecting the supported production claim block R2
until corrected or the affected claim is withdrawn.

For suspected exposure or artifact compromise, avoid public payloads, preserve
minimal controlled evidence, identify affected version/artifact identity, and
involve the maintainer. R3 must exercise yank/fixed-release and recovery procedures
before R2; a draft runbook is not evidence that recovery works.
