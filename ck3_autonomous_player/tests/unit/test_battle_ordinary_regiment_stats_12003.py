"""One focused case for the new ordinary damage stage and final-cache input."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


class OrdinaryDamageStage12003Test(unittest.TestCase):
    def test_named_stage_damage_and_partial_final_tuple(self):
        from xar_autoplayer.simulation.battle_first_contact_final_stat_refresh_12003 import PersonStatStage12003
        from xar_autoplayer.simulation.battle_ordinary_regiment_stats_12003 import (
            ordinary_damage_from_person_raw_numeric_inputs_12003,
            ordinary_damage_from_person_stage_12003,
            ordinary_damage_to_final_stat_input_12003,
        )
        # Native supplied aggregate; no weighted row, prowess or Province input.
        current = {"context": {"aggregate_properties": {
            "keys_u16": [0xB0, 0x1B3], "values_q64": [-50001, 50000], "count": 2}}}
        observed = ordinary_damage_from_person_raw_numeric_inputs_12003(current,
            selected_character_full_id=71, loaded_base_damage_raw=100000)
        self.assertTrue(observed.ready)
        self.assertEqual(observed.damage_raw, 74998)
        self.assertEqual(observed.stage, "frozen_current_person_context")
        named = PersonStatStage12003(71, "after_explicit_person_preparation", {
            "aggregate_properties": {"keys_u16": [0xB0, 0x1B3],
                                     "values_q64": [-150001, 50000], "count": 2}}, None)
        changed = ordinary_damage_from_person_stage_12003(named, loaded_base_damage_raw=100000)
        self.assertEqual(changed.damage_raw, -75001)  # native truncation toward zero
        self.assertFalse(changed.full_six_stat_getter_ready)
        partial = ordinary_damage_to_final_stat_input_12003(changed, side_index=0,
            bucket="levy", bucket_index=0, native_carmy_id=1012, regiment_id=31,
            target_province_id=900, siege_raw=0, toughness_raw=None, pursuit_raw=0, screen_raw=0)
        self.assertIsNone(partial.stat_cache)
        supplied = ordinary_damage_to_final_stat_input_12003(changed, side_index=1,
            bucket="levy", bucket_index=2, native_carmy_id=1022, regiment_id=32,
            target_province_id=900, siege_raw=-100000, toughness_raw=0, pursuit_raw=0, screen_raw=-3)
        self.assertEqual(tuple(asdict(supplied.stat_cache).values()), (0, -100000, -75001, 0, 0, -3))
        self.assertEqual(supplied.call_site, "247AB41")
        empty = {"context": {"aggregate_properties": {"count": 0}}}
        zero = ordinary_damage_from_person_raw_numeric_inputs_12003(empty,
            selected_character_full_id=71, loaded_base_damage_raw=0)
        self.assertTrue(zero.ready)
        self.assertEqual(zero.damage_raw, 0)
        missing = ordinary_damage_from_person_raw_numeric_inputs_12003(empty,
            selected_character_full_id=71, loaded_base_damage_raw=None)
        self.assertFalse(missing.ready)
        self.assertIsNone(missing.damage_raw)
        large = PersonStatStage12003(71, "large_operand_stage", {
            "aggregate_properties": {"keys_u16": [0x1B3], "values_q64": [50000], "count": 1}}, None)
        value = ordinary_damage_from_person_stage_12003(large, loaded_base_damage_raw=4000000001)
        self.assertEqual(value.damage_raw, 6000000001)
        self.assertFalse(value.native_write_performed)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--consumer-source", type=Path)
    parser.add_argument("--artifacts", type=Path, required=True)
    args = parser.parse_args()
    if args.consumer_source:
        name = "xar_autoplayer.simulation.battle_first_contact_final_stat_refresh_12003"
        spec = importlib.util.spec_from_file_location(name, args.consumer_source)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(OrdinaryDamageStage12003Test))
    args.artifacts.mkdir(parents=True, exist_ok=False)
    paths = [Path(__file__), ROOT / "src/xar_autoplayer/simulation/battle_ordinary_regiment_stats_12003.py"]
    if args.consumer_source:
        paths.append(args.consumer_source)
    (args.artifacts / "RESULT.json").write_text(json.dumps({
        "status": "GREEN" if result.wasSuccessful() else "RED", "tests_run": result.testsRun,
        "errors": len(result.errors), "failures": len(result.failures),
        "game_operations": 0, "native_builds": 0, "old_cases_rerun": 0,
        "qualification": "source-bound pure arithmetic over explicit supplied operands; no native/live credit",
        "sources": [{"path": p.as_posix(), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths],
    }, indent=2) + "\n", encoding="utf-8")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
