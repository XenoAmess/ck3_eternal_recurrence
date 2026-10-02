"""Source-bound frame-PTS continuity gate for one real Episode 2 clean span.

A recorder's ENCODED_UNREVIEWED result says only that a raw file was encoded.
An entire raw may have gaps while a later, independently selected clean span is
continuous. This contract checks the exact preserved full ffprobe frame table.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
import json
from pathlib import Path

from .episode_two_subtitle_contract import identity


MAX_FRAME_GAP_SECONDS = Decimal("0.2")


def _seconds(value: object, label: str) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{label} has no finite frame-PTS time") from exc
    if not number.is_finite():
        raise ValueError(f"{label} has no finite frame-PTS time")
    return number


def _binding(value: object, actual: dict, label: str) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"{label} lacks file identity")
    if (value.get("bytes") != actual["bytes"]
            or str(value.get("sha256", "")).upper() != actual["sha256"]):
        raise ValueError(f"{label} does not bind preserved original bytes")


def validate_pts_span(raw: Path, full_probe: Path, recorder_final: Path,
                      begin_seconds: float, end_seconds: float,
                      *, verified_raw_identity: dict | None = None) -> dict:
    """Reject a span that has missing/nonmonotonic PTS or a >200 ms frame gap.

    The frame table must be the *full* recorder ffprobe JSON bound by that
    recorder's final receipt. `begin_seconds` and `end_seconds` come from the
    CK3 adapter-verified clean span, not nearest-frame navigation hints.
    """
    raw = raw.resolve(strict=True)
    full_probe = full_probe.resolve(strict=True)
    recorder_final = recorder_final.resolve(strict=True)
    # The native-run artifact gate (or production preflight) already hashed a
    # potentially gigabyte-sized raw. Reuse only that caller-verified identity.
    raw_identity = verified_raw_identity if verified_raw_identity is not None else identity(raw)
    if (type(raw_identity.get("bytes")) is not int
            or raw.stat().st_size != raw_identity["bytes"]
            or not isinstance(raw_identity.get("sha256"), str)
            or len(raw_identity["sha256"]) != 64):
        raise ValueError("Recorder raw identity is incomplete or changed")
    probe_identity = identity(full_probe)
    final_identity = identity(recorder_final)
    final = json.loads(recorder_final.read_text(encoding="utf-8"))
    if (final.get("schema") != "xar.war-promo.bounded-recorder-final/v1"
            or final.get("result") != "ENCODED_UNREVIEWED"
            or final.get("ffmpeg_exit_code") != 0
            or final.get("ffprobe_exit_code") != 0
            or final.get("video_pts_complete") is not True):
        raise ValueError("PTS source lacks an encoded recorder-final receipt")
    _binding(final.get("raw"), raw_identity, "recorder raw")
    _binding(final.get("ffprobe_output"), probe_identity, "recorder full ffprobe")
    probe = json.loads(full_probe.read_text(encoding="utf-8"))
    video = [row for row in probe.get("streams", []) if row.get("codec_type") == "video"]
    if len(video) != 1 or type(video[0].get("index")) is not int:
        raise ValueError("Full ffprobe needs exactly one indexed video stream")
    index = video[0]["index"]
    begin = _seconds(begin_seconds, "clean span begin")
    end = _seconds(end_seconds, "clean span end")
    if begin < 0 or end <= begin:
        raise ValueError("Clean span has invalid PTS bounds")
    selected: list[Decimal] = []
    all_video = 0
    first_video_pts = None
    last_video_pts = None
    for frame in probe.get("frames", []):
        if frame.get("stream_index") != index:
            continue
        all_video += 1
        raw_pts = frame.get("best_effort_timestamp_time")
        if raw_pts is None:
            raw_pts = frame.get("pts_time")
        if raw_pts is None:
            raise ValueError("A video frame lacks exact PTS in full ffprobe")
        pts = _seconds(raw_pts, "video frame")
        if first_video_pts is None:
            first_video_pts = pts
        last_video_pts = pts
        if begin <= pts <= end:
            selected.append(pts)
    if all_video < 2 or len(selected) < 2:
        raise ValueError("Clean span lacks two exact video-frame PTS")
    recorded = final.get("frame_pts_by_stream", {}).get(str(index), {})
    if (recorded.get("count") != all_video
            or _seconds(recorded.get("first_pts_time"), "recorder first frame") != first_video_pts
            or _seconds(recorded.get("last_pts_time"), "recorder last frame") != last_video_pts):
        raise ValueError("Full frame table differs from the recorder-final frame summary")
    if (selected[0] - begin > MAX_FRAME_GAP_SECONDS
            or end - selected[-1] > MAX_FRAME_GAP_SECONDS):
        raise ValueError("Clean span boundary lies in an unrecorded PTS gap")
    largest = Decimal(0)
    for previous, current in zip(selected, selected[1:]):
        gap = current - previous
        if gap <= 0 or gap > MAX_FRAME_GAP_SECONDS:
            raise ValueError(f"Clean span crosses a missing/nonmonotonic frame-PTS gap: {gap}s")
        largest = max(largest, gap)
    return {"result": "PTS_CONTINUOUS_SPAN_UNREVIEWED",
            "raw": raw_identity, "full_ffprobe": probe_identity,
            "recorder_final": final_identity,
            "begin_seconds": str(begin), "end_seconds": str(end),
            "frame_count": len(selected), "largest_frame_gap_seconds": str(largest),
            "max_frame_gap_seconds": str(MAX_FRAME_GAP_SECONDS),
            "human_visual_review_completed": False}
