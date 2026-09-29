"""Focused source-to-budget checks for a bounded feast Start trial."""

from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.activity_feast_stage5_budget_v1 import (
    observe_feast_start_budget_v1,
)
from xar_autoplayer.activity_feast_stage5_start_formal_consumer import (
    assess_feast_start_private_v1,
)
from xar_autoplayer.construction_formal_consumer import (
    read_construction_ledger, write_construction_ledger,
)


def _inputs() -> dict[str, object]:
    return {
        "schema": "activity-feast-stage5-start-inputs-private-v1",
        "snapshot_revision": 3, "queried_revision": 5,
        "queried_snapshot_id": "native:3", "post_snapshot_id": "native:3",
        "date_raw": 53219928, "actor_character_id": 29829,
        "activity_key": "activity_feast", "selected_option_key": "feast_type_generic",
        "planning_stage": 5, "final_can_start": True,
        "native_guest_route_qualified": True, "guest_join_status": "observed",
        "arrival_time_observed": True, "timely_positive_join_count": 1,
        "resources": {
            key: {"configured_cost_raw": 1_000_000 if key == "gold" else 0}
            for key in ("gold", "treasury", "piety", "barter_goods")
        },
        "balances": {
            "gold": {"available": True, "raw": 120_000_000},
            **{key: {"available": False, "raw": None}
               for key in ("treasury", "piety", "barter_goods")},
        },
    }


def _snapshot() -> dict[str, object]:
    return {
        "paused": True, "map_ready": True,
        "played_character": {"character_id": 29829},
        "native_revision": 3, "revision": 5,
        "date_raw": 53219928, "snapshot_id": "native:3",
        "active_wars": [], "pending_character_interaction": None,
    }


class FeastStage5BudgetTest(unittest.TestCase):
    def test_peaceful_exclusive_lane_reaches_value_policy(self) -> None:
        with TemporaryDirectory() as temp:
            inputs = _inputs()
            observed = observe_feast_start_budget_v1(
                _snapshot(), inputs, state_dir=Path(temp))
            self.assertEqual(observed["status"], "observed")
            self.assertEqual(observed["budget"]["reserved_raw"]["gold"], 0)
            decision = assess_feast_start_private_v1(
                inputs, guest=None, budget=observed["budget"])
            self.assertEqual(decision["decision"], "start")

    def test_war_cash_remains_unknown_and_pending_interaction_holds(self) -> None:
        with TemporaryDirectory() as temp:
            inputs = _inputs()
            snapshot = _snapshot()
            snapshot["active_wars"] = [{"war_id": 11}]
            observed = observe_feast_start_budget_v1(
                snapshot, inputs, state_dir=Path(temp))
            self.assertEqual(observed["budget"]["active_war_count"], 1)
            decision = assess_feast_start_private_v1(
                inputs, guest=None, budget=observed["budget"])
            self.assertEqual(decision["reason"], "war_cash_reserve_unobserved")
            snapshot["pending_character_interaction"] = {"instance_id": 44}
            observed = observe_feast_start_budget_v1(
                snapshot, inputs, state_dir=Path(temp))
            self.assertIsNone(observed["budget"])

    def test_changed_paused_frame_has_no_budget(self) -> None:
        with TemporaryDirectory() as temp:
            snapshot = _snapshot()
            snapshot["native_revision"] += 1
            observed = observe_feast_start_budget_v1(
                snapshot, _inputs(), state_dir=Path(temp))
            self.assertEqual(observed["reason"], "budget_frame_unobserved")
            self.assertIsNone(observed["budget"])

    def test_unresolved_paid_construction_keeps_reservation_unknown(self) -> None:
        with TemporaryDirectory() as temp:
            state_dir = Path(temp)
            ledger = read_construction_ledger(state_dir)
            write_construction_ledger(state_dir, {
                **ledger, "pending": {"request_id": "still-unresolved"},
            })
            observed = observe_feast_start_budget_v1(
                _snapshot(), _inputs(), state_dir=state_dir)
            self.assertEqual(observed["reason"], "construction_pending")
            self.assertIsNone(observed["budget"])


if __name__ == "__main__":
    unittest.main()
