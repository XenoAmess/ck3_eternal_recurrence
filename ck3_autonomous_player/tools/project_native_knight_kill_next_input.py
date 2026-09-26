"""Bind a day-26 knight kill to a fresh day-27 native v3 planner input."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def response(attempt: Path, name: str) -> tuple[dict, str]:
    path = attempt / "ck3-output/interactive-requests-responses" / name
    row = json.loads(path.read_text(encoding="utf-8"))
    if row["result"] != "CALL_COMPLETED":
        raise ValueError(f"incomplete native response: {name}")
    return row["body"], digest(path)


def indexed(base: dict, key: str, member_key: str) -> dict[int, tuple[int, dict]]:
    return {row[key]: (army["army_id"], row)
            for army in base["armies"] for row in army[member_key]}


def index_regiments(base: dict) -> dict[int, tuple[int, dict]]:
    return indexed(base, "regiment_id", "regiments")


def index_knights(base: dict) -> dict[int, tuple[int, dict]]:
    return {row["character_id"]: (army["army_id"], row)
            for army in base["armies"] for row in army["knights"]["members"]}


def build(before: Path, after: Path) -> dict:
    summary = json.loads((before / "one-day-summary.json").read_text(encoding="utf-8"))
    before_v3, before_v3_sha = response(before, "004-v3.json")
    finish, finish_sha = response(before, "007-finish.json")
    save, save_sha = response(before, "008-after-save.json")
    if (finish_sha != summary["trace_response_sha256"]
            or save_sha != summary["post_event_save_response_sha256"]
            or digest(before / "d27-postevent-immutable.ck3")
               != summary["post_event_save_sha256"].upper()):
        raise ValueError("source attempt SHA binding failed")
    trace = finish["managed_trace"]["trace"]
    final = trace["records"][6]
    target = [row for row in final["characters"] if row["character_id"] == 33437]
    if (finish["status"] != "bounded_trace_available" or trace["failure_flags"] != 0
            or len(target) != 1 or target[0]["death_marker_present"] is not True
            or target[0]["current_regiment_id"] != 0):
        raise ValueError("source trace kill/detach boundary not established")
    snapshot, snapshot_sha = response(after, "001-initial-snapshot.json")
    control, control_sha = response(after, "002-control.json")
    after_v3, after_v3_sha = response(after, "003-v3.json")
    after_summary = json.loads((after / "next-input-summary.json").read_text(encoding="utf-8"))
    capture_path = after / "ck3-output/capture-report.json"
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    if (snapshot_sha != after_summary["snapshot_response_sha256"]
            or control_sha != after_summary["control_response_sha256"]
            or after_v3_sha != after_summary["v3_response_sha256"]
            or after_summary["source_save_sha256"] != summary["post_event_save_sha256"].upper()
            or capture["checkpoint_source"]["save"]["sha256"].upper()
               != summary["post_event_save_sha256"].upper()
            or snapshot["paused"] is not True
            or snapshot["date_raw"] != 53146872
            or after_v3["queried_revision"] != snapshot["revision"]
            or control["queried_revision"] != snapshot["revision"]
            or control["battle_control_snapshot"]["combat_id"] != 16777218
            or capture["worker"]["ok"] is not True
            or capture["environment_session_complete"] is not True
            or capture["cleanup_process_inventory"]["processes"]):
        raise ValueError("next-day isolated paused query or cleanup failed")
    first = before_v3["combat_simulation_inputs"]["base_inputs"]
    second = after_v3["combat_simulation_inputs"]["base_inputs"]
    if (before_v3["combat_simulation_inputs"]["completeness"]["base_input_observation_ready"] is not True
            or after_v3["combat_simulation_inputs"]["completeness"]["base_input_observation_ready"] is not True):
        raise ValueError("native v3 base inputs unavailable")
    regiments_before, regiments_after = index_regiments(first), index_regiments(second)
    knights_before, knights_after = index_knights(first), index_knights(second)
    if (len(regiments_before) != 69 or len(regiments_after) != 68
            or regiments_before.keys() - regiments_after.keys() != {65}
            or regiments_after.keys() - regiments_before.keys()
            or len(knights_before) != 30 or len(knights_after) != 29
            or knights_before.keys() - knights_after.keys() != {33437}
            or knights_after.keys() - knights_before.keys()
            or any(regiments_before[key] != regiments_after[key]
                   for key in regiments_before.keys() & regiments_after.keys())
            or any(knights_before[key] != knights_after[key]
                   for key in knights_before.keys() & knights_after.keys())
            or 34120 not in knights_after):
        raise ValueError("native v3 input transition differs from expected one-knight removal")
    return {
        "schema": "ck3.native_knight_kill_next_input.v1",
        "game_build": "1.19.0.6",
        "combat_id": 16777218,
        "source_day": 26,
        "next_day": 27,
        "source_save_sha256": summary["source_checkpoint_sha256"].upper(),
        "post_event_save_sha256": summary["post_event_save_sha256"].upper(),
        "source_v3_response_sha256": before_v3_sha,
        "source_trace_response_sha256": finish_sha,
        "next_snapshot_response_sha256": snapshot_sha,
        "next_control_response_sha256": control_sha,
        "next_v3_response_sha256": after_v3_sha,
        "next_capture_report_sha256": digest(capture_path),
        "next_capture_cleanup_processes": 0,
        "removed_regiment_id": 65,
        "removed_knight_character_id": 33437,
        "remaining_regiments_identical_v3_base_inputs": 68,
        "remaining_knights_identical_v3_base_inputs": 29,
        "killer_character_id": 34120,
        "killer_next_v3_member": knights_after[34120][1],
        "full_mutable_write_set_proven": False,
        "full_casualty_state_identical_proven": False,
        "other_event_paths_proven": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before-attempt", required=True, type=Path)
    parser.add_argument("--after-attempt", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = build(args.before_attempt, args.after_attempt)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output), "sha256": digest(args.output)}))


if __name__ == "__main__":
    main()
