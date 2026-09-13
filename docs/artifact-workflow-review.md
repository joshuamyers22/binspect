# R1 — artifact and workflow qualification without publishing

- Owner: Josh Myers; implementer: Codex; maintainer acceptance pending.
- Baseline: P3 `2863e6d`, draft PR #24; 2026-09-12 local date.
- Branch: `test/artifact-workflow-qualification`; status: in progress.

## Contract before iteration

Use the P3 locked build environment to produce one wheel/sdist pair. Validate
metadata and content, preserve their identities through upload/download, and
install each independently outside the source checkout. Test native Polars
estimation/export/plots, explicit pandas conversion and optional DPI using the
existing installed-code journey and seed 140101. Sdist installation must build
with locked backend dependencies, not resolve an unpinned isolated backend.

Add a nonpublishing CI path shared with release preparation. Exercise exact tag
acceptance and mismatched/malformed tag rejection. Do not grant publishing/OIDC
permissions to rehearsal jobs, create a release, modify repository settings or
waive P3 license findings. Recheck actual branch/ruleset/PyPI-environment controls;
missing access or unverified Trusted Publisher mapping stays explicit.

Retain Polars defaults/pandas compatibility, numerical/plotting behavior, package
version and statistical tolerances. Python scope stays 3.10–3.13 Linux/macOS.
Every artifact install must verify noneditable installed code and the expected
version, record actual dependency versions, and reject changed/missing/extra
handoff files. Checksums verify handoff integrity, not publisher authenticity.

Four evidence-changing phases / 120 minutes: implementation and regressions;
clean artifact-install probes; CI/release integration and read-only controls audit;
full `make check`, final evidence and review. Block High findings: source-checkout
imports masquerading as artifact installs, mutable builds/handoffs, unexpected
publishing routes, relaxed statistical checks or false control/acceptance claims.
Missing target evidence is Medium. At the ceiling preserve actual results and
remaining gates. P3 license acceptance and R2 publication remain separate.

## Evidence ledger

| Phase | Evidence | Result |
|---|---|---|
| Baseline | P3 gate, locked build group and release YAML inspected | Build tools are locked; no clean wheel/sdist installation or nonpublishing upload/download path exists. P3 remains blocked by six license reviews. |

## Disposition

Implementation and verification in progress. No publication or repository-setting
change is authorized by this record.
