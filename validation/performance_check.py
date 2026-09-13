"""Compare numerical workload evidence and enforce explicitly accepted host budgets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

TIME_FACTOR = 1.25
RSS_FACTOR = 1.20
IDENTITY_KEYS = (
    "host",
    "python",
    "versions",
    "threads",
    "lock_sha256",
    "harness_sha256",
)


def compatible(left, right):
    for key in IDENTITY_KEYS:
        if left[key] != right[key]:
            raise ValueError(f"Unqualified comparison environment: {key}")


def indexed(reports):
    result = {}
    for report in reports:
        compatible(reports[0]["identity"], report["identity"])
        for entry in report["workloads"]:
            name = entry["spec"]["name"]
            if name in result:
                raise ValueError(f"Duplicate workload: {name}")
            result[name] = entry
    return result


def compare(reference, candidate):
    compatible(reference[0]["identity"], candidate["identity"])
    before, after = indexed(reference), indexed([candidate])
    if before.keys() != after.keys():
        raise ValueError("Reference and candidate workloads differ.")
    checked, unavailable = [], []
    for name, entry in after.items():
        previous = before[name]
        if entry["spec"] != previous["spec"]:
            raise ValueError(f"Workload specification changed: {name}")
        if entry["status"] != "pass" or previous["status"] != "pass":
            unavailable.append(
                {"name": name, "before": previous["status"], "after": entry["status"]}
            )
            continue
        np.testing.assert_allclose(
            np.asarray(entry["numerical"], dtype=float),
            np.asarray(previous["numerical"], dtype=float),
            rtol=1e-12,
            atol=1e-12,
            equal_nan=True,
            err_msg=name,
        )
        checked.append(name)
    return {"numerically_equivalent": checked, "not_compared": unavailable}


def propose(report):
    limits = {}
    excluded = []
    for entry in report["workloads"]:
        name = entry["spec"]["name"]
        if entry["status"] != "pass":
            excluded.append({"name": name, "status": entry["status"]})
            continue
        trials = entry["trials"]
        if len(trials) < 3:
            raise ValueError("At least three fresh trials are required for budgets.")
        limits[name] = {
            "spec": entry["spec"],
            "timings": {
                key: max(t["timings"][key] for t in trials) * TIME_FACTOR
                for key in trials[0]["timings"]
            },
            "rss_bytes": {
                key: int(max(t[key] for t in trials) * RSS_FACTOR)
                for key in ("estimate_peak_rss_bytes", "process_peak_rss_bytes")
            },
        }
    return {
        "schema_version": 1,
        "acceptance": {"status": "pending", "reviewer": None, "date": None},
        "identity": report["identity"],
        "formula": {
            "time_max_multiplier": TIME_FACTOR,
            "rss_max_multiplier": RSS_FACTOR,
        },
        "limits": limits,
        "excluded": excluded,
    }


def enforce(budget, report):
    acceptance = budget["acceptance"]
    if (
        acceptance["status"] != "accepted"
        or not acceptance.get("reviewer")
        or not acceptance.get("date")
    ):
        raise ValueError(
            "Benchmark baseline/runner acceptance is pending; no accepted gate."
        )
    compatible(budget["identity"], report["identity"])
    entries = indexed([report])
    for name, limits in budget["limits"].items():
        if name not in entries:
            raise ValueError(f"Budgeted workload missing: {name}")
        entry = entries[name]
        if entry["status"] != "pass" or len(entry["trials"]) < 3:
            raise ValueError(f"Budgeted workload incomplete: {name}")
        if entry["spec"] != limits["spec"]:
            raise ValueError(f"Budgeted specification changed: {name}")
        for trial in entry["trials"]:
            for key, ceiling in limits["timings"].items():
                if trial["timings"][key] > ceiling:
                    raise ValueError(f"Timing budget exceeded: {name}: {key}")
            for key, ceiling in limits["rss_bytes"].items():
                if trial[key] > ceiling:
                    raise ValueError(f"Memory budget exceeded: {name}: {key}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--reference", type=Path, nargs="+")
    parser.add_argument("--propose", type=Path)
    parser.add_argument("--budget", type=Path)
    args = parser.parse_args()
    if not (args.reference or args.propose or args.budget):
        parser.error("Choose --reference, --propose or --budget.")
    report = json.loads(args.candidate.read_text())
    if args.reference:
        print(
            json.dumps(
                compare([json.loads(p.read_text()) for p in args.reference], report)
            )
        )
    if args.propose:
        args.propose.parent.mkdir(parents=True, exist_ok=True)
        args.propose.write_text(json.dumps(propose(report), indent=2) + "\n")
        print("Wrote proposed budgets; baseline/runner acceptance remains pending.")
    if args.budget:
        enforce(json.loads(args.budget.read_text()), report)
        print("Accepted workload budgets pass on the recorded environment.")


if __name__ == "__main__":
    main()
