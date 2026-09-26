"""Bound two natural reinforcements to original schedule/fire boundary receipts.

The seven-boundary trace is RED on these days.  Its first two records are
valid; the partial pre-fire record retains the native callback boundary and
the newly expanded side-army vector before the frozen pointer map rejects it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

CASES = ((11, 22), (21, 28))
RESPONSES = Path("ck3-output/interactive-requests-responses")


def _read(path: Path) -> tuple[dict, str]:
    data = path.read_bytes()
    value = json.loads(data)
    if value.get("result") != "CALL_COMPLETED":
        raise ValueError(f"incomplete original response: {path}")
    return value["body"], hashlib.sha256(data).hexdigest().upper()


def _enemy_armies(body: dict) -> list[int]:
    wars = body.get("active_wars")
    if not isinstance(wars, list) or len(wars) != 1:
        raise ValueError("expected one source war")
    return [row["army_id"] for row in wars[0]["enemy_armies"] if row["in_combat"] is True]


def _one(attempt: Path, source_day: int, joining_army_id: int) -> dict:
    base = attempt / RESPONSES
    finish, finish_sha = _read(base / f"trace-d{source_day:02d}-finish.json")
    before, before_sha = _read(base / f"trace-d{source_day:02d}-before-snapshot.json")
    after, after_sha = _read(base / f"trace-d{source_day:02d}-after-snapshot.json")
    control_receipt, control_sha = _read(
        base / f"trace-d{source_day + 1:02d}-before-control.json"
    )
    control = control_receipt["battle_control_snapshot"]
    if finish["accepted"] is not True or finish["status"] != "trace_unavailable":
        raise ValueError("source day was not a retained RED trace")
    managed = finish["managed_trace"]
    checkpoint = managed["managed_checkpoint"]
    trace = managed["trace"]
    if not (checkpoint["exact_one_day_observed"]
            and checkpoint["boundary_dates_match_checkpoint"]
            and checkpoint["detours_uninstalled"]
            and checkpoint["after"]["date_raw"] - checkpoint["before"]["date_raw"] == 24
            and trace["record_count"] == 7
            and trace["failure_flags"] == 1040):
        raise ValueError("bounded RED provenance changed")
    schedule, after_schedule, pre_fire = trace["records"][:3]
    if ([row["capture_failure_flags"] for row in (schedule, after_schedule, pre_fire)]
            != [0, 0, 16]
            or schedule["boundary"] != "native_capture_before_side0_schedule_call_0x27FB58F"
            or after_schedule["boundary"] != "native_capture_after_side1_schedule_return_0x27FB5AC"
            or pre_fire["boundary"] != "native_capture_before_side0_phase_fire_entry_0x23C9900"):
        raise ValueError("schedule/fire boundary sequence changed")
    before_armies = _enemy_armies(before)
    after_armies = _enemy_armies(after)
    control_armies = [row["public_cunit_id"] for row in control["attacker"]["ordered_armies"]]
    scheduled_armies = [row["army_id"] for row in after_schedule["sides"][0]["armies"]]
    partial_armies = [row["army_id"] for row in pre_fire["sides"][0]["armies"]]
    if (joining_army_id in before_armies or joining_army_id not in after_armies
            or len(after_armies) != len(before_armies) + 1
            or sorted(after_armies) != sorted([*before_armies, joining_army_id])
            or sorted(scheduled_armies) != sorted(before_armies)
            or control["combat_id"] != finish["combat_id"]
            or control["observed_date_raw"] != checkpoint["after"]["date_raw"]
            or control_armies != [*scheduled_armies, joining_army_id]
            or partial_armies != [*scheduled_armies, 0]
            or pre_fire["native_date_raw"] != after_schedule["native_date_raw"] + 24
            or pre_fire["phase_day"] != after_schedule["phase_day"] + 1):
        raise ValueError(f"new army did not appear between schedule and pre-fire: "
                         f"day={source_day}, before={before_armies}, after={after_armies}, "
                         f"scheduled={scheduled_armies}, control={control_armies}, "
                         f"partial={partial_armies}, "
                         f"dates={after_schedule['native_date_raw']}/{pre_fire['native_date_raw']}, "
                         f"phase_days={after_schedule['phase_day']}/{pre_fire['phase_day']}")
    return {
        "source_day": source_day,
        "arrival_day": source_day + 1,
        "combat_id": finish["combat_id"],
        "joining_army_id": joining_army_id,
        "finish_response_sha256": finish_sha,
        "before_snapshot_sha256": before_sha,
        "after_snapshot_sha256": after_sha,
        "arrival_control_sha256": control_sha,
        "source_date_raw": checkpoint["before"]["date_raw"],
        "arrival_date_raw": checkpoint["after"]["date_raw"],
        "scheduled_side0_army_ids": scheduled_armies,
        "arrival_snapshot_side0_army_ids": after_armies,
        "arrival_control_side0_army_ids_in_stored_order": control_armies,
        "partial_prefire_side0_army_ids": partial_armies,
        "schedule_side0_fighting_raw": after_schedule["sides"][0]["current_fighting_total_raw"],
        "prefire_side0_fighting_raw": pre_fire["sides"][0]["current_fighting_total_raw"],
        "prefire_capture_failure_flags": pre_fire["capture_failure_flags"],
        "whole_trace_status": finish["status"],
        "whole_trace_failure_flags": trace["failure_flags"],
        "join_before_side0_phase_fire_proven_for_this_day": True,
        "complete_seven_boundary_state_proven": False,
        "general_same_day_manager_order_proven": False,
    }


def project(attempt: Path) -> dict:
    rows = [_one(attempt, day, army) for day, army in CASES]
    if len({row["combat_id"] for row in rows}) != 1:
        raise ValueError("cases do not share CombatID")
    return {"schema": "ck3.native_join_phase_order_partial.v2",
            "game_build": "1.19.0.6", "combat_id": rows[0]["combat_id"],
            "cases": rows, "all_cases_join_before_side0_fire": True,
            "all_cases_full_trace_ready": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = project(args.attempt)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output),
                      "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest().upper()}))


if __name__ == "__main__":
    main()
