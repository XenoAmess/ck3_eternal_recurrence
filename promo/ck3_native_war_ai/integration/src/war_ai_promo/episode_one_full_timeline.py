"""Validate the episode-one observation script and derive its shot index."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--script", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    script = json.loads(arguments.script.read_text(encoding="utf-8"))
    rows = script["cues"]
    expected = [f"E1-F{index:02d}" for index in range(1, 26)]
    if [row["id"] for row in rows] != expected:
        raise ValueError("observation film requires its 25 ordered cue IDs")
    chapters = ["hook", "inputs", "daily", "events", "evidence", "decision"]
    if set(row["chapter_id"] for row in rows) != set(chapters):
        raise ValueError("all six script chapters must be present")
    previous_end = 0.0
    for row in rows:
        if row["shot_id"] != row["id"] or len(row["visual_points"]) != 3:
            raise ValueError(f"invalid shot contract: {row['id']}")
        if any(not isinstance(row[key], str) or not row[key].strip()
               for key in ("zh", "en", "visual_title", "evidence")):
            raise ValueError(f"empty script or evidence: {row['id']}")
        if row["visual_kind"] == "gameplay":
            begin = float(row["gameplay_start_seconds"])
            end = begin + float(row["gameplay_seconds"])
            if begin < previous_end or end > 266.4 or begin < 0:
                raise ValueError(f"gameplay overlap or out of source: {row['id']}")
            previous_end = end
        elif row["visual_kind"] != "card":
            raise ValueError(f"unknown visual kind: {row['id']}")
    timeline = {
        "format_version": 1,
        "source_script": str(arguments.script.as_posix()),
        "shots": [
            {
                "id": row["shot_id"],
                "title": row["visual_title"],
                "visual": row["visual_kind"],
                "evidence": row["evidence"],
            }
            for row in rows
        ],
    }
    with arguments.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(timeline, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({
        "cues": len(rows),
        "chinese_characters": sum(len(row["zh"]) for row in rows),
        "gameplay_unique_seconds": sum(float(row.get("gameplay_seconds", 0)) for row in rows),
        "timeline": str(arguments.output),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
