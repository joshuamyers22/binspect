"""Maintenance evidence and recovery decisions must fail closed."""

from __future__ import annotations

import importlib.util
from copy import deepcopy
from pathlib import Path

import pytest


def load(name):
    spec = importlib.util.spec_from_file_location(
        name, Path(__file__).resolve().parents[1] / f"validation/{name}.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


maintenance = load("maintenance")
recovery = load("recovery")


@pytest.fixture
def publication():
    manifest = {
        "schema_version": 1,
        "version": "0.9.0",
        "artifacts": [
            {"name": "binspect_regression-0.9.0-py3-none-any.whl", "sha256": "a" * 64},
            {"name": "binspect_regression-0.9.0.tar.gz", "sha256": "b" * 64},
        ],
    }
    index = {
        "info": {"name": "binspect-regression", "version": "0.9.0"},
        "urls": [
            {"filename": a["name"], "digests": {"sha256": a["sha256"]}, "yanked": False}
            for a in manifest["artifacts"]
        ],
    }
    return manifest, index


def test_complete_publication_never_suggests_reupload(publication):
    result = recovery.reconcile(*publication)
    assert result["state"] == "complete"
    assert result["action"] == "verify_published_installs_do_not_reupload"
    assert not result["release_qualified"]


def test_partial_publication_lists_only_missing_original_file(publication):
    manifest, index = publication
    index["urls"].pop()
    result = recovery.reconcile(manifest, index)
    assert result["state"] == "partial"
    assert result["missing"] == [manifest["artifacts"][1]["name"]]


@pytest.mark.parametrize("mutation", ["hash", "extra", "yanked", "defect", "empty"])
def test_recovery_handles_unsafe_or_incomplete_index_states(publication, mutation):
    manifest, index = publication
    expected = {
        "hash": "conflict",
        "extra": "conflict",
        "yanked": "yanked",
        "defect": "defective",
        "empty": "no_files_observed",
    }[mutation]
    if mutation == "hash":
        index["urls"][0]["digests"]["sha256"] = "c" * 64
    elif mutation == "extra":
        extra = deepcopy(index["urls"][0])
        extra["filename"] = "unreviewed.whl"
        index["urls"].append(extra)
    elif mutation == "yanked":
        index["urls"][0]["yanked"] = True
    elif mutation == "empty":
        index["urls"] = []
    result = recovery.reconcile(manifest, index, known_defect=mutation == "defect")
    assert result["state"] == expected
    assert result["authorization"].startswith("none")


@pytest.mark.parametrize(
    "mutation",
    [
        "duplicate",
        "version",
        "project",
        "invalid_digest",
        "missing_yank",
        "missing_body",
    ],
)
def test_ambiguous_index_evidence_is_rejected(publication, mutation):
    manifest, index = publication
    if mutation == "duplicate":
        index["urls"].append(index["urls"][0])
    elif mutation in ("version", "project"):
        index["info"]["version" if mutation == "version" else "name"] = "other"
    elif mutation == "invalid_digest":
        index["urls"][0]["digests"]["sha256"] = "unknown"
    elif mutation == "missing_yank":
        del index["urls"][0]["yanked"]
    else:
        index = {"error": "upstream unavailable"}
    with pytest.raises((KeyError, ValueError)):
        recovery.reconcile(manifest, index)


@pytest.mark.parametrize(
    "count,skipped,returncode,expected",
    [
        (74, False, 0, "pass"),
        (0, False, 0, "unverified"),
        (73, False, 0, "unverified"),
        (74, True, 0, "unverified"),
        (74, False, 2, "unverified"),
    ],
)
def test_reference_result_requires_all_cases_without_skips(
    tmp_path, count, skipped, returncode, expected
):
    path = tmp_path / "results.xml"
    cases = [
        f'<testcase name="test_{i}">{"<skipped />" if skipped and i == 0 else ""}</testcase>'
        for i in range(count)
    ]
    path.write_text("<testsuite>" + "".join(cases) + "</testsuite>")
    assert maintenance.reference_result(path, returncode)["status"] == expected


def test_reference_failure_is_retained_without_raw_payload(tmp_path):
    path = tmp_path / "results.xml"
    path.write_text(
        '<testsuite><testcase name="test_slope" classname="test_inference"><failure message="private payload">private traceback</failure></testcase></testsuite>'
    )
    result = maintenance.reference_result(path, 1)
    assert result["status"] == "fail"
    assert result["failures"] == [{"test": "test_slope", "module": "test_inference"}]
    assert "private" not in str(result)


def test_missing_or_malformed_reference_report_is_unverified(tmp_path):
    path = tmp_path / "results.xml"
    assert maintenance.reference_result(path, 0)["status"] == "unverified"
    path.write_text("truncated XML")
    assert maintenance.reference_result(path, 0)["status"] == "unverified"


def test_resolution_outage_replaces_stale_pass_with_owned_unverified_record(
    tmp_path, monkeypatch
):
    import json
    from types import SimpleNamespace

    monkeypatch.setattr(maintenance, "fingerprint", lambda: [])
    monkeypatch.setattr(
        maintenance.subprocess, "check_output", lambda *a, **k: "revision\n"
    )
    monkeypatch.setattr(
        maintenance.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(
            returncode=2, stdout=b"private upstream output"
        ),
    )
    (tmp_path / "result.json").write_text('{"status":"pass"}')
    assert not maintenance.probe("current", "3.12", tmp_path)
    result = json.loads((tmp_path / "result.json").read_text())
    assert result["status"] == "unverified" and result["release_hold"]
    assert result["owner"] == "Josh Myers"
    assert result["stages"][0]["returncode"] == 2
    assert "private" not in (tmp_path / "result.json").read_text()
    assert "private" not in (tmp_path / "stages.jsonl").read_text()
