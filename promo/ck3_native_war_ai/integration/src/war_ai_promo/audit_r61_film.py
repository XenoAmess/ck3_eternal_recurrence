"""Audit the uploaded R6.1 film, its full cue set and actual ASS subtitle files."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess


CHINESE_NUMERAL = frozenset("零〇一二三四五六七八九十百千万亿两点")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def seconds(value: str) -> float:
    hours, minutes, sec = value.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(sec)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--film", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--subtitles", type=Path, required=True)
    parser.add_argument("--upload-readback", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    film = args.film.resolve(strict=True)
    inputs = json.loads(args.inputs.resolve(strict=True).read_text(encoding="utf-8"))
    readback = json.loads(args.upload_readback.resolve(strict=True).read_text(encoding="utf-8"))
    if readback.get("status") != "uploaded" or readback.get("target") != film.name:
        raise ValueError("Exact film must be uploaded before the full copy audit")
    rows = inputs["cues"]
    errors = []
    if len(rows) != 33 or any(row.get("subtitle_mode") != "paragraph" for row in rows):
        errors.append("Expected 33 paragraph-caption cues")
    if len({row["id"] for row in rows}) != len(rows):
        errors.append("Duplicate cue identity")
    actual = Counter()
    longest = Counter()
    numeric_wraps = []
    for index, row in enumerate(rows, 1):
        cue_id = row["id"]
        subtitle = (args.subtitles / f"{index:04d}-{cue_id}.ass").resolve(strict=True)
        for line in subtitle.read_text(encoding="utf-8-sig").splitlines():
            if not line.startswith("Dialogue: "):
                continue
            parts = line.removeprefix("Dialogue: ").split(",", 9)
            if len(parts) != 10:
                errors.append(cue_id + ": malformed ASS Dialogue")
                continue
            language = "zh" if parts[3].startswith("Chinese") else "en"
            actual[language] += 1
            duration = seconds(parts[2]) - seconds(parts[1])
            longest[language] = max(longest[language], duration)
            if duration <= 0:
                errors.append(cue_id + ": nonpositive subtitle duration")
            chunks = parts[9].replace("{\\q2}", "").split("\\N")
            if len(chunks) > 2:
                errors.append(cue_id + ": more than two subtitle lines")
            if language == "zh" and len(chunks) == 2 and chunks[0] and chunks[1]:
                if chunks[0][-1] in CHINESE_NUMERAL and chunks[1][0] in CHINESE_NUMERAL:
                    numeric_wraps.append({"cue_id": cue_id, "before": chunks[0], "after": chunks[1]})
    if numeric_wraps:
        errors.append(f"Chinese numeral split across lines: {len(numeric_wraps)}")
    probe = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams",
                                       "-show_chapters", "-of", "json", str(film)],
                                      capture_output=True, check=True).stdout)
    if len(probe.get("chapters", [])) != 33:
        errors.append("Final film must contain 33 chapters")
    video = [stream for stream in probe["streams"] if stream["codec_type"] == "video"]
    audio = [stream for stream in probe["streams"] if stream["codec_type"] == "audio"]
    if len(video) != 1 or (video[0]["width"], video[0]["height"]) != (2560, 1440) or len(audio) != 1:
        errors.append("Unexpected video or audio stream layout")
    duration = float(probe["format"]["duration"])
    if not 1200 <= duration <= 2400 or abs(duration - inputs["actual_duration_seconds"]) > .15:
        errors.append("Final duration differs from frozen speech timeline")
    report = {
        "schema": "ck3-war-ai-r61-full-copy-audit.v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "state": "GREEN" if not errors else "RED",
        "film": str(film), "film_sha256": digest(film),
        "uploaded_before_audit": str(args.upload_readback.resolve()),
        "cue_count": len(rows), "chapter_count": len(probe.get("chapters", [])),
        "duration_seconds": duration,
        "actual_ass_blocks": dict(actual), "longest_ass_block_seconds": dict(longest),
        "numeral_line_splits": numeric_wraps,
        "gameplay_cue_count": sum(row["visual_kind"] == "gameplay" for row in rows),
        "gameplay_seconds_claimed": sum(row.get("gameplay_seconds", 0) for row in rows if row["visual_kind"] == "gameplay"),
        "errors": errors, "human_signoff": "not-provided",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({key: value for key, value in report.items() if key not in ("film", "numeral_line_splits")}, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
