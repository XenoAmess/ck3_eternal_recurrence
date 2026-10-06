"""One production compound for selected-refill besieging B and assault loss."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.service import GameplayBridgeService
from test_selected_refill_monthly_assembly_service import assembly_packet
from test_post_refill_land_rate_service_join import data_snapshot


def fixed_data(identity: int, persistent: int, current: int, maximum: int) -> dict:
    data = data_snapshot(0)
    data.update(army_regiment_id=identity, native_data_record_count=1)
    data["records"] = [data["records"][0]]
    data["records"][0].update(
        persistent_regiment_id=persistent, chunk_army_regiment_id=identity,
        current_soldiers=current, effective_current_soldiers=current,
        maximum_soldiers=maximum)
    return data


def regiment(index: int, identity: int, current: int, maximum: int, data: dict) -> dict:
    return {"stored_index": index, "army_regiment_id": identity, "available": True,
            "unavailable_reason": "", "current_soldiers": current,
            "maximum_soldiers": maximum, "replenishment_records_v1": deepcopy(data)}


def occurrence(index: int, unit: int, current: int, rows: list) -> dict:
    return {"stored_index": index, "public_unit_id": unit, "resolved_unit_id": unit,
            "unit_used_fallback": False, "current_province_id": 1,
            "current_province_used_fallback": False, "raw_unit18": 0,
            "raw_unit170": 0, "raw_unit44": 0, "native_carmy_id": 12,
            "army_used_fallback": False, "eligible": True, "available": True,
            "unavailable_reason": "", "native_whole_current_soldiers": current,
            "regiments": deepcopy(rows)}


def besieging_packet() -> dict:
    source = assembly_packet()
    selected = source["regiment_replenishment_records_v1"]
    rows = [regiment(0, 11001, 160, 200, selected[0]),
            regiment(1, 11001, 160, 200, selected[0]),
            regiment(2, 11002, 50, 100, selected[1]),
            regiment(3, 33000, 7, 9, fixed_data(33000, 70000, 7, 9))]
    excluded = occurrence(2, 0, 0, [])
    excluded.update(current_province_id=0, native_carmy_id=None,
                    army_used_fallback=None, eligible=False,
                    native_whole_current_soldiers=None)
    fallback = deepcopy(excluded)
    fallback.update(stored_index=3, public_unit_id=88, resolved_unit_id=0,
                    unit_used_fallback=True, current_province_id=1,
                    current_province_used_fallback=True, raw_unit170=1)
    source["current_province_besieging_contributors_v1"] = {
        "status": "available", "unavailable_reason": "", "province_id": 1,
        "native_province_unit_count": 4, "native_besieging_strength": 754,
        "contributors_ready": True, "native_assault_expected_loss": 75,
        "assault_context": {"status": "available", "unavailable_reason": "",
            "has_active_siege": True, "siege_id": 0, "breach_level_raw": 1,
            "casualty_percentage_count": 3, "casualty_percentage_raw": 1000000},
        "occurrences": [occurrence(0, 11, 377, rows), occurrence(1, 11, 377, rows),
                        excluded, fallback],
    }
    return source


def scalar_packet(current: int, percentage: int | None, *, repeats: int = 1) -> dict:
    source = besieging_packet()
    rows = [regiment(index, 44000, current, current,
                     fixed_data(44000, 71000, current, current))
            for index in range(repeats)]
    total = (current * repeats + (1 << 31)) % (1 << 32) - (1 << 31)
    family = source["current_province_besieging_contributors_v1"]
    family.update(native_province_unit_count=1, native_besieging_strength=total,
                  occurrences=[occurrence(0, 11, total, rows)],
                  native_assault_expected_loss=None)
    family["assault_context"]["casualty_percentage_raw"] = percentage
    return source


class FakeDriver:
    """An in-memory backend; it cannot reach SDK, pipes or game processes."""
    def __init__(self, source: dict) -> None:
        self.source = source
        self.calls = []

    def snapshot(self) -> dict:
        return {"paused": True, "revision": 42, "native_revision": 7,
                "date_raw": 10000, "snapshot_id": "offline-besieging-first",
                "backend_id": "pure-memory-fixture",
                "player_armies": [{"army_id": self.source["army_id"]}],
                "active_wars": [], "diagnostics": {"hello": {"game_version": "1.20.0.3"}}}

    def capabilities(self) -> dict:
        return {"action_steps": ["query-army-strengths-v1"]}

    def execute_step(self, step: str, *, expected_revision: int | None = None) -> dict:
        self.calls.append((step, expected_revision))
        return {"status": "available", "army_strengths": [deepcopy(self.source)],
                "native_readiness": {"current_strength": True, "full_monthly": False}}


class DriverService(GameplayBridgeService):
    """Keep production query/authority/joins and replace only backend calls."""
    def __init__(self, driver: FakeDriver) -> None:
        self.driver = driver

    def snapshot(self) -> dict:
        return self.driver.snapshot()

    def capabilities(self) -> dict:
        return self.driver.capabilities()

    def execute_step(self, step: str, *, expected_revision: int | None = None) -> dict:
        return self.driver.execute_step(step, expected_revision=expected_revision)


def query_with_fake_driver(source: dict) -> tuple[dict, FakeDriver]:
    driver = FakeDriver(source)
    result = DriverService(driver).query_army_strengths(
        [source["army_id"]], expected_revision=42)
    return result, driver


class PostRefillBesiegingCurrentServiceTests(unittest.TestCase):
    def test_actual_unavailable_native_count_and_default_province_are_unknown(self):
        outputs = {}

        def query(name, source):
            before = deepcopy(source)
            result, driver = query_with_fake_driver(source)
            self.assertEqual(driver.calls, [("query-army-strengths-v1", 42)])
            self.assertEqual(source, before)
            value = result["same_input_conditional_post_refill_besieging_current_v1"][0]
            self.assertIsNone(value["native_province_unit_count"])
            self.assertFalse(value["conditional_besieging_strength_ready"])
            self.assertIsNone(value["conditional_besieging_strength"])
            self.assertFalse(value["conditional_assault_expected_loss_ready"])
            self.assertIsNone(value["conditional_assault_expected_loss"])
            self.assertIsNone(value["assault_projection"]["zero_basis"])
            self.assertFalse(value["actual_effects"])
            self.assertFalse(value["full_monthly_ready"])
            self.assertIsNone(value["actual_post_besieging_strength"])
            outputs[name] = result
            if target := os.environ.get("XAR_BESIEGING_UNAVAILABLE_FIRST_OUTPUT"):
                Path(target).write_text(json.dumps(outputs, ensure_ascii=False, indent=2) + "\n",
                                        encoding="utf-8")
            return value

        unavailable = besieging_packet()
        family = unavailable["current_province_besieging_contributors_v1"]
        family.update(status="unavailable", unavailable_reason="current_Province_unreadable",
                      province_id=-1, native_province_unit_count=None,
                      native_besieging_strength=None, native_assault_expected_loss=None,
                      contributors_ready=False, occurrences=[])
        family["assault_context"].update(status="unavailable",
            unavailable_reason="current_Province_unreadable", has_active_siege=None,
            siege_id=None, breach_level_raw=None, casualty_percentage_count=None,
            casualty_percentage_raw=None)
        value = query("actual-early-unavailable-defaults", unavailable)
        self.assertEqual(value["province_id"], -1)
        self.assertFalse(value["native_besieging_strength_ready"])
        self.assertFalse(value["native_assault_expected_loss_ready"])

        observed = besieging_packet()
        observed["current_province_besieging_contributors_v1"].update(
            status="partial", unavailable_reason="resident_count_unreadable",
            native_province_unit_count=None, contributors_ready=False, occurrences=[])
        value = query("unavailable-count-independent-current-scalars", observed)
        self.assertTrue(value["native_besieging_strength_ready"])
        self.assertTrue(value["native_assault_expected_loss_ready"])
        self.assertEqual((value["native_besieging_strength"], value["native_assault_expected_loss"]), (754, 75))

    def test_flags0_occurrence_recount_physical_overlay_and_assault_source_branches(self):
        outputs = {}

        def query(name: str, source: dict) -> tuple[dict, dict]:
            before = deepcopy(source)
            result, driver = query_with_fake_driver(source)
            self.assertEqual(driver.calls, [("query-army-strengths-v1", 42)])
            self.assertEqual(source, before)
            self.assertEqual(result["native_readiness"],
                             {"current_strength": True, "full_monthly": False})
            values = result["same_input_conditional_post_refill_besieging_current_v1"]
            self.assertEqual(len(values), 1)
            value = values[0]
            self.assertEqual(value["army_id"], source["army_id"])
            for key in ("actual_replenishment", "actual_loss", "actual_effects",
                        "full_regular_refill_ready", "full_daily_assault_ready", "full_monthly_ready"):
                self.assertFalse(value[key])
            for key in ("actual_post_stage_current", "actual_post_besieging_strength", "actual_assault_loss"):
                self.assertIsNone(value[key])
            self.assertEqual(value["refill_ADDs_executed"], 0)
            outputs[name] = result
            if target := os.environ.get("XAR_BESIEGING_FIRST_OUTPUT"):
                Path(target).write_text(json.dumps(outputs, ensure_ascii=False, indent=2) + "\n",
                                        encoding="utf-8")
            return result, value

        result, value = query("nonzero-flags0-duplicate-overlay", besieging_packet())
        self.assertTrue(value["native_besieging_strength_ready"])
        self.assertTrue(value["native_assault_expected_loss_ready"])
        self.assertEqual((value["native_besieging_strength"], value["native_assault_expected_loss"]), (754, 75))
        self.assertTrue(value["conditional_besieging_strength_ready"])
        self.assertTrue(value["conditional_assault_expected_loss_ready"])
        self.assertEqual((value["conditional_besieging_strength"],
                          value["conditional_assault_expected_loss"]), (874, 87))
        self.assertEqual([row["conditional_whole_current_soldiers"] for row in value["occurrences"]],
                         [437, 437, 0, 0])
        first = value["occurrences"][0]["regiments"]
        self.assertEqual([row["army_regiment_id"] for row in first], [11001, 11001, 11002, 33000])
        self.assertEqual([row["conditional_current_soldiers"] for row in first], [180, 180, 70, 7])
        self.assertEqual(len(first[0]["refresh"]["record_contributions"]), 8)
        physical = {(row["persistent_regiment_id"], row["chunk_index"]): row
                    for row in value["merged_physical_chunks"]}
        self.assertEqual(physical[50001, 0]["current_soldiers"], 90)
        self.assertEqual(physical[50001, 0]["physical_add_count"], 1)
        self.assertEqual(physical[70000, 0]["current_soldiers"], 7)
        self.assertEqual(physical[70000, 0]["input_basis"], "unchanged_observed_besieging_DATA_physical_slot")
        self.assertEqual(value["selected_physical_overlay_count"], 8)
        assembly = result["same_input_conditional_selected_refill_monthly_assembly_v1"][0]
        self.assertEqual(assembly["derived_subject_frame"]["count_by_native_flags"]["0"], 250)
        self.assertEqual(assembly["joined_post_refill_land_rate"][
            "conditional_supply_usage_soldiers"], 360)
        self.assertEqual(value["occurrences"][2]["resolved_unit_id"], 0)
        self.assertEqual(value["occurrences"][2]["current_province_id"], 0)
        self.assertTrue(value["occurrences"][3]["unit_used_fallback"])
        self.assertTrue(value["occurrences"][3]["current_province_used_fallback"])
        self.assertEqual(value["occurrences"][3]["resolved_unit_id"], 0)
        self.assertEqual(result["army_strengths"][0]["current_province_besieging_contributors_v1"][
            "native_besieging_strength"], 754)

        wrapped = scalar_packet(1500000000, None, repeats=2)
        wrapped["current_province_besieging_contributors_v1"]["native_assault_expected_loss"] = 0
        _, value = query("wrap32-nonpositive-B-source-zero", wrapped)
        self.assertEqual(value["native_besieging_strength"], -1294967296)
        self.assertEqual(value["conditional_besieging_strength"], -1294967296)
        self.assertTrue(value["conditional_assault_expected_loss_ready"])
        self.assertEqual(value["conditional_assault_expected_loss"], 0)
        self.assertEqual(value["assault_projection"]["zero_basis"], "nonpositive_conditional_B")
        self.assertIsNone(value["assault_projection"]["division_path"])

        _, value = query("decomposed-native-division", scalar_packet(1500000000, 1000000))
        self.assertEqual(value["conditional_besieging_strength"], 1500000000)
        self.assertEqual(value["conditional_assault_expected_loss"], 150000000)
        self.assertEqual(value["assault_projection"]["division_path"], "decomposed")
        self.assertFalse(value["native_assault_expected_loss_ready"])
        _, value = query("wrap64-product-before-fixed-division", scalar_packet(2, (1 << 63) - 1))
        self.assertEqual(value["assault_projection"]["wrapped_product_raw"], -2)
        self.assertEqual(value["conditional_assault_expected_loss"], 0)
        _, value = query("signed-percentage-without-clamp", scalar_packet(500, -1000000))
        self.assertEqual(value["conditional_assault_expected_loss"], -50)

        missing = besieging_packet()
        family = missing["current_province_besieging_contributors_v1"]
        family.update(status="partial", unavailable_reason="unchanged_DATA_unavailable", contributors_ready=False)
        for admitted in family["occurrences"][:2]:
            admitted.update(available=False, unavailable_reason="unchanged_DATA_unavailable")
            admitted["regiments"][3].update(available=False,
                unavailable_reason="DATA_unavailable", replenishment_records_v1=None)
        _, value = query("missing-unchanged-DATA-keeps-native-scalars", missing)
        self.assertEqual((value["native_besieging_strength"], value["native_assault_expected_loss"]), (754, 75))
        self.assertTrue(value["native_besieging_strength_ready"])
        self.assertFalse(value["conditional_besieging_strength_ready"])
        self.assertIsNone(value["conditional_besieging_strength"])
        self.assertFalse(value["conditional_assault_expected_loss_ready"])
        self.assertIsNone(value["conditional_assault_expected_loss"])
        self.assertTrue(value["occurrences"][0]["regiments"][0]["conditional_ready"])
        self.assertFalse(value["occurrences"][0]["regiments"][3]["conditional_ready"])

        missing_percentage = besieging_packet()
        missing_percentage["current_province_besieging_contributors_v1"]["assault_context"].update(
            status="unavailable", unavailable_reason="percentage_unavailable", casualty_percentage_raw=None)
        _, value = query("missing-percentage-independent-derived-B", missing_percentage)
        self.assertTrue(value["conditional_besieging_strength_ready"])
        self.assertEqual(value["conditional_besieging_strength"], 874)
        self.assertFalse(value["conditional_assault_expected_loss_ready"])
        self.assertEqual(value["native_assault_expected_loss"], 75)

        no_siege = besieging_packet()
        no_siege["current_province_besieging_contributors_v1"].update(native_assault_expected_loss=0)
        no_siege["current_province_besieging_contributors_v1"]["assault_context"].update(
            has_active_siege=False, siege_id=None, breach_level_raw=None,
            casualty_percentage_count=None, casualty_percentage_raw=None)
        _, value = query("no-active-siege-unused-table-zero", no_siege)
        self.assertEqual(value["conditional_assault_expected_loss"], 0)
        self.assertTrue(value["conditional_assault_expected_loss_ready"])
        self.assertEqual(value["assault_projection"]["zero_basis"], "no_active_Siege")

        outside = besieging_packet()
        outside["current_province_besieging_contributors_v1"]["assault_context"].update(
            breach_level_raw=0, casualty_percentage_raw=None)
        _, value = query("breach-outside-unused-entry-zero", outside)
        self.assertEqual(value["conditional_assault_expected_loss"], 0)
        self.assertTrue(value["conditional_assault_expected_loss_ready"])
        self.assertEqual(value["assault_projection"]["zero_basis"], "breach_index_outside_loaded_table")

        empty = besieging_packet()
        empty["current_province_besieging_contributors_v1"].update(
            native_province_unit_count=-4, native_besieging_strength=0,
            native_assault_expected_loss=0, occurrences=[])
        empty["current_province_besieging_contributors_v1"]["assault_context"].update(
            status="unavailable", unavailable_reason="unused_context", has_active_siege=None,
            siege_id=None, breach_level_raw=None, casualty_percentage_count=None,
            casualty_percentage_raw=None)
        _, value = query("nonpositive-original-count-source-zero", empty)
        self.assertEqual(value["native_province_unit_count"], -4)
        self.assertTrue(value["conditional_besieging_strength_ready"])
        self.assertEqual(value["conditional_besieging_strength"], 0)
        self.assertTrue(value["conditional_assault_expected_loss_ready"])
        self.assertEqual(value["conditional_assault_expected_loss"], 0)

        legacy = assembly_packet()
        _, value = query("old-schema-family-absent", legacy)
        self.assertFalse(value["native_besieging_strength_ready"])
        self.assertFalse(value["conditional_besieging_strength_ready"])
        self.assertFalse(value["conditional_assault_expected_loss_ready"])
        self.assertIsNone(value["conditional_assault_expected_loss"])


if __name__ == "__main__":
    unittest.main()
