"""Write a source-bound edit list for the uploaded R6 film's machine review."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--film", type=Path, required=True)
    parser.add_argument("--segments-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = json.loads(args.inputs.resolve(strict=True).read_text(encoding="utf-8"))["cues"]
    film = args.film.resolve(strict=True)
    probe = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_format", "-of", "json", str(film)],
                                      check=True, capture_output=True).stdout)
    duration_ms = round(float(probe["format"]["duration"]) * 1000)
    segments = []
    cursor = 0
    for index, row in enumerate(rows, 1):
        cue_id = row["id"]
        source = (args.segments_directory / f"{index:04d}-{cue_id}.mp4").resolve(strict=True)
        length = round(row["duration_seconds"] * 1000)
        segments.append({"cue_id": cue_id, "source": str(source), "bytes": source.stat().st_size,
                         "sha256": digest(source), "start_ms": cursor, "duration_ms": length,
                         "end_ms": cursor + length})
        cursor += length
    if len(segments) not in (32, 33) or abs(cursor - duration_ms) > 150:
        raise ValueError(f"Segment total {cursor}ms differs from final film {duration_ms}ms")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(segments, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"segments": len(segments), "segment_duration_ms": cursor,
                      "film_duration_ms": duration_ms, "film_sha256": digest(film)}))


if __name__ == "__main__":
    main()
