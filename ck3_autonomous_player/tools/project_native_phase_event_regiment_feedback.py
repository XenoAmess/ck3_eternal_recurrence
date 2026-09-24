"""Bind one wound save to later native prowess and combat-entry refreshes.

This is a read-only exact-build observation of an independent replay. It does
not prove that the ledger entry was the unique cause of every later delta.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
from xar_autoplayer.simulation.native_battle_case import (  # noqa: E402
    EPISODE01_CASE_SHA256,
    EPISODE01_JOIN_KERNEL_SHA256,
    EPISODE01_JOIN_KERNEL_V2_SHA256,
    EPISODE01_PHASE_EVENT_SAVE_SHA256,
    EPISODE01_PHASE_EVENT_SHA256,
    load_episode01_join_day_kernel_parity,
    load_episode01_join_day_kernel_parity_v2,
    load_episode01_native_battle_case,
    load_episode01_phase_event_observations,
    load_episode01_phase_event_save_feedback,
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def phase_receipt(path: Path, expected_sha: str) -> dict:
    if sha(path) != expected_sha:
        raise ValueError(f"phase receipt SHA drift: {path}")
    envelope = json.loads(path.read_text(encoding="utf-8"))
    if envelope.get("result") != "CALL_COMPLETED":
        raise ValueError(f"phase receipt incomplete: {path}")
    return envelope["body"]["managed_trace"]["trace"]


def stage(record: dict, *, day: int, index: int) -> dict:
    if record["capture_failure_flags"] != 0:
        raise ValueError(f"day {day} record {index} capture failed")
    characters = [row for row in record["characters"] if row["character_id"] == 54144]
    regiments = [row for side in record["sides"] for row in side["regiments"]
                 if row["regiment_id"] == 220]
    if len(characters) != 1 or len(regiments) != 1:
        raise ValueError(f"day {day} record {index} target identity ambiguous")
    character, regiment = characters[0], regiments[0]
    if (character["current_regiment_id"] != 220
            or character["current_regiment_back_reference_matches"] is not True
            or regiment["fights_in_main_phase"] is not True):
        raise ValueError(f"day {day} record {index} character/regiment link failed")
    return {
        "source_day": day,
        "record_index": index,
        "boundary": record["boundary"],
        "native_date_raw": record["native_date_raw"],
        "capture_failure_flags": 0,
        "character_id": 54144,
        "regiment_id": 220,
        "prowess": character["prowess"],
        "martial": character["martial"],
        "regiment_current_fighting_raw": regiment["current_fighting_raw"],
        "effective_damage_raw": regiment["effective_damage_raw"],
        "effective_toughness_raw": regiment["effective_toughness_raw"],
    }


def project(trace_root: Path) -> dict:
    case = load_episode01_native_battle_case()
    events = load_episode01_phase_event_observations()
    saves = load_episode01_phase_event_save_feedback()
    stale = load_episode01_join_day_kernel_parity()
    refreshed = load_episode01_join_day_kernel_parity_v2()
    event = next(row for row in events["event_fire_pairs"] if row["source_day"] == 9)
    save = next(row for row in saves["event_save_pairs"] if row["event_source_day"] == 9)
    if (event["appended_battle_events"][0]["stable_key"] != "knight_wounded_by_enemy"
            or event["target_character_observations"][0]["character_id"] != 54144
            or save["target_character_id"] != 54144
            or save["saves"][0]["character"]["regiment_id"] != 220
            or save["saves"][1]["character"]["wounded_rank"] != 1):
        raise ValueError("day 9 wound save and ledger do not bind")
    by_day = {row["source_day"]: row for row in case["phase_traces"]}
    root = trace_root / "ck3-output" / "interactive-requests-responses"
    phase = {}
    receipt_hashes = {}
    for day in (9, 10, 11):
        path = root / f"trace-d{day:02d}-finish.json"
        receipt_hashes[str(day)] = sha(path)
        phase[day] = phase_receipt(path, by_day[day]["finish_receipt_sha256"])
    rows = [stage(phase[day]["records"][index], day=day, index=index)
            for day, index in ((9, 2), (10, 0), (10, 2), (11, 0))]
    if ([(row["prowess"], row["effective_toughness_raw"]) for row in rows]
            != [(4, 7400000), (4, 7400000), (2, 7400000), (2, 3700000)]
            or [(row["effective_damage_raw"]) for row in rows]
            != [37000000, 37000000, 37000000, 18500000]):
        raise ValueError("day 9-11 prowess/effective-stat sequence changed")
    old, new = stale["source_days"][0], refreshed["source_days"][0]
    if ((old["source_day"], new["source_day"]) != (11, 11)
            or old["residuals"] != [{"regiment_id": 220, "newly_joined": False,
                                     "predicted_minus_native_raw": 214}]
            or new["old_regiment_effective_toughness_changes"] != [
                {"regiment_id": 220, "control_toughness_raw": 7400000,
                 "pre_schedule_toughness_raw": 3700000}]
            or new["whole_side_current_exact"] is not True):
        raise ValueError("join-day residual and refresh evidence do not bind")
    return {
        "schema": "ck3-native-phase-event-regiment-feedback-v1",
        "game_version": case["game_version"],
        "combat_id": case["combat_id"],
        "trajectory": case["phase_trace_trajectory"],
        "case_sha256": EPISODE01_CASE_SHA256,
        "phase_event_sha256": EPISODE01_PHASE_EVENT_SHA256,
        "phase_event_save_sha256": EPISODE01_PHASE_EVENT_SAVE_SHA256,
        "join_kernel_initial_sha256": EPISODE01_JOIN_KERNEL_SHA256,
        "join_kernel_refreshed_sha256": EPISODE01_JOIN_KERNEL_V2_SHA256,
        "phase_receipt_sha256_by_source_day": receipt_hashes,
        "wound_event_source_day": 9,
        "wound_character_id": 54144,
        "wound_regiment_id": 220,
        "same_date_later_save_wounded_rank": 1,
        "stages": rows,
        "day_11_initial_conditional_residual_raw": 214,
        "day_11_refreshed_conditional_residual_raw": 0,
        "event_unique_cause_proven": False,
        "full_effect_write_set_proven": False,
        "source_day_11_whole_trace_available": False,
        "effective_stat_refresh_reconstructed": False,
        "planner_usable": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f"refusing to overwrite projection: {args.output}")
    report = project(args.trace_root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "sha256": sha(args.output),
                      "stages": len(report["stages"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
