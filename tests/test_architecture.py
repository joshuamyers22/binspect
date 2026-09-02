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


def test_comparison_result_model_does_not_depend_on_api_entrypoint() -> None:
    tree = ast.parse(Path("src/binspect/comparison_results.py").read_text())
    modules = {
        node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    }
    assert "api" not in modules


def test_visual_layer_policy_does_not_depend_on_rendering_adapters() -> None:
    source = Path("src/binspect/viz/layer_policy.py").read_text()
    assert "matplotlib" not in source
    assert "from .layers" not in source
    assert "from .theme" not in source


def test_visual_renderer_does_not_own_sampling_or_baseline_policy() -> None:
    source = Path("src/binspect/viz/layers.py").read_text()
    assert "default_rng" not in source
    assert "target ==" not in source
