"""Two new hand-expected qualified-knight subset-retreat compositions."""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict, replace
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
    name = "xar_autoplayer.simulation.battle_selected_owner_subset_retreat_12003"
    spec = importlib.util.spec_from_file_location(name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen V62 projection")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    from xar_autoplayer.simulation.battle_current_adapter import (
        CurrentBattleCondition, CurrentBattleEntry, CurrentBattleSide,
        CurrentLossInputs, CurrentLossSideInputs,
    )
    from xar_autoplayer.simulation.battle_current_next_day import CarriedBattleCondition
    from xar_autoplayer.simulation.battle_current_terminal import TerminalBackingRegiment
    from xar_autoplayer.simulation.combat_core import (
        BackingComponent, CombatRegimentState, DrawState, RegimentKind,
    )

    checks = 0
    completed_cases = []

    def require(value: bool, message: str) -> None:
        nonlocal checks
        checks += 1
        if not value:
            raise RuntimeError(message)

    def entry(regiment, army, owner, bucket, index, current, soft, count=3,
              knight=-1, published=-1, main=True, hard=100000, starting=None):
        components = (BackingComponent(max(9, count), count, 0),)
        kind = RegimentKind.LEVY if bucket == "levy" else RegimentKind.MEN_AT_ARMS
        state = CombatRegimentState(regiment, kind, current, soft, 100000, 0, 0, components)
        return CurrentBattleEntry(
            state, bucket, index, army, army+1000000, owner,
            current+soft+(hard or 0) if starting is None else starting,
            100000, main, hard, knight, components,
            {"regiment_id": regiment, "native_carmy_id": army,
             "knight_character_id_raw": published, "death_flag": regiment in (201, 204),
             "fixture_provenance": "explicit_source_composed_conditional_v62"},
        )

    def side(index, entries, armies, ledger):
        return CurrentBattleSide(
            side_index=index, role="attacker" if index == 0 else "defender",
            primary_participant_character_id=29829 if index == 0 else 45678,
            selected_commander_character_id=29829 if index == 0 else 45678,
            current_roll_points=7+index, roll_request=None, entries=entries,
            ordered_armies=tuple({"native_carmy_id": army, "public_cunit_id": army+1000000,
                                  "owner_character_id": owner, "combat_backlink_id": 16777284}
                                 for army, owner in armies),
            stored_current_fighting_raw=sum(row.state.current_raw for row in entries),
            stored_levy_current_fighting_raw=sum(row.state.current_raw for row in entries if row.bucket == "levy"),
            derived_current_fighting_raw=sum(row.state.current_raw for row in entries),
            derived_soft_casualties_raw=sum(row.state.soft_casualties_raw for row in entries),
            derived_main_fighting_entry_hard_casualties_raw=sum(
                row.starting_raw-row.state.current_raw-row.state.soft_casualties_raw
                for row in entries if row.fights_in_main_phase),
            non_main_start_minus_current_minus_soft_raw=sum(
                row.starting_raw-row.state.current_raw-row.state.soft_casualties_raw
                for row in entries if not row.fights_in_main_phase),
            participant_hard_ledger=ledger,
            participant_hard_total_raw=sum(item["hard_casualties_raw"] for item in ledger),
            loss_inputs=None, levy_damage_raw=None, levy_damage_source="new_v62_fixture",
            levy_damage_native_observed=False, levy_damage_primary_participant_character_id=None,
        )

    def carried(selected_entries, armies, ledger):
        opposition = (entry(301, 90100, 45678, "men_at_arms", 0, 900000, 0, count=9),)
        sides = (
            side(0, selected_entries, armies, ledger),
            side(1, opposition, ((90100, 45678),),
                 ({"participant_character_id": 45678, "hard_casualties_raw": 900000},)),
        )
        loss_sides = (CurrentLossSideInputs(0, 100000, 0, 0, 29829, 100000),
                      CurrentLossSideInputs(1, 100000, 0, 0, 45678, 100000))
        loss = CurrentLossInputs(100000, 16777284, 2610, 100000, 100000,
                                 50000, 50000, False, 0, loss_sides)
        source = {
            "status": "available", "snapshot_revision": 41, "observed_date_raw": 53237136,
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
            snapshot_revision=41, observed_date_raw=53237136, combat_id=16777284,
            province_id=2610, subject_side_index=0, side_scope="new_v62_conditional_fixture",
            phase="main", phase_raw=0, phase_day=9, base_combat_width=20,
            final_combat_width=20, roll_cadence_counter=2,
            base_advantage_raw=0, resolved_advantage_raw=0, sides=sides,
            loss_inputs=loss, active_counter_inputs=None,
            pursuit_modifier_sides={"status": "available", "sides": (
                {"pursuit_efficiency_raw": 0, "retreat_losses_raw": 0},
                {"pursuit_efficiency_raw": 0, "retreat_losses_raw": 0},
            )}, missing_inputs=(), source_snapshot=source,
        )
        return CarriedBattleCondition(
            condition, DrawState(7, 123456789), "caller_conditional_fixture",
            ("v62_source_closed_branch_inputs",), 2,
            {"snapshot_revision": 41, "observed_date_raw": 53237136, "combat_id": 16777284}, (),
        )

    def census(rows_by_army):
        return {army: tuple(TerminalBackingRegiment(army, regiment, count)
                            for regiment, count in rows)
                for army, rows in rows_by_army.items()}

    def frame_unchanged(before, result):
        after = result.carried
        fields = ("snapshot_revision", "observed_date_raw", "combat_id", "province_id",
                  "subject_side_index", "phase", "phase_raw", "phase_day", "roll_cadence_counter")
        require(tuple(getattr(before.condition, key) for key in fields)
                == tuple(getattr(after.condition, key) for key in fields),
                "qualified callback must retain the exact combat and calendar frame")
        require(before.condition.source_snapshot == after.condition.source_snapshot,
                "winner, baselines, global pools, ordinary duration and skip remain unchanged")
        require(before.draw_state == after.draw_state
                and before.simulated_main_ticks == after.simulated_main_ticks
                and before.origin_observed_frame == after.origin_observed_frame,
                "no random draw, main tick or observed-day advancement occurs")
        require(before.condition.sides[1] == after.condition.sides[1], "opposing side is untouched")
        require(result.actual_game_days_advanced == 0 and result.actual_execution_claimed is False
                and result.complete_native_transition is False and result.complete_monte_carlo is False
                and result.win_probability_ready is False,
                "conditional primitive does not claim live execution or complete transition")

    def case_qualified_knight_backing_skip():
        rows = (
            entry(101, 90001, 29829, "levy", 0, 200000, 250000),
            entry(102, 90003, 34567, "levy", 1, 500000, 0, count=5),
            entry(103, 90002, 29829, "levy", 2, 175000, 225000),
            entry(201, 90001, 29829, "men_at_arms", 0, 300000, 350000,
                  count=7, knight=55555, published=55555),
            entry(202, 90002, 29829, "men_at_arms", 1, 100000, 275000,
                  count=6, knight=66666, published=66666, main=False, hard=None, starting=500000),
            entry(203, 90003, 34567, "men_at_arms", 2, 400000, 0, count=4),
        )
        before = carried(rows, ((90001, 29829), (90003, 34567), (90002, 29829)), (
            {"participant_character_id": 29829, "hard_casualties_raw": 500000},
            {"participant_character_id": 34567, "hard_casualties_raw": 700000},
        ))
        backing = census({90001: ((101, 3), (201, 1), (1999, 11)),
                          90002: ((103, 3), (202, 1), (2999, 7)),
                          90003: ((102, 5), (203, 4), (3999, 13)),
                          90100: ((301, 9), (3099, 17))})
        original, original_backing = deepcopy(before), deepcopy(backing)
        inputs = module.selected_owner_pursuit_inputs_from_current_condition_12003(before.condition, selected_side_index=0)
        qualifications = inputs.knight_backing_qualifications_by_regiment
        require(qualifications[(90001, 201)].knight_getter_result is True
                and qualifications[(90002, 202)].knight_getter_result is True,
                "actual helper derives true from explicit same-frame qualified MAA producer-shaped records")
        require(qualifications[(90003, 203)].knight_getter_result is False
                and qualifications[(90001, 201)].source_context["kind"] == "current_bucket_qualified_knight_binding",
                "native-empty false and qualified current provenance remain distinct")
        require(inputs.pursuit_stat_multiplier_raw == 0 and inputs.minimum_pursuit_multiplier_raw == 0
                and inputs.pursuit_hard_conversion_raw == 50000
                and inputs.source_context["duration_divisor"] == 1
                and inputs.source_context["global_pools_or_skip_flag_copied"] is False,
                "subset uses supplied exact coefficients and duration one")
        event = module.AdmittedSelectedOwnerRetreat12003(16777284, 0, (29829,), 2727, True, {29829: inputs})
        result = module.apply_selected_owner_subset_retreats_12003(before, (event,), backing_by_army=backing)
        require(result.status == "available" and result.typed_gaps == (), "qualified and ordinary supplied callback is available")
        require(before == original and backing == original_backing, "caller input records remain unchanged")
        detail = result.event_ledger[0]
        require(detail["owner_character_id"] == 29829 and detail["duration_divisor"] == 1,
                "selected identity remains the full owner rather than an ArmyID")
        require(tuple(row.state.regiment_id for row in detail["copied_entries_before"]) == (103, 101, 202, 201),
                "native temporary copy order is reverse levy followed by reverse MAA")
        require(detail["selected_soft_raw_by_bucket"] == {"levy": 475000, "men_at_arms": 625000},
                "selected pools are not ordinary global pools")
        budgets = {row.kind.value: row for row in detail["numeric_domains"]}
        require((budgets["levy"].current_soft_raw, budgets["levy"].hard_raw) == (475000, 237500)
                and (budgets["men_at_arms"].current_soft_raw, budgets["men_at_arms"].hard_raw) == (625000, 312500),
                "each domain's hand conversion uses the selected pool with divisor one")
        require(detail["new_hard_casualties_raw"] == 550000 and detail["owner_hard_delta_raw"] == 550000,
                "qualified early return does not suppress copied/H58 logical attribution")
        writebacks = {row["regiment_id"]: row for row in detail["backing_writebacks"]}
        require({regiment: row["new_hard_casualties_raw"] for regiment, row in writebacks.items()}
                == {101: 125000, 103: 112500, 201: 175000, 202: 137500},
                "ordinary and qualified copied hard deltas match hand arithmetic")
        copied_before = {row.state.regiment_id: row for row in detail["copied_entries_before"]}
        copied_after = {row.state.regiment_id: row for row in detail["copied_entries_after"]}
        require({regiment: row.state.soft_casualties_raw for regiment, row in copied_after.items()}
                == {101: 125000, 103: 112500, 201: 175000, 202: 137500},
                "every copied soft decreases by exactly the converted hard raw")
        require(all(copied_after[regiment].state.current_raw == row.state.current_raw
                    and copied_after[regiment].starting_raw == row.starting_raw
                    and copied_after[regiment].knight_character_id_raw == row.knight_character_id_raw
                    and copied_after[regiment].source_entry == row.source_entry
                    for regiment, row in copied_before.items()),
                "copied current, starting, character identity and source metadata remain")
        require(all(copied_after[regiment].state.components == copied_before[regiment].state.components
                    and copied_after[regiment].backing_components == copied_before[regiment].backing_components
                    for regiment in (201, 202)), "qualified components seven/six are untouched")
        require(tuple(row.current_soldiers for row in copied_after[101].state.components) == (2,)
                and tuple(row.current_soldiers for row in copied_after[103].state.components) == (2,),
                "ordinary components receive one integer loss each")
        require(all(writebacks[regiment]["backing_hard_apply_invoked"] is True
                    and writebacks[regiment]["qualified_knight_backing_early_return"] is True
                    and writebacks[regiment]["regular_backing_call_selected"] is False
                    and writebacks[regiment]["backing_reaggregation_called"] is False
                    and writebacks[regiment]["whole_current_soldiers_after"] == 1
                    for regiment in (201, 202)),
                "qualified native hard call skips all backing writers and count recomputation")
        require(all(writebacks[regiment]["native_write_order"] == (
                    "qualified_knight_backing_hard_return", "copied_soft_decrease", "existing_owner_H58_increment")
                    and writebacks[regiment]["owner_ledger_is_second_whole_debit"] is False
                    for regiment in (201, 202)), "qualified return still precedes copied soft and owner H58 writes")
        require(all(writebacks[regiment]["regular_backing_call_selected"] is True
                    and writebacks[regiment]["backing_reaggregation_called"] is True
                    for regiment in (101, 103)), "ordinary hard branch alone mutates components and reaggregates")
        require(copied_after[202].hard_casualties_raw is None
                and copied_after[202].starting_raw-copied_after[202].state.current_raw-copied_after[202].state.soft_casualties_raw == 262500,
                "non-main explicit hard stays null while known residual increases by 137500")
        require(copied_after[201].source_entry["death_flag"] is True,
                "death flag does not invalidate the supplied qualified binding or cause a separate deletion")
        require(detail["removed_native_carmy_ids"] == (90002, 90001)
                and all(row["combat_backlink_id"] == -1 for row in detail["removed_armies_in_reverse_native_order"]),
                "native Army removal order and explicit departed backlink clear remain")
        require(detail["cached_current_debit_raw"] == 775000 and detail["cached_levy_current_debit_raw"] == 375000
                and detail["retained_rows_redebited"] is False,
                "membership uses the original selected current and is debited once")
        retained = result.carried.condition.sides[0]
        require(retained.entries == (replace(rows[1], bucket_index=0), replace(rows[5], bucket_index=0))
                and tuple(row["native_carmy_id"] for row in retained.ordered_armies) == (90003,),
                "retained allied rows and native Army survive unchanged except bucket reindex")
        require(retained.stored_current_fighting_raw == 900000 and retained.stored_levy_current_fighting_raw == 500000,
                "retained cache membership matches only the ally")
        require(retained.participant_hard_ledger == (
            {"participant_character_id": 29829, "hard_casualties_raw": 1050000},
            {"participant_character_id": 34567, "hard_casualties_raw": 700000},
        ) and retained.participant_hard_total_raw == 1750000, "existing selected H58 increments once and ally H58 is retained")
        whole = {army: tuple((row.regiment_id, row.current_soldiers) for row in values)
                 for army, values in result.backing_by_army.items()}
        require(whole[90001] == ((101, 2), (201, 1), (1999, 11))
                and whole[90002] == ((103, 2), (202, 1), (2999, 7)),
                "qualified whole census stays one and unreferenced full-Army regiments remain")
        require(result.backing_by_army[90003] == backing[90003] and result.backing_by_army[90100] == backing[90100],
                "nonselected whole backing is untouched")
        require(sum(row.current_soldiers for army in (90001, 90002) for row in backing[army])
                - sum(row.current_soldiers for army in (90001, 90002) for row in result.backing_by_army[army]) == 2,
                "logical raw550000 and H58 are not a second whole debit")
        require(tuple(result.departed_backing_by_army) == (90002, 90001)
                and result.departed_backing_by_army[90001] == result.backing_by_army[90001],
                "departed complete backing follows actual reverse Army removal")
        require(tuple(row.regiment_id for row in result.retained_backing_by_side[0]) == (102, 203, 3999),
                "retained full census includes the regiment absent from CombatEntry")
        frame_unchanged(before, result)
        return {"case": "qualified_knight_backing_skip", "status": "GREEN",
                "copy_order": [103, 101, 202, 201], "reverse_army_removal": [90002, 90001],
                "selected_soft_raw": {"levy": 475000, "men_at_arms": 625000},
                "logical_hard_delta_raw": 550000, "ordinary_whole_loss": 2,
                "qualified_component_counts_after": [7, 6], "qualified_whole_counts_after": [1, 1],
                "typed_gaps": []}

    def case_ordered_zero_false_then_unknown():
        rows = (
            entry(101, 90001, 29829, "levy", 0, 200000, 250000),
            entry(102, 90003, 34567, "levy", 1, 500000, 0, count=5),
            entry(104, 90004, 67890, "levy", 2, 250000, 0),
            entry(201, 90001, 29829, "men_at_arms", 0, 300000, 300000, knight=55555, published=None),
            entry(203, 90003, 34567, "men_at_arms", 1, 400000, 0, count=4, knight=66666, published=None),
            entry(204, 90004, 67890, "men_at_arms", 2, 100000, 400000, count=7, knight=77777, published=None),
        )
        before = carried(rows, ((90001, 29829), (90003, 34567), (90004, 67890)), (
            {"participant_character_id": 29829, "hard_casualties_raw": 500000},
            {"participant_character_id": 34567, "hard_casualties_raw": 700000},
            {"participant_character_id": 67890, "hard_casualties_raw": 900000},
        ))
        backing = census({90001: ((101, 3), (201, 3), (1999, 11)),
                          90003: ((102, 5), (203, 1), (3999, 13)),
                          90004: ((104, 3), (204, 1), (4999, 17)),
                          90100: ((301, 9), (3099, 17))})
        adapter = module.selected_owner_pursuit_inputs_from_current_condition_12003(before.condition, selected_side_index=0)
        require(adapter.knight_backing_qualifications_by_regiment[(90001, 201)].knight_getter_result is None
                and adapter.knight_backing_qualifications_by_regiment[(90004, 204)].knight_getter_result is None,
                "raw positive IDs with absent qualified publication do not prove true or false")
        false_map = dict(adapter.knight_backing_qualifications_by_regiment)
        false_map[(90001, 201)] = module.KnightBackingHardQualification12003(
            False, {"kind": "caller_conditional_2634880_false", "reason": "full-ID qualification fails in explicit scenario"})
        false_inputs = replace(adapter, knight_backing_qualifications_by_regiment=false_map)
        unknown_map = dict(adapter.knight_backing_qualifications_by_regiment)
        unknown_map[(90004, 204)] = module.KnightBackingHardQualification12003(None, {"kind": "caller_qualification_unknown"})
        unknown_inputs = replace(adapter, knight_backing_qualifications_by_regiment=unknown_map)
        event = module.AdmittedSelectedOwnerRetreat12003(
            16777284, 0, (34567, 29829, 67890), 2727, True,
            {29829: false_inputs, 67890: unknown_inputs}, {"kind": "explicit_conditional_callback_order"})
        result = module.apply_selected_owner_subset_retreats_12003(before, (event,), backing_by_army=backing)
        require(result.status == "partial" and len(result.event_ledger) == 3,
                "completed zero and false callbacks coexist with an uninstalled unknown callback")
        zero, explicit_false, unknown = result.event_ledger
        require(tuple(row["owner_character_id"] for row in result.event_ledger) == (34567, 29829, 67890)
                and tuple(row["owner_index"] for row in result.event_ledger) == (0, 1, 2),
                "actual supplied owner tuple order is retained")
        require(zero["branch"] == "no_soft_toughness" and zero["installed"] is True
                and zero["new_hard_casualties_raw"] == 0 and zero["backing_writebacks"] == (),
                "zero-soft occupied callback needs neither witness nor numeric context")
        require(zero["removed_native_carmy_ids"] == (90003,) and zero["cached_current_debit_raw"] == 900000,
                "zero-loss callback still performs its admitted membership removal")
        require(explicit_false["installed"] is True and explicit_false["new_hard_casualties_raw"] == 275000,
                "explicit false occupied predicate uses supplied ordinary hard conversion")
        false_writes = {row["regiment_id"]: row for row in explicit_false["backing_writebacks"]}
        require(false_writes[201]["new_hard_casualties_raw"] == 150000
                and false_writes[201]["regular_backing_call_selected"] is True
                and false_writes[201]["qualified_knight_backing_early_return"] is False
                and false_writes[201]["backing_reaggregation_called"] is True
                and false_writes[201]["knight_backing_qualification_source"]["kind"] == "caller_conditional_2634880_false",
                "false witness and positive occupied ID are different inputs with explicit conditional provenance")
        require(tuple((row.regiment_id, row.current_soldiers) for row in result.backing_by_army[90001])
                == ((101, 2), (201, 2), (1999, 11)),
                "false branch ordinary backing debit occurs once for each row")
        require(unknown["branch"] == "knight_backing_qualification_unavailable"
                and unknown["installed"] is False and unknown["new_hard_casualties_raw"] is None,
                "unknown positive qualification installs no speculative loss or membership removal")
        require(len(result.typed_gaps) == 1
                and result.typed_gaps[0].kind == "knight_backing_qualification_unavailable"
                and result.typed_gaps[0].owner_index == 2 and result.typed_gaps[0].owner_character_id == 67890,
                "one exact typed qualification gap preserves its callback coordinates")
        retained = result.carried.condition.sides[0]
        require(retained.entries == (replace(rows[2], bucket_index=0), replace(rows[5], bucket_index=0)),
                "unknown callback retains its logical rows and components without a death-flag deletion")
        require(retained.entries[1].source_entry["death_flag"] is True
                and retained.entries[1].knight_character_id_raw == 77777,
                "death metadata and occupied identity alone neither qualify nor delete")
        require(retained.ordered_armies == (before.condition.sides[0].ordered_armies[2],)
                and retained.ordered_armies[0]["combat_backlink_id"] == 16777284,
                "uninstalled owner's Army and backlink remain")
        require(retained.stored_current_fighting_raw == 350000
                and retained.stored_levy_current_fighting_raw == 250000,
                "membership caches include only completed callback debits")
        require(retained.participant_hard_ledger == (
            {"participant_character_id": 29829, "hard_casualties_raw": 775000},
            {"participant_character_id": 34567, "hard_casualties_raw": 700000},
            {"participant_character_id": 67890, "hard_casualties_raw": 900000},
        ) and retained.participant_hard_total_raw == 2375000,
                "only the explicit false callback increments H58; zero and unknown keep existing rows")
        require(result.backing_by_army[90003] == backing[90003]
                and result.backing_by_army[90004] == backing[90004]
                and result.backing_by_army[90100] == backing[90100],
                "zero, uninstalled unknown and opposing whole census are unchanged")
        require(tuple(result.departed_backing_by_army) == (90003, 90001)
                and tuple(row.regiment_id for row in result.retained_backing_by_side[0]) == (104, 204, 4999),
                "completed departure order and retained independent full census are preserved")
        frame_unchanged(before, result)
        return {"case": "ordered_zero_false_then_unknown", "status": "GREEN",
                "callback_order": [34567, 29829, 67890], "zero_hard_raw": 0,
                "false_hard_raw": 275000, "unknown_hard_raw": None,
                "false_whole_loss": 2, "typed_gaps": [asdict(gap) for gap in result.typed_gaps]}

    report = {"schema": "battle-selected-owner-knight-retreat-v62-focused/v1",
              "status": "RED", "readiness": "source-ready", "case_count": 2,
              "game": 0, "SDK": 0, "pipe": 0, "window": 0, "new_days": 0,
              "shared_mutation": 0, "Git": 0, "old_tests": 0, "native_full_build": 0}
    try:
        for case in (case_qualified_knight_backing_skip, case_ordered_zero_false_then_unknown):
            started = checks
            case_result = case()
            case_result["checks"] = checks-started
            completed_cases.append(case_result)
        report.update(status="GREEN", readiness="static-ready")
    except Exception as error:
        report.update(error=f"{type(error).__name__}: {error}", traceback=traceback.format_exc())
    report.update(cases=completed_cases, checks=checks)
    report["dependency_pins"] = []
    for module_name in (
        "xar_autoplayer.simulation.battle_selected_owner_subset_retreat_12003",
        "xar_autoplayer.simulation.battle_current_entry_events_12003",
        "xar_autoplayer.simulation.battle_current_adapter",
        "xar_autoplayer.simulation.battle_current_next_day",
        "xar_autoplayer.simulation.battle_current_terminal",
        "xar_autoplayer.simulation.combat_core",
    ):
        path = Path(sys.modules[module_name].__file__)
        report["dependency_pins"].append({"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="")
    print(json.dumps({"status": report["status"], "case_count": 2, "checks": checks,
                      "receipt": str(args.out), "error": report.get("error")}, indent=2))
    return 0 if report["status"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
