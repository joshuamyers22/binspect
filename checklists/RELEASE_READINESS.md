# Release readiness evidence

Copy this form into a release-specific record. An unchecked item is unresolved;
this template itself is not qualification. Follow the [plan](../binspect-plan.md)
and [release procedure](../RELEASING.md). Use exact commits/artifact digests and
actual reviewer decisions. No release date or approval is supplied here.

- Version / exact commit:
- Accountable release owner / reviewer:
- Qualification date / evidence record:
- Supported Python, OS, dependency and method scope:
- Decision: pending / approved / rejected
- Accepted residual risks, owner, rationale and expiry (if any):

## Scope, correctness and compatibility

- [ ] G1 brief/ADR/repository agreement accepted; open decisions have owners.
- [ ] G2 [threat model](../docs/THREAT_MODEL.md) reviewed; security/support limits
  and a verified private reporting route are documented.
- [ ] C1–C4 supported statistical claims have reference evidence; C3 has a named
  qualified reviewer and final-assessment evidence distinct from tuning cases.
- [ ] A1–A3 ownership, validation, exports and compatibility contracts pass.
- [ ] D1–D3 examples, figures and public documentation match released behavior.
- [ ] P1–P2 capacity budgets and supported dependency/Python/OS matrix are measured.
- [ ] Changelog, version, limitations and migration notes match the release scope.

## Repository and artifacts

- [ ] Recheck actual [GitHub controls](../docs/GOVERNANCE.md); required checks,
  review/bypass rules and release-environment ref restrictions match approved policy.
- [ ] Required CI and `make check` pass on the exact release commit, including DPI.
- [ ] P3 dependency/license/secret review, action pins and SBOM are complete.
- [ ] R1 locked build and tag/version/publisher-identity checks pass; PyPI Trusted
  Publisher mapping is independently inspected, not inferred from workflow YAML.
- [ ] R2 wheel/sdist contents, hashes, fresh installs, advertised extras and smoke
  journeys are checked across supported targets; provenance matches the artifacts.
- [ ] R3 failed-publish, yank/fixed-release and recovery procedures were exercised;
  owner, trigger and evidence retention for ongoing maintenance are recorded.
- [ ] Maintainer has explicitly authorized publication of these artifacts.

## After authorized publication

- [ ] Verify index identity, artifact hashes, metadata and clean install behavior.
- [ ] Record release URL, evidence and remaining owned follow-up work.
- [ ] Update plan/memory where durable facts changed; review/delete stale notes.

Known supported-method correctness, security or artifact-integrity gaps block
qualification until corrected or the affected claim is withdrawn. A waiver needs
an explicit reviewer decision and expiry; the implementing agent cannot supply it.
