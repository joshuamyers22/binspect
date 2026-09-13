"""Release policy rejects stale identities and failed cryptographic verification.

Verifier responses are synthetic; these tests do not qualify signed artifacts.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

VALIDATION = Path(__file__).resolve().parents[1] / "validation"
with pytest.MonkeyPatch.context() as patch:
    patch.syspath_prepend(str(VALIDATION))
    SPEC = importlib.util.spec_from_file_location(
        "provenance", VALIDATION / "provenance.py"
    )
    assert SPEC is not None and SPEC.loader is not None
    provenance = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(provenance)

SOURCE = "a" * 40
REF = "refs/tags/v0.1.1"
INVOCATION = "https://github.com/joshuamyers22/binspect/actions/runs/123/attempts/1"


@pytest.fixture
def release(tmp_path, monkeypatch):
    bundle = tmp_path / "bundle"
    (bundle / "dist").mkdir(parents=True)
    records = []
    for suffix in ("-py3-none-any.whl", ".tar.gz"):
        path = bundle / "dist" / f"binspect_regression-0.1.1{suffix}"
        path.write_bytes(b"synthetic artifact")
        records.append(
            {
                "name": path.name,
                "sha256": provenance.sha256(path),
                "size": path.stat().st_size,
            }
        )
    manifest = {"version": "0.1.1", "source_revision": SOURCE, "artifacts": records}
    # R1's integrity verification has separate tampering tests. Here test its use
    # and the additional authenticated identity policy, with no network/signing.
    checks = []

    def verify_bundle(*args):
        checks.append(args)
        return manifest

    monkeypatch.setattr(provenance, "verify_bundle", verify_bundle)
    attestation = tmp_path / "attestation.json"
    attestation.write_text("synthetic signed bundle placeholder")
    statement = {
        "_type": "https://in-toto.io/Statement/v1",
        "predicateType": provenance.PREDICATE,
        "subject": [
            {"name": r["name"], "digest": {"sha256": r["sha256"]}} for r in records
        ],
        "predicate": {
            "buildDefinition": {
                "buildType": provenance.BUILD_TYPE,
                "externalParameters": {
                    "workflow": {
                        "repository": "https://github.com/joshuamyers22/binspect",
                        "path": ".github/workflows/release.yml",
                        "ref": REF,
                    }
                },
                "resolvedDependencies": [
                    {
                        "uri": f"git+https://github.com/joshuamyers22/binspect@{REF}",
                        "digest": {"gitCommit": SOURCE},
                    }
                ],
            },
            "runDetails": {"metadata": {"invocationId": INVOCATION}},
        },
    }
    response = [
        {
            "verificationResult": {
                "signature": {
                    "certificate": {
                        "runInvocationURI": INVOCATION,
                        "buildTrigger": "release",
                    }
                },
                "statement": statement,
            }
        }
    ]
    calls = []

    def run(args, **kwargs):
        calls.append((args, kwargs))
        stdout = (
            "gh version 2.98.0 (2026-08-20)\n"
            if args == ["gh", "--version"]
            else json.dumps(response)
        )
        return subprocess.CompletedProcess(args, 0, stdout, "")

    monkeypatch.setattr(provenance.subprocess, "run", run)
    return {
        "args": dict(
            bundle=bundle,
            manifest_sha256="b" * 64,
            attestation=attestation,
            source=SOURCE,
            ref=REF,
            run_id="123",
            attempt="1",
        ),
        "response": response,
        "calls": calls,
        "checks": checks,
    }


def test_both_artifacts_require_crypto_identity_and_rechecked_integrity(release):
    result = provenance.verify(**release["args"])
    assert result["status"] == "pass"
    assert len(release["checks"]) == 2
    calls = release["calls"][1:]
    assert len(calls) == 2
    assert {Path(args[3]).suffix for args, _ in calls} == {".whl", ".gz"}
    for args, kwargs in calls:
        assert kwargs["check"] is True
        assert kwargs["capture_output"] is True
        assert kwargs["timeout"] == 180
        for flag, value in {
            "--repo": "joshuamyers22/binspect",
            "--signer-workflow": "joshuamyers22/binspect/.github/workflows/release.yml",
            "--cert-identity": f"https://github.com/joshuamyers22/binspect/.github/workflows/release.yml@{REF}",
            "--source-digest": SOURCE,
            "--signer-digest": SOURCE,
            "--source-ref": REF,
            "--cert-oidc-issuer": "https://token.actions.githubusercontent.com",
            "--predicate-type": "https://slsa.dev/provenance/v1",
            "--bundle": str(release["args"]["attestation"]),
        }.items():
            assert args[args.index(flag) + 1] == value
        assert "--deny-self-hosted-runners" in args


@pytest.mark.parametrize(
    "field,value",
    [
        ("source", "b" * 40),
        ("source", "main"),
        ("ref", "refs/heads/main"),
        ("ref", "refs/tags/v0.2.0"),
        ("run_id", "0"),
        ("attempt", ""),
    ],
)
def test_invalid_release_identity_stops_before_crypto(release, field, value):
    release["args"][field] = value
    with pytest.raises(ValueError):
        provenance.verify(**release["args"])
    assert release["calls"] == []


@pytest.mark.parametrize(
    "mutation",
    [
        "run",
        "attempt",
        "trigger",
        "missing-certificate",
        "subject",
        "extra-subject",
        "predicate",
        "build-type",
        "workflow",
        "dependency",
        "invocation",
        "empty",
        "malformed",
    ],
)
def test_authenticated_output_must_match_exact_release(release, mutation):
    response = release["response"]
    verified = response[0]["verificationResult"]
    certificate = verified["signature"]["certificate"]
    statement = verified["statement"]
    definition = statement["predicate"]["buildDefinition"]
    if mutation in ("run", "attempt"):
        certificate["runInvocationURI"] = (
            INVOCATION.replace("123", "456")
            if mutation == "run"
            else INVOCATION.replace("attempts/1", "attempts/2")
        )
    elif mutation == "trigger":
        certificate["buildTrigger"] = "pull_request"
    elif mutation == "missing-certificate":
        verified["signature"].clear()
    elif mutation == "subject":
        statement["subject"][0]["digest"]["sha256"] = "0" * 64
    elif mutation == "extra-subject":
        statement["subject"].append(copy.deepcopy(statement["subject"][0]))
    elif mutation == "predicate":
        statement["predicateType"] = "https://spdx.dev/Document"
    elif mutation == "build-type":
        definition["buildType"] = "untrusted"
    elif mutation == "workflow":
        definition["externalParameters"]["workflow"]["path"] = (
            ".github/workflows/ci.yml"
        )
    elif mutation == "dependency":
        definition["resolvedDependencies"][0]["digest"]["gitCommit"] = "b" * 40
    elif mutation == "invocation":
        statement["predicate"]["runDetails"]["metadata"]["invocationId"] = "other"
    elif mutation == "empty":
        response.clear()
    else:
        response[:] = [None]
    with pytest.raises((ValueError, KeyError, TypeError)):
        provenance.verify(**release["args"])


@pytest.mark.parametrize(
    "failure", ["signature", "missing-gh", "timeout", "invalid-json"]
)
def test_cli_failure_never_uses_unverified_output(release, monkeypatch, failure):
    original = provenance.subprocess.run

    def fail(args, **kwargs):
        if args == ["gh", "--version"]:
            return original(args, **kwargs)
        if failure == "signature":
            raise subprocess.CalledProcessError(
                1, args, output=json.dumps(release["response"])
            )
        if failure == "missing-gh":
            raise FileNotFoundError("gh")
        if failure == "timeout":
            raise subprocess.TimeoutExpired(args, 180)
        return subprocess.CompletedProcess(args, 0, "invalid-json", "")

    monkeypatch.setattr(provenance.subprocess, "run", fail)
    with pytest.raises((OSError, ValueError, subprocess.SubprocessError)):
        provenance.verify(**release["args"])


def test_changed_attestation_is_rejected(release, monkeypatch):
    original = provenance.subprocess.run

    def change(*args, **kwargs):
        result = original(*args, **kwargs)
        release["args"]["attestation"].write_text("changed")
        return result

    monkeypatch.setattr(provenance.subprocess, "run", change)
    with pytest.raises(ValueError, match="changed"):
        provenance.verify(**release["args"])


def test_second_artifact_failure_prevents_success(release, monkeypatch):
    original = provenance.subprocess.run

    def fail_second(args, **kwargs):
        if args[1:3] == ["attestation", "verify"] and args[3].endswith(".tar.gz"):
            raise subprocess.CalledProcessError(1, args)
        return original(args, **kwargs)

    monkeypatch.setattr(provenance.subprocess, "run", fail_second)
    with pytest.raises(subprocess.CalledProcessError):
        provenance.verify(**release["args"])
    assert len(release["checks"]) == 1


@pytest.mark.parametrize("failure_at", [1, 2])
def test_integrity_failure_before_or_after_crypto_blocks_success(
    release, monkeypatch, failure_at
):
    checks = []
    original = provenance.verify_bundle

    def fail(*args):
        checks.append(args)
        if len(checks) == failure_at:
            raise ValueError("Artifact checksum mismatch")
        return original(*args)

    monkeypatch.setattr(provenance, "verify_bundle", fail)
    with pytest.raises(ValueError, match="checksum"):
        provenance.verify(**release["args"])
    if failure_at == 1:
        assert release["calls"] == []


def test_symlinked_attestation_is_rejected_before_crypto(release):
    path = release["args"]["attestation"]
    target = path.with_suffix(".target")
    path.rename(target)
    path.symlink_to(target)
    with pytest.raises(ValueError, match="regular"):
        provenance.verify(**release["args"])
    assert release["calls"] == []


def test_cli_errors_are_sanitized_with_no_success_output(release, monkeypatch, capsys):
    def fail(**kwargs):
        raise ValueError("unrestricted diagnostic must not escape")

    monkeypatch.setattr(provenance, "verify", fail)
    args = ["provenance"]
    for key, value in release["args"].items():
        args.extend(["--" + key.replace("_", "-"), str(value)])
    monkeypatch.setattr(sys, "argv", args)
    assert provenance.main() == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert (
        captured.err == "Release provenance verification failed; publication blocked.\n"
    )
