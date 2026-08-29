#!/usr/bin/env python3
"""Generate full-screen promo visual-audit evidence from a release manifest.

This producer complements :mod:`audit_promo_visuals`.  It consumes the
immutable manifest emitted by ``prepare_promo_release_manifest.py``, extracts
every captured video chapter at a deterministic interval (including exact clip
endpoints), runs full-screen RapidOCR, and writes a hash-bound audit spec.

The generated spec is deliberately *not signed*.  Its manual sign-off is an
explicit PENDING template with false attestations.  A reviewer must watch every
captured chapter, copy the pending spec to a separately preserved signed spec,
and fill that block before ``audit_promo_visuals.py audit`` can return GREEN.
"""

from __future__ import annotations

import argparse
import io
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Sequence

import numpy as np
from PIL import Image


TOOLS_DIRECTORY = Path(__file__).resolve().parent
if str(TOOLS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIRECTORY))

import audit_promo_visuals as audit  # noqa: E402


SCHEMA_VERSION = 1
RUN_KIND = "zg361_promo_visual_evidence_run"
DEFAULT_SPEC_NAME = "promo-visual-audit-spec.PENDING.json"
DEFAULT_RUN_NAME = "promo-visual-evidence-run.json"
OCR_MIN_SCORE = 0.45
PENDING_REVIEW_TIME = "1970-01-01T00:00:00+00:00"
MANAGER_CLEAN_SPANS = {
    "calibration",
    "managed_scoreboard",
    "policy_cockpit",
    "jingcha_mandate",
    "free_jingcha_planner",
}
REVIEWED_OFFICIAL_CLEAN_SPANS = {
    "superior_assigned_325",
    "received_scoreboard_with_325",
    "policy_card_001",
    "policy_card_007",
    "policy_card_020",
    "policy_card_022",
    "policy_card_026",
    "policy_card_361",
}


class PrepareVisualAuditError(RuntimeError):
    """The release manifest cannot produce trustworthy visual evidence."""


def _read_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except OSError as exc:
        raise PrepareVisualAuditError(f"could not read {label}: {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise PrepareVisualAuditError(f"invalid JSON in {label}: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise PrepareVisualAuditError(f"{label} root must be an object: {path}")
    return payload


def _serialized(payload: object) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode(
        "utf-8"
    )


def _write_new_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write(_serialized(payload))
    except FileExistsError as exc:
        raise PrepareVisualAuditError(
            f"refusing to overwrite preserved visual-audit output: {path}"
        ) from exc


def _write_new_png(path: Path, image: Image.Image) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = io.BytesIO()
    image.save(encoded, format="PNG", compress_level=6)
    try:
        with path.open("xb") as handle:
            handle.write(encoded.getvalue())
    except FileExistsError as exc:
        raise PrepareVisualAuditError(
            f"refusing to overwrite preserved visual-audit frame: {path}"
        ) from exc


def _file_record(path: Path, label: str) -> dict[str, Any]:
    path = path.expanduser().resolve()
    if not path.is_file():
        raise PrepareVisualAuditError(f"required {label} does not exist: {path}")
    return {
        "path": str(path),
        "label": label,
        "bytes": path.stat().st_size,
        "sha256": audit.sha256_file(path),
    }


def sample_timestamps(start: float, end: float, interval: float) -> tuple[float, ...]:
    """Return deterministic six-decimal samples including both clip endpoints."""

    values = (start, end, interval)
    if any(not math.isfinite(value) for value in values):
        raise PrepareVisualAuditError("clip sampling values must be finite")
    if start < 0 or end <= start:
        raise PrepareVisualAuditError(
            f"invalid clip interval for sampling: {start!r}..{end!r}"
        )
    if interval <= 0 or interval > audit.MAX_SAMPLE_INTERVAL_SECONDS:
        raise PrepareVisualAuditError(
            "sampling interval must be greater than zero and no more than "
            f"{audit.MAX_SAMPLE_INTERVAL_SECONDS:.1f} seconds"
        )

    rounded_start = round(start, 6)
    rounded_end = round(end, 6)
    if rounded_end <= rounded_start:
        raise PrepareVisualAuditError(
            "clip interval collapses at the audit's six-decimal ffmpeg precision: "
            f"{start!r}..{end!r}"
        )
    result = [rounded_start]
    step = 1
    while True:
        candidate = round(start + step * interval, 6)
        if candidate >= rounded_end - 1e-9:
            break
        if candidate > result[-1]:
            result.append(candidate)
        step += 1
    if result[-1] != rounded_end:
        result.append(rounded_end)
    for left, right in zip(result, result[1:]):
        if right - left > interval + 1e-6:
            raise PrepareVisualAuditError(
                f"internal sampling gap {left:.6f}..{right:.6f} exceeds "
                f"{interval:.6f} seconds"
            )
    return tuple(result)


def _subject_rows(
    provenance: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    rows = provenance["subjects"]
    subjects: list[dict[str, Any]] = []
    role_map: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        # The projected manifest intentionally has no producer-selected runtime
        # identity.  The stable history key is therefore also the audit subject
        # ID, and every other field is copied from manifest provenance.
        subject_id = row["history_id"]
        subject = {
            "subject_id": subject_id,
            "history_id": row["history_id"],
            "display_name": row["display_name"],
            "roles": list(row["roles"]),
            "origin": row["origin"],
            "temporary_or_generated": row["temporary_or_generated"],
            "history_source": dict(row["history_source"]),
        }
        subjects.append(subject)
        for role in row["roles"]:
            role_map[role].append(subject_id)
    return subjects, {
        role: sorted(subject_ids) for role, subject_ids in sorted(role_map.items())
    }


def _chapter_subject_map(
    manifest: dict[str, Any], role_map: dict[str, list[str]]
) -> dict[str, list[str]]:
    """Bind each captured chapter to the role used by its clean capture span."""
    result: dict[str, list[str]] = {}
    rows = manifest.get("chapters")
    if not isinstance(rows, list):
        raise PrepareVisualAuditError("release manifest chapters must be an array")
    for row in rows:
        if not isinstance(row, dict) or row.get("material_status") != "captured":
            continue
        chapter_id = row.get("id")
        capture = row.get("capture")
        if not isinstance(chapter_id, str) or not isinstance(capture, dict):
            raise PrepareVisualAuditError(
                "every captured release chapter must retain its clean-span capture record"
            )
        span_id = capture.get("clean_span_id")
        if span_id in MANAGER_CLEAN_SPANS:
            role = "manager"
        elif span_id in REVIEWED_OFFICIAL_CLEAN_SPANS:
            role = "reviewed_official"
        else:
            raise PrepareVisualAuditError(
                f"captured chapter {chapter_id!r} has unmapped clean span {span_id!r}"
            )
        subject_ids = role_map.get(role)
        if not isinstance(subject_ids, list) or len(subject_ids) != 1:
            raise PrepareVisualAuditError(
                f"real-character provenance must bind exactly one {role!r} subject"
            )
        result[chapter_id] = list(subject_ids)
    return result


def _ocr_engine() -> Callable[[np.ndarray], Any]:
    try:
        from rapidocr_onnxruntime import RapidOCR
    except Exception as exc:  # pragma: no cover - exercised by release environment
        raise PrepareVisualAuditError(
            "RapidOCR is required; run this tool with tools/.venv"
        ) from exc
    try:
        return RapidOCR()
    except Exception as exc:  # pragma: no cover - model/runtime installation failure
        raise PrepareVisualAuditError(f"could not initialize RapidOCR: {exc}") from exc


def _ocr_payload(
    image: Image.Image,
    image_path: Path,
    engine: Callable[[np.ndarray], Any],
) -> dict[str, Any]:
    try:
        result, _elapsed = engine(np.asarray(image.convert("RGB")))
    except Exception as exc:
        raise PrepareVisualAuditError(
            f"RapidOCR failed for full-screen frame {image_path}: {exc}"
        ) from exc
    items: list[dict[str, Any]] = []
    for raw in result or []:
        if not isinstance(raw, (list, tuple)) or len(raw) < 3:
            continue
        box, text, score = raw[:3]
        try:
            confidence = float(score)
            points = [[float(point[0]), float(point[1])] for point in box]
        except (TypeError, ValueError, IndexError):
            continue
        value = str(text).strip()
        if not value or confidence < OCR_MIN_SCORE or not points:
            continue
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        items.append(
            {
                "text": value,
                "score": round(confidence, 6),
                "bbox": [min(xs), min(ys), max(xs), max(ys)],
                "points": points,
            }
        )
    if not items:
        raise PrepareVisualAuditError(
            "RapidOCR found no full-screen text; preserve this partial run and "
            f"inspect the frame before retrying in a new output directory: {image_path}"
        )
    return {
        "schema_version": 1,
        "engine": "rapidocr_onnxruntime",
        "minimum_score": OCR_MIN_SCORE,
        "image_sha256": audit.sha256_file(image_path),
        "items": items,
    }


def _timestamp_key(timestamp: float) -> str:
    micros = int(round(timestamp * 1_000_000))
    return f"t{micros:012d}"


def _captured_geometry(
    captured: dict[str, dict[str, Any]], ffprobe: str
) -> tuple[int, int]:
    geometries: set[tuple[int, int]] = set()
    probed: set[str] = set()
    for chapter in captured.values():
        source = chapter["source"]
        source_path = Path(source["path"])
        if chapter["type"] == "video_clip":
            if source["sha256"] in probed:
                continue
            probe = audit._probe_video(source_path, ffprobe)
            geometries.add((probe["width"], probe["height"]))
            probed.add(source["sha256"])
        else:
            try:
                with Image.open(source_path) as image:
                    if image.format != "PNG":
                        raise PrepareVisualAuditError(
                            f"captured still must be PNG for the visual audit: {source_path}"
                        )
                    geometries.add(image.size)
            except PrepareVisualAuditError:
                raise
            except Exception as exc:
                raise PrepareVisualAuditError(
                    f"could not decode captured still {source_path}: {exc}"
                ) from exc
    if len(geometries) != 1:
        raise PrepareVisualAuditError(
            "all captured release visuals must share one full-screen geometry; "
            f"found {sorted(geometries)!r}"
        )
    return next(iter(geometries))


def generate_pending_spec(
    *,
    release_manifest: Path,
    output_directory: Path,
    sampling_interval_seconds: float = 1.0,
    engine: Callable[[np.ndarray], Any] | None = None,
) -> tuple[Path, Path, dict[str, Any]]:
    """Write extracted evidence plus a deliberately PENDING audit spec."""

    release_manifest = release_manifest.expanduser().resolve()
    output_directory = output_directory.expanduser().resolve()
    if not math.isfinite(sampling_interval_seconds):
        raise PrepareVisualAuditError("sampling interval must be finite")
    if (
        sampling_interval_seconds <= 0
        or sampling_interval_seconds > audit.MAX_SAMPLE_INTERVAL_SECONDS
    ):
        raise PrepareVisualAuditError(
            "sampling interval must be greater than zero and no more than "
            f"{audit.MAX_SAMPLE_INTERVAL_SECONDS:.1f} seconds"
        )
    spec_path = output_directory / DEFAULT_SPEC_NAME
    run_path = output_directory / DEFAULT_RUN_NAME
    evidence_root = output_directory / "evidence"
    for target in (spec_path, run_path, evidence_root):
        if target.exists():
            raise PrepareVisualAuditError(
                "refusing to overwrite preserved visual-audit output; choose a new "
                f"--output-dir: {target}"
            )

    manifest = _read_object(release_manifest, "captured release manifest")
    try:
        captured, _chapter_rows = audit._manifest_chapters(manifest)
        _manifest_subjects, character_provenance = (
            audit._manifest_real_character_provenance(manifest)
        )
    except audit.AuditError as exc:
        raise PrepareVisualAuditError(str(exc)) from exc

    ffprobe = audit._media_program("ffprobe")
    ffmpeg = audit._media_program("ffmpeg")
    width, height = _captured_geometry(captured, ffprobe)
    subjects, role_map = _subject_rows(character_provenance)
    chapter_subjects = _chapter_subject_map(manifest, role_map)
    ocr = engine or _ocr_engine()

    source_order: dict[str, int] = {}
    source_paths: dict[str, Path] = {}
    video_groups: dict[tuple[str, float], set[str]] = defaultdict(set)
    still_groups: dict[str, set[str]] = defaultdict(set)
    chapter_schedules: dict[str, list[float] | None] = {}
    for chapter in captured.values():
        source = chapter["source"]
        source_sha = source["sha256"]
        if source_sha not in source_order:
            source_order[source_sha] = len(source_order) + 1
            source_paths[source_sha] = Path(source["path"])
        if chapter["type"] == "video_clip":
            schedule = sample_timestamps(
                chapter["start_seconds"],
                chapter["end_seconds"],
                sampling_interval_seconds,
            )
            chapter_schedules[chapter["chapter_id"]] = list(schedule)
            for timestamp in schedule:
                video_groups[(source_sha, timestamp)].add(chapter["chapter_id"])
        else:
            chapter_schedules[chapter["chapter_id"]] = None
            still_groups[source_sha].add(chapter["chapter_id"])

    evidence: list[dict[str, Any]] = []
    generated_files: list[Path] = []
    for (source_sha, timestamp), chapter_ids in sorted(
        video_groups.items(), key=lambda row: (source_order[row[0][0]], row[0][1])
    ):
        source_number = source_order[source_sha]
        evidence_id = f"video-{source_number:03d}-{_timestamp_key(timestamp)}"
        image_path = evidence_root / "video" / f"{evidence_id}.png"
        ocr_path = evidence_root / "video" / f"{evidence_id}.ocr.json"
        try:
            rgb = audit._extract_video_rgb(
                source_paths[source_sha], timestamp, width, height, ffmpeg
            )
        except audit.AuditError as exc:
            raise PrepareVisualAuditError(str(exc)) from exc
        image = Image.frombytes("RGB", (width, height), rgb)
        _write_new_png(image_path, image)
        generated_files.append(image_path)
        payload = _ocr_payload(image, image_path, ocr)
        _write_new_json(ocr_path, payload)
        generated_files.append(ocr_path)
        evidence.append(
            {
                "evidence_id": evidence_id,
                "chapter_ids": sorted(chapter_ids),
                "subject_ids": sorted(
                    {
                        subject_id
                        for chapter_id in chapter_ids
                        for subject_id in chapter_subjects[chapter_id]
                    }
                ),
                "source_sha256": source_sha,
                "timestamp_seconds": timestamp,
                "image": _file_record(image_path, "full-screen ffmpeg RGB24 frame"),
                "ocr": _file_record(ocr_path, "full-screen RapidOCR JSON"),
                "ocr_region": [0, 0, width, height],
            }
        )

    for source_sha, chapter_ids in sorted(
        still_groups.items(), key=lambda row: source_order[row[0]]
    ):
        source_number = source_order[source_sha]
        image_path = source_paths[source_sha]
        evidence_id = f"still-{source_number:03d}"
        ocr_path = evidence_root / "still" / f"{evidence_id}.ocr.json"
        try:
            with Image.open(image_path) as source_image:
                image = source_image.convert("RGB")
        except Exception as exc:
            raise PrepareVisualAuditError(
                f"could not decode captured still {image_path}: {exc}"
            ) from exc
        payload = _ocr_payload(image, image_path, ocr)
        _write_new_json(ocr_path, payload)
        generated_files.append(ocr_path)
        evidence.append(
            {
                "evidence_id": evidence_id,
                "chapter_ids": sorted(chapter_ids),
                "subject_ids": sorted(
                    {
                        subject_id
                        for chapter_id in chapter_ids
                        for subject_id in chapter_subjects[chapter_id]
                    }
                ),
                "source_sha256": source_sha,
                "image": _file_record(image_path, "exact captured manifest still"),
                "ocr": _file_record(ocr_path, "full-screen RapidOCR JSON"),
                "ocr_region": [0, 0, width, height],
            }
        )

    captured_chapter_ids = list(captured)
    pending_signoff = {
        "status": "PENDING",
        "reviewer": "PENDING_NOT_REVIEWED",
        "reviewed_at_utc": PENDING_REVIEW_TIME,
        "manifest_sha256": audit.sha256_file(release_manifest),
        "reviewed_chapter_ids": [],
        "attestations": {
            key: False for key in audit.REQUIRED_ATTESTATIONS
        },
        "template_notice": (
            "NOT A SIGN-OFF. Copy this spec to a new signed file only after a "
            "human reviewer watches every captured chapter at 1x and checks every still."
        ),
    }
    spec = {
        "schema_version": audit.SCHEMA_VERSION,
        "kind": audit.SPEC_KIND,
        "release_manifest": _file_record(
            release_manifest, "captured promo release manifest"
        ),
        "frame_geometry": {"width": width, "height": height},
        "sampling_interval_seconds": sampling_interval_seconds,
        "bookmark": dict(character_provenance["bookmark"]),
        "historical_characters": subjects,
        "subject_role_map": role_map,
        "additional_forbidden_tokens": [],
        "evidence": evidence,
        "manual_signoff": pending_signoff,
        "generation": {
            "producer": "mod_zhongguo_style/tools/prepare_promo_visual_audit.py",
            "evidence_status": "READY",
            "manual_review_status": "PENDING",
            "captured_chapter_ids": captured_chapter_ids,
            "chapter_sample_timestamps_seconds": chapter_schedules,
            "endpoint_policy": "exact_start_and_end_included",
            "video_decode": "ffmpeg full-frame rgb24; same extractor as audit consumer",
            "ocr": "RapidOCR full-screen; no crop, mask or redaction",
        },
    }
    _write_new_json(spec_path, spec)
    generated_files.append(spec_path)

    run = {
        "schema_version": SCHEMA_VERSION,
        "kind": RUN_KIND,
        "result": "EVIDENCE_READY_MANUAL_REVIEW_PENDING",
        "release_manifest": _file_record(
            release_manifest, "captured promo release manifest"
        ),
        "pending_spec": _file_record(spec_path, "unsigned PENDING visual-audit spec"),
        "output_directory": str(output_directory),
        "captured_chapter_ids": captured_chapter_ids,
        "video_frame_count": len(video_groups),
        "still_evidence_count": len(still_groups),
        "evidence_count": len(evidence),
        "manual_review_required": True,
        "generated_files": [
            _file_record(path, "preserved visual-audit process output")
            for path in generated_files
        ],
    }
    _write_new_json(run_path, run)
    return spec_path, run_path, run


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--release-manifest", type=Path, required=True)
    result.add_argument("--output-dir", type=Path, required=True)
    result.add_argument(
        "--sampling-interval-seconds",
        type=float,
        default=1.0,
        help="Full-screen video sample interval; must be >0 and <=1.0 (default: 1.0)",
    )
    return result


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    try:
        spec_path, run_path, run = generate_pending_spec(
            release_manifest=arguments.release_manifest,
            output_directory=arguments.output_dir,
            sampling_interval_seconds=arguments.sampling_interval_seconds,
        )
    except (PrepareVisualAuditError, audit.AuditError) as exc:
        print(f"RED: {exc}", file=sys.stderr)
        return 2
    print(
        "PENDING: visual evidence generated; manual full-clip review is still "
        f"required: chapters={len(run['captured_chapter_ids'])}; "
        f"evidence={run['evidence_count']}; spec={spec_path}; run={run_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
