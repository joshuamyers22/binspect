# G1/G2: repository agreement and library threat model

- Date: 2026-09-12; implementation base `f89e945`.
- Scope: G1/G2 in the [project plan](../binspect-plan.md).
- Implementer: Codex; accountable maintainer/reviewer: Josh Myers.
- Status: locally verified and ready for maintainer review; no agent self-approval of governance,
  security policy, statistical methods, or release decisions.

## Bounded verification contract

Objective: make repository/review ownership and library trust boundaries concrete,
evidence-linked, and usable across sessions. Preserve MIT licensing and the
existing statistical/API behavior. Document verified remote controls separately
from planned controls; do not enable or weaken them implicitly.

Pass criteria: adapted agreement/memory/notes/review/release records exist with
valid references; the threat model links current controls to tests and gives open
risks owners/due gates; clean-process tests cover import/estimation side effects;
the applicable full local gate passes. Any unsupported claim of protection or
security acceptance blocks this change's readiness for review.

Ceiling: three evidence-changing passes, 90 minutes, local tests and read-only
GitHub inspection; no publication, paid compute, or resource-exhaustion stress
test. Stop after the rubric passes or report remaining failures at the ceiling.
Escalate policy acceptance to maintainer review rather than attributing it to
the implementation agent. Existing user authorization covers completing and
pushing reviewable work; it does not imply that every residual risk was accepted.

## Evidence and disposition

| Pass | Changed evidence | Result / disposition |
|---|---|---|
| 1: baseline and boundary reproduction | Read-only GitHub audit; fresh-process runtime test with a new Matplotlib cache directory. | Main unprotected, no rulesets, private reporting/security updates disabled. Plain import triggered Matplotlib's font-manager timer, failing the new test. |
| 2: implementation | Adapted repository forms/policies and threat model; deferred top-level plotting exports while preserving their names/types. | Focused runtime/plot suite passed (34 tests before adding the export compatibility case); corrected new-test lint findings. Numerical behavior and public plotting exports retained. |
| 3: final gate | Added plotting-export compatibility evidence; full gate and documentation checks. | 211 unit tests, 6 locked DPI integration tests, 91.67% coverage; Ruff, strict mypy (27 source files), all 3 import contracts, wheel and sdist passed. 16 documents / 73 local links checked, balanced code fences and clean diff whitespace. |

The first full build could not resolve PyPI in the network sandbox. Repeating the
gate with authorized network access completed successfully. The upstream mizani
NumPy-timedelta deprecation warning remains visible; no suppression was added.
No statistical convention, tolerance or dependency was changed to pass checks.

The boundary regression denies Python-audited socket/process operations and
Python thread starts, checks root logging state, and verifies Matplotlib remains
unloaded through plain import and ordinary estimation. It does not cover arbitrary
caller object methods, native numerical workers, explicit plotting/theme access,
optional DPI, or every dependency path. This is a regression contract, not a
security sandbox or comprehensive supply-chain audit.

Detailed sanitized remote observations and unresolved controls belong in
[governance](GOVERNANCE.md). No GitHub settings or PyPI publisher mapping were
changed. Earlier roadmap and C1 draft PRs (#6 and #7) passed their GitHub CI;
that evidence does not qualify this subsequent change or a release.

Stop condition: local implementation rubric passed. Maintainer acceptance of the
brief/ADR, repository/security policy and residual risks remains open, as do the
remote controls assigned to G1/P3/R1 and later production gates. C2 is the next
numerical task after relevant baseline decisions; its bounded rejection fix does
not require inventing a common adjusted estimand. No independent review is claimed.
