"""One synthetic check of the actual R09 admission inherited by A/B relays."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/split_merge/root_relay.py'
spec = importlib.util.spec_from_file_location('ordinary_R09_admission_subject', PATH)
if spec is None or spec.loader is None:
    raise ValueError('actual admission source unavailable')
subject = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = subject
spec.loader.exec_module(subject)


class NativeAdmission(unittest.TestCase):
    def test_actual_admission_and_frame_keep_null_but_refuse_missing_and_identity_drift(self) -> None:
        machine = 'SYNTHETIC-ordinary'
        run = machine + '--vanilla--R0001'
        source = 'a' * 40
        context: dict[str, object] = {'machine_id': machine, 'source_head': source,
            'identity': {'machine_id': machine, 'run_id': run, 'sequence': 1, 'mod_key': 'vanilla'}}
        proof: dict[str, object] = {'machine_id': machine, 'run_id': run, 'source_head': source,
            'pid': 1234, 'process_creation_filetime_100ns': 134000000000000123,
            'connection_generation': 1, 'actual_runtime_character_full_id': 31254,
            'episode_run_id': None, 'stable_character_intent': {'historical_id': 1128,
                'bookmark_character_name_key': 'bookmark_rags_to_riches_duke_robert'}}
        binding = subject.admission(context, proof, run_id=run, source=source,
                                    sequence=1, machine=machine, minimum_sequence=1)
        self.assertIsNone(binding['episode'])
        self.assertEqual(binding['process_create_time_100ns'], 134000000000000123)
        frame: dict[str, object] = {'paused': True, 'map_ready': True, 'episode_run_id': None,
            'revision': 1, 'native_revision': 1, 'snapshot_id': 'SYNTHETIC:1', 'date_raw': 53146848,
            'active_event': None, 'pending_character_interaction': None,
            'player_armies': [{'army_id': 93, 'source': 'native'}],
            'played_character': {'character_id': 31254, 'alive': True},
            'diagnostics': {'connected': True, 'bridge_pid': 1234, 'connection_generation': 1,
                'hello': {'expected_ck3_version': '1.20.0.4', 'expected_ck3_sha256': subject.EXE_SHA,
                          'game_adapter_status': 'ready', 'ck3_build_match': True,
                          'pid': 1234, 'connection_generation': 1}}}
        subject.validate_frame(frame, binding)
        missing = dict(proof)
        del missing['episode_run_id']
        with self.assertRaisesRegex(RuntimeError, 'episode missing'):
            subject.admission(context, missing, run_id=run, source=source,
                              sequence=1, machine=machine, minimum_sequence=1)
        del frame['episode_run_id']
        with self.assertRaisesRegex(RuntimeError, 'episode missing'):
            subject.validate_frame(frame, binding)
        wrong = dict(proof)
        wrong['connection_generation'] = False
        with self.assertRaisesRegex(RuntimeError, 'positive runtime'):
            subject.admission(context, wrong, run_id=run, source=source,
                              sequence=1, machine=machine, minimum_sequence=1)


if __name__ == '__main__':
    unittest.main()
