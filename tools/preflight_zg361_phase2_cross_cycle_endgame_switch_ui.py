#!/usr/bin/env python3
"""No-launch preflight for the exact-build endgame Switch Character UI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from zg361_phase2_cross_cycle_endgame_switch_ui import (
    ProductSwitchCharacterError,
    preflight_switch_character_ui_source,
)


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GAME_ROOT = ROOT / "Crusader Kings III"


def main(*, game_root: Path, output: Path | None = None) -> int:
    try:
        evidence = preflight_switch_character_ui_source(game_root)
    except ProductSwitchCharacterError as error:
        evidence = dict(error.evidence)
        exit_code = 1
    else:
        exit_code = 0
    serialized = json.dumps(evidence, ensure_ascii=False, indent=2) + "\n"
    if output is not None:
        output = output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return exit_code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--game-root",
        type=Path,
        default=DEFAULT_GAME_ROOT,
        help="CK3 install root containing game/gui (read-only)",
    )
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    raise SystemExit(main(game_root=arguments.game_root, output=arguments.output))
