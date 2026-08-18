# Releasing

Releases use PyPI Trusted Publishing. No long-lived PyPI token belongs in GitHub.

## One-time PyPI setup

Create a pending trusted publisher for the `binspect-regression` distribution with:

- PyPI project name: `binspect-regression`
- GitHub owner: `joshuamyers22`
- GitHub repository: `binspect`
- Workflow filename: `release.yml`
- Environment: `pypi`

The publisher must be configured before publishing the first GitHub release.

## Release checklist

1. Ensure CI passes on `main` and the working tree is clean.
2. Update `CHANGELOG.md` and remove the development suffix from `__version__`.
3. Run the checks documented in `CONTRIBUTING.md` and inspect both distributions.
4. Commit the release changes and push `main`.
5. Create a GitHub release whose tag exactly matches `v{__version__}`.
6. Approve the protected `pypi` environment deployment when prompted.
7. Verify the new PyPI page and install the wheel into a fresh environment.

The workflow refuses to publish when the GitHub tag and package version differ.
