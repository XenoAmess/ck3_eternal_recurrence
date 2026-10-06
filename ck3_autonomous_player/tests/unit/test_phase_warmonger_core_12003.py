"""FIRST focused full V2 normalizer -> exact knight occurrence consumer case."""
from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.combat_contract import (
    combat_simulation_encounter_scope, normalize_combat_simulation_inputs,
)
from xar_autoplayer.bridge.phase_warmonger_core_contract import PHASE_WARMONGER_CORE_LEAF
from xar_autoplayer.simulation.phase_warmonger_core_12003 import (
    PhaseWarmongerKnightOccurrence12003, adapt_phase_warmonger_core_12003,
)
# Import fixture constructors only; no previous unittest method runs.
from test_combat_simulation_inputs_contract import _combat_inputs, _snapshot


def _leaf(rite_id: int, membership: bool | None, *, reason: str | None = None,
          resolution: str = "adopted", target: str | None = "tenet_warmonger") -> dict[str, object]:
    return {
        "status": "available" if reason is None else "unavailable",
        "source_character_id": 77,
        "raw_adopted_rite_id": rite_id,
        "rite_id": rite_id if resolution == "adopted" else None,
        "rite_resolution": resolution,
        "requested_tenet_key": "tenet_warmonger",
        "target_tenet_key": target,
        "warmonger_core_membership": membership,
        "unavailable_reason": reason,
    }


def _payload(leaf: dict[str, object] | None, *, army_index: int = 0) -> dict[str, object]:
    payload = _combat_inputs()
    army = payload["armies"][army_index]
    member = {
        "eligible": True, "character_id": 77,
        "source_regiment_id": army["regiments"][0]["regiment_id"],
        "army_id": army["native_carmy_id"], "participant_army_membership_verified": True,
        "prowess": 2, "knight_effectiveness_raw": 185_000,
        "effective_damage_raw": 18_500_000, "effective_toughness_raw": 3_700_000,
        "scale": 100_000,
        "phase_rite_parameters_v1": {
            "status": "available", "source_character_id": 77,
            "raw_adopted_rite_id": 123, "rite_id": 123, "faith_id": 901,
            "boolean_parameters_complete": True, "boolean_parameter_keys": ["warmonger"],
            "unavailable_reason": None,
        },
    }
    if leaf is not None:
        member[PHASE_WARMONGER_CORE_LEAF] = leaf
    army["knights"]["members"] = [member]
    return payload


def _normalize(payload: dict[str, object]) -> dict[str, object]:
    return normalize_combat_simulation_inputs(
        payload, expected_target_province_id=900, expected_attacker_entry_province_id=800,
        expected_encounter_scope=combat_simulation_encounter_scope(_snapshot(), [12], [22]),
    )


class PhaseWarmongerCore12003Tests(unittest.TestCase):
    def test_compound_production_normalizer_and_exact_knight_occurrence(self) -> None:
        cases = [
            (_leaf(0xF1000001, True), True, None),
            (_leaf(0xF1000001, False), False, None),
            (_leaf(0, False), False, None),
            (_leaf(0xFFFFFFFF, None, reason="native_fallback_core_membership_unobserved",
                   resolution="native_fallback", target=None), None,
             "native_fallback_core_membership_unobserved"),
            (_leaf(0, None, reason="warmonger_definition_unresolved", target=None), None,
             "warmonger_definition_unresolved"),
            (_leaf(0, None, reason="tenet_definition_key_unavailable", target=None), None,
             "tenet_definition_key_unavailable"),
            (_leaf(0, None, reason="core_tenet_collection_unavailable"), None,
             "core_tenet_collection_unavailable"),
            (None, None, "phase_warmonger_leaf_not_published"),
        ]
        baseline_completeness = _normalize(_payload(None))["completeness"]
        occurrence = PhaseWarmongerKnightOccurrence12003(12, 31, 77, 0)
        for leaf, expected, reason in cases:
            with self.subTest(reason=reason, value=expected):
                payload = _payload(leaf)
                before = copy.deepcopy(payload)
                normalized = _normalize(payload)
                self.assertEqual(payload, before)
                source = adapt_phase_warmonger_core_12003(normalized, occurrence=occurrence)
                self.assertIs(source.value, expected)
                self.assertEqual(source.unavailable_reason, reason)
                self.assertEqual(source.occurrence, occurrence)
                self.assertEqual(source.leaf, leaf)
                self.assertEqual(normalized["completeness"], baseline_completeness)
                self.assertFalse(normalized["completeness"]["monte_carlo_ready"])
                if expected is None:
                    with self.assertRaises(ValueError):
                        source.require_boolean()
                else:
                    self.assertIs(source.require_boolean(), expected)
        # The same Character in a separate valid query is a different source
        # occurrence. Existing V2 rejects duplicate knight identities per query.
        other = _normalize(_payload(_leaf(0, False), army_index=1))
        other_occurrence = PhaseWarmongerKnightOccurrence12003(22, 32, 77, 0)
        self.assertFalse(adapt_phase_warmonger_core_12003(other, occurrence=other_occurrence).require_boolean())
        for wrong in (PhaseWarmongerKnightOccurrence12003(12, 32, 77, 0),
                      PhaseWarmongerKnightOccurrence12003(12, 31, 77, 1),
                      PhaseWarmongerKnightOccurrence12003(22, 32, 78, 0)):
            source = adapt_phase_warmonger_core_12003(other, occurrence=wrong)
            self.assertIsNone(source.value)
            self.assertEqual(source.unavailable_reason, "phase_knight_occurrence_unobserved")
        malformed = _payload(_leaf(0, True))
        malformed["armies"][0]["knights"]["members"][0][PHASE_WARMONGER_CORE_LEAF]["source_character_id"] = 78
        with self.assertRaisesRegex(ValueError, "source CharacterID mismatch"):
            _normalize(malformed)


if __name__ == "__main__":
    unittest.main()
