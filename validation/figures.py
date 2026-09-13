"""Pinned, explicitly reviewed raster baselines; default mode never updates them."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from contextlib import contextmanager
from importlib.metadata import version
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager, ft2font
from PIL import Image

import binspect
from binspect.viz import deviation_layer

ROOT = Path(__file__).resolve().parents[1]
BASELINES = ROOT / "tests/baseline"
CASES = ("default", "paper", "audit", "deviation")
RMS_LIMIT = 0.5  # Prespecified 0-255 RGB scale; never inferred from failed images.
RC = {
    "backend": "Agg",
    "figure.dpi": 100,
    "savefig.dpi": 100,
    "font.family": "DejaVu Sans",
    "font.sans-serif": ["DejaVu Sans"],
    "font.serif": ["DejaVu Serif"],
    "text.usetex": False,
    "svg.fonttype": "none",
    "svg.hashsalt": "binspect-d2",
    "pdf.fonttype": 42,
}


@contextmanager
def render_context():
    """Reset user styling while keeping every change scoped to verification."""
    with mpl.rc_context(rc={**mpl.rcParamsDefault, **RC}):
        yield


def renderer() -> dict:
    """Rendering inputs that must match the baseline manifest exactly."""
    fonts = {}
    for family in ("DejaVu Sans", "DejaVu Serif"):
        path = Path(font_manager.findfont(family, fallback_to_default=False))
        fonts[family] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "python": platform.python_version_tuple()[:2],
        "implementation": platform.python_implementation(),
        "versions": {
            name: version(name) for name in ("matplotlib", "numpy", "scipy", "pillow")
        },
        "freetype": ft2font.__freetype_version__,
        "fonts_sha256": fonts,
        "rc": RC,
    }


def check_renderer(expected: dict, actual: dict) -> None:
    if json.dumps(expected, sort_keys=True) != json.dumps(actual, sort_keys=True):
        raise ValueError(
            "Renderer differs from baseline manifest; "
            "use the recorded Python/lock/fonts. "
            "A new renderer needs separate review, not a silently regenerated baseline."
        )


def example_result():
    """Deterministic synthetic curve with visible deviation and finite intervals."""
    x = np.linspace(-3, 3, 1200)
    y = 2 * np.tanh(x) + 0.35 * np.sin(23 * x)
    return binspect.binscatter(x=x, y=y, bins=12)


def make_figure(name: str):
    result = example_result()
    if name in ("default", "paper"):
        return result.plot(theme="paper" if name == "paper" else "notebook").figure
    if name == "audit":
        return result.audit()
    if name == "deviation":
        figure, ax = plt.subplots(figsize=(7.2, 4.6))
        deviation_layer(ax, result)
        ax.set(xlabel="x", ylabel="y", title="Standalone deviation")
        figure.tight_layout()
        return figure
    raise ValueError(f"Unknown baseline case: {name}")


def compare_png(expected: Path, actual: Path) -> float:
    with Image.open(expected) as source, Image.open(actual) as candidate:
        a = np.asarray(source.convert("RGBA"), dtype=float)
        b = np.asarray(candidate.convert("RGBA"), dtype=float)
    if a.shape != b.shape:
        raise ValueError(
            f"Image dimensions changed: {expected.name}: {a.shape} -> {b.shape}"
        )
    if not np.array_equal(a[..., 3], b[..., 3]):
        raise ValueError(f"Image opacity changed: {expected.name}")
    rms = float(np.sqrt(np.mean((a[..., :3] - b[..., :3]) ** 2)))
    if rms > RMS_LIMIT:
        raise ValueError(
            f"Image regression: {expected.name}: RMS {rms:.6f} > {RMS_LIMIT}"
        )
    return rms


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".work/figures")
    parser.add_argument(
        "--write-baselines",
        action="store_true",
        help="explicit maintainer review operation",
    )
    args = parser.parse_args()
    output = BASELINES if args.write_baselines else args.output
    if not args.write_baselines and (
        output.resolve() == BASELINES.resolve()
        or BASELINES.resolve() in output.resolve().parents
    ):
        raise ValueError("Comparison output must not overwrite baseline storage.")
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = BASELINES / "manifest.json"
    if not args.write_baselines:
        manifest = json.loads(manifest_path.read_text())
        check_renderer(manifest["renderer"], renderer())
        if manifest["rms_limit"] != RMS_LIMIT or manifest["cases"] != list(CASES):
            raise ValueError("Baseline policy differs from committed manifest.")
    results = {}
    with render_context():
        for name in CASES:
            figure = make_figure(name)
            target = output / f"{name}.png"
            figure.savefig(target, dpi=100, facecolor="white")
            plt.close(figure)
            if not args.write_baselines:
                expected = BASELINES / target.name
                digest = hashlib.sha256(expected.read_bytes()).hexdigest()
                if digest != manifest["sha256"][target.name]:
                    raise ValueError(
                        f"Baseline bytes differ from manifest: {target.name}"
                    )
                results[name] = compare_png(expected, target)
    if args.write_baselines:
        manifest = {
            "schema_version": 1,
            "renderer": renderer(),
            "host": {
                "system": platform.system(),
                "machine": platform.machine(),
                "release": platform.release(),
            },
            "lock_sha256": hashlib.sha256((ROOT / "uv.lock").read_bytes()).hexdigest(),
            "cases": list(CASES),
            "rms_limit": RMS_LIMIT,
            "sha256": {
                f"{name}.png": hashlib.sha256(
                    (output / f"{name}.png").read_bytes()
                ).hexdigest()
                for name in CASES
            },
            "review": (
                "Initial D2 candidates; local visual inspection recorded separately; "
                "maintainer acceptance pending."
            ),
        }
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        print("Wrote four review candidates and manifest; inspect before accepting.")
    else:
        print(json.dumps({"rms": results, "limit": RMS_LIMIT}, sort_keys=True))


if __name__ == "__main__":
    main()
