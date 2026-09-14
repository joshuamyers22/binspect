# binspect — production project plan

Updated 2026-09-13 after the v0.2.2 release: the immutable tag points to
`49cd7c2135992986ba356f7829c9b8f17b88c4a2`, release run `34789980329`
completed successfully, and PyPI serves the qualified wheel and sdist. The
post-release evidence merged to main as `f684420dfed300e14ca5f3faf1e722421704526b`.
Historical verification records retain their review-time status; this observation
supersedes pending-integration labels, not independent acceptance requirements.

The [release-stack integration review](docs/release-stack-integration-review.md)
records the earlier main-based reconciliation, artifact-integrity correction and
scoped license acceptance. PR #32 head `5d74040` and main `f9d0e08` each passed all
35 jobs; manual maintenance run `34785343032` passed all three locked/current profiles.

Polars-native preparation/default tables with pandas inputs and explicit conversion
are the user's accepted direction through [ADR-0002](docs/decisions/0002-polars-native-dataframes.md).
See the integrated [ownership evidence](docs/result-ownership-review.md),
[input/export contract](docs/INPUT_OUTPUT_CONTRACT.md),
[compatibility policy](docs/COMPATIBILITY.md), [guide](docs/site/index.md),
[figure scope](docs/site/guide/figure-exports.md), [gallery](docs/site/guide/gallery.md),
[performance evidence](docs/performance-review.md) and
[dependency scope](docs/site/guide/dependencies.md). Visual, policy, statistical and
performance-budget acceptance remain explicit review gates; site hosting is not configured.

P3, R1 and R3 are integrated through PR #30; the 0.2.0 preparation is integrated
through PR #32.
[Six exact license scopes](docs/SUPPLY_CHAIN.md) were accepted by Josh Myers on
2026-09-13 through 2026-10-13, and the fresh local P3 gate passes. R1 has passing actual
artifact handoff/installation evidence; R3 has passing local and GitHub reference
exercises but awaits its first scheduled run and actual operator evidence. Main
remains unprotected and private vulnerability reporting disabled. Josh confirmed the
exact PyPI Trusted Publisher identity on 2026-09-13.
The [license dossier](docs/LICENSE_REVIEW_DOSSIER.md) supplies exact archive notices
and distribution/profile scope for all six accepted decisions. The acceptance does
not change dependencies, authorize broader redistribution or waive future audits.

**R2 completed for v0.2.2 after two safely preserved failed attempts.** The
[0.2.0 record](docs/releases/0.2.0-readiness.md) and
[0.2.1 record](docs/releases/0.2.1-readiness.md) retain both failed runs and exact
signed pairs; the [0.2.2 record](docs/releases/0.2.2-readiness.md) owns the outcome. A bounded
[R2 renderer repair](docs/release-readiness-review.md) obtains the existing Python
3.12.14 pin through uv while preserving all image/renderer guards; its local and
CI comparisons pass at RMS 0.0. The authorized v0.2.0 workflow built, installed,
audited and signed its exact pair, then GitHub CLI 2.98 rejected redundant mutually
exclusive actor-identity selectors; publish was skipped. Recovery removes only the
redundant selector while preserving exact certificate/repository/tag/commit/run policy.
The v0.2.1 recovery passed those gates but its pinned publisher rejected valid Core
Metadata 2.5 before upload. Version 0.2.2 pins the signed PyPA v1.14.2 repair and
completed regression, full CI/audit, immutable tagging, explicit publication
authorization, protected-environment review, Trusted Publishing, public-index byte
reconciliation, provenance checks and a fresh installed-package journey.

C3 final assessment and qualified statistical acceptance remain open. The
[adjusted FWL uncertainty withdrawal](docs/adjusted-inference-boundary-review.md)
remains in force. The [expanded grid](docs/expanded-coverage-review.md) records
78.2% coverage for the uneven-cluster bin-average case. The separate
[binsreg function adapter](docs/binsreg-adapter-review.md) records 93.6% iid DPI,
94.3% with 60 balanced clusters and 42.4% with three uneven clusters at nominal
95%. These are distinct targets; the last result remains a diagnostic failure.
Merge authorization does not establish nominal coverage, upstream endorsement,
ADR acceptance, or completion of release/governance gates. Reserved assessment
seeds remain unrun. G1/G2 decisions and C3 claim qualification remain open as
specified in their records.

The user moved the binsreg integration ahead of A1. That implementation slice is
complete; other new estimators remain behind the correctness milestone. This
production plan supersedes the original unordered v0.5+ wishlist and its blanket
claim that v0.1–v0.4 was complete.

Aligned on 2026-09-12 with the production project template at `d59f3e6`.
The [project brief](PROJECT_BRIEF.md) defines the library scope; the
[template alignment](docs/template-alignment.md) maps requirements to evidence,
open tasks, and applicability decisions. The
[proposed baseline ADR](docs/decisions/0001-existing-library-baseline.md) records
departures from the template's engine/tool defaults. This is plan alignment,
not a claim that the repository already conforms. G1–G2 establish the missing
baseline alongside C1; their relevant contracts precede broader changes.

The [adversarial plan review](docs/project-plan-review.md) records the evidence,
counterexamples, and remaining risks behind this order. Updating this plan does
not resolve the implementation findings.

## 1. Product and scope

`binspect` means bin + inspect. It provides binned scatterplots and descriptive
diagnostics of departures from a linear fit. The import is `binspect`; the
distribution is `binspect-regression`.

The production target is a dependable Python library with explicit statistical
assumptions, reproducible results, composable publication figures, and verified
installable artifacts. A descriptive lack-of-fit score cannot establish that a
model is correct, identify causality, or replace a specification test.

Use Polars, NumPy, SciPy, and Matplotlib as required dependencies, with optional
pandas compatibility under the user-directed ADR-0002. The remaining baseline
ADR review and reference-validation conditions still apply. Use
`binsreg` as an optional integration for methods it implements; use independent
reference packages in validation without making them runtime requirements.
Interactive/web output, a general dataframe abstraction, and new inference theory
are outside this production milestone.

## 2. Verified baseline

| Area | Present at the reviewed commit | Qualification / remaining work |
|---|---|---|
| Estimation | Quantile, equal-width, custom bins; weighted means and dispersion; observation-level linear fit | C1–C4 below address selector and statistical contracts |
| Diagnostics | Weighted between/within decomposition, normalized lack of fit, heuristic verdict | Thresholds fixed; raw counts can overstate information |
| Controls | Numeric/categorical controls, weighted FWL, mean restoration | Grouped common-bin coordinates need correction |
| Uncertainty | Independent bin-mean intervals, classical slope SE, CR1 cluster paths | No selectable HC1 slope estimator; adjusted-bin inference needs validation |
| Results | Single/grouped results, tables, summaries, JSON-compatible exports | Frozen dataclasses contain mutable arrays; export provenance incomplete |
| Figures | Eight layers; notebook/paper/deck themes; audit and faceted figures | Artist and theme tests exist; visual baselines/accessibility evidence incomplete |
| Quality | Ruff, strict mypy, import boundaries, Python 3.10–3.13 on Linux/macOS, 85% coverage gate | Local baseline: 160 tests passed, 90.41% coverage on Python 3.12 |
| Packaging | Hatchling, lockfile, CI builds, release workflow using Trusted Publishing | Trigger is GitHub release publication; deployment settings require separate verification |
| Documentation | README, quickstart script, contribution/release instructions, hero image | No built documentation site, API reference, or docs CI |
| Validation | NumPy matrix equivalence tests, deterministic behavioral tests | No tracked external comparison workflow or Hypothesis property suite |

The old v0.1–v0.4 labels described intended feature sequencing, not package releases
or evidence of production readiness. Actual releases are recorded in
[CHANGELOG.md](CHANGELOG.md). Future release numbers are assigned when scope is
known; milestone IDs below are stable task identifiers.

## 3. Statistical contracts

These govern implementation and tests. Distinguish current behavior from changes
that require the acceptance criteria below.

### Bins and weighted means

Quantile edges currently use NumPy's interpolated quantiles. Values on an interior
edge go into the lower bin. Ties are not split; repeated edges and empty intervals
can reduce the number of bins. The old empirical-CDF assignment equation was not
an exact specification of this implementation. Equal counts are a conditional
property for suitable untied inputs, not a universal invariant.

Every retained row has one assignment; assignments and edges reconstruct the same
partition; counts sum to retained rows; each estimated bin has positive weight.
Custom outer bounds are preserved. Grouped exports must identify pooled intervals
even when individual groups have no observations there.

For weights `w_i >= 0`, let `W_j = sum_{i in j} w_i`. Then
`ybar_j = sum_{i in j} w_i*y_i / W_j` and similarly for `xbar_j`.
These means match a saturated **WLS** indicator fit with the same weights.
Unweighted means match OLS. Reliability weights are not frequency counts or a
complete survey sampling design.

`zero_weight="retain"` permits zero-weight rows to affect partition selection and
descriptive counts. Thus they can indirectly change binned estimates by moving
edges. Only `zero_weight="drop"` promises equivalence to omitting those rows
throughout the pipeline.

### FWL and adjusted coordinates

Residualize both variables on an intercept and encoded controls using the same
weights as the full least-squares fit; restore their weighted means for display.
Use a rank-aware least-squares solution rather than an explicit matrix inverse.

The slope fitted to the **observation-level residualized variables** equals the
coefficient on x in the full model when x is identified. A regression on bin means
generally has a different slope. Adjusted-model slope SEs must use the full
design's residual degrees of freedom and the chosen covariance convention.

Group-specific residualization changes coordinates. Reusing pooled residual-space
edges does not by itself define a common adjusted estimand; C2 must resolve this.
FWL coefficient equivalence alone does not validate inference on adjusted bin means
or identify a nonlinear covariate-adjusted conditional mean function.

### Decomposition and display

Use the same observations, weights, and coordinate system for all terms:

```text
ybar       = sum_i w_i*y_i / sum_i w_i
SS_total   = sum_i w_i*(y_i - ybar)^2
SS_between = sum_j W_j*(ybar_j - ybar)^2
SS_within  = sum_i w_i*(y_i - ybar_bin(i))^2
SS_lof     = sum_j W_j*(ybar_j - fitted_line(xbar_j))^2

SS_between + SS_within = SS_total
eta_sq = SS_between / SS_total
gap    = SS_lof / SS_total
```

For positive total variance, gap is nonnegative and is zero exactly when all
positive-weight bin means lie on the fitted line, within numerical tolerance.
There is no general ordering between eta-squared and observation-level linear
R-squared. Current zero-total-variance outputs use zero for eta-squared and gap;
document this convention rather than interpreting it as statistical evidence.

Deviation marks show signed vertical departures. Their visual lengths or filled
areas do not equal the weighted squared sum or normalized gap.

For a signed SD reference slope `s = sign(r)*sd_y/sd_x`, the identity is
`linear_slope = abs(r)*s`, not `r*s`. For exactly zero covariance the current
implementation chooses the positive orientation; constant y gives a zero slope.
Tests must include positive, negative, and zero correlation.

### Uncertainty and verdicts

Separate the estimand, weight interpretation, covariance estimator, finite-sample
correction, and reference distribution. Current independent weighted bin SEs use
weighted dispersion and Kish effective sample size. Classical slope SEs and CR1
cluster SEs are distinct procedures. Two available clusters make a computation
possible; they do not establish reliable small-sample coverage.

Current per-bin CR1 uses clusters represented in that bin and a correction
`G_j/(G_j-1)`; its t intervals use `G_j-1` degrees of freedom. This is not generally
the same finite-sample correction as one global saturated clustered regression.
Reference comparisons must match the design and correction being claimed.

Verdicts are descriptive heuristics, with default gap threshold 0.02 and minimum
effective bin count 30 under the C4 correction. Policies are configurable and
exported; classification can be disabled. Clustered classification requires an
explicit caller threshold, and constant outcomes are not assessed. These are not
power calculations, significance tests, or validation of linearity/coverage.

Per-bin IQR describes outcome dispersion. It is neither a confidence interval for
the median nor a fitted conditional quantile regression. Uniform confidence bands
require simultaneous inference; connecting pointwise interval endpoints is
insufficient.

## 4. Ordered implementation milestones

Tasks below remain **open** unless their implementation status is recorded in the
completion table. Local verification does not imply maintainer acceptance or
release. Work in listed order within each milestone unless a
dependency explicitly permits otherwise. Each task is intended as one reviewable
PR; split large tasks into contract, implementation, and validation PRs as needed.
Josh Myers is the accountable maintainer identified by package metadata; this does
not imply an on-call or delivery-date commitment. Assign an implementer and any
independent statistical reviewer before each task begins. Record due dates by the
milestone gates below until a calendar release date is selected. The implementer
records evidence; the maintainer accepts completion. No task is
done merely because it has an implementation or a passing coverage percentage.

### M0 — project requirements and repository baseline

**Dependencies:** none. **Exit:** G1–G2 have owned, reviewed evidence. These can
proceed alongside the bounded C1 correction; finish the relevant decisions before
C2/C3 contract changes. Do not defer security or ownership decisions until release.

| Order | Task | Acceptance criteria |
|---|---|---|
| G1 | Adopt the applicable repository agreement | Review the populated project brief and baseline ADR; record accepted decisions and owners without claiming agent self-approval. Add an adapted `AGENTS.md`, keyed/dated/evidence-linked `PROJECT_MEMORY.md`, bounded notes policy, ADR and improvement/verification records, and an evidence-based release checklist. Document repository/review ownership and actual GitHub control capabilities. Update memory only for durable facts. Preserve existing MIT licensing; do not copy the generator's proprietary default. Existing plan/review documents can satisfy equivalent records where their required fields are present. |
| G2 | Define the library threat model and support boundary | Cover caller arrays/dataframes/labels, optional dependencies, serialized output/figures, CI credentials, and published artifacts. Address invalid shapes/nonfinite values, pathological allocation requests, accidental sensitive-data exposure, malicious dependency/build changes, and artifact substitution. Specify tests, input/resource limits, supported versions, private reporting, risk owner and review date. Keep runtime import/estimation free from unsolicited network, logging, and configuration side effects. Document that service auth/health endpoints and hosted-data backup are outside this library's scope; do not claim that local execution eliminates untrusted input or supply-chain risk. |

### M1 — statistical correctness and supported combinations

**Dependencies:** C1 may start immediately; C2/C3 depend on the relevant G1/G2
contracts. **Exit:** C1–C4 accepted, known misleading behavior corrected
or explicitly unavailable, and applicable regression checks run in PR CI.

| Order | Task | Acceptance criteria |
|---|---|---|
| C1 | Correct DPI selection and integration metadata | Read the actual DPI result rather than ROT; use a supported upstream result field with documented regularization/mass-point behavior. Validate finite integer output. Make failed DPI selection an actionable error or an explicit, recorded fallback, never silently label ROT as DPI. Fix the extra-install message to `binspect-regression[dpi]`. Test success, distinct ROT/DPI values, unavailable dependency, failed selection, and discrete x. Add a required real-library check on a pinned environment; record selected rule, requested/actual bins, and any fallback in results. |
| C2 | Define grouped adjusted coordinates and interval identity | Reproduce the shifted-control failure in the review. Specify pooled versus within-group adjustment and mean restoration before implementing common bins; preserve per-group coefficient meaning. Until a coherent common-coordinate contract is implemented, reject `controls` plus `common_bins=True` with a specific explanation and supported alternative. Do not fix it merely by widening edges. Preserve pooled interval IDs or explicit empty intervals in grouped tables; never compare renumbered bins as though they were identical. Test disjoint support, empty intervals, shifted controls, weights, zero weights, missing inputs, and group-labelled failures. |
| C3 | Validate the inference contract | Write an estimand/weights/covariance/df table for every supported combination of controls, weights, and clusters. Validate observation-level OLS/WLS coefficients and classical/CR1 slope SEs against an independent full-design reference. Validate per-bin CR1 against matched within-bin intercept-only fits, explicitly distinguishing global saturated corrections. Assess uncertainty from estimated controls and data-selected partitions; label approximate conditional intervals accordingly or disable unsupported combinations. Resolve HC1 explicitly: implement a validated selectable estimator or document it as deferred and classical assumptions as a limitation. Add pinned mandatory reference checks and seeded coverage simulations with predeclared Monte Carlo tolerances; keep upstream drift checks separate. |
| C4 | Make diagnostic claims and policies accurate | Correct FWL and signed-SD claims in source docs, README, and tests. Remove statements equating displayed area with gap. Define configurable verdict thresholds, an opt-out, and exported policy values. Distinguish raw rows, positive-weight rows, effective sample size, and cluster counts; do not classify support solely from retained zero-weight rows. Document constant outcomes and unsupported/undefined inference. Test threshold boundaries, negative/zero correlation, constant y, highly unequal weights, sparse clusters, rank deficiency, and nonidentified x. |

C1 must also decide which weighted, clustered, controlled, and equal-width requests
can be faithfully delegated to the selector. Pass compatible metadata through or
reject unsupported combinations explicitly; an unweighted selector must not be
presented as optimal for a different estimation specification.

Before C3 changes inference, complete a project-specific statistical analysis plan
using the template fields: estimand, sample unit/inclusion, units and transformations,
ordered design/intercept, weights, covariance/df, assumptions, dependence, partition
selection, diagnostics, practical thresholds, multiple-comparison limitations,
numerical rank/conditioning, and absolute/relative tolerances. Mark forecasting,
financial decision utility, and Bayesian fields inapplicable with reasons. Keep
simulation development separate from locked final-assessment seeds/cases. Bind
validation results to input/plan/lock hashes, revision, reference versions, and
random-generator identity. The maintainer names a qualified reviewer before C3
sign-off; the implementation agent's review alone does not establish validity.

### M2 — result integrity and API stability

**Dependencies:** M1. **Exit:** consumers can rely on stable results and documented
schemas, including failure paths.

| Order | Task | Acceptance criteria |
|---|---|---|
| A1 | Protect stored results from mutation | Define ownership for input arrays, nested arrays, mappings, and returned tables. Ensure mutations of caller inputs or returned objects cannot silently desynchronize fits, tables, and plots. Choose defensive copies/read-only storage with measured memory cost. Add behavioral mutation tests for single and grouped results. |
| A2 | Define export and input contracts | Document supported types, shapes, positional/index alignment, group-label encoding, missingness, and zero-weight policies. Specify schema/version compatibility, numeric nulls, interval level/df, both bin and slope covariance types, original/retained/dropped counts, adjustment coordinates, selection provenance, and heuristic settings. Require strict JSON encoding and test degenerate/clustered/grouped cases. Avoid exporting raw observations by default. |
| A3 | Establish compatibility policy | Inventory public functions, result attributes, layers, defaults, warnings, and exceptions from real signatures. Publish a supported option matrix and migration examples. Record output/default changes in the changelog and assign patch/minor releases by their actual compatibility impact. Preserve `ax` input/output and scoped-theme behavior. |

A2 must define a deterministic, versioned evidence export for consequential use,
including ordered controls/design identity and links or hashes for the analysis
plan, inputs, software lock, and code. Raw data and data-derived fingerprints must
not be collected or published implicitly; callers control their own provenance
and retention. Separate changing timestamps from the deterministic result payload.

### M3 — documentation and figure verification

**Dependencies:** M1–M2 for final contracts. Documentation scaffolding may begin
earlier; pages must not claim unfinished methods.

| Order | Task | Acceptance criteria |
|---|---|---|
| D1 | Ship an executable user guide and API reference | Build MkDocs with strict link checks and generated API reference. Cover unadjusted/adjusted estimands, weights, cluster limitations, bin selection, group support, missingness, gap versus R-squared, and plot composition. Execute quickstart and guide examples in CI. Correct stale version, dependency, and release-trigger claims across README and contribution docs. Publish only after the build passes and hosting is configured. |
| D2 | Validate exported figures | Keep existing artist/axes/rcParams checks. Add a small, justified baseline set (default, paper, audit, standalone deviation) on a pinned rendering environment. Verify PNG plus PDF/SVG export, missing intervals, negative slopes, long labels, multi-panel layout, and caller-supplied axes. Record grayscale, color-vision, and light/dark-background checks before claiming support; label unsupported combinations. |
| D3 | Document reproducible examples | Provide seeded linear, nonlinear, heteroskedastic, clustered, weighted, discrete-x, and grouped-control examples. Explain both informative and misleading pictures. Record seeds and versions; use synthetic data or documented source/license/provenance for bundled data. |

### M4 — performance and dependency support

**Dependencies:** P1–P2 depend on M1–M2 and can run alongside M3. P3 is independent
and may start during M0; supply-chain findings must be triaged when discovered.
**Exit:** documented limits are measured; supported installs work without extras.

| Order | Task | Acceptance criteria |
|---|---|---|
| P1 | Establish and enforce workload limits | Benchmark estimation separately from rendering on 10k, 100k, and 1M rows, varying bin count, cluster count, groups, and control width. Record hardware, versions, wall time, peak memory, and output equivalence. The current dense bin-by-cluster aggregation must be replaced or explicitly bounded before high-cardinality claims; add a benchmark where clusters approach row count. Set numeric regression budgets from an accepted baseline on a controlled runner. Treat 10M rows as exploratory until demonstrated within a declared memory budget. |
| P2 | Verify dependency configurations | Test minimal runtime installation without binsreg, the DPI extra, locked development dependencies, declared lower bounds, and current compatible dependencies in separate jobs. Ensure optional-import failures point at the right distribution. Review Python support explicitly; add a version only when its matrix passes. |
| P3 | Add supply-chain and secret checks | Audit locked runtime/build/dev/docs/optional dependencies for vulnerabilities and license compatibility; record package/version, owner, expiry, and rationale for any reviewed exception. Generate and inspect a CycloneDX SBOM that covers the actual released artifacts and dependencies. Scan tracked history and built artifacts for secrets with controlled/redacted findings. Pin every third-party action, including the current mutable PyPI publisher reference, to a reviewed full SHA. Make dependency updates regenerate the lock and rerun numerical drift checks. Add an honest `make supply-chain` or equivalent gate to CI and release qualification; unavailable audit services are unverified, not passed. |

#### Recurring P3 license-renewal task

Complete a fresh scoped review before the current six decisions expire on
2026-10-13, and immediately when a covered package version/artifact or distribution
scope changes. Expiry-only renewal still requires current evidence; it is not a
date-only registry edit.

1. Classify the proposed scope as separately installed/non-bundled use or broader
   redistribution of dependency artifacts, caches, images or complete environments.
2. Verify the lock hash and exact package/version set. Download the selected
   wheel/sdist files, compare SHA-256 identities with the lock and evidence, and
   inspect regular license/notice members without executing build hooks, extracting
   unsafe links or substituting one artifact's notices for another's.
3. Regenerate the frozen dependency-profile exports and inspect the exact binspect
   candidate wheel/sdist metadata and contents for unexpected bundled dependency
   files. Changed dependency inputs also require `make check` and affected P2
   profiles; every review requires a fresh `make supply-chain` result.
4. Prepare one decision per affected package with exact version/artifacts, permitted
   distribution scope, applicable notice/source obligations, owner, reviewer,
   rationale, evidence, review date and proposed expiry. Broader GPL/MPL or
   file-specific redistribution questions require qualified legal review when the
   maintainer cannot establish the obligations confidently.
5. Keep each registry entry pending or expired until Josh Myers explicitly accepts
   it. Only then update `validation/supply-chain-exceptions.json`, the license
   dossier and dated evidence through a normal PR. An agent cannot extend approval,
   infer acceptance from CI, or treat license renewal as release authorization.

An expired, pending, version-mismatched or scope-mismatched decision blocks the
supply-chain gate and any affected release. The reproducible artifact-inspection
procedure remains in [the license dossier](docs/LICENSE_REVIEW_DOSSIER.md#reproduce-the-evidence).

Avoid promising conversion speedups or zero-copy processing without end-to-end
measurements through conversion, estimation, and rendering.

P1 uses the template performance-experiment record: falsifiable hypothesis,
simpler alternative, warm/cold boundaries, repeated-run distributions and baseline
variance, workload/host/lock identity, correctness guardrails, and a rollback
trigger. Throughput and memory budgets are library-specific; no service latency
SLO or hardware-specialization requirement is implied.

### M5 — release qualification

**Dependencies:** M0–M4. **Exit:** a traceable, install-tested release and a recorded
decision about remaining limitations. Stable 1.0 requires this evidence; completing
this planning revision does not declare the current package production-ready.

| Order | Task | Acceptance criteria |
|---|---|---|
| R1 | Exercise artifact and workflow behavior without publishing | Build wheel/sdist once using frozen, locked build tools; remove the current unpinned build/twine installation path and account for isolated build-backend resolution. Validate metadata, install each in clean environments outside the source checkout, and run estimation/export/plot smoke checks. Verify upload/download artifact handoff and version/tag rejection in a nonpublishing workflow path. Verify configured branch checks and the PyPI environment against the runbook; YAML alone does not prove protection or Trusted Publisher setup. |
| R3 | Establish maintenance and recovery | Document failed publication, yank/fixed-release procedures, dependency drift triage, and maintainer responsibility. Never replace an already published version. Run scheduled upstream comparison checks without making upstream outages a routine PR blocker; preserve logs/artifacts and assign findings for triage. Any numerical correctness divergence affecting a supported method blocks its next release until resolved or that method is withdrawn. |
| R2 | Qualify and verify a release | Require CI on the exact release commit, required pinned statistical references, docs/examples, supply-chain/secret checks, artifact checks, and accepted benchmark evidence. Attach checksums, SBOM, and verifiable build provenance tying the artifacts to the reviewed source and CI run; checksums alone do not authenticate a publisher. Review changelog/version/support matrix together. Complete the adapted release checklist with evidence links, approver/date, and owned residual risks with review/expiry dates. Publish via the existing GitHub `release: published` workflow after its prerequisites are met, then fresh-install the published distribution and verify artifact identity. |

Execute R1, then R3's recovery/readiness work, then R2 publication. R3's recurring
reviews and published-install monitoring continue afterward; rollback procedures
and support ownership must exist before release.

R3's library observability consists of user-controlled warnings/errors, reproducible
bug reports, CI/reference/benchmark trends, and release-install results. Review
these at each release and monthly maintenance triage; name the owner and retained
evidence location. Log at an owning application boundary only if an application
opts in. A runtime telemetry collector, event schema, storage service, or automatic
usage reporting requires a separate user need and privacy design. Any improvement
selected from trends needs baseline and later assessment windows, expected outcome,
guardrails, and an explicit inconclusive/regressed disposition.

## 5. Required evidence for each implementation PR

- A bounded problem, supported behavior, dependencies, and acceptance criteria
  referenced by task ID.
- Regression tests for actual defects; independent algebraic/reference checks for
  statistical claims. State floating-point tolerances and why they are appropriate.
- Existing lint, formatting, typing, import-boundary, test/coverage, and build gates
  as documented in [CONTRIBUTING.md](CONTRIBUTING.md).
- Focused properties: partition reconstruction, tied values, weighted/unweighted
  equivalence, zero-weight omission under `drop`, row permutation of estimates,
  and affine slope changes including sign reversal. Do not require identical plot
  sampling or group order unless those are promised contracts.
- Changes to user docs, exports, and changelog where observable behavior changes.
- A completion entry with PR/commit, checks, remaining limitations, and release
  impact. Keep the task open if an acceptance criterion is missing.
- At each milestone and before release, an evidence-based adversarial review using
  the template rubric; map existing P1 findings to High and P2 findings to Medium,
  escalate any credible critical risk, and record dispositions and owners. Use
  a bounded loop for material work: objective, invariants, new evidence per pass,
  predeclared iteration/time/compute ceilings, pass threshold, diminishing-return
  stop, and domain-escalation trigger. Do not treat repeated self-review as
  independent approval. Findings that affect supported correctness, security, or
  data integrity block qualification until resolved or explicitly withdrawn from
  supported scope.

Pinned integration comparisons belong in a required CI job. Scheduled comparisons
against newer dependencies detect drift. A numerical disagreement is investigated
before relaxing tolerances; a reference is valid only for a matched estimand,
weights, partition, covariance correction, and degrees of freedom.

## 6. Architecture constraints

Keep orchestration in `api.py`/`comparison.py`, input handling in
`input_data.py`/`prepared_data.py`, statistical estimators in `core/`, and
result presentation in the result/table/summary/serialization modules. Keep
Matplotlib rendering in `viz/`; numerical presentation policy already has its
own `viz/layer_policy.py`.

Import-linter enforces dependency boundaries, including no core-to-Matplotlib path
and no visualization-to-entry-point path. It cannot prove that drawing code
contains no statistical calculations. Review and behavioral/architecture tests
must enforce that distinction; presentation calculations are legitimate there.

Do not create the old proposed `variance.py`, dataset tree, or extra result modules
merely to match a diagram. Extract modules when the validated implementation has
a clear responsibility to move. Estimation remains usable without calling plotting;
themes remain opt-in and restore global state even after exceptions.

## 7. Deferred feature queue

These are ordered discovery candidates **after M5**, not release commitments.
Each needs a user problem, explicit estimand, design, independent validation,
maintenance cost, and acceptance criteria before implementation.

| Order | Candidate | Entry condition |
|---|---|---|
| F1 | Uniform confidence bands through an optional binsreg adapter | Specify the fitted function, adjustment, bias correction, simultaneous domain, weights/clusters, and reproducible simulation controls. Validate against upstream. Do not attach bands for a different estimand to the existing descriptive result. |
| F2 | Conditional quantile regression | Specify quantile-loss estimation, controls, weight semantics, and inference. Median/IQR bin summaries may be a separate descriptive feature; do not reuse least-squares FWL or label IQR as estimator uncertainty. |
| F3 | Formula interface | Demonstrated demand, explicit categorical/intercept/missingness behavior, equivalence with the existing API, optional dependency. |
| F4 | `hue=` convenience | Demonstrated usability gap beyond `compare(group=...)`; reuse the settled grouped coordinate and partition contracts. |

The former F5 Polars candidate was promoted into A2 by explicit user direction:
native preparation and tables with pandas compatibility. Workload/performance
qualification remains P1; changing the dataframe engine does not establish a speedup.

ReadTheDocs slug reservation, speculative competitor claims, launch-week setup
tasks, and the obsolete pyproject skeleton are removed from the delivery queue.
Applicable production-template adoption is tracked in M0, P3, and R1–R3. Git history
preserves the original plan. This plan is the source for priorities; the README,
API reference, and executable tests describe released behavior.

## 8. Completion record

| Date | Task | Evidence | Status |
|---|---|---|---|
| 2026-09-12 | Adversarial plan revision | [Review and reproductions](docs/project-plan-review.md); baseline 160 tests / 90.41% coverage | Plan rewritten; C1–R3 remain open |
| 2026-09-12 | Production-template alignment | [Requirement mapping and verification](docs/template-alignment.md), [brief](PROJECT_BRIEF.md), [proposed ADR](docs/decisions/0001-existing-library-baseline.md) | Planning records added; adoption and implementation gates remain open |
| 2026-09-12 | C1 — DPI selection | [Implementation and verification](docs/dpi-selection-review.md); `make check`: 209 unit tests, 6 real-library tests, 91.62% coverage, lint/types/imports/build passed; PR #7 CI passed | Pending maintainer review/integration. |
| 2026-09-12 | G1/G2 — repository agreement and threat model | [Implementation, control audit and verification](docs/repository-baseline-review.md) | Prepared for review; policy/ADR and residual-risk acceptance remain open. Remote control changes are tracked for G1/P3/R1. |
| 2026-09-12 | C2 — grouped coordinates and interval identity | [Contract and regressions](docs/grouped-interval-review.md); `make check`: 228 unit tests, 6 integration tests, 92.02% coverage, lint/types/imports/build passed | Explicit unsupported-combination guard and interval identity implemented; review/integration pending. Shared adjusted coordinates remain unavailable. |
| 2026-09-12 | C3 — initial inference contracts and references | [Analysis plan](docs/STATISTICAL_ANALYSIS_PLAN.md), [verification and locked assessment](docs/inference-contract-review.md); 238 unit tests, 30 integration tests, 92.16% coverage, required coverage/build gates pass | Partial: adjusted-bin coverage is 87.4% at nominal 95% in locked assessment; no nominal population-coverage claim. Expanded scenarios, method decisions and qualified review remain open. |
| 2026-09-12 | C3 — adjusted inference boundary and numerical identification | [Correction and evidence](docs/adjusted-inference-boundary-review.md); 251 unit tests, 46 integration/reference tests, 92.49% coverage, required development coverage/build gates pass | Adjusted-bin uncertainty withheld; numerical control-span guard and rescaled/redundant-control/few-cluster references implemented. Pending review/integration; expanded coverage and qualified C3 acceptance remain open. |
| 2026-09-12 | C3 — expanded development coverage | [Prespecified protocol](docs/EXPANDED_COVERAGE_PLAN.md), [clean-commit report and review](docs/expanded-coverage-review.md); 262 unit tests, 46 integrations/references, 92.49% coverage, both development protocols and builds pass | Required sanity cases pass; uneven-cluster bin coverage is 78.2% (80.7% weighted), preserved as diagnostic failure. Qualified support-policy/protocol review and locked assessment remain open. |
| 2026-09-12 | C3 reference review and C4 diagnostic policy | [Binsreg source/method review](docs/binsreg-reference-review.md), [C4 contract and verification](docs/diagnostic-policy-review.md); 296 unit tests, 50 integrations/references, 92.60% coverage, both development protocols and builds pass | Explicit policies, opt-out, accurate support and signed-SD/display claims implemented. Default clustered/constant outcomes unassessed. Pending review/integration; C3 final assessment/acceptance remain open. |
| 2026-09-12 | C3 — requested binsreg function adapter | [Committed protocol](docs/BINSREG_ADAPTER_PLAN.md), [implementation and clean development evidence](docs/binsreg-adapter-review.md); 334 unit tests, 72 integrations/references, 93.18% coverage, all three development protocols and builds pass | Original-coordinate adjusted function inference and explicit fallbacks implemented. Three uneven clusters give 42.4% coverage against the function target. Draft review/integration and qualified C3 acceptance/final assessment remain open; next independent item A1. |
| 2026-09-12 | A1 — result ownership and mutation isolation | [Ownership contract and measured evidence](docs/result-ownership-review.md); 349 unit tests, 72 integrations/references, 93.75% coverage; all development coverage gates pass; build passed after authorized network retry | Implementation reviewed in [PR #16](https://github.com/joshuamyers22/binspect/pull/16); see [stack review](docs/pr-stack-review.md). Unreleased; milestone acceptance remains separate. |
| 2026-09-12 | A2 — Polars-native inputs/tables and export contracts | [Contract and migration](docs/INPUT_OUTPUT_CONTRACT.md), [implementation evidence](docs/export-input-contract-review.md); final `make check`: 402 unit tests, 74 integrations/references, 94.56% coverage, native installation without pandas, all development coverage gates and builds pass | Implementation reviewed in [PR #17](https://github.com/joshuamyers22/binspect/pull/17), including the large-integer categorical correction in the [stack review](docs/pr-stack-review.md). Unreleased; M2 acceptance remains separate. |
| 2026-09-12 | A3 — compatibility policy | [Policy/migrations](docs/COMPATIBILITY.md), [runtime API inventory](docs/API_INVENTORY.md), [verification](docs/compatibility-policy-review.md); 197 existing contract/plot tests and four migration examples pass | Implementation reviewed in [PR #18](https://github.com/joshuamyers22/binspect/pull/18), with migration formatting corrected. Proposed 0.2.0 allocation and maintainer policy acceptance remain open. |
| 2026-09-12 | D1 — executable guide and API reference | [Guide](docs/site/index.md), [source-generated reference](docs/site/reference/estimation.md), [verification](docs/user-guide-review.md); `make docs` executes 28 Python blocks and the quickstart, then builds strictly | Implementation reviewed in [PR #19](https://github.com/joshuamyers22/binspect/pull/19). Hosting/publication remain open; the development site is not a released API claim. |
| 2026-09-12 | D2 — figure exports and baselines | [Visual limits/simulations](docs/site/guide/figure-exports.md), [four-image manifest](tests/baseline/manifest.json), [verification](docs/figure-export-review.md); 19 new export/guard checks and exact local baseline rerenders | Implementation reviewed in [PR #20](https://github.com/joshuamyers22/binspect/pull/20), with renderer setup corrected; see [stack review](docs/pr-stack-review.md). Broader accessibility/vector-viewer and maintainer visual qualification remain open. |
| 2026-09-12 | D3 — reproducible examples | [Executable gallery](docs/site/guide/gallery.md), [manifest](docs/site/assets/gallery/manifest.json), [verification](docs/example-gallery-review.md); seven fixed synthetic seeds, Polars tables, numerical assertions and retained figures | Implementation reviewed in [PR #21](https://github.com/joshuamyers22/binspect/pull/21). Teaching cases are not inference qualification. |
| 2026-09-12 | P1 — occupied-cluster aggregation and workload limits | [Measurement scope](docs/site/guide/performance.md), [experiment and retained evidence](docs/performance-review.md), [harness](validation/performance.py), [budget enforcement](validation/performance_check.py) | Implementation reviewed in [PR #22](https://github.com/joshuamyers22/binspect/pull/22). Baseline/controlled-runner acceptance remains open; 10M and general capacity are unqualified. |
| 2026-09-12 | P2 — dependency configurations | [Configuration guide](docs/site/guide/dependencies.md), [isolated installed-code checks](validation/dependencies.py), [actual evidence](docs/dependency-review.md) | Implementation reviewed in [PR #23](https://github.com/joshuamyers22/binspect/pull/23); see [stack review](docs/pr-stack-review.md). Python 3.10–3.13 retained; release qualification remains separate. Next implementation P3. |
| 2026-09-12 | P3 — supply-chain and secret checks | [Scope/pending decisions](docs/SUPPLY_CHAIN.md), [blocking gate](validation/supply_chain.py), [verification](docs/supply-chain-review.md) | Implemented on `security/supply-chain-checks`, stacked on P2. All locked versions are audited; build/audit tools and action refs are pinned; history/working/artifact secret scans and validated artifact-linked CycloneDX evidence are added. Six pending license reviews block the gate and P3 acceptance. Maintainer review/integration and remote controls remain open. R1 nonpublishing qualification is the next implementation item. |
| 2026-09-12 | R1 — artifact/workflow qualification | [Implementation and retained evidence](docs/artifact-workflow-review.md); [draft PR #25](https://github.com/joshuamyers22/binspect/pull/25); local full gate passes, 12 local and 24 CI clean artifact installs pass | Implemented on `test/artifact-workflow-qualification`, stacked on P3. Shared nonpublishing build/download/install path verified; Polars defaults and optional pandas conversion retained. Overall CI fails for six pending license reviews and unavailable pinned figure Python. Actual main/PyPI controls and Trusted Publisher mapping still need acceptance; no publication. Next implementation R3. |
| 2026-09-12 | R3 — maintenance and recovery | [Procedure](docs/MAINTENANCE.md), [retained evidence](docs/maintenance-recovery-review.md); [draft PR #26](https://github.com/joshuamyers22/binspect/pull/26) | Implemented on `chore/maintenance-recovery`, stacked on R1. 222 locked/current reference cases, three installed journeys, ten simulated recovery scenarios and the full local 600-test gate pass. Fresh-current monitoring moves to weekly/manual runs; locked/floor PR gates remain. Maintainer acceptance, default-branch schedule activation and actual PyPI operator recovery evidence remain open. P3/R1 gaps still block R2 publication. |
| 2026-09-12 | R2 — readiness preparation and figure provisioning repair | [Concrete readiness record](docs/releases/0.2.0-readiness.md), [verification](docs/release-readiness-review.md); [draft PR #27](https://github.com/joshuamyers22/binspect/pull/27) | Local 600-test full gate passes; uv-managed Python 3.12.14 restores the macOS CI figure job with unchanged baselines and RMS 0.0. All CI jobs pass except six pending license reviews. Read-only checks confirm main now includes #15–#23; #24–#26 remain drafts. R2 publication remains blocked by owned acceptance, controls, integration and exact-candidate artifact/provenance gates. No candidate/version/tag/release selected or published. |
| 2026-09-13 | P3 license scope acceptance and distribution-integrity follow-up | [Accepted scope](docs/SUPPLY_CHAIN.md), [artifact dossier](docs/LICENSE_REVIEW_DOSSIER.md), [integration review](docs/release-stack-integration-review.md) | Josh Myers accepted six exact separately installed/non-bundled dependency scopes through 2026-10-13. The strengthened checker rejects sdist manifest/byte and project-metadata divergence. The 639-test full gate and fresh online supply-chain gate pass locally; exact pushed-head CI and main integration remain next. No release is authorized. |
| 2026-09-13 | Release-hardening stack integration | [Merged PR #30](https://github.com/joshuamyers22/binspect/pull/30), [integration review](docs/release-stack-integration-review.md), [exact-head CI](https://github.com/joshuamyers22/binspect/actions/runs/34783516923) | All 35 jobs pass on exact head `30d0793`, including supply-chain and 12 artifact installations. PR #30 merged #24–#29 into main as `6d1169b`. Candidate selection, owner-held acceptance, actual controls, maintenance activation/recovery and release-specific provenance remain open; no release was published. |
| 2026-09-13 | R2 — v0.2.2 publication and reconciliation | [Release outcome](docs/releases/0.2.2-readiness.md), [GitHub release](https://github.com/joshuamyers22/binspect/releases/tag/v0.2.2), [release run](https://github.com/joshuamyers22/binspect/actions/runs/34789980329), [post-release PR #36](https://github.com/joshuamyers22/binspect/pull/36) | Authorized v0.2.2 published successfully. Its non-yanked PyPI wheel/sdist match the qualified pair byte-for-byte, both public provenance records identify the Trusted Publisher, and a fresh Python 3.12 installation passed. Post-release evidence and exact final-main CI are complete. |
| Due 2026-10-13 | P3 — renew six scoped license decisions | [Current scope and expiry](docs/LICENSE_REVIEW_DOSSIER.md), [blocking policy](docs/SUPPLY_CHAIN.md#six-approved-scoped-license-decisions) | Open recurring task. Refresh exact artifacts, profile/distribution scope, license/notice evidence and live supply-chain results; obtain explicit per-package maintainer acceptance before changing registry review/expiry fields. Run immediately for any earlier version, artifact or redistribution-scope change. |
