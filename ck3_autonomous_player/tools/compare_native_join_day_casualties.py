"""Check the agent casualty kernel with native join-before-damage inputs.

Both joined rosters and the day's outgoing damage are native observations.
This conditional parity check does not predict arrival, damage, effects, or a
whole-battle probability.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
from xar_autoplayer.simulation.combat_core import (  # noqa: E402
    CombatRegimentState,
    RegimentKind,
    apply_main_phase_casualties,
)
from xar_autoplayer.simulation.native_battle_case import (  # noqa: E402
    EPISODE01_CASE_SHA256,
    EPISODE01_JOIN_DAY_SHA256,
    load_episode01_join_day_casualties,
    load_episode01_native_battle_case,
)
from compare_native_main_tick_receipts import _source_entries  # noqa: E402


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def receipt(path: Path) -> dict:
    result = json.loads(path.read_text(encoding="utf-8"))
    if result.get("result") != "CALL_COMPLETED":
        raise ValueError(f"native receipt did not complete: {path}")
    return result["body"]


def compare(trace_root: Path) -> dict:
    case = load_episode01_native_battle_case()
    join = load_episode01_join_day_casualties()
    if case["case_id"] != join["case_id"]:
        raise ValueError("battle case and join observations do not bind")
    by_day = {row["source_day"]: row for row in case["phase_traces"]}
    responses = trace_root / "ck3-output" / "interactive-requests-responses"
    results = []
    for observation in join["join_observations"]:
        day, arrival_day = observation["source_day"], observation["arrival_day"]
        source_path = responses / f"trace-d{day:02d}-before-control.json"
        target_path = responses / f"trace-d{arrival_day:02d}-before-control.json"
        finish_path = responses / f"trace-d{day:02d}-finish.json"
        next_path = responses / f"trace-d{arrival_day:02d}-finish.json"
        for path, expected in (
            (source_path, by_day[day]["control_receipt_sha256"]),
            (target_path, by_day[arrival_day]["control_receipt_sha256"]),
            (finish_path, by_day[day]["finish_receipt_sha256"]),
            (next_path, observation["arrival_phase_receipt_sha256"]),
        ):
            if digest(path) != expected:
                raise ValueError(f"receipt SHA changed: {path}")
        source = receipt(source_path)["battle_control_snapshot"]
        target = receipt(target_path)["battle_control_snapshot"]
        if source["combat_id"] != case["combat_id"] or target["combat_id"] != case["combat_id"]:
            raise ValueError(f"day {day}: control CombatID mismatch")
        outgoing = receipt(finish_path)["managed_trace"]["trace"]["outgoing_damage"]
        if outgoing["count"] != 2:
            raise ValueError(f"day {day}: native outgoing pair absent")
        incoming = outgoing["side1_raw"]
        old_entries = _source_entries(source["attacker"])
        source_trace = receipt(finish_path)["managed_trace"]["trace"]
        pre_schedule = source_trace["records"][0]
        if (pre_schedule["capture_failure_flags"] != 0
                or pre_schedule["native_date_raw"] != source["observed_date_raw"]
                or pre_schedule["boundary"] != "native_capture_before_side0_schedule_call_0x27FB58F"):
            raise ValueError(f"day {day}: native pre-schedule effective stats unavailable")
        pre_schedule_rows = {
            row["regiment_id"]: row
            for side in pre_schedule["sides"]
            for row in side["regiments"]
        }
        changed_effective_stats = []
        refreshed_old_entries = []
        for entry in old_entries:
            native = pre_schedule_rows.get(entry.regiment_id)
            if native is None or native["current_fighting_raw"] != entry.current_raw:
                raise ValueError(f"day {day}: old regiment state changed before schedule")
            if native["effective_toughness_raw"] != entry.toughness_raw:
                changed_effective_stats.append({
                    "regiment_id": entry.regiment_id,
                    "control_toughness_raw": entry.toughness_raw,
                    "pre_schedule_toughness_raw": native["effective_toughness_raw"],
                })
            refreshed_old_entries.append(replace(
                entry, toughness_raw=native["effective_toughness_raw"]
            ))
        joined_ids = {row["regiment_id"] for row in observation["regiments"]
                      if row["fights_in_main_phase"]}
        next_trace = receipt(next_path)["managed_trace"]["trace"]
        first = next_trace["records"][0]
        if (first["capture_failure_flags"] != 0
                or first["native_date_raw"] != observation["arrival_phase_date_raw"]):
            raise ValueError(f"day {arrival_day}: next phase record not usable")
        new_entries = []
        for side in first["sides"]:
            for row in side["regiments"]:
                if row["regiment_id"] not in joined_ids:
                    continue
                new_entries.append(CombatRegimentState(
                    regiment_id=row["regiment_id"],
                    kind=RegimentKind.LEVY if row["bucket"] == "levy" else RegimentKind.MEN_AT_ARMS,
                    current_raw=row["starting_raw"],
                    soft_casualties_raw=0,
                    toughness_raw=row["effective_toughness_raw"],
                ))
        if {row.regiment_id for row in new_entries} != joined_ids:
            raise ValueError(f"day {arrival_day}: joined regiment inputs incomplete")
        entries = tuple(refreshed_old_entries) + tuple(new_entries)
        if len({row.regiment_id for row in entries}) != len(entries):
            raise ValueError(f"day {arrival_day}: duplicate old/new regiment identity")
        denominator = sum(row.current_raw for row in entries)
        predicted = apply_main_phase_casualties(
            entries,
            incoming_damage_raw=incoming,
            defending_total_fighting_men_raw=denominator,
        )
        target_rows = {
            row["regiment_id"]: row
            for bucket in ("levy_entries", "men_at_arms_entries")
            for row in target["attacker"][bucket]
        }
        residuals = []
        matched_joined = 0
        for entry in predicted.entries:
            native = target_rows.get(entry.regiment_id)
            if native is None:
                raise ValueError(f"day {arrival_day}: predicted regiment {entry.regiment_id} absent")
            residual = entry.current_raw - native["current_fighting_raw"]
            if residual:
                residuals.append({
                    "regiment_id": entry.regiment_id,
                    "newly_joined": entry.regiment_id in joined_ids,
                    "predicted_minus_native_raw": residual,
                })
            elif entry.regiment_id in joined_ids:
                matched_joined += 1
        if matched_joined != len(joined_ids):
            raise ValueError(f"day {arrival_day}: newly joined regiments failed conditional parity")
        results.append({
            "source_day": day,
            "arrival_day": arrival_day,
            "army_id": observation["army_id"],
            "source_control_receipt_sha256": digest(source_path),
            "arrival_control_receipt_sha256": digest(target_path),
            "source_phase_receipt_sha256": digest(finish_path),
            "arrival_phase_receipt_sha256": digest(next_path),
            "native_incoming_damage_raw": incoming,
            "pre_schedule_boundary": pre_schedule["boundary"],
            "pre_schedule_capture_failure_flags": pre_schedule["capture_failure_flags"],
            "old_regiment_effective_toughness_changes": changed_effective_stats,
            "old_fighting_regiment_count": len(old_entries),
            "joined_fighting_regiment_count": len(new_entries),
            "defending_total_fighting_men_before_damage_raw": denominator,
            "joined_regiment_current_exact_count": matched_joined,
            "all_joined_regiments_current_exact": True,
            "whole_side_current_exact": not residuals,
            "residuals": residuals,
            "source_day_whole_trace_available": False,
        })
    return {
        "schema": "ck3-native-join-day-conditional-casualty-parity-v2",
        "case_sha256": EPISODE01_CASE_SHA256,
        "join_evidence_sha256": EPISODE01_JOIN_DAY_SHA256,
        "game_version": case["game_version"],
        "combat_id": case["combat_id"],
        "trajectory": case["phase_trace_trajectory"],
        "conditioned_on_native_outgoing_damage": True,
        "conditioned_on_observed_joined_roster": True,
        "conditioned_on_native_pre_schedule_effective_toughness": True,
        "outgoing_damage_reconstructed": False,
        "join_policy_reconstructed": False,
        "effective_toughness_refresh_reconstructed": False,
        "whole_battle_win_probability_available": False,
        "planner_usable": False,
        "source_days": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f"refusing to overwrite comparison: {args.output}")
    report = compare(args.trace_root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "sha256": digest(args.output),
                      "joined_exact": [row["joined_regiment_current_exact_count"] for row in report["source_days"]],
                      "all_residual_counts": [len(row["residuals"]) for row in report["source_days"]]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
