#!/usr/bin/env python3
"""Compose the ZhongGuo 361 key art into the Workshop thumbnail.

The image model deliberately left the central medallion blank.  This script
adds exact typography (image models are not trusted for release text), keeps a
full-resolution titled master, and exports the launcher's required 640 px PNG.
"""

from __future__ import annotations

import argparse
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


MOD_ROOT = Path(__file__).resolve().parent.parent
SOURCE = MOD_ROOT / "images" / "zg361_key_art_imagegen_v1.png"
MASTER = MOD_ROOT / "images" / "zg361_key_art_titled_v1.png"
THUMBNAIL = MOD_ROOT / "thumbnail.png"
EXPECTED_SOURCE_SIZE = (1254, 1254)
THUMBNAIL_SIZE = (640, 640)
MAX_THUMBNAIL_BYTES = 1_000_000


def find_font(*, bold: bool) -> Path:
    candidates = (
        Path("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        "Microsoft YaHei or SimHei is required to reproduce the thumbnail"
    )


def png_bytes(image: Image.Image) -> bytes:
    output = BytesIO()
    image.save(output, format="PNG", optimize=True, compress_level=9)
    return output.getvalue()


def render() -> tuple[bytes, bytes]:
    with Image.open(SOURCE) as opened:
        if opened.size != EXPECTED_SOURCE_SIZE:
            raise ValueError(
                f"source must be {EXPECTED_SOURCE_SIZE}, got {opened.size}"
            )
        image = opened.convert("RGB")

    draw = ImageDraw.Draw(image)
    number_font = ImageFont.truetype(str(find_font(bold=True)), 246)
    title_font = ImageFont.truetype(str(find_font(bold=True)), 61)

    # The gold disc occupies the upper middle of the generated scene.  A soft
    # shadow and narrow warm-gold stroke make the exact type feel engraved.
    center_x = image.width // 2
    draw.text(
        (center_x + 7, 236 + 9),
        "361",
        font=number_font,
        anchor="mm",
        fill=(73, 35, 18),
        stroke_width=5,
        stroke_fill=(73, 35, 18),
    )
    draw.text(
        (center_x, 236),
        "361",
        font=number_font,
        anchor="mm",
        fill=(119, 21, 24),
        stroke_width=4,
        stroke_fill=(239, 190, 76),
    )
    draw.rounded_rectangle(
        (center_x - 184, 340, center_x + 184, 423),
        radius=18,
        fill=(76, 22, 17, 230),
        outline=(231, 178, 68),
        width=4,
    )
    draw.text(
        (center_x, 382),
        "天朝绩效制",
        font=title_font,
        anchor="mm",
        fill=(247, 215, 130),
        stroke_width=1,
        stroke_fill=(43, 12, 10),
    )

    master = png_bytes(image)
    thumbnail_image = image.resize(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
    thumbnail = png_bytes(thumbnail_image)
    if len(thumbnail) >= MAX_THUMBNAIL_BYTES:
        raise ValueError(
            f"thumbnail is {len(thumbnail)} bytes; must stay below "
            f"{MAX_THUMBNAIL_BYTES}"
        )
    return master, thumbnail


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args(argv)

    try:
        master, thumbnail = render()
    except (OSError, ValueError) as error:
        print(f"RED: {error}")
        return 1

    outputs = ((MASTER, master), (THUMBNAIL, thumbnail))
    if arguments.check:
        stale = [path for path, data in outputs if not path.is_file() or path.read_bytes() != data]
        if stale:
            print("RED: stale thumbnail projection:")
            for path in stale:
                print(f"  - {path.relative_to(MOD_ROOT)}")
            return 1
        print(
            "GREEN: thumbnail projection is reproducible "
            f"({len(thumbnail)} bytes, {THUMBNAIL_SIZE[0]}x{THUMBNAIL_SIZE[1]})"
        )
        return 0

    for path, data in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    print(
        "GREEN: composed titled key art and thumbnail "
        f"({len(thumbnail)} bytes, {THUMBNAIL_SIZE[0]}x{THUMBNAIL_SIZE[1]})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
