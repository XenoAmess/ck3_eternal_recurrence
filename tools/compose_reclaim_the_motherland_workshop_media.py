#!/usr/bin/env python3
"""Project real CK3 Reclaim acceptance captures into Workshop JPEGs."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT / "workshop" / "reclaim_the_motherland_media"
MAX_BYTES = 2_000_000
EXPECTED_SIZE = (2560, 1440)
QUALITY = 90
PROJECTIONS = (
    (
        "07_loyalty_summary.png",
        "00_divided_hearts_live.jpg",
        # Keep only the ordinary player event and surrounding China map. The
        # acceptance fixture's decision drawer and diagnostic notifications sit
        # outside this crop and must never enter storefront media.
        (300, 180, 1690, 920),
    ),
    (
        "08_later_dynasty_character.png",
        "01_later_dynasty_live.jpg",
        (0, 0, 1500, 1050),
    ),
    (
        "09_decision_visibility.png",
        "02_restoration_decision_live.jpg",
        (1400, 275, 2540, 650),
    ),
    (
        "10_restore_confirm.png",
        "03_restoration_confirm_live.jpg",
        (380, 275, 1800, 1130),
    ),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid acceptance evidence: {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"acceptance evidence is not an object: {path}")
    return value


def validate_capital_centered_green_run(artifacts: Path, cell: Path) -> None:
    report = read_json(artifacts / "report.json")
    navigation = read_json(cell / "08_song_capital_navigation.json")
    native = navigation.get("native_navigation")
    title = native.get("title") if isinstance(native, dict) else None
    camera = native.get("camera_center") if isinstance(native, dict) else None
    visual = navigation.get("visual_checks")
    checks = {
        "run_green": report.get("result") == "GREEN",
        "navigation_green": navigation.get("result") == "GREEN",
        "mcp_tool": navigation.get("mcp_tool")
        == "ck3_center_map_on_landed_title_v1",
        "kaifeng_title": isinstance(title, dict) and title.get("key") == "b_kaifeng",
        "title_bounds_center": isinstance(title, dict)
        and title.get("anchor_kind") == "title_bounds_center",
        "camera_settled": isinstance(camera, dict) and camera.get("settled") is True,
        "camera_postcondition": isinstance(camera, dict)
        and camera.get("postcondition_verified") is True,
        "camera_current_target_equal": isinstance(camera, dict)
        and camera.get("current_state") == camera.get("target_state"),
        "capital_region_visible": isinstance(visual, dict)
        and visual.get("song_capital_region_name_visible") is True,
        "italy_absent": isinstance(visual, dict)
        and visual.get("italy_labels_absent") is True,
        "acceptance_copy_absent": isinstance(visual, dict)
        and visual.get("acceptance_copy_absent") is True,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError(
            "Workshop media requires a GREEN Kaifeng-centered run; failed: "
            + ", ".join(failed)
        )


def render(artifacts: Path, output: Path) -> list[dict[str, object]]:
    artifacts = Path(artifacts).resolve()
    cell = artifacts / "cell" if (artifacts / "cell").is_dir() else artifacts
    validate_capital_centered_green_run(artifacts, cell)
    output.mkdir(parents=True, exist_ok=True)
    expected_outputs = {name for _, name, _ in PROJECTIONS}
    unexpected = sorted(
        path.name for path in output.glob("*.jpg") if path.name not in expected_outputs
    )
    if unexpected:
        raise ValueError(f"unexpected Workshop JPEGs: {unexpected}")

    records: list[dict[str, object]] = []
    for source_name, output_name, crop in PROJECTIONS:
        source = cell / source_name
        if not source.is_file():
            raise ValueError(f"acceptance capture missing: {source}")
        with Image.open(source) as image:
            image.load()
            if image.size != EXPECTED_SIZE:
                raise ValueError(f"unexpected capture size for {source_name}: {image.size}")
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
        print(f"RECLAIM WORKSHOP MEDIA FAILED: {error}", file=sys.stderr)
        return 1
    for record in records:
        print(
            f"{record['output']}: {record['dimensions'][0]}x{record['dimensions'][1]}, "
            f"{record['bytes']} bytes, SHA-256 {record['sha256']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
