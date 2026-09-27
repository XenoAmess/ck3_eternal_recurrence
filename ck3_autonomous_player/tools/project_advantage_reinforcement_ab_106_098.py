#!/usr/bin/env python3
"""Hash-bound, read-only comparison of the 106 reinforcement trace and 098 control."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from xar_autoplayer.bridge.combat_advantage_components_contract import (  # noqa: E402
    normalize_runtime_advantage_components_v1,
)


EXE_SHA = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
SAVE_SHA = "3F4B2FDAAE1AA2ED4D94958673DDADF4DCDF4A4F49073594B9AE32E782BB6953"
RECEIPT_SHA = "DD986180C7E9C4B42D43FC634884F5294387D18CF8F798012FAD621B37E9E4A5"
COMBAT_ID = 16777218
FROZEN = {
    "098": {
        "input-freeze.json": "DD0C346F046DB059C56B880A2F9C31686B83C3D5A104934DBB7AEF7D13B64C5C",
        "ck3-output/preflight.json": "3886CC56B2B96A7BC3F5B39DA771DC2CB887702882FBBA887F7F34C5C97B114D",
        "ck3-output/interactive-requests-responses/c098-trace-finish.json": "6B158A07A6071D058DE6F3E8994CA0065F09B2311EF79004EB1DDD445B1B8198",
    },
    "106": {
        "input-freeze.json": "8680F5432705E2DE89755D23265279F0CAD7AB89086C621E2215DC7D006FF8D3",
        "ck3-output/preflight.json": "FEB288712C9C608F705628B5F6FB4D18C02129664278E43989D669AC71647C6D",
        "ck3-output/interactive-requests-responses/c106-trace-finish.json": "9DF1DB4763A9CC74FCB66751A8D8353A9427D555247C12F474D0BD6D8A31B24A",
        "ck3-output/session-result.json": "6F720AF9BAD96F38B45CC379E64757C5EAE4C98278481C7BAC8BDD395AF9E025",
        "ck3-output/capture-report.json": "915CAEA1139905B5EC304C496D7EB861A93F8153E258AE6A31D29A4214B82400",
        "cleanup-check.json": "1B3FC992333B003DDA1F7DC1FD418172BA2A32FA68BCF6D43344EBB1F959E1C5",
    },
}
PROCESS_LOCAL_KEYS = {
    "thread_id", "owner_thread_token", "managed_daily_sequence_token",
    "scheduled_commander_event_identity_token",
}


def _load(root: Path, relative: str, expected_sha: str) -> dict:
    raw = (root / relative).read_bytes()
    actual = hashlib.sha256(raw).hexdigest().upper()
    if actual != expected_sha:
        raise ValueError(f"{relative}: expected {expected_sha}, got {actual}")
    result = json.loads(raw)
    if not isinstance(result, dict):
        raise ValueError(f"{relative}: expected object")
    return result


def _stable(value: object) -> object:
    if isinstance(value, dict):
        return {key: _stable(item) for key, item in value.items()
                if key not in PROCESS_LOCAL_KEYS}
    if isinstance(value, list):
        return [_stable(item) for item in value]
    return value


def _attempt(root: Path, number: str) -> dict:
    files = {name: _load(root, name, sha) for name, sha in FROZEN[number].items()}
    freeze = files["input-freeze.json"]
    preflight = files["ck3-output/preflight.json"]
    finish = files[f"ck3-output/interactive-requests-responses/c{number}-trace-finish.json"]
    if (freeze["source"]["sha256"] != SAVE_SHA
            or freeze["paired_receipt"]["sha256"] != RECEIPT_SHA
            or freeze["exe_sha256"] != EXE_SHA
            or freeze["combat_id"] != COMBAT_ID
            or freeze["start_date_raw"] != 53146488
            or preflight["game"]["sha256"] != EXE_SHA
            or preflight["checkpoint_source"]["save"]["sha256"] != SAVE_SHA
            or preflight["checkpoint_source"]["receipt"]["sha256"] != RECEIPT_SHA
            or preflight["bridge_dll"]["sha256"] != freeze["bridge"]["sha256"]):
        raise ValueError(f"attempt {number}: source, executable or DLL identity differs")
    managed = finish["body"]["managed_trace"]
    native = managed["trace"]
    checkpoint = managed["managed_checkpoint"]
    if (finish["result"] != "CALL_COMPLETED"
            or finish["body"]["accepted"] is not True
            or finish["body"]["combat_id"] != COMBAT_ID
            or native["status"] != "captured" or native["failure_flags"] != 0
            or native["record_count"] != 7 or len(native["records"]) != 7
            or any(row["capture_failure_flags"] != 0 for row in native["records"])
            or not all(native["readiness"][key] is True for key in (
                "exact_boundary_sequence", "same_full_generation_combat",
                "expected_one_day_date_split", "side_and_return_site_identity",
                "bounded_capture_complete", "runtime_counter_output_pair_complete"))
            or not all(checkpoint[key] is True for key in (
                "recoverable_checkpoint_created", "exact_one_day_observed",
                "boundary_dates_match_checkpoint", "detours_uninstalled"))
            or checkpoint["before"]["date_raw"] != 53146488
            or checkpoint["after"]["date_raw"] != 53146512):
        raise ValueError(f"attempt {number}: managed one-day trace incomplete")
    if (native["runtime_join_width"]["status"] != "captured"
            or native["runtime_join_width"]["count"] != 3
            or native["runtime_join_full_entries"]["status"] != "captured"
            or native["runtime_join_full_entries"]["count"] != 2
            or native["runtime_counter_output"]["pair_complete"] is not True):
        raise ValueError(f"attempt {number}: reinforcement or counter capture incomplete")
    return {"files": files, "freeze": freeze, "native": native, "managed": managed}


def project(attempt_106: Path, attempt_098: Path) -> dict:
    control = _attempt(attempt_098, "098")
    candidate = _attempt(attempt_106, "106")
    if control["freeze"]["source"]["sha256"] != candidate["freeze"]["source"]["sha256"]:
        raise ValueError("A/B checkpoint differs")
    for field in ("records", "runtime_join_width", "runtime_join_full_entries",
                  "runtime_counter_output", "post_counter_attack", "outgoing_damage"):
        if _stable(control["native"][field]) != _stable(candidate["native"][field]):
            raise ValueError(f"A/B {field} differs beyond process-local identities")
    if normalize_runtime_advantage_components_v1(
            control["managed"], combat_id=COMBAT_ID) is not None:
        raise ValueError("098 unexpectedly has advantage diagnostic")
    diagnostic = normalize_runtime_advantage_components_v1(
        candidate["managed"], combat_id=COMBAT_ID)
    if (not isinstance(diagnostic, dict) or diagnostic["available"] is not True
            or diagnostic["failure_flags"] != 0
            or diagnostic["diagnostic_observation_complete"] is not True
            or diagnostic["forecast_usable"] is not False
            or len(diagnostic["materializations"]) != 1):
        raise ValueError("106 advantage diagnostic incomplete")
    row = diagnostic["materializations"][0]
    if (row["complete"] is not True or row["date_raw"] != 53146488
            or row["base_raw"] != -300000 or row["resolved_raw"] != -1100000
            or [side["commander_character_id"] for side in row["sides"]] != [34320, 29829]
            or [side["roll"] for side in row["sides"]] != [7, 8]
            or [side["total_raw"] for side in row["sides"]] != [4200000, 5000000]):
        raise ValueError("106 advantage row differs")
    width = candidate["native"]["runtime_join_width"]["boundaries"]
    full = candidate["native"]["runtime_join_full_entries"]["boundaries"]
    if ([item["army_id"] for item in width] != [22, 22, 22]
            or [item["base_width"] for item in width] != [1645, 2467, 2467]
            or [item["final_width"] for item in width] != [1480, 2220, 2220]
            or [item["joined_side_index"] for item in full] != [-1, 0]
            or [len(item["sides"][0]["entries"]) for item in full] != [27, 40]
            or [len(item["incoming_regiments"]) for item in full] != [13, 13]):
        raise ValueError("106 incoming Army 22 transition differs")
    cleanup = candidate["files"]["cleanup-check.json"]
    if (cleanup["capture_returncode"] != 0 or cleanup["cleanup_ok"] is not True
            or cleanup["shutdown"]["cleanup_proven"] is not True
            or cleanup["shutdown"]["job_active_processes_final"] != 0
            or cleanup["session_result_sha256"] != FROZEN["106"]["ck3-output/session-result.json"]
            or cleanup["capture_report_sha256"] != FROZEN["106"]["ck3-output/capture-report.json"]):
        raise ValueError("106 clean exit differs")
    return {
        "schema": "ck3.advantage_reinforcement_same_checkpoint_ab_106_098.v1",
        "source_save_sha256": SAVE_SHA,
        "source_save_receipt_sha256": RECEIPT_SHA,
        "exe_sha256": EXE_SHA,
        "evidence_sha256": FROZEN,
        "gates": {"same_source": "GREEN", "full_trace_semantic_parity": "GREEN",
                  "incoming_army_22": "GREEN", "native_output_parity": "GREEN",
                  "advantage_diagnostic": "GREEN", "clean_exit": "GREEN",
                  "overall": "GREEN"},
        "comparison": {
            "combat_id": COMBAT_ID,
            "before_date_raw": 53146488,
            "after_date_raw": 53146512,
            "record_count": 7,
            "join_width": [{key: item[key] for key in (
                "army_id", "side_index", "phase_day", "base_width", "final_width")}
                           for item in width],
            "join_full_side0_entry_counts": [len(item["sides"][0]["entries"]) for item in full],
            "counter_side_retention_raw": [side["retention_raw"] for side in
                                           candidate["native"]["runtime_counter_output"]["sides"]],
            "post_counter_attack": candidate["native"]["post_counter_attack"],
            "outgoing_damage": candidate["native"]["outgoing_damage"],
        },
        "advantage_106": diagnostic,
        "conclusion": "same_source_reinforcement_day_observer_complete_retrospective_only",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-106", required=True, type=Path)
    parser.add_argument("--attempt-098", required=True, type=Path)
    parser.add_argument("--expected", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = project(args.attempt_106, args.attempt_098)
    raw = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if args.expected is not None and args.expected.read_bytes() != raw:
        raise ValueError("frozen 106/098 projection differs")
    if args.output is None:
        print(raw.decode("utf-8"), end="")
    else:
        with args.output.open("xb") as stream:
            stream.write(raw)
    if args.check and result["gates"]["overall"] != "GREEN":
        raise SystemExit("106/098 overall gate RED")


if __name__ == "__main__":
    main()
