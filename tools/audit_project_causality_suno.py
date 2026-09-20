#!/usr/bin/env python3
"""Audit the owner-supplied Suno WAV candidates for Project Causality."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


PAIR_ORDER = [
    "00-prologue",
    "01-spell",
    "02-robert",
    "03-method",
    "04-principle",
    "05-vision",
]


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, text=True, capture_output=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def probe(path: Path) -> dict[str, object]:
    result = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,size",
            "-show_entries",
            "stream=codec_name,sample_rate,channels",
            "-of",
            "json",
            str(path),
        ]
    )
    payload = json.loads(result.stdout)
    stream = payload["streams"][0]
    fmt = payload["format"]
    return {
        "duration_seconds": round(float(fmt["duration"]), 3),
        "size_bytes": int(fmt["size"]),
        "codec": stream["codec_name"],
        "sample_rate": int(stream["sample_rate"]),
        "channels": int(stream["channels"]),
    }


def loudness(path: Path) -> dict[str, float]:
    result = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-nostats",
            "-i",
            str(path),
            "-filter_complex",
            "ebur128=peak=true",
            "-f",
            "null",
            "NUL",
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    summary = result.stderr.rsplit("Summary:", 1)[-1]
    integrated = re.search(r"Integrated loudness:.*?I:\s*([+-]?[0-9.]+) LUFS", summary, re.S)
    loudness_range = re.search(r"Loudness range:.*?LRA:\s*([+-]?[0-9.]+) LU", summary, re.S)
    peak = re.search(r"True peak:.*?Peak:\s*([+-]?[0-9.]+) dBFS", summary, re.S)
    if not (integrated and loudness_range and peak):
        raise RuntimeError(f"Unable to parse ebur128 summary for {path}")
    return {
        "integrated_lufs": float(integrated.group(1)),
        "lra_lu": float(loudness_range.group(1)),
        "true_peak_dbfs": float(peak.group(1)),
    }


def render_spectrum(path: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(path),
            "-lavfi",
            "showspectrumpic=s=1600x260:legend=disabled:color=intensity:scale=log:fscale=log",
            "-frames:v",
            "1",
            str(destination),
        ],
        check=True,
    )


def make_contact_sheet(records: list[dict[str, object]], spectrum_dir: Path, destination: Path) -> None:
    font = ImageFont.load_default(size=24)
    small = ImageFont.load_default(size=19)
    canvas = Image.new("RGB", (1640, 1190), "#11151d")
    draw = ImageDraw.Draw(canvas)
    draw.text((20, 14), "Project Causality r14 — Suno A/B technical contact sheet", font=font, fill="#f2e7cd")

    by_stem = {str(item["stem"]): item for item in records}
    for row, pair in enumerate(PAIR_ORDER):
        y = 65 + row * 185
        for column, suffix in enumerate(("a", "b")):
            stem = f"{pair}-{suffix}"
            item = by_stem[stem]
            spectrum = Image.open(spectrum_dir / f"{stem}.png").convert("RGB").resize((790, 128))
            x = 20 + column * 810
            canvas.paste(spectrum, (x, y + 44))
            label = (
                f"{stem}  {item['duration_seconds']:.2f}s  "
                f"{item['integrated_lufs']:.1f} LUFS  "
                f"LRA {item['lra_lu']:.1f}  TP {item['true_peak_dbfs']:.1f}"
            )
            draw.text((x, y + 8), label, font=small, fill="#d7e4ef")
    destination.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(destination, quality=94)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    spectrum_dir = args.output_dir / "spectra"
    records: list[dict[str, object]] = []
    for path in sorted(args.input_dir.glob("*.wav")):
        record: dict[str, object] = {"file": str(path), "stem": path.stem, "sha256": sha256(path)}
        record.update(probe(path))
        record.update(loudness(path))
        render_spectrum(path, spectrum_dir / f"{path.stem}.png")
        records.append(record)

    if len(records) != 12:
        raise RuntimeError(f"Expected 12 WAV candidates, found {len(records)}")
    for record in records:
        if record["codec"] != "pcm_s16le" or record["sample_rate"] != 48000 or record["channels"] != 2:
            raise RuntimeError(f"Unexpected media format: {record}")
        if record["true_peak_dbfs"] >= 0:
            raise RuntimeError(f"Clipping candidate: {record}")

    (args.output_dir / "suno-audit.json").write_text(
        json.dumps({"schema": "project-causality-suno-audit.v1", "tracks": records}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    rows = [
        "# Project 因果律 r14 Suno 母带技术审计",
        "",
        "| 候选 | 时长 | LUFS-I | LRA | True Peak | SHA-256 |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for record in records:
        rows.append(
            f"| `{record['stem']}` | `{record['duration_seconds']:.3f}s` | "
            f"`{record['integrated_lufs']:.1f}` | `{record['lra_lu']:.1f}` | "
            f"`{record['true_peak_dbfs']:.1f} dBFS` | `{record['sha256']}` |"
        )
    rows.extend(
        [
            "",
            "全部候选均为 48 kHz、双声道 PCM 16-bit WAV，且无数字削波。",
            "技术指标不能替代听感判断；A/B 选择还需要结合章节情绪、配器密度和是否抢旁白。",
        ]
    )
    (args.output_dir / "suno-audit.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
    make_contact_sheet(records, spectrum_dir, args.output_dir / "suno-contact-sheet.jpg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
