#!/usr/bin/env python3
"""Print the Chinese narration carried by a Project Causality build plan."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


SENTENCE_RE = re.compile(r"[^。！？；]+[。！？；]?|[^。！？；]+$")


def timestamp(seconds: float) -> str:
    value = max(0, int(seconds))
    hours, remainder = divmod(value, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    payload = json.loads(args.plan.read_text(encoding="utf-8-sig"))
    cues = payload["cues"][args.start : args.end]
    sentence_index = 0
    lines: list[str] = []
    for cue in cues:
        text = "".join(block["text"].replace("\n", "") for block in cue["subtitle_blocks"])
        sentences = [match.group(0).strip() for match in SENTENCE_RE.finditer(text) if match.group(0).strip()]
        lines.append(
            f"\n[{cue['index']:03d}] {timestamp(float(cue['start_seconds']))} "
            f"{cue['id']} ({len(sentences)} sentences)"
        )
        for sentence in sentences:
            sentence_index += 1
            lines.append(f"  {sentence_index:03d}. {sentence}")
    rendered = "\n".join(lines).lstrip() + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
