"""Source-only regression for the observed unset ministry entitlement read.

The narrow evaluator intentionally evaluates every AND/OR operand, including
tooltip paths, and rejects undefined title references. It does not model CK3
membership, timing, or engine qualification.
"""
from __future__ import annotations

import itertools
import unittest

from test_reclaim_the_motherland_contract import (
    Block, Entry, MINISTRY_TRIGGER_OVERRIDE, direct_block, parse_clausewitz,
    read_script,
)

ENTITLEMENT = 'global_var:rmtm_ministry_entitlement_title'


def evaluate(block: Block, state: dict[str, bool], scope: str = 'character') -> bool:
    def entry_value(entry: Entry) -> bool:
        key, value = entry.key, entry.value
        if key in {'AND', 'OR', 'NOT'}:
            assert isinstance(value, Block)
            values = [entry_value(child) for child in value.entries]
            return any(values) if key == 'OR' else (not all(values) if key == 'NOT' else all(values))
        if key == 'trigger_if':
            assert isinstance(value, Block)
            limit = direct_block(value, 'limit')
            if not evaluate(limit, state, scope):
                return True
            return evaluate(Block(tuple(child for child in value.entries if child.key != 'limit')), state, scope)
        if key == 'title:h_china':
            assert isinstance(value, Block)
            return evaluate(value, state, 'china_title')
        if key == ENTITLEMENT:
            if not state['entitlement_exists']:
                raise ValueError('undefined entitlement title scope')
            assert isinstance(value, Block)
            return evaluate(value, state, 'entitlement_title')
        if key == 'exists':
            if value == ENTITLEMENT:
                return state['entitlement_exists']
            if value == 'holder' and scope == 'china_title':
                return state['china_holder_exists']
        if key == 'has_title' and value == 'title:h_china':
            return state['owns_china']
        if key == 'primary_title' and value == ENTITLEMENT:
            if not state['entitlement_exists']:
                raise ValueError('undefined entitlement comparison')
            return state['primary_matches_entitlement']
        if key == 'has_variable' and value == 'rmtm_restoration_hegemony' and scope == 'entitlement_title':
            return state['entitlement_marked']
        if key == 'government_has_flag':
            return state[str(value)]
        raise ValueError(f'unsupported regression trigger: {key} {entry.operator} {value!r}')

    return all([entry_value(entry) for entry in block.entries])


class TestReclaimMinistryScopeGuard(unittest.TestCase):
    def test_missing_entitlement_rejects_access_without_an_undefined_read(self) -> None:
        _, script = read_script(MINISTRY_TRIGGER_OVERRIDE)
        access = direct_block(script, 'tgp_has_access_to_ministry_trigger')
        for china_holder in (False, True):
            state = dict(owns_china=False, china_holder_exists=china_holder,
                         entitlement_exists=False, primary_matches_entitlement=False,
                         entitlement_marked=False, government_is_celestial=True,
                         government_uses_ministry_budget=True)
            with self.subTest(china_holder=china_holder):
                self.assertFalse(evaluate(access, state))

    def test_native_and_later_access_keep_all_original_permissions(self) -> None:
        _, script = read_script(MINISTRY_TRIGGER_OVERRIDE)
        access = direct_block(script, 'tgp_has_access_to_ministry_trigger')
        keys = ('owns_china', 'china_holder_exists', 'entitlement_exists',
                'primary_matches_entitlement', 'entitlement_marked',
                'government_is_celestial', 'government_uses_ministry_budget')
        for values in itertools.product((False, True), repeat=len(keys)):
            state = dict(zip(keys, values))
            expected = (state['owns_china'] or (
                not state['china_holder_exists'] and state['entitlement_exists']
                and state['primary_matches_entitlement'] and state['entitlement_marked']
            )) and state['government_is_celestial'] and state['government_uses_ministry_budget']
            with self.subTest(state=state):
                self.assertEqual(evaluate(access, state), expected)

    def test_original_eager_tooltip_shape_reproduces_missing_scope_counterexample(self) -> None:
        unsafe = parse_clausewitz('''AND = {
            exists = global_var:rmtm_ministry_entitlement_title
            primary_title = global_var:rmtm_ministry_entitlement_title
        }''')
        state = dict(entitlement_exists=False, primary_matches_entitlement=False)
        with self.assertRaisesRegex(ValueError, 'undefined entitlement comparison'):
            evaluate(unsafe, state)


if __name__ == '__main__':
    unittest.main()
