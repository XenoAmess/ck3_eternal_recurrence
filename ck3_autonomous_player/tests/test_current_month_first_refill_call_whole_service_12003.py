"""SOURCE_PREPARED / NOTRUN: one new whole native-wire actual-service compound.

Snapshot/envelope metadata is synthetic. Current C0 comes unchanged from the
new whole native producer; no old test, calendar model or replacement normalizer.
"""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest

_SOURCE_ROOT = Path(os.environ["XAR_MONTH_FIRST_SOURCE_ROOT"]).resolve()
sys.path.insert(0, str(_SOURCE_ROOT / "src"))
from xar_autoplayer.bridge.service import GameplayBridgeService

_FAMILY = "current_month_first_refill_call_inputs_v1"
_CASES = {
    "01-flags0-skip": (0, False), "02-flags1-not-month-first": (1, False),
    "03-flags2-month-first": (2, True), "04-flags3-other-bit-preserved": (3, True),
    "05-flags255-byte-width": (255, True), "06-game-state-unavailable": (None, None),
}
_FALSE_FLAGS = ("actual_pre_date_prepare_observed", "actual_post_date_refill_observed",
                "actual_after", "full_monthly_ready")


def _check_original(test: unittest.TestCase, raw: object, mapped: object, path: str) -> None:
    if isinstance(raw, dict):
        test.assertIsInstance(mapped, dict, path)
        for key, value in raw.items():
            test.assertIn(key, mapped, path)
            _check_original(test, value, mapped[key], f"{path}.{key}")
    elif isinstance(raw, list):
        test.assertIsInstance(mapped, list, path)
        test.assertEqual(len(mapped), len(raw), path)
        for index, value in enumerate(raw):
            _check_original(test, value, mapped[index], f"{path}[{index}]")
    else:
        test.assertIs(type(mapped), type(raw), path)
        test.assertEqual(mapped, raw, path)


class SyntheticMonthFirstWholeWireDriver:
    def __init__(self, row: dict[str, object], name: str) -> None:
        self.row, self.name, self.calls = row, name, []

    def take_snapshot(self) -> dict[str, object]:
        return {
            "paused": True, "revision": 42, "native_revision": 7, "date_raw": 1000,
            "snapshot_id": "synthetic-month-first-" + self.name,
            "backend_id": "synthetic-whole-native-wire-no-live",
            "player_armies": [{"army_id": 67108883}], "active_wars": [],
            "diagnostics": {"hello": {"game_version": "1.20.0.3", "executable_sha256": None}},
        }

    def capabilities(self) -> dict[str, object]:
        return {"action_steps": ["query-army-strengths-v1"], "synthetic_fixture": True}

    def execute_step(self, step: str, *, expected_revision: int | None = None) -> dict[str, object]:
        if step != "query-army-strengths-v1" or expected_revision != 42:
            raise ValueError("fixture supports only this readonly Strength query")
        self.calls.append((step, expected_revision))
        return {"status": self.row["status"], "army_strengths": [deepcopy(self.row)],
                "native_readiness": {"current_strength": True, "full_monthly": False},
                "fixture_provenance": {"transport_metadata_synthetic": True, "live_capture": False}}


class CurrentMonthFirstRefillCallWholeService12003Tests(unittest.TestCase):
    def test_whole_native_byte_mask2_preserves_current_rows_and_unavailable_null(self) -> None:
        self.assertEqual(sys.flags.optimize, 0, "FIRST invocation must not use -O")
        wire_dir = Path(os.environ["XAR_MONTH_FIRST_WIRE_DIR"])
        output_dir = Path(os.environ["XAR_MONTH_FIRST_OUTPUT_DIR"])
        output_dir.mkdir(parents=True, exist_ok=True)
        requested = os.environ.get("XAR_MONTH_FIRST_CASES")
        names = ([name.strip() for name in requested.split(",") if name.strip()]
                 if requested is not None else list(_CASES))
        self.assertTrue(names)
        self.assertEqual(len(names), len(set(names)))
        self.assertFalse(set(names) - set(_CASES))
        receipt = {"configured_case_count": 6, "selected_cases": names,
                   "source_commit_metadata": os.environ.get("XAR_MONTH_FIRST_SOURCE_COMMIT"),
                   "source_root": str(_SOURCE_ROOT), "live_capture": False, "cases": {}}
        for name in names:
            with self.subTest(case=name):
                flags, mask = _CASES[name]
                item = {"result": "RED", "live_capture": False, "expected_flags": flags,
                        "expected_mask2": mask, "wire_path": str(wire_dir / (name + ".json"))}
                receipt["cases"][name] = item
                try:
                    path = wire_dir / (name + ".json")
                    frozen = path.read_bytes()
                    row = json.loads(frozen)
                    before = deepcopy(row)
                    item["raw_whole_native_row"] = before
                    driver = SyntheticMonthFirstWholeWireDriver(row, name)
                    returned = GameplayBridgeService(driver).query_army_strengths([67108883], expected_revision=42)
                    item["actual_full_service"] = returned
                    self.assertEqual(driver.calls, [("query-army-strengths-v1", 42)])
                    self.assertEqual(returned["status"], "available")
                    self.assertEqual(returned["scope_status"], "available")
                    self.assertEqual(returned["native_readiness"],
                                     {"current_strength": True, "full_monthly": False})
                    self.assertIs(returned["fixture_provenance"]["live_capture"], False)
                    self.assertIsNone(returned["source"]["executable_sha256"])
                    self.assertEqual(returned["source"]["date_raw"], 1000)
                    self.assertEqual(len(returned["army_strengths"]), 1)
                    mapped = returned["army_strengths"][0]
                    _check_original(self, before, mapped, "army_strengths[0]")
                    self.assertEqual(mapped["current_soldiers"], 160)
                    self.assertEqual(mapped["maximum_soldiers"], 240)
                    self.assertEqual(mapped["ai_base_power_raw"], 300000)
                    self.assertEqual(mapped["current_supply_raw"], 9000000)
                    self.assertIsNone(mapped["current_supply_change_monthly_raw"])
                    leaf = mapped[_FAMILY]
                    self.assertEqual(leaf, before[_FAMILY])
                    self.assertEqual(leaf["subject_army_id"], 67108883)
                    self.assertEqual(leaf["subject_carmy_id"], 33554443)
                    self.assertEqual(leaf["game_state_calendar_flags_raw_u8"], flags)
                    self.assertIs(leaf["month_first_mask_2_set"], mask)
                    self.assertIs(leaf["ready"], flags is not None)
                    self.assertEqual(leaf["status"], "available" if flags is not None else "unavailable")
                    self.assertEqual(leaf["unavailable_reason"], None if flags is not None
                                     else "native_month_first_game_state_unavailable")
                    for field in _FALSE_FLAGS:
                        self.assertIs(leaf[field], False, field)
                    self.assertEqual(row, before)
                    self.assertEqual(path.read_bytes(), frozen)
                    item["result"] = "GREEN"
                except Exception as error:
                    item.update(error_type=type(error).__name__, error=str(error))
                    raise
                finally:
                    (output_dir / (name + "-service.json")).write_text(
                        json.dumps(item, indent=2) + "\n", encoding="utf-8")
                    (output_dir / "service-compound-receipt.json").write_text(
                        json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
