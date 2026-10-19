"""Finite latest-file retry; no Game, OBS or native bridge is constructed."""
import ast
import base64
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import importlib.util
import os
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).with_name('ck3_obs_capture.py')
spec = importlib.util.spec_from_file_location('mutable_capture_fixture', SOURCE)
capture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)


def locked_error(code=5):
    error = PermissionError('synthetic immutable-holder lock')
    error.winerror = code
    return error


class Clock:
    def __init__(self):
        self.value, self.sleeps = 0., []

    def monotonic(self):
        return self.value

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.value += seconds


class MutableReplaceTests(unittest.TestCase):
    def test_transient_png_replace_does_not_recapture_or_rewrite_pending(self):
        # Execute the actual nested screenshot producer with only its OBS client
        # replaced. Replacement retry must not repeat either screenshot RPC.
        node = next(n for n in ast.walk(ast.parse(SOURCE.read_text(encoding='utf-8')))
                    if isinstance(n, ast.FunctionDef) and n.name == 'screenshots')
        fixture_png = b'\x89PNG\r\n\x1a\nfixture'
        calls, attempts, guards = [], [], []
        client = SimpleNamespace(get_source_screenshot=lambda *args: calls.append(args) or
            SimpleNamespace(image_data='data:image/png;base64,' + base64.b64encode(fixture_png).decode()))
        original = Path.replace
        clock = Clock()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def replace(pending, destination):
                attempts.append((pending, destination, pending.read_bytes()))
                if len(attempts) <= 2:
                    raise locked_error()
                return original(pending, destination)
            namespace = {'guard': lambda: guards.append('guard'), '_output_binding': lambda engine: None,
                'source_binding': lambda: None, 'datetime': datetime, 'timezone': timezone,
                'profile': {'profile_name': 'own-scene-fixture'}, 'source': 'own-game-fixture',
                'engine': SimpleNamespace(client=client), 'root': root, 'base64': base64,
                'hashlib': capture.hashlib, 'frames': [], '_replace_mutable_latest': capture._replace_mutable_latest}
            exec(compile(ast.Module(body=[node], type_ignores=[]), str(SOURCE), 'exec'), namespace)
            with patch.object(Path, 'replace', replace), patch.object(capture.time, 'monotonic', clock.monotonic), patch.object(capture.time, 'sleep', clock.sleep):
                result = namespace['screenshots']('recording-latest', replace_latest=True)
            self.assertEqual(len(calls), 2)
            self.assertEqual(guards, ['guard'])
            self.assertEqual([row[0] for row in attempts[:3]], [attempts[0][0]] * 3)
            self.assertTrue(all(row[2] == fixture_png for row in attempts))
            self.assertEqual((root / 'recording-latest-game.png').read_bytes(), fixture_png)
            self.assertEqual((root / 'recording-latest-scene.png').read_bytes(), fixture_png)
            self.assertTrue(result['mutable_latest_frame'])
            self.assertLess(clock.value, 2.)

    def test_permanent_sharing_failure_keeps_original_bytes_and_fails_finitely(self):
        error, clock = locked_error(), Clock()
        with tempfile.TemporaryDirectory() as directory:
            old, pending = Path(directory) / 'latest.json', Path(directory) / 'latest.json.tmp'
            old.write_bytes(b'old'); pending.write_bytes(b'new')
            with patch.object(Path, 'replace', side_effect=error) as replace, patch.object(capture.time, 'monotonic', clock.monotonic), patch.object(capture.time, 'sleep', clock.sleep):
                with self.assertRaises(PermissionError) as raised:
                    capture._replace_mutable_latest(pending, old)
            self.assertIs(raised.exception, error)
            self.assertEqual(replace.call_count, 8)
            self.assertEqual((old.read_bytes(), pending.read_bytes()), (b'old', b'new'))
            self.assertLessEqual(sum(clock.sleeps), 2.)

    def test_nonsharing_errors_are_not_retried(self):
        error = OSError('actual nonsharing boundary'); error.winerror = 87
        with patch.object(Path, 'replace', side_effect=error) as replace, patch.object(capture.time, 'sleep') as sleep:
            with self.assertRaises(OSError) as raised:
                capture._replace_mutable_latest(Path('own.tmp'), Path('own.latest'))
        self.assertIs(raised.exception, error)
        self.assertEqual(replace.call_count, 1)
        sleep.assert_not_called()

    def test_deadline_stops_new_attempts_and_other_windows_share_codes_are_finite(self):
        clock, calls = Clock(), []
        def replace(pending, destination):
            calls.append((pending, destination)); clock.value += .99
            raise locked_error(32 if len(calls) == 1 else 33)
        with patch.object(Path, 'replace', replace), patch.object(capture.time, 'monotonic', clock.monotonic), patch.object(capture.time, 'sleep', clock.sleep):
            with self.assertRaises(PermissionError):
                capture._replace_mutable_latest(Path('own.tmp'), Path('own.latest'))
        self.assertEqual(len(calls), 2)
        self.assertEqual(clock.value, 2.)

    @unittest.skipUnless(os.name == 'nt', 'Windows shared-read replacement mechanics')
    def test_real_own_read_lock_releases_only_after_first_observed_win5(self):
        # Only two <=32B own temporary files; no PNG/OBS/Game object is needed.
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
            wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        kernel.CreateFileW.restype = wintypes.HANDLE
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle.restype = wintypes.BOOL
        errors, timers = [], []
        released = threading.Event()
        original = Path.replace
        with tempfile.TemporaryDirectory() as directory:
            old, pending = Path(directory) / 'own.latest', Path(directory) / 'own.tmp'
            old.write_bytes(b'old'); pending.write_bytes(b'new')
            handle = kernel.CreateFileW(str(old), 0x80000000, 3, None, 3, 0x80, None)
            self.assertNotIn(handle, (None, 0, ctypes.c_void_p(-1).value))
            def release():
                if kernel.CloseHandle(handle):
                    released.set()
            def replace(source, destination):
                try:
                    return original(source, destination)
                except PermissionError as error:
                    errors.append(error.winerror)
                    if not timers:
                        timer = threading.Timer(.05, release)
                        timers.append(timer)
                        timer.start()
                    raise
            try:
                with patch.object(Path, 'replace', replace):
                    capture._replace_mutable_latest(pending, old)
                for timer in timers:
                    timer.join(1.)
                self.assertTrue(errors)
                self.assertTrue(all(code in (5, 32, 33) for code in errors))
                self.assertTrue(released.is_set())
                self.assertEqual(old.read_bytes(), b'new')
                self.assertFalse(pending.exists())
            finally:
                for timer in timers:
                    timer.join(1.)
                if not released.is_set():
                    self.assertTrue(kernel.CloseHandle(handle))


if __name__ == '__main__':
    unittest.main()
