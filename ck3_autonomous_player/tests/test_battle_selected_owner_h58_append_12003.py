"""One new ordered scenario for source-closed missing-owner H58 creation."""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import replace
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import traceback
import types

sys.dont_write_bytecode = True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module-path", type=Path, required=True)
    parser.add_argument("--reference-src", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    module_path = args.module_path.resolve()
    reference_package = args.reference_src / "xar_autoplayer"
    for name, paths in (
        ("xar_autoplayer", [module_path.parents[1], reference_package]),
        ("xar_autoplayer.simulation", [module_path.parent, reference_package / "simulation"]),
    ):
        package = types.ModuleType(name)
        package.__path__ = [str(path) for path in paths]
        sys.modules[name] = package
    module_name = "xar_autoplayer.simulation.battle_selected_owner_subset_retreat_12003"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen V63 projection")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    from xar_autoplayer.simulation.battle_current_adapter import (
        CurrentBattleCondition, CurrentBattleEntry, CurrentBattleSide,
        CurrentLossInputs, CurrentLossSideInputs,
    )
    from xar_autoplayer.simulation.battle_current_next_day import CarriedBattleCondition
    from xar_autoplayer.simulation.battle_current_terminal import TerminalBackingRegiment
    from xar_autoplayer.simulation.combat_core import BackingComponent, CombatRegimentState, DrawState, RegimentKind

    checks = 0

    def require(value: bool, message: str) -> None:
        nonlocal checks
        checks += 1
        if not value:
            raise RuntimeError(message)

    def entry(regiment, army, owner, bucket, index, current, soft, count=3):
        components = (BackingComponent(max(8, count), count, 0),)
        kind = RegimentKind.LEVY if bucket == "levy" else RegimentKind.MEN_AT_ARMS
        state = CombatRegimentState(regiment, kind, current, soft, 100000, 0, 0, components)
        return CurrentBattleEntry(
            state, bucket, index, army, army+1000000, owner,
            current+soft+100000, 100000, True, 100000, -1, components,
            {"regiment_id": regiment, "native_carmy_id": army, "knight_character_id_raw": -1,
             "fixture_provenance": "new_v63_source_composed_conditional"},
        )

    def side(index, rows, armies, ledger):
        return CurrentBattleSide(
            side_index=index, role="attacker" if index == 0 else "defender",
            primary_participant_character_id=29829 if index == 0 else 45678,
            selected_commander_character_id=29829 if index == 0 else 45678,
            current_roll_points=7+index, roll_request=None, entries=rows,
            ordered_armies=tuple({"native_carmy_id": army, "public_cunit_id": army+1000000,
                                  "owner_character_id": owner, "combat_backlink_id": 16777284}
                                 for army, owner in armies),
            stored_current_fighting_raw=sum(row.state.current_raw for row in rows),
            stored_levy_current_fighting_raw=sum(row.state.current_raw for row in rows if row.bucket == "levy"),
            derived_current_fighting_raw=sum(row.state.current_raw for row in rows),
            derived_soft_casualties_raw=sum(row.state.soft_casualties_raw for row in rows),
            derived_main_fighting_entry_hard_casualties_raw=sum(
                row.starting_raw-row.state.current_raw-row.state.soft_casualties_raw for row in rows),
            non_main_start_minus_current_minus_soft_raw=0,
            participant_hard_ledger=ledger,
            participant_hard_total_raw=sum(row["hard_casualties_raw"] for row in ledger),
            loss_inputs=None, levy_damage_raw=None, levy_damage_source="new_v63_fixture",
            levy_damage_native_observed=False, levy_damage_primary_participant_character_id=None,
        )

    def case_missing_owner_creation_trigger_and_reuse():
        hard_zero_owner = 0x0100B26F  # Complete int32 ID; low24 alias 45679 already has a row.
        rows = (
            entry(101, 90001, 29829, "levy", 0, 200000, 325000),
            entry(102, 90003, 34567, "levy", 1, 500000, 0, 5),
            entry(103, 90002, 29829, "levy", 2, 175000, 125000),
            entry(105, 90005, 67890, "levy", 3, 100000, 0, 2),
            entry(201, 90001, 29829, "men_at_arms", 0, 300000, 275000),
            entry(203, 90003, 34567, "men_at_arms", 1, 400000, 0, 4),
            entry(204, 90004, hard_zero_owner, "men_at_arms", 2, 200000, 100000),
        )
        existing = (
            {"row_index": 0, "participant_character_id": 34567, "hard_casualties_raw": 700000,
             "hard_casualties": {"raw": 700000, "scale": 100000}},
            {"row_index": 1, "participant_character_id": 45679, "hard_casualties_raw": 400000,
             "hard_casualties": {"raw": 400000, "scale": 100000}},
        )
        sides = (
            side(0, rows, ((90001, 29829), (90003, 34567), (90002, 29829), (90004, hard_zero_owner), (90005, 67890)), existing),
            side(1, (entry(301, 90100, 45678, "men_at_arms", 0, 900000, 0, 9),),
                 ((90100, 45678),), ({"row_index": 0, "participant_character_id": 45678, "hard_casualties_raw": 900000},)),
        )
        loss_sides = (CurrentLossSideInputs(0, 100000, 0, 0, 29829, 100000),
                      CurrentLossSideInputs(1, 100000, 0, 0, 45678, 100000))
        loss = CurrentLossInputs(100000, 16777284, 2610, 100000, 100000,
                                 50000, 50000, False, 0, loss_sides)
        source = {
            "status": "available", "snapshot_revision": 43, "observed_date_raw": 53237136,
            "combat_id": 16777284, "province_id": 2610, "winner_raw": -1,
            "attacker": {"stored_terminal_loss_baseline_raw": 10000000, "stored_levy_initial_raw": 6000000},
            "defender": {"stored_terminal_loss_baseline_raw": 9000000, "stored_levy_initial_raw": 4000000},
            "current_pursuit_inputs_v1": {
                "losing_side_index": 0, "initial_loser_levy_soft_raw": 9000000,
                "initial_loser_maa_soft_raw": 8000000, "pursuit_phase_days": 7,
                "losing_side_skip_pursuit": True, "pursuit_stat_multiplier_raw": 0,
                "base_toughness_multiplier_raw": 100000, "minimum_pursuit_multiplier_raw": 0,
            },
        }
        condition = CurrentBattleCondition(
            snapshot_revision=43, observed_date_raw=53237136, combat_id=16777284,
            province_id=2610, subject_side_index=0, side_scope="new_v63_conditional_fixture",
            phase="main", phase_raw=0, phase_day=9, base_combat_width=20,
            final_combat_width=20, roll_cadence_counter=2,
            base_advantage_raw=0, resolved_advantage_raw=0, sides=sides,
            loss_inputs=loss, active_counter_inputs=None,
            pursuit_modifier_sides={"status": "available", "sides": (
                {"pursuit_efficiency_raw": 0, "retreat_losses_raw": 0},
                {"pursuit_efficiency_raw": 0, "retreat_losses_raw": 0},
            )}, missing_inputs=(), source_snapshot=source,
        )
        before = CarriedBattleCondition(
            condition, DrawState(7, 123456789), "caller_conditional_fixture",
            ("v63_source_closed_h58_append",), 2,
            {"snapshot_revision": 43, "observed_date_raw": 53237136, "combat_id": 16777284}, (),
        )
        backing = {army: tuple(TerminalBackingRegiment(army, regiment, count) for regiment, count in items)
                   for army, items in {
                       90001: ((101, 3), (201, 3), (1999, 11)), 90002: ((103, 3), (2999, 7)),
                       90003: ((102, 5), (203, 4), (3999, 13)), 90004: ((204, 3), (4999, 5)),
                       90005: ((105, 2), (5999, 6)), 90100: ((301, 9), (3099, 17)),
                   }.items()}
        original, original_backing = deepcopy(before), deepcopy(backing)
        inputs = module.selected_owner_pursuit_inputs_from_current_condition_12003(condition, selected_side_index=0)
        hard_zero_inputs = replace(inputs, pursuit_hard_conversion_raw=0,
                                   source_context={"kind": "explicit_conditional_hard_conversion_zero"})
        event = module.AdmittedSelectedOwnerRetreat12003(
            16777284, 0, (29829, hard_zero_owner, 67890), 2727, True,
            {29829: inputs, hard_zero_owner: hard_zero_inputs}, {"kind": "new_v63_ordered_creation_scenario"})
        result = module.apply_selected_owner_subset_retreats_12003(before, (event,), backing_by_army=backing)
        require(result.status == "available" and result.typed_gaps == (), "source-closed missing-owner case no longer reports the old append gap")
        require(before == original and backing == original_backing, "caller inputs and full census are not mutated")
        require(tuple(row["owner_character_id"] for row in result.event_ledger) == (29829, hard_zero_owner, 67890),
                "explicit callback order governs reached getter order")
        main_owner, hard_zero, soft_zero = result.event_ledger
        require(tuple(row.state.regiment_id for row in main_owner["copied_entries_before"]) == (103, 101, 201),
                "new owner's writer order is reverse levy then MAA")
        require(main_owner["selected_soft_raw_by_bucket"] == {"levy": 450000, "men_at_arms": 275000}
                and main_owner["duration_divisor"] == 1 and main_owner["new_hard_casualties_raw"] == 362500,
                "hand hard result uses selected pools and divisor one")
        writers = main_owner["owner_hard_writebacks_in_native_order"]
        require(len(writers) == 3 and tuple(row["row_index"] for row in writers) == (2, 2, 2)
                and tuple(row["participant_character_id"] for row in writers) == (29829, 29829, 29829),
                "all three copied writers target one full-owner tail row")
        require(tuple(row["row_created"] for row in writers) == (True, False, False)
                and tuple(row["initialized_hard_raw"] for row in writers) == (0, None, None),
                "first getter initializes once; subsequent getters reuse without reset")
        require(tuple(row["delta_raw"] for row in writers) == (62500, 162500, 137500)
                and tuple(row["hard_before_raw"] for row in writers) == (0, 62500, 225000)
                and tuple(row["hard_after_raw"] for row in writers) == (62500, 225000, 362500),
                "source caller applies each raw delta exactly once in numerical order")
        require(all(row["native_getter"] == "264EA10" and row["first_matching_full_key"] is True
                    and row["backing_debited_by_owner_ledger"] is False for row in writers),
                "find/append uses full key and owner attribution adds no backing loss")
        writes = main_owner["backing_writebacks"]
        require(tuple(row["owner_hard_writeback"] for row in writes) == writers
                and all(row["owner_hard_getter_called"] is True for row in writes),
                "each reached soft-positive row has one getter/writeback record")
        require(tuple(row["native_write_order"][2] for row in writes) == (
            "new_owner_H58_initialize_append_and_increment", "existing_owner_H58_increment", "existing_owner_H58_increment"),
                "append occurs after backing/copied updates and only on the first writer")
        after_rows = {row.state.regiment_id: row for row in main_owner["copied_entries_after"]}
        require({regiment: row.state.soft_casualties_raw for regiment, row in after_rows.items()}
                == {101: 162500, 103: 62500, 201: 137500}, "logical copied soft follows the converted hard delta")
        require({regiment: row.state.components[0].current_soldiers for regiment, row in after_rows.items()}
                == {101: 2, 103: 3, 201: 2}, "ordinary integer losses are one, zero, one")
        require(all(row.state.current_raw == next(old.state.current_raw for old in rows if old.state.regiment_id == regiment)
                    for regiment, row in after_rows.items()), "append does not alter copied current")
        zero_writers = hard_zero["owner_hard_writebacks_in_native_order"]
        require(hard_zero["new_hard_casualties_raw"] == 0 and len(zero_writers) == 1
                and zero_writers[0]["row_index"] == 3 and zero_writers[0]["row_created"] is True
                and zero_writers[0]["participant_character_id"] == hard_zero_owner
                and zero_writers[0]["initialized_hard_raw"] == 0
                and zero_writers[0]["hard_before_raw"] == 0 and zero_writers[0]["delta_raw"] == 0
                and zero_writers[0]["hard_after_raw"] == 0,
                "positive soft with hard zero still creates the next zero account")
        require(hard_zero["backing_writebacks"][0]["owner_hard_getter_called"] is True
                and hard_zero["copied_entries_after"][0].state.soft_casualties_raw == 100000
                and result.backing_by_army[90004] == backing[90004],
                "hard-zero getter changes neither soft nor independent whole backing")
        require(soft_zero["branch"] == "no_soft_toughness" and soft_zero["new_hard_casualties_raw"] == 0
                and soft_zero["owner_hard_writebacks_in_native_order"] == ()
                and soft_zero["backing_writebacks"] == (), "soft zero has no getter and no created row")
        retained = result.carried.condition.sides[0]
        require(retained.participant_hard_ledger[:2] == existing, "existing row indexes, order and metadata are unchanged")
        require(retained.participant_hard_ledger[2:] == (
            {"row_index": 2, "participant_character_id": 29829, "hard_casualties_raw": 362500},
            {"row_index": 3, "participant_character_id": hard_zero_owner, "hard_casualties_raw": 0},
        ), "new query-shaped rows append in actual getter order with no auxiliary wire fields")
        require(tuple(row["participant_character_id"] for row in retained.participant_hard_ledger)
                == (34567, 45679, 29829, hard_zero_owner) and retained.participant_hard_total_raw == 1462500,
                "two new accounts preserve prior total plus one logical loss; soft-zero owner is absent")
        require(retained.entries == (replace(rows[1], bucket_index=0), replace(rows[5], bucket_index=0))
                and tuple(row["native_carmy_id"] for row in retained.ordered_armies) == (90003,),
                "only explicitly selected owner memberships leave, with ally retained")
        require(main_owner["removed_native_carmy_ids"] == (90002, 90001)
                and hard_zero["removed_native_carmy_ids"] == (90004,)
                and soft_zero["removed_native_carmy_ids"] == (90005,),
                "departure order follows the existing reverse native Army lists")
        require(retained.stored_current_fighting_raw == 900000 and retained.stored_levy_current_fighting_raw == 500000,
                "append accounting does not add a membership debit")
        require(tuple((row.regiment_id, row.current_soldiers) for row in result.backing_by_army[90001])
                == ((101, 2), (201, 2), (1999, 11))
                and result.backing_by_army[90002] == backing[90002],
                "independent whole census receives exactly the component integer losses")
        require(sum(row.current_soldiers for army in (90001, 90002) for row in backing[army])
                - sum(row.current_soldiers for army in (90001, 90002) for row in result.backing_by_army[army]) == 2,
                "logical raw362500 and append/H58 do not become a second whole debit")
        require(all(result.backing_by_army[army] == backing[army] for army in (90003, 90004, 90005, 90100)),
                "unrelated, zero-hard and zero-soft complete whole census remain")
        require(tuple(result.departed_backing_by_army) == (90002, 90001, 90004, 90005)
                and tuple(row.regiment_id for row in result.retained_backing_by_side[0]) == (102, 203, 3999),
                "complete backing includes regiments absent from CombatEntry")
        frame_fields = ("snapshot_revision", "observed_date_raw", "combat_id", "province_id", "phase", "phase_raw", "phase_day")
        require(tuple(getattr(condition, field) for field in frame_fields)
                == tuple(getattr(result.carried.condition, field) for field in frame_fields),
                "combat/calendar frame remains exact")
        require(result.carried.condition.source_snapshot == condition.source_snapshot,
                "winner, initial baselines and unrelated global inputs remain")
        require(result.carried.draw_state == before.draw_state
                and result.carried.simulated_main_ticks == before.simulated_main_ticks
                and result.carried.origin_observed_frame == before.origin_observed_frame,
                "no draw, main tick or observed-day carry occurs")
        require(result.carried.condition.sides[1] == condition.sides[1], "opposing side remains unchanged")
        require(result.actual_game_days_advanced == 0 and result.actual_execution_claimed is False
                and result.complete_native_transition is False and result.win_probability_ready is False,
                "this conditional primitive claims no live execution or full transition")
        return {"case": "missing_owner_creation_trigger_and_reuse", "status": "GREEN",
                "callback_order": [29829, hard_zero_owner, 67890], "new_row_owners": [29829, hard_zero_owner],
                "new_row_indexes": [2, 3], "new_row_hard_raw": [362500, 0],
                "main_owner_writer_deltas_raw": [62500, 162500, 137500],
                "main_owner_writer_after_raw": [62500, 225000, 362500],
                "logical_hard_delta_raw": 362500, "whole_soldier_loss": 2,
                "final_owner_ledger": retained.participant_hard_ledger, "typed_gaps": []}

    report = {"schema": "battle-selected-owner-h58-append-v63-focused/v1",
              "status": "RED", "readiness": "source-ready", "case_count": 1, "cases": [],
              "game": 0, "SDK": 0, "pipe": 0, "window": 0, "new_days": 0,
              "shared_mutation": 0, "Git": 0, "old_tests": 0, "native_full_build": 0}
    try:
        case = case_missing_owner_creation_trigger_and_reuse()
        case["checks"] = checks
        report.update(status="GREEN", readiness="static-ready", cases=[case])
    except Exception as error:
        report.update(error=f"{type(error).__name__}: {error}", traceback=traceback.format_exc())
    report["checks"] = checks
    report["dependency_pins"] = []
    for name in (
        "xar_autoplayer.simulation.battle_selected_owner_subset_retreat_12003",
        "xar_autoplayer.simulation.battle_current_entry_events_12003",
        "xar_autoplayer.simulation.battle_current_adapter",
        "xar_autoplayer.simulation.battle_current_next_day",
        "xar_autoplayer.simulation.battle_current_terminal",
        "xar_autoplayer.simulation.combat_core",
    ):
        path = Path(sys.modules[name].__file__)
        report["dependency_pins"].append({"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="")
    print(json.dumps({"status": report["status"], "case_count": 1, "checks": checks,
                      "receipt": str(args.out), "error": report.get("error")}, indent=2))
    return 0 if report["status"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
