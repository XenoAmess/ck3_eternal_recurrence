"""Actual capture PTS and causal-in-time display sampling, never motion inference."""
from bisect import bisect_right
from fractions import Fraction
import math
import statistics

FRAME_PROBE_SCHEMA = "ck3-war-ai.gameplay-frame-timestamps.v2"
TIMING_POLICY = "actual-pts-current-frame-hold-v1"


def analyze_timestamps(payload):
    streams = payload.get("streams", [])
    if len(streams) != 1:
        raise ValueError("Frame probe must expose exactly one selected video stream")
    stream = streams[0]
    tick = Fraction(stream["time_base"])
    duration = Fraction(str(payload["format"]["duration"]))
    if tick <= 0 or duration <= 0:
        raise ValueError("Positive time base and duration required")
    frames = []
    for index, row in enumerate(payload.get("frames", [])):
        if "pts" not in row or "pts_time" not in row:
            raise ValueError(f"Decoded frame {index} lacks actual PTS")
        pts = int(row["pts"])
        seconds = Fraction(pts) * tick
        if abs(seconds - Fraction(str(row["pts_time"]))) > max(tick / 2, Fraction(1, 1000000)):
            raise ValueError("Frame PTS and reported seconds disagree")
        declared_ticks = row.get("duration", row.get("pkt_duration"))
        declared = (Fraction(int(declared_ticks))*tick if declared_ticks is not None else
                    Fraction(str(row.get("duration_time", row.get("pkt_duration_time", 0)))))
        if seconds < 0 or declared < 0:
            raise ValueError("Negative frame PTS or duration")
        frames.append({"decoded_index": index, "pts": pts, "pts_seconds": float(seconds),
                       "declared_duration_seconds": float(declared),
                       "declared_duration_ticks": int(declared_ticks) if declared_ticks is not None else None})
    if len(frames) < 2:
        raise ValueError("Fewer than two actual decoded frames")
    times = [Fraction(row["pts"]) * tick for row in frames]
    if any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError("Decoded PTS are not strictly increasing")
    if times[-1] >= duration:
        raise ValueError("Last frame PTS is not inside recording duration")
    gaps = [float(b-a) for a, b in zip(times, times[1:])]
    # Interior frame display lasts to the next actual PTS. At EOF there is no
    # next PTS: only a positive declared final-frame duration establishes support.
    tail = (Fraction(frames[-1]["declared_duration_ticks"])*tick
            if frames[-1]["declared_duration_ticks"] is not None else
            Fraction(str(frames[-1]["declared_duration_seconds"])))
    supported_end = min(duration, times[-1] + tail)
    tolerance = max(float(tick)/2 + 0.000002, 0.00001)
    max_error = max(abs(float(value) - index/30) for index, value in enumerate(times))
    contiguous = max_error <= tolerance
    count_matches = abs(len(frames)/30 - float(duration)) <= max(float(tick)+0.000002, 0.002)
    return {"stream": stream, "duration_seconds": float(duration), "frames": frames,
        "decoded_frame_count": len(frames), "nominal_30fps_frame_count": round(float(duration)*30),
        "first_pts_seconds": float(times[0]), "last_pts_seconds": float(times[-1]),
        "minimum_gap_seconds": min(gaps), "maximum_gap_seconds": max(gaps),
        "mean_gap_seconds": statistics.mean(gaps), "median_gap_seconds": statistics.median(gaps),
        "mean_observed_frame_rate": (len(frames)-1)/float(times[-1]-times[0]),
        "gaps_outside_30fps_quantization": [{"after_decoded_index": i,
            "begin_seconds": float(times[i]), "end_seconds": float(times[i+1]), "gap_seconds": gap}
            for i, gap in enumerate(gaps) if abs(gap-1/30) > float(tick)+0.000002],
        "maximum_zero_based_30fps_error_seconds": max_error,
        "time_base_quantization_tolerance_seconds": tolerance,
        "contiguous_zero_based_30fps": contiguous, "frame_count_matches_duration": count_matches,
        "capture_media_compatible": True, "capture_media_timing_policy": TIMING_POLICY,
        "supported_end_seconds": float(supported_end),
        "tail_support": "declared-final-frame-duration" if tail > 0 else "no-duration; stop-at-last-PTS",
        "sampling_quality": {"classification": "observed-CFR30" if contiguous and count_matches else "timestamped-non-CFR30",
            "decoded_frames_are_independent_observations": False,
            "motion_between_samples_observed": False,
            "absence_of_behavior_between_samples_proven": False,
            "note": "Frame count is decoded capture samples, not unique images. 30fps delivery does not improve source temporal resolution."}}


def display_sampling(timing, window, clean_begin):
    """Map each output timestamp to the most recent actual source frame.

    Reject unsupported starts/tails; an output frame's entire display interval
    must fit the selected time window. Large interior gaps remain disclosed.
    """
    if timing.get("schema") != FRAME_PROBE_SCHEMA or timing.get("capture_media_timing_policy") != TIMING_POLICY:
        raise ValueError("A fresh v2 actual-PTS report is required; old CFR-only compatibility is not reinterpreted")
    tick = Fraction(timing["stream"]["time_base"])
    frames = timing["frames"]
    times = [Fraction(row["pts"]) * tick for row in frames]
    start = Fraction(window["output_grid_first_frame"], 30)
    stop = Fraction(window["output_grid_stop_frame_exclusive"], 30)
    last_duration = (Fraction(frames[-1]["declared_duration_ticks"])*tick
                     if frames[-1].get("declared_duration_ticks") is not None else
                     Fraction(str(frames[-1]["declared_duration_seconds"])))
    supported_end = min(Fraction(str(timing["duration_seconds"])), times[-1] + last_duration)
    if start < times[0] or stop > supported_end:
        raise ValueError("Selected time window exceeds actual PTS/final-frame-duration support; no leading or tail padding")
    mapping = []
    for output_index in range(window["expected_frame_count"]):
        source_time = start + Fraction(output_index, 30)
        index = bisect_right(times, source_time) - 1
        if index < 0 or times[index] < Fraction(str(clean_begin)):
            raise ValueError("Current frame began outside the clean span; cannot borrow an unreviewed earlier frame")
        mapping.append({"output_frame": output_index, "output_pts_seconds": output_index/30,
            "source_time_seconds": float(source_time), "source_decoded_index": index,
            "source_pts": frames[index]["pts"], "source_pts_seconds": float(times[index])})
    first, last = mapping[0]["source_decoded_index"], mapping[-1]["source_decoded_index"]
    # Include one real future frame as a timing boundary where available. It is
    # never displayed before its PTS and is removed by the output frame limit.
    sentinel = min(bisect_right(times, stop), len(times)-1)
    denominator = math.lcm(tick.denominator, 30)
    if denominator > 2**31-1:
        raise ValueError("Exact source/output common time base exceeds FFmpeg rational range")
    selected_gaps = [float(times[i+1]-times[i]) for i in range(first, min(last+1, len(times)-1))]
    return {"policy": TIMING_POLICY, "output_fps": 30,
        "playback_speed": 1, "interpolation": False, "looping": False, "tail_padding": False,
        "first_source_decoded_index": first, "last_sampled_source_decoded_index": last,
        "decode_stop_frame_exclusive": sentinel+1,
        "source_frame_count_in_decode_window": sentinel+1-first,
        "distinct_source_frames_displayed": len({row["source_decoded_index"] for row in mapping}),
        "output_frame_count": len(mapping), "maximum_selected_gap_seconds": max(selected_gaps, default=0),
        "filter_time_base_denominator": denominator,
        "filter_start_offset_ticks": int(start*denominator), "mapping": mapping,
        "scope": "Current-frame display sampling at original 1x PTS; no new motion, causality or observation resolution."}
