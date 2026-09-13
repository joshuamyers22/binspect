# R2 — release readiness review and renderer qualification

- Owner: Josh Myers; implementer: Codex; maintainer/release acceptance pending.
- Baseline: R3 `fc826db`, draft PR #26; 2026-09-12 local date.
- Branch: `chore/release-readiness`; status: in progress.

## Contract before iteration

Assemble a proposed 0.2.0 release readiness record with exact evidence identities,
missing approvals, concrete owners/actions and publication prerequisites. Recheck
actual remote controls and PR integration. Do not bump the version, create a tag,
merge, publish, configure controls, approve licenses or invent independent review.
Existing 0.1.1 build evidence cannot qualify proposed 0.2.0 release artifacts.

Resolve the known figure-job interpreter availability failure if an available
exact Python patch satisfies the existing CPython 3.12 renderer contract and all
unchanged image comparisons. Keep baseline PNGs, renderer manifest, font/library
pins, statistical tolerances, API, Polars defaults and pandas compatibility intact.
No new runtime functionality or fresh assessment seeds are in scope.

Three phases / 60 minutes: evidence/control inventory and candidate renderer probe;
small workflow/documentation changes and required `make check`; retained local/CI
evidence, consolidated readiness disposition and stacked draft PR. A failed renderer
comparison is a blocker, not a reason to regenerate baselines or widen guards.
Publication remains blocked by missing release-specific evidence and acceptance.
At the ceiling retain actual results and owned next actions; no approval is inferred
from another successful development check.

## Evidence ledger

| Phase | Evidence | Result |
|---|---|---|
| Baseline | R1/R3 retained results and release workflow | Latest local full gate: 600 tests. CI remains red for six pending licenses and unavailable Python 3.12.14 arm64 in the figure job. Actual controls, statistical/policy/performance acceptance and release provenance remain open. |

## Disposition

Readiness review and bounded renderer investigation in progress. No publication
is authorized or performed by this task.
