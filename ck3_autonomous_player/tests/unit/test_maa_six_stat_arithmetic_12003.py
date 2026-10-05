"""One new case covering native MAA scratch/apply/order and practical consumer."""
from __future__ import annotations

import argparse
from dataclasses import asdict, replace
import importlib.util
import json
from pathlib import Path
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


class MaaSixStatArithmetic12003Test(unittest.TestCase):
    def test_named_class_aggregate_to_native_apply_environment_and_final_input(self):
        from xar_autoplayer.simulation.battle_first_contact_final_stat_refresh_12003 import (
            EntrySixStatCache12003 as Cache, PersonStatStage12003,
        )
        from xar_autoplayer.simulation.battle_maa_regiment_stats_12003 import (
            MaaSixStatStageResult12003, maa_modifier_scratch_from_person_stage_12003,
            apply_maa_six_stat_modifiers_12003, finish_maa_environment_stage_12003,
            maa_six_stats_to_final_stat_input_12003,
        )
        properties = {
            0x1B7: -50001, 0x1B8: 50000, 0x1BA: -200000,
            0x1BD: -150001, 0x1BE: 50000, 0x1BF: -150001, 0x1C0: -100000,
            0x900: 50000, 0x901: 50000,
        }
        keys = sorted(properties)
        stage = PersonStatStage12003(71, "explicit_after_person_preparation", {
            "aggregate_properties": {"count": len(keys), "keys_u16": keys,
                                     "values_q64": [properties[key] for key in keys]}}, None)
        scratch = maa_modifier_scratch_from_person_stage_12003(stage,
            class_row_present=True, class_add_keys_u16=(0x900,) + (0xFFFF,) * 5,
            class_mult_keys_u16=(0x901,) + (0xFFFF,) * 5)
        self.assertTrue(scratch.ready)
        self.assertEqual(scratch.add_q64, (50000, -150001, -50001, 0, 0, -150001))
        self.assertEqual(scratch.factor_q64, (150000, 0, 150000, -100000, 100000, 150000))
        applied = apply_maa_six_stat_modifiers_12003(
            Cache(3, 100000, 100000, 100000, 4000000001, 100000), scratch,
            stage="explicit_after_Character_context_apply")
        self.assertTrue(applied.ready)
        self.assertEqual(tuple(asdict(applied.stat_cache).values()),
                         (5, 0, 74998, -100000, 4000000001, -75001))
        self.assertFalse(applied.ledger["damage_toughness_floor_applied"])
        negative = apply_maa_six_stat_modifiers_12003(
            Cache(-3, 0, 0, 0, 0, 0), scratch, stage="negative_max_stage")
        self.assertEqual(negative.stat_cache.effective_max_size, -3)
        zero = Cache(0, 0, 0, 0, 0, 0)
        components = {
            "type_terrain": Cache(2147483647, -1, 25000, 0, -4000000002, 75001),
            "type_province": Cache(1, -2, 0, 300001, 0, 0),
            "linked_terrain": zero, "linked_province": zero,
        }
        # Explicit baseline stage already includes the real +120/selector/
        # accolade stages. Their construction is not claimed by this primitive.
        baseline = replace(applied, stage="explicit_after_all_baseline_and_accolade_modifiers")
        finished = finish_maa_environment_stage_12003(baseline,
            stage="explicit_changed_Province_getter_end", definition620_present=False,
            components=components, source_province_id=900, linked_character_full_ids=(71, 71))
        self.assertTrue(finished.ready)
        self.assertEqual(tuple(asdict(finished.stat_cache).values()),
                         (-2147483643, -3, 100000, 200001, -1, 0))
        self.assertEqual([term["component"] for term in finished.ledger["terms"]],
            ["type_terrain", "type_definition", "type_province",
             "linked_terrain", "linked_definition", "linked_province"])
        self.assertEqual(finished.ledger["linked_character_full_ids"], (71, 71))
        final = maa_six_stats_to_final_stat_input_12003(finished, side_index=1,
            bucket_index=2, native_carmy_id=1012, regiment_id=31, target_province_id=900)
        self.assertEqual((final.bucket, final.call_site, final.stat_cache),
                         ("men_at_arms", "247AB41", finished.stat_cache))
        self.assertFalse(finished.full_getter_construction_ready)
        self.assertFalse(finished.full_entry_ready)
        missing = finish_maa_environment_stage_12003(baseline, stage="missing_required_vector",
            definition620_present=True, components=components, source_province_id=900,
            linked_character_full_ids=(71, 71))
        self.assertFalse(missing.ready)
        self.assertIsNone(missing.stat_cache)
        self.assertIn("components.type_definition.effective_max_size", missing.missing_inputs)
        empty_stage = PersonStatStage12003(71, "observed_empty_context", {
            "aggregate_properties": {"count": 0, "keys_u16": [], "values_q64": []}}, None)
        empty_scratch = maa_modifier_scratch_from_person_stage_12003(empty_stage, class_row_present=False)
        self.assertTrue(empty_scratch.ready)
        self.assertEqual(empty_scratch.add_q64, (0,) * 6)
        self.assertEqual(empty_scratch.factor_q64, (100000,) * 6)
        empty_applied = apply_maa_six_stat_modifiers_12003(zero, empty_scratch, stage="zero_stage")
        self.assertTrue(empty_applied.ready)
        self.assertEqual(empty_applied.stat_cache, zero)
        unknown_class = maa_modifier_scratch_from_person_stage_12003(empty_stage, class_row_present=None)
        self.assertFalse(unknown_class.ready)
        self.assertIsNone(unknown_class.add_q64)


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
    start = time.perf_counter()
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(MaaSixStatArithmetic12003Test))
    elapsed = time.perf_counter() - start
    args.artifacts.mkdir(parents=True, exist_ok=False)
    (args.artifacts / "RESULT.json").write_text(json.dumps({
        "status": "GREEN" if result.wasSuccessful() else "RED", "tests_run": result.testsRun,
        "errors": len(result.errors), "failures": len(result.failures), "elapsed_seconds": elapsed,
        "old_cases_rerun": 0, "native_builds": 0, "game_operations": 0,
        "qualification": "Closed MAA context/apply/end-stage arithmetic and practical final consumer on explicit named intermediate operands; baseline construction remains partial",
    }, indent=2) + "\n", encoding="utf-8")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
