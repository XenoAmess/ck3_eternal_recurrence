"""Offline regression for actual new phase source and its nonreligious AST."""
from __future__ import annotations

import copy
import json
import unittest

import build_ck3_12002_phase_ast as phase


class NewPhaseAstTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = phase.build()

    def test_actual_source_load_order_and_base_weights(self):
        expected = [("commander_none", 1000), ("commander_wounded", 25),
                    ("commander_maimed", 10), ("commander_killed", 5),
                    ("knight_none", 2000), ("knight_berserker_attack", 30),
                    ("knight_become_berserker", 30), ("knight_shieldmaiden_attack", 30),
                    ("knight_becomes_incapable", 1), ("knight_wounded", 100),
                    ("knight_maimed", 40), ("knight_killed", 30),
                    ("knight_qualify_for_accolade", 5)]
        self.assertEqual([(row["key"], row["base_weight"]) for row in self.payload["event_rows"]], expected)
        self.assertEqual([row["global_load_index"] for row in self.payload["event_rows"]], list(range(13)))
        self.assertEqual(len(self.payload["files"]), 11)

    def test_reproducible_new_ast_hash_and_no_old_identity(self):
        frozen = json.loads(phase.OUTPUT.read_text(encoding="utf-8-sig"))
        self.assertEqual(self.payload, frozen)
        value = copy.deepcopy(frozen)
        value.pop("canonical_ast_sha256")
        self.assertEqual(phase.digest(value), frozen["canonical_ast_sha256"])
        self.assertEqual(frozen["executable_sha256"], phase.SHA)
        self.assertNotIn("91EDCEED", json.dumps(frozen))
        self.assertTrue(frozen["completeness"]["nonreligious_source_ast_migrated"])
        self.assertFalse(frozen["completeness"]["complete_phase_ast_migrated"])

    def test_new_nullable_accolade_operator_preserved_in_actual_source(self):
        row = next(item for item in self.payload["source_definitions"] if item["key"] == "knight_berserker_attack")
        nodes = [item for item in phase.walk(row["source_ast"]) if item.get("key") == "accolade"]
        self.assertEqual([item["operator"] for item in nodes], ["?="])
        calls = []
        self.assertFalse(phase.nullable_scope(None, lambda scope: calls.append(scope)))
        self.assertEqual(calls, [])
        self.assertTrue(phase.nullable_scope(707, lambda scope: calls.append(scope)))
        self.assertEqual(calls, [707])

    def test_cooldown_variable_predicate_and_dead_liege_progress(self):
        names = ["beheaded_warrior", "beheaded_warrior_cooldown"]
        self.assertTrue(phase.evaluate_variable_none(names, {}))
        self.assertFalse(phase.evaluate_variable_none(names, {"beheaded_warrior": 0}))
        self.assertFalse(phase.evaluate_variable_none(names, {"beheaded_warrior_cooldown": False}))
        self.assertEqual(phase.accolade_progress(False, {"accolade_progress": 900_000}), 0)
        self.assertEqual(phase.accolade_progress(True, {"accolade_progress": 900_000}), 900_000)
        row = next(item for item in self.payload["source_definitions"] if item["key"] == "accolade_progress")
        self.assertTrue(any(item.get("key") == "is_alive" and item.get("value") == "yes" for item in phase.walk(row)))

    def test_religion_retained_opaque_and_never_interpreted(self):
        nodes = self.payload["deferred_source_nodes"]
        self.assertTrue(nodes)
        self.assertTrue(any("rite_has_parameter" in item["raw_text"] for item in nodes))
        self.assertTrue(any("spiritual_fulfillment" in item["raw_text"] for item in nodes))
        for item in nodes:
            self.assertEqual(item["domain"], "religion_and_rites")
            self.assertEqual(len(item["raw_sha256"]), 64)
        row = next(item for item in self.payload["event_rows"] if item["key"] == "commander_wounded")
        with self.assertRaises(phase.DeferredDomain):
            phase.evaluate_nonreligious_value(row["chance_ast"], {})

    def test_actual_nonreligious_chance_uses_version_independent_kernel(self):
        row = self.payload["event_rows"][0]
        references = {"root.perks.stalwart_leader": True, "root.is_ai": False,
                      "root.is_acclaimed": True, "root.dynasty.perks.warfare_legacy_3": True,
                      "game_rules.easy_difficulty": False, "game_rules.very_easy_difficulty": False,
                      "root.ai_should_get_extreme_conqueror_bonuses": False}
        self.assertEqual(phase.evaluate_nonreligious_value(row["chance_ast"], references), 280_000_000)
        references["root.is_ai"] = True
        self.assertEqual(phase.evaluate_nonreligious_value(row["chance_ast"], references), 210_000_000)
        wounded = self.payload["event_rows"][1]
        self.assertTrue(phase.evaluate_nonreligious_value(wounded["validity_ast"],
                        {"root.exists": True, "root.traits.wounded.rank_raw": 300_000}))
        self.assertFalse(phase.evaluate_nonreligious_value(wounded["validity_ast"],
                         {"root.exists": True, "root.traits.wounded.rank_raw": 400_000}))

    def test_ordered_repeated_names_and_comments_in_parser(self):
        text = 'has_none_of_variables={name="a#inside" name=b} # outside\naccolade ?= {add_glory=1}'
        result = phase.Parser(text).block()
        entries = result["entries"][0]["value"]["entries"]
        self.assertEqual([item["key"] for item in entries], ["name", "name"])
        self.assertEqual(entries[0]["value"], '"a#inside"')
        self.assertEqual(result["entries"][1]["operator"], "?=")


if __name__ == "__main__":
    unittest.main()
