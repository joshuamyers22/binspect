"""Executable dependency rules for result presentation policy."""

import ast
from pathlib import Path


def test_result_tables_do_not_depend_on_api_or_visualization_adapters() -> None:
    tree = ast.parse(Path("src/binspect/result_tables.py").read_text())
    modules = {
        node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    }
    assert modules.isdisjoint({"api", "viz", "viz.figure", "viz.audit"})
