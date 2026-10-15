from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.war_contract import normalize_army_strengths


def row():
    return {
        "status": "available", "army_id": 0, "native_carmy_id": 0,
        "scope_role": "player", "war_ids": [], "regiment_count": 1,
        "current_soldiers": 900, "maximum_soldiers": 1500,
        "ai_base_power_raw": 0, "ai_base_power_scale": 100_000,
        "unavailable_reason": None,
        "county_entry_inputs_v1": {
            "status": "available", "source": "native_current_county_entry_inputs",
            "unavailable_reason": None, "whole_soldiers": 900,
            "current_loss_budget": 0, "effective_fraction_raw": 0,
            "minimum_multiplier_raw": 0, "loaded_minimum_soldiers": 100,
            "fraction_scale": 100_000, "soldier_scale": 1,
            "condition": {
                "status": "available", "source": "current_stored_route_first_province",
                "unavailable_reason": None, "actor_character_id": 33388,
                "source_province_id": 1, "target_province_id": 2,
                "mode": 1, "passes": False,
            },
            "multiplier_floor_inputs_v1": {
                "status": "available", "source": "native_current_county_multiplier_floor_inputs",
                "unavailable_reason": None, "fraction_scale": 100_000,
                "base_floor_raw": 0, "army_1d4_nonzero_floor_raw": 100_000,
                "army_1d4_raw": 0,
            },
        },
    }


def observed(value):
    return normalize_army_strengths([value])[0]["county_entry_inputs_v1"]


class CountyMultiplierFloorInputsContractTests(unittest.TestCase):
    def test_zero_floor_zero_budget_and_false_condition_are_actual_values(self):
        value = row()
        self.assertEqual(observed(value), value["county_entry_inputs_v1"])
        self.assertIs(observed(value)["condition"]["passes"], False)

    def test_signed_q64_and_unclassified_nonzero_byte_are_preserved(self):
        value = row()
        inputs = value["county_entry_inputs_v1"]
        inputs["multiplier_floor_inputs_v1"].update(
            base_floor_raw=-(2**63), army_1d4_nonzero_floor_raw=2**63-1,
            army_1d4_raw=255,
        )
        inputs["condition"]["mode"] = 0
        self.assertEqual(observed(value), inputs)

    def test_missing_read_and_missing_parent_budget_are_independent_and_legacy_omits(self):
        value = row()
        inputs = value["county_entry_inputs_v1"]
        floors = inputs["multiplier_floor_inputs_v1"]
        floors.update(status="unavailable", unavailable_reason="county_multiplier_base_floor_read_failed",
                      base_floor_raw=None, army_1d4_nonzero_floor_raw=None, army_1d4_raw=None)
        self.assertEqual(observed(value)["current_loss_budget"], 0)
        self.assertIsNone(observed(value)["multiplier_floor_inputs_v1"]["base_floor_raw"])
        del inputs["multiplier_floor_inputs_v1"]
        self.assertNotIn("multiplier_floor_inputs_v1", observed(value))
        inputs["multiplier_floor_inputs_v1"] = row()["county_entry_inputs_v1"]["multiplier_floor_inputs_v1"]
        inputs.update(status="unavailable", unavailable_reason="county_entry_budget_bindings_unavailable")
        for key in ("whole_soldiers", "current_loss_budget", "effective_fraction_raw",
                    "minimum_multiplier_raw", "loaded_minimum_soldiers"):
            inputs[key] = None
        inputs["condition"].update(status="unavailable", unavailable_reason="county_entry_budget_unavailable",
                                   actor_character_id=None, source_province_id=None, target_province_id=None,
                                   mode=None, passes=None)
        self.assertEqual(observed(value)["multiplier_floor_inputs_v1"]["army_1d4_nonzero_floor_raw"], 100_000)

    def test_malformed_child_and_raw_byte_mode_disagreement_are_rejected(self):
        for key, invalid in (("base_floor_raw", True), ("base_floor_raw", 2**63),
                             ("army_1d4_nonzero_floor_raw", -(2**63)-1),
                             ("army_1d4_raw", False), ("army_1d4_raw", -1),
                             ("army_1d4_raw", 256), ("army_1d4_raw", 9),
                             ("fraction_scale", True), ("source", "inferred_default"),
                             ("status", "unavailable")):
            with self.subTest(key=key, invalid=invalid):
                value = deepcopy(row())
                value["county_entry_inputs_v1"]["multiplier_floor_inputs_v1"][key] = invalid
                with self.assertRaises(ValueError):
                    observed(value)


if __name__ == "__main__":
    unittest.main()
