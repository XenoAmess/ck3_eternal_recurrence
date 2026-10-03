#!/usr/bin/env python3
"""Project the accepted clean experience-view capture into Workshop media."""

from __future__ import annotations

import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import sys

from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = ROOT / "images" / "superman_qiang_gameplay_experience.png"
DEFAULT_OUTPUT = ROOT / "workshop" / "superman_qiang_media" / "01_experience_view.jpg"
SOURCE_SHA256 = "dbb4b4085b775fcc93b9b2a1f13de82a2a6f4b562886f4409356a0561450e5cf"
EXPECTED_SIZE = (1024, 768)
CROP = (0, 0, 1024, 768)
QUALITY = 90
MAX_BYTES = 1024 * 1024


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_green_gate(path: Path) -> dict[str, object]:
    gate = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(gate, dict):
        raise ValueError("acceptance gate root must be an object")
    expected = {
        "schema": "sxad.genuine-existing-save-installation-gate.v1",
        "ok": True,
        "vanilla_loading": {"enabled_mods": [], "disabled_dlcs": []},
        "production_loading": {"enabled_mods": ["mod/sxad_product.mod"], "disabled_dlcs": []},
        "changed_character_ids": [],
        "viewed_subject": 31254,
        "normal_ui_experience": 0,
        "normal_ui_effective_skills": [5, 24, 11, 11, 7, 21],
        "image_sha256": SOURCE_SHA256,
        "image_size": list(EXPECTED_SIZE),
        "error_log_sha256": sha256_bytes(b""),
    }
    if any(gate.get(key) != value for key, value in expected.items()):
        raise ValueError("media requires the clean production-only R0013 acceptance gate")
    return gate


def rendered_bytes(source: Path) -> tuple[bytes, tuple[int, int]]:
    raw = source.read_bytes()
    if sha256_bytes(raw) != SOURCE_SHA256:
        raise ValueError("gameplay capture SHA-256 differs from the accepted source")
    with Image.open(BytesIO(raw)) as image:
        image.load()
        if image.format != "PNG" or image.size != EXPECTED_SIZE:
            raise ValueError(f"unexpected gameplay capture format or dimensions: {image.format}, {image.size}")
        projected = image.convert("RGB").crop(CROP)
        stream = BytesIO()
        # Same encoding contract as the existing Workshop media composers.
        projected.save(stream, format="JPEG", quality=QUALITY, optimize=True,
                       progressive=True, subsampling=0)
    data = stream.getvalue()
    if len(data) >= MAX_BYTES:
        raise ValueError(f"Workshop native media must be below 1 MiB ({len(data)} bytes)")
    return data, projected.size


def render(source: Path, output: Path, gate_path: Path, *, check: bool = False) -> dict[str, object]:
    load_green_gate(gate_path)
    data, dimensions = rendered_bytes(source)
    if check:
        if not output.is_file() or output.read_bytes() != data:
            raise ValueError("checked-in media differs from the deterministic projection")
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(data)
    return {
        "gate": str(gate_path.resolve()),
        "gate_sha256": sha256_bytes(gate_path.read_bytes()),
        "source": str(source.resolve()), "source_sha256": SOURCE_SHA256,
        "source_bytes": source.stat().st_size,
        "output": str(output.resolve()), "crop": list(CROP),
        "dimensions": list(dimensions), "bytes": len(data), "sha256": sha256_bytes(data),
        "quality": QUALITY, "optimize": True, "progressive": True, "subsampling": 0,
        "check": check,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--gate", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        record = render(args.source, args.output, args.gate, check=args.check)
    except (OSError, ValueError) as error:
        print(f"SUPERMAN QIANG WORKSHOP MEDIA FAILED: {error}", file=sys.stderr)
        return 1
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
