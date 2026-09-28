"""Extract sparse E2-05 review stills with source frame PTS and frozen provenance.

This is only a navigation aid; it never certifies a clean span or event fact.
Wait for the managed CK3/cash screen session to release before running it.
"""

from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import re
import shutil
import struct
import subprocess
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path


SHOWINFO_PTS = re.compile(r"\bpts_time:([0-9]+(?:\.[0-9]+)?)")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def file_identity(path: Path) -> dict[str, object]:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)}


def png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as stream:
        header = stream.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError(f"not a valid PNG header: {path}")
    return struct.unpack(">II", header[16:24])


def pinned_source(path: Path, row: dict, stat: dict) -> None:
    if path != Path(row["path"]).resolve(strict=True):
        raise ValueError(f"source path differs from frozen link: {path}")
    current = path.stat()
    if current.st_size != row["bytes"] or current.st_size != stat["bytes"]:
        raise ValueError(f"source size differs from frozen link: {path}")
    if current.st_mtime_ns != stat["mtime_ns"]:
        raise ValueError(f"source mtime differs from frozen link: {path}")


def probe_video_pts(path: Path) -> tuple[list[Decimal], list[str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    strings = [frame["best_effort_timestamp_time"] for frame in data["frames"]
               if frame.get("media_type", "video") == "video"
               and frame.get("best_effort_timestamp_time")]
    values = [Decimal(value) for value in strings]
    if not values or any(right <= left for left, right in zip(values, values[1:])):
        raise ValueError("frozen ffprobe video PTS is missing or nonmonotonic")
    return values, strings


def match_probe_pts(value: Decimal, values: list[Decimal], strings: list[str]) -> str:
    index = bisect.bisect_left(values, value)
    candidates = [candidate for candidate in (index - 1, index) if 0 <= candidate < len(values)]
    best = min(candidates, key=lambda candidate: abs(values[candidate] - value))
    if abs(values[best] - value) > Decimal("0.001"):
        raise ValueError(f"FFmpeg PTS {value} has no exact frozen ffprobe match")
    return strings[best]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--postrun-links", required=True, type=Path)
    parser.add_argument("--postrun-links-sha256", required=True)
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--ffprobe-json", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--seek", action="append", required=True, type=int,
                        help="repeat for each requested whole-second source position")
    args = parser.parse_args()
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        parser.error("ffmpeg not found")
    if args.output.exists():
        parser.error("output already exists; use a fresh append-only attempt")
    if len(set(args.seek)) != len(args.seek) or any(value < 0 or value >= 600 for value in args.seek):
        parser.error("seek values must be distinct integers in [0, 600)")

    links_path = args.postrun_links.resolve(strict=True)
    if sha256(links_path) != args.postrun_links_sha256.upper():
        raise ValueError("postrun link bytes do not match the pinned SHA-256")
    links = json.loads(links_path.read_text(encoding="utf-8"))
    if links.get("result") != "MEDIA_PTS_CANDIDATE_UNREVIEWED":
        raise ValueError("unexpected frozen postrun link status")
    raw = args.raw.resolve(strict=True)
    probe = args.ffprobe_json.resolve(strict=True)
    pinned_source(raw, links["raw_from_prior_full_sha_audit"], links["raw_stat_during_link_audit"])
    pinned_source(probe, links["ffprobe_from_prior_full_sha_audit"],
                  links["ffprobe_stat_during_link_audit"])
    if sha256(probe) != links["ffprobe_from_prior_full_sha_audit"]["sha256"]:
        raise ValueError("frozen ffprobe content changed")
    if links["video_pts_summary"]["missing_pts_count"] != 0 or \
            links["video_pts_summary"]["nonmonotonic_count"] != 0 or \
            links["video_pts_summary"]["gap_count"] != 0:
        raise ValueError("frozen PTS audit is not continuous")
    pts_values, pts_strings = probe_video_pts(probe)

    args.output.mkdir(parents=True)
    intent = {
        "schema": "xar.war-promo.e2-05-sparse-visual-intent/v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "SPARSE_VISUAL_CANDIDATE_UNREVIEWED",
        "postrun_links": file_identity(links_path),
        "raw": links["raw_from_prior_full_sha_audit"],
        "raw_rehashed_by_sampler": False,
        "ffprobe": links["ffprobe_from_prior_full_sha_audit"],
        "requested_seek_seconds": args.seek,
        "full_speed_human_review": False,
        "clean_spans_certified": False,
    }
    (args.output / "intent.json").write_text(
        json.dumps(intent, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    samples = []
    for second in args.seek:
        still = args.output / f"seek-{second:03d}.png"
        stderr_path = args.output / f"seek-{second:03d}.ffmpeg.stderr.txt"
        argv = [ffmpeg, "-hide_banner", "-loglevel", "info", "-nostdin", "-n",
                "-threads", "1", "-filter_threads", "1", "-ss", str(second),
                "-copyts", "-i", str(raw), "-map", "0:v:0", "-an",
                "-vf", "showinfo", "-frames:v", "1", "-compression_level", "1",
                str(still)]
        result = subprocess.run(argv, capture_output=True, text=True, check=False)
        stderr_path.write_text(result.stderr, encoding="utf-8")
        if result.returncode != 0 or not still.is_file():
            raise RuntimeError(f"FFmpeg seek {second} failed; partial attempt preserved")
        showinfo = SHOWINFO_PTS.findall(result.stderr)
        if not showinfo:
            raise ValueError(f"seek {second} has no showinfo PTS; partial attempt preserved")
        measured = Decimal(showinfo[0])
        if abs(measured - Decimal(second)) > Decimal("0.5"):
            raise ValueError(f"seek {second} decoded distant frame {measured}; partial preserved")
        matched = match_probe_pts(measured, pts_values, pts_strings)
        width, height = png_dimensions(still)
        if (width, height) != (2560, 1440):
            raise ValueError(f"seek {second} PNG geometry {width}x{height} differs from raw")
        samples.append({
            "requested_seek_seconds": second,
            "ffmpeg_showinfo_pts_seconds": str(measured),
            "frozen_ffprobe_frame_pts_seconds": matched,
            "still": file_identity(still),
            "png_width": width,
            "png_height": height,
            "ffmpeg_stderr": file_identity(stderr_path),
            "ffmpeg_exit_code": result.returncode,
            "argv": argv,
        })
    index = {**intent, "schema": "xar.war-promo.e2-05-sparse-visual-index/v1",
             "completed_at_utc": datetime.now(timezone.utc).isoformat(), "samples": samples}
    (args.output / "sample-index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(args.output / "sample-index.json")


if __name__ == "__main__":
    main()
