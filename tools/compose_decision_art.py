"""Render XAR decision source art as CK3-native 1100x440 DXT1 DDS files."""

from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "images"
OUTPUT_DIR = (
    ROOT / "XenoAmess_s_Eternal_Recurrence" / "gfx" / "interface"
    / "illustrations" / "decisions"
)
WIDTH = 1100
HEIGHT = 440
ASSETS = {
    "decision_glassfire_ledger.png": "decision_xar_ledger.dds",
    "decision_lifetime_contract.png": "decision_xar_contract.dds",
    "decision_glassfire_courtier.png": "decision_xar_courtier.dds",
}


def render(source):
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


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for source_name, output_name in ASSETS.items():
        source = SOURCE_DIR / source_name
        output = OUTPUT_DIR / output_name
        if not source.is_file():
            raise FileNotFoundError(f"decision source art missing: {source}")
        render(source).save(output, pixel_format="DXT1")
        with output.open("rb") as stream:
            header = stream.read(128)
        if header[:4] != b"DDS " or header[84:88] != b"DXT1":
            raise RuntimeError(f"unexpected DDS format: {output}")
        print(f"wrote {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
