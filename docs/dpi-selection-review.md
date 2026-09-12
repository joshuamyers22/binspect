# C1: DPI selection correction

Status: implemented and locally verified on `fix/dpi-selection`; pending maintainer
review/integration. Owner: implementation by Codex; maintainer
review by Josh Myers. Scope: [C1 in the project plan](../binspect-plan.md).

## Contract and bounded verification

- Correctness: a DPI request uses the upstream `nbinsdpi` count for a piecewise
  constant model, requested spacing, full sample, and enabled mass-point checks.
  binspect owns its subsequent quantile/empty-bin reduction; it does not claim
  identical knots or intervals to binsreg. No ROT fallback or silent clipping.
- Supported scope: unweighted, uncontrolled, unclustered estimates, with quantile
  or equal-width spacing. Reject other DPI combinations before calling the
  backend; integer/custom/heuristic choices remain available for those estimates.
- Failure policy: missing dependency, failed numerical selection, missing/invalid
  count, or a count outside [2, retained sample size] gives an actionable
  `InvalidBinningError`. Preserve exception causes for backend failures.
- Provenance: selected rule, requested/actual counts, and fallback status are
  available in result metadata and exports. Common group edges are labelled as
  pooled selection with the parent's rule; independent groups select separately.
- Non-goals: inference changes, grouped-control repair, engine migration, new
  fallback algorithms, dependency upgrades, or publication.
- Evidence: failing regression before the fix; focused adapter/error/export
  tests; real binsreg integration with the committed lock; existing full gate.
- Blocking threshold: any incorrect method, ignored supported option, silent
  fallback, broken public behavior outside the documented correction, or failed
  required check. Coverage is a guardrail rather than proof.
- Ceiling: three evidence-changing implementation/review passes, 90 minutes of
  implementation verification; no paid compute or large-data benchmark. Stop
  when criteria and applicable gates pass. Escalate unsupported statistical
  assumptions instead of broadening scope; record any remaining findings.
- This is an implementation self-review, not independent statistical approval
  or release authorization. G1/G2 and C2 onward remain separate plan tasks.

## Upstream contract

The pinned development environment contains binsreg 3.2.1. Its selector documents
`nbinsdpi` separately from `nbinsrot_regul` and `nbinsdpi_uknot`. The adapter uses
the count before upstream unique-knot reduction because binspect constructs its
own edges. Explicit options are `bins=(0, 0)`, `binsmethod="dpi"`, `binspos="qs"`
or `"es"`, `masspoints="on"`, `vce="HC1"`, and `randcut=None`. HC1 here belongs
to upstream selection, not to binspect's reported slope covariance.

See the [upstream selector source](https://github.com/nppackages/binsreg/blob/main/Python/binsreg/src/binsreg/binsregselect.py).

## Evidence and disposition

| Pass | New evidence | Outcome |
|---|---|---|
| 1 | Regression test with distinct upstream ROT/DPI fields | Failed before implementation: returned ROT 5 instead of DPI 17. |
| 2 | Adapter/error/provenance tests and real binsreg calls for both spacings and discrete inputs | 49 new unit cases and 6 real-library cases pass. The original seed-7 case now returns DPI 65 rather than ROT 35 in the local locked environment. |
| 3 | Full local gate and diff review | `make check` passes: Ruff lint/format, strict mypy, all 3 import contracts, 209 unit tests (6 integration cases deliberately deselected), 91.62% coverage, 6 separately executed integration tests, wheel and sdist builds. |

The initial full-gate attempt hit restricted dependency resolution; rerunning with
approved network access succeeded. The gate also identified formatting in the
earlier plan review's Python examples, which was corrected. An upstream mizani
deprecation warning appears during import; no test is skipped or warning hidden.

The new `dpi-integration` CI job installs the committed lock on Python 3.12 and
runs `make integration` in frozen mode. It has no `continue-on-error` or optional
skip. GitHub execution and required-status enforcement have not been verified
for this local branch; G1/R1 track governance settings. No release was published.

Stop condition: C1's local implementation rubric passed. Numerical inference,
weighted/clustered/controlled DPI, G1/G2, and C2 onward remain outside this slice.
The added metadata fields are additive schema changes recorded in the changelog;
the unsupported DPI combinations intentionally raise where the old selector
silently omitted options. Review these compatibility effects before integration.
