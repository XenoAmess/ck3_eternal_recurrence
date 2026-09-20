#!/usr/bin/env python3
"""Build the clean 1440p cold-open motion plate for Project Causality r13."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = (
    ROOT
    / "artifacts/project-causality/2026-09-20-r13/assets/project-causality-r13-hook-motion.mp4"
)
WIDTH = 2560
HEIGHT = 1440
FPS = 30


def run(command: list[str]) -> None:
    print("RUN:", " ".join(command), flush=True)
    subprocess.run(command, check=True)


def scale_filter() -> str:
    return (
        f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={WIDTH}:{HEIGHT},setsar=1,fps={FPS},format=yuv420p"
    )


def render_still(ffmpeg: str, source: Path, duration: float, output: Path) -> None:
    frames = int(round(duration * FPS))
    vf = (
        f"scale={WIDTH + 160}:{HEIGHT + 90}:force_original_aspect_ratio=increase,"
        f"crop={WIDTH + 160}:{HEIGHT + 90},"
        f"zoompan=z='min(zoom+0.00010,1.055)':"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS},"
        "setsar=1,format=yuv420p"
    )
    run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-loop",
            "1",
            "-i",
            str(source),
            "-vf",
            vf,
            "-frames:v",
            str(frames),
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            str(output),
        ]
    )


def render_clip(
    ffmpeg: str, source: Path, start: float, duration: float, output: Path
) -> None:
    run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            str(start),
            "-t",
            str(duration),
            "-i",
            str(source),
            "-vf",
            scale_filter(),
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            str(output),
        ]
    )


def build(output: Path, ffmpeg_override: str | None) -> Path:
    ffmpeg = ffmpeg_override or shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is not available")
    key_art = ROOT / "images/project_causality/promo/project_causality_key_art.png"
    pact = ROOT / "screenshots/gallery/01_pact.jpg"
    shop = ROOT / "screenshots/gallery/02_reincarnation_shop.jpg"
    scoreboard = ROOT / "mod_zhongguo_style/workshop/media/03_scoreboard.jpg"
    coa = (
        ROOT
        / "artifacts/project-causality/2026-09-19-r9/coa-production-capture/coat-of-arms-editor-r9.webm"
    )
    robert = (
        ROOT
        / "artifacts/project-causality/2026-09-20-r12/robert-mcp-showcase-main-menu-continuous.mp4"
    )
    method = (
        ROOT
        / "artifacts/project-causality/2026-09-20-r12/assets/method-pipeline-motion.mp4"
    )
    cta = ROOT / "artifacts/project-causality/2026-09-20-r12/assets/cta-motion.mp4"
    sources = [key_art, pact, shop, scoreboard, coa, robert, method, cta]
    missing = [str(path) for path in sources if not path.is_file()]
    if missing:
        raise RuntimeError("missing hook source(s): " + ", ".join(missing))

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="project-causality-r13-hook-") as raw:
        work = Path(raw)
        specs: list[tuple[str, Path, float, float]] = [
            ("still", key_art, 0.0, 14.0),
            ("still", pact, 0.0, 5.0),
            ("still", shop, 0.0, 5.0),
            ("still", scoreboard, 0.0, 5.0),
            ("clip", coa, 8.0, 8.0),
            ("clip", coa, 25.0, 5.0),
            ("clip", robert, 0.0, 4.0),
            ("clip", robert, 44.0, 4.0),
            ("clip", robert, 174.0, 5.0),
            ("clip", robert, 317.0, 6.0),
            ("clip", method, 40.0, 6.0),
            ("clip", cta, 0.0, 18.0),
            ("still", key_art, 0.0, 14.0),
        ]
        parts: list[Path] = []
        for index, (kind, source, start, duration) in enumerate(specs):
            part = work / f"{index:02d}.mp4"
            if kind == "still":
                render_still(ffmpeg, source, duration, part)
            else:
                render_clip(ffmpeg, source, start, duration, part)
            parts.append(part)
        concat = work / "concat.txt"
        concat.write_text(
            "".join(f"file '{path.as_posix()}'\n" for path in parts), encoding="utf-8"
        )
        temporary = output.with_name(f".{output.name}.partial.mp4")
        run(
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
                str(concat),
                "-an",
                "-vf",
                "format=yuv420p",
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(temporary),
            ]
        )
        temporary.replace(output)

    manifest = output.with_suffix(".json")
    manifest.write_text(
        json.dumps(
            {
                "schema": "project-causality-r13-hook-motion.v1",
                "output": str(output.resolve()),
                "duration_seconds": 99.0,
                "resolution": [WIDTH, HEIGHT],
                "fps": FPS,
                "sections": [
                    {"name": "pain", "start": 0.0, "end": 14.0},
                    {"name": "repetition", "start": 14.0, "end": 37.0},
                    {"name": "proof", "start": 37.0, "end": 67.0},
                    {"name": "audiences", "start": 67.0, "end": 85.0},
                    {"name": "question-and-title", "start": 85.0, "end": 99.0},
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"WROTE: {output}")
    print(f"WROTE: {manifest}")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--ffmpeg")
    args = parser.parse_args()
    build(args.output.expanduser().resolve(), args.ffmpeg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
