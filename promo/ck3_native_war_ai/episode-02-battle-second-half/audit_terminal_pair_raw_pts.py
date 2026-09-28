"""Read-only per-frame PTS and mark audit for E2-09 bounded raw files.

The report binds existing recorder files. Wall-clock mark offsets are never
asserted to be video PTS or clean spans.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from bisect import bisect_left
from datetime import datetime, timezone
from pathlib import Path


def identity(path: Path) -> dict:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    return {"path": str(path.resolve()), "bytes": size,
            "sha256": digest.hexdigest().upper()}


def audit_segment(root: Path) -> dict:
    final_path = root / "recorder-final.json"
    probe_path = root / "ffprobe.json"
    marks_path = root / "marks.jsonl"
    final = json.loads(final_path.read_text(encoding="utf-8"))
    probe = json.loads(probe_path.read_text(encoding="utf-8"))
    marks = [json.loads(line) for line in marks_path.read_text(encoding="utf-8").splitlines() if line]
    frames = [f for f in probe["frames"] if f.get("media_type") == "video"]
    pts = [float(f["pts_time"]) for f in frames]
    widths = {f.get("width") for f in frames}
    heights = {f.get("height") for f in frames}
    gaps = [round(right - left, 6) for left, right in zip(pts, pts[1:])]
    largest_gaps = sorted(
        ({"from_pts_seconds": pts[index], "to_pts_seconds": pts[index + 1],
          "gap_seconds": gap} for index, gap in enumerate(gaps)),
        key=lambda row: row["gap_seconds"], reverse=True,
    )[:5]
    nearest = []
    for mark in marks:
        wall_offset = mark.get("approx_seconds_from_recorder_start")
        if not isinstance(wall_offset, (int, float)):
            continue
        at = bisect_left(pts, wall_offset)
        candidates = [p for p in pts[max(0, at - 1): min(len(pts), at + 1)]]
        closest = min(candidates, key=lambda p: abs(p - wall_offset)) if candidates else None
        nearest.append({"kind": mark.get("kind"), "wall_offset_seconds": wall_offset,
                        "nearest_video_pts_seconds_for_navigation_only": closest,
                        "wall_to_pts_difference_seconds": round(closest - wall_offset, 6) if closest is not None else None,
                        "screenshot_sha256": (mark.get("screenshot") or {}).get("sha256"),
                        "control_sha256": (mark.get("control") or {}).get("sha256"),
                        "report_sha256": (mark.get("report") or {}).get("sha256")})
    return {
        "root": str(root.resolve()),
        "files": {"final": identity(final_path), "probe": identity(probe_path),
                  "marks": identity(marks_path), "raw": identity(Path(final["raw"]["path"]))},
        "recorder_result": final["result"], "format_duration_seconds": final["format_duration_seconds"],
        "frame_count": len(frames), "first_pts_seconds": pts[0] if pts else None,
        "last_pts_seconds": pts[-1] if pts else None,
        "all_pts_strictly_increasing": all(gap > 0 for gap in gaps),
        "minimum_gap_seconds": min(gaps) if gaps else None,
        "maximum_gap_seconds": max(gaps) if gaps else None,
        "gaps_over_100ms": sum(gap > 0.1 for gap in gaps),
        "gaps_over_500ms": sum(gap > 0.5 for gap in gaps),
        "largest_gaps": largest_gaps,
        "frame_widths": sorted(widths), "frame_heights": sorted(heights),
        "marks": nearest,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output exists; use a new append-only report path")
    segments = [audit_segment(args.attempt_root / f"recording-e2-09-terminal-a{i:02}") for i in (1, 2)]
    a02_marks = {m["kind"]: m for m in segments[1]["marks"]}
    writer = a02_marks.get("e2t-s02-d32-writer")
    after = a02_marks.get("e2t-s02-d32-war4-after")
    same_report = bool(writer and after and writer["report_sha256"] == after["report_sha256"])
    report = {
        "schema": "ck3.episode02.terminal-pair-raw-pts-audit.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "segments": segments,
        "writer_and_war4_after_same_a02_recorder_and_report_sha": same_report,
        "limits": ["Mark wall offsets are not video PTS; nearest PTS is navigation only.",
                   "This is an automated file audit, not clean-span certification or 1x human review."],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output), "sha256": identity(args.output)["sha256"],
                      "frame_counts": [s["frame_count"] for s in segments],
                      "same_report": same_report}, ensure_ascii=False))


if __name__ == "__main__":
    main()
