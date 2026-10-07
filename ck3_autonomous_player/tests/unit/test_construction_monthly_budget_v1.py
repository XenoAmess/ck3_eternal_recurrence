"""Controlled .4 fixtures for cash math; no native/live qualification claim."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.construction_monthly_budget_v1 import (
    project_construction_monthly_budget_v1,
    query_construction_monthly_budget_private_v1,
)
from xar_autoplayer.bridge.version_identity import CK3_12003, CK3_12004
from xar_autoplayer.bridge.war_cash_private_transport_v1 import (
    MONTHLY_FLOW_SEMANTICS, MONTHLY_FLOW_SEMANTICS_12004,
)


def cash_fixture(*, gold=10_000_000, gross=800_000, expenses=1_000_000,
                 current=500_000, all_raised=800_000, build=CK3_12004):
    def military(amount):
        vector = [amount, 0, 0, 0, 0, 0, 9_000_000, 0, 0, 0]
        return {
            "status": "available", "unavailable_reason": None,
            "resource_raw_native": vector, "gold_raw": amount,
            "treasury_raw": vector[6], "raw_scale": 100_000,
            "owner_character_id": 29829, "resource_id": "29829",
            "war_ids": [117440524], "time_basis": "month",
            "source_scope": "actor_owned_military_once_across_all_wars",
            "future_war_cost_upper_ready": False,
        }

    return {
        "schema": "xar.ck3.war-cash-current-resources.v1", "status": "available",
        "read_only": True, "advertised": False, "formal_action_ready": False,
        "game_version": build.game_version, "executable_sha256": build.executable_sha256,
        "played_character_id": 29829, "snapshot_revision": 2, "date_raw": 53288256,
        "queried_snapshot_id": "controlled-fixture:2", "queried_revision": 3,
        "queried_native_revision": 2, "active_war_ids": [117440524],
        "player_army_ids": [0, 218104048],
        "current_treasury": {"raw": gold, "scale": 100_000},
        "player_monthly_gross_income": {"raw": gross, "scale": 100_000},
        "player_monthly_total_expenses": {"raw": expenses, "scale": 100_000},
        "player_monthly_net_income": {"raw": gross - expenses, "scale": 100_000},
        "monthly_income_semantics": deepcopy(
            MONTHLY_FLOW_SEMANTICS_12004 if build == CK3_12004 else MONTHLY_FLOW_SEMANTICS),
        "current_treasury_unavailable_reason": None,
        "monthly_gross_income_unavailable_reason": None,
        "monthly_total_expenses_unavailable_reason": None,
        "monthly_net_income_unavailable_reason": None,
        "military_expenses": {"current": military(current), "all_raised": military(all_raised)},
        "readiness": {
            "current_treasury_ready": True, "monthly_gross_income_ready": True,
            "monthly_total_expenses_ready": True, "monthly_net_income_ready": True,
            "current_military_expenses_ready": True, "all_raised_military_expenses_ready": True,
            "same_frame_ready": True,
        },
    }


def project(cash, **overrides):
    return project_construction_monthly_budget_v1(cash, **{
        "construction_gold_cost_raw": 1_000_000, "reserve_gold_raw": 3_000_000,
        "existing_commitment_gold_raw": 2_000_000, "horizon_months": 4,
        **overrides,
    })


class ConstructionMonthlyBudgetTests(unittest.TestCase):
    def test_negative_net_and_all_raised_replacement_count_expense_once(self):
        cash = cash_fixture()
        before = deepcopy(cash)
        result = project(cash)
        current, raised = (result["scenarios"][key] for key in ("current", "all_raised"))
        self.assertEqual(current["net_monthly_gold_raw"], -200_000)
        self.assertEqual(current["cash_after_construction_and_commitments_raw"], 7_000_000)
        self.assertEqual(current["projected_ending_gold_raw"], 6_200_000)
        self.assertEqual(current["burn_reservation_raw"], 800_000)
        self.assertEqual(current["minimum_projected_gold_raw"], 6_200_000)
        self.assertEqual(current["maximum_one_off_spend_raw"], 4_200_000)
        self.assertTrue(current["scenario_floor_ready"])
        self.assertIsNone(current["first_month_reserve_breach"])
        self.assertEqual(raised["net_monthly_gold_raw"], -500_000)
        self.assertEqual(raised["projected_ending_gold_raw"], 5_000_000)
        self.assertEqual(raised["burn_reservation_raw"], 2_000_000)
        self.assertEqual(raised["maximum_one_off_spend_raw"], 3_000_000)
        self.assertEqual(cash, before)
        self.assertFalse(result["future_war_cost_upper_ready"])
        self.assertFalse(result["per_regiment_upkeep_ready"])
        self.assertIsNone(result["selected_step"])
        self.assertFalse(result["formal_action_ready"])

    def test_positive_income_does_not_fund_extra_upfront_spend(self):
        result = project(cash_fixture(gross=1_200_000, current=300_000),
                         construction_gold_cost_raw=4_000_000,
                         existing_commitment_gold_raw=1_000_000)
        current = result["scenarios"]["current"]
        self.assertEqual(current["net_monthly_gold_raw"], 200_000)
        self.assertEqual(current["projected_ending_gold_raw"], 5_800_000)
        self.assertEqual(current["minimum_projected_gold_raw"], 5_000_000)
        self.assertEqual(current["burn_reservation_raw"], 0)
        self.assertEqual(current["maximum_one_off_spend_raw"], 6_000_000)
        raised = result["scenarios"]["all_raised"]
        self.assertEqual(raised["net_monthly_gold_raw"], -300_000)
        self.assertEqual(raised["projected_ending_gold_raw"], 3_800_000)

    def test_observed_zero_is_available_and_treasury_slot_is_not_gold(self):
        result = project(cash_fixture(gross=0, expenses=0, current=0, all_raised=0))
        self.assertEqual(result["status"], "available")
        for row in result["scenarios"].values():
            self.assertTrue(row["scenario_ready"])
            self.assertEqual(row["net_monthly_gold_raw"], 0)
            self.assertEqual(row["burn_reservation_raw"], 0)
            self.assertEqual(row["minimum_projected_gold_raw"], 7_000_000)
            self.assertEqual(row["maximum_one_off_spend_raw"], 5_000_000)
        self.assertEqual(result["source_cash_resources"]["military_expenses"]["current"]["treasury_raw"], 9_000_000)

    def test_reserve_breach_is_strict_and_month_zero_means_upfront_shortfall(self):
        cash = cash_fixture(gold=5_000_000, gross=500_000)
        result = project(cash, reserve_gold_raw=2_000_000,
                         existing_commitment_gold_raw=1_000_000)
        row = result["scenarios"]["current"]
        self.assertEqual(row["minimum_projected_gold_raw"], 1_000_000)
        self.assertFalse(row["scenario_floor_ready"])
        self.assertEqual(row["first_month_reserve_breach"], 3)
        upfront = project(cash, construction_gold_cost_raw=3_000_000,
                          reserve_gold_raw=2_000_000,
                          existing_commitment_gold_raw=1_000_000)
        self.assertEqual(upfront["scenarios"]["current"]["first_month_reserve_breach"], 0)

    def test_missing_all_raised_preserves_independent_current_scenario(self):
        cash = cash_fixture()
        cash["status"] = "partial"
        cash["readiness"]["all_raised_military_expenses_ready"] = False
        cash["military_expenses"]["all_raised"].update(
            status="unavailable", unavailable_reason="native_all_raised_maintenance_unavailable",
            resource_raw_native=None, gold_raw=None, treasury_raw=None)
        result = project(cash)
        self.assertEqual(result["status"], "partial")
        self.assertTrue(result["scenarios"]["current"]["scenario_ready"])
        raised = result["scenarios"]["all_raised"]
        self.assertFalse(raised["scenario_ready"])
        self.assertIsNone(raised["net_monthly_gold_raw"])
        self.assertIsNone(raised["burn_reservation_raw"])
        self.assertIsNone(raised["scenario_floor_ready"])
        self.assertEqual(raised["missing_inputs"], {
            "military_expenses.all_raised": "native_all_raised_maintenance_unavailable"})

    def test_unknown_full_expenses_and_net_remain_partial(self):
        cash = cash_fixture()
        for field, flag, reason in (
            ("player_monthly_total_expenses", "monthly_total_expenses_ready", "monthly_total_expenses_unavailable_reason"),
            ("player_monthly_net_income", "monthly_net_income_ready", "monthly_net_income_unavailable_reason"),
        ):
            cash[field] = None
            cash["readiness"][flag] = False
            cash[reason] = "native_total_expense_read_failed"
        result = project(cash)
        for row in result["scenarios"].values():
            self.assertFalse(row["scenario_ready"])
            self.assertIsNone(row["maximum_one_off_spend_raw"])
            self.assertIsNone(row["projected_ending_gold_raw"])
            self.assertEqual(row["missing_inputs"]["player_monthly_net_income"], "native_total_expense_read_failed")

    def test_unknown_wallet_and_unready_frame_never_create_cash(self):
        cash = cash_fixture()
        cash["current_treasury"] = None
        cash["readiness"]["current_treasury_ready"] = False
        cash["current_treasury_unavailable_reason"] = "war_cash_treasury_unavailable"
        result = project(cash)
        for row in result["scenarios"].values():
            self.assertIsNone(row["cash_after_construction_and_commitments_raw"])
            self.assertIsNone(row["minimum_projected_gold_raw"])
            self.assertEqual(row["missing_inputs"]["current_treasury"], "war_cash_treasury_unavailable")
        cash = cash_fixture()
        cash["readiness"]["same_frame_ready"] = False
        self.assertIsNone(project(cash)["scenarios"]["current"]["cash_after_construction_and_commitments_raw"])

    def test_exact3_and_exact4_remain_distinct_and_legacy_net_is_rejected(self):
        for build in (CK3_12003, CK3_12004):
            result = project(cash_fixture(build=build))
            self.assertEqual(result["game_version"], build.game_version)
            self.assertEqual(result["executable_sha256"], build.executable_sha256)
        legacy = cash_fixture()
        for field in ("monthly_income_semantics", "player_monthly_gross_income", "player_monthly_total_expenses"):
            legacy.pop(field)
        with self.assertRaisesRegex(ValueError, "v2 NET semantics marker"):
            project(legacy)
        wrong_net = cash_fixture()
        wrong_net["player_monthly_net_income"]["raw"] = 800_000
        with self.assertRaisesRegex(ValueError, "NET is not income minus total expenses"):
            project(wrong_net)
        wrong_build = cash_fixture()
        wrong_build["executable_sha256"] = CK3_12003.executable_sha256
        with self.assertRaisesRegex(ValueError, "frozen exact build"):
            project(wrong_build)

    def test_query_once_keeps_source_and_rejects_invalid_policy_before_query(self):
        class Driver:
            def __init__(self):
                self.calls = []

            def query_war_cash_current_resources_private_v1(self, *, expected_revision):
                self.calls.append(expected_revision)
                return cash_fixture()

        driver = Driver()
        result = query_construction_monthly_budget_private_v1(
            driver, expected_revision=3, construction_gold_cost_raw=1_000_000,
            reserve_gold_raw=3_000_000, existing_commitment_gold_raw=2_000_000,
            horizon_months=4)
        self.assertEqual(driver.calls, [3])
        self.assertEqual(result["source"], "ck3_query_war_cash_current_resources_private_v1")
        self.assertEqual(result["source_frame"]["queried_revision"], 3)
        for overrides in (
            {"horizon_months": 0}, {"horizon_months": 25}, {"horizon_months": True},
            {"horizon_months": 1.0}, {"construction_gold_cost_raw": -1},
            {"reserve_gold_raw": True}, {"existing_commitment_gold_raw": -1},
        ):
            args = {"construction_gold_cost_raw": 0, "reserve_gold_raw": 0,
                    "existing_commitment_gold_raw": 0, "horizon_months": 1,
                    **overrides}
            with self.assertRaises(ValueError):
                query_construction_monthly_budget_private_v1(driver, expected_revision=3, **args)
        self.assertEqual(driver.calls, [3])


if __name__ == "__main__":
    unittest.main()
