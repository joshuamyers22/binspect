# C3 expanded coverage protocol

Date: 2026-09-12. Baseline: `ef4ff92`, following PR #11.
Owner: Josh Myers; implementer: Codex; qualified reviewer unassigned.
Status: prespecified development evidence, pending qualified review. This protocol
extends the [original plan](STATISTICAL_ANALYSIS_PLAN.md) and respects the
[adjusted-bin withdrawal](adjusted-inference-boundary-review.md). Those historical
documents and the locked v1 report remain unchanged. No runtime estimator changes.

## Objective and bounded verification

Measure the returned unadjusted intervals under nonflat means, data-selected bins,
and few/unbalanced clusters. Preserve failed outcomes and separate arithmetic
agreement from population coverage. A passing scenario does not establish a
general guarantee. No causal, forecasting, financial, Bayesian or simultaneous
inference claim is evaluated; no caller data or telemetry is collected.

Commit this specification before running simulations. Up to three evidence-changing
review passes and 90 minutes: specify and verify the harness, execute development,
then record and review the evidence. Wrong targets, omitted failures, changed
seeds/tolerances after observing coverage, or failing required checks block the
slice. Keep diagnosed limitations explicit; do not fit a replacement method here.
Use deterministic oracle/failure-accounting tests, frozen dependencies and the
full `make check` gate. Stop after those checks and a reviewable draft PR; C3
acceptance requires a named qualified reviewer and reviewed final assessment.

## Sampling and estimands

Each replicate has 600 rows, x independently Uniform(-1,1), independent standard
normal observation errors, no controls or missingness, and nominal 95% intervals.
Cluster labels represent independent units; a standard normal shock is shared by
all rows in each cluster. All shocks, x and observation errors are independent.
The weighted case draws independent Uniform(0.5,2) reliability weights; there are
no zero weights. Raw synthetic inputs are hashed but not persisted.

Nonflat cases use y = 2 + x + 2*x² + error. Cluster cases use
y = 2 + 1.5*x + cluster shock + error, so slope target beta = 1.5. Generate x,
observation error, cluster shocks (if any), then weights (if any), in that order.
Do not evaluate classical linear slope uncertainty under the quadratic mean.

Choose exactly one bin per replicate: the original partition interval containing
x=0, using left-closed/right-open membership (a knot at zero selects its right
interval). Resolve its original interval ID to the compact estimate index.
An absent interval or undefined uncertainty is a failed replicate, not a redraw.
For Uniform(-1,1), the independent population average over interval [a,b] is
2 + (a+b)/2 + 2*(a²+a*b+b²)/3 for the quadratic mean, and
2 + 1.5*(a+b)/2 for the linear mean. This is an analytic integral, not the
regression function at the displayed x mean or the average fitted sample values.
Weights independent of x/errors leave this population target unchanged.

Fixed partitions use linspace(-1,1,6). Quantile selection uses five bins. DPI calls
the actual locked binspect adapter on every replicate with quantile spacing;
no ROT fallback, cached partition, count clipping or weights/clusters/controls.
For selected bins the target is the population average over the realized random
interval, evaluated across repeated full samples. This design measures the effect
of selection on that random target; it does not condition selection bias away.

For clustered slopes form a validation-only interval beta_hat ± t(.975,G−1)*SE
from the public slope SE and public reference df. No slope-CI API is introduced.
Bin intervals use their returned local CR1 df. The covariance and df conventions
remain those in the original plan, matched previously to
[Statsmodels CR1](https://www.statsmodels.org/stable/generated/statsmodels.stats.sandwich_covariance.cov_cluster.html);
critical values use [SciPy's t quantile](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.t.html).

## Prespecified grid, seeds and interpretation

Use NumPy PCG64, 1,000 independent replicates per row. Development seeds are
71000 + the table offset. Reserve 81000–81007 for a future reviewed assessment;
this harness exposes only development and must not run those assessment seeds.
Do not reuse original 51000-series or rescaling-reference seeds.

| Offset | Scenario | Partition / dependence | Nominal coverage gate |
|---|---|---|---|
| 0 | fixed_nonflat | Fixed, quadratic mean, iid | Bin interval required sanity case |
| 1 | quantile_nonflat | Five quantile bins, quadratic mean, iid | Diagnostic |
| 2 | dpi_nonflat | Actual DPI count/quantile edges, quadratic mean, iid | Diagnostic |
| 3 | cluster_60 | Fixed, linear mean, 60 clusters of 10 | Bin and slope intervals required sanity cases |
| 4 | cluster_5 | Fixed, linear mean, 5 clusters of 120 | Diagnostic bin and slope |
| 5 | cluster_2 | Fixed, linear mean, 2 clusters of 300 | Diagnostic bin and slope |
| 6 | cluster_3_unbalanced | Fixed, linear mean, sizes 480/60/60 | Diagnostic bin and slope |
| 7 | weighted_cluster_3 | Same sizes, independent reliability weights | Diagnostic bin and slope |

The nominal band is unchanged: .95 ± 4*sqrt(.95*.05/1000), approximately
[.9224,.9776]. Apply it separately to each metric, without pooling dependent bins
or bin/slope hits. It is a scenario falsification threshold, not formal familywise
acceptance or a universal calibration statement. Diagnostic deviations stay visible
and must inform limitations; do not silently promote them to required successes.
All scenarios must have zero failed replicates for the execution gate. A required
coverage deviation blocks the coverage gate; a diagnostic deviation alone does not.

Per metric report hits, valid/failed counts, unconditional hits/1000, Monte Carlo
SE sqrt(p*(1-p)/1000), interval mean width over valid intervals, and nominal-band
status. Count invalid selection/undefined intervals as misses in the denominator.
Report exception and warning class counts without messages/raw data, actual bin
count histogram, and selected-bin cluster counts. Unexpected exceptions abort
instead of being laundered into successful diagnostics. Missing optional packages
are environment failures. DPI upstream stdout/stderr is captured and discarded;
only warning classes and explicit failure types enter structured evidence.

## Evidence and review boundary

Bind each report to git revision/dirty state, this plan and protocol hashes, lock
hash, generated-input hash, Python and NumPy/SciPy/Statsmodels/binsreg versions,
RNG identity and command. Keep an aggregate JSON development report from a clean
protocol commit. Runtime estimates never collect this evidence. CI reruns the
development grid using the committed lock; it does not run final-assessment seeds.
Retain original development and locked failures without overwriting their evidence.

Review findings in a separate record so this prespecification stays fixed after
execution. Before final assessment the maintainer assigns a qualified reviewer to
accept/amend this protocol and the scope of supported claims. Any revision after
viewing assessment requires a fresh assessment set. Existing adjusted-bin inference
remains unavailable; passing DPI here does not validate formal binsreg intervals,
uniform bands, other DGPs, arbitrary weights, or a minimum safe cluster count.
