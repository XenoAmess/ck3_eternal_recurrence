"""Strict new monthly NET semantics; archived v1 packets retain their bytes."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from xar_autoplayer.bridge.war_cash_private_transport_v1 import (
    MONTHLY_FLOW_SEMANTICS, _monthly_flow,
)

def value(gross=500000, expenses=720000, net=-220000):
    return {"game_version": "1.20.0.3", "monthly_income_semantics": deepcopy(MONTHLY_FLOW_SEMANTICS),
            "player_monthly_gross_income": {"raw": gross, "scale": 100000},
            "player_monthly_total_expenses": {"raw": expenses, "scale": 100000},
            "player_monthly_net_income": {"raw": net, "scale": 100000},
            "readiness": {"monthly_gross_income_ready": True, "monthly_total_expenses_ready": True,
                          "monthly_net_income_ready": True},
            "monthly_gross_income_unavailable_reason": None,
            "monthly_total_expenses_unavailable_reason": None,
            "monthly_net_income_unavailable_reason": None}

def unavailable(row, field, flag, reason, message):
    row[field] = None
    row["readiness"][flag] = False
    row[reason] = message

class MonthlyNetIncomeWireTests(unittest.TestCase):
    def test_true_net_preserves_signed_zero_and_boundaries(self):
        for gross, expenses in ((500000, 720000), (0, 0), (-500000, -200000),
                                (-(1 << 63), 0), ((1 << 63)-1, 0)):
            with self.subTest(gross=gross, expenses=expenses):
                row = value(gross, expenses, gross-expenses)
                before = deepcopy(row)
                _monthly_flow(row)
                self.assertEqual(row, before)

    def test_gross_or_military_only_difference_cannot_be_net(self):
        for false_net in (500000, 200000, 0):
            with self.assertRaisesRegex(ValueError, "NET is not income minus total expenses"):
                _monthly_flow(value(net=false_net))

    def test_missing_complete_expenses_keeps_unknown_net(self):
        row = value()
        unavailable(row, "player_monthly_total_expenses", "monthly_total_expenses_ready",
                    "monthly_total_expenses_unavailable_reason", "native unavailable")
        with self.assertRaisesRegex(ValueError, "NET is not income minus total expenses"):
            _monthly_flow(row)
        unavailable(row, "player_monthly_net_income", "monthly_net_income_ready",
                    "monthly_net_income_unavailable_reason", "native unavailable")
        _monthly_flow(row)
        self.assertEqual(row["player_monthly_gross_income"]["raw"], 500000)
        self.assertIsNone(row["player_monthly_net_income"])

    def test_signed_overflow_is_explicit_unknown(self):
        for gross, expenses in ((-(1 << 63), 1), ((1 << 63)-1, -1)):
            row = value(gross, expenses, 0)
            unavailable(row, "player_monthly_net_income", "monthly_net_income_ready",
                        "monthly_net_income_unavailable_reason", "war_cash_monthly_net_income_overflow")
            _monthly_flow(row)
            row["monthly_net_income_unavailable_reason"] = "other"
            with self.assertRaisesRegex(ValueError, "unknown NET"):
                _monthly_flow(row)
        row = value()
        unavailable(row, "player_monthly_net_income", "monthly_net_income_ready",
                    "monthly_net_income_unavailable_reason", "war_cash_monthly_net_income_overflow")
        with self.assertRaisesRegex(ValueError, "unknown NET"):
            _monthly_flow(row)

    def test_wrong_month_scale_type_signed_range_are_rejected(self):
        for field in ("player_monthly_gross_income", "player_monthly_total_expenses", "player_monthly_net_income"):
            for bad in ({"raw": True, "scale": 100000}, {"raw": 1, "scale": 30},
                        {"raw": 1, "scale": 100000.0},
                        {"raw": 1 << 63, "scale": 100000}, {"raw": -(1 << 63)-1, "scale": 100000}):
                with self.subTest(field=field, bad=bad):
                    row = value(); row[field] = bad
                    with self.assertRaisesRegex(ValueError, "scalar is malformed"):
                        _monthly_flow(row)

    def test_exact3_scope_sources_and_military_inclusion_required(self):
        for key, bad in (("time_basis", "day"), ("source_scope", "military_only"),
                         ("income_source", "hud_fit"), ("expense_source", "current_military"),
                         ("military_expenses_included", False), ("military_expenses_included", 1)):
            row = value(); row["monthly_income_semantics"][key] = bad
            with self.assertRaisesRegex(ValueError, "exact-build semantics"):
                _monthly_flow(row)
        row = value(); row["game_version"] = "1.20.0.2"
        with self.assertRaisesRegex(ValueError, "exact-build semantics"):
            _monthly_flow(row)

    def test_unmarked_new_scalars_or_inconsistent_readiness_are_rejected(self):
        row = value(); row.pop("monthly_income_semantics")
        with self.assertRaisesRegex(ValueError, "semantics marker"):
            _monthly_flow(row)
        for key in ("monthly_gross_income_ready", "monthly_total_expenses_ready", "monthly_net_income_ready"):
            row = value(); row["readiness"][key] = 1
            with self.assertRaisesRegex(ValueError, "availability is inconsistent"):
                _monthly_flow(row)

    def test_legacy_v1_income_claim_is_preserved_without_true_net_marker(self):
        for version in ("1.20.0.2", "1.20.0.3"):
            legacy = {"game_version": version, "player_monthly_net_income": {"raw": 469417, "scale": 100000}}
            before = deepcopy(legacy)
            _monthly_flow(legacy)
            self.assertEqual(legacy, before)
            self.assertNotIn("monthly_income_semantics", legacy)

if __name__ == "__main__":
    unittest.main()
