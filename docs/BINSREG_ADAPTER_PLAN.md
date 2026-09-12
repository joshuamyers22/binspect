# Binsreg inference adapter: method and verification plan

Date: 2026-09-12. Baseline `877c854`; owner Josh Myers; implementer Codex.
The user explicitly requested binsreg's adjusted and few-cluster methods, moving
this integration ahead of A1. This is an opt-in method addition, not release or
statistical acceptance. [Reference review](binsreg-reference-review.md).

## Estimand and supported API

Add `binspect.binsreg(...)` returning a separate `BinsregResult`. Fit the upstream
semilinear function in original x coordinates, jointly with encoded controls;
evaluate controls at their positive-weight sample means by default, or explicit
encoded values/zero. Do not attach function intervals to FWL residual-space bins.
Keep the existing binscatter/compare estimators and their inference boundary intact.

Use the optional existing binsreg extra and actual upstream `binsreg`, with
degree-0 dots and `ci=True` (normal path degree 1/continuity 1), `asyvar=False`,
HC1 when independent or upstream cluster covariance, user confidence level,
quantile/equal-width spacing, DPI count by default or explicit integer count.
Keep upstream `dfcheck=(20,30)` and mass-point safeguards. No arbitrary keyword
forwarding, tuning bypasses, bootstrap, simultaneous bands or grouped-method API
is included in this initial adapter. No few-cluster coverage guarantee is invented.

Input contract: arrays/dataframe columns, numeric/categorical controls, optional
positive reliability weights and cluster labels. Apply complete-case filtering
consistently; drop zero weights before partition/estimation and report input,
missing and zero-weight row counts. No index joins. Original x/y are never
residualized. Require at least four rows, nonconstant x, two clusters if supplied,
and an identified full-rank control/x design. Supply copied arrays to upstream.
Export encoded control names and evaluation values so the target is reviewable.

## Output and fallback behavior

Expose separate copied dot and interval tables, metadata, strict JSON, summary,
and an optional Matplotlib plot. Intervals are drawn around their own fitted
centers; they need not be centered on degree-0 dots. Do not invent a linear slope,
gap or diagnostic verdict for this different result type. Store no raw rows.

Upstream warnings remain visible and are captured as controlled issue codes, with
requested/actual counts and degree settings. Its small-effective-sample fallback
can retain constant-fit intervals; report `limited_support`, the fallback and
actual degree 0 instead of trusting options metadata that may retain degree 1.
Expose those intervals as upstream returned them, labelled approximate with no
few-cluster guarantee. Other method changes (including DPI-to-ROT) are explicit.
If a warning cannot be classified, report unverified method status and do not
claim the requested method was preserved. Sanitize upstream errors, suppress
unstructured upstream stdout/stderr, and do not export raw warning/error text.
The adapter is optional and must not initialize binsreg or plotting at import.

## Verification before qualification

Commit this plan before simulations. Blocking findings: mixed estimands, silent
fallback, unvalidated upstream result schema, suppressed support issues, caller
mutation, incorrect counts/df/controls, raw-input leakage or failing required tests.
Use at most three evidence-changing passes / 90 minutes: adapter and API tests,
matched real-library references, then coverage/evidence and full gate. Stop at a
reviewable draft; unsupported upstream failures stay explicit. No new release claim.

Matched references use synthetic seed 93000, crossed controls/weights/clusters and
both spacing modes where supported. Compare dots and CI limits to direct locked
binsreg at rtol=1e-9, atol=1e-11 after identical filtering/coding/evaluation.
Include missingness/zero weights, categorical controls, 2/3-cluster fallback,
invalid output, missing dependency, strict JSON, copied results and plot centers.

Prespecified development coverage: PCG64 seeds 94000–94002, 1,000 replicates of
600 rows each, nominal 95%, x Uniform(-1,1). Generate x, z Normal(1,1), observation
error Normal(0,1), then independent Normal(0,1) cluster shocks when present.
Always y=2+x+2*x²+z+error (+ cluster shock). Fit numeric control z with `at=[1]`.
Scenarios: iid with actual DPI; 60 clusters of 10 with explicit 5 bins; uneven
clusters 480/60/60 with explicit 5 bins. Evaluate the returned CI whose x is nearest
zero (first in a tie); its true target is 3+x+2*x² at that evaluation point.
For fallback constant intervals still report coverage against this function target,
explicitly a diagnostic of the fallback, not a redefined population-bin average.

Report hits/1000, invalid replicates as misses, Monte Carlo SE, mean interval width,
status/issue/count histograms, plan/script/lock/input hashes, version/RNG/revision.
Nominal band .95 ± 4*sqrt(.95*.05/1000) is prespecified. Require zero invalid runs
and the iid higher-degree case inside the band. Clustered cases are diagnostic;
preserve every deviation. Reserve assessment seeds 95000–95002, do not run them
in this implementation turn. Run prior coverage protocols unchanged. `make check`
must include adapter references and new development coverage before pushing.
