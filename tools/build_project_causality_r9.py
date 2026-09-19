#!/usr/bin/env python3
"""Build the r9 non-music picture lock with fresh CoA and Robert footage."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[1]
R8 = ROOT / "artifacts/project-causality/2026-09-19-r8/project-causality-r8-nomusic-picture-lock.mp4"
R9_DIR = ROOT / "artifacts/project-causality/2026-09-19-r9"
WORK = R9_DIR / "work"
MANIFEST = ROOT / "promo/project_causality/r9/agent-showcase.json"
AGENT = WORK / "agent-showcase.mp4"
COA = R9_DIR / "coa-production-capture/coat-of-arms-editor-r9.webm"
OUTPUT = R9_DIR / "project-causality-r9-nomusic-picture-lock.mp4"
SIDECAR = OUTPUT.with_suffix(".video.json")
REPORTS = [
    R9_DIR / "evidence/fresh-opening-through-prewar.report.json",
    R9_DIR / "evidence/declaration-raise-siege.report.json",
    R9_DIR / "evidence/score50-through-victory.report.json",
]

FPS = 30
WIDTH = 2560
HEIGHT = 1440
PRE_FRAMES = 21619
COA_FRAMES = 1602
OLD_AGENT_END_FRAME = 34921
TAIL_FRAMES = 25822
AGENT_FRAMES = 12600
TOTAL_FRAMES = PRE_FRAMES + COA_FRAMES + AGENT_FRAMES + TAIL_FRAMES


class BuildError(RuntimeError):
    pass


def run(command: Sequence[str | Path]) -> None:
    print("RUN:", " ".join(str(value) for value in command), flush=True)
    completed = subprocess.run([str(value) for value in command], check=False)
    if completed.returncode:
        raise BuildError(f"command failed with exit code {completed.returncode}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def probe(ffprobe: str, path: Path) -> dict[str, Any]:
    result = subprocess.run(
        [ffprobe, "-v", "error", "-count_frames", "-show_streams", "-show_format", "-of", "json", path],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode:
        raise BuildError(result.stderr.strip() or f"ffprobe failed for {path}")
    return json.loads(result.stdout)


def reported_frames(ffprobe: str, path: Path) -> int:
    if not path.is_file():
        return 0
    data = probe(ffprobe, path)
    video = next((row for row in data["streams"] if row.get("codec_type") == "video"), {})
    return int(video.get("nb_read_frames") or video.get("nb_frames") or 0)


def build_agent(force: bool) -> None:
    sidecar = AGENT.with_suffix(".video.json")
    if AGENT.is_file() and sidecar.is_file() and not force:
        try:
            cached = json.loads(sidecar.read_text(encoding="utf-8"))
            if cached["manifest"]["sha256"].upper() == sha256(MANIFEST):
                print(f"REUSE: {AGENT}", flush=True)
                return
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            pass
    python = ROOT / "tools/.venv/Scripts/python.exe"
    if not python.is_file():
        shared = Path(r"Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe")
        python = shared if shared.is_file() else Path(sys.executable)
    command: list[str | Path] = [
        python,
        ROOT / "tools/build_full_agent_showcase.py",
        "--manifest", MANIFEST,
        "--output", AGENT,
        "--work-dir", WORK / "agent-build",
        "--preset", "ultrafast",
        "--crf", "18",
    ]
    if force:
        command.append("--force")
    run(command)


def encode_segment(ffmpeg: str, ffprobe: str, source: Path, start_frame: int, frames: int, output: Path, force: bool) -> None:
    if output.is_file() and not force and reported_frames(ffprobe, output) == frames and output.stat().st_mtime_ns >= source.stat().st_mtime_ns:
        print(f"REUSE: {output}", flush=True)
        return
    duration = frames / FPS
    start = start_frame / FPS
    temporary = output.with_name(f".{output.stem}.partial.mp4")
    temporary.unlink(missing_ok=True)
    run([
        ffmpeg, "-y", "-hide_banner", "-loglevel", "warning", "-ss", f"{start:.6f}", "-i", source,
        "-vf", f"fps={FPS},scale={WIDTH}:{HEIGHT}:flags=lanczos,setsar=1,trim=duration={duration:.6f},setpts=PTS-STARTPTS,format=yuv420p",
        "-af", f"aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,apad,atrim=duration={duration:.6f},asetpts=PTS-STARTPTS",
        "-frames:v", str(frames), "-c:v", "h264_nvenc", "-preset", "p6", "-tune", "hq", "-rc", "vbr", "-cq", "18", "-b:v", "0",
        "-g", "60", "-bf", "0", "-profile:v", "high", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-metadata:s:a:0", "language=zho", "-movflags", "+faststart", temporary,
    ])
    temporary.replace(output)


def encode_coa(ffmpeg: str, ffprobe: str, output: Path, force: bool) -> None:
    if output.is_file() and not force and reported_frames(ffprobe, output) == COA_FRAMES and output.stat().st_mtime_ns >= max(COA.stat().st_mtime_ns, R8.stat().st_mtime_ns):
        print(f"REUSE: {output}", flush=True)
        return
    duration = COA_FRAMES / FPS
    audio_start = PRE_FRAMES / FPS
    audio_end = (PRE_FRAMES + COA_FRAMES) / FPS
    temporary = output.with_name(f".{output.stem}.partial.mp4")
    temporary.unlink(missing_ok=True)
    graph = (
        f"[0:v]fps={FPS},scale={WIDTH}:{HEIGHT}:flags=lanczos,setsar=1,trim=duration={duration:.6f},setpts=PTS-STARTPTS,format=yuv420p[v];"
        f"[1:a]atrim=start={audio_start:.6f}:end={audio_end:.6f},asetpts=PTS-STARTPTS,aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,apad,atrim=duration={duration:.6f}[a]"
    )
    run([
        ffmpeg, "-y", "-hide_banner", "-loglevel", "warning", "-i", COA, "-i", R8,
        "-filter_complex", graph, "-map", "[v]", "-map", "[a]", "-frames:v", str(COA_FRAMES),
        "-c:v", "h264_nvenc", "-preset", "p6", "-tune", "hq", "-rc", "vbr", "-cq", "18", "-b:v", "0",
        "-g", "60", "-bf", "0", "-profile:v", "high", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-metadata:s:a:0", "language=zho", "-movflags", "+faststart", temporary,
    ])
    temporary.replace(output)


def assemble(ffmpeg: str, ffprobe: str, force: bool) -> list[Path]:
    segments_dir = WORK / "assembly-segments"
    segments_dir.mkdir(parents=True, exist_ok=True)
    pre = segments_dir / "00-r8-pre.mp4"
    coa = segments_dir / "01-coa.mp4"
    agent = segments_dir / "02-agent.mp4"
    tail = segments_dir / "03-r8-tail.mp4"
    encode_segment(ffmpeg, ffprobe, R8, 0, PRE_FRAMES, pre, force)
    encode_coa(ffmpeg, ffprobe, coa, force)
    encode_segment(ffmpeg, ffprobe, AGENT, 0, AGENT_FRAMES, agent, force)
    encode_segment(ffmpeg, ffprobe, R8, OLD_AGENT_END_FRAME, TAIL_FRAMES, tail, force)
    concat = segments_dir / "concat.ffconcat"
    concat.write_text(
        "ffconcat version 1.0\n" + "".join(f"file '{path.resolve().as_posix()}'\n" for path in (pre, coa, agent, tail)),
        encoding="utf-8",
    )
    temporary = OUTPUT.with_name(".project-causality-r9.partial.mp4")
    temporary.unlink(missing_ok=True)
    run([ffmpeg, "-y", "-hide_banner", "-loglevel", "warning", "-f", "concat", "-safe", "0", "-i", concat, "-c", "copy", "-movflags", "+faststart", temporary])
    temporary.replace(OUTPUT)
    return [pre, coa, agent, tail]


def validate(ffprobe: str, segments: list[Path]) -> None:
    data = probe(ffprobe, OUTPUT)
    video = next((row for row in data["streams"] if row.get("codec_type") == "video"), None)
    audio = next((row for row in data["streams"] if row.get("codec_type") == "audio"), None)
    if not video or not audio:
        raise BuildError("final video lacks video or audio")
    frames = int(video.get("nb_read_frames") or video.get("nb_frames") or 0)
    duration = float(data["format"]["duration"])
    if frames != TOTAL_FRAMES or (video.get("width"), video.get("height")) != (WIDTH, HEIGHT):
        raise BuildError(f"final geometry/frame validation failed: frames={frames}, geometry={video.get('width')}x{video.get('height')}")
    if video.get("codec_name") != "h264" or video.get("pix_fmt") != "yuv420p" or audio.get("codec_name") != "aac":
        raise BuildError("final codec validation failed")
    payload = {
        "schema": "project-causality-r9-picture-lock.v1",
        "title": "project因果律",
        "subtitle": "伪天司的辉煌愿景",
        "status": "non-music-picture-lock-candidate-awaiting-owner-review",
        "publication_authorized": False,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "music": {"included": False, "operator_boundary": "Suno was not opened or automated."},
        "video": {"path": str(OUTPUT.relative_to(ROOT)).replace("\\", "/"), "sha256": sha256(OUTPUT), "bytes": OUTPUT.stat().st_size, "duration_seconds": duration, "frames": frames, "width": video.get("width"), "height": video.get("height"), "fps": video.get("avg_frame_rate"), "codec": video.get("codec_name"), "pixel_format": video.get("pix_fmt")},
        "audio": {"codec": audio.get("codec_name"), "sample_rate": audio.get("sample_rate"), "channels": audio.get("channels"), "voice": "zh-CN-XiaoxiaoNeural"},
        "editorial": {"allowed_duration_seconds": {"minimum": 1200, "maximum": 2700}, "coa_replacement_frames": COA_FRAMES, "fresh_agent_showcase_frames": AGENT_FRAMES, "total_frames": TOTAL_FRAMES},
        "timeline": [
            {"id": "reviewed-r8-through-coa-intro", "start_frame": 0, "end_frame": PRE_FRAMES},
            {"id": "real-coat-of-arms-editor", "start_frame": PRE_FRAMES, "end_frame": PRE_FRAMES + COA_FRAMES},
            {"id": "fresh-robert-fixed-benchmark", "start_frame": PRE_FRAMES + COA_FRAMES, "end_frame": PRE_FRAMES + COA_FRAMES + AGENT_FRAMES},
            {"id": "reviewed-r8-method-principle-vision", "start_frame": PRE_FRAMES + COA_FRAMES + AGENT_FRAMES, "end_frame": TOTAL_FRAMES},
        ],
        "capability_boundary": {
            "classification": "production-live fixed Robert 1066 to Palermo benchmark",
            "proved": ["fresh ruler selection", "opening event decisions", "character and realm review", "Palermo target interaction", "war declaration", "raise and move", "ordinary-event recovery", "war-score observation", "enforce demands", "disband armies", "save checkpoint"],
            "not_claimed": ["arbitrary ruler planning", "arbitrary casus belli selection", "general multi-army war autonomy"],
            "shutdown_note": "The final run completed the gameplay milestone, while its shutdown attestation remained RED because the watchdog had already exited; the final process inventory was empty.",
        },
        "sources": [{"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)} for path in [R8, COA, MANIFEST, AGENT, *REPORTS, *segments]],
    }
    SIDECAR.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"VIDEO: {OUTPUT}")
    print(f"SIDECAR: {SIDECAR}")
    print(f"SHA256: {payload['video']['sha256']}")
    print(f"DURATION: {duration:.3f}s ({duration / 60:.2f} min)")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise BuildError("ffmpeg and ffprobe are required")
    for path in [R8, COA, MANIFEST, *REPORTS]:
        if not path.is_file():
            raise BuildError(f"missing required source: {path}")
    WORK.mkdir(parents=True, exist_ok=True)
    build_agent(args.force)
    if reported_frames(ffprobe, AGENT) != AGENT_FRAMES:
        raise BuildError("agent showcase does not contain exactly 12600 frames")
    segments = assemble(ffmpeg, ffprobe, args.force)
    validate(ffprobe, segments)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BuildError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
