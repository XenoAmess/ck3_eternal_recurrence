"""One new meaningful same-query source-to-six-cache consumer case."""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))


class OrdinarySixStatSources12003Test(unittest.TestCase):
    def test_production_normalized_sources_supply_current_and_explicit_changed_stage(self):
        from test_combat_simulation_inputs_contract import _combat_inputs
        from xar_autoplayer.bridge.combat_contract import _normalize_regiment
        from xar_autoplayer.simulation.battle_first_contact_final_stat_refresh_12003 import PersonStatStage12003
        from xar_autoplayer.simulation.battle_ordinary_regiment_stats_12003 import (
            ordinary_six_stats_from_combat_regiment_12003,
            ordinary_six_stats_from_person_stage_12003,
            ordinary_six_stats_to_final_stat_input_12003,
        )
        leaf = {"status": "available", "selected_character_full_id": 71,
            "character_resolution": "generation_resolved", "aggregate_properties": {
                "count": 10, "keys_u16": [0xB0, 0xB1, 0xB2, 0xB3, 0xB4, 0x1B2, 0x1B3, 0x1B4, 0x1B5, 0x1B6],
                "values_q64": [-50001, 0, 100000, 0, -150001, -100000, 50000, -200000, 0, 50000]},
            "loaded_bases": {"siege_raw": 100000, "damage_raw": 100000, "toughness_raw": 100000,
                             "pursuit_raw": 4000000001, "screen_raw": 100000},
            "scale": 100000, "unavailable_reason": None}
        raw = _combat_inputs()["armies"][0]["regiments"][0]
        raw["ordinary_stat_inputs_v1"] = leaf
        before = deepcopy(raw)
        gaps = set()
        normalized = _normalize_regiment(raw, name="ordinary.regiment", target_province_id=900,
                                         current_province_id=800, input_gaps=gaps)
        result = ordinary_six_stats_from_combat_regiment_12003(normalized)
        self.assertTrue(result.ready)
        self.assertFalse(gaps)
        self.assertEqual(tuple(asdict(result.stat_cache).values()), (0, 0, 74998, -100000, 4000000001, -75001))
        self.assertEqual(raw, before)
        changed_context = deepcopy(leaf["aggregate_properties"])
        changed_context["values_q64"][0] = -150001
        stage = PersonStatStage12003(71, "explicit_changed_stage", {"aggregate_properties": changed_context}, None)
        changed = ordinary_six_stats_from_person_stage_12003(stage, loaded_bases=normalized["ordinary_stat_inputs_v1"]["loaded_bases"])
        self.assertEqual(changed.stat_cache.effective_damage_raw, -75001)
        final = ordinary_six_stats_to_final_stat_input_12003(changed, side_index=1, bucket="levy",
            bucket_index=2, native_carmy_id=1012, regiment_id=31, target_province_id=900)
        self.assertEqual(final.call_site, "247AB41")
        self.assertEqual(final.stat_cache, changed.stat_cache)
        self.assertFalse(changed.full_entry_ready)
        missing = deepcopy(raw)
        missing["ordinary_stat_inputs_v1"].update(status="unavailable", unavailable_reason="ordinary_loaded_or_aggregate_operand_unavailable")
        missing["ordinary_stat_inputs_v1"]["loaded_bases"]["screen_raw"] = None
        normalized_missing = _normalize_regiment(missing, name="ordinary.regiment", target_province_id=900,
                                                 current_province_id=800, input_gaps=set())
        partial = ordinary_six_stats_from_combat_regiment_12003(normalized_missing)
        self.assertFalse(partial.ready)
        self.assertIsNone(partial.stat_cache)
        self.assertEqual(normalized_missing["effective_stats"]["status"], "available")
        empty = deepcopy(normalized)
        empty["ordinary_stat_inputs_v1"]["aggregate_properties"] = {"count": 0, "keys_u16": [], "values_q64": []}
        empty["ordinary_stat_inputs_v1"]["loaded_bases"] = {key: 0 for key in leaf["loaded_bases"]}
        zeros = ordinary_six_stats_from_combat_regiment_12003(empty)
        self.assertTrue(zeros.ready)
        self.assertEqual(tuple(asdict(zeros.stat_cache).values()), (0, 0, 0, 0, 0, 0))


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
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(OrdinarySixStatSources12003Test))
    args.artifacts.mkdir(parents=True, exist_ok=False)
    (args.artifacts / "RESULT.json").write_text(json.dumps({
        "status": "GREEN" if result.wasSuccessful() else "RED", "tests_run": result.testsRun,
        "errors": len(result.errors), "failures": len(result.failures),
        "old_cases_rerun": 0, "native_builds": 0, "game_operations": 0,
        "qualification": "Production strict-normalizer optional source leaf to all six ordinary getter results and practical final input; explicit conditional context, no live credit",
    }, indent=2) + "\n", encoding="utf-8")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
