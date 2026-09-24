"""Project observed phase-event ledger appends without inventing effect parity.

The ring captures only a bounded subset of mutable state.  A battle-event row
appearing between fire boundaries is evidence of a ledger append, not proof
that its named script effect completed or that all later feedback is known.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from xar_autoplayer.simulation.native_battle_case import (  # noqa: E402
    load_episode01_native_battle_case,
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _indexed(rows: list[dict], key: str) -> dict[int, dict]:
    result = {row[key]: row for row in rows}
    if len(result) != len(rows):
        raise ValueError(f"duplicate {key}")
    return result


def _deltas(before: list[dict], after: list[dict], key: str) -> list[dict]:
    left, right = _indexed(before, key), _indexed(after, key)
    if left.keys() != right.keys():
        raise ValueError(f"tracked {key} identity set changed within fire pair")
    return [
        {"id": identity, "before": left[identity], "after": right[identity]}
        for identity in sorted(left)
        if left[identity] != right[identity]
    ]


def _character_at(record: dict, character_id: int) -> dict | None:
    return _indexed(record["characters"], "character_id").get(character_id)


def project(trace_root: Path) -> dict:
    trace_root = trace_root.resolve()
    case = load_episode01_native_battle_case()
    response_dir = trace_root / "ck3-output" / "interactive-requests-responses"
    traces_by_day = {source["source_day"]: source for source in case["phase_traces"]}
    rows = []
    for source in case["phase_traces"]:
        day = source["source_day"]
        name = "day04-finish.json" if day == 4 else f"trace-d{day:02d}-finish.json"
        path = response_dir / name
        if digest(path) != source["finish_receipt_sha256"]:
            raise ValueError(f"day {day}: source receipt hash mismatch")
        body = json.loads(path.read_text(encoding="utf-8"))["body"]
        trace = body["managed_trace"]["trace"]
        if trace["readiness"]["original_trace_ready"] is not False:
            raise ValueError(f"day {day}: unexpected production-ready trace")
        records = trace["records"]
        if len(records) < 6:
            continue
        for side_index, left_index, right_index in ((0, 2, 3), (1, 4, 5)):
            before, after = records[left_index], records[right_index]
            if (before["capture_failure_flags"] or after["capture_failure_flags"]
                    or before["combat_id"] != case["combat_id"]
                    or after["combat_id"] != case["combat_id"]
                    or before["native_date_raw"] != after["native_date_raw"]):
                continue
            old_events, new_events = before["battle_events"], after["battle_events"]
            if new_events[:len(old_events)] != old_events:
                raise ValueError(f"day {day}: battle event ledger is not append-only")
            appended = new_events[len(old_events):]
            if not appended:
                continue
            if any(event["side_index"] != side_index for event in appended):
                raise ValueError(f"day {day}: event side identity mismatch")
            next_source = traces_by_day.get(day + 1)
            next_records = []
            if next_source is not None:
                next_path = response_dir / f"trace-d{day + 1:02d}-finish.json"
                if digest(next_path) != next_source["finish_receipt_sha256"]:
                    raise ValueError(f"day {day + 1}: source receipt hash mismatch")
                next_records = json.loads(next_path.read_text(encoding="utf-8"))["body"][
                    "managed_trace"
                ]["trace"]["records"]
            next_target_rows = []
            for event in appended:
                target_id = event["right_character_id"] if event["target_right"] else event["left_character_id"]
                next_target_rows.append({
                    "character_id": target_id,
                    "same_fire_before": _character_at(before, target_id),
                    "same_fire_after": _character_at(after, target_id),
                    "next_source_day_record0": _character_at(next_records[0], target_id)
                    if len(next_records) > 0 else None,
                    "next_source_day_record2": _character_at(next_records[2], target_id)
                    if len(next_records) > 2 else None,
                    "next_source_day_receipt_sha256": next_source["finish_receipt_sha256"]
                    if next_source is not None else None,
                })
            rows.append({
                "source_day": day,
                "target_day": day + 1,
                "source_trace_status": source["status"],
                "source_receipt_sha256": source["finish_receipt_sha256"],
                "phase_side_index": side_index,
                "fire_record_indices": [left_index, right_index],
                "native_date_raw": before["native_date_raw"],
                "appended_battle_events": appended,
                "observed_character_core_deltas_within_fire": _deltas(
                    before["characters"], after["characters"], "character_id"
                ),
                "observed_accolade_deltas_within_fire": _deltas(
                    before["accolades"], after["accolades"], "accolade_id"
                ),
                "target_character_observations": next_target_rows,
                "global_rng_counter_before": before["global_rng"]["counter"],
                "global_rng_counter_after": after["global_rng"]["counter"],
                "full_mutable_transition_bundle_complete": False,
                "effect_execution_or_complete_feedback_proven": False,
            })
    return {
        "schema": "ck3-native-phase-event-observations-v1",
        "case_id": case["case_id"],
        "game_version": case["game_version"],
        "combat_id": case["combat_id"],
        "trace_run_dir": str(trace_root),
        "phase_trace_trajectory": case["phase_trace_trajectory"],
        "event_fire_pairs": rows,
        "battle_event_row_count": sum(len(row["appended_battle_events"]) for row in rows),
        "effect_execution_or_complete_feedback_proven": False,
        "planner_usable": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f"refusing to overwrite output: {args.output}")
    result = project(args.trace_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "sha256": digest(args.output),
                      "fire_pairs": len(result["event_fire_pairs"]),
                      "event_rows": result["battle_event_row_count"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
