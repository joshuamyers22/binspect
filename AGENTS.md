# binspect agent working agreement

User instructions for the current task take precedence. Code/tests establish
current behavior; the [brief](PROJECT_BRIEF.md), reviewed ADRs, and
[plan](binspect-plan.md) establish intended scope. This agreement does not grant
merge, release, or external-configuration authority.

## Retrieve and verify

Read README, PROJECT_BRIEF, PROJECT_MEMORY, and the relevant plan task before
material work. Verify memory against linked implementation/tests. Inspect the
working tree and preserve unrelated changes. Proposed decisions are not accepted
decisions; never invent a reviewer or approval.

Keep numerical calculations in core, input preparation at its boundary, result
presentation in result modules, and rendering in viz. Preserve the current
pandas/NumPy/SciPy baseline while [ADR-0001](docs/decisions/0001-existing-library-baseline.md)
is reviewed. Do not import a template's unrelated service or license defaults.

## Work and verify in bounded slices

Use an existing defect reproduction or behavioral test as the safety net. For
material work, record objective, invariants, blocking severities, evidence,
iteration/time ceilings, and stop/escalation rules before extended iteration in
an adapted [verification record](templates/AGENTIC_VERIFICATION_LOOP.md).
Each subsequent pass must change evidence; repeated self-review is not independent
approval. Do not spawn additional agents unless the user or applicable
instructions explicitly authorize delegation.

Install the committed environment with `uv sync --frozen --all-extras`; run
`make check` for source/workflow changes. This includes lint/format, strict mypy,
import contracts, unit tests/coverage, locked DPI/Statsmodels integration,
prespecified development coverage simulations, and builds.
Documentation-only changes need link/example/format checks; do not call skipped
software checks passed. New failures or material code changes justify reruns.
Never silently change statistical conventions, drop failing reference tests, or
relax numerical tolerances to make a gate pass.

The [governance record](docs/GOVERNANCE.md) separates actual GitHub controls from
the review policy. Security/governance/release policy edits need a concrete,
reviewable diff and normal maintainer review. User authorization may cover
preparing and pushing that diff; the agent must not present its own review as
maintainer or independent statistical acceptance. Publish only with authorization
and the applicable [release evidence](checklists/RELEASE_READINESS.md).

## Memory and notes

PROJECT_MEMORY is a short, stable-key index of verified constraints, non-obvious
state, traps, and open work. Update entries in place, date them, and link evidence.
Do not duplicate the plan, append session narratives, or preserve resolved state
as current; Git/PR history carries the audit trail.

Keep disposable scratch in ignored `.work/`. Use the
[notes policy](notes/README.md) and [work-note form](templates/WORK_NOTE.md)
only when handoff, incident, experiment, or multi-session coordination needs it.
Record observations and conclusions, never hidden reasoning or transcripts.
Promote durable facts into tests/docs/ADRs/memory and close/delete stale notes.

Never store secrets, caller data, private labels, unrestricted error payloads,
raw logs, personal/client information, or credentials in tracked records.
Do not add runtime telemetry or network calls to this in-process library.
A user-reported trend needs controlled evidence and an
[improvement plan](templates/IMPROVEMENT_PLAN.md), not copied production logs.

At completion, review the diff, report actual checks and limitations, update
durable memory when facts changed, and leave plan status honest about review,
integration, and release.
