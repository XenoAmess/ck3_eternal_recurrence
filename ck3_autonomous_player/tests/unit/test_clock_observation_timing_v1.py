"""Focused offline profile tests; Win32/Native calls always use fakes."""
from pathlib import Path
import ast
import copy
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[1] / 'src/xar_autoplayer/bridge/native_driver.py'
sys.path.insert(0, str(HERE.parents[1] / 'src'))
import xar_autoplayer.bridge.army_query_timing as timing
from xar_autoplayer.bridge import clock_observation_timing_v1 as profile

UNPROFILE_HUNKS = [('            clock_wait_timing = start_army_timing("driver.exact_clock_resume_to_paused")\n', '            from .clock_observation_timing_v1 import (\n                start_clock_observation_v1, finish_clock_observation_v1,\n            )\n            clock_observation = start_clock_observation_v1(self, current)\n            clock_wait_timing = start_army_timing("driver.exact_clock_resume_to_paused")\n'), ('            finally:\n                finish_army_timing(clock_wait_timing, step="life-advance",\n', '            finally:\n                finish_clock_observation_v1(self, clock_observation, current)\n                finish_army_timing(clock_wait_timing, step="life-advance",\n'), ('            changed = self.take_internal_semantic_snapshot()\n            return changed\n        finally:\n            finish_army_timing(\n                timing, step="life-advance", before_snapshot=before_snapshot,\n', '            changed = self.take_internal_semantic_snapshot()\n            if getattr(self, "_exact_clock_observation_v1", None) is not None:\n                from .clock_observation_timing_v1 import observe_clock_snapshot_v1\n                observe_clock_snapshot_v1(self, changed)\n            return changed\n        finally:\n            finish_army_timing(\n                timing, step="life-advance", before_snapshot=before_snapshot,\n')]

def unprofiled_source(raw):
    text = raw.decode('utf-8').replace('\r\n', '\n')
    for before, after in UNPROFILE_HUNKS:
        assert text.count(after) == 1
        text = text.replace(after, before, 1)
    return text.encode('utf-8')


class Cpu:
    instances = []
    def __init__(self, pid):
        self.pid, self.calls, self.closed = pid, 0, False
        self.instances.append(self)
    def sample(self):
        self.calls += 1
        return {'creation_filetime': 777, 'kernel_100ns': self.calls * 100,
                'user_100ns': self.calls * 200, 'host_monotonic_ms': 1390625000 + self.calls}
    def close(self):
        self.closed = True


def fixture():
    return json.loads((HERE / 'fixtures/clock_actual_sem65_projection.json').read_text(encoding='utf-8'))['projection']


def rows(path):
    if not path.exists(): return []
    return [row for line in path.read_text(encoding='utf-8').splitlines()
            if (row := json.loads(line)).get('schema') == 'xar.ck3.exact-clock-observation.v1']


class ClockTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='clock-profile-', dir=None)
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'timings.jsonl'
        Cpu.instances.clear()

    def test_actual_cached_fields_are_allowlisted_and_missing_native_time_is_null(self):
        s = fixture(); before = copy.deepcopy(s)
        result = profile.cached_clock_fields_v1(s)
        self.assertEqual(result['game_pid'], 100984)
        self.assertEqual(result['observer_last_read_ms'], 0)
        self.assertEqual(result['owner_pump_epochs'], 233883)
        self.assertEqual(result['heartbeat_sequence'], 9760)
        self.assertIsNone(result['native_snapshot_monotonic_ms'])
        self.assertEqual(s, before)
        self.assertNotIn('diagnostics', result)
        self.assertNotIn('history', result)
        self.assertLess(len(json.dumps(result)), 1500)

    def test_first_date_and_pause_same_frame_share_one_cpu_read_and_do_not_repeat(self):
        s = fixture(); s['date_raw'] = 53411184
        recorder = profile.ClockObservationV1(str(self.path), s, cpu_factory=Cpu)
        advanced = copy.deepcopy(s); advanced['date_raw'] += 24
        recorder.observe(advanced); recorder.observe(advanced); recorder.close(advanced)
        actual = rows(self.path)
        self.assertEqual([r['phase'] for r in actual],
                         ['resume_begin', 'first_date_seen', 'paused_observed', 'resume_to_paused_final'])
        self.assertEqual(actual[1]['cpu_user_100ns'], actual[2]['cpu_user_100ns'])
        self.assertEqual(actual[2]['cpu_delta_from_previous_phase_100ns'], 0)
        self.assertEqual(Cpu.instances[0].calls, 3)
        self.assertTrue(Cpu.instances[0].closed)

    def test_pid_mismatch_never_reads_a_different_process(self):
        s = fixture(); recorder = profile.ClockObservationV1(str(self.path), s, cpu_factory=Cpu)
        other = copy.deepcopy(s); other['date_raw'] += 24
        other['diagnostics']['bridge_pid'] = 1234
        other['diagnostics']['hello']['pid'] = 1234
        recorder.observe(other); recorder.close(other)
        self.assertEqual(Cpu.instances[0].calls, 1)
        self.assertIsNone(rows(self.path)[1]['process_creation_filetime'])
        self.assertIsNone(rows(self.path)[1]['cpu_delta_from_resume_100ns'])
        invalid = copy.deepcopy(s); invalid['diagnostics']['hello']['pid'] = True
        self.assertIsNone(profile._bound_pid(invalid))

    def test_cpu_unavailable_does_not_create_a_late_false_zero_baseline(self):
        class MissingFirst(Cpu):
            def sample(self):
                if self.calls == 0:
                    self.calls += 1
                    return None
                return super().sample()
        s = fixture(); recorder = profile.ClockObservationV1(str(self.path), s, cpu_factory=MissingFirst)
        s['date_raw'] += 24; recorder.observe(s); recorder.close(s)
        self.assertTrue(all(r['cpu_delta_from_resume_100ns'] is None for r in rows(self.path)))

    def test_creation_change_or_counter_regression_cannot_produce_cpu_delta(self):
        class Changed(Cpu):
            def sample(self):
                result = super().sample()
                result['creation_filetime'] += self.calls
                return result
        s = fixture(); recorder = profile.ClockObservationV1(str(self.path), s, cpu_factory=Changed)
        s['date_raw'] += 24; recorder.observe(s); recorder.close(s)
        self.assertEqual(rows(self.path)[0]['cpu_delta_from_resume_100ns'], 0)
        self.assertTrue(all(r['cpu_delta_from_resume_100ns'] is None for r in rows(self.path)[1:]))

    def test_real_cpu_sampler_checks_creation_with_mocked_win32_calls_only(self):
        import ctypes
        from ctypes import wintypes
        class Kernel:
            def __init__(self): self.creation, self.closed = 123, []
            def GetProcessTimes(self, handle, *outputs):
                self_handle = handle
                assert self_handle == 99
                for output, value in zip(outputs, (self.creation, 0, 0x100000002, 0x200000003)):
                    output._obj.dwHighDateTime = value >> 32
                    output._obj.dwLowDateTime = value & 0xffffffff
                return True
            def GetTickCount64(self): return 300
            def CloseHandle(self, handle): self.closed.append(handle)
        sampler = profile._BoundProcessCpuV1.__new__(profile._BoundProcessCpuV1)
        sampler.pid, sampler.handle, sampler.creation = 100984, 99, None
        sampler.ctypes, sampler.wintypes, sampler.kernel32 = ctypes, wintypes, Kernel()
        observed = sampler.sample()
        self.assertEqual(observed['kernel_100ns'], 0x100000002)
        self.assertEqual(observed['user_100ns'], 0x200000003)
        sampler.kernel32.creation = 456
        self.assertIsNone(sampler.sample())
        sampler.close(); sampler.close()
        self.assertEqual(sampler.kernel32.closed, [99])

    def test_disabled_profile_has_no_cpu_or_output_and_io_failure_cannot_raise(self):
        driver = types.SimpleNamespace()
        with patch.dict(os.environ, {}, clear=True), patch.object(profile, 'ClockObservationV1') as factory:
            self.assertIsNone(profile.start_clock_observation_v1(driver, fixture()))
            factory.assert_not_called()
        bad = Path(self.tmp.name) / 'missing' / 'cannot-write.jsonl'
        recorder = profile.ClockObservationV1(str(bad), fixture(), cpu_factory=Cpu)
        recorder.close(fixture())
        self.assertTrue(Cpu.instances[0].closed)
        self.assertFalse(bad.exists())

    def _clock_class(self, raw):
        tree = ast.parse(raw.decode('utf-8'))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'NativeHeadlessGameplayDriver')
        selected = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name in
                    ('_advance_exact_day_with_sentinel', '_wait_for_life_advance_snapshot', '_wait_for_life_advance_change')]
        unit = ast.Module(body=[ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0),
                               ast.ClassDef(name='ActualClock', bases=[], keywords=[], body=selected, decorator_list=[])], type_ignores=[])
        ast.fix_missing_locations(unit)
        scope = {'__package__': 'xar_autoplayer.bridge', 'time': __import__('time'),
                 'start_army_timing': timing.start_army_timing, 'finish_army_timing': timing.finish_army_timing,
                 '_date_raw': lambda s, label: s['date_raw'], '_validate_revision': lambda r, label: None,
                 '_positive_seconds': lambda t, label: t,
                 '_TACTICAL_DAILY_SENTINEL_ARM_PREFIX': 'research-arm-tactical-daily-sentinel-v1-',
                 '_TACTICAL_DAILY_SENTINEL_ARM_CAPABILITY': 'arm', '_TACTICAL_DAILY_SENTINEL_STATUS_STEP': 'research-query-tactical-daily-sentinel-v1',
                 '_TACTICAL_DAILY_SENTINEL_STATUS_CAPABILITY': 'query', '_TACTICAL_DAILY_SENTINEL_CANCEL_PREFIX': 'cancel-',
                 '_TACTICAL_DAILY_SENTINEL_CANCEL_CAPABILITY': 'cancel',
                 '_normalize_tactical_daily_sentinel_status': lambda s: copy.deepcopy(s),
                 '_validate_tactical_daily_sentinel_arm': lambda *a, **k: None,
                 '_validate_tactical_daily_sentinel_stop': lambda *a, **k: None,
                 '_life_advance_new_modal_hint': lambda *a: None,
                 'BridgeUnavailableError': RuntimeError}
        exec(compile(unit, str(SOURCE), 'exec'), scope)
        return scope['ActualClock']

    def _run_production_clock(self, raw, *, fail_wait=False):
        actual = self._clock_class(raw)
        s = fixture(); s.update(date_raw=53411184, paused=True, speed=5, revision=2, native_revision=8, episode_run_id='actual-P26')
        frames = [copy.deepcopy(s) for _ in range(4)]
        frames[1].update(paused=False, revision=3, native_revision=9)
        frames[2].update(date_raw=53411208, paused=False, revision=4, native_revision=10)
        frames[3].update(date_raw=53411208, paused=True, revision=6, native_revision=12)
        class Driver(actual):
            command_timeout_seconds = life_advance_timeout_seconds = 30
            def __init__(self):
                self.index = 0; self.commands = []; self.pauses = 0; self.state = self
            def take_internal_semantic_snapshot(self): return frames[self.index]
            def capabilities(self): return {'snapshot': True}
            def wait_for_public_change(self, *args):
                if fail_wait: raise RuntimeError('original-native-wait-failure')
                self.index += 1
            def _execute_primitive_step(self, step, **kwargs):
                self.commands.append(step)
                return {'accepted': True, 'status': 'available', 'step': step, 'tactical_daily_sentinel': {'generation': 1}}
            def _execute_composite_primitive(self, step, current):
                return self._execute_primitive_step(step)
            def _resume_life_advance(self, current, actions, **kwargs):
                result = self._execute_primitive_step('resume-map'); actions.append({'step': 'resume-map', 'result': result})
                return self._wait_for_life_advance_snapshot(current, lambda s: s['paused'] is False, timeout_seconds=30)
            def _pause_life_advance(self, current, actions): self.pauses += 1; return current
        driver = Driver(); actions = []
        try:
            result = driver._advance_exact_day_with_sentinel(frames[0], speed=5, actions=actions)
            return driver, actions, result
        except Exception as error:
            return driver, actions, error

    def test_actual_three_production_clock_methods_preserve_commands_and_return(self):
        modified = SOURCE.read_bytes(); base = unprofiled_source(modified)
        # These phase frames retain the actual P26 46/47 raw dates/revisions;
        # the Native/OS boundaries and clock scheduling are explicitly fakes.
        with patch.dict(os.environ, {}, clear=True):
            before = self._run_production_clock(base)
        with patch.dict(os.environ, {'XAR_CK3_ARMY_TIMING_JSONL': str(self.path)}), \
             patch.object(profile.ClockObservationV1, '__init__', self._fake_init):
            after = self._run_production_clock(modified)
        self.assertEqual(before[1:], after[1:])
        self.assertEqual(before[0].commands, after[0].commands)
        self.assertEqual(after[0].index, 3)
        self.assertIsNone(after[0]._exact_clock_observation_v1)
        self.assertEqual([r['phase'] for r in rows(self.path)],
                         ['resume_begin', 'resume_observed', 'first_date_seen', 'paused_observed', 'resume_to_paused_final'])
        self.assertEqual(Cpu.instances[-1].calls, 5)
        self.assertTrue(Cpu.instances[-1].closed)

    @staticmethod
    def _fake_init(self, path, snapshot):
        ClockTests._original_init(self, path, snapshot, cpu_factory=Cpu)

    def test_production_clock_exception_and_cleanup_are_unchanged(self):
        modified = SOURCE.read_bytes(); base = unprofiled_source(modified)
        with patch.dict(os.environ, {}, clear=True):
            before = self._run_production_clock(base, fail_wait=True)
        with patch.dict(os.environ, {'XAR_CK3_ARMY_TIMING_JSONL': str(self.path)}), \
             patch.object(profile.ClockObservationV1, '__init__', self._fake_init):
            after = self._run_production_clock(modified, fail_wait=True)
        self.assertEqual(str(before[2]), str(after[2]))
        self.assertEqual(str(after[2]), 'original-native-wait-failure')
        self.assertEqual(before[1], after[1])
        self.assertEqual(before[0].commands, after[0].commands)
        self.assertEqual(before[0].pauses, after[0].pauses)
        self.assertTrue(Cpu.instances[-1].closed)
        self.assertNotIn('paused_observed', [r['phase'] for r in rows(self.path)])


ClockTests._original_init = profile.ClockObservationV1.__init__
if __name__ == '__main__':
    unittest.main(verbosity=2)
