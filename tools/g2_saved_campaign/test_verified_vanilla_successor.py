"""Synthetic queue transport only; no real death, SAVE or Game operation."""
import copy
import unittest

from tools.g2_saved_campaign.m7_ordinary_successor_queue import ordinary_no_pact_lifecycle
from tools.g2_saved_campaign.m7_ordinary_successor_async_queue import AsyncOrdinarySuccessorQueue
from tools.g2_saved_campaign.test_m7_async_successor_adoption import _AdoptedQueue, _adopt_completed
from tools.g2_saved_campaign.test_m7_async_successor_persistence import completed_continuation_fixture


def vanilla_fixture():
    fixture = completed_continuation_fixture()
    binding = copy.deepcopy(fixture['source_snapshot']['succession_lifecycle'])
    binding.update(xar_enabled=None, pact_contract='absent_by_verified_xar_mod_not_loaded',
                   source='absent_by_verified_xar_mod_not_loaded')
    fixture['source_snapshot']['succession_lifecycle'] = copy.deepcopy(binding)
    fixture['successor_snapshot']['succession_lifecycle'] = copy.deepcopy(binding)
    fixture['turn']['result']['succession_lifecycle'] = copy.deepcopy(binding)
    return fixture


class VerifiedVanillaSuccessorTests(unittest.IsolatedAsyncioTestCase):
    async def test_completed_original_handoff_keeps_same_owner_and_saves_once(self):
        fixture = vanilla_fixture()
        self.assertEqual(fixture['source_snapshot']['revision'], 6)
        self.assertEqual(fixture['source_snapshot']['native_revision'], 42)
        queue = _AdoptedQueue(fixture)
        transitions = []
        result = await _adopt_completed(AsyncOrdinarySuccessorQueue(queue), fixture, transitions)
        self.assertEqual(result['status'], 'saved')
        self.assertEqual(len(transitions), 1)
        self.assertIsNone(result['transition']['succession_lifecycle']['xar_enabled'])
        self.assertEqual(result['transition']['succession_lifecycle'],
                         fixture['source_snapshot']['succession_lifecycle'])
        tools = [call[0] for call in queue.calls]
        self.assertEqual(tools.count('ck3_save_checkpoint'), 1)
        self.assertNotIn('ck3_execute_step', tools)
        self.assertNotIn('ck3_auto_turn', tools)
        self.assertEqual(set(queue.callback_owners), {id(queue)})

    async def test_unknown_none_binding_rejects_before_any_callback(self):
        fixture = vanilla_fixture()
        fixture['source_snapshot']['succession_lifecycle']['pact_contract'] = 'unknown'
        queue = _AdoptedQueue(fixture)
        with self.assertRaises(ValueError):
            await _adopt_completed(AsyncOrdinarySuccessorQueue(queue), fixture, [])
        self.assertEqual(queue.calls, [])
        self.assertEqual(queue.observations, [])

    def test_exact_new_contract_and_legacy_off(self):
        value = vanilla_fixture()['source_snapshot']['succession_lifecycle']
        self.assertTrue(ordinary_no_pact_lifecycle(value))
        self.assertTrue(ordinary_no_pact_lifecycle(
            completed_continuation_fixture()['source_snapshot']['succession_lifecycle']))
        mutations = {
            'unknown_source': lambda v: v.update(source='unbound'),
            'unknown_pact': lambda v: v.update(pact_contract='unknown'),
            'missing_digest': lambda v: v.pop('environment_sha256'),
            'wrong_digest': lambda v: v.update(environment_sha256='not-a-digest'),
            'wrong_schema': lambda v: v.update(schema='unknown'),
            'rogue': lambda v: v.update(lifecycle='rogue_one_life'),
            'enabled': lambda v: v.update(xar_enabled='xar_on'),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                bad = copy.deepcopy(value)
                mutate(bad)
                self.assertFalse(ordinary_no_pact_lifecycle(bad))


if __name__ == '__main__':
    unittest.main()
