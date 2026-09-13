# P3 — supply-chain and secret checks

- Owner/reviewer: Josh Myers; implementer: Codex; integrated through PR #30.
- Baseline: P2 `54b197d`, draft PR #23; 2026-09-12 local date.
- Branch: `security/supply-chain-checks`; implementation locally verified.
- Current gate result: **pass** after the six exact license scopes were accepted
  by Josh Myers on 2026-09-13.

## Contract before iteration

Audit the locked runtime, optional, development, documentation and build package
versions for known vulnerabilities and license metadata. Include the lock's
platform-specific versions, not just packages installed on this host. Build tools
must be explicit and locked to identify the tools used for audited artifacts.
Generate and inspect CycloneDX evidence for the wheel/sdist and dependency graph.
Scan complete available Git history, tracked working files and extracted built
artifacts for secrets using a pinned scanner; retain only redacted metadata.
Reject shallow history, missing scanner/service data, unknown license review,
expired/unreviewed exceptions and mutable third-party action references.

Prepare CI and release gating, not a release or repository-setting change. Keep
the MIT project license, Polars defaults/pandas compatibility, numerical behavior,
reserved seeds, rendering baselines and package version unchanged. Dependency
updates must retain a regenerated lock and pass numerical drift/full local gates.
Do not invent license/security acceptance, ignore vulnerabilities automatically,
weaken statistical checks, or publish sensitive findings in public records.

Four evidence-changing phases / 120 minutes of local work and necessary downloads:
tool/baseline audit; bounded fixes and gate regressions; CI/release integration;
full `make check`, audit and review. Existing P2 and full locked checks are the
safety net. Block High findings: missed dependency/artifact scope, secret exposure,
false clean status, unreviewed vulnerabilities or artifact identity mismatch.
Missing repeatable evidence or action pins is Medium. At the ceiling preserve
actual findings and unresolved gates; do not turn unavailable checks into passes.
Maintainer policy/license approval and R1/R2 release qualification stay explicit.

## Evidence ledger

| Phase | Evidence | Result |
|---|---|---|
| Baseline | Existing CI/release workflow, lock, threat/release records | P2 is locally verified. Release publisher uses mutable `release/v1`; build tools are unpinned. No supply-chain gate exists. |
| Tool/lock audit | Pin Hatchling 1.32.0, build 1.6.1, Twine 7.0.0, pip-audit 2.10.1, CycloneDX library 11.12.0 and Gitleaks 8.30.1 | Lock now contains 153 registry name/version pairs. Build changes from 1.6.0 to 1.6.1; numerical/rendering dependency versions are unchanged. Direct all-pin pip-audit input rejected duplicate names; disjoint batches (143/8/2) preserve every platform-specific version and their union is checked. |
| Advisory/license probes | Live PyPI services for all 153 versions | No known vulnerabilities reported; no vulnerability exceptions. Six license reviews remain pending: binsreg, certifi, docutils, fqdn, hypothesis and pathspec. Mypy-extensions' missing metadata is resolved through its hash-verified locked wheel's MIT license, not an approval override. |
| Secret probes | Default Gitleaks history scan | Three generic API-key findings were actual source digests. Every value matched its historical source bytes. Exact path/key/value exclusions preserve the default rules and all other findings. History, tracked working files, extracted distributions and a generated positive canary pass. |
| Bounded gate fixes | Rejection regressions and installed tooling | Boolean SPDX expression objects require explicit identity checks, not Python truth evaluation. Artifact verification now includes the legitimate `py.typed` marker; regression fixtures reproduce the initial rejection. Isolated tooling prevents normal uv development commands from changing audit/build tools mid-run. Stale local 0.1.0/dev0 distributions were correctly rejected by identity checks. No statistical tolerance or scanner rule was disabled. |
| CI/release integration | Separate blocking CI job and release pre-handoff gate | Full history fetch; exact lock consistency; pinned action refs and uv 0.12.5. Release audits existing distributions before upload/publishing; controlled evidence is retained even on failure. Workflow execution and actual repository/publisher controls remain unverified locally. |
| Full local gate | Final `make check` | Passed: 480 unit tests, 34 DPI/adapter and 40 Statsmodels reference tests, 94.65% coverage, mypy (38 files), four import contracts, native no-pandas journey, all development coverage protocols, 38 doc blocks plus quickstart, strict MkDocs, four PNG baselines with RMS 0.0, and locked nonisolated sdist/wheel builds. |
| Complete supply-chain gate | Fresh isolated environment and live services | Actions, all 153 advisory checks, artifact identity, all secret scopes and CycloneDX validation pass. License screening fails on the six explicitly pending reviews. Exit is nonzero as designed; this gate is not reported as clean or accepted. |

The 22 new regression cases reject missing/skipped/wrong advisory inventory,
pending/expired/mismatched exceptions, unsafe archives, mutable actions, sensitive
scanner fields and stale/altered artifacts. Final full checks use unchanged
statistical conventions and assessment seeds remain reserved.

## Retained evidence and reproduction

Run `make supply-chain` as described in [the scope/runbook](SUPPLY_CHAIN.md).
The committed evidence snapshot contains a [controlled report](evidence/supply-chain-2026-09-12.json),
[all package license metadata](evidence/supply-chain-licenses-2026-09-12.json),
and the [compressed CycloneDX graph](evidence/supply-chain-sbom-2026-09-12.cdx.json.gz)
for the actual inspected wheel/sdist built from implementation commit `358c38a`.
Decompress the `.cdx.json.gz` file to inspect normal CycloneDX JSON; its uncompressed
SHA-256 must match the report. These are development artifacts, not a published
release. The source revision identifies the implementation commit; a later
evidence-only commit records the snapshot and is not the artifact build input.
Regenerate against the exact future release artifact bytes; never substitute this
dated snapshot for release approval.

Gitleaks official release assets supplied the checked SHA-256 values in
[the scanner pins](../validation/scanner-pins.json). The publisher's official
v1.13.0 annotated tag resolves through tag object
`106e0b0b7c337fa67ed433972f777c6357f78598` to commit
`ed0c53931b1dc9bd32cbe73a98c7f6766f8a527e`. Its
[action entry point](https://raw.githubusercontent.com/pypa/gh-action-pypi-publish/ed0c53931b1dc9bd32cbe73a98c7f6766f8a527e/action.yml)
retains Trusted Publishing/attestation inputs, Linux execution and a pinned nested
setup-python fallback. P3 pins repository workflow references; it does not certify
every component of that action's generated publisher container. R1/R2 still own
publisher execution, artifact handoff, provenance and release qualification.

Initial sandbox GitHub/download failures were retried with authorized network
access; unavailable services were never reported as passes. Raw secret reports
remain temporary and are projected to rule/file/line/commit metadata before
retention. The scanner canary is generated at runtime and carries no authority.

## License disposition

See [the six concrete decisions and primary sources](SUPPLY_CHAIN.md#six-approved-scoped-license-decisions)
and [the approval registry](../validation/supply-chain-exceptions.json). Owner and
reviewer: Josh Myers; reviewed 2026-09-13; review expiry: 2026-10-13. The approvals
cover the documented separately installed, non-bundled PyPI scope. Changed versions,
broader redistribution or expiry require renewed review and applicable GPL/MPL or
file-specific notice/source obligations. The project remains MIT. No dependency was
removed or relicensed to evade this review.

## Disposition

P3 implementation and its scoped license review are integrated through PR #30. A
fresh local online gate and exact-head CI run 34783516923 pass all six stages after
the maintainer decision. This does not authorize publication or broaden the recorded
scope. Repository controls and R1/R2 release-specific evidence remain separate gates.
