"""Execute the predeclared, bounded coverage protocol on synthetic inputs only."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

import binspect
from binspect.core.estimate import estimate_bins
from binspect.exceptions import BinspectError

ROOT = Path(__file__).resolve().parents[1]
REPETITIONS = 1000
SCENARIOS = ("iid", "weighted", "clustered", "adjusted", "quantile")
NOMINAL = 0.95
MARGIN = 4 * math.sqrt(NOMINAL * (1 - NOMINAL) / REPETITIONS)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def digest(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def run(phase: str) -> dict:
    base_seed = 41000 if phase == "development" else 51000
    inputs_hash = hashlib.sha256()
    outcomes = []
    for offset, scenario in enumerate(SCENARIOS):
        rng = np.random.Generator(np.random.PCG64(base_seed + offset))
        hits = valid = 0
        errors: dict[str, int] = {}
        for _ in range(REPETITIONS):
            x = rng.uniform(-1, 1, 600)
            y = 2 + rng.normal(size=600)
            weights = rng.uniform(0.5, 2, 600) if scenario == "weighted" else None
            clusters = np.repeat(np.arange(60), 10) if scenario == "clustered" else None
            controls = rng.normal(size=600) if scenario == "adjusted" else None
            if clusters is not None:
                y += rng.normal(size=60)[clusters]
            if controls is not None:
                y += 1.5 * controls
            for values in (x, y, weights, clusters, controls):
                inputs_hash.update(
                    b"None" if values is None else values.astype("<f8").tobytes()
                )
            try:
                result = binspect.binscatter(
                    x=x,
                    y=y,
                    weights=weights,
                    cluster=clusters,
                    controls=controls,
                    ci=None if controls is not None else 0.95,
                    bins=5
                    if scenario in {"adjusted", "quantile"}
                    else np.linspace(-1, 1, 6),
                )
                positions = np.flatnonzero(result.binning.interval_ids == 2)
                if positions.size != 1:
                    raise ValueError("prespecified interval absent")
                index = positions[0]
                estimates = result.estimates
                if controls is not None:
                    if (
                        not np.isnan(estimates.se).all()
                        or estimates.ci_level is not None
                    ):
                        raise AssertionError(
                            "public adjusted-bin uncertainty was not withheld"
                        )
                    estimates = estimate_bins(
                        result.x,
                        result.y,
                        result.binning.assignment,
                        result.n_bins,
                        weights=weights,
                        clusters=clusters,
                    )
                lower, upper = (
                    estimates.ci_lo[index],
                    estimates.ci_hi[index],
                )
                if not np.isfinite([lower, upper]).all():
                    raise ValueError("undefined prespecified interval")
                valid += 1
                hits += int(lower <= 2 <= upper)
            except (BinspectError, ValueError, ArithmeticError) as exc:
                name = type(exc).__name__
                errors[name] = errors.get(name, 0) + 1
        rate = hits / REPETITIONS
        required = scenario in {"iid", "weighted", "clustered"}
        outcomes.append(
            {
                "scenario": scenario,
                "scope": "withdrawn_adjusted_formula"
                if scenario == "adjusted"
                else "public_unadjusted",
                "seed": base_seed + offset,
                "required": required,
                "hits": hits,
                "valid": valid,
                "failed": REPETITIONS - valid,
                "coverage": rate,
                "mc_se": math.sqrt(rate * (1 - rate) / REPETITIONS),
                "within_nominal_band": NOMINAL - MARGIN <= rate <= NOMINAL + MARGIN,
                "errors": errors,
            }
        )
    return {
        "schema_version": 2,
        "phase": phase,
        "revision": git("rev-parse", "HEAD"),
        "dirty": bool(git("status", "--porcelain")),
        "rng": "numpy.random.PCG64",
        "repetitions": REPETITIONS,
        "nominal": NOMINAL,
        "acceptance_band": [NOMINAL - MARGIN, NOMINAL + MARGIN],
        "python": sys.version.split()[0],
        "versions": {
            name: importlib.metadata.version(name)
            for name in ["numpy", "scipy", "statsmodels"]
        },
        "hashes": {
            path: digest(path)
            for path in [
                "docs/STATISTICAL_ANALYSIS_PLAN.md",
                "docs/adjusted-inference-boundary-review.md",
                "validation/coverage.py",
                "uv.lock",
            ]
        },
        "generated_inputs_sha256": inputs_hash.hexdigest(),
        "outcomes": outcomes,
        "command": "uv run --frozen --extra dev --extra validation "
        f"python validation/coverage.py --phase {phase}",
        "required_pass": all(
            row["within_nominal_band"] and row["failed"] == 0
            for row in outcomes
            if row["required"]
        ),
        "limitations": "Initial scenarios only; diagnostics are not general coverage "
        "qualification. See the analysis plan's open C3 cases.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=["development", "assessment"], required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.phase == "assessment":
        parser.error(
            "v1 assessment seeds are consumed; reproduce the historical protocol at "
            "clean c19c2a8 or specify a reviewed new assessment protocol"
        )
    report = run(args.phase)
    serialized = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized)
    print(serialized, end="")
    raise SystemExit(0 if report["required_pass"] else 1)


if __name__ == "__main__":
    main()
