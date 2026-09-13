# R2 — release readiness review and renderer qualification

- Owner: Josh Myers; implementer: Codex; maintainer/release acceptance pending.
- Baseline: R3 `fc826db`, draft PR #26; 2026-09-12 local date.
- Branch: `chore/release-readiness`; status: readiness preparation complete; publication blocked.

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

| Renderer investigation | Official actions/python-versions manifest and uv 0.12.5's managed downloads | No macOS arm64 3.12.14 build in setup-python's manifest; uv provides the exact patch. The managed interpreter matches every field of the existing renderer contract. |
| Repair | `ddec636`; [draft PR #27](https://github.com/joshuamyers22/binspect/pull/27) | Figure CI now uses isolated, managed Python 3.12.14 through pinned uv 0.12.5 and the frozen lock. No baseline, font/library pin, tolerance, package version or runtime change. |
| Local verification | [Retained environment and results](evidence/release-readiness-2026-09-12.json) | Managed renderer: four RMS values 0.0. Full `make check`: 526 unit + 34 DPI + 40 reference tests (600), 94.65% coverage, strict mypy (38 files), four import contracts, all development simulations, 38 docs blocks plus quickstart, strict site, figures and wheel/sdist build pass. Reserved assessments unrun. |
| Remote verification | [CI run 34733407408](https://github.com/joshuamyers22/binspect/actions/runs/34733407408), head `ddec636` | Figure job passes on macos-15, all four RMS values 0.0. Every other job passes except supply-chain, which fails only for the same six pending licenses; vulnerability, action, artifact, secret and SBOM checks pass. Overall CI remains failed. |
| Readiness/control review | [Proposed 0.2.0 record](releases/0.2.0-readiness.md), retained GitHub/PyPI observations | PRs #15–#23 are already merged; main is `2a6a486`. #24–#26 remain drafts. Main remains unprotected, rulesets empty, PyPI self-review allowed/ref restrictions absent, private reporting disabled, owner-side publisher mapping unverified. PyPI reports 0.1.1; its hashes differ from the development pair. |
| Final evidence | Recorded input/artifact identities, local Markdown links, formatting and pinned evidence scan | Controlled evidence contains no secret findings and no new exclusion. The readiness checklist remains unapproved; code verification does not close policy, license, statistical, performance, visual, operator or release-specific evidence gates. |

## Evidence identity and limitations

Implementation/CI head is `ddec636e69d247067d134919381c7683a381b1bf`; the remote
checkout revision is a PR merge and is not a selected release candidate. The local
managed-renderer probe preceded the workflow commit; renderer code, baseline PNGs,
manifest, font/library lock and runtime inputs are unchanged across it. A later
documentation/evidence commit is not the recorded CI head. Full local checks ran
on the implementation revision; final documentation wording/link changes received
separate link/format checks.

The original failure was interpreter provisioning, not a pixel regression. The
fix retains Python 3.12.14 and every existing renderer check; it does not regenerate
or approve baseline images. Both the local host and GitHub macos-15 now match them.
Maintainer visual acceptance and general host/accessibility claims remain separate.

The read-only integration observation corrects stale memory/plan labels. It does
not assert that this agent performed or approved those merges, nor infer statistical
or risk acceptance from a merged PR. PR #24's retained P2 base and divergence from
current main must be handled during the remaining integration review.

PyPI metadata observations are not verification of downloaded published bytes,
release provenance or owner-side permissions. A 404 for proposed 0.2.0 does not
prove that filenames were never used. The known 0.1.1 development pair cannot be
relabeled as 0.2.0 or replace files already published under the same names.
No candidate-specific 0.2.0 artifact, passing audit, verifiable build provenance,
published-install result or release approval was created here.

## Disposition

R2 readiness preparation and the bounded renderer repair are ready for maintainer
review in draft PR #27, stacked on R3. **R2 publication is not complete and remains
blocked.** The concrete next actions, owners and evidence requirements are in the
[proposed release record](releases/0.2.0-readiness.md). Do not repeatedly rerun
unchanged development checks in place of obtaining the missing decisions.
No merge, version bump, tag, GitHub release, publish, yank, control change, license
approval or independent-review acceptance was performed.
