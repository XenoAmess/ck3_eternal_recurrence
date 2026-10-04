#!/usr/bin/env python3
"""Crop and encode one hash-bound real PNG; never alter UI content or capture it."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
import sys

from PIL import Image, __version__ as pillow_version

MAX_BYTES = 1024 * 1024


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def project(source: Path, expected_sha: str, crop: tuple[int, int, int, int] | None,
            quality: int) -> tuple[bytes, bytes, dict[str, object]]:
    expected_sha = expected_sha.lower()
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha):
        raise ValueError("source SHA-256 must be exactly 64 hexadecimal characters")
    raw = source.read_bytes()
    if digest(raw) != expected_sha:
        raise ValueError("source bytes differ from the explicitly supplied SHA-256")
    if not 1 <= quality <= 100:
        raise ValueError("JPEG quality must be 1 to 100")
    with Image.open(BytesIO(raw)) as original:
        original.load()
        if original.format != "PNG":
            raise ValueError("real original capture must be a preserved PNG")
        width, height = original.size
        source_mode = original.mode
        rect = crop if crop is not None else (0, 0, width, height)
        left, top, right, bottom = rect
        if not (0 <= left < right <= width and 0 <= top < bottom <= height):
            raise ValueError(f"crop {rect} is outside actual source dimensions {(width, height)}")
        output = original.convert("RGB").crop(rect)
        stream = BytesIO()
        output.save(stream, "JPEG", quality=quality, optimize=True,
                    progressive=True, subsampling=0)
        projected = stream.getvalue()
    return raw, projected, {
        "source_path": source.resolve().as_posix(), "source_sha256": digest(raw),
        "source_bytes": len(raw), "source_dimensions": [width, height],
        "source_format": "PNG", "source_mode": source_mode,
        "crop_left_top_right_bottom": list(rect),
        "output_dimensions": [right - left, bottom - top],
        "output_format": "JPEG", "output_mode": "RGB", "quality": quality,
        "optimize": True, "progressive": True, "subsampling": 0,
        "resized": False, "content_edited": False, "image_generation_used": False,
        "output_bytes": len(projected), "output_sha256": digest(projected),
        "strict_max_bytes": MAX_BYTES, "below_native_byte_limit": len(projected) < MAX_BYTES,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--crop", type=int, nargs=4, metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"))
    parser.add_argument("--quality", type=int, default=95)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--capture-report", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        if not re.fullmatch(r"[A-Za-z0-9_-]+", args.name):
            raise ValueError("name must be a simple ASCII basename")
        raw, projected, details = project(args.source, args.source_sha256,
                                         tuple(args.crop) if args.crop is not None else None,
                                         args.quality)
        directory = args.output_dir.resolve()
        target = directory / (args.name + ".jpg")
        retained = directory / (args.name + ".raw.png")
        provenance = directory / (args.name + ".provenance.json")
        if args.check:
            if retained.read_bytes() != raw or target.read_bytes() != projected:
                raise ValueError("retained source or JPEG differs from the deterministic projection")
            if not details["below_native_byte_limit"]:
                raise ValueError("checked media exceeds the strict native 1 MiB byte limit")
            print(json.dumps({"check": True, "byte_identical": True, **details}, ensure_ascii=False, indent=2))
            return 0
        directory.mkdir(parents=True, exist_ok=True)
        if any(path.exists() for path in (target, retained, provenance)):
            raise ValueError("new projection requires a fresh output name/attempt; existing assets are preserved")
        with retained.open("xb") as handle:
            handle.write(raw)
        actual_target = target if details["below_native_byte_limit"] else target.with_name(args.name + ".oversize.jpg")
        with actual_target.open("xb") as handle:
            handle.write(projected)
        report_identity = None
        if args.capture_report is not None:
            report_raw = args.capture_report.read_bytes()
            report_identity = {"path": args.capture_report.resolve().as_posix(),
                               "bytes": len(report_raw), "sha256": digest(report_raw)}
        record = {
            "schema": "superman-qiang.real-gameplay-screenshot-projection.v1",
            "recorded_utc": datetime.now(timezone.utc).isoformat(),
            "status": "pending_direct_visual_and_capture_review" if details["below_native_byte_limit"] else "rejected_native_byte_limit",
            **details, "retained_raw_path": retained.as_posix(),
            "output_path": actual_target.as_posix(), "capture_report": report_identity,
            "capture_result_inferred": False,
            "visual_review": "pending", "published": False,
            "tool": {"path": str(Path(__file__).resolve()),
                     "sha256": digest(Path(__file__).read_bytes()),
                     "argv": [sys.executable, *sys.argv], "pillow_version": pillow_version,
                     "python_version": sys.version},
        }
        with provenance.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps(record, ensure_ascii=False, indent=2))
        if not details["below_native_byte_limit"]:
            return 1
    except (OSError, ValueError) as error:
        print(f"REAL GAMEPLAY PROJECTION FAILED: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
