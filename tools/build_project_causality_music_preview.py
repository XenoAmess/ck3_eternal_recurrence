#!/usr/bin/env python3
"""Build a chapter-aware no-continuation Suno music preview."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


TRACKS = [
    {
        "name": "prologue",
        "file": "00-prologue-a.wav",
        "gain": 0.33,
        "threshold": 0.020,
        "ratio": 8,
        "attack_ms": 20,
        "release_ms": 500,
    },
    {
        "name": "spell",
        "file": "01-spell-a.wav",
        "gain": 0.31,
        "threshold": 0.019,
        "ratio": 9,
        "attack_ms": 20,
        "release_ms": 550,
    },
    {
        "name": "robert",
        "file": "02-robert-b.wav",
        "gain": 0.35,
        "threshold": 0.022,
        "ratio": 7,
        "attack_ms": 15,
        "release_ms": 450,
    },
    {
        "name": "method",
        "file": "03-method-a.wav",
        "gain": 0.33,
        "threshold": 0.019,
        "ratio": 9,
        "attack_ms": 20,
        "release_ms": 550,
    },
    {
        "name": "principle",
        "file": "04-principle-a.wav",
        "gain": 0.38,
        "threshold": 0.019,
        "ratio": 9,
        "attack_ms": 20,
        "release_ms": 550,
    },
    {
        "name": "vision",
        "file": "05-vision-a.wav",
        "gain": 0.36,
        "threshold": 0.022,
        "ratio": 7,
        "attack_ms": 15,
        "release_ms": 450,
    },
]
CROSSFADE_SECONDS = 12.0
MIX_PROFILE = "music-forward-v1"


def run(command: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=capture,
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def chapter_filter(input_index: int, chapter: dict[str, object], output_label: str) -> list[str]:
    repeats = int(chapter["repeats"])
    duration = float(chapter["end"]) - float(chapter["start"])
    pieces: list[str] = []
    if repeats == 1:
        source = f"[{input_index}:a]"
    else:
        split_labels = [f"{output_label}s{index}" for index in range(repeats)]
        pieces.append(f"[{input_index}:a]asplit={repeats}" + "".join(f"[{label}]" for label in split_labels))
        previous = split_labels[0]
        for index, next_label in enumerate(split_labels[1:], start=1):
            joined = f"{output_label}x{index}"
            pieces.append(
                f"[{previous}][{next_label}]acrossfade=d={CROSSFADE_SECONDS}:c1=tri:c2=tri[{joined}]"
            )
            previous = joined
        source = f"[{previous}]"

    fade_out = 8.0 if chapter["name"] == "vision" else 4.0
    fade_out_start = duration - fade_out
    pieces.append(
        f"{source}atrim=duration={duration:.3f},asetpts=PTS-STARTPTS,"
        f"afade=t=in:st=0:d=2,afade=t=out:st={fade_out_start:.3f}:d={fade_out:.3f},"
        f"volume={float(chapter['gain']):.3f}"
        f"[{output_label}]"
    )
    return pieces


def probe(path: Path) -> dict[str, object]:
    result = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-show_entries",
            "stream=index,codec_type,codec_name,sample_rate,channels",
            "-show_chapters",
            "-of",
            "json",
            str(path),
        ],
        capture=True,
    )
    return json.loads(result.stdout)


def loudness(path: Path) -> str:
    result = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-nostats",
            "-i",
            str(path),
            "-map",
            "0:a:0",
            "-af",
            "ebur128=peak=true",
            "-f",
            "null",
            "NUL",
        ],
        check=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )
    summary = result.stderr.rsplit("Summary:", 1)[-1]
    match = re.search(
        r"Integrated loudness:.*?Peak:\s+-?\d+(?:\.\d+)? dBFS",
        summary,
        flags=re.DOTALL,
    )
    if not match:
        raise RuntimeError("Could not parse ebur128 summary")
    return match.group(0).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-video", required=True, type=Path)
    parser.add_argument("--music-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--output-name",
        default="project-causality-suno-base-loop-preview.mp4",
    )
    parser.add_argument(
        "--reuse-rendered-output",
        action="store_true",
        help="Skip the mix render and rerun media QA plus sidecar generation on the existing output.",
    )
    parser.add_argument(
        "--skip-full-decode",
        action="store_true",
        help="Skip the expensive full decode when it already passed in the current delivery run.",
    )
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / args.output_name
    sidecar = output.with_suffix(".json")

    source_media = probe(args.source_video)
    film_duration = float(source_media["format"]["duration"])
    source_chapters = source_media.get("chapters", [])
    if not isinstance(source_chapters, list) or len(source_chapters) < 7:
        raise RuntimeError("Source video must contain the eight Project Causality chapters")
    starts = [float(chapter["start_time"]) for chapter in source_chapters]
    boundaries = [0.0, starts[2], starts[3], starts[4], starts[5], starts[6], film_duration]

    command = ["ffmpeg", "-y", "-hide_banner", "-i", str(args.source_video)]
    chapters: list[dict[str, object]] = []
    selected: list[dict[str, object]] = []
    for index, track in enumerate(TRACKS):
        music_path = args.music_dir / str(track["file"])
        if not music_path.is_file():
            raise FileNotFoundError(music_path)
        track_duration = float(probe(music_path)["format"]["duration"])
        chapter_duration = boundaries[index + 1] - boundaries[index]
        repeats = 1
        covered = track_duration
        while covered + 0.01 < chapter_duration:
            repeats += 1
            covered += track_duration - CROSSFADE_SECONDS
        chapter = {
            **track,
            "start": boundaries[index],
            "end": boundaries[index + 1],
            "repeats": repeats,
            "track_duration_seconds": track_duration,
        }
        chapters.append(chapter)
        command.extend(["-i", str(music_path)])
        selected.append(
            {
                **chapter,
                "path": str(music_path),
                "sha256": sha256(music_path),
            }
        )

    filters: list[str] = []
    chapter_labels: list[str] = []
    for index, chapter in enumerate(chapters, start=1):
        label = f"chapter{index - 1}"
        chapter_labels.append(label)
        filters.extend(chapter_filter(index, chapter, label))
    filters.append(
        f"[0:a:0]aresample=48000,asetpts=PTS-STARTPTS,asplit=2[voice][keyroot]"
    )
    raw_keys = [f"key{index}raw" for index in range(len(chapters))]
    filters.append(
        f"[keyroot]asplit={len(chapters)}"
        + "".join(f"[{label}]" for label in raw_keys)
    )
    ducked_labels: list[str] = []
    for index, chapter in enumerate(chapters):
        key_label = f"key{index}"
        ducked_label = f"ducked{index}"
        ducked_labels.append(ducked_label)
        filters.append(
            f"[{raw_keys[index]}]atrim=start={float(chapter['start']):.3f}:"
            f"end={float(chapter['end']):.3f},asetpts=PTS-STARTPTS[{key_label}]"
        )
        filters.append(
            f"[{chapter_labels[index]}][{key_label}]sidechaincompress="
            f"threshold={float(chapter['threshold']):.3f}:ratio={float(chapter['ratio']):g}:"
            f"attack={int(chapter['attack_ms'])}:release={int(chapter['release_ms'])}:"
            f"knee=6:makeup=1[{ducked_label}]"
        )
    filters.append(
        "".join(f"[{label}]" for label in ducked_labels)
        + f"concat=n={len(chapters)}:v=0:a=1,highpass=f=70,lowpass=f=14000[ducked]"
    )
    filters.append(
        "[voice][ducked]amix=inputs=2:weights='1 1':normalize=0,"
        "loudnorm=I=-16:LRA=7:TP=-1.5,aresample=48000:async=1:first_pts=0,asetpts=N/SR/TB[mix]"
    )
    command.extend(
        [
            "-filter_complex",
            ";".join(filters),
            "-map",
            "0:v:0",
            "-map",
            "[mix]",
            "-map",
            "0:s?",
            "-map",
            "0:d?",
            "-map_metadata",
            "0",
            "-map_chapters",
            "0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "320k",
            "-c:s",
            "copy",
            "-c:d",
            "copy",
            "-movflags",
            "+faststart",
            "-metadata:s:a:0",
            "title=Owner narration plus music-forward Suno preview",
            str(output),
        ]
    )
    if args.reuse_rendered_output:
        if not output.is_file() or output.stat().st_size == 0:
            raise FileNotFoundError(output)
    else:
        run(command)

    media = probe(output)
    duration = float(media["format"]["duration"])
    if abs(duration - film_duration) > 0.1:
        raise RuntimeError(f"Unexpected output duration: {duration}")
    stream_types = [stream["codec_type"] for stream in media["streams"]]
    if stream_types.count("video") != 1 or stream_types.count("audio") != 1 or stream_types.count("subtitle") != 1:
        raise RuntimeError(f"Unexpected streams: {media['streams']}")

    if not args.skip_full_decode:
        run(["ffmpeg", "-v", "error", "-i", str(output), "-f", "null", "NUL"])
    payload = {
        "schema": "project-causality-suno-base-loop-preview.v3",
        "status": "review-preview-not-publication-master",
        "source_video": str(args.source_video),
        "source_video_sha256": sha256(args.source_video),
        "output": str(output),
        "output_sha256": sha256(output),
        "duration_seconds": duration,
        "mix_profile": MIX_PROFILE,
        "crossfade_seconds": CROSSFADE_SECONDS,
        "chapter_mix": [
            {
                "name": chapter["name"],
                "gain": chapter["gain"],
                "threshold": chapter["threshold"],
                "ratio": chapter["ratio"],
                "attack_ms": chapter["attack_ms"],
                "release_ms": chapter["release_ms"],
                "knee": 6,
            }
            for chapter in chapters
        ],
        "selected_tracks": selected,
        "media": media,
        "loudness_summary": loudness(output),
        "limitations": [
            "Long chapters loop the selected base master because no continuations are included.",
            "This preview is for judging music direction, transitions, and narration masking only.",
        ],
    }
    sidecar.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)
    print(payload["output_sha256"])
    print(payload["loudness_summary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
