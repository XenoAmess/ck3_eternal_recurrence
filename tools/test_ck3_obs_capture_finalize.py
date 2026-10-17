"""Production capture closure helpers with only thread/priority I/O boundaries fake."""
import ast
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

PACK = Path(__file__).resolve().parent
SOURCE = PACK / 'ck3_obs_capture.py'
spec = importlib.util.spec_from_file_location('private_capture_closed_ordering', SOURCE)
capture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)


class DeferredThread:
    created = []

    def __init__(self, *, target, args, name, daemon):
        self.target, self.args, self.name, self.daemon = target, args, name, daemon
        self.started = False
        self.__class__.created.append(self)

    def start(self):
        self.started = True


class CaptureClosedOrdering(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='ordering-')
        self.addCleanup(self.temp.cleanup)
        recording = Path(self.temp.name)
        self.sid = 'f1111111-1111-4111-8111-111111111111'
        self.root = recording / self.sid
        self.root.mkdir()
        self.output = recording / (self.sid + '.mkv')
        self.output.write_bytes(b'synthetic-closed-media')
        self.cleanup = {'inputs_unbound': True, 'unknown_or_global_stop_calls': 0, 'engine_close': {
            'requested': True, 'actual_exit_code': 0, 'normal_exit_proven': True, 'forced_process_calls': 0}}
        for name, data in [('cleanup.json', self.cleanup), ('closed-file-probe.json', {
                'format': {'size': str(self.output.stat().st_size)}, 'streams': [{'codec_type': 'video'}]}),
                ('started.json', {'game_pid': 700, 'game_creation_filetime': 123456700}),
                ('obs-launch.json', {'pid': 701, 'creation_filetime': 123456701})]:
            (self.root / name).write_text(json.dumps(data), encoding='utf-8')
        self.job = {'session_id': self.sid, 'pid': 700, 'game_creation_filetime': 123456700,
                    'recording_root': str(recording)}
        self.completed = {'state': 'completed', 'path': str(self.output), 'bytes': self.output.stat().st_size}
        self.full_hash_calls = []
        actual_sha = capture._sha

        def checked_sha(path):
            if Path(path) == self.output:
                self.full_hash_calls.append('full-media-hash')
                self.assertTrue((self.root / 'capture_closed.json').exists())
                self.assertTrue((self.root / 'cleanup.json').exists())
            return actual_sha(path)

        DeferredThread.created = []
        self.sha_patch = patch.object(capture, '_sha', checked_sha)
        self.thread_patch = patch.object(capture.threading, 'Thread', DeferredThread)
        self.priority_patch = patch.object(capture, '_lower_media_finalizer_priority',
                                          lambda: {'scope': 'synthetic-own-worker', 'applied': True})
        for item in (self.sha_patch, self.thread_patch, self.priority_patch):
            item.start()
            self.addCleanup(item.stop)

    def publish(self):
        capture._publish_capture_closed_and_finalize(self.root, self.job, self.completed, self.cleanup)

    def test_capture_closed_normal_cleanup_precedes_background_hash_and_completed(self):
        self.publish()
        self.assertEqual(self.full_hash_calls, [])
        self.assertFalse((self.root / 'completed.json').exists())
        fact = json.loads((self.root / 'capture_closed.json').read_bytes())
        self.assertTrue(fact['media_sha256_pending'])
        self.assertEqual(fact['session_id'], self.sid)
        self.assertEqual((fact['game_pid'], fact['obs_pid']), (700, 701))
        self.assertEqual(fact['output_bytes'], self.output.stat().st_size)
        self.assertTrue(DeferredThread.created[0].started)
        self.assertFalse(DeferredThread.created[0].daemon)
        DeferredThread.created[0].target(*DeferredThread.created[0].args)
        completed = json.loads((self.root / 'completed.json').read_bytes())
        self.assertEqual(completed['sha256'], hashlib.sha256(self.output.read_bytes()).hexdigest())
        self.assertEqual(self.full_hash_calls, ['full-media-hash'])

    def test_real_producer_to_public_readonly_consumer_without_waiting_for_hash(self):
        self.job["receipt_root"] = str(self.root)
        (self.root / "job.json").write_text(json.dumps(self.job), encoding="utf-8")
        self.publish()
        result = capture.read_capture_closed_receipt(
            self.root, session_id=self.sid, game_pid=700,
            game_creation_filetime=123456700, recording_worker_pid=os.getpid(),
            recording_root=self.output.parent)
        self.assertEqual(result["status"], "CAPTURE_CLOSED_VERIFIED")
        self.assertFalse(result["completed_file_observed"])
        self.assertFalse(result["media_sha256_verified"])
        self.assertFalse(result["video_body_read"])
        self.assertEqual(self.full_hash_calls, [])

    def test_non_normal_or_forced_cleanup_cannot_publish_capture_closed_or_hash(self):
        for name in ('forced', 'exit_nonzero', 'not_unbound'):
            with self.subTest(name=name):
                changed = copy.deepcopy(self.cleanup)
                if name == 'forced': changed['engine_close']['forced_process_calls'] = 1
                elif name == 'exit_nonzero': changed['engine_close']['actual_exit_code'] = 1
                else: changed['inputs_unbound'] = False
                with self.assertRaises(RuntimeError):
                    capture._publish_capture_closed_and_finalize(self.root, self.job, self.completed, changed)
                self.assertFalse((self.root / 'capture_closed.json').exists())
                self.assertEqual(self.full_hash_calls, [])

    def test_wrong_session_output_cannot_publish_or_hash(self):
        changed = {**self.job, 'session_id': 'crossed-session'}
        with self.assertRaises(RuntimeError):
            capture._publish_capture_closed_and_finalize(self.root, changed, self.completed, self.cleanup)
        self.assertEqual(self.full_hash_calls, [])

    def test_game_only_uses_actual_started_generation(self):
        self.job["game_creation_filetime"] = None
        self.publish()
        fact = json.loads((self.root / "capture_closed.json").read_bytes())
        self.assertEqual(fact["game_creation_filetime"], 123456700)
        self.assertEqual(self.full_hash_calls, [])

    def test_wrong_or_missing_started_generation_is_rejected(self):
        for value in (
            {"game_pid": 799, "game_creation_filetime": 123456700},
            {"game_pid": 700, "game_creation_filetime": True},
            {"game_pid": 700, "game_creation_filetime": 123456799},
        ):
            with self.subTest(value=value):
                (self.root / "started.json").write_text(json.dumps(value), encoding="utf-8")
                with self.assertRaises(RuntimeError):
                    self.publish()
                self.assertFalse((self.root / "capture_closed.json").exists())
                self.assertEqual(self.full_hash_calls, [])

    def test_media_hash_error_keeps_capture_closed_and_separate_integrity_failure(self):
        self.publish()
        with patch.object(capture, '_sha', side_effect=OSError('synthetic media read failure')):
            DeferredThread.created[0].target(*DeferredThread.created[0].args)
        self.assertTrue((self.root / 'capture_closed.json').exists())
        self.assertTrue((self.root / 'media-finalization-failed.json').exists())
        self.assertFalse((self.root / 'failed.json').exists())
        self.assertFalse((self.root / 'completed.json').exists())

    def test_actual_worker_releases_exitstack_before_publishing_and_never_hashes_video_inside_capture(self):
        tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
        worker = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'run_worker')
        calls = [node for node in ast.walk(worker) if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Name) and node.func.id == '_publish_capture_closed_and_finalize']
        self.assertEqual(len(calls), 1)
        self.assertTrue(any(isinstance(node, ast.Expr) and node.value is calls[0] for node in worker.body))
        self.assertFalse(any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id == '_sha' and node.args and isinstance(node.args[0], ast.Name)
            and node.args[0].id == 'output' for node in ast.walk(worker)))
        close_with = next(node for node in worker.body if isinstance(node, ast.With))
        self.assertGreater(calls[0].lineno, close_with.end_lineno)


if __name__ == '__main__':
    unittest.main(verbosity=2)
