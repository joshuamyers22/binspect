"""Run the checkout's executable gallery page and retain its synthetic artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import runpy
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs/site/guide/gallery.md"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".work/gallery")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    helpers = runpy.run_path(str(ROOT / "validation/documentation.py"))
    extract = helpers["example_source"]
    source, count = extract(PAGE.read_text())
    with tempfile.TemporaryDirectory(prefix="binspect-gallery-") as directory:
        script = Path(directory) / "gallery.py"
        script.write_text(source)
        command = (
            "from pathlib import Path; "
            f"exec(compile(Path({str(script)!r}).read_text(), {str(PAGE)!r}, 'exec'))"
        )
        subprocess.run(
            [sys.executable, "-c", command],
            cwd=output,
            env={**os.environ, "MPLBACKEND": "Agg"},
            check=True,
            timeout=60,
        )
    path = output / "manifest.json"
    manifest = json.loads(path.read_text())
    manifest["source_sha256"] = {
        str(item.relative_to(ROOT)): hashlib.sha256(item.read_bytes()).hexdigest()
        for item in (PAGE, Path(__file__).resolve(), ROOT / "uv.lock")
    }
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"Executed {count} gallery blocks; figures and manifest: {output}")


if __name__ == "__main__":
    main()
