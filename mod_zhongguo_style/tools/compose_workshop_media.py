#!/usr/bin/env python3
"""Create deterministic Steam Workshop JPEGs from the final ZhongGuo 361 GREEN run.

The source PNGs remain outside the repository in the immutable acceptance
artifact.  This script only creates presentation projections and never alters
those captures.  ``--check`` renders in memory and verifies the tracked JPEGs
are byte-for-byte current.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
from io import BytesIO
from pathlib import Path
import sys

from PIL import Image


MOD_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = MOD_ROOT / "workshop" / "media"
DEFAULT_ARTIFACTS = Path(
    r"Z:\ck3_mod_rewrite_process_assets\zg361\runs\zga_20260829_061314_ea5f04ad"
)
EXPECTED_SIZE = (2560, 1440)
MAX_BYTES = 2_000_000
JPEG_QUALITY = 90


@dataclass(frozen=True)
class Projection:
    source: str
    source_sha256: str
    output: str
    crop: tuple[int, int, int, int]


PROJECTIONS = (
    Projection(
        "06_calibration_event.png",
        "8e1813d538be9f95736d9f07eb88b7bcb719320d421eb37dfbcfce649bd65aab",
        "01_calibration_meeting.jpg",
        (420, 280, 1610, 875),
    ),
    Projection(
        "07_result_summary.png",
        "b020a11ea9e8e10db7aaace83dff11bbde05cb9b2af6a64b3aa9ce55d92b2f7d",
        "02_review_cohort_frozen.jpg",
        (430, 275, 1605, 885),
    ),
    Projection(
        "08_scoreboard_panel.png",
        "bb45518330ea20399d0b73f6776c72ac5da6f3ebdf1e2c84dc6643430ad9aca3",
        "03_scoreboard.jpg",
        (430, 130, 1640, 1020),
    ),
    Projection(
        "09_jingcha_mandate_event.png",
        "9f7bb4ee382677c035d6256da3d5c113959e2026b3a1ef59fce33d22ae53cb06",
        "04_jingcha_mandate.jpg",
        (420, 280, 1610, 875),
    ),
    Projection(
        "09_jingcha_activity_detail.png",
        "c34f54b69898f8bf5a630226b86dfb185cf3acc2052faa0183d7f771e10123c1",
        "05_free_jingcha_activity.jpg",
        (720, 120, 2000, 1200),
    ),
    Projection(
        "10_superior_result.png",
        "93ecfad072711b6caa1759fefa267f492897e36b8ce14905230541a7f7eab46f",
        "06_superior_325_result.jpg",
        (430, 275, 1605, 885),
    ),
)


def sha256(data: bytes | Path) -> str:
    if isinstance(data, Path):
        data = data.read_bytes()
    return hashlib.sha256(data).hexdigest()


def jpeg_bytes(source: Path, crop: tuple[int, int, int, int]) -> tuple[bytes, tuple[int, int]]:
    with Image.open(source) as image:
        image.load()
        if image.size != EXPECTED_SIZE:
            raise ValueError(f"unexpected capture size for {source.name}: {image.size}")
        projected = image.convert("RGB").crop(crop)
        output = BytesIO()
        projected.save(
            output,
            format="JPEG",
            quality=JPEG_QUALITY,
            optimize=True,
            progressive=True,
            subsampling=0,
        )
    return output.getvalue(), projected.size


def render(artifacts: Path, output: Path, *, check: bool) -> list[dict[str, object]]:
    cell = artifacts / "cell" if (artifacts / "cell").is_dir() else artifacts
    expected_outputs = {projection.output for projection in PROJECTIONS}
    existing = {path.name for path in output.glob("*.jpg")} if output.is_dir() else set()
    unexpected = sorted(existing - expected_outputs)
    if unexpected:
        raise ValueError(f"unexpected Workshop JPEGs: {unexpected}")
    if not check:
        output.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, object]] = []
    stale: list[str] = []
    for projection in PROJECTIONS:
        source = cell / projection.source
        if not source.is_file():
            raise ValueError(f"acceptance capture missing: {source}")
        actual_source_hash = sha256(source)
        if actual_source_hash != projection.source_sha256:
            raise ValueError(
                f"source hash mismatch for {source.name}: {actual_source_hash}"
            )
        data, dimensions = jpeg_bytes(source, projection.crop)
        if len(data) >= MAX_BYTES:
            raise ValueError(
                f"Workshop image exceeds 2 MB: {projection.output} ({len(data)} bytes)"
            )
        target = output / projection.output
        if check:
            if not target.is_file() or target.read_bytes() != data:
                stale.append(str(target.relative_to(MOD_ROOT)))
        else:
            target.write_bytes(data)
        records.append(
            {
                "source": projection.source,
                "source_sha256": actual_source_hash,
                "output": projection.output,
                "crop": projection.crop,
                "dimensions": dimensions,
                "bytes": len(data),
                "sha256": sha256(data),
            }
        )
    if stale:
        raise ValueError("stale Workshop media: " + ", ".join(stale))
    return records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, default=DEFAULT_ARTIFACTS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args(argv)
    try:
        records = render(arguments.artifacts.resolve(), arguments.output.resolve(), check=arguments.check)
    except (OSError, ValueError) as error:
        print(f"RED: {error}", file=sys.stderr)
        return 1
    for record in records:
        print(
            f"{record['output']}: {record['dimensions'][0]}x{record['dimensions'][1]}, "
            f"{record['bytes']} bytes, SHA-256 {record['sha256']}"
        )
    print(f"GREEN: {len(records)} deterministic Workshop JPEGs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
