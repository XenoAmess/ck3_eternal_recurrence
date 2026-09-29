from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.activity_feast_stage5_value_policy import assess_feast_stage5_start


def _assess(**changes: object) -> dict[str, object]:
    request: dict[str, object] = {
        "activity_key": "activity_feast",
        "selected_option_key": "feast_type_generic",
        "planning_stage": 5,
        "final_can_start": True,
        "configured_cost_raw": [1_000_000, 0, 0, 0],
        "balance_available": [True, False, False, False],
        "balance_raw": [12_000_000, 0, 0, 0],
        "reserved_raw": [2_000_000, 0, 0, 0],
        "expected_nonhost_guest_count": 3,
        "peaceful_spend_allowed": True,
        "gold_floor_raw": 3_000_000,
        "active_war_count": 1,
        "war_cash_reserve_raw": 4_000_000,
    }
    request.update(changes)
    return assess_feast_stage5_start(**request)


class FeastStage5ValuePolicyTests(unittest.TestCase):
    def test_positive_generic_feast_can_reserve_only_observed_charges(self) -> None:
        result = _assess()
        self.assertEqual(result["decision"], "start")
        self.assertEqual(result["status"], "ready")
        self.assertTrue(result["positive_value_supported"])
        self.assertEqual(result["resource_commitment_raw"], [1_000_000, 0, 0, 0])
        self.assertEqual(result["submit_reserve_raw"], [9_000_000, 0, 0, 0])
        self.assertEqual(result["scale"], 100_000)

    def test_missing_guests_final_gate_or_cost_cannot_approve_start(self) -> None:
        self.assertEqual(_assess(expected_nonhost_guest_count=None)["reason"], "guest_route_unproven")
        self.assertEqual(_assess(final_can_start=False)["reason"], "native_final_start_unavailable")
        missing = _assess(configured_cost_raw=[None, 0, 0, 0])
        self.assertEqual(missing["reason"], "configured_cost_unobserved")
        self.assertEqual(missing["status"], "missing_input")
        self.assertTrue(missing["positive_value_supported"])

    def test_unknown_war_cash_is_not_zero_and_peaceful_budget_is_explicit(self) -> None:
        missing = _assess(war_cash_reserve_raw=None)
        self.assertEqual(missing["reason"], "war_cash_reserve_unobserved")
        self.assertEqual(missing["status"], "missing_input")
        self.assertEqual(_assess(peaceful_spend_allowed=None)["reason"], "peaceful_spend_unapproved")
        self.assertEqual(_assess(gold_floor_raw=None)["reason"], "gold_reserve_unobserved")
        self.assertEqual(_assess(balance_raw=[9_999_999, 0, 0, 0])["reason"], "gold_budget_exceeded")

    def test_positive_other_resource_requires_real_balance(self) -> None:
        self.assertEqual(
            _assess(configured_cost_raw=[0, 500_000, 0, 0])["reason"],
            "treasury_balance_unobserved",
        )
        self.assertEqual(
            _assess(
                configured_cost_raw=[0, 500_000, 0, 0],
                balance_available=[False, True, False, False],
                balance_raw=[0, 750_000, 0, 0],
                reserved_raw=[0, 250_001, 0, 0],
            )["reason"],
            "treasury_budget_exceeded",
        )
        free = _assess(
            configured_cost_raw=[0, 0, 0, 0],
            balance_available=[False, False, False, False],
            gold_floor_raw=None,
            active_war_count=None,
            war_cash_reserve_raw=None,
        )
        self.assertEqual(free["decision"], "start")
        self.assertEqual(free["submit_reserve_raw"], [2_000_000, 0, 0, 0])

    def test_wrong_activity_and_invalid_vectors_never_signal_start(self) -> None:
        self.assertEqual(_assess(selected_option_key="feast_type_murder")["reason"], "unsupported_activity_or_type")
        with self.assertRaisesRegex(ValueError, "four named resources"):
            _assess(configured_cost_raw=[1, 2])
        with self.assertRaisesRegex(ValueError, "nonnegative"):
            _assess(reserved_raw=[-1, 0, 0, 0])


if __name__ == "__main__":
    unittest.main()
