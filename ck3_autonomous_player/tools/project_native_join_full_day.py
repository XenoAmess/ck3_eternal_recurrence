"""Project one exact-build natural join from a complete seven-boundary trace.

The projection preserves the raw receipt identity and distinguishes a bounded
phase capture from the still-missing full mutable transition bundle.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


RESPONSE_SUFFIXES = (
    "before-snapshot", "before-control", "save", "after-save-snapshot",
    "begin", "advance", "after-snapshot", "finish",
)
BOUNDARIES = (
    "native_capture_before_side0_schedule_call_0x27FB58F",
    "native_capture_after_side1_schedule_return_0x27FB5AC",
    "native_capture_before_side0_phase_fire_entry_0x23C9900",
    "native_capture_after_side0_phase_fire_return_0x2309EF7",
    "native_capture_before_side1_phase_fire_entry_0x23C9900",
    "native_capture_after_side1_phase_fire_return_0x2309EFF",
    "paused_next_day_stable_query",
)
COMBAT_ID = 16777218
CASES = {
    11: {"prefix": "d11r2", "joining_army_id": 22, "date_raw": 53146488},
    21: {"prefix": "d21", "joining_army_id": 28, "date_raw": 53146728},
}


def _read_json(path: Path) -> tuple[dict, str]:
    raw = path.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest().upper()


def _army_ids(record: dict, side: int) -> list[int]:
    return [row["army_id"] for row in record["sides"][side]["armies"]]


def _enemy_armies(snapshot: dict) -> list[int]:
    wars = snapshot.get("active_wars")
    if not isinstance(wars, list) or len(wars) != 1:
        raise ValueError("expected exactly one original active war")
    return [row["army_id"] for row in wars[0]["enemy_armies"] if row["in_combat"]]


def project(attempt: Path, source_day: int = 11) -> dict:
    case = CASES[source_day]
    prefix = case["prefix"]
    joining_army_id = case["joining_army_id"]
    date_raw = case["date_raw"]
    base = attempt / "ck3-output"
    receipts: dict[str, dict] = {}
    receipt_hashes: dict[str, str] = {}
    for suffix in RESPONSE_SUFFIXES:
        name = f"{prefix}-{suffix}"
        receipt, sha = _read_json(base / "interactive-requests-responses" / f"{name}.json")
        if receipt.get("result") != "CALL_COMPLETED":
            raise ValueError(f"original response not completed: {name}")
        receipts[name] = receipt["body"]
        receipt_hashes[name] = sha
    copy, copy_sha = _read_json(base / "checkpoint-copy.json")
    preflight, preflight_sha = _read_json(base / "preflight.json")
    capture, capture_sha = _read_json(base / "capture-report.json")
    if (copy["source"]["date_raw"] != date_raw
            or copy["source"]["actor"] != 29829
            or copy["source"]["save"]["sha256"] != copy["profile_copy"]["sha256"]
            or capture["environment_session_complete"] is not True
            or preflight["game"]["sha256"] !=
            "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"):
        raise ValueError("source/clean shutdown/exact-build binding failed")
    begin = receipts[f"{prefix}-begin"]
    save = receipts[f"{prefix}-save"]
    advance = receipts[f"{prefix}-advance"]
    finish = receipts[f"{prefix}-finish"]
    after_save = receipts[f"{prefix}-after-save-snapshot"]
    before = receipts[f"{prefix}-before-snapshot"]
    after = receipts[f"{prefix}-after-snapshot"]
    if (save["checkpoint"]["status"] != "saved"
            or begin["status"] != "armed" or finish["status"] != "bounded_trace_available"
            or before["date_raw"] != date_raw or after_save["date_raw"] != date_raw
            or after["date_raw"] != date_raw + 24
            or advance["ending_date_raw"] - advance["starting_date_raw"] != 24
            or finish["combat_id"] != COMBAT_ID):
        raise ValueError("session/day/managed trace did not close")
    managed = finish["managed_trace"]
    checkpoint = managed["managed_checkpoint"]
    trace = managed["trace"]
    readiness = trace["readiness"]
    records = trace["records"]
    if (checkpoint["recoverable_checkpoint_created"] is not True
            or checkpoint["exact_one_day_observed"] is not True
            or checkpoint["boundary_dates_match_checkpoint"] is not True
            or checkpoint["detours_uninstalled"] is not True
            or trace["status"] != "captured" or trace["failure_flags"] != 0
            or trace["record_count"] != 7 or len(records) != 7
            or readiness["bounded_capture_complete"] is not True
            or [row["boundary"] for row in records] != list(BOUNDARIES)
            or any(row["capture_failure_flags"] != 0 for row in records)
            or [row["native_date_raw"] for row in records] !=
            [date_raw, date_raw, *([date_raw + 24] * 5)]
            or any(row["combat_id"] != COMBAT_ID for row in records)):
        raise ValueError("seven original boundaries are not fully captured")
    old = _army_ids(records[1], 0)
    joined = _army_ids(records[2], 0)
    if (joining_army_id in old or joined != [*old, joining_army_id]
            or any(_army_ids(row, 0) != old for row in records[:2])
            or any(_army_ids(row, 0) != joined for row in records[2:])
            or sorted(_enemy_armies(before)) != sorted(old)
            or sorted(_enemy_armies(after)) != sorted(joined)
            or any(_army_ids(row, 1) != _army_ids(records[0], 1) for row in records)):
        raise ValueError(f"army {joining_army_id} did not join at the observed boundary")
    prefire = {r["regiment_id"]: r for r in records[2]["sides"][0]["regiments"]
               if r["army_id"] == joining_army_id}
    final = {r["regiment_id"]: r for r in records[6]["sides"][0]["regiments"]
             if r["army_id"] == joining_army_id}
    if not prefire or prefire.keys() != final.keys():
        raise ValueError("joining regiments did not retain identity")
    regiment_deltas = []
    for regiment_id, source in prefire.items():
        target = final[regiment_id]
        soft = target["soft_casualties_raw"] - source["soft_casualties_raw"]
        source_hard = source["hard_casualties_raw"]
        target_hard = target["hard_casualties_raw"]
        if source_hard is None or target_hard is None:
            if source_hard is not None or target_hard is not None or source["fights_in_main_phase"]:
                raise ValueError(f"joining regiment hard-loss availability drift: {regiment_id}")
            hard = None
        else:
            hard = target_hard - source_hard
        current = source["current_fighting_raw"] - target["current_fighting_raw"]
        if source["starting_raw"] != target["starting_raw"] or current != soft + (hard or 0):
            raise ValueError(f"joining regiment arithmetic drift: {regiment_id}")
        regiment_deltas.append({"regiment_id": regiment_id,
                               "bucket": source["bucket"],
                               "fights_in_main_phase": source["fights_in_main_phase"],
                               "before_current_raw": source["current_fighting_raw"],
                               "after_current_raw": target["current_fighting_raw"],
                               "soft_delta_raw": soft, "hard_delta_raw": hard,
                               "current_drop_raw": current})
    regiment_deltas.sort(key=lambda row: row["regiment_id"])
    return {
        "schema": "ck3.native_join_full_day.v1", "game_build": "1.19.0.6",
        "combat_id": COMBAT_ID, "source_date_raw": date_raw,
        "arrival_date_raw": date_raw + 24, "joining_army_id": joining_army_id,
        "source_save_sha256": copy["source"]["save"]["sha256"],
        "source_receipt_sha256": copy["source"]["receipt"]["sha256"],
        "bridge_dll_sha256": preflight["bridge_dll"]["sha256"],
        "checkpoint_copy_sha256": copy_sha, "preflight_sha256": preflight_sha,
        "capture_report_sha256": capture_sha, "response_sha256": receipt_hashes,
        "old_side0_army_ids": old, "new_side0_army_ids": joined,
        "new_army_present_before_first_side0_fire": True,
        "boundaries": [{"boundary": row["boundary"],
                        "date_raw": row["native_date_raw"],
                        "phase_day": row["phase_day"],
                        "side0_army_ids": _army_ids(row, 0),
                        "side0_fighting_raw": row["sides"][0]["current_fighting_total_raw"],
                        "side0_regiment_count": len(row["sides"][0]["regiments"]),
                        "side1_army_ids": _army_ids(row, 1),
                        "side1_fighting_raw": row["sides"][1]["current_fighting_total_raw"],
                        "capture_failure_flags": row["capture_failure_flags"]}
                       for row in records],
        "outgoing_damage": trace["outgoing_damage"],
        "post_counter_attack": trace["post_counter_attack"],
        "joining_regiments": regiment_deltas,
        "joining_fighting_regiment_count": sum(r["fights_in_main_phase"] for r in regiment_deltas),
        "joining_soft_delta_raw": sum(r["soft_delta_raw"] for r in regiment_deltas),
        "joining_hard_delta_raw": sum(r["hard_delta_raw"] or 0 for r in regiment_deltas),
        "joining_current_drop_raw": sum(r["current_drop_raw"] for r in regiment_deltas),
        "bounded_seven_boundary_capture_complete": True,
        "full_mutable_transition_bundle_complete": readiness["full_mutable_transition_bundle_complete"],
        "original_trace_ready": readiness["original_trace_ready"],
        "general_cross_manager_call_order_proven": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=Path, required=True)
    parser.add_argument("--source-day", type=int, choices=sorted(CASES), default=11)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = project(args.attempt, args.source_day)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output),
                      "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest().upper(),
                      "joining_regiment_count": len(result["joining_regiments"]),
                      "joining_soft_delta_raw": result["joining_soft_delta_raw"],
                      "joining_hard_delta_raw": result["joining_hard_delta_raw"]}))


if __name__ == "__main__":
    main()
