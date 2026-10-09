#!/usr/bin/env python3
"""Offline regression for actual TED interaction display failures; no CK3."""
from __future__ import annotations

import copy
from pathlib import Path
import unittest

import validate_tributary_expansion_directives_static as gate


ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "mod_tributary_expansion_directives"
SECONDARY = "recipient_secondary_ted_issue_expansion_directive_interaction"


class TributaryExpansionDisplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.interaction = (MOD / gate.SCRIPT_PATHS[1]).read_text(encoding="utf-8-sig")
        cls.localized = {
            language: gate.loc_entries(
                (MOD / f"localization/{language}/ted_tributary_expansion_l_{language}.yml").read_text(
                    encoding="utf-8-sig"
                )
            )
            for language in gate.LANGUAGES
        }

    def test_actual_production_display_data_has_nine_complete_languages(self):
        self.assertEqual(len(self.localized), 9)
        self.assertEqual(gate.interaction_localization_errors(self.interaction, self.localized), [])

    def test_original_r21_failures_are_rejected_together(self):
        broken = self.interaction.replace(
            "\tlocalization_values = {\n\t\tTED_WAR_SUBSIDY = ted_war_subsidy_value\n\t}\n\n", ""
        )
        self.assertNotEqual(broken, self.interaction)
        localized = copy.deepcopy(self.localized)
        for entries in localized.values():
            entries.pop(SECONDARY)
            entries["ted_offer_war_subsidy_option"] = entries["ted_offer_war_subsidy_option"].replace(
                "$TED_WAR_SUBSIDY|0$", "[SCOPE.ScriptValue('ted_war_subsidy_value')|0]"
            )
        errors = gate.interaction_localization_errors(broken, localized)
        self.assertTrue(any("not bound" in error for error in errors))
        self.assertTrue(any("display token" in error for error in errors))
        self.assertTrue(any("secondary-recipient label" in error for error in errors))

    def test_a_single_missing_blank_or_raw_secondary_label_is_rejected(self):
        for language, invalid in (("german", None), ("simp_chinese", " "), ("english", SECONDARY)):
            with self.subTest(language=language):
                localized = copy.deepcopy(self.localized)
                if invalid is None:
                    localized[language].pop(SECONDARY)
                else:
                    localized[language][SECONDARY] = invalid
                errors = gate.interaction_localization_errors(self.interaction, localized)
                self.assertEqual(len(errors), 1)
                self.assertIn(language, errors[0])

    def test_miswired_or_non_numeric_subsidy_display_is_rejected(self):
        wrong_value = self.interaction.replace(
            "TED_WAR_SUBSIDY = ted_war_subsidy_value", "TED_WAR_SUBSIDY = 50"
        )
        self.assertTrue(gate.interaction_localization_errors(wrong_value, self.localized))
        for invalid in ("[gold_i]", "[gold_i]$WRONG_VALUE|0$", "[gold_i]$TED_WAR_SUBSIDY|0$" * 2):
            with self.subTest(invalid=invalid):
                localized = copy.deepcopy(self.localized)
                localized["english"]["ted_offer_war_subsidy_option"] = invalid
                errors = gate.interaction_localization_errors(self.interaction, localized)
                self.assertEqual(len(errors), 1)
                self.assertIn("display token", errors[0])


if __name__ == "__main__":
    unittest.main()
