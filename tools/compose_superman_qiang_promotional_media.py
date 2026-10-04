#!/usr/bin/env python3
"""Project generated marketing posters to a fixed publish size; no content edits."""
from __future__ import annotations
import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import sys

from PIL import Image

SIZE = (1600, 900)
QUALITY = 95
MAX_BYTES = 1024 * 1024
NAMES = ("01_absorption", "02_transfer", "03_records")

def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def rendered_bytes(source: Path) -> tuple[bytes, dict[str, object]]:
    raw = source.read_bytes()
    with Image.open(BytesIO(raw)) as image:
        image.load()
        width, height = image.size
        if image.format != "PNG":
            raise ValueError("generated source must be PNG")
        target_ratio = SIZE[0] / SIZE[1]
        if width / height > target_ratio:
            crop_height = float(height)
            crop_width = height * target_ratio
        else:
            crop_width = float(width)
            crop_height = width / target_ratio
        left, top = (width - crop_width) / 2, (height - crop_height) / 2
        crop = (left, top, left + crop_width, top + crop_height)
        projected = image.convert("RGB").resize(SIZE, Image.Resampling.LANCZOS, box=crop)
        stream = BytesIO()
        projected.save(stream, format="JPEG", quality=QUALITY, optimize=True,
                       progressive=True, subsampling=0)
    output = stream.getvalue()
    if len(output) >= MAX_BYTES:
        raise ValueError(f"native media must be below 1 MiB: {len(output)} bytes")
    return output, {
        "source_path": source.resolve().as_posix(), "source_sha256": digest(raw),
        "source_bytes": len(raw), "source_dimensions": [width, height],
        "source_crop_left_top_right_bottom": list(crop),
        "projection": "centered aspect-preserving crop and LANCZOS size projection",
        "output_dimensions": list(SIZE), "output_format": "JPEG", "output_mode": "RGB",
        "quality": QUALITY, "optimize": True, "progressive": True, "subsampling": 0,
        "output_sha256": digest(output), "output_bytes": len(output),
        "content_editing": False,
    }

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        manifest = json.loads(args.manifest.read_bytes())
        entries = {entry["id"]: entry for entry in manifest["entries"] if entry["selected"]}
        if set(entries) != set(NAMES) or manifest["prior_R13_media_used"] is not False:
            raise ValueError("manifest does not bind the three new selected poster sources")
        records = []
        for name in NAMES:
            source = args.source_dir / (name + ".png")
            data, record = rendered_bytes(source)
            if record["source_sha256"] != entries[name]["sha256"]:
                raise ValueError(f"source differs from generation manifest: {name}")
            output = args.output_dir / (name + ".jpg")
            if args.check:
                if output.read_bytes() != data:
                    raise ValueError(f"projection differs from reviewed bytes: {name}")
            else:
                output.parent.mkdir(parents=True, exist_ok=True)
                with output.open("xb") as handle:
                    handle.write(data)
            record["output_path"] = output.resolve().as_posix()
            records.append(record)
        print(json.dumps({"check": args.check, "posters": records}, ensure_ascii=False, indent=2))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"MARKETING MEDIA PROJECTION FAILED: {error}", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
