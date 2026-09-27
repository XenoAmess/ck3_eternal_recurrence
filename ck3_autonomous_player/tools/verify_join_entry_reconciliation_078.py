"""Read-only reconciliation of the frozen 078 join-width gap.

The seven-boundary entry rows bracket the join by one native day; they are not
the exact wrapper-entry and wrapper-return snapshots proposed for attempt 080.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


FINISH_SHA256 = "9BFCEFF0BD1454F47B2371683B342E4FB8EC634CE4AF1397937375873FD51FF8"
COMBAT_ID = 16777218
JOINING_ARMY_ID = 22
PRE_DATE_RAW = 53146488
JOIN_DATE_RAW = 53146512


def _entries(side: dict) -> dict[int, dict]:
    rows = side["regiments"]
    by_id = {row["regiment_id"]: row for row in rows}
    if len(by_id) != len(rows):
        raise ValueError("duplicate full RegimentID in side entry array")
    return by_id


def verify(raw: bytes) -> dict:
    if hashlib.sha256(raw).hexdigest().upper() != FINISH_SHA256:
        raise ValueError("078 original finish SHA-256 mismatch")
    finish = json.loads(raw)
    trace = finish["body"]["managed_trace"]["trace"]
    join = trace["runtime_join_width"]
    records = trace["records"]
    if (finish["result"] != "CALL_COMPLETED" or trace["status"] != "failed"
            or join["status"] != "failed" or join["count"] != 2
            or join["first_failure_code"] != 5 or len(records) != 7
            or [row["boundary"] for row in join["boundaries"]] != [0, 1]
            or any(row["combat_id"] != COMBAT_ID for row in join["boundaries"])
            or [row["native_date_raw"] for row in join["boundaries"]]
            != [JOIN_DATE_RAW, JOIN_DATE_RAW]
            or records[1]["combat_id"] != COMBAT_ID
            or records[2]["combat_id"] != COMBAT_ID
            or records[1]["native_date_raw"] != PRE_DATE_RAW
            or records[2]["native_date_raw"] != JOIN_DATE_RAW):
        raise ValueError("078 status, identity, or boundary sequence changed")
    before, after = records[1], records[2]
    before_join, after_join = join["boundaries"]
    sides = []
    for side_index in (0, 1):
        earlier = before["sides"][side_index]
        later = after["sides"][side_index]
        old = _entries(earlier)
        new = _entries(later)
        changed = sorted(key for key in old.keys() & new.keys() if old[key] != new[key])
        removed = sorted(old.keys() - new.keys())
        added = sorted(new.keys() - old.keys())
        added_other_army = sorted(key for key in added
                                 if new[key]["army_id"] != JOINING_ARMY_ID)
        old_current = sum(row["current_fighting_raw"] for row in old.values())
        added_current = sum(new[key]["current_fighting_raw"] for key in added)
        new_current = sum(row["current_fighting_raw"] for row in new.values())
        row = {
            "side": side_index,
            "before_cache_raw": earlier["current_fighting_total_raw"],
            "before_entry_current_sum_raw": old_current,
            "before_cache_minus_entries_raw": earlier["current_fighting_total_raw"] - old_current,
            "old_entry_count": len(old),
            "old_entries_changed": changed,
            "old_entries_removed": removed,
            "new_entry_ids": added,
            "new_other_army_entry_ids": added_other_army,
            "new_entry_current_sum_raw": added_current,
            "after_entry_current_sum_raw": new_current,
            "join_entry_cache_raw": before_join["side_fighting_total_raw"][side_index],
            "join_return_cache_raw": after_join["side_fighting_total_raw"][side_index],
            "after_phase_fire_entry_cache_raw": later["current_fighting_total_raw"],
            "after_cache_minus_entries_raw": later["current_fighting_total_raw"] - new_current,
        }
        if (changed or removed or added_other_army
                or row["join_entry_cache_raw"] != row["before_cache_raw"]
                or row["join_return_cache_raw"] != new_current
                or row["after_phase_fire_entry_cache_raw"] != new_current
                or old_current + added_current != new_current):
            raise ValueError(f"side {side_index} entry reconciliation failed")
        sides.append(row)
    if (sides[0]["before_cache_minus_entries_raw"] != 5627319
            or sides[0]["new_entry_current_sum_raw"] != 256000000
            or len(sides[0]["new_entry_ids"]) != 13
            or sides[1]["before_cache_minus_entries_raw"] != 6540081
            or sides[1]["new_entry_ids"]):
        raise ValueError("078 expected reconciliation vector changed")
    return {
        "schema": "ck3.join_entry_reconciliation_078.v1",
        "source_finish_sha256": FINISH_SHA256,
        "combat_id": COMBAT_ID,
        "joining_army_id": JOINING_ARMY_ID,
        "record_before_date_raw": PRE_DATE_RAW,
        "join_date_raw": JOIN_DATE_RAW,
        "same_exact_wrapper_boundary_entry_rows": False,
        "three_boundary_join_width_complete": False,
        "phase_fire_width_argument": None,
        "sides": sides,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--finish", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.finish.read_bytes()), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
