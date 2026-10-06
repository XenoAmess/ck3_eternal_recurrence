"""One new compound same-query operand -> actual stock chance AST case."""
from __future__ import annotations

import copy
import json
import unittest

from xar_autoplayer.bridge.phase_berserker_chance_contract import CHANCE_TRAIT_KEYS
from xar_autoplayer.simulation.battle_phase_events_12003 import load_stock_phase_events_12003
from xar_autoplayer.simulation.phase_berserker_chance_12003 import (
    adapt_phase_berserker_chance_inputs_12003, evaluate_berserker_stock_chance_12003,
)
from xar_autoplayer.simulation.phase_warmonger_core_12003 import PhaseWarmongerKnightOccurrence12003
# Data constructors only. This case does not run old tests or evaluate Core/validity.
from test_phase_berserker_validity_12003 import _normalize, _payload, _remaining


def _bool(value, reason="fixture_domain_unavailable"):
    return {"status": "available" if value is not None else "unavailable", "value": value,
            "unavailable_reason": None if value is not None else reason}


def _chance(*, ai=True, stalwart=False, warfare=False, acclaimed=False, traits=None, zero=False):
    house, dynasty, accolade = (0, 0, 0) if zero else (0xE1000001, 0xF1000001, 0xC1000001)
    observed_traits = dict.fromkeys(CHANCE_TRAIT_KEYS, False)
    observed_traits.update(traits or {})
    return {
        "source_character_id": 77, "is_ai": _bool(ai),
        "stalwart": {"definition_key": "stalwart_leader_perk", "presence": _bool(stalwart)},
        "dynasty": {"raw_house_id": house, "house_id": house, "raw_dynasty_id": dynasty,
                    "dynasty_id": dynasty, "house_resolution": "resolved", "dynasty_resolution": "resolved",
                    "warfare_legacy_3": {"definition_key": "warfare_legacy_3", "presence": _bool(warfare)}},
        "acclaimed": {"raw_accolade_id": accolade if acclaimed is True else 0xFFFFFFFF,
                      "accolade_id": accolade if acclaimed is True else None,
                      "resolution": "resolved" if acclaimed is True else "absent" if acclaimed is False else "unresolved",
                      "is_acclaimed": _bool(acclaimed)},
        "traits": {key: _bool(value) for key, value in observed_traits.items()},
    }


def _with_chance(leaf, heritage=False):
    # Existing encounter/Core/heritage wrapper is synthetic context, never native leaf credit.
    payload = _payload(_remaining(heritage, False, (False, False, False)), None)
    if leaf is not None:
        payload["armies"][0]["knights"]["members"][0]["phase_berserker_chance_inputs_v1"] = leaf
    return payload


def _known_authored_raw(leaf, heritage):
    """Independent twenty authored source clauses, before the AST's wound folding."""
    traits = {key: value["value"] for key, value in leaf["traits"].items()}
    ai = leaf["is_ai"]["value"]
    stalwart = leaf["stalwart"]["presence"]["value"]
    clauses = [
        (stalwart and not ai, 150000), (stalwart and ai, 115000),
        (leaf["acclaimed"]["is_acclaimed"]["value"], 125000),
        (leaf["dynasty"]["warfare_legacy_3"]["presence"]["value"], 125000),
        (traits["wrathful"], 500000), (traits["giant"], 500000),
        (traits["impatient"], 300000), (traits["sadistic"], 200000),
        (traits["brave"], 200000), (traits["ambitious"], 200000),
        (heritage, 200000), (traits["content"], 50000),
        (traits["compassionate"], 25000), (traits["temperate"], 25000),
        (traits["lazy"], 25000), (traits["patient"], 25000),
        (traits["wounded_1"], 50000), (traits["wounded_2"], 50000),
        (traits["wounded_3"], 25000),
        (any(traits[key] for key in ("one_legged", "disfigured", "one_eyed", "maimed")), 50000),
    ]
    raw = 3000000
    for applies, factor in clauses:
        if applies:
            raw = (raw * factor) // 100000
    return raw


class PhaseBerserkerChance12003Tests(unittest.TestCase):
    def test_compound_production_normalizer_actual_chance_and_unknowns(self):
        stock = load_stock_phase_events_12003()
        row = next(row for row in stock.event_rows if row.key == "knight_become_berserker")
        self.assertEqual(len(row.chance_ast["modifiers"]), 18)
        occurrence = PhaseWarmongerKnightOccurrence12003(12, 31, 77, 0)
        known_cases = [
            ("base", _chance(), False),
            ("heritage", _chance(), True),
            ("player_bonuses", _chance(ai=False, stalwart=True, warfare=True, acclaimed=True,
                 traits={"wrathful": True, "giant": True, "patient": True}), True),
            ("ai_injuries", _chance(stalwart=True, warfare=True, acclaimed=True,
                 traits={"wounded_2": True, "one_legged": True, "disfigured": True}), False),
            ("all_direct_traits", _chance(traits=dict.fromkeys(CHANCE_TRAIT_KEYS[:11], True)), True),
            ("wound1", _chance(traits={"wounded_1": True}), False),
            ("wound2", _chance(traits={"wounded_2": True}), False),
            ("wound3", _chance(traits={"wounded_3": True}), False),
            ("legal_zero", _chance(stalwart=True, warfare=True, acclaimed=True, zero=True), True),
        ]
        evaluations = 0
        baseline = None
        for name, leaf, heritage in known_cases:
            with self.subTest(name=name):
                payload = _with_chance(leaf, heritage)
                before = copy.deepcopy(payload)
                normalized = _normalize(payload)
                source = adapt_phase_berserker_chance_inputs_12003(normalized, occurrence=occurrence)
                result = evaluate_berserker_stock_chance_12003(source, stock=stock)
                evaluations += 1
                expected = _known_authored_raw(leaf, heritage)
                self.assertEqual(result.raw_value, expected)
                self.assertEqual(result.integer_weight, expected // 100000)
                self.assertEqual(result.unknown_dependencies, ())
                self.assertEqual(len(result.operation_trace), 18)
                self.assertEqual(result.scope, "authored_stock_knight_chance_row_value_only")
                self.assertEqual(payload, before)
                self.assertEqual(normalized["armies"][0]["knights"]["members"][0]["phase_berserker_chance_inputs_v1"], leaf)
                baseline = normalized["completeness"] if baseline is None else baseline
                self.assertEqual(normalized["completeness"], baseline)
                self.assertFalse(normalized["completeness"]["monte_carlo_ready"])
                if name == "player_bonuses":
                    self.assertEqual((result.raw_value, result.integer_weight), (87890625, 878))
                if name == "ai_injuries":
                    self.assertEqual((result.raw_value, result.integer_weight), (1347656, 13))
                    self.assertEqual(sum(item["applied"] is True for item in result.operation_trace[-1:]), 1)
                if name == "legal_zero":
                    self.assertEqual(leaf["dynasty"]["house_id"], 0)
                    self.assertEqual(leaf["dynasty"]["dynasty_id"], 0)
                    self.assertEqual(leaf["acclaimed"]["accolade_id"], 0)

        cases = [
            ("irrelevant_ai_unknown", _chance(ai=None, stalwart=False), False, 3000000, None),
            ("maim_or_decisive", _chance(traits={"one_legged": True, "maimed": None}), False, 1500000, None),
            ("unknown_heritage", _chance(), None, None, "root.culture.heritage_north_germanic"),
            ("unknown_wound_rank", _chance(traits={"wounded_1": True, "wounded_3": None}), False, None,
             "derived.become_berserker_wound_factor_raw"),
            ("multiple_wound_rank", _chance(traits={"wounded_1": True, "wounded_2": True}), False, None,
             "derived.become_berserker_wound_factor_raw"),
            ("unknown_direct_trait", _chance(traits={"giant": None}), False, None, "root.traits.giant"),
            ("missing_leaf", None, False, None, "derived.root_player_stalwart"),
        ]
        for name, leaf, heritage, expected, needed in cases:
            with self.subTest(name=name):
                normalized = _normalize(_with_chance(leaf, heritage))
                source = adapt_phase_berserker_chance_inputs_12003(normalized, occurrence=occurrence)
                result = evaluate_berserker_stock_chance_12003(source, stock=stock)
                evaluations += 1
                self.assertEqual(result.raw_value, expected)
                self.assertEqual(result.integer_weight, None if expected is None else expected // 100000)
                self.assertEqual(len(result.operation_trace), 18)
                self.assertEqual(normalized["completeness"], baseline)
                if needed is not None:
                    self.assertIn(needed, result.unknown_dependencies)
                    self.assertIn(needed, result.unavailable_reasons)
                else:
                    self.assertEqual(result.unknown_dependencies, ())
                if name == "multiple_wound_rank":
                    self.assertEqual(result.unavailable_reasons[needed], "wounded_traits_multiple_present")
                if name == "maim_or_decisive":
                    self.assertIn("root.traits.maimed", source.unavailable_reasons)
        wrong = adapt_phase_berserker_chance_inputs_12003(_normalize(_with_chance(_chance())),
            occurrence=PhaseWarmongerKnightOccurrence12003(12, 31, 77, 1))
        self.assertIsNone(evaluate_berserker_stock_chance_12003(wrong, stock=stock).integer_weight)
        evaluations += 1
        mismatch = _with_chance(_chance())
        mismatch["armies"][0]["knights"]["members"][0]["phase_berserker_chance_inputs_v1"]["source_character_id"] = 78
        with self.assertRaisesRegex(ValueError, "source CharacterID mismatch"):
            _normalize(mismatch)
        print(json.dumps({"new_compound_cases": 1, "actual_stock_chance_evaluations": evaluations,
                          "synthetic_context": True, "native_credit": False}))


if __name__ == "__main__":
    unittest.main()
