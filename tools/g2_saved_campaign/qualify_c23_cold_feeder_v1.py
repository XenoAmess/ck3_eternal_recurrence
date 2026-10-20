"""Three focused RAM-only checks for the finite C23 cold feeder producer."""
import ast
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve().parent
ns = {'__name__': '_C23_source_only_producer', '__file__': str(OWN / 'prepare_c23_cold_feeder_v1.py')}
exec(compile((OWN / 'prepare_c23_cold_feeder_v1.py').read_bytes(), ns['__file__'], 'exec'), ns)
GRAPH, REPORT = ns['build_sources']()
FEEDER = GRAPH[ns['FEEDER']]
TREE = ast.parse(FEEDER)
MACHINE = ns['MACHINE']
T = ns['T']


def require(ok, why):
    if not ok:
        raise ValueError(why)


def selected(names, env):
    return ns['functions'](FEEDER, set(names), env)


class MemoryPath:
    def __init__(self, value, present):
        self.value, self.present = str(value).replace('\\', '/'), present
    def __truediv__(self, name):
        return MemoryPath(self.value + '/' + str(name), self.present)
    def __str__(self):
        return self.value
    def exists(self):
        return self.value in self.present
    def is_file(self):
        return self.exists()


class Focused(unittest.TestCase):
    def test_01_algorithm_inverse_and_full_publish_to_validated_receipt(self):
        require(REPORT['algorithm_inverse_pass'] and REPORT['generated_bytes'] <= 98304, 'inverse/cap')
        dep = (OWN / 'full_lifecycle_timing_v1.py').read_bytes()
        helper = {'__name__': 'source_only_full_clock'}
        exec(compile(dep, '<pinned FULL lifecycle>', 'exec'), helper)
        present, rows, trace = set(), {}, []
        def clock():
            trace.append('mono_start' if trace.count('mono_start') == 0 else 'mono_end')
            return 1000 if trace.count('mono_end') == 0 else 2100
        timer = helper['FullLifecycleTimingV1'](enabled=True, clock=clock)
        def path(seq, parent):
            return parent / ('%04d.json' % seq)
        def read(p):
            return copy.deepcopy(rows[str(p)])
        def atomic(p, row):
            trace.append('atomic_publish')
            present.add(str(p)); rows[str(p)] = copy.deepcopy(row)
        env = {'Path': Path, 'N': MemoryPath('N', present), 'INBOX': MemoryPath('I', present),
            'OUTBOX': MemoryPath('O', present), 'STOP': MemoryPath('STOP', present),
            'request_path': path, 'read': read, 'atomic': atomic, 'next_sequence': lambda: 10483,
            '_FULL_TIMING_V1': timer, 'BASELINE_CYCLES': 4753, 'BASELINE_DATE_RAW': 53144328}
        selected(('request_maximum', 'publish_or_follow', 'result_for'), env)
        self.assertEqual(env['publish_or_follow'](10483), 'published_new_exact_control')
        response = path(10483, env['OUTBOX'])
        present.add(str(response))
        rows[str(response)] = {'request': read(path(10483, env['INBOX'])), 'result': {
            'is_error': False, 'structured_content': {'status': 'bounded_loop_finished',
            'actual_turns': 30, 'cumulative_cycles': 4783, 'actual_end_date_raw': 53274648,
            'next_sequence': 10544}}}
        original_result = env['result_for']
        def validated(*args, **kwargs):
            value = original_result(*args, **kwargs); trace.append('original_result_validated'); return value
        env['result_for'] = validated
        main = next(n for n in TREE.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
        receipt = next(n for n in ast.walk(main) if isinstance(n, ast.Try)
            and len(n.body) == 1 and isinstance(n.body[0], ast.Assign)
            and isinstance(n.body[0].value, ast.Call)
            and isinstance(n.body[0].value.func, ast.Name) and n.body[0].value.func.id == 'result_for')
        outer = next(n for n in ast.walk(main) if isinstance(n, ast.Try) and receipt in n.body)
        body = [receipt, outer.body[1],
            ast.Return(value=ast.Name(id='full_wall_fields', ctx=ast.Load()))]
        fn = ast.FunctionDef(name='timed_result', args=ast.arguments(posonlyargs=[],
            args=[ast.arg(arg='sequence'), ast.arg(arg='first'), ast.arg(arg='previous_cycles')],
            kwonlyargs=[], kw_defaults=[], defaults=[]), body=body, decorator_list=[])
        exec(compile(ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[])), '<exact receipt seams>', 'exec'), env)
        fields = env['timed_result'](10483, True, 4753)
        self.assertEqual(trace, ['mono_start', 'atomic_publish', 'original_result_validated', 'mono_end'])
        self.assertEqual(fields['full_wall_ns'], 1100)
        self.assertEqual(fields['full_timing_origin'], 'new_submission_same_producer')
        rows[str(response)]['result']['structured_content']['cumulative_cycles'] = 4784
        with self.assertRaises(ValueError):
            env['timed_result'](10483, True, 4753)
        rows[str(response)]['result']['structured_content']['cumulative_cycles'] = 4783
        self.assertEqual(timer.after_receipt(10483), {})  # Failed validation discards, with no timestamp.
        self.assertEqual(env['publish_or_follow'](10483), 'following_existing_exact_control')
        self.assertIsNone(timer.after_receipt(10483)['full_wall_ns'])
        rows[str(response)]['result']['is_error'] = True
        with self.assertRaises(ValueError):
            env['timed_result'](10483, True, 4753)
        self.assertEqual(timer.after_receipt(10483), {})

    def test_02_actual_five_refs_and_old_game_are_not_pre_admitted(self):
        frame = {'date_raw': 53274624, 'actor_character_id': 40526,
            'episode_run_id': 'native-40526-1bec95182886', 'native_revision': 1}
        cp = {'status': 'saved', 'date_raw': 53274624}
        game = {'pid': 999999, 'creation_filetime': 134368995759027620,
            'creation_date': 'source-only-fixture', 'old_save_loaded': True, 'load_save_name': 'xar_checkpoint'}
        old = {'status': 'repair_required', 'machine_id': MACHINE, 'last_settled_cycles': 4734,
            'last_settled_date_raw': 53274408, 'start_date_raw': 53144328, 'target_date_raw': 53407128,
            'game_binding': {'pid': 30852, 'creation_date': '20261019160615.902761+000'}}
        def rf(name, count=1, digest='0' * 64):
            return {'path': str(T / name), 'bytes': count, 'sha256': digest}
        refs = {'cold_admission': rf('cold.json'), 'cold_bound': rf('p37-queue/ROOT-C23-NORMAL-COLD-BOUND.json'),
            'actual_Game': rf('ROOT-ACTUAL-GAME-LAUNCH-C23.json'), 'map_admission': rf('map.json'),
            'old_ledger': rf('immutable-predecessor.json', 7921,
                '51ee9a97aecbc0b14560110ddbb3f3fd41fc532f9c2647493efd0e2c3d0247e8')}
        frontier_ref = rf('F99.json', 9089, '312165ea447d2b1e94be0d0b7e0b749a8892f59b1034feb93df90a880f326fce')
        state_ref = rf('state.json', 9054, 'c2c672d520267e6f860dd968ce2ccf1c06faca10fd1cd0552d213929b9a8dac8')
        save_ref = rf('10480-row.json', 10236, '5b0844c484d3ca23ab73e7b6af9db528398fe40eef62648128d3bd4e1578853b')
        source_ref = rf(ns['FEEDER'])
        a = {'schema': 'xar.C23-saved-frontier-feeder/v1', 'machine_id': MACHINE,
            'ordinary_cycle_credit': 0, 'original_actions_replayed': False, 'window_origin_reset': False,
            'review_deadline_utc': ns['DEADLINE'], 'sources': refs, 'feeder_task_spec': rf('SPEC.json'),
            'feeder_task_nonce': 'a' * 32, 'feeder_source': source_ref, 'first_control_sequence': 10483,
            'continue_marker': str(T / 'ROOT-C23-FIRST-FULL-CONTINUE100.json')}
        state = {'actual_saved_checkpoint': cp, 'completed_cycles': 4753, 'counts': {'checkpoint_saved': 74}}
        cold = {'sdk_freeze': rf('freeze.json'), 'source_abort_index': frontier_ref,
            'original_state': state_ref, 'save_response': save_ref,
            'new_Game': {k: game[k] for k in ('pid', 'creation_filetime', 'creation_date')}}
        docs = {
            refs['cold_admission']['path']: cold, refs['cold_bound']['path']: {
                'schema': 'xar.c23.normal-checkpoint-cold-bound/v1', 'machine_id': MACHINE,
                'opening_frame': frame, 'completed_cycles': 4753, 'T0_date_raw': 53144328,
                'new_ordinary_cycle_credit': 0, 'AUTO_or_MET_replayed': False, 'checkpoint': cp},
            refs['actual_Game']['path']: game, refs['map_admission']['path']: {
                'status': 'GREEN', 'reviewer': '/root', 'machine_id': MACHINE,
                'actual_initial_frame': frame, 'game_pid': game['pid'],
                'game_creation_filetime': game['creation_filetime']},
            refs['old_ledger']['path']: old, cold['sdk_freeze']['path']: {},
            frontier_ref['path']: {'completed_cycles': 4753, 'date_raw': 53274624,
                'checkpoint_saved_count': 74, 'next_sequence': 10481, 'new_SDK_pair_published': False},
            state_ref['path']: state, save_ref['path']: {'result': {'structured_content': {'checkpoint': cp}}},
            a['feeder_task_spec']['path']: {'schema': 'xar.interactive-task-owner/v1',
                'role': 'feeder', 'machine_id': MACHINE, 'nonce': 'a' * 32,
                'task_name': 'XARG2ManagedOwner-' + 'a' * 32, 'stage': str(T / ns['LAUNCHER']),
                'stage_sha256': 'fixture-stage', 'stage_args': ['--first-control-sequence', '10483'],
                'stop_path': None, 'env': {}},
        }
        calls = []
        cold_module = ModuleType('root_p37c23_cold_resume')
        def cold_inputs(value):
            calls.append('cold_inputs'); return state, {}, cp, {}, {}
        cold_module.cold_inputs = cold_inputs
        helper_module = ModuleType('root_c23_source_abort_checkpoint_inputs')
        def business(*args):
            calls.append('Source24_full_freeze'); return {'commit': 'fixture-only'}
        def recording(*args):
            calls.append('actual_recording'); return {'binding': {
                'Game_pid': game['pid'], 'Game_creation_filetime': game['creation_filetime']}}
        helper_module.validate_frozen_business = business
        helper_module.current_recording_inputs_v1 = recording
        saved_modules = {k: sys.modules.get(k) for k in (cold_module.__name__, helper_module.__name__)}
        sys.modules[cold_module.__name__] = cold_module; sys.modules[helper_module.__name__] = helper_module
        present = set()
        env = {'N': T, 'Path': Path, 'MARKER': T / 'p37-queue/ROOT-C23-NORMAL-COLD-BOUND.json',
            'CONTINUITY_WINDOW': T.parent / 'ROOT-CONTINUITY-WINDOW.json', '__file__': str(T / ns['FEEDER']),
            'datetime': datetime, 'timezone': timezone, 'sha': lambda p: 'fixture-stage',
            'c23_checked_file': lambda *args: copy.deepcopy(a),
            'c23_checked': lambda r, limit=65536: copy.deepcopy(docs[r['path']]),
            'c23_ref': lambda p: source_ref, 'next_sequence': lambda: 10483,
            'request_path': lambda seq, root: MemoryPath(str(root) + '/' + str(seq), present),
            'INBOX': 'I', 'OUTBOX': 'O'}
        selected(('c23_require', 'admitted'), env)
        try:
            value = env['admitted']()
            self.assertEqual(value['old_ledger']['last_settled_cycles'], 4734)
            self.assertEqual(calls, ['cold_inputs', 'Source24_full_freeze', 'actual_recording'])
            hold = a['sources']; a['sources'] = {}
            with self.assertRaises(ValueError):
                env['admitted']()
            a['sources'] = hold
            docs[refs['actual_Game']['path']]['creation_filetime'] = 134368995759027619
            with self.assertRaises(ValueError):
                env['admitted']()
        finally:
            for key, value in saved_modules.items():
                if value is None: sys.modules.pop(key, None)
                else: sys.modules[key] = value

    def test_03_saved_alignment_and_single_task_hold_missing_wrong_correct(self):
        ledger = {'__name__': 'source_only_ledger'}
        exec(compile(GRAPH[ns['LEDGER']], '<unchanged ledger plus finite branch>', 'exec'), ledger)
        old_path = T.parent / 'ROOT-CONTINUITY-WINDOW.json'
        raw = old_path.read_bytes()
        require(len(raw) == 7921 and hashlib.sha256(raw).hexdigest() ==
            '51ee9a97aecbc0b14560110ddbb3f3fd41fc532f9c2647493efd0e2c3d0247e8', 'actual predecessor changed')
        old = json.loads(raw); original = copy.deepcopy(old)
        src = {'predecessor': {'sha256': '51ee9a97aecbc0b14560110ddbb3f3fd41fc532f9c2647493efd0e2c3d0247e8'},
            'frontier': {'sha256': '312165ea447d2b1e94be0d0b7e0b749a8892f59b1034feb93df90a880f326fce'},
            'state': {'sha256': 'c2c672d520267e6f860dd968ce2ccf1c06faca10fd1cd0552d213929b9a8dac8'},
            'SAVE10480': {'sha256': '5b0844c484d3ca23ab73e7b6af9db528398fe40eef62648128d3bd4e1578853b'}}
        details = {'machine_id': MACHINE, 'evidence_id': 'source-only-fixture', 'source': src,
            'old_ledger': old, 'game': {'pid': 999999, 'creation_date': 'source-only-fixture',
                'creation_filetime': 134368995759027620}, 'frame': {'date_raw': 53274624,
                'actor_character_id': 40526, 'episode_run_id': 'native-40526-1bec95182886'}}
        updated = ledger['transition'](old, 'C23_saved_frontier_aligned', details)
        changed = {'status', 'game_binding', 'latest_binding', 'last_settled_cycles', 'last_settled_date_raw',
            'cold_handoff_count', 'previous_interruption', 'C23_saved_frontier_alignment'}
        self.assertEqual({k:v for k,v in old.items() if k not in changed},
            {k:v for k,v in updated.items() if k not in changed})
        self.assertEqual(old, original)
        self.assertEqual(updated['last_settled_cycles'], 4753)
        self.assertEqual(updated['C23_saved_frontier_alignment']['ordinary_cycle_credit'], 0)
        bad = copy.deepcopy(details); bad['game']['creation_filetime'] -= 1
        with self.assertRaises(ValueError): ledger['transition'](old, 'C23_saved_frontier_aligned', bad)
        present, status_calls, sleeps = set(), [], []
        root = MemoryPath('N', present); stop = MemoryPath('STOP', present)
        marker = MemoryPath('CONTINUE', present)
        v = {'machine_id': MACHINE, 'feeder_task_nonce': 'a' * 32, 'feeder_task_spec': {'sha256': 'S'},
            'feeder_source': {'sha256': 'F'}, 'review_deadline_utc': ns['DEADLINE'], 'continue_marker': marker}
        result = {'actual_end_date_raw': 53274648, 'cumulative_cycles': 4783, 'next_sequence': 10544}
        fields = {'full_timing_control_sequence': 10483, 'full_timing_clock': 'monotonic_ns',
            'full_timing_origin': 'new_submission_same_producer', 'full_submit_monotonic_ns': 1000,
            'full_receipt_validated_monotonic_ns': 2100, 'full_wall_ns': 1100}
        env = {'datetime': datetime, 'timezone': timezone, 'N': root, 'STOP': stop,
            'Path': lambda p: p, 'INBOX': root / 'I', 'request_path': lambda seq, p: p / str(seq),
            'c23_ref': lambda p: {'path': str(p), 'bytes': 1, 'sha256': 'fixture-only'},
            'status': lambda *args, **kwargs: status_calls.append((args, kwargs))}
        def sleep(delay):
            sleeps.append(delay); present.add(str(stop))
        env['time'] = SimpleNamespace(sleep=sleep)
        selected(('c23_require', 'c23_gate_expected', 'c23_accept_continue', 'c23_first_batch_hold'), env)
        expected = env['c23_gate_expected'](v, 10483, result, 'response', fields)
        self.assertFalse(env['c23_first_batch_hold'](v, 10483, result, 'response', fields))
        self.assertEqual(len(sleeps), 1)
        self.assertEqual(status_calls[0][0][0], 'root_review_hold')
        present.remove(str(stop)); present.add(str(marker))
        note = {'schema': 'xar.C23-first-FULL-root-continue/v1', 'reviewer': '/root',
            'reviewed_at_utc': datetime.now(timezone.utc).isoformat(), 'first_batch': expected}
        self.assertTrue(env['c23_accept_continue'](note, expected))
        bad = copy.deepcopy(note); bad['first_batch']['feeder_task_nonce'] = 'b' * 32
        with self.assertRaises(ValueError): env['c23_accept_continue'](bad, expected)
        wrong_origin = dict(fields, full_timing_origin='submission_not_observed')
        with self.assertRaises(ValueError):
            env['c23_gate_expected'](v, 10483, result, 'response', wrong_origin)
        # Inject the already frozen expected first-batch tuple to test the
        # once-only hold return; the real function creates it exactly once.
        env['c23_gate_expected'] = lambda *args: expected
        env['c23_checked_file'] = lambda *args: note
        self.assertTrue(env['c23_first_batch_hold'](v, 10483, result, 'response', fields))
        main = next(n for n in TREE.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
        gates = [n for n in ast.walk(main) if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name) and n.func.id == 'c23_first_batch_hold']
        self.assertEqual(len(gates), 1)

    def test_04_strict_manually_reviewed_deadline_binding(self):
        newer = '2026-10-20T03:48:56.993837Z'
        older = '2026-10-20T01:48:56.993837Z'
        self.assertEqual(ns['DEADLINE'], newer)
        self.assertIn(newer, ns['ADMITTED'])
        self.assertNotIn(older, ns['ADMITTED'])
        admission = {'schema': 'xar.C23-saved-frontier-feeder/v1', 'machine_id': MACHINE,
            'ordinary_cycle_credit': 0, 'original_actions_replayed': False,
            'window_origin_reset': False, 'review_deadline_utc': newer, 'sources': {}}
        env = {'N': T, 'c23_checked_file': lambda *args: copy.deepcopy(admission)}
        selected(('c23_require', 'admitted'), env)
        with self.assertRaisesRegex(ValueError, 'all five actual cold references required'):
            env['admitted']()  # The exact new deadline passes, then missing actual refs still reject.
        admission['review_deadline_utc'] = older
        with self.assertRaisesRegex(ValueError, 'not an actual cold admission'):
            env['admitted']()
        class FixedClock:
            current = datetime(2026, 10, 20, 2, 0, tzinfo=timezone.utc)
            @classmethod
            def now(cls, tz): return cls.current
            fromisoformat = staticmethod(datetime.fromisoformat)
        env = {'datetime': FixedClock, 'timezone': timezone}
        selected(('c23_require', 'c23_accept_continue'), env)
        expected = {'review_deadline_utc': newer, 'hold_started_at_utc': '2026-10-20T01:59:00+00:00'}
        marker = {'schema': 'xar.C23-first-FULL-root-continue/v1', 'reviewer': '/root',
            'reviewed_at_utc': '2026-10-20T02:00:00+00:00', 'first_batch': expected}
        self.assertTrue(env['c23_accept_continue'](marker, expected))
        wrong = copy.deepcopy(marker); wrong['first_batch']['review_deadline_utc'] = older
        with self.assertRaises(ValueError): env['c23_accept_continue'](wrong, expected)
        expired = dict(expected, review_deadline_utc=older)
        wrong['first_batch'] = expired
        with self.assertRaises(ValueError): env['c23_accept_continue'](wrong, expired)
        FixedClock.current = datetime.fromisoformat(newer.replace('Z', '+00:00'))
        with self.assertRaises(ValueError): env['c23_accept_continue'](marker, expected)


def main():
    require(sys.argv[1:] in ([], ['--deadline-only']), 'only the explicit finite deadline check selector is accepted')
    suite = (unittest.TestSuite([Focused('test_04_strict_manually_reviewed_deadline_binding')])
        if sys.argv[1:] else unittest.defaultTestLoader.loadTestsFromTestCase(Focused))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    owned = [OWN / n for n in ('prepare_c23_cold_feeder_v1.py', 'qualify_c23_cold_feeder_v1.py', 'c23_cold_feeder_plan_v1.json')]
    source_rows = [{'path': str(p.resolve()), 'bytes': p.stat().st_size,
        'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in owned]
    require(sum(r['bytes'] for r in source_rows) <= 65536, 'source64KiB hard cap exceeded')
    metadata = {'path': str(T.parent / 'ROOT-CONTINUITY-WINDOW.json'), 'bytes': 7921,
        'sha256': '51ee9a97aecbc0b14560110ddbb3f3fd41fc532f9c2647493efd0e2c3d0247e8'}
    upper = REPORT['logical_participating_upper_bytes'] + 3 * (sum(r['bytes'] for r in source_rows) + metadata['bytes'])
    require(upper <= 2621440, 'complete participation including own three leaves exceeds cap')
    print(json.dumps({'schema': 'xar.C23-cold-feeder-focused-source-only/v1', 'machine_id': MACHINE,
        'observed_at_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'SOURCE_ONLY_PASS' if result.wasSuccessful() else 'SOURCE_ONLY_RED',
        'focused_checks': result.testsRun, 'sources': source_rows, 'source_gross_bytes': sum(r['bytes'] for r in source_rows),
        'generated': REPORT['generated'], 'generated_bytes': REPORT['generated_bytes'],
        'qualification_only_metadata_input': metadata,
        'logical_participating_payload_bytes': REPORT['logical_participating_payload_bytes'] + sum(r['bytes'] for r in source_rows) + metadata['bytes'],
        'logical_participating_upper_bytes': upper, 'actual_resident_peak_measured': False,
        'source_payload_ceiling_not_process_RAM_measurement': True,
        'runtime_H_or_performance_credit': 0, 'outputs_materialized': False,
        'scratch_bytes': 0, 'D_writes': 0, 'Task_Game_SDK_Native_OBS_desktop_calls': 0}, separators=(',', ':')))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
