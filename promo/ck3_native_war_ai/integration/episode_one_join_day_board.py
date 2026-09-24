"""Build a film-safe reinforcement arrival/casualty board from agent evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "ck3_autonomous_player" / "src"))
from xar_autoplayer.simulation.native_battle_case import (  # noqa: E402
    EPISODE01_JOIN_DAY_SHA256,
    EPISODE01_JOIN_KERNEL_SHA256,
    EPISODE01_JOIN_KERNEL_V2_SHA256,
    load_episode01_join_day_casualties,
    load_episode01_join_day_kernel_parity,
    load_episode01_join_day_kernel_parity_v2,
)


def build_board() -> dict:
    evidence = load_episode01_join_day_casualties()
    parity = load_episode01_join_day_kernel_parity()
    parity_by_day = {row["source_day"]: row for row in parity["source_days"]}
    refreshed = load_episode01_join_day_kernel_parity_v2()
    refreshed_by_day = {row["source_day"]: row for row in refreshed["source_days"]}
    joins = []
    for row in evidence["join_observations"]:
        kernel = parity_by_day[row["source_day"]]
        kernel_refreshed = refreshed_by_day[row["source_day"]]
        if (kernel["arrival_day"] != row["arrival_day"]
                or kernel["army_id"] != row["army_id"]
                or kernel_refreshed["arrival_day"] != row["arrival_day"]
                or kernel_refreshed["army_id"] != row["army_id"]):
            raise ValueError("join-day kernel and observed roster do not bind")
        fighting = [item for item in row["regiments"] if item["fights_in_main_phase"]]
        prejoin = sum(item["prejoin_saved_current_raw"] for item in fighting)
        current = sum(item["arrival_day_current_fighting_raw"] for item in fighting)
        soft = sum(item["arrival_day_soft_casualties_raw"] for item in fighting)
        hard = sum(item["arrival_day_hard_casualties_raw"] for item in fighting)
        if prejoin - current != soft + hard:
            raise ValueError("join-day casualty totals do not reconcile")
        joins.append({
            "source_day": row["source_day"],
            "arrival_day": row["arrival_day"],
            "army_id": row["army_id"],
            "arrival_date_raw": row["arrival_phase_date_raw"],
            "prejoin_snapshot_sha256": row["snapshots"][0]["receipt_sha256"],
            "arrival_snapshot_sha256": row["snapshots"][1]["receipt_sha256"],
            "arrival_phase_receipt_sha256": row["arrival_phase_receipt_sha256"],
            "fighting_regiment_count": len(fighting),
            "nonfighting_regiment_count": len(row["regiments"]) - len(fighting),
            "prejoin_fighting_current_raw": prejoin,
            "arrival_day_fighting_current_raw": current,
            "arrival_day_soft_casualties_raw": soft,
            "arrival_day_hard_casualties_raw": hard,
            "sample_regiment": next(item for item in fighting if item["regiment_id"] in (175, 224)),
            "same_day_casualties_observed": True,
            "conditional_kernel_joined_exact_count": kernel["joined_regiment_current_exact_count"],
            "conditional_kernel_whole_side_exact": kernel["whole_side_current_exact"],
            "conditional_kernel_residuals": kernel["residuals"],
            "native_pre_schedule_toughness_changes":
                kernel_refreshed["old_regiment_effective_toughness_changes"],
            "refreshed_conditional_kernel_whole_side_exact":
                kernel_refreshed["whole_side_current_exact"],
            "kernel_uses_native_outgoing_damage": True,
            "kernel_uses_native_pre_schedule_toughness": True,
            "source_day_whole_trace_available": False,
        })
    return {
        "schema": "ck3-episode01-join-day-board-v3",
        "source_report_sha256": EPISODE01_JOIN_DAY_SHA256,
        "conditional_kernel_report_sha256": EPISODE01_JOIN_KERNEL_SHA256,
        "refreshed_conditional_kernel_report_sha256": EPISODE01_JOIN_KERNEL_V2_SHA256,
        "game_version": evidence["game_version"],
        "combat_id": evidence["combat_id"],
        "phase_trace_trajectory": evidence["phase_trace_trajectory"],
        "joins": joins,
        "same_day_reinforcement_damage_observed": True,
        "global_manager_order_proven": False,
        "outgoing_damage_reconstructed": False,
        "join_policy_reconstructed": False,
        "effective_toughness_refresh_reconstructed": False,
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
    print(json.dumps({"output": str(args.output),
                      "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest().upper(),
                      "joins": len(board["joins"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
