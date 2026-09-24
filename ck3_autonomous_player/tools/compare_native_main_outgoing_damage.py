"""Compare agent main damage scaling with one native independent replay.

The comparison is conditional on native post-counter attack and native advantage.
Observed same-day join rosters and width refreshes are supplied as inputs. This
does not independently forecast damage, battle outcome, or win probability.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
from xar_autoplayer.simulation.combat_core import (  # noqa: E402
    FIXED_SCALE,
    advantage_damage_multiplier_raw,
    outgoing_damage_raw,
    update_combat_width,
)
from xar_autoplayer.simulation.native_battle_case import (  # noqa: E402
    EPISODE01_CASE_SHA256,
    EPISODE01_JOIN_DAY_SHA256,
    load_episode01_join_day_casualties,
    load_episode01_native_battle_case,
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def receipt(path: Path, expected: str) -> dict:
    if sha(path) != expected:
        raise ValueError(f"native receipt SHA drift: {path}")
    envelope = json.loads(path.read_text(encoding="utf-8"))
    if envelope.get("result") != "CALL_COMPLETED":
        raise ValueError(f"native receipt incomplete: {path}")
    return envelope["body"]


def control_path(root: Path, day: int) -> Path:
    return root / ("day04-control.json" if day == 4 else f"trace-d{day:02d}-before-control.json")


def finish_path(root: Path, day: int) -> Path:
    return root / ("day04-finish.json" if day == 4 else f"trace-d{day:02d}-finish.json")


def terrain_width(game_root: Path) -> tuple[int, dict]:
    province_path = game_root / "common" / "province_terrain" / "00_province_terrain.txt"
    terrain_path = game_root / "common" / "terrain_types" / "00_terrains.txt"
    expected_province = "922A5B8BA73007B18E95F1CCFCDBE075A03F5DE61CBF8FF8F66698BEDBB3BE3C"
    expected_terrain = "39D79AD120BF85B49D6EE8D96FE4D94EDBBABC190A41662DBA8ECA8DE0ACE64E"
    if sha(province_path) != expected_province or sha(terrain_path) != expected_terrain:
        raise ValueError("exact-build province/terrain source SHA drift")
    provinces = province_path.read_text(encoding="utf-8-sig")
    terrains = terrain_path.read_text(encoding="utf-8-sig")
    if re.search(r"^2633=forest\s*$", provinces, re.M) is None:
        raise ValueError("Messina province 2633 is not stock forest")
    forest = re.search(r"^forest\s*=\s*\{(.*?)^\}", terrains, re.M | re.S)
    if forest is None or re.search(r"^\s*combat_width\s*=\s*0\.9\s*$", forest.group(1), re.M) is None:
        raise ValueError("stock forest combat width is not 0.9")
    return 90000, {
        "province_terrain_source_sha256": expected_province,
        "terrain_types_source_sha256": expected_terrain,
        "battle_province_id": 2633,
        "battle_terrain_key": "forest",
    }


def compare(trace_root: Path, game_root: Path) -> dict:
    case = load_episode01_native_battle_case()
    joins = load_episode01_join_day_casualties()
    terrain_multiplier, terrain_proof = terrain_width(game_root)
    by_day = {row["source_day"]: row for row in case["phase_traces"]}
    join_by_day = {row["source_day"]: row for row in joins["join_observations"]}
    root = trace_root / "ck3-output" / "interactive-requests-responses"
    days = []
    previous_base_width = 0
    for day in range(4, 27):
        control_file = control_path(root, day)
        finish_file = finish_path(root, day)
        control = receipt(control_file, by_day[day]["control_receipt_sha256"])["battle_control_snapshot"]
        trace = receipt(finish_file, by_day[day]["finish_receipt_sha256"])["managed_trace"]["trace"]
        if (control["combat_id"] != case["combat_id"]
                or control["phase"] != "main"
                or trace["post_counter_attack"]["count"] != 2
                or trace["outgoing_damage"]["count"] != 2):
            raise ValueError(f"day {day}: native main input identity mismatch")
        advantage_record = trace["records"][1]
        if (advantage_record["capture_failure_flags"] != 0
                or advantage_record["native_date_raw"] != control["observed_date_raw"]
                or advantage_record["boundary"] != "native_capture_after_side1_schedule_return_0x27FB5AC"):
            raise ValueError(f"day {day}: valid same-date advantage record missing")
        raw_advantage = advantage_record["resolved_advantage_raw"]
        if raw_advantage % FIXED_SCALE != 0:
            raise ValueError(f"day {day}: nonintegral native advantage unsupported")
        advantage = raw_advantage // FIXED_SCALE
        joined_fighting_raw = 0
        target_receipt_sha = None
        native_width = control["final_combat_width"]
        native_base_width = control["base_combat_width"]
        if day in join_by_day:
            joined_fighting_raw = sum(
                row["prejoin_saved_current_raw"] for row in join_by_day[day]["regiments"]
                if row["fights_in_main_phase"]
            )
            arrival_day = join_by_day[day]["arrival_day"]
            target_file = control_path(root, arrival_day)
            target_receipt_sha = by_day[arrival_day]["control_receipt_sha256"]
            target = receipt(target_file, target_receipt_sha)["battle_control_snapshot"]
            if target["combat_id"] != case["combat_id"]:
                raise ValueError(f"day {day}: arrival width identity mismatch")
            native_width = target["final_combat_width"]
            native_base_width = target["base_combat_width"]
        side_0_fighting = control["attacker"]["derived_current_fighting_raw"] + joined_fighting_raw
        side_1_fighting = control["defender"]["derived_current_fighting_raw"]
        base_width, width = update_combat_width(
            side_0_fighting, side_1_fighting,
            previous_base_width=previous_base_width,
            terrain_width_multiplier_raw=terrain_multiplier,
        )
        if (base_width, width) != (native_base_width, native_width):
            raise ValueError(f"day {day}: native combat width mismatch")
        previous_base_width = base_width
        sides = []
        for side_index in (0, 1):
            native_post_counter = trace["post_counter_attack"][f"side{side_index}_raw"]
            native_outgoing = trace["outgoing_damage"][f"side{side_index}_raw"]
            fighting = side_0_fighting if side_index == 0 else side_1_fighting
            has_advantage = (side_index == 0 and advantage > 0) or (side_index == 1 and advantage < 0)
            multiplier = advantage_damage_multiplier_raw(abs(advantage)) if has_advantage else FIXED_SCALE
            predicted = outgoing_damage_raw(
                native_post_counter,
                advantage_multiplier_raw=multiplier,
                final_combat_width=width,
                side_current_fighting_men_raw=fighting,
            )
            sides.append({
                "side_index": side_index,
                "native_post_counter_attack_raw": native_post_counter,
                "native_advantage_multiplier_raw": multiplier,
                "current_fighting_men_before_damage_raw": fighting,
                "native_outgoing_damage_raw": native_outgoing,
                "agent_outgoing_damage_raw": predicted,
                "agent_minus_native_raw": predicted - native_outgoing,
            })
        days.append({
            "source_day": day,
            "control_receipt_sha256": sha(control_file),
            "finish_receipt_sha256": sha(finish_file),
            "arrival_control_receipt_sha256": target_receipt_sha,
            "phase_trace_status": by_day[day]["status"],
            "advantage_record_index": 1,
            "advantage_record_capture_failure_flags": 0,
            "resolved_advantage_raw": raw_advantage,
            "computed_base_combat_width": base_width,
            "computed_final_combat_width": width,
            "native_base_combat_width": native_base_width,
            "native_final_combat_width": native_width,
            "combat_width_exact": True,
            "observed_joined_fighting_men_raw": joined_fighting_raw,
            "sides": sides,
            "both_sides_exact": all(row["agent_minus_native_raw"] == 0 for row in sides),
        })
    return {
        "schema": "ck3-native-main-outgoing-conditional-parity-v2",
        "case_sha256": EPISODE01_CASE_SHA256,
        "join_evidence_sha256": EPISODE01_JOIN_DAY_SHA256,
        "game_version": case["game_version"],
        "combat_id": case["combat_id"],
        "trajectory": case["phase_trace_trajectory"],
        "terrain_width_multiplier_raw": terrain_multiplier,
        **terrain_proof,
        "source_days": days,
        "native_outgoing_values_compared": len(days) * 2,
        "exact_outgoing_values": sum(
            row["agent_minus_native_raw"] == 0 for day in days for row in day["sides"]
        ),
        "conditioned_on_native_post_counter_attack": True,
        "conditioned_on_native_advantage": True,
        "conditioned_on_observed_joined_roster": True,
        "conditioned_on_stock_terrain_width": True,
        "post_counter_attack_reconstructed": False,
        "advantage_reconstructed": False,
        "join_policy_reconstructed": False,
        "width_formula_reconstructed_from_observed_join_timing": True,
        "width_update_timing_reconstructed": False,
        "whole_battle_win_probability_available": False,
        "planner_usable": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace-root", type=Path, required=True)
    parser.add_argument("--game-root", type=Path, required=True,
                        help="Exact-build CK3 game directory containing common/")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f"refusing to overwrite comparison: {args.output}")
    result = compare(args.trace_root.resolve(), args.game_root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "sha256": sha(args.output),
                      "exact": result["exact_outgoing_values"],
                      "compared": result["native_outgoing_values_compared"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
