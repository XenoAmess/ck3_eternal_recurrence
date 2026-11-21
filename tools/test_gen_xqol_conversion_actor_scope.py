"""R70 regression: stock actor availability must survive pending projection."""
import unittest
import copy
import tempfile
import re
from pathlib import Path
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
        product = Path(__file__).resolve().parents[1] / "mod_xenoamess_quality_of_life"
        actual_save = (product / "events/xqol_events.txt").read_text(encoding="utf-8-sig")
        saved_field = re.search(
            r"set_variable\s*=\s*\{\s*name\s*=\s*(\w+)\s+value\s*=\s*var:(\w+)\s*\}"
            r"\s*xqol_bulk_conversion_dispatch_effect\s*=\s*yes", actual_save,
        )
        self.assertIsNotNone(saved_field)
        if saved_field is None:
            self.fail("Production Save must commit the draft before dispatch")
        self.assertEqual(variable.group(1), saved_field.group(2))
        initialized = re.findall(
            r"set_variable\s*=\s*\{\s*name\s*=\s*(\w+)\s+value\s*=\s*50\s*\}"
            r"\s*set_variable\s*=\s*\{\s*name\s*=\s*(\w+)\s+value\s*=\s*var:(\w+)\s*\}"
            r"\s*xqol_bulk_conversion_dispatch_effect\s*=\s*yes"
            r"\s*remove_variable\s*=\s*(\w+)", producer,
        )
        draft = variable.group(1)
        self.assertEqual([(draft, saved_field.group(1), draft, draft)] * 2, initialized)
        original_assertion = (Path(__file__).parent / "fixtures/xqol_acceptance/common/scripted_effects/zqa_phase2_interaction_effects.txt").read_text(encoding="utf-8-sig")
        self.assertIn(f"var:{saved_field.group(1)} = 50", original_assertion)


@unittest.skipUnless((GAME / "common/governments/00_government_types.txt").is_file(),
                     "Current-government input qualification requires actual installed source")
class CurrentGovernmentInputTests(unittest.TestCase):
    governments = ("administrative_government", "meritocratic_government", "celestial_government")
    relative = "common/governments/00_government_types.txt"

    def test_current_source_gate_accepts_actual_input_and_rejects_wrong_government_pin(self) -> None:
        self.assertEqual([], vanilla_contract.source_errors(GAME))
        changed = copy.deepcopy(vanilla_contract.CONTRACT)
        changed["files"][self.relative] = "0" * 64
        with mock.patch.object(vanilla_contract, "CONTRACT", changed):
            self.assertEqual(["XQOL exact-build source SHA-256 changed: " + self.relative],
                             vanilla_contract.source_errors(GAME))

    def test_supported_government_lookup_refuses_missing_and_duplicate_definitions(self) -> None:
        for government in self.governments:
            actual = vanilla_contract.native_definition(self.relative, government)
            self.assertEqual(1, actual.count("mechanic_type = administrative"))
            with tempfile.TemporaryDirectory(prefix="xqol-current-government-") as temporary:
                path = Path(temporary) / self.relative
                path.parent.mkdir(parents=True)
                for body in ("", actual + "\n" + actual):
                    path.write_text(body, encoding="utf-8")
                    with mock.patch.object(vanilla_contract, "GAME", Path(temporary)):
                        with self.assertRaisesRegex(ValueError, "expected one"):
                            vanilla_contract.native_definition(self.relative, government)

    def test_actual_script_validator_rejects_each_supported_government_losing_admin_mechanic(self) -> None:
        import validate_xenoamess_quality_of_life as validator
        read = vanilla_contract.native_definition
        for government in self.governments:
            def mutated(relative: str, key: str) -> str:
                definition = read(relative, key)
                return (definition.replace("mechanic_type = administrative", "mechanic_type = feudal", 1)
                        if relative == self.relative and key == government else definition)
            errors: list[str] = []
            with mock.patch.object(vanilla_contract, "native_definition", side_effect=mutated):
                validator.check_scripts(errors)
            self.assertIn("supported government no longer uses the administrative mechanic: " + government,
                          errors)


class SavedEntryBridgeTests(unittest.TestCase):
    """Saved startup reachability/once guards; no Native or engine qualification."""

    @staticmethod
    def payload_digest(payloads: dict[str, bytes]) -> str:
        import hashlib
        digest = hashlib.sha256()
        for relative, raw in sorted(payloads.items()):
            digest.update(relative.encode() + b"\0" + raw + b"\0")
        return digest.hexdigest()

    @staticmethod
    def one(block, key):
        import extract_auto_upgrade_buildings as parser
        matches = [entry.value for entry in block.entries if entry.key == key]
        if len(matches) != 1 or not isinstance(matches[0], parser.Block):
            raise AssertionError("one actual block required: " + key)
        return matches[0]

    @classmethod
    def guard_accepts(cls, block, *, actor="1128", alive=True, ai=False,
                      date="1066.9.15", flags=frozenset()):
        # A deliberately bounded test interpreter for the emitted guard AST,
        # not a runtime substitute for CK3 trigger evaluation.
        for entry in block.entries:
            if entry.key == "NOT":
                if cls.guard_accepts(entry.value, actor=actor, alive=alive,
                                     ai=ai, date=date, flags=flags):
                    return False
            elif entry.key == "has_character_flag":
                if entry.value not in flags:
                    return False
            elif entry.key == "this":
                if entry.value != "character:" + actor:
                    return False
            elif entry.key == "is_ai":
                if entry.value != ("yes" if ai else "no"):
                    return False
            elif entry.key == "is_alive":
                if entry.value != ("yes" if alive else "no"):
                    return False
            elif entry.key == "current_date":
                if entry.value != date:
                    return False
            else:
                raise AssertionError("unreviewed fixture guard: " + entry.key)
        return True

    def test_default_whole_fixture_outputs_remain_byte_exact(self) -> None:
        import prepare_xqol_ui_fixture as ui
        repo = Path(core_fixture.prep.__file__).resolve().parents[1]
        expected = {
            "celestial": "8203a7cb0beccd9bc71025633badac574b6661f5c44f0774e6be6106ab592d32",
            "administrative": "fb4e12ad6275a038082358f7167f8919b049e6b4c35d20e8bbebce6a71f6ceab",
        }
        for scenario, digest in expected.items():
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as temporary:
                output = Path(temporary) / "fixture"
                with mock.patch.object(core_fixture.prep, "engine_identity", return_value={}):
                    core_fixture.prepare(repo, output, scenario)
                payloads = {p.relative_to(output).as_posix(): p.read_bytes()
                            for p in output.rglob("*") if p.is_file()}
                self.assertEqual(digest, self.payload_digest(payloads))
        self.assertEqual("97242450fe9a467e2ac557e290788f9253f5f1902edaaf9bbaf0c10cc0b7223e",
                         self.payload_digest({n: s.encode("utf-8-sig") for n, s in ui.project().items()}))

    def test_saved_entry_has_a_registered_dynamic_state_and_actual_player_root(self) -> None:
        import extract_auto_upgrade_buildings as parser
        import prepare_xqol_ui_fixture as ui
        for files, prefix in ((core_fixture.saved_entry_files(), "zqa120"),
                              (ui.project(saved_entry_bridge=True), "zqauitail")):
            with self.subTest(prefix=prefix):
                window = files[f"gui/{prefix}_saved_entry_bridge.gui"]
                widget = files[f"gui/scripted_widgets/{prefix}_saved_entry_widgets.txt"]
                self.assertEqual(f"gui/{prefix}_saved_entry_bridge.gui = {prefix}_saved_entry_bridge_window\n", widget)
                self.assertIn(f'name = "{prefix}_saved_entry_bridge_window"', window)
                for callback in ("IsShown", "Execute"):
                    self.assertIn(f"GetScriptedGui('{prefix}_saved_entry_gui').{callback}( GuiScope.SetRoot( GetPlayer.MakeScope ).End )", window)
                self.assertIn("trigger_when =", window)
                self.assertIn("on_start =", window)
                self.assertIn('visible = "[GetPlayer.IsValid]"', window)
                self.assertIn("alwaystransparent = yes", window)
                for relative, text in files.items():
                    if relative.endswith((".gui", ".txt")):
                        parser.parse_clausewitz(text)

    def test_both_guards_reject_wrong_owner_date_and_previously_initialized_saves(self) -> None:
        import extract_auto_upgrade_buildings as parser
        import prepare_xqol_ui_fixture as ui
        for files, prefix in ((core_fixture.saved_entry_files(), "zqa120"),
                              (ui.project(saved_entry_bridge=True), "zqauitail")):
            text = files[f"common/scripted_guis/{prefix}_saved_entry_guis.txt"]
            root = self.one(parser.parse_clausewitz(text), prefix + "_saved_entry_gui")
            shown = self.one(root, "is_shown")
            limited = self.one(self.one(self.one(root, "effect"), "if"), "limit")
            self.assertEqual(shown, limited)
            self.assertTrue(self.guard_accepts(shown))
            for changes in ({"actor": "han_8052"}, {"ai": True}, {"alive": False},
                            {"date": "1066.9.16"},
                            {"flags": {prefix + "_saved_entry_dispatched"}},
                            {"flags": {"zqa_fixture_initialized"}}):
                with self.subTest(prefix=prefix, changes=changes):
                    self.assertFalse(self.guard_accepts(shown, **changes))
                    self.assertFalse(self.guard_accepts(limited, **changes))

    def test_core_spends_fixture_once_flag_before_original_delayed_event(self) -> None:
        import extract_auto_upgrade_buildings as parser
        files = core_fixture.saved_entry_files()
        root = self.one(parser.parse_clausewitz(files['common/scripted_guis/zqa120_saved_entry_guis.txt']), 'zqa120_saved_entry_gui')
        effect = self.one(self.one(root, "effect"), "if")
        keys = [entry.key for entry in effect.entries]
        self.assertLess(keys.index("add_character_flag"), keys.index("trigger_event"))
        self.assertEqual("zqa120_saved_entry_dispatched", effect.entries[1].value)
        event = self.one(effect, "trigger_event")
        self.assertEqual({"id": "zqa120.1", "days": "1"},
                         {entry.key: entry.value for entry in event.entries})
        self.assertFalse(any(entry.key in {"set_variable", "start_war", "end_war"}
                             for entry in effect.entries))

    def test_ui_bridge_preserves_original_preparation_body_and_has_no_parallel_hook(self) -> None:
        import extract_auto_upgrade_buildings as parser
        import prepare_xqol_ui_fixture as ui
        original = ui.project()['common/on_action/zqauitail_on_actions.txt']
        player = core_fixture.prep.balanced_excerpt(original, r"^        random_player\s*=\s*\{")
        expected = self.one(parser.parse_clausewitz(player), "random_player")
        files = ui.project(saved_entry_bridge=True)
        root = self.one(parser.parse_clausewitz(files['common/scripted_guis/zqauitail_saved_entry_guis.txt']), 'zqauitail_saved_entry_gui')
        effect = self.one(self.one(root, "effect"), "if")
        self.assertEqual(expected.entries, effect.entries[3:])
        self.assertEqual("add_character_flag", effect.entries[1].key)
        self.assertNotIn("on_game_start_after_lobby", files['common/on_action/zqauitail_on_actions.txt'])
        self.assertEqual(ui.project()['descriptor.mod'], files['descriptor.mod'])

    def test_actual_saved_core_projection_changes_only_startup_and_adds_three_files(self) -> None:
        repo = Path(core_fixture.prep.__file__).resolve().parents[1]
        for scenario in ("celestial", "administrative"):
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as temporary:
                original, saved = Path(temporary) / "original", Path(temporary) / "saved"
                with mock.patch.object(core_fixture.prep, "engine_identity", return_value={}):
                    old = core_fixture.prepare(repo, original, scenario)
                    new = core_fixture.prepare(repo, saved, scenario, saved_entry_bridge=True)
                before = {p.relative_to(original).as_posix(): p.read_bytes() for p in original.rglob("*") if p.is_file()}
                after = {p.relative_to(saved).as_posix(): p.read_bytes() for p in saved.rglob("*") if p.is_file()}
                self.assertEqual(set(core_fixture.saved_entry_files()), after.keys() - before.keys())
                self.assertEqual(["common/on_action/zqa120_on_actions.txt"],
                                 [name for name in before if before[name] != after[name]])
                self.assertNotIn("on_game_start_after_lobby", after['common/on_action/zqa120_on_actions.txt'].decode('utf-8-sig'))
                self.assertEqual(old['required_markers'], new['required_markers'])
                self.assertEqual(60, new['max_game_days'])
                self.assertEqual("NOT_RUN", new['startup_observed'])
                self.assertIn("Saved Robert1128 at1066-09-15", new['bookmark'])
                self.assertFalse(new['native_abi_loaded'])
                self.assertFalse(new['gui_callbacks_mounted'])


if __name__ == "__main__":
    unittest.main()
