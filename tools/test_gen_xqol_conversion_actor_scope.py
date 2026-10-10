"""R70 regression: stock actor availability must survive pending projection."""
import unittest
from unittest import mock

import gen_xqol_phase2 as generator
import xqol_conversion_scope_contract as scope_contract
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


if __name__ == "__main__":
    unittest.main()
