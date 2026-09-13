"""Compare installed code with existing references in locked/current environments."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCES = (
    "test_dpi.py",
    "test_binsreg_contract.py",
    "test_binsreg_adapter.py",
    "test_inference.py",
)
EXPECTED_TESTS = 74


def fingerprint():
    paths = [
        ROOT / "pyproject.toml",
        ROOT / "uv.lock",
        ROOT / "validation/dependency_smoke.py",
        Path(__file__),
        *sorted((ROOT / "src/binspect").rglob("*")),
        *(ROOT / "tests/integration" / name for name in REFERENCES),
    ]
    return [
        {
            "path": str(p.relative_to(ROOT)),
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
        }
        for p in paths
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
    ]


def reference_result(path, returncode):
    """No tests, skips, malformed reports or interrupted runs can be a pass."""
    try:
        cases = list(ET.parse(path).getroot().iter("testcase"))
    except (OSError, ET.ParseError):
        return {"status": "unverified", "reason": "missing_or_invalid_test_report"}
    failures = [
        {"test": c.get("name", "unknown"), "module": c.get("classname", "unknown")}
        for c in cases
        if c.find("failure") is not None or c.find("error") is not None
    ]
    skipped = sum(c.find("skipped") is not None for c in cases)
    status = "fail" if failures else "pass"
    if not failures and (returncode != 0 or len(cases) != EXPECTED_TESTS or skipped):
        status = "unverified"
    return {
        "status": status,
        "collected": len(cases),
        "skipped": skipped,
        "failures": failures,
    }


def probe(profile, python, output):
    output.mkdir(parents=True, exist_ok=True)
    report_path = output / "result.json"
    report_path.unlink(missing_ok=True)
    before = fingerprint()
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    record = {
        "schema_version": 1,
        "profile": profile,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "source_revision": revision,
        "inputs": before,
        "owner": "Josh Myers",
        "status": "unverified",
        "stages": [],
    }
    log = output / "stages.jsonl"
    log.write_text("")

    def execute(stage, args, *, cwd, accepted=(0,)):
        started = time.monotonic()
        try:
            result = subprocess.run(
                args,
                cwd=cwd,
                capture_output=True,
                timeout=600,
                env={
                    **os.environ,
                    "MPLBACKEND": "Agg",
                    "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
                },
            )
            event = {"stage": stage, "returncode": result.returncode}
        except (OSError, subprocess.TimeoutExpired):
            event = {"stage": stage, "returncode": None}
            result = None
        event["seconds"] = round(time.monotonic() - started, 3)
        record["stages"].append(event)
        with log.open("a") as stream:
            stream.write(json.dumps(event, sort_keys=True) + "\n")
        if result is None or result.returncode not in accepted:
            raise RuntimeError(stage)
        return result

    try:
        with tempfile.TemporaryDirectory(prefix="binspect-maintenance-") as directory:
            work = Path(directory)
            wheels = work / "wheels"
            execute(
                "locked_wheel_build",
                [
                    sys.executable,
                    "-m",
                    "build",
                    "--wheel",
                    "--no-isolation",
                    "--outdir",
                    str(wheels),
                ],
                cwd=ROOT,
            )
            (wheel,) = wheels.glob("*.whl")
            record["wheel_sha256"] = hashlib.sha256(wheel.read_bytes()).hexdigest()
            env = work / "venv"
            execute(
                "create_environment",
                ["uv", "venv", "--python", python, str(env)],
                cwd=work,
            )
            executable = env / "bin/python"
            installer = ["uv", "pip", "install", "--python", str(executable)]
            if profile == "locked":
                requirements = work / "requirements.txt"
                execute(
                    "export_lock",
                    [
                        "uv",
                        "export",
                        "--frozen",
                        "--no-emit-project",
                        "--extra",
                        "dev",
                        "--extra",
                        "dpi",
                        "--extra",
                        "validation",
                        "--output-file",
                        str(requirements),
                    ],
                    cwd=ROOT,
                )
                execute(
                    "install_dependencies",
                    [*installer, "--require-hashes", "-r", str(requirements)],
                    cwd=work,
                )
                execute(
                    "install_wheel", [*installer, "--no-deps", str(wheel)], cwd=work
                )
            else:
                # The validation extra intentionally stays out: it pins Statsmodels.
                execute(
                    "resolve_current",
                    [
                        *installer,
                        "--refresh",
                        f"{wheel}[dpi,pandas]",
                        "statsmodels",
                        "pytest>=8.0",
                    ],
                    cwd=work,
                )
            execute(
                "dependency_consistency",
                ["uv", "pip", "check", "--python", str(executable)],
                cwd=work,
            )
            identity = work / "identity.py"
            identity.write_text("""import importlib.metadata as m
import json, pathlib, platform, sys, zipfile
import binspect
root = pathlib.Path(binspect.__file__).parent.parent
assert "site-packages" in root.parts
assert m.version("binspect-regression") == binspect.__version__
with zipfile.ZipFile(sys.argv[1]) as wheel:
    for name in wheel.namelist():
        if name.startswith("binspect/") and not name.endswith("/"):
            assert (root / name).read_bytes() == wheel.read(name)
direct = m.distribution("binspect-regression").read_text("direct_url.json")
assert direct and not json.loads(direct).get("dir_info", {}).get("editable", False)
print(json.dumps({"python": platform.python_version(), "system": platform.system(),
    "versions": {d.metadata["Name"]: d.version for d in m.distributions()}}))
""")
            result = execute(
                "installed_identity",
                [str(executable), "-I", str(identity), str(wheel)],
                cwd=work,
            )
            record["environment"] = json.loads(result.stdout)
            tests = work / "tests"
            tests.mkdir()
            for name in REFERENCES:
                shutil.copyfile(ROOT / "tests/integration" / name, tests / name)
            config = work / "pytest.ini"
            config.write_text(
                "[pytest]\nmarkers =\n    integration: independent references\n"
            )
            junit = work / "results.xml"
            result = execute(
                "references",
                [
                    str(executable),
                    "-I",
                    "-m",
                    "pytest",
                    str(tests),
                    "-c",
                    str(config),
                    "--strict-markers",
                    "-m",
                    "integration",
                    f"--junitxml={junit}",
                    "-q",
                ],
                cwd=work,
                accepted=(0, 1, 2, 3, 4, 5),
            )
            record["references"] = reference_result(junit, result.returncode)
            record["status"] = record["references"]["status"]
            journey = work / "journey.json"
            execute(
                "installed_journey",
                [
                    str(executable),
                    "-I",
                    str(ROOT / "validation/dependency_smoke.py"),
                    "--pandas",
                    "--dpi",
                    "--output",
                    str(journey),
                ],
                cwd=work,
            )
            record["journey"] = json.loads(journey.read_text())
            if record["journey"].get("status") != "pass":
                record["status"] = "unverified"
    except (RuntimeError, ValueError, OSError):
        record.update(
            status="unverified", reason="stage_failed_or_evidence_unavailable"
        )
    if (
        fingerprint() != before
        or subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
        != revision
    ):
        record.update(status="unverified", reason="inputs_changed_during_run")
    record["release_hold"] = record["status"] != "pass"
    record["triage"] = (
        "Review at monthly maintenance and before release."
        if record["status"] == "pass"
        else (
            "Josh Myers: investigate before the next release; classify infrastructure, "
            "compatibility or numerical divergence."
        )
    )
    report_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(f"{profile}: {record['status']}; evidence: {report_path}")
    return record["status"] == "pass"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("locked", "current"), required=True)
    parser.add_argument("--python", default="3.12")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(
        0 if probe(args.profile, args.python, args.output.resolve()) else 1
    )


if __name__ == "__main__":
    main()
