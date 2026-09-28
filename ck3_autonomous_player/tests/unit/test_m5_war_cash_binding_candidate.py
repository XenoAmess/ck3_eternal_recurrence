from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.m5_war_cash_binding_candidate import (
    add_independent_cash_reserves_v1,
    require_structural_action_quote_binding_v1,
)


FRAME = {
    "played_character_id": 29829, "snapshot_id": "native:9",
    "revision": 10, "native_revision": 9, "date_raw": 53219112,
    "episode_run_id": "native-29829-test",
}
WAR_ID = 16777231


def move_plan() -> dict[str, object]:
    return {
        "selected_step": "move-army-71-to-2614",
        "priced_command": {
            "kind": "move_army", "army_id": 71,
            "origin_province_id": 83886367,
            "target_province_id": 2614,
            "route_province_ids": [83886367, 2614],
            "route_preview_query_sequence": 14,
        },
    }


def quote(plan: dict[str, object]) -> dict[str, object]:
    return {
        "source_frame": dict(FRAME), "war_id": WAR_ID,
        "selected_step": plan["selected_step"],
        "priced_command": deepcopy(plan["priced_command"]),
        "quoted_cost_raw": 1_000_000, "scale": 100_000,
        "native_quote_id": "synthetic-quote-1",
    }


class WarCashBindingCandidateTests(unittest.TestCase):
    def test_move_quote_is_structural_only(self) -> None:
        plan = move_plan()
        result = require_structural_action_quote_binding_v1(
            plan=plan, quote=quote(plan), frame=FRAME, war_id=WAR_ID,
        )
        self.assertEqual(result["quoted_cost_raw"], 1_000_000)
        self.assertFalse(result["same_frame_native_quote_proven"])
        self.assertFalse(result["formal_cash_eligible"])

    def test_same_frame_repriced_action_and_route_cannot_reuse_quote(self) -> None:
        plan = move_plan()
        old = quote(plan)
        changed = deepcopy(plan)
        changed["priced_command"]["route_preview_query_sequence"] = 15
        with self.assertRaisesRegex(ValueError, "selected command"):
            require_structural_action_quote_binding_v1(
                plan=changed, quote=old, frame=FRAME, war_id=WAR_ID,
            )
        changed = deepcopy(plan)
        changed["selected_step"] = "move-army-71-to-2615"
        with self.assertRaisesRegex(ValueError, "selected command"):
            require_structural_action_quote_binding_v1(
                plan=changed, quote=old, frame=FRAME, war_id=WAR_ID,
            )
        changed = deepcopy(plan)
        changed["priced_command"]["route_province_ids"] = [83886367, 2613, 2614]
        with self.assertRaisesRegex(ValueError, "selected command"):
            require_structural_action_quote_binding_v1(
                plan=changed, quote=old, frame=FRAME, war_id=WAR_ID,
            )

    def test_cross_frame_and_war_quote_are_rejected(self) -> None:
        plan = move_plan()
        old = quote(plan)
        with self.assertRaisesRegex(ValueError, "frame"):
            require_structural_action_quote_binding_v1(
                plan=plan, quote=old,
                frame={**FRAME, "native_revision": 10}, war_id=WAR_ID,
            )
        with self.assertRaisesRegex(ValueError, "WarID"):
            require_structural_action_quote_binding_v1(
                plan=plan, quote=old, frame=FRAME, war_id=WAR_ID + 1,
            )

    def test_read_only_query_zero_is_not_a_native_zero_proof(self) -> None:
        plan = {
            "selected_step": "query-war-termination-options-16777231",
            "priced_command": {
                "kind": "read_only_query", "war_id": WAR_ID,
                "query_name": "war_termination_options",
            },
        }
        candidate = quote(plan)
        candidate["quoted_cost_raw"] = 0
        result = require_structural_action_quote_binding_v1(
            plan=plan, quote=candidate, frame=FRAME, war_id=WAR_ID,
        )
        self.assertEqual(result["quoted_cost_raw"], 0)
        self.assertFalse(result["native_quote_pure_read_proven"])
        self.assertFalse(result["formal_cash_eligible"])

    def test_query_name_cannot_price_another_selected_query_step(self) -> None:
        plan = {
            "selected_step": "query-other-war-step",
            "priced_command": {
                "kind": "read_only_query", "war_id": WAR_ID,
                "query_name": "war_termination_options",
            },
        }
        # Even a quote which repeats all the plan's mislabeled identity must
        # not price another command through the same zero-cost query.
        with self.assertRaisesRegex(ValueError, "read-only query identity"):
            require_structural_action_quote_binding_v1(
                plan=plan, quote=quote(plan), frame=FRAME, war_id=WAR_ID,
            )
        plan["selected_step"] = f"query-unknown-options-{WAR_ID}"
        plan["priced_command"]["query_name"] = "unknown_options"
        with self.assertRaisesRegex(ValueError, "read-only query identity"):
            require_structural_action_quote_binding_v1(
                plan=plan, quote=quote(plan), frame=FRAME, war_id=WAR_ID,
            )

    def test_independent_reserves_close_max_gap(self) -> None:
        # With 400 gold treasury, 100 gold action and independent 200 + 150
        # gold floors, max(200, 150) admits a spend that the sum rejects.
        result = add_independent_cash_reserves_v1(
            construction_policy_floor_raw=20_000_000,
            future_war_cost_upper_raw=10_000_000,
            future_risk_budget_raw=2_000_000,
            war_policy_minimum_raw=3_000_000,
        )
        self.assertEqual(result["required_global_gold_reserve_raw"], 35_000_000)
        self.assertLessEqual(10_000_000 + max(20_000_000, 15_000_000), 40_000_000)
        self.assertGreater(10_000_000 + result["required_global_gold_reserve_raw"],
                           40_000_000)
        self.assertFalse(result["formal_action_ready"])

    def test_missing_or_overflowed_reserve_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Q100000"):
            add_independent_cash_reserves_v1(
                construction_policy_floor_raw=20_000_000,
                future_war_cost_upper_raw=None,
                future_risk_budget_raw=0,
                war_policy_minimum_raw=0,
            )
        with self.assertRaisesRegex(ValueError, "overflow"):
            add_independent_cash_reserves_v1(
                construction_policy_floor_raw=(1 << 63) - 1,
                future_war_cost_upper_raw=1,
                future_risk_budget_raw=0,
                war_policy_minimum_raw=0,
            )


if __name__ == "__main__":
    unittest.main()
