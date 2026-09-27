#!/usr/bin/env python3
"""Hash-bound, read-only comparison of the 104 advantage observer and 100 control."""

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
SAVE_SHA = "E6155C9C127EC3D1D758468653E8ABC3458A96B50EA053E303FDCCAD18C0B731"
RECEIPT_SHA = "A68C4D38CC14B11FCB4078E8D9074C9EE5793B0EF20674199327E6D0A983B415"
COMBAT_ID = 16777218
FROZEN = {
    "100": {
        "input-freeze.json": "7FB661DC36CF67733F17E447B53B8CDC0E99A4682FA2025792C23EB598338C81",
        "ck3-output/preflight.json": "43ECB33997C889D901D0009A1ADAA227CB090A8BD2C127D2FC2F22D3D7EB9BE9",
        "ck3-output/interactive-requests-responses/c100-trace-finish.json": "644580703FE18769B081CCEBCC96B473BF459E4489835777117D6B070014FBFC",
    },
    "104": {
        "input-freeze.json": "855D2F8A763547C1054AA2FCCD167FB3652C351FAD8E6770BA3148066D75F3F4",
        "ck3-output/preflight.json": "AA46C402FFD96D013FB48AF7B087150FB4401EDB234EBC46BCDB1ED6B5DB8512",
        "ck3-output/interactive-requests-responses/c104-trace-finish.json": "B92CF0978C4B5954704ADACE63C4DC5B3936396F491DA3872163BE7F4BA02A68",
        "ck3-output/session-result.json": "72571438CC5AC209B15AD3B0009089C29537B50B3DE815DD87C7ED372B003FFD",
        "ck3-output/capture-report.json": "82F9ED3F1ACB5F939F3DA17C3ED734C1B21AFE7957C276189F4D7D71EB5697C1",
        "cleanup-check.json": "1441CB38DED1A95F57ADD0A213571E11493113D2AD488CAA969B30AEF12DF5D3",
    },
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


def _attempt(root: Path, number: str) -> dict:
    files = {name: _load(root, name, sha) for name, sha in FROZEN[number].items()}
    freeze = files["input-freeze.json"]
    preflight = files["ck3-output/preflight.json"]
    trace = files[f"ck3-output/interactive-requests-responses/c{number}-trace-finish.json"]
    if (freeze["source"]["sha256"] != SAVE_SHA
            or freeze["paired_receipt"]["sha256"] != RECEIPT_SHA
            or freeze["exe_sha256"] != EXE_SHA
            or freeze["combat_id"] != COMBAT_ID
            or freeze["start_date_raw"] != 53146512
            or preflight["game"]["sha256"] != EXE_SHA
            or preflight["checkpoint_source"]["save"]["sha256"] != SAVE_SHA
            or preflight["checkpoint_source"]["receipt"]["sha256"] != RECEIPT_SHA
            or preflight["bridge_dll"]["sha256"] != freeze["bridge"]["sha256"]):
        raise ValueError(f"attempt {number}: source, executable or DLL identity differs")
    body = trace["body"]
    managed = body["managed_trace"]
    native = managed["trace"]
    checkpoint = managed["managed_checkpoint"]
    if (trace["result"] != "CALL_COMPLETED" or body["accepted"] is not True
            or body["combat_id"] != COMBAT_ID or native["status"] != "captured"
            or native["failure_flags"] != 0 or native["record_count"] != 7
            or len(native["records"]) != 7
            or not all(checkpoint[key] is True for key in (
                "recoverable_checkpoint_created", "exact_one_day_observed",
                "boundary_dates_match_checkpoint", "detours_uninstalled"))
            or checkpoint["before"]["date_raw"] != 53146512
            or checkpoint["after"]["date_raw"] != 53146536):
        raise ValueError(f"attempt {number}: managed one-day trace is incomplete")
    return {"files": files, "freeze": freeze, "preflight": preflight,
            "managed": managed, "native": native}


def project(attempt_104: Path, attempt_100: Path) -> dict:
    control = _attempt(attempt_100, "100")
    candidate = _attempt(attempt_104, "104")
    if control["freeze"]["source"] != candidate["freeze"]["source"]:
        raise ValueError("A/B source checkpoint differs")
    for field in ("runtime_counter_output", "post_counter_attack", "outgoing_damage"):
        if control["native"][field] != candidate["native"][field]:
            raise ValueError(f"A/B {field} differs")
    if control["native"]["runtime_counter_output"]["pair_complete"] is not True:
        raise ValueError("A/B counter output is incomplete")
    if normalize_runtime_advantage_components_v1(
            control["managed"], combat_id=COMBAT_ID) is not None:
        raise ValueError("100 unexpectedly contains advantage diagnostics")
    diagnostic = normalize_runtime_advantage_components_v1(
        candidate["managed"], combat_id=COMBAT_ID)
    if (not isinstance(diagnostic, dict) or diagnostic["available"] is not True
            or diagnostic["failure_flags"] != 0
            or diagnostic["diagnostic_observation_complete"] is not True
            or diagnostic["forecast_usable"] is not False
            or len(diagnostic["materializations"]) != 1):
        raise ValueError("104 advantage diagnostic is not complete")
    row = diagnostic["materializations"][0]
    if (row["complete"] is not True or row["base_raw"] != -300000
            or row["resolved_raw"] != -1100000
            or [side["roll"] for side in row["sides"]] != [7, 8]
            or [side["nested_aggregator_calls"] for side in row["sides"]] != [1, 1]
            or [side["primary_aggregator_calls"] for side in row["sides"]] != [1, 1]
            or diagnostic["first_aggregator_failure"]["gate"] != 0):
        raise ValueError("104 complete advantage row differs")
    for number, result in (("100", control), ("104", candidate)):
        first = result["native"]["records"][0]
        if (first["base_advantage_raw"] != row["base_raw"]
                or first["resolved_advantage_raw"] != row["resolved_raw"]
                or first["advantage_rolls_raw"] != [7, 8]):
            raise ValueError(f"{number} cached advantage differs")
    cleanup = candidate["files"]["cleanup-check.json"]
    if (cleanup["capture_returncode"] != 0 or cleanup["cleanup_ok"] is not True
            or cleanup["shutdown"]["cleanup_proven"] is not True
            or cleanup["shutdown"]["job_active_processes_final"] != 0
            or cleanup["session_result_sha256"] != FROZEN["104"]["ck3-output/session-result.json"]
            or cleanup["capture_report_sha256"] != FROZEN["104"]["ck3-output/capture-report.json"]):
        raise ValueError("104 clean exit differs")
    return {
        "schema": "ck3.advantage_components_same_checkpoint_ab_104_100.v1",
        "source_save_sha256": SAVE_SHA,
        "source_save_receipt_sha256": RECEIPT_SHA,
        "exe_sha256": EXE_SHA,
        "evidence_sha256": FROZEN,
        "gates": {"same_source": "GREEN", "freeze_manifest_provenance": "GREEN",
                  "raw_ab_comparison": "GREEN", "advantage_diagnostic": "GREEN",
                  "clean_exit": "GREEN", "overall": "GREEN"},
        "comparison": {
            "combat_id": COMBAT_ID,
            "before_date_raw": 53146512,
            "after_date_raw": 53146536,
            "counter_pair_equal": True,
            "post_counter_attack_equal": True,
            "outgoing_damage_equal": True,
            "runtime_counter_output": candidate["native"]["runtime_counter_output"],
            "post_counter_attack": candidate["native"]["post_counter_attack"],
            "outgoing_damage": candidate["native"]["outgoing_damage"],
        },
        "advantage_104": diagnostic,
        "conclusion": "same_source_single_day_observer_complete_retrospective_only",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-104", required=True, type=Path)
    parser.add_argument("--attempt-100", required=True, type=Path)
    parser.add_argument("--expected", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = project(args.attempt_104, args.attempt_100)
    raw = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if args.expected is not None and args.expected.read_bytes() != raw:
        raise ValueError("frozen 104/100 projection differs")
    if args.output is None:
        print(raw.decode("utf-8"), end="")
    else:
        with args.output.open("xb") as stream:
            stream.write(raw)
    if args.check and result["gates"]["overall"] != "GREEN":
        raise SystemExit("104/100 overall gate RED")


if __name__ == "__main__":
    main()
