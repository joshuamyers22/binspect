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

## Signed release provenance

After the release build, installation matrix and audit succeed, a separate
`provenance` job verifies the same artifact-ID handoff and uses the full-SHA-pinned
[`actions/attest` action](https://github.com/actions/attest/tree/1e69f48acb82d1966a394da916b4c1698aa569d6)
to sign both distribution digests. Only that job receives `attestations: write`
and signing OIDC permissions. It does not enter the `pypi` environment. The R1
build/installation workflow remains read-only. This is provenance issued after
qualification within the release run, not an isolated-builder or SLSA level claim.

The job retains `attestation.json` and a controlled verification summary as the
`release-provenance` Actions artifact (requested retention: 90 days); the signing
action also registers the attestation with GitHub. The publisher downloads by the
returned immutable artifact ID and reruns [the verifier](validation/provenance.py)
against the signed bundle and both distributions. It never trusts the downloaded
summary as proof. The existing independently supplied manifest hash is still
required. Attestation files are kept outside the publisher's distribution folder.

[GitHub CLI verification](https://cli.github.com/manual/gh_attestation_verify)
checks signatures, artifact digests, GitHub OIDC issuer, repository, exact workflow
certificate identity, source/signer commit and tag ref, and rejects self-hosted
runners. Additional policy checks the authenticated certificate's release trigger
and run-attempt URI, the exact two subjects, and matching workflow/source/run
claims. Parsing arbitrary bundle JSON does not authenticate it. No result is
emitted until both artifacts and a final integrity recheck pass. Missing tooling,
network/trust-service errors and unsupported output schemas block publication.
The controlled report records the runner's actual `gh` version; it is supplied by
the GitHub-hosted runner, not a frozen Python dependency.

To reverify retained evidence from the exact candidate checkout, supply identities
from the independently reviewed release record, not from the downloaded summary:

```bash
python validation/provenance.py --bundle .work/artifact-bundle \
  --manifest-sha256 <reviewed-manifest-sha256> \
  --attestation .work/provenance/attestation.json \
  --source <reviewed-40-character-commit> --ref refs/tags/<reviewed-tag> \
  --run-id <reviewed-run-id> --attempt <reviewed-attempt>
```

Preserve the signed bundle, manifest, distributions, matching SBOM/audit and
controlled result in the approved release evidence store before Actions retention
expires. Signed bundle verification can still need trust-root network access;
this command does not claim fully offline operation. A publish-only rerun has a
new attempt and deliberately rejects earlier-attempt signatures. Reconcile index
state through the recovery procedure before authorizing a new full release run;
never weaken the attempt check to retry a potentially partial publication.

This automation has fixture-based rejection tests; actual candidate signing and
verification remain a release gate. See [scope and evidence](docs/release-provenance-review.md).
Neither a valid signature nor workflow execution establishes statistical, license,
maintainer or publisher-configuration acceptance.

## Failed publication and recovery

Stop automatic retries when index state is ambiguous. Follow the
[maintenance and recovery procedure](docs/MAINTENANCE.md) to reconcile the original
artifact hashes, handle partial uploads, review a yank/fixed release and verify
consumer reinstalls. Never replace published bytes or reuse a deleted filename.
The read-only checker and synthetic exercise grant no publishing authority.
