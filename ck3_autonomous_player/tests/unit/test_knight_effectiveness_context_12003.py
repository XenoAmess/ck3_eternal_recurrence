"""New selected-Character context fields through the production knight consumer."""

from copy import deepcopy
import unittest

from xar_autoplayer.bridge.combat_contract import _normalize_knights


class KnightEffectivenessContext12003Test(unittest.TestCase):
    def test_current_context_identity_inputs_and_independent_missing(self):
        context = {
            "schema": "ck3_12003_knight_effectiveness_context_v1",
            "status": "available",
            "character_id": 29829,
            "modifier_indices": list(range(0xC1, 0xCA)),
            "modifier_raw": [25000, -1000, 0, 200, -300, 0, 700, 0, -900],
            "operand_raw": [100000, 0, -50000, 0, 2200000, -300000,
                            1400000, 1800000, 700000],
            "scale": 100000,
            "unavailable_reason": None,
        }
        member = {
            "eligible": True, "character_id": 56513,
            "source_regiment_id": 67108900, "army_id": 33554460,
            "participant_army_membership_verified": True,
            "prowess": 0, "knight_effectiveness_raw": 100000,
            "effective_damage_raw": 5000000,
            "effective_toughness_raw": 1000000, "scale": 100000,
            "effectiveness_context": context,
        }
        leaf = {"status": "available", "members": [member],
                "loaded_damage_multiplier": 50, "loaded_toughness_multiplier": 10,
                "unavailable_reason": None}

        def consume(value):
            gaps = set()
            output = _normalize_knights(value, name="army.knights",
                native_carmy_id=33554460, regiment_ids={67108900}, input_gaps=gaps,
                seen_knight_ids=set(), seen_knight_regiment_ids=set())
            self.assertEqual(gaps, set())
            return output["members"][0]

        current = consume(leaf)
        self.assertEqual(current["character_id"], 56513)
        self.assertEqual(current["effectiveness_context"], context)
        self.assertEqual(current["prowess"], 0)
        self.assertEqual(current["knight_effectiveness_raw"], 100000)

        old = deepcopy(leaf)
        del old["members"][0]["effectiveness_context"]
        self.assertNotIn("effectiveness_context", consume(old))

        missing = deepcopy(leaf)
        missing["members"][0]["effectiveness_context"] = {
            **context, "status": "unavailable", "modifier_raw": None,
            "operand_raw": None, "unavailable_reason": "effectiveness_context_modifiers_unavailable",
        }
        missing_result = consume(missing)
        self.assertEqual(missing_result["effectiveness_context"]["character_id"], 29829)
        self.assertIsNone(missing_result["effectiveness_context"]["modifier_raw"])
        self.assertEqual(missing_result["effective_damage_raw"], 5000000)

        independent = deepcopy(leaf)
        independent["members"][0]["effectiveness_context"]["character_id"] = 56513
        self.assertEqual(consume(independent)["effectiveness_context"]["character_id"], 56513)

        for replacement in ([*range(0xB6, 0xBF)], [193] * 9):
            malformed = deepcopy(leaf)
            malformed["members"][0]["effectiveness_context"]["modifier_indices"] = replacement
            with self.assertRaisesRegex(ValueError, "modifier_indices"):
                consume(malformed)


if __name__ == "__main__":
    unittest.main()
