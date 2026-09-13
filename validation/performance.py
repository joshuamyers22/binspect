"""Sequential synthetic workload measurements with resource guards."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import platform
import resource
import statistics
import subprocess
import sys
import tempfile
import time
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THREADS = {
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "VECLIB_MAXIMUM_THREADS": "1",
    "POLARS_MAX_THREADS": "1",
    "MPLBACKEND": "Agg",
}
SEED = 130101
RSS_LIMIT = 2 * 1024**3
TIME_LIMIT = 120


def workloads(sizes):
    for n in sizes:
        for name, options in (
            ("base", {}),
            ("bins100", {"bins": 100}),
            ("clusters100", {"clusters": 100}),
            ("clusters_n", {"clusters": n, "bins": 100}),
            ("groups4", {"groups": 4}),
            ("groups16", {"groups": 16}),
            ("controls4", {"controls": 4}),
            ("controls16", {"controls": 16}),
            ("default_plot", {"layers": "default"}),
            ("clusters_n_default", {"clusters": n, "bins": 100, "layers": "default"}),
        ):
            yield {
                "name": f"{name}_{n}",
                "n": n,
                "bins": 20,
                "groups": 0,
                "controls": 0,
                "clusters": 0,
                "layers": "summary",
                **options,
            }


def peak_rss():
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if sys.platform == "darwin" else value * 1024)


def worker(spec, destination):
    import numpy as np
    import polars as pl

    import binspect

    rng = np.random.Generator(np.random.PCG64(SEED))
    n = spec["n"]
    x = rng.uniform(-3, 3, n)
    columns = {"x": x, "y": x + 0.3 * x**2 + rng.normal(size=n)}
    for index in range(spec["controls"]):
        z = rng.normal(size=n)
        columns[f"z{index}"] = z
        columns["y"] += 0.2 * z
    if spec["clusters"]:
        columns["cluster"] = np.arange(n) % spec["clusters"]
    if spec["groups"]:
        columns["group"] = np.arange(n) % spec["groups"]
    frame = pl.DataFrame(columns)
    del columns, x
    options = {"x": "x", "y": "y", "bins": spec["bins"]}
    if spec["controls"]:
        options.update(controls=[f"z{i}" for i in range(spec["controls"])], ci=None)
    if spec["clusters"]:
        options["cluster"] = "cluster"
    estimate = binspect.compare if spec["groups"] else binspect.binscatter
    if spec["groups"]:
        options["group"] = "group"
    timings = {}
    references = []
    for phase in ("first", "warm"):
        gc.collect()
        start = time.perf_counter()
        result = estimate(frame, **options)
        timings[f"estimate_{phase}_s"] = time.perf_counter() - start
        members = (
            [result.pooled, *result.results.values()] if spec["groups"] else [result]
        )
        numerical = []
        for member in members:
            assert isinstance(member.table, pl.DataFrame)
            numerical.extend(
                [
                    member.fit.slope,
                    member.fit.intercept,
                    member.fit.se_slope,
                    member.decomposition.gap,
                ]
            )
            for attr in (
                "x_mean",
                "y_mean",
                "y_sd",
                "se",
                "ci_lo",
                "ci_hi",
                "n",
                "sum_w",
                "n_clusters",
                "ci_df",
            ):
                array = getattr(member.estimates, attr)
                if array is not None:
                    numerical.extend(array.tolist())
            numerical.extend(member.binning.partition_edges.tolist())
            numerical.extend(member.binning.interval_ids.tolist())
        references.append(np.asarray(numerical))
        if phase == "first":
            del result, members, member
    np.testing.assert_allclose(references[0], references[1], rtol=1e-12, atol=1e-12)
    estimate_peak = peak_rss()
    # Imports are outside timing; first construction/draw includes renderer caches.
    import matplotlib.pyplot as plt

    show = {} if spec["layers"] == "default" else {"show": ("bins", "ci", "fit")}
    for phase in ("first", "warm"):
        gc.collect()
        start = time.perf_counter()
        output = result.plot(annotate=None, **show)
        figure = output if spec["groups"] else output.figure
        figure.canvas.draw()
        timings[f"render_{phase}_s"] = time.perf_counter() - start
        plt.close(figure)
        del figure, output
    record = {
        "timings": timings,
        "estimate_peak_rss_bytes": estimate_peak,
        "process_peak_rss_bytes": peak_rss(),
        "numerical": [float(v) if np.isfinite(v) else None for v in references[1]],
    }
    destination.write_text(json.dumps(record, allow_nan=False) + "\n")


def trial(spec, directory):
    destination = directory / "trial.json"
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--worker",
        json.dumps(spec),
        "--output",
        str(destination),
    ]
    start = time.perf_counter()
    with (directory / "stderr.txt").open("w") as log:
        child = subprocess.Popen(
            command,
            env={**os.environ, **THREADS},
            stdout=subprocess.DEVNULL,
            stderr=log,
        )
        reason = None
        sampled_peak = 0
        try:
            while child.poll() is None:
                probe = subprocess.run(
                    ["ps", "-o", "rss=", "-p", str(child.pid)],
                    capture_output=True,
                    text=True,
                )
                if probe.returncode == 0 and probe.stdout.strip():
                    sampled_peak = max(sampled_peak, int(probe.stdout.strip()) * 1024)
                elif child.poll() is None:
                    raise RuntimeError("RSS monitor unavailable; no unguarded trial.")
                if sampled_peak > RSS_LIMIT:
                    reason = "rss_limit"
                    break
                if time.perf_counter() - start > TIME_LIMIT:
                    reason = "time_limit"
                    break
                time.sleep(0.1)
        finally:
            if child.poll() is None:
                child.kill()
            child.wait()
    if reason:
        return {"status": reason, "sampled_peak_rss_bytes": sampled_peak}
    if child.returncode:
        raise RuntimeError(
            f"Worker failed: {spec['name']}: {(directory / 'stderr.txt').read_text()}"
        )
    result = json.loads(destination.read_text())
    result["status"] = "pass"
    result["sampled_peak_rss_bytes"] = sampled_peak
    if result["process_peak_rss_bytes"] > RSS_LIMIT:
        result["status"] = "rss_limit"
    return result


def identity():
    files = sorted((ROOT / "src/binspect").rglob("*.py"))
    digest = hashlib.sha256()
    for path in files:
        digest.update(str(path.relative_to(ROOT)).encode())
        digest.update(path.read_bytes())
    hardware = (
        subprocess.check_output(
            ["sysctl", "-n", "machdep.cpu.brand_string", "hw.memsize", "hw.ncpu"],
            text=True,
        ).splitlines()
        if sys.platform == "darwin"
        else [platform.processor(), "unrecorded", str(os.cpu_count())]
    )
    return {
        "host": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "hardware": hardware,
        },
        "python": platform.python_version(),
        "versions": {
            name: version(name)
            for name in (
                "binspect-regression",
                "numpy",
                "polars",
                "scipy",
                "matplotlib",
                "pillow",
            )
        },
        "threads": THREADS,
        "source_sha256": digest.hexdigest(),
        "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "lock_sha256": hashlib.sha256((ROOT / "uv.lock").read_bytes()).hexdigest(),
        "revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".work/performance.json")
    parser.add_argument(
        "--sizes", type=int, nargs="+", default=[10_000, 100_000, 1_000_000]
    )
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--legacy-dense", action="store_true")
    parser.add_argument("--worker", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        worker(json.loads(args.worker), args.output)
        return
    if args.trials < 3 or any(
        n not in (10_000, 100_000, 1_000_000) for n in args.sizes
    ):
        parser.error("Use at least three trials and prespecified 10k/100k/1M sizes.")
    report = {
        "schema_version": 1,
        "acceptance": "pending",
        "identity": identity(),
        "seed": SEED,
        "rss_limit_bytes": RSS_LIMIT,
        "trial_timeout_s": TIME_LIMIT,
        "legacy_dense": args.legacy_dense,
        "workloads": [],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for spec in workloads(args.sizes):
        entry = {"spec": spec, "trials": []}
        dense_bytes = 24 * spec["bins"] * spec["clusters"]
        if args.legacy_dense and dense_bytes > 256 * 1024**2:
            entry.update(
                status="preflight_skip",
                reason="legacy dense working arrays exceed 256 MiB",
                predicted_dense_bytes=dense_bytes,
            )
        else:
            for _ in range(args.trials):
                with tempfile.TemporaryDirectory(prefix="binspect-perf-") as temporary:
                    measured = trial(spec, Path(temporary))
                numerical = measured.pop("numerical", None)
                if numerical is not None:
                    if "numerical" not in entry:
                        entry["numerical"] = numerical
                    elif entry["numerical"] != numerical:
                        raise ValueError(
                            "Identical seeded workload changed numerical output."
                        )
                entry["trials"].append(measured)
                if measured["status"] != "pass":
                    break
            entry["status"] = entry["trials"][-1]["status"]
            if entry["status"] == "pass":
                entry["summary"] = {}
                for key in entry["trials"][0]["timings"]:
                    values = [item["timings"][key] for item in entry["trials"]]
                    entry["summary"][key] = {
                        "median": statistics.median(values),
                        "min": min(values),
                        "max": max(values),
                        "stdev": statistics.stdev(values),
                    }
        report["workloads"].append(entry)
        args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
        print(f"{spec['name']}: {entry['status']}", flush=True)


if __name__ == "__main__":
    main()
