# Supply-chain checks and license review

P3 adds a blocking `make supply-chain` gate. Josh Myers accepted the six exact,
scoped license decisions on 2026-09-13; the resulting local gate passes. The
approvals apply to the documented PyPI scope in which dependencies are installed
separately and are not bundled in binspect distributions. They are not blanket
compatibility findings or permission to redistribute dependency environments
without their applicable notice/source obligations. The project remains MIT,
Polars remains native/default, and pandas compatibility remains available.

## Run and inspect

```sh
uv sync --frozen --all-extras
make supply-chain
```

The target creates an isolated locked environment with the build and audit groups.
It needs PyPI advisory/metadata access and the official Gitleaks release download.
It writes controlled results to `.work/supply-chain/result.json`, all package
license metadata to `licenses.json`, and a validated CycloneDX 1.5 graph to
`sbom.cdx.json`. Locally built, inspected distributions remain under `artifacts/`.
No old result, license report or SBOM can stand in for a failed rerun.

The release workflow calls the same checker with `--artifacts dist`: those exact
wheel/sdist files are inspected before the existing artifact handoff and publisher
job. It does not rebuild them during the audit. P3 does not publish a release;
R1 still exercises nonpublishing handoff/tag checks and actual publisher controls,
and R2 still requires explicit release authorization and provenance qualification.

## Coverage and failure behavior

| Check | Scope and rejection conditions |
|---|---|
| Advisory audit | Every registry name/version in `uv.lock`, including alternate Python/platform versions and runtime, pandas/DPI, dev/docs, build and audit tools. Separate unique-name batches prevent pip-audit from rejecting or deduplicating alternate versions. Inventory must match exactly; skipped packages, service failures and missing results are unverified and fail. |
| License screening | Version-specific PyPI expressions/classifiers, with short valid SPDX legacy fields as fallback. Known permissive identifiers/families receive a metadata-screen pass; other/unknown terms require a recorded review. This does not inspect every vendored notice in every upstream binary. |
| Build/artifact identity | Hatchling 1.32.0, build 1.6.1 and Twine 7.0.0 are locked. No isolated backend re-resolution occurs in the audited build. Exactly one wheel and sdist must pass metadata checks; names, versions, declared dependencies/extras, classifiers, Python requirement and license match the project. Library bytes (including `py.typed`) match the checkout, and the sdist contains exactly `PKG-INFO` plus every tracked file with identical bytes. Unsafe links/traversal, duplicate members and oversized archives fail. |
| Secret scan | Gitleaks 8.30.1 archive checksums are pinned for Linux/macOS x64/arm64. A generated synthetic GitHub-token canary must be detected. Full available Git history (`--all --full-history`), tracked working files and extracted distributions are scanned. Shallow history is rejected. Findings retain only rule/file/line/commit; raw matches, secrets, authors and messages are not published. |
| SBOM | uv 0.12.5 exports the complete locked graph, including alternate versions and hashes. The checker adds license evidence and actual artifact SHA-256 identities, checks exact package coverage, and validates against CycloneDX 1.5. Dependency components describe separately installed packages; they are not a claim that binspect vendors them. |
| Workflow references | Every third-party `uses:` reference in repository workflow YAML must have a full commit SHA. The publisher uses signed v1.14.2's resolved commit and the gate checks that its reviewed Twine 7.0.0 supports the artifacts' Core Metadata 2.5. An unreviewed publisher pin or newer artifact metadata fails. Action pins are not an audit of every runner binary or the publisher container's entire operating-system supply chain. |

Pip-audit queries the [PyPI advisory service](https://github.com/pypa/pip-audit),
using pinned inputs with `--strict --no-deps --disable-pip`; it does not run an
unrequested resolver or automatically fix/ignore findings. A clean report means
no known advisories were reported for these versions at that time, not absence
of all vulnerabilities. License metadata queries are also live, without a stale
local result fallback. Registry package names/versions are sent; caller data is
never an input to this tooling.

Gitleaks uses its [default detection rules](https://github.com/gitleaks/gitleaks)
with recursive archive/decode depth 3. Pattern scanning cannot prove absence of
all secrets, especially opaque binary content or encodings beyond that depth.
Binary wheel/native dependencies are not recursively vulnerability-scanned here.
Full-history scope is all refs available in the checkout, not deleted remote refs
or unreachable objects. CI fetches complete history; repository settings and
private reporting remain the separately recorded governance work.

## Six approved scoped license decisions

[The exception registry](../validation/supply-chain-exceptions.json) records exact
package/version, owner and reviewer Josh Myers, 2026-09-13 review date, rationale,
evidence and a 2026-10-13 review expiry. All six entries are `approved` for the
scope below. Changed versions, expired entries or broader redistribution still
fail or require renewed review.

The [exact-artifact review dossier](LICENSE_REVIEW_DOSSIER.md) now supplies twelve
locked upstream archive identities, packaged notice hashes, eight dependency
profile exports and the inspected binspect distribution scope. In particular,
dev/docs are advertised extras; Docutils' source archive contains a GPL editor
helper absent from its wheel; fqdn's source archive omits the wheel's license file.
These observations supplied the artifact-specific basis for the scoped approvals;
they do not support a blanket finding for other artifacts or distribution models.

| Package/version | Observed terms / accepted scope |
|---|---|
| binsreg 3.2.1 | [GPL-3.0-only metadata](https://pypi.org/pypi/binsreg/3.2.1/json); accepted as a separately installed optional DPI/function backend. No backend files are bundled. Redistributed combined environments must preserve applicable GPL license/source obligations and be reviewed again. |
| certifi 2026.7.22 | MPL-2.0 certificate bundle accepted as a separately installed docs/build/audit dependency. Redistributing its covered files, an environment, cache or image requires applicable MPL notice/source availability and renewed review. |
| fqdn 1.5.1 | MPL-2.0 audit/schema-validation dependency accepted only as separately installed tooling. Prefer the inspected wheel; redistribution, particularly of the notice-incomplete sdist, requires renewed review. |
| hypothesis 6.165.10 | MPL-2.0 development test dependency accepted as separately installed tooling. A redistributed test environment must retain applicable MPL and third-party notices and be reviewed again. |
| pathspec 1.1.1 | MPL-2.0 build/development/docs dependency accepted as separately installed tooling. Redistributing covered files or environments requires applicable MPL notice/source availability and renewed review. |
| docutils 0.23 | Mixed public-domain/BSD/GPL metadata in Twine's rendering dependency, accepted as separately installed build tooling. Its [COPYING document](https://docutils.sourceforge.io/COPYING.html) distinguishes file-specific terms; the GPL Emacs helper is sdist-only in the inspected pair. Redistributing Docutils artifacts/environments requires retaining the applicable file-specific terms and renewed review. |

Mozilla describes MPL as [file-level copyleft](https://www.mozilla.org/en-US/MPL/2.0/FAQ/)
with distribution obligations. These entries call for scope review; no dependency
or project license has been changed to bypass it. A maintainer decision should
identify what is distributed, required notices/source availability, and any
restrictions on the supported integration. Do not equate optional installation
with a blanket license exemption.

Mypy-extensions 1.1.0 omits PyPI license metadata but ships an MIT license.
[Artifact evidence](../validation/license-evidence.json) identifies its exact
locked wheel/member/text hashes. The checker downloads and verifies those bytes;
changed metadata or hashes require reinspection. This resolves missing metadata,
rather than waiving a license finding.

A vulnerability or license exception only applies when exact package/version/finding
match, status is `approved`, owner/reviewer/rationale/evidence are populated, and
review/expiry dates include the check date. Approval is a maintainer record. Expired
or pending entries block the gate. The current vulnerability exception list is empty.

## Reviewed scanner false positives

Three historical findings were keys such as `src/binspect/api.py` followed by
source SHA-256 values. Each digest was verified against the corresponding source
bytes at its recorded commit. [The evidence](../validation/secret-fingerprints.json)
and [scanner configuration](../validation/gitleaks.toml) allow only those exact
key/value pairs in the two named evidence files. No API-key rule is disabled and
no broad path or history baseline is ignored. Inline `gitleaks:allow` comments and
external ignore files cannot suppress this gate. Future unrelated findings fail.

## Dependency updates and release evidence

Regenerate `uv.lock` whenever dependency inputs change. CI checks lock consistency
with `uv sync --locked --all-extras --all-groups`; it does not quietly repair a
stale lock. Every update still runs the existing unit/native, DPI/Statsmodels
references, development coverage simulations, documentation and figure checks.
Run `make check`, P2's affected dependency profiles and `make supply-chain` locally.
Do not relax numerical tolerances, reuse reserved assessment seeds or automatically
replace images to accept dependency drift.

CI and release jobs retain only the controlled result/license/SBOM files, including
on failure. Publication cannot proceed past a failed audit. Match the exact
artifact digests and source revision in a fresh report to the release-readiness
record; old local evidence is not approval for a future release. Review scope,
actual results and remaining gates are recorded in [the P3 review](supply-chain-review.md).
