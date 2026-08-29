#!/usr/bin/env python3
"""Audit final ZhongGuo promo visuals for historical subjects and test-only UI.

The CK3 acceptance runner is allowed to expose fixture controls while proving
gameplay.  A promotional cut is not.  This offline gate consumes an immutable
release manifest plus full-screen PNG/OCR evidence selected from its exact
visual sources.  It verifies declared hashes, historical-character provenance,
continuous sampling coverage, forbidden fixture text, and a manual sign-off.

The audit report is append-only and reproducible: ``verify`` re-opens the bound
spec and every referenced file, rebuilds the deterministic evaluation, and
optionally checks the report SHA-256 recorded by a later release manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from PIL import Image

import promo_real_character_contract as real_characters


SCHEMA_VERSION = 1
SPEC_KIND = "zg361_promo_visual_audit_spec"
REPORT_KIND = "zg361_promo_visual_audit_report"
MAX_SAMPLE_INTERVAL_SECONDS = 1.0
DEFAULT_FORBIDDEN_TOKENS = (
    "决议和大型工程",
    "361制实机验收",
    "开始361制实机验收",
    "验收上司给我的绩效",
    "验收免费京察规划器",
    "验收规划器",
    "演示政策卡",
    "演示触发器",
    "切换至宋帝并开考",
    "切换受考",
    "发出京察召集令",
    "打开此卡",
    "ZhongGuo 361 live acceptance",
    "Verify My Superior's Rating",
    "Verify the Free Jingcha Planner",
    "Promo Policy Card",
    "Switch to Song and begin review",
    "Open this card",
    "ZGA",
    "zga_",
    "zga.",
)
REQUIRED_ATTESTATIONS = (
    "historical_characters_only",
    "fixture_test_ui_absent",
    "full_clip_reviewed",
    "no_crop_mask_or_redaction",
)
IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9_.:-]+$")
SHA256_RE = re.compile(r"^[0-9A-Fa-f]{64}$")


class AuditError(RuntimeError):
    """The audit spec or one of its immutable inputs is invalid."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest().upper()


def _read_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except OSError as exc:
        raise AuditError(f"could not read {label}: {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise AuditError(f"invalid JSON in {label}: {path}: {exc}") from exc


def _actual_file_record(path: Path, label: str) -> dict[str, Any]:
    path = path.expanduser().resolve()
    if not path.is_file():
        raise AuditError(f"required {label} does not exist: {path}")
    return {
        "path": str(path),
        "label": label,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def _validate_file_record(raw: Any, context: str) -> tuple[Path, dict[str, Any]]:
    if not isinstance(raw, dict):
        raise AuditError(f"{context} must be an object with path/bytes/sha256")
    raw_path = raw.get("path")
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise AuditError(f"{context}.path must be a non-empty absolute path")
    expanded = Path(os.path.expandvars(os.path.expanduser(raw_path)))
    if not expanded.is_absolute():
        raise AuditError(f"{context}.path must be absolute: {raw_path!r}")
    path = expanded.resolve()
    if not path.is_file():
        raise AuditError(f"{context}.path does not exist: {path}")
    expected_bytes = raw.get("bytes")
    if (
        isinstance(expected_bytes, bool)
        or not isinstance(expected_bytes, int)
        or expected_bytes < 0
    ):
        raise AuditError(f"{context}.bytes must be a non-negative integer")
    expected_sha = raw.get("sha256")
    if not isinstance(expected_sha, str) or SHA256_RE.fullmatch(expected_sha) is None:
        raise AuditError(f"{context}.sha256 must be 64 hexadecimal characters")
    actual_bytes = path.stat().st_size
    actual_sha = sha256_file(path)
    if expected_bytes != actual_bytes:
        raise AuditError(
            f"{context} byte count mismatch: {expected_bytes} != {actual_bytes}"
        )
    if expected_sha.upper() != actual_sha:
        raise AuditError(f"{context} SHA-256 mismatch")
    label = raw.get("label")
    if label is not None and (not isinstance(label, str) or not label.strip()):
        raise AuditError(f"{context}.label must be a non-empty string when present")
    normalized = {
        "path": str(path),
        "bytes": actual_bytes,
        "sha256": actual_sha,
    }
    if isinstance(label, str):
        normalized["label"] = label
    return path, normalized


def _nonempty_string(raw: Any, context: str) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise AuditError(f"{context} must be a non-empty string")
    return raw.strip()


def _identifier(raw: Any, context: str) -> str:
    value = _nonempty_string(raw, context)
    if IDENTIFIER_RE.fullmatch(value) is None:
        raise AuditError(f"{context} contains unsupported characters: {value!r}")
    return value


def _string_list(raw: Any, context: str, *, identifiers: bool = False) -> list[str]:
    if not isinstance(raw, list) or not raw:
        raise AuditError(f"{context} must be a non-empty array")
    values = [
        _identifier(value, f"{context}[{index}]")
        if identifiers
        else _nonempty_string(value, f"{context}[{index}]")
        for index, value in enumerate(raw)
    ]
    if len(values) != len(set(values)):
        raise AuditError(f"{context} contains duplicates")
    return values


def _number(raw: Any, context: str) -> float:
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        raise AuditError(f"{context} must be a finite number")
    value = float(raw)
    if not math.isfinite(value):
        raise AuditError(f"{context} must be a finite number")
    return value


def _media_program(name: str) -> str:
    executable = shutil.which(name)
    if executable is None:
        raise AuditError(
            f"{name} is required to verify bound promotional video evidence"
        )
    return executable


def _run_media(command: Sequence[str], context: str) -> bytes:
    try:
        completed = subprocess.run(
            list(command),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except OSError as exc:
        raise AuditError(f"could not run {context}: {exc}") from exc
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        if len(detail) > 1200:
            detail = detail[-1200:]
        suffix = f": {detail}" if detail else ""
        raise AuditError(
            f"{context} failed with exit code {completed.returncode}{suffix}"
        )
    return completed.stdout


def _probe_duration(raw: Any, context: str) -> float | None:
    if raw is None or isinstance(raw, bool):
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(value) or value <= 0:
        return None
    return value


def _probe_video(path: Path, ffprobe: str) -> dict[str, Any]:
    output = _run_media(
        (
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=codec_type,codec_name,width,height,duration:format=duration",
            "-of",
            "json",
            str(path),
        ),
        f"ffprobe for video source {path}",
    )
    try:
        payload = json.loads(output.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuditError(f"ffprobe returned invalid JSON for {path}: {exc}") from exc
    streams = payload.get("streams") if isinstance(payload, dict) else None
    if not isinstance(streams, list) or len(streams) != 1:
        raise AuditError(f"ffprobe found no primary video stream in {path}")
    stream = streams[0]
    if not isinstance(stream, dict) or stream.get("codec_type") != "video":
        raise AuditError(f"ffprobe did not identify a real video stream in {path}")
    width = stream.get("width")
    height = stream.get("height")
    if (
        isinstance(width, bool)
        or not isinstance(width, int)
        or width <= 0
        or isinstance(height, bool)
        or not isinstance(height, int)
        or height <= 0
    ):
        raise AuditError(f"ffprobe returned invalid video geometry for {path}")
    format_row = payload.get("format")
    format_duration = (
        _probe_duration(format_row.get("duration"), "format.duration")
        if isinstance(format_row, dict)
        else None
    )
    duration = format_duration or _probe_duration(
        stream.get("duration"), "stream.duration"
    )
    if duration is None:
        raise AuditError(f"ffprobe returned no positive finite video duration for {path}")
    codec_name = stream.get("codec_name")
    if not isinstance(codec_name, str) or not codec_name.strip():
        raise AuditError(f"ffprobe returned no video codec for {path}")
    return {
        "codec_name": codec_name,
        "width": width,
        "height": height,
        "duration_seconds": duration,
    }


def _extract_video_rgb(
    path: Path,
    timestamp: float,
    width: int,
    height: int,
    ffmpeg: str,
) -> bytes:
    output = _run_media(
        (
            ffmpeg,
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{timestamp:.6f}",
            "-i",
            str(path),
            "-map",
            "0:v:0",
            "-frames:v",
            "1",
            "-an",
            "-sn",
            "-dn",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "pipe:1",
        ),
        f"ffmpeg frame extraction from {path} at {timestamp:.6f}s",
    )
    expected_bytes = width * height * 3
    if len(output) != expected_bytes:
        raise AuditError(
            "ffmpeg did not return exactly one full RGB frame from "
            f"{path} at {timestamp:.6f}s: {len(output)} != {expected_bytes} bytes"
        )
    return output


def _normalize_ocr_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return "".join(character for character in normalized if character.isalnum() or character == "_")


def _ocr_items(path: Path, expected_image_sha256: str) -> list[dict[str, Any]]:
    payload = _read_json(path, "OCR evidence")
    if not isinstance(payload, dict):
        raise AuditError(f"OCR evidence root must be an object: {path}")
    image_sha = payload.get("image_sha256")
    if not isinstance(image_sha, str) or SHA256_RE.fullmatch(image_sha) is None:
        raise AuditError(
            f"OCR evidence image_sha256 must be 64 hexadecimal characters: {path}"
        )
    if image_sha.upper() != expected_image_sha256:
        raise AuditError(
            f"OCR evidence image_sha256 does not bind its submitted PNG: {path}"
        )
    rows = next(
        (
            payload[key]
            for key in ("items", "results", "ocr")
            if isinstance(payload.get(key), list)
        ),
        None,
    )
    if rows is None:
        raise AuditError(
            f"OCR evidence object must contain an items/results/ocr array: {path}"
        )
    if not rows:
        raise AuditError(f"OCR evidence contains no text rows: {path}")
    normalized: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise AuditError(f"OCR evidence row {index} is not an object: {path}")
        text = row.get("text")
        if not isinstance(text, str):
            raise AuditError(f"OCR evidence row {index} lacks string text: {path}")
        bbox = row.get("bbox")
        if bbox is not None:
            if (
                not isinstance(bbox, list)
                or len(bbox) != 4
                or any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in bbox)
            ):
                raise AuditError(f"OCR evidence row {index} has invalid bbox: {path}")
        normalized.append({"text": text})
    return normalized


def _validate_png(path: Path, width: int, height: int, context: str) -> None:
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            if image.format != "PNG":
                raise AuditError(f"{context} must be PNG, got {image.format!r}")
            if image.size != (width, height):
                raise AuditError(
                    f"{context} is {image.size[0]}x{image.size[1]}, expected "
                    f"full-screen {width}x{height}"
                )
    except AuditError:
        raise
    except Exception as exc:
        raise AuditError(f"could not decode {context}: {path}: {exc}") from exc


def _history_key_exists(path: Path, history_id: str) -> bool:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise AuditError(f"history source is not UTF-8: {path}: {exc}") from exc
    pattern = re.compile(rf"(?m)^\s*{re.escape(history_id)}\s*=\s*\{{")
    return pattern.search(text) is not None


def _file_identity(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": record["path"],
        "bytes": record["bytes"],
        "sha256": record["sha256"],
    }


def _manifest_real_character_provenance(
    manifest: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    provenance = manifest.get("release_manifest_provenance")
    raw = (
        provenance.get("real_character_provenance")
        if isinstance(provenance, dict)
        else None
    )
    if not isinstance(raw, dict) or raw.get("schema_version") != 1:
        raise AuditError(
            "release manifest real_character_provenance schema_version must be 1"
        )
    rows = raw.get("subjects")
    if not isinstance(rows, list) or not rows:
        raise AuditError(
            "release manifest real_character_provenance.subjects must be a non-empty array"
        )
    bookmark = raw.get("bookmark")
    if not isinstance(bookmark, dict):
        raise AuditError(
            "release manifest real_character_provenance.bookmark must be an object"
        )
    normalized_bookmark = {
        "id": _identifier(bookmark.get("id"), "release manifest provenance bookmark.id"),
        "start_date": _nonempty_string(
            bookmark.get("start_date"),
            "release manifest provenance bookmark.start_date",
        ),
    }
    by_history_id: dict[str, dict[str, Any]] = {}
    normalized_rows: list[dict[str, Any]] = []
    reviewed_history_ids: list[str] = []
    for index, raw_subject in enumerate(rows):
        context = (
            "release manifest real_character_provenance.subjects"
            f"[{index}]"
        )
        if not isinstance(raw_subject, dict):
            raise AuditError(f"{context} must be an object")
        history_id = _identifier(
            raw_subject.get("history_id"), f"{context}.history_id"
        )
        if history_id == real_characters.MANAGER_HISTORY_ID:
            expected = real_characters.manager()
        elif history_id in real_characters.REVIEWED_OFFICIAL_CONTRACT:
            expected = real_characters.reviewed_official(history_id)
            reviewed_history_ids.append(history_id)
        else:
            raise AuditError(
                f"{context}.history_id is outside the frozen historical allowlist: "
                f"{history_id!r}"
            )
        if history_id in by_history_id:
            raise AuditError(
                "release manifest real_character_provenance repeats "
                f"history_id {history_id!r}"
            )
        display_name = _nonempty_string(
            raw_subject.get("display_name"), f"{context}.display_name"
        )
        roles = sorted(
            _string_list(
                raw_subject.get("roles"), f"{context}.roles", identifiers=True
            )
        )
        if display_name != expected["display_name"]:
            raise AuditError(
                f"{context}.display_name must be {expected['display_name']!r}"
            )
        if set(roles) != set(expected["roles"]):
            raise AuditError(
                f"{context}.roles must be exactly {sorted(expected['roles'])!r}"
            )
        if raw_subject.get("origin") != "ck3_history_database":
            raise AuditError(f"{context}.origin must be 'ck3_history_database'")
        if raw_subject.get("temporary_or_generated") is not False:
            raise AuditError(f"{context}.temporary_or_generated must be false")
        history_path, history_source = _validate_file_record(
            raw_subject.get("history_source"), f"{context}.history_source"
        )
        if not _history_key_exists(history_path, history_id):
            raise AuditError(
                f"{context}.history_id {history_id!r} is absent from its bound CK3 history source"
            )
        normalized = {
            "history_id": history_id,
            "display_name": display_name,
            "roles": roles,
            "origin": "ck3_history_database",
            "temporary_or_generated": False,
            "history_source": history_source,
        }
        by_history_id[history_id] = normalized
        normalized_rows.append(normalized)
    if (
        len(by_history_id) != 2
        or real_characters.MANAGER_HISTORY_ID not in by_history_id
        or len(reviewed_history_ids) != 1
    ):
        raise AuditError(
            "release manifest real_character_provenance must contain exactly "
            "Zhao Shu and one resolved reviewed official from the frozen allowlist"
        )
    if normalized_bookmark != real_characters.BOOKMARK:
        raise AuditError(
            "release manifest real_character_provenance must bind the 1066 Song bookmark"
        )
    return by_history_id, {
        "schema_version": 1,
        "bookmark": normalized_bookmark,
        "subjects": normalized_rows,
    }


def _character_contract(subject: dict[str, Any]) -> dict[str, Any]:
    return {
        "history_id": subject["history_id"],
        "display_name": subject["display_name"],
        "roles": sorted(subject["roles"]),
        "origin": subject["origin"],
        "temporary_or_generated": subject["temporary_or_generated"],
        "history_source": _file_identity(subject["history_source"]),
    }


def _manifest_chapters(
    manifest: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    if manifest.get("project_status") != "captured_release_candidate":
        raise AuditError(
            "release manifest project_status must be 'captured_release_candidate'"
        )
    provenance = manifest.get("release_manifest_provenance")
    if not isinstance(provenance, dict) or provenance.get("capture_result") != "GREEN":
        raise AuditError(
            "release manifest provenance must bind capture_result='GREEN'"
        )
    rows = manifest.get("chapters")
    if not isinstance(rows, list) or not rows:
        raise AuditError("release manifest chapters must be a non-empty array")
    captured: dict[str, dict[str, Any]] = {}
    normalized: list[dict[str, Any]] = []
    all_ids: set[str] = set()
    for index, row in enumerate(rows):
        context = f"release manifest chapters[{index}]"
        if not isinstance(row, dict):
            raise AuditError(f"{context} must be an object")
        chapter_id = _identifier(row.get("id"), f"{context}.id")
        if chapter_id in all_ids:
            raise AuditError(f"release manifest repeats chapter id {chapter_id!r}")
        all_ids.add(chapter_id)
        if row.get("material_status") == "placeholder" or row.get("type") == "placeholder_card":
            raise AuditError(f"release manifest still contains placeholder {chapter_id}")
        if row.get("material_status") != "captured":
            continue
        promo_type = row.get("type")
        if promo_type not in {"still", "video_clip"}:
            raise AuditError(
                f"captured chapter {chapter_id} has unsupported type {promo_type!r}"
            )
        _source_path, source = _validate_file_record(
            row.get("source"), f"captured chapter {chapter_id}.source"
        )
        chapter = {
            "chapter_id": chapter_id,
            "type": promo_type,
            "source": source,
        }
        if promo_type == "video_clip":
            start = _number(row.get("start_seconds"), f"chapter {chapter_id}.start_seconds")
            end = _number(row.get("end_seconds"), f"chapter {chapter_id}.end_seconds")
            if start < 0 or end <= start:
                raise AuditError(f"chapter {chapter_id} has invalid clip interval")
            chapter["start_seconds"] = start
            chapter["end_seconds"] = end
        captured[chapter_id] = chapter
        normalized.append(chapter)
    if not captured:
        raise AuditError("release manifest contains no captured visual chapters")
    return captured, normalized


def _evaluate_spec(spec_path: Path) -> dict[str, Any]:
    spec_path = spec_path.expanduser().resolve()
    spec = _read_json(spec_path, "visual audit spec")
    if not isinstance(spec, dict):
        raise AuditError("visual audit spec root must be an object")
    if spec.get("schema_version") != SCHEMA_VERSION:
        raise AuditError(
            f"visual audit spec schema_version must be {SCHEMA_VERSION}"
        )
    if spec.get("kind") != SPEC_KIND:
        raise AuditError(f"visual audit spec kind must be {SPEC_KIND!r}")

    manifest_path, manifest_record = _validate_file_record(
        spec.get("release_manifest"), "release_manifest"
    )
    manifest = _read_json(manifest_path, "release manifest")
    if not isinstance(manifest, dict):
        raise AuditError("release manifest root must be an object")
    captured, chapter_rows = _manifest_chapters(manifest)
    manifest_subjects, manifest_character_provenance = (
        _manifest_real_character_provenance(manifest)
    )

    geometry = spec.get("frame_geometry")
    if not isinstance(geometry, dict):
        raise AuditError("frame_geometry must be an object")
    width = geometry.get("width")
    height = geometry.get("height")
    for value, name in ((width, "width"), (height, "height")):
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise AuditError(f"frame_geometry.{name} must be a positive integer")

    video_sources: dict[str, dict[str, Any]] = {}
    video_chapters = [
        chapter for chapter in captured.values() if chapter["type"] == "video_clip"
    ]
    ffmpeg: str | None = None
    if video_chapters:
        ffprobe = _media_program("ffprobe")
        ffmpeg = _media_program("ffmpeg")
        for chapter in video_chapters:
            source = chapter["source"]
            source_sha = source["sha256"]
            if source_sha not in video_sources:
                probe = _probe_video(Path(source["path"]), ffprobe)
                if (probe["width"], probe["height"]) != (width, height):
                    raise AuditError(
                        "ffprobe video geometry does not match frame_geometry for "
                        f"{source['path']}: {probe['width']}x{probe['height']} != "
                        f"{width}x{height}"
                    )
                video_sources[source_sha] = {
                    "source": source,
                    "probe": probe,
                }
            probe = video_sources[source_sha]["probe"]
            if chapter["end_seconds"] > probe["duration_seconds"] + 1e-3:
                raise AuditError(
                    f"chapter {chapter['chapter_id']} ends at "
                    f"{chapter['end_seconds']:.6f}s beyond ffprobe duration "
                    f"{probe['duration_seconds']:.6f}s"
                )
            chapter["video_probe"] = probe

    interval = _number(
        spec.get("sampling_interval_seconds"), "sampling_interval_seconds"
    )
    if interval <= 0 or interval > MAX_SAMPLE_INTERVAL_SECONDS:
        raise AuditError(
            "sampling_interval_seconds must be greater than zero and no more than "
            f"{MAX_SAMPLE_INTERVAL_SECONDS:.1f}"
        )

    bookmark = spec.get("bookmark")
    if not isinstance(bookmark, dict):
        raise AuditError("bookmark must be an object")
    normalized_bookmark = {
        "id": _identifier(bookmark.get("id"), "bookmark.id"),
        "start_date": _nonempty_string(bookmark.get("start_date"), "bookmark.start_date"),
    }
    if normalized_bookmark != manifest_character_provenance["bookmark"]:
        raise AuditError(
            "bookmark must exactly match release manifest real_character_provenance"
        )

    subjects_raw = spec.get("historical_characters")
    if not isinstance(subjects_raw, list) or not subjects_raw:
        raise AuditError("historical_characters must be a non-empty array")
    subjects: dict[str, dict[str, Any]] = {}
    subjects_by_history_id: dict[str, dict[str, Any]] = {}
    subject_rows: list[dict[str, Any]] = []
    for index, raw in enumerate(subjects_raw):
        context = f"historical_characters[{index}]"
        if not isinstance(raw, dict):
            raise AuditError(f"{context} must be an object")
        subject_id = _identifier(raw.get("subject_id"), f"{context}.subject_id")
        if subject_id in subjects:
            raise AuditError(f"duplicate historical subject id {subject_id!r}")
        history_id = _identifier(raw.get("history_id"), f"{context}.history_id")
        if history_id in subjects_by_history_id:
            raise AuditError(f"duplicate historical history_id {history_id!r}")
        display_name = _nonempty_string(raw.get("display_name"), f"{context}.display_name")
        roles = sorted(
            _string_list(raw.get("roles"), f"{context}.roles", identifiers=True)
        )
        if raw.get("origin") != "ck3_history_database":
            raise AuditError(f"{context}.origin must be 'ck3_history_database'")
        if raw.get("temporary_or_generated") is not False:
            raise AuditError(f"{context}.temporary_or_generated must be false")
        history_path, history_source = _validate_file_record(
            raw.get("history_source"), f"{context}.history_source"
        )
        if not _history_key_exists(history_path, history_id):
            raise AuditError(
                f"{context}.history_id {history_id!r} is absent from its bound CK3 history source"
            )
        subject = {
            "subject_id": subject_id,
            "history_id": history_id,
            "display_name": display_name,
            "roles": roles,
            "origin": "ck3_history_database",
            "temporary_or_generated": False,
            "history_source": history_source,
        }
        subjects[subject_id] = subject
        subjects_by_history_id[history_id] = subject
        subject_rows.append(subject)

    audit_character_contract = {
        history_id: _character_contract(subject)
        for history_id, subject in subjects_by_history_id.items()
    }
    manifest_character_contract = {
        history_id: _character_contract(subject)
        for history_id, subject in manifest_subjects.items()
    }
    if audit_character_contract != manifest_character_contract:
        missing = sorted(set(manifest_character_contract) - set(audit_character_contract))
        unexpected = sorted(set(audit_character_contract) - set(manifest_character_contract))
        mismatched = sorted(
            history_id
            for history_id in set(audit_character_contract) & set(manifest_character_contract)
            if audit_character_contract[history_id]
            != manifest_character_contract[history_id]
        )
        raise AuditError(
            "historical_characters must exactly match release manifest "
            "real_character_provenance; "
            f"missing={missing!r}; unexpected={unexpected!r}; "
            f"mismatched={mismatched!r}"
        )

    extra_tokens = spec.get("additional_forbidden_tokens", [])
    if not isinstance(extra_tokens, list):
        raise AuditError("additional_forbidden_tokens must be an array")
    forbidden_tokens = list(DEFAULT_FORBIDDEN_TOKENS)
    for index, token in enumerate(extra_tokens):
        value = _nonempty_string(token, f"additional_forbidden_tokens[{index}]")
        if value not in forbidden_tokens:
            forbidden_tokens.append(value)
    normalized_tokens = {
        token: _normalize_ocr_text(token) for token in forbidden_tokens
    }

    evidence_raw = spec.get("evidence")
    if not isinstance(evidence_raw, list) or not evidence_raw:
        raise AuditError("evidence must be a non-empty array")
    evidence_ids: set[str] = set()
    evidence_rows: list[dict[str, Any]] = []
    chapter_evidence: dict[str, list[dict[str, Any]]] = {
        chapter_id: [] for chapter_id in captured
    }
    findings: list[dict[str, Any]] = []
    extracted_frames: dict[tuple[str, float], bytes] = {}
    for index, raw in enumerate(evidence_raw):
        context = f"evidence[{index}]"
        if not isinstance(raw, dict):
            raise AuditError(f"{context} must be an object")
        evidence_id = _identifier(raw.get("evidence_id"), f"{context}.evidence_id")
        if evidence_id in evidence_ids:
            raise AuditError(f"duplicate evidence id {evidence_id!r}")
        evidence_ids.add(evidence_id)
        chapter_ids = _string_list(
            raw.get("chapter_ids"), f"{context}.chapter_ids", identifiers=True
        )
        unknown_chapters = sorted(set(chapter_ids) - set(captured))
        if unknown_chapters:
            raise AuditError(
                f"{context} references unknown/non-captured chapters: "
                + ", ".join(unknown_chapters)
            )
        subject_ids = _string_list(
            raw.get("subject_ids"), f"{context}.subject_ids", identifiers=True
        )
        unknown_subjects = sorted(set(subject_ids) - set(subjects))
        if unknown_subjects:
            raise AuditError(
                f"{context} references unknown historical subjects: "
                + ", ".join(unknown_subjects)
            )
        image_path, image_record = _validate_file_record(
            raw.get("image"), f"{context}.image"
        )
        ocr_path, ocr_record = _validate_file_record(
            raw.get("ocr"), f"{context}.ocr"
        )
        _validate_png(image_path, width, height, f"{context}.image")
        region = raw.get("ocr_region")
        if region != [0, 0, width, height]:
            raise AuditError(
                f"{context}.ocr_region must be full-screen [0, 0, {width}, {height}]"
            )
        source_sha = raw.get("source_sha256")
        if not isinstance(source_sha, str) or SHA256_RE.fullmatch(source_sha) is None:
            raise AuditError(f"{context}.source_sha256 must be 64 hexadecimal characters")
        source_sha = source_sha.upper()
        expected_source_shas = {
            captured[chapter_id]["source"]["sha256"] for chapter_id in chapter_ids
        }
        if expected_source_shas != {source_sha}:
            raise AuditError(
                f"{context}.source_sha256 does not bind every referenced chapter source"
            )
        chapter_types = {captured[chapter_id]["type"] for chapter_id in chapter_ids}
        if len(chapter_types) != 1:
            raise AuditError(f"{context} cannot mix still and video chapters")
        timestamp: float | None = None
        if chapter_types == {"video_clip"}:
            timestamp = _number(raw.get("timestamp_seconds"), f"{context}.timestamp_seconds")
            for chapter_id in chapter_ids:
                chapter = captured[chapter_id]
                if not (
                    chapter["start_seconds"] - 1e-6
                    <= timestamp
                    <= chapter["end_seconds"] + 1e-6
                ):
                    raise AuditError(
                        f"{context} timestamp {timestamp:.3f}s lies outside chapter {chapter_id}"
                    )
        elif raw.get("timestamp_seconds") is not None:
            raise AuditError(f"{context}.timestamp_seconds is only valid for video clips")
        if chapter_types == {"still"} and image_record["sha256"] != source_sha:
            raise AuditError(
                f"{context} still evidence image is not the exact manifest source"
            )

        if timestamp is not None:
            if ffmpeg is None:
                raise AuditError("ffmpeg is unavailable for captured video evidence")
            cache_key = (source_sha, timestamp)
            source_path = Path(video_sources[source_sha]["source"]["path"])
            extracted_rgb = extracted_frames.get(cache_key)
            if extracted_rgb is None:
                extracted_rgb = _extract_video_rgb(
                    source_path,
                    timestamp,
                    width,
                    height,
                    ffmpeg,
                )
                extracted_frames[cache_key] = extracted_rgb
            try:
                with Image.open(image_path) as submitted_image:
                    submitted_rgb = submitted_image.convert("RGB").tobytes()
            except Exception as exc:
                raise AuditError(
                    f"could not decode {context}.image for pixel comparison: "
                    f"{image_path}: {exc}"
                ) from exc
            if submitted_rgb != extracted_rgb:
                raise AuditError(
                    f"{context}.image pixels do not match bound video frame "
                    f"{source_path} at {timestamp:.6f}s"
                )

        ocr = _ocr_items(ocr_path, image_record["sha256"])
        joined = "".join(row["text"] for row in ocr)
        normalized_joined = _normalize_ocr_text(joined)
        hits = [
            token
            for token, normalized_token in normalized_tokens.items()
            if normalized_token and normalized_token in normalized_joined
        ]
        row = {
            "evidence_id": evidence_id,
            "chapter_ids": chapter_ids,
            "subject_ids": subject_ids,
            "source_sha256": source_sha,
            "image": image_record,
            "ocr": ocr_record,
            "ocr_image_sha256": image_record["sha256"],
            "ocr_region": region,
            "ocr_item_count": len(ocr),
            "forbidden_hits": hits,
        }
        if timestamp is not None:
            row["timestamp_seconds"] = timestamp
        evidence_rows.append(row)
        for chapter_id in chapter_ids:
            chapter_evidence[chapter_id].append(row)
        for token in hits:
            findings.append(
                {
                    "evidence_id": evidence_id,
                    "chapter_ids": chapter_ids,
                    "token": token,
                }
            )

    errors: list[str] = []
    chapter_results: list[dict[str, Any]] = []
    for chapter_id, chapter in captured.items():
        rows = chapter_evidence[chapter_id]
        subject_ids = sorted(
            {
                subject_id
                for row in rows
                for subject_id in row["subject_ids"]
            }
        )
        chapter_result = {
            **chapter,
            "evidence_ids": [row["evidence_id"] for row in rows],
            "subject_ids": subject_ids,
            "evidence_count": len(rows),
        }
        if not rows:
            errors.append(f"captured chapter {chapter_id} has no full-screen OCR/PNG evidence")
        elif chapter["type"] == "video_clip":
            timestamps = sorted(
                {float(row["timestamp_seconds"]) for row in rows}
            )
            chapter_result["sample_timestamps_seconds"] = timestamps
            start = float(chapter["start_seconds"])
            end = float(chapter["end_seconds"])
            if timestamps[0] > start + interval + 1e-6:
                errors.append(
                    f"chapter {chapter_id} sampling starts too late: "
                    f"{timestamps[0]:.3f}s for {start:.3f}s start"
                )
            if timestamps[-1] < end - interval - 1e-6:
                errors.append(
                    f"chapter {chapter_id} sampling ends too early: "
                    f"{timestamps[-1]:.3f}s for {end:.3f}s end"
                )
            for left, right in zip(timestamps, timestamps[1:]):
                if right - left > interval + 1e-6:
                    errors.append(
                        f"chapter {chapter_id} sampling gap {left:.3f}s..{right:.3f}s "
                        f"exceeds {interval:.3f}s"
                    )
                    break
        chapter_results.append(chapter_result)

    signoff = spec.get("manual_signoff")
    if not isinstance(signoff, dict):
        raise AuditError("manual_signoff must be an object")
    reviewer = _nonempty_string(signoff.get("reviewer"), "manual_signoff.reviewer")
    reviewed_at = _nonempty_string(
        signoff.get("reviewed_at_utc"), "manual_signoff.reviewed_at_utc"
    )
    try:
        parsed_reviewed_at = datetime.fromisoformat(reviewed_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AuditError("manual_signoff.reviewed_at_utc must be ISO-8601") from exc
    if parsed_reviewed_at.tzinfo is None:
        raise AuditError("manual_signoff.reviewed_at_utc must include a timezone")
    if signoff.get("status") != "GREEN":
        errors.append("manual_signoff.status is not GREEN")
    signed_manifest_sha = signoff.get("manifest_sha256")
    if (
        not isinstance(signed_manifest_sha, str)
        or signed_manifest_sha.upper() != manifest_record["sha256"]
    ):
        errors.append("manual_signoff.manifest_sha256 does not bind the release manifest")
    reviewed_chapters = signoff.get("reviewed_chapter_ids")
    if not isinstance(reviewed_chapters, list) or any(
        not isinstance(value, str) for value in reviewed_chapters
    ):
        raise AuditError("manual_signoff.reviewed_chapter_ids must be an array of strings")
    if set(reviewed_chapters) != set(captured) or len(reviewed_chapters) != len(set(reviewed_chapters)):
        errors.append(
            "manual_signoff.reviewed_chapter_ids must cover every captured chapter exactly once"
        )
    attestations = signoff.get("attestations")
    if not isinstance(attestations, dict):
        raise AuditError("manual_signoff.attestations must be an object")
    for attestation in REQUIRED_ATTESTATIONS:
        if attestations.get(attestation) is not True:
            errors.append(f"manual sign-off lacks true attestation {attestation!r}")

    if findings:
        errors.append(
            f"forbidden fixture/test-only text appears in {len(findings)} evidence frame(s)"
        )
    result = "GREEN" if not errors else "RED"
    return {
        "result": result,
        "release_manifest": manifest_record,
        "release_manifest_real_character_provenance": manifest_character_provenance,
        "bookmark": normalized_bookmark,
        "frame_geometry": {"width": width, "height": height},
        "video_sources": [
            video_sources[source_sha] for source_sha in sorted(video_sources)
        ],
        "sampling_interval_seconds": interval,
        "forbidden_tokens": forbidden_tokens,
        "historical_characters": subject_rows,
        "chapters": chapter_results,
        "evidence": evidence_rows,
        "findings": findings,
        "manual_signoff": {
            "status": signoff.get("status"),
            "reviewer": reviewer,
            "reviewed_at_utc": reviewed_at,
            "manifest_sha256": (
                signed_manifest_sha.upper()
                if isinstance(signed_manifest_sha, str)
                else signed_manifest_sha
            ),
            "reviewed_chapter_ids": reviewed_chapters,
            "attestations": {
                key: attestations.get(key) for key in REQUIRED_ATTESTATIONS
            },
        },
        "summary": {
            "captured_chapters": len(captured),
            "historical_characters": len(subjects),
            "full_screen_evidence_frames": len(evidence_rows),
            "forbidden_hits": len(findings),
        },
        "errors": errors,
    }


def create_report(spec_path: Path) -> dict[str, Any]:
    spec_path = spec_path.expanduser().resolve()
    spec_record = _actual_file_record(spec_path, "Promo visual audit spec")
    try:
        evaluation = _evaluate_spec(spec_path)
    except AuditError as exc:
        evaluation = {
            "result": "RED",
            "findings": [],
            "summary": {
                "captured_chapters": 0,
                "historical_characters": 0,
                "full_screen_evidence_frames": 0,
                "forbidden_hits": 0,
            },
            "errors": [str(exc)],
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": REPORT_KIND,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "spec": spec_record,
        "evaluation_sha256": _canonical_sha256(evaluation),
        "evaluation": evaluation,
    }


def write_report(spec_path: Path, output: Path) -> tuple[dict[str, Any], Path]:
    output = output.expanduser().resolve()
    if output.exists():
        raise AuditError(f"refusing to overwrite preserved visual audit report: {output}")
    report = create_report(spec_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report, output


def verify_report(report_path: Path, expected_sha256: str | None = None) -> dict[str, Any]:
    report_path = report_path.expanduser().resolve()
    if expected_sha256 is not None:
        if SHA256_RE.fullmatch(expected_sha256) is None:
            raise AuditError("--expected-report-sha256 must be 64 hexadecimal characters")
        if sha256_file(report_path) != expected_sha256.upper():
            raise AuditError("visual audit report SHA-256 does not match release binding")
    report = _read_json(report_path, "visual audit report")
    if not isinstance(report, dict):
        raise AuditError("visual audit report root must be an object")
    if report.get("schema_version") != SCHEMA_VERSION or report.get("kind") != REPORT_KIND:
        raise AuditError("visual audit report schema/kind is unsupported")
    spec_path, normalized_spec = _validate_file_record(
        report.get("spec"), "visual audit report spec"
    )
    stored = report.get("evaluation")
    if not isinstance(stored, dict):
        raise AuditError("visual audit report evaluation must be an object")
    stored_sha = report.get("evaluation_sha256")
    if not isinstance(stored_sha, str) or stored_sha.upper() != _canonical_sha256(stored):
        raise AuditError("visual audit report evaluation SHA-256 is invalid")
    recomputed = _evaluate_spec(spec_path)
    recomputed_sha = _canonical_sha256(recomputed)
    if stored_sha.upper() != recomputed_sha or stored != recomputed:
        raise AuditError("visual audit report no longer reproduces from its bound inputs")
    if normalized_spec != report["spec"]:
        raise AuditError("visual audit report spec record is not canonical")
    if recomputed.get("result") != "GREEN":
        raise AuditError("visual audit report is RED")
    return report


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    subparsers = result.add_subparsers(dest="command", required=True)
    audit = subparsers.add_parser("audit", help="create an append-only GREEN/RED report")
    audit.add_argument("--spec", type=Path, required=True)
    audit.add_argument("--output", type=Path, required=True)
    verify = subparsers.add_parser("verify", help="rebuild and verify an existing report")
    verify.add_argument("--report", type=Path, required=True)
    verify.add_argument("--expected-report-sha256")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    try:
        if arguments.command == "audit":
            report, output = write_report(arguments.spec, arguments.output)
            result = report["evaluation"]["result"]
            print(
                f"{result}: promo visual audit: {output}; "
                f"sha256={sha256_file(output)}"
            )
            if result != "GREEN":
                for error in report["evaluation"].get("errors", []):
                    print(f"RED: {error}", file=sys.stderr)
                return 2
            return 0
        verified = verify_report(
            arguments.report, arguments.expected_report_sha256
        )
        summary = verified["evaluation"]["summary"]
        print(
            "GREEN: verified promo visual audit: "
            f"chapters={summary['captured_chapters']}; "
            f"historical_characters={summary['historical_characters']}; "
            f"frames={summary['full_screen_evidence_frames']}; "
            f"sha256={sha256_file(arguments.report.expanduser().resolve())}"
        )
        return 0
    except AuditError as exc:
        print(f"RED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
