"""One new same-query diagnostic contract case; actual814 enclosing inputs reused."""

from copy import deepcopy
import json
from pathlib import Path
import unittest

from xar_autoplayer.bridge.combat_contract import (
    _normalize_knights, combat_simulation_encounter_scope,
    normalize_combat_simulation_inputs,
)


FIXTURE = Path(__file__).parents[1] / "fixtures/combat/live_814_12003_general_battle_v2.json"
SELECTED_CONTEXT = Path(__file__).parents[1] / "fixtures/combat/live_814_selected_character_33435_context.json"


def source_shaped_observation(selected_id):
    # The new leaf is synthetic. The surrounding814 inputs are genuine cached data.
    def occurrence(index, installed, paired_present, paired_installed):
        return {"occurrence": index, "old_model_matches_installed": installed,
                "old_owner_matches_selected": True, "paired_model_present": paired_present,
                "paired_model_matches_old": False if paired_present else None,
                "paired_model_matches_installed": paired_installed,
                "paired_owner_matches_selected": True if paired_present else None}
    return {
        "schema": "ck3_12003_knight_current_model_association_v1",
        "read_scope": "frozen_current_character_values", "selected_character_id": selected_id,
        "current_installed": {"status": "available", "carrier_present": True,
            "installed_model_present": True, "owner_present": True,
            "owner_matches_selected": True, "getter_receiver_matches_model_inline": True,
            "context_source": "model_inline", "unavailable_reason": None},
        "queue_census": {"status": "available", "old_count_raw": 3, "pair_count_raw": 3,
            "first_unread_occurrence": None,
            "relevant_occurrences": [occurrence(0, True, True, False),
                                     occurrence(1, False, True, True),
                                     occurrence(2, True, False, None)],
            "unavailable_reason": None},
    }


class KnightCurrentModelAssociation12003Test(unittest.TestCase):
    def test_same_sample_physical_comparisons_and_independent_unknown(self):
        frame = json.loads(FIXTURE.read_text(encoding="utf-8"))["frame"]
        raw = deepcopy(frame["combat_simulation_inputs"])
        army = next(row for row in raw["armies"] if row["knights"]["members"])
        member = army["knights"]["members"][0]
        selected = json.loads(SELECTED_CONTEXT.read_text(encoding="utf-8"))
        self.assertEqual(member["character_id"], selected["linked_character_id"])
        member["effectiveness_context"] = selected["effectiveness_context"]
        context = member["effectiveness_context"]
        scalar, damage = member["knight_effectiveness_raw"], member["effective_damage_raw"]
        new = source_shaped_observation(context["character_id"])
        context["current_model_association_v1"] = new
        scope = combat_simulation_encounter_scope(frame, [218104048], [134218098])
        normalized = normalize_combat_simulation_inputs(raw,
            expected_target_province_id=2606, expected_attacker_entry_province_id=8756,
            expected_encounter_scope=scope)
        observed_army = next(row for row in normalized["armies"] if row["army_id"] == army["army_id"])
        observed = observed_army["knights"]["members"][0]
        self.assertEqual(observed["effectiveness_context"]["current_model_association_v1"], new)
        self.assertEqual(observed["knight_effectiveness_raw"], scalar)
        self.assertEqual(observed["effective_damage_raw"], damage)
        self.assertTrue(normalized["completeness"]["input_observation_ready"])
        self.assertFalse(normalized["completeness"]["monte_carlo_ready"])

        def consume_leaf(value):
            gaps = set()
            output = _normalize_knights(value, name="army.knights",
                native_carmy_id=army["native_carmy_id"],
                regiment_ids={row["regiment_id"] for row in army["regiments"]},
                input_gaps=gaps, seen_knight_ids=set(), seen_knight_regiment_ids=set())
            self.assertEqual(gaps, set())
            self.assertEqual(output["members"][0]["knight_effectiveness_raw"], scalar)
            self.assertEqual(output["members"][0]["effective_damage_raw"], damage)
            return output["members"][0]["effectiveness_context"]

        partial = deepcopy(army["knights"])
        leaf = partial["members"][0]["effectiveness_context"]["current_model_association_v1"]
        leaf["queue_census"]["status"] = "partial"
        leaf["queue_census"]["unavailable_reason"] = "paired_model_owner_unreadable"
        leaf["queue_census"]["relevant_occurrences"][0]["paired_owner_matches_selected"] = None
        self.assertIsNone(consume_leaf(partial)["current_model_association_v1"]["queue_census"]
            ["relevant_occurrences"][0]["paired_owner_matches_selected"])
        empty = deepcopy(partial)
        queue = empty["members"][0]["effectiveness_context"]["current_model_association_v1"]["queue_census"]
        queue.update(status="available", old_count_raw=0, pair_count_raw=0,
                     relevant_occurrences=[], unavailable_reason=None)
        self.assertEqual(consume_leaf(empty)["current_model_association_v1"]["queue_census"]["old_count_raw"], 0)
        missing = deepcopy(partial)
        queue = missing["members"][0]["effectiveness_context"]["current_model_association_v1"]["queue_census"]
        queue.update(status="unavailable", old_count_raw=None, pair_count_raw=None,
                     relevant_occurrences=[], unavailable_reason="modifier_manager_reads_unavailable")
        self.assertIsNone(consume_leaf(missing)["current_model_association_v1"]["queue_census"]["old_count_raw"])
        old = deepcopy(army["knights"])
        del old["members"][0]["effectiveness_context"]["current_model_association_v1"]
        self.assertNotIn("current_model_association_v1", consume_leaf(old))


if __name__ == "__main__":
    unittest.main()
