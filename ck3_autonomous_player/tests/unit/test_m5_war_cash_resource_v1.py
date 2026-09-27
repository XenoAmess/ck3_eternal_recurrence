from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.m5_war_cash_resource_v1 import (
    observe_active_war_cash_resource_v1,
    require_complete_war_cash_resource_v1,
)

FRAME = {
    "played_character_id": 29829,
    "native_revision": 3,
    "date_raw": 53217624,
    "snapshot_id": "native:3",
    "revision": 4,
    "episode_run_id": "native-29829-2bc2d599f7f9",
}
WAR_ID = 16777231


def snapshot() -> dict[str, object]:
    return {
        **FRAME, "paused": True, "map_ready": True,
        "played_character_gold": {"raw": 111_861_020, "scale": 100_000},
        "active_wars": [{"war_id": WAR_ID}],
    }


def amount(raw: int, source: str) -> dict[str, object]:
    return {"raw": raw, "scale": 100_000, "source": source}


def complete_inputs() -> dict[str, object]:
    return {
        "source_frame": dict(FRAME), "war_id": WAR_ID,
        "pending_war_cash_raw": amount(2_000_000, "test-same-frame-pending"),
        "immediate_war_action_cost_raw": amount(1_000_000, "test-fee"),
        "future_war_cost_upper_raw": amount(6_000_000, "test-horizon-bound"),
        "future_risk_budget_raw": amount(2_000_000, "test-risk-allowance"),
        "policy_minimum_gold_reserve_raw": amount(3_000_000, "test-policy"),
        "horizon_days": 7,
        "future_bound_assumptions": ["synthetic seven-day bound"],
    }


class WarCashResourceTests(unittest.TestCase):
    def test_h2825_evidence_yields_typed_missing_not_zero(self) -> None:
        receipt = observe_active_war_cash_resource_v1(
            snapshot=snapshot(), war_id=WAR_ID,
            inputs={"source_frame": FRAME, "war_id": WAR_ID},
        )
        self.assertEqual(receipt["status"], "incomplete")
        self.assertEqual(receipt["observed_treasury_raw"], 111_861_020)
        self.assertIsNone(receipt["existing_shared_gold_commitment_raw"])
        self.assertIsNone(receipt["war_future_gold_cost_raw"])
        self.assertIn("future_war_cost_upper_raw", receipt["missing"])
        self.assertIn("policy_minimum_gold_reserve_raw", receipt["missing"])
        with self.assertRaisesRegex(ValueError, "complete same-frame"):
            require_complete_war_cash_resource_v1(
                receipt, frame=FRAME, war_id=WAR_ID,
            )

    def test_complete_resource_separates_pending_action_and_future_reserve(self) -> None:
        receipt = observe_active_war_cash_resource_v1(
            snapshot=snapshot(), war_id=WAR_ID, inputs=complete_inputs(),
        )
        self.assertEqual(receipt["status"], "complete")
        self.assertEqual(receipt["existing_shared_gold_commitment_raw"], 2_000_000)
        self.assertEqual(receipt["immediate_war_action_cost_raw"], 1_000_000)
        self.assertEqual(receipt["war_future_gold_cost_raw"], 8_000_000)
        self.assertEqual(receipt["joint_gold_reserve_raw"], 11_000_000)
        self.assertEqual(receipt["horizon_days"], 7)
        self.assertEqual(
            require_complete_war_cash_resource_v1(
                receipt, frame=FRAME, war_id=WAR_ID,
            )["war_id"], WAR_ID,
        )

    def test_stale_frame_and_wrong_war_are_rejected(self) -> None:
        inputs = complete_inputs()
        inputs["source_frame"] = {**FRAME, "revision": 5}
        with self.assertRaisesRegex(ValueError, "full paused frame"):
            observe_active_war_cash_resource_v1(
                snapshot=snapshot(), war_id=WAR_ID, inputs=inputs,
            )
        inputs = complete_inputs()
        inputs["war_id"] = WAR_ID + 1
        with self.assertRaisesRegex(ValueError, "WarID"):
            observe_active_war_cash_resource_v1(
                snapshot=snapshot(), war_id=WAR_ID, inputs=inputs,
            )

    def test_unproved_zero_and_forged_reserve_are_rejected(self) -> None:
        inputs = complete_inputs()
        inputs["pending_war_cash_raw"] = 0
        with self.assertRaisesRegex(ValueError, "sourced nonnegative"):
            observe_active_war_cash_resource_v1(
                snapshot=snapshot(), war_id=WAR_ID, inputs=inputs,
            )
        receipt = observe_active_war_cash_resource_v1(
            snapshot=snapshot(), war_id=WAR_ID, inputs=complete_inputs(),
        )
        forged = deepcopy(receipt)
        forged["joint_gold_reserve_raw"] = 0
        with self.assertRaisesRegex(ValueError, "does not balance"):
            require_complete_war_cash_resource_v1(
                forged, frame=FRAME, war_id=WAR_ID,
            )


if __name__ == "__main__":
    unittest.main()
