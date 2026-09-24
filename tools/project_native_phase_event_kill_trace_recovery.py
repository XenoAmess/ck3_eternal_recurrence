"""Bind a repaired seven-boundary day-26 native trace to its same-day saves.

This is a capture-fidelity observation, not a complete effect write set or a
whole-battle forecast. The source run remains immutable outside the repo.
"""

from __future__ import annotations

import argparse
from decimal import Decimal
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "ck3_autonomous_player/src"))
sys.path.insert(0, str(REPO / "ck3_autonomous_player/tools"))
from xar_autoplayer.simulation.native_battle_case import (  # noqa: E402
    EPISODE01_PAIRED_COUNTER_SHA256,
    load_episode01_paired_counter_r14_parity,
)
from project_native_phase_event_save_feedback import (  # noqa: E402
    RAKALY_EXE_SHA256,
    RAKALY_VERSION,
    _character_snapshot,
    digest,
)

SOURCE_CHECKPOINT_SHA256 = "C1276153435766A875B0984F1A3AD426CB3AFCFB6EC33061CEE6650538CFFD2B"
EVENT = {
    "left_character_id": 33437,
    "right_character_id": 34120,
    "stable_key": "knight_killed_by_enemy",
    "type_raw": 3,
    "side_index": 1,
    "target_right": False,
}


def _receipt(run: Path, stem: str) -> tuple[dict, str]:
    path = run / "ck3-output/interactive-requests-responses" / f"{stem}.json"
    row = json.loads(path.read_text(encoding="utf-8"))
    if row.get("result") != "CALL_COMPLETED":
        raise ValueError(f"response incomplete: {stem}")
    return row["body"], digest(path)


def _character(record: dict, character_id: int) -> dict:
    return next(row for row in record["characters"] if row["character_id"] == character_id)


def project(run: Path, rakaly_exe: Path) -> dict:
    run = run.resolve()
    if digest(rakaly_exe) != RAKALY_EXE_SHA256:
        raise ValueError("Rakaly executable bytes changed")
    source_day = next(row for row in load_episode01_paired_counter_r14_parity()["days"]
                      if row["day"] == 26)
    if source_day["checkpoint_sha256"].upper() != SOURCE_CHECKPOINT_SHA256:
        raise ValueError("paired case source checkpoint changed")
    copied = json.loads((run / "ck3-output/checkpoint-copy.json").read_text(encoding="utf-8"))
    if copied["source"]["save"]["sha256"] != SOURCE_CHECKPOINT_SHA256 or copied["old_attempt_modified"]:
        raise ValueError("source copy provenance changed")

    before, before_receipt_sha = _receipt(run, "002-before-save")
    v3, v3_receipt_sha = _receipt(run, "004-v3")
    finish, trace_receipt_sha = _receipt(run, "007-finish")
    after, after_receipt_sha = _receipt(run, "008-after-save")
    before_save = run / "d26-restored-before-immutable.ck3"
    after_save = run / "d27-postevent-immutable.ck3"
    if (digest(before_save) != before["checkpoint"]["sha256"].upper()
            or digest(before_save) != before["episode_seed"]["sha256"].upper()
            or digest(after_save) != after["checkpoint"]["sha256"].upper()
            or before["checkpoint"]["date_raw"] != 53146848
            or after["checkpoint"]["date_raw"] != 53146872):
        raise ValueError("same-day immutable save identity changed")

    trace = finish["managed_trace"]["trace"]
    records = trace["records"]
    if (finish["status"] != "bounded_trace_available"
            or trace["failure_flags"] != 0 or len(records) != 7
            or [row["capture_failure_flags"] for row in records] != [0] * 7
            or trace["readiness"]["bounded_capture_complete"] is not True
            or trace["readiness"]["full_mutable_transition_bundle_complete"] is not False
            or trace["readiness"]["original_trace_ready"] is not False
            or records[5]["battle_events"] != records[4]["battle_events"] + [EVENT]
            or records[6]["battle_events"] != records[5]["battle_events"]):
        raise ValueError("repaired seven-boundary native signature changed")

    before_core = _character(records[5], 33437)
    final_core = _character(records[6], 33437)
    side_before = records[5]["sides"][1]
    side_after = records[6]["sides"][1]
    schedule_before = side_before["scheduled_knights"]
    schedule_after = side_after["scheduled_knights"]
    if (before_core["death_marker_present"] is not False
            or before_core["current_regiment_id"] != 65
            or before_core["prowess"] != 4
            or final_core["death_marker_present"] is not True
            or final_core["current_regiment_id"] != 0
            or final_core["prowess"] != 2
            or len(schedule_before) != 1 or len(schedule_after) != 1
            or schedule_before[0]["regiment_id"] != 65
            or schedule_before[0]["current_character_id"] != 33437
            or schedule_after[0]["regiment_id"] != 65
            or schedule_after[0]["current_character_id"] != -1
            or schedule_before[0]["event_identity_token"] != schedule_after[0]["event_identity_token"]
            or not any(row["regiment_id"] == 65 for row in side_before["knights"])
            or any(row["regiment_id"] == 65 for row in side_after["knights"])
            or any(row["regiment_id"] == 65 for row in side_after["regiments"])):
        raise ValueError("death, detachment, or stale schedule signature changed")

    melted = [run / "d26-restored-before-melted.ck3", run / "d27-postevent-melted.ck3"]
    texts = [path.read_text(encoding="utf-8-sig") for path in melted]
    target = [_character_snapshot(text, 33437) for text in texts]
    killer = [_character_snapshot(text, 34120) for text in texts]
    if (not target[0]["alive_data_present"] or not target[1]["dead_data_present"]
            or target[1]["death_reason"] != "death_battle"
            or target[1]["killer_character_id"] != 34120
            or target[0]["regiment_id"] != 65 or target[1]["regiment_id"] is not None
            or killer[0]["base_skill_values"] != killer[1]["base_skill_values"]):
        raise ValueError("same-day save transition changed")
    prestige_currency = Decimal(killer[1]["prestige_currency"]) - Decimal(killer[0]["prestige_currency"])
    prestige_accumulated = Decimal(killer[1]["prestige_accumulated"]) - Decimal(killer[0]["prestige_accumulated"])
    if prestige_currency != Decimal("150") or prestige_accumulated != Decimal("150"):
        raise ValueError("killer prestige delta changed")

    phase_inputs = v3["combat_simulation_inputs"]["phase_event_inputs"]
    if (v3["status"] != "unavailable" or phase_inputs["status"] != "unavailable"
            or phase_inputs["unavailable_reason"] !=
            "native_phase_definition_context_culture_parameter_unavailable:knights_slightly_more_prone_to_injury"):
        raise ValueError("concurrent v3 input gap changed")
    return {
        "schema": "xar.ck3.episode01.phase-event-kill-trace-recovery/v1",
        "game_build": "CK3 1.19.0.6",
        "capture_run": str(run),
        "restored_source_paired_report_sha256": EPISODE01_PAIRED_COUNTER_SHA256,
        "restored_source_save_sha256": SOURCE_CHECKPOINT_SHA256,
        "rakaly_version": RAKALY_VERSION,
        "rakaly_exe_sha256": RAKALY_EXE_SHA256,
        "before_save_receipt_sha256": before_receipt_sha,
        "v3_response_sha256": v3_receipt_sha,
        "trace_response_sha256": trace_receipt_sha,
        "after_save_receipt_sha256": after_receipt_sha,
        "before_native_save_sha256": digest(before_save),
        "after_native_save_sha256": digest(after_save),
        "before_melted_save_sha256": digest(melted[0]),
        "after_melted_save_sha256": digest(melted[1]),
        "before_date_raw": 53146848,
        "after_date_raw": 53146872,
        "trace_status": finish["status"],
        "boundary_count": len(records),
        "boundary_capture_failure_flags": [row["capture_failure_flags"] for row in records],
        "trace_failure_flags": trace["failure_flags"],
        "appended_event": EVENT,
        "event_appended_between_boundaries": [4, 5],
        "target_core_before_final_query": before_core,
        "target_core_at_final_query": final_core,
        "scheduled_knight_before_final_query": schedule_before[0],
        "scheduled_knight_at_final_query": schedule_after[0],
        "target_regiment_present_before_final_query": True,
        "target_regiment_present_at_final_query": False,
        "target_before_and_after_save": target,
        "killer_before_and_after_save": killer,
        "killer_prestige_currency_delta": str(prestige_currency),
        "killer_prestige_accumulated_delta": str(prestige_accumulated),
        "v3_phase_event_input_status": phase_inputs["status"],
        "v3_phase_event_input_unavailable_reason": phase_inputs["unavailable_reason"],
        "seven_boundary_capture_available": True,
        "full_mutable_transition_bundle_complete": False,
        "full_event_write_set_proven": False,
        "only_possible_cause_proven": False,
        "whole_battle_win_probability_available": False,
        "planner_usable": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--rakaly-exe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = project(args.run, args.rakaly_exe)
    with args.output.open("x", encoding="utf-8", newline="\n") as out:
        json.dump(report, out, ensure_ascii=False, indent=2)
        out.write("\n")
    print(json.dumps({"output": str(args.output), "sha256": digest(args.output)}))


if __name__ == "__main__":
    main()
