"""Audit the complete lock, artifacts and history; fail on missing evidence."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import importlib.metadata
import io
import json
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from datetime import date, datetime, timezone
from email.parser import BytesParser
from pathlib import Path, PurePosixPath

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from packaging.markers import Marker
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parents[1]
PERMISSIVE = {
    "0BSD",
    "Apache-2.0",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "CC0-1.0",
    "ISC",
    "MIT",
    "MIT-0",
    "MIT-CMU",
    "PSF-2.0",
    "Zlib",
}
CLASSIFIERS = {
    "Apache Software License",
    "BSD License",
    "ISC License (ISCL)",
    "MIT License",
    "Python Software Foundation License",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(args, *, cwd=ROOT, accepted=(0,), timeout=600, env=None):
    result = subprocess.run(
        args, cwd=cwd, capture_output=True, timeout=timeout, env=env
    )
    if result.returncode not in accepted:
        # Never copy scanner/service output into public logs or exception text.
        raise RuntimeError(f"{Path(str(args[0])).name} exited {result.returncode}")
    return result


def pinned_packages(lock):
    packages = lock["package"]
    result = {}
    for package in packages:
        source = package["source"]
        if source == {"editable": "."}:
            continue
        if source != {"registry": "https://pypi.org/simple"}:
            raise ValueError("Unaudited non-PyPI dependency source")
        key = (canonicalize_name(package["name"]), package["version"])
        if key in result:
            raise ValueError("Duplicate locked package identity")
        result[key] = package
    if not result:
        raise ValueError("Empty lock inventory")
    return result


def audit_batches(packages):
    batches = []
    for name, version in sorted(packages):
        batch = next((b for b in batches if name not in b), None)
        if batch is None:
            batch = {}
            batches.append(batch)
        batch[name] = version
    return batches


def validate_audit(payload, expected):
    found = set()
    findings = []
    for item in payload["dependencies"]:
        if item.get("skip_reason"):
            raise ValueError("Advisory service skipped a dependency")
        key = (canonicalize_name(item["name"]), item["version"])
        if key in found:
            raise ValueError("Duplicate audited package")
        found.add(key)
        for vulnerability in item["vulns"]:
            findings.append(
                {
                    "package": key[0],
                    "version": key[1],
                    "id": vulnerability["id"],
                    "fix_versions": vulnerability.get("fix_versions", []),
                    "aliases": vulnerability.get("aliases", []),
                }
            )
    if found != set(expected):
        raise ValueError("Advisory inventory does not match the complete lock")
    return findings


def approved(finding, exceptions, today):
    for entry in exceptions:
        if all(entry.get(k) == finding[k] for k in ("package", "version", "id")):
            try:
                valid = (
                    entry["status"] == "approved"
                    and all(
                        entry[k].strip()
                        for k in ("owner", "reviewer", "rationale", "evidence")
                    )
                    and date.fromisoformat(entry["reviewed_at"])
                    <= today
                    <= date.fromisoformat(entry["expires"])
                )
            except (KeyError, TypeError, ValueError):
                valid = False
            if valid:
                return True
    return False


def permissive_license(expression, classifiers):
    if expression:
        from license_expression import get_spdx_licensing

        try:
            licensing = get_spdx_licensing()
            parsed = licensing.parse(expression, validate=True, strict=True)
            return (
                parsed is not None and set(licensing.license_keys(parsed)) <= PERMISSIVE
            )
        except Exception:
            return False
    labels = [c.removeprefix("License :: OSI Approved :: ") for c in classifiers]
    return bool(labels) and set(labels) <= CLASSIFIERS


def license_metadata(key, *, evidence=(), packages=None):
    import requests
    from license_expression import get_spdx_licensing

    name, version = key
    url = f"https://pypi.org/pypi/{name}/{version}/json"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    payload = response.json()
    info = payload["info"]
    if (canonicalize_name(info["name"]), info["version"]) != key:
        raise ValueError("License service returned a different package")
    expression = info.get("license_expression")
    if not expression and info.get("license") and len(info["license"]) < 200:
        try:
            get_spdx_licensing().parse(info["license"], validate=True, strict=True)
            expression = info["license"]
        except Exception:
            pass
    classifiers = [c for c in info.get("classifiers", []) if c.startswith("License ::")]
    resolved = None
    for entry in evidence:
        if (entry["package"], entry["version"]) != key:
            continue
        if expression or classifiers:
            raise ValueError("License metadata changed; recheck artifact evidence")
        wheels = packages[key].get("wheels", [])
        if not any(
            w["url"] == entry["artifact_url"]
            and w["hash"] == "sha256:" + entry["artifact_sha256"]
            for w in wheels
        ):
            raise ValueError("License evidence artifact is not locked")
        artifact = requests.get(entry["artifact_url"], timeout=30)
        artifact.raise_for_status()
        if hashlib.sha256(artifact.content).hexdigest() != entry["artifact_sha256"]:
            raise ValueError("License evidence wheel hash mismatch")
        with zipfile.ZipFile(io.BytesIO(artifact.content)) as wheel:
            license_text = wheel.read(entry["member"])
        if hashlib.sha256(license_text).hexdigest() != entry["license_sha256"]:
            raise ValueError("License evidence text hash mismatch")
        expression = entry["expression"]
        resolved = entry
    return {
        "package": name,
        "version": version,
        "id": "license-review",
        "expression": expression,
        "classifiers": classifiers,
        "license_text_sha256": hashlib.sha256(
            (info.get("license") or "").encode()
        ).hexdigest(),
        "source": url,
        "metadata_screen": "pass"
        if permissive_license(expression, classifiers)
        else "review",
        "artifact_evidence": resolved,
    }


def safe_member(name, size):
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or "\\" in name or size > 128 * 1024**2:
        raise ValueError("Unsafe or oversized archive member")
    return path


def extract_artifact(artifact, destination):
    total = 0
    names = []

    def write(name, size, data):
        nonlocal total
        path = safe_member(name, size)
        total += size
        if total > 256 * 1024**2 or len(names) > 20000:
            raise ValueError("Archive exceeds inspection limit")
        target = destination / path
        if target.exists():
            raise ValueError("Duplicate archive member")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data.read())
        names.append(name)

    if artifact.suffix == ".whl":
        with zipfile.ZipFile(artifact) as archive:
            for member in archive.infolist():
                if member.is_dir():
                    continue
                if (member.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ValueError("Archive symlink")
                with archive.open(member) as data:
                    write(member.filename, member.file_size, data)
    else:
        with tarfile.open(artifact) as archive:
            for member in archive:
                if member.isdir():
                    safe_member(member.name, 0)
                    continue
                if not member.isfile():
                    raise ValueError("Archive special file")
                with archive.extractfile(member) as data:
                    write(member.name, member.size, data)
    if not names:
        raise ValueError("Empty artifact")
    return names


def tracked_manifest(root):
    listed = command(["git", "ls-files", "-z"], cwd=root).stdout.decode().split("\0")
    paths = [name for name in listed if name]
    if not paths or len(paths) != len(set(paths)):
        raise ValueError("Tracked source manifest is empty or ambiguous")
    for name in paths:
        source = root / safe_member(name, 0)
        if source.is_symlink() or not source.is_file():
            raise ValueError("Tracked source is missing or symlinked")
    return paths


def expected_requirements(project):
    requirements = [Requirement(value) for value in project.get("dependencies", [])]
    for extra, values in project.get("optional-dependencies", {}).items():
        for value in values:
            requirement = Requirement(value)
            extra_marker = Marker(f'extra == "{canonicalize_name(extra)}"')
            requirement.marker = (
                Marker(f"({requirement.marker}) and ({extra_marker})")
                if requirement.marker
                else extra_marker
            )
            requirements.append(requirement)
    return sorted(map(str, requirements))


def verify_distribution_metadata(info, root):
    project = tomllib.loads((root / "pyproject.toml").read_text())["project"]
    observed_requirements = sorted(
        str(Requirement(value)) for value in info.get_all("Requires-Dist", [])
    )
    expected_extras = sorted(
        canonicalize_name(value) for value in project.get("optional-dependencies", {})
    )
    observed_extras = sorted(
        canonicalize_name(value) for value in info.get_all("Provides-Extra", [])
    )
    license_file = project.get("license", {}).get("file")
    observed_license = info["License"].replace("\n        ", "\n").strip()
    if (
        info["Summary"] != project["description"]
        or info["Requires-Python"] != project["requires-python"]
        or observed_requirements != expected_requirements(project)
        or observed_extras != expected_extras
        or info.get_all("Classifier", []) != project.get("classifiers", [])
        or info.get_all("License-File", []) != [license_file]
        or observed_license != (root / license_file).read_text().strip()
    ):
        raise ValueError("Artifact metadata differs from pyproject or license")


def verify_artifact_source(artifact, destination, names, root=ROOT):
    if artifact.suffix == ".whl":
        metadata = [n for n in names if n.endswith(".dist-info/METADATA")]
        source_prefix = ""
        if len(metadata) != 1:
            raise ValueError("Wheel metadata missing")
        distribution_prefix = metadata[0].split("/")[0] + "/"
        if any(not n.startswith(("binspect/", distribution_prefix)) for n in names):
            raise ValueError("Unexpected bundled wheel content")
    else:
        metadata = [n for n in names if n.count("/") == 1 and n.endswith("/PKG-INFO")]
        if len(metadata) != 1:
            raise ValueError("Sdist metadata missing")
        prefix = metadata[0].split("/")[0] + "/"
        source_prefix = prefix + "src/"
        tracked = tracked_manifest(root)
        observed_manifest = {
            name.removeprefix(prefix) for name in names if name.startswith(prefix)
        }
        if any(not name.startswith(prefix) for name in names) or observed_manifest != {
            *tracked,
            "PKG-INFO",
        }:
            raise ValueError("Sdist manifest differs from checkout")
        for name in tracked:
            if (destination / prefix / name).read_bytes() != (root / name).read_bytes():
                raise ValueError("Sdist file bytes differ from checkout")
    info = BytesParser().parsebytes((destination / metadata[0]).read_bytes())
    expected_version = re.search(
        r'^__version__ = "([^"]+)"',
        (root / "src/binspect/__init__.py").read_text(),
        re.MULTILINE,
    )[1]
    if (
        canonicalize_name(info["Name"]) != "binspect-regression"
        or info["Version"] != expected_version
    ):
        raise ValueError("Artifact name/version differs from checkout")
    verify_distribution_metadata(info, root)
    expected = {
        str(p.relative_to(root / "src")): p
        for p in (root / "src/binspect").rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
    }
    observed = {
        n.removeprefix(source_prefix)
        for n in names
        if n.startswith(source_prefix + "binspect/")
    }
    if observed != set(expected):
        raise ValueError("Artifact library files differ from checkout")
    for name, source in expected.items():
        if (destination / source_prefix / name).read_bytes() != source.read_bytes():
            raise ValueError("Artifact library bytes differ from checkout")
    return info["Version"]


def scanner(work, pins):
    import requests

    system = {"Darwin": "darwin", "Linux": "linux"}[platform.system()]
    arch = {"arm64": "arm64", "aarch64": "arm64", "x86_64": "x64"}[platform.machine()]
    asset = f"gitleaks_{pins['version']}_{system}_{arch}.tar.gz"
    expected = pins["archives"][asset]
    response = requests.get(
        f"https://github.com/gitleaks/gitleaks/releases/download/v{pins['version']}/{asset}",
        timeout=60,
    )
    response.raise_for_status()
    archive = work / asset
    archive.write_bytes(response.content)
    if digest(archive) != expected:
        raise ValueError("Scanner archive checksum mismatch")
    executable = work / "gitleaks"
    with tarfile.open(archive) as contents:
        member = contents.getmember("gitleaks")
        if not member.isfile():
            raise ValueError("Scanner is not a regular file")
        executable.write_bytes(contents.extractfile(member).read())
    executable.chmod(0o700)
    if command([executable, "version"]).stdout.decode().strip() != pins["version"]:
        raise ValueError("Scanner version mismatch")
    return executable


def scan(executable, target, report, *, history=False, config, work):
    args = [
        executable,
        "git" if history else "dir",
        str(target),
        "--redact=100",
        "--no-banner",
        "--no-color",
        "--report-format=json",
        "--report-path",
        str(report),
        "--ignore-gitleaks-allow",
        "--gitleaks-ignore-path",
        str(work / "empty-ignore"),
        "--config",
        str(config),
        "--max-archive-depth=3",
        "--max-decode-depth=3",
        "--timeout=300",
    ]
    if history:
        args.append("--log-opts=--all --full-history")
    result = command(args, accepted=(0, 1), timeout=360)
    raw = json.loads(report.read_text())
    findings = [
        {
            "rule": f["RuleID"],
            "file": f["File"],
            "line": f["StartLine"],
            "commit": f.get("Commit", ""),
        }
        for f in raw
    ]
    # Raw records can include author/message/match fields even when redacted.
    report.unlink()
    if bool(findings) != (result.returncode == 1):
        raise ValueError("Secret scanner exit/report mismatch")
    return findings


def action_pins(root):
    refs = []
    for path in sorted((root / ".github/workflows").glob("*.y*ml")):
        for match in re.finditer(r"\buses:\s*([^\s#]+)", path.read_text()):
            ref = match[1]
            if ref.startswith("./"):
                continue
            if not re.fullmatch(r"[\w.-]+/[\w./-]+@[0-9a-f]{40}", ref):
                raise ValueError("Mutable third-party action reference")
            refs.append(ref)
    if not refs:
        raise ValueError("No workflow actions inspected")
    return sorted(set(refs))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=ROOT / ".work/supply-chain/result.json"
    )
    parser.add_argument(
        "--artifacts", type=Path, help="Inspect existing artifacts instead of building"
    )
    args = parser.parse_args()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.unlink(missing_ok=True)
    for filename in ("licenses.json", "sbom.cdx.json"):
        output.with_name(filename).unlink(missing_ok=True)
    lock = tomllib.loads((ROOT / "uv.lock").read_text())
    packages = pinned_packages(lock)
    policy = json.loads((ROOT / "validation/supply-chain-exceptions.json").read_text())
    pins = json.loads((ROOT / "validation/scanner-pins.json").read_text())
    license_evidence = json.loads(
        (ROOT / "validation/license-evidence.json").read_text()
    )
    before = {
        str(p.relative_to(ROOT)): digest(p)
        for p in [
            ROOT / "uv.lock",
            ROOT / "pyproject.toml",
            *sorted((ROOT / "src").rglob("*.py")),
            *sorted((ROOT / "validation").glob("supply*")),
            ROOT / "validation/scanner-pins.json",
            ROOT / "validation/gitleaks.toml",
            ROOT / "validation/license-evidence.json",
            ROOT / "validation/secret-fingerprints.json",
        ]
    }
    result = {
        "schema_version": 1,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "source_revision": command(["git", "rev-parse", "HEAD"])
        .stdout.decode()
        .strip(),
        "sha256": before,
        "checks": {},
        "locked_versions": len(packages),
        "tools": {
            "uv": command(["uv", "--version"]).stdout.decode().strip(),
            "pip-audit": importlib.metadata.version("pip-audit"),
            "gitleaks": pins["version"],
        },
    }

    def check(name, function):
        try:
            result["checks"][name] = function()
        except Exception as error:
            result["checks"][name] = {
                "status": "unverified",
                "error_type": type(error).__name__,
            }
        print(name, result["checks"][name]["status"], flush=True)

    today = datetime.now(timezone.utc).date()
    with tempfile.TemporaryDirectory(prefix="binspect-supply-chain-") as directory:
        work = Path(directory)

        def actions():
            return {"status": "pass", "refs": action_pins(ROOT)}

        check("actions", actions)

        def vulnerabilities():
            findings = []
            for i, batch in enumerate(audit_batches(packages)):
                requirements = work / f"pins-{i}.txt"
                requirements.write_text(
                    "".join(f"{n}=={v}\n" for n, v in batch.items())
                )
                report = work / f"audit-{i}.json"
                run = command(
                    [
                        sys.executable,
                        "-m",
                        "pip_audit",
                        "--strict",
                        "--no-deps",
                        "--disable-pip",
                        "--progress-spinner=off",
                        "--desc=off",
                        "--cache-dir",
                        str(work / "advisory-cache"),
                        "-r",
                        str(requirements),
                        "-f",
                        "json",
                        "-o",
                        str(report),
                    ],
                    accepted=(0, 1),
                )
                observed = validate_audit(json.loads(report.read_text()), batch.items())
                if bool(observed) != (run.returncode == 1):
                    raise ValueError("Advisory exit/report mismatch")
                findings.extend(observed)
            unresolved = [
                f for f in findings if not approved(f, policy["vulnerabilities"], today)
            ]
            return {
                "status": "fail" if unresolved else "pass",
                "audited_versions": len(packages),
                "findings": findings,
                "unresolved": unresolved,
            }

        check("vulnerabilities", vulnerabilities)
        licenses = []

        def licensing():
            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
                licenses.extend(
                    pool.map(
                        lambda key: license_metadata(
                            key, evidence=license_evidence, packages=packages
                        ),
                        sorted(packages),
                    )
                )
            unresolved = [
                f
                for f in licenses
                if f["metadata_screen"] != "pass"
                and not approved(f, policy["licenses"], today)
            ]
            return {
                "status": "fail" if unresolved else "pass",
                "inspected_versions": len(licenses),
                "unresolved": unresolved,
            }

        check("licenses", licensing)
        if licenses:
            output.with_name("licenses.json").write_text(
                json.dumps(licenses, indent=2) + "\n"
            )
        artifacts = []
        extracted = work / "artifacts"

        def artifact_build():
            dist = args.artifacts.resolve() if args.artifacts else work / "dist"
            if not args.artifacts:
                command(
                    [
                        sys.executable,
                        "-m",
                        "build",
                        "--no-isolation",
                        "--outdir",
                        str(dist),
                    ]
                )
            artifacts.extend(sorted(dist.glob("*")))
            if (
                len(artifacts) != 2
                or sum(p.suffix == ".whl" for p in artifacts) != 1
                or sum(p.name.endswith(".tar.gz") for p in artifacts) != 1
            ):
                raise ValueError("Expected exactly one wheel and one sdist")
            command([sys.executable, "-m", "twine", "check", *map(str, artifacts)])
            records = []
            for artifact in artifacts:
                names = extract_artifact(artifact, extracted / artifact.name)
                version = verify_artifact_source(
                    artifact, extracted / artifact.name, names
                )
                records.append(
                    {
                        "name": artifact.name,
                        "sha256": digest(artifact),
                        "files": len(names),
                        "version": version,
                    }
                )
                if not args.artifacts:
                    retained = output.parent / "artifacts"
                    retained.mkdir(exist_ok=True)
                    shutil.copyfile(artifact, retained / artifact.name)
            return {
                "status": "pass",
                "artifacts": records,
                "build_tools": {
                    n: importlib.metadata.version(n)
                    for n in ("build", "hatchling", "twine")
                },
            }

        check("artifacts", artifact_build)

        def secrets():
            if (
                command(["git", "rev-parse", "--is-shallow-repository"]).stdout.strip()
                != b"false"
            ):
                raise ValueError("Full history required")
            executable = scanner(work, pins)
            (work / "empty-ignore").write_text("")
            config = ROOT / "validation/gitleaks.toml"
            canary = work / "canary"
            canary.mkdir()
            token = (
                "ghp_"
                + hashlib.sha256(b"binspect synthetic scanner canary").hexdigest()[:36]
            )
            (canary / "synthetic.txt").write_text(token)
            detected = scan(
                executable, canary, work / "canary.json", config=config, work=work
            )
            if not any(f["rule"] == "github-pat" for f in detected):
                raise ValueError("Secret scanner failed its synthetic canary")
            tracked = work / "tracked"
            for name in command(["git", "ls-files", "-z"]).stdout.decode().split("\0"):
                if not name:
                    continue
                source = ROOT / name
                if source.is_symlink() or not source.is_file():
                    raise ValueError("Missing or symlinked tracked file")
                target = tracked / safe_member(name, source.stat().st_size)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
            if result["checks"]["artifacts"]["status"] != "pass":
                raise ValueError("Artifacts unavailable for secret inspection")
            findings = {}
            for label, target in (
                ("history", ROOT),
                ("tracked", tracked),
                ("artifacts", extracted),
            ):
                findings[label] = scan(
                    executable,
                    target,
                    work / f"{label}.json",
                    history=label == "history",
                    config=config,
                    work=work,
                )
            return {
                "status": "fail" if any(findings.values()) else "pass",
                "findings": findings,
                "commits": int(command(["git", "rev-list", "--all", "--count"]).stdout),
            }

        check("secrets", secrets)

        def sbom():
            from cyclonedx.schema import SchemaVersion
            from cyclonedx.validation.json import JsonStrictValidator

            if result["checks"]["artifacts"]["status"] != "pass" or len(
                licenses
            ) != len(packages):
                raise ValueError("Artifact/license inventory incomplete")
            raw = work / "lock.cdx.json"
            command(
                [
                    "uv",
                    "export",
                    "--frozen",
                    "--all-extras",
                    "--all-groups",
                    "--format=cyclonedx1.5",
                    "--output-file",
                    str(raw),
                ]
            )
            bom = json.loads(raw.read_text())
            observed = {
                (canonicalize_name(c["name"]), c["version"]) for c in bom["components"]
            }
            if observed != set(packages):
                raise ValueError("SBOM omits locked package versions")
            by_package = {(x["package"], x["version"]): x for x in licenses}
            for component in bom["components"]:
                entry = by_package[
                    (canonicalize_name(component["name"]), component["version"])
                ]
                if entry["expression"]:
                    component["licenses"] = [{"expression": entry["expression"]}]
                elif entry["classifiers"]:
                    component["licenses"] = [
                        {"license": {"name": x}} for x in entry["classifiers"]
                    ]
            wheel = next(p for p in artifacts if p.suffix == ".whl")
            with zipfile.ZipFile(wheel) as contents:
                metadata = [
                    n for n in contents.namelist() if n.endswith(".dist-info/METADATA")
                ]
                if len(metadata) != 1:
                    raise ValueError("Wheel metadata identity missing")
                info = BytesParser().parsebytes(contents.read(metadata[0]))
            root = bom["metadata"]["component"]
            if canonicalize_name(info["Name"]) != "binspect-regression":
                raise ValueError("Unexpected artifact distribution")
            root.update(
                version=info["Version"],
                purl=f"pkg:pypi/binspect-regression@{info['Version']}",
                licenses=[{"license": {"id": "MIT"}}],
            )
            for artifact in artifacts:
                ref = f"artifact:{artifact.name}:{digest(artifact)}"
                bom["components"].append(
                    {
                        "type": "file",
                        "bom-ref": ref,
                        "name": artifact.name,
                        "hashes": [{"alg": "SHA-256", "content": digest(artifact)}],
                        "properties": [
                            {
                                "name": "binspect:scope",
                                "value": "inspected artifact; separate dependencies",
                            }
                        ],
                    }
                )
                bom["dependencies"].append({"ref": ref, "dependsOn": [root["bom-ref"]]})
            encoded = json.dumps(bom, indent=2) + "\n"
            errors = JsonStrictValidator(SchemaVersion.V1_5).validate_str(encoded)
            if errors:
                raise ValueError("CycloneDX schema validation failed")
            target = output.with_name("sbom.cdx.json")
            target.write_text(encoded)
            return {
                "status": "pass",
                "components": len(bom["components"]),
                "schema": "CycloneDX 1.5",
                "sha256": digest(target),
            }

        check("sbom", sbom)
    if any(digest(ROOT / p) != h for p, h in before.items()):
        result["checks"]["source_identity"] = {"status": "unverified"}
    result["status"] = (
        "pass"
        if all(c["status"] == "pass" for c in result["checks"].values())
        else "fail"
    )
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"Supply-chain gate: {result['status']}; report: {output}")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
