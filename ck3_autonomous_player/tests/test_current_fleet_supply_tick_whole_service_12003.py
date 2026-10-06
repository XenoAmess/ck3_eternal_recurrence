"""FIRST_NOT_RUN: one new native-whole-row -> actual service compound.

The eight JSON rows must come from the new native reader and the production
AppendArmyStrengthV1 serializer. Only the transport/snapshot metadata below is
synthetic. It is not a paused CK3 capture or evidence of an actual next callback.
No existing test module, replacement normalizer or replacement model is used.
"""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest


_SOURCE_ROOT = Path(os.environ["XAR_FLEET_TICK_SOURCE_ROOT"]).resolve()
sys.path.insert(0, str(_SOURCE_ROOT / "src"))

from xar_autoplayer.bridge.service import GameplayBridgeService


_BASELINE = "df87fd8562120b901413793ded4680b7b4dabd8e"
_RAW_FAMILY = "current_fleet_supply_tick_inputs_v1"
_DERIVED_FAMILY = "same_input_conditional_next_admitted_day_fleet_rate_v1"
_UNIT_ID = 67108883
_CARMY_ID = 33554443
_PROVINCE_ID = 470
_REVISION = 42
_NATIVE_REVISION = 7
_FLAGS = (
    "actual_next_callback_ready", "actual_after", "actual_post_stage_observed",
    "full_daily_supply_transition_ready", "full_monthly_ready",
)
_FIXED_CONTEXT = [
    "same Fleet association", "same Province/terrain", "same commander/fallback",
    "same loaded slots/modifier context",
]

# Independent literals from FIRST-FIXTURE-PLAN.json, not model-derived values.
_CASES = {
    "01-date-opens-next-day": {
        "date": 1000, "raw_status": "available", "raw_ready": True, "raw_reason": None,
        "status": "available", "ready": True, "next_date": 1024, "rate": -500000,
        "admitted": True, "branch": "negative_base_adjusted", "division": "fast",
        "divisor": 100000, "missing": [], "observed": 0,
    },
    "02-still-future-partial-downstream": {
        "date": 1000, "raw_status": "unavailable", "raw_ready": False,
        "raw_reason": "native_fleet_supply_terrain_unavailable",
        "status": "available", "ready": True, "next_date": 1024, "rate": 0,
        "admitted": False, "branch": "future_fleet_date", "division": None,
        "divisor": None, "missing": [], "observed": 0,
    },
    "03-positive-terrain772": {
        "date": 1000, "raw_status": "available", "raw_ready": True, "raw_reason": None,
        "status": "available", "ready": True, "next_date": 1024, "rate": 0,
        "admitted": True, "branch": "positive_terrain772_modifier", "division": None,
        "divisor": None, "missing": [], "observed": 0,
    },
    "04-native-fallback-absent-numeric-key": {
        "date": 1000, "raw_status": "available", "raw_ready": True, "raw_reason": None,
        "status": "available", "ready": True, "next_date": 1024, "rate": -500000,
        "admitted": True, "branch": "negative_base_adjusted", "division": "fast",
        "divisor": 100000, "missing": [], "observed": 0,
    },
    "05-fleet-zero-divisor": {
        "date": 1000, "raw_status": "available", "raw_ready": True, "raw_reason": None,
        "status": "available", "ready": True, "next_date": 1024, "rate": 4294967295,
        "admitted": True, "branch": "negative_base_adjusted",
        "division": "fleet_zero_divisor_positive_u32_max", "divisor": 0,
        "missing": [], "observed": 0,
    },
    "06-partial-needed-fixed-modifier": {
        "date": 1000, "raw_status": "unavailable", "raw_ready": False,
        "raw_reason": "native_fleet_supply_fixed_modifier_output_unavailable",
        "status": "unavailable", "ready": False, "next_date": 1024, "rate": None,
        "admitted": True, "branch": None, "division": None, "divisor": None,
        "missing": ["commander_modifier_1a9_raw"], "observed": 0,
    },
    "07-not-fleet": {
        "date": None, "raw_status": "not_fleet", "raw_ready": True, "raw_reason": None,
        "status": "not_fleet", "ready": False, "next_date": None, "rate": None,
        "admitted": None, "branch": "native_not_fleet", "division": None,
        "divisor": None, "missing": [], "observed": -600000,
    },
    "08-signed-clock-wrap": {
        "date": 2147483640, "raw_status": "available", "raw_ready": True, "raw_reason": None,
        "status": "available", "ready": True, "next_date": -2147483632, "rate": 0,
        "admitted": False, "branch": "future_fleet_date", "division": None,
        "divisor": None, "missing": [], "observed": 0,
    },
}


def _write_json(path: Path | None, value: object) -> None:
    if path is not None:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _check_original_scalars(test: unittest.TestCase, raw: object, mapped: object, path: str) -> None:
    """Check every original scalar/null/flag; allow production-added fields."""
    if isinstance(raw, dict):
        test.assertIsInstance(mapped, dict, path)
        for key, item in raw.items():
            test.assertIn(key, mapped, path)
            _check_original_scalars(test, item, mapped[key], f"{path}.{key}")
    elif isinstance(raw, list):
        test.assertIsInstance(mapped, list, path)
        test.assertEqual(len(mapped), len(raw), path)
        for index, item in enumerate(raw):
            _check_original_scalars(test, item, mapped[index], f"{path}[{index}]")
    else:
        test.assertIs(type(mapped), type(raw), path)
        test.assertEqual(mapped, raw, path)


class SyntheticWholeWireDriver:
    """Transport-only fixture: the native whole row is never edited/rebuilt."""

    def __init__(self, whole_row: dict[str, object], case_name: str, date: int | None) -> None:
        self.whole_row = whole_row
        self.calls: list[tuple[str, int | None]] = []
        self.case_name = case_name
        # Scope/pause/revision/date/capability are synthetic service prerequisites.
        self.synthetic_date = 1000 if date is None else date

    def take_snapshot(self) -> dict[str, object]:
        return {
            "paused": True, "revision": _REVISION, "native_revision": _NATIVE_REVISION,
            "date_raw": self.synthetic_date,
            "snapshot_id": f"synthetic-fleet-tick-first-{self.case_name}",
            "backend_id": "synthetic-native-whole-row-fixture-no-live-session",
            "player_armies": [{"army_id": _UNIT_ID}], "active_wars": [],
            "diagnostics": {"hello": {
                "game_version": "1.20.0.3", "executable_sha256": None,
                "synthetic_fixture": True, "live_capture": False,
            }},
        }

    def capabilities(self) -> dict[str, object]:
        return {"action_steps": ["query-army-strengths-v1"], "synthetic_fixture": True}

    def execute_step(self, step: str, *, expected_revision: int | None = None) -> dict[str, object]:
        self.calls.append((step, expected_revision))
        if step != "query-army-strengths-v1" or expected_revision != _REVISION:
            raise ValueError("synthetic fixture supports only the sealed readonly Strength query")
        return {
            "status": self.whole_row["status"], "army_strengths": [deepcopy(self.whole_row)],
            "native_readiness": {"current_strength": True, "full_monthly": False},
            "fixture_provenance": {
                "whole_row_producer": "new native reader -> actual AppendArmyStrengthV1",
                "query_envelope_synthetic": True, "snapshot_metadata_synthetic": True,
                "native_readiness_envelope_synthetic": True,
                "live_capture": False, "actual_next_callback_observed": False,
            },
        }


class CurrentFleetSupplyTickWholeService12003Tests(unittest.TestCase):
    def test_whole_native_wires_keep_observations_and_conditional_fleet_rate(self) -> None:
        self.assertEqual(sys.flags.optimize, 0, "Root FIRST invocation must not use -O")
        wire_dir = Path(os.environ["XAR_FLEET_TICK_WIRE_DIR"])
        output_dir = Path(os.environ["XAR_FLEET_TICK_OUTPUT_DIR"])
        output_dir.mkdir(parents=True, exist_ok=True)
        requested = os.environ.get("XAR_FLEET_TICK_CASES")
        names = ([name.strip() for name in requested.split(",") if name.strip()]
                 if requested is not None else list(_CASES))
        self.assertTrue(names, "case resume must select at least one FIRST case")
        self.assertEqual(len(names), len(set(names)), "case resume must not repeat a selected case")
        self.assertFalse(set(names) - set(_CASES), "only these eight FIRST case names are accepted")
        receipt = {
            "topic": "current-fleet-supply-tick/one-whole-service-compound",
            "source_baseline_metadata": _BASELINE,
            "adopted_source_commit_metadata": os.environ.get("XAR_FLEET_TICK_SOURCE_COMMIT"),
            "source_root": str(_SOURCE_ROOT), "configured_case_count": 8,
            "selected_cases": names, "test_method_count": 1,
            "old_test_modules_imported_by_this_test": [], "old_test_methods_executed": 0,
            "live_capture": False, "game_days": 0, "cases": {},
        }
        for name in names:
            with self.subTest(case=name):
                expected = _CASES[name]
                item = {"result": "RED", "wire_path": str(wire_dir / (name + ".json")),
                        "expected": expected, "live_capture": False}
                receipt["cases"][name] = item
                try:
                    wire_path = wire_dir / (name + ".json")
                    frozen_bytes = wire_path.read_bytes()
                    raw_row = json.loads(frozen_bytes)
                    item["raw_whole_native_row"] = deepcopy(raw_row)
                    before = deepcopy(raw_row)
                    self.assertIsInstance(raw_row, dict)
                    self.assertNotIn("army_strengths", raw_row, "fixture file must be a whole row")
                    self.assertEqual(raw_row["army_id"], _UNIT_ID)
                    self.assertEqual(raw_row["native_carmy_id"], _CARMY_ID)
                    self.assertEqual(raw_row["status"], "available")
                    self.assertEqual(raw_row["scope_role"], "player")
                    self.assertEqual(raw_row["war_ids"], [])
                    self.assertEqual(raw_row["regiment_count"], 1)
                    self.assertEqual(raw_row["current_soldiers"], 160)
                    self.assertEqual(raw_row["maximum_soldiers"], 240)
                    self.assertEqual(raw_row["ai_base_power_raw"], 300000)
                    self.assertEqual(raw_row["current_supply_raw"], 9000000)
                    self.assertEqual(raw_row["current_supply_change_monthly_raw"], expected["observed"])
                    self.assertEqual(raw_row["gathering_days_status"], "unavailable")
                    self.assertIsNone(raw_row["gathering_days_left"])
                    self.assertIs(raw_row["gathering_days_ready"], False)
                    driver = SyntheticWholeWireDriver(raw_row, name, expected["date"])
                    service = GameplayBridgeService(driver)
                    self.assertIs(type(service), GameplayBridgeService)
                    returned = service.query_army_strengths([_UNIT_ID], expected_revision=_REVISION)
                    item["actual_full_service"] = returned
                    self.assertEqual(driver.calls, [("query-army-strengths-v1", _REVISION)])
                    self.assertEqual(returned["status"], "available")
                    self.assertEqual(returned["scope_status"], "available")
                    self.assertEqual(returned["native_readiness"],
                                     {"current_strength": True, "full_monthly": False})
                    self.assertIs(returned["fixture_provenance"]["live_capture"], False)
                    self.assertIs(returned["fixture_provenance"]["query_envelope_synthetic"], True)
                    self.assertEqual(returned["source"]["revision"], _REVISION)
                    self.assertEqual(returned["source"]["native_revision"], _NATIVE_REVISION)
                    self.assertEqual(returned["source"]["date_raw"], driver.synthetic_date)
                    self.assertIsNone(returned["source"]["executable_sha256"])
                    self.assertEqual(returned["source"]["snapshot_id"],
                                     f"synthetic-fleet-tick-first-{name}")
                    self.assertEqual(len(returned["army_strengths"]), 1)
                    actual_row = returned["army_strengths"][0]
                    _check_original_scalars(self, before, actual_row, "army_strengths[0]")
                    raw = actual_row[_RAW_FAMILY]
                    self.assertEqual(raw, before[_RAW_FAMILY])
                    self.assertEqual(raw["source"], "native_current_fleet_supply_tick_inputs")
                    self.assertEqual(raw["subject_army_id"], _UNIT_ID)
                    self.assertEqual(raw["subject_carmy_id"], _CARMY_ID)
                    self.assertEqual(raw["province_id"], _PROVINCE_ID)
                    self.assertEqual(raw["status"], expected["raw_status"])
                    self.assertIs(raw["ready"], expected["raw_ready"])
                    self.assertEqual(raw["unavailable_reason"], expected["raw_reason"])
                    self.assertEqual(raw["current_native_date_low32"], expected["date"])
                    self.assertEqual(raw["scale"], 100000)
                    self.assertNotIn(_DERIVED_FAMILY, actual_row)
                    derived = returned[_DERIVED_FAMILY]
                    self.assertEqual(len(derived), 1)
                    self.assertEqual(derived[0]["army_id"], _UNIT_ID)
                    projection = derived[0]["projection"]
                    self.assertEqual(projection["source"], "conditional_same_context_next_admitted_day_fleet_rate")
                    self.assertEqual(projection["status"], expected["status"])
                    self.assertIs(projection["conditional_fleet_rate_ready"], expected["ready"])
                    self.assertEqual(projection["current_native_date_low32"], expected["date"])
                    self.assertEqual(projection["conditional_next_date_low32"], expected["next_date"])
                    self.assertEqual(projection["conditional_full_fleet_rate_raw"], expected["rate"])
                    self.assertIs(projection["fleet_date_admitted"], expected["admitted"])
                    self.assertEqual(projection["branch"], expected["branch"])
                    self.assertEqual(projection["division_path"], expected["division"])
                    self.assertEqual(projection["commander_divisor_raw"], expected["divisor"])
                    self.assertEqual(projection["missing_inputs"], expected["missing"])
                    self.assertEqual(projection["current_observed_total_rate_raw"], expected["observed"])
                    self.assertEqual(projection["scale"], 100000)
                    self.assertEqual(projection["fixed_context"], _FIXED_CONTEXT)
                    for flag in _FLAGS:
                        self.assertIs(projection[flag], False, flag)
                    if name == "01-date-opens-next-day":
                        self.assertEqual(raw["fleet_day_raw"], 1024)
                        self.assertEqual(raw["loaded_fleet_day_sentinel_raw"], -1)
                        self.assertGreater(raw["fleet_day_raw"], raw["current_native_date_low32"])
                        self.assertEqual(raw["terrain_modifier_772_raw"], 0)
                        self.assertEqual(raw["loaded_fleet_loss_raw"], 500000)
                        self.assertEqual(raw["commander_modifier_1a9_raw"], 0)
                        self.assertNotEqual(projection["conditional_full_fleet_rate_raw"],
                                            actual_row["current_supply_change_monthly_raw"])
                    elif name == "02-still-future-partial-downstream":
                        self.assertEqual(raw["fleet_day_raw"], 2000)
                        self.assertIsNone(raw["terrain_magic_38_raw"])
                        self.assertIsNone(raw["terrain_modifier_772_raw"])
                        self.assertIsNone(raw["loaded_fleet_loss_raw"])
                        self.assertIsNone(raw["commander_modifier_1a9_raw"])
                    elif name == "03-positive-terrain772":
                        self.assertEqual(raw["fleet_day_raw"], -1)
                        self.assertEqual(raw["loaded_fleet_day_sentinel_raw"], -1)
                        self.assertEqual(raw["terrain_modifier_772_raw"], 1)
                        self.assertIsNone(raw["loaded_fleet_loss_raw"])
                        self.assertIsNone(raw["commander_modifier_1a9_raw"])
                    elif name == "04-native-fallback-absent-numeric-key":
                        self.assertIs(raw["fleet_used_native_fallback"], True)
                        self.assertIs(raw["commander_used_native_fallback"], True)
                        self.assertNotEqual(raw["fleet_raw_full_id"], raw["fleet_resolved_full_id"])
                        self.assertNotEqual(raw["commander_raw_full_id"], raw["commander_resolved_full_id"])
                        self.assertEqual(raw["terrain_modifier_772_id"], 65535)
                        self.assertEqual(raw["terrain_modifier_772_raw"], 0)
                        self.assertEqual(raw["commander_modifier_1a9_raw"], 0)
                    elif name == "05-fleet-zero-divisor":
                        self.assertEqual(raw["commander_modifier_1a9_raw"], -100000)
                        self.assertEqual(raw["loaded_divisor_floor_raw"], 0)
                        self.assertEqual(projection["conditional_full_fleet_rate_raw"], 0xFFFFFFFF)
                        self.assertNotEqual(projection["conditional_full_fleet_rate_raw"], -1)
                    elif name == "06-partial-needed-fixed-modifier":
                        self.assertEqual(raw["terrain_modifier_772_raw"], 0)
                        self.assertEqual(raw["loaded_fleet_loss_raw"], 500000)
                        self.assertIsNone(raw["commander_modifier_1a9_raw"])
                        self.assertIsNone(projection["conditional_full_fleet_rate_raw"])
                        self.assertEqual(actual_row["current_supply_change_monthly_raw"], 0)
                    elif name == "07-not-fleet":
                        self.assertIs(raw["native_fleet_branch_applicable"], False)
                        for key in ("fleet_raw_full_id", "fleet_day_raw", "terrain_modifier_772_raw",
                                    "loaded_fleet_loss_raw", "commander_modifier_1a9_raw"):
                            self.assertIsNone(raw[key], key)
                        gain = actual_row["current_land_resupply_v1"]
                        land = actual_row["current_land_supply_rate_inputs_v1"]
                        self.assertIs(gain["current_observation_ready"], True)
                        self.assertIs(gain["native_resupply_eligible"], True)
                        self.assertEqual(gain["loaded_gain_raw"], 2000000)
                        self.assertIs(land["current_observation_ready"], True)
                        self.assertEqual(land["province_component_raw"], -600000)
                    elif name == "08-signed-clock-wrap":
                        self.assertEqual(raw["fleet_day_raw"], -2147483620)
                        self.assertEqual(raw["loaded_fleet_day_sentinel_raw"], -1)
                        self.assertGreater(raw["fleet_day_raw"], projection["conditional_next_date_low32"])
                    self.assertEqual(raw_row, before, "service must not mutate the parsed native wire")
                    self.assertEqual(wire_path.read_bytes(), frozen_bytes, "native wire bytes must survive unchanged")
                    item["result"] = "GREEN"
                except Exception as error:
                    item["error_type"] = type(error).__name__
                    item["error"] = str(error)
                    raise
                finally:
                    _write_json(output_dir / (name + "-service.json"), item)
                    _write_json(output_dir / "service-compound-receipt.json", receipt)


if __name__ == "__main__":
    unittest.main()
