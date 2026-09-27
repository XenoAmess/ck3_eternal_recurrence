"""Project attempt 083's three same-combat native join-width boundaries.

The original managed response and clean-exit receipt are immutable inputs.
This tool never attaches to or mutates CK3.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


FINISH_SHA256 = "4342DBBECF58C8DA38A34B525BE930510442BF734738FDD720B123BC0D01B247"
CLEANUP_SHA256 = "3D58E471CB43C648004E3452E26A14E386DB646480155C82B4AAE2E1D126FABF"
EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
BRIDGE_SHA256 = "8DC462F92BA1FBF7066FC9C87601651DAB34626FDF5D9289A5839CB7ED821109"
SAVE_SHA256 = "3F4B2FDAAE1AA2ED4D94958673DDADF4DCDF4A4F49073594B9AE32E782BB6953"


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def project(finish_raw: bytes, cleanup_raw: bytes) -> dict[str, object]:
    if _sha(finish_raw) != FINISH_SHA256 or _sha(cleanup_raw) != CLEANUP_SHA256:
        raise ValueError("083 source bytes changed")
    response = json.loads(finish_raw)
    cleanup = json.loads(cleanup_raw)
    if response.get("result") != "CALL_COMPLETED":
        raise ValueError("083 native finish did not complete")
    body = response["body"]
    managed = body["managed_trace"]
    checkpoint = managed["managed_checkpoint"]
    trace = managed["trace"]
    width = trace["runtime_join_width"]
    if (
        body["combat_id"] != 16777218
        or body["status"] != "bounded_trace_available"
        or body["production_trace_ready"] is not False
        or checkpoint["before"]["date_raw"] != 53146488
        or checkpoint["after"]["date_raw"] != 53146512
        or checkpoint["exact_one_day_observed"] is not True
        or checkpoint["boundary_dates_match_checkpoint"] is not True
        or checkpoint["detours_uninstalled"] is not True
        or trace["status"] != "captured"
        or trace["failure_flags"] != 0
        or width["status"] != "captured"
        or width["count"] != 3
        or width["first_failure_code"] != 0
        or cleanup["capture_returncode"] != 0
        or cleanup["cleanup_ok"] is not True
    ):
        raise ValueError("083 complete-capture contract changed")
    rows = width["boundaries"]
    if len(rows) != 3:
        raise ValueError("083 requires all three raw boundaries")
    before, after, fire = rows
    for index, row in enumerate(rows):
        if (
            row["boundary"] != index
            or row["combat_id"] != 16777218
            or row["army_id"] != 22
            or row["native_date_raw"] != 53146512
            or len(row["side_fighting_total_raw"]) != 2
        ):
            raise ValueError("083 join/fire identity changed")
    if (
        (before["side_index"], after["side_index"], fire["side_index"])
        != (-1, 0, 0)
        or (before["phase_day"], after["phase_day"], fire["phase_day"])
        != (7, 7, 8)
        or len({row["thread_id"] for row in rows}) != 1
        or before["thread_id"] == checkpoint["before"]["thread_id"]
        or before["outgoing_width_argument"] != -1
        or after["outgoing_width_argument"] != -1
        or fire["outgoing_width_argument"] != after["final_width"]
        or fire["base_width"] != after["base_width"]
        or fire["final_width"] != after["final_width"]
        or fire["side_fighting_total_raw"] != after["side_fighting_total_raw"]
    ):
        raise ValueError("083 width production/consumption boundary changed")

    def boundary(row: dict[str, object]) -> dict[str, object]:
        totals = row["side_fighting_total_raw"]
        return {
            "boundary": row["boundary"],
            "thread_id": row["thread_id"],
            "phase_day": row["phase_day"],
            "side_index": row["side_index"],
            "base_width": row["base_width"],
            "final_width": row["final_width"],
            "outgoing_width_argument": row["outgoing_width_argument"],
            "side_fighting_total_raw": totals,
            "candidate_half_total_truncated": sum(totals) // 200000,
        }

    return {
        "schema": "ck3.native_join_width_three_boundary_observation.v1",
        "source": {
            "attempt": 83,
            "finish_response_name": "jwidth083-finish.json",
            "finish_sha256": FINISH_SHA256,
            "cleanup_sha256": CLEANUP_SHA256,
            "exe_sha256": EXE_SHA256,
            "bridge_sha256": BRIDGE_SHA256,
            "save_sha256": SAVE_SHA256,
        },
        "collector_status": "captured",
        "collector_failure_flags": 0,
        "first_failure_code": 0,
        "combat_id": 16777218,
        "native_date_raw": 53146512,
        "candidate_joining_army_id": 22,
        "mailbox_thread_id": checkpoint["before"]["thread_id"],
        "join_and_fire_thread_id": before["thread_id"],
        "fighting_total_scale": 100000,
        "boundaries": [boundary(row) for row in rows],
        "observed_delta": {
            "base_width": after["base_width"] - before["base_width"],
            "final_width": after["final_width"] - before["final_width"],
        },
        "three_boundary_complete": True,
        "fire_width": fire["outgoing_width_argument"],
        "clean_exit": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--finish", type=Path, required=True)
    parser.add_argument("--cleanup", type=Path, required=True)
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    projected = project(args.finish.read_bytes(), args.cleanup.read_bytes())
    if args.fixture is not None:
        expected = json.loads(args.fixture.read_text(encoding="utf-8"))
        if projected != expected:
            raise ValueError("checked-in 083 complete fixture mismatch")
    serialized = json.dumps(projected, ensure_ascii=False, sort_keys=True, indent=2)
    if args.output is not None:
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(serialized + "\n")
    print(serialized)


if __name__ == "__main__":
    main()
