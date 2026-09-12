# Project brief — binspect

Date: 2026-09-12. Baseline: package 0.1.1 at `59c6a39`.
Status: populated planning baseline; G1 records maintainer acceptance and any
amendments. Adapted from the production template's project brief for an existing
distributable library. See the [alignment record](docs/template-alignment.md).

## Outcome

**Problem and users:** Python researchers and analysts need inspectable binned
summaries, explicit uncertainty assumptions, and reusable figures when assessing
departures from a linear fit.

**Critical journeys:** estimate from arrays/dataframe columns; adjust for controls;
use weights/clusters; compare groups on interpretable coordinates; inspect/export
results; compose plots on supplied axes; install the published distribution.

**Measurable success:** each supported journey has executable acceptance evidence;
no unresolved supported-method correctness defect from the adversarial review;
strict JSON exports and stable results after caller mutation; passing declared
Python/OS and dependency configurations; clean wheel/sdist installs; reproducible
statistical-reference and release evidence. Performance claims must satisfy the
measured budgets established by P1 rather than an invented universal target.

**Non-goals:** causal identification, model certification, production forecasting
or trading decisions, a hosted service, runtime data collection, automatic usage
reporting, a universal dataframe layer, and new statistical theory. Formal
simultaneous inference and quantile regression are deferred feature designs.

## Constraints and risk

| Field | binspect contract / outstanding decision |
|---|---|
| Runtime/deployment | In-process Python package installed by callers; Python 3.12 local default, currently tested on 3.10–3.13 Linux/macOS. The manifest admits newer Python versions that the current matrix has not validated. |
| Expected load/growth | P1 measures 10k–1M observations with varying bins, groups, clusters, and control width; 10M remains exploratory. No supported capacity ceiling is claimed until measurement. |
| Data classification/retention | Caller inputs can be sensitive. The library does not own their storage or retention. Examples/CI use synthetic or explicitly licensed public data; no raw caller data, labels, unrestricted logs, or identifying hashes enter tracked review/memory records. |
| Availability/recovery | Synchronous library calls; no service uptime SLO, on-call rotation, hosted-data RPO/RTO, or queue. Failures must be explicit and preserve caller state; package rollback means reinstalling a known version or issuing a fixed release. |
| Latency/capacity | Measure estimation and rendering separately, include allocation/conversion cost, and define pathological-input behavior. No real-time deadline or service tail-latency promise. |
| Legal/licensing | Existing repository is MIT; retain it. P3 must verify dependency and bundled-data compatibility. Template proprietary defaults do not authorize a license change. |
| Budget/deadline | No delivery date or monetary budget has been assigned. Use milestone dependencies as due gates; task owners set bounded verification resources before material work. |
| Ownership/support | Package metadata identifies Josh Myers as maintainer; G1 records review/release responsibilities, support cadence, and qualified statistical reviewer assignment. Do not infer a staffed service commitment. |
| Concurrency | No library worker service or shared-state concurrency guarantee is promised. A1 defines ownership; theme/global-state behavior needs documented limits for callers using threads. |

Top failure scenarios, with owners assigned through G1/G2:

1. A labelled method silently computes a different estimator or covariance.
2. Adjusted/grouped results mix coordinates or compare different intervals.
3. Aliasing, malformed data, rank deficiency, or huge intermediate allocations
   produce inconsistent results or exhaust caller resources.
4. Sensitive values escape through exceptions, exported evidence, figures, CI
   records, or investigation notes.
5. A compromised dependency/action or unverified build publishes an incorrect
   artifact under a trusted package identity.

## System outline

**Sources of truth:** code and executable tests determine current behavior;
this brief and reviewed ADRs define intended constraints; the
[plan](binspect-plan.md) orders work. The changelog records releases; project
[memory](PROJECT_MEMORY.md) only indexes verified evidence.

**Dependencies and boundaries:** pandas/array inputs enter validation/preparation;
the NumPy/SciPy core estimates results; optional binsreg integration selects bins
or supplies separate original-coordinate function inference;
result modules export summaries; Matplotlib layers render. Package consumers and
CI/PyPI distribution are separate trust boundaries. Keep runtime I/O and side
effects explicit. Current engine choices and the stricter template defaults are
reconciled in the [proposed baseline ADR](docs/decisions/0001-existing-library-baseline.md).

**Invariants:** partition/weight/coordinate consistency; correct observation-level
FWL; explicit covariance/df; descriptive rather than causal/test claims; no silent
method fallback; honest undefined results; stable owned result data; strict export
schemas; scoped plotting state; no import-time external work.

**Statistical evidence:** C3 creates the method analysis plan with explicit sample,
units, missingness, design matrix, covariance, diagnostics, and final-assessment
cases. Forecasting splits, as-of trading features, economic utility, Bayesian
priors, and a persisted dataset catalog are not implied by a plotting/diagnostics
library. Dependence and partition-selection effects remain applicable inference
questions. Evidence export is opt-in and caller-owned.

**Delivery:** retain the existing GitHub-release-to-PyPI route while R1–R2 harden
locked builds, verification, action pins, SBOM/provenance, and artifact tests.
No license, hosted infrastructure, or GitHub policy is changed by this document.

**Observability/replay:** use controlled warnings/errors, reproducible synthetic
cases, numerical references, CI and install results, and repeated benchmarks.
R3 defines release/monthly review ownership and evidence retention. Service event
schemas and runtime collectors are out of scope unless a future application needs
them and defines privacy/retention contracts.

## Acceptance evidence

| Requirement | Verification | Accountable owner | Status |
|---|---|---|---|
| Statistical meaning | C1–C4 counterexamples, references, analysis plan, final-assessment simulations | Maintainer; named statistical reviewer before C3 acceptance | Open |
| Integrity/API | A1–A3 mutation, input, export and compatibility tests | Maintainer | Open |
| Figure/user journey | D1–D3 executed examples, docs and export checks | Maintainer | Open |
| Capacity/support | P1–P2 measured workloads and dependency matrix | Maintainer | Open |
| Security/distribution | G2, P3, R1–R3 threat controls, audits, artifact/provenance evidence | Maintainer | Open |
| Repository continuity | G1 agreement, memory, bounded records, ownership/checklist | Maintainer | Prepared for review; see [G1/G2 evidence](docs/repository-baseline-review.md) |

The earlier 160-test, 90.41%-coverage baseline is recorded in the
[adversarial review](docs/project-plan-review.md); it does not close these gates.

## Open decisions

| Decision | Due gate | Owner / evidence |
|---|---|---|
| Accept or amend the existing pandas/numerical/type-checker baseline | G1, before broader engine/contract changes | Maintainer; proposed ADR |
| Choose grouped adjusted coordinates and supported combinations | Before C2 implementation beyond a bounded rejection fix | Maintainer; C2 design/reference cases |
| Validate covariance, HC1 disposition, and adjusted-bin estimands | Before C3 sign-off; method plan before inference changes | Maintainer and designated statistical reviewer |
| Define measurable capacity limits and benchmark host | Before P1 acceptance or performance claims | Maintainer; benchmark evidence |
| Confirm GitHub controls, publisher identity, support and recovery responsibility | G1 planning; verified before R2 | Maintainer; actual configuration evidence |
| Assign calendar release date and reviewer availability | Before scheduling R2 | Maintainer; no date assumed |
