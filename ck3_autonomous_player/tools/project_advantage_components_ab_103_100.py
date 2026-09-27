#!/usr/bin/env python3
"""Read-only, hash-bound 103/100 same-checkpoint advantage observer A/B."""

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


TRACE_SHA = {
    "103": "0F40394F58FFFDC2C35FF812893729E83E1997700C4E964530446E6E90DBA938",
    "100": "644580703FE18769B081CCEBCC96B473BF459E4489835777117D6B070014FBFC",
}
EXE_SHA = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
SOURCE_SHA = "E6155C9C127EC3D1D758468653E8ABC3458A96B50EA053E303FDCCAD18C0B731"
SAVE_RECEIPT_SHA = "A68C4D38CC14B11FCB4078E8D9074C9EE5793B0EF20674199327E6D0A983B415"
COMBAT_ID = 16777218


def _load(path: Path, *, expected_sha: str | None = None) -> tuple[dict, str]:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest().upper()
    if expected_sha is not None and digest != expected_sha:
        raise ValueError(f"raw evidence SHA differs: {path}")
    return json.loads(raw), digest


def _path(root: Path, relative: str) -> Path:
    return root / relative


def project(attempt_103: Path, attempt_100: Path) -> dict[str, object]:
    attempts = {"103": attempt_103, "100": attempt_100}
    values = {}
    hashes = {}
    for number, root in attempts.items():
        trace_path = _path(root, f"ck3-output/interactive-requests-responses/c{number}-trace-finish.json")
        trace, hashes[f"trace_finish_{number}"] = _load(trace_path, expected_sha=TRACE_SHA[number])
        freeze, hashes[f"input_freeze_{number}"] = _load(_path(root, "input-freeze.json"))
        preflight, hashes[f"preflight_{number}"] = _load(_path(root, "ck3-output/preflight.json"))
        if (freeze["source"]["sha256"] != SOURCE_SHA
                or freeze["paired_receipt"]["sha256"] != SAVE_RECEIPT_SHA
                or freeze["combat_id"] != COMBAT_ID
                or freeze["start_date_raw"] != 53146512
                or preflight["game"]["sha256"] != EXE_SHA
                or preflight["checkpoint_source"]["save"]["sha256"] != SOURCE_SHA
                or preflight["checkpoint_source"]["receipt"]["sha256"] != SAVE_RECEIPT_SHA):
            raise ValueError(f"attempt {number} does not match pinned source/build")
        body = trace["body"]
        managed = body["managed_trace"]
        checkpoint = managed["managed_checkpoint"]
        native = managed["trace"]
        if (body["accepted"] is not True or body["combat_id"] != COMBAT_ID
                or native["status"] != "captured" or native["failure_flags"] != 0
                or native["record_count"] != 7 or len(native["records"]) != 7
                or not all(checkpoint[key] is True for key in (
                    "recoverable_checkpoint_created", "exact_one_day_observed",
                    "boundary_dates_match_checkpoint", "detours_uninstalled"))
                or checkpoint["before"]["date_raw"] != 53146512
                or checkpoint["after"]["date_raw"] != 53146536):
            raise ValueError(f"attempt {number} trace gates differ")
        values[number] = {"freeze": freeze, "preflight": preflight,
                          "body": body, "managed": managed, "native": native}

    old, new = values["100"], values["103"]
    if old["freeze"]["source"] != new["freeze"]["source"]:
        raise ValueError("A/B source checkpoint identity differs")
    same_fields = ("outgoing_damage", "post_counter_attack", "runtime_counter_output")
    for field in same_fields:
        if old["native"][field] != new["native"][field]:
            raise ValueError(f"A/B native {field} differs")
    if old["native"]["runtime_counter_output"]["pair_complete"] is not True:
        raise ValueError("A/B counter pair is incomplete")
    if normalize_runtime_advantage_components_v1(old["managed"], combat_id=COMBAT_ID) is not None:
        raise ValueError("100 unexpectedly has optional advantage diagnostic")
    diagnostic = normalize_runtime_advantage_components_v1(new["managed"], combat_id=COMBAT_ID)
    if not isinstance(diagnostic, dict):
        raise ValueError("103 advantage diagnostic missing")
    rows = diagnostic["materializations"]
    if (diagnostic["available"] is not False
            or diagnostic["failure_flags"] != 64
            or diagnostic["diagnostic_observation_complete"] is not False
            or diagnostic["forecast_usable"] is not False
            or len(rows) != 1 or rows[0]["complete"] is not True):
        raise ValueError("103 diagnostic availability/gates differ")
    row = rows[0]
    if (row["base_raw"], row["resolved_raw"],
            [side["roll"] for side in row["sides"]]) != (
                -300000, -1100000, [7, 8]):
        raise ValueError("103 diagnostic row numbers differ")
    for number in ("100", "103"):
        first = values[number]["native"]["records"][0]
        if (first["base_advantage_raw"] != row["base_raw"]
                or first["resolved_advantage_raw"] != row["resolved_raw"]
                or first["advantage_rolls_raw"] != [7, 8]):
            raise ValueError(f"attempt {number} cache/diagnostic mismatch")

    freeze_provenance_green = (new["freeze"]["exe_sha256"] == EXE_SHA
                               and old["freeze"]["exe_sha256"] == EXE_SHA)
    return {
        "schema": "ck3.advantage_components_same_checkpoint_ab_103_100.v1",
        "game_build": "1.19.0.6-steam23530548",
        "exe_sha256_preflight": EXE_SHA,
        "source_save_sha256": SOURCE_SHA,
        "source_save_receipt_sha256": SAVE_RECEIPT_SHA,
        "evidence_sha256": hashes,
        "input_freeze_103_exe_typo": {
            "recorded": new["freeze"]["exe_sha256"],
            "matches_measured_preflight": new["freeze"]["exe_sha256"] == EXE_SHA,
        },
        "gates": {
            "raw_ab_comparison": "GREEN",
            "freeze_manifest_provenance": "GREEN" if freeze_provenance_green else "RED",
            "overall": "GREEN" if freeze_provenance_green else "RED",
        },
        "comparison": {
            "combat_id": COMBAT_ID,
            "before_date_raw": 53146512,
            "after_date_raw": 53146536,
            "native_trace_failure_flags_both": 0,
            "counter_pair_equal": True,
            "post_counter_attack_equal": True,
            "outgoing_damage_equal": True,
            "runtime_counter_output": new["native"]["runtime_counter_output"],
            "post_counter_attack": new["native"]["post_counter_attack"],
            "outgoing_damage": new["native"]["outgoing_damage"],
        },
        "advantage_103": {
            "available": diagnostic["available"],
            "failure_flags": diagnostic["failure_flags"],
            "diagnostic_observation_complete": diagnostic["diagnostic_observation_complete"],
            "forecast_usable": diagnostic["forecast_usable"],
            "row": row,
        },
        "conclusion": "same_source_existing_outputs_reproduced; advantage_diagnostic_unavailable_not_live_validated",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-103", required=True, type=Path)
    parser.add_argument("--attempt-100", required=True, type=Path)
    parser.add_argument("--expected", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true",
                        help="require all gates GREEN (103 is expected RED)")
    args = parser.parse_args()
    result = project(args.attempt_103, args.attempt_100)
    body = (json.dumps(result,
                       ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if args.expected is not None and args.expected.read_bytes() != body:
        raise ValueError("frozen A/B projection differs")
    if args.output is None:
        print(body.decode("utf-8"), end="")
    else:
        with args.output.open("xb") as file:
            file.write(body)
    if args.check and result["gates"]["overall"] != "GREEN":
        raise SystemExit("overall provenance gate RED; see frozen A/B projection")


if __name__ == "__main__":
    main()
