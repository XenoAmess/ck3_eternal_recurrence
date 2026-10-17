"""Metadata-only actual crash replay and future non-AUTO identity boundaries."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest
import uuid

import tempfile
from tools import ck3_stall_edl as fixed
from tools import collect_stall_edl as collector
ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tools/fixtures'
PROJECTION = json.loads((FIXTURES / 'edl_null_sequence_projection.json').read_bytes())
ACTUAL = PROJECTION['actual_status_fields']
PREVIOUS = json.loads((FIXTURES / 'edl_null_sequence_previous.json').read_bytes())
PACK = None
STATUS_PATH = None


def write(row, suffix):
    root = PACK / 'test-inputs'
    root.mkdir(exist_ok=True)
    path = root / (uuid.uuid4().hex + '-' + suffix + '.json')
    fixed.create(path, row)
    return path

def status(incident='synthetic-second-no-auto', sequence=None, *, withdrawn=False):
    row = deepcopy(ACTUAL)
    row.update(incident_id=incident, opened_at_utc='2026-10-17T06:30:00+00:00')
    row['halt_receipt'] = fixed.pin(write({'synthetic': True, 'kind': 'pair-observation'}, 'halt'))
    if sequence is not None:
        row['original_request'] = {'sequence': sequence}
    if withdrawn:
        row.update(withdrawn=True, EDL_wait_interval_allowed=False,
                   withdrawn_at_utc='2026-10-17T06:31:00+00:00')
    return row

def seed(intervals=None):
    config = fixed.as_config(PREVIOUS)
    config.update(intervals=intervals or [], markers=[], evidence_pins={})
    return fixed.build(config)

def prior(sequence=None, namespace='p36'):
    row = {'id': 'synthetic-legacy-wait', 'game_pid': ACTUAL['binding']['game_pid'],
           'start_at_utc': '2026-10-17T06:20:00+00:00',
           'end_at_utc': '2026-10-17T06:21:00+00:00'}
    if sequence is not None:
        row['original_auto_sequence'] = sequence
    if namespace is not None:
        row['source_sdk_prefix'] = namespace
    return row

class Focused(unittest.TestCase):
    def setUp(self):
        global PACK, STATUS_PATH
        self.temp = tempfile.TemporaryDirectory(prefix='edl-identity-')
        PACK = Path(self.temp.name)
        # Only this metadata pin is rebound. Actual identities/times and the
        # missing original_request field remain unchanged; no old path is read.
        actual = deepcopy(ACTUAL)
        actual['halt_receipt'] = fixed.pin(write({'synthetic': True}, 'halt'))
        STATUS_PATH = write(actual, 'actual-projection')

    def tearDown(self):
        self.temp.cleanup()

    def test_actual_null_identity_adds_one_incident_without_reclaiming_old_wait(self):
        self.assertTrue(PROJECTION['original_request_field_absent_in_actual_status'])
        self.assertNotIn('original_request', ACTUAL)
        before = fixed.build(fixed.as_config(PREVIOUS))
        after = fixed.sync_status(before, STATUS_PATH)
        self.assertEqual(len(after['intervals']), len(before['intervals']) + 1)
        self.assertEqual(after['intervals'][-1]['incident_id'], ACTUAL['incident_id'])
        self.assertIsNone(after['intervals'][-1]['end_at_utc'])

    def test_actual_new_collector_preserves_six_previous_waits(self):
        store = PACK / ('collector-replay-' + uuid.uuid4().hex)
        store.mkdir()
        path, result = collector.consume(PREVIOUS, STATUS_PATH,
            store, ROOT / 'tools/recording-stall-policy.json')
        self.assertTrue(path.is_file())
        self.assertEqual(len(result['intervals']), len(PREVIOUS['intervals']) + 1)
        for before, after in zip(PREVIOUS['intervals'], result['intervals']):
            for key in ('id', 'incident_id', 'start_at_utc', 'end_at_utc'):
                self.assertEqual(before.get(key), after.get(key))
        self.assertEqual(result['intervals'][-1]['incident_id'], ACTUAL['incident_id'])
        self.assertIsNone(result['intervals'][-1]['end_at_utc'])

    def test_empty_seed_then_second_non_auto_is_not_silently_lost(self):
        first = fixed.sync_status(seed(), STATUS_PATH)
        config = fixed.as_config(first)
        # Explicit synthetic closed boundary: no actual recovery is asserted.
        config['intervals'][0]['end_at_utc'] = '2026-10-17T06:27:00+00:00'
        closed = fixed.build(config)
        second = write(status(), 'second-non-auto')
        after = fixed.sync_status(closed, second)
        self.assertEqual(len(after['intervals']), 2)
        self.assertEqual(after['intervals'][0]['incident_id'], ACTUAL['incident_id'])
        self.assertEqual(after['intervals'][1]['incident_id'], 'synthetic-second-no-auto')

    def test_missing_null_zero_negative_and_bool_are_not_auto_keys(self):
        for value in (None, 0, -1, True, False):
            with self.subTest(value=value):
                old = seed([prior(1)])
                result = fixed.sync_status(old, write(status(sequence=value), 'invalid-sequence'))
                self.assertEqual(len(result['intervals']), 2)
                self.assertNotIn('incident_id', result['intervals'][0])

    def test_known_positive_same_namespace_legacy_key_still_matches(self):
        result = fixed.sync_status(seed([prior(19)]), write(status(sequence=19), 'legacy-match'))
        self.assertEqual(len(result['intervals']), 1)
        self.assertEqual(result['intervals'][0]['incident_id'], 'synthetic-second-no-auto')

    def test_unknown_and_other_namespace_and_bool_legacy_key_do_not_match(self):
        for old in (prior(19, None), prior(19, 'p35'), prior(True, 'p36')):
            with self.subTest(old=old):
                value = 1 if old.get('original_auto_sequence') is True else 19
                result = fixed.sync_status(seed([old]), write(status(sequence=value), 'no-cross-sdk'))
                self.assertEqual(len(result['intervals']), 2)
                self.assertNotIn('incident_id', result['intervals'][0])

    def test_withdrawn_non_auto_only_adds_no_edit_marker(self):
        old = seed([prior(), dict(prior(), id='synthetic-second-null-wait',
                                 start_at_utc='2026-10-17T06:22:00+00:00',
                                 end_at_utc='2026-10-17T06:23:00+00:00')])
        result = fixed.sync_status(old, write(status(withdrawn=True), 'withdrawn'))
        self.assertEqual(result['intervals'], old['intervals'])
        self.assertEqual(len(result['markers']), 1)
        self.assertFalse(result['markers'][0]['recovery_claimed'])

    def test_genuinely_ambiguous_positive_keys_still_fail_closed(self):
        rows = [prior(19), dict(prior(19), id='synthetic-second-positive-wait',
                               start_at_utc='2026-10-17T06:22:00+00:00',
                               end_at_utc='2026-10-17T06:23:00+00:00')]
        with self.assertRaisesRegex(ValueError, 'ambiguously matches multiple waits'):
            fixed.sync_status(seed(rows), write(status(sequence=19), 'ambiguous-positive'))

if __name__ == '__main__':
    unittest.main(verbosity=2)
