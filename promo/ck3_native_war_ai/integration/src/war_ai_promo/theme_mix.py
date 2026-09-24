"""Mix the single series theme into a new episode review candidate.

The video stream and chapter table come from the rendered source film.
This project-specific wrapper uses xar-promo's deterministic audio planner; its
FFmpeg command has no voice gain, duck windows, or automatic normalization.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from xar_promo.audio import AudioMixSpec, AudioStem, plan_audio_mix


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _probe(ffprobe: str, path: Path) -> dict:
    result = subprocess.run(
        [ffprobe, "-v", "error", "-show_format", "-show_streams", "-show_chapters", "-of", "json", str(path)],
        check=True,
        capture_output=True,
    )
    return json.loads(result.stdout.decode("utf-8"))


def _one_stream(probe: dict, codec_type: str) -> dict:
    streams = [stream for stream in probe["streams"] if stream["codec_type"] == codec_type]
    if len(streams) != 1:
        raise ValueError(f"expected one {codec_type} stream, got {len(streams)}")
    return streams[0]


def _chapter_signature(probe: dict) -> list[tuple[str, float, float]]:
    return [
        (
            chapter.get("tags", {}).get("title", ""),
            float(chapter["start_time"]),
            float(chapter["end_time"]),
        )
        for chapter in probe["chapters"]
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--film", type=Path, required=True)
    parser.add_argument("--music", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--work-directory", type=Path, required=True)
    parser.add_argument("--music-gain-db", type=float, default=-17.0)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--ffprobe", default="ffprobe")
    args = parser.parse_args()

    film = args.film.resolve(strict=True)
    music = args.music.resolve(strict=True)
    output = args.output.resolve()
    work = args.work_directory.resolve()
    if not math.isfinite(args.music_gain_db) or not -120 <= args.music_gain_db <= 0:
        parser.error("--music-gain-db must be a finite number between -120 and 0")
    if output.exists() or work.exists():
        parser.error("output and work directory must be new; use a fresh attempt")
    if output.suffix.lower() != ".mp4":
        parser.error("output must be an MP4 file")

    film_probe = _probe(args.ffprobe, film)
    music_probe = _probe(args.ffprobe, music)
    film_video = _one_stream(film_probe, "video")
    film_audio = _one_stream(film_probe, "audio")
    music_audio = _one_stream(music_probe, "audio")
    if any(stream["codec_type"] == "video" for stream in music_probe["streams"]):
        raise ValueError("music must be an audio-only file")
    if int(film_audio["sample_rate"]) != 48000 or film_audio["channels"] != 2:
        raise ValueError("source film must have 48 kHz stereo audio")
    if int(music_audio["sample_rate"]) != 48000 or music_audio["channels"] != 2:
        raise ValueError("series theme must have 48 kHz stereo audio")
    duration = float(film_probe["format"]["duration"])
    if duration <= 0:
        raise ValueError("source film has no positive duration")

    spec = AudioMixSpec(
        stems=(
            AudioStem(stem_id="source-film-narration", path=film, gain_db=0.0),
            AudioStem(
                stem_id="single-series-theme-loop",
                path=music,
                gain_db=args.music_gain_db,
                fade_in_seconds=2.0,
                fade_out_seconds=8.0,
            ),
        ),
        duration_seconds=duration,
        sample_rate=48000,
        channels=2,
        normalize=False,
        metadata={"policy": "one theme, fixed music gain, voice unchanged, no ducking"},
    )
    plan = plan_audio_mix(spec, output_label="theme_mix")
    partial = output.with_name(output.stem + ".partial.mp4")
    if partial.exists():
        parser.error(f"partial output already exists: {partial}")
    work.mkdir(parents=True)
    output.parent.mkdir(parents=True, exist_ok=True)

    argv = [
        args.ffmpeg,
        "-nostdin", "-hide_banner", "-loglevel", "warning", "-n",
        "-i", str(film),
        "-stream_loop", "-1", "-i", str(music),
        "-filter_complex", plan.filtergraph,
        "-map", "0:v:0", "-map", "[theme_mix]",
        "-map_chapters", "0", "-map_metadata", "0",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-movflags", "+faststart", "-t", f"{duration:.6f}",
        "-progress", str(work / "ffmpeg-progress.txt"),
        str(partial),
    ]
    receipt = {
        "schema": "ck3-war-ai-theme-remix.v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "state": "started",
        "source_film": {"path": str(film), "bytes": film.stat().st_size, "sha256": _sha256(film)},
        "music": {"path": str(music), "bytes": music.stat().st_size, "sha256": _sha256(music)},
        "mix": plan.to_mapping(),
        "music_gain_db": args.music_gain_db,
        "voice_gain_db": 0.0,
        "duck_windows": [],
        "automatic_normalization": False,
        "music_loop": "FFmpeg -stream_loop -1 on the same source WAV",
        "argv": argv,
        "output": str(output),
    }
    receipt_path = work / "theme-mix-receipt.json"
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (work / "ffmpeg-stdout.txt").open("wb") as stdout, (work / "ffmpeg-stderr.txt").open("wb") as stderr:
        result = subprocess.run(argv, stdout=stdout, stderr=stderr, check=False)
    receipt["ffmpeg_exit_code"] = result.returncode
    receipt["partial"] = str(partial) if partial.exists() else None
    if result.returncode != 0:
        receipt["state"] = "render-failed"
        receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return result.returncode

    output_probe = _probe(args.ffprobe, partial)
    output_video = _one_stream(output_probe, "video")
    output_audio = _one_stream(output_probe, "audio")
    if any(output_video[key] != film_video[key] for key in ("codec_name", "width", "height", "r_frame_rate")):
        raise ValueError("rendered video stream properties differ from source film")
    if output_audio["codec_name"] != "aac" or int(output_audio["sample_rate"]) != 48000 or output_audio["channels"] != 2:
        raise ValueError("rendered audio is not 48 kHz stereo AAC")
    source_chapters = _chapter_signature(film_probe)
    rendered_chapters = _chapter_signature(output_probe)
    if len(source_chapters) != len(rendered_chapters) or any(
        source[0] != rendered[0] or abs(source[1] - rendered[1]) > 0.002 or abs(source[2] - rendered[2]) > 0.002
        for source, rendered in zip(source_chapters, rendered_chapters)
    ):
        raise ValueError("rendered chapter table differs from source film")
    if abs(float(output_probe["format"]["duration"]) - duration) > 0.05:
        raise ValueError("rendered duration differs from source film")

    os.replace(partial, output)
    (work / "output-probe.json").write_text(json.dumps(output_probe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    receipt["state"] = "rendered-technical-checks-passed"
    receipt["output_probe"] = str(work / "output-probe.json")
    receipt["output_bytes"] = output.stat().st_size
    receipt["output_sha256"] = _sha256(output)
    receipt["duration_seconds"] = float(output_probe["format"]["duration"])
    receipt["chapters"] = rendered_chapters
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"RENDERED: {output}; bytes={receipt['output_bytes']}; sha256={receipt['output_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
