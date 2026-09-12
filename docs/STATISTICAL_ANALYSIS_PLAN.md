# Statistical analysis plan: current mean/slope inference

Date: 2026-09-12. Baseline: `2b09086`. Owner: Josh Myers; implementer: Codex.
Status: specified before this validation run; pending qualified maintainer-assigned
review. This describes current calculations and their limits, not accepted
production inference. No runtime estimator change is proposed here.

## Decision, sample and estimands

Decide whether current OLS/WLS slope and bin-mean uncertainty implementations match
their stated arithmetic and where their interpretation must be limited. There is
no causal hypothesis, predictive deployment, significance-based feature search,
financial action or practical effect threshold. The verdict remains descriptive.

Observations are caller rows; clusters are caller-specified sampling units. Inputs
may use arbitrary caller units. Controls are encoded with an intercept and numeric
columns/categorical indicators; x and y are projected separately and shifted to
their sample weighted means. Grouped adjustment uses separate fits and partitions.
Use `[intercept, numeric controls, categorical indicators, x]` in references, with
explicit reference coding and positive-weight rows only. A fitted adjusted slope
targets x's full-design coefficient; its displayed intercept is a shifted-coordinate
intercept and is not the full model intercept. A bin mean targets a weighted mean
in the observed partition, not the regression function at the displayed x mean.

Current preprocessing drops nonfinite x/y/weights and missing controls/clusters when
`dropna=True`, raises otherwise, and always excludes missing group labels. There is
no imputation, outlier trimming or censoring model. Missingness/selection may bias
population conclusions. Zero weights may remain in partition selection and counts,
but are omitted from slope degrees of freedom and cluster counts; `drop` removes
them entirely. Reliability weights are scale-invariant, not replicated frequencies
or a survey-design specification. Caller-owned real datasets are not retained.

## Calculation contract

Let n+ be positive-weight rows, r the full weighted design rank, G the number of
positive-weight clusters, S1=sum(w), S2=sum(w²), and neff=S1²/S2. A bin-local suffix
j restricts these quantities to that bin. Unweighted w=1. `classical` means residual
scale times inverse weighted cross-product with df=n+−r. Its weighted interpretation
requires a correctly specified mean and error variance proportional to 1/w;
arbitrary reliability weights do not by themselves justify that model.

| Controls | Weights | Clusters | Slope coefficient / covariance | Bin mean covariance / t-reference df |
|---|---|---|---|---|
| No | No | No | OLS; classical, n−2 residual df | sample variance/nj; nj−1 |
| No | Yes | No | WLS; classical, n+−2 residual df | reliability variance/neffj; max(neffj−1,1) |
| Yes | No | No | Full-design x coefficient by FWL; classical, n−r | as unweighted above on adjusted y; first-stage uncertainty omitted |
| Yes | Yes | No | Full-design x coefficient by weighted FWL; classical, n+−r | reliability formula on adjusted y; first-stage uncertainty omitted |
| No | No | Yes | OLS; CR1 with G/(G−1) × (n−1)/(n−2) | bin-local CR1; Gj−1 |
| No | Yes | Yes | WLS; CR1 with G/(G−1) × (n+−1)/(n+−2) | weighted bin-local CR1; Gj−1 |
| Yes | No | Yes | Full-design x coefficient; CR1 with G/(G−1) × (n−1)/(n−r) | bin-local CR1 on adjusted y; first-stage uncertainty omitted |
| Yes | Yes | Yes | Full-design x coefficient; CR1 with G/(G−1) × (n+−1)/(n+−r) | weighted bin-local CR1 on adjusted y; first-stage uncertainty omitted |

Reliability variance is sum(w*(y−mean)²)/(S1−S2/S1). It differs from classical
inverse-variance WLS covariance. For equal weights it reduces to ordinary sample
variance. Bin-local CR1 variance is Gj/(Gj−1) × sum(cluster score²)/S1j², where a
score sums w*(y−mean) within that cluster and bin. Match an intercept-only regression
*inside each bin*, not a global saturated regression with different finite-sample
corrections. Gj<2 yields undefined clustered uncertainty; singleton/effective
singleton independent bins are undefined. Slope t-reference df is G−1 for CR1 and
n+−r for classical covariance; the public API currently exposes SEs, not slope CIs.

HC1 is deferred and is not selectable or used for binspect's returned uncertainty.
The optional DPI selector's internal HC1 option does not change this. Classical
slope covariance is not heteroskedasticity robust. Clusters must be independent
across labels; arbitrary within-cluster dependence is allowed by the sandwich
approximation, but few/unbalanced clusters can have poor coverage.

All bin intervals are labelled approximate pointwise conditional intervals. They
omit uncertainty from fitted controls and selected boundaries/counts (especially
outcome-dependent DPI), and are neither simultaneous bands nor confidence intervals
for a causal effect. Quantile/equal-width boundaries also depend on observed x.
No multiplicity/model-selection correction is supplied. Conditional labels do not
assert that conditioning makes first-stage uncertainty disappear.

Primary reference documentation: [Statsmodels WLS](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.WLS.html)
and [cluster covariance](https://www.statsmodels.org/stable/generated/statsmodels.stats.sandwich_covariance.cov_cluster.html).
The locked 0.15.0 implementation was inspected: cluster scores use whitened design
and residuals. Validation explicitly removes zero-weight rows before reference
fitting. Statsmodels stays a validation dependency, not a runtime requirement.

## Reference and numerical checks

Mandatory frozen integration checks use Statsmodels 0.15.0, seed 31001/PCG64,
600 synthetic rows and 60 clusters. Cross all eight weight/control/cluster cases
and both zero-weight policies. Controls include numeric and categorical columns;
include missingness and zero-weight-only clusters. Compare coefficients/SEs with
rtol=1e−9 and atol=1e−11 on well-conditioned full-rank designs. Compare bin CR1
to local intercept-only WLS/OLS and unweighted independent SEs to local OLS.
Validate weighted independent dispersion separately rather than demand false
WLS equivalence. Rank-deficient/ill-conditioned designs need explicit treatment:
do not change tolerances or claim them validated from the full-rank cases.

## Coverage protocol and evidence boundary

Development seeds start at 41000; locked assessment seeds start at 51000, using
NumPy PCG64. Each scenario uses 600 rows, 5 bins, 1,000 repetitions and nominal 95%
pointwise intervals. Only one prespecified bin (ID 2) contributes a Bernoulli result
per replicate; bins within a dataset are not independent Monte Carlo replications.
Report hits, valid/failed counts, rate and Monte Carlo SE. Failures are not dropped
from a denominator to improve coverage. Development never changes final seeds.

Required sanity cases: fixed equal-width partition, flat conditional mean 2,
normal iid errors; the same with random positive reliability weights independent
of errors; the same with 60 independent cluster shocks plus observation noise.
Nominal acceptance band is 0.95 ± 4*sqrt(0.95*0.05/1000), approximately [0.9224,
0.9776], separately for these three cases; any invalid replicate blocks the gate.
This is a falsification threshold for these scenarios, not a universal coverage
guarantee. Four-SE bounds limit incidental multiple-case false alarms.

Diagnostic cases: fitted-control adjustment with sample-quantile bins and the same
flat adjusted target,
and sample-quantile selection under the flat target. Use the same count/seeds/band
for reporting; do not treat a passing diagnostic as validation of every adjusted
or selected-partition estimand. Outcome-dependent DPI, nonflat regression functions,
near-singular designs and very few/unbalanced clusters require additional reviewed
scenarios before broader claims. These limitations remain open C3 work even if
the initial protocol passes. Do not silently promote exploratory outcomes to
release qualification.

Run development first. Commit the plan/protocol before executing locked assessment.
Record git revision, dirty state, plan/protocol/lock and generated-input hashes,
Python/NumPy/SciPy/Statsmodels versions, RNG identity and command in the JSON report.
Runtime estimates do not collect this evidence automatically. Check protocol output
in CI using development seeds; reserve the locked report for review and retain it
as a versioned evidence artifact. No repeated final-seed tuning after a failure:
record failure and revise the plan with a fresh assessment set.

## Applicability, review and follow-up

The pandas/NumPy boundary is retained under proposed ADR-0001; no Polars pipeline
is needed for generated validation arrays. Forecasting folds, timestamps, embargo,
transaction costs, live parity, Bayesian priors/posteriors and sampler diagnostics
are inapplicable: this is frequentist library validation without prediction or
trading. Synthetic inputs have no external data-owner/license obligations; code
and evidence retain the repository MIT terms.

Josh Myers assigns a qualified statistical reviewer before C3 acceptance. This
agent may prepare/run reproducible evidence but cannot supply independent approval.
Mismatch or failed required coverage blocks the affected claim; fix or withdraw
it with preserved failure evidence. Recheck on covariance, preparation, dependency
or partition changes, and at release. Further method claims require amended plan,
new controlled cases and independent review; there is no causal certification.
