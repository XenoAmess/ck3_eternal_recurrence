"""Build a shot-safe comparison of three observed native battle replays.

This board deliberately offers no statistical win percentage or planner gate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "ck3_autonomous_player" / "src"))

from xar_autoplayer.simulation.native_battle_case import (  # noqa: E402
    EPISODE01_REPEATABILITY_SHA256,
    load_episode01_native_battle_repeatability,
)


def build_board() -> dict[str, object]:
    evidence = load_episode01_native_battle_repeatability()
    day_six = []
    terminal = []
    for trial in evidence["trials"]:
        day = trial["daily"][5]
        day_six.append({
            "trial": trial["trial"], "mode": trial["mode"],
            "day": 6, "date_raw": day["date_raw"],
            "enemy_current_raw_from_regiments": day["side_current_raw_from_regiments"][0],
            "player_current_raw_from_regiments": day["side_current_raw_from_regiments"][1],
            "control_response_sha256": day["control_response_sha256"],
            "may_splice_into_other_trajectory": False,
        })
        terminal.append({
            "trial": trial["trial"], "terminal_date_raw": trial["terminal_date_raw"],
            "winner_relative_to_player": "enemy" if not trial["player_won"] else "player",
            "terminal_response_sha256": trial["terminal_response_sha256"],
        })
    return {
        "schema": "ck3-episode01-repeatability-board-v1",
        "source_report_sha256": EPISODE01_REPEATABILITY_SHA256,
        "game_version": evidence["game_version"],
        "combat_id": evidence["combat_id"],
        "day_six_comparison": day_six,
        "pairwise_first_divergence": evidence["pairwise_divergence"],
        "terminal_outcomes": terminal,
        "independent_random_draws_proven": False,
        "calibrated_win_probability_available": False,
        "planner_usable": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f"refusing to overwrite repeatability board: {args.output}")
    board = build_board()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(board, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"output": str(args.output),
                      "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest().upper(),
                      "trials": len(board["terminal_outcomes"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
