# Maintenance and recovery

Proposed R3 procedure; accountable owner: Josh Myers. Maintainer acceptance remains
pending. This document authorizes no publication, yank, deletion, settings change
or user notification. Follow [release readiness](../checklists/RELEASE_READINESS.md)
and [releasing](../RELEASING.md) for every actual release action.

## Routine checks and triage

The [maintenance workflow](../.github/workflows/maintenance.yml) runs weekly on
Monday at 07:23 UTC and supports manual dispatch. It compares the same 74 committed
reference tests in fresh installed environments with locked dependencies and
current compatible dependencies. Current probes resolve stable runtime/pandas/DPI
packages plus Statsmodels and pytest; they intentionally omit the validation extra's
Statsmodels pin. Build tools remain frozen. No lockfile is rewritten.

The current probes also run the existing installed dependency journey, covering
Polars tables, explicit pandas conversion, JSON, adjustment, grouping and plotting.
Python 3.12 compares locked/current references; current Python 3.13 retains P2's
fresh dependency journey. The nine locked/floor P2 configurations and the required
locked statistical CI gates continue on PRs; fresh-current monitoring moves here.
This workflow has no PR trigger and must not become a required PR check. Outages
fail the maintenance run as unverified, rather than passing or changing tolerances.

Josh reviews failed runs at the next maintenance session and before any affected
release, and reviews trends monthly even when runs pass. This is a proposed cadence,
not a staffed response-time promise. The workflow records Josh as triage owner; it
does not open issues, assign collaborators or send messages automatically. If Josh
is unavailable, publication waits until an explicitly designated maintainer accepts
responsibility. There is no implicit backup or automatic release authority.

The workflow requests 90-day retention for `result.json` and `stages.jsonl`: source/test/lock hashes,
wheel identity, actual dependency versions, test counts, failed test identifiers,
stage exit codes and timings. Raw subprocess output, traceback payloads, environment
variables and caller data are excluded. Missing/truncated reports, skipped or missing
tests, timeouts and dependency-resolution failures cannot pass. Record a sanitized
issue/work note before artifact expiry for any unresolved finding; promote durable
findings into tests, the plan and project memory. Preserve the run URL, UTC date,
profile, versions, failure identifiers, owner, next action and review due gate.

| Observation | Owner's next action | Release consequence |
|---|---|---|
| Resolution/service/runner unavailable | Check index and runner status, retry the unchanged probe, retain both dispositions. Compare with the locked run. | Unverified evidence cannot qualify a release; no numerical divergence is inferred from an outage. |
| Current fails, locked passes | Reproduce the failing test with exact recorded versions; read upstream changes and separate API/contract drift from a changed numerical target. | Any numerical correctness divergence affecting a supported method blocks its next release until resolved or explicitly withdrawn. An API drift failure also needs disposition before claiming that dependency support. |
| Locked fails too | Reproduce the existing reference in the committed environment; investigate source/runner drift. | Required locked correctness gates remain blocking. Never discard failing cases or widen tolerances. |
| Both pass | Review version changes and upstream scope, then run affected P2/P3/R1 gates before accepting an update. | Arithmetic parity alone does not qualify a new binsreg version, coverage, license compatibility or all admitted dependency combinations. |
| Repeated user/performance trend | Create a bounded [improvement plan](../templates/IMPROVEMENT_PLAN.md), with baseline/follow-up windows and guardrails. | Record improved, unchanged, regressed or inconclusive evidence; do not infer an improvement from a single report. |

Use the existing [statistical analysis plan](STATISTICAL_ANALYSIS_PLAN.md) for method
changes. Reserved assessment seeds remain unavailable for maintenance tuning.
Support reports should include a minimal synthetic reproduction, versions, method,
warning/status, and expected versus observed behavior. Do not request raw caller
data or add library telemetry. Follow [security reporting](../SECURITY.md) for
suspected exposure; the unverified private-reporting route remains an open control.

GitHub schedules execute the default branch and may be delayed or disabled after
inactivity. This draft branch has no active scheduled deployment. After integration,
Josh verifies the workflow is enabled, manually runs it, checks all three configurations and
actual retention, then records the first scheduled run. See [GitHub's schedule semantics](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule).

Local reproduction (online resolution; output contains controlled evidence):

```sh
uv run --isolated --frozen --group build python validation/maintenance.py \
  --profile locked --python 3.12 --output .work/maintenance/locked
uv run --isolated --frozen --group build python validation/maintenance.py \
  --profile current --python 3.12 --output .work/maintenance/current
```

## Failed or ambiguous publication

1. Stop retries. Preserve the exact reviewed commit, R1 bundle, independently
   recorded manifest hash, run URL and completed publisher steps. Do not rebuild
   under the same version to work around an upload error, change the tag, disable
   the audit, introduce a long-lived token, or enable blanket `skip-existing`.
2. Inspect the release-specific index response and download observed files to a
   temporary directory for independent digest verification. An outage, permission
   error, missing response or empty/deleted release is not proof a filename is free.
   PyPI's [release JSON API](https://docs.pypi.org/api/json/#get-a-release) exposes
   filenames, hashes and yank state; metadata alone does not prove actual file bytes
   or publisher authenticity. Record observation time and index identity.
3. Compare those observations with the original reviewed pair using the read-only
   [recovery checker](../validation/recovery.py). It requires the independent
   manifest digest and complete release-specific JSON. It performs no network or
   publishing calls and grants no authorization.

```sh
python validation/recovery.py --manifest .work/reviewed/manifest.json \
  --manifest-sha256 <independently-recorded-sha256> \
  --index .work/release-index.json --output .work/recovery-decision.json
```

| Observed state | Recovery decision for explicit maintainer review |
|---|---|
| No files observed | Verify project/version history, actual file availability and original release authorization. Only then consider retrying the exact original pair; a deleted filename cannot be reused. |
| One matching file present | Preserve it. Verify the missing original file and authorizations. Review a narrowly scoped OIDC workflow to upload only that missing file, or choose a new fixed version. The current release workflow does not implement this partial-retry action. |
| Both files match | Do not reupload. Verify published installs and complete post-release evidence; a failed CI step may have followed a successful upload. |
| Conflicting hash or unexpected file | Stop. Investigate integrity/identity; do not overwrite or delete to retry. A corrected build requires a new version and full release qualification. |
| Yanked file/release | Keep the yank in place while reviewing a fixed version. Do not silently unyank or finish uploading an affected release. |
| Known defect | Withhold unpublished artifacts. If files are already published, review a yank and a fixed release even when hashes match perfectly. Use `--known-defect` to record this distinction. |

PyPI forbids reuse of an already used distribution filename, including after its
file is deleted. The project additionally requires a new version for changed
published content. See [PyPI's filename-reuse policy](https://pypi.org/help/#file-name-reuse).
Publication remains a maintainer action through reviewed Trusted Publishing and
the applicable environment. A recovery decision JSON is never a publish grant.

## Yank, fix and consumer recovery

For a broken, incompatible or insecure release, Josh reviews affected versions,
methods, user impact, a known-good alternative and the proposed public reason.
With explicit authorization, use the PyPI project's release-management page,
select that release's **Options → Yank**, and enter the reviewed reason. Verify the
release-specific index marks it yanked and retains the expected file hashes. Keep
original artifacts and incident evidence. Do not delete the release as a rollback.

PyPI currently yanks whole releases. Exact `==`/`===` pins may still install a yanked
release, so a yank does not repair existing environments or guarantee every resolver
avoids the version. These mechanics and limitations follow [PyPI's yank documentation](https://docs.pypi.org/project-management/yanking/).
Any user notice needs separate authorization and should explain affected versions,
known limits and a concrete migration without caller data.

Prepare the fix in a new version with a regression reproducing the defect. Review
version/changelog/support scope together, rerun the required statistical, dependency,
artifact, supply-chain and release gates, obtain authorization, then publish through
the normal route. A numerical failure must be fixed or the affected method withdrawn;
a passing unrelated test or an upstream claim does not settle it.

Consumers recover in a fresh environment from an explicitly chosen known-good
version and recorded dependency constraints/hashes, verify installed versions and
run the affected synthetic journey. Do not automatically label the preceding version
safe. For Polars-native development behavior, older published versions may have
different table/API contracts: use the [compatibility guide](COMPATIBILITY.md).
Retain the original environment long enough to reproduce the incident and compare
results. A package downgrade cannot undo outputs or downstream analyses already
produced; the consuming application owner decides which results require rerunning.

## Exercises and acceptance

The R3 exercise uses synthetic release-index states and the R1 artifact manifest:
empty, partial, complete, conflicting, extra-file, yanked and known-defect cases,
plus malformed evidence. It verifies decisions and rejection without uploading or
yanking. R1 supplies actual clean reinstall evidence for the preserved pair. This
does not exercise PyPI permissions, real yank behavior, partial OIDC retry or a
published fixed release. Those need explicit authorization and release-specific
operator evidence before closing the corresponding readiness item.

See [R3 implementation/evidence](maintenance-recovery-review.md). Josh owns the
license review expiry/scope, actual branch/PyPI controls, publisher mapping and the
unavailable pinned CI figure renderer from R1. Recovery preparation does not waive
those gates or authorize R2 publication.
