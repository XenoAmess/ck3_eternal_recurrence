#!/usr/bin/env python3
"""Compress selected real CK3 Auto Upgrade Buildings captures for Workshop."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT / "workshop" / "auto_upgrade_buildings_media"
MAX_BYTES = 2_000_000
EXPECTED_SIZE = (2560, 1440)
QUALITY = 90
PROJECTIONS = (
    (
        "05_policy_selector_clean_surface.png",
        "ca1687baced2205882c27192e8546705079e03358c213454cee57041cc38da9d",
        "01_policy_selector.jpg",
    ),
    (
        "05_policy_selector_hover_treasury_first_pause.png",
        "4d3ec4f56dab7b7a015a07c522cb6f59b9929d736c668de0159f37271facded4",
        "02_policy_hover_treasury_first_pause.jpg",
    ),
    (
        "05_policy_selector_natural_confirmation.png",
        "344227287c91db6eafa305edd4afc77da8202d9c1732d7c4d515ca6857233703",
        "03_policy_confirmation.jpg",
    ),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render(artifacts: Path, output: Path) -> list[dict[str, object]]:
    artifacts = Path(artifacts).resolve()
    cell = artifacts / "cell" if (artifacts / "cell").is_dir() else artifacts
    output.mkdir(parents=True, exist_ok=True)
    expected_outputs = {output_name for _, _, output_name in PROJECTIONS}
    unexpected = sorted(
        path.name for path in output.glob("*.jpg") if path.name not in expected_outputs
    )
    if unexpected:
        raise ValueError(f"unexpected Workshop JPEGs: {unexpected}")

    records: list[dict[str, object]] = []
    for source_name, expected_source_sha256, output_name in PROJECTIONS:
        source = cell / source_name
        if not source.is_file():
            raise ValueError(f"acceptance capture missing: {source}")
        source_sha256 = sha256(source)
        if source_sha256 != expected_source_sha256:
            raise ValueError(
                f"unexpected source bytes for {source_name}: {source_sha256}"
            )
        with Image.open(source) as image:
            image.load()
            if image.size != EXPECTED_SIZE:
                raise ValueError(f"unexpected capture size for {source_name}: {image.size}")
            projected = image.convert("RGB")
            target = output / output_name
            projected.save(
                target,
                format="JPEG",
                quality=QUALITY,
                optimize=True,
                progressive=True,
                subsampling=0,
            )
        size = target.stat().st_size
        if size >= MAX_BYTES:
            raise ValueError(f"Workshop image exceeds 2 MB: {target} ({size} bytes)")
        records.append(
            {
                "source": source_name,
                "source_sha256": source_sha256,
                "output": output_name,
                "dimensions": list(projected.size),
                "bytes": size,
                "sha256": sha256(target),
            }
        )
    return records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    try:
        records = render(args.artifacts, args.output)
    except (OSError, ValueError) as error:
        print(f"AUTO UPGRADE BUILDINGS WORKSHOP MEDIA FAILED: {error}", file=sys.stderr)
        return 1
    for record in records:
        print(
            f"{record['output']}: {record['dimensions'][0]}x{record['dimensions'][1]}, "
            f"{record['bytes']} bytes, SHA-256 {record['sha256']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
