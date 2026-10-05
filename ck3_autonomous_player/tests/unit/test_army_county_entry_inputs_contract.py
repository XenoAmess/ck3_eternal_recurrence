from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.war_contract import normalize_army_strengths


def row() -> dict[str, object]:
    return {
        "status": "available", "army_id": 0, "native_carmy_id": 0,
        "scope_role": "player", "war_ids": [], "regiment_count": 1,
        "current_soldiers": 900, "maximum_soldiers": 1500,
        "ai_base_power_raw": 0, "ai_base_power_scale": 100_000,
        "unavailable_reason": None,
        "county_entry_inputs_v1": {
            "status": "available", "source": "native_current_county_entry_inputs",
            "unavailable_reason": None, "whole_soldiers": 900,
            "current_loss_budget": 137, "effective_fraction_raw": 5_000,
            "minimum_multiplier_raw": 100_000, "loaded_minimum_soldiers": 100,
            "fraction_scale": 100_000, "soldier_scale": 1,
            "condition": {
                "status": "available", "source": "current_stored_route_first_province",
                "unavailable_reason": None, "actor_character_id": 33388,
                "source_province_id": 1, "target_province_id": 2,
                "mode": 1, "passes": True,
            },
        },
    }


class CountyEntryInputsContractTests(unittest.TestCase):
    def test_current_native_budget_is_preserved_without_recomputing_or_applied_fields(self):
        value = row()
        output = normalize_army_strengths([value])[0]["county_entry_inputs_v1"]
        self.assertEqual(output, value["county_entry_inputs_v1"])
        self.assertEqual(output["current_loss_budget"], 137)
        self.assertNotIn("applied_loss", output)

    def test_zero_budget_false_condition_and_mode_zero_remain_observed(self):
        value = row()
        value["county_entry_inputs_v1"]["current_loss_budget"] = 0
        value["county_entry_inputs_v1"]["condition"].update(mode=0, passes=False)
        output = normalize_army_strengths([value])[0]["county_entry_inputs_v1"]
        self.assertEqual(output["current_loss_budget"], 0)
        self.assertIs(output["condition"]["passes"], False)

    def test_no_route_or_unresolved_actor_condition_does_not_erase_budget(self):
        for reason in ("no_stored_route", "actor_character_unresolved"):
            with self.subTest(reason=reason):
                value = row()
                value["county_entry_inputs_v1"]["condition"].update(
                    status="unavailable", unavailable_reason=reason,
                    actor_character_id=None, source_province_id=None,
                    target_province_id=None, mode=None, passes=None,
                )
                output = normalize_army_strengths([value])[0]["county_entry_inputs_v1"]
                self.assertEqual(output["current_loss_budget"], 137)
                self.assertIsNone(output["condition"]["passes"])

    def test_unavailable_subdomain_preserves_ordinary_strength(self):
        value = row()
        inputs = value["county_entry_inputs_v1"]
        inputs.update(status="unavailable", unavailable_reason="county_entry_budget_bindings_unavailable")
        for key in ("whole_soldiers", "current_loss_budget", "effective_fraction_raw",
                    "minimum_multiplier_raw", "loaded_minimum_soldiers"):
            inputs[key] = None
        inputs["condition"].update(
            status="unavailable", unavailable_reason="county_entry_budget_unavailable",
            actor_character_id=None, source_province_id=None,
            target_province_id=None, mode=None, passes=None,
        )
        self.assertEqual(normalize_army_strengths([value])[0]["current_soldiers"], 900)
        inputs["current_loss_budget"] = 0
        with self.assertRaises(ValueError):
            normalize_army_strengths([value])

    def test_historical_producer_omits_block_without_backfilling(self):
        value = row()
        del value["county_entry_inputs_v1"]
        self.assertNotIn("county_entry_inputs_v1", normalize_army_strengths([value])[0])

    def test_malformed_or_unbound_current_inputs_fail_closed(self):
        for key, invalid in (
            ("current_loss_budget", True), ("current_loss_budget", -1),
            ("current_loss_budget", 901), ("whole_soldiers", 899),
            ("whole_soldiers", 2**31), ("effective_fraction_raw", 2**63),
            ("minimum_multiplier_raw", -(2**63)-1),
            ("fraction_scale", True), ("fraction_scale", 100),
            ("soldier_scale", 100_000), ("source", "applied_loss"),
            ("status", "forecast"), ("unavailable_reason", "not_null"),
            ("loaded_minimum_soldiers", True),
        ):
            with self.subTest(key=key, invalid=invalid):
                value = row()
                value["county_entry_inputs_v1"][key] = invalid
                with self.assertRaises(ValueError):
                    normalize_army_strengths([value])

    def test_malformed_condition_identity_or_observation_fail_closed(self):
        for key, invalid in (
            ("actor_character_id", -1), ("actor_character_id", True),
            ("source_province_id", 0), ("target_province_id", 2**31),
            ("mode", 2), ("mode", True), ("passes", 1), ("passes", None),
            ("source", "final_route_destination"),
            ("status", "unavailable"), ("unavailable_reason", "not_null"),
        ):
            with self.subTest(key=key, invalid=invalid):
                value = row()
                value["county_entry_inputs_v1"]["condition"][key] = invalid
                with self.assertRaises(ValueError):
                    normalize_army_strengths([value])

    def test_unknown_extra_or_missing_fields_rejected(self):
        original = row()
        for section in ("budget", "condition"):
            for mutation in ("extra", "missing"):
                with self.subTest(section=section, mutation=mutation):
                    value = deepcopy(original)
                    inputs = value["county_entry_inputs_v1"]
                    target = inputs if section == "budget" else inputs["condition"]
                    if mutation == "extra":
                        target["applied_loss"] = 137
                    else:
                        del target["source"]
                    with self.assertRaises(ValueError):
                        normalize_army_strengths([value])

    def test_unavailable_army_cannot_publish_current_county_inputs(self):
        value = row()
        value.update(status="unavailable", unavailable_reason="native_carmy_not_found",
                     regiment_count=None, current_soldiers=None, maximum_soldiers=None,
                     ai_base_power_raw=None)
        with self.assertRaises(ValueError):
            normalize_army_strengths([value])

    def test_signed_raw_operands_preserved_and_not_cast_to_unsigned(self):
        value = row()
        value["county_entry_inputs_v1"].update(
            effective_fraction_raw=-(2**63), minimum_multiplier_raw=2**63-1,
            loaded_minimum_soldiers=-(2**31),
        )
        output = normalize_army_strengths([value])[0]["county_entry_inputs_v1"]
        self.assertEqual(output["effective_fraction_raw"], -(2**63))


if __name__ == "__main__":
    unittest.main()
