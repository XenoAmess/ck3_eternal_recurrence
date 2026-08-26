#!/usr/bin/env python3
"""Crop and compress real CK3 Ox Here acceptance captures for Workshop."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys

from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT / "workshop" / "ox_here_media"
MAX_BYTES = 2_000_000
EXPECTED_SIZE = (2560, 1440)
QUALITY = 90
PROJECTIONS = (
    (
        "07_recruit_option.png",
        "01_decision_options.jpg",
        (900, 90, 1720, 1380),
    ),
    (
        "08_ox_here_arrival_event.png",
        "02_arrival_event.jpg",
        (575, 270, 1980, 1085),
    ),
    (
        "08_ox_here_arrival_event.png",
        "03_warrior_portrait.jpg",
        (1160, 300, 1880, 1085),
    ),
    (
        "08_ox_here_arrival_event_closed.png",
        "04_champion_appointment.jpg",
        (635, 55, 1740, 300),
    ),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render(artifacts: Path, output: Path) -> list[dict[str, object]]:
    artifacts = Path(artifacts).resolve()
    cell = artifacts / "cell" if (artifacts / "cell").is_dir() else artifacts
    output.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []
    expected_outputs = {name for _, name, _ in PROJECTIONS}
    existing = {path.name for path in output.glob("*.jpg")}
    unexpected = sorted(existing - expected_outputs)
    if unexpected:
        raise ValueError(f"unexpected Workshop JPEGs: {unexpected}")
    for source_name, output_name, crop in PROJECTIONS:
        source = cell / source_name
        if not source.is_file():
            raise ValueError(f"acceptance capture missing: {source}")
        with Image.open(source) as image:
            image.load()
            if image.size != EXPECTED_SIZE:
                raise ValueError(
                    f"unexpected capture size for {source_name}: {image.size}"
                )
            projected = image.convert("RGB").crop(crop)
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
                "source_sha256": sha256(source),
                "output": output_name,
                "crop": list(crop),
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
        print(f"OX HERE WORKSHOP MEDIA FAILED: {error}", file=sys.stderr)
        return 1
    for record in records:
        print(
            f"{record['output']}: {record['dimensions'][0]}x{record['dimensions'][1]}, "
            f"{record['bytes']} bytes, SHA-256 {record['sha256']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
