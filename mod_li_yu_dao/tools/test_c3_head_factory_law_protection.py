"""Focused AST contract for conditional factory cleanup; no native runtime claim.

The actual R14 B3/B4 law delta motivates this candidate. Cases with a preexisting
law or absent scope are offline guard checks, not fabricated live observations.
"""
from __future__ import annotations
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = ROOT.parent
PARSER = REPOSITORY / 'tools/extract_auto_upgrade_buildings.py'
spec = importlib.util.spec_from_file_location('candidate_law_clausewitz_parser', PARSER)
parser = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = parser
spec.loader.exec_module(parser)
Block = parser.Block
parse_clausewitz = parser.parse_clausewitz
LAW = 'same_faith_succession_law'
SAVED = 'lyd_c3_factory_had_same_faith_law'

def entries(block, key):
    return [e for e in block.entries if e.key == key]

def single(block, key):
    rows = entries(block, key)
    if len(rows) != 1:
        raise AssertionError((key, len(rows)))
    return rows[0].value

def factory_body(text):
    definition = single(parse_clausewitz(text), 'lyd_c3_create_owned_temporal_head_effect')
    return single(definition, 'if')

def fingerprint(value):
    if isinstance(value, Block):
        return [(e.key, e.operator, fingerprint(e.value)) for e in value.entries]
    return value

def should_cleanup(limit, scope_values, present_laws):
    # Interpret only the candidate's exact trigger vocabulary. Missing values
    # raise if read; trigger_if/else must reject absent scope before numeric use.
    branch = single(limit, 'trigger_if')
    presence = single(single(branch, 'limit'), 'exists')
    scope_name = presence.removeprefix('scope:')
    if scope_name in scope_values:
        match = single(branch, 'scope:' + scope_name)
        gate = scope_values[scope_name] == int(match)
    else:
        gate = single(single(limit, 'trigger_else'), 'always') == 'yes'
    law = single(limit, 'has_realm_law')
    return gate and law in present_laws

class FactoryLawProtectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = (ROOT / 'common/scripted_effects/lyd_c3_head_factory.txt').read_text(encoding='utf-8-sig')
        cls.body = factory_body(cls.text)
        cls.capture = entries(cls.body, 'if')[0].value
        cls.cleanup = entries(cls.body, 'if')[1].value
        cls.limit = single(cls.cleanup, 'limit')

    def test_snapshot_is_reset_before_any_native_creation(self):
        body = self.body.entries
        self.assertEqual(body[0].key, 'limit')
        self.assertEqual(body[1].key, 'save_scope_value_as')
        self.assertEqual(single(body[1].value, 'name'), SAVED)
        self.assertEqual(single(body[1].value, 'value'), '1')
        self.assertEqual(body[2].key, 'if')
        self.assertEqual(single(single(self.capture, 'limit'), 'has_realm_law'), LAW)
        capture = single(self.capture, 'save_scope_value_as')
        self.assertEqual(single(capture, 'name'), SAVED)
        self.assertEqual(single(capture, 'value'), '2')
        # An old zero capture is rejected by the positive sentinel contract.
        unsafe = self.text.replace('name = ' + SAVED + ' value = 1', 'name = ' + SAVED + ' value = 0')
        unsafe_body = factory_body(unsafe)
        self.assertNotEqual(single(unsafe_body.entries[1].value, 'value'), '1')
        self.assertLess(2, next(i for i,e in enumerate(body) if e.key == 'create_dynamic_title'))

    def test_only_newly_present_law_is_removed(self):
        self.assertTrue(should_cleanup(self.limit, {SAVED: 1}, {LAW}))
        self.assertFalse(should_cleanup(self.limit, {SAVED: 0}, {LAW}))
        self.assertEqual(single(self.cleanup, 'remove_realm_law'), LAW)
        self.assertEqual([e.key for e in self.cleanup.entries], ['limit', 'remove_realm_law'])

    def test_preexisting_law_is_preserved(self):
        self.assertFalse(should_cleanup(self.limit, {SAVED: 2}, {LAW}))

    def test_law_not_present_after_creation_is_not_removed(self):
        self.assertFalse(should_cleanup(self.limit, {SAVED: 1}, set()))

    def test_absent_snapshot_rejects_without_numeric_read(self):
        self.assertFalse(should_cleanup(self.limit, {}, {LAW}))

    def test_cleanup_occurs_after_temporal_title_law(self):
        body = self.body.entries
        addition = next(i for i,e in enumerate(body) if e.key == 'scope:new_title' and entries(e.value, 'add_title_law'))
        cleanup = next(i for i,e in enumerate(body) if e.value is self.cleanup)
        self.assertGreater(cleanup, addition)
        self.assertLess(cleanup, next(i for i,e in enumerate(body) if e.key == 'set_variable'))

    def test_owner_and_shared_template_ast_match_generated(self):
        for relative in ['tools/leadership_templates/common/scripted_effects/lyd_c3_head_factory.txt.in',
                         'tools/school_consent_templates/common/scripted_effects/lyd_c3_head_factory.txt']:
            text = (ROOT / relative).read_text(encoding='utf-8-sig')
            self.assertEqual(fingerprint(parse_clausewitz(text)), fingerprint(parse_clausewitz(self.text)))

    def test_no_persistent_flag_or_law_list_or_heir_id_replay(self):
        def visit(value):
            if isinstance(value, Block):
                for e in value.entries:
                    yield e
                    yield from visit(e.value)
        all_entries = list(visit(self.body))
        self.assertFalse(any(e.key in {'add_character_flag','remove_character_flag','add_realm_law','add_realm_law_skip_effects','set_player_heir','set_heir'} for e in all_entries))
        self.assertEqual(sum(e.key == 'remove_realm_law' for e in all_entries), 1)
        self.assertEqual([single(e.value, 'name') for e in all_entries if e.key == 'set_variable'],
                         ['lyd_c2_owned_head_title', 'lyd_c2_owner_faith', 'lyd_c3_office_faith'])

    def test_actual_B3_B4_delta_matches_candidate_trigger(self):
        fixture = json.loads((ROOT / 'tools/fixtures/c3_factory_laws/ACTUAL-R14-B3-B4-SAMEFAITH-LAW.json').read_bytes())
        before_rows = fixture['law_list_delta']['before']
        after_rows = fixture['law_list_delta']['after']
        self.assertTrue(all(r['key'] is None for r in before_rows + after_rows))
        before = [r['value'] for r in before_rows]
        after = [r['value'] for r in after_rows]
        self.assertNotIn(LAW, before)
        self.assertIn(LAW, after)
        self.assertEqual(set(after) - set(before), {LAW})
        self.assertEqual(set(before) - set(after), set())
        self.assertTrue(should_cleanup(self.limit, {SAVED: 1}, set(after)))
        self.assertEqual(set(fixture['political_changed_title_hashes']), {'2230','2231','2235','2262','2264'})
        self.assertTrue(all(r['holder_before'] == r['holder_after'] == 31254 and r['before_AST'] != r['after_AST']
                            for r in fixture['political_changed_title_hashes'].values()))

    def test_entire_original_factory_AST_unchanged_after_pruning_new_guard(self):
        original = deepcopy(self.body)
        original = replace(original, entries=[e for e in original.entries
                            if e is not None and e.key != 'save_scope_value_as'
                            and not (e.key == 'if' and (entries(e.value, 'save_scope_value_as') or entries(e.value, 'remove_realm_law')))])
        # Only this declared candidate reordering is normalized back before
        # comparison to the frozen original factory. No effect value may change.
        body = list(original.entries)
        faith_heads = [(i, e) for i, e in enumerate(body)
                       if e.key == 'faith' and entries(e.value, 'set_religious_head_title')]
        holder_scopes = [(i, e) for i, e in enumerate(body)
                         if e.key == 'scope:new_title' and entries(e.value, 'change_title_holder')]
        self.assertEqual(len(faith_heads), 1)
        self.assertEqual(len(holder_scopes), 1)
        fi, faith_entry = faith_heads[0]
        hi, holder_entry = holder_scopes[0]
        self.assertEqual([e.key for e in holder_entry.value.entries], ['change_title_holder'])
        self.assertEqual(hi, fi + 1)
        self.assertEqual(body[fi - 1].key, 'scope:new_title')
        props = body[fi - 1]
        combined = replace(props, value=replace(props.value,
                           entries=[*props.value.entries, *holder_entry.value.entries]))
        body[fi - 1:hi + 1] = [combined]
        ri = next(i for i,e in enumerate(body) if e.key == 'resolve_title_and_vassal_change')
        body.insert(ri + 1, faith_entry)
        original = replace(original, entries=body)
        actual = hashlib.sha256(json.dumps(fingerprint(original), ensure_ascii=True, separators=(',',':')).encode()).hexdigest()
        self.assertEqual(actual, 'd79fad675555e5ed4082f48a16086615e1a5ed5e7e6cd8b0308e201991c8e213')

    def test_missing_scope_fallback_regression_is_detected(self):
        mutant = deepcopy(self.limit)
        fallback = single(single(mutant, 'trigger_else'), 'always')
        self.assertEqual(fallback, 'no')
        # Parse the intentionally unsafe source variant, rather than mutating
        # the frozen parser's immutable Entry/Block tuples.
        self.assertEqual(self.text.count('trigger_else = { always = no }'), 1)
        unsafe_text = self.text.replace('trigger_else = { always = no }', 'trigger_else = { always = yes }')
        mutant_cleanup = entries(factory_body(unsafe_text), 'if')[1].value
        mutant = single(mutant_cleanup, 'limit')
        self.assertTrue(should_cleanup(mutant, {}, {LAW}))

    def test_declared_head_before_holder_ordering_keeps_law_after_resolve(self):
        body = self.body.entries
        fi = next(i for i,e in enumerate(body)
                  if e.key == 'faith' and entries(e.value, 'set_religious_head_title'))
        hi = next(i for i,e in enumerate(body)
                  if e.key == 'scope:new_title' and entries(e.value, 'change_title_holder'))
        ri = next(i for i,e in enumerate(body) if e.key == 'resolve_title_and_vassal_change')
        li = next(i for i,e in enumerate(body)
                  if e.key == 'scope:new_title' and entries(e.value, 'add_title_law'))
        self.assertLess(fi, hi)
        self.assertLess(hi, ri)
        self.assertLess(ri, li)
        props = body[fi - 1]
        self.assertEqual(props.key, 'scope:new_title')
        self.assertEqual([e.key for e in props.value.entries],
            ['set_variable','set_variable','set_destroy_if_invalid_heir',
             'set_no_automatic_claims','set_definitive_form','set_always_follows_primary_heir'])
        self.assertEqual([single(e.value,'name') for e in props.value.entries if e.key == 'set_variable'],
                         ['lyd_c2_owned_head_title','lyd_c2_owner_faith'])
        self.assertEqual(single(body[li].value, 'add_title_law'), 'temporal_head_of_faith_succession_law')

if __name__ == '__main__':
    unittest.main()
