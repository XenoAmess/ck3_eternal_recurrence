"""New source-clock/zero-writer contradictions; no prior fixture replay."""
from copy import deepcopy
import unittest

from xar_autoplayer.bridge.army_zero_stock_clock_12004 import (
    project_zero_stock_next_callback_candidate_12004,
    select_actual_zero_stock_supply_preferred_12004,
)
from xar_autoplayer.bridge.episode04_starvation_loss_12004 import EXE_SHA256


def clock_row():
    current, following = 43800000, 43800024
    phases = [dict(phase_index_i32=i, status="available", ready=True,
                   unavailable_reason=None, capacity_raw_i32=3, count_raw_i32=3,
                   data_pointer_present=True, matching_positions=[0, 2] if i == 1 else [],
                   subject_occurrence_count_i32=2 if i == 1 else 0) for i in range(30)]
    source = dict(schema_version=1, source="native_source_derived_next_daily_supply_frame_inputs_12004",
                  stage="source_derived_conditional_next_date_pair", status="available", ready=True,
                  unavailable_reason=None, subject_army_id_u32=10, subject_carmy_id_u32=20,
                  current_date_storage_raw64=current, current_date_raw_i32=current,
                  current_native_day_index_raw_i32=12, source_derived_next_date_raw_i32=following,
                  source_derived_next_native_day_index_raw_i32=1,
                  actual_future_date_stage_observed=False, actual_future_callback_observed=False,
                  future_bucket_mutations_reconstructed=False, future_stock_or_strength_ready=False,
                  full_daily_supply_transition_ready=False, full_monthly_ready=False)
    return dict(status="available", army_id=10, native_carmy_id=20, current_supply_raw=0,
                army_update_clock_v1=dict(status="available", ready=True, unavailable_reason=None,
                    current_date_raw=current, native_day_index=12, selected_bucket_phase=12,
                    observed_army_bucket_phase=1, last_supply_update_date_raw=current - 720,
                    grace_anchor_date_raw=current, loaded_grace_days=0,
                    last_supply_update_date_storage_raw64=current - 720,
                    grace_anchor_date_storage_raw64=current),
                monthly_loss_budget_inputs_v1=dict(unit_native_170_raw=0, native_unit_in_combat=False,
                    native_unit_gathering=False, army_gathering_count_raw=0),
                source_derived_next_daily_supply_frame_inputs_v1=source,
                future_daily_supply_schedule_inputs_v1=dict(schema_version=1,
                    source="native_future_daily_supply_schedule_inputs_12004",
                    stage="observed_current_all_phase_schedule", status="available", ready=True,
                    unavailable_reason=None, subject_army_id_u32=10, subject_carmy_id_u32=20,
                    current_date_storage_raw64=current, current_date_raw_i32=current,
                    native_day_index_raw_i32=12, selected_phase_index_i32=12,
                    secondary_identity="game_data_plus_2a548", phases=phases,
                    actual_future_callback_observed=False, future_bucket_mutations_reconstructed=False,
                    full_daily_supply_transition_ready=False, full_monthly_ready=False))


def actual_row(stock=0, *, pc=0x24E35FF, kind="supply_preferred"):
    invocation = dict(invocation_token=11, native_thread_id=4, nesting_depth=1,
                      parent_invocation_token=0, callback_entry_rva=0x24E3410,
                      callback_caller_return_rva=0x2A9AB4B)
    callback = dict(sequence=100, army_id=10, native_carmy_id=20,
                    supply_parent_invocation_v1=invocation, caller_return_rva=0x2A9AB4B,
                    passed_date_raw64=43800024, same_instance_after=True, capture_failure_flags=0,
                    before=dict(supply_raw=0), after=dict(supply_raw=0))
    writer = dict(sequence=7, caller_kind=kind, caller_return_rva=pc, observed_date_raw=43800024,
                  supply_parent_context_v1=dict(invocation=deepcopy(invocation),
                      capture_failure_flags=0, receiver_identity_matches=True, army_id=10,
                      native_carmy_id=20, passed_date_raw64=43800024,
                      stock_at_writer_entry_raw=stock, stock_scale=100000),
                  same_instance_after=True, physical_capture_complete=True,
                  physical_debit_observed=True, capture_failure_flags=0,
                  native_data_record_count=1, captured_data_record_count=1,
                  physical_slot_count=1, actual_physical_soldier_debit=1,
                  data_aliases=[dict(data_record_index=0, physical_slot_index=0,
                                    persistent_regiment_id=9, data_chunk_ordinal=0)],
                  physical_slots=[dict(physical_slot_index=0, same_instance_after=True,
                      before=dict(current_soldiers=40, maximum_soldiers=40, state_raw=0),
                      after=dict(current_soldiers=39, maximum_soldiers=40, state_raw=0))])
    return dict(army_id=10, native_carmy_id=20,
                actual_supply_callback_observations_v1=dict(observer_installed=True,
                    oldest_available_sequence=100, latest_sequence=100,
                    unattributed_capture_failures=0, events=[callback]),
                actual_loss_writer_observations_v1=dict(observer_installed=True,
                    oldest_available_sequence=7, latest_sequence=7,
                    unattributed_capture_failures=0, events=[writer]))


def actual(row):
    return select_actual_zero_stock_supply_preferred_12004(
        row, game_version="1.20.0.4", executable_sha256=EXE_SHA256,
        callback_after_sequence=99, loss_after_sequence=6)


class ZeroStockClockTests(unittest.TestCase):
    def test_actual_next_pair_and_repeated_slots_are_not_current_d_plus_one(self):
        value = project_zero_stock_next_callback_candidate_12004(clock_row())
        self.assertIs(value["conditional_zero_entry_capture_candidate"], True)
        self.assertEqual(value["next_native_day_index_raw_i32"], 1)
        self.assertEqual(value["conditional_original_pointer_positions"], [0, 2])
        self.assertEqual(value["conditional_callback_opportunity_count"], 2)
        self.assertIsNone(value["successful_updater_count"])
        self.assertFalse(value["physical_loss_observed"])

    def test_grace_equality_rejects_and_full_date_is_independent(self):
        row = clock_row()
        row["army_update_clock_v1"]["loaded_grace_days"] = 1
        value = project_zero_stock_next_callback_candidate_12004(row)
        self.assertIs(value["conditional_zero_entry_capture_candidate"], False)
        self.assertEqual(value["next_admission"]["rejection"], "native_grace_strict_greater")

    def test_selected_phase_readiness_does_not_require_other_29(self):
        row = clock_row()
        family = row["future_daily_supply_schedule_inputs_v1"]
        family.update(status="partial", ready=False, unavailable_reason="phase29_unreadable")
        family["phases"][29].update(status="unavailable", ready=False,
                                    unavailable_reason="header_unreadable")
        self.assertIs(project_zero_stock_next_callback_candidate_12004(row)[
            "conditional_zero_entry_capture_candidate"], True)
        family["phases"][1].update(matching_positions=[], subject_occurrence_count_i32=0)
        self.assertIs(project_zero_stock_next_callback_candidate_12004(row)[
            "conditional_zero_entry_capture_candidate"], False)

    def test_missing_pair_stays_unknown_and_incoherent_seed_is_rejected(self):
        row = clock_row()
        row.pop("source_derived_next_daily_supply_frame_inputs_v1")
        value = project_zero_stock_next_callback_candidate_12004(row)
        self.assertIsNone(value["conditional_zero_entry_capture_candidate"])
        self.assertIsNone(value["next_selected_phase_i32"])
        row = clock_row()
        row["army_update_clock_v1"]["native_day_index"] = 13
        row["army_update_clock_v1"]["selected_bucket_phase"] = 13
        with self.assertRaisesRegex(ValueError, "same-row native next seed"):
            project_zero_stock_next_callback_candidate_12004(row)

    def test_single_positive_requires_writer_exact_zero_and_direct_daily_supply(self):
        positive = actual(actual_row())
        self.assertTrue(positive["positive_physical_debit_observed"])
        self.assertEqual(positive["selected_invocation_debit_sum"], 1)
        self.assertFalse(positive["complete_interval_loss_total_ready"])
        self.assertFalse(positive["complete_cycle_observed"])
        for stock, pc, kind in ((1, 0x24E35FF, "supply_preferred"),
                                (0, 0x24E377C, "siege_or_raid_preferred"),
                                (0, 0x2A958E8, "residual_allocator")):
            with self.subTest(stock=stock, pc=pc):
                self.assertFalse(actual(actual_row(stock, pc=pc, kind=kind))[
                    "positive_physical_debit_observed"])

    def test_callback_zero_to_zero_without_writer_is_no_zero_loss_claim(self):
        row = actual_row()
        row["actual_loss_writer_observations_v1"].update(events=[], latest_sequence=6)
        value = actual(row)
        self.assertFalse(value["positive_physical_debit_observed"])
        self.assertIsNone(value["selected_invocation_debit_sum"])
        self.assertFalse(value["complete_interval_loss_total_ready"])

    def test_partial_receiver_identity_and_boolean_zero_are_not_candidates(self):
        row = clock_row()
        row.pop("army_id")
        self.assertIs(project_zero_stock_next_callback_candidate_12004(row)[
            "conditional_zero_entry_capture_candidate"], False)
        row = clock_row()
        row["current_supply_raw"] = False
        self.assertIsNone(project_zero_stock_next_callback_candidate_12004(row)[
            "conditional_zero_entry_capture_candidate"])


if __name__ == "__main__":
    unittest.main()
