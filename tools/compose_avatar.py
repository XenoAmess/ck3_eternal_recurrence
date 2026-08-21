"""Compose the wide event-scene source images into CK3-native DDS files.

Event windows reserve the left side for text. The source images therefore
use a wide composition with the focal subject on the right; this generator
cover-crops each source to CK3's 1592x848 event-scene canvas and applies the
same mild left-column darkening used by the original Glassfire scene. The
ASSETS mapping is the authoritative source/output inventory and is also
consumed by the static parity checks.
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "images"
OUTPUT_DIR = (
    ROOT / "XenoAmess_s_Eternal_Recurrence" / "gfx" / "interface"
    / "illustrations" / "event_scenes"
)
W, H = 1592, 848
ASSETS = {
    "glassfire_avatar_wide.png": "xar_glassfire_avatar.dds",
    "recurrence_end_wide.png": "xar_recurrence_end.dds",
}

# Compatibility aliases for callers that used the original single-asset
# script constants.
SRC = str(SOURCE_DIR / "glassfire_avatar_wide.png")
OUT_DIR = str(OUTPUT_DIR)
OUT = str(OUTPUT_DIR / "xar_glassfire_avatar.dds")


def render(source):
    """Return a rendered RGB event scene at exactly 1592x848 pixels."""
    with Image.open(source) as original:
        image = original.convert("RGB")

    # Cover-crop to exactly the CK3 event-scene dimensions.
    scale = max(W / image.width, H / image.height)
    image = image.resize(
        (round(image.width * scale), round(image.height * scale)),
        Image.Resampling.LANCZOS,
    )
    left = (image.width - W) // 2
    top = (image.height - H) // 2
    canvas = image.crop((left, top, left + W, top + H))

    # Mild gradient darkening over the left text column (text readability).
    text_w = round(W * 0.55)
    gradient = Image.linear_gradient("L").resize((text_w, 1))
    gradient = gradient.rotate(90, expand=True).resize((text_w, H))
    gradient = gradient.point(lambda value: max(0, 70 - round(value * 70 / 255)))
    canvas.paste(Image.new("RGB", (text_w, H), (0, 0, 0)), (0, 0), gradient)
    return canvas


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for source_name, output_name in ASSETS.items():
        source = SOURCE_DIR / source_name
        output = OUTPUT_DIR / output_name
        if not source.is_file():
            raise FileNotFoundError(f"event source art missing: {source}")
        render(source).save(output, pixel_format="DXT1")
        with output.open("rb") as stream:
            header = stream.read(128)
        if header[:4] != b"DDS " or header[84:88] != b"DXT1":
            raise RuntimeError(f"unexpected DDS format: {output}")
        print(f"wrote {output.relative_to(ROOT)} ({output.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
