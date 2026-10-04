"""Two hand-expected selected-owner retreat compositions; no game transport."""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict, replace
import hashlib
import importlib
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
    package_root = args.reference_src / "xar_autoplayer"
    producer_package = module_path.parents[1]
    for name, paths in (
        ("xar_autoplayer", [producer_package, package_root]),
        ("xar_autoplayer.simulation", [module_path.parent, package_root / "simulation"]),
    ):
        namespace = types.ModuleType(name)
        namespace.__path__ = [str(path) for path in paths]
        sys.modules[name] = namespace
    name = "xar_autoplayer.simulation.battle_selected_owner_subset_retreat_12003"
    spec = importlib.util.spec_from_file_location(name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("frozen producer module import failed")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    from xar_autoplayer.simulation.battle_current_adapter import (
        CurrentBattleCondition, CurrentBattleEntry, CurrentBattleSide,
        CurrentLossInputs, CurrentLossSideInputs,
    )
    from xar_autoplayer.simulation.battle_current_next_day import CarriedBattleCondition
    from xar_autoplayer.simulation.battle_current_terminal import TerminalBackingRegiment
    from xar_autoplayer.simulation.combat_core import BackingComponent, CombatRegimentState, DrawState, RegimentKind

    checks = 0
    cases = []

    def require(value: bool, message: str) -> None:
        nonlocal checks
        checks += 1
        if not value:
            raise RuntimeError(message)

    def entry(regiment, army, owner, bucket, index, current, soft,
              *, main=True, starting=None, hard=100000, count=3, knight=-1):
        kind = RegimentKind.LEVY if bucket == "levy" else RegimentKind.MEN_AT_ARMS
        components = (BackingComponent(max(8, count), count, 0),)
        state = CombatRegimentState(regiment, kind, current, soft, 100000, 0, 0, components)
        return CurrentBattleEntry(
            state, bucket, index, army, army + 1000000, owner,
            current + soft + (hard or 0) if starting is None else starting,
            100000, main, hard, knight, components,
            {"fixture": "v61-native-composed", "death_flag": regiment in (101, 102),
             "native_order_token": regiment},
        )

    def side(index, entries, armies, ledger):
        return CurrentBattleSide(
            side_index=index, role="attacker" if index == 0 else "defender",
            primary_participant_character_id=29829 if index == 0 else 45678,
            selected_commander_character_id=29829 if index == 0 else 45678,
            current_roll_points=7 + index, roll_request=None, entries=entries,
            ordered_armies=armies,
            stored_current_fighting_raw=sum(row.state.current_raw for row in entries),
            stored_levy_current_fighting_raw=sum(row.state.current_raw for row in entries if row.bucket == "levy"),
            derived_current_fighting_raw=sum(row.state.current_raw for row in entries),
            derived_soft_casualties_raw=sum(row.state.soft_casualties_raw for row in entries),
            derived_main_fighting_entry_hard_casualties_raw=sum(
                row.starting_raw-row.state.current_raw-row.state.soft_casualties_raw for row in entries if row.fights_in_main_phase),
            non_main_start_minus_current_minus_soft_raw=sum(
                row.starting_raw-row.state.current_raw-row.state.soft_casualties_raw for row in entries if not row.fights_in_main_phase),
            participant_hard_ledger=ledger,
            participant_hard_total_raw=sum(row["hard_casualties_raw"] for row in ledger),
            loss_inputs=None, levy_damage_raw=None, levy_damage_source="fixture",
            levy_damage_native_observed=False, levy_damage_primary_participant_character_id=None,
        )

    def make_carried():
        selected = (
            entry(101, 90001, 29829, "levy", 0, 200000, 250000),
            entry(102, 90003, 34567, "levy", 1, 500000, 0, count=5, knight=55555),
            entry(103, 90002, 29829, "levy", 2, 175000, 150000),
            entry(201, 90001, 29829, "men_at_arms", 0, 300000, 225000),
            entry(202, 90002, 29829, "men_at_arms", 1, 0, 75000, main=False, starting=100000, hard=None),
            entry(203, 90003, 34567, "men_at_arms", 2, 400000, 0, count=4),
        )
        opposition = (entry(301, 90100, 45678, "men_at_arms", 0, 900000, 0, count=9),)
        armies = tuple({"native_carmy_id": army, "public_cunit_id": army+1000000,
                        "owner_character_id": owner, "combat_backlink_id": 16777284}
                       for army, owner in ((90001, 29829), (90003, 34567), (90002, 29829)))
        other_armies = ({"native_carmy_id": 90100, "public_cunit_id": 1090100,
                         "owner_character_id": 45678, "combat_backlink_id": 16777284},)
        sides = (
            side(0, selected, armies, ({"participant_character_id": 29829, "hard_casualties_raw": 500000},
                                      {"participant_character_id": 34567, "hard_casualties_raw": 700000})),
            side(1, opposition, other_armies, ({"participant_character_id": 45678, "hard_casualties_raw": 900000},)),
        )
        loss_sides = (
            CurrentLossSideInputs(0, 100000, 0, 0, 29829, 100000),
            CurrentLossSideInputs(1, 100000, 0, 0, 45678, 100000),
        )
        loss = CurrentLossInputs(100000, 16777284, 2610, 100000, 100000,
                                 50000, 50000, False, 0, loss_sides)
        source = {
            "winner_raw": -1,
            "attacker": {"stored_terminal_loss_baseline_raw": 10000000, "stored_levy_initial_raw": 6000000},
            "defender": {"stored_terminal_loss_baseline_raw": 9000000, "stored_levy_initial_raw": 4000000},
            "current_pursuit_inputs_v1": {
                "losing_side_index": 0, "initial_loser_levy_soft_raw": 9000000,
                "initial_loser_maa_soft_raw": 8000000, "pursuit_phase_days": 7,
                "losing_side_skip_pursuit": True,
                "pursuit_stat_multiplier_raw": 0, "base_toughness_multiplier_raw": 100000,
                "minimum_pursuit_multiplier_raw": 0,
            },
        }
        condition = CurrentBattleCondition(
            snapshot_revision=31, observed_date_raw=53237136, combat_id=16777284,
            province_id=2610, subject_side_index=0, side_scope="fixture-native-composed",
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
            ("frozen_native_composed_inputs",), 2,
            {"snapshot_revision": 31, "observed_date_raw": 53237136, "combat_id": 16777284}, (),
        )

    def full_backing():
        return {
            90001: tuple(TerminalBackingRegiment(90001, rid, count) for rid, count in ((101, 3), (201, 3), (1999, 11))),
            90002: tuple(TerminalBackingRegiment(90002, rid, count) for rid, count in ((103, 3), (202, 3), (2999, 7))),
            90003: tuple(TerminalBackingRegiment(90003, rid, count) for rid, count in ((102, 5), (203, 4), (3999, 13))),
            90100: tuple(TerminalBackingRegiment(90100, rid, count) for rid, count in ((301, 9), (3099, 17))),
        }

    def unchanged_frame(before, result):
        after = result.carried
        keys = ("snapshot_revision", "observed_date_raw", "combat_id", "province_id",
                "subject_side_index", "phase", "phase_raw", "phase_day",
                "roll_cadence_counter", "base_advantage_raw", "resolved_advantage_raw")
        require(tuple(getattr(before.condition, key) for key in keys)
                == tuple(getattr(after.condition, key) for key in keys),
                "selected callback must retain the exact combat/calendar frame")
        require(before.condition.source_snapshot == after.condition.source_snapshot,
                "winner, initial baselines and unrelated global pools/duration/skip stay unchanged")
        require(before.draw_state == after.draw_state and before.simulated_main_ticks == after.simulated_main_ticks
                and before.origin_observed_frame == after.origin_observed_frame,
                "there is no draw, main-loss replay or calendar carry")
        require(before.condition.sides[1] == after.condition.sides[1],
                "opposing side remains unchanged")
        require(result.actual_game_days_advanced == 0 and result.actual_execution_claimed is False
                and result.complete_native_transition is False and result.win_probability_ready is False,
                "conditional primitive does not claim execution, full transition or win probability")

    def case_selected_fractional_writeback():
        before = make_carried()
        original = deepcopy(before)
        backing = full_backing()
        backing_original = deepcopy(backing)
        inputs = module.selected_owner_pursuit_inputs_from_current_condition_12003(before.condition, selected_side_index=0)
        require(inputs.pursuit_stat_multiplier_raw == 0 and inputs.minimum_pursuit_multiplier_raw == 0
                and inputs.pursuit_hard_conversion_raw == 50000,
                "same-query adapter preserves literal zero and the v60 hard-conversion slot")
        require(inputs.source_context["duration_divisor"] == 1
                and inputs.source_context["global_pools_or_skip_flag_copied"] is False,
                "subset coefficient adapter does not admit ordinary global pool/duration/skip inputs")
        event = module.AdmittedSelectedOwnerRetreat12003(16777284, 0, (29829,), 2727, True, {29829: inputs},
                                                        {"kind": "explicit_focused_conditional_264F0F0"})
        result = module.apply_selected_owner_subset_retreats_12003(before, (event,), backing_by_army=backing)
        require(result.status == "available" and result.typed_gaps == (), "fully supplied ordinary subset is available")
        require(before == original and backing == backing_original, "producer does not mutate caller-owned inputs")
        require(len(result.event_ledger) == 1, "one admitted owner creates one callback ledger")
        row = result.event_ledger[0]
        require(row["owner_character_id"] == 29829 and row["owner_index"] == 0 and row["duration_divisor"] == 1,
                "full owner CharacterID is distinct from both selected ArmyIDs")
        require(tuple(entry.state.regiment_id for entry in row["copied_entries_before"]) == (103, 101, 202, 201),
                "copied order is reverse levy followed by reverse MAA")
        require(row["selected_soft_raw_by_bucket"] == {"levy": 400000, "men_at_arms": 300000},
                "selected pools exclude all unrelated owners")
        domains = {item.kind.value: item for item in row["numeric_domains"]}
        require((domains["levy"].current_soft_raw, domains["levy"].extra_daily_raw,
                 domains["levy"].floor_daily_raw, domains["levy"].hard_raw) == (400000, 0, 400000, 200000),
                "levy hand budget uses selected 400000 with divisor one")
        require((domains["men_at_arms"].current_soft_raw, domains["men_at_arms"].extra_daily_raw,
                 domains["men_at_arms"].floor_daily_raw, domains["men_at_arms"].hard_raw) == (300000, 0, 300000, 150000),
                "MAA hand budget uses selected 300000 with divisor one")
        require(row["new_hard_casualties_raw"] == 350000 and row["owner_hard_delta_raw"] == 350000,
                "raw attribution receives exactly one 3.5-soldier converted delta")
        expected_hard = {101: 125000, 103: 75000, 201: 112500, 202: 37500}
        expected_soft = {101: 125000, 103: 75000, 201: 112500, 202: 37500}
        require({item["regiment_id"]: item["new_hard_casualties_raw"] for item in row["backing_writebacks"]} == expected_hard,
                "per-row converted hard matches independent hand arithmetic")
        after_rows = {entry.state.regiment_id: entry for entry in row["copied_entries_after"]}
        before_rows = {entry.state.regiment_id: entry for entry in row["copied_entries_before"]}
        require({rid: entry.state.soft_casualties_raw for rid, entry in after_rows.items()} == expected_soft,
                "copied soft decreases only by its converted hard delta")
        require(all(after_rows[rid].state.current_raw == before_rows[rid].state.current_raw
                    and after_rows[rid].starting_raw == before_rows[rid].starting_raw for rid in after_rows),
                "copied current and starting counts remain unchanged")
        require(after_rows[202].hard_casualties_raw is None
                and after_rows[202].starting_raw-after_rows[202].state.current_raw-after_rows[202].state.soft_casualties_raw == 62500,
                "non-main null explicit hard remains null while residual increases by 37500")
        require(all(item["native_write_order"] == ("regular_backing_hard", "copied_soft_decrease", "existing_owner_H58_increment")
                    and item["owner_ledger_is_second_whole_debit"] is False for item in row["backing_writebacks"]),
                "native write order separates attribution from whole census debit")
        require(row["removed_native_carmy_ids"] == (90002, 90001),
                "Army removal reverses the original native list, without confusing owner identity")
        require(all(army["combat_backlink_id"] == -1 for army in row["removed_armies_in_reverse_native_order"]),
                "only explicitly departed Army backlinks are cleared")
        require(row["cached_current_debit_raw"] == 675000 and row["cached_levy_current_debit_raw"] == 375000
                and row["retained_rows_redebited"] is False and row["backing_army_regiment_membership_removed"] is False,
                "membership caches are debited once and complete backing membership remains")
        retained = result.carried.condition.sides[0]
        require(tuple(entry.state.regiment_id for entry in retained.entries) == (102, 203)
                and retained.entries == (replace(before.condition.sides[0].entries[1], bucket_index=0),
                                         replace(before.condition.sides[0].entries[5], bucket_index=0)),
                "allied entry payload and relative bucket order remain unchanged")
        require(tuple(army["native_carmy_id"] for army in retained.ordered_armies) == (90003,)
                and retained.ordered_armies == (before.condition.sides[0].ordered_armies[1],),
                "allied native Army payload remains unchanged")
        require(retained.stored_current_fighting_raw == 900000 and retained.stored_levy_current_fighting_raw == 500000,
                "stored cache membership subtraction uses selected original current, not casualty raw")
        require(retained.participant_hard_ledger == (
            {"participant_character_id": 29829, "hard_casualties_raw": 850000},
            {"participant_character_id": 34567, "hard_casualties_raw": 700000},
        ) and retained.participant_hard_total_raw == 1550000, "owner hard ledger receives the delta once; ally stays untouched")
        counts = {army: tuple((item.regiment_id, item.current_soldiers) for item in rows)
                  for army, rows in result.backing_by_army.items()}
        require(counts[90001] == ((101, 2), (201, 2), (1999, 11))
                and counts[90002] == ((103, 3), (202, 3), (2999, 7)),
                "integer component writebacks lose exactly two, with unreferenced regiments retained")
        require(result.backing_by_army[90003] == backing[90003] and result.backing_by_army[90100] == backing[90100],
                "unselected whole backing is untouched")
        require(sum(item.current_soldiers for army in (90001, 90002) for item in backing[army])
                - sum(item.current_soldiers for army in (90001, 90002) for item in result.backing_by_army[army]) == 2,
                "fractional Q and owner H58 do not become a second whole-soldier loss")
        require(tuple(result.departed_backing_by_army) == (90002, 90001)
                and result.departed_backing_by_army[90001] == result.backing_by_army[90001],
                "departed full backing is a separate complete view")
        require(tuple((item.regiment_id, item.current_soldiers) for item in result.retained_backing_by_side[0])
                == ((102, 5), (203, 4), (3999, 13)),
                "retained whole census includes regiments not in the combat entry subset")
        unchanged_frame(before, result)
        return {"case": "selected_fractional_writeback", "status": "GREEN",
                "copy_order": [103, 101, 202, 201], "reverse_army_removal": [90002, 90001],
                "selected_soft_raw": {"levy": 400000, "men_at_arms": 300000},
                "raw_hard_delta": 350000, "whole_soldier_delta": 2,
                "departed_backing": counts, "typed_gaps": []}

    def case_ordered_zero_then_missing():
        before = make_carried()
        source = deepcopy(before.condition.source_snapshot)
        source["current_pursuit_inputs_v1"]["pursuit_stat_multiplier_raw"] = None
        before = replace(before, condition=replace(before.condition, source_snapshot=source))
        missing = module.selected_owner_pursuit_inputs_from_current_condition_12003(before.condition, selected_side_index=0)
        require(missing.pursuit_stat_multiplier_raw is None and missing.minimum_pursuit_multiplier_raw == 0
                and missing.pursuit_hard_conversion_raw == 50000,
                "same-query adapter keeps unavailable coefficient distinct from literal zero")
        event = module.AdmittedSelectedOwnerRetreat12003(16777284, 0, (34567, 29829), 2727, True,
                                                        {29829: missing}, {"kind": "explicit_callback_order"})
        result = module.apply_selected_owner_subset_retreats_12003(before, (event,), backing_by_army=None)
        require(result.status == "partial" and len(result.event_ledger) == 2, "known zero callback and missing positive callback remain distinct")
        zero, gap = result.event_ledger
        require(tuple(row["owner_character_id"] for row in result.event_ledger) == (34567, 29829)
                and tuple(row["owner_index"] for row in result.event_ledger) == (0, 1),
                "explicit callback tuple order is neither sorted nor inferred")
        require(zero["selected_soft_raw_by_bucket"] == {"levy": 0, "men_at_arms": 0}
                and zero["branch"] == "no_soft_toughness" and zero["installed"] is True
                and zero["new_hard_casualties_raw"] == 0 and zero["backing_writebacks"] == (),
                "legitimate soft zero needs no unavailable rules or occupied-knight hard call")
        require(zero["removed_native_carmy_ids"] == (90003,) and zero["cached_current_debit_raw"] == 900000,
                "zero loss still performs the explicitly admitted membership callback")
        require(gap["branch"] == "numeric_inputs_unavailable" and gap["installed"] is False
                and gap["new_hard_casualties_raw"] is None,
                "missing positive operand installs no speculative loss or retreat")
        require({item.kind for item in result.typed_gaps} == {
            "departed_whole_census_unavailable", "missing_numeric_operand:pursuit_stat_multiplier_raw"},
            "typed gaps distinguish independent whole census absence and the selected numeric gap")
        require(result.backing_by_army is None and result.departed_backing_by_army == {90003: None}
                and result.retained_backing_by_side == {0: None, 1: None},
                "CombatEntry counts never fabricate a complete whole Army census")
        retained = result.carried.condition.sides[0]
        expected = (before.condition.sides[0].entries[0],
                    replace(before.condition.sides[0].entries[2], bucket_index=1),
                    before.condition.sides[0].entries[3],
                    before.condition.sides[0].entries[4])
        require(retained.entries == expected, "missing positive callback retains all selected owner payload and backing components")
        require(retained.entries[0].source_entry["death_flag"] is True,
                "a death flag alone does not delete the uninstalled selected row")
        require(retained.ordered_armies == (before.condition.sides[0].ordered_armies[0],
                                            before.condition.sides[0].ordered_armies[2]),
                "only completed zero callback removes its Army; positive-gap Armies remain")
        require(retained.participant_hard_ledger == before.condition.sides[0].participant_hard_ledger
                and retained.participant_hard_total_raw == 1200000,
                "zero and unknown are not substituted into new owner hard losses")
        require(retained.stored_current_fighting_raw == 675000 and retained.stored_levy_current_fighting_raw == 375000,
                "callback sequencing preserves only the actual completed membership debit")
        unchanged_frame(before, result)
        return {"case": "ordered_zero_then_missing", "status": "GREEN",
                "callback_order": [34567, 29829], "zero_new_hard_raw": 0,
                "missing_new_hard_raw": None, "whole_census": None,
                "typed_gaps": [asdict(item) for item in result.typed_gaps]}

    report = {"schema": "battle-selected-owner-subset-retreat-v61-focused/v1",
              "status": "RED", "readiness": "source-ready", "cases": [],
              "game": 0, "SDK": 0, "pipe": 0, "window": 0, "new_days": 0,
              "shared_mutation": 0, "Git": 0, "old_tests": 0, "native_full_build": 0}
    try:
        for case in (case_selected_fractional_writeback, case_ordered_zero_then_missing):
            started_checks = checks
            result = case()
            result["checks"] = checks-started_checks
            cases.append(result)
        report.update(status="GREEN", readiness="static-ready", cases=cases, checks=checks, case_count=2)
    except Exception as error:
        report.update(error=f"{type(error).__name__}: {error}", traceback=traceback.format_exc(),
                      cases=cases, checks=checks, case_count=2)
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
    print(json.dumps({"status": report["status"], "case_count": report["case_count"],
                      "checks": checks, "receipt": str(args.out), "error": report.get("error")}, indent=2))
    return 0 if report["status"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
