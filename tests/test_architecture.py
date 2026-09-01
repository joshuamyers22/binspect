"""Executable dependency rules for result presentation policy."""

import ast
from pathlib import Path


def test_result_tables_do_not_depend_on_api_or_visualization_adapters() -> None:
    tree = ast.parse(Path("src/binspect/result_tables.py").read_text())
    modules = {
        node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    }
    assert modules.isdisjoint({"api", "viz", "viz.figure", "viz.audit"})


def test_input_normalization_does_not_depend_on_estimation_or_presentation() -> None:
    tree = ast.parse(Path("src/binspect/input_data.py").read_text())
    modules = {
        node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    }
    assert modules.isdisjoint({"api", "comparison", "results", "viz"})
