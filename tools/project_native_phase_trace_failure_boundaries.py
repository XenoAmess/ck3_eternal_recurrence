"""Classify exact local trace failure boundaries without promoting RED traces."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "ck3_autonomous_player" / "src"))
from xar_autoplayer.simulation.native_battle_case import (
    EPISODE01_PAIRED_COUNTER_SHA256,
    load_episode01_paired_counter_r14_parity,
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def body(path: Path) -> dict:
    row = json.loads(path.read_text(encoding="utf-8"))
    if row.get("result") != "CALL_COMPLETED":
        raise ValueError(f"source response incomplete: {path}")
    return row["body"]


def project(paired_run: Path) -> dict:
    paired = load_episode01_paired_counter_r14_parity()
    if Path(paired["capture_run"]).resolve() != paired_run.resolve():
        raise ValueError("paired replay path drifted")
    responses = paired_run / "ck3-output" / "interactive-requests-responses"
    red = []
    for source in paired["days"]:
        day = source["day"]
        trace_path = responses / f"d{day:02d}-finish.json"
        if digest(trace_path) != source["trace_response_sha256"]:
            raise ValueError(f"day {day}: native trace bytes drifted")
        trace = body(trace_path)["managed_trace"]["trace"]
        failures = [index for index, record in enumerate(trace["records"])
                    if record["capture_failure_flags"] != 0]
        if not failures:
            if source["trace_status"] != "bounded_trace_available":
                raise ValueError(f"day {day}: report/trace status drifted")
            continue
        if (source["trace_status"] != "trace_unavailable"
                or trace["status"] != "failed"
                or trace["record_count"] != 7
                or trace["failure_flags"] != 1040
                or any(trace["records"][index]["capture_failure_flags"] != 16
                       for index in failures)):
            raise ValueError(f"day {day}: failure shape drifted")
        advance_path = responses / f"d{day:02d}-advance.json"
        advance = body(advance_path)
        before = advance["war_progress_before"]["wars"][0]["enemy_armies"]
        after = advance["war_progress_after"]["wars"][0]["enemy_armies"]
        before_combat = {a["army_id"] for a in before if a["in_combat"]}
        joined = [a["army_id"] for a in after
                  if a["in_combat"] and a["army_id"] not in before_combat]
        first = failures[0]
        if day in (11, 21):
            expected = 22 if day == 11 else 28
            if (first != 2 or failures != [2, 3, 4, 5, 6]
                    or joined != [expected]
                    or [a["army_id"] for a in before if a["army_id"] == expected and not a["in_combat"]] != [expected]
                    or trace["records"][2]["sides"][0]["armies"][-1]["army_id"] != 0):
                raise ValueError(f"day {day}: join boundary signature drifted")
            classification = "frozen_begin_roster_cannot_resolve_new_army"
        elif day == 26:
            if first != 6 or failures != [6] or joined:
                raise ValueError("day 26: final-only boundary signature drifted")
            classification = "final_paused_query_identity_failure_unlocalized"
        else:
            raise ValueError(f"unexpected RED day {day}")
        red.append({
            "day": day,
            "first_failing_boundary_index": first,
            "locally_valid_boundary_indices": list(range(first)),
            "failing_boundary_indices": failures,
            "capture_failure_bit": 16,
            "aggregate_failure_flags": 1040,
            "same_day_newly_joined_enemy_army_ids": joined,
            "classification": classification,
            "full_trace_available": False,
            "native_trace_response_sha256": source["trace_response_sha256"],
            "daily_advance_response_sha256": digest(advance_path),
        })
    if [row["day"] for row in red] != [11, 21, 26]:
        raise ValueError("RED day census drifted")
    return {
        "schema": "xar.ck3.episode01.paired-trace-failure-boundaries/v1",
        "game_build": "CK3 1.19.0.6",
        "source_paired_report_sha256": EPISODE01_PAIRED_COUNTER_SHA256,
        "paired_run": str(paired_run.resolve()),
        "observed_main_days": 23,
        "whole_trace_green_days": 20,
        "whole_trace_red_days": 3,
        "red_days": red,
        "join_day_capture_repaired": False,
        "final_identity_failure_repaired": False,
        "phase_effect_transition_complete": False,
        "whole_battle_win_probability_available": False,
        "planner_usable": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paired-run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = project(args.paired_run)
    with args.output.open("x", encoding="utf-8", newline="\n") as out:
        json.dump(report, out, ensure_ascii=False, indent=2)
        out.write("\n")
    print(json.dumps({"red_days": [row["day"] for row in report["red_days"]],
                      "sha256": digest(args.output)}))


if __name__ == "__main__":
    main()
