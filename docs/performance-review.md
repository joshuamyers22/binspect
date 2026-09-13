# P1 — workload measurement and occupied cluster aggregation

- Owner: Josh Myers; implementer: Codex; baseline/runner acceptance: pending.
- Date / library baseline: 2026-09-12 / `e331e3a`, stacked on D3 PR #21.
- Status: experiment in progress on `perf/cluster-workloads`.
- Scope: [P1](../binspect-plan.md), adapted from the production-template
  performance experiment and local bounded verification agreement.

## Prespecified experiment

Hypothesis: replacing dense bin-by-cluster score/count arrays with aggregation over
occupied pairs removes O(B*C) auxiliary storage without changing CR1 counts, means,
SEs or interval conventions. The current calculation has two B*C arrays plus a
score-square temporary (approximately 24*B*C bytes on this host). Occupied pairs
are at most the positive-weight row count. The simpler alternative is an explicit
dense-allocation refusal; prefer occupied aggregation if numerical references pass.
Do not modify labels, FWL, zero-weight policy, Polars outputs or pandas conversion.

Safety net: existing direct-score and Statsmodels references, new crossed/nested/
unique-label and zero-weight/cancellation cases (rtol 1e-12, atol 1e-12), plus an
allocation guard that rejects bin*cluster-sized bincount output before allocation.
Any numerical mismatch, omitted workload/failure, misleading support claim or
unbounded benchmark child is High and blocks completion. Documentation gaps are
Medium. No seeds or numerical tolerances may be tuned after observing results.

Measure Polars preparation/estimation end to end (including the API's input
conversion and immutable-result copies), separately from Matplotlib construction
and Agg draw. Synthetic data generation/imports are outside timed regions but
inside whole-process peak RSS. Each trial uses a fresh child, one first call and
one warm repeat per stage, with garbage collection between calls. Rendering uses
precomputed results; check output equivalence outside timed regions. No parallel
benchmark workers. Record individual trials, median/min/max, hardware, lock/source
identity and numerical equivalence. First-call timing is not cold disk-cache timing.

Grid: 10k, 100k and 1M rows; base 20 bins; 100 bins; 100 clusters; clusters=n
with 100 bins; 4/16 groups; 4/16 numeric controls. All cases use PCG64 seed 130101
(fresh stream per size/specification). Three fresh trials per case, all rows used
for estimation. Render both default layers and a bins/CI/fit-only view for base and
near-row-count clusters; other cases use bins/CI/fit only. Group rendering includes
all facets. Large rugs remain explicit measured workloads, not silently sampled.

Local resource ceiling: one child at a time, 120 seconds per trial and 2 GiB RSS;
stop/record that case on exceeding either limit. Monitor RSS from the parent and
terminate the child if exceeded; sampling is a guard, not a hard allocation limit.
Preflight skips legacy dense cases above 256 MiB predicted score/count/square
storage, records the reason, and never labels them measured. No 10M trial or
general capacity promise. Host is Apple M1 Pro, 8 logical CPUs, 16 GiB RAM, macOS
arm64; controlled thread settings are recorded. Host facts required an authorized
read outside the sandbox. This workstation is a candidate benchmark host, not an
accepted CI runner.

Maximum four evidence-changing phases / 90 minutes / local compute only: baseline
harness and measurements; aggregation plus reference/guard tests; candidate grid
and comparison; full gate/docs/review. Roll back the optimization on a supported
numerical mismatch. If a workload hits a cap, record it as unqualified and document
the bounded alternative; do not increase the cap to make it pass. Numeric timing/
RSS regression budgets must be derived from retained repeated measurements and
remain proposed until a maintainer accepts the baseline and controlled runner.
Implement comparison/enforcement without fabricating that acceptance.
Before candidate measurements, fix the proposal rule at 1.25 times each timing's
maximum trial and 1.20 times each RSS maximum. These are review candidates, not
statistical confidence limits or accepted support promises; excluded/capped cases
receive no budget. Enforcement must reject pending acceptance, changed environments,
missing/incomplete cases, and time/memory overruns.

## Evidence ledger

| Phase | Changed evidence | Result / next action |
|---|---|---|
| Baseline inspection | Dense score/count/square allocation and existing CR1 references | 100 bins × 1M clusters implies ~2.4 GB in those working arrays alone; allocation fix and measured envelope required. |

## Disposition

Experiment pending. Local verification is not maintainer acceptance, a release or
new inference qualification. No external service/runtime telemetry is introduced.
