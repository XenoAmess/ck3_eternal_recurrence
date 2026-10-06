"""One new compound production normalizer -> source adapter -> consumer case."""

from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.combat_contract import (
    combat_simulation_encounter_scope,
    normalize_combat_simulation_inputs,
)
from xar_autoplayer.bridge.phase_rite_parameters_contract import (
    PHASE_RITE_PARAMETERS_LEAF,
    normalize_phase_rite_parameters_v1,
)
from xar_autoplayer.simulation.battle_phase_events_12003 import load_stock_phase_events_12003
from xar_autoplayer.simulation.phase_rite_parameters_12003 import (
    DEATH_IS_GLORY_EVENT_ROLES_12003,
    ROOT_DEATH_IS_GLORY_REF,
    PhaseRiteOccurrence12003,
    adapt_phase_rite_parameters_12003,
    apply_death_is_glory_modifier_12003,
)
# Reuse fixture builders only. None of the older unittest cases run here.
from test_combat_simulation_inputs_contract import _combat_inputs, _snapshot


def _leaf(character_id: int, rite_id: int, keys: list[str], faith_id: int | None = 901) -> dict[str, object]:
    return {
        "status": "available",
        "source_character_id": character_id,
        "raw_adopted_rite_id": rite_id,
        "rite_id": rite_id,
        "faith_id": faith_id,
        "boolean_parameters_complete": True,
        "boolean_parameter_keys": keys,
        "unavailable_reason": None,
    }


def _normalize(value: dict[str, object]) -> dict[str, object]:
    return normalize_combat_simulation_inputs(
        value,
        expected_target_province_id=900,
        expected_attacker_entry_province_id=800,
        expected_encounter_scope=combat_simulation_encounter_scope(_snapshot(), [12], [22]),
    )


class PhaseRiteParameters12003Tests(unittest.TestCase):
    def test_compound_production_leaf_source_occurrences_and_modifier(self) -> None:
        value = _combat_inputs()
        for army in value["armies"]:
            army["commander"].update({
                "status": "available", "character_id": 77,
                "generic_advantage_points": 3,
            })
        value["armies"][0]["commander"][PHASE_RITE_PARAMETERS_LEAF] = _leaf(
            77, 0xF1000001, ["death_is_glory", "other_observed_parameter"]
        )
        value["armies"][1]["commander"][PHASE_RITE_PARAMETERS_LEAF] = _leaf(77, 0xF1000001, [])
        member = {
            "eligible": True, "character_id": 77, "source_regiment_id": 31,
            "army_id": 1_012, "participant_army_membership_verified": True,
            "prowess": 2, "knight_effectiveness_raw": 185_000,
            "effective_damage_raw": 18_500_000, "effective_toughness_raw": 3_700_000,
            "scale": 100_000,
            PHASE_RITE_PARAMETERS_LEAF: _leaf(
                77, 0, ["killing_bestows_heads", "decapitation_steals_prestige_as_piety"], None
            ),
        }
        value["armies"][0]["knights"]["members"] = [member]
        before = copy.deepcopy(value)
        normalized = _normalize(value)
        self.assertEqual(value, before)
        first_commander = PhaseRiteOccurrence12003("commander", 12, None, 77)
        other_commander = PhaseRiteOccurrence12003("commander", 22, None, 77)
        knight = PhaseRiteOccurrence12003("knight", 12, 31, 77)
        first = adapt_phase_rite_parameters_12003(normalized, occurrence=first_commander)
        second = adapt_phase_rite_parameters_12003(normalized, occurrence=other_commander)
        knight_root = adapt_phase_rite_parameters_12003(normalized, occurrence=knight)
        selected = adapt_phase_rite_parameters_12003(normalized, occurrence=knight, scope="selected_enemy_knight")
        self.assertTrue(first.require_boolean(ROOT_DEATH_IS_GLORY_REF))
        self.assertFalse(second.require_boolean(ROOT_DEATH_IS_GLORY_REF))
        self.assertFalse(knight_root.require_boolean(ROOT_DEATH_IS_GLORY_REF))
        self.assertEqual(first.occurrence, first_commander)
        self.assertEqual(second.occurrence, other_commander)
        self.assertEqual(knight_root.occurrence.source_regiment_id, 31)
        self.assertEqual(first.leaf["raw_adopted_rite_id"], 0xF1000001)
        self.assertEqual(knight_root.leaf["rite_id"], 0)
        self.assertIsNone(knight_root.leaf["faith_id"])
        self.assertTrue(selected.require_boolean("selected_enemy_knight.rite.killing_bestows_heads"))
        self.assertTrue(selected.require_boolean("selected_enemy_knight.rite.decapitation_steals_prestige_as_piety"))
        # The source fixture's Faith main Rite deliberately differs. The
        # adapter accepts only the candidate's adopted leaf, never this set.
        main_rite = _leaf(77, 4123, ["death_is_glory"])
        self.assertNotEqual(main_rite["rite_id"], knight_root.leaf["rite_id"])
        self.assertIn("death_is_glory", main_rite["boolean_parameter_keys"])
        self.assertNotIn("death_is_glory", knight_root.leaf["boolean_parameter_keys"])
        self.assertTrue(normalized["completeness"]["input_observation_ready"])
        self.assertFalse(normalized["completeness"]["monte_carlo_ready"])

        stock = load_stock_phase_events_12003()
        for event_key, role in DEATH_IS_GLORY_EVENT_ROLES_12003.items():
            row = next(row for row in stock.event_rows if row.key == event_key)
            self.assertEqual(row.event_type, role)
            self.assertIn(ROOT_DEATH_IS_GLORY_REF, row.state_dependencies)
            source = first if role == "commander" else knight_root
            self.assertEqual(apply_death_is_glory_modifier_12003(
                100_009, event_key=event_key, source=source
            ), 110_009 if role == "commander" else 100_009)
        self.assertEqual(apply_death_is_glory_modifier_12003(
            -100_009, event_key="commander_wounded", source=first
        ), -110_009)

        # Full Character generation is preserved by the leaf normalizer too.
        high_character = _leaf(0xF1234567, 0, [])
        self.assertEqual(normalize_phase_rite_parameters_v1(
            high_character, expected_character_id=0xF1234567
        )["source_character_id"], 0xF1234567)

        absent = {
            "status": "absent", "source_character_id": 77,
            "raw_adopted_rite_id": 0xFFFFFFFF, "rite_id": None, "faith_id": None,
            "boolean_parameters_complete": False, "boolean_parameter_keys": [],
            "unavailable_reason": None,
        }
        for leaf, expected_status, expected_bool, expected_reason in (
            (absent, "absent", False, None),
            ({**_leaf(77, 0, []), "status": "unavailable",
              "boolean_parameters_complete": False,
              "unavailable_reason": "rite_boolean_key_unavailable"},
             "unavailable", None, "rite_boolean_key_unavailable"),
            (None, "unavailable", None, "phase_rite_parameters_leaf_not_published"),
        ):
            case = copy.deepcopy(value)
            carrier = case["armies"][0]["commander"]
            if leaf is None:
                carrier.pop(PHASE_RITE_PARAMETERS_LEAF)
            else:
                carrier[PHASE_RITE_PARAMETERS_LEAF] = leaf
            observed = _normalize(case)
            source = adapt_phase_rite_parameters_12003(observed, occurrence=first_commander)
            self.assertEqual(source.status, expected_status)
            self.assertIs(source.refs[ROOT_DEATH_IS_GLORY_REF], expected_bool)
            self.assertEqual(source.unavailable_reason, expected_reason)
            self.assertEqual(observed["completeness"], normalized["completeness"])
            if leaf is None:
                self.assertIsNone(observed["armies"][0]["commander"].get(PHASE_RITE_PARAMETERS_LEAF))
            if expected_bool is None:
                with self.assertRaisesRegex(ValueError, "unavailable"):
                    apply_death_is_glory_modifier_12003(100_009, event_key="commander_wounded", source=source)
            else:
                self.assertEqual(apply_death_is_glory_modifier_12003(
                    100_009, event_key="commander_wounded", source=source
                ), 100_009)

        unavailable_knight = copy.deepcopy(value)
        unavailable_knight["armies"][0]["knights"]["members"][0][PHASE_RITE_PARAMETERS_LEAF] = {
            **_leaf(77, 0, []), "status": "unavailable",
            "rite_id": None, "faith_id": None,
            "boolean_parameters_complete": False,
            "unavailable_reason": "rite_pointer_unavailable",
        }
        selected_unknown = adapt_phase_rite_parameters_12003(
            _normalize(unavailable_knight), occurrence=knight, scope="selected_enemy_knight"
        )
        self.assertTrue(all(value is None for value in selected_unknown.refs.values()))
        unobserved = adapt_phase_rite_parameters_12003(
            normalized, occurrence=PhaseRiteOccurrence12003("knight", 22, 31, 77)
        )
        self.assertIsNone(unobserved.refs[ROOT_DEATH_IS_GLORY_REF])
        self.assertEqual(unobserved.unavailable_reason, "phase_role_occurrence_unobserved")


if __name__ == "__main__":
    unittest.main(verbosity=2)
