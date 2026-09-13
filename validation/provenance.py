"""Verify release attestations with GitHub CLI, then enforce exact run policy.

Only successful verifier output is parsed. This module does not implement crypto,
accept saved verification summaries, sign artifacts, or authorize publication.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from artifacts import check_tag, sha256, verify_bundle

REPOSITORY = "joshuamyers22/binspect"
WORKFLOW = ".github/workflows/release.yml"
PREDICATE = "https://slsa.dev/provenance/v1"
BUILD_TYPE = "https://actions.github.io/buildtypes/workflow/v1"


def check_statement(results, manifest, ref, invocation):
    """Additional policy on authenticated gh output, never raw bundle JSON."""
    expected_subjects = {
        (record["name"], record["sha256"]) for record in manifest["artifacts"]
    }
    if not isinstance(results, list) or not results:
        raise ValueError("No verified attestations")
    for result in results:
        verified = result["verificationResult"]
        certificate = verified["signature"]["certificate"]
        if (
            certificate["runInvocationURI"] != invocation
            or certificate["buildTrigger"] != "release"
        ):
            raise ValueError("Attestation certificate has the wrong release run")
        statement = verified["statement"]
        subjects = statement["subject"]
        if (
            statement["_type"] != "https://in-toto.io/Statement/v1"
            or statement["predicateType"] != PREDICATE
            or len(subjects) != len(expected_subjects)
            or {(s["name"], s["digest"]["sha256"]) for s in subjects}
            != expected_subjects
        ):
            raise ValueError("Attestation subjects or predicate differ")
        predicate = statement["predicate"]
        definition = predicate["buildDefinition"]
        if (
            definition["buildType"] != BUILD_TYPE
            or definition["externalParameters"]["workflow"]
            != {
                "repository": f"https://github.com/{REPOSITORY}",
                "path": WORKFLOW,
                "ref": ref,
            }
            or definition["resolvedDependencies"]
            != [
                {
                    "uri": f"git+https://github.com/{REPOSITORY}@{ref}",
                    "digest": {"gitCommit": manifest["source_revision"]},
                }
            ]
            or predicate["runDetails"]["metadata"]["invocationId"] != invocation
        ):
            raise ValueError("Attestation build identity differs")


def verify(bundle, manifest_sha256, attestation, *, source, ref, run_id, attempt):
    if not re.fullmatch("[0-9a-f]{40}", source) or not all(
        re.fullmatch("[1-9][0-9]*", value) for value in (run_id, attempt)
    ):
        raise ValueError("Exact source commit, run and attempt are required")
    manifest = verify_bundle(bundle, manifest_sha256)
    if source != manifest["source_revision"] or not ref.startswith("refs/tags/"):
        raise ValueError("Release source or ref differs from qualified bundle")
    check_tag(ref.removeprefix("refs/tags/"), manifest["version"])
    if attestation.is_symlink() or not attestation.is_file():
        raise ValueError("A regular signed attestation bundle is required")
    attestation_digest = sha256(attestation)
    invocation = (
        f"https://github.com/{REPOSITORY}/actions/runs/{run_id}/attempts/{attempt}"
    )
    version = subprocess.run(
        ["gh", "--version"], capture_output=True, text=True, check=True, timeout=30
    ).stdout.splitlines()[0]
    if not re.fullmatch(r"gh version [0-9.]+ \([0-9-]+\)", version):
        raise ValueError("Unrecognized verifier version")
    for record in manifest["artifacts"]:
        completed = subprocess.run(
            [
                "gh",
                "attestation",
                "verify",
                str((bundle / "dist" / record["name"]).resolve()),
                "--bundle",
                str(attestation.resolve()),
                "--repo",
                REPOSITORY,
                "--signer-workflow",
                f"{REPOSITORY}/{WORKFLOW}",
                "--cert-identity",
                f"https://github.com/{REPOSITORY}/{WORKFLOW}@{ref}",
                "--source-digest",
                source,
                "--signer-digest",
                source,
                "--source-ref",
                ref,
                "--cert-oidc-issuer",
                "https://token.actions.githubusercontent.com",
                "--predicate-type",
                PREDICATE,
                "--deny-self-hosted-runners",
                "--format",
                "json",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=180,
        )
        check_statement(json.loads(completed.stdout), manifest, ref, invocation)
    # Detect changes during either verification; never emit partial success.
    verify_bundle(bundle, manifest_sha256)
    if sha256(attestation) != attestation_digest or attestation.is_symlink():
        raise ValueError("Attestation bundle changed during verification")
    return {
        "schema_version": 1,
        "status": "pass",
        "verifier": version,
        "repository": REPOSITORY,
        "workflow": WORKFLOW,
        "source_revision": source,
        "ref": ref,
        "invocation": invocation,
        "manifest_sha256": manifest_sha256,
        "attestation_sha256": attestation_digest,
        "artifacts": manifest["artifacts"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--attestation", type=Path, required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--ref", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--attempt", required=True)
    args = parser.parse_args()
    try:
        result = verify(**vars(args))
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        IndexError,
        subprocess.SubprocessError,
    ):
        print(
            "Release provenance verification failed; publication blocked.",
            file=sys.stderr,
        )
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
