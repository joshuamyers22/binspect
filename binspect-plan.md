# binspect — production project plan

Updated 2026-09-12 against `main` at `59c6a39`, package version `0.1.1`.

**Next task: C1 — correct and validate `bins="dpi"`.** Complete the correctness
milestone before adding estimators. This document replaces the original unordered
v0.5+ wishlist and supersedes its blanket claim that v0.1–v0.4 was complete.

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

Retain NumPy, pandas, SciPy, and Matplotlib as the current required dependencies,
subject to the baseline ADR's review and reference-validation conditions. Use
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

Verdicts are descriptive heuristics, currently gap threshold 0.02 and minimum
raw bin count 30. They are not power calculations, significance tests, or a
validation of linearity. C4 must address effective sample size and cluster support.

Per-bin IQR describes outcome dispersion. It is neither a confidence interval for
the median nor a fitted conditional quantile regression. Uniform confidence bands
require simultaneous inference; connecting pointwise interval endpoints is
insufficient.

## 4. Ordered implementation milestones

All tasks below are **open**. Work in listed order within each milestone unless a
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

Avoid promising a Polars fast path or zero-copy processing without end-to-end
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
| F5 | Polars input optimization | Benchmarks establish conversion as a material bottleneck; define copies and supported dtypes before adding an optional path. |

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
