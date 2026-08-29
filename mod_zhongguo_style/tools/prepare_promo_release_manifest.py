#!/usr/bin/env python3
"""Project one GREEN ZhongGuo promo capture into a zero-placeholder manifest.

The capture runner intentionally keeps one long, lossless-ish MKV plus timeline
marks and lossless policy-card stills.  This tool turns that immutable bundle
into an external release-candidate manifest without trimming or overwriting any
source media.  Claims that lack an independent live shot remain conspicuous
generated evidence/boundary cards; they are never relabelled as gameplay.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Sequence


TOOLS_DIRECTORY = Path(__file__).resolve().parent
PROJECT_DIRECTORY = TOOLS_DIRECTORY.parent
REPOSITORY_ROOT = PROJECT_DIRECTORY.parent
DEFAULT_BASE_MANIFEST = PROJECT_DIRECTORY / "promo" / "promo-manifest.json"

if str(TOOLS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIRECTORY))

import build_promo_video as promo  # noqa: E402
import promo_real_character_contract as real_characters  # noqa: E402


POLICY_IDS = (1, 7, 20, 22, 26, 361)
CLEAN_SPAN_IDS = (
    "calibration",
    "managed_scoreboard",
    "policy_cockpit",
    "jingcha_mandate",
    "free_jingcha_planner",
    "superior_assigned_325",
    "received_scoreboard_with_325",
    *(f"policy_card_{mechanism_id:03d}" for mechanism_id in POLICY_IDS),
)
REQUIRED_MARKS = (
    "recording_started_after_gameplay_hud",
    *(mark for span_id in CLEAN_SPAN_IDS for mark in (
        f"{span_id}_clean_begin",
        f"{span_id}_clean_end",
    )),
    "all_requested_product_screens_captured",
    "recording_stop_requested",
)


class PrepareError(RuntimeError):
    """A GREEN capture cannot safely become a release manifest."""


def _read_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except OSError as exc:
        raise PrepareError(f"could not read {label}: {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise PrepareError(f"invalid JSON in {label}: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise PrepareError(f"{label} root must be an object: {path}")
    return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _file_record(path: Path, label: str) -> dict[str, Any]:
    path = path.expanduser().resolve()
    if not path.is_file():
        raise PrepareError(f"required {label} does not exist: {path}")
    return {
        "path": str(path),
        "label": label,
        "bytes": path.stat().st_size,
        "sha256": _sha256(path),
    }


def _verified_file_record(raw: Any, label: str) -> tuple[Path, dict[str, Any]]:
    if not isinstance(raw, dict):
        raise PrepareError(f"{label} must be a path/bytes/sha256 object")
    raw_path = raw.get("path")
    if not isinstance(raw_path, str) or not Path(raw_path).is_absolute():
        raise PrepareError(f"{label}.path must be absolute")
    path = Path(raw_path).expanduser().resolve()
    if not path.is_file():
        raise PrepareError(f"{label}.path does not exist: {path}")
    actual_bytes = path.stat().st_size
    actual_sha = _sha256(path)
    if raw.get("bytes") != actual_bytes:
        raise PrepareError(f"{label}.bytes does not match {path}")
    declared_sha = raw.get("sha256")
    if not isinstance(declared_sha, str) or declared_sha.upper() != actual_sha:
        raise PrepareError(f"{label}.sha256 does not match {path}")
    return path, {
        "path": str(path),
        "label": label,
        "bytes": actual_bytes,
        "sha256": actual_sha,
    }


def _history_key_exists(path: Path, history_id: str) -> bool:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise PrepareError(f"CK3 history source is not UTF-8: {path}") from exc
    return re.search(
        rf"(?m)^\s*{re.escape(history_id)}\s*=\s*\{{",
        text,
    ) is not None


def _paradox_top_level_block(text: str, key: str) -> str:
    match = re.search(rf"(?m)^\s*{re.escape(key)}\s*=\s*\{{", text)
    if match is None:
        raise PrepareError(f"CK3 history source is missing top-level block {key}")
    opening = text.index("{", match.start(), match.end())
    depth = 0
    quoted = False
    escaped = False
    for index in range(opening, len(text)):
        character = text[index]
        if quoted:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                quoted = False
            continue
        if character == '"':
            quoted = True
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return text[match.start() : index + 1]
    raise PrepareError(f"CK3 history source has unterminated block {key}")


def _indexed_files(index: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = index.get("files")
    if not isinstance(rows, list):
        raise PrepareError("evidence index files must be an array")
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("path"), str):
            raise PrepareError("evidence index contains an invalid file row")
        normalized = row["path"].replace("\\", "/")
        if normalized in result:
            raise PrepareError(f"evidence index repeats file {normalized}")
        result[normalized] = row
    return result


def _verify_indexed_file(
    artifact_root: Path,
    indexed: dict[str, dict[str, Any]],
    relative: str,
) -> Path:
    normalized = relative.replace("\\", "/")
    row = indexed.get(normalized)
    if row is None:
        raise PrepareError(f"evidence index is missing {normalized}")
    path = (artifact_root / Path(normalized)).resolve()
    try:
        path.relative_to(artifact_root)
    except ValueError as exc:
        raise PrepareError(f"indexed path escapes capture root: {normalized}") from exc
    if not path.is_file():
        raise PrepareError(f"indexed capture file is missing: {path}")
    actual_bytes = path.stat().st_size
    actual_sha = _sha256(path)
    if row.get("bytes") != actual_bytes:
        raise PrepareError(
            f"evidence index byte count mismatch for {normalized}: "
            f"{row.get('bytes')!r} != {actual_bytes}"
        )
    indexed_sha = row.get("sha256")
    if not isinstance(indexed_sha, str) or indexed_sha.upper() != actual_sha:
        raise PrepareError(f"evidence index SHA-256 mismatch for {normalized}")
    return path


def _verified_indexed_record(
    raw: Any,
    label: str,
    artifact_root: Path,
    indexed: dict[str, dict[str, Any]],
) -> tuple[Path, dict[str, Any]]:
    path, record = _verified_file_record(raw, label)
    try:
        relative = path.relative_to(artifact_root).as_posix()
    except ValueError as exc:
        raise PrepareError(f"{label}.path lies outside the capture artifact root") from exc
    indexed_path = _verify_indexed_file(artifact_root, indexed, relative)
    if indexed_path != path:
        raise PrepareError(f"{label}.path does not resolve to its indexed capture file")
    return path, {
        "path": str(path),
        "bytes": record["bytes"],
        "sha256": record["sha256"],
    }


def _mark_map(timeline: dict[str, Any]) -> dict[str, float]:
    rows = timeline.get("marks")
    if not isinstance(rows, list):
        raise PrepareError("capture timeline marks must be an array")
    marks: dict[str, float] = {}
    prior = -1.0
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("label"), str):
            raise PrepareError("capture timeline contains an invalid mark")
        seconds = row.get("seconds")
        if isinstance(seconds, bool) or not isinstance(seconds, (int, float)):
            raise PrepareError(f"timeline mark {row['label']!r} has invalid seconds")
        seconds = float(seconds)
        if seconds < 0 or seconds < prior:
            raise PrepareError("capture timeline marks must be non-negative and ordered")
        prior = seconds
        if row["label"] in marks:
            raise PrepareError(f"capture timeline repeats mark {row['label']!r}")
        marks[row["label"]] = seconds
    missing = [label for label in REQUIRED_MARKS if label not in marks]
    if missing:
        raise PrepareError("capture timeline is missing marks: " + ", ".join(missing))
    return marks


def _clean_frame_gates(
    timeline: dict[str, Any],
    marks: dict[str, float],
    artifact_root: Path,
    indexed: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    rows = timeline.get("clean_frame_gates")
    if not isinstance(rows, list):
        raise PrepareError("capture timeline clean_frame_gates must be an array")
    gates: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(rows):
        if not isinstance(raw, dict):
            raise PrepareError(f"clean_frame_gates[{index}] must be an object")
        span_id = raw.get("span_id")
        if not isinstance(span_id, str) or span_id not in CLEAN_SPAN_IDS:
            raise PrepareError(
                f"clean_frame_gates[{index}] has unsupported span_id {span_id!r}"
            )
        if span_id in gates:
            raise PrepareError(f"clean_frame_gates repeats {span_id!r}")
        begin_mark = f"{span_id}_clean_begin"
        end_mark = f"{span_id}_clean_end"
        if raw.get("begin_mark") != begin_mark or raw.get("end_mark") != end_mark:
            raise PrepareError(
                f"clean-frame gate {span_id!r} does not bind its exact clean marks"
            )
        if raw.get("result") != "GREEN":
            raise PrepareError(f"clean-frame gate {span_id!r} is not GREEN")
        if raw.get("full_screen") is not True:
            raise PrepareError(
                f"clean-frame gate {span_id!r} does not attest full_screen=true"
            )
        if raw.get("fixture_test_ui_absent") is not True:
            raise PrepareError(
                f"clean-frame gate {span_id!r} does not attest fixture_test_ui_absent=true"
            )
        if raw.get("native_decisions_drawer_absent") is not True:
            raise PrepareError(
                f"clean-frame gate {span_id!r} does not attest "
                "native_decisions_drawer_absent=true"
            )
        frames = raw.get("frames")
        if not isinstance(frames, list) or len(frames) != 2:
            raise PrepareError(
                f"clean-frame gate {span_id!r} must bind exact begin/end frame proofs"
            )
        verified_frames: list[dict[str, Any]] = []
        for frame_index, phase in enumerate(("begin", "end")):
            frame = frames[frame_index]
            context = f"clean-frame gate {span_id!r} {phase} frame"
            if not isinstance(frame, dict):
                raise PrepareError(f"{context} must be an object")
            for key, expected in (
                ("schema_version", 1),
                ("result", "GREEN"),
                ("span", span_id),
                ("phase", phase),
                ("full_screen", True),
                ("fixture_test_ui_absent", True),
                ("native_decisions_drawer_absent", True),
                ("drawer_absence_consecutive_samples", 2),
            ):
                if frame.get(key) != expected:
                    raise PrepareError(
                        f"{context}.{key} must be {expected!r}, got {frame.get(key)!r}"
                    )
            if frame.get("forbidden_hits") != []:
                raise PrepareError(f"{context} contains forbidden OCR hits")
            samples = frame.get("drawer_absence_samples")
            if not isinstance(samples, list) or len(samples) != 2:
                raise PrepareError(
                    f"{context} must bind two consecutive Decisions-header samples"
                )
            verified_samples: list[dict[str, Any]] = []
            for sample_index, sample in enumerate(samples, start=1):
                sample_context = f"{context} drawer sample {sample_index}"
                if not isinstance(sample, dict) or sample.get("sample_index") != sample_index:
                    raise PrepareError(f"{sample_context} has an invalid sample index")
                if not isinstance(sample.get("normalized_decisions_header_ocr"), str):
                    raise PrepareError(
                        f"{sample_context} lacks normalized Decisions-header OCR"
                    )
                _, image_record = _verified_indexed_record(
                    sample.get("image"),
                    f"{sample_context}.image",
                    artifact_root,
                    indexed,
                )
                _, ocr_record = _verified_indexed_record(
                    sample.get("ocr"),
                    f"{sample_context}.ocr",
                    artifact_root,
                    indexed,
                )
                verified_samples.append(
                    {
                        "sample_index": sample_index,
                        "normalized_decisions_header_ocr": sample[
                            "normalized_decisions_header_ocr"
                        ],
                        "image": image_record,
                        "ocr": ocr_record,
                    }
                )
            if frame.get("image") != samples[0].get("image"):
                raise PrepareError(f"{context}.image must bind its first sample image")
            if frame.get("ocr") != samples[0].get("ocr"):
                raise PrepareError(f"{context}.ocr must bind its first sample OCR")
            gate_path, gate_record = _verified_indexed_record(
                frame.get("gate"), f"{context}.gate", artifact_root, indexed
            )
            gate_payload = _read_object(gate_path, f"{context} gate JSON")
            expected_gate_payload = {
                key: value for key, value in frame.items() if key != "gate"
            }
            if gate_payload != expected_gate_payload:
                raise PrepareError(
                    f"{context} gate JSON does not exactly bind its timeline proof"
                )
            verified_frames.append(
                {
                    "schema_version": 1,
                    "result": "GREEN",
                    "span": span_id,
                    "phase": phase,
                    "full_screen": True,
                    "fixture_test_ui_absent": True,
                    "native_decisions_drawer_absent": True,
                    "drawer_absence_consecutive_samples": 2,
                    "drawer_absence_samples": verified_samples,
                    "gate": gate_record,
                }
            )
        begin = marks[begin_mark]
        end = marks[end_mark]
        if end <= begin:
            raise PrepareError(
                f"clean span {span_id!r} is not positive: {begin:.3f}..{end:.3f}"
            )
        gates[span_id] = {
            "span_id": span_id,
            "begin_mark": begin_mark,
            "end_mark": end_mark,
            "result": "GREEN",
            "full_screen": True,
            "fixture_test_ui_absent": True,
            "native_decisions_drawer_absent": True,
            "frames": verified_frames,
        }
    missing = [span_id for span_id in CLEAN_SPAN_IDS if span_id not in gates]
    if missing:
        raise PrepareError(
            "capture timeline is missing GREEN clean-frame gates: "
            + ", ".join(missing)
        )
    if len(gates) != len(CLEAN_SPAN_IDS):
        raise PrepareError("capture timeline has unexpected clean-frame gates")
    return gates


def _real_character_provenance(timeline: dict[str, Any]) -> dict[str, Any]:
    raw = timeline.get("real_character_provenance")
    if not isinstance(raw, dict) or raw.get("schema_version") != 1:
        raise PrepareError(
            "capture timeline real_character_provenance schema_version must be 1"
        )
    rows = raw.get("subjects")
    if not isinstance(rows, list):
        raise PrepareError("real_character_provenance.subjects must be an array")
    subjects: dict[str, dict[str, Any]] = {}
    reviewed_history_ids: list[str] = []
    for index, subject in enumerate(rows):
        context = f"real_character_provenance.subjects[{index}]"
        if not isinstance(subject, dict):
            raise PrepareError(f"{context} must be an object")
        history_id = subject.get("history_id")
        if history_id == real_characters.MANAGER_HISTORY_ID:
            expected = real_characters.manager()
        elif history_id in real_characters.REVIEWED_OFFICIAL_CONTRACT:
            expected = real_characters.reviewed_official(str(history_id))
            reviewed_history_ids.append(str(history_id))
        else:
            raise PrepareError(
                f"{context}.history_id is outside the frozen manager/reviewed "
                f"historical allowlist: {history_id!r}"
            )
        if history_id in subjects:
            raise PrepareError(f"real_character_provenance repeats {history_id}")
        if subject.get("display_name") != expected["display_name"]:
            raise PrepareError(
                f"{context}.display_name must be {expected['display_name']!r}"
            )
        roles = subject.get("roles")
        if (
            not isinstance(roles, list)
            or any(not isinstance(role, str) for role in roles)
            or set(roles) != set(expected["roles"])
            or len(roles) != len(set(roles))
        ):
            raise PrepareError(
                f"{context}.roles must be exactly {sorted(expected['roles'])!r}"
            )
        if subject.get("origin") != "ck3_history_database":
            raise PrepareError(f"{context}.origin must be 'ck3_history_database'")
        if subject.get("temporary_or_generated") is not False:
            raise PrepareError(f"{context}.temporary_or_generated must be false")
        history_path, history_source = _verified_file_record(
            subject.get("history_source"), f"{context}.history_source"
        )
        if not _history_key_exists(history_path, history_id):
            raise PrepareError(
                f"{context}.history_id {history_id!r} is absent from its history source"
            )
        subjects[history_id] = {
            "history_id": history_id,
            "display_name": expected["display_name"],
            "roles": sorted(expected["roles"]),
            "origin": "ck3_history_database",
            "temporary_or_generated": False,
            "history_source": history_source,
        }
    if (
        len(subjects) != 2
        or real_characters.MANAGER_HISTORY_ID not in subjects
        or len(reviewed_history_ids) != 1
    ):
        raise PrepareError(
            "real_character_provenance must bind exactly Zhao Shu and one resolved "
            "reviewed official from the frozen historical allowlist"
        )
    reviewed_history_id = reviewed_history_ids[0]
    reviewed_contract = real_characters.reviewed_official(reviewed_history_id)
    expected_bookmark = dict(real_characters.BOOKMARK)
    if raw.get("bookmark") != expected_bookmark:
        raise PrepareError(
            "real_character_provenance.bookmark must bind the 1066 Song start"
        )
    title_history_path, title_history_source = _verified_file_record(
        raw.get("title_history_source"),
        "real_character_provenance.title_history_source",
    )
    try:
        title_text = title_history_path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise PrepareError(
            f"CK3 title history source is not UTF-8: {title_history_path}"
        ) from exc
    china_block = _paradox_top_level_block(title_text, "h_china")
    if re.search(
        r"1063\.4\.30\s*=\s*\{[^}]*holder\s*=\s*han_8052",
        china_block,
        re.S,
    ) is None:
        raise PrepareError("h_china history does not bind han_8052 at the 1066 start")
    reviewed_title = str(reviewed_contract["title_id"])
    reviewed_holder_date = str(reviewed_contract["holder_date"])
    reviewed_liege_title = str(reviewed_contract["liege_title_id"])
    reviewed_liege_holder_id = str(reviewed_contract["liege_holder_id"])
    reviewed_liege_holder_date = str(reviewed_contract["liege_holder_date"])
    reviewed_title_block = _paradox_top_level_block(title_text, reviewed_title)
    if re.search(
        rf"{re.escape(reviewed_holder_date)}\s*=\s*\{{"
        rf"[^}}]*holder\s*=\s*{re.escape(reviewed_history_id)}",
        reviewed_title_block,
        re.S,
    ) is None:
        raise PrepareError(
            f"{reviewed_title} history does not bind {reviewed_history_id} "
            f"on {reviewed_holder_date}"
        )
    if re.search(
        rf"\bliege\s*=\s*{re.escape(reviewed_liege_title)}\b",
        reviewed_title_block,
    ) is None:
        raise PrepareError(
            f"{reviewed_title} history does not bind its holder under "
            f"{reviewed_liege_title}"
        )
    reviewed_liege_block = _paradox_top_level_block(
        title_text, reviewed_liege_title
    )
    if re.search(
        rf"{re.escape(reviewed_liege_holder_date)}\s*=\s*\{{"
        rf"[^}}]*holder\s*=\s*{re.escape(reviewed_liege_holder_id)}",
        reviewed_liege_block,
        re.S,
    ) is None:
        raise PrepareError(
            f"{reviewed_liege_title} history does not bind direct liege holder "
            f"{reviewed_liege_holder_id} on {reviewed_liege_holder_date}"
        )
    title_assertions = {
        "h_china_holder_at_start": "han_8052",
        "reviewed_official_title_at_start": reviewed_title,
        "reviewed_official_holder_at_start": reviewed_history_id,
        "reviewed_official_holder_date": reviewed_holder_date,
        "reviewed_official_title_liege_at_start": reviewed_liege_title,
        "reviewed_official_direct_liege_holder_at_start": reviewed_liege_holder_id,
        "reviewed_official_direct_liege_holder_date": reviewed_liege_holder_date,
    }
    if raw.get("title_history_assertions") != title_assertions:
        raise PrepareError(
            "real_character_provenance.title_history_assertions do not match "
            "the verified 1066 title history"
        )
    return {
        "schema_version": 1,
        "bookmark": expected_bookmark,
        "subjects": [
            subjects[real_characters.MANAGER_HISTORY_ID],
            subjects[reviewed_history_id],
        ],
        "title_history_source": title_history_source,
        "title_history_assertions": title_assertions,
    }


def _capture_bundle(artifact_root: Path) -> dict[str, Any]:
    artifact_root = artifact_root.expanduser().resolve()
    if not artifact_root.is_dir():
        raise PrepareError(f"capture artifact root does not exist: {artifact_root}")
    try:
        artifact_root.relative_to(REPOSITORY_ROOT.resolve())
    except ValueError:
        pass
    else:
        raise PrepareError("capture artifacts must stay outside the repository")

    report_path = artifact_root / "report.json"
    timeline_path = artifact_root / "cell" / "promo" / "capture-timeline.json"
    index_path = artifact_root / "evidence-index.json"
    report = _read_object(report_path, "capture report")
    timeline = _read_object(timeline_path, "capture timeline")
    index = _read_object(index_path, "evidence index")
    cell = report.get("cell")
    if report.get("result") != "GREEN" or not isinstance(cell, dict) or cell.get("result") != "GREEN":
        raise PrepareError(
            f"capture report must be GREEN at root and cell; got "
            f"{report.get('result')!r}/{cell.get('result') if isinstance(cell, dict) else None!r}"
        )
    if index.get("result") != "GREEN":
        raise PrepareError(f"evidence index must be GREEN, got {index.get('result')!r}")
    indexed_root = index.get("artifact_root")
    if not isinstance(indexed_root, str) or Path(indexed_root).resolve() != artifact_root:
        raise PrepareError("evidence index artifact_root does not match the requested run")
    if timeline.get("exclude_ck3_loading") is not True:
        raise PrepareError("capture timeline does not attest exclusion of CK3 loading")
    source_kind = timeline.get("source_kind")
    if not isinstance(source_kind, str) or "real CK3" not in source_kind:
        raise PrepareError("capture timeline is not classified as real CK3 capture")

    indexed = _indexed_files(index)
    _verify_indexed_file(artifact_root, indexed, "report.json")
    _verify_indexed_file(
        artifact_root, indexed, "cell/promo/capture-timeline.json"
    )
    raw_value = timeline.get("raw_path")
    if not isinstance(raw_value, str) or not Path(raw_value).is_absolute():
        raise PrepareError("capture timeline raw_path must be absolute")
    raw_path = Path(raw_value).resolve()
    try:
        raw_relative = raw_path.relative_to(artifact_root).as_posix()
    except ValueError as exc:
        raise PrepareError("capture raw MKV must be contained by the artifact root") from exc
    _verify_indexed_file(artifact_root, indexed, raw_relative)
    raw_sha = _sha256(raw_path)
    if not isinstance(timeline.get("raw_sha256"), str) or timeline["raw_sha256"].upper() != raw_sha:
        raise PrepareError("capture timeline raw_sha256 does not match the MKV")
    if timeline.get("raw_bytes") != raw_path.stat().st_size:
        raise PrepareError("capture timeline raw_bytes does not match the MKV")

    marks = _mark_map(timeline)
    clean_frame_gates = _clean_frame_gates(
        timeline, marks, artifact_root, indexed
    )
    real_characters = _real_character_provenance(timeline)
    recording_start = marks["recording_started_after_gameplay_hud"]
    recording_stop = marks["recording_stop_requested"]
    for span_id in CLEAN_SPAN_IDS:
        begin = marks[f"{span_id}_clean_begin"]
        end = marks[f"{span_id}_clean_end"]
        if begin < recording_start or end > recording_stop:
            raise PrepareError(
                f"clean span {span_id!r} lies outside the recorded gameplay window"
            )
    final_clean_end = marks[f"policy_card_{POLICY_IDS[-1]:03d}_clean_end"]
    if marks["all_requested_product_screens_captured"] < final_clean_end:
        raise PrepareError(
            "all_requested_product_screens_captured precedes the final clean span"
        )

    reported_capture = cell.get("promo_capture")
    if not isinstance(reported_capture, dict):
        raise PrepareError("GREEN report does not bind promo_capture evidence")
    if (
        not isinstance(reported_capture.get("raw_sha256"), str)
        or reported_capture["raw_sha256"].upper() != raw_sha
        or reported_capture.get("marks") != timeline.get("marks")
        or reported_capture.get("clean_frame_gates")
        != timeline.get("clean_frame_gates")
        or reported_capture.get("real_character_provenance")
        != timeline.get("real_character_provenance")
        or reported_capture.get("exclude_ck3_loading") is not True
    ):
        raise PrepareError(
            "GREEN report promo_capture does not match the timeline/MKV, clean gates, "
            "or real-character provenance"
        )

    scenario = cell.get("scenario_evidence")
    if not isinstance(scenario, dict):
        raise PrepareError("GREEN report lacks scenario_evidence")
    reviewed_subjects = [
        row
        for row in real_characters["subjects"]
        if "reviewed_official" in row["roles"]
    ]
    if len(reviewed_subjects) != 1:
        raise PrepareError(
            "verified real-character provenance does not contain exactly one reviewed official"
        )
    reviewed_history_id = reviewed_subjects[0]["history_id"]
    personal_result = scenario.get("superior_assigned_player_result")
    runtime_attestation = scenario.get("real_character_runtime_attestation")
    if (
        scenario.get("reviewed_official_history_id") != reviewed_history_id
        or not isinstance(personal_result, dict)
        or personal_result.get("reviewed_official_history_id")
        != reviewed_history_id
        or not isinstance(runtime_attestation, dict)
        or runtime_attestation.get("reviewed_official_history_id")
        != reviewed_history_id
    ):
        raise PrepareError(
            "GREEN report scenario, personal-result evidence, and runtime attestation "
            "must all bind the timeline's exact reviewed official"
        )
    if not isinstance(scenario.get("promo_received_scoreboard"), dict):
        raise PrepareError("GREEN report lacks the received-scoreboard promo evidence")
    policy_rows = scenario.get("promo_policy_cards")
    if not isinstance(policy_rows, list):
        raise PrepareError("GREEN report lacks promo_policy_cards")
    reported_policy_ids = [
        row.get("mechanism_id") for row in policy_rows if isinstance(row, dict)
    ]
    if reported_policy_ids != list(POLICY_IDS):
        raise PrepareError(
            f"GREEN report policy cards are {reported_policy_ids!r}; "
            f"expected {list(POLICY_IDS)!r}"
        )

    policy_paths: dict[int, Path] = {}
    for mechanism_id in POLICY_IDS:
        relative = f"cell/12_policy_{mechanism_id:03d}_event.png"
        policy_paths[mechanism_id] = _verify_indexed_file(
            artifact_root, indexed, relative
        )
    superior_result = _verify_indexed_file(
        artifact_root, indexed, "cell/10_superior_result.png"
    )
    return {
        "artifact_root": artifact_root,
        "report_path": report_path.resolve(),
        "timeline_path": timeline_path.resolve(),
        "index_path": index_path.resolve(),
        "report": report,
        "timeline": timeline,
        "index": index,
        "raw_path": raw_path,
        "marks": marks,
        "clean_frame_gates": clean_frame_gates,
        "real_character_provenance": real_characters,
        "policy_paths": policy_paths,
        "superior_result_path": superior_result,
    }


def _clear_visual(chapter: dict[str, Any]) -> None:
    for key in (
        "source",
        "evidence_sources",
        "start_seconds",
        "end_seconds",
        "clip_duration_seconds",
        "fit",
        "capture",
    ):
        chapter.pop(key, None)


def _common_evidence(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _file_record(bundle["report_path"], "GREEN promo acceptance report"),
        _file_record(bundle["timeline_path"], "Capture timeline and clip marks"),
        _file_record(bundle["index_path"], "Append-only evidence index"),
    ]


def _set_boundary(
    chapter: dict[str, Any],
    bundle: dict[str, Any],
    *,
    zh_status: str,
    en_status: str,
    body_zh: list[str],
    body_en: list[str],
) -> None:
    _clear_visual(chapter)
    chapter["type"] = "title_card"
    chapter["material_status"] = "generated"
    chapter["status"] = {
        "zh": zh_status,
        "en": en_status,
        "classification": "generated-evidence-boundary",
    }
    chapter["body_zh"] = body_zh
    chapter["body_en"] = body_en
    chapter["evidence_sources"] = _common_evidence(bundle)


def _clean_span_window(
    bundle: dict[str, Any], span_id: str
) -> tuple[float, float, str, str]:
    if span_id not in CLEAN_SPAN_IDS:
        raise PrepareError(f"unsupported clean span {span_id!r}")
    marks = bundle["marks"]
    start_label = f"{span_id}_clean_begin"
    end_label = f"{span_id}_clean_end"
    start = marks[start_label]
    end = marks[end_label]
    if end <= start + 0.50:
        raise PrepareError(
            f"clean span {start_label}..{end_label} is too short: "
            f"{start:.3f}..{end:.3f}"
        )
    return start, end, start_label, end_label


def _set_video(
    chapter: dict[str, Any],
    bundle: dict[str, Any],
    *,
    capture_id: str,
    label: str,
    zh_status: str,
    en_status: str,
    shot: str,
    clean_span: str,
) -> None:
    _clear_visual(chapter)
    start, end, start_label, end_label = _clean_span_window(bundle, clean_span)
    chapter["type"] = "video_clip"
    chapter["material_status"] = "captured"
    chapter["status"] = {
        "zh": zh_status,
        "en": en_status,
        "classification": "clean-real-character-capture",
    }
    chapter["source"] = _file_record(
        bundle["raw_path"],
        f"{label}; GREEN clean-gated real-CK3 raw MKV; loading and test UI excluded",
    )
    chapter["evidence_sources"] = _common_evidence(bundle)
    chapter["start_seconds"] = start
    chapter["end_seconds"] = end
    chapter["capture"] = {
        "id": capture_id,
        "exclude_ck3_loading": True,
        "shot": shot,
        "clean_span_id": clean_span,
        "clean_frame_gate": bundle["clean_frame_gates"][clean_span],
        "timeline_start_mark": start_label,
        "timeline_end_mark": end_label,
    }


def project_manifest(
    *, artifact_root: Path, base_manifest: Path = DEFAULT_BASE_MANIFEST
) -> tuple[dict[str, Any], dict[str, Any]]:
    bundle = _capture_bundle(artifact_root)
    base_manifest = base_manifest.expanduser().resolve()
    base = _read_object(base_manifest, "base promo manifest")
    # Run the normal loader first so this projection never hides a broken
    # narration/topic/subtitle contract in the checked-in authoring manifest.
    promo.load_manifest(base_manifest)
    payload = copy.deepcopy(base)
    chapters = payload.get("chapters")
    if not isinstance(chapters, list):
        raise PrepareError("base manifest chapters must be an array")
    by_id = {
        chapter.get("id"): chapter
        for chapter in chapters
        if isinstance(chapter, dict) and isinstance(chapter.get("id"), str)
    }
    expected_ids = {
        "00-cold-open",
        "01-who-rates-whom",
        "02-okr-kpi",
        "03-forced-distribution",
        "04-calibration",
        "05-peer-review-politics",
        "06-jingcha",
        "07-scoreboard-receipt",
        "08-money-and-grade",
        "09-pip-bottom",
        "10-promotion-hc",
        "11-credit-and-dependencies",
        "12-appeal",
        "13-361-policy-cards",
        "14-core-loop",
        "15-honest-boundary",
        "16-finale",
    }
    if set(by_id) != expected_ids:
        raise PrepareError("base promo chapter set changed; review the release projection")

    payload["project_status"] = "captured_release_candidate"
    payload["release_manifest_provenance"] = {
        "schema_version": 1,
        "generator": "mod_zhongguo_style/tools/prepare_promo_release_manifest.py",
        "capture_artifact_root": str(bundle["artifact_root"]),
        "capture_result": "GREEN",
        "base_manifest": _file_record(base_manifest, "Checked-in promo authoring manifest"),
        "capture_report": _file_record(bundle["report_path"], "GREEN promo acceptance report"),
        "capture_timeline": _file_record(bundle["timeline_path"], "Capture timeline and clip marks"),
        "evidence_index": _file_record(bundle["index_path"], "Append-only evidence index"),
        "raw_capture": _file_record(bundle["raw_path"], "Preserved real-CK3 raw MKV"),
        "policy_card_ids": list(POLICY_IDS),
        "clean_span_ids": list(CLEAN_SPAN_IDS),
        "clean_frame_gates": [
            bundle["clean_frame_gates"][span_id] for span_id in CLEAN_SPAN_IDS
        ],
        "real_character_provenance": bundle["real_character_provenance"],
        "generated_boundary_chapters": [
            "01-who-rates-whom",
            "09-pip-bottom",
            "14-core-loop",
            "15-honest-boundary",
        ],
        "loading_exclusion": "raw recording began after gameplay HUD; every clip uses only its exact *_clean_begin/*_clean_end span",
    }

    opening = by_id["00-cold-open"]
    opening["status"] = {
        "zh": "正式候选开场卡",
        "en": "CAPTURED RELEASE CANDIDATE · OPENING",
        "classification": "captured-release-generated",
    }

    _set_boundary(
        by_id["01-who-rates-whom"],
        bundle,
        zh_status="生成证据边界卡：层级未单独录屏",
        en_status="GENERATED EVIDENCE/BOUNDARY · HIERARCHY NOT SEPARATELY RECORDED",
        body_zh=["实机报告确认公爵及以上入口", "伯爵、男爵边界不伪装成独立实录"],
        body_en=["GREEN report binds the duke-or-higher entry", "Count/baron boundary is not presented as a separate live shot"],
    )
    _set_video(
        by_id["02-okr-kpi"],
        bundle,
        capture_id="CAP-RELEASE-POLICY-001",
        label="clean policy card #001",
        zh_status="干净实机政策卡 #001：不冒充独立 OKR 面板",
        en_status="CLEAN POLICY #001 · NO STANDALONE OKR UI CLAIM",
        shot="同一 GREEN run 的 #001 KPI 分项证据单；只展示真实 A/B/C 政策卡。",
        clean_span="policy_card_001",
    )
    _set_video(
        by_id["03-forced-distribution"],
        bundle,
        capture_id="CAP-RELEASE-MANAGED-SCOREBOARD",
        label="clean managed-scoreboard excerpt",
        zh_status="干净实机：新人保护考核榜",
        en_status="CLEAN CAPTURE · NEWCOMER-PROTECTED SCOREBOARD",
        shot="只使用 managed scoreboard 的独立干净区间；7/16/0 明示为新人保护样本。",
        clean_span="managed_scoreboard",
    )
    _set_video(
        by_id["04-calibration"],
        bundle,
        capture_id="CAP-RELEASE-CALIBRATION",
        label="clean calibration excerpt",
        zh_status="干净实机：真实校准会三选项",
        en_status="CLEAN CAPTURE · THREE REAL CALIBRATION CHOICES",
        shot="同一 GREEN run 的校准会连续片段；不声称存在命名档案或任意点名器。",
        clean_span="calibration",
    )
    _set_video(
        by_id["05-peer-review-politics"],
        bundle,
        capture_id="CAP-RELEASE-POLICY-007",
        label="clean policy card #007",
        zh_status="干净实机政策卡 #007：同侪互动未单独录屏",
        en_status="CLEAN POLICY #007 · PEER INTERACTION NOT SEPARATELY RECORDED",
        shot="同一 GREEN run 的 #007 背靠背 360 邀评政策卡；不冒充举荐/攻讦互动录像。",
        clean_span="policy_card_007",
    )

    jingcha = by_id["06-jingcha"]
    jingcha_cues = jingcha.get("cues")
    if not isinstance(jingcha_cues, list) or len(jingcha_cues) != 3:
        raise PrepareError("06-jingcha must retain exactly three authoring cues")
    planner_chapter = copy.deepcopy(jingcha)
    jingcha["cues"] = [copy.deepcopy(jingcha_cues[0])]
    _set_video(
        jingcha,
        bundle,
        capture_id="CAP-RELEASE-JINGCHA-MANDATE",
        label="clean Jingcha mandate excerpt",
        zh_status="干净实机：半强制京察弹窗",
        en_status="CLEAN CAPTURE · SEMI-MANDATORY JINGCHA",
        shot="只使用京察发令弹窗的独立干净区间，不跨越测试决议操作。",
        clean_span="jingcha_mandate",
    )
    planner_chapter["id"] = "06b-free-jingcha-planner"
    planner_chapter["title_zh"] = "京察规划：活动免费，拒办理由有明确上司"
    planner_chapter["title_en"] = "JINGCHA PLANNER: FREE EVENT, ACCOUNTABLE REFUSAL"
    planner_chapter["cues"] = [copy.deepcopy(cue) for cue in jingcha_cues[1:]]
    _set_video(
        planner_chapter,
        bundle,
        capture_id="CAP-RELEASE-JINGCHA-PLANNER",
        label="clean free-Jingcha planner excerpt",
        zh_status="干净实机：免费举办与拒办入口",
        en_status="CLEAN CAPTURE · FREE PLANNER AND REFUSAL ENTRY",
        shot="只使用免费京察规划器的独立干净区间，不复用打开测试决议抽屉的动作。",
        clean_span="free_jingcha_planner",
    )
    jingcha_index = chapters.index(jingcha)
    chapters.insert(jingcha_index + 1, planner_chapter)

    _set_video(
        by_id["07-scoreboard-receipt"],
        bundle,
        capture_id="CAP-RELEASE-RECEIVED-SCOREBOARD",
        label="clean received-scoreboard excerpt",
        zh_status="干净实机：本人所属考核单元与 3.25",
        en_status="CLEAN CAPTURE · RECEIVED BOARD WITH 3.25",
        shot="同一 GREEN run 的本人所属考核单元；管理者榜已在前章展示。",
        clean_span="received_scoreboard_with_325",
    )
    _set_video(
        by_id["08-money-and-grade"],
        bundle,
        capture_id="CAP-RELEASE-SUPERIOR-325",
        label="clean superior-assigned 3.25 excerpt",
        zh_status="干净实机：上司 3.25 告身与四重处分",
        en_status="CLEAN CAPTURE · SUPERIOR 3.25 AND FOURFOLD CONSEQUENCE",
        shot="同一 GREEN run 的上司 3.25 告身；正式重录画面使用四重精确文案，报告绑定罚没与退款断言。",
        clean_span="superior_assigned_325",
    )
    _set_boundary(
        by_id["09-pip-bottom"],
        bundle,
        zh_status="生成证据边界卡：PIP/末位未独立录屏",
        en_status="GENERATED EVIDENCE/BOUNDARY · PIP/BOTTOM NOT SEPARATELY RECORDED",
        body_zh=["3.25 告身已实录", "一年 PIP 与连续末位规则不伪装成现场镜头"],
        body_en=["The 3.25 receipt is captured", "One-year PIP and repeat-bottom rules are not impersonated as live footage"],
    )

    promotion_hc = by_id["10-promotion-hc"]
    original_cues = promotion_hc.get("cues")
    if not isinstance(original_cues, list) or len(original_cues) != 2:
        raise PrepareError("10-promotion-hc must retain exactly two authoring cues")
    hc_chapter = copy.deepcopy(promotion_hc)
    promotion_hc["cues"] = [copy.deepcopy(original_cues[0])]
    promotion_hc["topics"] = ["promotion_packet"]
    _set_video(
        promotion_hc,
        bundle,
        capture_id="CAP-RELEASE-POLICY-020",
        label="clean policy card #020",
        zh_status="干净实机政策卡 #020：晋升通道未单独录屏",
        en_status="CLEAN POLICY #020 · PROMOTION TRACK NOT SEPARATELY RECORDED",
        shot="同一 GREEN run 的 #020 晋升包与跨部门答辩政策卡。",
        clean_span="policy_card_020",
    )
    hc_chapter["id"] = "10b-hc-policy-022"
    hc_chapter["title_zh"] = "HC：编制不是许愿池，是压力账"
    hc_chapter["title_en"] = "HEADCOUNT: NOT A WISH ENGINE, A PRESSURE LEDGER"
    hc_chapter["cues"] = [copy.deepcopy(original_cues[1])]
    hc_chapter["topics"] = ["hc"]
    _set_video(
        hc_chapter,
        bundle,
        capture_id="CAP-RELEASE-POLICY-022",
        label="clean policy card #022",
        zh_status="干净实机政策卡 #022：不冒充招聘模拟器",
        en_status="CLEAN POLICY #022 · NO STANDALONE HIRING SIM CLAIM",
        shot="同一 GREEN run 的 #022 软 HC / 编制预算政策卡。",
        clean_span="policy_card_022",
    )
    promotion_index = chapters.index(promotion_hc)
    chapters.insert(promotion_index + 1, hc_chapter)

    credit_chapter = by_id["11-credit-and-dependencies"]
    credit_cues = credit_chapter.get("cues")
    if not isinstance(credit_cues, list) or len(credit_cues) != 2:
        raise PrepareError(
            "11-credit-and-dependencies must retain exactly two authoring cues"
        )
    cockpit_chapter = copy.deepcopy(credit_chapter)
    credit_chapter["cues"] = [copy.deepcopy(credit_cues[0])]
    _set_video(
        credit_chapter,
        bundle,
        capture_id="CAP-RELEASE-POLICY-026",
        label="clean policy card #026",
        zh_status="干净实机政策卡 #026：不冒充项目仲裁器",
        en_status="CLEAN POLICY #026 · NO PROJECT ARBITRATION UI CLAIM",
        shot="同一 GREEN run 的 #026 真实贡献 / 上司可见度双账政策卡。",
        clean_span="policy_card_026",
    )
    cockpit_chapter["id"] = "11b-policy-cockpit"
    cockpit_chapter["title_zh"] = "制度驾驶舱：账本会说话，但不会替你编项目"
    cockpit_chapter["title_en"] = "POLICY COCKPIT: LEDGERS SPEAK, PROJECTS ARE NOT INVENTED"
    cockpit_chapter["cues"] = [copy.deepcopy(credit_cues[1])]
    _set_video(
        cockpit_chapter,
        bundle,
        capture_id="CAP-RELEASE-POLICY-COCKPIT",
        label="clean policy-cockpit excerpt",
        zh_status="干净实机：制度驾驶舱与组织账",
        en_status="CLEAN CAPTURE · POLICY COCKPIT AND ORGANIZATION LEDGERS",
        shot="只使用制度驾驶舱的独立干净区间；不跨越测试决议或事件清理动作。",
        clean_span="policy_cockpit",
    )
    credit_index = chapters.index(credit_chapter)
    chapters.insert(credit_index + 1, cockpit_chapter)

    _set_video(
        by_id["12-appeal"],
        bundle,
        capture_id="CAP-RELEASE-APPEAL-ENTRY",
        label="clean 3.25 receipt with appeal entry",
        zh_status="干净实机告身：申诉入口；退款由同 run 报告绑定",
        en_status="CLEAN RECEIPT · REFUND BOUND BY SAME-RUN REPORT",
        shot="同一 GREEN run 的 3.25 告身与申诉入口；不把报告断言伪装成连续退款录像。",
        clean_span="superior_assigned_325",
    )
    _set_video(
        by_id["13-361-policy-cards"],
        bundle,
        capture_id="CAP-RELEASE-POLICY-361",
        label="clean policy card #361",
        zh_status="干净实机政策卡 #361：六张样卡均绑定同一 run",
        en_status="CLEAN POLICY #361 · SIX CAPTURED CARDS, ONE GREEN RUN",
        shot="同一 GREEN run 的 #361 绩效宪章；其余样卡分别出现在 #001/#007/#020/#022/#026 章节。",
        clean_span="policy_card_361",
    )
    _set_boundary(
        by_id["14-core-loop"],
        bundle,
        zh_status="生成证据边界卡：核心循环不跨测试操作拼接",
        en_status="GENERATED EVIDENCE/BOUNDARY · NO CROSS-FIXTURE CORE-LOOP CLIP",
        body_zh=[
            "校准、榜单、京察、告身各有独立干净镜头",
            "同 run 报告绑定机制闭环；画面不跨越测试决议操作",
        ],
        body_en=[
            "Calibration, boards, Jingcha and receipt each use a clean span",
            "The same-run report binds the loop; no clip crosses fixture operations",
        ],
    )

    boundary = by_id["15-honest-boundary"]
    boundary["status"] = {
        "zh": "正式候选证据边界",
        "en": "RELEASE-CANDIDATE EVIDENCE BOUNDARY",
        "classification": "generated-evidence-boundary",
    }
    boundary["body_zh"] = [
        "零占位不等于每项都有独立实录",
        "未单拍章节明确显示 GENERATED EVIDENCE/BOUNDARY",
        "连续实机与六张政策卡绑定同一 GREEN run",
    ]
    boundary["body_en"] = [
        "Zero placeholders does not mean every claim has a separate live shot",
        "Unrecorded chapters are explicit GENERATED EVIDENCE/BOUNDARY cards",
        "Continuous gameplay and six policy cards bind to one GREEN run",
    ]
    # The draft wording says this is a placeholder animatic.  Keep its joke and
    # bilingual cadence while making the release candidate factually correct.
    boundary["cues"][0] = {
        "zh": "这是可调整的脚本和证据分镜。没单独实录的就明确写边界卡，漂亮卡片不冒充 CK3 现场。",
        "en": "This remains an editable evidence cut. Anything not separately recorded is an explicit boundary card; a polished card never impersonates live CK3.",
    }
    boundary["evidence_sources"] = _common_evidence(bundle)

    finale = by_id["16-finale"]
    finale["status"] = {
        "zh": "正式候选结尾卡",
        "en": "CAPTURED RELEASE CANDIDATE · FINALE",
        "classification": "captured-release-generated",
    }

    # Every concrete source in the external manifest is absolute and immutable.
    # The normal loader verifies each declared byte count and SHA before output.
    provenance = {
        "schema_version": 1,
        "kind": "zg361_promo_release_manifest_projection",
        "generator": str(Path(__file__).resolve()),
        "base_manifest": _file_record(base_manifest, "Checked-in promo authoring manifest"),
        "capture_artifact_root": str(bundle["artifact_root"]),
        "capture_result": "GREEN",
        "capture_report": _file_record(bundle["report_path"], "GREEN promo acceptance report"),
        "capture_timeline": _file_record(bundle["timeline_path"], "Capture timeline and clip marks"),
        "evidence_index": _file_record(bundle["index_path"], "Append-only evidence index"),
        "raw_capture": _file_record(bundle["raw_path"], "Preserved real-CK3 raw MKV"),
        "policy_stills": {
            f"{mechanism_id:03d}": _file_record(
                bundle["policy_paths"][mechanism_id],
                f"GREEN policy card #{mechanism_id:03d}",
            )
            for mechanism_id in POLICY_IDS
        },
        "policy_card_ids": list(POLICY_IDS),
        "clean_span_ids": list(CLEAN_SPAN_IDS),
        "clean_frame_gates": [
            bundle["clean_frame_gates"][span_id] for span_id in CLEAN_SPAN_IDS
        ],
        "real_character_provenance": bundle["real_character_provenance"],
        "generated_boundary_chapters": [
            "01-who-rates-whom",
            "09-pip-bottom",
            "14-core-loop",
            "15-honest-boundary",
        ],
        "source_files_modified": False,
    }
    return payload, provenance


def _serialized(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def write_projection(
    *,
    artifact_root: Path,
    output: Path,
    base_manifest: Path = DEFAULT_BASE_MANIFEST,
) -> tuple[Path, Path]:
    output = output.expanduser().resolve()
    try:
        output.relative_to(REPOSITORY_ROOT.resolve())
    except ValueError:
        pass
    else:
        raise PrepareError("release manifest output must be outside the repository")
    provenance_path = output.with_name(f"{output.stem}.provenance.json")
    if output.exists() or provenance_path.exists():
        existing = output if output.exists() else provenance_path
        raise PrepareError(f"refusing to overwrite preserved promo output: {existing}")

    payload, provenance = project_manifest(
        artifact_root=artifact_root, base_manifest=base_manifest
    )
    manifest_bytes = _serialized(payload)
    manifest_sha = hashlib.sha256(manifest_bytes).hexdigest().upper()
    provenance["output_manifest"] = {
        "path": str(output),
        "bytes": len(manifest_bytes),
        "sha256": manifest_sha,
    }

    # Exercise the real manifest loader, including declared source hashes,
    # before committing append-only output names.
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="zg361-promo-manifest-check-") as temporary:
        check_path = Path(temporary) / "captured-release-manifest.json"
        check_path.write_bytes(manifest_bytes)
        checked, _chapters = promo.load_manifest(check_path)
        if checked.get("project_status") != "captured_release_candidate":
            raise PrepareError("projected manifest lost release-candidate status")
        if checked.get("_placeholder_count") != 0:
            raise PrepareError("projected manifest still contains placeholders")

    with output.open("xb") as handle:
        handle.write(manifest_bytes)
    with provenance_path.open("xb") as handle:
        handle.write(_serialized(provenance))
    return output, provenance_path


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--artifact-root", type=Path, required=True)
    result.add_argument("--output", type=Path, required=True)
    result.add_argument(
        "--base-manifest", type=Path, default=DEFAULT_BASE_MANIFEST
    )
    return result


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    try:
        output, provenance = write_projection(
            artifact_root=arguments.artifact_root,
            output=arguments.output,
            base_manifest=arguments.base_manifest,
        )
    except (PrepareError, promo.PromoError) as exc:
        print(f"RED: {exc}", file=sys.stderr)
        return 2
    print(f"GREEN: captured release manifest: {output}")
    print(f"GREEN: immutable projection provenance: {provenance}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
