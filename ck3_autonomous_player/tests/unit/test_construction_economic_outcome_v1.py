"""Meaningful receipt projections; fixtures are controlled, not paused live."""

from __future__ import annotations

from copy import deepcopy
import unittest

from xar_autoplayer.construction_economic_outcome_v1 import (
    construction_economic_outcome_v1,
)
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.bridge.war_cash_private_transport_v1 import MONTHLY_FLOW_SEMANTICS_12004


def completed_receipt() -> dict[str, object]:
    return {
        "status": "applied", "postcondition_verified": True,
        "completion_status": "completed", "completion_observed_date_raw": 200,
        "candidate": {"barony_title_id": 2103, "province_id": 2635,
                      "authored_monthly_income_delta_hundredths": 50},
        "pre_player_monthly_gold_income_raw": 400000,
        "observed_player_monthly_gold_income_raw": 450000,
        "income_observed_date_raw": 200,
        "pre_province_income_observation": {
            "status": "observed", "barony_title_id": 2103, "province_id": 2635,
            "native_province_monthly_income_raw": 87000, "date_raw": 100},
        "construction_province_income_observation": {
            "status": "observed", "barony_title_id": 2103, "province_id": 2635,
            "native_province_monthly_income_raw": 137000, "date_raw": 200},
    }


class ConstructionEconomicOutcomeTests(unittest.TestCase):
    def test_completed_aggregate_changes_do_not_claim_attributed_net_benefit(self) -> None:
        receipt = completed_receipt()
        original = deepcopy(receipt)
        result = construction_economic_outcome_v1(receipt, exact_ck3_build="1.20.0.4")
        self.assertEqual(result["phase"], "completed")
        self.assertEqual(result["player_gross_monthly_income_change"]["delta_raw"], 50000)
        self.assertEqual(result["province_income_change"]["delta_raw"], 50000)
        self.assertIsNone(result["province_income_change"]["scale"])
        self.assertFalse(result["readiness"]["building_attribution_ready"])
        self.assertFalse(result["readiness"]["net_benefit_ready"])
        self.assertFalse(result["readiness"]["m5_realized_value_ready"])
        self.assertEqual(receipt, original)

    def test_zero_and_negative_aggregate_changes_remain_observations(self) -> None:
        receipt = completed_receipt()
        receipt["observed_player_monthly_gold_income_raw"] = 400000
        receipt["construction_province_income_observation"]["native_province_monthly_income_raw"] = 86000
        result = construction_economic_outcome_v1(receipt, exact_ck3_build="1.20.0.4")
        self.assertTrue(result["readiness"]["player_gross_aggregate_change_ready"])
        self.assertEqual(result["player_gross_monthly_income_change"]["delta_raw"], 0)
        self.assertEqual(result["province_income_change"]["delta_raw"], -1000)

    def test_old_active_income_cannot_be_used_as_completed_income(self) -> None:
        receipt = completed_receipt()
        receipt["income_observed_date_raw"] = 199
        receipt["construction_province_income_observation"]["date_raw"] = 199
        result = construction_economic_outcome_v1(receipt, exact_ck3_build="1.20.0.4")
        self.assertTrue(result["material_completed"])
        self.assertIsNone(result["player_gross_monthly_income_change"]["delta_raw"])
        self.assertIsNone(result["province_income_change"]["delta_raw"])
        self.assertEqual(result["next_observation_kind"], "existing_player_root_then_material_receipt")

    def test_progress_never_implies_completion_and_legacy_income_is_unqualified(self) -> None:
        receipt = completed_receipt()
        receipt["completion_status"] = "in_progress"
        receipt["construction_progress_observation"] = {"native_remaining_work_raw": 0}
        result = construction_economic_outcome_v1(receipt, exact_ck3_build="1.20.0.4")
        self.assertEqual(result["phase"], "active")
        self.assertFalse(result["material_completed"])
        self.assertIsNone(result["player_gross_monthly_income_change"]["delta_raw"])
        legacy = construction_economic_outcome_v1(completed_receipt(), exact_ck3_build="1.19.0.6")
        self.assertFalse(legacy["readiness"]["player_gross_aggregate_change_ready"])
        self.assertEqual(legacy["player_gross_monthly_income_change"]["unavailable_reason"],
                         "player_income_semantics_not_qualified")

    def test_missing_pre_baseline_is_not_repaired_by_a_current_query(self) -> None:
        receipt = completed_receipt()
        receipt["pre_player_monthly_gold_income_raw"] = None
        receipt["pre_province_income_observation"] = None
        result = construction_economic_outcome_v1(receipt, exact_ck3_build="1.20.0.4")
        self.assertIsNone(result["next_observation_kind"])
        self.assertIsNone(result["player_gross_monthly_income_change"]["delta_raw"])
        self.assertIsNone(result["province_income_change"]["delta_raw"])

    def test_true_net_and_stock_changes_are_observed_without_building_attribution(self) -> None:
        # Controlled interval: gross stays fixed, total expense falls, and an
        # independently proved construction debit explains only part of cash.
        def cash(date: int, wallet: int, expenses: int) -> dict[str, object]:
            return {
                "game_version": CK3_12004.game_version,
                "executable_sha256": CK3_12004.executable_sha256,
                "played_character_id": 29829, "date_raw": date,
                "monthly_income_semantics": dict(MONTHLY_FLOW_SEMANTICS_12004),
                "current_treasury": {"raw": wallet, "scale": 100000},
                "player_monthly_gross_income": {"raw": 450000, "scale": 100000},
                "player_monthly_total_expenses": {"raw": expenses, "scale": 100000},
                "player_monthly_net_income": {"raw": 450000 - expenses, "scale": 100000},
                "monthly_gross_income_unavailable_reason": None,
                "monthly_total_expenses_unavailable_reason": None,
                "monthly_net_income_unavailable_reason": None,
                "readiness": {"monthly_gross_income_ready": True,
                              "monthly_total_expenses_ready": True,
                              "monthly_net_income_ready": True,
                              "current_treasury_ready": True, "same_frame_ready": True},
            }

        receipt = completed_receipt()
        receipt.update(actor_character_id=29829, pre_date_raw=100,
                       action_request_id="controlled-construction-once")
        receipt["candidate"].update(stock_gold_cost_raw=14250000, gold_before_raw=100000000)
        receipt["start_receipt"] = {
            "status": "applied", "postcondition_verified": True,
            "action_request_id": "controlled-construction-once",
            "post_player_gold_raw": 85750000,
        }
        result = construction_economic_outcome_v1(
            receipt, exact_ck3_build="1.20.0.4",
            pre_cash_v2=cash(100, 100000000, 400000),
            post_cash_v2=cash(224, 90000000, 380000))
        observed = result["observed_cash_change"]
        self.assertEqual(observed["status"], "observed")
        self.assertEqual(observed["elapsed_game_hours"], 124)
        self.assertEqual(observed["monthly_rate_changes"]["player_monthly_gross_income"]["delta_raw"], 0)
        self.assertEqual(observed["monthly_rate_changes"]["player_monthly_total_expenses"]["delta_raw"], -20000)
        self.assertEqual(observed["monthly_rate_changes"]["player_monthly_net_income"]["delta_raw"], 20000)
        self.assertEqual(observed["personal_gold_change"]["delta_raw"], -10000000)
        self.assertEqual(observed["verified_construction_gold_debit_raw"], 14250000)
        self.assertEqual(observed["personal_gold_residual_after_verified_debit_raw"], 4250000)
        self.assertTrue(result["readiness"]["player_net_monthly_change_ready"])
        self.assertTrue(observed["unallocated_other_transactions"])
        self.assertFalse(observed["building_attribution_ready"])
        self.assertFalse(observed["actual_roi_ready"])
        self.assertFalse(result["readiness"]["net_benefit_ready"])


if __name__ == "__main__":
    unittest.main()
