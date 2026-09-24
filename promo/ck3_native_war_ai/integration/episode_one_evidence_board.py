"""Build shot-safe episode-one facts from the agent's native battle case.

The board separates the original outcome from the divergent independent phase
replay.  It intentionally contains no model probability or approval field.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "ck3_autonomous_player" / "src"))

from xar_autoplayer.simulation.native_battle_case import (
    EPISODE01_CASE_SHA256,
    EPISODE01_PARITY_SHA256,
    load_episode01_main_tick_parity,
    load_episode01_native_battle_case,
)


def build_board() -> dict[str, object]:
    case = load_episode01_native_battle_case()
    parity = load_episode01_main_tick_parity()
    by_day = {row["day"]: row for row in case["daily"]}
    original_beats = []
    for day in (1, 2, 4, 12, 22, 28, 31):
        row = by_day[day]
        original_beats.append({
            "day": day,
            "date_raw": row["date_raw"],
            "phase": row["phase"],
            "enemy_army_ids": row["side0"]["army_ids"],
            "enemy_current_raw": row["side0"]["current_raw"],
            "player_current_raw": row["side1"]["current_raw"],
            "source_trajectory": "original-31-day-capture",
        })
    replay_beats = [
        {
            "source_day": row["source_day"],
            "target_day": row["target_day"],
            "status": row["status"],
            "new_battle_events": row["new_battle_events"],
            "finish_receipt_sha256": row["finish_receipt_sha256"],
            "source_trajectory": "independent-replay-from-contact-checkpoint",
            "may_splice_into_original": False,
        }
        for row in case["phase_traces"]
        if row["new_battle_events"]
    ]
    return {
        "schema": "ck3-episode01-evidence-board-v1",
        "case_sha256": EPISODE01_CASE_SHA256,
        "game_version": case["game_version"],
        "combat_id": case["combat_id"],
        "first_numeric_replay_divergence_day": case["first_numeric_divergence_source_day"],
        "original_beats": original_beats,
        "independent_replay_event_beats": replay_beats,
        "conditional_main_tick_parity": {
            "report_sha256": EPISODE01_PARITY_SHA256,
            "conditioned_on_native_outgoing_damage": True,
            "stable_bounded_exact_days": parity["stable_bounded_exact_days"],
            "all_source_exact_days": [
                row["source_day"] for row in parity["source_days"]
                if row["all_source_fighting_regiments_current_raw_exact"]
            ],
            "residual_or_identity_change_days": [
                {
                    "source_day": row["source_day"],
                    "attacker_mismatch_count": row["attacker"]["mismatch_count"],
                    "defender_mismatch_count": row["defender"]["mismatch_count"],
                    "same_attacker_army_ids": row["same_attacker_army_ids"],
                    "trace_status": row["trace_status"],
                }
                for row in parity["source_days"]
                if not row["stable_bounded_current_raw_exact"]
            ],
            "win_probability_available": False,
        },
        "original_terminal": {
            "date_raw": case["terminal_date_raw"],
            "winner_relative_to_player": case["winner_relative_to_player"],
            "player_warscore_delta_raw": case["battle_warscore_player_delta_raw_q100000"],
        },
        "calibrated_win_probability_available": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"refusing to overwrite evidence board: {args.output}")
    board = build_board()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(board, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest().upper(),
        "original_beats": len(board["original_beats"]),
        "replay_event_beats": len(board["independent_replay_event_beats"]),
        "strict_parity_days": board["conditional_main_tick_parity"]["stable_bounded_exact_days"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
