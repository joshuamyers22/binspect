# Repository ownership and GitHub controls

Verified 2026-09-12 through read-only GitHub API calls. Repository:
`joshuamyers22/binspect`, public, default branch `main`.
Policy additions here are proposed for maintainer review in G1; no remote
configuration was changed by this task.

## Ownership and review

Josh Myers (`@joshuamyers22`) is the repository owner and accountable maintainer.
Implementers supply focused changes and actual verification evidence. The
maintainer decides compatibility, risk acceptance, merges, releases, and
statistical-review assignments. This records accountability, not an on-call
commitment or a guarantee of independent review in a single-maintainer project.

Proposed working policy: use reviewable PRs, preserve exact-head CI evidence,
and obtain accountable review of security/governance/release changes. A qualified
statistical reviewer must be assigned before C3 acceptance. When the author and
maintainer are the same person, record that limitation rather than fabricating
independence. [CODEOWNERS](../.github/CODEOWNERS) routes ownership once integrated;
it is not an enforcement mechanism by itself.

A user may authorize preparation and pushing of proposed policies. Only an
explicit review disposition establishes acceptance. ADR-0001 remains proposed;
the existing library stack remains the working baseline pending that disposition.

## Observed controls

| Control | Observed result | Consequence / due gate |
|---|---|---|
| Main branch protection | GET branch protection returned 404, “Branch not protected.” | No enforced required checks/reviews, force-push or deletion protection verified; G1/R1. |
| Repository rulesets | Empty list. | No substitute ruleset enforcement observed; G1/R1. |
| Actions policy | Enabled; all actions allowed; SHA-pinning not required remotely. | Workflow pins must be checked in source; mutable publisher ref remains a P3 gap. |
| Secret scanning / push protection | Both enabled. | Useful controls, not evidence that every secret/data leak is prevented. P3 still audits history/artifacts. |
| Dependabot security updates | Disabled in repository settings. | Version-update schedule exists in YAML; automatic security-fix PRs are a separate gap, due P3. |
| Private vulnerability reporting | `enabled: false`. | The public “Report a vulnerability” route is unavailable. The maintainer must enable it or publish a verified private contact before R2. |
| PyPI environment | Required reviewer `joshuamyers22`; prevent-self-review false; no branch/tag deployment policy. | Approval exists, but self-review is allowed and ref restrictions are absent. R1 verifies desired policy. |
| PyPI Trusted Publisher | Not inspected at PyPI. | GitHub OIDC YAML/environment alone does not verify publisher mapping or successful publication; R1/R2. |

No account-plan limitation was returned for this public repository. Do not copy
the production-template repository's historical private-repository limitation
as evidence about binspect.

## Recheck procedure

Use authenticated GET requests for these endpoints, recording only the summarized
fields above; do not retain tokens, secret values, raw response dumps, or personal
profile payloads:

- `repos/joshuamyers22/binspect`
- `repos/joshuamyers22/binspect/branches/main/protection`
- `repos/joshuamyers22/binspect/rulesets`
- `repos/joshuamyers22/binspect/actions/permissions`
- `repos/joshuamyers22/binspect/environments/pypi`
- `repos/joshuamyers22/binspect/private-vulnerability-reporting`

Record the date and distinguish an absent control from permission/network failure.
Configuration changes need the owner's reviewed decision; this document is not a
request to enable controls automatically.

## Proposed enforcement target and remaining decisions

Before R2, the maintainer reviews a concrete configuration change for main:
require PRs and the applicable CI matrix plus `dpi-integration`, block force pushes
and deletion, define bypass/admin behavior, and decide how approvals work for the
actual collaborator set. Define allowed deployment refs and reviewer/self-review
policy for PyPI. Verify required checks after job names change.

Review Dependabot security updates and action policy in P3, verify a usable private
reporting route, and retain the release evidence in the
[checklist](../checklists/RELEASE_READINESS.md). These are open controls with owner
Josh Myers, review due before their named gates and after any settings change.
A proposed policy or CODEOWNERS file does not make main protected.
