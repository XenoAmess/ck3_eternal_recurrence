#!/usr/bin/env python3
"""Freeze the narrow Sway outcome source tree; file-only, no game access."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from ck3_12002_nonwar_event_sources import SourceTree, portable_definition, assignments, values

EXE_SHA = "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"

SPECS = [
    ("common/schemes/scheme_types/sway_scheme.txt", "sway"),
    ("common/on_action/schemes/sway_on_actions.txt", "sway_success"),
    ("common/on_action/schemes/sway_on_actions.txt", "sway_failure"),
    ("common/scripted_effects/00_scheme_scripted_effects.txt", "sway_end_effect"),
    ("common/script_values/00_scheme_values.txt", "sway_opinion_increase_per_success"),
    ("common/script_values/00_scheme_values.txt", "sway_max_value"),
    ("common/scripted_effects/00_scheme_scripted_effects.txt", "reset_failed_scheme_effect"),
]
SPECS.extend(("events/scheme_events/sway_scheme/sway_outcome_events.txt", key)
             for key in ("sway_outcome.0001", "sway_outcome.0002", "sway_outcome.1001",
                         "sway_outcome.1002", "sway_outcome.1003", "sway_outcome.1004",
                         "sway_outcome.2001", "sway_outcome.2002"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path, required=True)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--print-block", action="append", default=[])
    args = parser.parse_args()
    actual_sha = hashlib.sha256(args.exe.read_bytes()).hexdigest().upper()
    if actual_sha != EXE_SHA:
        raise ValueError("Executable does not match frozen CK3 1.20.0.2")
    tree = SourceTree(args.game_root)
    blocks = {}
    for path, key in SPECS:
        definition = tree.definition(path, key)
        payload, text, _ = tree.read(path)
        tokens = definition["token_objects"]
        source = text[tokens[0].offset:tokens[-1].end]
        row = portable_definition(definition)
        row["source"] = source
        if definition["tokens"][2] == "{":
            row["fields"] = [{"name": name, "line": body[0].line, "tokens": values(body)}
                             for name, body in assignments(tokens[3:-1])]
        blocks[key] = row
    document = {"schema": "xar.ck3.sway-outcome-source-tree", "schema_version": 1,
                "build": "1.20.0.2", "exe_sha256": actual_sha,
                "game_root": str(args.game_root), "read_only": True,
                "live_verified": False, "blocks": blocks}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for key in args.print_block:
        print(key, blocks[key]["line"])
        print(blocks[key]["source"])
    print(json.dumps({"output": str(args.output), "source_blocks": len(blocks),
                      "exe_sha256": actual_sha, "live_verified": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
