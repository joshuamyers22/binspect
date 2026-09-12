"""Prespecified C3 development simulations; no final-assessment seed access."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.metadata
import io
import json
import math
import subprocess
import sys
import warnings
from collections import Counter
from pathlib import Path

import numpy as np
from scipy import stats

import binspect
from binspect.exceptions import BinspectError

ROOT = Path(__file__).resolve().parents[1]
REPETITIONS = 1000
NOMINAL = 0.95
MARGIN = 4 * math.sqrt(NOMINAL * (1 - NOMINAL) / REPETITIONS)
SCENARIOS = (
    ("fixed_nonflat", (), False, True),
    ("quantile_nonflat", (), False, False),
    ("dpi_nonflat", (), False, False),
    ("cluster_60", (10,) * 60, False, True),
    ("cluster_5", (120,) * 5, False, False),
    ("cluster_2", (300,) * 2, False, False),
    ("cluster_3_unbalanced", (480, 60, 60), False, False),
    ("weighted_cluster_3", (480, 60, 60), True, False),
)


def population_mean(lower: float, upper: float, *, quadratic: bool) -> float:
    """Integral of the prespecified mean over a uniform population interval."""
    if not -1 <= lower < upper <= 1:
        raise ValueError("invalid population interval")
    midpoint = (lower + upper) / 2
    if quadratic:
        return 2 + midpoint + 2 * (lower**2 + lower * upper + upper**2) / 3
    return 2 + 1.5 * midpoint


def anchor_index(partition: np.ndarray, interval_ids: np.ndarray) -> int:
    original_id = int(np.searchsorted(partition, 0.0, side="right")) - 1
    if original_id < 0 or original_id >= len(partition) - 1:
        raise ValueError("anchor outside partition")
    positions = np.flatnonzero(interval_ids == original_id)
    if len(positions) != 1:
        raise ValueError("anchor interval absent")
    return int(positions[0])


class Metric:
    def __init__(self) -> None:
        self.hits = 0
        self.valid = 0
        self.width_sum = 0.0
        self.errors: Counter[str] = Counter()

    def record(self, lower: float, upper: float, target: float) -> None:
        if not np.isfinite([lower, upper, target]).all() or lower > upper:
            self.errors["UndefinedInterval"] += 1
            return
        self.valid += 1
        self.hits += int(lower <= target <= upper)
        self.width_sum += upper - lower

    def report(self, repetitions: int, *, required: bool) -> dict:
        assert self.valid + sum(self.errors.values()) == repetitions
        rate = self.hits / repetitions
        return {
            "required": required,
            "hits": self.hits,
            "valid": self.valid,
            "failed": repetitions - self.valid,
            "coverage": rate,
            "mc_se": math.sqrt(rate * (1 - rate) / repetitions),
            "mean_width_valid": self.width_sum / self.valid if self.valid else None,
            "within_nominal_band": NOMINAL - MARGIN <= rate <= NOMINAL + MARGIN,
            "errors": dict(sorted(self.errors.items())),
        }


def simulate(scenario: tuple, seed: int, repetitions: int = REPETITIONS) -> dict:
    name, sizes, weighted, required = scenario
    rng = np.random.Generator(np.random.PCG64(seed))
    inputs_hash = hashlib.sha256()
    metrics = {"bin": Metric()}
    if sizes:
        metrics["slope"] = Metric()
    bin_counts: Counter[int] = Counter()
    cluster_counts: Counter[int] = Counter()
    warning_counts: Counter[str] = Counter()
    for _ in range(repetitions):
        x = rng.uniform(-1, 1, 600)
        noise = rng.normal(size=600)
        clusters = np.repeat(np.arange(len(sizes)), sizes) if sizes else None
        y = (
            2 + 1.5 * x + rng.normal(size=len(sizes))[clusters] + noise
            if sizes
            else 2 + x + 2 * x**2 + noise
        )
        weights = rng.uniform(0.5, 2, 600) if weighted else None
        for values in (x, y, weights, clusters):
            inputs_hash.update(
                b"None" if values is None else values.astype("<f8").tobytes()
            )
        with (
            warnings.catch_warnings(record=True) as captured,
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            warnings.simplefilter("always")
            try:
                result = binspect.binscatter(
                    x=x,
                    y=y,
                    weights=weights,
                    cluster=clusters,
                    bins="dpi"
                    if name == "dpi_nonflat"
                    else 5
                    if name == "quantile_nonflat"
                    else np.linspace(-1, 1, 6),
                )
            except (BinspectError, ValueError, ArithmeticError) as exc:
                for metric in metrics.values():
                    metric.errors[type(exc).__name__] += 1
                result = None
        warning_counts.update(type(item.message).__name__ for item in captured)
        if result is None:
            continue
        bin_counts[result.n_bins] += 1
        try:
            index = anchor_index(
                result.binning.partition_edges, result.binning.interval_ids
            )
            original_id = result.binning.interval_ids[index]
            lower, upper = result.binning.partition_edges[original_id : original_id + 2]
            target = population_mean(lower, upper, quadratic=not sizes)
            if result.estimates.n_clusters is not None:
                cluster_counts[int(result.estimates.n_clusters[index])] += 1
            metrics["bin"].record(
                result.estimates.ci_lo[index], result.estimates.ci_hi[index], target
            )
        except (ValueError, ArithmeticError) as exc:
            metrics["bin"].errors[type(exc).__name__] += 1
        if sizes:
            half_width = (
                stats.t.ppf(0.975, result.fit.inference_df) * result.fit.se_slope
            )
            metrics["slope"].record(
                result.fit.slope - half_width, result.fit.slope + half_width, 1.5
            )
    return {
        "scenario": name,
        "seed": seed,
        "generated_inputs_sha256": inputs_hash.hexdigest(),
        "metrics": {
            key: metric.report(repetitions, required=required)
            for key, metric in metrics.items()
        },
        "actual_bin_counts": dict(sorted(bin_counts.items())),
        "selected_bin_cluster_counts": dict(sorted(cluster_counts.items())),
        "warning_counts": dict(sorted(warning_counts.items())),
    }


def gate(outcomes: list[dict]) -> bool:
    return bool(outcomes) and all(
        metric["failed"] == 0
        and (not metric["required"] or metric["within_nominal_band"])
        for row in outcomes
        for metric in row["metrics"].values()
    )


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def run() -> dict:
    # Environment failures must abort before simulating or counting misses.
    versions = {
        name: importlib.metadata.version(name)
        for name in ("numpy", "scipy", "statsmodels", "binsreg")
    }
    # Import once, outside per-replicate warning accounting.
    import binsreg  # noqa: F401

    revision, dirty = git("rev-parse", "HEAD"), bool(git("status", "--porcelain"))
    paths = (
        "docs/EXPANDED_COVERAGE_PLAN.md",
        "validation/expanded_coverage.py",
        "uv.lock",
    )
    hashes = {
        path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in paths
    }
    outcomes = []
    for offset, scenario in enumerate(SCENARIOS):
        outcomes.append(simulate(scenario, 71000 + offset))
        print(f"Completed {scenario[0]} ({REPETITIONS} replicates)", file=sys.stderr)
    if revision != git("rev-parse", "HEAD") or any(
        hashes[path] != hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        for path in paths
    ):
        raise RuntimeError("protocol, lock or revision changed during simulation")
    return {
        "schema_version": 1,
        "protocol": "expanded-c3-development-v1",
        "phase": "development",
        "revision": revision,
        "dirty": dirty,
        "hashes": hashes,
        "rng": "numpy.random.PCG64",
        "python": sys.version.split()[0],
        "versions": versions,
        "repetitions": REPETITIONS,
        "nominal": NOMINAL,
        "acceptance_band": [NOMINAL - MARGIN, NOMINAL + MARGIN],
        "outcomes": outcomes,
        "required_pass": gate(outcomes),
        "command": "uv run --frozen --extra dev --extra validation --extra dpi "
        "python validation/expanded_coverage.py --phase development",
        "limitations": "Development evidence only; diagnostic coverage failures "
        "remain limitations. Qualified review and new locked assessment are pending.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=["development"], required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run()
    serialized = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized)
    print(serialized, end="")
    raise SystemExit(0 if report["required_pass"] else 1)


if __name__ == "__main__":
    main()
