"""One compound production query case for native Province supply contributors."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from test_associated_refill_current_assembly import (
    MemoryStrengthService, packet as associated_packet, record,
)


def data_snapshot(regiment, records):
    return {
        "army_regiment_id": regiment, "source": "native_all_data_records",
        "status": "available", "ready": True,
        "native_data_record_count": len(records), "unavailable_reason": None,
        "native_loss_writer_skipped": False,
        "loss_writer_admission_unavailable_reason": None, "records": records,
    }


def regiment(index, identity, current, maximum, eligible, snapshot=None):
    return {
        "stored_index": index, "army_regiment_id": identity,
        "status": "available", "unavailable_reason": None,
        "current_soldiers": current, "maximum_soldiers": maximum,
        "native_supply_loss_eligible": eligible,
        "replenishment_records_v1": snapshot,
    }


def occurrence(index, unit, owner, carmy, basis, current, regiments):
    return {
        "stored_index": index, "army_id": unit,
        "status": "available", "unavailable_reason": None,
        "owner_character_id": owner, "included": basis != "native_not_common_war_side",
        "inclusion_basis": basis, "native_carmy_id": carmy,
        "native_eligible_current_soldiers": current, "regiments": regiments,
    }


def contributor_packet():
    source = associated_packet()
    primary_data = deepcopy(source["regiment_replenishment_records_v1"][0])
    primary = [regiment(0, 30, 268, 309, True, primary_data),
               regiment(1, 99, 5000, 6000, False)]
    common_side = [
        regiment(0, 50, 10, 20, True, data_snapshot(
            50, [record(0, 150, 0, 50, 10, 20, 0, 10000)])),
        regiment(1, 60, 8, 9, True, data_snapshot(
            60, [record(0, 160, 0, 60, 8, 9, 0, 10000)])),
        regiment(2, 70, 0, 1, True, data_snapshot(
            70, [record(0, 170, 0, 70, 0, 1, 0, 1)])),
    ]
    first = occurrence(0, 0, 29829, 0, "same_owner", 268, primary)
    repeated = deepcopy(first)
    repeated["stored_index"] = 3
    source["current_province_supply_contributors_v1"] = {
        "source": "native_current_province_mode0", "status": "available",
        "unavailable_reason": None, "current_usage_ready": True,
        "contributors_ready": True, "province_id": 71, "subject_army_id": 0,
        "subject_carmy_id": 0, "owner_character_id": 29829,
        "native_province_unit_count": 4, "native_supply_limit_soldiers": 600,
        "native_supply_usage_soldiers": 554, "soldiers_scale": 1,
        "occurrences": [first,
                        occurrence(1, -1728053200, 777, 42,
                                   "native_common_war_side", 18, common_side),
                        occurrence(2, 88, 888, None,
                                   "native_not_common_war_side", None, []),
                        repeated],
    }
    # The subject's ineligible regiment belongs to its real current roster,
    # although its DATA is unnecessary for the Province flag2 contribution.
    strength = deepcopy(source["regiment_strengths"][0])
    ineligible = deepcopy(strength)
    ineligible.update({"army_regiment_id": 99, "current_soldiers": 5000,
                       "maximum_soldiers": 6000, "native_supply_loss_eligible": False})
    source.update({"regiment_count": 2, "current_soldiers": 5268,
                   "maximum_soldiers": 6309,
                   "regiment_strengths": [strength, ineligible],
                   "regiment_replenishment_records_v1": [deepcopy(primary_data)]})
    inputs = source["loss_application_inputs_v1"]
    inputs.update({"whole_soldiers": 5268, "definition_le_zero_soldiers": 5268,
                   "supply_eligible_soldiers": 268,
                   "definition_le_zero_supply_eligible_soldiers": 268})
    return source


class ContributorService(MemoryStrengthService):
    def __init__(self, row):
        super().__init__(row)
        self.query_calls = 0

    def execute_step(self, step, *, expected_revision=None):
        self.query_calls += 1
        return super().execute_step(step, expected_revision=expected_revision)


class CurrentProvinceSupplyContributorTests(unittest.TestCase):
    def test_production_query_counts_occurrences_after_one_selected_physical_refill(self):
        source = contributor_packet()
        original = deepcopy(source)
        service = ContributorService(source)
        answer = service.query_army_strengths([0], expected_revision=2)
        allocation = answer["loss_allocation_requests_v1"][0]
        projected = allocation["same_input_conditional_province_supply_usage_v1"]
        self.assertEqual(service.query_calls, 1)
        self.assertEqual(projected["status"], "available")
        self.assertTrue(projected["current_usage_ready"])
        self.assertTrue(projected["contributors_ready"])
        self.assertEqual((projected["native_supply_limit_soldiers"],
                          projected["native_supply_usage_soldiers"],
                          projected["current_contributor_sum_soldiers"]), (600, 554, 554))
        self.assertTrue(projected["current_contributor_sum_ready"])
        self.assertTrue(projected["conditional_usage_ready"])
        self.assertEqual(projected["conditional_supply_usage_soldiers"], 596)
        self.assertEqual([row["army_id"] for row in projected["occurrences"]],
                         [0, -1728053200, 88, 0])
        self.assertEqual([row["conditional_eligible_current_soldiers"]
                          for row in projected["occurrences"]], [288, 20, 0, 288])
        self.assertEqual([row["inclusion_basis"] for row in projected["occurrences"]],
                         ["same_owner", "native_common_war_side",
                          "native_not_common_war_side", "same_owner"])
        self.assertEqual(projected["occurrences"][0]["regiments"][1][
            "conditional_supply_contribution"], 0)
        chunks = {(row["persistent_regiment_id"], row["chunk_index"]): row
                  for row in projected["physical_refill"]["physical_chunks"]}
        self.assertEqual((chunks[130, 0]["same_input_q"],
                          chunks[130, 0]["current_soldiers"],
                          chunks[130, 0]["physical_add_count"],
                          len(chunks[130, 0]["data_occurrences"])), (10, 90, 1, 2))
        self.assertEqual((chunks[160, 0]["same_input_q"],
                          chunks[160, 0]["physical_add_count"],
                          chunks[160, 0]["current_soldiers"]), (0, 1, 8))
        self.assertEqual(chunks[170, 0]["current_soldiers"], 0)
        self.assertEqual(len(projected["physical_regiment_coverage"][0]["occurrences"]), 2)
        self.assertFalse(projected["actual_replenishment"])
        self.assertFalse(projected["actual_loss"])
        self.assertIsNone(projected["actual_post_stage_current"])
        self.assertIsNone(projected["actual_post_supply_usage_soldiers"])
        self.assertFalse(projected["full_regular_refill_ready"])
        self.assertFalse(projected["full_monthly_ready"])
        self.assertEqual(answer["army_strengths"][0]["current_soldiers"], 5268)
        self.assertEqual(answer["army_strengths"][0][
            "current_province_supply_contributors_v1"]["native_supply_usage_soldiers"], 554)
        self.assertEqual(allocation["same_input_conditional_monthly_loss_budgets_v1"][
            "actual_loss"], False)
        self.assertEqual(source, original)

        missing = deepcopy(source)
        missing["current_province_supply_contributors_v1"]["occurrences"][1][
            "regiments"][0]["replenishment_records_v1"] = None
        partial = ContributorService(missing).query_army_strengths([0])[
            "loss_allocation_requests_v1"][0]["same_input_conditional_province_supply_usage_v1"]
        self.assertTrue(partial["current_usage_ready"])
        self.assertTrue(partial["contributors_ready"])
        self.assertEqual(partial["native_supply_usage_soldiers"], 554)
        self.assertEqual(partial["current_contributor_sum_soldiers"], 554)
        self.assertFalse(partial["conditional_usage_ready"])
        self.assertIsNone(partial["conditional_supply_usage_soldiers"])
        self.assertTrue(partial["occurrences"][0]["conditional_ready"])
        self.assertFalse(partial["occurrences"][1]["regiments"][0]["conditional_ready"])
        self.assertTrue(partial["occurrences"][1]["regiments"][1]["conditional_ready"])

        unreadable = deepcopy(source)
        family = unreadable["current_province_supply_contributors_v1"]
        family.update({"status": "partial", "unavailable_reason": "unit_generation_unreadable",
                       "contributors_ready": False})
        family["occurrences"][2].update({"status": "unavailable",
            "unavailable_reason": "unit_generation_unreadable", "included": None,
            "inclusion_basis": None, "owner_character_id": None})
        unknown = ContributorService(unreadable).query_army_strengths([0])[
            "loss_allocation_requests_v1"][0]["same_input_conditional_province_supply_usage_v1"]
        self.assertTrue(unknown["current_usage_ready"])
        self.assertFalse(unknown["conditional_usage_ready"])
        self.assertIsNone(unknown["occurrences"][2]["conditional_eligible_current_soldiers"])
        self.assertEqual(unknown["native_supply_usage_soldiers"], 554)

        no_scalar = deepcopy(source)
        no_scalar["current_province_supply_contributors_v1"].update({
            "status": "partial", "unavailable_reason": "native_usage_unreadable",
            "current_usage_ready": False, "native_supply_usage_soldiers": None})
        conditional = ContributorService(no_scalar).query_army_strengths([0])[
            "loss_allocation_requests_v1"][0]["same_input_conditional_province_supply_usage_v1"]
        self.assertFalse(conditional["current_usage_ready"])
        self.assertIsNone(conditional["native_supply_usage_soldiers"])
        self.assertTrue(conditional["conditional_usage_ready"])
        self.assertEqual(conditional["conditional_supply_usage_soldiers"], 596)

        empty = deepcopy(source)
        empty["current_province_supply_contributors_v1"].update({
            "native_province_unit_count": 0, "native_supply_limit_soldiers": 0,
            "native_supply_usage_soldiers": 0, "occurrences": []})
        zero = ContributorService(empty).query_army_strengths([0])[
            "loss_allocation_requests_v1"][0]["same_input_conditional_province_supply_usage_v1"]
        self.assertTrue(zero["current_usage_ready"])
        self.assertTrue(zero["conditional_usage_ready"])
        self.assertEqual((zero["native_supply_limit_soldiers"],
                          zero["native_supply_usage_soldiers"],
                          zero["conditional_supply_usage_soldiers"]), (0, 0, 0))
        self.assertEqual(zero["physical_refill"]["physical_chunks"], [])

        independent = deepcopy(source)
        independent.pop("loss_application_inputs_v1")
        early = ContributorService(independent).query_army_strengths([0])[
            "loss_allocation_requests_v1"][0]
        self.assertFalse(early["writer_requests_ready"])
        self.assertEqual(early["same_input_conditional_province_supply_usage_v1"][
            "conditional_supply_usage_soldiers"], 596)

        legacy = deepcopy(source)
        legacy.pop("current_province_supply_contributors_v1")
        absent = ContributorService(legacy).query_army_strengths([0])[
            "loss_allocation_requests_v1"][0]["same_input_conditional_province_supply_usage_v1"]
        self.assertFalse(absent["current_usage_ready"])
        self.assertFalse(absent["conditional_usage_ready"])
        self.assertIsNone(absent["conditional_supply_usage_soldiers"])
        self.assertFalse(absent["actual_replenishment"])
        self.assertFalse(absent["full_monthly_ready"])
        self.assertEqual(source, original)


if __name__ == "__main__":
    unittest.main()
