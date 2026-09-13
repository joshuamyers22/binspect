"""Execute fenced Python examples and the quickstart without touching tracked files.

Every Python fence in the guide and published contract examples is executed, in
page order with one fresh process/temporary directory per page. Generated API
docstring examples are reference material, not part of this executable guide.
Run from the repository root with the frozen docs/pandas/DPI environment.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FENCE = re.compile(r"^( {0,3})(`{3,}|~{3,})(.*)$")


def example_source(markdown: str) -> tuple[str, int]:
    """Extract all Python fences, preserving source line numbers for tracebacks."""
    output: list[str] = []
    fence = ""
    executable = False
    indent = 0
    count = 0
    for line in markdown.splitlines():
        match = FENCE.match(line)
        if not fence and match:
            spaces, fence, info = match.groups()
            indent = len(spaces)
            language = info.strip()
            if language.split(maxsplit=1)[:1] in (["python"], ["py"]):
                if language not in ("python", "py"):
                    raise ValueError(
                        "Python fences must use plain python or py labels."
                    )
                executable = True
                count += 1
            output.append("")
        elif (
            fence
            and match
            and match[2][0] == fence[0]
            and len(match[2]) >= len(fence)
            and not match[3].strip()
        ):
            fence = ""
            executable = False
            output.append("")
        else:
            removed = min(indent, len(line) - len(line.lstrip(" ")))
            output.append(line[removed:] if executable else "")
    if fence:
        raise ValueError("Unclosed Markdown code fence.")
    return "\n".join(output) + "\n", count


def run_page(path: Path, *, timeout: int = 60) -> int:
    """Run examples from one page; failures and timeouts fail the calling gate."""
    source, count = example_source(path.read_text())
    if not count:
        return 0
    with tempfile.TemporaryDirectory(prefix="binspect-docs-") as directory:
        script = Path(directory) / "examples.py"
        script.write_text(source)
        # Compile with the source page's name so failures identify the exact line.
        command = (
            "from pathlib import Path; "
            f"exec(compile(Path({str(script)!r}).read_text(), {str(path)!r}, 'exec'))"
        )
        subprocess.run(
            [sys.executable, "-c", command],
            cwd=directory,
            env={**os.environ, "MPLBACKEND": "Agg"},
            check=True,
            timeout=timeout,
        )
    label = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
    print(f"PASS {label}: {count} Python blocks", flush=True)
    return count


def main() -> None:
    pages = sorted((ROOT / "docs/site").rglob("*.md"))
    pages += [
        ROOT / "README.md",
        ROOT / "docs/INPUT_OUTPUT_CONTRACT.md",
        ROOT / "docs/COMPATIBILITY.md",
    ]
    count = sum(run_page(path) for path in pages)
    if not count:
        raise ValueError("No executable documentation examples found.")
    with tempfile.TemporaryDirectory(prefix="binspect-quickstart-") as directory:
        output = Path(directory) / "quickstart.png"
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "examples/quickstart.py"),
                "--output",
                str(output),
            ],
            cwd=directory,
            env={**os.environ, "MPLBACKEND": "Agg"},
            check=True,
            timeout=60,
        )
        if not output.is_file() or output.stat().st_size == 0:
            raise ValueError("Quickstart did not produce its requested figure.")
    print(f"PASS {count} documentation blocks and quickstart figure", flush=True)


if __name__ == "__main__":
    main()
