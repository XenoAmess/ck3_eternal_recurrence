"""Render the ten-level trait overlay required by CK3's star texture convention."""

import math
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = (
    ROOT / "XenoAmess_s_Eternal_Recurrence" / "gfx" / "interface"
    / "icons" / "traits" / "_stars_10.dds"
)
SIZE = 120
SCALE = 4


def star_points(center_x, center_y, outer_radius, inner_radius):
    points = []
    for index in range(10):
        angle = -math.pi / 2 + index * math.pi / 5
        radius = outer_radius if index % 2 == 0 else inner_radius
        points.append((
            center_x + math.cos(angle) * radius,
            center_y + math.sin(angle) * radius,
        ))
    return points


def render():
    canvas = Image.new("RGBA", (SIZE * SCALE, SIZE * SCALE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    for y in (47, 73):
        for x in (20, 40, 60, 80, 100):
            draw.polygon(
                star_points(
                    (x + 1.5) * SCALE, (y + 2) * SCALE,
                    10.5 * SCALE, 4.5 * SCALE),
                fill=(10, 6, 3, 150),
            )
            draw.polygon(
                star_points(
                    x * SCALE, y * SCALE, 10.5 * SCALE, 4.5 * SCALE),
                fill=(74, 50, 28, 255),
            )
            draw.polygon(
                star_points(
                    x * SCALE, (y - 0.5) * SCALE, 9 * SCALE, 3.9 * SCALE),
                fill=(190, 153, 100, 255),
            )
    return canvas.resize((SIZE, SIZE), Image.Resampling.LANCZOS)


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    render().save(OUTPUT)
    with OUTPUT.open("rb") as stream:
        header = stream.read(128)
    if header[:4] != b"DDS " or header[84:88] != b"\0\0\0\0":
        raise RuntimeError(f"unexpected uncompressed DDS format: {OUTPUT}")
    print(f"wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
