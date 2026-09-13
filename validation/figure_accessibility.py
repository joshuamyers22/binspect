"""Local qualitative color/background review artifacts, not accessibility certification.

Machado et al. (2009), DOI 10.1109/TVCG.2009.113, severity-100 data matrices,
verified against colorspacious' transcription of the authors' supplementary data:
https://github.com/njsmith/colorspacious/blob/master/colorspacious/cvd.py
Matrices operate on linear RGB; output is clipped to gamut and encoded to sRGB.
Only the numerical supplementary data are used; implementation below is local.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from figures import example_result, render_context
from matplotlib.colors import to_rgb
from PIL import Image, ImageDraw

from binspect.viz import get_theme

MATRICES = {
    "protan": [
        [0.152286, 1.052583, -0.204868],
        [0.114503, 0.786281, 0.099216],
        [-0.003882, -0.048116, 1.051998],
    ],
    "deutan": [
        [0.367322, 0.860646, -0.227968],
        [0.280085, 0.672501, 0.047413],
        [-0.011820, 0.042940, 0.968881],
    ],
    "tritan": [
        [1.255528, -0.076749, -0.178779],
        [-0.078411, 0.930809, 0.147602],
        [0.004733, 0.691367, 0.303900],
    ],
}
LUMINANCE = np.array([0.2126, 0.7152, 0.0722])


def linear_rgb(rgb):
    return np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)


def transform(image: Image.Image, mode: str) -> Image.Image:
    if mode == "original":
        return image.convert("RGB")
    linear = linear_rgb(np.asarray(image.convert("RGB"), dtype=float) / 255)
    if mode == "grayscale":
        converted = np.repeat((linear @ LUMINANCE)[..., None], 3, axis=-1)
    else:
        converted = linear @ np.asarray(MATRICES[mode]).T
    converted = np.clip(converted, 0, 1)
    encoded = np.where(
        converted <= 0.0031308,
        converted * 12.92,
        1.055 * converted ** (1 / 2.4) - 0.055,
    )
    return Image.fromarray(np.rint(encoded * 255).astype(np.uint8))


def luminance(color):
    return float(linear_rgb(np.array(to_rgb(color))) @ LUMINANCE)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(".work/figure-review"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    modes = ("original", "grayscale", "protan", "deutan", "tritan")
    backgrounds = ("white", "#F2F2F2", "#202124")
    report = {
        "scope": "qualitative simulation; not accessibility certification",
        "themes": {},
    }
    with render_context():
        result = example_result()
        for name in ("notebook", "paper", "deck"):
            sheet = Image.new(
                "RGB", (550 * len(modes), 390 * len(backgrounds)), "white"
            )
            draw = ImageDraw.Draw(sheet)
            palette = get_theme(name).palette
            report["themes"][name] = {
                "accent_luminance": luminance(palette.accent),
                "neutral_luminance": luminance(palette.neutral),
                "text_background_ratios": {},
            }
            for row, background in enumerate(backgrounds):
                fig, ax = plt.subplots(figsize=(5.5, 3.6))
                fig.set_facecolor(background)
                ax.set_facecolor(background)
                result.plot(
                    ax=ax,
                    theme=name,
                    show=("bins", "fit", "sd_line", "ci", "deviation"),
                    annotate=None,
                    legend=True,
                )
                fig.tight_layout()
                path = args.output / f"{name}-{row}.png"
                fig.savefig(path, dpi=100, facecolor=background)
                plt.close(fig)
                a, b = sorted([luminance(palette.text), luminance(background)])
                report["themes"][name]["text_background_ratios"][background] = (
                    b + 0.05
                ) / (a + 0.05)
                with Image.open(path) as source:
                    for col, mode in enumerate(modes):
                        draw.text(
                            (col * 550 + 8, row * 390 + 6),
                            f"{name} | {background} | {mode}",
                            fill="black",
                        )
                        sheet.paste(
                            transform(source, mode), (col * 550, row * 390 + 25)
                        )
            sheet.save(args.output / f"{name}-review.png")
    (args.output / "review.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    print(f"Wrote three 15-panel simulation/background sheets to {args.output}")


if __name__ == "__main__":
    main()
