"""Build a film-safe R14 board from the same report used by the agent."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "ck3_autonomous_player" / "src"))
from xar_autoplayer.simulation.native_battle_case import (  # noqa: E402
    EPISODE01_PAIRED_COUNTER_SHA256,
    load_episode01_paired_counter_r14_parity,
)


def build_board() -> dict:
    report = load_episode01_paired_counter_r14_parity()
    examples = []
    for row in report["days"]:
        if row["day"] not in (4, 5, 11, 12, 21, 22, 26):
            continue
        examples.append({
            "source_day": row["day"],
            "attacker_army_ids": row["attacker_army_ids"],
            "trace_status": row["trace_status"],
            "native_enemy_r14_raw": row["native_enemy_r14_raw"],
            "derived_enemy_r14_raw": row["derived_enemy_r14_raw"],
            "native_player_r14_raw": row["native_player_r14_raw"],
            "derived_player_r14_raw": row["derived_player_r14_raw"],
            "side_comparison": row["side_comparison"],
            "classification": row["classification"],
        })
    return {
        "schema": "ck3-episode01-counter-r14-board-v1",
        "source_report_sha256": EPISODE01_PAIRED_COUNTER_SHA256,
        "same_replay_days": report["observed_days"],
        "conditional_exact_side_comparisons": report["conditional_exact_side_comparisons"],
        "conditional_comparable_side_count": report["conditional_comparable_side_count"],
        "unresolved_join_days": report["unresolved_days"],
        "examples": examples,
        "conditioned_on_native_current_fighting_raw": True,
        "conditioned_on_native_effective_damage_raw": True,
        "join_day_recompute_complete": False,
        "whole_battle_win_probability_available": False,
        "planner_usable": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f"refusing to overwrite board: {args.output}")
    board = build_board()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(board, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"sha256": hashlib.sha256(args.output.read_bytes()).hexdigest().upper(),
                      "examples": len(board["examples"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
