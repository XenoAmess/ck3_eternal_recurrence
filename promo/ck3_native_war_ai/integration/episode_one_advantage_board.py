"""Build the roll-cadence board from the agent's same-run advantage evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "ck3_autonomous_player" / "src"))
from xar_autoplayer.simulation.native_battle_case import (  # noqa: E402
    EPISODE01_PAIRED_ADVANTAGE_SHA256,
    load_episode01_paired_advantage_parity,
)


def build_board() -> dict:
    report = load_episode01_paired_advantage_parity()
    periods = []
    for row in report["days"]:
        if not periods or periods[-1]["observed_roll_points"] != row["observed_roll_points"]:
            periods.append({
                "start_day": row["day"],
                "end_day": row["day"],
                "observed_roll_points": row["observed_roll_points"],
                "zero_roll_advantage_raw": row["zero_roll_advantage_raw"],
                "resolved_advantage_raw": row["native_advantage_raw"],
            })
        else:
            periods[-1]["end_day"] = row["day"]
    return {
        "schema": "ck3-episode01-advantage-roll-board-v1",
        "source_report_sha256": EPISODE01_PAIRED_ADVANTAGE_SHA256,
        "main_days": report["observed_main_days"],
        "conditional_exact_advantage_days": report["conditional_exact_advantage_days"],
        "observed_roll_periods": periods,
        "conditioned_on_native_zero_roll_context": True,
        "conditioned_on_native_observed_roll_points": True,
        "whole_phase_trace_red_days": [row["day"] for row in report["days"]
                                        if row["whole_phase_trace_status"] != "bounded_trace_available"],
        "future_rolls_predicted": False,
        "whole_battle_win_probability_available": False,
        "planner_usable": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    board = build_board()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as out:
        json.dump(board, out, ensure_ascii=False, indent=2)
        out.write("\n")
    print(json.dumps({"sha256": hashlib.sha256(args.output.read_bytes()).hexdigest().upper()}))


if __name__ == "__main__":
    main()
