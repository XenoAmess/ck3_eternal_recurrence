"""Bind an independent day-26 native kill event to its same-date CK3 saves.

The bounded phase trace is RED at the final paused query. This projector
retains the valid fire boundaries and verifies the two immutable saves without
claiming a full event write set or a calibrated battle forecast.
"""

from __future__ import annotations

import argparse
from decimal import Decimal
import hashlib
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

EXPECTED_EVENT = {
    "left_character_id": 33437,
    "right_character_id": 34120,
    "stable_key": "knight_killed_by_enemy",
    "type_raw": 3,
    "side_index": 1,
    "target_right": False,
}
RUN_SOURCE_SHA256 = "C1276153435766A875B0984F1A3AD426CB3AFCFB6EC33061CEE6650538CFFD2B"


def receipt(run: Path, name: str) -> tuple[dict, str]:
    path = run / "ck3-output/interactive-requests-responses" / name
    row = json.loads(path.read_text(encoding="utf-8"))
    if row.get("result") != "CALL_COMPLETED":
        raise ValueError(f"response not complete: {name}")
    return row["body"], digest(path)


def project(run: Path, rakaly_exe: Path) -> dict:
    run = run.resolve()
    if digest(rakaly_exe) != RAKALY_EXE_SHA256:
        raise ValueError("Rakaly executable bytes changed")
    paired = load_episode01_paired_counter_r14_parity()
    source_day = next(row for row in paired["days"] if row["day"] == 26)
    if source_day["checkpoint_sha256"].upper() != RUN_SOURCE_SHA256:
        raise ValueError("restored source checkpoint no longer matches paired report")
    copied = json.loads((run / "ck3-output/checkpoint-copy.json").read_text(encoding="utf-8"))
    if copied["source"]["save"]["sha256"] != RUN_SOURCE_SHA256 or copied["old_attempt_modified"]:
        raise ValueError("checkpoint copy provenance changed")
    before_body, before_receipt_sha = receipt(run, "002-before-save.json")
    after_body, after_receipt_sha = receipt(run, "008-after-save.json")
    finish_body, trace_receipt_sha = receipt(run, "007-finish.json")
    before_save = run / "d26-restored-before-immutable.ck3"
    after_save = run / "d27-postevent-immutable.ck3"
    if (digest(before_save) != before_body["checkpoint"]["sha256"].upper()
            or digest(before_save) != before_body["episode_seed"]["sha256"].upper()
            or digest(after_save) != after_body["checkpoint"]["sha256"].upper()
            or before_body["checkpoint"]["date_raw"] != 53146848
            or after_body["checkpoint"]["date_raw"] != 53146872):
        raise ValueError("immutable save receipt/date mismatch")
    trace = finish_body["managed_trace"]["trace"]
    records = trace["records"]
    if (finish_body["status"] != "trace_unavailable" or trace["failure_flags"] != 1040
            or len(records) != 7
            or [row["capture_failure_flags"] for row in records] != [0, 0, 0, 0, 0, 0, 16]
            or records[5]["battle_events"] != records[4]["battle_events"] + [EXPECTED_EVENT]):
        raise ValueError("native kill-event boundary signature changed")
    target_core = next(row for row in records[5]["characters"]
                       if row["character_id"] == EXPECTED_EVENT["left_character_id"])
    before_side = records[5]["sides"][1]
    final_side = records[6]["sides"][1]
    schedule_before = before_side["scheduled_knights"]
    schedule_after = final_side["scheduled_knights"]
    if (target_core["death_marker_present"]
            or target_core["current_regiment_id"] != 65
            or len(schedule_before) != 1 or len(schedule_after) != 1
            or schedule_before[0]["regiment_id"] != 65
            or schedule_before[0]["current_character_id"] != 33437
            or schedule_after[0]["regiment_id"] != 65
            or schedule_after[0]["current_character_id"] != 0
            or schedule_before[0]["event_identity_token"]
            != schedule_after[0]["event_identity_token"]
            or not any(row["regiment_id"] == 65 for row in before_side["knights"])
            or any(row["regiment_id"] == 65 for row in final_side["knights"])
            or records[6]["characters"] or records[6]["battle_events"]):
        raise ValueError("post-kill stale scheduled regiment signature changed")
    melted_files = (run / "d26-restored-before-melted.ck3",
                    run / "d27-postevent-melted.ck3")
    texts = [path.read_text(encoding="utf-8-sig") for path in melted_files]
    target = [_character_snapshot(text, 33437) for text in texts]
    opponent = [_character_snapshot(text, 34120) for text in texts]
    if (target[0]["trait_lookup_sha256"] != target[1]["trait_lookup_sha256"]
            or opponent[0]["trait_lookup_sha256"] != opponent[1]["trait_lookup_sha256"]
            or not target[0]["alive_data_present"]
            or not target[1]["dead_data_present"]
            or target[1]["death_date"] != "1066.12.30"
            or target[1]["death_reason"] != "death_battle"
            or target[1]["killer_character_id"] != 34120
            or target[0]["regiment_id"] != 65
            or target[1]["regiment_id"] is not None
            or not opponent[0]["alive_data_present"]
            or not opponent[1]["alive_data_present"]
            or opponent[0]["regiment_id"] != opponent[1]["regiment_id"]
            or opponent[0]["base_skill_values"] != opponent[1]["base_skill_values"]):
        raise ValueError("kill target/opponent save transition changed")
    prestige_currency = Decimal(opponent[1]["prestige_currency"]) - Decimal(opponent[0]["prestige_currency"])
    prestige_accumulated = Decimal(opponent[1]["prestige_accumulated"]) - Decimal(opponent[0]["prestige_accumulated"])
    if prestige_currency != Decimal("150") or prestige_accumulated != Decimal("150"):
        raise ValueError("opponent prestige transition changed")
    return {
        "schema": "xar.ck3.episode01.phase-event-kill-replay-feedback/v1",
        "game_build": "CK3 1.19.0.6",
        "capture_run": str(run),
        "restored_source_paired_report_sha256": EPISODE01_PAIRED_COUNTER_SHA256,
        "restored_source_save_sha256": RUN_SOURCE_SHA256,
        "rakaly_version": RAKALY_VERSION,
        "rakaly_exe_sha256": RAKALY_EXE_SHA256,
        "rakaly_command": "melt <immutable.ck3> --unknown-key stringify --format ck3 --out <melted.ck3>",
        "before_save_receipt_sha256": before_receipt_sha,
        "after_save_receipt_sha256": after_receipt_sha,
        "trace_response_sha256": trace_receipt_sha,
        "before_native_save_sha256": digest(before_save),
        "after_native_save_sha256": digest(after_save),
        "before_melted_save_sha256": digest(melted_files[0]),
        "after_melted_save_sha256": digest(melted_files[1]),
        "before_date_raw": 53146848,
        "after_date_raw": 53146872,
        "appended_event": EXPECTED_EVENT,
        "event_appended_between_boundaries": [4, 5],
        "target_core_at_last_valid_boundary": target_core,
        "target_regiment_id_before": 65,
        "target_regiment_present_in_final_side_knights": False,
        "stale_scheduled_regiment_id_at_final_query": 65,
        "target_before_and_after": target,
        "opponent_before_and_after": opponent,
        "opponent_prestige_currency_delta": str(prestige_currency),
        "opponent_prestige_accumulated_delta": str(prestige_accumulated),
        "opponent_base_prowess_delta": 0,
        "full_event_write_set_proven": False,
        "only_possible_cause_proven": False,
        "full_phase_trace_available": False,
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
