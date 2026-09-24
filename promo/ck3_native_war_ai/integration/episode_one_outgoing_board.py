"""Build a film-safe main-damage board from the shared agent parity report."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "ck3_autonomous_player" / "src"))
from xar_autoplayer.simulation.native_battle_case import (  # noqa: E402
    EPISODE01_OUTGOING_SHA256,
    load_episode01_main_outgoing_conditional_parity,
)


def build_board() -> dict:
    report = load_episode01_main_outgoing_conditional_parity()
    examples = []
    for row in report["source_days"]:
        if row["source_day"] not in (4, 5, 11, 21):
            continue
        examples.append({
            "source_day": row["source_day"],
            "phase_trace_status": row["phase_trace_status"],
            "control_receipt_sha256": row["control_receipt_sha256"],
            "finish_receipt_sha256": row["finish_receipt_sha256"],
            "resolved_advantage_raw": row["resolved_advantage_raw"],
            "final_combat_width": row["final_combat_width"],
            "width_source": row["width_source"],
            "observed_joined_fighting_men_raw": row["observed_joined_fighting_men_raw"],
            "sides": row["sides"],
            "both_sides_exact": row["both_sides_exact"],
        })
    return {
        "schema": "ck3-episode01-outgoing-damage-board-v1",
        "source_report_sha256": EPISODE01_OUTGOING_SHA256,
        "game_version": report["game_version"],
        "combat_id": report["combat_id"],
        "trajectory": report["trajectory"],
        "source_days_compared": len(report["source_days"]),
        "native_outgoing_values_compared": report["native_outgoing_values_compared"],
        "exact_outgoing_values": report["exact_outgoing_values"],
        "examples": examples,
        "conditioned_on_native_post_counter_attack": True,
        "conditioned_on_native_advantage": True,
        "conditioned_on_observed_joined_roster_and_width": True,
        "post_counter_attack_reconstructed": False,
        "advantage_reconstructed": False,
        "join_policy_reconstructed": False,
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
    print(json.dumps({"output": str(args.output),
                      "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest().upper(),
                      "examples": len(board["examples"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
