"""Render one deterministic R7D design frame from preserved R7 evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from war_ai_promo.episode_one_r7d_same_battle import _stage


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--script", type=Path, required=True)
    parser.add_argument("--frames", type=Path, required=True)
    parser.add_argument("--cue", default="M07")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cues = json.loads(args.script.read_text(encoding="utf-8"))["cues"]
    matches = [cue for cue in cues if cue["id"] == args.cue]
    if len(matches) != 1:
        raise ValueError(f"Expected one cue {args.cue}")
    cue = matches[0]
    source = args.frames / f"messina-original-{cue['source_time_seconds']:03d}s.png"
    target = args.frames / f"messina-original-{cue['target_time_seconds']:03d}s.png"
    for frame in (source, target):
        if not frame.is_file():
            raise FileNotFoundError(frame)
    _stage(cue, 1, source, target, args.output)
    print(args.output)


if __name__ == "__main__":
    main()
