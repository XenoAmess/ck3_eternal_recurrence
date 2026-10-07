"""Stage decoded native Sway material, or consume it after a real normal turn.

This file-only Root helper does not connect to CK3, send a command or advance
time. Inputs are the decoded outputs of the existing registered MCP tools.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                       / "ck3_autonomous_player" / "src"))

from xar_autoplayer.sway_formal_consumer import consume_sway_following_turn
from xar_autoplayer.sway_material_consumer import record_sway_material_intervention


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    record = commands.add_parser("record")
    record.add_argument("--state-dir", type=Path, required=True)
    record.add_argument("--sway-read", type=Path, required=True)
    record.add_argument("--opinion-read", type=Path, required=True)
    record.add_argument("--output", type=Path, required=True)
    consume = commands.add_parser("consume")
    consume.add_argument("--state-dir", type=Path, required=True)
    consume.add_argument("--following-snapshot", type=Path, required=True,
                         help="Actual after snapshot of the completed normal gameplay turn")
    consume.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "record":
        result = record_sway_material_intervention(
            args.state_dir,
            sway_read=json.loads(args.sway_read.read_text(encoding="utf-8-sig")),
            opinion_read=json.loads(args.opinion_read.read_text(encoding="utf-8-sig")),
        )
    else:
        result = consume_sway_following_turn(
            args.state_dir,
            json.loads(args.following_snapshot.read_text(encoding="utf-8-sig")),
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
