"""Read-only target seeds for a player's active-combat retreat preview."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.native_driver import (  # noqa: E402
    _action_steps,
    _active_combat_retreat_preview_steps,
)
from xar_autoplayer.bridge.war_contract import (  # noqa: E402
    PREVIEW_MOVE_ARMY_CAPABILITY,
    move_army_step,
    preview_move_army_step,
)
from xar_autoplayer.bridge.active_combat_retreat_contract import (  # noqa: E402
    preview_active_combat_retreat_v1_step,
)


def _steps(*, enemy_at_ally: bool = False, paused: bool = True) -> set[str]:
    enemies = [
        {
            "army_id": 201,
            "current_province_id": 20,
            "move_target_province_id": 12 if enemy_at_ally else None,
            "route_province_ids": [12] if enemy_at_ally else [],
            "army_state": "regular",
        }
    ]
    return set(
        _action_steps(
            [PREVIEW_MOVE_ARMY_CAPABILITY],
            active_wars=[
                {
                    "enemy_armies": enemies,
                    "allied_armies": [
                        {
                            "army_id": 301,
                            "current_province_id": 13,
                            "army_state": "regular",
                        },
                        {
                            "army_id": 302,
                            "current_province_id": 14,
                            "army_state": "combat",
                        },
                    ],
                    "war_objective_province_ids": [],
                }
            ],
            player_armies=[
                {
                    "army_id": 101,
                    "current_province_id": 10,
                    "controllable": True,
                    "in_combat": True,
                    "army_state": "combat",
                },
                {
                    "army_id": 102,
                    "current_province_id": 11,
                    "controllable": True,
                    "army_state": "regular",
                },
                {
                    "army_id": 103,
                    "current_province_id": 12,
                    "controllable": True,
                    "army_state": "sieging",
                },
            ],
            paused=paused,
        )
    )


class ActiveCombatRetreatDestinationSeedTests(unittest.TestCase):
    def test_stationary_friendly_positions_offer_preview_only(self) -> None:
        steps = _steps()
        self.assertIn(preview_move_army_step(101, 11), steps)
        self.assertIn(preview_move_army_step(101, 12), steps)
        self.assertNotIn(move_army_step(101, 11), steps)
        self.assertNotIn(move_army_step(101, 12), steps)
        self.assertNotIn(preview_move_army_step(101, 13), steps)
        self.assertNotIn(preview_move_army_step(101, 14), steps)
        typed = _active_combat_retreat_preview_steps(
            {
                "paused": True,
                "player_armies": [
                    {
                        "army_id": 101,
                        "current_province_id": 10,
                        "controllable": True,
                        "in_combat": True,
                    }
                ],
            },
            steps,
        )
        self.assertIn(preview_active_combat_retreat_v1_step(101, 11), typed)
        self.assertIn(preview_active_combat_retreat_v1_step(101, 12), typed)

    def test_hostile_route_and_unpaused_frame_suppress_seeds(self) -> None:
        steps = _steps(enemy_at_ally=True)
        self.assertIn(preview_move_army_step(101, 11), steps)
        self.assertNotIn(preview_move_army_step(101, 12), steps)
        unpaused = _steps(paused=False)
        self.assertNotIn(preview_move_army_step(101, 11), unpaused)
        self.assertNotIn(preview_move_army_step(101, 12), unpaused)


if __name__ == "__main__":
    unittest.main()
