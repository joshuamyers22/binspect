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
2. Update `CHANGELOG.md` and remove the development suffix from `__version__`.
3. Run the checks documented in `CONTRIBUTING.md` and inspect both distributions.
4. Commit the release changes and push `main`.
5. Create a GitHub release whose tag exactly matches `v{__version__}`.
6. Approve the protected `pypi` environment deployment when prompted.
7. Verify the new PyPI page and install the wheel into a fresh environment.

The workflow refuses to publish when the GitHub tag and package version differ.
