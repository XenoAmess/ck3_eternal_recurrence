from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from xar_autoplayer.bridge.war_contract import normalize_army_strengths
from xar_autoplayer.bridge.army_full_land_supply_rate_projection import (
    project_full_land_supply_rate_v1, _native_fixed_mul, _native_fixed_div,
)


def inputs(**changes: object) -> dict:
    return {
        "source": "native_current_province_land_supply_rate_inputs", "status": "available",
        "unavailable_reason": None, "current_observation_ready": True,
        "province_id": 1, "subject_army_id": 11, "subject_carmy_id": 12,
        "owner_character_id": 33388, "commander_raw_full_id": 777,
        "commander_resolved_full_id": 777, "commander_used_native_fallback": False,
        "native_land_branch_applicable": True, "native_province_component_applicable": True,
        "province_component_raw": -600000, "commander_modifier_1a9_raw": 100000,
        "loaded_excess_slope_raw": 10000, "loaded_min_loss_raw": 200000,
        "loaded_max_loss_raw": 5000000, "loaded_divisor_floor_raw": 300000,
        "scale": 100000, **changes,
    }


def row(rate: object = None, *, gain: int = 2345678) -> dict:
    result = {
        "status": "available", "army_id": 11, "native_carmy_id": 12,
        "scope_role": "player", "war_ids": [], "regiment_count": 0,
        "current_soldiers": 0, "maximum_soldiers": 0,
        "ai_base_power_raw": 0, "ai_base_power_scale": 100000, "unavailable_reason": None,
        "current_supply_change_monthly_raw": -432100, "current_supply_change_monthly_scale": 100000,
        "current_land_resupply_v1": {
            "source": "native_current_province_land_resupply", "status": "available",
            "unavailable_reason": None, "current_observation_ready": True,
            "province_id": 1, "owner_character_id": 33388, "native_land_branch_applicable": True,
            "native_resupply_eligible": True, "loaded_gain_raw": gain, "scale": 100000,
        },
        "current_province_supply_contributors_v1": {
            "source": "native_current_province_mode0", "status": "available",
            "unavailable_reason": None, "current_usage_ready": True, "contributors_ready": True,
            "province_id": 1, "subject_army_id": 11, "subject_carmy_id": 12,
            "owner_character_id": 33388, "native_province_unit_count": 0,
            "native_supply_limit_soldiers": 100, "native_supply_usage_soldiers": 80,
            "soldiers_scale": 1, "occurrences": [],
        },
    }
    if rate is not None:
        result["current_land_supply_rate_inputs_v1"] = rate
    return result


class CurrentFullLandSupplyRateTests(unittest.TestCase):
    def test_production_normalizer_and_source_numeric_branches(self) -> None:
        def project(rate: dict, usage: int = 100, gain: int = 2345678) -> dict:
            capture = normalize_army_strengths([row(rate, gain=gain)])[0]
            projected = project_full_land_supply_rate_v1(
                capture, selected_refill_usage_soldiers=usage)
            self.assertEqual(capture["current_supply_change_monthly_raw"], -432100)
            self.assertFalse(projected["actual_after"])
            self.assertFalse(projected["actual_post_stage_observed"])
            self.assertFalse(projected["full_monthly_supply_change_ready"])
            return projected

        # Under/equal limit still adjusts a negative Province component before adding gain.
        for usage in (80, 100):
            p = project(inputs(), usage)
            self.assertTrue(p["full_land_rate_ready"])
            self.assertEqual(p["commander_divisor_raw"], 300000)  #MAX floor, not min/cap
            self.assertEqual(p["local_component_after_adjustment_raw"], -200000)
            self.assertEqual(p["conditional_full_land_rate_raw"], 2145678)
        # Over-limit positive local component bypasses commander adjustment; gain is absent.
        p = project(inputs(province_component_raw=700000), 110)
        self.assertEqual((p["excess_loss_raw"], p["conditional_full_land_rate_raw"]), (200000, 500000))
        self.assertEqual(p["division_path"], "not_negative")
        p = project(inputs(province_component_raw=0, loaded_max_loss_raw=400000), 200)
        self.assertEqual((p["excess_loss_raw"], p["conditional_full_land_rate_raw"]), (400000, -133333))
        p = project(inputs(province_component_raw=0, loaded_min_loss_raw=600000,
                           loaded_max_loss_raw=400000), 110)
        self.assertEqual((p["excess_loss_raw"], p["conditional_full_land_rate_raw"]), (600000, -200000))
        p = project(inputs(loaded_divisor_floor_raw=0, commander_modifier_1a9_raw=-100000), gain=0)
        self.assertEqual((p["division_path"], p["conditional_full_land_rate_raw"]),
                         ("zero_divisor_raw_minus_one", -1))
        p = project(inputs(province_component_raw=-6000000, loaded_max_loss_raw=300000,
                           loaded_divisor_floor_raw=100000, commander_modifier_1a9_raw=0), gain=0)
        self.assertEqual(p["conditional_full_land_rate_raw"], -300000)  #second floor
        p = project(inputs(native_province_component_applicable=False, province_component_raw=0,
                           commander_raw_full_id=-1, commander_resolved_full_id=-1,
                           commander_used_native_fallback=True, commander_modifier_1a9_raw=0,
                           loaded_excess_slope_raw=0, loaded_min_loss_raw=0,
                           loaded_max_loss_raw=0, loaded_divisor_floor_raw=0), gain=0)
        self.assertEqual(p["conditional_full_land_rate_raw"], 0)
        # Native primitive boundary vectors, including all three division paths.
        self.assertEqual(_native_fixed_mul(3037000499, 3037000499), 92233720309262)
        self.assertEqual(_native_fixed_mul(3037000500, 3037000499), 92233720339632)
        self.assertEqual(_native_fixed_mul((1 << 63) - 1, 100000), (1 << 63) - 1)
        self.assertEqual(_native_fixed_div(-600000, -300000), (200000, "fast"))
        self.assertEqual(_native_fixed_div(-10**18, 10**10), (-10**13, "wide_divisor"))
        self.assertEqual(_native_fixed_div(-92233720368548, 3), (-3074457345618266666, "decomposed"))
        self.assertEqual(_native_fixed_div(-10**18, -(1 << 63)), (0, "decomposed"))
        # Missing new family preserves the independently observed total, never substitutes it.
        legacy = normalize_army_strengths([row()])[0]
        self.assertNotIn("current_land_supply_rate_inputs_v1", legacy)
        self.assertFalse(project_full_land_supply_rate_v1(
            legacy, selected_refill_usage_soldiers=80)["full_land_rate_ready"])
        p = project(inputs(status="unavailable", current_observation_ready=False,
                           unavailable_reason="missing_slot", loaded_divisor_floor_raw=None))
        self.assertFalse(p["full_land_rate_ready"])
        self.assertIsNone(p["conditional_full_land_rate_raw"])
        bad_context = normalize_army_strengths([row(inputs())])[0]
        bad_context["current_province_supply_contributors_v1"]["owner_character_id"] += 1
        with self.assertRaises(ValueError):
            project_full_land_supply_rate_v1(bad_context, selected_refill_usage_soldiers=100)
        for bad in (inputs(loaded_excess_slope_raw=True), inputs(scale=True),
                    inputs(commander_modifier_1a9_raw=None), inputs(extra_field=0),
                    inputs(native_province_component_applicable=False, province_component_raw=-1)):
            with self.assertRaises(ValueError):
                normalize_army_strengths([row(bad)])
        self.assertEqual(row(inputs())["current_land_supply_rate_inputs_v1"], inputs())


if __name__ == "__main__":
    unittest.main()
