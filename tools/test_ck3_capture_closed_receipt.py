from pathlib import Path
import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch

from ck3_capture_closed_receipt import validate_capture_closed_receipt


class CaptureClosedReceiptTests(unittest.TestCase):
    def setUp(self):
        parent = Path(__file__).resolve().parent
        self.temporary = tempfile.TemporaryDirectory(dir=parent, prefix='capture-closed-fixture-')
        self.fixture = Path(self.temporary.name).resolve()
        self.assertTrue(self.fixture.is_relative_to(parent))
        self.sid = 'cab8bd7c-a0c6-4695-8c87-39b7c947acc5'
        self.recordings = self.fixture / 'recordings'
        self.root = self.recordings / self.sid
        self.root.mkdir(parents=True)
        self.output = self.recordings / (self.sid + '.mkv')
        self.output.write_bytes(b'fixture-closed-video-body')
        self.expected = {'session_id': self.sid, 'game_pid': 100, 'game_creation_filetime': 123,
                         'recording_worker_pid': 789, 'recording_root': self.recordings}
        self.job = {'session_id': self.sid, 'pid': 100, 'game_creation_filetime': 123,
                    'receipt_root': str(self.root), 'recording_root': str(self.recordings)}
        self.write('job.json', self.job)
        self.write('started.json', {'game_pid': 100, 'game_creation_filetime': 123})
        self.write('obs-launch.json', {'pid': 456, 'creation_filetime': 457})
        self.close = {'actual_exit_code': 0, 'normal_exit_proven': True, 'forced_process_calls': 0}
        self.cleanup = {'inputs_unbound': True, 'engine_close': self.close,
                        'unknown_or_global_stop_calls': 0}
        self.write('cleanup.json', self.cleanup)
        self.write('closed-file-probe.json', {'streams': [{'codec_type': 'video'}],
                                            'format': {'size': str(self.output.stat().st_size)}})
        self.capture = {'schema': 'xar.ck3.capture-closed-before-media-hash/v1',
                        'session_id': self.sid, 'game_pid': 100, 'game_creation_filetime': 123,
                        'obs_pid': 456, 'obs_creation_filetime': 457,
                        'postprocessing_worker_pid': 789, 'inputs_unbound': True,
                        'engine_close': self.close, 'capture_custody_released_before_publication': True,
                        'media_sha256_pending': True, 'output_path': str(self.output),
                        'output_bytes': self.output.stat().st_size,
                        'final_completed_path': str(self.root / 'completed.json')}
        self.repin()

    def tearDown(self):
        self.assertTrue(self.fixture.is_relative_to(Path(__file__).resolve().parent))
        self.temporary.cleanup()

    def write(self, name, value):
        (self.root / name).write_text(json.dumps(value), encoding='utf-8')

    def repin(self):
        for key, name in [('cleanup', 'cleanup.json'), ('closed_file_probe', 'closed-file-probe.json')]:
            path = self.root / name
            self.capture[key] = {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        self.write('capture_closed.json', self.capture)

    def verify(self, **overrides):
        return validate_capture_closed_receipt(self.root, **dict(self.expected, **overrides))

    def test_closed_capture_passes_without_completed_or_reading_video_body(self):
        original = Path.read_bytes
        def small_receipts_only(path):
            if path.resolve() == self.output:
                raise AssertionError('consumer must not read the video body')
            return original(path)
        with patch.object(Path, 'read_bytes', small_receipts_only):
            result = self.verify()
        self.assertEqual(result['status'], 'CAPTURE_CLOSED_VERIFIED')
        self.assertIs(result['completed_file_observed'], False)
        self.assertIs(result['media_sha256_verified'], False)
        self.assertIs(result['video_body_read'], False)

    def test_game_only_nullable_job_birth_uses_actual_started_birth(self):
        self.write('job.json', dict(self.job, game_creation_filetime=None))
        self.assertEqual(self.verify()['game_creation_filetime'], 123)
        self.write('started.json', {'game_pid': 100, 'game_creation_filetime': 124})
        with self.assertRaisesRegex(ValueError, 'actual started Game identity'):
            self.verify()

    def test_missing_capture_publication_is_pending_even_with_cleanup(self):
        (self.root / 'capture_closed.json').unlink()
        self.assertIsNone(self.verify())

    def test_missing_cleanup_publication_is_pending(self):
        (self.root / 'cleanup.json').unlink()
        self.assertIsNone(self.verify())

    def test_final_media_failure_is_separate_from_capture_closure(self):
        self.write('media-finalization-failed.json', {'error': 'offline hash failed'})
        self.assertIs(self.verify()['media_finalization_failed_file_observed'], True)
        self.write('completed.json', {'sha256': 'unverified-by-consumer'})
        self.assertIs(self.verify()['completed_file_observed'], True)
        self.assertIs(self.verify()['media_sha256_verified'], False)

    def test_independent_game_worker_and_root_admission_mismatches(self):
        for key, value in [('game_pid', 101), ('game_creation_filetime', 124),
                           ('recording_worker_pid', 790), ('game_pid', True),
                           ('recording_root', self.fixture / 'wrong-root')]:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                self.verify(**{key: value})

    def test_native_capture_and_obs_identities_are_exact(self):
        for key, value in [('game_pid', 101), ('game_creation_filetime', 124),
                           ('obs_pid', 455), ('obs_creation_filetime', 458),
                           ('postprocessing_worker_pid', 790), ('inputs_unbound', False),
                           ('capture_custody_released_before_publication', False)]:
            self.write('capture_closed.json', dict(self.capture, **{key: value}))
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.verify()

    def test_normal_exit_cannot_be_replaced_by_forced_or_failed_exit(self):
        for close in [dict(self.close, forced_process_calls=1),
                      dict(self.close, actual_exit_code=1), dict(self.close, normal_exit_proven=False)]:
            self.write('cleanup.json', dict(self.cleanup, engine_close=close))
            self.capture['engine_close'] = close
            self.repin()
            with self.subTest(close=close), self.assertRaises(ValueError):
                self.verify()

    def test_boolean_exit_ack_does_not_prove_integer_exit_zero(self):
        close = dict(self.close, actual_exit_code=False)
        self.write('cleanup.json', dict(self.cleanup, engine_close=close))
        self.capture['engine_close'] = close
        self.repin()
        with self.assertRaises(ValueError):
            self.verify()

    def test_malformed_file_probe_is_rejected_as_validation_error(self):
        self.write('closed-file-probe.json', {'streams': ['untyped'], 'format': 'untyped'})
        self.repin()
        with self.assertRaisesRegex(ValueError, 'file probe'):
            self.verify()

    def test_small_receipt_hash_tamper_rejects(self):
        self.write('cleanup.json', dict(self.cleanup, unknown_or_global_stop_calls=1))
        with self.assertRaisesRegex(ValueError, 'small receipt pin differs'):
            self.verify()

    def test_small_receipt_path_escape_rejects_before_read(self):
        self.capture['cleanup']['path'] = str(self.fixture / 'outside.json')
        self.write('capture_closed.json', self.capture)
        with self.assertRaisesRegex(ValueError, 'small receipt pin differs'):
            self.verify()

    def test_original_job_scope_mismatch_rejects(self):
        self.write('job.json', dict(self.job, receipt_root=str(self.fixture)))
        with self.assertRaisesRegex(ValueError, 'job/actual started Game identity'):
            self.verify()

    def test_wrong_video_path_even_with_same_size_rejects(self):
        other = self.recordings / 'wrong.mkv'
        other.write_bytes(self.output.read_bytes())
        self.capture['output_path'] = str(other)
        self.write('capture_closed.json', self.capture)
        with self.assertRaises(ValueError):
            self.verify()

    def test_video_size_and_probe_must_agree(self):
        self.write('closed-file-probe.json', {'streams': [{'codec_type': 'video'}], 'format': {'size': '1'}})
        self.repin()
        with self.assertRaises(ValueError):
            self.verify()

    def test_real_capture_failure_cannot_be_ignored(self):
        self.write('failed.json', {'stage': 'capture'})
        with self.assertRaisesRegex(ValueError, 'capture failure'):
            self.verify()


if __name__ == '__main__':
    unittest.main(verbosity=2)
