"""One new compound production normalizer -> actual stock AST validity case."""
from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.combat_contract import combat_simulation_encounter_scope, normalize_combat_simulation_inputs
from xar_autoplayer.simulation.battle_phase_events_12003 import load_stock_phase_events_12003
from xar_autoplayer.simulation.phase_berserker_validity_12003 import (
    adapt_phase_berserker_validity_inputs_12003, evaluate_berserker_stock_validity_12003,
)
from xar_autoplayer.simulation.phase_warmonger_core_12003 import PhaseWarmongerKnightOccurrence12003
# Constructors only; no previously passed unittest method executes.
from test_combat_simulation_inputs_contract import _combat_inputs, _snapshot


def _remaining(heritage: bool | None, germanic: bool | None, traits, *, zero: bool = False):
    culture_id, rite_id, faith_id, religion_id = (0, 0, 0, 0) if zero else (
        0xE1000001, 0xF1000001, 0xD1000002, 0xC1000003,
    )
    keys = ["heritage_north_germanic" if heritage else "heritage_other", "ethos_bellicose",
            "language_norse", "martial_custom_male_only", "naming_list_norse"]
    return {
        "source_character_id": 77,
        "culture": {
            "status": "available" if heritage is not None else "unavailable",
            "raw_culture_id": culture_id if heritage is not None else 0xFFFFFFFF,
            "culture_id": culture_id if heritage is not None else None,
            "resolution": "resolved" if heritage is not None else "native_fallback",
            "selected_pillar_keys": keys if heritage is not None else None,
            "heritage_north_germanic": heritage,
            "unavailable_reason": None if heritage is not None else "native_fallback_heritage_unobserved",
        },
        "religion": {
            "status": "available" if germanic is not None else "unavailable",
            "raw_adopted_rite_id": rite_id, "rite_id": rite_id,
            "raw_faith_id": faith_id, "faith_id": faith_id,
            "raw_religion_id": religion_id, "religion_id": religion_id, "resolution": "resolved",
            "religion_key": ("germanic_religion" if germanic else "christianity_religion") if germanic is not None else None,
            "germanic": germanic,
            "unavailable_reason": None if germanic is not None else "religion_definition_key_unavailable",
        },
        "traits": {
            key: {"status": "available" if value is not None else "unavailable", "value": value,
                  "unavailable_reason": None if value is not None else "trait_definition_unresolved"}
            for key, value in zip(("craven", "berserker", "calm"), traits)
        },
    }


def _payload(leaf, warmonger: bool | None, *, zero: bool = False):
    payload = _combat_inputs()
    rite_id = 0 if zero else 0xF1000001
    member = {
        "eligible": True, "character_id": 77, "source_regiment_id": 31,
        "army_id": 1012, "participant_army_membership_verified": True,
        "prowess": 2, "knight_effectiveness_raw": 185000,
        "effective_damage_raw": 18500000, "effective_toughness_raw": 3700000, "scale": 100000,
        "phase_warmonger_core_v1": {
            "status": "available" if warmonger is not None else "unavailable",
            "source_character_id": 77, "raw_adopted_rite_id": rite_id, "rite_id": rite_id,
            "rite_resolution": "adopted", "requested_tenet_key": "tenet_warmonger",
            "target_tenet_key": "tenet_warmonger" if warmonger is not None else None,
            "warmonger_core_membership": warmonger,
            "unavailable_reason": None if warmonger is not None else "warmonger_definition_unresolved",
        },
    }
    if leaf is not None:
        member["phase_berserker_validity_inputs_v1"] = leaf
    payload["armies"][0]["knights"]["members"] = [member]
    return payload


def _normalize(payload):
    return normalize_combat_simulation_inputs(
        payload, expected_target_province_id=900, expected_attacker_entry_province_id=800,
        expected_encounter_scope=combat_simulation_encounter_scope(_snapshot(), [12], [22]),
    )


class PhaseBerserkerValidity12003Tests(unittest.TestCase):
    def test_compound_production_inputs_and_actual_stock_ast_three_states(self):
        stock = load_stock_phase_events_12003()
        row = next(row for row in stock.event_rows if row.key == "knight_become_berserker")
        self.assertEqual(row.event_type, "knight")
        occurrence = PhaseWarmongerKnightOccurrence12003(12, 31, 77, 0)
        cases = [
            (True, False, (False, False, False), True, True),
            (False, True, (False, False, False), True, True),
            (False, False, (False, False, False), True, False),
            (True, False, (True, False, False), True, False),
            (None, False, (False, False, False), True, None),
            (True, None, (False, False, False), True, True),
            (True, False, (False, False, None), True, None),
            (None, None, (False, True, False), None, False),
            (None, None, (None, None, None), False, False),
            (True, True, (False, False, False), None, None),
        ]
        baseline = None
        for heritage, germanic, traits, warmonger, expected in cases:
            with self.subTest(heritage=heritage, germanic=germanic, traits=traits, warmonger=warmonger):
                leaf = _remaining(heritage, germanic, traits)
                payload = _payload(leaf, warmonger)
                before = copy.deepcopy(payload)
                normalized = _normalize(payload)
                self.assertEqual(payload, before)
                source = adapt_phase_berserker_validity_inputs_12003(normalized, occurrence=occurrence)
                result = evaluate_berserker_stock_validity_12003(source, stock=stock)
                self.assertIs(result.value, expected)
                self.assertEqual(result.scope, "authored_stock_knight_validity_only")
                self.assertEqual(source.occurrence, occurrence)
                self.assertEqual(normalized["armies"][0]["knights"]["members"][0]["phase_berserker_validity_inputs_v1"], leaf)
                unknown = tuple(path for path, value in source.refs.items() if value is None)
                self.assertEqual(result.unknown_ref_paths, unknown)
                self.assertEqual(set(result.unavailable_reasons), set(unknown))
                if baseline is None:
                    baseline = normalized["completeness"]
                self.assertEqual(normalized["completeness"], baseline)
                self.assertFalse(normalized["completeness"]["monte_carlo_ready"])
        zero = _normalize(_payload(_remaining(True, True, (False, False, False), zero=True), True, zero=True))
        zero_source = adapt_phase_berserker_validity_inputs_12003(zero, occurrence=occurrence)
        self.assertTrue(evaluate_berserker_stock_validity_12003(zero_source, stock=stock).value)
        zero_leaf = zero["armies"][0]["knights"]["members"][0]["phase_berserker_validity_inputs_v1"]
        self.assertEqual(zero_leaf["culture"]["culture_id"], 0)
        self.assertEqual([zero_leaf["religion"][key] for key in ("rite_id", "faith_id", "religion_id")], [0, 0, 0])
        legacy = _normalize(_payload(None, True))
        legacy_source = adapt_phase_berserker_validity_inputs_12003(legacy, occurrence=occurrence)
        self.assertIsNone(evaluate_berserker_stock_validity_12003(legacy_source, stock=stock).value)
        self.assertEqual(len(legacy_source.unavailable_reasons), 5)
        wrong_occurrence = PhaseWarmongerKnightOccurrence12003(12, 31, 77, 1)
        wrong_source = adapt_phase_berserker_validity_inputs_12003(zero, occurrence=wrong_occurrence)
        self.assertIsNone(evaluate_berserker_stock_validity_12003(wrong_source, stock=stock).value)
        mismatch = _payload(_remaining(True, True, (False, False, False)), True)
        mismatch["armies"][0]["knights"]["members"][0]["phase_berserker_validity_inputs_v1"]["source_character_id"] = 78
        with self.assertRaisesRegex(ValueError, "source CharacterID mismatch"):
            _normalize(mismatch)


if __name__ == "__main__":
    unittest.main()
