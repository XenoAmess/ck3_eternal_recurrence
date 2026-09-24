"""Project same-day native zero-roll context plus observed rolls against R14-boundary advantage.

This closes conditional roll arithmetic on the paired replay. It does not
predict the zero-roll context, future rolls, event effects, or joining policy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "ck3_autonomous_player" / "src"))
from xar_autoplayer.simulation.native_advantage import resolved_advantage_with_commander_rolls_raw
from xar_autoplayer.simulation.native_battle_case import (
    EPISODE01_PAIRED_COUNTER_SHA256,
    load_episode01_paired_counter_r14_parity,
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def response(path: Path) -> dict:
    row = json.loads(path.read_text(encoding="utf-8"))
    if row.get("result") != "CALL_COMPLETED":
        raise ValueError(f"native response incomplete: {path}")
    return row["body"]


def project(paired_run: Path) -> dict:
    paired = load_episode01_paired_counter_r14_parity()
    if Path(paired["capture_run"]).resolve() != paired_run.resolve():
        raise ValueError("paired run identity drifted")
    responses = paired_run / "ck3-output" / "interactive-requests-responses"
    days = []
    for source in paired["days"]:
        day = source["day"]
        v3_path = responses / f"d{day:02d}-v3.json"
        trace_path = responses / f"d{day:02d}-finish.json"
        if digest(v3_path) != source["v3_response_sha256"] or digest(trace_path) != source["trace_response_sha256"]:
            raise ValueError(f"day {day}: paired native bytes changed")
        v3 = response(v3_path)
        phase = v3["combat_simulation_inputs"]["phase_event_inputs"]
        model = phase["advantage_model"]
        dynamic = model["resolved_dynamic"]
        if (v3["status"] != "available" or phase["status"] != "available"
                or model["status"] != "available" or dynamic["status"] != "available"
                or dynamic["helper_status"] != "original_helpers_matched"
                or dynamic["original_total_helper_match"] is not True):
            raise ValueError(f"day {day}: native advantage inputs unavailable")
        trace = response(trace_path)["managed_trace"]["trace"]
        boundary = trace["records"][source["boundary_index"]]
        if (boundary["native_date_raw"] != source["date_raw"]
                or boundary["capture_failure_flags"] != 0
                or boundary["base_advantage_raw"] != model["base_static_accumulator_raw"]):
            raise ValueError(f"day {day}: local advantage boundary unavailable")
        zero = dynamic["resolved_advantage_at_zero_roll_raw"]
        sides = dynamic["sides"]
        if (len(sides) != 2
                or [s["side"] for s in sides] != ["attacker", "defender"]
                or zero != model["base_static_accumulator_raw"] + sides[0]["side_total_raw"] - sides[1]["side_total_raw"]):
            raise ValueError(f"day {day}: zero-roll decomposition drifted")
        rolls = boundary["advantage_rolls_raw"]
        if not isinstance(rolls, list) or len(rolls) != 2 or any(not isinstance(r, int) for r in rolls):
            raise ValueError(f"day {day}: roll points unavailable")
        projected = resolved_advantage_with_commander_rolls_raw(zero, rolls[0], rolls[1])
        observed = boundary["resolved_advantage_raw"]
        days.append({
            "day": day,
            "date_raw": source["date_raw"],
            "zero_roll_advantage_raw": zero,
            "base_static_advantage_raw": model["base_static_accumulator_raw"],
            "side_dynamic_raw": [s["side_total_raw"] for s in sides],
            "observed_roll_points": rolls,
            "projected_advantage_raw": projected,
            "native_advantage_raw": observed,
            "delta_raw": projected - observed,
            "whole_phase_trace_status": source["trace_status"],
            "native_v3_response_sha256": source["v3_response_sha256"],
            "native_trace_response_sha256": source["trace_response_sha256"],
        })
    if [row["day"] for row in days] != list(range(4, 27)):
        raise ValueError("paired main-day span changed")
    return {
        "schema": "xar.ck3.episode01.paired-advantage-parity/v1",
        "game_build": "CK3 1.19.0.6",
        "source_paired_report_sha256": EPISODE01_PAIRED_COUNTER_SHA256,
        "paired_run": str(paired_run.resolve()),
        "observed_main_days": len(days),
        "conditional_exact_advantage_days": sum(row["delta_raw"] == 0 for row in days),
        "conditioned_on": ["native_same_date_zero_roll_advantage_context", "native_observed_commander_roll_points"],
        "zero_roll_context_reconstructed_independently": False,
        "future_rolls_predicted": False,
        "phase_effect_transition_complete": False,
        "join_policy_reconstructed": False,
        "whole_battle_win_probability_available": False,
        "planner_usable": False,
        "days": days,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paired-run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = project(args.paired_run)
    with args.output.open("x", encoding="utf-8", newline="\n") as out:
        json.dump(result, out, ensure_ascii=False, indent=2)
        out.write("\n")
    print(json.dumps({"exact": result["conditional_exact_advantage_days"],
                      "observed": result["observed_main_days"], "sha256": digest(args.output)}))


if __name__ == "__main__":
    main()
