#!/usr/bin/env python3
"""Generate icons and splash screens for a PWA from a logo or an initial.

Usage:
    python generate_icons.py --source logo.png --out assets/icons
    python generate_icons.py --text "B" --bg "#FFC107" --fg "#101418" --out assets/icons
    python generate_icons.py --source logo.png --out assets/icons --splash assets/splash

Requires Pillow:  pip install pillow
"""

from __future__ import annotations

import argparse
import pathlib
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover
    sys.exit("Pillow is missing. Install it with: pip install pillow")

LANCZOS = getattr(Image, "Resampling", Image).LANCZOS

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]

SPLASH_SIZES = [
    (1170, 2532),
    (1284, 2778),
    (1290, 2796),
    (1320, 2868),
    (1125, 2436),
    (1242, 2688),
    (828, 1792),
    (750, 1334),
    (1242, 2208),
    (1536, 2048),
    (1668, 2388),
    (2048, 2732),
]


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for candidate in FONT_CANDIDATES:
        if pathlib.Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def hex_color(value: str) -> tuple[int, int, int, int]:
    value = value.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    if len(value) != 6:
        raise argparse.ArgumentTypeError(f"Invalid color: {value}")
    return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16), 255)


def load_logo(path: str | None) -> Image.Image | None:
    if not path:
        return None
    image = Image.open(path).convert("RGBA")
    bbox = image.getbbox()
    return image.crop(bbox) if bbox else image


def fit(image: Image.Image, box: int) -> Image.Image:
    """Scale the logo so it fits inside a square of side `box`."""
    ratio = min(box / image.width, box / image.height)
    size = (max(1, int(image.width * ratio)), max(1, int(image.height * ratio)))
    return image.resize(size, LANCZOS)


def draw_mark(canvas: Image.Image, logo: Image.Image | None, text: str,
              fg: tuple[int, int, int, int], scale: float) -> None:
    draw = ImageDraw.Draw(canvas)
    size = min(canvas.width, canvas.height)
    if logo is not None:
        target = fit(logo, int(size * scale))
        x = (canvas.width - target.width) // 2
        y = (canvas.height - target.height) // 2
        canvas.alpha_composite(target, (x, y))
        return

    font = load_font(int(size * scale * 1.25))
    label = text or "A"
    bbox = draw.textbbox((0, 0), label, font=font)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    draw.text(
        ((canvas.width - width) / 2 - bbox[0], (canvas.height - height) / 2 - bbox[1]),
        label,
        font=font,
        fill=fg,
    )


def make_icon(size: int, bg: tuple[int, int, int, int], logo: Image.Image | None,
              text: str, fg: tuple[int, int, int, int], rounded: bool,
              mark_scale: float) -> Image.Image:
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    if rounded:
        radius = int(size * 0.22)
        draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=bg)
    else:
        draw.rectangle([0, 0, size - 1, size - 1], fill=bg)
    draw_mark(canvas, logo, text, fg, mark_scale)
    return canvas


def make_splash(width: int, height: int, bg: tuple[int, int, int, int],
                logo: Image.Image | None, text: str, fg: tuple[int, int, int, int],
                label: str) -> Image.Image:
    canvas = Image.new("RGBA", (width, height), bg)
    base = min(width, height)
    mark = make_icon(int(base * 0.22), bg, logo, text, fg, rounded=True, mark_scale=0.66)
    canvas.alpha_composite(mark, ((width - mark.width) // 2, int(height * 0.36)))

    if label:
        draw = ImageDraw.Draw(canvas)
        font = load_font(max(16, int(base * 0.045)))
        bbox = draw.textbbox((0, 0), label, font=font)
        draw.text(
            ((width - (bbox[2] - bbox[0])) / 2 - bbox[0], int(height * 0.62)),
            label,
            font=font,
            fill=fg,
        )
    return canvas


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate assets for a PWA")
    parser.add_argument("--source", help="Logo image, PNG/JPG (optional)")
    parser.add_argument("--text", default="", help="Initial to use when there is no logo")
    parser.add_argument("--bg", default="#0b0f14", type=hex_color, help="Background color")
    parser.add_argument("--fg", default="#ffffff", type=hex_color, help="Text/logo color")
    parser.add_argument("--out", default="assets/icons", help="Icon output folder")
    parser.add_argument("--splash", default="", help="Splash output folder (optional)")
    parser.add_argument("--splash-label", default="", help="Text under the logo on the splash")
    parser.add_argument(
        "--splash-sizes",
        default="",
        help="Comma-separated sizes, e.g. 1170x2532,1290x2796",
    )
    args = parser.parse_args()

    logo = load_logo(args.source)
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    icons = {
        "icon-192.png": make_icon(192, args.bg, logo, args.text, args.fg, True, 0.62),
        "icon-512.png": make_icon(512, args.bg, logo, args.text, args.fg, True, 0.62),
        "maskable-512.png": make_icon(512, args.bg, logo, args.text, args.fg, False, 0.60),
        "apple-touch-icon.png": make_icon(180, args.bg, logo, args.text, args.fg, False, 0.62),
        "favicon-32.png": make_icon(32, args.bg, logo, args.text, args.fg, True, 0.62),
    }
    for name, image in icons.items():
        path = out / name
        image.save(path, "PNG")
        print(f"icon   {path}  {image.width}x{image.height}")

    if args.splash:
        sizes = SPLASH_SIZES
        if args.splash_sizes:
            sizes = []
            for item in args.splash_sizes.split(","):
                width, height = item.lower().split("x")
                sizes.append((int(width), int(height)))

        splash_dir = pathlib.Path(args.splash)
        splash_dir.mkdir(parents=True, exist_ok=True)
        for width, height in sizes:
            image = make_splash(
                width, height, args.bg, logo, args.text, args.fg, args.splash_label
            )
            path = splash_dir / f"{width}x{height}.png"
            image.save(path, "PNG")
            print(f"splash {path}  {width}x{height}")


if __name__ == "__main__":
    main()
