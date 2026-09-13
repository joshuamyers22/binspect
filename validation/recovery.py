"""Read-only reconciliation of reviewed artifacts and a saved PyPI release response."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


def reconcile(manifest, index, *, known_defect=False):
    if (
        not isinstance(manifest, dict)
        or not isinstance(manifest.get("artifacts"), list)
        or not isinstance(manifest.get("version"), str)
        or not isinstance(index, dict)
        or not isinstance(index.get("info"), dict)
        or not isinstance(index.get("urls"), list)
    ):
        raise ValueError("Complete manifest and release-index objects are required")
    version = manifest["version"]
    expected_names = {
        f"binspect_regression-{version}-py3-none-any.whl",
        f"binspect_regression-{version}.tar.gz",
    }
    artifacts = manifest["artifacts"]
    if manifest["schema_version"] != 1 or len(artifacts) != 2:
        raise ValueError("Expected a reviewed R1 wheel/sdist manifest")
    expected = {a["name"]: a["sha256"] for a in artifacts}
    if set(expected) != expected_names or any(
        not re.fullmatch("[0-9a-f]{64}", digest) for digest in expected.values()
    ):
        raise ValueError("Invalid expected artifacts")
    # A saved HTTP error, missing body or ambiguous result is never absence proof.
    info = index["info"]
    if (
        re.sub(r"[-_.]+", "-", info["name"]).lower() != "binspect-regression"
        or info["version"] != version
    ):
        raise ValueError("Index project/version differs from reviewed artifacts")
    observed = {}
    yanked = False
    for file in index["urls"]:
        name, digest = file["filename"], file["digests"]["sha256"]
        if name in observed or not re.fullmatch("[0-9a-f]{64}", digest):
            raise ValueError("Duplicate or invalid index artifact")
        if not isinstance(file["yanked"], bool):
            raise ValueError("Missing or invalid yank state")
        observed[name] = digest
        yanked |= file["yanked"]
    conflicts = sorted(
        name for name, digest in observed.items() if expected.get(name) != digest
    )
    missing = sorted(set(expected) - set(observed))
    if conflicts:
        state, action = "conflict", "stop_and_investigate_new_version_required"
    elif yanked:
        state, action = "yanked", "keep_yanked_and_review_fixed_release"
    elif known_defect and observed:
        state, action = "defective", "review_yank_and_fixed_release"
    elif known_defect:
        state, action = "defective_unpublished", "withhold_and_fix_before_publication"
    elif not observed:
        state, action = (
            "no_files_observed",
            "verify_history_and_authorization_before_retry",
        )
    elif missing:
        state, action = "partial", "review_upload_of_only_missing_original_files"
    else:
        state, action = "complete", "verify_published_installs_do_not_reupload"
    return {
        "schema_version": 1,
        "version": version,
        "state": state,
        "action": action,
        "missing": missing,
        "conflicts": conflicts,
        "owner": "Josh Myers",
        "authorization": "none; this tool only proposes a recovery decision",
        "release_qualified": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--known-defect", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve() in {args.manifest.resolve(), args.index.resolve()}:
        parser.error("Output must not overwrite input evidence")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.unlink(missing_ok=True)
    if hashlib.sha256(args.manifest.read_bytes()).hexdigest() != args.manifest_sha256:
        parser.error("Manifest differs from the independently recorded digest")
    try:
        result = reconcile(
            json.loads(args.manifest.read_text()),
            json.loads(args.index.read_text()),
            known_defect=args.known_defect,
        )
    except (KeyError, TypeError, ValueError, OSError):
        parser.error(
            "Unverified input; obtain a complete release-specific index response"
        )
    result["manifest_sha256"] = args.manifest_sha256
    result["index_sha256"] = hashlib.sha256(args.index.read_bytes()).hexdigest()
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(result["action"])


if __name__ == "__main__":
    main()
