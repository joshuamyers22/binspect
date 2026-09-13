# R3 — maintenance and recovery preparation

- Owner: Josh Myers; implementer: Codex; maintainer acceptance pending.
- Baseline: R1 `16e4b28`, draft PR #25; 2026-09-12 local date.
- Branch: `chore/maintenance-recovery`; status: in progress.

## Contract before iteration

Document failed/partial publication, yanking, fixed releases, consumer recovery,
monthly drift triage and accountable ownership. Exercise recovery decisions locally
against synthetic index states and existing artifact hashes, without publishing,
yanking, deleting, changing repository settings or sending messages to others.
Never replace published bytes or infer that a missing index response means absent.

Run the existing 74 reference/integration cases against locked and current upstream
dependencies in fresh installed environments. Keep test inputs, tolerances and
reserved assessment seeds unchanged. The scheduled/manual workflow must preserve
controlled stage logs, dependency versions and findings assigned to Josh for triage;
it must not be a routine PR requirement or convert outages/missing tests into a pass.
Any supported-method numerical divergence blocks its next release pending resolution
or explicit withdrawal. No new runtime network access or telemetry is in scope.

Four phases / 90 minutes: implement workflow/runner and failure regressions; write
and exercise recovery procedures; run locked/current probes and required `make check`;
review diff, retain evidence, push stacked draft PR and update plan/memory. Block
High findings: false passes, changed numerical conventions, editable/source imports,
publish or overwrite routes, leaked sensitive logs and fabricated approvals. Missing
remote scheduler or maintainer acceptance remains explicit. Stop at the ceiling with
actual evidence; do not waive P3/R1 gaps or move to R2 publication without approval.

## Evidence ledger

| Phase | Evidence | Result |
|---|---|---|
| Baseline | Existing R1 artifact checks, release runbook and 74 independent/reference tests | No recovery reconciliation tool or scheduled current-versus-locked reference runner. R1/P3 license, renderer and control gaps remain open. |

## Disposition

Implementation and verification in progress. Policy acceptance, deployment controls
and release authorization remain with the maintainer.
