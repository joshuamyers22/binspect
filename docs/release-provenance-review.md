# R2 — authenticated artifact provenance

Owner: Josh Myers. Implementer: Codex. Maintainer acceptance pending.
Baseline: `feec019`, draft #27. Branch: `security/release-provenance`.

## Contract before iteration

Add release-only signing of the already built, installed and audited wheel/sdist,
with independent verification before publication. Bind verification to exact
artifact bytes, source and signer commit, release ref, workflow and run attempt.
Preserve the read-only, nonpublishing R1 reusable workflow. Signing permissions
belong only to the release provenance job; signing does not grant release approval.
Do not modify runtime behavior, Polars defaults, pandas support, versions,
statistical seeds/tolerances, licenses, repository settings or release decisions.

Three phases / 60 minutes: inspect official action/verifier contracts; implement
and test rejection paths plus required `make check`; review diff and record a
stacked draft PR. Identity, integrity or missing verification failures block
publication. Unsupported tooling or unavailable services fail closed. No live
release event will be created to exercise signing. Fixture tests do not constitute
cryptographic qualification; actual signed candidate evidence remains required.
Stop at the ceiling with precise remaining work; never manufacture acceptance.

## Evidence and disposition

The release workflow adds a signing job after successful artifact installation and
audit, and a mandatory fresh verification step immediately before the publisher.
The original manifest handoff and read-only R1 workflow are preserved. The signed
bundle is retained separately by immutable artifact ID with 90-day requested
retention. No version, package API, lock or statistical input changed.

Targeted checks: 30 provenance rejection/policy tests plus 21 existing
artifact integrity tests pass. Parsed workflow checks confirm the release-only
trigger, dependency order, signing permission scope and prepublication gate.
Ruff, formatting and 157 local Markdown links pass.

At implementation `a0a758fedc022ecc2acc6d973801886e2c34a1b9`, required `make check`
passes: 556 unit + 34 DPI + 40 reference tests (630), 94.65% coverage, strict mypy
(38 files), four import contracts, native Polars without pandas, all prespecified
development simulations, 38 docs blocks plus quickstart, strict site, four figure
comparisons at RMS 0.0 and wheel/sdist build. Reserved assessments remain unrun.

[CI run 34734345196](https://github.com/joshuamyers22/binspect/actions/runs/34734345196)
at that head completes with 34 passing jobs. Only supply-chain fails, exclusively
for the six existing pending licenses; its action, vulnerability, artifact, secret
and SBOM checks pass. The separate local audit fails for the same license reviews
and leaves secret scanning **unverified** after `ReadTimeout`; its other checks
pass. The local timeout is not relabeled as a pass using CI's separate evidence.
No scanner exception was added or license decision changed.
The retained evidence directory separately passes the cached Gitleaks 8.30.1
scanner, after verifying its archive and executable against the committed pin.
That bounded evidence scan does not replace the unverified full local secret audit.

[Controlled evidence](evidence/release-provenance-2026-09-12.json) records exact
inputs, action/probe identities, job conclusions and audit dispositions. Draft
[PR #28](https://github.com/joshuamyers22/binspect/pull/28) is stacked on #27.
Subsequent documentation/evidence commits are distinct from the verified
implementation head and receive separate link/format/secret checks.

The official `actions/attest` v4.2.2 tag resolves to
`1e69f48acb82d1966a394da916b4c1698aa569d6`. Inspection of that commit's action
definition and shipped `dist/index.js` confirms default SLSA v1 provenance,
basename subjects, the workflow build-type URI and run-attempt metadata used by
the policy. Storage-record creation is disabled; no artifact-metadata permission
is granted. This inspection is not independent supply-chain acceptance.

GitHub CLI 2.98.0 successfully authenticated the upstream
[`actions/attest-demo` wheel fixture](https://github.com/cli/cli/tree/v2.98.0/pkg/cmd/attestation/test/data)
with its signed bundle, repository/workflow/source/ref restrictions and hosted
runner requirement. The certificate exposes `runInvocationURI` and `buildTrigger`
as expected. Initial sandbox trust-root initialization failed; the permitted
network retry passed. The fixture was retained only in ignored scratch and never
installed or executed. It is an upstream workflow-dispatch artifact, not binspect
release evidence, and would fail binspect's release policy.

Contract sources: [pinned signing action](https://github.com/actions/attest/tree/1e69f48acb82d1966a394da916b4c1698aa569d6),
[GitHub CLI verification and certificate/predicate trust boundary](https://cli.github.com/manual/gh_attestation_verify),
and [Sigstore certificate extension schema](https://github.com/sigstore/sigstore-go/blob/main/pkg/fulcio/certificate/extensions.go).

This signs already qualified bytes later in the same release workflow; it does
not isolate the builder or establish a SLSA level. Runner-supplied `gh` is recorded
rather than pinned by the Python lock. Actual candidate signing, service/retention
behavior, PyPI controls and maintainer acceptance remain unverified. Release-only
jobs cannot be exercised by routine PR CI. No new attestation, release event,
publication, settings change or approval has been performed.
