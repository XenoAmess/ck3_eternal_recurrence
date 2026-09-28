"""Link one completed E2-05 recorder to a prior full-PTS audit without rehashing raw.

Run only after the screen owner confirms natural FFmpeg close and ck3-screen
RELEASE. This reads the prior PTS report and small receipts, never starts CK3,
decodes video, certifies a clean span, or records human approval.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
from pathlib import Path
from typing import Any


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    require(isinstance(value, dict), f"not a JSON object: {path}")
    return value


def identity(path: Path) -> dict[str, Any]:
    path = path.resolve(strict=True)
    require(path.is_file(), f"missing file: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"path": str(path), "bytes": path.stat().st_size,
            "sha256": digest.hexdigest().upper()}


def small_ref(reference: Any, *, root: Path) -> dict[str, Any]:
    require(isinstance(reference, dict) and isinstance(reference.get("path"), str),
            "invalid small evidence reference")
    path = Path(reference["path"]).resolve(strict=True)
    require(path.is_relative_to(root), f"small evidence escapes attempt: {path}")
    require(path.stat().st_size <= 100 * 1024 * 1024,
            f"small-evidence-only audit refuses large file: {path}")
    actual = identity(path)
    require(actual == reference, f"small evidence byte/SHA differs: {path}")
    return actual


def link(recorder: Path, session_output: Path, pts_audit: Path) -> dict[str, Any]:
    recorder = recorder.resolve(strict=True)
    session_output = session_output.resolve(strict=True)
    attempt = session_output.parent
    require(recorder.parent == attempt and session_output.name == "ck3-output",
            "recorder/session are not siblings in one live attempt")
    pts_id = identity(pts_audit)
    pts = read_object(pts_audit)
    require(pts.get("schema") == "xar.war-promo.raw-video-pts-audit/v1" and
            pts.get("human_visual_review_completed") is False and
            pts.get("clean_spans_certified") is False,
            "prior PTS report is not a machine-only raw audit")
    paths = {name: recorder / name for name in
             ("recorder-intent.json", "recorder-start.json", "recorder-end.json",
              "recorder-final.json", "marks.jsonl", "ffprobe.json")}
    intent = read_object(paths["recorder-intent.json"])
    start = read_object(paths["recorder-start.json"])
    end = read_object(paths["recorder-end.json"])
    final = read_object(paths["recorder-final.json"])
    require(Path(intent.get("workdir", "")).resolve() == recorder and
            Path(intent.get("session_output", "")).resolve() == session_output,
            "recorder intent belongs to another attempt")
    raw = Path(intent["raw_path"]).resolve(strict=True)
    require(raw.parent == recorder / "raw" and raw.is_file(), "unexpected raw path")
    raw_stat_before = raw.stat()
    probe_path = paths["ffprobe.json"].resolve(strict=True)
    require(probe_path.is_file(), "full ffprobe disappeared after PTS audit")
    probe_stat_before = probe_path.stat()
    # Full raw and full FFprobe SHA values come from the independently run
    # PTS audit. Do not read either large file a second time here.
    require(pts.get("recorder_intent") == identity(paths["recorder-intent.json"]) and
            pts.get("recorder_final") == identity(paths["recorder-final.json"]) and
            pts.get("raw") == final.get("raw") == end.get("raw") and
            pts.get("full_ffprobe") == final.get("ffprobe_output") and
            Path(pts["raw"]["path"]).resolve() == raw and
            Path(pts["full_ffprobe"]["path"]).resolve() == probe_path,
            "PTS audit, recorder end and recorder final do not bind the same raw/probe")
    require(raw_stat_before.st_size == pts["raw"]["bytes"],
            "raw size changed after PTS audit")
    require(probe_stat_before.st_size == pts["full_ffprobe"]["bytes"],
            "full ffprobe size changed after PTS audit")
    marks_id = identity(paths["marks.jsonl"])
    require(final.get("marks") == marks_id, "marks journal differs from recorder final")
    rows = [json.loads(line) for line in paths["marks.jsonl"].read_text(encoding="utf-8").splitlines()
            if line]
    require(len(rows) >= 2 and all(isinstance(row, dict) for row in rows), "mark journal missing")
    require(rows[0].get("kind") == "recorder-start" and rows[-1].get("kind") == "recorder-end" and
            rows[0].get("monotonic_ns") == start.get("monotonic_ns") and
            rows[-1].get("monotonic_ns") == end.get("monotonic_ns") and
            rows[0].get("pid") == start.get("pid") and
            rows[-1].get("pid") == end.get("pid") and
            rows[0].get("utc") == start.get("started_at") and
            rows[-1].get("utc") == end.get("ended_at") and
            all(type(row.get("monotonic_ns")) is int for row in rows) and
            all(a["monotonic_ns"] < b["monotonic_ns"] for a, b in zip(rows, rows[1:])),
            "marks journal boundaries or order differ from recorder")
    require(end.get("ffmpeg_exit_code") == 0 and end.get("interrupted") is False and
            final.get("ffmpeg_exit_code") == 0 and final.get("ffprobe_exit_code") == 0 and
            final.get("result") == "ENCODED_UNREVIEWED" and
            final.get("video_pts_complete") is True and
            final.get("clean_spans_certified") is False and
            final.get("human_review_completed") is False,
            "recorder did not close as an unreviewed encoding")
    marks = []
    for row in rows[1:-1]:
        require(row.get("approx_seconds_are_not_video_pts") is True,
                "mark incorrectly treats wall time as media PTS")
        evidence = {}
        for key in ("control", "report", "screenshot"):
            if row.get(key) is not None:
                evidence[key] = small_ref(row[key], root=attempt)
        marks.append({"kind": row.get("kind"), "date_raw": row.get("date_raw"),
                      "war_id": row.get("war_id"), "combat_id": row.get("combat_id"),
                      "wall_seconds_navigation_only": row.get("approx_seconds_from_recorder_start"),
                      "evidence": evidence})
    session = read_object(session_output / "session-result.json")
    capture = read_object(session_output / "capture-report.json")
    shutdown = session.get("shutdown") or {}
    cleanup = (session.get("ok") is True and shutdown.get("ok") is True and
               shutdown.get("tree_gone") is True and shutdown.get("cleanup_proven") is True and
               not (shutdown.get("final_ck3_inventory") or {}).get("processes"))
    require(cleanup, "managed CK3 cleanup is not proven")
    require(capture.get("result") == "ENVIRONMENT_SESSION_COMPLETE_NO_VIDEO" and
            capture.get("environment_session_complete") is True and
            capture.get("adapter_bundle_validated") is False and
            (capture.get("worker") or {}).get("ok") is True and
            not (capture.get("cleanup_process_inventory") or {}).get("processes"),
            "managed capture session is not complete")
    pts_result = pts.get("result")
    require(pts_result in ("PTS_CONTINUOUS_UNREVIEWED", "RED_PRESERVED"),
            "unknown PTS audit result")
    if pts_result == "PTS_CONTINUOUS_UNREVIEWED":
        try:
            span = Decimal(pts["span_seconds"])
            minimum = Decimal(pts["min_duration_seconds"])
            max_gap = Decimal(pts["max_frame_gap_seconds"])
            first = Decimal(pts["first_pts_seconds"])
            last = Decimal(pts["last_pts_seconds"])
        except (KeyError, InvalidOperation, TypeError) as exc:
            raise ValueError("continuous PTS report lacks valid duration/gap bounds") from exc
        require(type(pts.get("frame_count_with_pts")) is int and
                pts["frame_count_with_pts"] > 1 and
                pts.get("missing_pts_count") == 0 and
                pts.get("nonmonotonic_count") == 0 and
                pts.get("gap_count") == 0 and
                span.is_finite() and minimum.is_finite() and max_gap.is_finite() and
                first.is_finite() and last.is_finite() and
                span >= minimum >= Decimal("590") and
                Decimal(0) < max_gap <= Decimal("0.2") and
                first >= 0 and last > first and last - first == span,
                "continuous PTS result contradicts its frame/gap/duration counts")
        streams = [row for row in final.get("streams", []) if row.get("codec_type") == "video"]
        require(len(streams) == 1 and pts.get("video_stream_index") == streams[0].get("index"),
                "PTS report video stream differs from recorder final")
        final_frames = (final.get("frame_pts_by_stream") or {}).get(str(streams[0]["index"])) or {}
        require(final_frames.get("count") == pts["frame_count_with_pts"] and
                Decimal(str(final_frames.get("first_pts_time"))) == first and
                Decimal(str(final_frames.get("last_pts_time"))) == last,
                "PTS report frame count/endpoints differ from recorder final")
    raw_stat_after = raw.stat()
    probe_stat_after = probe_path.stat()
    require((raw_stat_before.st_size, raw_stat_before.st_mtime_ns) ==
            (raw_stat_after.st_size, raw_stat_after.st_mtime_ns),
            "raw changed during small-file link audit")
    require((probe_stat_before.st_size, probe_stat_before.st_mtime_ns) ==
            (probe_stat_after.st_size, probe_stat_after.st_mtime_ns),
            "full ffprobe changed during small-file link audit")
    return {"schema": "xar.war-promo.e2-05-postrun-links/v1",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "result": ("MEDIA_PTS_CANDIDATE_UNREVIEWED" if pts_result == "PTS_CONTINUOUS_UNREVIEWED"
                       else "MEDIA_PTS_GAPS_OR_RED_UNREVIEWED"),
            "pts_audit_result": pts_result,
            "pts_audit": pts_id,
            "capture_report_result": capture.get("result"),
            "session_result": identity(session_output / "session-result.json"),
            "capture_report": identity(session_output / "capture-report.json"),
            "recorder_intent": identity(paths["recorder-intent.json"]),
            "recorder_start": identity(paths["recorder-start.json"]),
            "recorder_end": identity(paths["recorder-end.json"]),
            "recorder_final": identity(paths["recorder-final.json"]),
            "raw_from_prior_full_sha_audit": pts["raw"],
            "raw_stat_during_link_audit": {"bytes": raw_stat_after.st_size,
                                           "mtime_ns": raw_stat_after.st_mtime_ns},
            "ffprobe_from_prior_full_sha_audit": pts["full_ffprobe"],
            "ffprobe_stat_during_link_audit": {"bytes": probe_stat_after.st_size,
                                               "mtime_ns": probe_stat_after.st_mtime_ns},
            "marks_journal": marks_id,
            "marks": marks,
            "video_pts_summary": {key: pts.get(key) for key in
                                  ("frame_count_with_pts", "first_pts_seconds",
                                   "last_pts_seconds", "missing_pts_count",
                                   "nonmonotonic_count", "gap_count", "gaps_first_20")},
            "target_event_visual_verified": False,
            "adapter_bundle_validated": False,
            "clean_spans_certified": False,
            "human_1x_review_performed": False,
            "film_signoff_granted": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recorder-workdir", required=True, type=Path)
    parser.add_argument("--session-output", required=True, type=Path)
    parser.add_argument("--pts-audit", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    require(not args.output.exists() and args.output.parent.is_dir() and
            not args.output.resolve().is_relative_to(args.session_output.parent.resolve()),
            "output must be a new external file")
    try:
        result = link(args.recorder_workdir, args.session_output, args.pts_audit)
        code = 0 if result["result"] == "MEDIA_PTS_CANDIDATE_UNREVIEWED" else 2
    except Exception as exc:
        result = {"schema": "xar.war-promo.e2-05-postrun-links/v1",
                  "created_at_utc": datetime.now(timezone.utc).isoformat(),
                  "result": "RED_PRESERVED", "error": repr(exc),
                  "clean_spans_certified": False,
                  "human_1x_review_performed": False,
                  "film_signoff_granted": False}
        code = 2
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps({"result": result["result"], "output": str(args.output)}, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
