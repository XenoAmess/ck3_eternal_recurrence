#!/usr/bin/env python3
"""Render the Auto Upgrade Buildings decision art as CK3-native DXT1 DDS."""

from __future__ import annotations

import argparse
import io
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "images" / "auto_upgrade_buildings_decision.png"
OUTPUT = (
    ROOT
    / "mod_auto_upgrade_buildings"
    / "gfx"
    / "interface"
    / "illustrations"
    / "decisions"
    / "decision_auto_upgrade_buildings.dds"
)
WIDTH = 1100
HEIGHT = 440


def render(source: Path = SOURCE) -> Image.Image:
    """Center-crop without distortion, then resize to the CK3 decision surface."""
    with Image.open(source) as original:
        image = original.convert("RGB")
    scale = max(WIDTH / image.width, HEIGHT / image.height)
    image = image.resize(
        (round(image.width * scale), round(image.height * scale)),
        Image.Resampling.LANCZOS,
    )
    left = (image.width - WIDTH) // 2
    top = (image.height - HEIGHT) // 2
    return image.crop((left, top, left + WIDTH, top + HEIGHT))


def dds_bytes(source: Path = SOURCE) -> bytes:
    payload = io.BytesIO()
    render(source).save(payload, format="DDS", pixel_format="DXT1")
    return payload.getvalue()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify that the tracked DDS is byte-identical to a fresh render",
    )
    args = parser.parse_args(argv)
    if not SOURCE.is_file():
        raise FileNotFoundError(f"decision source art missing: {SOURCE}")
    expected = dds_bytes()
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_bytes() != expected:
            raise RuntimeError(f"generated decision art is stale: {OUTPUT}")
        print(f"verified {OUTPUT.relative_to(ROOT)}")
        return 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(expected)
    if expected[:4] != b"DDS " or expected[84:88] != b"DXT1":
        raise RuntimeError(f"unexpected DDS format: {OUTPUT}")
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
