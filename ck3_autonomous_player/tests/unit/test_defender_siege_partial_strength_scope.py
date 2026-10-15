from __future__ import annotations

import unittest

from xar_autoplayer.strategy import (
    _primary_defender_siege_relief_assessment,
    _same_frame_army_strength_balance,
)

class DefenderSiegePartialStrengthScopeTests(unittest.TestCase):
    def _frame(self) -> dict[str, object]:
        player = {
            "army_id": 11, "current_province_id": 30,
            "army_state": "regular", "army_state_code": 1,
            "in_combat": False, "retreating": False,
            "move_target_province_id": None, "route_province_ids": [],
        }
        enemy = {
            "army_id": 21, "current_province_id": 32,
            "army_state": "sieging", "army_state_code": 3,
            "in_combat": False, "retreating": False,
            "move_target_province_id": None, "route_province_ids": [],
        }
        return {
            "date_raw": 53_328_720, "paused": True, "map_ready": True,
            "active_event": None, "pending_character_interaction": None,
            "player_armies": [player],
            "active_wars": [{
                "war_id": 95, "player_side": "defender",
                "player_is_primary_war_leader": True,
                "player_relative_war_score": 3,
                "allied_armies": [player], "enemy_armies": [enemy],
            }],
            "army_strengths_status": "available",
            "army_strengths": [
                {
                    "army_id": 11, "status": "available", "scope_role": "player",
                    "war_ids": [95], "current_soldiers": 2300,
                    "maximum_soldiers": 2500, "ai_base_power_raw": 5500000000,
                },
                {
                    "army_id": 21, "status": "available",
                    "scope_role": "active_war_enemy", "war_ids": [95],
                    "current_soldiers": 800, "maximum_soldiers": 900,
                    "ai_base_power_raw": 2000000000,
                },
            ],
        }

    def _relief(self, frame: dict[str, object]) -> dict[str, object]:
        return _primary_defender_siege_relief_assessment(
            frame,
            commands=[],
            active_wars=frame["active_wars"],
            controlled_armies=frame["player_armies"],
            pursuit_army=frame["player_armies"][0],
        )

    def test_unrelated_missing_carmy_does_not_block_complete_siege_war(self):
        frame = self._frame()
        frame["army_strengths_status"] = "partial"
        frame["army_strengths"].append({
            "army_id": 335544341,
            "scope_role": "active_war_enemy",
            "war_ids": [134217770],
            "status": "unavailable",
            "unavailable_reason": "native_carmy_not_found",
        })

        balance = _same_frame_army_strength_balance(frame, 95)
        self.assertIsNotNone(balance)
        self.assertEqual(balance["friendly_army_ids"], [11])
        self.assertEqual(balance["enemy_army_ids"], [21])
        relief = self._relief(frame)
        self.assertEqual(relief["status"], "forecast_required", relief)
        self.assertEqual(relief["war_id"], 95)

    def test_missing_carmy_in_siege_war_still_blocks(self):
        frame = self._frame()
        frame["army_strengths_status"] = "partial"
        frame["army_strengths"][1]["status"] = "unavailable"
        for key in ("current_soldiers", "maximum_soldiers", "ai_base_power_raw"):
            frame["army_strengths"][1][key] = None
        frame["army_strengths"][1]["unavailable_reason"] = "native_carmy_not_found"

        self.assertIsNone(_same_frame_army_strength_balance(frame, 95))
        relief = self._relief(frame)
        self.assertEqual(relief["status"], "observation_unavailable", relief)
        self.assertEqual(
            relief["required_observation"],
            "complete-same-frame-siege-position-and-war-strength",
        )

    def test_available_and_empty_scope_existing_contract(self):
        frame = self._frame()
        self.assertIsNotNone(_same_frame_army_strength_balance(frame, 95))
        self.assertIsNone(_same_frame_army_strength_balance(frame, 134217770))
        frame["paused"] = False
        self.assertIsNone(_same_frame_army_strength_balance(frame, 95))


if __name__ == "__main__":
    unittest.main()
