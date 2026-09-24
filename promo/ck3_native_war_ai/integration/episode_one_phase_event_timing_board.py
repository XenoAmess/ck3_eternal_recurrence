"""Build a shot-safe ledger-versus-state timeline from shared agent evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "ck3_autonomous_player" / "src"))

from xar_autoplayer.simulation.native_battle_case import (  # noqa: E402
    EPISODE01_PHASE_EVENT_SHA256,
    load_episode01_phase_event_observations,
)


def build_board() -> dict[str, object]:
    evidence = load_episode01_phase_event_observations()
    examples = []
    for row in evidence["event_fire_pairs"]:
        if row["source_day"] not in (5, 15):
            continue
        event = row["appended_battle_events"][0]
        target = row["target_character_observations"][0]
        examples.append({
            "source_day": row["source_day"],
            "target_day": row["target_day"],
            "event_key_as_recorded_in_battle_ledger": event["stable_key"],
            "ledger_target_character_id": target["character_id"],
            "same_fire_before_prowess": target["same_fire_before"]["prowess"],
            "same_fire_after_prowess": target["same_fire_after"]["prowess"],
            "same_fire_after_death_marker": target["same_fire_after"]["death_marker_present"],
            "next_source_day_record0": target["next_source_day_record0"],
            "next_source_day_record2": target["next_source_day_record2"],
            "source_receipt_sha256": row["source_receipt_sha256"],
            "next_source_day_receipt_sha256": target["next_source_day_receipt_sha256"],
            "whole_day_trace_available": row["source_trace_status"] == "bounded_trace_available",
            "complete_effect_feedback_proven": False,
        })
    return {
        "schema": "ck3-episode01-phase-event-timing-board-v2",
        "source_report_sha256": EPISODE01_PHASE_EVENT_SHA256,
        "game_version": evidence["game_version"],
        "combat_id": evidence["combat_id"],
        "phase_trace_trajectory": evidence["phase_trace_trajectory"],
        "all_observed_ledger_append_days": [
            row["source_day"] for row in evidence["event_fire_pairs"]
        ],
        "examples": examples,
        "complete_effect_feedback_proven": False,
        "calibrated_win_probability_available": False,
        "planner_usable": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f"refusing to overwrite timing board: {args.output}")
    board = build_board()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(board, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "output": str(args.output),
        "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest().upper(),
        "examples": len(board["examples"]),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
