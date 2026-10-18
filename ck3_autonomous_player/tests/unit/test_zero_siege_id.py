"""R20 native row161: storage-validated active SiegeID zero."""
import copy
import json
import unittest
from xar_autoplayer.bridge.war_contract import _normalize_active_siege

class ZeroSiegeIdRegression(unittest.TestCase):
    def test_actual_active_zero_siege_preserves_observation_and_rejects_invalid_ids(self):
        original = json.loads(ACTUAL)
        result = _normalize_active_siege(original, name="occupation.rows[161].active_siege")
        self.assertEqual(result["siege_id"], 0)
        self.assertEqual(result["besieging_army_id"], 8)
        self.assertEqual(result["current_work"], original["current_work"])
        self.assertEqual(result["province_unit_occurrences"], original["province_unit_occurrences"])
        self.assertFalse(result["can_start_assault"])
        for invalid in (None, False, -1, 0xFFFFFFFF, 2**31):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                changed = copy.deepcopy(original)
                changed["siege_id"] = invalid
                _normalize_active_siege(changed, name="occupation.rows[161].active_siege")

ACTUAL = '{"siege_id":0,"besieging_army_id":8,"player_army_besieging":false,"progress_fraction":{"raw":0,"scale":100000},"current_work":{"raw":0,"scale":100000},"total_work":{"raw":32500000,"scale":100000},"remaining_work":{"raw":32500000,"scale":100000},"days_left":170,"ordinary_daily_progress":{"raw":192000,"scale":100000},"eligible_regiment_siege_work":{"raw":80000,"scale":100000},"highest_eligible_siege_tier":1,"province_unit_occurrences":[{"occurrence_index":0,"public_unit_id":8,"native_carmy_id":8,"eligible":true,"qualified_regiment_ids":[8,9,10,11]},{"occurrence_index":1,"public_unit_id":9,"native_carmy_id":9,"eligible":true,"qualified_regiment_ids":[12,13,14,15]},{"occurrence_index":2,"public_unit_id":10,"native_carmy_id":10,"eligible":true,"qualified_regiment_ids":[16,17,18,19]},{"occurrence_index":3,"public_unit_id":11,"native_carmy_id":11,"eligible":true,"qualified_regiment_ids":[20,21,22,23]}],"current_phase_length":{"raw":2000000,"scale":100000},"prepared_phase_length":{"raw":0,"scale":100000},"phase_counter":0,"can_advance":true,"phase_event_state":{"breach_level":0,"starvation_level":0,"disease_level":0,"desertion_count":0,"stalemate_count":0},"prepared_selected_phase_event_enum":5,"assault_observable":true,"breach_level":0,"walls_breached":false,"assault_in_progress":false,"can_start_assault":false,"can_stop_assault":false,"assault_daily_progress":{"raw":0,"scale":100000},"assault_daily_casualties":0}'
