"""Fail-closed Episode 2 clip edit and offline, unsigned reel candidate renderer.

No CK3, recording, TTS, publication, production declaration or human approval is
created here. ``check-shape`` is a light read-only authoring check. ``build``
requires real adapter-verified spans, an existing 1x human raw review and exact
source bytes; every media output goes into one new external append-only attempt.
The output is deliberately *not* a chapter-reel.v1 production receipt. A human
must review the actual rendered reels and visible labels before that receipt.
"""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from xar_promo.adapters.ck3 import load_capture_bundle

from .episode_two_pts_contract import validate_pts_span
from .assemble_episode_two import _installed_wheel_digest
from .episode_two_second_half import (
    CARD_REPLAYS, CHAPTER_CARDS, CHAPTER_IDS, FORMAL_CARD_INDEX_SHA,
    FORMAL_CARD_SHA, _card_replays, card_filename,
)


SCHEMA = "ck3-war-ai.episode02.reel-edit.v1"
TARGET_FRAMES = dict(zip(CHAPTER_IDS, (2700, 10200, 12000, 15450, 10500, 2850)))
FPS = 30
HEX = re.compile(r"[0-9A-Fa-f]{64}\Z")
SEGMENT_ID = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,79}\Z")
TARGET_WIDTH, TARGET_HEIGHT = 2560, 1440


def _read(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _identity(path: Path) -> dict:
    return {"bytes": path.stat().st_size, "sha256": _sha(path)}


def _read_bound_json(path: Path) -> tuple[dict, dict]:
    """Parse and hash the same bytes used for an undeclared bundle source."""
    path = path.resolve(strict=True)
    payload = path.read_bytes()
    data = json.loads(payload)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data, {"source": str(path), "bytes": len(payload),
                  "sha256": hashlib.sha256(payload).hexdigest().upper()}


def _binding(row: object, label: str, *, verify_bytes: bool = True) -> Path:
    if (not isinstance(row, dict) or not isinstance(row.get("source"), str)
            or not isinstance(row.get("sha256"), str) or HEX.fullmatch(row["sha256"]) is None
            or type(row.get("bytes")) is not int or row["bytes"] < 1):
        raise ValueError(f"{label} needs absolute source, positive bytes and SHA-256")
    path = Path(row["source"])
    if not path.is_absolute():
        raise ValueError(f"{label} source must be absolute")
    path = path.resolve(strict=True)
    if path.stat().st_size != row["bytes"]:
        raise ValueError(f"{label} byte length differs")
    if verify_bytes and _sha(path) != row["sha256"].upper():
        raise ValueError(f"{label} SHA-256 differs")
    return path


def _seconds(value: object, label: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{label} needs finite seconds") from exc
    if not result.is_finite() or result < 0:
        raise ValueError(f"{label} needs nonnegative finite seconds")
    return result


def _label(value: object, required: str, label: str) -> str:
    if (not isinstance(value, str) or required not in value or not value.strip()
            or len(value) > 128 or any(char in value for char in "{}\\\r\n")):
        raise ValueError(f"{label} must visibly name its source without ASS control characters")
    return value


def _capture_frame_budget(begin: Decimal, end: Decimal, frames: int, sid: str) -> None:
    """The final 30 fps frame must land on the inclusive reviewed end PTS."""
    source_span = end - begin
    last_output_pts = Decimal(frames - 1) / FPS
    if (source_span <= 0 or frames < 2
            or abs(last_output_pts - source_span) > Decimal("0.001")):
        raise ValueError(f"{sid} frame budget differs from its full source PTS interval")


def check_shape(spec: dict) -> dict:
    """Small, read-only structural check; never upgrades originals to GREEN."""
    if (spec.get("schema") != SCHEMA
            or spec.get("status") != "reviewed-clean-spans-edit-planned"
            or spec.get("human_signoff") != "not-provided"
            or spec.get("synthetic") is not False):
        raise ValueError("A real, unsigned Episode 2 reel edit is required")
    for key in ("project_config", "narration_script", "subtitle_fragments", "card_index"):
        row = spec.get(key)
        if (not isinstance(row, dict) or not isinstance(row.get("source"), str)
                or not Path(row["source"]).is_absolute() or type(row.get("bytes")) is not int
                or row["bytes"] < 1 or not isinstance(row.get("sha256"), str)
                or HEX.fullmatch(row["sha256"]) is None):
            raise ValueError(f"Missing exact {key} identity")
    chapters = spec.get("chapters")
    if not isinstance(chapters, list) or [row.get("id") for row in chapters] != list(CHAPTER_IDS):
        raise ValueError("All six chapters are required in ProjectConfig order")
    ids: set[str] = set()
    raw_uses: dict[str, tuple[str, str, Decimal, Decimal]] = {}
    for chapter in chapters:
        chapter_id = chapter["id"]
        if chapter.get("target_frames") != TARGET_FRAMES[chapter_id]:
            raise ValueError(f"{chapter_id} must use the frozen 29:50 frame budget")
        segments = chapter.get("segments")
        if not isinstance(segments, list) or not segments:
            raise ValueError(f"{chapter_id} has no visual edit")
        if sum(row.get("frames", 0) for row in segments if type(row.get("frames")) is int) != TARGET_FRAMES[chapter_id]:
            raise ValueError(f"{chapter_id} segment frames do not cover its chapter")
        cards: list[str] = []
        capture_count = 0
        for row in segments:
            sid, frames, kind = row.get("id"), row.get("frames"), row.get("kind")
            if (not isinstance(sid, str) or SEGMENT_ID.fullmatch(sid) is None
                    or sid in ids or type(frames) is not int or frames < 1):
                raise ValueError(f"{chapter_id} has a duplicate/invalid segment or frame count")
            ids.add(sid)
            if kind == "capture":
                capture_count += 1
                attempt = row.get("attempt_id")
                if (not isinstance(attempt, str) or not attempt or attempt.startswith("SYNTHETIC-")
                        or not isinstance(row.get("span_id"), str) or not row["span_id"]
                        or not isinstance(row.get("bundle_root"), str)
                        or not Path(row["bundle_root"]).is_absolute()):
                    raise ValueError(f"{sid} needs a real adapter attempt and span")
                begin, end = _seconds(row.get("begin_pts_seconds"), "clip begin"), _seconds(row.get("end_pts_seconds"), "clip end")
                _capture_frame_budget(begin, end, frames, sid)
                _label(row.get("source_label"), attempt, sid)
                for key in ("raw", "clean_span_audit", "human_review", "pts_probe",
                            "recorder_final", "cold_load_save", "cold_load_receipt", "control"):
                    if not isinstance(row.get(key), dict):
                        raise ValueError(f"{sid} lacks {key} identity")
                if (type(row.get("raw_width")) is not int or type(row.get("raw_height")) is not int
                        or min(row["raw_width"], row["raw_height"]) < 1):
                    raise ValueError(f"{sid} lacks original capture dimensions")
                raw_sha = str(row["raw"].get("sha256", "")).upper()
                overlap = [prior for prior in raw_uses.values()
                           if prior[1] == raw_sha and begin <= prior[3] and end >= prior[2]]
                recap = row.get("recap_of")
                if recap is not None:
                    prior = raw_uses.get(recap)
                    if (chapter_id != "closing" or prior is None or prior[1] != raw_sha
                            or begin < prior[2] or end > prior[3] or "回顾" not in row["source_label"]):
                        raise ValueError(f"{sid} recap does not bind an earlier same-raw interval")
                if overlap and (recap is None or any(prior[0] != recap for prior in overlap)):
                    raise ValueError(f"{sid} silently repeats original game frames")
                raw_uses[sid] = (sid, raw_sha, begin, end)
            elif kind == "still":
                card_id = row.get("card_id")
                if card_id is not None:
                    if card_id not in CARD_REPLAYS:
                        raise ValueError(f"{sid} has unknown formal card")
                    cards.append(card_id)
                    _label(row.get("source_label"), card_id, sid)
                else:
                    _label(row.get("source_label"), "E2", sid)
                for key in ("image", "origin", "render_receipt"):
                    if not isinstance(row.get(key), dict):
                        raise ValueError(f"{sid} lacks its exact still source")
            else:
                raise ValueError(f"{sid} has unsupported visual kind")
        if capture_count < 1 or sorted(cards) != sorted(CHAPTER_CARDS.get(chapter_id, ())):
            raise ValueError(f"{chapter_id} needs real capture and exactly its formal cards")
    return {"schema": "ck3-war-ai.episode02.reel-edit-shape-check.v1",
            "status": "STRUCTURE_ONLY_UNVERIFIED_ORIGINALS", "chapter_ids": list(CHAPTER_IDS),
            "chapter_frames": TARGET_FRAMES, "total_frames": sum(TARGET_FRAMES.values()),
            "human_signoff": "not-provided"}


def _exact_pts(probe: Path, begin: Decimal, end: Decimal,
               width: int, height: int) -> None:
    data = _read(probe)
    video = [row for row in data.get("streams", []) if row.get("codec_type") == "video"]
    if (len(video) != 1 or video[0].get("width") != width
            or video[0].get("height") != height):
        raise ValueError("Clip source probe needs one video stream")
    stream_id = video[0]["index"]
    seen = set()
    for frame in data.get("frames", []):
        if frame.get("stream_index") == stream_id:
            seen.add(Decimal(str(frame.get("best_effort_timestamp_time", frame.get("pts_time")))))
    if begin not in seen or end not in seen:
        raise ValueError("Clip in/out must be exact source frame PTS, not wall-clock marks")


def _capture_attempt_root(row: dict, source_manifest: dict,
                          expected_root: Path | None = None) -> Path:
    sid = row["id"]
    declared = Path(source_manifest.get("attempt_root", ""))
    if not declared.is_absolute():
        raise ValueError(f"{sid} capture attempt root must be absolute")
    original_attempt = declared.resolve(strict=True)
    if (original_attempt.name != row["attempt_id"]
            or (expected_root is not None and original_attempt != expected_root)):
        raise ValueError(f"{sid} capture attempt root differs from its pinned same-run card")
    return original_attempt


def _verify_capture(row: dict, expected_attempt_root: Path | None = None) -> tuple[Path, object, dict]:
    sid = row["id"]
    root = Path(row["bundle_root"]).resolve(strict=True)
    clean_path = _binding(row["clean_span_audit"], f"{sid} clean audit")
    review_path = _binding(row["human_review"], f"{sid} human review")
    if review_path != root / "source/human-review.json":
        raise ValueError(f"{sid} human review is not the adapter bundle original")
    clean, review = _read(clean_path), _read(review_path)
    if (clean.get("schema") != "ck3-war-ai.episode02.clean-span-audit.v1"
            or clean.get("result") != "GREEN" or clean.get("span_id") != row["span_id"]
            or clean.get("attempt_id") != row["attempt_id"]
            or Path(clean.get("capture_artifact_root", "")).resolve() != root
            or review.get("schema") != "xar.war-promo.exact-span-human-review/v1"
            or review.get("reviewer", {}).get("kind") != "human"
            or review.get("review_scope") != "full_raw_1x_and_exact_span_endpoints"
            or review.get("human_1x_full_raw_review_performed") is not True):
        raise ValueError(f"{sid} has no same-attempt human-reviewed GREEN span")
    reviewed = [x for x in review.get("spans", []) if x.get("span_id") == row["span_id"]]
    if (len(reviewed) != 1 or reviewed[0].get("continuous_visual_review_performed") is not True
            or reviewed[0].get("source_identity_visible_and_checked") is not True
            or reviewed[0].get("no_foreign_overlay") is not True):
        raise ValueError(f"{sid} selected span lacks 1x visual review")
    bundle = load_capture_bundle(root, required_span_ids=[row["span_id"]])
    span = bundle.clean_span(row["span_id"])
    if (clean.get("raw_video_sha256", "").upper() != bundle.raw_capture.sha256
            or clean.get("raw_video_bytes") != bundle.raw_capture.bytes
            or clean.get("report_sha256", "").upper() != bundle.report.sha256
            or clean.get("timeline_sha256", "").upper() != bundle.timeline.sha256
            or clean.get("evidence_index_sha256", "").upper() != bundle.evidence_index.sha256
            or clean.get("begin_seconds") != span.begin_seconds
            or clean.get("end_seconds") != span.end_seconds):
        raise ValueError(f"{sid} clean audit differs from adapter evidence")
    raw = _binding(row["raw"], f"{sid} raw", verify_bytes=False)
    if (raw != bundle.raw_capture.path or row["raw"]["sha256"].upper() != bundle.raw_capture.sha256
            or row["raw"]["bytes"] != bundle.raw_capture.bytes):
        raise ValueError(f"{sid} raw must be the adapter-verified copy")
    source_manifest, source_manifest_binding = _read_bound_json(root / "source/source-manifest.json")
    original_attempt = _capture_attempt_root(row, source_manifest, expected_attempt_root)
    if source_manifest.get("status") != "PENDING_CLEAN_REVIEW":
        raise ValueError(f"{sid} clean bundle belongs to another capture attempt")
    begin, end = _seconds(row["begin_pts_seconds"], "clip begin"), _seconds(row["end_pts_seconds"], "clip end")
    if (begin < Decimal(str(span.begin_seconds)) or end > Decimal(str(span.end_seconds))
            or Decimal(str(reviewed[0]["begin_pts_seconds"])) != Decimal(str(span.begin_seconds))
            or Decimal(str(reviewed[0]["end_pts_seconds"])) != Decimal(str(span.end_seconds))):
        raise ValueError(f"{sid} clip extends beyond its human-reviewed clean span")
    probe = _binding(row["pts_probe"], f"{sid} full frame probe")
    final = _binding(row["recorder_final"], f"{sid} recorder final")
    _exact_pts(probe, begin, end, row["raw_width"], row["raw_height"])
    validate_pts_span(raw, probe, final, float(begin), float(end),
                      verified_raw_identity={"bytes": bundle.raw_capture.bytes,
                                             "sha256": bundle.raw_capture.sha256})
    save = _binding(row["cold_load_save"], f"{sid} cold-load save")
    save_receipt = _binding(row["cold_load_receipt"], f"{sid} cold-load receipt")
    control = _binding(row["control"], f"{sid} native control")
    original_recorder = Path(source_manifest["recorder_root"]).resolve(strict=True)
    intent, intent_binding = _read_bound_json(
        root / "source" / original_recorder.name / "recorder-intent.json")
    for key, path, declared in (("source_save", save, row["cold_load_save"]),
                                ("source_receipt", save_receipt, row["cold_load_receipt"])):
        original = intent.get(key, {})
        if (Path(original.get("path", "")).resolve() != path
                or original.get("bytes") != declared["bytes"]
                or str(original.get("sha256", "")).upper() != declared["sha256"].upper()):
            raise ValueError(f"{sid} {key} is not the actual recorder cold-load source")
    if (not control.is_relative_to(original_attempt)
            or not any(Path(item["path"]) == control
                       and item["bytes"] == row["control"]["bytes"]
                       and item["sha256"].upper() == row["control"]["sha256"].upper()
                       for item in source_manifest["files"])):
        raise ValueError(f"{sid} native control is not in its capture source inventory")
    return raw, bundle, {"attempt_root": str(original_attempt),
                         "source_manifest": source_manifest_binding,
                         "recorder_intent": intent_binding}


def _verify_still(row: dict, card_rows: dict, index_path: Path) -> Path:
    sid = row["id"]
    image = _binding(row["image"], f"{sid} PNG")
    if image.suffix.lower() != ".png":
        raise ValueError(f"{sid} still must be PNG")
    with image.open("rb") as stream:
        header = stream.read(24)
    if (header[:16] != b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
            or int.from_bytes(header[16:20], "big") != TARGET_WIDTH
            or int.from_bytes(header[20:24], "big") != TARGET_HEIGHT):
        raise ValueError(f"{sid} PNG is not 2560x1440")
    origin = _binding(row["origin"], f"{sid} still origin")
    receipt = _read(_binding(row["render_receipt"], f"{sid} render receipt"))
    if (receipt.get("schema") != "ck3-war-ai.episode02.still-raster.v1"
            or receipt.get("image_sha256", "").upper() != row["image"]["sha256"].upper()
            or receipt.get("source_sha256", "").upper() != row["origin"]["sha256"].upper()
            or receipt.get("width") != TARGET_WIDTH or receipt.get("height") != TARGET_HEIGHT
            or receipt.get("status") != "rasterized-unreviewed"):
        raise ValueError(f"{sid} PNG render receipt is not source-bound")
    card_id = row.get("card_id")
    if card_id:
        card = card_rows[card_id]
        if (origin != index_path.parent / card_filename(card_id)
                or origin.name != card.get("artifact", card_filename(card_id))
                or row["origin"]["sha256"].upper() != FORMAL_CARD_SHA[card_id]):
            raise ValueError(f"{sid} formal card raster differs from indexed SVG")
        replay = card["replay"]
        if replay not in row["source_label"]:
            raise ValueError(f"{sid} card label omits its indexed replay")
        if replay in ("039_040", "020", "070", "036_038"):
            if (replay not in row["source_label"] or "历史研究" not in row["source_label"]
                    or "非当前录制" not in row["source_label"]):
                raise ValueError(f"{sid} historical research card lacks visible scope label")
    return image


def _same_run_card_gate(chapter: dict, index: dict) -> dict[str, Path]:
    captures = [row for row in chapter["segments"] if row["kind"] == "capture"]
    expected_roots: dict[str, Path] = {}
    for card_id in CHAPTER_CARDS.get(chapter["id"], ()):
        card = next(row for row in index["cards"] if row["id"] == card_id)
        replay = card["replay"]
        if replay not in ("A05", "A01"):
            continue
        source = index["replays"][replay]
        expected_root = Path(source["source_preflight"]).parent.parent.resolve(strict=True)
        expected_roots[replay] = expected_root
        expected_attempt = expected_root.name
        expected_save = source["source_save_sha256"].upper()
        if not captures or not all(row["attempt_id"] == expected_attempt
                                   and row["cold_load_save"]["sha256"].upper() == expected_save
                                   for row in captures):
            raise ValueError(f"{card_id} lacks exclusively same-run {replay} raw and cold-load save")
    if len(set(expected_roots.values())) > 1:
        raise ValueError("A chapter's current cards name different source attempt roots")
    return expected_roots


def verify_sources(spec: dict) -> tuple[dict[str, Path], dict[Path, object], dict[str, dict]]:
    """Heavy read-only source audit for a future build, never run on live raw."""
    check_shape(spec)
    config = _binding(spec["project_config"], "ProjectConfig")
    script = _binding(spec["narration_script"], "narration script")
    fragments = _read(_binding(spec["subtitle_fragments"], "subtitle fragments"))
    index_path = _binding(spec["card_index"], "card index")
    if (spec["card_index"]["sha256"].upper() != FORMAL_CARD_INDEX_SHA
            or fragments.get("schema") != "ck3-war-ai.episode02.subtitle-input-fragments.v1"
            or fragments.get("status") != "machine-source-checked-not-human-reviewed"
            or fragments.get("project_config") != _identity(config)
            or fragments.get("narration_script") != _identity(script)):
        raise ValueError("Reel edit lost the frozen formal card/TTS ProjectConfig source")
    config_data, index = _read(config), _read(index_path)
    if ([r.get("id") for r in config_data.get("chapters", [])] != list(CHAPTER_IDS)
            or _card_replays(index) != {r["id"]: r["replay"] for r in index["cards"]}):
        raise ValueError("Reel edit ProjectConfig or card index chapter identity differs")
    card_rows = {row["id"]: row for row in index["cards"]}
    speech = {row["id"]: row["speech_duration_seconds"] for row in fragments["chapters"]}
    if list(speech) != list(CHAPTER_IDS):
        raise ValueError("Six bound TTS speech durations are required")
    bound: dict[str, Path] = {}
    bundles: dict[Path, object] = {}
    source_provenance: dict[str, dict] = {}
    for chapter in spec["chapters"]:
        if TARGET_FRAMES[chapter["id"]] / FPS < speech[chapter["id"]]:
            raise ValueError(f"{chapter['id']} edit is shorter than source narration")
        same_run_roots = _same_run_card_gate(chapter, index)
        expected_root = next(iter(same_run_roots.values()), None)
        for row in chapter["segments"]:
            if row["kind"] == "capture":
                raw, bundle, provenance = _verify_capture(row, expected_root)
                bound[row["id"]] = raw
                bundles[bundle.artifact_root] = bundle
                key = str(bundle.artifact_root)
                if key in source_provenance and source_provenance[key] != provenance:
                    raise ValueError("Capture bundle source provenance changed during initial audit")
                source_provenance[key] = provenance
            else:
                bound[row["id"]] = _verify_still(row, card_rows, index_path)
    # The caller revalidates these bundles again after a future media build.
    return bound, bundles, source_provenance


def _ass_label(text: str, frames: int) -> str:
    # ASS centisecond end may exceed the last video frame by <10 ms, harmless.
    centiseconds = math.ceil(frames * 100 / FPS)
    end = f"{centiseconds // 360000}:{centiseconds // 6000 % 60:02}:{centiseconds // 100 % 60:02}.{centiseconds % 100:02}"
    return ("[Script Info]\nScriptType: v4.00+\nPlayResX: 2560\nPlayResY: 1440\n"
            "[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\n"
            "Style: Source,Microsoft YaHei,34,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,3,1,7,42,42,36,1\n"
            "[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n"
            f"Dialogue: 0,0:00:00.00,{end},Source,,0,0,0,,{text}\n")


def segment_argv(row: dict, source: Path, output: Path, ffmpeg: str) -> list[str]:
    common = [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-n"]
    if row["kind"] == "capture":
        # A declared end PTS names the last reviewed frame. FFmpeg trim's end
        # is exclusive, so advance it just enough to include that exact frame.
        inclusive_end = _seconds(row["end_pts_seconds"], "clip end") + Decimal("0.001")
        vf = (f"trim=start={row['begin_pts_seconds']}:end={inclusive_end},"
              "setpts=PTS-STARTPTS,fps=30,scale=2560:1440:flags=lanczos,"
              "setsar=1,ass=label.ass")
        source_args = ["-i", str(source)]
        frame_limit = []  # Full trimmed interval must encode; _probe checks the actual count.
    else:
        vf = "setsar=1,ass=label.ass"
        source_args = ["-loop", "1", "-framerate", "30", "-i", str(source)]
        frame_limit = ["-frames:v", str(row["frames"])]
    return common + source_args + ["-vf", vf] + frame_limit + ["-an",
                                   "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                                   "-pix_fmt", "yuv420p", "-r", "30", "-threads", "2",
                                   "-movflags", "+faststart", str(output)]


def _run(attempt: Path, name: str, argv: list[str], *, cwd: Path) -> None:
    log = attempt / "commands" / name
    log.mkdir(parents=True, exist_ok=False)
    (log / "argv.json").write_text(json.dumps(argv, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    process: subprocess.Popen | None = None
    returncode: int | None = None
    with (log / "stdout.bin").open("xb") as stdout, (log / "stderr.bin").open("xb") as stderr:
        try:
            process = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.DEVNULL,
                                       stdout=stdout, stderr=stderr)
            returncode = process.wait()
        except BaseException as exc:
            cleanup_error = None
            if process is not None:
                try:
                    if process.poll() is None:
                        process.terminate()
                    try:
                        returncode = process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        returncode = process.wait(timeout=5)
                except Exception as cleanup_exc:
                    cleanup_error = repr(cleanup_exc)
                    returncode = process.poll()
            (log / "execution-error.json").write_text(json.dumps({
                "status": "INTERRUPTED_OR_NOT_STARTED_PRESERVED",
                "exception_type": type(exc).__name__, "error": repr(exc),
                "pid": process.pid if process is not None else None,
                "returncode": returncode, "cleanup_error": cleanup_error,
                "stdout_stderr_streamed_to_files": True,
            }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            raise
        finally:
            (log / "exit-code.txt").write_text(
                f"{returncode if returncode is not None else 'NOT_STARTED'}\n", encoding="ascii")
    if returncode != 0:
        raise RuntimeError(f"{name} failed with exit {returncode}; attempt retained")


def _probe(attempt: Path, name: str, path: Path, ffprobe: str, frames: int) -> dict:
    argv = [ffprobe, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)]
    _run(attempt, f"probe-{name}", argv, cwd=attempt)
    payload = (attempt / "commands" / f"probe-{name}" / "stdout.bin").read_bytes()
    (attempt / "probes" / f"{name}.json").write_bytes(payload)
    data = json.loads(payload)
    video = [row for row in data.get("streams", []) if row.get("codec_type") == "video"]
    if (len(video) != 1 or video[0].get("width") != TARGET_WIDTH
            or video[0].get("height") != TARGET_HEIGHT
            or video[0].get("avg_frame_rate") != "30/1"
            or int(video[0].get("nb_frames", -1)) != frames):
        raise ValueError(f"{name} output lacks exact 2560x1440/30fps/frame count")
    if abs(float(data["format"]["duration"]) - frames / FPS) > (0.5 / FPS + 0.001):
        raise ValueError(f"{name} output duration differs from edit frames")
    return data


def _recheck_nonraw_inputs(spec: dict, source_provenance: dict[str, dict] | None = None) -> None:
    """Catch edits to declared originals during a long render without rehashing GB raw."""
    rows = [spec[key] for key in ("project_config", "narration_script",
                                  "subtitle_fragments", "card_index")]
    for chapter in spec["chapters"]:
        for segment in chapter["segments"]:
            keys = ("clean_span_audit", "human_review", "pts_probe", "recorder_final",
                    "cold_load_save", "cold_load_receipt", "control") if segment["kind"] == "capture" else (
                    "image", "origin", "render_receipt")
            rows.extend(segment[key] for key in keys)
    for bundle in (source_provenance or {}).values():
        rows.extend((bundle["source_manifest"], bundle["recorder_intent"]))
    seen: set[tuple[str, int, str]] = set()
    for row in rows:
        marker = (row["source"], row["bytes"], row["sha256"].upper())
        if marker not in seen:
            _binding(row, "post-render declared source")
            seen.add(marker)


def _resolve_media_tool(command: str) -> tuple[str, dict]:
    found = shutil.which(command)
    if not found:
        raise ValueError(f"Required media tool is unavailable: {command}")
    path = Path(found).resolve(strict=True)
    return str(path), {"source": str(path), **_identity(path)}


def build(spec_path: Path, attempt: Path, *, selected_version: str,
          selected_wheel_sha256: str, ffmpeg: str = "ffmpeg", ffprobe: str = "ffprobe") -> dict:
    spec_path = spec_path.resolve(strict=True)
    plan_bytes = spec_path.read_bytes()
    spec = json.loads(plan_bytes)
    if not isinstance(spec, dict):
        raise ValueError("Reel edit plan must be a JSON object")
    check_shape(spec)
    if not attempt.is_absolute() or attempt.exists() or "'" in str(attempt):
        raise ValueError("A new absolute external attempt directory is required")
    attempt = attempt.resolve()
    if attempt.is_relative_to(Path(__file__).resolve().parents[5]):
        raise ValueError("Reel render attempt must be outside the repository")
    if (importlib.metadata.version("xar-promo-toolchain") != selected_version
            or _installed_wheel_digest() != selected_wheel_sha256.upper()):
        raise ValueError("Selected interpreter differs from the checked official wheel")
    attempt.mkdir(parents=True, exist_ok=False)
    for directory in ("commands", "probes", "segments", "reels"):
        (attempt / directory).mkdir()
    (attempt / "input-plan.json").write_bytes(plan_bytes)
    try:
        sources, bundles, source_provenance = verify_sources(spec)
        ffmpeg, ffmpeg_identity = _resolve_media_tool(ffmpeg)
        ffprobe, ffprobe_identity = _resolve_media_tool(ffprobe)
        _run(attempt, "ffmpeg-version", [ffmpeg, "-version"], cwd=attempt)
        _run(attempt, "ffprobe-version", [ffprobe, "-version"], cwd=attempt)
        (attempt / "verified-inputs.json").write_text(json.dumps({
            "schema": "ck3-war-ai.episode02.reel-edit-input-audit.v1",
            "status": "SOURCE_CHECKED_HUMAN_ATTESTATION_NOT_FILM_REVIEW",
            "input_plan": {"source": str(spec_path), **_identity(spec_path)},
            "source_bindings": {row["id"]: row["raw"] if row["kind"] == "capture" else row["image"]
                                for chapter in spec["chapters"] for row in chapter["segments"]},
            "source_provenance": source_provenance,
            "toolchain_version": selected_version,
            "toolchain_wheel_sha256": selected_wheel_sha256.upper(),
            "ffmpeg": ffmpeg_identity, "ffprobe": ffprobe_identity,
            "human_film_signoff": False,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        reels = []
        for chapter in spec["chapters"]:
            folder = attempt / "segments" / chapter["id"]
            folder.mkdir()
            concat = []
            for number, row in enumerate(chapter["segments"]):
                segment_dir = folder / f"{number:03}-{row['id']}"
                segment_dir.mkdir()
                (segment_dir / "label.ass").write_text(_ass_label(row["source_label"], row["frames"]),
                                                         encoding="utf-8", newline="\n")
                output = segment_dir / "segment.mp4"
                _run(attempt, f"segment-{row['id']}", segment_argv(row, sources[row["id"]], output, ffmpeg),
                     cwd=segment_dir)
                _probe(attempt, f"segment-{row['id']}", output, ffprobe, row["frames"])
                concat.append(f"file '{output.as_posix()}'\n")
            concat_path = folder / "concat.ffconcat"
            concat_path.write_text("ffconcat version 1.0\n" + "".join(concat), encoding="utf-8", newline="\n")
            reel = attempt / "reels" / f"reel-{chapter['id']}.mp4"
            _run(attempt, f"concat-{chapter['id']}", [ffmpeg, "-nostdin", "-hide_banner",
                 "-loglevel", "error", "-n", "-f", "concat", "-safe", "0", "-i", str(concat_path),
                 "-map", "0:v:0", "-an", "-c", "copy", "-movflags", "+faststart", str(reel)],
                 cwd=folder)
            _probe(attempt, f"reel-{chapter['id']}", reel, ffprobe, chapter["target_frames"])
            reels.append({"id": chapter["id"], "path": str(reel), **_identity(reel),
                          "target_frames": chapter["target_frames"], "segments": [r["id"] for r in chapter["segments"]]})
        # Rehash the exact CK3 bundle sources after all media reads, including raw copies.
        for bundle in bundles.values():
            bundle.verify_unchanged()
        _recheck_nonraw_inputs(spec, source_provenance)
        _binding(ffmpeg_identity, "post-render FFmpeg binary")
        _binding(ffprobe_identity, "post-render FFprobe binary")
        if spec_path.read_bytes() != plan_bytes:
            raise ValueError("Reel edit plan changed during render")
        result = {"schema": "ck3-war-ai.episode02.reel-edit-candidates.v1",
                  "status": "ENCODED_PENDING_HUMAN_REEL_AND_LABEL_REVIEW",
                  "production_chapter_reel_receipts_created": False, "film_created": False,
                  "human_film_signoff": False, "publication": "not-performed",
                  "input_plan": {"source": str(spec_path), **_identity(spec_path)},
                  "source_provenance": source_provenance,
                  "reels": reels, "total_target_frames": sum(TARGET_FRAMES.values()),
                  "total_target_seconds": sum(TARGET_FRAMES.values()) / FPS}
        (attempt / "candidate-reels.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                                                      encoding="utf-8", newline="\n")
        return result
    except BaseException as exc:
        (attempt / "failure.json").write_text(json.dumps({"status": "FAILED_PRESERVED",
            "error": repr(exc), "production_reel_receipts_created": False}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8", newline="\n")
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check-shape", "build"))
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--attempt-directory", type=Path)
    parser.add_argument("--selected-version")
    parser.add_argument("--selected-wheel-sha256")
    parser.add_argument("--ffmpeg", default=os.environ.get("WAR_PROMO_FFMPEG", "ffmpeg"))
    parser.add_argument("--ffprobe", default=os.environ.get("WAR_PROMO_FFPROBE", "ffprobe"))
    args = parser.parse_args()
    if args.command == "check-shape":
        result = check_shape(_read(args.spec.resolve(strict=True)))
    else:
        if args.attempt_directory is None:
            parser.error("build requires --attempt-directory")
        if not args.selected_version or not args.selected_wheel_sha256:
            parser.error("build requires --selected-version and --selected-wheel-sha256")
        result = build(args.spec, args.attempt_directory,
                       selected_version=args.selected_version,
                       selected_wheel_sha256=args.selected_wheel_sha256,
                       ffmpeg=args.ffmpeg, ffprobe=args.ffprobe)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
