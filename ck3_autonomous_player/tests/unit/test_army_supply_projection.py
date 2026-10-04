"""Focused fixtures for the archived native clamp and stock-state semantics."""

import importlib.util
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).resolve().parents[2] / "src/xar_autoplayer/bridge/army_supply_projection.py"
SPEC = importlib.util.spec_from_file_location("army_supply_projection_candidate", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
diagnose = MODULE.diagnose_frozen_supply


class ArmySupplyProjectionFixture(unittest.TestCase):
    def test_negative_rate_clamps_stock_and_keeps_attrition_independent(self):
        result = diagnose(stock_raw=100000, capacity_raw=10000000, monthly_change_raw=-454545, observed_current_attrition_raw=0)
        self.assertEqual(result["frozen_monthly_change_raw"], -454545)
        self.assertEqual(result["stock_after_one_successful_update_raw"], 0)
        self.assertEqual(result["milestones"]["zero_supplies"]["successful_update_events"], 1)
        self.assertEqual(result["stock_data_state"]["stock_data_base_attrition_raw"], 5000)
        self.assertEqual(result["observed_current_attrition_raw"], 0)
        self.assertIsNone(result["projected_final_native_attrition_raw"])
        self.assertIsNone(result["projected_casualties"])

    def test_exact_ten_boundary_and_observed_stocks_keep_event_units(self):
        boundary = diagnose(stock_raw=1000000, capacity_raw=30000000, monthly_change_raw=-454545)
        self.assertEqual(boundary["stock_data_state"]["stock_data_base_attrition_raw"], 0)
        self.assertEqual(boundary["milestones"]["below_10_supplies"]["successful_update_events"], 1)
        self.assertEqual(boundary["milestones"]["below_10_supplies"]["stock_data_base_attrition_raw"], 5000)
        low = diagnose(stock_raw=9999850, capacity_raw=10000000, monthly_change_raw=-454545, observed_current_attrition_raw=0)
        high = diagnose(stock_raw=30000000, capacity_raw=30000000, monthly_change_raw=-454545, observed_current_attrition_raw=0)
        self.assertEqual([low["milestones"][k]["successful_update_events"] for k in ("below_60_supplies", "below_10_supplies", "zero_supplies")], [9, 20, 22])
        self.assertEqual([high["milestones"][k]["successful_update_events"] for k in ("below_60_supplies", "below_10_supplies", "zero_supplies")], [53, 64, 67])
        self.assertEqual(low["milestones"]["below_10_supplies"]["stock_raw"], 908950)
        self.assertEqual(high["milestones"]["below_10_supplies"]["stock_raw"], 909120)
        for result in (low, high):
            self.assertIsNone(result["elapsed_days"])
            self.assertIsNone(result["depletion_date_raw"])
            self.assertEqual(result["observed_current_attrition_raw"], 0)
            self.assertIsNone(result["projected_final_native_attrition_raw"])


if __name__ == "__main__":
    unittest.main()
