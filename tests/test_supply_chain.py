"""Supply-chain checks must reject incomplete, unsafe or waived-by-default evidence."""

from __future__ import annotations

import importlib.util
import io
import json
import tarfile
import zipfile
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest

SPEC = importlib.util.spec_from_file_location(
    "supply_chain", Path(__file__).resolve().parents[1] / "validation/supply_chain.py"
)
assert SPEC is not None and SPEC.loader is not None
supply = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(supply)


def test_all_platform_versions_survive_audit_batches():
    pairs = {("numpy", "1.24.0"), ("numpy", "2.5.2"), ("polars", "1.44.2")}
    batches = supply.audit_batches(pairs)
    assert len(batches) == 2
    assert {pair for batch in batches for pair in batch.items()} == pairs


@pytest.mark.parametrize(
    "dependencies",
    [
        [],
        [{"name": "numpy", "version": "2.5.2", "skip_reason": "unavailable"}],
        [{"name": "numpy", "version": "2.5.3", "vulns": []}],
    ],
)
def test_missing_skipped_or_wrong_advisory_versions_fail(dependencies):
    with pytest.raises(ValueError):
        supply.validate_audit({"dependencies": dependencies}, {("numpy", "2.5.2")})


def test_known_vulnerability_is_retained():
    findings = supply.validate_audit(
        {
            "dependencies": [
                {
                    "name": "numpy",
                    "version": "2.5.2",
                    "vulns": [{"id": "TEST-advisory", "fix_versions": ["2.5.3"]}],
                }
            ]
        },
        {("numpy", "2.5.2")},
    )
    assert findings == [
        {
            "package": "numpy",
            "version": "2.5.2",
            "id": "TEST-advisory",
            "fix_versions": ["2.5.3"],
            "aliases": [],
        }
    ]


@pytest.mark.parametrize(
    "change",
    [
        {"status": "pending"},
        {"reviewer": ""},
        {"expires": "2026-09-11"},
        {"version": "2.5.3"},
        {"reviewed_at": "2026-09-14"},
        {"rationale": ""},
    ],
)
def test_exception_requires_exact_scope_actual_review_and_current_expiry(change):
    finding = {"package": "numpy", "version": "2.5.2", "id": "TEST-advisory"}
    entry = {
        **finding,
        "status": "approved",
        "owner": "test owner",
        "reviewer": "test reviewer",
        "rationale": "synthetic test",
        "evidence": "test fixture",
        "reviewed_at": "2026-09-12",
        "expires": "2026-10-12",
    }
    assert supply.approved(finding, [entry], date(2026, 9, 13))
    entry.update(change)
    assert not supply.approved(finding, [entry], date(2026, 9, 13))


@pytest.mark.parametrize(
    "member", ["../outside", "/outside", "x/../../outside", "x\\outside"]
)
def test_archive_traversal_rejected(tmp_path, member):
    artifact = tmp_path / "bad.whl"
    with zipfile.ZipFile(artifact, "w") as archive:
        archive.writestr(member, "synthetic")
    with pytest.raises(ValueError):
        supply.extract_artifact(artifact, tmp_path / "unpacked")
    assert not (tmp_path / "outside").exists()


def test_tar_symlink_and_duplicate_members_rejected(tmp_path):
    artifact = tmp_path / "bad.tar.gz"
    with tarfile.open(artifact, "w:gz") as archive:
        member = tarfile.TarInfo("link")
        member.type = tarfile.SYMTYPE
        member.linkname = "../outside"
        archive.addfile(member)
    with pytest.raises(ValueError, match="special"):
        supply.extract_artifact(artifact, tmp_path / "unpacked")
    with tarfile.open(artifact, "w:gz") as archive:
        for _ in range(2):
            member = tarfile.TarInfo("duplicate")
            member.size = 1
            archive.addfile(member, io.BytesIO(b"x"))
    with pytest.raises(ValueError, match="Duplicate"):
        supply.extract_artifact(artifact, tmp_path / "unpacked")


def test_mutable_action_cannot_pass(tmp_path):
    folder = tmp_path / ".github/workflows"
    folder.mkdir(parents=True)
    workflow = folder / "ci.yml"
    workflow.write_text("steps:\n  - uses: owner/action@v1\n")
    with pytest.raises(ValueError, match="Mutable"):
        supply.action_pins(tmp_path)
    workflow.write_text("steps:\n  - uses: owner/action@" + "a" * 40 + "\n")
    assert supply.action_pins(tmp_path) == ["owner/action@" + "a" * 40]


def test_release_publisher_supports_artifact_core_metadata():
    refs = supply.action_pins(Path(__file__).resolve().parents[1])
    reviewed = supply.publisher_compatibility(refs, ["2.5", "2.5"])
    assert reviewed == {
        "action": "pypa/gh-action-pypi-publish@"
        "dc37677b2e1c63e2034f94d8a5b11f265b73ba33",
        "release": "v1.14.2",
        "twine": "7.0.0",
        "max_core_metadata": "2.5",
        "artifact_core_metadata": ["2.5"],
    }


@pytest.mark.parametrize(
    ("refs", "metadata"),
    [
        (
            ["pypa/gh-action-pypi-publish@ed0c53931b1dc9bd32cbe73a98c7f6766f8a527e"],
            ["2.5"],
        ),
        (
            ["pypa/gh-action-pypi-publish@dc37677b2e1c63e2034f94d8a5b11f265b73ba33"],
            ["2.6"],
        ),
        ([], ["2.5"]),
        (
            ["pypa/gh-action-pypi-publish@dc37677b2e1c63e2034f94d8a5b11f265b73ba33"],
            [],
        ),
    ],
)
def test_unreviewed_publisher_metadata_combinations_fail(refs, metadata):
    with pytest.raises(ValueError):
        supply.publisher_compatibility(refs, metadata)


def test_secret_projection_drops_match_and_identity(monkeypatch, tmp_path):
    report = tmp_path / "raw.json"
    report.write_text(
        json.dumps(
            [
                {
                    "RuleID": "synthetic",
                    "File": "fixture",
                    "StartLine": 1,
                    "Commit": "",
                    "Secret": "synthetic private value",
                    "Match": "synthetic private value",
                    "Author": "private author",
                }
            ]
        )
    )

    class Completed:
        returncode = 1

    monkeypatch.setattr(supply, "command", lambda *a, **kw: Completed())
    findings = supply.scan(
        "fake", tmp_path, report, config=tmp_path / "config", work=tmp_path
    )
    assert findings == [
        {"rule": "synthetic", "file": "fixture", "line": 1, "commit": ""}
    ]
    assert not report.exists()
    assert "private" not in json.dumps(findings)


def test_non_registry_dependency_is_not_silently_skipped():
    with pytest.raises(ValueError, match="non-PyPI"):
        supply.pinned_packages(
            {
                "package": [
                    {
                        "name": "example",
                        "version": "1",
                        "source": {"git": "https://example.invalid"},
                    }
                ]
            }
        )


@pytest.mark.parametrize("tamper", ["version", "bytes", "extra"])
def test_artifact_identity_must_match_checkout(tmp_path, tamper):
    root = tmp_path / "source"
    package = root / "src/binspect"
    package.mkdir(parents=True)
    source = '__version__ = "0.1.1"\n'
    (package / "__init__.py").write_text(source)
    (package / "py.typed").write_text("")
    (root / "LICENSE").write_text("Synthetic license\n")
    (root / "pyproject.toml").write_text(
        """[project]
name = "binspect-regression"
dynamic = ["version"]
description = "Synthetic package"
requires-python = ">=3.10"
license = { file = "LICENSE" }
classifiers = ["Synthetic classifier"]
dependencies = ["numpy>=1"]
[project.optional-dependencies]
test = ["pytest>=8"]
"""
    )
    extracted = tmp_path / "unpacked"
    (extracted / "binspect").mkdir(parents=True)
    (extracted / "binspect/__init__.py").write_text(source)
    (extracted / "binspect/py.typed").write_text("")
    metadata_dir = extracted / "binspect_regression-0.1.1.dist-info"
    metadata_dir.mkdir()
    metadata = metadata_dir / "METADATA"
    metadata.write_text(
        """Name: binspect-regression
Version: 0.1.1
Summary: Synthetic package
Requires-Python: >=3.10
Requires-Dist: numpy>=1
Requires-Dist: pytest>=8; extra == 'test'
Provides-Extra: test
Classifier: Synthetic classifier
License-File: LICENSE
License: Synthetic license

"""
    )
    names = [
        "binspect/__init__.py",
        "binspect/py.typed",
        "binspect_regression-0.1.1.dist-info/METADATA",
    ]
    artifact = tmp_path / "package.whl"
    assert supply.verify_artifact_source(artifact, extracted, names, root) == "0.1.1"
    if tamper == "version":
        metadata.write_text("Name: binspect-regression\nVersion: 0.0.1\n")
    elif tamper == "bytes":
        (extracted / "binspect/__init__.py").write_text(source + "# different\n")
    else:
        names.append("unexpected/library.py")
    with pytest.raises(ValueError):
        supply.verify_artifact_source(artifact, extracted, names, root)


@pytest.mark.parametrize("tamper", ["bytes", "missing", "extra", "outside"])
def test_sdist_manifest_and_all_tracked_bytes_must_match_checkout(
    tmp_path, monkeypatch, tamper
):
    root = tmp_path / "source"
    package = root / "src/binspect"
    package.mkdir(parents=True)
    source = '__version__ = "0.1.1"\n'
    tracked = {
        "LICENSE": "Synthetic license\n",
        "README.md": "reviewed documentation\n",
        "pyproject.toml": """[project]
name = "binspect-regression"
dynamic = ["version"]
description = "Synthetic package"
requires-python = ">=3.10"
license = { file = "LICENSE" }
classifiers = ["Synthetic classifier"]
dependencies = ["numpy>=1"]
[project.optional-dependencies]
test = ["pytest>=8"]
""",
        "src/binspect/__init__.py": source,
        "src/binspect/py.typed": "",
    }
    for name, contents in tracked.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents)
    monkeypatch.setattr(
        supply,
        "command",
        lambda *args, **kwargs: SimpleNamespace(
            stdout=("\0".join(tracked) + "\0").encode()
        ),
    )
    prefix = "binspect_regression-0.1.1/"
    extracted = tmp_path / "unpacked"
    for name, contents in tracked.items():
        path = extracted / prefix / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents)
    metadata = extracted / prefix / "PKG-INFO"
    metadata.write_text(
        """Name: binspect-regression
Version: 0.1.1
Summary: Synthetic package
Requires-Python: >=3.10
Requires-Dist: numpy>=1
Requires-Dist: pytest>=8; extra == 'test'
Provides-Extra: test
Classifier: Synthetic classifier
License-File: LICENSE
License: Synthetic license

"""
    )
    names = [*(prefix + name for name in tracked), prefix + "PKG-INFO"]
    artifact = tmp_path / "package.tar.gz"
    assert supply.verify_artifact_source(artifact, extracted, names, root) == "0.1.1"
    if tamper == "bytes":
        (extracted / prefix / "README.md").write_text("different\n")
    elif tamper == "missing":
        names.remove(prefix + "README.md")
    elif tamper == "extra":
        names.append(prefix + "setup.py")
    else:
        names.append("outside-prefix")
    with pytest.raises(ValueError, match="Sdist"):
        supply.verify_artifact_source(artifact, extracted, names, root)


@pytest.mark.parametrize(
    "header,replacement",
    [
        ("Requires-Dist: numpy>=1", "Requires-Dist: numpy>=2"),
        ("Provides-Extra: test", "Provides-Extra: hidden"),
        ("License: Synthetic license", "License: Different license"),
    ],
)
def test_artifact_metadata_must_match_declared_project(tmp_path, header, replacement):
    root = tmp_path / "source"
    package = root / "src/binspect"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text('__version__ = "0.1.1"\n')
    (root / "LICENSE").write_text("Synthetic license\n")
    (root / "pyproject.toml").write_text(
        """[project]
name = "binspect-regression"
dynamic = ["version"]
description = "Synthetic package"
requires-python = ">=3.10"
license = { file = "LICENSE" }
classifiers = []
dependencies = ["numpy>=1"]
[project.optional-dependencies]
test = ["pytest>=8"]
"""
    )
    extracted = tmp_path / "unpacked"
    (extracted / "binspect").mkdir(parents=True)
    (extracted / "binspect/__init__.py").write_text('__version__ = "0.1.1"\n')
    metadata_dir = extracted / "binspect_regression-0.1.1.dist-info"
    metadata_dir.mkdir()
    metadata = """Name: binspect-regression
Version: 0.1.1
Summary: Synthetic package
Requires-Python: >=3.10
Requires-Dist: numpy>=1
Requires-Dist: pytest>=8; extra == 'test'
Provides-Extra: test
License-File: LICENSE
License: Synthetic license

""".replace(header, replacement)
    (metadata_dir / "METADATA").write_text(metadata)
    names = [
        "binspect/__init__.py",
        "binspect_regression-0.1.1.dist-info/METADATA",
    ]
    with pytest.raises(ValueError, match="metadata"):
        supply.verify_artifact_source(tmp_path / "package.whl", extracted, names, root)
