"""Public prepare/allocate/run scope boundaries; isolated IDs and no game/SDK.

The real allocator and immutable public artifacts run against a temporary test
namespace. Only machine/screen/process boundaries and business observations are
substituted; none of these results is live runtime qualification.
"""
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch
import argparse
import contextlib
import copy
import io
import json
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--scratch-root', type=Path)
options, remaining = parser.parse_known_args()
sys.argv = [sys.argv[0], *remaining]
sys.path[:0] = [str(REPO / 'tools'), str(REPO / 'ck3_autonomous_player/src')]
import ck3_mod_acceptance as entry
import ck3_mod_acceptance_allocate as allocator
from ck3_mod_acceptance_cases import r10_prepare_adapter as adapter
from ck3_mod_acceptance_cases import r06_refill_one_day as r06
from ck3_mod_acceptance_cases import r04_county_entry as r04
from steam_offline_state_contract import ProbeResult, ProbeWire, parse_result


def unavailable_steam_receipt_fixture(machine_id: str) -> ProbeWire:
    """A typed path-forwarding fixture, never evidence of actual offline mode."""
    receipt = ProbeResult(machine_id, '2026-10-20T00:00:00Z', '0' * 32,
        'unavailable', 'source_not_qualified', None, None, None,
        ('scope_fixture_no_Steam_read',)).to_wire()
    if parse_result(receipt).to_wire() != receipt:
        raise AssertionError('shared Steam receipt roundtrip differs')
    return receipt


class PublicR06ScopeTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(dir=options.scratch_root)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        for name in ('game/binaries', 'source', 'userdir', 'artifacts', 'lease/tools',
                     'lease/promo/ck3_native_war_ai/integration'):
            (self.root / name).mkdir(parents=True)
        engine = self.root / 'game/binaries/ck3.exe'
        engine.write_bytes(b'test fixture, never an executable')
        flags = ['--agent-source-root', '--game-dir', '--bridge-dll', '--bridge-injector',
                 '--bridge-pipe', '--output', '--state-dir', '--plan', '--control-plan-dir',
                 '--fixture-profile', *entry.BUDGET_FLAGS.values(), *entry.SAVED_FLAGS.values()]
        host = self.root / 'host.py'
        host.write_text('import argparse\np=argparse.ArgumentParser()\n' +
                        ''.join('p.add_argument(' + repr(flag) + ')\n' for flag in flags) +
                        "raise RuntimeError('test host must never execute')\n", encoding='utf-8')
        self.paths = {'source_root': self.root / 'source', 'host': host}
        for name in ('source_index', 'native_source_index', 'dll', 'injector', 'save',
                     'inventory', 'initial', 'launcher', 'queue', 'keeper'):
            path = self.root / (name + '.fixture')
            path.write_bytes(b'{}')
            self.paths[name] = path
        self.bus = self.root / 'lease/tools/codex_task_bus.py'
        self.bus.write_bytes(b'# never executed\n')
        (self.root / 'lease/promo/ck3_native_war_ai/integration/screen_bus_lease.py').write_bytes(b'# fixture\n')
        def row(key: str) -> dict[str, object]:
            return {'path_key': key, **{k: v for k, v in entry.pin(self.paths[key]).items() if k != 'path'}}
        self.machine = 'scope-test-machine'
        catalog = entry.read_json(REPO / 'tools/ck3_mod_acceptance_r10_products.json')
        required = catalog['products']['war-episode04-r10']['cases'][0]['required_mcp_tools']
        self.manifest = {'schema': entry.MANIFEST_SCHEMA, 'machine_id': self.machine,
            'source_root': {'path_key': 'source_root'}, 'host': row('host'),
            'source_index': row('source_index'), 'native_source_index': row('native_source_index'),
            'native': {'dll': row('dll'), 'injector': row('injector')},
            'game': {'version': 'test-only', 'exe_sha256': entry.pin(engine)['sha256']},
            'capabilities': {key: {'source_build_ready': True, 'actual_live_qualified': False} for key in required}}
        self.manifest_path = self.root / 'manifest.json'
        self.write(self.manifest_path, self.manifest)
        self.runtime_path = self.root / 'runtime.json'
        self.runtime = {'schema': entry.RUNTIME_SCHEMA, 'manifest': entry.pin(self.manifest_path),
            'python': sys.executable, 'repo_root': str(REPO), 'game_dir': str(self.root / 'game'),
            'userdir_root': str(self.root / 'userdir'), 'artifacts_root': str(self.root / 'artifacts'),
            'paths': {k: str(v) for k, v in self.paths.items()},
            'reviewed_launcher': entry.pin(self.paths['launcher']), 'control_queue': entry.pin(self.paths['queue']),
            'allocation': {'lease_repo': str(self.root / 'lease'), 'task_prefix': 'isolated-scope-test-',
                'screen_keeper': entry.pin(self.paths['keeper']), 'task_bus': entry.pin(self.bus)}}
        self.write(self.runtime_path, self.runtime)
        self.products_path = REPO / 'tools/ck3_mod_acceptance_r10_products.json'
        save = entry.pin(self.paths['save'])
        self.seed = {'save': save['path'], 'bytes': save['bytes'], 'sha256': save['sha256'],
                     'player_id': 12, 'date_raw': 1000}
        self.inputs = {'army_id': 0, 'native_carmy_id': 0, 'war_id': 1,
            'goal_province_id': 13, 'staging_province_id': 6, 'director_scope_revision': 'scope-test',
            'normal_checkpoint_receipt': entry.pin(self.paths['initial']),
            'budgets': dict(command_timeout=120, readiness_timeout=1800, timeout=5400, hold_seconds=3600, poll_interval=.25),
            'r06_refill_one_day': dict(scene_root=str(self.root), capacity_admission=None, producer={},
                expected_source_save_sha256=save['sha256'], expected_start_date_raw=1000,
                source_province_id=6, actor_id=12, army_id=0, native_carmy_id=0,
                driver_limit_bytes=1024*1024, profile_limit_bytes=1024*1024,
                deadline_utc='2100-01-01T00:00:00Z', prefix='scope-test')}
        self.state = self.root / 'prepared-state'
        self.prepared_path = self.root / 'prepared/prepared-case.json'
        # Keep the real adapter validator and route. Profile materialization is a
        # test seam so this suite never opens a game installation or large save.
        loader = patch.object(entry.Selection, 'load_adapter', return_value=adapter)
        self.addCleanup(loader.stop)
        loader.start()

    def write(self, path: Path, value: object) -> None:
        path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')

    def args(self, mode: str, context: Path | None = None) -> NS:
        return NS(mode=mode, runtime=self.runtime_path, products=self.products_path,
            product='war-episode04-r10', case='r10-common-preparation', run_context=context,
            prepared_case=self.prepared_path if self.prepared_path.exists() else None,
            case_inputs=self.root / 'inputs.json', prepare_output=self.prepared_path.parent)

    def prepare(self) -> bytes:
        self.write(self.root / 'inputs.json', {'state_dir': str(self.state),
            'saved_campaign': self.seed, 'case_inputs': self.inputs})
        def profile(context: dict[str, object]) -> dict[str, object]:
            adapter.validate_contract(context)
            self.state.mkdir()
            (self.state / 'profile').mkdir()
            return {'startup': {'mode': 'saved_campaign', 'state_dir': str(self.state),
                'saved_campaign': {**self.seed, 'product_inventory': str(self.paths['inventory'])}},
                'initial_plan': entry.pin(self.paths['initial']), 'files': {}, 'runtime_status': 'NOT_RUN'}
        with patch.object(adapter, 'prepare_case', side_effect=profile):
            value = entry.native_dispatch(self.args('prepare'))
        self.assertEqual(value['status'], 'CASE_PREPARED_NOT_ALLOCATED_NOT_RUN')
        return self.prepared_path.read_bytes()

    def allocate(self) -> dict[Path, bytes]:
        bootstrap = self.root / 'bootstrap.json'
        self.write(bootstrap, {})
        prior = self.root / 'prior-release.json'
        self.write(prior, {})
        keeper = self.root / 'keeper-output'
        admission = self.root / 'machine-admission'
        admission.mkdir()
        args = self.args('allocate')
        args.__dict__.update(attempt='a01', keeper_output=keeper, previous_release=prior,
            first_machine_bootstrap=bootstrap, previous_failure_close=None,
            previous_live=None, previous_keeper=None, latest_screen_release=None)
        binding = {'machine_id': self.machine, 'state_root': str(self.root / 'isolated-id-state')}
        original = entry.pin(bootstrap)
        closure = {'bootstrap': original, 'archive_index': original, 'original_evidence': {}}
        child = Mock(pid=987654)
        def finish(*unused: object) -> int:
            keeper.mkdir(exist_ok=True)
            self.write(keeper / 'report.json', {'test_only': True})
            return 0
        def process(argv: list[str], **unused: object) -> NS:
            if argv[0] == 'git':
                return NS(returncode=0, stdout=b'', stderr=b'')
            return NS(returncode=0, stdout=b'{"task":{"last_sequence":1}}', stderr=b'')
        with contextlib.ExitStack() as stack:
            for name, value in [('actual_machine_binding', binding), ('shared_bus_history', ([], False)),
                ('current_screen_absent', {}), ('validate_legacy_bootstrap', closure),
                ('runtime_process_inventory', {'blockers': []}), ('claim_machine_admission', admission),
                ('keeper_command', ['not-executed']), ('wait_for_keeper_ready', {'test_only': True})]:
                stack.enter_context(patch.object(allocator, name, return_value=value))
            stack.enter_context(patch.object(allocator, 'wait_for_allocated_keeper', side_effect=finish))
            stack.enter_context(patch.object(allocator.subprocess, 'run', side_effect=process))
            launch = stack.enter_context(patch.object(allocator.subprocess, 'Popen', return_value=child))
            stack.enter_context(patch('psutil.Process', return_value=NS(create_time=lambda: 1)))
            with contextlib.redirect_stdout(io.StringIO()):
                entry.native_dispatch(args)
        launch.assert_called_once()  # substituted keeper only, no OS launch
        ledger = entry.read_json(self.root / 'single-use-ledger/allocated.json')
        self.live = Path(ledger['live'])
        self.ready = entry.read_json(self.live / 'ready-context.json')
        self.assertEqual(self.ready['run_id'], self.live.name)
        history = self.root / 'isolated-id-state' / self.machine / 'vanilla/allocations.jsonl'
        self.assertEqual(json.loads(history.read_text())['run_id'], self.live.name)
        return {p: p.read_bytes() for p in (self.prepared_path,
            self.live / 'allocated-context.json', self.live / 'frozen-argv.json')}

    def scope(self) -> None:
        cap = {'machine_id': self.machine, 'run_id': self.live.name, 'admitted': True,
            'budget_status': 'GREEN', 'scene_root': str(self.root),
            'component_roots': {'profile': str(self.state), 'driver': str(self.live)},
            'component_ceiling_bytes': {'profile': 1024*1024, 'driver': 1024*1024},
            'quota_review_at_utc': '2100-01-01T00:00:00Z', 'run_hard_deadline_utc': '2100-01-01T00:00:00Z'}
        self.cap_path = self.root / 'capacity.actual.json'
        self.write(self.cap_path, cap)
        value = {'schema': 'ck3-mod-acceptance-r06-post-allocate-scope-v1', 'machine_id': self.machine,
            'run_id': self.live.name, 'run_dir': str(self.live), 'state_dir': str(self.state),
            'prepared_case': entry.pin(self.prepared_path), 'runtime_manifest': entry.pin(self.manifest_path),
            'allocated_context': entry.pin(self.live / 'allocated-context.json'),
            'frozen_argv': entry.pin(self.live / 'frozen-argv.json'), 'capacity_admission': entry.pin(self.cap_path)}
        self.scope_path = self.root / 'scope.json'
        self.write(self.scope_path, value)
        self.reviewed = copy.deepcopy(self.ready)
        # An explicit synthetic operator exercises the real reviewer guard.
        # This fixture never claims Root review or actual Steam/Game state.
        self.reviewed['reviewer'] = '/scope-fixture-operator'
        self.steam_receipt_path = self.root / 'steam-unavailable-fixture.json'
        self.write(self.steam_receipt_path, unavailable_steam_receipt_fixture(self.machine))
        self.reviewed.update(r06_post_allocate_scope=entry.pin(self.scope_path),
            steam_offline_receipt=str(self.steam_receipt_path))
        self.reviewed_path = self.root / 'reviewed-context.json'
        self.write(self.reviewed_path, self.reviewed)

    def select(self, context: Path | None = None) -> entry.Selection:
        return entry.Selection(self.runtime_path, self.products_path, 'war-episode04-r10',
            'r10-common-preparation', context or self.reviewed_path, self.prepared_path)

    def test_public_prepare_real_isolated_allocate_scope_preflight_run_same_client(self) -> None:
        prepared = self.prepare()
        originals = self.allocate()
        self.assertEqual(originals[self.prepared_path], prepared)
        no_scope = entry.native_dispatch(self.args('preflight', self.live / 'ready-context.json'))
        self.assertTrue(any('Exact bounded R06' in reason for reason in no_scope['blockers']))
        self.scope()
        self.assertEqual(entry.native_dispatch(self.args('preflight', self.reviewed_path))['blockers'], [])
        selected = self.select()
        from ck3_mod_acceptance_client import resolve_operator_reviewer
        self.assertEqual(resolve_operator_reviewer(selected), '/scope-fixture-operator')
        derived = selected.adapter_context()
        self.assertEqual(derived['case_inputs']['r06_refill_one_day']['capacity_admission'], entry.pin(self.cap_path))
        self.assertIsNone(selected.prepared['case_inputs']['r06_refill_one_day']['capacity_admission'])
        client = NS(output=self.live / 'case-output', _handle=object(), _process={'pid': 30},
            wait_hold=Mock(), retain_process=Mock(), checkpoint=Mock(), close_handle=Mock(),
            normal_close=Mock(return_value={'normal_close_qualified': True}))
        client.output.mkdir()
        frame = {'diagnostics': {'bridge_pid': 30, 'connection_generation': 2},
            'played_character': {'character_id': 12}, 'episode_run_id': None}
        relay = NS(client=NS(snapshot=lambda: frame))
        with patch.object(entry.subprocess, 'run', return_value=NS(returncode=0)) as launcher, \
             patch('ck3_mod_acceptance_client.CaseClient', return_value=client) as public_client, \
             patch('ck3_live_run_id.current_machine_id', return_value=self.machine), \
             patch('ck3_mod_acceptance_cases.r08_writer_common_adapter.retained_creation_filetime', return_value=35), \
             patch.object(adapter, 'CommonRequestRelay', return_value=relay), \
             patch.object(adapter, 'collect_ready_t0', return_value={'readiness': {}}), \
             patch.object(r06, 'run_case', return_value={'actual_days': 0, 'test_only': True}) as actor:
            result = entry.native_dispatch(self.args('run', self.reviewed_path))
        self.assertNotIn('case_error', result)
        public_client.assert_called_once()
        self.assertIs(actor.call_args.args[1], client)
        self.assertEqual(actor.call_args.args[0]['case_inputs'], derived['case_inputs'])
        launcher.assert_called_once()
        argv = launcher.call_args.args[0]
        self.assertEqual(argv[-2:], ['--steam-offline-receipt', str(self.steam_receipt_path)])
        self.assertNotIn('--proof', argv)
        self.assertNotIn('--challenge', argv)
        receipt = parse_result(entry.read_json(self.steam_receipt_path))
        self.assertEqual(receipt.status, 'unavailable')
        self.assertNotIn('offline_mode', receipt.to_wire())
        client.normal_close.assert_called_once()
        client.close_handle.assert_called_once()
        for path, original in originals.items():
            self.assertEqual(path.read_bytes(), original, str(path))
        self.assertEqual(entry.read_json(self.reviewed_path)['case_inputs'], selected.prepared['case_inputs'])

    def test_run_requires_background_receipt_before_launcher(self) -> None:
        self.prepare(); self.allocate(); self.scope()
        for mode in ('missing', 'null', 'empty'):
            reviewed = copy.deepcopy(self.reviewed)
            if mode == 'missing':
                del reviewed['steam_offline_receipt']
            else:
                reviewed['steam_offline_receipt'] = None if mode == 'null' else ''
            self.write(self.reviewed_path, reviewed)
            with self.subTest(mode=mode), patch.object(entry.subprocess, 'run') as launch:
                with self.assertRaisesRegex(ValueError, 'steam_offline_receipt'):
                    entry.native_dispatch(self.args('run', self.reviewed_path))
                launch.assert_not_called()

    def test_reviewer_missing_null_and_persisted_drift_refuse_before_launcher(self) -> None:
        self.prepare(); self.allocate(); self.scope()
        original = copy.deepcopy(self.reviewed)
        for mode in ('missing', 'null', 'empty'):
            reviewed = copy.deepcopy(original)
            if mode == 'missing':
                del reviewed['reviewer']
            else:
                reviewed['reviewer'] = None if mode == 'null' else ''
            self.write(self.reviewed_path, reviewed)
            with self.subTest(mode=mode), \
                 patch.object(entry.subprocess, 'run') as launch, \
                 patch('ck3_mod_acceptance_client.CaseClient') as public_client, \
                 patch.object(adapter, 'run_case') as business:
                with self.assertRaisesRegex(ValueError, 'reviewer'):
                    entry.native_dispatch(self.args('run', self.reviewed_path))
                launch.assert_not_called()
                public_client.assert_not_called()
                business.assert_not_called()
        self.write(self.reviewed_path, original)
        selected = self.select()
        changed = copy.deepcopy(original)
        changed['reviewer'] = '/different-synthetic-operator'
        self.write(self.reviewed_path, changed)
        with patch.object(entry.subprocess, 'run') as launch, \
             patch('ck3_mod_acceptance_client.CaseClient') as public_client, \
             patch.object(adapter, 'run_case') as business:
            with self.assertRaisesRegex(ValueError, 'differs from persisted allocated context'):
                selected.run()
            launch.assert_not_called()
            public_client.assert_not_called()
            business.assert_not_called()

    def test_prepare_refuses_prefilled_capacity_without_allocating(self) -> None:
        self.inputs['r06_refill_one_day']['capacity_admission'] = {'run_id': 'guessed'}
        with self.assertRaisesRegex(ValueError, 'explicit null capacity'):
            self.prepare()
        self.assertFalse((self.root / 'isolated-id-state').exists())

    def test_scope_rejects_crossed_or_expired_inputs_before_public_launcher(self) -> None:
        self.prepare(); self.allocate(); self.scope()
        scope = entry.read_json(self.scope_path)
        cap = entry.read_json(self.cap_path)
        variants = [('scope-run', lambda s, c, r: s.update(run_id='guessed-run')),
            ('scope-machine', lambda s, c, r: s.update(machine_id='other-machine')),
            ('scope-prepared', lambda s, c, r: s['prepared_case'].update(sha256='0'*64)),
            ('scope-runtime', lambda s, c, r: s['runtime_manifest'].update(sha256='0'*64)),
            ('allocated-substitute', lambda s, c, r: s.update(allocated_context=entry.pin(self.scope_path))),
            ('cap-run', lambda s, c, r: c.update(run_id='predicted')),
            ('cap-machine', lambda s, c, r: c.update(machine_id='other-machine')),
            ('cap-expired', lambda s, c, r: c.update(quota_review_at_utc='2000-01-01T00:00:00Z')),
            ('cap-root', lambda s, c, r: c['component_roots'].update(driver=str(self.root))),
            ('cap-ceiling', lambda s, c, r: c['component_ceiling_bytes'].update(driver=1)),
            ('reviewed-inputs', lambda s, c, r: r['case_inputs'].update(army_id=99))]
        for name, change in variants:
            with self.subTest(name=name):
                s, c, reviewed = copy.deepcopy(scope), copy.deepcopy(cap), copy.deepcopy(self.reviewed)
                change(s, c, reviewed)
                self.write(self.cap_path, c)
                s['capacity_admission'] = entry.pin(self.cap_path)
                self.write(self.scope_path, s)
                reviewed['r06_post_allocate_scope'] = entry.pin(self.scope_path)
                self.write(self.reviewed_path, reviewed)
                with patch.object(entry.subprocess, 'run') as launch:
                    with self.assertRaises((ValueError, KeyError)):
                        entry.native_dispatch(self.args('run', self.reviewed_path))
                launch.assert_not_called()

    def test_default_and_r04_keep_original_context_and_public_route(self) -> None:
        for kind in ('default', 'r04'):
            with self.subTest(kind=kind):
                # A second fixture keeps prepare's single-use contract intact.
                case = PublicR06ScopeTests('runTest')
                case.setUp()
                try:
                    del case.inputs['r06_refill_one_day']
                    if kind == 'r04': case.inputs['r04_county_entry'] = {'test_route': True}
                    with patch.object(r04, 'validate_contract'):
                        case.prepare(); case.allocate()
                    selected = case.select(case.live / 'ready-context.json')
                    context = selected.adapter_context()
                    self.assertNotIn('r06_post_allocate_scope', context)
                    self.assertEqual(context['case_inputs'], case.inputs)
                    client = NS(retain_process=Mock(), _process={'pid': 30}, checkpoint=Mock())
                    frame = {'diagnostics': {'bridge_pid': 30, 'connection_generation': 2},
                        'played_character': {'character_id': 12}, 'episode_run_id': None}
                    with patch.object(r04, 'validate_contract'), \
                         patch.object(r04, 'run_case', return_value={'test_only': True}) as actor, \
                         patch.object(r06, 'run_case') as other, \
                         patch('ck3_live_run_id.current_machine_id', return_value=case.machine), \
                         patch('ck3_mod_acceptance_cases.r08_writer_common_adapter.retained_creation_filetime', return_value=35), \
                         patch.object(adapter, 'CommonRequestRelay', return_value=NS(client=NS(snapshot=lambda: frame))), \
                         patch.object(adapter, 'collect_ready_t0', return_value={'readiness': {}}):
                        adapter.run_case(context, client)
                    self.assertEqual(actor.call_count, int(kind == 'r04'))
                    if kind == 'r04': self.assertIs(actor.call_args.args[1], client)
                    other.assert_not_called()
                    selected.context['r06_post_allocate_scope'] = {}
                    with self.assertRaisesRegex(ValueError, 'cannot override another case'):
                        selected.adapter_context()
                finally:
                    case.doCleanups()


if __name__ == '__main__':
    unittest.main()
