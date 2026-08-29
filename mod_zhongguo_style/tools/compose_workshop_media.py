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
import json
from pathlib import Path
import sys
from typing import Any, Sequence

from PIL import Image


MOD_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = MOD_ROOT / "workshop" / "media"
DEFAULT_POLICY_LOCK = MOD_ROOT / "workshop" / "media-policy-lock.json"
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
    output_sha256: str


@dataclass(frozen=True)
class PolicyCardRecipe:
    mechanism_id: int
    source: str
    output: str
    crop: tuple[int, int, int, int]


PROJECTIONS = (
    Projection(
        "06_calibration_event.png",
        "8e1813d538be9f95736d9f07eb88b7bcb719320d421eb37dfbcfce649bd65aab",
        "01_calibration_meeting.jpg",
        (420, 280, 1610, 875),
        "abdc899a14ce6ce0f48df5af0e18290efa65971e65ebea3e39eb94bba59575a2",
    ),
    Projection(
        "07_result_summary.png",
        "b020a11ea9e8e10db7aaace83dff11bbde05cb9b2af6a64b3aa9ce55d92b2f7d",
        "02_review_cohort_frozen.jpg",
        (430, 275, 1605, 885),
        "9ca4d85efb4be45f16927912343509e81ec9722a190a1d4a805a50fe3b8adccf",
    ),
    Projection(
        "08_scoreboard_panel.png",
        "bb45518330ea20399d0b73f6776c72ac5da6f3ebdf1e2c84dc6643430ad9aca3",
        "03_scoreboard.jpg",
        (430, 130, 1640, 1020),
        "98d06d1661745761ab94d90628eedbf67668e5e77a74863ce5c46c27753fb790",
    ),
    Projection(
        "09_jingcha_mandate_event.png",
        "9f7bb4ee382677c035d6256da3d5c113959e2026b3a1ef59fce33d22ae53cb06",
        "04_jingcha_mandate.jpg",
        (420, 280, 1610, 875),
        "77dc6bd7da79ed79448c849f6597298291cb33bf73653517604e76417071ea64",
    ),
    Projection(
        "09_jingcha_activity_detail.png",
        "c34f54b69898f8bf5a630226b86dfb185cf3acc2052faa0183d7f771e10123c1",
        "05_free_jingcha_activity.jpg",
        (720, 120, 2000, 1200),
        "784b2f2b3cb3c763990ea4133064600a2fb66e5602ef3dfa6c7429fc74b0f9d4",
    ),
    Projection(
        "10_superior_result.png",
        "93ecfad072711b6caa1759fefa267f492897e36b8ce14905230541a7f7eab46f",
        "06_superior_325_result.jpg",
        (430, 275, 1605, 885),
        "58ac67ad919a93f279c0d21de53e1244d9e83b58071a910260c8c60b59f28bd1",
    ),
)


# These recipes deliberately carry no hashes until the final promo-capture run
# exists.  ``--create-policy-lock`` accepts only the same fully indexed GREEN
# capture bundle used by the promo release projector, then freezes the missing
# source/output hashes in an auditable JSON lock.  This prevents a fixture,
# failed take, or attractive mock-up from quietly becoming Workshop evidence.
POLICY_CARD_RECIPES = (
    PolicyCardRecipe(
        1,
        "12_policy_001_event.png",
        "07_policy_001_kpi_evidence.jpg",
        (420, 280, 1610, 875),
    ),
    PolicyCardRecipe(
        361,
        "12_policy_361_event.png",
        "08_policy_361_charter.jpg",
        (420, 280, 1610, 875),
    ),
)


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdefABCDEF" for character in value)
    )


def _projection_from_lock_row(
    row: object, recipe: PolicyCardRecipe
) -> Projection:
    if not isinstance(row, dict):
        raise ValueError("policy-card lock projection must be an object")
    expected = {
        "mechanism_id": recipe.mechanism_id,
        "source": recipe.source,
        "output": recipe.output,
        "crop": list(recipe.crop),
    }
    for key, value in expected.items():
        if row.get(key) != value:
            raise ValueError(
                f"policy-card lock {key} mismatch for #{recipe.mechanism_id:03d}: "
                f"{row.get(key)!r} != {value!r}"
            )
    for key in ("source_sha256", "output_sha256"):
        if not _is_sha256(row.get(key)):
            raise ValueError(
                f"policy-card lock has invalid {key} for #{recipe.mechanism_id:03d}"
            )
    expected_dimensions = [
        recipe.crop[2] - recipe.crop[0],
        recipe.crop[3] - recipe.crop[1],
    ]
    if row.get("dimensions") != expected_dimensions:
        raise ValueError(
            f"policy-card lock dimensions mismatch for #{recipe.mechanism_id:03d}"
        )
    byte_count = row.get("bytes")
    if (
        isinstance(byte_count, bool)
        or not isinstance(byte_count, int)
        or byte_count <= 0
        or byte_count >= MAX_BYTES
    ):
        raise ValueError(
            f"policy-card lock has invalid byte count for #{recipe.mechanism_id:03d}"
        )
    return Projection(
        source=recipe.source,
        source_sha256=str(row["source_sha256"]).lower(),
        output=recipe.output,
        crop=recipe.crop,
        output_sha256=str(row["output_sha256"]).lower(),
    )


def _green_capture_bundle(artifacts: Path) -> dict[str, Any]:
    try:
        import prepare_promo_release_manifest as promo_release
    except ImportError as exc:
        raise ValueError(f"could not load GREEN-capture validator: {exc}") from exc
    try:
        return promo_release._capture_bundle(artifacts.resolve())
    except promo_release.PrepareError as exc:
        raise ValueError(f"policy-card source is not a valid GREEN capture: {exc}") from exc


def load_policy_lock(
    path: Path, *, artifact_root: Path | None = None
) -> tuple[Projection, ...]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except OSError as exc:
        raise ValueError(f"could not read policy-card lock: {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid policy-card lock JSON: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("policy-card lock root must be an object")
    if payload.get("format_version") != 1 or payload.get("result") != "GREEN":
        raise ValueError("policy-card lock must be format version 1 and GREEN")
    if payload.get("policy_ids") != [recipe.mechanism_id for recipe in POLICY_CARD_RECIPES]:
        raise ValueError("policy-card lock must contain exactly #001 and #361 in order")
    for key, label in (
        ("report_sha256", "report"),
        ("evidence_index_sha256", "evidence-index"),
        ("timeline_sha256", "timeline"),
        ("raw_capture_sha256", "raw-capture"),
    ):
        if not _is_sha256(payload.get(key)):
            raise ValueError(f"policy-card lock lacks a valid {label} SHA-256")
    locked_root = payload.get("artifact_root")
    if not isinstance(locked_root, str) or not Path(locked_root).is_absolute():
        raise ValueError("policy-card lock artifact_root must be absolute")
    if artifact_root is not None and Path(locked_root).resolve() != artifact_root.resolve():
        raise ValueError(
            "policy-card lock belongs to a different capture artifact: "
            f"{Path(locked_root).resolve()} != {artifact_root.resolve()}"
        )
    if artifact_root is not None:
        bundle = _green_capture_bundle(artifact_root)
        for key, bundle_key in (
            ("report_sha256", "report_path"),
            ("evidence_index_sha256", "index_path"),
            ("timeline_sha256", "timeline_path"),
            ("raw_capture_sha256", "raw_path"),
        ):
            if str(payload[key]).lower() != sha256(bundle[bundle_key]):
                raise ValueError(
                    f"policy-card lock {key} no longer matches its capture artifact"
                )
    rows = payload.get("projections")
    if not isinstance(rows, list) or len(rows) != len(POLICY_CARD_RECIPES):
        raise ValueError("policy-card lock must contain exactly two projections")
    return tuple(
        _projection_from_lock_row(row, recipe)
        for row, recipe in zip(rows, POLICY_CARD_RECIPES, strict=True)
    )


def create_policy_lock(artifacts: Path, output: Path) -> dict[str, Any]:
    """Freeze #001/#361 only from a complete GREEN promo capture bundle."""
    bundle = _green_capture_bundle(artifacts)

    rows: list[dict[str, object]] = []
    for recipe in POLICY_CARD_RECIPES:
        source = bundle["policy_paths"][recipe.mechanism_id]
        data, dimensions = jpeg_bytes(source, recipe.crop)
        if len(data) >= MAX_BYTES:
            raise ValueError(
                f"Workshop image exceeds 2 MB: {recipe.output} ({len(data)} bytes)"
            )
        rows.append(
            {
                "mechanism_id": recipe.mechanism_id,
                "source": recipe.source,
                "source_sha256": sha256(source),
                "output": recipe.output,
                "crop": list(recipe.crop),
                "dimensions": list(dimensions),
                "bytes": len(data),
                "output_sha256": sha256(data),
            }
        )
    payload: dict[str, Any] = {
        "format_version": 1,
        "result": "GREEN",
        "artifact_root": str(artifacts.resolve()),
        "report_sha256": sha256(bundle["report_path"]),
        "evidence_index_sha256": sha256(bundle["index_path"]),
        "timeline_sha256": sha256(bundle["timeline_path"]),
        "raw_capture_sha256": sha256(bundle["raw_path"]),
        "policy_ids": [recipe.mechanism_id for recipe in POLICY_CARD_RECIPES],
        "projections": rows,
    }
    encoded = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if output.exists():
        if output.read_bytes() != encoded:
            raise ValueError(f"refusing to overwrite existing policy-card lock: {output}")
        return payload
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(encoded)
    return payload


def selected_projections(
    policy_lock: Path | None,
    *,
    artifact_root: Path | None = None,
    policy_cards_only: bool = False,
) -> tuple[Projection, ...]:
    if policy_lock is None:
        if policy_cards_only:
            raise ValueError("--policy-cards-only requires a policy-card lock")
        return PROJECTIONS
    policy_projections = load_policy_lock(policy_lock, artifact_root=artifact_root)
    if policy_cards_only:
        return policy_projections
    return PROJECTIONS + policy_projections


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


def render(
    artifacts: Path,
    output: Path,
    *,
    check: bool,
    projections: Sequence[Projection] = PROJECTIONS,
) -> list[dict[str, object]]:
    cell = artifacts / "cell" if (artifacts / "cell").is_dir() else artifacts
    expected_outputs = {projection.output for projection in projections}
    existing = {path.name for path in output.glob("*.jpg")} if output.is_dir() else set()
    unexpected = sorted(existing - expected_outputs)
    if unexpected:
        raise ValueError(f"unexpected Workshop JPEGs: {unexpected}")
    if not check:
        output.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, object]] = []
    stale: list[str] = []
    for projection in projections:
        source = cell / projection.source
        if not source.is_file():
            raise ValueError(f"acceptance capture missing: {source}")
        actual_source_hash = sha256(source)
        if actual_source_hash != projection.source_sha256:
            raise ValueError(
                f"source hash mismatch for {source.name}: {actual_source_hash}"
            )
        data, dimensions = jpeg_bytes(source, projection.crop)
        rendered_hash = sha256(data)
        if rendered_hash != projection.output_sha256:
            raise ValueError(
                f"renderer output hash changed for {projection.output}: {rendered_hash}"
            )
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
                "sha256": rendered_hash,
            }
        )
    if stale:
        raise ValueError("stale Workshop media: " + ", ".join(stale))
    return records


def verify_tracked_outputs(
    output: Path, *, projections: Sequence[Projection] = PROJECTIONS
) -> list[dict[str, object]]:
    """Verify committed Workshop media when the external raw artifact is unavailable."""
    expected_outputs = {projection.output for projection in projections}
    existing = {path.name for path in output.iterdir()} if output.is_dir() else set()
    if existing != expected_outputs:
        missing = sorted(expected_outputs - existing)
        unexpected = sorted(existing - expected_outputs)
        raise ValueError(
            f"tracked Workshop media inventory mismatch; missing={missing}, "
            f"unexpected={unexpected}"
        )

    records: list[dict[str, object]] = []
    for projection in projections:
        target = output / projection.output
        data = target.read_bytes()
        actual_hash = sha256(data)
        if actual_hash != projection.output_sha256:
            raise ValueError(
                f"tracked Workshop media hash mismatch for {projection.output}: "
                f"{actual_hash}"
            )
        if len(data) >= MAX_BYTES:
            raise ValueError(
                f"Workshop image exceeds 2 MB: {projection.output} ({len(data)} bytes)"
            )
        expected_dimensions = (
            projection.crop[2] - projection.crop[0],
            projection.crop[3] - projection.crop[1],
        )
        with Image.open(target) as image:
            image.load()
            if image.format != "JPEG" or image.size != expected_dimensions:
                raise ValueError(
                    f"tracked Workshop media format/dimensions mismatch for "
                    f"{projection.output}: {image.format} {image.size}"
                )
        records.append(
            {
                "source": projection.source,
                "source_sha256": projection.source_sha256,
                "output": projection.output,
                "crop": projection.crop,
                "dimensions": expected_dimensions,
                "bytes": len(data),
                "sha256": actual_hash,
            }
        )
    return records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, default=DEFAULT_ARTIFACTS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--policy-lock",
        type=Path,
        help=(
            "include pinned #001/#361 projections from this GREEN-capture lock; "
            f"the release default is {DEFAULT_POLICY_LOCK.relative_to(MOD_ROOT)}"
        ),
    )
    parser.add_argument(
        "--policy-cards-only",
        action="store_true",
        help=(
            "render/check only release slots 7-8; requires --policy-lock or the "
            "committed default lock"
        ),
    )
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true")
    modes.add_argument(
        "--check-tracked",
        action="store_true",
        help="verify committed JPEG inventory/hashes without the external raw artifact",
    )
    modes.add_argument(
        "--create-policy-lock",
        type=Path,
        metavar="PATH",
        help=(
            "validate --artifacts as one complete GREEN promo capture and write "
            "an append-only #001/#361 projection lock"
        ),
    )
    arguments = parser.parse_args(argv)
    try:
        artifacts = arguments.artifacts.resolve()
        if arguments.create_policy_lock:
            payload = create_policy_lock(
                artifacts, arguments.create_policy_lock.resolve()
            )
            for row in payload["projections"]:
                print(
                    f"{row['output']}: {row['dimensions'][0]}x{row['dimensions'][1]}, "
                    f"{row['bytes']} bytes, SHA-256 {row['output_sha256']}"
                )
            print(
                "GREEN: policy-card lock created from one indexed GREEN capture; "
                "no Workshop JPEGs were written"
            )
            return 0

        policy_lock = arguments.policy_lock
        if policy_lock is None and DEFAULT_POLICY_LOCK.is_file():
            policy_lock = DEFAULT_POLICY_LOCK
        projections = selected_projections(
            policy_lock.resolve() if policy_lock else None,
            artifact_root=None if arguments.check_tracked else artifacts,
            policy_cards_only=arguments.policy_cards_only,
        )
        if arguments.check_tracked:
            records = verify_tracked_outputs(
                arguments.output.resolve(), projections=projections
            )
        else:
            records = render(
                artifacts,
                arguments.output.resolve(),
                check=arguments.check,
                projections=projections,
            )
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
