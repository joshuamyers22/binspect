"""Prespecified binsreg adapter development coverage; assessment seeds excluded."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import subprocess
import sys
import warnings
from collections import Counter
from pathlib import Path

import numpy as np

import binspect
from binspect.exceptions import BinspectError

ROOT = Path(__file__).resolve().parents[1]
REPETITIONS = 1000
NOMINAL = 0.95
MARGIN = 4 * math.sqrt(NOMINAL * (1 - NOMINAL) / REPETITIONS)
SCENARIOS = (
    ("adjusted_iid_dpi", (), "dpi", True),
    ("adjusted_cluster_60", (10,) * 60, 5, False),
    ("adjusted_cluster_3_uneven", (480, 60, 60), 5, False),
)


def simulate(scenario: tuple, seed: int, repetitions: int = REPETITIONS) -> dict:
    name, sizes, count, required = scenario
    rng = np.random.Generator(np.random.PCG64(seed))
    inputs_hash = hashlib.sha256()
    hits = valid = 0
    width_sum = 0.0
    errors: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    issues: Counter[str] = Counter()
    counts: Counter[int] = Counter()
    degrees: Counter[str] = Counter()
    for _ in range(repetitions):
        x = rng.uniform(-1, 1, 600)
        z = rng.normal(1, 1, 600)
        error = rng.normal(0, 1, 600)
        clusters = np.repeat(np.arange(len(sizes)), sizes) if sizes else None
        y = 2 + x + 2 * x**2 + z + error
        if sizes:
            y += rng.normal(0, 1, len(sizes))[clusters]
        for values in (x, z, y, clusters):
            inputs_hash.update(
                b"None" if values is None else values.astype("<f8").tobytes()
            )
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", binspect.BinsregWarning)
                result = binspect.binsreg(
                    x=x, y=y, controls=z, cluster=clusters, bins=count, at=[1.0]
                )
            meta, intervals = result.metadata, result.intervals
            statuses[meta["inference_status"]] += 1
            issues.update(meta["issues"])
            counts[meta["actual_bins"]] += 1
            degrees[json.dumps(meta["actual_intervals"])] += 1
            if intervals.empty:
                raise ValueError("intervals unavailable")
            row = intervals.iloc[int(np.argmin(np.abs(intervals.x.to_numpy())))]
            target = 3 + row.x + 2 * row.x**2
            if (
                not np.isfinite([row.ci_lo, row.ci_hi, target]).all()
                or row.ci_lo > row.ci_hi
            ):
                raise ValueError("invalid interval")
            valid += 1
            hits += int(row.ci_lo <= target <= row.ci_hi)
            width_sum += row.ci_hi - row.ci_lo
        except (BinspectError, ValueError, ArithmeticError) as exc:
            errors[type(exc).__name__] += 1
    assert valid + sum(errors.values()) == repetitions
    rate = hits / repetitions
    return {
        "scenario": name,
        "seed": seed,
        "generated_inputs_sha256": inputs_hash.hexdigest(),
        "required_coverage": required,
        "target": "3 + x + 2*x^2 at returned interval x nearest zero",
        "fallback_interpretation": "Coverage against the function target, "
        "not a population-bin mean",
        "hits": hits,
        "valid": valid,
        "failed": repetitions - valid,
        "coverage": rate,
        "mc_se": math.sqrt(rate * (1 - rate) / repetitions),
        "mean_width_valid": width_sum / valid if valid else None,
        "within_nominal_band": NOMINAL - MARGIN <= rate <= NOMINAL + MARGIN,
        "errors": dict(sorted(errors.items())),
        "status_counts": dict(sorted(statuses.items())),
        "issue_counts": dict(sorted(issues.items())),
        "actual_bin_counts": dict(sorted(counts.items())),
        "actual_interval_degrees": dict(sorted(degrees.items())),
    }


def gate(outcomes: list[dict]) -> bool:
    return bool(outcomes) and all(
        row["failed"] == 0
        and (not row["required_coverage"] or row["within_nominal_band"])
        for row in outcomes
    )


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def run() -> dict:
    versions = {
        name: importlib.metadata.version(name)
        for name in ("numpy", "scipy", "statsmodels", "binsreg")
    }
    # Environment failure must abort, rather than count as simulated misses.
    import binsreg  # noqa: F401

    revision, dirty = git("rev-parse", "HEAD"), bool(git("status", "--porcelain"))
    paths = (
        "docs/BINSREG_ADAPTER_PLAN.md",
        "validation/binsreg_coverage.py",
        "uv.lock",
        "src/binspect/binsreg_api.py",
        "src/binspect/binsreg_inputs.py",
        "src/binspect/binsreg_results.py",
    )
    hashes = {
        path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in paths
    }
    outcomes = []
    for offset, scenario in enumerate(SCENARIOS):
        outcomes.append(simulate(scenario, 94000 + offset))
        print(f"Completed {scenario[0]} ({REPETITIONS} replicates)", file=sys.stderr)
    if revision != git("rev-parse", "HEAD") or any(
        hashes[path] != hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        for path in paths
    ):
        raise RuntimeError(
            "protocol, implementation, lock or revision changed during simulation"
        )
    return {
        "schema_version": 1,
        "protocol": "binsreg-adapter-development-v1",
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
        "python validation/binsreg_coverage.py --phase development",
        "limitations": "Development evidence for this function target and DGP only; "
        "Clustered cases are diagnostic. No author endorsement or qualified "
        "acceptance. "
        "Assessment seeds 95000-95002 remain reserved and unrun.",
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
