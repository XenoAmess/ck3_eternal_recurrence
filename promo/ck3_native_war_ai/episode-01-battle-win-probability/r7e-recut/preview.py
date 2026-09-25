"""Preview a deterministic R7E design frame using preserved Messina evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from war_ai_promo.episode_one_r7e_same_battle import _stage


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--script", type=Path, required=True)
    parser.add_argument("--frames", type=Path, required=True)
    parser.add_argument("--cue", default="E1-F01")
    parser.add_argument("--stage", type=int, choices=[0, 1, 2], default=2)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = json.loads(args.script.read_text(encoding="utf-8"))["cues"]
    matches = [row for row in rows if row["id"] == args.cue]
    if len(matches) != 1:
        raise ValueError(f"Expected one cue {args.cue}")
    row = matches[0]
    source = args.frames / f"messina-original-{row['source_time_seconds']:03d}s.png"
    target = args.frames / f"messina-original-{row['target_time_seconds']:03d}s.png"
    for frame in (source, target):
        if not frame.is_file():
            raise FileNotFoundError(frame)
    _stage(row, args.stage, source, target, args.output)
    print(args.output)


if __name__ == "__main__":
    main()
