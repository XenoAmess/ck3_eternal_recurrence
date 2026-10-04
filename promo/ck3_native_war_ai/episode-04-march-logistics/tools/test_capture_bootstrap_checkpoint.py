"""Offline save-receipt compatibility tests; no SDK, native process or screen."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('episode04_checkpoint_bootstrap_test_subject',
    Path(__file__).with_name('capture_bootstrap.py'))
bootstrap = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bootstrap
spec.loader.exec_module(bootstrap)


class CheckpointReceiptTests(unittest.TestCase):
    def setUp(self):
        explicit = os.environ.get('E04_CHECKPOINT_FIXTURE_ROOT')
        if explicit:
            self.directory = Path(explicit) / self._testMethodName
            self.directory.mkdir(parents=True, exist_ok=False)
        else:
            # Fixture bytes are retained after the run, rather than deleted.
            self.directory = Path(tempfile.mkdtemp(prefix='e04-checkpoint-receipt-'))
        self.profile = self.directory / 'source-profile'
        (self.profile / 'save games').mkdir(parents=True)
        self.save = self.profile / 'save games' / 'xar_checkpoint.ck3'
        self.save.write_bytes(b'offline-checkpoint-fixture-not-a-live-ck3-save')
        self.receipt_path = self.directory / 'save-receipt.json'
        self.build_path = self.directory / 'source-prepared.json'
        self.packet = {'is_error': False, 'request': {'tool': 'ck3_save_checkpoint', 'arguments': {}},
            'body': {'step': 'save-checkpoint', 'accepted': True, 'checkpoint': {
                'status': 'saved', 'path': str(self.save), 'size': self.save.stat().st_size,
                'sha256': hashlib.sha256(self.save.read_bytes()).hexdigest(),
                'episode_character_id': 33388, 'date_raw': 53149272,
                'succession_lifecycle': {'lifecycle': 'ordinary_campaign_succession',
                    'xar_enabled': 'xar_off', 'pact_contract': 'absent_by_fresh_campaign_xar_off_contract',
                    'source': 'pure-vanilla-enabled-mods-empty'}}}}
        self.build = {'game': {'sha256': bootstrap.EXE_SHA}, 'profile_dir': str(self.profile)}

    def observe(self, save=None):
        self.receipt_path.write_text(json.dumps(self.packet), encoding='utf-8')
        self.build_path.write_text(json.dumps(self.build), encoding='utf-8')
        return bootstrap.checkpoint_source(save or self.save, self.receipt_path, self.build_path)

    def test_dedicated_save_tool_is_accepted(self):
        result = self.observe()
        self.assertEqual((result['actor_id'], result['date_raw']), (33388, 53149272))

    def test_execute_step_save_tool_is_accepted(self):
        self.packet['request'] = {'tool': 'ck3_execute_step',
            'arguments': {'step': 'save-checkpoint', 'expected_revision': None}}
        result = self.observe()
        self.assertEqual(result['receipt']['path'], str(self.receipt_path.resolve()))

    def test_archived_identical_bytes_still_keep_original_profile_binding(self):
        archived = self.directory / 'archived-copy.ck3'
        archived.write_bytes(self.save.read_bytes())
        result = self.observe(archived)
        self.assertEqual(result['save']['path'], str(archived.resolve()))

    def test_execute_other_step_is_rejected_even_with_saved_body(self):
        self.packet['request'] = {'tool': 'ck3_execute_step', 'arguments': {'step': 'pause-map'}}
        with self.assertRaises(ValueError): self.observe()

    def test_execute_missing_arguments_is_rejected(self):
        self.packet['request'] = {'tool': 'ck3_execute_step'}
        with self.assertRaises(ValueError): self.observe()

    def test_unknown_tool_is_rejected(self):
        self.packet['request']['tool'] = 'ck3_take_snapshot'
        with self.assertRaises(ValueError): self.observe()

    def test_sdk_error_is_rejected(self):
        self.packet['is_error'] = True
        with self.assertRaises(ValueError): self.observe()

    def test_not_materialized_is_rejected(self):
        self.packet['body']['checkpoint']['status'] = 'submitted'
        with self.assertRaises(ValueError): self.observe()

    def test_size_mismatch_is_rejected(self):
        self.packet['body']['checkpoint']['size'] += 1
        with self.assertRaises(ValueError): self.observe()

    def test_sha_mismatch_is_rejected(self):
        self.packet['body']['checkpoint']['sha256'] = '0' * 64
        with self.assertRaises(ValueError): self.observe()

    def test_wrong_original_profile_is_rejected(self):
        self.build['profile_dir'] = str(self.directory / 'unrelated-profile')
        with self.assertRaises(ValueError): self.observe()

    def test_boolean_actor_is_rejected(self):
        self.packet['body']['checkpoint']['episode_character_id'] = True
        with self.assertRaises(ValueError): self.observe()

    def test_missing_date_is_rejected(self):
        self.packet['body']['checkpoint'].pop('date_raw')
        with self.assertRaises(ValueError): self.observe()

    def test_nonvanilla_lifecycle_is_rejected(self):
        self.packet['body']['checkpoint']['succession_lifecycle']['xar_enabled'] = 'xar_on'
        with self.assertRaises(ValueError): self.observe()

    def test_wrong_game_build_is_rejected(self):
        self.build['game']['sha256'] = '0' * 64
        with self.assertRaises(ValueError): self.observe()


if __name__ == '__main__':
    unittest.main()
