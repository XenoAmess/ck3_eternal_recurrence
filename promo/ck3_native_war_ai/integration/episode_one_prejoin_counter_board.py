"""Build the film's join-day R14 board from the agent's v2 evidence report."""

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
    EPISODE01_PREJOIN_COUNTER_V2_SHA256,
    load_episode01_prejoin_counter_r14_parity_v2,
)


def build_board() -> dict:
    report = load_episode01_prejoin_counter_r14_parity_v2()
    return {
        "schema": "ck3-episode01-prejoin-counter-r14-board-v2",
        "source_paired_report_sha256": EPISODE01_PAIRED_COUNTER_SHA256,
        "source_prejoin_report_sha256": EPISODE01_PREJOIN_COUNTER_V2_SHA256,
        "conditional_exact_r14_side_comparisons": report["conditional_exact_r14_side_comparisons"],
        "native_r14_side_comparisons": report["native_r14_side_comparisons"],
        "join_examples": [
            {
                key: row[key]
                for key in (
                    "source_day", "joined_army_id", "prejoin_active_attacker_army_ids",
                    "hypothetical_attacker_army_ids", "prejoin_fighting_regiment_count",
                    "native_r14_raw", "predicted_r14_raw", "delta_raw",
                    "source_whole_phase_trace_status",
                )
            }
            for row in report["join_day_repairs"]
        ],
        "conditioned_on_native_current_fighting_raw": True,
        "conditioned_on_native_effective_damage_raw": True,
        "conditioned_on_observed_join_timing": True,
        "same_date_prejoin_hypothetical_query_available": True,
        "join_policy_reconstructed": False,
        "advantage_reconstructed": False,
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
    print(json.dumps({"sha256": hashlib.sha256(args.output.read_bytes()).hexdigest().upper()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
