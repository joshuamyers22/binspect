"""Documentation gates must execute examples and retain failing evidence."""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "documentation", Path(__file__).resolve().parents[1] / "validation/documentation.py"
)
assert SPEC is not None and SPEC.loader is not None
documentation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(documentation)


def test_page_executes_all_blocks_with_shared_state_in_temporary_directory(tmp_path):
    page = tmp_path / "guide.md"
    page.write_text(
        "# Example\n\n```python\nfrom pathlib import Path\nx = 7\n```\n"
        "\nProse\n\n~~~py\nassert x == 7\nPath('output.txt').write_text('example')\n~~~\n"
    )
    assert documentation.run_page(page) == 2
    assert not (tmp_path / "output.txt").exists()


def test_failed_example_preserves_page_and_line_in_traceback(tmp_path, capfd):
    page = tmp_path / "broken.md"
    page.write_text("# Broken\n\n```python\nassert False, 'broken example'\n```\n")
    with pytest.raises(subprocess.CalledProcessError):
        documentation.run_page(page)
    error = capfd.readouterr().err
    assert str(page) in error and "line 4" in error and "broken example" in error


@pytest.mark.parametrize(
    "markdown",
    ["```python\nx=1\n", "```python title=example\nx=1\n```\n"],
)
def test_malformed_python_fences_fail_instead_of_silently_skipping(markdown):
    with pytest.raises(ValueError):
        documentation.example_source(markdown)


def test_prose_and_non_python_fences_are_not_executed(tmp_path):
    page = tmp_path / "reference.md"
    page.write_text("# Reference\n\n```text\nthis is not Python\n```\n")
    assert documentation.run_page(page) == 0


def test_indented_fences_and_longer_closing_fences_are_executed(tmp_path):
    page = tmp_path / "indented.md"
    page.write_text("# Example\n\n   ```python\n   assert False\n   ````\n")
    with pytest.raises(subprocess.CalledProcessError):
        documentation.run_page(page)
