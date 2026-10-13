from __future__ import annotations

import os
from pathlib import Path
import sys
import unittest


UNIT_ROOT = Path(os.environ.get(
    "XAR_ARMY_ORDERS_UNIT_ROOT", str(Path(__file__).resolve().parent)
))
sys.path.insert(0, str(UNIT_ROOT))

from test_gameplay_bridge import _army, _native_war_plan, _preview_row


def _deferred_destination(index: int, target: int) -> dict[str, object]:
    row = _preview_row(
        index, origin=2585, target=target, date_raw=24_000, route=[]
    )
    row["result"].update(accepted=False, status="deferred")
    row["result"]["route_preview"].update(
        status="deferred",
        reason="army_not_move_ready",
        native_rejection_stage="move_mode_unavailable",
        native_error="CK3 army has no move mode for the destination",
    )
    return row


class OrdinaryArmyDestinationMoveModeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.player = _army(
            11, soldiers=900, province_id=2585, controllable=True,
            army_state="sieging", route_province_ids=[],
        )
        self.enemy = _army(
            21, soldiers=800, province_id=2600, controllable=False,
            move_target_province_id=2585, army_state="moving",
            route_province_ids=[2596, 2585],
        )

    def _plan(self, history, steps):
        return _native_war_plan(
            player=self.player, enemies=[self.enemy], score=24,
            date_raw=24_000, objectives=[2585, 2510, 2520],
            history=history, steps=steps,
        )

    def test_destination_rejection_previews_next_objective_under_threat(self) -> None:
        plan = self._plan(
            [_deferred_destination(1, 2510)],
            ("preview-move-army-11-to-2520", "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_route_preview", plan)
        self.assertEqual(
            plan["selected_step"], "preview-move-army-11-to-2520", plan
        )
        self.assertIn(
            {
                "target_province_id": 2510,
                "status": "move_mode_unavailable",
                "native_rejection_stage": "move_mode_unavailable",
            },
            plan["route_rejections"],
        )
        self.assertNotEqual(plan["selected_step"], "life-advance")

    def test_next_available_preview_still_uses_existing_route_audit(self) -> None:
        plan = self._plan(
            [
                _deferred_destination(1, 2510),
                _preview_row(
                    2, origin=2585, target=2520, date_raw=24_000,
                    route=[2470, 2520],
                ),
            ],
            ("move-army-11-to-2520", "life-advance"),
        )

        self.assertEqual(plan["selected_step"], "move-army-11-to-2520", plan)
        self.assertEqual(plan["phase"], "native_war_pursuit", plan)
        self.assertNotEqual(plan["selected_step"], "life-advance")

    def test_all_destination_rejections_keep_no_safe_route_outcome(self) -> None:
        plan = self._plan(
            [
                _deferred_destination(1, 2510),
                _deferred_destination(2, 2520),
            ],
            ("life-advance",),
        )

        self.assertEqual(plan["phase"], "native_war_no_safe_exact_route", plan)
        self.assertIsNone(plan["selected_step"])
        self.assertEqual(plan["required_step"], "safe-exact-war-route")
        rejected = [
            row["target_province_id"]
            for row in plan["route_rejections"]
            if row.get("status") == "move_mode_unavailable"
        ]
        self.assertEqual(rejected, [2510, 2520])


if __name__ == "__main__":
    unittest.main(verbosity=2)
