"""Check challenger decision explanations against the authoritative admission AST.

These are static Clausewitz contracts, not CK3 execution or tooltip screenshots.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
BASE = 'tools/leadership_templates/'
DECISION = BASE + 'common/decisions/lyd_c3_leadership_decisions.txt.in'
TRIGGERS = BASE + 'common/scripted_triggers/lyd_c3_leadership_triggers.txt.in'
sys.path.insert(0, str(REPO / 'tools'))
from extract_auto_upgrade_buildings import Block, parse_clausewitz


def parse(path):
    return parse_clausewitz(path.read_text(encoding='utf-8-sig'))


def block(body, key):
    matches = [entry.value for entry in body.entries if entry.key == key and isinstance(entry.value, Block)]
    if len(matches) != 1:
        raise AssertionError(f'Expected one {key}: {len(matches)}')
    return matches[0]


def visit(body, ancestors=()):
    for entry in body.entries:
        yield entry, ancestors
        if isinstance(entry.value, Block):
            yield from visit(entry.value, ancestors + (entry.key,))


def canonical(body, definitions):
    """Erase display wrappers and inline only the two admission trigger calls.

    Conjunct order is irrelevant; scope/logical wrappers, operators, both branches
    and all their predicates remain. The final hidden guard is checked separately.
    """
    values = []
    for entry in body.entries:
        if entry.key == 'custom_description':
            unlabelled = Block(tuple(item for item in entry.value.entries if item.key != 'text'))
            values.extend(canonical(unlabelled, definitions))
        elif entry.key == 'hidden_trigger':
            continue
        elif entry.key in definitions and entry.value == 'yes':
            values.extend(canonical(definitions[entry.key], definitions))
        elif isinstance(entry.value, Block):
            values.append((entry.key, entry.operator, canonical(entry.value, definitions)))
        else:
            values.append((entry.key, entry.operator, entry.value))
    return tuple(sorted(values, key=repr))


class ChallengerTooltipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proposed = block(parse(ROOT / DECISION), 'lyd_c3_register_challenger_decision')
        triggers = parse(ROOT / TRIGGERS)
        cls.definitions = {key: block(triggers, key) for key in (
            'lyd_c3_native_challenger_admitted_trigger',
            'lyd_c3_native_challenger_eligible_trigger',
        )}

    def test_visible_conditions_preserve_backend_admission_ast(self):
        self.assertEqual(
            canonical(self.definitions['lyd_c3_native_challenger_admitted_trigger'], self.definitions),
            canonical(block(self.proposed, 'is_valid'), self.definitions),
        )

    def test_final_backend_guard_and_nonempty_incumbent_scope_are_preserved(self):
        valid = block(self.proposed, 'is_valid')
        final = valid.entries[-1]
        self.assertEqual(final.key, 'hidden_trigger')
        self.assertEqual(final.value, parse_clausewitz('lyd_c3_native_challenger_admitted_trigger = yes'))
        self.assertEqual(sum(e.key == 'hidden_trigger' for e in valid.entries), 1)
        expected = block(self.definitions['lyd_c3_native_challenger_eligible_trigger'], 'trigger_if')
        actual = block(valid, 'trigger_if')
        self.assertEqual(block(actual, 'limit'), block(expected, 'limit'))
        self.assertEqual(canonical(block(valid, 'trigger_else'), {}), canonical(parse_clausewitz('always = no'), {}))
        for entry, ancestors in visit(valid):
            if entry.key in {'faith.religious_head', 'faith.religious_head_title'} and isinstance(entry.value, Block):
                self.assertIn('trigger_if', ancestors)

    def test_first_headless_hint_and_all_individual_localizations(self):
        valid = block(self.proposed, 'is_valid')
        first = valid.entries[0]
        self.assertEqual(first.key, 'custom_description')
        self.assertEqual(first.value.entries[0].value, 'lyd_c3_challenger_has_head_tt')
        self.assertEqual(first.value.entries[1:], parse_clausewitz('exists = faith.religious_head exists = faith.religious_head_title').entries)
        labels = [entry.value for entry, _ in visit(valid) if entry.key == 'text']
        self.assertEqual(len(set(labels)), 16)
        for language in ('simp_chinese', 'english'):
            path = ROOT / BASE / f'localization/{language}/lyd_c3_leadership_l_{language}.yml.in'
            text = path.read_text(encoding='utf-8-sig')
            lines = dict(re.findall(r'^ (lyd_c3_[A-Za-z0-9_]+):0 "([^"\n]*)"$', text, flags=re.M))
            self.assertTrue(set(labels) <= lines.keys())
            self.assertNotIn('lyd_c3_native_challenger_ready', lines)
            for label in set(labels):
                self.assertTrue(lines[label])
            self.assertIn('原版儒家若仍无宗主' if language == 'simp_chinese' else 'Headless vanilla Confucianism', lines[labels[0]])
            self.assertNotIn('lyd_common_faith', text)
        self.assertNotIn('lyd_common_faith', (ROOT / DECISION).read_text(encoding='utf-8-sig'))

    def test_visibility_and_execution_keep_the_original_guards(self):
        self.assertEqual(block(self.proposed, 'is_shown'), parse_clausewitz(
            'lyd_c3_player_actor_trigger = yes lyd_c3_claim_current_trigger = yes NOT = { has_variable = lyd_c3_claim_title }'))
        self.assertEqual(block(self.proposed, 'effect'), parse_clausewitz(
            'custom_tooltip = lyd_c3_register_challenger_result '
            'hidden_effect = { if = { limit = { lyd_c3_player_actor_trigger = yes } lyd_c3_register_native_claim_effect = yes } }'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
