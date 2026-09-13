# P3 — exact-artifact license review preparation

Owner: Josh Myers. Implementer: Codex. License decisions remain pending.
Baseline: `af4972c`, draft #28. Branch: `docs/license-review-dossier`.

## Contract before iteration

Prepare concrete evidence for the six pending license decisions using locked
upstream artifact hashes, packaged license/notice members, dependency paths and
the contents/metadata of the inspected binspect development distributions. Make
the difference between default runtime, advertised extras, tooling groups and
bundled files explicit. Record review questions and choices without supplying
maintainer approval or a legal compatibility conclusion.

Three phases / 45 minutes: inspect exact archives and primary license sources;
prepare a compact dossier with reproducible identities; verify links, evidence
hashes and secret scan, then push a stacked draft PR. No source/workflow, dependency,
version, statistical seed/tolerance, Polars/pandas contract or license decision
changes. Documentation-only checks apply; do not claim a fresh `make check`.
Unexpected hashes, unsafe archives or contradictory scope block affected claims.
At the ceiling record missing evidence and owned decisions instead of inventing
approval. Do not install or execute downloaded packages, publish or change settings.

## Evidence and disposition

The [dossier](LICENSE_REVIEW_DOSSIER.md) and [controlled evidence](evidence/license-dossier-2026-09-12.json)
cover all six pending packages. Twelve upstream downloads match the exact committed
lock hashes. Regular license/notice members were read without installing packages
or executing build hooks. Docutils' six stylesheet links were inventoried but not
extracted or followed; the repository's artifact guards are unchanged.

Eight frozen profile exports distinguish default/pandas/validation use (none of
these six dependencies) from advertised extras and separate tooling groups. The
inspected binspect wheel/sdist match the prior audit's `a0a758f` hashes, advertise
dev/docs/dpi/pandas/validation extras, contain no matching upstream package
directories, and carry the unchanged binspect MIT license. These dated development
bytes do not qualify a release candidate or the published PyPI distribution.

Material review findings: Docutils ships the GPL Emacs helper in its source
archive but not its wheel, although both carry GPL license text. Fqdn's sdist
omits the wheel's MPL license file. Certifi and binsreg carry notices linking to
full license texts. Hypothesis allows file-specific third-party exceptions and
has 80 locked wheel variants; only the chosen arm64 wheel and source archive were
inspected here. No blanket artifact/version compatibility is inferred.

Sandbox download DNS failed; the authorized network retry succeeded. The read-only
inventory records Docutils' source links without following them and reads only
regular members. Production extraction guards were not relaxed for this inventory.

Verification passes: twelve archive hashes, nineteen notice/helper member hashes,
two binspect MIT notices and all recorded input hashes were rechecked. All eight
frozen profile exports completed. All 163 local Markdown links resolve; Ruff,
formatting and whitespace checks pass. The retained evidence directory passes
Gitleaks 8.30.1 after its cached archive/executable were checked against the
committed scanner pin. No scanner exclusion was added.

Only documentation/evidence changed. No source/workflow changed;
the full software gate is not rerun or claimed passed for this documentation slice.
All six registry decisions remain pending, with unchanged empty reviewer/date
fields. The dossier gives each reviewer a concrete scope question and disposition
choices; no license, dependency, version, repository setting or approval changed.
