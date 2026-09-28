"""Audit every preserved video-frame PTS in a bounded raw recorder.

This is an automatic continuity check, not a clean-span or visual signoff.
Input files stay unchanged; the report is written only to a new external path.
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


def identity(path: Path) -> dict[str, Any]:
    before = path.stat()
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise RuntimeError(f"file changed during audit: {path}")
    return {"path": str(path.resolve()), "bytes": after.st_size,
            "sha256": digest.hexdigest().upper()}


def decimal_arg(value: str) -> Decimal:
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError("must be a decimal number") from exc
    if not parsed.is_finite() or parsed <= 0:
        raise argparse.ArgumentTypeError("must be finite and positive")
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recorder-workdir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--min-duration", type=decimal_arg, default=Decimal("590"))
    parser.add_argument("--max-frame-gap", type=decimal_arg, default=Decimal("0.2"))
    args = parser.parse_args()
    if args.output.exists() or not args.output.parent.is_dir():
        parser.error("output must be new in an existing external audit directory")
    intent_path = args.recorder_workdir / "recorder-intent.json"
    final_path = args.recorder_workdir / "recorder-final.json"
    probe_path = args.recorder_workdir / "ffprobe.json"
    intent = json.loads(intent_path.read_text(encoding="utf-8"))
    final = json.loads(final_path.read_text(encoding="utf-8"))
    raw_path = Path(intent["raw_path"])
    if raw_path.parent.resolve() != (args.recorder_workdir / "raw").resolve():
        parser.error("raw path escapes this recorder workdir")
    raw_id = identity(raw_path)
    probe_id = identity(probe_path)
    if final.get("raw") != raw_id or final.get("ffprobe_output") != probe_id:
        parser.error("recorder final does not bind current raw and full ffprobe bytes")
    data = json.loads(probe_path.read_text(encoding="utf-8"))
    video_streams = [row for row in data.get("streams", [])
                     if row.get("codec_type") == "video"]
    if len(video_streams) != 1:
        parser.error("expected exactly one video stream")
    index = video_streams[0]["index"]
    pts: list[Decimal] = []
    missing: list[int] = []
    for position, frame in enumerate(data.get("frames", [])):
        if frame.get("stream_index") != index:
            continue
        raw_pts = frame.get("best_effort_timestamp_time") or frame.get("pts_time")
        try:
            value = Decimal(raw_pts) if raw_pts is not None else None
        except InvalidOperation:
            value = None
        if value is None or not value.is_finite():
            missing.append(position)
        else:
            pts.append(value)
    nonmonotonic = []
    gaps = []
    for position in range(1, len(pts)):
        gap = pts[position] - pts[position - 1]
        if gap <= 0:
            nonmonotonic.append({"frame_index": position, "delta_seconds": str(gap)})
        elif gap > args.max_frame_gap:
            gaps.append({"frame_index": position, "delta_seconds": str(gap)})
    duration = pts[-1] - pts[0] if len(pts) >= 2 else Decimal(0)
    passing = (final.get("result") == "ENCODED_UNREVIEWED" and
               len(pts) > 1 and not missing and not nonmonotonic and not gaps and
               duration >= args.min_duration)
    report = {
        "schema": "xar.war-promo.raw-video-pts-audit/v1",
        "audited_at": datetime.now(timezone.utc).isoformat(),
        "result": "PTS_CONTINUOUS_UNREVIEWED" if passing else "RED_PRESERVED",
        "human_visual_review_completed": False,
        "clean_spans_certified": False,
        "recorder_intent": identity(intent_path),
        "recorder_final": identity(final_path),
        "raw": raw_id,
        "full_ffprobe": probe_id,
        "video_stream_index": index,
        "frame_count_with_pts": len(pts),
        "missing_pts_count": len(missing),
        "missing_pts_positions_first_20": missing[:20],
        "first_pts_seconds": str(pts[0]) if pts else None,
        "last_pts_seconds": str(pts[-1]) if pts else None,
        "span_seconds": str(duration),
        "min_duration_seconds": str(args.min_duration),
        "max_frame_gap_seconds": str(args.max_frame_gap),
        "nonmonotonic_count": len(nonmonotonic),
        "nonmonotonic_first_20": nonmonotonic[:20],
        "gap_count": len(gaps),
        "gaps_first_20": gaps[:20],
    }
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps({"result": report["result"], "frame_count": len(pts),
                      "span_seconds": str(duration), "output": str(args.output)},
                     ensure_ascii=False))
    return 0 if passing else 2


if __name__ == "__main__":
    raise SystemExit(main())
