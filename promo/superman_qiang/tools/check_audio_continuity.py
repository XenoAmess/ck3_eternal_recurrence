"""Measure trailer audio sample coverage, steady music gain and encoded fidelity.

This check binds its results to actual movie bytes and retained lossless mix
stems. It does not perform, infer or grant a human playback signoff.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
from typing import Any

import numpy as np


SAMPLE_RATE = 48000
AAC_FRAME_SAMPLES = 1024
TIMESTAMP_TOLERANCE_SAMPLES = 2
DEFAULT_REFERENCE = Path(
    "C:/ck3-superman-qiang-promo-20261004/render-A0004/build/"
    "deliverables/superman-qiang-player-trailer.mp4"
)


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _correlation(left: np.ndarray, right: np.ndarray) -> float:
    a = left.reshape(-1).astype(np.float64)
    b = right.reshape(-1).astype(np.float64)
    denominator = math.sqrt(float(np.dot(a, a)) * float(np.dot(b, b)))
    return float(np.dot(a, b) / denominator) if denominator else 0.0


def _zero_runs(values: np.ndarray, absolute_start: int) -> list[dict[str, Any]]:
    """Find literal/nearly literal zero holes of at least 40 ms in both channels."""
    silent = np.max(np.abs(values), axis=1) <= 1e-7
    transitions = np.diff(np.concatenate(([False], silent, [False])).astype(np.int8))
    starts = np.flatnonzero(transitions == 1)
    ends = np.flatnonzero(transitions == -1)
    return [
        {"start_seconds": (absolute_start + int(start)) / SAMPLE_RATE,
         "end_seconds": (absolute_start + int(end)) / SAMPLE_RATE,
         "duration_seconds": int(end - start) / SAMPLE_RATE}
        for start, end in zip(starts, ends)
        if int(end - start) >= round(.04 * SAMPLE_RATE)
    ]


def check_audio_continuity(movie: Path, attempt: Path, output: Path) -> dict[str, Any]:
    """Write a fresh audit directory and return its machine-only result.

    ``continuous-mix.wav`` is the sum of the two retained pre-master stems;
    ``audio-mix-policy.json`` specifies the final constant master gain in dB.
    The music stem already contains its constant bed gain and opening/ending
    edits. This avoids mistaking natural changes in the music for mixer gain.
    """
    movie = movie.resolve(strict=True)
    attempt = attempt.resolve(strict=True)
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise RuntimeError("The verified interpreter environment needs ffmpeg and ffprobe on PATH")
    counter = 0

    def command(label: str, argv: list[str]) -> bytes:
        nonlocal counter
        counter += 1
        completed = subprocess.run(argv, capture_output=True)
        prefix = output / f"{counter:02d}-{label}"
        prefix.with_suffix(".stdout.txt").write_bytes(completed.stdout)
        prefix.with_suffix(".stderr.txt").write_bytes(completed.stderr)
        prefix.with_suffix(".command.json").write_text(
            json.dumps({"argv": argv, "exit_code": completed.returncode},
                       ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        completed.check_returncode()
        return completed.stdout

    def pcm(label: str, source: Path, *, align_timestamps: bool = False) -> np.ndarray:
        destination = output / f"{label}.f32le"
        argv = [ffmpeg, "-nostdin", "-hide_banner", "-v", "error", "-n",
                "-i", str(source), "-map", "0:a:0"]
        if align_timestamps:
            argv += ["-af", "aresample=48000:async=1:first_pts=0"]
        argv += ["-ar", str(SAMPLE_RATE), "-ac", "2", "-f", "f32le", str(destination)]
        command(f"decode-{label}", argv)
        if destination.stat().st_size % 8:
            raise ValueError("Decoded stereo float PCM has a partial sample")
        return np.memmap(destination, dtype="<f4", mode="r").reshape(-1, 2)

    timeline_path = attempt / "build/timeline.json"
    timeline = json.loads(timeline_path.read_bytes())
    total_samples = round(float(timeline["duration_seconds"]) * SAMPLE_RATE)
    policy_path = attempt / "build/audio-mix-policy.json"
    policy = json.loads(policy_path.read_bytes()) if policy_path.is_file() else {}
    master_gain_db = float(policy.get("master_gain_db", 1.0))
    master_gain = 10 ** (master_gain_db / 20)
    reference = Path(policy.get("reference_video_path", str(DEFAULT_REFERENCE))).resolve()
    checks: dict[str, bool] = {}
    diagnostics: dict[str, Any] = {}
    probe = json.loads(command("audio-packet-probe", [
        ffprobe, "-v", "error", "-select_streams", "a:0", "-show_packets",
        "-show_streams", "-of", "json", str(movie)]))
    stream = probe["streams"][0]
    packets = probe["packets"]
    time_base = Fraction(stream["time_base"])
    samples_per_tick = time_base * SAMPLE_RATE
    timestamps = [Fraction(int(packet["pts"])) * samples_per_tick for packet in packets]
    skip_samples = sum(int(item.get("skip_samples", 0))
                       for item in packets[0].get("side_data_list", []))
    skip_priming = timestamps[0] < 0 and skip_samples >= AAC_FRAME_SAMPLES
    first_content = 1 if skip_priming else 0
    packet_gaps = []
    for index in range(first_content, len(packets) - 1):
        interval = timestamps[index + 1] - timestamps[index]
        excess = interval - AAC_FRAME_SAMPLES
        if abs(excess) > TIMESTAMP_TOLERANCE_SAMPLES:
            packet_gaps.append({
                "packet_index": index,
                "start_seconds": float(timestamps[index] / SAMPLE_RATE),
                "next_seconds": float(timestamps[index + 1] / SAMPLE_RATE),
                "interval_samples": float(interval),
                "excess_samples": float(excess),
                "excess_seconds": float(excess / SAMPLE_RATE),
                "container_reported_duration": packets[index].get("duration"),
            })
    discard_padding = sum(int(item.get("discard_padding", 0))
                          for item in packets[-1].get("side_data_list", []))
    nominal_end = timestamps[-1] + AAC_FRAME_SAMPLES - discard_padding
    checks["aac_packet_clock_has_no_sample_holes"] = not packet_gaps
    checks["aac_starts_at_sample_zero_after_encoder_priming"] = (
        abs(timestamps[first_content]) <= TIMESTAMP_TOLERANCE_SAMPLES)
    checks["aac_packet_clock_covers_complete_movie"] = (
        abs(nominal_end - total_samples) <= TIMESTAMP_TOLERANCE_SAMPLES)
    diagnostics["packet_clock"] = {
        "time_base": str(time_base), "packet_count": len(packets),
        "encoder_priming_skip_samples": skip_samples,
        "first_content_sample": float(timestamps[first_content]),
        "end_sample": float(nominal_end), "gap_count": len(packet_gaps),
        "gaps": packet_gaps,
        "method": "PTS intervals checked against 1024 AAC samples, never against an inflated container packet duration",
    }
    actual = pcm("actual-audio", movie)
    aligned = pcm("timestamp-aligned-audio", movie, align_timestamps=True)
    checks["decoded_pcm_covers_all_planned_samples"] = (
        abs(len(actual) - total_samples) <= TIMESTAMP_TOLERANCE_SAMPLES)
    checks["timestamp_aligned_pcm_covers_all_planned_samples"] = (
        abs(len(aligned) - total_samples) <= TIMESTAMP_TOLERANCE_SAMPLES)
    diagnostics["sample_coverage"] = {"planned_samples": total_samples,
        "decoded_samples": len(actual), "timestamp_aligned_samples": len(aligned),
        "decoded_shortfall_seconds": (total_samples - len(actual)) / SAMPLE_RATE}

    cuts = []
    for row in timeline["scenes"][1:]:
        at = round(float(row["start_seconds"]) * SAMPLE_RATE)
        start, end = max(0, at - SAMPLE_RATE), min(total_samples, at + SAMPLE_RATE)
        holes = _zero_runs(aligned[start:min(end, len(aligned))], start)
        cuts.append({"scene": row["id"], "cut_seconds": at / SAMPLE_RATE,
                     "window_seconds": [start / SAMPLE_RATE, end / SAMPLE_RATE],
                     "zero_holes": holes,
                     "window_has_all_samples": len(aligned) >= end})
    checks["nine_cuts_have_complete_windows_without_zero_holes"] = (
        len(cuts) == 9 and all(not cut["zero_holes"] and cut["window_has_all_samples"] for cut in cuts))

    def video_hash(source: Path, label: str) -> str:
        value = command(label, [ffmpeg, "-nostdin", "-hide_banner", "-v", "error",
            "-i", str(source), "-map", "0:v:0", "-c", "copy", "-f", "hash",
            "-hash", "sha256", "-"]).decode("utf-8").strip()
        if not value.startswith("SHA256="):
            raise ValueError("Unexpected FFmpeg video hash response")
        return value.split("=", 1)[1].lower()

    actual_video_sha = video_hash(movie, "actual-elementary-video-hash")
    reference_video_sha = video_hash(reference, "reference-elementary-video-hash") if reference.is_file() else None
    checks["approved_a4_video_elementary_bytes_unchanged"] = (
        reference_video_sha is not None and actual_video_sha == reference_video_sha)
    diagnostics["video_identity"] = {"actual_elementary_sha256": actual_video_sha,
        "reference_path": str(reference), "reference_movie_sha256": _sha(reference) if reference.is_file() else None,
        "reference_elementary_sha256": reference_video_sha}

    stems = {name: attempt / f"build/intermediate/continuous-{name}.wav"
             for name in ("mix", "music", "voice")}
    checks["retained_lossless_stems_and_explicit_policy_exist"] = (
        policy_path.is_file() and "master_gain_db" in policy and all(path.is_file() for path in stems.values()))
    stem_bindings = [{"name": name, "path": str(path), "sha256": _sha(path) if path.is_file() else None}
                     for name, path in stems.items()]
    if all(path.is_file() for path in stems.values()):
        decoded = {name: pcm(name + "-reference", path) for name, path in stems.items()}
        checks["lossless_stems_cover_exactly_all_planned_samples"] = all(
            abs(len(values) - total_samples) <= TIMESTAMP_TOLERANCE_SAMPLES
            for values in decoded.values())
        length = min([total_samples, len(actual)] + [len(values) for values in decoded.values()])
        reference_mix = decoded["mix"][:length].astype(np.float64)
        expected = reference_mix * master_gain
        encoded = actual[:length].astype(np.float64)
        stem_sum = decoded["music"][:length].astype(np.float64) + decoded["voice"][:length].astype(np.float64)
        stem_error_peak = float(np.max(np.abs(reference_mix - stem_sum)))
        checks["lossless_mix_equals_music_plus_voice_before_master_gain"] = stem_error_peak <= 2e-6
        reference_power = float(np.mean(expected ** 2))
        error_power = float(np.mean((encoded - expected) ** 2))
        snr = 10 * math.log10(reference_power / max(error_power, 1e-30))
        correlation = _correlation(encoded, expected)
        fitted_gain = float(np.sum(encoded * expected) / max(float(np.sum(expected ** 2)), 1e-30))
        fitted_gain_db = 20 * math.log10(max(abs(fitted_gain), 1e-30))
        checks["encoded_audio_matches_continuous_mix_with_constant_master_gain"] = (
            correlation >= .98 and snr >= 18 and abs(fitted_gain_db) <= .25)
        diagnostics["mix_fidelity"] = {"compared_samples": length,
            "master_gain_db": master_gain_db, "correlation": correlation,
            "signal_to_error_db": snr, "fitted_gain_db_relative_to_expected": fitted_gain_db,
            "stem_sum_peak_error": stem_error_peak}
        for cut in cuts:
            start = round(cut["window_seconds"][0] * SAMPLE_RATE)
            end = min(length, round(cut["window_seconds"][1] * SAMPLE_RATE))
            blocks = []
            block_samples = round(.1 * SAMPLE_RATE)
            for offset in range(start, end - block_samples + 1, block_samples):
                tail = offset + block_samples
                voice = decoded["voice"][offset:tail]
                if float(np.max(np.abs(voice))) > 1e-6:
                    continue
                music = decoded["music"][offset:tail].astype(np.float64)
                encoded_music = actual[offset:tail].astype(np.float64)
                power = float(np.sum(music ** 2))
                if power / music.size <= 1e-10:
                    continue
                gain = float(np.sum(encoded_music * music) / power)
                blocks.append({"start_seconds": offset / SAMPLE_RATE,
                    "gain_db_relative_to_music_stem": 20 * math.log10(max(abs(gain), 1e-30)),
                    "correlation": _correlation(encoded_music, music)})
            gains = [block["gain_db_relative_to_music_stem"] for block in blocks]
            median = float(np.median(gains)) if gains else None
            cut["music_only_gain_blocks"] = blocks
            cut["median_music_gain_db"] = median
            cut["music_gain_range_db"] = max(gains) - min(gains) if gains else None
            cut["steady_music_gain_pass"] = (
                len(blocks) >= 4 and median is not None and abs(median - master_gain_db) <= .25
                and all(abs(value - master_gain_db) <= .5 for value in gains)
                and all(block["correlation"] >= .98 for block in blocks))
        checks["music_gain_is_constant_across_all_nine_cuts"] = all(
            cut["steady_music_gain_pass"] for cut in cuts) and len(cuts) == 9
    else:
        checks["lossless_stems_cover_exactly_all_planned_samples"] = False
        checks["lossless_mix_equals_music_plus_voice_before_master_gain"] = False
        checks["encoded_audio_matches_continuous_mix_with_constant_master_gain"] = False
        checks["music_gain_is_constant_across_all_nine_cuts"] = False

    diagnostics["cuts"] = cuts
    report = {"format_version": 1, "kind": "superman_qiang_audio_continuity_check",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "result": "PASS" if all(checks.values()) else "FAIL",
        "movie_path": str(movie), "movie_sha256": _sha(movie),
        "movie_bytes": movie.stat().st_size, "sample_rate": SAMPLE_RATE,
        "checks": checks, "diagnostics": diagnostics,
        "source_bindings": {"timeline_path": str(timeline_path), "timeline_sha256": _sha(timeline_path),
            "policy_path": str(policy_path), "policy_sha256": _sha(policy_path) if policy_path.is_file() else None,
            "lossless_stems": stem_bindings},
        "thresholds": {"timestamp_tolerance_samples": TIMESTAMP_TOLERANCE_SAMPLES,
            "zero_hole_minimum_seconds": .04, "zero_sample_absolute_limit": 1e-7,
            "fidelity_minimum_correlation": .98, "fidelity_minimum_signal_to_error_db": 18,
            "music_gain_median_tolerance_db": .25, "music_gain_block_tolerance_db": .5},
        "scope": "Machine measurements on actual movie bytes, packet times, decoded samples and lossless stems; natural source-music dynamics remain in the reference.",
        "human_full_playback": "not-recorded", "manual_signoff_granted": False}
    destination = output / "audio-continuity-check.json"
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report["report_path"] = str(destination)
    report["report_sha256"] = _sha(destination)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--movie", type=Path, required=True)
    parser.add_argument("--attempt-directory", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    args = parser.parse_args()
    report = check_audio_continuity(args.movie, args.attempt_directory, args.output_directory)
    print(json.dumps({key: report[key] for key in ("result", "checks", "report_path", "report_sha256")}, ensure_ascii=False))
    return 0 if report["result"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
