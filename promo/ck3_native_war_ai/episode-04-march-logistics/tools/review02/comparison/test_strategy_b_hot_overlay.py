"""New offline wiring checks; no old normal-day/strategy matrix is repeated."""
from contextlib import redirect_stdout
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

FILE = Path(__file__).resolve()
HERE = FILE.parent
REPO = FILE.parents[6]
ROOT = REPO
SHARED = HERE.parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    out = importlib.util.module_from_spec(spec); spec.loader.exec_module(out)
    return out


A = module('B_hot_argv_test_subject', HERE / 'strategy_b_run_argv.py')
B = module('B_hot_stages_test_subject', HERE / 'strategy_b_stages.py')


class Wiring(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.now = datetime(2026, 10, 17, 1, 0, tzinfo=timezone.utc)
        self.source = '611bc985ae95f477dd7314df11f8602cd1e595f3'
        self.total = 512 * 1024 * 1024
        self.machine = 'unit-machine'
        self.run = self.machine + '--vanilla--R0199'
        self.runtime = {'pid': 11, 'process_create_time_100ns': 22, 'generation': 33,
                        'actor': 44, 'episode': 'unit-episode'}
        self.guard_path = SHARED / 'runtime_binding.py'
        self.plan = {'status': 'frozen', 'build': {'source_head': self.source},
                     'normal_save': {'sha256': 'b' * 64}}
        self.arm = {'label': 'B', 'loaded_save_sha256': 'b' * 64,
                    'runtime': {'source_head': self.source, 'machine_id': self.machine, 'pid': 11,
                        'process_create_time_100ns': 22, 'connection_generation': 33,
                        'player_character_id': 44, 'episode': 'unit-episode'},
                    'cold_start': {'strategy_army_ids': [777]}}
        self.context = {'source_head': self.source, 'machine_id': self.machine,
            'identity': {'machine_id': self.machine, 'run_id': self.run, 'sequence': 199, 'mod_key': 'vanilla'}}
        self.proof = {'source_head': self.source, 'machine_id': self.machine, 'run_id': self.run,
            'pid': 11, 'process_creation_filetime_100ns': 22, 'connection_generation': 33,
            'actual_runtime_character_full_id': 44, 'episode_run_id': 'unit-episode'}
        state = self.base / 'state-a02'; state.mkdir()
        prepared = {'machine_id': self.machine, 'assets_root': str(self.base.resolve()), 'state_dir': str(state.resolve()),
                    'checkpoint': {'source': {'save': {'sha256': 'b' * 64}}}}
        self.prepared = self.put('prepared.json', prepared)
        self.proof['proof_chain'] = [{'files': [self.prepared]}]
        cap = {'admitted': True, 'machine_id': self.machine, 'source_head': self.source, 'run_id': self.run,
            'scene_root': str(self.base.resolve()), 'policy_version': '1.0.0', 'root_atomic_adoption_required': False,
            'root_adopted_at_utc': '2026-10-17T00:00:00+00:00', 'quota_review_at_utc': '2026-10-17T02:00:00+00:00',
            'source_binding': {'new_clean_integrated_source_head': self.source},
            'component_ceiling_bytes': {'driver': self.total}, 'new_scene_aggregate_bytes': self.total}
        self.cap = self.put('capacity.json', cap)
        operation = {'schema': 'xar.e04.live-operation-binding.v1', 'operation_id': 'unit-B',
            'machine_id': self.machine, 'source_head': self.source, 'scene_root': str(self.base.resolve()),
            'run_id': self.run, 'run_sequence': 199, 'runtime': self.runtime, 'normal_save_sha256': 'b' * 64,
            'max_runtime_total_bytes': self.total, 'created_at_utc': '2026-10-17T00:30:00+00:00',
            'deadline_utc': '2026-10-17T02:00:00+00:00', 'capacity_admission': self.cap,
            'guard_sha256': A.pin(self.guard_path)['sha256']}
        self.binding = {'repo': str(REPO), 'overlay_root': str(REPO), 'python': sys.executable,
            'evidence_root': str(self.base), 'case_id': 'unit-B', 'plan': self.put('plan.json', self.plan),
            's0_arm': self.put('arm.json', self.arm), 'context': self.put('context.json', self.context),
            'runtime_proof': self.put('proof.json', self.proof), 'request_helper': self.put('request.py', '# unit only\n'),
            'module_pins': self.put('modules.json', {}), 'live_binding': self.put('live.json', operation),
            'prepared': self.prepared,
            'code_overrides': {'root-relay': A.pin(SHARED / 'split_merge/root_relay.py'),
                               'comparison-core': A.pin(SHARED / 'comparison/r10_compare.py')}}

    def put(self, name, value):
        path = self.base / name
        path.write_text(value if type(value) is str else json.dumps(value), encoding='utf-8')
        return A.pin(path)

    def build(self, stage='baseline', **kw):
        return A.build(self.binding, stage, 'unit-a01', now_utc=self.now, **kw)

    def test_argv_external_code_current_pure_guard_and_explicit_live_tuple(self):
        out = self.build(); argv = out['argv']; code = out['code_pins']
        self.assertEqual(code['self']['path'], str((HERE / 'strategy_b_stages.py').resolve()))
        self.assertEqual(code['normal-stages']['path'], str((HERE / 'strategy_b_normal_stages.py').resolve()))
        self.assertEqual(code['root-relay']['path'], str((SHARED / 'split_merge/root_relay.py').resolve()))
        self.assertEqual(code['next-adapter']['path'], str((REPO / A.PREFIX / 'comparison/strategy_b_next.py').resolve()))
        self.assertEqual(code['comparison-core']['path'], str((SHARED / 'comparison/r10_compare.py').resolve()))
        self.assertEqual(argv[argv.index('--army-id') + 1], '777')
        self.assertEqual(argv[argv.index('--run-sequence') + 1], '199')
        self.assertEqual(argv[argv.index('--live-binding') + 1], self.binding['live_binding']['path'])
        self.assertEqual(argv[argv.index('--runtime-capacity-admission') + 1], self.cap['path'])
        self.assertFalse(out['game_or_relay_request_submitted'])
        bad = dict(self.proof, pid=99); self.binding['runtime_proof'] = self.put('foreign-proof.json', bad)
        with self.assertRaisesRegex(ValueError, 'live process/create-time'):
            self.build()
        self.binding['runtime_proof'] = self.put('proof.json', self.proof)
        old = self.binding.pop('live_binding')
        with self.assertRaisesRegex(ValueError, 'explicit live_binding'):
            self.build()
        self.binding['live_binding'] = old
        self.binding['max_evidence_file_bytes'] = 32 * 1024 * 1024
        with self.assertRaisesRegex(ValueError, 'explicit evidence capacity'):
            self.build()

    def test_real_main_external_guard_path_and_budget_order_before_stage(self):
        previous = self.put('previous.json', {'unit_previous': True})
        argv = self.build('advance-stage-day', previous=[previous['path'], previous['sha256']])['argv'][5:]
        calls = []
        live = NS(machine=self.machine, deadline=self.now,
            live_operation_guard=NS(capacity_pin=self.cap, binding={'max_runtime_total_bytes': self.total}))
        def guard_module(path, name):
            calls.append(('guard', Path(path).resolve()))
            self.assertEqual(Path(path).resolve(), self.guard_path.resolve())
            self.assertEqual(Path(path).resolve().parent, HERE.parent)
            return A.module(path)
        def relay(args):
            calls.append(('relay', args)); live.a = args
            self.assertEqual(args.live_binding, Path(self.binding['live_binding']['path']))
            self.assertEqual(args.source_head, self.source); self.assertEqual(args.run_sequence, 199)
            return live
        root = NS(__file__=str(SHARED / 'split_merge/root_relay.py'), pin=A.pin,
            load=lambda p: json.loads(Path(p).read_bytes()), Relay=relay, module=guard_module, MACHINE='historical-unit')
        def evidence(path, **kw):
            calls.append(('evidence', kw)); return NS(root=Path(path))
        def budget(options, **kw):
            calls.append(('budget', options, kw))
            self.assertEqual(options['runtime_capacity_admission'], [self.cap['path'], self.cap['sha256']])
            return NS(bind_live=lambda live, **opts: calls.append(('bound', opts)))
        core = NS(Evidence=evidence, runtime_total_budget=budget)
        nxt = NS(c=core, b=NS(recipe=lambda p, e: calls.append(('recipe', p)), c=core))
        class Stages:
            def __init__(_, *args, **kw):
                calls.append(('stages', kw))
            def run(_, stage):
                calls.append(('run', stage))
                return self.put('result.json', {'status': 'UNIT_WIRING_ONLY'})
        def reviewed(path, name, sha):
            return root if name == 'reviewed_r09_root_relay_for_B' else core if name == 'r10_compare' else nxt
        with patch.object(B, 'reviewed_module', reviewed), patch.object(B, 'BStages', Stages), patch.dict(sys.modules), redirect_stdout(io.StringIO()):
            self.assertEqual(B.main(argv), 0)
        labels = [c[0] for c in calls]
        self.assertLess(labels.index('recipe'), labels.index('relay'))
        self.assertLess(labels.index('guard'), labels.index('budget'))
        self.assertLess(labels.index('bound'), labels.index('stages'))
        self.assertEqual(calls[-1], ('run', 'advance-stage-day'))
        self.assertEqual(next(c[1]['expected_machine_ids'] for c in calls if c[0] == 'evidence'), {self.machine})
        without_prepared = list(argv)
        index = without_prepared.index('--prepared')
        del without_prepared[index:index + 4]
        with patch.object(B, 'reviewed_module', side_effect=AssertionError('must reject before Relay loading')):
            with self.assertRaisesRegex(RuntimeError, 'requires actual prepared'):
                B.main(without_prepared)
            partial = without_prepared + ['--prepared', self.binding['prepared']['path']]
            with self.assertRaisesRegex(RuntimeError, 'PATH and SHA'):
                B.main(partial)

    def test_actual_stage_dispatch_keeps_normal_claim_and_arrival_helper_boundaries(self):
        st = B.BStages.__new__(B.BStages)
        helper_pin = A.pin(HERE / 'strategy_b_normal_stages.py')
        arrival = self.put('arrival.json', {'unit_actual_arrival_standin': True})
        common_path = REPO / A.PREFIX / 'comparison/strategy_b_common_horizon.py'
        a = NS(normal_stages=Path(helper_pin['path']), normal_stages_sha256=helper_pin['sha256'],
            move_army_id=777, common_horizon=common_path, common_horizon_sha256=A.pin(common_path)['sha256'],
            arrival_arm=Path(arrival['path']), arrival_arm_sha256=arrival['sha256'], days=1, day_start_raw=123)
        st.live = NS(a=a); st.r = NS(pin=A.pin); st.state = {}; st.pending_packet = None
        st.write = lambda status, **kw: {'status': status, **kw}
        observed = []
        normal = NS(move=lambda s, aid, post=False: observed.append(('move', aid, post)),
                    day=lambda s, recovery=False: observed.append(('day', recovery)))
        common = NS(advance=lambda s, ref, days, recovery_start=None:
            observed.append(('common', ref, days, recovery_start)))
        with patch.object(B, 'reviewed_module', lambda p, n, sha: common if n == 'B_reviewed_common_horizon' else normal):
            st.run('move-stage-post'); st.run('recover-stage-day'); st.run('recover-common-horizon-day')
            self.assertEqual(observed, [('move', 777, True), ('day', True), ('common', arrival, 1, 123)])
            self.assertEqual(st.state['normal_stage_helper'], helper_pin)
            st.state['normal_pending_day'] = {'original': 'unit'}
            def fail(*args, **kw):
                raise ValueError('original Arm/Resume unknown')
            normal.day = fail
            out = st.run('advance-stage-day')
            self.assertEqual(out['status'], 'HOLD_NORMAL_STAGE_OR_ORIGINAL_PENDING')
            self.assertIsNone(out['time_advanced']); self.assertFalse(out['action_retry_allowed'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
