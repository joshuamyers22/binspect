# R3 — maintenance and recovery preparation

- Owner: Josh Myers; implementer: Codex; maintainer acceptance pending.
- Baseline: R1 `16e4b28`, draft PR #25; 2026-09-12 local date.
- Branch: `chore/maintenance-recovery`; status: implemented; maintainer acceptance/activation pending.

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

| Implementation | `5a6de08`, recovery guard `742ea4a`; [draft PR #26](https://github.com/joshuamyers22/binspect/pull/26) | Weekly/manual read-only runner, 25 failure/recovery regressions, preserved numerical references and a read-only recovery checker implemented. Fresh-current P2 monitoring moves to the schedule; nine locked/floor PR jobs remain. |
| Installed maintenance probes | [Retained profiles, versions and stage logs](evidence/maintenance-recovery-2026-09-12.json) | Locked Python 3.12.11 and current Python 3.12.11/3.13.15 each pass all 74 existing references and the installed Polars/pandas/DPI journey: 222 reference cases, zero skips. Current NumPy 2.5.3 passes versus locked 2.5.2; the committed lock is unchanged. |
| Recovery exercise | Same retained record; R1 manifest identity independently checked | Ten CLI scenarios pass: empty, partial, complete, conflicting hash, extra file, yanked, known defect, unavailable index, changed manifest and malformed file collection. Rejected input leaves no stale successful decision. No index mutation or publication occurs. |
| Full local gate | `make check` after recovery guard | 526 unit + 34 DPI + 40 reference tests (600), 94.65% coverage, strict mypy on 38 source files, four import contracts, all development simulations, 38 docs blocks plus quickstart, strict site build, four figures at RMS 0.0 and wheel/sdist build pass. Reserved assessments unrun. |
| Remote implementation CI | [Run 34732623859](https://github.com/joshuamyers22/binspect/actions/runs/34732623859), head `5a6de08` | Completed failed: the six existing license reviews and unavailable Python 3.12.14 arm64 in the figure job. Every other job passed, including nine P2 configurations and all R1 artifact consumers. This run predates the recovery-only guard. |
| Security/evidence review | Pinned Gitleaks 8.30.1 `git --all --full-history`; final retained-evidence scan | History scan reports 88 commits with no findings using existing exact exclusions. No new scanner exclusion, dependency/lock/runtime change or sensitive log retention. Remote audit passes all nonlicense checks. |

## Evidence identity and limits

The three probes ran at `5a6de0874d74288c1a92658dacf09c7c623fbbd8`.
After the recovery-only guard at `742ea4a643d86ccb2cf27dea16d2bb1f8026201c`, every
recorded runtime, test, runner and lock fingerprint still matched, so those probes
were retained without repeating unchanged comparisons. The ten recovery CLI cases
and final full gate use that guard revision; two documentation wording edits made
during the gate are recorded explicitly. A later evidence-only commit is not a
maintenance wheel build input.

Review found that an empty object could be mistaken for an empty index file list.
The checker now rejects non-list file collections; four additional regressions and
the malformed-index CLI scenario pass. The initial 596-test full gate was followed
by the final 600-test gate after this material change. Initial sandbox resolution
failures returned unverified stage evidence; approved network retries passed.

The exercise is a local reconciliation simulation using synthetic index states and
the preserved R1 artifact manifest. R1 supplies actual clean reinstalls of that pair.
No real failed upload, yank/unyank, partial OIDC retry, consumer version downgrade
or published fixed release was performed. PyPI operator permissions and the recovery
readiness checkbox remain unqualified; the runbook spells out the required separate
operator evidence and authorization. Checksums are not publisher authentication.

The scheduled workflow has no PR trigger, publication/OIDC permission, issue-writing
permission or automatic message sender. Its metadata names Josh Myers for triage;
that is an ownership record, not an issue assignment or independent approval.
GitHub schedule activation, requested 90-day artifact retention and the first manual
and scheduled runs must be verified after integration into the default branch.
They were not executed remotely from this draft branch. Local probes do not prove
future service availability, general dependency qualification or statistical coverage.

## Disposition

R3 implementation, local maintenance comparisons and simulated recovery decisions
are ready for maintainer review. Policy acceptance, integration/schedule activation,
actual operator recovery evidence, P3 license reviews and R1 renderer/control/publisher
gaps remain open. No merge, publish, yank, settings change or waiver was performed.
Next phase is R2 readiness/evidence review; publication remains blocked by the
outstanding acceptance and qualification gates.
