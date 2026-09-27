"""Project exact attempt 085 native full-entry evidence without changing CK3."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


FINISH_SHA256 = "A7F01C89BE66B34A6F2862BAEFC4354EF74507B6D5178E2949C381DEDC32FD88"
CLEANUP_SHA256 = "5FD3CFE8AB9A69D557042B5CA3DE2CC59587C6BA679BF430F2BA15A98337CB37"
EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
BRIDGE_SHA256 = "1CC2AE965CD0EE897F918D50AF038F3DA874354DA7F3A57D2710B7BCCF44366F"
SAVE_SHA256 = "3F4B2FDAAE1AA2ED4D94958673DDADF4DCDF4A4F49073594B9AE32E782BB6953"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def entries_by_id(side: dict) -> dict[int, list[int]]:
    rows = side["entries"]
    require(all(len(row) == 9 for row in rows), "entry column count")
    result = {row[0]: row for row in rows}
    require(len(result) == len(rows), "duplicate full RegimentID")
    require(sum(row[5] for row in rows) == side["entry_current_sum_raw"],
            "entry sum does not match native total")
    require(side["cached_fighting_total_raw"] - side["entry_current_sum_raw"]
            == side["cache_minus_entry_raw"], "native residual mismatch")
    return result


def analyze(finish_raw: bytes, cleanup_raw: bytes) -> dict:
    response = json.loads(finish_raw)
    cleanup = json.loads(cleanup_raw)
    require(response["result"] == "CALL_COMPLETED", "private finish failed")
    body = response["body"]
    managed = body["managed_trace"]
    checkpoint = managed["managed_checkpoint"]
    trace = managed["trace"]
    width = trace["runtime_join_width"]
    full = trace["runtime_join_full_entries"]
    require(body["combat_id"] == 16777218, "unexpected CombatID")
    require(checkpoint["before"]["date_raw"] == 53146488 and
            checkpoint["after"]["date_raw"] == 53146512 and
            checkpoint["exact_one_day_observed"] is True and
            checkpoint["detours_uninstalled"] is True, "checkpoint/date boundary")
    require(trace["status"] == "captured" and trace["failure_flags"] == 0,
            "private collector not fully captured")
    require(width["status"] == "captured" and width["count"] == 3 and
            width["first_failure_code"] == 0, "width boundary incomplete")
    require(full["status"] == "captured" and full["count"] == 2 and
            full["first_failure_code"] == 0, "full-entry boundary incomplete")
    require(cleanup["capture_returncode"] == 0 and
            cleanup["cleanup_ok"] is True, "CK3 clean exit not proven")

    before, after = full["boundaries"]
    w_before, w_after, w_fire = width["boundaries"]
    for index, (row, wrow) in enumerate(((before, w_before),
                                         (after, w_after))):
        require(row["boundary"] == index and wrow["boundary"] == index,
                "join boundary order")
        require(row["combat_id"] == wrow["combat_id"] == 16777218 and
                row["incoming_army_id"] == wrow["army_id"] == 22 and
                row["native_date_raw"] == wrow["native_date_raw"] == 53146512 and
                row["thread_id"] == wrow["thread_id"],
                "width/full-entry identity mismatch")
        require([side["cached_fighting_total_raw"] for side in row["sides"]]
                == wrow["side_fighting_total_raw"],
                "width/full-entry cache mismatch")
    require(before["joined_side_index"] == -1 and
            after["joined_side_index"] == 0 and
            22 not in before["sides"][0]["army_ids"] and
            22 in after["sides"][0]["army_ids"],
            "joined-side roster mismatch")
    require(w_fire["combat_id"] == 16777218 and
            w_fire["army_id"] == 22 and
            w_fire["outgoing_width_argument"] == w_after["final_width"],
            "first fire width mismatch")

    side_changes = []
    for side_index in (0, 1):
        old_side, new_side = before["sides"][side_index], after["sides"][side_index]
        old, new = entries_by_id(old_side), entries_by_id(new_side)
        common = old.keys() & new.keys()
        added = sorted(new.keys() - old.keys())
        removed = sorted(old.keys() - new.keys())
        changed = sorted(rid for rid in common if old[rid] != new[rid])
        side_changes.append({
            "side_index": side_index,
            "before_cached_raw": old_side["cached_fighting_total_raw"],
            "before_entry_sum_raw": old_side["entry_current_sum_raw"],
            "before_cache_minus_entry_raw": old_side["cache_minus_entry_raw"],
            "after_cached_raw": new_side["cached_fighting_total_raw"],
            "after_entry_sum_raw": new_side["entry_current_sum_raw"],
            "after_cache_minus_entry_raw": new_side["cache_minus_entry_raw"],
            "added_army_ids": sorted(set(new_side["army_ids"]) -
                                     set(old_side["army_ids"])),
            "removed_army_ids": sorted(set(old_side["army_ids"]) -
                                       set(new_side["army_ids"])),
            "unchanged_regiment_count": len(common) - len(changed),
            "changed_regiments": [
                {"regiment_id": rid, "before": old[rid], "after": new[rid]}
                for rid in changed
            ],
            "added_regiments": [new[rid] for rid in added],
            "removed_regiments": [old[rid] for rid in removed],
            "added_current_sum_raw": sum(new[rid][5] for rid in added),
            "removed_current_sum_raw": sum(old[rid][5] for rid in removed),
        })
    incoming = before["incoming_regiments"]
    require(incoming == after["incoming_regiments"],
            "incoming native army changed across wrapper")
    require(all(len(row) == 2 for row in incoming), "incoming column count")
    added_by_id = {row[0]: row for row in side_changes[0]["added_regiments"]}
    require(set(added_by_id) == {row[0] for row in incoming},
            "joined entry IDs differ from incoming CArmy IDs")
    for regiment_id, basic_soldiers in incoming:
        require(added_by_id[regiment_id][4] == basic_soldiers * 100000,
                "entry starting soldiers differ from incoming CRegiment base")
    return {
        "schema": "ck3.native_join_full_entry_accounting.v1",
        "source": {"attempt": 85, "finish_sha256": FINISH_SHA256,
                   "cleanup_sha256": CLEANUP_SHA256,
                   "exe_sha256": EXE_SHA256,
                   "bridge_sha256": BRIDGE_SHA256,
                   "save_sha256": SAVE_SHA256},
        "identity": {"combat_id": 16777218, "joining_army_id": 22,
                     "native_date_raw": 53146512,
                     "join_thread_id": before["thread_id"]},
        "collector_status": "captured",
        "incoming_columns": full["incoming_columns"],
        "entry_columns": full["entry_columns"],
        "incoming_regiments": incoming,
        "incoming_basic_soldiers_total": sum(row[1] for row in incoming),
        "added_starting_sum_raw": sum(row[4] for row in added_by_id.values()),
        "added_zero_current_regiment_ids": sorted(
            regiment_id for regiment_id, row in added_by_id.items()
            if row[5] == 0
        ),
        "sides": side_changes,
        "width": {"before_base": w_before["base_width"],
                  "before_final": w_before["final_width"],
                  "after_base": w_after["base_width"],
                  "after_final": w_after["final_width"],
                  "first_fire_argument": w_fire["outgoing_width_argument"]},
        "clean_exit": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--finish", type=Path, required=True)
    parser.add_argument("--cleanup", type=Path, required=True)
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    finish_raw, cleanup_raw = args.finish.read_bytes(), args.cleanup.read_bytes()
    require(sha(finish_raw) == FINISH_SHA256, "085 finish SHA changed")
    require(sha(cleanup_raw) == CLEANUP_SHA256, "085 cleanup SHA changed")
    result = analyze(finish_raw, cleanup_raw)
    if args.fixture is not None:
        require(result == json.loads(args.fixture.read_text(encoding="utf-8")),
                "checked-in 085 full-entry fixture mismatch")
    serialized = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2)
    if args.output is not None:
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(serialized + "\n")
    print(serialized)


if __name__ == "__main__":
    main()
