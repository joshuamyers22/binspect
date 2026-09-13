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

The local integration commit is `a1940587ecf13c258c8ff482f3f68cf4ad11817b`, with
parents `83d28ae` (stack plus this verification contract) and `2a6a486` (main).
All 77 existing main source/test/baseline files, excluding the intentionally
updated baseline README, match main exactly. The stack's validation scripts,
workflows, manifest and lock match `8830649`. Runtime source has no diff from main.

All 35 Polars contract tests pass on the combined branch. Required `make check`
passes: 558 unit + 34 DPI + 40 reference tests (632), 94.65% coverage, strict mypy
(38 source files), four import contracts, native Polars without pandas, unchanged
development simulations, 38 docs blocks plus quickstart, strict site, four image
comparisons at RMS 0.0 and wheel/sdist build. Reserved assessments remain unrun.
The detached preintegration checkout was removed after the reproduction; controlled
outcomes remain recorded here rather than retaining raw failure logs.

[Draft PR #30](https://github.com/joshuamyers22/binspect/pull/30) targets `main`.
[CI run 34735451959](https://github.com/joshuamyers22/binspect/actions/runs/34735451959)
at integration head `a194058` completes with 34 passing jobs. Supply-chain alone
fails, exclusively for the same six pending license decisions; its vulnerability,
action, artifact, secret and SBOM checks pass. The recorded audit source hash for
the category boundary matches this combined tree. The CI checkout is a PR merge
revision; the [controlled evidence](evidence/release-stack-integration-2026-09-12.json)
records both identities and the exact inspected development artifact hashes.

This branch is prepared for maintainer integration review. It has no runtime-source
diff from current main and introduces the pending release-tooling stack through
one main-based draft. Earlier PRs #24–#29 retain their original branches/bases and
review history. A later documentation/evidence commit is distinct from the
verified integration head and receives separate documentation/evidence checks.
Final checks pass for 189 local Markdown links, Ruff/formatting, whitespace and
the retained evidence directory's pinned Gitleaks scan. The scanner's cached
archive and executable match the committed pin; no exclusion was added.
No GitHub PR has been merged, no previous draft changed or closed, and no release,
setting or approval changed. License, statistical, policy, performance, visual,
operator and exact-release gates remain open.

## 2026-09-13 follow-up review

Review of the combined diff found one artifact-integrity defect: the sdist checker
claimed full manifest equivalence while only comparing `pyproject.toml` and package
source, and distribution dependency/extra/license metadata was not compared with
the project declaration. The fix verifies that an sdist contains exactly its
generated `PKG-INFO` plus every Git-tracked file with identical bytes, and verifies
declared dependencies, extras, classifiers, Python requirement and license for
both distribution formats. Seven new rejection regressions exercise altered,
missing, extra and outside-prefix sdist members and altered metadata.

Fresh local wheel and sdist builds pass the strengthened verifier. `make check`
passes with 565 unit tests, 34 DPI integrations and 40 references (639 total),
94.65% coverage, all type/import, native, simulation, documentation, figure and
build gates. A new online `make supply-chain` run passes actions, vulnerabilities,
artifacts, secrets and SBOM checks and fails only for the unchanged six pending
license decisions. [CI run 34781858587](https://github.com/joshuamyers22/binspect/actions/runs/34781858587)
on exact fix commit `efb6e34` completes with 34 passing jobs. The
strengthened artifact check and all 12 clean-install jobs pass; supply-chain's
actions, vulnerability, artifact, secret and SBOM checks pass, and only the six
license entries fail. Main remains unprotected as of the read-only GitHub query;
that does not justify bypassing the fail-closed license gate. Integration and all
owner-held acceptance decisions remain pending.
