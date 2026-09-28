"""Bind four existing recorder sidecars to frame-exact navigation windows.

Reads the four complete FFprobe JSON files but only stats the GB-sized raw
videos. The output is a search plan, never a clean-span or visual review.
"""

from __future__ import annotations

import argparse
from bisect import bisect_left, bisect_right
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
GAP_LIMIT = Decimal("0.2")
THREE = ROOT / "three-raw-adapter-queue-20260928.json"
REINFORCEMENT = ROOT / "reinforcement-raw-adapter-queue-20260928.json"


def require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def identity(path: Path) -> dict[str, Any]:
    path = path.resolve(strict=True)
    before = path.stat()
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    after = path.stat()
    require((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns),
            f"file changed during hash: {path}")
    return {"path": path.as_posix(), "bytes": after.st_size,
            "sha256": digest.hexdigest().upper()}


def read_json(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8-sig"))
    require(isinstance(obj, dict), f"JSON object required: {path}")
    return obj


def checked_sidecar(path: Path, expected: dict[str, Any] | None = None) -> dict[str, Any]:
    found = identity(path)
    if expected is not None:
        require(found["bytes"] == expected["bytes"] and
                found["sha256"] == expected["sha256_checked_this_pass"],
                f"small sidecar changed: {path}")
    return found


def select_window(pts: list[Decimal], begin: Decimal, end: Decimal) -> dict[str, Any]:
    """Use only frames inside the requested window; reject every >200ms gap."""
    require(begin < end, "window begin must precede end")
    left = bisect_left(pts, begin)
    right = bisect_right(pts, end) - 1
    require(0 <= left < right < len(pts), f"too few frames in {begin}–{end}")
    deltas = [(pts[i] - pts[i - 1], i) for i in range(left + 1, right + 1)]
    largest, _ = max(deltas)
    breaks = [{"before_pts_seconds": str(pts[i - 1]),
               "after_pts_seconds": str(pts[i]), "gap_seconds": str(delta)}
              for delta, i in deltas if delta > GAP_LIMIT]
    return {"requested_begin_seconds": str(begin), "requested_end_seconds": str(end),
            "exact_begin_pts_seconds": str(pts[left]),
            "exact_end_pts_seconds": str(pts[right]),
            "requested_begin_is_frame_pts": pts[left] == begin,
            "requested_end_is_frame_pts": pts[right] == end,
            "begin_frame_index": left, "end_frame_index": right,
            "frame_count": right - left + 1,
            "actual_duration_seconds": str(pts[right] - pts[left]),
            "max_adjacent_gap_seconds": str(largest),
            "gaps_over_0_2_seconds": breaks,
            "machine_status": "GAP_REJECTED" if breaks else "PTS_CANDIDATE_UNREVIEWED"}


def normalize_sources() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    three = read_json(THREE)
    fourth = read_json(REINFORCEMENT)
    require(three["schema"] == "xar.war-promo.episode02-adapter-queue/v1" and
            three["adapter_eligible"] is False and
            three["human_1x_review_performed"] is False and
            len(three["sources"]) == 3, "three-raw queue status changed")
    require(fourth["schema"] == "xar.war-promo.episode02-reinforcement-adapter-queue/v1" and
            fourth["adapter_eligible"] is False and
            fourth["clean_spans_certified"] is False and
            fourth["human_1x_review_performed"] is False,
            "reinforcement queue status changed")
    rows = list(three["sources"])
    rows.append({"id": "e2-06-07-a01", "attempt_root": fourth["attempt_root"],
                 "recorder_root": fourth["recorder_root"],
                 "raw_bytes_from_recorder_final": fourth["raw"]["bytes_stat_checked_this_pass"],
                 "raw_sha256_from_recorder_final":
                     fourth["raw"]["sha256_from_recorder_final_not_rehashed_this_pass"],
                 "ffprobe_bytes_from_recorder_final":
                     fourth["ffprobe"]["bytes_stat_checked_this_pass"],
                 "frame_count_from_pts_audit": fourth["pts_audit"]["frames"],
                 "candidate_windows_seconds": fourth["candidate_search_windows_seconds"],
                 "queue_small_sidecars": fourth})
    queues = []
    for path in (THREE, REINFORCEMENT):
        item = identity(path)
        item["path"] = path.name  # checked-in report remains valid in another worktree
        queues.append(item)
    return rows, queues


def audit_source(row: dict[str, Any]) -> dict[str, Any]:
    attempt = Path(row["attempt_root"]).resolve(strict=True)
    recorder = Path(row["recorder_root"]).resolve(strict=True)
    require(recorder.parent == attempt, f"recorder/attempt mismatch: {row['id']}")
    final_path = recorder / "recorder-final.json"
    capture_path = attempt / "ck3-output/capture-report.json"
    session_path = attempt / "ck3-output/session-result.json"
    final_id = checked_sidecar(final_path,
                               (row.get("queue_small_sidecars") or {}).get("recorder_final"))
    capture_id = checked_sidecar(capture_path,
                                 (row.get("queue_small_sidecars") or {}).get("capture_report"))
    session_id = checked_sidecar(session_path,
                                 (row.get("queue_small_sidecars") or {}).get("session_result"))
    final = read_json(final_path)
    capture = read_json(capture_path)
    session = read_json(session_path)
    shutdown = session.get("shutdown") or {}
    require(capture.get("result") == "ENVIRONMENT_SESSION_COMPLETE_NO_VIDEO" and
            capture.get("environment_session_complete") is True and
            capture.get("adapter_bundle_validated") is False and
            (capture.get("worker") or {}).get("ok") is True and
            not (capture.get("cleanup_process_inventory") or {}).get("processes") and
            session.get("ok") is True and shutdown.get("tree_gone") is True and
            shutdown.get("cleanup_proven") is True,
            f"managed capture was not cleanly shut down: {row['id']}")
    require(final.get("result") == "ENCODED_UNREVIEWED" and
            final.get("clean_spans_certified") is False and
            final.get("human_review_completed") is False and
            final.get("video_pts_complete") is True and
            final.get("ffmpeg_exit_code") == 0 and
            final.get("ffprobe_exit_code") == 0,
            f"recorder not sealed as unreviewed: {row['id']}")
    raw_ref = final["raw"]
    raw = Path(raw_ref["path"])
    require(not raw.is_symlink() and raw.resolve(strict=True).parent == (recorder / "raw").resolve(),
            f"raw escapes recorder: {row['id']}")
    require(raw.stat().st_size == raw_ref["bytes"] == row["raw_bytes_from_recorder_final"] and
            raw_ref["sha256"] == row["raw_sha256_from_recorder_final"],
            f"raw size or historical receipt differs: {row['id']}")
    probe = recorder / "ffprobe.json"
    require(Path(final["ffprobe_output"]["path"]).resolve(strict=True) == probe.resolve(),
            f"FFprobe path differs: {row['id']}")
    probe_id = identity(probe)
    require(probe_id["bytes"] == final["ffprobe_output"]["bytes"] ==
            row["ffprobe_bytes_from_recorder_final"] and
            probe_id["sha256"] == final["ffprobe_output"]["sha256"],
            f"FFprobe bytes/hash changed: {row['id']}")
    fourth = row.get("queue_small_sidecars") or {}
    if fourth:
        checked_sidecar(recorder / "pts-audit-a01.json", fourth["pts_audit"])
        checked_sidecar(recorder / "marks.jsonl", fourth["marks"])
        require(final["ffprobe_output"]["sha256"] ==
                fourth["ffprobe"]["sha256_from_recorder_final_not_rehashed_this_pass"] and
                final["format_duration_seconds"] == fourth["raw"]["format_duration_seconds"],
                "reinforcement probe/duration differs from queue")
        require(raw.resolve().as_posix() == (attempt / fourth["raw"]["relative_path"]).resolve().as_posix(),
                "reinforcement raw path differs from queue")
        require(probe.resolve().as_posix() ==
                (attempt / fourth["ffprobe"]["relative_path"]).resolve().as_posix(),
                "reinforcement FFprobe path differs from queue")
    data = read_json(probe)
    streams = [s for s in data.get("streams", []) if s.get("codec_type") == "video"]
    require(len(streams) == 1 and streams[0].get("width") == 1920 and
            streams[0].get("height") == 1080,
            f"expected one 1920x1080 video stream: {row['id']}")
    index = streams[0]["index"]
    pts = [Decimal(frame.get("best_effort_timestamp_time") or frame["pts_time"])
           for frame in data.get("frames", []) if frame.get("stream_index") == index]
    require(len(pts) == row["frame_count_from_pts_audit"] ==
            final["frame_pts_by_stream"][str(index)]["count"] and
            all(a < b for a, b in zip(pts, pts[1:])),
            f"FFprobe frame count/PTS order differs: {row['id']}")
    gaps = [{"before_pts_seconds": str(a), "after_pts_seconds": str(b),
             "gap_seconds": str(b - a)} for a, b in zip(pts, pts[1:]) if b - a > GAP_LIMIT]
    windows = []
    for window in row["candidate_windows_seconds"]:
        begin, end = Decimal(str(window["begin"])), Decimal(str(window["end"]))
        result = select_window(pts, begin, end)
        if window.get("exact_endpoints_verified") is True:
            require(result["requested_begin_is_frame_pts"] and
                    result["requested_end_is_frame_pts"],
                    f"uncorrected exact-endpoint claim: {row['id']} {window['purpose']}")
        correction = window.get("frame_pts_correction")
        if correction is not None:
            require(result["exact_begin_pts_seconds"] == correction["begin"] and
                    result["exact_end_pts_seconds"] == correction["end"] and
                    not result["requested_end_is_frame_pts"],
                    f"recorded frame-PTS correction no longer matches: "
                    f"{row['id']} {window['purpose']}")
        require(result["machine_status"] == "PTS_CANDIDATE_UNREVIEWED",
                f"candidate crosses a gap: {row['id']} {window['purpose']}")
        windows.append({"purpose": window["purpose"],
                        "visual_risk": window.get("visual_risk"),
                        "original_window_claimed_exact": window.get("exact_endpoints_verified") is True,
                        "frame_pts_correction": correction,
                        "original_exact_claim_confirmed":
                            (result["requested_begin_is_frame_pts"] and
                             result["requested_end_is_frame_pts"])
                            if window.get("exact_endpoints_verified") is True else None,
                        **result})
    forbidden = row.get("forbidden_window_seconds")
    rejected = None
    if forbidden:
        rejected = {"reason": forbidden["reason"],
                    **select_window(pts, Decimal(str(forbidden["begin"])),
                                    Decimal(str(forbidden["end"])))}
        require(rejected["machine_status"] == "GAP_REJECTED" and
                any(item["gap_seconds"] == "7.566000" or
                    Decimal(item["gap_seconds"]) == Decimal("7.566")
                    for item in rejected["gaps_over_0_2_seconds"]),
                "known A05 a02 7.566-second gap was not rejected")
    return {"id": row["id"], "attempt_root": attempt.as_posix(),
            "recorder_root": recorder.as_posix(),
            "capture_report": capture_id, "session_result": session_id,
            "recorder_final": final_id,
            "raw_stat_bytes": raw.stat().st_size,
            "raw_sha256_from_recorder_final_not_rehashed": raw_ref["sha256"],
            "ffprobe_verified": probe_id,
            "video_width": streams[0]["width"],
            "video_height": streams[0]["height"],
            "format_duration_seconds": final["format_duration_seconds"],
            "frame_count": len(pts), "all_gaps_over_0_2_seconds": gaps,
            "candidate_windows": windows, "forbidden_window": rejected,
            "visual_review_performed": False, "clean_spans_certified": False}


def build() -> dict[str, Any]:
    rows, queues = normalize_sources()
    ids = [row["id"] for row in rows]
    require(len(ids) == len(set(ids)) == 4, "four distinct source IDs required")
    sources = [audit_source(row) for row in rows]
    require(sum(source["raw_stat_bytes"] for source in sources) == 4421454290,
            "four-raw inventory size changed")
    return {"schema": "xar.war-promo.episode02-four-raw-pts-candidates/v1",
            "status": "MACHINE_PTS_CANDIDATES_ONLY_UNREVIEWED",
            "queue_sources": queues,
            "raw_sha256_rehashed_this_pass": False,
            "full_ffprobe_sha256_rehashed_this_pass": True,
            "human_1x_review_performed": False,
            "clean_spans_certified": False,
            "adapter_eligible": False,
            "sources": sources,
            "total_raw_stat_bytes": sum(source["raw_stat_bytes"] for source in sources),
            "total_ffprobe_verified_bytes": sum(source["ffprobe_verified"]["bytes"]
                                                for source in sources)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--output", type=Path, help="write a new, never-overwritten report")
    group.add_argument("--check", type=Path, help="compare with a frozen report")
    args = parser.parse_args()
    if args.output and (args.output.exists() or not args.output.parent.is_dir()):
        parser.error("output must be a new file in an existing directory")
    result = build()
    if args.check:
        require(read_json(args.check) == result, f"frozen report differs: {args.check}")
    else:
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    print(json.dumps({"status": result["status"], "sources": len(result["sources"]),
                      "candidate_windows": sum(len(source["candidate_windows"])
                                               for source in result["sources"]),
                      "known_gap_rejected": result["sources"][2]["forbidden_window"] is not None},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
