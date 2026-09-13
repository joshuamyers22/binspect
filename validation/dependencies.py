"""Build isolated dependency configurations and run installed-code contracts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILES = ("minimal", "dpi", "locked", "lower", "lower-pandas", "lower-dpi", "current")


def run(command, **kwargs):
    subprocess.run(command, check=True, timeout=600, **kwargs)


def source_hashes():
    return {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (
            ROOT / "pyproject.toml",
            ROOT / "uv.lock",
            ROOT / "validation/dependency-floors.txt",
            ROOT / "validation/dependency_smoke.py",
            ROOT / "validation/dependencies.py",
            *sorted((ROOT / "src/binspect").rglob("*.py")),
        )
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=PROFILES, required=True)
    parser.add_argument("--python", default="3.12")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.unlink(missing_ok=True)
    before = source_hashes()
    pandas = args.profile in ("dpi", "locked", "lower-pandas", "lower-dpi", "current")
    dpi = args.profile in ("dpi", "locked", "lower-dpi", "current")
    with tempfile.TemporaryDirectory(prefix="binspect-dependencies-") as directory:
        work = Path(directory)
        environment = work / "venv"
        run(["uv", "venv", "--python", args.python, str(environment)])
        python = environment / "bin/python"
        install = ["uv", "pip", "install", "--python", str(python)]
        if args.profile in ("minimal", "dpi", "locked"):
            requirements = work / "requirements.txt"
            export = [
                "uv",
                "export",
                "--frozen",
                "--no-dev",
                "--no-emit-project",
                "--no-hashes",
                "--output-file",
                str(requirements),
            ]
            if args.profile == "locked":
                export += ["--all-extras"]
            elif dpi:
                export += ["--extra", "dpi"]
            run(export, cwd=ROOT, stdout=subprocess.DEVNULL)
            run([*install, "-r", str(requirements)])
            run([*install, "--no-deps", str(ROOT)])
        else:
            extras = "[dpi]" if dpi else "[pandas]" if pandas else ""
            if args.profile == "current":
                extras = "[dpi,pandas]"
            arguments = [*install, "--refresh", f"{ROOT}{extras}"]
            if args.profile.startswith("lower"):
                constraints = work / "floors.txt"
                # DPI supplies pandas transitively; its constraints determine
                # that version. The pandas extra's direct floor has its own job.
                constraints.write_text(
                    "\n".join(
                        line
                        for line in (ROOT / "validation/dependency-floors.txt")
                        .read_text()
                        .splitlines()
                        if not (
                            args.profile == "lower-dpi" and line.startswith("pandas==")
                        )
                    )
                    + "\n"
                )
                arguments += ["-c", str(constraints)]
            run(arguments)
        run(["uv", "pip", "check", "--python", str(python)])
        result = work / "result.json"
        smoke = [
            str(python),
            "-I",
            str(ROOT / "validation/dependency_smoke.py"),
            "--output",
            str(result),
        ]
        if pandas:
            smoke.append("--pandas")
        if dpi:
            smoke.append("--dpi")
        if args.profile.startswith("lower"):
            smoke += ["--floors", str(ROOT / "validation/dependency-floors.txt")]
        run(smoke, cwd=work, env={**os.environ, "MPLBACKEND": "Agg"})
        record = json.loads(result.read_text())
    record.update(
        profile=args.profile,
        checked_at=datetime.now(timezone.utc).isoformat(),
        source_revision=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
    )
    if source_hashes() != before:
        raise RuntimeError("Source/configuration changed during the dependency check.")
    record["sha256"] = before
    args.output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(json.dumps(record, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
