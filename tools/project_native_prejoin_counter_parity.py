"""Bind same-date hypothetical reinforcement inputs to native R14 on two join days.

The source checkpoint is reloaded read-only for the v3 query. The original
paired run supplies pre-join fighting Q values, an immutable moving-army save,
and the native R14 after contact. No join timing or phase-effect forecast is
inferred from the exact arithmetic result.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "ck3_autonomous_player" / "src"))
sys.path.insert(0, str(REPO / "ck3_autonomous_player" / "tools"))
from xar_autoplayer.simulation.combat_input import freeze_combat_simulation_input
from xar_autoplayer.simulation.native_battle_case import (
    EPISODE01_PAIRED_COUNTER_SHA256,
    load_episode01_paired_counter_r14_parity,
)
from project_native_join_day_casualties import RAKALY_EXE_SHA256, _source_regiments


MELTED_SHA256 = {
    11: "D20D6B73BE790098130F4C9A5BB8A64FB39EBE20BF7332204A961D903DED0BA2",
    21: "FAF359742D91185B3CDE0F533F93CF0163FAA3107AAA839FAC9F6C5C3FAF4FB1",
}
JOIN_CASES = ((11, 22), (21, 28))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def response_body(path: Path) -> dict:
    row = json.loads(path.read_text(encoding="utf-8"))
    if row.get("result") != "CALL_COMPLETED":
        raise ValueError(f"native response incomplete: {path}")
    return row["body"]


def project(paired_run: Path, prejoin_runs: dict[int, Path], rakaly_exe: Path) -> dict:
    if digest(rakaly_exe) != RAKALY_EXE_SHA256:
        raise ValueError("Rakaly executable bytes changed")
    baseline = load_episode01_paired_counter_r14_parity()
    by_day = {row["day"]: row for row in baseline["days"]}
    paired_responses = paired_run / "ck3-output" / "interactive-requests-responses"
    repairs = []
    for day, joined_army_id in JOIN_CASES:
        source = by_day[day]
        raw_save = paired_run / f"d{day:02d}-immutable.ck3"
        if digest(raw_save) != source["checkpoint_sha256"]:
            raise ValueError(f"day {day}: original checkpoint drifted")
        melted = paired_run / f"d{day:02d}-melted.ck3"
        if digest(melted) != MELTED_SHA256[day]:
            raise ValueError(f"day {day}: melted save drifted")
        before = _source_regiments(melted.read_text(encoding="utf-8-sig"), joined_army_id)
        prejoin_root = prejoin_runs[day]
        responses = prejoin_root / "ck3-output" / "interactive-requests-responses"
        snapshot_path = responses / "001-snapshot.json"
        control_path = responses / "002-control.json"
        v3_path = responses / "003-prejoin-v3.json"
        snapshot = response_body(snapshot_path)
        control = response_body(control_path)["battle_control_snapshot"]
        v3 = response_body(v3_path)
        expected_date = 53146320 + 24 * (day - 4)
        if (snapshot["date_raw"] != expected_date or snapshot["paused"] is not True
                or control["observed_date_raw"] != expected_date
                or control["combat_id"] != 16777218
                or control["phase_raw"] != 1
                or v3["status"] != "available"):
            raise ValueError(f"day {day}: same-date paused combat identity failed")
        active = [army["public_cunit_id"] for army in control["attacker"]["ordered_armies"]]
        if active != ([16777221, 16777231, 27] + ([22] if day == 21 else [])):
            raise ValueError(f"day {day}: prejoin active attacker roster drifted")
        base = v3["combat_simulation_inputs"]["base_inputs"]
        if base["completeness"]["input_observation_ready"] is not True:
            raise ValueError(f"day {day}: hypothetical base input unavailable")
        model = freeze_combat_simulation_input(base)
        if (list(model.encounter.attacker_army_ids) != active + [joined_army_id]
                or list(model.encounter.defender_army_ids) != [18]):
            raise ValueError(f"day {day}: candidate roster drifted")
        joined = [army for army in model.armies if army.public_army_id == joined_army_id]
        if (len(joined) != 1
                or {reg.regiment_id: reg.current_soldiers for reg in joined[0].regiments} != before):
            raise ValueError(f"day {day}: saved moving regiment census disagrees with v3")
        trace_path = paired_responses / f"d{day:02d}-finish.json"
        if digest(trace_path) != source["trace_response_sha256"]:
            raise ValueError(f"day {day}: native R14 receipt drifted")
        trace = response_body(trace_path)["managed_trace"]["trace"]
        boundary = trace["records"][1]
        if (boundary["capture_failure_flags"] != 0
                or [side["side_index"] for side in boundary["sides"]] != [0, 1]
                or boundary["native_date_raw"] != expected_date):
            raise ValueError(f"day {day}: prejoin local boundary unavailable")
        old = {
            "enemy": {reg["regiment_id"]: reg for reg in boundary["sides"][0]["regiments"]},
            "player_or_allied": {reg["regiment_id"]: reg for reg in boundary["sides"][1]["regiments"]},
        }
        entries = {}
        damage = {}
        for side in old:
            current = []
            current_damage = {}
            for army in model.armies_for_side(side):
                for regiment in army.regiments:
                    entry = regiment.to_initial_combat_state()
                    if regiment.regiment_id in old[side]:
                        observed = old[side][regiment.regiment_id]
                        entry = replace(entry,
                                        current_raw=observed["current_fighting_raw"],
                                        toughness_raw=observed["effective_toughness_raw"])
                        if regiment.fights_in_main_phase:
                            current_damage[regiment.regiment_id] = observed["effective_damage_raw"]
                    elif army.public_army_id == joined_army_id and regiment.regiment_id in before:
                        entry = replace(entry, current_raw=before[regiment.regiment_id] * 100_000
                                        if regiment.fights_in_main_phase else 0)
                        if regiment.fights_in_main_phase:
                            current_damage[regiment.regiment_id] = regiment.stats.damage_raw
                    else:
                        raise ValueError(f"day {day}: regiment identity drifted: {regiment.regiment_id}")
                    current.append(entry)
            entries[side] = tuple(current)
            damage[side] = current_damage
        predictions = {}
        native = {
            "enemy": trace["post_counter_attack"]["side0_raw"],
            "player_or_allied": trace["post_counter_attack"]["side1_raw"],
        }
        for side in old:
            other = "enemy" if side == "player_or_allied" else "player_or_allied"
            predictions[side] = model.post_counter_attack_from_fighting_entries_raw(
                side, entries[side], entries[other], damage[side]
            )
        repairs.append({
            "source_day": day,
            "joined_army_id": joined_army_id,
            "prejoin_active_attacker_army_ids": active,
            "hypothetical_attacker_army_ids": active + [joined_army_id],
            "prejoin_saved_regiment_count": len(before),
            "prejoin_fighting_regiment_count": sum(r.fights_in_main_phase for r in joined[0].regiments),
            "native_r14_raw": native,
            "predicted_r14_raw": predictions,
            "delta_raw": {side: predictions[side] - native[side] for side in native},
            "source_checkpoint_sha256": digest(raw_save),
            "melted_save_sha256": digest(melted),
            "prejoin_snapshot_sha256": digest(snapshot_path),
            "prejoin_control_sha256": digest(control_path),
            "same_day_v3_response_sha256": digest(v3_path),
            "source_phase_trace_sha256": digest(trace_path),
            "source_whole_phase_trace_status": source["trace_status"],
        })
    repaired = {row["source_day"]: row for row in repairs}
    exact_sides = 0
    for day, row in by_day.items():
        if day in repaired:
            exact_sides += sum(delta == 0 for delta in repaired[day]["delta_raw"].values())
        else:
            exact_sides += sum(value == "exact" for value in row["side_comparison"].values())
    return {
        "schema": "xar.ck3.episode01.prejoin-counter-r14-parity/v2",
        "game_build": "CK3 1.19.0.6",
        "source_paired_report_sha256": EPISODE01_PAIRED_COUNTER_SHA256,
        "paired_run": str(paired_run.resolve()),
        "prejoin_runs": {str(day): str(path.resolve()) for day, path in prejoin_runs.items()},
        "rakaly_exe_sha256": RAKALY_EXE_SHA256,
        "same_date_hypothetical_prejoin_query_available": True,
        "native_r14_side_comparisons": 46,
        "conditional_exact_r14_side_comparisons": exact_sides,
        "join_day_repairs": repairs,
        "conditioned_on": [
            "observed_join_timing", "native_old_side_current_fighting_raw",
            "native_old_side_effective_damage_raw", "native_prejoin_saved_regiment_current",
        ],
        "join_policy_reconstructed": False,
        "phase_effect_transition_complete": False,
        "advantage_reconstructed": False,
        "whole_battle_win_probability_available": False,
        "planner_usable": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paired-run", type=Path, required=True)
    parser.add_argument("--prejoin-day11", type=Path, required=True)
    parser.add_argument("--prejoin-day21", type=Path, required=True)
    parser.add_argument("--rakaly-exe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = project(args.paired_run, {11: args.prejoin_day11, 21: args.prejoin_day21}, args.rakaly_exe)
    with args.output.open("x", encoding="utf-8", newline="\n") as out:
        json.dump(report, out, ensure_ascii=False, indent=2)
        out.write("\n")
    print(json.dumps({"exact": report["conditional_exact_r14_side_comparisons"],
                      "compared": report["native_r14_side_comparisons"],
                      "sha256": digest(args.output)}))


if __name__ == "__main__":
    main()
