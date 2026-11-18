"""R70 regression: stock actor availability must survive pending projection."""
import unittest
import re
from unittest import mock

import gen_xqol_phase2 as generator
import xqol_conversion_scope_contract as scope_contract
import xqol_vanilla_contract as vanilla_contract
import prepare_xqol_1_20_fixture as core_fixture
from xqol_conversion_scope_contract import pending_conversion_scope_errors
from xqol_vanilla_contract import GAME, block, native_definition


def contract_fixture(relative, key):
    # Minimal scope contract for CI without installed CK3. Real stock is checked
    # separately below; acceptance weights are outside this regression.
    return key + " = {\n" + "\n".join((
        "\tis_shown = {\n\t\tscope:recipient = { is_ai = yes }\n\t}",
        "\tis_available = {\n\t\ttrigger_if = {\n\t\t\tlimit = { is_ai = yes }\n\t\t\tis_adult = yes\n\t\t}\n\t}",
        "\tis_valid_showing_failures_only = {\n\t\tvalid_demand_conversion_conditions_trigger = yes\n\t}",
    )) + "\n}"


class ConversionActorScopeTests(unittest.TestCase):
    read_definition = staticmethod(contract_fixture)

    @classmethod
    def setUpClass(cls):
        cls.enterClassContext(mock.patch.object(generator, "native_definition", side_effect=cls.read_definition))
        cls.enterClassContext(mock.patch.object(scope_contract, "native_definition", side_effect=cls.read_definition))
        cls.enterClassContext(mock.patch.object(generator, "native_conversion_acceptance", return_value="\t\tbase = 0"))
        cls.private = {
            kind: generator.render_conversion_interaction(kind, 2, 5)
            for kind in ("courtier", "ruler")
        }

    def test_real_generated_courtier_and_ruler_preserve_stock_scope(self):
        for kind, private in self.private.items():
            with self.subTest(kind=kind):
                self.assertEqual([], pending_conversion_scope_errors(private, kind))

    def test_original_none_root_and_wrong_named_scopes_are_rejected(self):
        for kind, private in self.private.items():
            # Extract the real emitted actor block after removing only the
            # separate original one-line human guard, not a copied renderer.
            body = block(private, "is_valid", indentation="\t")
            available = block(
                body.replace("\t\tscope:actor = { xqol_human_ruler_trigger = yes }", "", 1),
                "scope:actor", indentation="\t\t",
            )
            stock = self.read_definition(
                "common/character_interactions/00_religious_interactions.txt",
                {"courtier": "ask_for_conversion_courtier_interaction",
                 "ruler": "demand_conversion_vassal_ruler_interaction"}[kind],
            )
            stock_field = block(stock, "is_available", indentation="\t")
            bare = "\n".join(stock_field.splitlines()[1:-1])
            variants = {
                "original_none_root": bare,
                "recipient": available.replace("scope:actor", "scope:recipient", 1),
                "puppet_or_actor": available.replace("scope:actor", "scope:puppet_or_actor", 1),
            }
            for name, replacement in variants.items():
                with self.subTest(kind=kind, mutation=name):
                    mutated = private.replace(available, replacement, 1)
                    self.assertNotEqual(private, mutated)
                    self.assertTrue(pending_conversion_scope_errors(mutated, kind))

    def test_other_stock_field_omission_and_pending_recursion_are_rejected(self):
        for kind, private in self.private.items():
            with self.subTest(kind=kind, mutation="missing_stock_validity"):
                mutated = private.replace("valid_demand_conversion_conditions_trigger = yes", "always = yes", 1)
                self.assertTrue(pending_conversion_scope_errors(mutated, kind))
            with self.subTest(kind=kind, mutation="pending_recursion"):
                mutated = private.replace("is_valid = {", "is_valid = {\n\t\tis_character_interaction_valid = { interaction = ask_for_conversion_courtier_interaction recipient = scope:recipient }", 1)
                self.assertTrue(pending_conversion_scope_errors(mutated, kind))


@unittest.skipUnless((GAME / "common/character_interactions/00_religious_interactions.txt").is_file(),
                     "Current-stock regression requires the exact installed CK3 source")
class CurrentStockConversionActorScopeTests(ConversionActorScopeTests):
    read_definition = staticmethod(native_definition)


class FlorinGoldenObligationTests(unittest.TestCase):
    quote = '''golden_obligation_value = {
    value = minor_gold_value
    if = {
        limit = {
            trigger_if = {
                limit = { exists = scope:puppet_or_actor }
                scope:puppet_or_actor ?= { has_strong_hook = prev }
            }
            trigger_else = { scope:actor ?= { has_strong_hook = prev } }
        }
        multiply = 1.5
    }
}'''
    payment = '''golden_obligation_value_check_current_situation = {
    add = gold
    floor = yes
    max = golden_obligation_value
}'''

    def definition(self, relative: str, key: str) -> str:
        self.assertEqual("common/script_values/00_interaction_values.txt", relative)
        return {"golden_obligation_value": self.quote,
                "golden_obligation_value_check_current_situation": self.payment}[key]

    def test_real_generator_accepts_uncapped_florin_quote_and_keeps_strong_hook_actor(self) -> None:
        with (mock.patch.object(vanilla_contract, "native_definition", side_effect=self.definition),
              mock.patch.object(generator, "require_sources"),
              mock.patch.object(generator, "render_release_interactions", return_value="")):
            emitted = generator.generated_payloads()["common/script_values/xqol_generated_payment_values.txt"]
        self.assertIn("xqol_full_golden_obligation_value = {", emitted)
        self.assertIn("scope:puppet_or_actor ?= { has_strong_hook = prev }", emitted)
        self.assertIn("scope:actor ?= { has_strong_hook = prev }", emitted)
        self.assertIn("multiply = 1.5", emitted)
        self.assertNotIn("floor = yes", emitted)
        self.assertNotIn("max = gold", emitted)

    def test_wallet_capped_quote_and_changed_payment_path_are_rejected(self) -> None:
        for name, quote, payment in (
            ("old_cap_reappears", self.quote[:-1] + "\nmax = gold\n}", self.payment),
            ("wrong_payment_cap", self.quote, self.payment.replace("max = golden_obligation_value", "max = 10")),
            ("lost_integer_floor", self.quote, self.payment.replace("floor = yes", "floor = no")),
        ):
            with self.subTest(name=name):
                values = {"golden_obligation_value": quote,
                          "golden_obligation_value_check_current_situation": payment}
                with mock.patch.object(vanilla_contract, "native_definition", side_effect=lambda _relative, key: values[key]):
                    with self.assertRaisesRegex(ValueError, "quote/payment split changed"):
                        vanilla_contract.native_full_golden_obligation()


class CoreConversionEntryTests(unittest.TestCase):
    def test_both_actual_core_dispatch_entries_initialize_the_consumed_draft(self) -> None:
        consumer = generator.render_conversion_dispatch()
        variable = re.search(r"trigger\s*=\s*var:(\w+)", consumer)
        self.assertIsNotNone(variable)
        if variable is None:
            self.fail("Generated dispatcher must have one explicit variable input")
        producer = core_fixture.events(False)
        initialized = re.findall(
            r"set_variable\s*=\s*\{\s*name\s*=\s*(\w+)\s+value\s*=\s*50\s*\}"
            r"\s*xqol_bulk_conversion_dispatch_effect\s*=\s*yes", producer,
        )
        self.assertEqual([variable.group(1)] * 2, initialized)


if __name__ == "__main__":
    unittest.main()
