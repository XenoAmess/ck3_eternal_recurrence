#!/usr/bin/env python3
"""Build the retimed Project Causality r7 picture-lock with architecture motion.

This is a post-production build over the frozen r6 cue segments.  It preserves
the approved narration and chapter gates, removes only verified tail slack,
and replaces selected visual intervals with architecture plates derived from
the checked-in Mermaid atlas.  It never launches CK3, operates Suno, or uploads
media.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_R6 = ROOT / "artifacts" / "project-causality" / "2026-09-19-r6"
DEFAULT_OUTPUT_DIR = ROOT / "artifacts" / "project-causality" / "2026-09-19-r7"
DEFAULT_PLAN = ROOT / "promo" / "project_causality" / "30m" / "architecture-shot-plan.json"
DEFAULT_PLATES = DEFAULT_OUTPUT_DIR / "architecture-plates" / "manifest.json"
FPS = 30
TARGET_SECONDS = 1530
TARGET_FRAMES = TARGET_SECONDS * FPS
GATE_PREFIXES = {
    "03-spell-declaration",
    "10-method-declaration",
    "17-principle-declaration",
    "22-vision-declaration",
}


class R7BuildError(RuntimeError):
    """Raised when the r7 editorial contract cannot be built."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise R7BuildError(f"missing JSON: {path}") from exc
    except json.JSONDecodeError as exc:
        raise R7BuildError(
            f"invalid JSON: {path}:{exc.lineno}:{exc.colno}: {exc.msg}"
        ) from exc
    if not isinstance(value, dict):
        raise R7BuildError(f"JSON root must be an object: {path}")
    return value


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    os.replace(temporary, path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _find_program(override: str | None, name: str) -> Path:
    if override:
        candidate = Path(override)
        if candidate.is_file():
            return candidate.resolve()
        raise R7BuildError(f"{name} does not exist: {candidate}")
    resolved = shutil.which(name)
    if resolved:
        return Path(resolved).resolve()
    raise R7BuildError(f"{name} was not found")


def _run(command: list[str | Path], *, cwd: Path | None = None) -> None:
    completed = subprocess.run(
        [str(value) for value in command],
        cwd=cwd or ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        raise R7BuildError(
            f"command failed ({completed.returncode}): {' '.join(map(str, command[:8]))}\n"
            f"{completed.stdout[-5000:]}"
        )


def _probe(ffprobe: Path, path: Path, *, count_frames: bool = False) -> dict[str, Any]:
    command: list[str | Path] = [
        ffprobe,
        "-v",
        "error",
        "-show_streams",
        "-show_format",
    ]
    if count_frames:
        command.append("-count_frames")
    command.extend(["-of", "json", path])
    completed = subprocess.run(
        [str(value) for value in command],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        raise R7BuildError(f"ffprobe failed for {path}: {completed.stderr[-2000:]}")
    return json.loads(completed.stdout)


def _ceil_frames(seconds: float) -> int:
    return int(math.ceil(seconds * FPS - 1e-9))


def _allocate_integer(total: int, weights: list[float]) -> list[int]:
    if total < 0:
        raise R7BuildError("cannot allocate a negative frame budget")
    if not weights:
        return []
    weight_sum = sum(weights)
    if weight_sum <= 0:
        result = [0] * len(weights)
        for index in range(total):
            result[index % len(result)] += 1
        return result
    raw = [total * weight / weight_sum for weight in weights]
    result = [int(math.floor(value)) for value in raw]
    remaining = total - sum(result)
    order = sorted(range(len(raw)), key=lambda index: raw[index] - result[index], reverse=True)
    for index in order[:remaining]:
        result[index] += 1
    return result


def _retime_chapters(chapters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    minimum: list[int] = []
    available: list[int] = []
    old_frames: list[int] = []
    for chapter in chapters:
        old = int(round(float(chapter["duration_seconds"]) * FPS))
        segment_id = str(chapter["id"]).rsplit("-", 1)[0]
        if segment_id in GATE_PREFIXES:
            floor = old
        else:
            floor = _ceil_frames(float(chapter["narration_duration_seconds"]) + 0.25)
        if floor > old:
            raise R7BuildError(
                f"narration floor exceeds source slot for {chapter['id']}: {floor}>{old}"
            )
        minimum.append(floor)
        available.append(old - floor)
        old_frames.append(old)
    extra = TARGET_FRAMES - sum(minimum)
    if extra < 0 or extra > sum(available):
        raise R7BuildError(
            f"target {TARGET_FRAMES} frames is outside safe range "
            f"{sum(minimum)}..{sum(old_frames)}"
        )
    additions = _allocate_integer(extra, [float(value) for value in available])
    result: list[dict[str, Any]] = []
    old_cursor = 0
    new_cursor = 0
    for chapter, old, floor, addition in zip(chapters, old_frames, minimum, additions):
        frames = floor + addition
        result.append(
            {
                "id": chapter["id"],
                "index": int(chapter["index"]),
                "old_start_frame": old_cursor,
                "old_end_frame": old_cursor + old,
                "old_frames": old,
                "new_start_frame": new_cursor,
                "new_end_frame": new_cursor + frames,
                "new_frames": frames,
                "narration_duration_seconds": float(chapter["narration_duration_seconds"]),
                "source_segment": chapter["segment"]["path"],
            }
        )
        old_cursor += old
        new_cursor += frames
    if old_cursor != 1800 * FPS or new_cursor != TARGET_FRAMES:
        raise R7BuildError(
            f"retime did not close: source={old_cursor} target={new_cursor}"
        )
    return result


def _plate_index(manifest: dict[str, Any]) -> dict[tuple[str, int], Path]:
    result: dict[tuple[str, int], Path] = {}
    for row in manifest.get("plates", []):
        key = (str(row["shot_id"]), int(row["beat_index"]))
        path = ROOT / str(row["path"])
        if not path.is_file() or _sha256(path) != row.get("sha256"):
            raise R7BuildError(f"architecture plate is missing or stale: {path}")
        result[key] = path
    return result


def _source_beats(plan: dict[str, Any], plates: dict[tuple[str, int], Path]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for shot in plan.get("shots", []):
        for index, beat in enumerate(shot.get("beats", [])):
            kind = str(beat["kind"])
            row: dict[str, Any] = {
                "shot_id": str(shot["id"]),
                "diagram_id": str(shot["diagram_id"]),
                "beat_index": index,
                "kind": kind,
                "view": str(beat["view"]),
                "start_frame": int(round(float(beat["start"]) * FPS)),
                "end_frame": int(round(float(beat["end"]) * FPS)),
            }
            if kind.startswith("diagram"):
                try:
                    row["plate"] = plates[(row["shot_id"], index)]
                except KeyError as exc:
                    raise R7BuildError(
                        f"missing plate for {row['shot_id']} beat {index}"
                    ) from exc
            result.append(row)
    return result


def _pieces_for_chapter(
    chapter: dict[str, Any], beats: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    start = int(chapter["old_start_frame"])
    end = int(chapter["old_end_frame"])
    boundaries = {start, end}
    relevant: list[dict[str, Any]] = []
    for beat in beats:
        overlap_start = max(start, int(beat["start_frame"]))
        overlap_end = min(end, int(beat["end_frame"]))
        if overlap_start < overlap_end:
            relevant.append(beat)
            boundaries.add(overlap_start)
            boundaries.add(overlap_end)
    ordered = sorted(boundaries)
    pieces: list[dict[str, Any]] = []
    for left, right in zip(ordered, ordered[1:]):
        midpoint = (left + right) / 2
        active = next(
            (
                beat
                for beat in relevant
                if beat["start_frame"] <= midpoint < beat["end_frame"]
            ),
            None,
        )
        if active and str(active["kind"]).startswith("diagram"):
            kind = "diagram"
            plate = active["plate"]
            label = f"{active['shot_id']}:{active['view']}"
        else:
            kind = "original"
            plate = None
            label = "original" if active is None else f"{active['shot_id']}:live_cutaway"
        if pieces and pieces[-1]["kind"] == kind and pieces[-1].get("plate") == plate:
            pieces[-1]["source_end_frame"] = right
            pieces[-1]["label"] = label
        else:
            pieces.append(
                {
                    "kind": kind,
                    "plate": plate,
                    "label": label,
                    "source_start_frame": left,
                    "source_end_frame": right,
                }
            )
    weights = [
        float(piece["source_end_frame"] - piece["source_start_frame"])
        for piece in pieces
    ]
    allocated = _allocate_integer(int(chapter["new_frames"]), weights)
    for piece, frames in zip(pieces, allocated):
        piece["new_frames"] = frames
    return [piece for piece in pieces if piece["new_frames"] > 0]


def _seconds(frames: int) -> str:
    return f"{frames / FPS:.6f}"


def _segment_fingerprint(
    chapter: dict[str, Any],
    pieces: list[dict[str, Any]],
    plate_manifest_hash: str,
    preset: str,
) -> str:
    payload = {
        "schema": 2,
        "render_pipeline": "normalized-exact-30fps",
        "preset": preset,
        "source_segment_sha256": _sha256(Path(str(chapter["source_segment"]))),
        "new_frames": chapter["new_frames"],
        "pieces": [
            {
                key: (str(value) if isinstance(value, Path) else value)
                for key, value in piece.items()
            }
            for piece in pieces
        ],
        "plate_manifest_sha256": plate_manifest_hash,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode("utf-8")
    ).hexdigest().upper()


def _render_trimmed_segment(
    *,
    ffmpeg: Path,
    source: Path,
    destination: Path,
    frames: int,
    preset: str,
) -> None:
    duration = _seconds(frames)
    _run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            source,
            "-filter_complex",
            f"[0:v]fps={FPS},trim=end_frame={frames},setpts=N/({FPS}*TB),format=yuv420p[v];"
            f"[0:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
            f"apad,atrim=duration={duration},asetpts=N/SR/TB[a]",
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-r",
            str(FPS),
            "-c:v",
            "libx264",
            "-preset",
            preset,
            "-crf",
            "18",
            "-profile:v",
            "high",
            "-level:v",
            "5.1",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-movflags",
            "+faststart",
            destination,
        ]
    )


def _render_architecture_segment(
    *,
    ffmpeg: Path,
    chapter: dict[str, Any],
    source_manifest: dict[str, Any],
    pieces: list[dict[str, Any]],
    destination: Path,
    preset: str,
) -> None:
    source_segment = Path(str(chapter["source_segment"]))
    chapter_directory = source_segment.parent
    ass_source = chapter_directory / "chapter.zh-CN.ass"
    if not ass_source.is_file():
        raise R7BuildError(f"missing chapter subtitle source: {ass_source}")
    shutil.copy2(ass_source, destination.parent / "chapter.zh-CN.ass")

    command: list[str | Path] = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error"]
    filters: list[str] = []
    input_index = 0
    cue_source_start = int(chapter["old_start_frame"])
    for piece_index, piece in enumerate(pieces):
        duration = _seconds(int(piece["new_frames"]))
        if piece["kind"] == "diagram":
            command.extend(["-loop", "1", "-framerate", str(FPS), "-t", duration, "-i", piece["plate"]])
            filters.append(
                f"[{input_index}:v]scale=2560:1440:flags=lanczos,setsar=1,"
                f"fps={FPS},trim=duration={duration},setpts=PTS-STARTPTS[v{piece_index}]"
            )
        else:
            if source_manifest["type"] == "video_clip":
                local_source_offset = (
                    int(piece["source_start_frame"]) - cue_source_start
                ) / FPS
                source_offset = float(source_manifest.get("start_seconds", 0.0)) + local_source_offset
                command.extend(["-ss", f"{source_offset:.6f}", "-i", source_manifest["source"]])
                crop = (
                    "crop=ih*4/3:ih*3/4:(iw-ow)/2:0,"
                    if source_manifest.get("crop_embedded_lower_third") is True
                    else ""
                )
                filters.append(
                    f"[{input_index}:v]{crop}scale=2560:1440:force_original_aspect_ratio=decrease:flags=lanczos,"
                    f"pad=2560:1440:(ow-iw)/2:(oh-ih)/2:color=0x060910,setsar=1,fps={FPS},"
                    f"tpad=stop_mode=clone:stop_duration={duration},trim=duration={duration},"
                    f"setpts=PTS-STARTPTS[v{piece_index}]"
                )
            else:
                frame = chapter_directory / "frame.png"
                if not frame.is_file():
                    raise R7BuildError(f"missing clean visual frame: {frame}")
                command.extend(["-loop", "1", "-framerate", str(FPS), "-t", duration, "-i", frame])
                filters.append(
                    f"[{input_index}:v]scale=2560:1440:flags=lanczos,setsar=1,fps={FPS},"
                    f"trim=duration={duration},setpts=PTS-STARTPTS[v{piece_index}]"
                )
        input_index += 1

    audio_index = input_index
    command.extend(["-i", source_segment])
    video_inputs = "".join(f"[v{index}]" for index in range(len(pieces)))
    total_duration = _seconds(int(chapter["new_frames"]))
    filters.append(
        f"{video_inputs}concat=n={len(pieces)}:v=1:a=0[cat]"
    )
    filters.append(
        f"[cat]trim=duration={total_duration},setpts=PTS-STARTPTS,"
        "ass=chapter.zh-CN.ass,format=yuv420p[v]"
    )
    filters.append(
        f"[{audio_index}:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
        f"apad,atrim=duration={total_duration},asetpts=N/SR/TB[a]"
    )
    command.extend(
        [
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-r",
            str(FPS),
            "-c:v",
            "libx264",
            "-preset",
            preset,
            "-crf",
            "18",
            "-profile:v",
            "high",
            "-level:v",
            "5.1",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-movflags",
            "+faststart",
            destination,
        ]
    )
    _run(command, cwd=destination.parent)


def _concat(ffmpeg: Path, segments: list[Path], destination: Path) -> None:
    concat = destination.parent / "concat.txt"
    lines = []
    for segment in segments:
        escaped = segment.resolve().as_posix().replace("'", "'\\''")
        lines.append(f"file '{escaped}'")
    concat.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    _run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            concat,
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            destination,
        ]
    )


def _source_manifest_rows(source: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = source.get("chapters")
    if not isinstance(rows, list):
        raise R7BuildError("r6 manifest has no chapters")
    return {str(row["id"]): row for row in rows}


def build(args: argparse.Namespace) -> tuple[Path, Path]:
    ffmpeg = _find_program(args.ffmpeg, "ffmpeg")
    ffprobe = _find_program(args.ffprobe, "ffprobe")
    r6 = args.r6.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    source_sidecar_path = r6 / "project-causality-30m-nomusic-picture-lock.video.json"
    source_manifest_path = r6 / "project-causality-30m.manifest.json"
    source_video_path = r6 / "project-causality-30m-nomusic-picture-lock.mp4"
    source_sidecar = _load_json(source_sidecar_path)
    source_manifest = _load_json(source_manifest_path)
    source_rows = _source_manifest_rows(source_manifest)
    chapters = source_sidecar.get("chapters")
    if not isinstance(chapters, list) or len(chapters) != 86:
        raise R7BuildError("r6 sidecar must contain the frozen 86 cues")
    timeline = _retime_chapters(chapters)

    plan_path = args.plan.expanduser().resolve()
    plates_path = args.plates.expanduser().resolve()
    plan = _load_json(plan_path)
    plate_manifest = _load_json(plates_path)
    if plate_manifest.get("plan_sha256") != _sha256(plan_path):
        raise R7BuildError("architecture plates are stale against the shot plan")
    plates = _plate_index(plate_manifest)
    beats = _source_beats(plan, plates)
    plate_manifest_hash = _sha256(plates_path)

    work = output_dir / "work"
    segment_dir = work / "segments"
    segment_dir.mkdir(parents=True, exist_ok=True)
    segment_paths: list[Path] = []
    edit_rows: list[dict[str, Any]] = []
    architecture_frames = 0
    for index, chapter in enumerate(timeline):
        chapter_id = str(chapter["id"])
        source_row = source_rows.get(chapter_id)
        if source_row is None:
            raise R7BuildError(f"missing r6 manifest row for {chapter_id}")
        pieces = _pieces_for_chapter(chapter, beats)
        architecture_frames += sum(
            int(piece["new_frames"]) for piece in pieces if piece["kind"] == "diagram"
        )
        cue_dir = segment_dir / f"{index:03d}-{chapter_id}"
        cue_dir.mkdir(parents=True, exist_ok=True)
        segment = cue_dir / "segment.mp4"
        record_path = cue_dir / "segment.build.json"
        fingerprint = _segment_fingerprint(
            chapter, pieces, plate_manifest_hash, args.preset
        )
        cached = False
        if not args.force and segment.is_file() and record_path.is_file():
            try:
                cached = _load_json(record_path).get("fingerprint") == fingerprint
            except R7BuildError:
                cached = False
        if not cached:
            print(
                f"[{index + 1:02d}/{len(timeline)}] "
                f"{'ARCH' if any(piece['kind'] == 'diagram' for piece in pieces) else 'TRIM'} "
                f"{chapter_id} -> {_seconds(int(chapter['new_frames']))}s",
                flush=True,
            )
            if any(piece["kind"] == "diagram" for piece in pieces):
                _render_architecture_segment(
                    ffmpeg=ffmpeg,
                    chapter=chapter,
                    source_manifest=source_row,
                    pieces=pieces,
                    destination=segment,
                    preset=args.preset,
                )
            else:
                _render_trimmed_segment(
                    ffmpeg=ffmpeg,
                    source=Path(str(chapter["source_segment"])),
                    destination=segment,
                    frames=int(chapter["new_frames"]),
                    preset=args.preset,
                )
            _atomic_json(
                record_path,
                {
                    "schema": "project-causality-r7-segment.v1",
                    "fingerprint": fingerprint,
                    "id": chapter_id,
                    "frames": chapter["new_frames"],
                    "architecture": any(piece["kind"] == "diagram" for piece in pieces),
                    "sha256": _sha256(segment),
                },
            )
        segment_paths.append(segment)
        edit_rows.append(
            {
                **chapter,
                "new_start_seconds": chapter["new_start_frame"] / FPS,
                "new_end_seconds": chapter["new_end_frame"] / FPS,
                "new_duration_seconds": chapter["new_frames"] / FPS,
                "pieces": [
                    {
                        **{
                            key: value
                            for key, value in piece.items()
                            if key != "plate"
                        },
                        **(
                            {"plate": Path(piece["plate"]).relative_to(ROOT).as_posix()}
                            if piece.get("plate")
                            else {}
                        ),
                        "new_duration_seconds": piece["new_frames"] / FPS,
                    }
                    for piece in pieces
                ],
                "segment": segment.relative_to(ROOT).as_posix(),
                "segment_sha256": _sha256(segment),
            }
        )

    output = output_dir / "project-causality-r7-nomusic-picture-lock.mp4"
    print(f"CONCAT: {len(segment_paths)} segments", flush=True)
    _concat(ffmpeg, segment_paths, output)
    media = _probe(ffprobe, output, count_frames=True)
    video_stream = next(
        (row for row in media.get("streams", []) if row.get("codec_type") == "video"),
        None,
    )
    audio_stream = next(
        (row for row in media.get("streams", []) if row.get("codec_type") == "audio"),
        None,
    )
    if video_stream is None or audio_stream is None:
        raise R7BuildError("r7 output is missing video or audio")
    frame_count = int(video_stream.get("nb_read_frames") or video_stream.get("nb_frames") or 0)
    duration = float(media.get("format", {}).get("duration", 0.0))
    if frame_count != TARGET_FRAMES:
        raise R7BuildError(
            f"r7 has {frame_count} video frames; expected {TARGET_FRAMES}"
        )
    if abs(duration - TARGET_SECONDS) > 0.08:
        raise R7BuildError(f"r7 duration is {duration:.6f}s; expected about {TARGET_SECONDS}s")

    sidecar = output.with_suffix(".video.json")
    payload = {
        "schema": "project-causality-r7-picture-lock.v1",
        "title": "project因果律",
        "subtitle": "伪天司的辉煌愿景",
        "status": "non-music-picture-lock-candidate-awaiting-continuous-owner-review",
        "publication_authorized": False,
        "music": {
            "included": False,
            "operator_boundary": "Suno was not opened or automated by this build.",
        },
        "source": {
            "r6_video": source_video_path.relative_to(ROOT).as_posix(),
            "r6_video_sha256": _sha256(source_video_path),
            "r6_sidecar": source_sidecar_path.relative_to(ROOT).as_posix(),
            "r6_sidecar_sha256": _sha256(source_sidecar_path),
            "r6_manifest": source_manifest_path.relative_to(ROOT).as_posix(),
            "r6_manifest_sha256": _sha256(source_manifest_path),
            "architecture_plan": plan_path.relative_to(ROOT).as_posix(),
            "architecture_plan_sha256": _sha256(plan_path),
            "architecture_plates": plates_path.relative_to(ROOT).as_posix(),
            "architecture_plates_sha256": plate_manifest_hash,
        },
        "editorial": {
            "target_seconds": TARGET_SECONDS,
            "target_frames": TARGET_FRAMES,
            "actual_seconds": duration,
            "actual_frames": frame_count,
            "architecture_seconds": architecture_frames / FPS,
            "chapter_count": len(edit_rows),
            "retime_policy": "preserve narration and gates; remove only cue tail slack; proportionally retime architecture beats",
        },
        "video": {
            "path": output.relative_to(ROOT).as_posix(),
            "sha256": _sha256(output),
            "bytes": output.stat().st_size,
            "codec": video_stream.get("codec_name"),
            "width": video_stream.get("width"),
            "height": video_stream.get("height"),
            "fps": video_stream.get("avg_frame_rate"),
            "pixel_format": video_stream.get("pix_fmt"),
        },
        "audio": {
            "codec": audio_stream.get("codec_name"),
            "sample_rate": audio_stream.get("sample_rate"),
            "channels": audio_stream.get("channels"),
        },
        "chapters": edit_rows,
    }
    _atomic_json(sidecar, payload)
    print(f"VIDEO:   {output}")
    print(f"SIDECAR: {sidecar}")
    return output, sidecar


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--r6", type=Path, default=DEFAULT_R6)
    result.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    result.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    result.add_argument("--plates", type=Path, default=DEFAULT_PLATES)
    result.add_argument("--ffmpeg")
    result.add_argument("--ffprobe")
    result.add_argument("--preset", default="veryfast")
    result.add_argument("--force", action="store_true")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        build(args)
        return 0
    except (R7BuildError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
