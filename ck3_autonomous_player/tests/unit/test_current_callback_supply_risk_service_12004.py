"""One new real Army-service compound; FIRST execution belongs to Root."""
from copy import deepcopy
import json
import os
from pathlib import Path
import unittest

from test_conditional_monthly_loss_budgets import monthly_budget_packet, MemoryStrengthService


def current_packet() -> dict:
    row = monthly_budget_packet()
    row.update(current_soldiers=101, maximum_soldiers=101,
               current_supply_raw=750000, current_supply_capacity_raw=6000000,
               current_attrition_fraction_raw=0, current_attrition_fraction_scale=100000)
    row["monthly_loss_budget_inputs_v1"].update(
        loaded_supply_state_levels=[60, 7, 0], loaded_supply_state_fractions_raw=[0, 0, 2500])
    row["regiment_strengths"][0].update(current_soldiers=101, maximum_soldiers=101)
    row["regiment_replenishment_records_v1"][0]["records"][0].update(
        current_soldiers=101, effective_current_soldiers=101, maximum_soldiers=101)
    row["loss_application_inputs_v1"].update(
        whole_soldiers=101, definition_le_zero_soldiers=101, supply_eligible_soldiers=101,
        definition_le_zero_supply_eligible_soldiers=101, siege_active=False, raid_active=False,
        raid_association_id=-1)
    row["current_daily_supply_dispatch_inputs_v1"] = {
        "source": "native_current_selected_supply_bucket_subject_occurrences",
        "status": "available", "ready": True, "unavailable_reason": None,
        "capture_boundary": "current_paused_strength",
        "subject_army_id": 0, "subject_carmy_id": 0, "current_date_raw": 264,
        "native_day_index": 11, "selected_bucket_phase": 11,
        "selected_bucket_capacity_raw": 8, "selected_bucket_count_raw": 5,
        "selected_bucket_data_present": True, "subject_dispatch_occurrence_count": 2,
        "subject_occurrence_indices": [1, 3], "actual_callback_observed": False,
        "earlier_stage_outputs_reconstructed": False, "full_daily_supply_transition_ready": False,
        "full_monthly_ready": False,
    }
    return row


class CurrentCallbackSupplyRiskService12004Tests(unittest.TestCase):
    def test_current_stock_crossing_and_branch_specific_supply_budget(self) -> None:
        outputs = {}

        def query(label: str, packet: dict) -> dict:
            before = deepcopy(packet)
            service = MemoryStrengthService(packet)
            result = service.query_army_strengths([0], expected_revision=2)
            self.assertEqual(service.calls, 1)
            self.assertEqual(packet, before)
            self.assertEqual(result["army_strengths"][0]["current_supply_raw"], packet["current_supply_raw"])
            value = result["current_callback_supply_risk_v1"][0]["projection"]
            for field in ("actual_callback_observed", "actual_supply_update_observed", "actual_loss",
                          "earlier_stage_outputs_reconstructed", "future_callback_selection_ready",
                          "future_date_or_day_derived", "full_daily_supply_transition_ready", "full_monthly_ready"):
                self.assertIs(value[field], False, field)
            self.assertIsNone(value["actual_post_stage_supply_raw"])
            self.assertIsNone(value["actual_post_stage_current"])
            outputs[label] = result
            if target := os.environ.get("XAR_CURRENT_CALLBACK_SUPPLY_RISK_FIRST_OUTPUT"):
                Path(target).write_text(json.dumps(outputs, indent=2) + "\n", encoding="utf-8")
            return value

        value = query("loaded-runtime-crossing", current_packet())
        self.assertTrue(value["ready"])
        self.assertEqual(value["observed_current_supply_raw"], 750000)
        self.assertEqual(value["observed_current_attrition_fraction_raw"], 0)
        self.assertEqual(value["observed_current_supply_loss_budget_soldiers"], 0)
        self.assertEqual(value["observed_current_stock_state"]["base_fraction_raw"], 0)
        self.assertEqual(value["conditional_post_stock_raw"], 650000)
        self.assertEqual(value["conditional_post_stock_state"]["base_fraction_raw"], 2500)
        self.assertEqual(value["conditional_supply_budget_soldiers"], 2)
        self.assertTrue(value["conditional_positive_supply_budget"])
        self.assertTrue(value["conditional_enters_positive_supply_base_state"])
        self.assertEqual(value["observed_subject_callback_positions"], [1, 3])
        self.assertEqual(value["observed_subject_callback_occurrences"], 2)
        self.assertTrue(value["observed_current_day_callback_selected"])
        self.assertEqual(value["admission_witnesses"][-1]["elapsed_days"], 11)

        packet = current_packet()
        packet["current_supply_raw"] = 800000
        packet.pop("loss_application_inputs_v1")
        value = query("exact-runtime-threshold", packet)
        self.assertTrue(value["ready"])
        self.assertEqual(value["conditional_post_stock_raw"], 700000)
        self.assertEqual(value["conditional_supply_budget_soldiers"], 0)
        self.assertFalse(value["conditional_enters_positive_supply_base_state"])
        self.assertEqual(value["missing_inputs"], [])

        packet = current_packet()
        packet["current_supply_change_monthly_raw"] = None
        packet.pop("loss_application_inputs_v1")
        packet["monthly_loss_budget_inputs_v1"].update(
            status="unavailable", ready=False, unavailable_reason="unused state-table read unavailable",
            native_unit_in_combat=True, loaded_supply_state_levels=None,
            loaded_supply_state_fractions_raw=None)
        value = query("known-combat-rejection", packet)
        self.assertTrue(value["ready"])
        self.assertFalse(value["conditional_callback_admitted"])
        self.assertEqual(value["admission_rejection"], "native_unit_in_combat")
        self.assertEqual(value["conditional_post_stock_raw"], 750000)
        self.assertEqual(value["conditional_supply_budget_soldiers"], 0)
        self.assertEqual(value["missing_inputs"], [])

        packet = current_packet()
        packet.pop("loss_application_inputs_v1")
        packet["monthly_loss_budget_inputs_v1"].update(
            status="unavailable", ready=False, unavailable_reason="unused state-table read unavailable",
            native_fleet_supply_loss_suppressed=True, loaded_supply_state_levels=None,
            loaded_supply_state_fractions_raw=None)
        value = query("fleet-suppressed-unused-component", packet)
        self.assertTrue(value["ready"])
        self.assertEqual(value["conditional_post_stock_raw"], 650000)
        self.assertEqual(value["conditional_supply_budget_soldiers"], 0)
        self.assertEqual(value["missing_inputs"], [])

        packet = current_packet()
        packet.pop("loss_application_inputs_v1")
        value = query("missing-eligible-current", packet)
        self.assertFalse(value["ready"])
        self.assertTrue(value["conditional_post_stock_ready"])
        self.assertEqual(value["conditional_post_stock_raw"], 650000)
        self.assertIsNone(value["conditional_supply_budget_soldiers"])
        self.assertEqual(value["missing_inputs"], ["supply_eligible_soldiers"])

        packet = current_packet()
        packet.update(current_supply_raw=50000, current_supply_capacity_raw=None,
                      current_attrition_fraction_raw=2500)
        packet["loss_application_inputs_v1"]["current_supply_loss_budget"] = 2
        value = query("negative-sum-zero-without-capacity", packet)
        self.assertTrue(value["ready"])
        self.assertEqual(value["conditional_post_stock_raw"], 0)
        self.assertEqual(value["conditional_supply_budget_soldiers"], 2)

        packet = current_packet()
        packet["current_supply_change_monthly_raw"] = None
        value = query("missing-rate", packet)
        self.assertFalse(value["ready"])
        self.assertTrue(value["observed_current_stock_state"]["ready"])
        self.assertIsNone(value["conditional_post_stock_raw"])
        self.assertIsNone(value["conditional_supply_budget_soldiers"])
        self.assertEqual(value["missing_inputs"], ["current_supply_change_monthly_raw"])

        packet = current_packet()
        packet["current_daily_supply_dispatch_inputs_v1"].update(
            selected_bucket_count_raw=0, selected_bucket_data_present=False,
            subject_dispatch_occurrence_count=0, subject_occurrence_indices=[])
        value = query("observed-empty-current-bucket", packet)
        self.assertFalse(value["observed_current_day_callback_selected"])
        self.assertEqual(value["observed_subject_callback_occurrences"], 0)
        self.assertEqual(value["conditional_supply_budget_soldiers"], 2)


if __name__ == "__main__":
    unittest.main()
