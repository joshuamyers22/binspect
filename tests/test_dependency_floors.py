"""Reject floor evidence that silently tests newer or undeclared versions."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "dependency_smoke",
    Path(__file__).resolve().parents[1] / "validation/dependency_smoke.py",
)
assert SPEC is not None and SPEC.loader is not None
smoke = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(smoke)


@pytest.fixture
def floors(tmp_path, monkeypatch):
    path = tmp_path / "floors.txt"
    path.write_text("polars==1.0.0\npandas==2.0.0\nbinsreg==3.2.1\n")
    monkeypatch.setattr(
        smoke.importlib.metadata,
        "requires",
        lambda _: [
            "polars>=1.0",
            'pandas>=2.0; extra == "pandas"',
            'binsreg>=3.2.1; extra == "dpi"',
            'pytest>=8; extra == "dev"',
        ],
    )
    versions = {"polars": "1.0.0", "pandas": "2.0.0", "binsreg": "3.2.1"}
    monkeypatch.setattr(smoke.importlib.metadata, "version", versions.__getitem__)
    return path, versions


def test_direct_floor_versions_pass(floors):
    path, _ = floors
    smoke.verify_floors(path, pandas=True, dpi=False)


def test_upgraded_direct_floor_fails(floors):
    path, versions = floors
    versions["polars"] = "1.44.2"
    with pytest.raises(AssertionError, match="polars"):
        smoke.verify_floors(path, pandas=False, dpi=False)


def test_floor_file_cannot_omit_or_change_a_declared_minimum(floors):
    path, _ = floors
    path.write_text("polars==1.1.0\npandas==2.0.0\n")
    with pytest.raises(AssertionError):
        smoke.verify_floors(path, pandas=True, dpi=False)


def test_dpi_transitive_pandas_may_exceed_standalone_extra_floor(floors):
    path, versions = floors
    versions["pandas"] = "2.3.3"
    smoke.verify_floors(path, pandas=True, dpi=True)
    with pytest.raises(AssertionError, match="pandas"):
        smoke.verify_floors(path, pandas=True, dpi=False)
