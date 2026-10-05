"""One new normalized MAA source leaf to all six stats and final-input case."""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict
import importlib.util
import json
from pathlib import Path
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


class MaaObservedInputs12003Test(unittest.TestCase):
    def test_real_groups_ordered_duplicates_fallback_and_independent_unavailable(self):
        from xar_autoplayer.bridge.maa_stat_inputs_contract import FIELDS, STAT_NAMES, ENV_NAMES, normalize_maa_stat_inputs_v1
        from xar_autoplayer.simulation.battle_maa_observed_inputs_12003 import maa_six_stats_from_combat_regiment_12003
        from xar_autoplayer.simulation.battle_maa_regiment_stats_12003 import maa_six_stats_to_final_stat_input_12003

        def stats(*values):
            return dict(zip(STAT_NAMES, values))

        def properties(mapping):
            keys = sorted(mapping)
            return {"count": len(keys), "keys_u16": keys, "values_q64": [mapping[key] for key in keys]}

        zero = stats(0, 0, 0, 0, 0, 0)
        source = dict.fromkeys(FIELDS)
        source.update(status="available", source_target_province_id=900, source_regiment_full_id=31,
            selected_character_full_id=71, character_resolution="generation_resolved",
            inner_type_is_gdbo=True, selector_mode=True, selected_type_class=5,
            type_bases=stats(100, 100000, 200000, 300000, 400000, 500000),
            selected_properties=properties({0x1BF: 900, 0x1B8: 50000, 0x1BA: 50000}),
            class_row_present=True, class_add_keys_u16=[65535] * 6, class_mult_keys_u16=[65535] * 6,
            culture_full_id=80, government_index=0,
            government_rows=[{"definition_index": 0, "row_index": 0, "definition_is_gdbo": True,
                "definition_matches_selected_type": False, "class_filter": -1, "stats": None}],
            global_rows=[{"definition_index": 0, "row_index": 1, "definition_is_gdbo": False,
                "definition_matches_selected_type": False, "class_filter": 5,
                "stats": stats(5, 100, 200, 300, 400, 500)}],
            extra_properties=properties({0x1C1: -200, 0x1C5: -400400, 0x1CB: 10000, 0x1CC: -10000}),
            extra_add_keys_u16=[65535] * 5, extra_mult_keys_u16=[65535] * 5,
            extra_title_full_id=101, extra_holder_full_id=72, holder_piety_rank=2,
            selected_government_byte_4d6=5, selector_factor_q64=50000,
            linked_character_full_ids=[71, 71], definition620_present=False,
            environment_components={key: (None if "definition" in key else zero) for key in ENV_NAMES},
            fallback_ordinary_bases=dict.fromkeys(STAT_NAMES[1:]), scale=100000,
            accolade_blocks=[{"linked_index": index, "character_full_id": 71, "accolade_full_id": 90,
                "row_index": 0, "level": 1, "properties": properties({0x1B7: 15000})} for index in (0, 1)])
        normalized = normalize_maa_stat_inputs_v1(source, name="new_source")
        before = deepcopy(normalized)
        row = {"maa_stat_inputs_v1": normalized, "effective_stats": stats(999, 999, 999, 999, 999, 999)}
        result = maa_six_stats_from_combat_regiment_12003(row)
        self.assertTrue(result.ready)
        self.assertTrue(result.full_getter_construction_ready)
        self.assertEqual(tuple(asdict(result.stat_cache).values()), (105, 50500, 200000, 195195, 0, 250250))
        self.assertEqual(result.ledger["linked_character_full_ids"], (71, 71))
        self.assertEqual(len(result.ledger["accolade_fold_updates"]), 2)
        self.assertEqual(normalized, before)
        self.assertFalse(result.full_entry_ready)
        final = maa_six_stats_to_final_stat_input_12003(result, side_index=0, bucket_index=1,
            native_carmy_id=1012, regiment_id=31, target_province_id=900)
        self.assertEqual(final.stat_cache, result.stat_cache)
        self.assertTrue(final.source_provenance["full_getter_construction_ready"])
        fallback = deepcopy(source)
        fallback.update(inner_type_is_gdbo=False, selected_properties=properties({0xB0: -200000}),
            fallback_ordinary_bases=dict(zip(STAT_NAMES[1:], (0, 100000, 0, -1, 0))))
        fallback_result = maa_six_stats_from_combat_regiment_12003({"maa_stat_inputs_v1":
            normalize_maa_stat_inputs_v1(fallback, name="inner_nonGDbo")})
        self.assertTrue(fallback_result.ready)
        self.assertEqual(tuple(asdict(fallback_result.stat_cache).values()), (0, 0, 100000, 100000, -1, 0))
        unavailable = deepcopy(source)
        unavailable.update(status="unavailable", unavailable_reason="maa_selected_context_unavailable", selected_properties=None)
        missing = maa_six_stats_from_combat_regiment_12003({"maa_stat_inputs_v1":
            normalize_maa_stat_inputs_v1(unavailable, name="missing_context")})
        self.assertFalse(missing.ready)
        self.assertIsNone(missing.stat_cache)
        empty = deepcopy(source)
        empty.update(class_row_present=False, selector_mode=False, selected_properties=properties({}),
            government_rows=[], global_rows=[], accolade_blocks=[], linked_character_full_ids=[])
        empty_result = maa_six_stats_from_combat_regiment_12003({"maa_stat_inputs_v1":
            normalize_maa_stat_inputs_v1(empty, name="native_empty")})
        self.assertTrue(empty_result.ready)
        self.assertEqual(empty_result.stat_cache.effective_damage_raw, 200000)


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
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(MaaObservedInputs12003Test))
    elapsed = time.perf_counter() - start
    args.artifacts.mkdir(exist_ok=False, parents=True)
    (args.artifacts / "RESULT.json").write_text(json.dumps({
        "status": "GREEN" if result.wasSuccessful() else "RED", "tests_run": result.testsRun,
        "errors": len(result.errors), "failures": len(result.failures), "elapsed_seconds": elapsed,
        "old_cases_rerun": 0, "game_operations": 0, "native_builds": 0,
        "qualification": "New normalized actual MAA source leaf -> six-stat construction -> existing final-input adapter; current conditional source operands only",
    }, indent=2) + "\n", encoding="utf-8")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
