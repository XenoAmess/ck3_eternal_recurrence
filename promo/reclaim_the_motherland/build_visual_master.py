"""Build the 96-second picture master from real CK3 evidence and approved art.

The shot manifest is attempt-specific and remains process evidence.  Video shots
are anchored to an immutable capture-timeline event instead of guessed wall-clock
timestamps; still shots retain their exact source hash in the output report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


EXPECTED_CHAPTERS = (
    ("prologue", 6.0),
    ("kaifeng", 9.0),
    ("fracture", 12.0),
    ("later_song", 12.0),
    ("reconquest", 12.0),
    ("restoration_decision", 12.0),
    ("edict", 12.0),
    ("restored", 8.0),
    ("title_card", 5.0),
    ("music_tail", 8.0),
)
TOTAL_SECONDS = 96.0


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as source:
        return json.load(source)


def validate_shot_manifest(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, dict) or value.get("kind") != "rmtm-visual-shot-manifest":
        raise ValueError("shot manifest has the wrong kind")
    shots = value.get("shots")
    if not isinstance(shots, list) or len(shots) != len(EXPECTED_CHAPTERS):
        raise ValueError("shot manifest must contain the ten approved chapters")
    validated: list[dict[str, Any]] = []
    for raw, (chapter_id, duration) in zip(shots, EXPECTED_CHAPTERS, strict=True):
        if not isinstance(raw, dict):
            raise ValueError(f"invalid shot entry for {chapter_id}")
        if raw.get("id") != chapter_id or float(raw.get("duration_seconds", -1)) != duration:
            raise ValueError(f"shot timing mismatch for {chapter_id}")
        kind = raw.get("source_kind")
        if kind not in {"still", "capture"}:
            raise ValueError(f"unsupported source kind for {chapter_id}: {kind!r}")
        source = Path(str(raw.get("source", ""))).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(f"missing source for {chapter_id}: {source}")
        normalized = dict(raw)
        normalized["source"] = source
        if kind == "capture":
            if not str(raw.get("anchor_event_suffix", "")).strip():
                raise ValueError(f"capture shot {chapter_id} needs anchor_event_suffix")
            normalized["lead_seconds"] = float(raw.get("lead_seconds", 0.0))
        validated.append(normalized)
    if abs(sum(duration for _, duration in EXPECTED_CHAPTERS) - TOTAL_SECONDS) > 0.001:
        raise AssertionError("internal approved timeline is not 96 seconds")
    return validated


def resolve_capture_start(
    timeline: dict[str, Any], anchor_event_suffix: str, lead_seconds: float
) -> float:
    events = timeline.get("events")
    if not isinstance(events, list):
        raise ValueError("capture timeline has no events")
    matches = [
        event
        for event in events
        if isinstance(event, dict)
        and str(event.get("path", "")).replace("\\", "/").endswith(anchor_event_suffix)
    ]
    if len(matches) != 1:
        raise ValueError(
            f"capture anchor {anchor_event_suffix!r} matched {len(matches)} events"
        )
    return max(0.0, float(matches[0]["seconds_from_capture_start"]) - lead_seconds)


def _video_filter(crop_mode: str) -> str:
    if crop_mode == "left_gameplay":
        return "crop=1920:1080:0:180,fps=30,format=yuv420p"
    if crop_mode != "full":
        raise ValueError(f"unsupported capture crop mode: {crop_mode!r}")
    return (
        "scale=1920:1080:force_original_aspect_ratio=increase,"
        "crop=1920:1080,fps=30,format=yuv420p"
    )


def _still_filter(motion: str) -> str:
    if motion == "pan_left":
        x = "max(0,(iw-iw/zoom)*(1-on/1800))"
    elif motion == "pan_right":
        x = "min(iw-iw/zoom,(iw-iw/zoom)*on/1800)"
    else:
        x = "iw/2-(iw/zoom/2)"
    return (
        "scale=2304:1296:force_original_aspect_ratio=increase,"
        "crop=2304:1296,"
        "zoompan="
        "z='min(max(zoom,pzoom)+0.00010,1.06)':"
        f"x='{x}':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps=30,"
        "format=yuv420p"
    )


def _segment_argv(
    ffmpeg: Path, shot: dict[str, Any], output: Path, timeline: dict[str, Any]
) -> tuple[list[str], float | None]:
    duration = float(shot["duration_seconds"])
    source = Path(shot["source"])
    if shot["source_kind"] == "capture":
        start = resolve_capture_start(
            timeline,
            str(shot["anchor_event_suffix"]),
            float(shot["lead_seconds"]),
        )
        command = [
            str(ffmpeg), "-hide_banner", "-loglevel", "error", "-y",
            "-ss", f"{start:.3f}", "-t", f"{duration:.3f}", "-i", str(source),
            "-vf", _video_filter(str(shot.get("crop_mode", "full"))),
        ]
    else:
        start = None
        command = [
            str(ffmpeg), "-hide_banner", "-loglevel", "error", "-y",
            "-loop", "1", "-framerate", "30", "-t", f"{duration:.3f}",
            "-i", str(source), "-vf", _still_filter(str(shot.get("motion", "zoom"))),
        ]
    command.extend(
        [
            "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "18",
            "-pix_fmt", "yuv420p", "-r", "30", "-t", f"{duration:.3f}",
            "-video_track_timescale", "90000", "-movflags", "+faststart", str(output),
        ]
    )
    return command, start


def _run(command: list[str], stdout_path: Path, stderr_path: Path) -> None:
    with stdout_path.open("x", encoding="utf-8") as stdout, stderr_path.open(
        "x", encoding="utf-8"
    ) as stderr:
        completed = subprocess.run(command, stdout=stdout, stderr=stderr, text=True)
    if completed.returncode != 0:
        raise RuntimeError(f"command failed ({completed.returncode}): {command}")


def _normalize_argv(ffmpeg: Path, intermediate: Path, output: Path) -> list[str]:
    """Pad sub-frame concat rounding and emit an exact 96-second master."""

    return [
        str(ffmpeg), "-hide_banner", "-loglevel", "error", "-y", "-i",
        str(intermediate), "-vf",
        "tpad=stop_mode=clone:stop_duration=0.2,fps=30,trim=duration=96,setpts=PTS-STARTPTS",
        "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt",
        "yuv420p", "-r", "30", "-t", "96.000", "-video_track_timescale", "90000",
        "-movflags", "+faststart", str(output),
    ]


def build(args: argparse.Namespace) -> int:
    attempt = args.attempt_directory.expanduser().resolve()
    if attempt.exists():
        raise FileExistsError(f"visual-master attempt already exists: {attempt}")
    attempt.mkdir(parents=True)
    segments = attempt / "segments"
    logs = attempt / "logs"
    segments.mkdir()
    logs.mkdir()

    manifest_path = args.shot_manifest.expanduser().resolve()
    manifest = _load_json(manifest_path)
    shots = validate_shot_manifest(manifest)
    timeline_path = args.capture_timeline.expanduser().resolve()
    timeline = _load_json(timeline_path)
    if timeline.get("kind") != "reclaim-promo-capture-timeline":
        raise ValueError("wrong capture timeline kind")
    ffmpeg = args.ffmpeg.expanduser().resolve()
    ffprobe = args.ffprobe.expanduser().resolve()

    report_rows: list[dict[str, Any]] = []
    segment_paths: list[Path] = []
    for index, shot in enumerate(shots, start=1):
        segment = segments / f"{index:02d}-{shot['id']}.mp4"
        command, capture_start = _segment_argv(ffmpeg, shot, segment, timeline)
        _write_json(
            logs / f"{index:02d}-{shot['id']}.command.json",
            {"argv": command, "shell": False},
        )
        _run(
            command,
            logs / f"{index:02d}-{shot['id']}.stdout.txt",
            logs / f"{index:02d}-{shot['id']}.stderr.txt",
        )
        segment_paths.append(segment)
        source = Path(shot["source"])
        report_rows.append(
            {
                "id": shot["id"],
                "source_kind": shot["source_kind"],
                "source": str(source),
                "source_sha256": _sha256(source),
                "anchor_event_suffix": shot.get("anchor_event_suffix"),
                "capture_start_seconds": capture_start,
                "duration_seconds": shot["duration_seconds"],
                "segment": str(segment),
                "segment_sha256": _sha256(segment),
            }
        )

    concat_list = attempt / "concat.txt"
    concat_list.write_text(
        "".join(f"file '{path.as_posix().replace(chr(39), chr(39) * 2)}'\n" for path in segment_paths),
        encoding="utf-8",
    )
    intermediate = attempt / "concat-intermediate.mp4"
    concat_command = [
        str(ffmpeg), "-hide_banner", "-loglevel", "error", "-y", "-f", "concat",
        "-safe", "0", "-i", str(concat_list), "-c", "copy", "-movflags", "+faststart",
        str(intermediate),
    ]
    _write_json(logs / "concat.command.json", {"argv": concat_command, "shell": False})
    _run(concat_command, logs / "concat.stdout.txt", logs / "concat.stderr.txt")

    output = attempt / "visual-master-a01.mp4"
    normalize_command = _normalize_argv(ffmpeg, intermediate, output)
    _write_json(logs / "normalize.command.json", {"argv": normalize_command, "shell": False})
    _run(normalize_command, logs / "normalize.stdout.txt", logs / "normalize.stderr.txt")

    probe_command = [
        str(ffprobe), "-v", "error", "-show_entries",
        "format=duration:stream=codec_type,width,height,avg_frame_rate,pix_fmt",
        "-of", "json", str(output),
    ]
    probe = subprocess.run(probe_command, check=True, capture_output=True, text=True)
    (attempt / "probe.stdout.json").write_text(probe.stdout, encoding="utf-8")
    (attempt / "probe.stderr.txt").write_text(probe.stderr, encoding="utf-8")
    probe_value = json.loads(probe.stdout)
    duration = float(probe_value["format"]["duration"])
    video_streams = [
        stream for stream in probe_value.get("streams", []) if stream.get("codec_type") == "video"
    ]
    result = (
        "GREEN"
        if abs(duration - TOTAL_SECONDS) <= 0.050
        and len(video_streams) == 1
        and video_streams[0].get("width") == 1920
        and video_streams[0].get("height") == 1080
        and video_streams[0].get("pix_fmt") == "yuv420p"
        else "RED"
    )
    report = {
        "format_version": 1,
        "kind": "rmtm-visual-master-build",
        "result": result,
        "shot_manifest": str(manifest_path),
        "shot_manifest_sha256": _sha256(manifest_path),
        "capture_timeline": str(timeline_path),
        "capture_timeline_sha256": _sha256(timeline_path),
        "shots": report_rows,
        "concat_intermediate": {
            "path": str(intermediate),
            "sha256": _sha256(intermediate),
            "bytes": intermediate.stat().st_size,
        },
        "output": {"path": str(output), "sha256": _sha256(output), "bytes": output.stat().st_size},
        "probe": probe_value,
        "process_material_retained": True,
    }
    _write_json(attempt / "report.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if result == "GREEN" else 1


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("--attempt-directory", required=True, type=Path)
    value.add_argument("--shot-manifest", required=True, type=Path)
    value.add_argument("--capture-timeline", required=True, type=Path)
    value.add_argument("--ffmpeg", required=True, type=Path)
    value.add_argument("--ffprobe", required=True, type=Path)
    return value


if __name__ == "__main__":
    raise SystemExit(build(parser().parse_args()))
