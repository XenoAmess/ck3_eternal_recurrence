#!/usr/bin/env python3
"""Render the generated Mandala Purge key art as a Workshop thumbnail."""

from __future__ import annotations

import argparse
import io
from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "images" / "remove_mandala_key_art.png"
OUTPUT = ROOT / "mod_remove_mandala" / "thumbnail.png"
SIZE = (640, 640)
MAX_BYTES = 1_000_000


def render(source: Path = SOURCE) -> Image.Image:
    with Image.open(source) as original:
        image = original.convert("RGB")
    return ImageOps.fit(
        image,
        SIZE,
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )


def rendered_bytes(source: Path = SOURCE) -> bytes:
    output = io.BytesIO()
    render(source).save(output, format="PNG", optimize=True, compress_level=9)
    data = output.getvalue()
    if len(data) >= MAX_BYTES:
        raise RuntimeError(
            f"compressed Mandala Purge thumbnail is {len(data)} bytes; "
            f"limit is below {MAX_BYTES}"
        )
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the tracked thumbnail is byte-identical to a fresh render",
    )
    args = parser.parse_args()
    if not SOURCE.is_file():
        raise FileNotFoundError(f"Mandala Purge key art missing: {SOURCE}")
    expected = rendered_bytes()
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_bytes() != expected:
            raise RuntimeError(
                "mod_remove_mandala/thumbnail.png is stale against its key art"
            )
        print(
            f"verified {OUTPUT.relative_to(ROOT)}: {len(expected)} bytes, "
            f"{SIZE[0]}x{SIZE[1]}"
        )
        return 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(expected)
    print(
        f"wrote {OUTPUT.relative_to(ROOT)}: {len(expected)} bytes, "
        f"{SIZE[0]}x{SIZE[1]}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
