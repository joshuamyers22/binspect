"""Reject altered artifact handoffs and release tags before installation."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "artifacts", Path(__file__).resolve().parents[1] / "validation/artifacts.py"
)
assert SPEC is not None and SPEC.loader is not None
artifacts = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(artifacts)


@pytest.fixture
def bundle(tmp_path, monkeypatch):
    root = tmp_path / "source"
    (root / "src/binspect").mkdir(parents=True)
    (root / "src/binspect/__init__.py").write_text('__version__ = "0.1.1"\n')
    (root / "uv.lock").write_text("locked inputs")
    (root / "validation").mkdir()
    (root / "validation/dependency_smoke.py").write_text("installed journey")
    monkeypatch.setattr(artifacts.subprocess, "check_output", lambda *a, **k: "abc\n")
    destination = tmp_path / "bundle"
    dist = destination / "dist"
    dist.mkdir(parents=True)
    records = []
    for suffix in ("-py3-none-any.whl", ".tar.gz"):
        path = dist / f"binspect_regression-0.1.1{suffix}"
        path.write_bytes(b"synthetic archive bytes")
        records.append(
            {
                "name": path.name,
                "sha256": artifacts.sha256(path),
                "size": path.stat().st_size,
            }
        )
    manifest = {
        "schema_version": 1,
        "version": "0.1.1",
        "source_revision": "abc",
        "lock_sha256": artifacts.sha256(root / "uv.lock"),
        "smoke_sha256": artifacts.sha256(root / "validation/dependency_smoke.py"),
        "artifacts": records,
    }
    path = destination / "manifest.json"
    path.write_text(json.dumps(manifest))
    return root, destination, artifacts.sha256(path)


def test_unchanged_bundle_is_accepted(bundle):
    root, destination, digest = bundle
    assert artifacts.verify_bundle(destination, digest, root=root)["version"] == "0.1.1"


@pytest.mark.parametrize(
    "mutation",
    ["manifest", "artifact", "missing", "extra", "symlink", "lock", "smoke", "version"],
)
def test_changed_bundle_or_checkout_is_rejected(bundle, mutation):
    root, destination, digest = bundle
    wheel = next((destination / "dist").glob("*.whl"))
    if mutation == "manifest":
        (destination / "manifest.json").write_text("{}")
    elif mutation == "artifact":
        wheel.write_bytes(b"tampered artifact")
    elif mutation == "missing":
        wheel.unlink()
    elif mutation == "extra":
        (destination / "dist/extra.whl").write_bytes(b"unexpected")
    elif mutation == "symlink":
        target = destination.parent / "outside.whl"
        wheel.rename(target)
        wheel.symlink_to(target)
    elif mutation == "lock":
        (root / "uv.lock").write_text("changed lock")
    elif mutation == "smoke":
        (root / "validation/dependency_smoke.py").write_text("changed journey")
    else:
        (root / "src/binspect/__init__.py").write_text('__version__ = "0.2.0"')
    with pytest.raises(ValueError):
        artifacts.verify_bundle(destination, digest, root=root)


@pytest.mark.parametrize("digest", ["", "a" * 63, "g" * 64, "0" * 64])
def test_independent_manifest_digest_is_required(bundle, digest):
    root, destination, _ = bundle
    with pytest.raises(ValueError):
        artifacts.verify_bundle(destination, digest, root=root)


def test_wrong_checkout_revision_is_rejected(bundle, monkeypatch):
    root, destination, digest = bundle
    monkeypatch.setattr(artifacts.subprocess, "check_output", lambda *a, **k: "other\n")
    with pytest.raises(ValueError, match="revision"):
        artifacts.verify_bundle(destination, digest, root=root)


@pytest.mark.parametrize("tag", ["0.1.1", "v0.1.2", "v0.1.1\n", "v0.1.1/extra", ""])
def test_malformed_or_mismatched_tag_is_rejected(tag):
    with pytest.raises(ValueError):
        artifacts.check_tag(tag, "0.1.1")


def test_exact_release_tag_is_accepted():
    artifacts.check_tag("v0.1.1", "0.1.1")


def test_qualification_rejects_uncommitted_inputs(tmp_path, monkeypatch):
    monkeypatch.setattr(
        artifacts.subprocess, "check_output", lambda *a, **k: " M src/binspect/api.py\n"
    )
    with pytest.raises(ValueError, match="clean committed"):
        artifacts.build(tmp_path / "bundle")
    assert not (tmp_path / "bundle").exists()
