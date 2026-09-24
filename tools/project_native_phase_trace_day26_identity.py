"""Localize the day-26 final-query identity failure from immutable native receipts.

This is a diagnostic of the research-only capture transport, not a battle
effect model. The earlier v1 failure report is kept unchanged.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from project_native_phase_trace_failure_boundaries import body, digest, project as project_failures


REPO = Path(__file__).resolve().parents[1]
RING_SOURCE = REPO / "ck3_autonomous_player/native_bridge/src/combat_phase_event_trace_ring_v1.cpp"


def project(paired_run: Path) -> dict:
    previous = project_failures(paired_run)
    day26 = next(row for row in previous["red_days"] if row["day"] == 26)
    path = paired_run / "ck3-output/interactive-requests-responses/d26-finish.json"
    trace = body(path)["managed_trace"]["trace"]
    fire_before, fire_after, final = trace["records"][4:7]
    prior_events = fire_before["battle_events"]
    new_events = fire_after["battle_events"]
    expected_event = {
        "left_character_id": 34867,
        "right_character_id": 47032,
        "stable_key": "knight_killed_by_enemy",
        "type_raw": 3,
        "side_index": 1,
        "target_right": False,
    }
    if (day26["first_failing_boundary_index"] != 6
            or day26["same_day_newly_joined_enemy_army_ids"]
            or new_events != prior_events + [expected_event]
            or fire_after["capture_failure_flags"] != 0
            or final["capture_failure_flags"] != 16):
        raise ValueError("day-26 event and final failure signature changed")
    side_before = fire_after["sides"][1]
    side_final = final["sides"][1]
    scheduled_before = side_before["scheduled_knights"]
    scheduled_final = side_final["scheduled_knights"]
    if (len(scheduled_before) != 1 or len(scheduled_final) != 1
            or scheduled_before[0]["regiment_id"] != 62
            or scheduled_before[0]["current_character_id"] != 34867
            or scheduled_final[0]["regiment_id"] != 62
            or scheduled_final[0]["current_character_id"] != 0
            or scheduled_before[0]["event_identity_token"]
            != scheduled_final[0]["event_identity_token"]
            or not any(row["regiment_id"] == 62 for row in side_before["knights"])
            or any(row["regiment_id"] == 62 for row in side_final["knights"])
            or not any(row["regiment_id"] == 62 for row in side_before["regiments"])
            or any(row["regiment_id"] == 62 for row in side_final["regiments"])
            or not side_before["armies"] or not side_final["armies"]
            or final["characters"] or final["battle_events"] or final["accolades"]):
        raise ValueError("day-26 scheduled regiment/side capture signature changed")
    source = RING_SOURCE.read_text(encoding="utf-8")
    guards = (
        "row.regiment_id = LoadAt<std::int32_t>(\n        native_row, kSideScheduledKnightRegimentIdOffset);",
        "LoadAt<std::int32_t>(resolved->object, kRegimentIdOffset) !=\n            row.regiment_id",
        "row.current_character_id =\n        LoadAt<std::int32_t>(resolved->object, kRegimentCharacterIdOffset);",
        "!ReadSide(plan, 1, output.sides[1], failure_flags) ||\n      !ReadCharacters(plan, output, failure_flags)",
    )
    if not all(guard in source for guard in guards):
        raise ValueError("exact-build capture guard/order changed; re-review inference")
    return {
        "schema": "xar.ck3.episode01.paired-trace-day26-identity/v1",
        "game_build": previous["game_build"],
        "source_failure_report_sha256": hashlib.sha256(
            (REPO / "ck3_autonomous_player/src/xar_autoplayer/simulation/data/"
             "ck3_1_19_0_6_episode01_messina_paired_trace_failure_boundaries.json").read_bytes()
        ).hexdigest().upper(),
        "source_native_trace_response_sha256": digest(path),
        "capture_source_sha256": digest(RING_SOURCE),
        "day": 26,
        "first_failing_boundary_index": 6,
        "event_appended_between_boundaries": [4, 5],
        "appended_event": expected_event,
        "last_valid_target_regiment_id": 62,
        "last_valid_target_character_id": 34867,
        "final_side1_knight_regiment_present": False,
        "final_side1_regiment_bucket_present": False,
        "final_side1_scheduled_regiment_id": 62,
        "final_side1_scheduled_character_id_field": 0,
        "inferred_first_failing_read": "ReadSide(side1).scheduled_knights.regiment_identity_guard",
        "inference_basis": "scheduled row identity fields assigned; character field remains default; later character/battle-event/accolade reads not reached under exact source order",
        "same_day_post_event_save_available": False,
        "event_effect_write_set_complete": False,
        "full_trace_available": False,
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
    print(json.dumps({"output": str(args.output), "sha256": digest(args.output)}))


if __name__ == "__main__":
    main()
