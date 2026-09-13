# Releasing

Releases use PyPI Trusted Publishing. No long-lived PyPI token belongs in GitHub.
Use a release-specific [readiness record](checklists/RELEASE_READINESS.md) before
publication. The steps below describe the existing publishing route; they do not
establish that production qualification or publisher setup has been completed.

## One-time PyPI setup

Create a pending trusted publisher for the `binspect-regression` distribution with:

- PyPI project name: `binspect-regression`
- GitHub owner: `joshuamyers22`
- GitHub repository: `binspect`
- Workflow filename: `release.yml`
- Environment: `pypi`

The publisher must be configured before publishing the first GitHub release.
Its actual PyPI mapping has not been verified in the repository control audit.
On 2026-09-12 the GitHub `pypi` environment required Josh Myers's review but had no
deployment branch/tag restriction, and `main` had no protection or rulesets.
See [governance](docs/GOVERNANCE.md) for observations and proposed R1 controls.

## Release checklist

1. Complete the readiness record and obtain release authorization; ensure CI passes
   on the exact `main` commit and the working tree is clean.
2. Set the chosen release version in `__version__` and update `CHANGELOG.md`.
   The current value is 0.1.1 with no development suffix; the proposed 0.2.0
   allocation still requires acceptance and release qualification.
3. Run the checks documented in `CONTRIBUTING.md` and inspect both distributions.
   Require a fresh passing [supply-chain report](docs/SUPPLY_CHAIN.md) for their
   exact digests. Six license reviews currently block that gate; pending registry
   entries are not approvals. The workflow builds with locked tools, audits the
   same qualified artifact pair, retains controlled evidence, and only then hands
   those distributions to the publisher. See the nonpublishing qualification path
   below; actual repository controls and Trusted Publisher acceptance remain open.
4. Commit the release changes and push `main`.
5. Create a GitHub release whose tag exactly matches `v{__version__}`.
6. Approve the protected `pypi` environment deployment when prompted.
7. Verify the new PyPI page and install the wheel into a fresh environment.

The workflow refuses to publish when the GitHub tag and package version differ.
Its trigger is a **published GitHub release**; pushing a tag alone does not publish
the package. Documentation builds are a separate CI job and do not deploy a site.
Site publication requires configured hosting, a strict passing build and explicit
maintainer authorization; D1 adds no deployment credentials or publishing workflow.

## Nonpublishing artifact qualification

CI calls [the reusable artifact workflow](.github/workflows/artifacts.yml); release
preparation calls that same workflow with the expected release tag. A clean
committed checkout produces one wheel/sdist pair using frozen build-group tools
and `--no-isolation`, checks metadata and source contents, then uploads a manifest
and distributions. Consumers download by artifact ID and verify an independently
passed manifest SHA-256, source revision, lock, journey and each file's size/hash.
Missing, changed, extra or linked artifacts fail before installation. The manifest
is integrity evidence; it is not authenticated publisher provenance.

The consumer matrix exercises both artifacts on Linux/macOS Python 3.10–3.13 with
runtime-only dependencies, plus pandas and DPI profiles on Python 3.12. Each
artifact gets a fresh environment outside checkout. Sdist builds use a separate
build environment with hash-locked requirements and `--no-isolation`; the resulting
wheel is inspected against source and installed without dependency resolution.
The seeded installed-code journey checks estimation, Polars tables, JSON/evidence,
plots, optional pandas conversion and DPI. Native installs assert pandas is absent.

To reproduce locally from a clean commit, choose an unused bundle directory:

```bash
uv run --isolated --frozen --group build python validation/artifacts.py build \
  --bundle .work/artifact-bundle
# Copy the printed manifest_sha256 value; keep it independent of the download.
uv run --isolated --frozen --group build python validation/artifacts.py install \
  --bundle .work/artifact-bundle --manifest-sha256 <recorded-sha256> \
  --python 3.12 --profile native --output .work/artifact-native.json
```

Repeat installs with `--profile pandas` and `--profile dpi` as applicable. The
rehearsal has read-only repository permissions, no publishing job, environment or
OIDC permission. Release audits the same qualified pair and verifies the manifest
again immediately before the publisher. A failed license gate still blocks it.
See [R1 evidence and outstanding controls](docs/artifact-workflow-review.md).

## Failed publication and recovery

Stop automatic retries when index state is ambiguous. Follow the
[maintenance and recovery procedure](docs/MAINTENANCE.md) to reconcile the original
artifact hashes, handle partial uploads, review a yank/fixed release and verify
consumer reinstalls. Never replace published bytes or reuse a deleted filename.
The read-only checker and synthetic exercise grant no publishing authority.
