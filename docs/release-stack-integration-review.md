# R2 — prepare the release stack against current main

Owner: Josh Myers. Implementer: Codex. Integration/release acceptance pending.
Baseline stack: `8830649` (draft #29). Main: `2a6a486` (merged through #23).
Branch: `review/release-stack-integration`.

## Contract before iteration

Prepare a review branch containing current main and the P3/R1/R3/R2 draft stack.
Resolve conflicts while preserving both main's category-identity correction and
its regression tests, and the stack's supply-chain, artifact, maintenance,
renderer, provenance and license-evidence work. Open a draft PR targeting main.
Local branch integration is preparation, not a GitHub PR merge or release decision.

Three phases / 60 minutes: compare both parents and reproduce the missing main
fix; resolve conflicts and verify the combined tree with required `make check`;
retain precise evidence and prepare a draft. Preserve Polars-native tables,
optional pandas conversion, numerical tolerances, reserved seeds, version, licenses
and pending approvals. Do not mutate main, rewrite/close prior PRs, publish, run
release signing, activate schedules or change settings. Correctness regressions,
lost parent changes, unresolved conflicts and new CI failures block readiness.
At the ceiling record actual remaining work rather than fabricating acceptance.

## Evidence and disposition

Main has the declared-integer-category fix and two regression cases absent from
the stack. Without integration, categories `2**53` and `2**53 + 1` can collapse
during float conversion. Main also carries its prior stack review and documentation
changes that must be reconciled, not silently discarded.

Both main regression cases fail against a detached checkout of stack `8830649`:
the expected alternating dummy column becomes all ones. The combined branch
preserves main's source correction and complete regression file byte-for-byte.
No new statistical tolerance or synthetic seed was introduced.

Five conflicted files were reconciled. The CI workflow and two renderer documents
retain the stack's verified uv-managed 3.12.14 path; main's alternate patch-selection
repair is superseded by that tested setup. The automatically merged contributor
guide is aligned with it. Memory/plan retain current pending gates and the later
stack work while incorporating main's A1–P2 review dispositions. Main's historical
`pr-stack-review.md` and categorical changelog entry are preserved.

Targeted and full combined-tree verification pending. No GitHub PR has been merged,
no previous draft changed or closed, and no release, setting or approval changed.
