"""Render the Vivhite key art as its launcher and Workshop thumbnail."""

import io
from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "images" / "vivhite_courtier_key_art.png"
OUTPUT = ROOT / "Eternal_Recurrence_Vivhite_Courtier" / "thumbnail.png"
SIZE = (640, 640)


def render(source=SOURCE):
    with Image.open(source) as original:
        image = original.convert("RGB")
    return ImageOps.fit(
        image,
        SIZE,
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )


def rendered_bytes(source=SOURCE):
    output = io.BytesIO()
    render(source).save(output, format="PNG", optimize=True)
    return output.getvalue()


def main():
    if not SOURCE.is_file():
        raise FileNotFoundError(f"Vivhite key art missing: {SOURCE}")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(rendered_bytes())
    print(f"wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
