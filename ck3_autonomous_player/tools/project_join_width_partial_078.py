"""Read-only projection of attempt 078's two native join-width boundaries.

The source response is deliberately RED as a whole. This projector preserves
that status and never infers the absent first phase-fire argument.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


FINISH_SHA256 = "9BFCEFF0BD1454F47B2371683B342E4FB8EC634CE4AF1397937375873FD51FF8"
EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
BRIDGE_SHA256 = "8EEFBE8854BFC28FA9CD61F1677B7AB66C642C6F005EBB9661775E2FFE7FE0A0"
SAVE_SHA256 = "3F4B2FDAAE1AA2ED4D94958673DDADF4DCDF4A4F49073594B9AE32E782BB6953"


def project(raw: bytes) -> dict[str, object]:
    if hashlib.sha256(raw).hexdigest().upper() != FINISH_SHA256:
        raise ValueError("078 finish SHA-256 mismatch")
    response = json.loads(raw)
    if response["result"] != "CALL_COMPLETED":
        raise ValueError("078 finish was not completed")
    body = response["body"]
    managed = body["managed_trace"]
    checkpoint = managed["managed_checkpoint"]
    trace = managed["trace"]
    width = trace["runtime_join_width"]
    if (body["combat_id"] != 16777218 or body["status"] != "trace_unavailable"
            or body["production_trace_ready"] is not False
            or checkpoint["before"]["date_raw"] != 53146488
            or checkpoint["after"]["date_raw"] != 53146512
            or not checkpoint["exact_one_day_observed"]
            or trace["status"] != "failed" or trace["failure_flags"] != 262144
            or width["status"] != "failed" or width["count"] != 2
            or width["first_failure_code"] != 5
            or len(width["boundaries"]) != 2):
        raise ValueError("078 partial-capture contract changed")
    rows = width["boundaries"]
    before, after = rows
    for index, row in enumerate(rows):
        if (row["boundary"] != index or row["combat_id"] != 16777218
                or row["army_id"] != 22 or row["native_date_raw"] != 53146512
                or row["phase_day"] != 7 or row["outgoing_width_argument"] != -1
                or len(row["side_fighting_total_raw"]) != 2):
            raise ValueError("078 join boundary identity changed")
    if (before["side_index"] != -1 or after["side_index"] != 0
            or before["thread_id"] != after["thread_id"]
            or before["thread_id"] == checkpoint["before"]["thread_id"]):
        raise ValueError("078 thread/side identity changed")

    def boundary(row: dict[str, object]) -> dict[str, object]:
        totals = row["side_fighting_total_raw"]
        return {
            "boundary": row["boundary"],
            "side_index": row["side_index"],
            "thread_id": row["thread_id"],
            "base_width": row["base_width"],
            "final_width": row["final_width"],
            "side_fighting_total_raw": totals,
            "candidate_half_total_truncated": sum(totals) // 200000,
        }

    return {
        "schema": "ck3.native_join_width_partial_observation.v1",
        "source": {
            "attempt": 78,
            "finish_response_name": "jwidth078-finish.json",
            "finish_sha256": FINISH_SHA256,
            "exe_sha256": EXE_SHA256,
            "bridge_sha256": BRIDGE_SHA256,
            "save_sha256": SAVE_SHA256,
        },
        "collector_status": "failed",
        "collector_failure_flags": 262144,
        "first_failure_code": 5,
        "combat_id": 16777218,
        "native_date_raw": 53146512,
        "candidate_joining_army_id": 22,
        "mailbox_thread_id": checkpoint["before"]["thread_id"],
        "join_thread_id": before["thread_id"],
        "phase_fire_thread_id": None,
        "fighting_total_scale": 100000,
        "boundaries": [boundary(before), boundary(after)],
        "observed_delta": {
            "base_width": after["base_width"] - before["base_width"],
            "final_width": after["final_width"] - before["final_width"],
        },
        "three_boundary_complete": False,
        "fire_width": None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--finish", type=Path, required=True)
    parser.add_argument("--fixture", type=Path)
    args = parser.parse_args()
    projected = project(args.finish.read_bytes())
    if args.fixture is not None:
        expected = json.loads(args.fixture.read_text(encoding="utf-8"))
        if projected != expected:
            raise ValueError("checked-in 078 partial fixture mismatch")
    print(json.dumps(projected, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
