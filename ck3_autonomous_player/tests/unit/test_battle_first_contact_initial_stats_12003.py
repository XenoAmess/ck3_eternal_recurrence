"""One new case for the same-query initial Army Province adapter."""
from copy import deepcopy
import unittest

from xar_autoplayer.simulation.battle_first_contact_final_stat_refresh_12003 import (
    EntrySixStatCache12003, initial_entry_stats_from_combat_regiment_12003,
)


def _stats(province, values):
    return dict(zip(
        ("max_size", "siege_value_raw", "damage_raw", "toughness_raw", "pursuit_raw", "screen_raw"),
        values), status="available", source_target_province_id=province,
        scale=100000, unavailable_reason=None)


class FirstContactInitialStats12003Tests(unittest.TestCase):
    def test_equal_reuse_and_different_province_actual_initial_tuple(self):
        army = {"native_carmy_id": 101, "current_province_id": 2586}
        target = _stats(2586, (100, 0, 100000, 200000, 0, 0))
        initial = _stats(2585, (0, 0, -100000, 0, 400000, 500000))
        regiment = {"regiment_id": 90, "effective_stats": target}
        original = deepcopy(regiment)
        equal = initial_entry_stats_from_combat_regiment_12003(
            army, regiment, requested_target_province_id=2586)
        self.assertTrue(equal.ready)
        self.assertEqual(equal.stat_cache, EntrySixStatCache12003(100, 0, 100000, 200000, 0, 0))
        self.assertEqual(equal.ledger["selected_leaf"], "effective_stats")
        self.assertNotIn("initialization_context_stats", regiment)
        # An optional different-Province leaf is not demanded in equal branch.
        equal_extra = initial_entry_stats_from_combat_regiment_12003(
            army, dict(regiment, initialization_context_stats={"status": "unavailable"}),
            requested_target_province_id=2586)
        self.assertEqual(equal_extra.stat_cache, equal.stat_cache)

        different_army = dict(army, current_province_id=2585)
        different = initial_entry_stats_from_combat_regiment_12003(
            different_army, dict(regiment, initialization_context_stats=initial),
            requested_target_province_id=2586)
        self.assertTrue(different.ready)
        self.assertEqual(different.initialization_province_id, 2585)
        self.assertEqual(different.stat_cache, EntrySixStatCache12003(0, 0, -100000, 0, 400000, 500000))
        self.assertEqual(different.ledger["selected_leaf"], "initialization_context_stats")
        self.assertNotEqual(different.stat_cache, equal.stat_cache)
        for value in (None, {"status": "unavailable"}, target):
            missing = initial_entry_stats_from_combat_regiment_12003(
                different_army, dict(regiment, initialization_context_stats=value),
                requested_target_province_id=2586)
            self.assertFalse(missing.ready)
            self.assertIsNone(missing.stat_cache)
            self.assertTrue(missing.missing_inputs)
        unknown = initial_entry_stats_from_combat_regiment_12003(
            dict(army, current_province_id=None), regiment,
            requested_target_province_id=2586)
        self.assertFalse(unknown.ready)
        self.assertIsNone(unknown.stat_cache)
        self.assertEqual(regiment, original)
        self.assertFalse(different.ledger["admission_predicted"])
        self.assertFalse(different.ledger["posteffect_tuple_used_as_initial"])
        self.assertFalse(different.full_initialization_ready)
        self.assertFalse(different.native_write_performed)
        self.assertEqual(different.actual_game_days_advanced, 0)


if __name__ == "__main__":
    unittest.main()
