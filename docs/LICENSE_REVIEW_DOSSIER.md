# Six license decisions: exact artifacts and distribution scope

Prepared for Josh Myers; **all six exact-version scopes were accepted by Josh
Myers on 2026-09-13** in the
[registry](../validation/supply-chain-exceptions.json), with review expiry
2026-10-13. This dossier supplies the artifact evidence and accepted scope. The
approvals do not authorize broader dependency-environment redistribution or a
binspect release.
The [verification record](license-dossier-review.md) defines its bounded scope.

## What the inspected binspect artifacts distribute

The inspected development wheel and sdist come from `a0a758f`, declare 0.1.1,
and match the preceding audit's recorded hashes. They are not the PyPI 0.1.1
files or a selected 0.2.0 candidate. [Machine-readable evidence](evidence/license-dossier-2026-09-12.json)
contains their full identities, metadata and the twelve inspected upstream archive
identities, including every selected license/notice member's hash and size.

Neither binspect archive contains package directories for the six dependencies.
They advertise **dev, docs, dpi, pandas and validation** extras in distribution
metadata. The package's MIT license does not establish the terms for separately
installed dependencies or combined use. Directory inventory also cannot rule out
renamed/copied fragments; this is not a whole-code copyright audit.

The following membership comes from eight frozen universal requirement exports.
It describes the committed lock, not all future versions allowed by the published
requirements, nor every platform-specific installed environment. None of these six
packages occurs in the runtime-only, pandas or validation profile exports.

| Package | Advertised extra containing it | Repository tooling group | Illustrative locked dependency path |
|---|---|---|---|
| binsreg 3.2.1 | dpi | — | binspect[dpi] → binsreg |
| certifi 2026.7.22 | docs | build, audit | mkdocs-material / twine / pip-audit → requests → certifi |
| docutils 0.23 | — | build | twine → readme-renderer → docutils |
| fqdn 1.5.1 | — | audit | cyclonedx-python-lib[validation] → jsonschema[format-nongpl] → fqdn |
| hypothesis 6.165.10 | dev | — | binspect[dev] → hypothesis |
| pathspec 1.1.1 | dev, docs | build | mypy / mkdocs / hatchling → pathspec |

Consequently, describing certifi, hypothesis or pathspec as *only internal tooling*
would miss an advertised installation path. Conversely, dependency declarations
are not evidence that those upstream packages are embedded in binspect's archives.

## Package evidence and accepted decisions

One wheel and the source archive were hash-checked against `uv.lock` for each
package. Five wheels are universal Python wheels. Hypothesis has 80 locked wheel
variants; this inspection covers its CPython 3.10+ stable-ABI macOS arm64 wheel and
sdist only. It does not inspect notices in the other 79 wheels or every embedded
native component. Recheck the actual selected release tooling/platform artifacts.

### binsreg 3.2.1

The wheel's `binsreg-3.2.1.dist-info/licenses/LICENSE.md` and the sdist's
`LICENSE.md` are byte-identical. They specify GNU GPL version 3 and link to the
full license; package metadata says `GPL-3.0-only`. The notice is 459 bytes, not
a bundled copy of the complete GPL. See the [versioned metadata](https://pypi.org/pypi/binsreg/3.2.1/json)
and exact archive/member hashes in the evidence.

**Accepted 2026-09-13:** use as a separately installed optional DPI/function
backend; no binsreg files are bundled in binspect artifacts. Binspect retains its
MIT license. Any redistribution of binsreg or a combined environment must preserve
applicable GPL license/source obligations and receive renewed review.

### certifi 2026.7.22

Both archives carry an identical 989-byte `LICENSE` notice describing the
Mozilla-derived CA certificate bundle and referencing MPL 2.0. This is a notice
with a license link rather than the full MPL text. Its current binspect paths are
the advertised docs extra and separate build/audit groups; the inspected binspect
archives do not carry a `certifi` package directory.

**Accepted 2026-09-13:** use as a separately installed docs/build/audit dependency;
no certifi files are bundled in binspect artifacts. Any redistribution of the
certificate bundle, environment, cache or image must retain applicable MPL
notice/source availability under
[MPL sections 3.1–3.4](https://www.mozilla.org/en-US/MPL/2.0/#3-responsibilities)
and receive renewed review.

### docutils 0.23

Both archives carry identical `COPYING.rst`, BSD-0-Clause and BSD-2-Clause texts,
and a GPL-3.0 text. The packaged copying document assigns terms by file and
describes BSD relicensing for certain formerly GPL components. The GPL Emacs
helper `tools/editors/emacs/rst.el` occurs in the sdist, **not the inspected wheel**;
the wheel still contains the GPL license text. Neither observation justifies
classifying every Docutils file as GPL or treating the source archive as the wheel.
The [current upstream copying page](https://docutils.sourceforge.io/COPYING.html)
is context; the hash-identified packaged document owns this version's evidence.

**Accepted 2026-09-13:** use as separately installed Twine/readme-renderer tooling;
no Docutils files are bundled in binspect artifacts. The GPL Emacs helper remains
sdist-only in the inspected pair. Redistributing Docutils artifacts or environments
must retain the applicable file-specific terms/notices and receive renewed review.
Six sdist stylesheet symlinks were inventoried without extraction or following
links; they do not affect the inspected regular license members.

### fqdn 1.5.1

The wheel contains a 16,725-byte `fqdn-1.5.1.dist-info/LICENSE` with MPL 2.0.
The exact sdist has no `LICENSE`, `COPYING` or `NOTICE` file; its metadata and
`setup.py` identify MPL 2.0. These are different artifact observations. No missing
license file was inserted into the archive, and no upstream approval was assumed.
The dependency is reached through the audit group's schema-validation extra.

**Accepted 2026-09-13:** use only as separately installed audit tooling; no fqdn
files are bundled in binspect artifacts. Prefer the inspected wheel when retaining
tooling. Redistribution, especially of the notice-incomplete sdist, requires
renewed source/notice review; do not substitute wheel contents for sdist evidence.

### hypothesis 6.165.10

The selected wheel and sdist contain identical 17,141-byte `LICENSE.txt` files.
They state MPL 2.0 as the general license and explicitly allow file-specific
third-party exceptions; wheel metadata declares MPL-2.0. The selected wheel is
platform-specific. This inventory does not establish the license composition of
every native wheel or all third-party code noted by the project.

**Accepted 2026-09-13:** use as a separately installed development-test dependency;
no Hypothesis files or test environment are bundled in binspect artifacts. Any
redistributed test environment must retain applicable MPL and file-specific
third-party notices and receive renewed artifact review.

### pathspec 1.1.1

Both archives carry an identical 16,726-byte MPL 2.0 `LICENSE`. The locked paths
include advertised dev/docs extras and Hatchling's build environment. A build
dependency is not automatically embedded in the resulting binspect wheel.

**Accepted 2026-09-13:** use as separately installed build/dev/docs tooling; no
pathspec files are bundled in binspect artifacts. Any redistribution of covered
files or tooling environments must retain applicable MPL notice/source availability
and receive renewed review.

Mozilla's [FAQ](https://www.mozilla.org/en-US/MPL/2.0/FAQ/) distinguishes use from
distribution and explains its file-based license scope. The exact license and
selected artifacts remain the inputs to a scoped decision; this dossier makes no
blanket compatibility finding for these packages.

## Recorded maintainer decision

For **each** package, Josh Myers accepted the explicitly described, separately
installed scope on 2026-09-13 through the 2026-10-13 review expiry. The accepted
obligations are:

- binspect wheel/sdist files do not bundle these dependency packages;
- upstream licenses and notices remain attached to separately installed artifacts;
- redistribution of dependency artifacts, caches, images or complete environments
  must meet applicable GPL/MPL/file-specific notice and source obligations; and
- version, artifact, distribution-scope or expiry changes require renewed review.

The registry records the reviewer, review date, scope, rationale, evidence and
expiry. These are scoped approvals, not a broad finding across every wheel or
future version; this twelve-archive inventory does not inspect every wheel. No
notice, dependency, scanner exclusion or project license was changed to pass CI.

## Reproduce the evidence

1. Check the recorded lock hash and exact `(package, version)` entries. Download
   the recorded wheel/sdist URLs and compare each SHA-256 with both evidence and
   lock. Do not execute build hooks to inspect an archive.
2. List members with a ZIP/TAR reader. Read the identified regular license/notice
   members and compare sizes/hashes. Do not extract or follow archive links.
3. Export each profile with `uv export --frozen --no-default-groups --no-emit-project
   --no-hashes --no-header --no-annotate`, adding `--extra NAME` for each extra or
   `--only-group NAME` for build/audit. Preserve any environment markers.
4. Inspect exact binspect candidate wheel/sdist metadata and contents again. The
   recorded development pair establishes a dated scope observation, not release
   authorization, a passing fresh audit or qualification of published files.
