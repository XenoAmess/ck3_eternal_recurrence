#!/usr/bin/env python3
"""Build the 20–45 minute Project Causality r8 picture lock.

The r8 edit preserves the reviewed r7 spine, replaces all four chapter gates,
adds a creator-value explanation, and expands the CK3 autonomous-player
section with both an honestly labelled archival Robert regression and current
production-live native loops.  It never launches CK3 and never opens Suno.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[1]
R7_DIR = ROOT / "artifacts" / "project-causality" / "2026-09-19-r7"
R7_VIDEO = R7_DIR / "project-causality-r7-nomusic-picture-lock.mp4"
OUTPUT_DIR = ROOT / "artifacts" / "project-causality" / "2026-09-19-r8"
WORK_DIR = OUTPUT_DIR / "work"
OUTPUT_VIDEO = OUTPUT_DIR / "project-causality-r8-nomusic-picture-lock.mp4"
OUTPUT_SIDECAR = OUTPUT_VIDEO.with_suffix(".video.json")
PROMO_DIR = ROOT / "promo" / "project_causality" / "r8"

ROBERT_RUN = Path(
    r"C:\Users\xenoa\AppData\Local\XarAutoplayer\runs\20260823T032552Z-dev-session-b4ded92f"
)
ROBERT_START = dt.datetime.fromisoformat("2026-08-23T03:27:00+00:00")
ROBERT_END = dt.datetime.fromisoformat("2026-08-23T05:43:00+00:00")
ROBERT_TIMELAPSE = WORK_DIR / "robert-archive-timelapse.mp4"

VALUE_MANIFEST = PROMO_DIR / "value-showcase.json"
AGENT_MANIFEST = PROMO_DIR / "agent-showcase.json"
GATE_MANIFEST = PROMO_DIR / "chapter-gates-showcase.json"
VALUE_VIDEO = WORK_DIR / "value-showcase.mp4"
AGENT_VIDEO = WORK_DIR / "agent-showcase.mp4"
GATE_VIDEO = WORK_DIR / "chapter-gates-showcase.mp4"

WIDTH = 2560
HEIGHT = 1440
FPS = 30
TARGET_FRAMES = 60743
TARGET_SECONDS = TARGET_FRAMES / FPS


class BuildError(RuntimeError):
    pass


def _run(command: Sequence[str | Path], *, cwd: Path | None = None) -> None:
    printable = " ".join(str(item) for item in command)
    print(f"RUN: {printable}", flush=True)
    result = subprocess.run(
        [str(item) for item in command],
        cwd=str(cwd) if cwd else None,
        check=False,
    )
    if result.returncode:
        raise BuildError(f"command failed with exit code {result.returncode}: {printable}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _probe(ffprobe: str, path: Path) -> dict[str, Any]:
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-count_frames",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode:
        raise BuildError(f"ffprobe failed for {path}: {result.stderr.strip()}")
    return json.loads(result.stdout)


def _reported_frames(path: Path) -> int:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe or not path.is_file():
        return 0
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=nb_frames",
            "-of",
            "default=nk=1:nw=1",
            str(path),
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    try:
        return int(result.stdout.strip()) if result.returncode == 0 else 0
    except ValueError:
        return 0


def _reported_start_time(path: Path) -> float:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe or not path.is_file():
        return 999.0
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=start_time",
            "-of",
            "default=nk=1:nw=1",
            str(path),
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    try:
        return float(result.stdout.strip()) if result.returncode == 0 else 999.0
    except ValueError:
        return 999.0


def _select_robert_frames() -> list[Path]:
    artifacts = ROBERT_RUN / "artifacts"
    if not artifacts.is_dir():
        raise BuildError(f"missing historical Robert run: {artifacts}")
    rows: list[tuple[dt.datetime, Path]] = []
    for observation in artifacts.glob("*.observation.json"):
        try:
            payload = json.loads(observation.read_text(encoding="utf-8"))
            captured_at = dt.datetime.fromisoformat(
                payload["policy_observation"]["captured_at"]
            )
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            continue
        if not ROBERT_START <= captured_at <= ROBERT_END:
            continue
        image = observation.with_name(
            observation.name.removesuffix(".observation.json") + ".png"
        )
        if image.is_file():
            rows.append((captured_at, image))
    rows.sort(key=lambda row: (row[0], row[1].name))
    if len(rows) < 600:
        raise BuildError(
            f"historical Robert interval has only {len(rows)} usable frames; expected at least 600"
        )
    selected: list[Path] = []
    for index in range(600):
        source_index = round(index * (len(rows) - 1) / 599)
        selected.append(rows[source_index][1])
    print(
        f"ROBERT: selected {len(selected)} of {len(rows)} real observation frames "
        f"from {ROBERT_START.isoformat()} through {ROBERT_END.isoformat()}",
        flush=True,
    )
    return selected


def _ffconcat_path(path: Path) -> str:
    return path.resolve().as_posix().replace("'", "'\\''")


def build_robert_timelapse(ffmpeg: str, *, force: bool) -> None:
    if ROBERT_TIMELAPSE.is_file() and not force:
        print(f"REUSE: {ROBERT_TIMELAPSE}", flush=True)
        return
    selected = _select_robert_frames()
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    concat = WORK_DIR / "robert-archive-frames.ffconcat"
    lines = ["ffconcat version 1.0"]
    for image in selected:
        lines.append(f"file '{_ffconcat_path(image)}'")
        lines.append("duration 0.5")
    lines.append(f"file '{_ffconcat_path(selected[-1])}'")
    concat.write_text("\n".join(lines) + "\n", encoding="utf-8")
    temporary = ROBERT_TIMELAPSE.with_name(".robert-archive-timelapse.partial.mp4")
    temporary.unlink(missing_ok=True)
    command: list[str | Path] = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "warning",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        concat,
        "-vf",
        f"scale={WIDTH}:{HEIGHT}:flags=lanczos,setsar=1,fps={FPS},format=yuv420p",
        "-t",
        "300",
        "-an",
        "-c:v",
        "h264_nvenc",
        "-preset",
        "p6",
        "-tune",
        "hq",
        "-rc",
        "vbr",
        "-cq",
        "18",
        "-b:v",
        "0",
        "-profile:v",
        "high",
        "-movflags",
        "+faststart",
        temporary,
    ]
    try:
        _run(command)
    except BuildError:
        temporary.unlink(missing_ok=True)
        fallback = command[:]
        encoder_index = fallback.index("h264_nvenc")
        fallback[encoder_index:] = [
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-profile:v",
            "high",
            "-movflags",
            "+faststart",
            temporary,
        ]
        _run(fallback)
    temporary.replace(ROBERT_TIMELAPSE)


def build_showcase(
    manifest: Path,
    output: Path,
    build_dir: Path,
    *,
    force: bool,
) -> None:
    sidecar = output.with_suffix(".video.json")
    if output.is_file() and sidecar.is_file() and not force:
        try:
            manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
            sidecar_payload = json.loads(sidecar.read_text(encoding="utf-8"))
            recorded_hash = sidecar_payload["manifest"]["sha256"]
            referenced: list[Path] = [manifest]
            for chapter in manifest_payload.get("chapters", []):
                for key in ("source", "sound_effect"):
                    value = chapter.get(key) if isinstance(chapter, dict) else None
                    if isinstance(value, str):
                        candidate = Path(value)
                        if not candidate.is_absolute():
                            candidate = (manifest.parent / candidate).resolve()
                        referenced.append(candidate)
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            pass
        else:
            if (
                recorded_hash.upper() == _sha256(manifest)
                and all(path.is_file() for path in referenced)
                and output.stat().st_mtime_ns
                >= max(path.stat().st_mtime_ns for path in referenced)
            ):
                print(f"REUSE: {output}", flush=True)
                return
    python = ROOT / "tools" / ".venv" / "Scripts" / "python.exe"
    if not python.is_file():
        shared_python = Path(r"Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe")
        python = shared_python if shared_python.is_file() else Path(sys.executable)
    command: list[str | Path] = [
        python,
        ROOT / "tools" / "build_full_agent_showcase.py",
        "--manifest",
        manifest,
        "--output",
        output,
        "--work-dir",
        build_dir,
        "--preset",
        "ultrafast",
        "--crf",
        "18",
    ]
    if force:
        command.append("--force")
    environment = os.environ.copy()
    environment.setdefault("XAR_PROMO_SOURCE", r"Z:\workspace\xar_promo_toolchain")
    printable = " ".join(str(item) for item in command)
    print(f"RUN: {printable}", flush=True)
    result = subprocess.run([str(item) for item in command], env=environment, check=False)
    if result.returncode:
        raise BuildError(
            f"showcase builder failed with exit code {result.returncode}: {manifest}"
        )


def assemble_final(ffmpeg: str, *, force: bool) -> None:
    required = [R7_VIDEO, VALUE_VIDEO, AGENT_VIDEO, GATE_VIDEO]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise BuildError("missing assembly inputs: " + ", ".join(missing))
    if (
        OUTPUT_VIDEO.is_file()
        and not force
        and _reported_frames(OUTPUT_VIDEO) == TARGET_FRAMES
        and OUTPUT_VIDEO.stat().st_mtime_ns
        >= max(path.stat().st_mtime_ns for path in required)
    ):
        print(f"REUSE: {OUTPUT_VIDEO}", flush=True)
        return

    # Render one exact-frame segment at a time.  A single graph with five
    # independent trims of the 25-minute r7 source forces FFmpeg to retain too
    # many decoded 1440p frames concurrently on Windows.
    slices = [
        (R7_VIDEO, 0.0, 4624),
        (VALUE_VIDEO, 0.0, 5400),
        (GATE_VIDEO, 0.0, 600),
        (R7_VIDEO, 174.133333, 12597),
        (AGENT_VIDEO, 0.0, 11700),
        (GATE_VIDEO, 20.0, 600),
        (R7_VIDEO, 689.266667, 10708),
        (GATE_VIDEO, 40.0, 600),
        (R7_VIDEO, 1066.2, 5986),
        (GATE_VIDEO, 60.0, 600),
        (R7_VIDEO, 1285.733333, 7328),
    ]
    if sum(row[2] for row in slices) != TARGET_FRAMES:
        raise BuildError("internal assembly slice frame total drifted")
    segment_dir = WORK_DIR / "assembly-segments"
    segment_dir.mkdir(parents=True, exist_ok=True)
    segment_paths: list[Path] = []
    for index, (source, start, frames) in enumerate(slices):
        segment = segment_dir / f"{index:02d}.mp4"
        segment_paths.append(segment)
        if (
            segment.is_file()
            and not force
            and _reported_frames(segment) == frames
            and abs(_reported_start_time(segment)) < 0.001
            and segment.stat().st_mtime_ns >= source.stat().st_mtime_ns
        ):
            print(f"REUSE: {segment}", flush=True)
            continue
        duration = frames / FPS
        temporary_segment = segment.with_name(f".{segment.stem}.partial.mp4")
        temporary_segment.unlink(missing_ok=True)
        common: list[str | Path] = [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "warning",
            "-ss",
            f"{start:.6f}",
            "-i",
            source,
            "-vf",
            (
                f"fps={FPS},scale={WIDTH}:{HEIGHT}:flags=lanczos,setsar=1,"
                f"tpad=stop_mode=clone:stop_duration=1,trim=duration={duration:.6f},"
                "setpts=PTS-STARTPTS,format=yuv420p"
            ),
            "-af",
            (
                "aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
                f"apad,atrim=duration={duration:.6f},asetpts=PTS-STARTPTS"
            ),
            "-frames:v",
            str(frames),
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-metadata:s:a:0",
            "language=zho",
            "-movflags",
            "+faststart",
        ]
        nvenc = [
            *common,
            "-c:v",
            "h264_nvenc",
            "-preset",
            "p6",
            "-tune",
            "hq",
            "-rc",
            "vbr",
            "-cq",
            "18",
            "-b:v",
            "0",
            "-g",
            "60",
            "-bf",
            "0",
            "-profile:v",
            "high",
            "-pix_fmt",
            "yuv420p",
            temporary_segment,
        ]
        try:
            _run(nvenc)
        except BuildError:
            temporary_segment.unlink(missing_ok=True)
            cpu = [
                *common,
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "18",
                "-g",
                "60",
                "-keyint_min",
                "60",
                "-sc_threshold",
                "0",
                "-bf",
                "0",
                "-profile:v",
                "high",
                "-pix_fmt",
                "yuv420p",
                temporary_segment,
            ]
            _run(cpu)
        temporary_segment.replace(segment)

    concat = segment_dir / "concat.ffconcat"
    concat.write_text(
        "ffconcat version 1.0\n"
        + "".join(f"file '{_ffconcat_path(path)}'\n" for path in segment_paths),
        encoding="utf-8",
    )
    temporary = OUTPUT_VIDEO.with_name(".project-causality-r8.partial.mp4")
    temporary.unlink(missing_ok=True)
    _run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "warning",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            concat,
            "-c:v",
            "copy",
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
            temporary,
        ]
    )
    temporary.replace(OUTPUT_VIDEO)


def validate_and_write_sidecar(ffprobe: str) -> None:
    if OUTPUT_SIDECAR.is_file():
        try:
            cached = json.loads(OUTPUT_SIDECAR.read_text(encoding="utf-8"))
            cached_video = cached["video"]
            current_sha256 = _sha256(OUTPUT_VIDEO)
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            pass
        else:
            if (
                cached_video.get("sha256") == current_sha256
                and cached.get("editorial", {}).get("actual_frames") == TARGET_FRAMES
            ):
                duration = float(cached["editorial"]["actual_seconds"])
                print(f"VIDEO: {OUTPUT_VIDEO}", flush=True)
                print(f"SIDECAR: {OUTPUT_SIDECAR}", flush=True)
                print(f"SHA256: {current_sha256}", flush=True)
                print(f"DURATION: {duration:.3f}s ({duration / 60:.2f} min)", flush=True)
                return
    probe = _probe(ffprobe, OUTPUT_VIDEO)
    streams = probe.get("streams", [])
    video = next((row for row in streams if row.get("codec_type") == "video"), None)
    audio = next((row for row in streams if row.get("codec_type") == "audio"), None)
    if not isinstance(video, dict) or not isinstance(audio, dict):
        raise BuildError("final video is missing a video or audio stream")
    frame_count = int(video.get("nb_read_frames") or video.get("nb_frames") or 0)
    duration = float(probe.get("format", {}).get("duration", 0.0))
    problems: list[str] = []
    if (video.get("width"), video.get("height")) != (WIDTH, HEIGHT):
        problems.append(f"geometry={video.get('width')}x{video.get('height')}")
    if video.get("codec_name") != "h264" or video.get("pix_fmt") != "yuv420p":
        problems.append(
            f"video={video.get('codec_name')}/{video.get('pix_fmt')}"
        )
    if audio.get("codec_name") != "aac" or str(audio.get("sample_rate")) != "48000":
        problems.append(
            f"audio={audio.get('codec_name')}/{audio.get('sample_rate')}"
        )
    if frame_count != TARGET_FRAMES:
        problems.append(f"frames={frame_count}, expected {TARGET_FRAMES}")
    if abs(duration - TARGET_SECONDS) > 0.15:
        problems.append(f"duration={duration:.3f}, expected {TARGET_SECONDS:.3f}")
    if problems:
        raise BuildError("final media validation failed: " + "; ".join(problems))

    timeline = [
        ("reviewed-r7-prologue", 0.0, 154.133333),
        ("creator-value-two-entries-four-gains", 154.133333, 334.133333),
        ("spell-gate-artistic-v2", 334.133333, 354.133333),
        ("reviewed-r7-spell-products", 354.133333, 774.033333),
        ("autonomous-player-expanded-live-evidence", 774.033333, 1164.033333),
        ("method-gate-artistic-v2", 1164.033333, 1184.033333),
        ("reviewed-r7-method", 1184.033333, 1540.966666),
        ("principle-gate-artistic-v2", 1540.966666, 1560.966666),
        ("reviewed-r7-principle", 1560.966666, 1760.499999),
        ("vision-gate-artistic-v2", 1760.499999, 1780.499999),
        ("reviewed-r7-vision-and-close", 1780.499999, TARGET_SECONDS),
    ]
    source_paths = [
        R7_VIDEO,
        VALUE_VIDEO,
        AGENT_VIDEO,
        GATE_VIDEO,
        ROBERT_RUN / "events.jsonl",
        VALUE_MANIFEST,
        AGENT_MANIFEST,
        GATE_MANIFEST,
    ]
    payload = {
        "schema": "project-causality-r8-picture-lock.v1",
        "title": "project因果律",
        "subtitle": "伪天司的辉煌愿景",
        "status": "non-music-picture-lock-candidate-awaiting-continuous-owner-review",
        "publication_authorized": False,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "music": {
            "included": False,
            "operator_boundary": "Suno was not opened or automated by this build.",
        },
        "editorial": {
            "allowed_duration_seconds": {"minimum": 1200, "maximum": 2700},
            "target_seconds": TARGET_SECONDS,
            "target_frames": TARGET_FRAMES,
            "actual_seconds": duration,
            "actual_frames": frame_count,
            "creator_value_insert_seconds": 180,
            "autonomous_player_insert_seconds": 390,
            "chapter_gate_seconds": 80,
        },
        "capability_boundary": {
            "historical_robert": (
                "Archived real observation sequence from a fixed Robert 1066 Palermo "
                "regression. It proves that path occurred; it is not a claim of current "
                "general war autonomy."
            ),
            "current_native_loops": (
                "Battle hold and owner-subset retreat are production-live loops for the "
                "exact recorded build. Notification acknowledgement is fixture-live."
            ),
        },
        "video": {
            "path": str(OUTPUT_VIDEO.relative_to(ROOT)).replace("\\", "/"),
            "sha256": _sha256(OUTPUT_VIDEO),
            "bytes": OUTPUT_VIDEO.stat().st_size,
            "codec": video.get("codec_name"),
            "width": video.get("width"),
            "height": video.get("height"),
            "fps": video.get("avg_frame_rate"),
            "pixel_format": video.get("pix_fmt"),
        },
        "audio": {
            "codec": audio.get("codec_name"),
            "sample_rate": audio.get("sample_rate"),
            "channels": audio.get("channels"),
        },
        "timeline": [
            {"id": item[0], "start_seconds": item[1], "end_seconds": item[2]}
            for item in timeline
        ],
        "sources": [
            {
                "path": str(path),
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
            for path in source_paths
        ],
    }
    OUTPUT_SIDECAR.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"VIDEO: {OUTPUT_VIDEO}", flush=True)
    print(f"SIDECAR: {OUTPUT_SIDECAR}", flush=True)
    print(f"SHA256: {payload['video']['sha256']}", flush=True)
    print(f"DURATION: {duration:.3f}s ({duration / 60:.2f} min)", flush=True)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--force", action="store_true", help="rebuild cached components")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise BuildError("ffmpeg and ffprobe must be on PATH")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    for path in (R7_VIDEO, VALUE_MANIFEST, AGENT_MANIFEST, GATE_MANIFEST):
        if not path.is_file():
            raise BuildError(f"required input is missing: {path}")
    build_robert_timelapse(ffmpeg, force=args.force)
    build_showcase(
        VALUE_MANIFEST,
        VALUE_VIDEO,
        WORK_DIR / "value-build",
        force=args.force,
    )
    build_showcase(
        AGENT_MANIFEST,
        AGENT_VIDEO,
        WORK_DIR / "agent-build",
        force=args.force,
    )
    build_showcase(
        GATE_MANIFEST,
        GATE_VIDEO,
        WORK_DIR / "gate-build",
        force=args.force,
    )
    assemble_final(ffmpeg, force=args.force)
    validate_and_write_sidecar(ffprobe)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BuildError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
