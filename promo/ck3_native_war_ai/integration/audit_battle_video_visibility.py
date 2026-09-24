"""Sample a raw CK3 battle clip for the manually bound Messina marker."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import cv2

from battle_frame_gate import DEFAULT_SEARCH_RECT, DEFAULT_TEMPLATE_RECT


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--interval-seconds", type=float, default=1.0)
    parser.add_argument("--minimum-score", type=float, default=0.75)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    if args.interval_seconds <= 0 or not 0 < args.minimum_score <= 1:
        parser.error("interval and threshold are out of range")
    source = cv2.imread(str(args.reference), cv2.IMREAD_COLOR)
    if source is None:
        raise ValueError("reference image is unreadable")
    x0, y0, x1, y1 = DEFAULT_TEMPLATE_RECT
    sx0, sy0, sx1, sy1 = DEFAULT_SEARCH_RECT
    template = source[y0:y1, x0:x1]
    capture = cv2.VideoCapture(str(args.video))
    if not capture.isOpened():
        raise ValueError("video is unreadable")
    fps = capture.get(cv2.CAP_PROP_FPS)
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    if fps <= 0 or frame_count <= 0:
        raise ValueError("video has no valid frame timing")
    samples = []
    try:
        count = int((frame_count - 1) / fps / args.interval_seconds) + 1
        for index in range(count):
            seconds = index * args.interval_seconds
            capture.set(cv2.CAP_PROP_POS_MSEC, seconds * 1000)
            ok, frame = capture.read()
            if not ok:
                break
            if frame.shape != source.shape:
                raise ValueError("video frame differs from reference size")
            search = frame[sy0:sy1, sx0:sx1]
            correlation = cv2.matchTemplate(search, template, cv2.TM_CCOEFF_NORMED)
            _minimum, maximum, _min_loc, location = cv2.minMaxLoc(correlation)
            samples.append({
                "seconds": round(seconds, 3), "score": round(float(maximum), 6),
                "visible": bool(maximum >= args.minimum_score),
                "match_top_left": [sx0 + location[0], sy0 + location[1]],
            })
    finally:
        capture.release()
    intervals = []
    open_start = None
    for sample in samples:
        if sample["visible"] and open_start is None:
            open_start = sample["seconds"]
        if not sample["visible"] and open_start is not None:
            intervals.append([open_start, sample["seconds"]])
            open_start = None
    if open_start is not None:
        intervals.append([open_start, min(frame_count / fps, samples[-1]["seconds"] + args.interval_seconds)])
    video_bytes = args.video.read_bytes()
    reference_bytes = args.reference.read_bytes()
    report = {
        "schema": "ck3.messina-battle-video-visibility-audit.v1",
        "video": {"path": str(args.video.resolve()), "bytes": len(video_bytes),
                  "sha256": hashlib.sha256(video_bytes).hexdigest().upper()},
        "reference": {"path": str(args.reference.resolve()), "bytes": len(reference_bytes),
                      "sha256": hashlib.sha256(reference_bytes).hexdigest().upper()},
        "fps": fps, "frame_count": frame_count, "duration_seconds": frame_count / fps,
        "sample_interval_seconds": args.interval_seconds,
        "minimum_score": args.minimum_score,
        "template_rect": list(DEFAULT_TEMPLATE_RECT),
        "search_rect": list(DEFAULT_SEARCH_RECT),
        "samples": samples,
        "visible_sample_count": sum(sample["visible"] for sample in samples),
        "visible_intervals_seconds": intervals,
    }
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"video": str(args.video), "duration_seconds": report["duration_seconds"],
                      "visible_samples": report["visible_sample_count"],
                      "total_samples": len(samples),
                      "visible_intervals_seconds": intervals}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
