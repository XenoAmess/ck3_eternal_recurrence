"""Pure DATA tests of the exact functions used by candidate main; no main or Win32 calls."""
import copy
import importlib.util
from pathlib import Path
import unittest

_spec = importlib.util.spec_from_file_location(
    'owned_custody_candidate', Path(__file__).with_name('post-owned-once108.py'))
candidate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(candidate)


class Harness:
    def __init__(self, **config):
        self.config = config
        self.state = {'hwnd': 17, 'lparam': 29, 'messages': []}
        self.events = []
        self.records = {}
        self.posts = []
        self.verifications = 0
        self.owner_queries = 0
        self.clock = 0
        self.primary = RuntimeError('original DATA failure')
        self.terminal = OSError('terminal DATA record failure')

    def stamp(self):
        self.clock += 1
        return 'DATA-%d' % self.clock

    def verify(self):
        self.verifications += 1
        self.events.append(('verify', self.verifications))
        if 'owner' in self.config:
            def query():
                self.owner_queries += 1
                return self.config['owner']
            candidate.require_window_owner(query, 77132)
        if self.config.get('verify_fail') == self.verifications:
            raise self.primary

    def post(self, message, wparam):
        self.posts.append((message, wparam))
        self.events.append(('post', message, wparam))
        index = len(self.posts)
        if self.config.get('post_fail') == index:
            raise self.primary
        rejected = self.config.get('reject') == index
        return not rejected, (100 + index if rejected else 0)

    def persist(self, name, value):
        self.events.append(('persist', name))
        if self.config.get('intent_fail') and name == (
                'MESSAGE-%02d-INTENT.json' % self.config['intent_fail']):
            raise self.primary
        if self.config.get('result_fail') and name == (
                'MESSAGE-%02d-RESULT.json' % self.config['result_fail']):
            raise self.primary
        if name == 'ACTUAL.json' and self.config.get('terminal_fail'):
            raise self.terminal
        if name in self.records:
            raise AssertionError('create-only DATA record reused')
        self.records[name] = copy.deepcopy(value)

    def final(self):
        self.events.append(('final',))
        if self.config.get('final_fail'):
            raise self.primary
        return {'final_game': 'DATA_ONLY', 'ledger_unchanged': True}

    def run(self):
        return candidate.finish_attempt(
            self.state,
            lambda: candidate.post_sequence(
                self.state, self.verify, self.post, self.persist, self.stamp),
            self.final, self.persist, self.stamp)


class TestOwnedMessageCustody(unittest.TestCase):
    def test_normal_order_and_known_rejection_stop(self):
        h = Harness()
        self.assertIs(h.state, h.run())
        expected = [
            ('verify', 1), ('persist', 'MESSAGE-01-INTENT.json'), ('post', 0x0200, 0),
            ('persist', 'MESSAGE-01-RESULT.json'),
            ('verify', 2), ('persist', 'MESSAGE-02-INTENT.json'), ('post', 0x0201, 1),
            ('persist', 'MESSAGE-02-RESULT.json'),
            ('verify', 3), ('persist', 'MESSAGE-03-INTENT.json'), ('post', 0x0202, 0),
            ('persist', 'MESSAGE-03-RESULT.json'), ('final',), ('persist', 'ACTUAL.json')]
        self.assertEqual(expected, h.events)
        self.assertEqual([(0x0200, 0), (0x0201, 1), (0x0202, 0)], h.posts)
        self.assertEqual(3, h.state['durable_result_count'])
        self.assertIsNone(h.state['in_flight'])
        self.assertFalse(h.records['ACTUAL.json']['effect_verified'])
        self.assertTrue(h.records['ACTUAL.json']['do_not_repeat'])
        for index, raw in enumerate(((0x0200, 0), (0x0201, 1), (0x0202, 0)), 1):
            intent = h.records['MESSAGE-%02d-INTENT.json' % index]
            self.assertEqual((17, 29, raw[0], raw[1]),
                             (intent['hwnd'], intent['lparam'], intent['message'], intent['wparam']))
            self.assertEqual('POST_MAY_HAVE_BEGUN_OUTCOME_UNKNOWN', intent['status'])
            self.assertIs(True, h.records['MESSAGE-%02d-RESULT.json' % index]['accepted'])
        for rejected_at in (1, 2):
            with self.subTest(rejected_at=rejected_at):
                h = Harness(reject=rejected_at)
                h.run()
                self.assertEqual([(0x0200, 0), (0x0201, 1)][:rejected_at], h.posts)
                self.assertEqual('POST_REJECTED', h.state['sequence_status'])
                self.assertEqual(rejected_at, h.state['durable_result_count'])
                last = h.records['MESSAGE-%02d-RESULT.json' % rejected_at]
                self.assertIs(False, last['accepted'])
                self.assertEqual(100 + rejected_at, last['error'])
                self.assertIsNone(h.state['in_flight'])
                self.assertNotEqual(
                    'WINDOW_MESSAGES_QUEUED_EFFECT_UNKNOWN_DO_NOT_REPEAT',
                    h.records['ACTUAL.json']['classification'])
                if rejected_at == 2:
                    self.assertIs(True, h.records['MESSAGE-01-RESULT.json']['accepted'])
                self.assertNotIn('MESSAGE-%02d-INTENT.json' % (rejected_at + 1), h.records)

    def test_partial_unknown_and_final_failures_preserve_original(self):
        cases = [
            ('down_then_verify', {'verify_fail': 3}, 2, 2, None),
            ('post_throws', {'post_fail': 2}, 2, 1, 2),
            ('intent_write', {'intent_fail': 2}, 1, 1, None),
            ('result_write', {'result_fail': 2}, 2, 1, 2),
            ('final_verify', {'final_fail': True}, 3, 3, None),
            ('secondary_terminal', {'verify_fail': 3, 'terminal_fail': True}, 2, 2, None),
            ('terminal_only', {'terminal_fail': True}, 3, 3, None)]
        for label, config, post_count, durable_count, pending_index in cases:
            with self.subTest(case=label):
                h = Harness(**config)
                original = h.terminal if label == 'terminal_only' else h.primary
                with self.assertRaises(type(original)) as caught:
                    h.run()
                self.assertIs(original, caught.exception)
                self.assertEqual(post_count, len(h.posts))
                self.assertEqual(durable_count, h.state['durable_result_count'])
                self.assertEqual(durable_count, len(
                    [name for name in h.records if name.endswith('-RESULT.json')]))
                self.assertEqual('FAILED', h.state['terminal_status'])
                self.assertEqual(1, h.events.count(('persist', 'ACTUAL.json')))
                self.assertTrue(all(row['accepted'] is True for row in h.state['messages']))
                if pending_index is None:
                    self.assertIsNone(h.state['in_flight'])
                else:
                    self.assertEqual(pending_index, h.state['in_flight']['index'])
                    self.assertEqual('POST_MAY_HAVE_BEGUN_OUTCOME_UNKNOWN',
                                     h.state['in_flight']['status'])
                    self.assertIn('MESSAGE-%02d-INTENT.json' % pending_index, h.records)
                    self.assertNotIn('MESSAGE-%02d-RESULT.json' % pending_index, h.records)
                if post_count < 3:
                    self.assertNotIn((0x0202, 0), h.posts)
                if label == 'down_then_verify':
                    self.assertNotIn(('final',), h.events)
                    actual = h.records['ACTUAL.json']
                    self.assertEqual(2, len(actual['messages']))
                    self.assertEqual('PRECHECK', actual['failure_phase'])
                if label == 'result_write':
                    self.assertIs(True, h.state['messages'][1]['accepted'])
                if label == 'final_verify':
                    self.assertEqual('FINAL_VERIFY', h.records['ACTUAL.json']['failure_phase'])
                    self.assertEqual(3, len(h.records['ACTUAL.json']['messages']))
                if label == 'secondary_terminal':
                    self.assertEqual('OSError', h.state['terminal_record_error']['type'])
                    self.assertNotIn('ACTUAL.json', h.records)
                if label == 'terminal_only':
                    self.assertNotIn('ACTUAL.json', h.records)

    def test_failed_current_window_query_cannot_reuse_old_pid(self):
        for observed in ((0, 77132), (1, 999)):
            with self.subTest(query=observed):
                h = Harness(owner=observed)
                with self.assertRaises(RuntimeError):
                    h.run()
                self.assertEqual(1, h.owner_queries)
                self.assertEqual([], h.posts)
                self.assertNotIn('MESSAGE-01-INTENT.json', h.records)
                self.assertEqual('PRECHECK', h.records['ACTUAL.json']['failure_phase'])
        h = Harness(owner=(1, 77132))
        h.run()
        self.assertEqual(3, h.owner_queries)
        self.assertEqual(3, len(h.posts))


if __name__ == '__main__':
    unittest.main()
