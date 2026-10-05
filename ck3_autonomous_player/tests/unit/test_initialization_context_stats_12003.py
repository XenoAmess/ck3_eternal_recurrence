"""One focused source-closed case for initial stats through the strict consumer."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_combat_simulation_inputs_contract import _combat_inputs, _snapshot
from xar_autoplayer.bridge.combat_contract import (
    _normalize_regiment, combat_simulation_encounter_scope,
    normalize_combat_simulation_inputs,
)

CONSUMER_SOURCE: Path | None = None


def consumer_adapter():
    name = "xar_autoplayer.simulation.battle_first_contact_final_stat_refresh_12003"
    if CONSUMER_SOURCE is None:
        module = importlib.import_module(name)
    else:
        spec = importlib.util.spec_from_file_location(name, CONSUMER_SOURCE)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return module.initial_entry_stats_from_combat_regiment_12003


class InitializationContextStats12003Test(unittest.TestCase):
    def test_current_province_leaf_normalizes_and_supplies_initial_stage_only(self):
        adapter = consumer_adapter()
        initial = {
            "status": "available", "source_target_province_id": 800,
            "max_size": 200, "siege_value_raw": -100_000,
            "damage_raw": 2_000_000, "toughness_raw": 3_000_000,
            "pursuit_raw": 0, "screen_raw": -500_000,
            "scale": 100_000, "unavailable_reason": None,
        }
        raw = _combat_inputs()
        raw["armies"][0]["regiments"][0]["initialization_context_stats"] = initial
        before = deepcopy(raw)

        def normalize(value):
            return normalize_combat_simulation_inputs(
                value, expected_target_province_id=900,
                expected_attacker_entry_province_id=800,
                expected_encounter_scope=combat_simulation_encounter_scope(_snapshot(), [12], [22]),
            )

        normalized = normalize(raw)
        army = normalized["armies"][0]
        regiment = army["regiments"][0]
        result = adapter(army, regiment, requested_target_province_id=900)
        self.assertTrue(result.ready)
        self.assertEqual((result.native_carmy_id, result.regiment_id,
                          result.initialization_province_id), (1012, 31, 800))
        self.assertEqual(result.stat_cache.effective_damage_raw, 2_000_000)
        self.assertEqual(result.stat_cache.effective_pursuit_raw, 0)
        self.assertEqual(result.stat_cache.effective_screen_raw, -500_000)
        self.assertEqual(regiment["effective_stats"]["damage_raw"], 2_500_000)
        self.assertEqual(regiment["initialization_context_stats"], initial)
        self.assertEqual(raw, before)
        self.assertFalse(result.native_write_performed)
        self.assertFalse(result.full_initialization_ready)

        # Equality consumes the already-returned target tuple without a new leaf.
        defender = normalized["armies"][1]
        self.assertNotIn("initialization_context_stats", defender["regiments"][0])
        equal = adapter(defender, defender["regiments"][0], requested_target_province_id=900)
        self.assertTrue(equal.ready)
        self.assertEqual(equal.stat_cache.effective_damage_raw, 2_500_000)

        # A failed optional source stays independent from the valid target query.
        unavailable = {key: None for key in initial if key not in
                       {"status", "scale", "unavailable_reason"}}
        unavailable.update(status="unavailable", scale=100_000,
                           unavailable_reason="effective_stats_helper_failed")
        missing = deepcopy(raw)
        missing["armies"][0]["regiments"][0]["initialization_context_stats"] = unavailable
        missing_query = normalize(missing)
        self.assertTrue(missing_query["completeness"]["input_observation_ready"])
        missing_army = missing_query["armies"][0]
        missing_result = adapter(missing_army, missing_army["regiments"][0],
                                 requested_target_province_id=900)
        self.assertFalse(missing_result.ready)
        self.assertIsNone(missing_result.stat_cache)
        absent = normalize(_combat_inputs())["armies"][0]
        self.assertFalse(adapter(absent, absent["regiments"][0],
                                 requested_target_province_id=900).ready)

        # Conversely, valid initial stats survive unavailable target stats.
        target_failed = deepcopy(raw["armies"][0]["regiments"][0])
        target_failed.update(status="unavailable", unavailable_reason="effective_stats_helper_failed")
        target_failed["effective_stats"] = unavailable
        gaps = set()
        independent = _normalize_regiment(target_failed, name="army.regiments[0]",
            target_province_id=900, current_province_id=800, input_gaps=gaps)
        self.assertTrue(adapter(army, independent, requested_target_province_id=900).ready)
        self.assertIn("effective_regiment_stats", gaps)
        wrong_source = deepcopy(raw)
        wrong_source["armies"][0]["regiments"][0]["initialization_context_stats"][
            "source_target_province_id"
        ] = 900
        with self.assertRaisesRegex(ValueError, "target ProvinceID mismatch"):
            normalize(wrong_source)


def main() -> int:
    global CONSUMER_SOURCE
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts", type=Path)
    parser.add_argument("--consumer-source", type=Path,
                        help="Explicit committed peer adapter source before Root integration")
    args = parser.parse_args()
    CONSUMER_SOURCE = args.consumer_source
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(InitializationContextStats12003Test)
    )
    if args.artifacts:
        args.artifacts.mkdir(parents=True, exist_ok=True)
        sources = [Path(__file__), ROOT / "src/xar_autoplayer/bridge/combat_contract.py"]
        if CONSUMER_SOURCE:
            sources.append(CONSUMER_SOURCE)
        receipt = {
            "status": "GREEN" if result.wasSuccessful() else "RED",
            "tests_run": result.testsRun, "errors": len(result.errors),
            "failures": len(result.failures), "game_operations": 0,
            "native_build": False,
            "open_kaishek": {"status": "not-applicable",
                "reason": "Native six-stat wire normalization and Python adapter; no Paradox script semantics"},
            "sources": [{"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                        for path in sources],
        }
        (args.artifacts / "FOCUSED-PYTHON-RESULT.json").write_text(
            json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
