"""Build once, verify handoff integrity and exercise clean artifact installations."""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.metadata
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(args, *, cwd=ROOT, **kwargs):
    return subprocess.run(args, cwd=cwd, check=True, timeout=600, **kwargs)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_version(root=ROOT):
    tree = ast.parse((root / "src/binspect/__init__.py").read_text())
    values = [
        ast.literal_eval(node.value)
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "__version__" for t in node.targets)
    ]
    if len(values) != 1 or not isinstance(values[0], str):
        raise ValueError("One literal package version is required")
    return values[0]


def check_tag(tag, version):
    if (
        not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+(?:[a-z0-9.+-]*)", tag)
        or tag != f"v{version}"
    ):
        raise ValueError("Release tag must exactly match v{package_version}")


def verify_bundle(bundle, expected_sha256, *, root=ROOT):
    manifest_path = bundle / "manifest.json"
    if not re.fullmatch("[0-9a-f]{64}", expected_sha256):
        raise ValueError("An independently supplied manifest SHA-256 is required")
    if manifest_path.is_symlink() or sha256(manifest_path) != expected_sha256:
        raise ValueError("Handoff manifest changed")
    manifest = json.loads(manifest_path.read_text())
    if manifest["schema_version"] != 1 or manifest["version"] != source_version(root):
        raise ValueError("Unsupported manifest or wrong version")
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    if manifest["source_revision"] != revision or manifest["lock_sha256"] != sha256(
        root / "uv.lock"
    ):
        raise ValueError("Handoff source revision or lock differs from checkout")
    if manifest["smoke_sha256"] != sha256(root / "validation/dependency_smoke.py"):
        raise ValueError("Installed-code journey differs from build input")
    expected_names = {
        f"binspect_regression-{manifest['version']}-py3-none-any.whl",
        f"binspect_regression-{manifest['version']}.tar.gz",
    }
    records = manifest["artifacts"]
    if len(records) != 2 or {r["name"] for r in records} != expected_names:
        raise ValueError("Expected exactly the wheel and sdist for this version")
    if {p.name for p in bundle.iterdir()} != {"manifest.json", "dist"}:
        raise ValueError("Unexpected bundle entry")
    dist = bundle / "dist"
    if dist.is_symlink() or {p.name for p in dist.iterdir()} != expected_names:
        raise ValueError("Missing or unexpected handoff artifact")
    for record in records:
        path = dist / record["name"]
        if path.is_symlink() or not path.is_file() or sha256(path) != record["sha256"]:
            raise ValueError("Artifact checksum mismatch")
        if path.stat().st_size != record["size"]:
            raise ValueError("Artifact size mismatch")
    return manifest


def build(bundle, tag=""):
    version = source_version()
    if tag:
        check_tag(tag, version)
    if subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=normal"],
        cwd=ROOT,
        text=True,
    ).strip():
        raise ValueError("Qualification builds require a clean committed checkout")
    from supply_chain import extract_artifact, verify_artifact_source

    if bundle.exists() and any(bundle.iterdir()):
        raise ValueError("Build requires a fresh empty bundle directory")
    bundle.mkdir(parents=True, exist_ok=True)
    before = {
        "lock": sha256(ROOT / "uv.lock"),
        "smoke": sha256(ROOT / "validation/dependency_smoke.py"),
    }
    dist = bundle / "dist"
    run([sys.executable, "-m", "build", "--no-isolation", "--outdir", str(dist)])
    artifacts = sorted(dist.iterdir())
    if len(artifacts) != 2:
        raise ValueError("Build did not produce exactly two artifacts")
    run([sys.executable, "-m", "twine", "check", *map(str, artifacts)])
    with tempfile.TemporaryDirectory(
        prefix="binspect-artifact-inspection-"
    ) as directory:
        for artifact in artifacts:
            destination = Path(directory) / artifact.name
            names = extract_artifact(artifact, destination)
            verify_artifact_source(artifact, destination, names)
    manifest = {
        "schema_version": 1,
        "version": version,
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "lock_sha256": before["lock"],
        "smoke_sha256": before["smoke"],
        "built_at": datetime.now(timezone.utc).isoformat(),
        "build_tools": {
            name: importlib.metadata.version(name)
            for name in ("build", "hatchling", "twine")
        },
        "artifacts": [
            {"name": p.name, "sha256": sha256(p), "size": p.stat().st_size}
            for p in artifacts
        ],
    }
    path = bundle / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    digest = sha256(path)
    verify_bundle(bundle, digest)
    return digest


def export_requirements(path, profile, *, build_tools=False):
    args = [
        "uv",
        "export",
        "--frozen",
        "--no-dev",
        "--no-emit-project",
        "--output-file",
        str(path),
    ]
    if build_tools:
        args += ["--only-group", "build"]
    elif profile != "native":
        args += ["--extra", "pandas" if profile == "pandas" else "dpi"]
    run(args, stdout=subprocess.DEVNULL)


def install(bundle, digest, python, profile):
    manifest = verify_bundle(bundle, digest)
    records = []
    for artifact in manifest["artifacts"]:
        with tempfile.TemporaryDirectory(
            prefix="binspect-artifact-install-"
        ) as directory:
            work = Path(directory)
            environment = work / "venv"
            run(["uv", "venv", "--python", python, str(environment)])
            executable = environment / "bin/python"
            requirements = work / "requirements.txt"
            export_requirements(requirements, profile)
            run(
                [
                    "uv",
                    "pip",
                    "install",
                    "--python",
                    str(executable),
                    "--require-hashes",
                    "-r",
                    str(requirements),
                ]
            )
            # Build the sdist in a distinct locked environment, then install its
            # resulting wheel into the runtime-only child. No build tools leak
            # into the native journey and no isolated backend resolves upstream.
            candidate = bundle / "dist" / artifact["name"]
            installed_from = artifact["name"]
            if candidate.name.endswith(".tar.gz"):
                build_environment = work / "build-venv"
                run(["uv", "venv", "--python", python, str(build_environment)])
                build_python = build_environment / "bin/python"
                build_requirements = work / "build-requirements.txt"
                export_requirements(build_requirements, profile, build_tools=True)
                run(
                    [
                        "uv",
                        "pip",
                        "install",
                        "--python",
                        str(build_python),
                        "--require-hashes",
                        "-r",
                        str(build_requirements),
                    ]
                )
                from supply_chain import extract_artifact, verify_artifact_source

                unpacked = work / "sdist"
                extract_artifact(candidate, unpacked)
                source = unpacked / f"binspect_regression-{manifest['version']}"
                wheels = work / "rebuilt"
                run(
                    [
                        str(build_python),
                        "-I",
                        "-m",
                        "build",
                        "--wheel",
                        "--no-isolation",
                        "--outdir",
                        str(wheels),
                        str(source),
                    ],
                    cwd=work,
                )
                generated = list(wheels.glob("*.whl"))
                if len(generated) != 1:
                    raise ValueError("Sdist install did not produce one wheel")
                candidate = generated[0]
                inspection = work / "rebuilt-inspection"
                names = extract_artifact(candidate, inspection)
                verify_artifact_source(candidate, inspection, names)
            run(
                [
                    "uv",
                    "pip",
                    "install",
                    "--python",
                    str(executable),
                    "--no-deps",
                    str(candidate),
                ],
                cwd=work,
            )
            run(["uv", "pip", "check", "--python", str(executable)], cwd=work)
            # Verify the actual installed distribution and every library file
            # against the delivered wheel (or the wheel built from the sdist).
            identity = work / "identity.py"
            identity.write_text("""import importlib.metadata as m
import json, pathlib, sys, zipfile
import binspect
expected_version, wheel_path = sys.argv[1:]
assert m.version("binspect-regression") == expected_version == binspect.__version__
root = pathlib.Path(binspect.__file__).parent.parent
assert "site-packages" in root.parts
with zipfile.ZipFile(wheel_path) as wheel:
    for name in wheel.namelist():
        if name.startswith("binspect/") and not name.endswith("/"):
            assert (root / name).read_bytes() == wheel.read(name), name
direct = m.distribution("binspect-regression").read_text("direct_url.json")
assert direct and not json.loads(direct).get("dir_info", {}).get("editable", False)
""")
            run(
                [
                    str(executable),
                    "-I",
                    str(identity),
                    manifest["version"],
                    str(candidate),
                ],
                cwd=work,
            )
            result_path = work / "result.json"
            smoke = [
                str(executable),
                "-I",
                str(ROOT / "validation/dependency_smoke.py"),
                "--output",
                str(result_path),
            ]
            if profile != "native":
                smoke.append("--pandas")
            if profile == "dpi":
                smoke.append("--dpi")
            run(smoke, cwd=work, env={**os.environ, "MPLBACKEND": "Agg"})
            record = json.loads(result_path.read_text())
            record.update(
                artifact=installed_from,
                artifact_sha256=artifact["sha256"],
                installed_wheel_sha256=sha256(candidate),
                profile=profile,
            )
            records.append(record)
    verify_bundle(bundle, digest)
    return {
        "status": "pass",
        "manifest_sha256": digest,
        "source_revision": manifest["source_revision"],
        "checks": records,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    building = sub.add_parser("build")
    building.add_argument("--bundle", type=Path, required=True)
    building.add_argument("--expected-tag", default="")
    building.add_argument("--github-output", type=Path)
    for name in ("verify", "install"):
        command = sub.add_parser(name)
        command.add_argument("--bundle", type=Path, required=True)
        command.add_argument("--manifest-sha256", required=True)
        if name == "install":
            command.add_argument("--python", default="3.12")
            command.add_argument(
                "--profile", choices=("native", "pandas", "dpi"), default="native"
            )
            command.add_argument("--output", type=Path, required=True)
    tag = sub.add_parser("tag")
    tag.add_argument("--tag", required=True)
    args = parser.parse_args()
    if args.command == "tag":
        check_tag(args.tag, source_version())
    elif args.command == "build":
        digest = build(args.bundle.resolve(), args.expected_tag)
        print(f"manifest_sha256={digest}")
        if args.github_output:
            with args.github_output.open("a") as output:
                output.write(f"manifest-sha256={digest}\n")
    elif args.command == "verify":
        verify_bundle(args.bundle.resolve(), args.manifest_sha256)
        print("Artifact handoff verified.")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.unlink(missing_ok=True)
        record = install(
            args.bundle.resolve(), args.manifest_sha256, args.python, args.profile
        )
        args.output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        print(f"Both artifact installs passed: {args.profile}, Python {args.python}.")


if __name__ == "__main__":
    main()
