"""Synthetic A1 allocation probe; not a P1 capacity/performance qualification.

Run with the locked environment and optionally PYTHONPATH pointing to a baseline
source tree. Input creation and one warmup are outside tracemalloc/timing. Reports
include all repeated measurements, retained numeric payload and synthetic exports
for exact before/after equivalence checks. No caller data is accepted.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import platform
import time
import tracemalloc
from dataclasses import fields
from pathlib import Path

import numpy as np
import pandas as pd

import binspect


def payload_bytes(result):
    if isinstance(result, binspect.BinscatterCollection):
        return sum(payload_bytes(r) for r in result.results.values()) + payload_bytes(
            result.pooled
        )
    return sum(
        value.nbytes
        for owner in (result, result.binning, result.estimates)
        for field in fields(owner)
        if isinstance(value := getattr(owner, field.name), np.ndarray)
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", nargs="+", type=int, default=[10_000, 100_000])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--label", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    reports = []
    for n in args.rows:
        rng = np.random.default_rng(421)
        x = rng.normal(size=n)
        frame = pd.DataFrame(
            {
                "x": x,
                "y": x**2 + rng.normal(size=n),
                "w": rng.uniform(0.5, 2, n),
                "group": np.arange(n) % 4,
            }
        )
        for grouped in (False, True):
            for weighted in (False, True):

                def estimate(frame=frame, weighted=weighted, grouped=grouped):
                    kwargs = dict(
                        x="x", y="y", bins=20, weights="w" if weighted else None
                    )
                    return (
                        binspect.compare(frame, group="group", **kwargs)
                        if grouped
                        else binspect.binscatter(frame, **kwargs)
                    )

                warmup = estimate().to_dict()
                runs = []
                for _ in range(args.repeats):
                    gc.collect()
                    tracemalloc.start()
                    start = time.perf_counter()
                    result = estimate()
                    elapsed = time.perf_counter() - start
                    current, peak = tracemalloc.get_traced_memory()
                    tracemalloc.stop()
                    assert result.to_dict() == warmup
                    runs.append(
                        {
                            "seconds": elapsed,
                            "retained_bytes": current,
                            "peak_bytes": peak,
                        }
                    )
                    payload = payload_bytes(result)
                    del result
                reports.append(
                    {
                        "rows": n,
                        "grouped": grouped,
                        "weighted": weighted,
                        "numeric_payload_bytes": payload,
                        "runs": runs,
                        "synthetic_export": warmup,
                    }
                )
    report = {
        "label": args.label,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "lock_sha256": hashlib.sha256(Path("uv.lock").read_bytes()).hexdigest(),
        "cases": reports,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, allow_nan=False, indent=2) + "\n")
    print(f"Wrote {len(reports)} synthetic allocation cases to {args.output}")


if __name__ == "__main__":
    main()
