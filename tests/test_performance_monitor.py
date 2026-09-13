"""Benchmark children must stop when memory observation or resource guards fail."""

from __future__ import annotations

import runpy
from pathlib import Path
from types import SimpleNamespace

import pytest

HARNESS = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "validation/performance.py")
)


@pytest.mark.parametrize("condition", ["monitor", "rss", "timeout"])
def test_trial_terminates_child_on_guard_failure(condition, monkeypatch, tmp_path):
    class Child:
        pid = 123
        returncode = None
        killed = False
        waited = False

        def poll(self):
            return self.returncode

        def kill(self):
            self.killed = True
            self.returncode = -9

        def wait(self):
            self.waited = True

    child = Child()
    subprocess = HARNESS["subprocess"]
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: child)
    probe = SimpleNamespace(returncode=0, stdout="128")
    if condition == "monitor":
        probe.returncode, probe.stdout = 1, ""
    elif condition == "rss":
        probe.stdout = str(HARNESS["RSS_LIMIT"] // 1024 + 1)
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: probe)
    readings = iter([0, HARNESS["TIME_LIMIT"] + 1])
    monkeypatch.setattr(HARNESS["time"], "perf_counter", lambda: next(readings))
    if condition == "monitor":
        with pytest.raises(RuntimeError, match="monitor unavailable"):
            HARNESS["trial"]({"name": "fixture"}, tmp_path)
    else:
        result = HARNESS["trial"]({"name": "fixture"}, tmp_path)
        assert result["status"] == ("rss_limit" if condition == "rss" else "time_limit")
    assert child.killed and child.waited
