# Optional binsreg function inference: implementation and evidence

Date: 2026-09-12. Baseline `877c854`; implementer Codex; accountable maintainer
Josh Myers. The user requested this integration ahead of A1. It is implemented
for review, with no release or qualified statistical acceptance implied.

## Method contract

The [method and verification plan](BINSREG_ADAPTER_PLAN.md) was committed as
`86ff35e` before development simulations. The [upstream review](binsreg-reference-review.md)
identifies binsreg 3.2.1 and its source hashes. The
[authors' software paper](https://nppackages.github.io/references/Cattaneo-Crump-Farrell-Feng_2025_Stata.pdf)
provides the function-inference context; it does not establish a general
few-cluster guarantee or endorse this implementation.

`binspect.binsreg()` delegates the original-coordinate semilinear function fit to
that optional backend. Encoded numeric/categorical controls enter the joint design.
The evaluation values are positive-weight sample means, zero or a supplied vector;
`asyvar=False` includes full coefficient covariance but treats evaluation values
as fixed. The adapter requests degree-0 dots, degree-1/continuity-1 pointwise
intervals, normal critical values, HC1 or upstream cluster covariance, DPI or
explicit bin counts, full-sample selection and upstream mass-point/df safeguards.

Input filtering uses one complete-case mask, always drops zero weights and reports
both counts. A normalized full-rank x/control design and at least two active
clusters are required. These guards identify estimability, not coverage validity.
`BinsregResult` retains aggregate tables and metadata with copied public accessors;
its plot places intervals around their own fitted centers. It has no FWL slope,
gap or diagnostic verdict. Existing adjusted FWL uncertainty remains withheld.

Sanitized `BinsregWarning` messages and issue codes expose support and method
changes. Constant-fit fallback is `limited_support`, including corrected actual
degree metadata when upstream options still retain the requested degree. It may
also change spacing; actual placement is left uncertified in that path. DPI-to-ROT
fallback is explicit. Unknown warnings, unexpected changes and unvalidated backend
versions yield `unverified_method`. Missing or malformed output fails explicitly;
unavailable intervals have a separate status. Raw input rows, cluster labels and
upstream messages are not retained in exported results or this evidence.

## Development coverage

The [retained aggregate report](evidence/binsreg-adapter-development-2026-09-12.json)
comes from clean implementation commit `081066b`. It records protocol, script,
implementation, lock and generated-input hashes, versions and RNG identity.
PCG64 seeds 94000–94002 supply 1,000 replicates per case, 600 rows per replicate.
At the returned interval x nearest zero, the target is the prespecified
`3 + x + 2*x²`, with control evaluated at 1.

| Case | Coverage at nominal 95% | Monte Carlo SE | Mean width | Actual CI method |
|---|---:|---:|---:|---|
| Adjusted iid, DPI | 93.6% | 0.77 percentage points | 0.593 | Degree 1, all 1,000 runs |
| Adjusted 60 clusters of 10, requested 5 bins | 94.3% | 0.73 percentage points | 0.623 | Degree 1, all 1,000 runs |
| Adjusted 3 clusters sized 480/60/60, requested 5 bins | 42.4% | 1.56 percentage points | 1.059 | Degree 0, 3 bins, all 1,000 runs |

All 3,000 runs completed. The iid case is inside the prespecified 92.24–97.76%
development band. Clustered cases were declared diagnostic before simulation;
the uneven-cluster failure is retained and is not converted into a passing
coverage claim. All fixed-count runs report the upstream approximation-bias
warning; all three-cluster runs additionally report small-sample and constant-fit
fallback issues. This is evidence that adopting binsreg does not repair the
few-cluster problem. Its 42.4% function-target coverage is not directly comparable
to the earlier 78.2% population-bin-average result: the estimands and designs differ.

The development band is a regression check for this stated design, not broad
method qualification. Assessment seeds 95000–95002 remain reserved and unrun;
the earlier assessment reservations and consumed-seed restrictions are unchanged.

## Verification and disposition

The bounded verification proceeded through API contracts, matched references,
then coverage and the full gate. The first full-suite attempt caught a test-module
basename collision; renaming the boundary test resolved collection. Source review
also identified fallback spacing as uncertified; equal-width fallback comparisons
now guard that metadata. Rendering follows the repository's visualization boundary.

`make check` passes at the clean implementation revision: 334 unit tests, 32 real
binsreg integration tests (22 adapter cases), 40 Statsmodels references, Ruff
(96 files), 93.18% unit coverage, strict mypy (33 files), all three import contracts, all three
development protocols and wheel/sdist builds. Expected adjusted-inference warnings
and the existing upstream timedelta deprecation remain visible. Numerical
tolerances, dependencies and old inference protocols were not changed.
All 91 relative links in the affected guidance resolve. The README adapter example,
plot and strict JSON export execute. Retained-report hashes match the final source;
old plans/scripts/reports are byte-for-byte unchanged, and all expanded development
outcomes match the prior aggregate evidence exactly.

The adapter slice is ready for maintainer review and integration as a draft stacked
after PR #13. C3's support/claim decisions, qualified review and final assessment
remain open. A1 result ownership/mutation isolation is the next independent plan
item; the copied accessors on this new result do not resolve the older result types.
