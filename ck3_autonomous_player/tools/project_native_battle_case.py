"""Project immutable CK3 battle receipts into a portable shared evidence case.

The projected data is for film timelines and simulator calibration alike.  It
never upgrades a bounded native trace into a planner-qualified forecast.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PureWindowsPath


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _entry_current(side: dict[str, object]) -> int:
    return sum(
        int(row["current_fighting_raw"])
        for bucket in ("levy_entries", "men_at_arms_entries")
        for row in side[bucket]
    )


def _new_events(before: dict[str, object], after: dict[str, object]) -> list[dict[str, object]]:
    first = before["battle_events"]
    second = after["battle_events"]
    if not isinstance(first, list) or not isinstance(second, list) or second[:len(first)] != first:
        raise ValueError("battle events are not append-only within a phase boundary")
    return second[len(first):]


def project(original_path: Path, trace_root: Path) -> dict[str, object]:
    original = read_json(original_path)
    if original.get("schema") != "episode01-ck3-original-battle-r1":
        raise ValueError("unexpected original-case schema")
    days = original["daily"]
    if len(days) != 31 or [row["day"] for row in days] != list(range(1, 32)):
        raise ValueError("original case has a non-contiguous daily sequence")
    if [row["date_raw"] for row in days] != [original["first_date_raw"] + 24 * i for i in range(31)]:
        raise ValueError("original case has a date gap")
    if original["terminal_date_raw"] != original["first_date_raw"] + 31 * 24:
        raise ValueError("terminal date does not follow the final observed day")
    receipts = [
        {"day": row["day"], "kind": row["kind"],
         "file": PureWindowsPath(row["path"]).name, "sha256": row["sha256"]}
        for row in original["source_files"]
    ]
    response_dir = trace_root / "ck3-output" / "interactive-requests-responses"
    traces = []
    for source_day in range(4, 28):
        if source_day == 4:
            prefix = "day04"
            checkpoint = trace_root / "day04-immutable.ck3"
            control_path = response_dir / "day04-control.json"
        else:
            prefix = f"trace-d{source_day:02d}"
            checkpoint = trace_root / f"{prefix}-immutable.ck3"
            control_path = response_dir / f"{prefix}-before-control.json"
        finish_path = response_dir / f"{prefix}-finish.json"
        control = read_json(control_path)["body"]["battle_control_snapshot"]
        case_day = days[source_day - 1]
        side0 = control["attacker"]
        side1 = control["defender"]
        observed = [_entry_current(side0), _entry_current(side1)]
        expected = [case_day["side0"]["current_raw"], case_day["side1"]["current_raw"]]
        replay_matches = bool(
            control["combat_id"] == original["combat_id"]
            and control["observed_date_raw"] == case_day["date_raw"]
            and control["phase"] == case_day["phase"]
            and observed == expected
            and [row["public_cunit_id"] for row in side0["ordered_armies"]]
            == case_day["side0"]["army_ids"]
            and [row["public_cunit_id"] for row in side1["ordered_armies"]]
            == case_day["side1"]["army_ids"]
        )
        finish = read_json(finish_path)["body"]
        trace = finish["managed_trace"]["trace"]
        records = trace["records"]
        new_events = []
        if len(records) >= 6:
            for side_index, left, right in ((0, 2, 3), (1, 4, 5)):
                for event in _new_events(records[left], records[right]):
                    new_events.append({"phase_side_index": side_index, **event})
        traces.append({
            "source_day": source_day,
            "target_day": source_day + 1,
            "source_date_raw": case_day["date_raw"],
            "checkpoint_sha256": digest(checkpoint),
            "control_receipt_sha256": digest(control_path),
            "finish_receipt_sha256": digest(finish_path),
            "replay_matches_original_day": replay_matches,
            "original_side_current_raw": expected,
            "replay_side_current_raw": observed,
            "status": finish["status"],
            "failure_flags": trace["failure_flags"],
            "record_count": trace["record_count"],
            "readiness": trace["readiness"],
            "outgoing_damage": trace["outgoing_damage"],
            "post_counter_attack": trace["post_counter_attack"],
            "new_battle_events": new_events,
        })
    first_divergence = next(
        (row["source_day"] for row in traces if not row["replay_matches_original_day"]),
        None,
    )
    return {
        "schema": "ck3-native-battle-evidence-v1",
        "case_id": "episode01-sicily-messina-combat-16777218",
        "game_version": original["game_version"],
        "executable_sha256": original["executable_sha256"],
        "original_case_receipt_sha256": digest(original_path),
        "war_id": original["war_id"],
        "combat_id": original["combat_id"],
        "province_id": original["province_id"],
        "first_date_raw": original["first_date_raw"],
        "terminal_date_raw": original["terminal_date_raw"],
        "winner_side": original["winner_side"],
        "winner_relative_to_player": original["winner_relative_to_player"],
        "battle_warscore_player_delta_raw_q100000": original["battle_warscore_player_delta_raw_q100000"],
        "joins": original["joins"],
        "daily": days,
        "original_receipts": receipts,
        "phase_traces": traces,
        "phase_trace_trajectory": "independent-replay-from-original-contact-checkpoint",
        "same_random_trajectory_proven": False,
        "first_numeric_divergence_source_day": first_divergence,
        "phase_trace_may_bind_to_original_daily_transition": False,
        "planner_usable": False,
        "calibrated_win_probability_available": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--trace-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"refusing to overwrite existing projection: {args.output}")
    result = project(args.original, args.trace_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output), "sha256": digest(args.output),
        "days": len(result["daily"]), "phase_traces": len(result["phase_traces"]),
        "replay_matching_days": sum(row["replay_matches_original_day"] for row in result["phase_traces"]),
        "bounded_traces": sum(row["status"] == "bounded_trace_available" for row in result["phase_traces"]),
        "new_battle_events": sum(len(row["new_battle_events"]) for row in result["phase_traces"]),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
