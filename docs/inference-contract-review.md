# C3: inference contract and initial reference validation

- Date: 2026-09-12; baseline `2b09086`, stacked after PR #9.
- Implementer: Codex; accountable reviewer: Josh Myers; qualified statistical
  reviewer not yet assigned.
- Status: initial implementation and locked assessment recorded; C3 acceptance
  remains open because broader coverage/design work and qualified review remain.

## Bounded verification contract

Objective: specify current inference, add independent locked references and initial
predeclared coverage evidence, and expose limits/df without changing numerical
estimators. Preserve current API estimates, MIT, dependency scope and prior tests.
The [analysis plan](STATISTICAL_ANALYSIS_PLAN.md) defines methods, assumptions,
reference matching, seeds, tolerances and remaining cases before this run.

Block on coefficient/SE reference mismatches, failed required coverage, incorrect
metadata, dropped failures or unreported limitations. Maximum three evidence-changing
review passes and 90 minutes; ordinary local/CI compute, no publication or remote
settings. Stop when the bounded rubric passes or report unresolved failures at
the ceiling. Qualified review and broader coverage scenarios remain separate
acceptance requirements; passing software tests cannot self-approve them.

## Evidence

| Pass | Evidence | Result / disposition |
|---|---|---|
| 1: contract and references | Inspected current and locked upstream covariance code; specified the analysis plan before runs. | 24 matched Statsmodels/NumPy reference cases pass across all weight/control/cluster combinations and both slope zero-weight policies. No coefficient/SE calculation was changed. |
| 2: development simulation | Prespecified 1,000 replicates per case, seeds 41000–41004, same fixed tolerances. | IID 95.5%, weighted 95.1%, clustered 95.9%; all required cases pass. Adjusted diagnostic 89.2% fails the nominal band; quantile diagnostic 94.2%. No invalid replicates. Adjusted-bin nominal population coverage is explicitly unvalidated in metadata/docs; C3 stays open. |
| 3: full gate | Runtime metadata tests, existing suites, independent references, coverage protocol, lint/types/imports/build and documentation checks. | `make check`: 238 unit tests, 6 DPI integrations, 24 reference integrations, 92.16% unit coverage, all 3 import contracts, strict mypy (28 source files), Ruff and wheel/sdist passed. |

The implementation adds metadata for the existing covariance and actual degrees of
freedom, without replacing classical or CR1 calculations. HC1 is explicitly deferred.
The upstream mizani deprecation warning remains visible. Network access was needed
to resolve/install the new explicit validation extra; supported local runtime
versions were retained. Universal-lock resolution also removes the old Emscripten
Statsmodels alternative and adds a plotnine alternative; Emscripten is outside the
declared tested platform matrix. This is recorded rather than hidden as a runtime
engine migration.

The [reference suite](../tests/integration/test_inference.py) checks well-conditioned
full-rank designs. The [coverage protocol](../validation/coverage.py) compares one
prespecified interval per independent replicate; results are not pooled across
correlated bins. Development clarified in the plan that the adjusted diagnostic
uses sample-quantile bins; code/seeds/thresholds did not change after observing it.
All reported coverage uses 1,000 as its denominator; no failure was dropped.

The adjusted diagnostic targets the population mean 2 under y=2+1.5*z+noise,
with independent x and z. Mean-restoring residualization includes variation in
the estimated adjustment/restored mean that the bin-only SE omits. The 89.2%
result is evidence against a general nominal population-coverage claim, not proof
of one universal correction. The public result continues to offer an explicitly
limited approximate interval; it must not be used as validated population inference.

## Locked assessment

The plan, protocol and implementation were committed as `c19c2a8` before running
seeds 51000–51004 from a clean tree. The
[assessment JSON](evidence/inference-coverage-2026-09-12.json) records that revision,
source/plan/lock hashes, generated-input hash, versions and RNG identity.

| Scenario | Coverage / 1,000 replicates | Monte Carlo SE | Disposition |
|---|---|---|---|
| IID | 94.6% | 0.71 percentage points | Required sanity case passed |
| Reliability weights | 95.6% | 0.65 percentage points | Required sanity case passed |
| Clustered | 94.9% | 0.70 percentage points | Required sanity case passed |
| Adjusted diagnostic | 87.4% | 1.05 percentage points | Outside nominal band; confirms undercoverage concern |
| Quantile diagnostic | 95.2% | 0.68 percentage points | Within band for flat target only |

No invalid replicate occurred. Required-case acceptance band was fixed at
[92.243%, 97.757%] before either run. Neither scenarios nor tolerances were changed
after observing results. The report's `required_pass` covers only its three
prespecified sanity cases; the failing adjusted diagnostic remains visible and
does not pass C3. Assessment seeds are now consumed and cannot serve as an unseen
assessment set for future method tuning. Use a reviewed new set after changes.

Reproduction command: `uv run --frozen --extra dev --extra validation python
validation/coverage.py --phase assessment --output docs/evidence/inference-coverage-2026-09-12.json`
from clean `c19c2a8`. Do not overwrite this historical report with a changed method.
Independent statistical approval has not been supplied by this run.

## Remaining C3 work

Nominal adjusted-bin inference requires a reviewed estimand and uncertainty design,
or continued withdrawal of that claim. Add reviewed nonflat/data-selected/DPI,
rank-deficient/ill-conditioned and few/unbalanced-cluster scenarios before broader
qualification. Assign a qualified statistical reviewer and resolve baseline policy
decisions before C3 sign-off. The new CI gate protects the initial references and
sanity cases; it does not convert the failing diagnostic into a passing method.
