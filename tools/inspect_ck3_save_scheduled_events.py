#!/usr/bin/env python3
"""Inspect a CK3 save's queued triggered events without launching the game.

The output is prelaunch evidence only.  It can narrow a bounded live scenario,
but it cannot replace exact-build MCP observation or a product postcondition.
"""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Iterator, Sequence

from inspect_ck3_save_player_topology import _sha256


SCHEMA_VERSION = 1
KIND = "ck3_scheduled_event_queue_offline_v1"


def _ck3_date(value: str) -> date:
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", value)
    if match is None:
        raise ValueError(f"invalid CK3 date: {value!r}")
    return date(*(int(part) for part in match.groups()))


def _triggered_events(path: Path) -> Iterator[dict[str, object]]:
    block: list[str] = []
    depth = 0
    with path.open("r", encoding="utf-8", errors="replace") as stream:
        for line in stream:
            if not block:
                if line == "triggered_event={\n":
                    block = [line]
                    depth = 1
                continue
            block.append(line)
            depth += line.count("{") - line.count("}")
            if depth:
                continue
            text = "".join(block)
            block = []
            event = re.search(r'(?m)^\s*(?:event|on_action)="([^"]+)"$', text)
            queued_date = re.search(r"(?m)^\s*date=([^\s]+)$", text)
            root = re.search(
                r"root=\{\s*type=char\s*identity=(\d+)", text, re.DOTALL
            )
            if event is not None and queued_date is not None:
                yield {
                    "event": event.group(1),
                    "root_character_id": int(root.group(1)) if root else None,
                    "date": queued_date.group(1),
                }


def inspect_melted(
    path: Path, *, event_prefix: str = "", root_character_id: int | None = None
) -> dict[str, object]:
    current_date: str | None = None
    game_version: str | None = None
    with path.open("r", encoding="utf-8", errors="replace") as stream:
        for line in stream:
            if game_version is None:
                match = re.fullmatch(r'version="([^"]+)"', line.strip())
                if match is not None:
                    game_version = match.group(1)
            if current_date is None:
                match = re.fullmatch(r"date=([^\s]+)\n?", line)
                if match is not None:
                    current_date = match.group(1)
            if game_version is not None and current_date is not None:
                break
    if current_date is None:
        raise ValueError("save has no top-level current date")
    current = _ck3_date(current_date)
    matches = []
    for row in _triggered_events(path):
        if event_prefix and not str(row["event"]).startswith(event_prefix):
            continue
        if (
            root_character_id is not None
            and row["root_character_id"] != root_character_id
        ):
            continue
        matches.append(
            {
                **row,
                "days_from_current": (_ck3_date(str(row["date"])) - current).days,
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": KIND,
        "result": "GREEN",
        "authority": "offline-prelaunch-only-live-exact-build-mcp-remains-authoritative",
        "game_version": game_version,
        "current_date": current_date,
        "event_prefix": event_prefix,
        "root_character_id": root_character_id,
        "matched_count": len(matches),
        "matches": matches,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--save", type=Path)
    source.add_argument("--melted", type=Path)
    parser.add_argument("--rakaly", type=Path)
    parser.add_argument("--event-prefix", default="")
    parser.add_argument("--root-character-id", type=int)
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    temporary: tempfile.TemporaryDirectory[str] | None = None
    try:
        if args.melted is not None:
            melted = args.melted.resolve()
            if not melted.is_file():
                raise ValueError("melted input does not exist")
            source_record = None
            rakaly_record = None
        else:
            save = args.save.resolve()
            rakaly = args.rakaly.resolve() if args.rakaly is not None else None
            if not save.is_file() or rakaly is None or not rakaly.is_file():
                raise ValueError("--save requires an existing --rakaly executable")
            temporary = tempfile.TemporaryDirectory(prefix="ck3-scheduled-events-")
            melted = Path(temporary.name) / "source-melted.ck3"
            completed = subprocess.run(
                [str(rakaly), "melt", str(save), "-o", str(melted)],
                check=False,
                capture_output=True,
                text=True,
            )
            if completed.returncode != 0 or not melted.is_file():
                raise RuntimeError(
                    f"Rakaly melt failed ({completed.returncode}): "
                    f"{completed.stderr.strip()}"
                )
            source_record = {
                "path": str(save),
                "bytes": save.stat().st_size,
                "sha256": _sha256(save),
                "container_header": save.read_bytes()[:7].decode(
                    "ascii", errors="replace"
                ),
            }
            rakaly_record = {
                "path": str(rakaly),
                "bytes": rakaly.stat().st_size,
                "sha256": _sha256(rakaly),
            }
        report = inspect_melted(
            melted,
            event_prefix=args.event_prefix,
            root_character_id=args.root_character_id,
        )
        report["source"] = source_record
        report["rakaly"] = rakaly_record
        report["melted_sha256"] = _sha256(melted)
        payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.output is not None:
            output = args.output.resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(payload, encoding="utf-8")
        print(payload, end="")
        return 0
    finally:
        if temporary is not None:
            temporary.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
