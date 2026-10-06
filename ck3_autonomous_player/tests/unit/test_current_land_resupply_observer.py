from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.war_contract import normalize_army_strengths
from xar_autoplayer.bridge.army_current_land_resupply_contract import (
    project_land_resupply_gain_component_v1,
)


def row(inputs: object = None) -> dict:
    result = {
        "status": "available", "army_id": 11, "native_carmy_id": 12,
        "scope_role": "player", "war_ids": [], "regiment_count": 0,
        "current_soldiers": 0, "maximum_soldiers": 0,
        "ai_base_power_raw": 0, "ai_base_power_scale": 100000,
        "unavailable_reason": None,
        "current_supply_change_monthly_raw": -432100,
        "current_supply_change_monthly_scale": 100000,
    }
    if inputs is not None:
        result["current_land_resupply_v1"] = inputs
    return result


def inputs(**changes: object) -> dict:
    return {
        "source": "native_current_province_land_resupply", "status": "available",
        "unavailable_reason": None, "current_observation_ready": True,
        "province_id": 1, "owner_character_id": 33388,
        "native_land_branch_applicable": True, "native_resupply_eligible": True,
        "loaded_gain_raw": 2345678, "scale": 100000,
        **changes,
    }


class CurrentLandResupplyObserverTests(unittest.TestCase):
    def test_current_observation_and_distinct_gain_component(self) -> None:
        # First compound case exercises the production Strength normalizer hook.
        normalized = normalize_army_strengths([row(inputs())])[0]
        current = normalized["current_land_resupply_v1"]
        self.assertEqual(current["owner_character_id"], 33388)
        self.assertEqual(current["loaded_gain_raw"], 2345678)
        self.assertEqual(normalized["current_supply_change_monthly_raw"], -432100)
        for usage, gain in ((499, 2345678), (500, 2345678), (501, 0)):
            projected = project_land_resupply_gain_component_v1(
                current, usage_soldiers=usage, limit_soldiers=500)
            self.assertTrue(projected["gain_component_ready"])
            self.assertEqual(projected["gain_component_raw"], gain)
            self.assertFalse(projected["full_monthly_supply_change_ready"])
            self.assertFalse(projected["actual_post_stage_observed"])
        for eligible, loaded, expected in ((False, 2345678, 0), (True, 0, 0), (True, -17, -17)):
            current = normalize_army_strengths([row(inputs(
                native_resupply_eligible=eligible, loaded_gain_raw=loaded))])[0][
                    "current_land_resupply_v1"]
            projected = project_land_resupply_gain_component_v1(
                current, usage_soldiers=0, limit_soldiers=0)
            self.assertTrue(current["current_observation_ready"])
            self.assertTrue(projected["gain_component_ready"])
            self.assertEqual(projected["gain_component_raw"], expected)
        for partial in (
            inputs(status="unavailable", current_observation_ready=False,
                   unavailable_reason="current_province_resupply_owner_unresolved",
                   owner_character_id=None, native_resupply_eligible=None),
            inputs(status="not_land", current_observation_ready=False,
                   owner_character_id=None, native_land_branch_applicable=False,
                   native_resupply_eligible=None),
        ):
            current = normalize_army_strengths([row(partial)])[0]["current_land_resupply_v1"]
            self.assertEqual(current["loaded_gain_raw"], 2345678)
            projected = project_land_resupply_gain_component_v1(
                current, usage_soldiers=1, limit_soldiers=500)
            self.assertFalse(projected["gain_component_ready"])
            self.assertIsNone(projected["gain_component_raw"])
        self.assertNotIn("current_land_resupply_v1", normalize_army_strengths([row()])[0])
        with self.assertRaises(ValueError):
            normalize_army_strengths([row(inputs(native_resupply_eligible=1))])
        with self.assertRaises(ValueError):
            normalize_army_strengths([row(inputs(loaded_gain_raw=None))])


if __name__ == "__main__":
    unittest.main()
