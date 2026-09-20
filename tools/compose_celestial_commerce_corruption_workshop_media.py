#!/usr/bin/env python3
"""Project a GREEN corruption-policy capture into the Workshop media strip."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "workshop/celestial_commerce_corruption_media"
SOURCE_NAME = "07_production_event_tier_four.png"
OUTPUT_NAME = "01_corruption_policy_event.jpg"
EXPECTED_SIZE = (2560, 1440)
CROP = (575, 343, 1895, 1086)
QUALITY = 90
MAX_BYTES = 2_000_000


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def load_green_report(artifacts: Path) -> Path:
    report_path = artifacts / "report.json"
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read acceptance report: {error}") from error
    cell = report.get("cell") if isinstance(report, dict) else None
    if report.get("result") != "GREEN" or not isinstance(cell, dict):
        raise ValueError("Workshop gameplay media requires a GREEN acceptance report")
    evidence = cell.get("scenario_evidence")
    expected = {
        "installed_build": "1.19.0.6",
        "celestial_government_allows_barter": True,
        "production_decision_rendered_and_confirmed": True,
        "production_event_tier_four_selected": True,
        "corruption_trait_applied": "xccc_corruption_4",
        "tier_four_tax_rate": 0.5,
    }
    if not isinstance(evidence, dict) or any(
        evidence.get(key) != value for key, value in expected.items()
    ):
        raise ValueError("GREEN report lacks the corruption-policy evidence contract")
    return report_path


def rendered_bytes(source: Path) -> tuple[bytes, tuple[int, int]]:
    with Image.open(source) as image:
        image.load()
        if image.size != EXPECTED_SIZE:
            raise ValueError(f"unexpected gameplay capture dimensions: {image.size}")
        projected = image.convert("RGB").crop(CROP)
        stream = BytesIO()
        projected.save(
            stream,
            format="JPEG",
            quality=QUALITY,
            optimize=True,
            progressive=True,
            subsampling=0,
        )
    return stream.getvalue(), projected.size


def render(artifacts: Path, output: Path) -> dict[str, object]:
    artifacts = Path(artifacts).resolve()
    output = Path(output).resolve()
    report_path = load_green_report(artifacts)
    cell = artifacts / "cell" if (artifacts / "cell").is_dir() else artifacts
    source = cell / SOURCE_NAME
    if not source.is_file():
        raise ValueError(f"GREEN gameplay capture missing: {source}")
    unexpected = (
        sorted(path.name for path in output.glob("*.jpg") if path.name != OUTPUT_NAME)
        if output.is_dir()
        else []
    )
    if unexpected:
        raise ValueError(f"unexpected Workshop JPEGs: {unexpected}")
    data, dimensions = rendered_bytes(source)
    if len(data) >= MAX_BYTES:
        raise ValueError(f"Workshop image exceeds 2 MB ({len(data)} bytes)")
    output.mkdir(parents=True, exist_ok=True)
    target = output / OUTPUT_NAME
    target.write_bytes(data)
    return {
        "report": str(report_path),
        "report_sha256": sha256_file(report_path),
        "source": str(source),
        "source_sha256": sha256_file(source),
        "output": str(target),
        "crop": list(CROP),
        "dimensions": list(dimensions),
        "bytes": len(data),
        "sha256": sha256_bytes(data),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    try:
        record = render(args.artifacts, args.output)
    except (OSError, ValueError) as error:
        print(f"CELESTIAL COMMERCE WORKSHOP MEDIA FAILED: {error}", file=sys.stderr)
        return 1
    print(
        f"{Path(record['output']).name}: "
        f"{record['dimensions'][0]}x{record['dimensions'][1]}, "
        f"{record['bytes']} bytes, SHA-256 {record['sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
