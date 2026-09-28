"""Bind a finished external recorder, then package explicitly reviewed CK3 spans.

``prepare`` creates an append-only, non-admissible source inventory. ``package``
requires a separate full-speed human review of exact raw PTS endpoints and
creates a new, self-contained bundle for xar-promo's CK3 adapter. Neither
command starts CK3, decodes video, infers screen content, or signs off a film.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import shutil
from typing import Any


SCHEMA = "xar.war-promo.existing-capture-source/v1"
REVIEW_SCHEMA = "xar.war-promo.exact-span-human-review/v1"
SHA = re.compile(r"^[0-9a-fA-F]{64}$")
ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    require(isinstance(value, dict), f"JSON root must be an object: {path}")
    return value


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def record(path: Path) -> dict[str, Any]:
    path = path.resolve(strict=True)
    require(path.is_file(), f"not a file: {path}")
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha(path)}


def verified(reference: Any, *, within: Path | None = None) -> dict[str, Any]:
    require(isinstance(reference, dict), "file reference must be an object")
    require(isinstance(reference.get("path"), str), "file reference path missing")
    path = Path(reference["path"]).resolve(strict=True)
    if within is not None:
        require(path.is_relative_to(within.resolve()), f"evidence escapes source root: {path}")
    require(type(reference.get("bytes")) is int and reference["bytes"] >= 0,
            f"invalid byte count: {path}")
    require(isinstance(reference.get("sha256"), str) and SHA.fullmatch(reference["sha256"]),
            f"invalid SHA-256: {path}")
    actual = record(path)
    require(actual["bytes"] == reference["bytes"] and
            actual["sha256"] == reference["sha256"].upper(),
            f"source byte/SHA mismatch: {path}")
    return actual


def write_new(path: Path, value: dict[str, Any]) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as output:
        json.dump(value, output, ensure_ascii=False, indent=2)
        output.write("\n")
        output.flush()
        os.fsync(output.fileno())


def toolchain_identity(requirements: Path) -> dict[str, str]:
    requirement = requirements.read_text(encoding="utf-8")
    url = re.search(r"https://github\.com/XenoAmess/xar_promo_toolchain/releases/download/"
                    r"(v[0-9.]+)/([^\s\\]+\.whl)", requirement)
    digest = re.search(r"--hash=sha256:([0-9a-fA-F]{64})", requirement)
    require(url is not None and digest is not None, "exact promo wheel pin missing")
    installed = importlib.metadata.version("xar-promo-toolchain")
    require(url.group(1) == f"v{installed}", "installed toolchain differs from wheel pin")
    return {"version": installed, "release_tag": url.group(1),
            "wheel_sha256": digest.group(1).upper(), "wheel_url": url.group(0)}


def decimal_pts(value: Any, label: str) -> Decimal:
    require(isinstance(value, (str, int, float)) and not isinstance(value, bool),
            f"{label} must be a decimal PTS")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"invalid {label}") from exc
    require(result.is_finite() and result >= 0, f"invalid {label}")
    return result


def checked_marks(path: Path, recorder: Path, attempt: Path, elapsed: Decimal) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    require(len(rows) >= 2 and all(isinstance(row, dict) for row in rows), "marks journal missing")
    require(rows[0].get("kind") == "recorder-start" and rows[-1].get("kind") == "recorder-end",
            "marks journal lacks recorder boundaries")
    require(all(type(row.get("monotonic_ns")) is int for row in rows), "invalid mark monotonic clock")
    require(all(a["monotonic_ns"] < b["monotonic_ns"] for a, b in zip(rows, rows[1:])),
            "marks journal is not monotonic")
    refs: dict[str, dict[str, Any]] = {}
    projected = []
    for row in rows[1:-1]:
        approx = decimal_pts(row.get("approx_seconds_from_recorder_start"), "wall-clock mark")
        require(row.get("approx_seconds_are_not_video_pts") is True,
                "mark must explicitly disclaim media PTS")
        require(approx <= elapsed, "wall-clock mark lies after recorder end")
        bound: dict[str, dict[str, Any]] = {}
        for key in ("control", "report", "screenshot"):
            if row.get(key) is not None:
                item = verified(row[key], within=attempt)
                bound[key] = item
                refs[item["path"]] = item
        projected.append({"kind": row.get("kind"), "wall_clock_navigation_seconds": str(approx),
                          "media_pts_seconds": None, "date_raw": row.get("date_raw"),
                          "combat_id": row.get("combat_id"), "war_id": row.get("war_id"),
                          "evidence": bound})
    return projected, list(refs.values())


def prepare(attempt: Path, recorder: Path, output: Path, requirements: Path) -> dict[str, Any]:
    attempt = attempt.resolve(strict=True)
    recorder = recorder.resolve(strict=True)
    require(recorder.parent == attempt, "recorder must be a direct child of capture attempt")
    require(not output.exists() and output.parent.is_dir(), "output must be a new child of an existing directory")
    require(not output.resolve().is_relative_to(attempt), "output must be outside original attempt")
    capture_path = attempt / "ck3-output/capture-report.json"
    capture = read_json(capture_path)
    require(capture.get("result") == "ENVIRONMENT_SESSION_COMPLETE_NO_VIDEO" and
            capture.get("environment_session_complete") is True and
            capture.get("adapter_bundle_validated") is False,
            "original report is not a completed no-video managed session")
    require((capture.get("worker") or {}).get("ok") is True and
            not (capture.get("cleanup_process_inventory") or {}).get("processes"),
            "managed session worker or final process inventory is not clean")
    session_result = read_json(attempt / "ck3-output/session-result.json")
    shutdown = session_result.get("shutdown") or {}
    require(session_result.get("ok") is True and shutdown.get("ok") is True and
            shutdown.get("tree_gone") is True and shutdown.get("cleanup_proven") is True,
            "managed session shutdown is not proven")
    final_path = recorder / "recorder-final.json"
    final = read_json(final_path)
    require(final.get("result") == "ENCODED_UNREVIEWED" and
            final.get("clean_spans_certified") is False and
            final.get("human_review_completed") is False and
            final.get("ffmpeg_exit_code") == 0 and final.get("ffprobe_exit_code") == 0 and
            final.get("video_pts_complete") is True,
            "recorder is not a finished unreviewed encoding")
    raw = verified(final.get("raw"), within=recorder)
    probe = verified(final.get("ffprobe_output"), within=recorder)
    marks = verified(final.get("marks"), within=recorder)
    intent_path = recorder / "recorder-intent.json"
    start_path = recorder / "recorder-start.json"
    end_path = recorder / "recorder-end.json"
    intent, start, end = (read_json(path) for path in (intent_path, start_path, end_path))
    require(Path(intent.get("raw_path", "")).resolve() == Path(raw["path"]), "intent raw differs")
    require(Path(intent.get("session_output", "")).resolve() == (attempt / "ck3-output").resolve(),
            "recorder intent belongs to a different managed session")
    require(end.get("ffmpeg_exit_code") == 0 and end.get("interrupted") is False,
            "recorder end was interrupted")
    verified(end.get("raw"), within=recorder)
    require(type(start.get("monotonic_ns")) is int, "invalid recorder start")
    elapsed = decimal_pts(end.get("elapsed_monotonic_seconds"), "recorder duration")
    require(elapsed > 0 and end.get("monotonic_ns") > start.get("monotonic_ns"),
            "invalid recorder duration")
    projected, mark_refs = checked_marks(Path(marks["path"]), recorder, attempt, elapsed)
    frame_counts = final.get("frame_pts_by_stream") or {}
    require(any(type(row.get("count")) is int and row["count"] > 1
                for row in frame_counts.values() if isinstance(row, dict)), "no video frames")
    fixed_paths = [capture_path, attempt / "ck3-output/session-result.json", final_path,
                   intent_path, start_path, end_path, recorder / "ffprobe-command.json",
                   recorder / "geometry-admission.json", recorder / "ffmpeg.stderr.txt",
                   Path(probe["path"]), Path(marks["path"]), Path(raw["path"])]
    source_files = {str(path.resolve()): record(path) for path in fixed_paths}
    source_files.update({row["path"]: row for row in mark_refs})
    manifest = {"schema": SCHEMA, "status": "PENDING_CLEAN_REVIEW",
                "adapter_eligible": False, "human_1x_review_performed": False,
                "attempt_root": str(attempt), "recorder_root": str(recorder),
                "toolchain": toolchain_identity(requirements),
                "capture_report_result": capture["result"],
                "recorder_result": final["result"], "raw": raw,
                "ffprobe": probe, "marks_journal": marks,
                "format_duration_seconds": str(decimal_pts(final.get("format_duration_seconds"), "format duration")),
                "navigation_marks": projected,
                "files": sorted(source_files.values(), key=lambda row: row["path"]),
                "clean_spans": [],
                "missing_evidence": ["human full-speed raw and exact-frame review",
                                     "explicit exact begin/end PTS and raw-derived frame images",
                                     "per-span gap <= 0.2 seconds and visible source identity",
                                     "new self-contained adapter report/timeline/index"]}
    output.mkdir()
    write_new(output / "source-manifest.json", manifest)
    return {"status": manifest["status"], "source_manifest": record(output / "source-manifest.json")}


def frame_pts(probe: Path) -> list[Decimal]:
    payload = read_json(probe)
    streams = [row for row in payload.get("streams", []) if row.get("codec_type") == "video"]
    require(len(streams) == 1, "ffprobe must contain exactly one video stream")
    index = streams[0]["index"]
    pts = [decimal_pts(frame.get("best_effort_timestamp_time") or frame.get("pts_time"), "frame PTS")
           for frame in payload.get("frames", []) if frame.get("stream_index") == index]
    require(len(pts) > 1 and all(a < b for a, b in zip(pts, pts[1:])),
            "video frame PTS must be strictly increasing")
    return pts


def copy_bound(reference: dict[str, Any], destination: Path) -> dict[str, Any]:
    original = verified(reference)
    destination.parent.mkdir(parents=True, exist_ok=True)
    require(not destination.exists(), f"bundle file exists: {destination}")
    shutil.copyfile(original["path"], destination)
    copied = record(destination)
    require((copied["bytes"], copied["sha256"]) ==
            (original["bytes"], original["sha256"]), f"copied source differs: {destination}")
    return copied


def package(source_manifest: Path, review_path: Path, output: Path) -> dict[str, Any]:
    source_manifest = source_manifest.resolve(strict=True)
    review_path = review_path.resolve(strict=True)
    require(not output.exists() and output.parent.is_dir(), "output must be a new child of an existing directory")
    source = read_json(source_manifest)
    review = read_json(review_path)
    require(source.get("schema") == SCHEMA and source.get("status") == "PENDING_CLEAN_REVIEW",
            "source manifest is not an unreviewed inventory")
    require(review.get("schema") == REVIEW_SCHEMA and
            review.get("reviewer", {}).get("kind") == "human" and
            isinstance(review.get("reviewer", {}).get("id"), str) and
            bool(review["reviewer"]["id"].strip()) and
            review.get("review_scope") == "full_raw_1x_and_exact_span_endpoints" and
            review.get("human_1x_full_raw_review_performed") is True,
            "explicit human 1x raw/endpoint review is required")
    reviewed_at = datetime.fromisoformat(review["reviewed_at_utc"])
    require(reviewed_at.utcoffset() is not None, "review time needs timezone")
    require(review.get("gameplay_hud_visible_at_recording_start") is True and
            review.get("loading_excluded_from_selected_spans") is True,
            "human review must attest gameplay HUD and no loading in selected spans")
    require(review.get("source_manifest") == record(source_manifest),
            "review is not bound to this exact source manifest")
    require(review.get("raw") == source["raw"], "review raw binding differs")
    require(not output.resolve().is_relative_to(Path(source["attempt_root"]).resolve()),
            "bundle output must be outside original attempt")
    require(isinstance(review.get("spans"), list) and review["spans"], "review has no spans")
    for item in source["files"]:
        verified(item)
    pts = frame_pts(Path(source["ffprobe"]["path"]))
    pts_set = set(pts)
    duration = decimal_pts(source["format_duration_seconds"], "format duration")
    required_refs: dict[str, dict[str, Any]] = {}
    checked_spans = []
    span_ids: set[str] = set()
    for span in review["spans"]:
        span_id = span.get("span_id")
        require(isinstance(span_id, str) and ID.fullmatch(span_id) is not None and span_id not in span_ids,
                "invalid or duplicate span id")
        span_ids.add(span_id)
        begin = decimal_pts(span.get("begin_pts_seconds"), "begin PTS")
        end = decimal_pts(span.get("end_pts_seconds"), "end PTS")
        require(begin < end and end <= pts[-1] and end <= duration and
                begin in pts_set and end in pts_set, "span endpoints must be exact raw frame PTS")
        selected = [value for value in pts if begin <= value <= end]
        max_gap = max(b - a for a, b in zip(selected, selected[1:]))
        require(max_gap <= Decimal("0.2"), f"span crosses a raw PTS gap: {span_id} {max_gap}")
        require(span.get("continuous_visual_review_performed") is True and
                span.get("source_identity_visible_and_checked") is True and
                span.get("no_foreign_overlay") is True,
                f"span visual review is incomplete: {span_id}")
        for phase, expected in (("begin", begin), ("end", end)):
            frame = span.get(f"{phase}_frame")
            require(isinstance(frame, dict), f"missing {phase} frame")
            require(decimal_pts(frame.get("pts_seconds"), "endpoint PTS") == expected,
                    f"{phase} frame PTS differs")
            require(frame.get("reviewed_at_1x") is True and frame.get("gameplay_hud") is True and
                    frame.get("source_identity_visible") is True and frame.get("no_loading") is True,
                    f"{phase} frame review incomplete")
            image = verified(frame.get("image"))
            extraction = verified(frame.get("extraction_receipt"))
            receipt = read_json(Path(extraction["path"]))
            require(receipt.get("raw") == source["raw"] and
                    receipt.get("image") == image and
                    decimal_pts(receipt.get("pts_seconds"), "extraction PTS") == expected and
                    receipt.get("result") == "EXTRACTED_UNREVIEWED",
                    f"{phase} extraction receipt does not bind raw, image, exact PTS")
            required_refs[image["path"]] = image
            required_refs[extraction["path"]] = extraction
        checked_spans.append((span, begin, end, str(max_gap)))
    output.mkdir()
    try:
        raw_path = output / "cell/promo/raw" / Path(source["raw"]["path"]).name
        copied_raw = copy_bound(source["raw"], raw_path)
        indexed: list[dict[str, Any]] = []
        def indexed_row(ref: dict[str, Any]) -> dict[str, Any]:
            path = Path(ref["path"])
            return {"path": path.relative_to(output.resolve()).as_posix(),
                    "bytes": ref["bytes"], "sha256": ref["sha256"]}
        indexed.append(indexed_row(copied_raw))
        origin = output / "source"
        for item in source["files"]:
            path = Path(item["path"])
            attempt = Path(source["attempt_root"])
            relative = path.relative_to(attempt)
            if path == Path(source["raw"]["path"]):
                continue
            indexed.append(indexed_row(copy_bound(item, origin / relative)))
        indexed.append(indexed_row(copy_bound(record(source_manifest), output / "source/source-manifest.json")))
        indexed.append(indexed_row(copy_bound(record(review_path), output / "source/human-review.json")))
        timeline_marks = [{"label": "recording_started_after_gameplay_hud", "seconds": 0.0}]
        gates = []
        for span, begin, end, max_gap in checked_spans:
            sid = span["span_id"]
            timeline_marks.extend([{"label": f"{sid}_clean_begin", "seconds": float(begin)},
                                   {"label": f"{sid}_clean_end", "seconds": float(end)}])
            frames = []
            for phase in ("begin", "end"):
                original = span[f"{phase}_frame"]
                prefix = output / "cell/promo/proof" / sid
                image = copy_bound(original["image"], prefix / f"{phase}.png")
                extraction = copy_bound(original["extraction_receipt"], prefix / f"{phase}-extraction.json")
                indexed.extend((indexed_row(image), indexed_row(extraction)))
                frame = {"schema_version": 1, "result": "GREEN", "span": sid,
                         "phase": phase, "image": image, "extraction": extraction,
                         "human_review": indexed_row(record(output / "source/human-review.json")),
                         "producer_assertions": {"exact_pts": original["pts_seconds"],
                                                 "gameplay_hud": True,
                                                 "source_identity_visible": True,
                                                 "no_loading": True,
                                                 "max_gap_seconds": max_gap}}
                # The adapter requires every path/bytes/SHA record in a frame
                # to use absolute paths inside this bundle.
                frame["human_review"] = record(output / "source/human-review.json")
                gate_path = prefix / f"{phase}-gate.json"
                write_new(gate_path, frame)
                gate = record(gate_path)
                indexed.append(indexed_row(gate))
                frame["gate"] = gate
                frames.append(frame)
            gates.append({"span_id": sid, "result": "GREEN",
                          "begin_mark": f"{sid}_clean_begin", "end_mark": f"{sid}_clean_end",
                          "frames": frames})
        timeline_marks.append({"label": "recording_stop_requested", "seconds": float(duration)})
        timeline_marks.sort(key=lambda row: row["seconds"])
        timeline = {"schema": 2, "source_kind": "real CK3 desktop capture after gameplay HUD",
                    "exclude_ck3_loading": True, "raw_path": str(raw_path.resolve()),
                    "raw_bytes": copied_raw["bytes"], "raw_sha256": copied_raw["sha256"],
                    "marks": timeline_marks, "clean_frame_gates": gates,
                    "clean_capture_complete": True, "missing_clean_spans": [],
                    "producer_scope": "explicit human 1x raw review and exact selected-span endpoint images"}
        timeline_path = output / "cell/promo/capture-timeline.json"
        write_new(timeline_path, timeline)
        indexed.append(indexed_row(record(timeline_path)))
        report = {"schema_version": 1, "result": "GREEN",
                  "cell": {"schema_version": 1, "result": "GREEN", "promo_capture": timeline},
                  "source_capture_report_result": source["capture_report_result"],
                  "human_review_completed": True, "film_signoff_granted": False}
        write_new(output / "report.json", report)
        indexed.append(indexed_row(record(output / "report.json")))
        write_new(output / "evidence-index.json", {"schema_version": 1, "result": "GREEN",
                                                 "artifact_root": str(output.resolve()), "files": indexed})
        from xar_promo.adapters.ck3 import load_capture_bundle
        bundle = load_capture_bundle(output, required_span_ids=span_ids)
        bundle.verify_unchanged()
        result = {"status": "ADAPTER_VALIDATED_SELECTED_SPANS_ONLY",
                  "adapter_bundle": str(output.resolve()), "source_capture_report_result": source["capture_report_result"],
                  "human_raw_review": record(output / "source/human-review.json"),
                  "report": record(output / "report.json"), "timeline": record(timeline_path),
                  "evidence_index": record(output / "evidence-index.json"),
                  "raw": copied_raw, "span_ids": sorted(span_ids), "film_signoff_granted": False}
        write_new(output / "bundle-receipt.json", result)
        return result
    except Exception as exc:
        write_new(output / "failure.json", {"status": "FAILED_PRESERVED", "error": repr(exc)})
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare", help="create pending source inventory only")
    prep.add_argument("--attempt", required=True, type=Path)
    prep.add_argument("--recorder", required=True, type=Path)
    prep.add_argument("--output", required=True, type=Path)
    prep.add_argument("--requirements", type=Path,
                      default=Path(__file__).resolve().parents[3] / "tools/requirements-promo-toolchain.txt")
    pack = commands.add_parser("package", help="require exact human review, then validate new adapter bundle")
    pack.add_argument("--source-manifest", required=True, type=Path)
    pack.add_argument("--human-review", required=True, type=Path)
    pack.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = (prepare(args.attempt, args.recorder, args.output, args.requirements)
              if args.command == "prepare" else
              package(args.source_manifest, args.human_review, args.output))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
