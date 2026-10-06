"""SOURCE_PREPARED/NOTRUN: four fresh native whole rows through actual service.

The driver supplies only transport/pause/scope/revision metadata. It never edits
the production-serialized row or calls any old test/model/normalizer fixture.
"""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest

_SOURCE_ROOT = Path(os.environ["XAR_DAILY_SUPPLY_DISPATCH_SOURCE_ROOT"]).resolve()
sys.path.insert(0, str(_SOURCE_ROOT / "src"))
from xar_autoplayer.bridge.service import GameplayBridgeService

_FAMILY = "current_daily_supply_dispatch_inputs_v1"
_UNIT, _CARMY, _REVISION = 67108883, 33554443, 42
_FALSE = ("actual_callback_observed", "earlier_stage_outputs_reconstructed",
          "full_daily_supply_transition_ready", "full_monthly_ready")
_CASES = {
    "01-original-ordered-subject-occurrences":
        (1000, 30, 0, 2, 4, True, [1, 2], 2, True, None),
    "02-unsigned-day-empty-selected-bucket":
        (0, -1, 15, 0, 0, False, [], 0, True, None),
    "03-subject-only-in-another-bucket":
        (1000, 30, 0, 1, 1, True, [], 0, True, None),
    "04-selected-count-with-unavailable-pointer-data":
        (1000, 30, 0, 1, 1, False, None, None, False,
         "daily_supply_dispatch_bucket_header_invalid"),
}


def _original_leaves(test: unittest.TestCase, original: object, actual: object) -> None:
    if isinstance(original, dict):
        test.assertIsInstance(actual, dict)
        for key, value in original.items():
            test.assertIn(key, actual)
            _original_leaves(test, value, actual[key])
    elif isinstance(original, list):
        test.assertIsInstance(actual, list)
        test.assertEqual(len(original), len(actual))
        for left, right in zip(original, actual):
            _original_leaves(test, left, right)
    else:
        test.assertIs(type(actual), type(original))
        test.assertEqual(actual, original)


class SyntheticWholeWireDriver:
    def __init__(self, row: dict[str, object], name: str, date: int) -> None:
        self.row, self.name, self.date = row, name, date
        self.calls: list[tuple[str, int | None]] = []

    def take_snapshot(self) -> dict[str, object]:
        return {
            "paused": True, "revision": _REVISION, "native_revision": 7,
            "date_raw": self.date,
            "snapshot_id": f"synthetic-current-daily-dispatch-{self.name}",
            "backend_id": "synthetic-native-whole-wire-no-game-session",
            "player_armies": [{"army_id": _UNIT}], "active_wars": [],
            "diagnostics": {"hello": {"game_version": "1.20.0.3",
                "executable_sha256": None, "synthetic_fixture": True, "live_capture": False}},
        }

    def capabilities(self) -> dict[str, object]:
        return {"action_steps": ["query-army-strengths-v1"], "synthetic_fixture": True}

    def execute_step(self, step: str, *, expected_revision: int | None = None) -> dict[str, object]:
        self.calls.append((step, expected_revision))
        if step != "query-army-strengths-v1" or expected_revision != _REVISION:
            raise ValueError("fixture transport supports only the existing Strength query")
        return {
            "status": self.row["status"], "army_strengths": [deepcopy(self.row)],
            "native_readiness": {"current_strength": True, "full_monthly": False},
            "fixture_provenance": {"whole_row_producer": "actual ReadArmyStrengthsForScope -> AppendArmyStrengthV1",
                "query_envelope_synthetic": True, "snapshot_metadata_synthetic": True,
                "native_readiness_envelope_synthetic": True, "live_capture": False,
                "actual_callback_observed": False},
        }


class CurrentDailySupplyDispatchWholeService12003Tests(unittest.TestCase):
    def test_fresh_whole_rows_preserve_current_original_subject_occurrences(self) -> None:
        self.assertEqual(sys.flags.optimize, 0)
        directory = Path(os.environ["XAR_DAILY_SUPPLY_DISPATCH_WIRE_DIR"])
        output_directory = Path(os.environ["XAR_DAILY_SUPPLY_DISPATCH_OUTPUT_DIR"])
        output_directory.mkdir(parents=True, exist_ok=True)
        receipt = {
            "topic": "current-daily-supply-dispatch/one-whole-service-compound",
            "source_root": str(_SOURCE_ROOT), "wire_directory": str(directory),
            "test_method_count": 1, "configured_case_count": 4,
            "old_test_methods_executed": 0, "live_capture": False,
            "actual_callback_observed": False, "game_days": 0,
            "result": "IN_PROGRESS", "cases": {},
        }
        for name, expected in _CASES.items():
            with self.subTest(case=name):
                artifact_path = output_directory / (name + "-service.json")
                item = {
                    "case": name, "result": "RED", "expected": expected,
                    "wire_path": str(directory / (name + ".json")),
                    "live_capture": False, "actual_callback_observed": False,
                    "raw_whole_native_row": None, "raw_original_family": None,
                    "actual_service_result": None, "returned_raw_family": None,
                }
                try:
                    raw = json.loads((directory / (name + ".json")).read_bytes())
                    before = deepcopy(raw)
                    item["raw_whole_native_row"] = before
                    item["raw_original_family"] = deepcopy(raw.get(_FAMILY))
                    self.assertEqual(raw["army_id"], _UNIT)
                    self.assertEqual(raw["native_carmy_id"], _CARMY)
                    self.assertEqual(raw["status"], "available")
                    self.assertEqual(raw["current_supply_raw"], 9000000)
                    self.assertEqual(raw["current_soldiers"], 160)
                    self.assertEqual(raw["maximum_soldiers"], 240)
                    self.assertEqual(raw["ai_base_power_raw"], 300000)
                    self.assertIs(raw["gathering_days_ready"], False)
                    self.assertIsNone(raw["gathering_days_left"])
                    driver = SyntheticWholeWireDriver(raw, name, expected[0])
                    returned = GameplayBridgeService(driver).query_army_strengths(
                        [_UNIT], expected_revision=_REVISION)
                    item["actual_service_result"] = returned
                    self.assertEqual(driver.calls, [("query-army-strengths-v1", _REVISION)])
                    self.assertEqual(returned["status"], "available")
                    self.assertEqual(returned["scope_status"], "available")
                    self.assertEqual(returned["native_readiness"],
                                     {"current_strength": True, "full_monthly": False})
                    row = returned["army_strengths"][0]
                    item["returned_raw_family"] = deepcopy(row.get(_FAMILY))
                    _original_leaves(self, before, row)
                    inputs = row[_FAMILY]
                    self.assertEqual(inputs, before[_FAMILY])
                    keys = ("current_date_raw", "native_day_index", "selected_bucket_phase",
                            "selected_bucket_capacity_raw", "selected_bucket_count_raw",
                            "selected_bucket_data_present", "subject_occurrence_indices",
                            "subject_dispatch_occurrence_count", "ready", "unavailable_reason")
                    for key, value in zip(keys, expected):
                        self.assertIs(type(inputs[key]), type(value))
                        self.assertEqual(inputs[key], value)
                    self.assertEqual(inputs["subject_army_id"], _UNIT)
                    self.assertEqual(inputs["subject_carmy_id"], _CARMY)
                    self.assertEqual(inputs["source"], "native_current_selected_supply_bucket_subject_occurrences")
                    self.assertEqual(inputs["capture_boundary"], "current_paused_strength")
                    self.assertEqual(inputs["status"], "available" if expected[8] else "unavailable")
                    for flag in _FALSE:
                        self.assertIs(inputs[flag], False)
                    self.assertIs(returned["fixture_provenance"]["live_capture"], False)
                    self.assertIsNone(returned["source"]["executable_sha256"])
                    self.assertEqual(raw, before)
                    item["result"] = "GREEN"
                except Exception as error:
                    item["error_type"] = type(error).__name__
                    item["error"] = str(error)
                    raise
                finally:
                    artifact_path.write_text(
                        json.dumps(item, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                    original = item["raw_original_family"]
                    original = original if isinstance(original, dict) else {}
                    observed = item["returned_raw_family"]
                    observed = observed if isinstance(observed, dict) else {}
                    actual_service = item["actual_service_result"]
                    actual_service = actual_service if isinstance(actual_service, dict) else {}
                    receipt["cases"][name] = {
                        "result": item["result"], "artifact_path": str(artifact_path),
                        "whole_service_status": actual_service.get("status"),
                        "scope_status": actual_service.get("scope_status"),
                        "original_family_status": original.get("status"),
                        "original_family_ready": original.get("ready"),
                        "returned_family_status": observed.get("status"),
                        "returned_family_ready": observed.get("ready"),
                        "unavailable_reason": observed.get("unavailable_reason"),
                        "selected_bucket_count_raw": observed.get("selected_bucket_count_raw"),
                        "subject_occurrence_indices": observed.get("subject_occurrence_indices"),
                        "subject_dispatch_occurrence_count": observed.get("subject_dispatch_occurrence_count"),
                    }
                    if "error" in item:
                        receipt["cases"][name]["error_type"] = item["error_type"]
                        receipt["cases"][name]["error"] = item["error"]
                    receipt["attempted_case_count"] = len(receipt["cases"])
                    if any(case["result"] == "RED" for case in receipt["cases"].values()):
                        receipt["result"] = "RED"
                    elif len(receipt["cases"]) == len(_CASES):
                        receipt["result"] = "GREEN"
                    (output_directory / "service-compound-receipt.json").write_text(
                        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
