# R1 — artifact and workflow qualification without publishing

- Owner: Josh Myers; implementer: Codex; maintainer acceptance pending.
- Baseline: P3 `2863e6d`, draft PR #24; 2026-09-12 local date.
- Branch: `test/artifact-workflow-qualification`; status: implemented; qualification gaps remain.

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

| Implementation | `0c3fb1e`; [draft PR #25](https://github.com/joshuamyers22/binspect/pull/25); 21 rejection/identity regressions | Shared build/install workflow, exact tag guard and independent manifest verification implemented. Runtime/source/version/defaults unchanged. |
| Local qualification | [Retained manifests and install records](evidence/artifact-workflow-2026-09-12.json) | One clean committed pair; wheel and sdist pass native Python 3.10.21, 3.11.16, 3.12.11 and 3.13.15, plus pandas and DPI on 3.12.11: 12 installs on macOS arm64. |
| Remote handoff | [CI run 34731681077](https://github.com/joshuamyers22/binspect/actions/runs/34731681077) | Producer and all 12 consumer jobs pass: 24 clean wheel/sdist installs across Linux/macOS Python 3.10–3.13 and the optional profiles. Actual upload/download verified; no publishing path executed. |
| Full local gates | `make check` on stable implementation commit | 501 unit + 34 DPI + 40 reference tests (575), coverage 94.65%, strict mypy (38 files), four import contracts, all development simulations, 38 documentation blocks plus quickstart, strict docs, four figures at RMS 0.0 and build pass. Reserved assessments remain unrun. |
| Exact artifact audit | [Report](evidence/artifact-supply-chain-2026-09-12.json), [compressed license metadata](evidence/artifact-licenses-2026-09-12.json.gz), [validated compressed CycloneDX](evidence/artifact-sbom-2026-09-12.cdx.json.gz) | Actions, all 153 locked-version vulnerability checks, artifact contents, history/working/artifact secrets and SBOM pass. Six pending license reviews fail the overall gate; CI has the same audit disposition. |
| Actual controls | Read-only authenticated GitHub API; summarized in retained record and [governance](GOVERNANCE.md) | Main unprotected, no rulesets; PyPI requires Josh's review but permits self-review and has no deployment ref restrictions. Actions allow all refs; private reporting disabled. Owner-side PyPI Trusted Publisher mapping unverified. No settings changed. |

## Evidence identity and limitations

The retained local pair was built from clean commit
`0c3fb1ecbab26c0f136689df2714d4f740505022`. CI checked out PR merge revision
`f0a357297fcb030b33112e0e6eadc356789e0c55`; that distinction is recorded in each
manifest. The wheel and sdist bytes match between these local and CI producers.
Every installation report's manifest/source/artifact hashes were checked against
the downloaded pair before retention. A later evidence-only commit is not the
build input. Checksums establish integrity, not authenticated publisher provenance.

The complete remote CI run is **failed**, despite the artifact workflow passing:
P3's six license reviews remain pending, and the existing figure job cannot obtain
Python 3.12.14 arm64 for macOS 15.7.9 from `setup-python`. Its image comparison did
not run. The local recorded renderer passes; no baseline or tolerance was changed.
The maintainer must qualify an available controlled renderer before treating that
remote gate as satisfied. This is an observed availability gap, not a pixel mismatch.

An earlier local simulation rejected evidence when the implementation commit
changed during execution. The full gate was rerun successfully with the revision
held stable; the rejected run and preliminary dirty-tree builds are not retained
as qualification. Build now rejects uncommitted inputs. Initial sandbox DNS
failures were retried with network approval using the same hash-locked inputs.

The retained audit report represents input digests as separate path/SHA-256
records: filenames containing `api` or `secret` otherwise triggered the generic
credential rule. Each digest was verified against its source file; the original
report digest and the format change are recorded. Audit findings are unchanged.
The retained evidence passes the pinned scanner with no new exclusions.

Workflow mechanics follow the official [reusable-workflow documentation](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows)
and [artifact-ID download contract](https://github.com/actions/download-artifact).
The shared workflow has only `contents: read`; release's separate publisher
requires all qualification/audit jobs and the `pypi` environment, then checks the
same bundle immediately before publishing.

## Disposition

R1 implementation and artifact-handoff testing are complete; maintainer acceptance,
repository/Trusted Publisher controls, renderer availability and P3 license review
remain open. The overall CI run is not green and this is not release qualification.
Next implementation is R3 maintenance/recovery preparation, before R2 publication.
No release, merge, publication, waiver or repository-setting change was performed.

## 2026-09-13 integration follow-up

A main-based review of draft #30 found that the artifact checker enforced package
source identity but did not enforce its documented full-sdist manifest claim, and
did not tie wheel/sdist dependency, extra, Python and license metadata back to
`pyproject.toml` and `LICENSE`. The integrated branch now rejects a missing, extra,
outside-prefix or byte-altered tracked sdist member and altered dependency, extra
or license metadata. Seven new regressions cover these cases. Fresh locally built
wheel and sdist files pass the strengthened checker.

The required full gate passes with 565 unit tests, 34 DPI integrations and 40
reference tests (639 total), 94.65% coverage, type/import contracts, all development
simulations, executable/strict documentation, four RMS-0.0 figure comparisons and
builds. A fresh online supply-chain run passes action, vulnerability, artifact,
secret and SBOM checks; it still fails only on the six owner-held pending license
decisions. [CI run 34781858587](https://github.com/joshuamyers22/binspect/actions/runs/34781858587)
on exact fix commit `efb6e34` has 34 passing jobs, including the strengthened
artifact build and all 12 install jobs; supply-chain again fails only at licensing
while its other five checks pass. This follow-up hardens implementation readiness
but does not supply license, integration or release acceptance.

Josh Myers subsequently accepted the six exact separately installed/non-bundled
license scopes on 2026-09-13 through 2026-10-13. A fresh online supply-chain run
passes all six stages, including the strengthened artifact verifier. This removes
the P3 license blocker but does not supply candidate-specific artifact/provenance,
publisher-control or release approval.
