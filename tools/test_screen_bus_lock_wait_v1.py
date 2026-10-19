"""Owned temporary bus contention only: no CK3, current task bus or desktop."""
from contextlib import redirect_stdout
import errno
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

from tools import codex_task_bus as bus
from tools.g2_saved_campaign import screen_bus_lease_lock_wait_v1 as keeper

SOURCE = Path(bus.__file__).resolve()
BASE_PYTHON = getattr(sys, '_base_executable', sys.executable)


class ScreenLockWaitTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='xar-owned-bus-lock-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.bus = self.root / 'bus'
        (self.bus / 'tasks').mkdir(parents=True)
        (self.bus / 'bin').mkdir()
        (self.bus / 'bin/codex_task_bus.py').write_bytes(SOURCE.read_bytes())
        (self.bus / '.lock').write_bytes(b'0')
        self.sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest().upper()
        self.task = {'schema': bus.SCHEMA, 'task_id': 'owned-fixture', 'state': 'running',
            'resources': [bus.SCREEN_RESOURCE], 'last_sequence': 1, 'repo': str(self.root),
            'git': {'head': 'a' * 40, 'dirty_entries': 0},
            'updated_at_utc': datetime.now(timezone.utc).isoformat()}
        self.event = {'schema': bus.SCHEMA, 'sequence': 1, 'kind': 'registered',
            'task_id': 'owned-fixture', 'state': 'running', 'resources': [bus.SCREEN_RESOURCE]}
        bus.write_json_atomic(self.bus / 'tasks/owned-fixture.json', self.task)
        (self.bus / 'sequence.txt').write_text('1\n')
        (self.bus / 'events.jsonl').write_text(json.dumps(self.event) + '\n')

    def cli(self, wait, *args):
        return [BASE_PYTHON, str(SOURCE), '--bus-dir', str(self.bus),
            '--expected-cli-sha256', self.sha, '--lock-wait-seconds', str(wait), *args]

    def state_bytes(self):
        return tuple((self.bus / name).read_bytes() for name in
            ('tasks/owned-fixture.json', 'sequence.txt', 'events.jsonl', '.lock'))

    def test_actual_owned_lock_wait_exceeds_old_ten_second_window_then_reads(self):
        before = self.state_bytes()
        started = time.monotonic()
        with bus.bus_lock(self.bus, require_existing=True):
            child = subprocess.Popen(self.cli(45, 'list', '--require-existing'),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            try:
                time.sleep(11.0)
                self.assertIsNone(child.poll(), 'child must still be waiting on our owned byte lock')
            except BaseException:
                child.kill(); child.communicate(timeout=5); raise
        stdout, stderr = child.communicate(timeout=10)
        elapsed = time.monotonic() - started
        self.assertEqual(child.returncode, 0, stderr)
        self.assertGreaterEqual(elapsed, 11)
        self.assertEqual(json.loads(stdout)['tasks'][0]['task_id'], 'owned-fixture')
        self.assertEqual(self.state_bytes(), before)
        print(json.dumps({'owned_lock_mechanical': 'PASS', 'elapsed_seconds': elapsed,
            'child_returncode': child.returncode, 'protected_bus_bytes_unchanged': True}))

    def test_actual_owned_timeout_is_typed_and_never_enters_protected_read(self):
        (self.bus / 'tasks/owned-fixture.json').write_bytes(b'invalid JSON must not be read while locked')
        before = self.state_bytes()
        with bus.bus_lock(self.bus, require_existing=True):
            result = subprocess.run(self.cli(.1, 'list', '--require-existing'),
                capture_output=True, timeout=5, check=False,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        row = json.loads(result.stdout)
        self.assertEqual(result.returncode, 4, result.stderr)
        self.assertEqual(row['code'], 'BUS_BUSY')
        self.assertIs(row['lock_acquired'], False)
        self.assertIs(row['protected_operation_started'], False)
        self.assertLess(row['elapsed_seconds'], 1)
        self.assertEqual(self.state_bytes(), before)

    def test_token_mismatch_after_lock_is_still_conflict_without_mutation(self):
        before = self.state_bytes()
        result = subprocess.run(self.cli(45, 'release-screen-cas', '--task', 'owned-fixture',
            '--expected-sequence', '2', '--summary', 'must reject'), capture_output=True,
            timeout=5, check=False, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertEqual(json.loads(result.stdout)['code'], 'CAS_CONFLICT')
        self.assertEqual(self.state_bytes(), before)

    def test_keeper_opts_in_and_never_retries_successful_heartbeat(self):
        changed = {**self.task, 'last_sequence': 2}
        event = {'kind': 'heartbeat', 'task_id': 'owned-fixture', 'sequence': 2, 'event_id': 'owned-event'}
        responses = [dict(schema=bus.SCHEMA, ok=True, tasks=[self.task]),
                     dict(schema=bus.SCHEMA, ok=True, task=changed, event=event),
                     dict(schema=bus.SCHEMA, ok=True, tasks=[changed])]
        calls = []
        def run(argv, **kwargs):
            calls.append(argv)
            return subprocess.CompletedProcess(argv, 0, json.dumps(responses.pop(0)).encode(), b'')
        with mock.patch.object(keeper, 'checkout_head', return_value='a' * 40), \
             mock.patch.object(keeper.subprocess, 'run', side_effect=run):
            result = keeper.renew_once(source=SOURCE, bus_dir=self.bus, expected_sha=self.sha,
                task_id='owned-fixture', expected_sequence=1, repo=self.root)
        self.assertEqual(result['sequence'], 2)
        self.assertEqual(len(calls), 3)
        self.assertEqual(sum('heartbeat' in argv for argv in calls), 1)
        self.assertTrue(all(argv[argv.index('--lock-wait-seconds') + 1] == '45' for argv in calls))
        self.assertTrue(all('--require-existing' in argv for argv in (calls[0], calls[2])))

    def test_missing_existing_bus_read_does_not_create_or_claim(self):
        missing = self.root / 'absent'
        result = subprocess.run([BASE_PYTHON, str(SOURCE), '--bus-dir', str(missing),
            '--lock-wait-seconds', '45', 'list', '--require-existing'],
            capture_output=True, timeout=5, check=False)
        self.assertEqual(result.returncode, 3)
        self.assertFalse(missing.exists())

    def test_default_compatibility_limit_and_context_reset(self):
        self.assertEqual(bus._LOCK_WAIT_SECONDS.get(), 10)
        with bus.lock_wait_seconds(45): self.assertEqual(bus._LOCK_WAIT_SECONDS.get(), 45)
        self.assertEqual(bus._LOCK_WAIT_SECONDS.get(), 10)
        for invalid in (-1, 46, float('inf'), float('nan')):
            with self.assertRaises(ValueError):
                with bus.lock_wait_seconds(invalid): pass

    @unittest.skipUnless(sys.platform == 'win32', 'exact msvcrt nonblocking seam')
    def test_deadline_reached_before_next_attempt_never_takes_new_lock(self):
        import msvcrt
        now = [0.0]
        def sleep(seconds): now[0] += seconds
        with mock.patch.object(bus.time, 'monotonic', side_effect=lambda: now[0]), \
             mock.patch.object(bus.time, 'sleep', side_effect=sleep), \
             mock.patch.object(msvcrt, 'locking', side_effect=[OSError(errno.EACCES, 'owned busy'), None]) as lock:
            with bus.lock_wait_seconds(.05):
                with self.assertRaises(bus.BusBusy):
                    with bus.bus_lock(self.bus, require_existing=True):
                        self.fail('deadline-expired lock must not enter protected operation')
        self.assertEqual(lock.call_count, 1)


if __name__ == '__main__': unittest.main()
