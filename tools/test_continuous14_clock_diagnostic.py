"""Actual public queue/Host/client/clock branches; authored transport, no Game/OS I/O."""
from __future__ import annotations

import ast
import asyncio
import copy
import json
from pathlib import Path
import sys
import tempfile
import time
from types import MethodType, SimpleNamespace
from typing import Protocol, runtime_checkable
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ck3_autonomous_player/src'))
sys.path.insert(0, str(REPO / 'tools'))
from ck3_mod_acceptance_background_types import (
    CONTINUOUS14_CONTRACT_V1, CONTINUOUS14_PASSIVE_STORY_TYPES_V1,
    ProductAcceptanceClockV1, ProductAcceptancePurposeV1,
    continuous14_contract_matches_v1, continuous14_status_sample_v1, continuous14_endpoint_v1,
)
from ck3_mod_acceptance_queue import validate_steps
from ck3_mod_acceptance_client import CaseClient
from ck3_mod_acceptance_cases import generic_product_adapter as adapter
from xar_autoplayer.bridge.version_identity import CK3_1210
from xar_autoplayer.bridge.native_driver import (
    NativeProtocolState, NativeHeadlessGameplayDriver, _normalize_tactical_daily_sentinel_status)
from xar_autoplayer.bridge.driver import BridgeUnavailableError
import test_product_acceptance_purpose as purpose_helpers

HOST = REPO / 'ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py'
CONFIG = REPO / 'tools/ck3_mod_acceptance_cases/financial_markets_clock_cadence_continuous14.json'
START = 53146656
FAMILIES = ['game.command.research-arm-tactical-daily-sentinel-v1-N',
    'game.command.research-query-tactical-daily-sentinel-v1',
    'game.command.research-cancel-tactical-daily-sentinel-v1-generation-N']


def frame(day: int = 0) -> dict[str, object]:
    if type(day) is not int or day not in (0, 14):
        raise AssertionError('No real Native producer supports a running Full in this diagnostic')
    return {'schema': 'ck3_1210_full_state_v1', 'source': 'injected-dll-named-pipe',
        'backend_id': 'native-headless', 'episode_projection': 'native_campaign',
        'game_version': '1.21.0', 'executable_sha256': CK3_1210.executable_sha256,
        'adapter_id': 'ck3-1.21.0-msvc-x64', 'backend': 'ck3-1.21.0-native-headless-main-thread',
        'snapshot_id': f'native:{100 + day}', 'revision': 200 + day, 'native_revision': 100 + day,
        'date_raw': START + day * 24, 'speed': 1, 'paused': True, 'map_ready': True,
        'local_player_id': 31254, 'played_character': {'character_id': 31254, 'alive': True, 'source': 'native'},
        'active_wars': [], 'player_armies': [], 'active_event': None, 'pending_character_interaction': None,
        'episode_run_id': 'authored-current-run', 'managed_campaign_run_binding': {'run_id': 'authored-current-run'},
        'diagnostics': {'connected': True, 'bridge_pid': 43, 'connection_generation': 8, 'pipe_name': 'authored-pipe',
            'hello': {'pid': 43, 'connection_generation': 8, 'expected_ck3_version': '1.21.0',
                'expected_ck3_sha256': CK3_1210.executable_sha256, 'game_adapter_id': 'ck3-1.21.0-msvc-x64',
                'ck3_build_match': True, 'capabilities': FAMILIES + ['game.state.snapshot',
                    'game.query.fresh-full-state.v1', 'game.command.pause-map',
                    'game.command.resume-map', 'game.command.set-speed-1']}}}


def capabilities(cached: dict[str, object] | None = None) -> dict[str, object]:
    # Authored projection of actual cached fields; no Native query or new world frame.
    source = frame() if cached is None else cached
    diagnostics = copy.deepcopy(source['diagnostics'])
    if not isinstance(diagnostics, dict) or not isinstance(diagnostics.get('hello'), dict):
        raise AssertionError('Actual cached diagnostics/HELLO fields required')
    advertised = diagnostics['hello']['capabilities']
    return {'snapshot': True, 'diagnostics': diagnostics,
        'bridge_capabilities': list(advertised),
        'action_steps': [name for name in ('pause-map', 'resume-map', 'set-speed-1')
            if 'game.command.' + name in advertised]}


def status(day: int = 0) -> dict[str, object]:
    value = {'state': 'armed', 'generation': 3, 'starting_date_raw': START, 'target_date_raw': START + 336,
        'last_observed_date_raw': START + day * 24, 'trigger_date_raw': 0, 'speed': 1,
        'mode': 'terminal_or_sentinel', 'army_count': 0, 'combat_count': 0, 'completed_daily_ticks': day,
        'intermediate_pause_count': 0, 'trigger_flags': 0, 'trigger_reasons': [],
        'signed_date_delta_from_target_raw': 0, 'overshoot_days': -1,
        'pause_wrapper_called': False, 'pause_observed': False, 'terminal_observed': False, 'abnormal': False}
    if day == 14:
        value.update(state='triggered', trigger_date_raw=START + 336, trigger_flags=1,
            trigger_reasons=['date_deadline'], overshoot_days=0, pause_wrapper_called=True, pause_observed=True)
    return _normalize_tactical_daily_sentinel_status(value)


def purpose(case: str = 'clock-cadence-continuous14') -> ProductAcceptancePurposeV1:
    return ProductAcceptancePurposeV1('authored-machine', 'authored-current-run', 'financial-markets',
        case, Path('authored-state'), 'authored-pipe', 14, False,
        'continuous14_diagnostic' if case == 'clock-cadence-continuous14' else 'one_day_acceptance')


@runtime_checkable
class HostAPI(Protocol):
    report: dict[str, object]
    snapshot: dict[str, object]
    async def execute(self, rows: list[dict[str, object]]) -> None: ...
    async def continuous14_diagnostic(self, row: dict[str, object]) -> dict[str, object]: ...


def actual_host(*, selected_case: str = 'clock-cadence-continuous14', skip: int | None = None,
                owner_change_day: int | None = None, missing_capability: bool = False,
                lost_resume_ack: bool = False) -> tuple[HostAPI, list[str]]:
    tree = ast.parse(HOST.read_bytes())
    original = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'PlanClient')
    names = {'continuous14_diagnostic', 'execute', 'invoke', 'advance'}
    methods = [node for node in original.body if isinstance(node, ast.AsyncFunctionDef) and node.name in names]
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in {'lookup', 'resolve'}]
    if len(methods) != 4 or len(functions) != 2:
        raise AssertionError('Actual Host method closure changed')
    namespace: dict[str, object] = {'asyncio': asyncio, 'json': json, 'time': time, 'Path': Path,
        'now': lambda: 'AUTHORED-NO-GAME', 'load_product_acceptance_clock_v1':
            lambda args: ProductAcceptanceClockV1(purpose(selected_case))}
    module = ast.fix_missing_locations(ast.Module(body=[ast.ImportFrom(module='__future__',
        names=[ast.alias(name='annotations')], level=0), *functions,
        ast.ClassDef(name='ActualPlanClient', bases=[], keywords=[], body=methods, decorator_list=[])], type_ignores=[]))
    exec(compile(module, str(HOST), 'exec'), namespace)
    factory = namespace['ActualPlanClient']
    if not isinstance(factory, type):
        raise AssertionError('Actual Host class missing')
    candidate = factory()
    calls: list[str] = []
    current_day, native_sequence, public_sequence, running = 0, 100, 200, False
    cached = frame()

    async def fresh() -> dict[str, object]:
        # A cached old paused Full is not a current running observation. This
        # port deliberately refuses any attempt to use it as one in the Host.
        if running and current_day < 14:
            raise AssertionError('Q26 running Full is unavailable; never manufacture it')
        candidate.snapshot = copy.deepcopy(cached)
        return copy.deepcopy(cached)

    async def call(name: str, arguments: dict[str, object] | None = None) -> dict[str, object]:
        nonlocal current_day, native_sequence, public_sequence, running, cached
        if name == 'ck3_get_capabilities':
            value = capabilities(cached)
            if missing_capability:
                value['bridge_capabilities'] = FAMILIES[1:]
            if owner_change_day is not None and current_day >= owner_change_day:
                value['diagnostics']['connection_generation'] += 1
                value['diagnostics']['hello']['connection_generation'] += 1
            return value
        if name == 'ck3_take_fresh_full_snapshot_v1':
            if running and current_day < 14:
                raise AssertionError('Real Native Full producer rejects running; test cannot supply one')
            calls.append('fresh-paused-full@' + str(current_day))
            native_sequence += 1; public_sequence += 1
            cached = frame(current_day)
            cached.update(native_revision=native_sequence, revision=public_sequence,
                snapshot_id='native:' + str(native_sequence))
            candidate.snapshot = copy.deepcopy(cached)
            return copy.deepcopy(cached)
        if name != 'ck3_execute_step' or arguments is None:
            raise AssertionError('Unexpected actual Host transport: ' + name)
        step = str(arguments['step'])
        calls.append(step)
        if step == 'research-query-tactical-daily-sentinel-v1':
            if arguments.get('expected_revision') is not None:
                raise AssertionError('Status query uses its existing nullable revision contract')
            if not running:
                raise AssertionError('No status before original resume')
            current_day += 1
            if current_day == skip:
                current_day += 1
            return {'step': step, 'accepted': True, 'status': 'available',
                'tactical_daily_sentinel': status(current_day)}
        if type(arguments.get('expected_revision')) is not int or arguments['expected_revision'] != cached['revision']:
            raise AssertionError('Mutating controls retain the exact actual paused Full revision')
        if step.startswith('research-arm-'):
            return {'step': step, 'accepted': True, 'status': 'available', 'tactical_daily_sentinel': status()}
        if step == 'resume-map':
            running = True
            if lost_resume_ack:
                raise OSError('Authored lost ACK after possible original resume dispatch')
            return {'schema': 'ck3_1210_full_clock_control_result_v1', 'step': step, 'accepted': True,
                'queue_status': 'submitted', 'effect_attempted': True, 'full_snapshot_before_verified': True,
                'physical_save_confirmed': False, 'complete_snapshot': False}
        raise AssertionError('Unexpected action; no pause/resume/replay/event choosing permitted: ' + step)

    for name, value in {'report': {'steps': []}, 'snapshot': frame(), 'results': {}, 'episode_identity': None,
        'args': SimpleNamespace(saved_campaign_save=None, frontend_mod_load_observation=False, command_timeout=300),
        'tools': {name: {'inputSchema': {'properties': {}}} for name in
                  ('ck3_get_capabilities', 'ck3_take_snapshot', 'ck3_take_fresh_full_snapshot_v1', 'ck3_execute_step')},
        'managed_done': SimpleNamespace(is_set=lambda: False), 'write': lambda: None,
        'fresh': fresh, 'call': call}.items():
        setattr(candidate, name, value)
    if not isinstance(candidate, HostAPI):
        raise AssertionError('Actual Host interface incomplete')
    return candidate, calls


async def no_wait(seconds: float) -> None:
    return None


def experiment(client: HostAPI) -> dict[str, object]:
    with patch('asyncio.sleep', new=no_wait):
        asyncio.run(client.execute([{'id': 'original-continuous14', 'kind': 'continuous14_diagnostic', 'timeout': 240}]))
    rows = client.report['steps']
    return rows[0]['result']


class Continuous14Tests(unittest.TestCase):
    def test_original_one_day_clock_does_not_accept_multiday_or_diagnostic_purpose(self) -> None:
        old = ProductAcceptanceClockV1(purpose('market-evolution'))
        self.assertEqual(old.deadline(frame(), START + 24, r05_scope_bound=False)['target_date_raw'], START + 24)
        with self.assertRaises(ValueError): old.deadline(frame(), START + 336, r05_scope_bound=False)
        new = ProductAcceptanceClockV1(purpose())
        with self.assertRaises(ValueError): new.deadline(frame(), START + 24, r05_scope_bound=False)
        with self.assertRaises(ValueError): old.continuous14_deadline(frame(), START + 336, r05_scope_bound=False)

    def test_new_clock_is_exact_current_plus336_once_without_r05(self) -> None:
        for target in (START + 24, START + 312, START + 360, True):
            with self.subTest(target=target), self.assertRaises(ValueError):
                ProductAcceptanceClockV1(purpose()).continuous14_deadline(frame(), target, r05_scope_bound=False)
        clock = ProductAcceptanceClockV1(purpose())
        with self.assertRaises(ValueError): clock.continuous14_deadline(frame(), START + 336, r05_scope_bound=True)
        self.assertEqual(clock.continuous14_deadline(frame(), START + 336, r05_scope_bound=False)['requested_days'], 14)
        with self.assertRaises(ValueError): clock.continuous14_deadline(frame(), START + 336, r05_scope_bound=False)

    def test_fixed_public_contract_rejects_bool_float_unknown_and_missing(self) -> None:
        self.assertTrue(continuous14_contract_matches_v1(copy.deepcopy(CONTINUOUS14_CONTRACT_V1)))
        for name, value in [('speed', True), ('days', 14.0), ('timeout_seconds', 600), ('extra', 1)]:
            altered = copy.deepcopy(CONTINUOUS14_CONTRACT_V1); altered[name] = value
            self.assertFalse(continuous14_contract_matches_v1(altered))
        altered = copy.deepcopy(CONTINUOUS14_CONTRACT_V1); altered.pop('physical_saves')
        self.assertFalse(continuous14_contract_matches_v1(altered))

    def test_real_purpose_producer_queue_and_new_case_binding_before_publish(self) -> None:
        fixture = purpose_helpers.ProductPurposeTests(methodName='runTest'); fixture.setUp(); self.addCleanup(fixture.doCleanups)
        config = json.loads(CONFIG.read_bytes())
        fixture.contract = config
        fixture.prepared.update(product='financial-markets', case='clock-cadence-continuous14')
        fixture.frozen.update(mod_key='financial-markets', cell='clock-cadence-continuous14')
        purpose_helpers.write(fixture.frozen_path, fixture.frozen)
        fixture.context.update(product='financial-markets', case='clock-cadence-continuous14',
            frozen_argv=purpose_helpers.pin(fixture.frozen_path))
        fixture.refresh_contract(); fixture.produce()
        loaded = fixture.consume()
        self.assertEqual(loaded.purpose.clock_purpose, 'continuous14_diagnostic')
        report = {'steps': [], 'mcp_tools': {'tools': [{'name': 'ck3_execute_step', 'inputSchema': {}}]}}
        step = {'id': 'fresh', 'kind': 'continuous14_diagnostic', 'timeout': 240}
        self.assertEqual(validate_steps([step], report, fixture.frozen), ['fresh'])
        with self.assertRaises(ValueError): validate_steps([dict(step, days=14)], report, fixture.frozen)
        with self.assertRaises(ValueError): validate_steps([dict(step, timeout=True)], report, fixture.frozen)
        with self.assertRaises(ValueError): validate_steps([dict(step, kind='advance_day', days=14)], report, fixture.frozen)
        report['continuous14_diagnostic'] = {'state': 'INCOMPLETE_NEVER_REPLAY'}
        with self.assertRaises(ValueError): validate_steps([step], report, fixture.frozen)

    def test_actual_host_execute_uses_status_only_and_never_requests_a_running_full(self) -> None:
        host, calls = actual_host(); value = experiment(host)
        self.assertEqual(value['state'], 'COMPLETE_DIAGNOSTIC_ONLY')
        self.assertEqual([row['day'] for row in value['samples']], list(range(1, 15)))
        self.assertEqual([row['status']['last_observed_date_raw'] for row in value['samples']],
            [START + 24 * day for day in range(1, 15)])
        self.assertTrue(all(set(row) == {'day', 'status', 'owner_before', 'owner_after'} for row in value['samples']))
        self.assertEqual(sum(step.startswith('research-arm-') for step in calls), 1)
        self.assertEqual(calls.count('resume-map'), 1)
        self.assertEqual(calls.count('research-query-tactical-daily-sentinel-v1'), 14)
        self.assertEqual([step for step in calls if step.startswith('fresh-paused-full@')],
            ['fresh-paused-full@0', 'fresh-paused-full@0', 'fresh-paused-full@14'])
        self.assertNotIn('pause-map', calls)
        self.assertIs(value['financial_daily_coverage_verified'], False)
        self.assertTrue(all(value[key] is False for key in ('business_pass', 'performance_pass', 'product_release_pass')))

    def test_real_host_rejects_wrong_case_before_any_transport_and_legacy_advance_stays_one_day(self) -> None:
        host, calls = actual_host(selected_case='market-evolution')
        with self.assertRaisesRegex(ValueError, 'independent diagnostic purpose'): experiment(host)
        self.assertEqual(calls, [])
        with self.assertRaisesRegex(ValueError, 'requires one day'):
            asyncio.run(host.execute([{'id': 'legacy', 'kind': 'advance_day', 'days': 14, 'timeout': 240}]))
        self.assertEqual(calls, [])

    def test_missing_daily_sample_fails_without_interpolation_or_rearm(self) -> None:
        host, calls = actual_host(skip=7)
        with self.assertRaisesRegex(ValueError, 'missing'): experiment(host)
        value = host.report['continuous14_diagnostic']
        self.assertEqual(value['state'], 'INCOMPLETE_NEVER_REPLAY')
        self.assertEqual([row['day'] for row in value['samples']], list(range(1, 7)))
        self.assertEqual(calls.count('resume-map'), 1)
        count = len(calls)
        with self.assertRaisesRegex(ValueError, 'already consumed'):
            asyncio.run(host.continuous14_diagnostic({'id': 'different', 'kind': 'continuous14_diagnostic', 'timeout': 240}))
        self.assertEqual(len(calls), count)

    def test_missing_capability_has_no_arm_resume_and_lost_ack_never_replays(self) -> None:
        host, calls = actual_host(missing_capability=True)
        with self.assertRaisesRegex(ValueError, 'capability'): experiment(host)
        self.assertEqual(calls, ['fresh-paused-full@0'])
        host, calls = actual_host(lost_resume_ack=True)
        with self.assertRaises(OSError): experiment(host)
        self.assertEqual(calls.count('resume-map'), 1)
        self.assertEqual(host.report['continuous14_diagnostic']['state'], 'INCOMPLETE_NEVER_REPLAY')

    def test_live_connection_change_preserves_partial_status_window_and_selects_nothing(self) -> None:
        host, calls = actual_host(owner_change_day=4)
        with self.assertRaisesRegex(ValueError, 'PID/pipe/connection'): experiment(host)
        self.assertEqual(len(host.report['continuous14_diagnostic']['samples']), 3)
        self.assertFalse(any('select-event' in step for step in calls))
        self.assertEqual(calls.count('resume-map'), 1)
        self.assertNotIn('fresh-paused-full@14', calls)

    def test_real_status_duplicates_are_not_samples_and_generation_date_pause_or_gap_fails(self) -> None:
        caps = capabilities()
        self.assertIsNone(continuous14_status_sample_v1(frame(), status(), status(), 0, caps, caps))
        self.assertIsNone(continuous14_status_sample_v1(frame(), status(1), status(), 1, caps, caps))
        for name, changed in [('generation', 4), ('last_observed_date_raw', START + 25),
                              ('speed', True), ('state', 'failed'), ('completed_daily_ticks', 2)]:
            actual = status(1); actual[name] = changed
            with self.subTest(name=name), self.assertRaises((ValueError, BridgeUnavailableError)):
                continuous14_status_sample_v1(frame(), actual, status(), 0, caps, caps)
        sample = continuous14_status_sample_v1(frame(), status(1), status(), 0, caps, caps)
        self.assertEqual(set(sample), {'day', 'status', 'owner_before', 'owner_after'})
        for name, changed in [('connected', False), ('bridge_pid', 44), ('pipe_name', 'foreign-pipe')]:
            foreign = capabilities(); foreign['diagnostics'][name] = changed
            with self.subTest(owner=name), self.assertRaises(ValueError):
                continuous14_status_sample_v1(frame(), status(1), status(), 0, caps, foreign)
        with self.assertRaisesRegex(AssertionError, 'No real Native producer'):
            frame(1)

    def test_final_status_and_fresh_paused_full_require_exact_deadline_and_same_actor(self) -> None:
        caps = capabilities()
        self.assertEqual(continuous14_status_sample_v1(frame(), status(14), status(), 13, caps, caps)['day'], 14)
        continuous14_endpoint_v1(frame(), frame(14), status(), status(14))
        for name, value in [('completed_daily_ticks', 13), ('intermediate_pause_count', 1),
                            ('overshoot_days', 1), ('trigger_reasons', ['native_pause'])]:
            actual = status(14); actual[name] = value
            with self.subTest(name=name), self.assertRaises((ValueError, BridgeUnavailableError)):
                continuous14_endpoint_v1(frame(), frame(14), status(), actual)
        altered = frame(14); altered['played_character']['character_id'] += 1
        with self.assertRaises(ValueError): continuous14_endpoint_v1(frame(), altered, status(), status(14))

    def test_actual_case_client_consumes_host_result_and_cannot_be_borrowed(self) -> None:
        host, _ = actual_host(); value = experiment(host)
        client = object.__new__(CaseClient)
        config = json.loads(CONFIG.read_bytes())
        selected = {'product': 'financial-markets', 'case': 'clock-cadence-continuous14', 'case_contract': config}
        calls: list[list[dict[str, object]]] = []
        def execute(steps, name, timeout=None, reserve=90):
            calls.append(steps); return [{'result': copy.deepcopy(value)}]
        client.selection = SimpleNamespace(adapter_context=lambda: selected)
        client.manifest = {'game': {'version': '1.21.0', 'exe_sha256': CK3_1210.executable_sha256}}
        client._binding = None; client._seq = 0
        client.guard = lambda reserve: {'steps': []}; client.remaining = lambda: 500
        client.execute_plan = execute
        self.assertEqual(client.continuous14_diagnostic()['result']['elapsed_hours'], 336)
        self.assertEqual(calls[0][0]['kind'], 'continuous14_diagnostic')
        selected['case'] = 'market-evolution'
        with self.assertRaises(ValueError): client.continuous14_diagnostic()
        self.assertEqual(len(calls), 1)

    def test_real_adapter_uses_two_save_reviews_and_never_ordinary_day_or_observer_arm(self) -> None:
        host, _ = actual_host(); value = experiment(host)
        config = json.loads(CONFIG.read_bytes())
        context = {'case_contract': config, 'product': 'financial-markets', 'case': config['case_id'], 'run_id': 'authored-run',
            'case_inputs': {'post_start': {'government_key': 'feudal_government',
                'primary_title_tier_key': 'duchy', 'independent': True}}}
        config = adapter.resolve_post_start(context)['case_contract']
        phases: list[str] = []
        class Client:
            def snapshot(self): return frame()
            def continuous14_diagnostic(self): return {'result': value}
            def checkpoint(self, name, facts): return None
        def phase(client, context, name, requirements, snapshot, compiled):
            phases.append(name); return {'authored_transport_review': name}
        with patch.object(adapter, 'compiled_contract', return_value=({'config': config}, {'authored_pin': True})), \
                patch.object(adapter, 'root_phase', side_effect=phase):
            facts = adapter.run_case(context, Client())
        self.assertEqual(phases, [row['id'] for row in config['gui_phases']])
        self.assertEqual(len(phases), 2)
        self.assertFalse(facts['business_pass']); self.assertFalse(facts['performance_pass'])
        self.assertIs(facts['financial_daily_coverage_verified'], False)

    def test_passive_catalog_is_finite_and_registry_has_no_existing_case_budget_change(self) -> None:
        config = json.loads(CONFIG.read_bytes())
        self.assertEqual(config['passive_story_types'], list(CONTINUOUS14_PASSIVE_STORY_TYPES_V1))
        self.assertIn('xfma_market_evolution_e5_observer', config['passive_story_types'])
        self.assertIn('xfma_spot_e3_observer', config['passive_story_types'])
        self.assertIn('xfma_ai_capacity_day_record', config['passive_story_types'])
        # Execute only the actual load-carrier catalog writer, not profile/launch preparation.
        tree = ast.parse(Path(adapter.__file__).read_bytes())
        prepare = next(node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == '_prepare_fixture_case')
        catalog = [node for node in ast.walk(prepare) if isinstance(node, ast.If)
            and isinstance(node.test, ast.Name) and node.test.id == 'continuous14']
        validation = [node for node in prepare.body if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == 'continuous14' for target in node.targets)]
        self.assertEqual(len(catalog), 1)
        self.assertEqual(len(validation), 1)
        actual = compile(ast.fix_missing_locations(ast.Module(body=[*validation, *catalog], type_ignores=[])),
            str(adapter.__file__), 'exec')
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory)
            context = {'product': 'financial-markets', 'case': config['case_id'], 'case_contract': config}
            namespace = {'context': context, 'config': config, 'fixture': fixture,
                'json_object': adapter.json_object, '_continuous14_enabled': adapter._continuous14_enabled}
            exec(actual, namespace)
            emitted = (fixture / 'common/story_cycles/xfma_clock_cadence_passive.txt').read_text(encoding='utf-8-sig')
            self.assertEqual(emitted, ''.join(name + ' = { visible = no }\n'
                for name in CONTINUOUS14_PASSIVE_STORY_TYPES_V1))
            self.assertIn('xfma_ai_capacity_day_record = { visible = no }\n', emitted)
            self.assertNotIn('on_action', emitted); self.assertNotIn('effect', emitted)
            missing = copy.deepcopy(config); missing['passive_story_types'].remove('xfma_ai_capacity_day_record')
            namespace.update(config=missing, context={**context, 'case_contract': missing})
            with self.assertRaisesRegex(ValueError, 'Exact finite passive'):
                exec(actual, namespace)
            self.assertEqual((fixture / 'common/story_cycles/xfma_clock_cadence_passive.txt')
                .read_text(encoding='utf-8-sig'), emitted)
        self.assertNotIn('xfma_market_evolution_e6_observer', config['passive_story_types'])
        registry = json.loads((REPO / 'tools/ck3_mod_acceptance_products.json').read_bytes())
        cases = registry['products']['financial-markets']['cases']
        diagnostic = next(row for row in cases if row['id'] == config['case_id'])
        self.assertFalse(config['continuous14_contract']['financial_daily_coverage_verified'])
        self.assertFalse(diagnostic['business_contract_applicable'])
        self.assertFalse(diagnostic['whole_product_acceptance_credit'])
        self.assertEqual(next(row for row in cases if row['id'] == 'market-evolution')['budgets']['timeout'], 10800)


    def test_actual_sdk_status_primitive_uses_real_protocol_cache_without_fresh_full(self) -> None:
        # Execute actual SDK cache + primitive, with only the endpoint authored.
        # A new status date is permitted while the cached paused Full stays old;
        # that cache is explicitly not a current running world observation.
        state = NativeProtocolState('authored-cache-pipe')
        state.ingest({'type': 'hello', 'protocol_version': 1, 'pid': 43, 'connection_generation': 8,
            'expected_ck3_version': '1.21.0', 'expected_ck3_sha256': CK3_1210.executable_sha256,
            'game_adapter_id': 'ck3-1.21.0-msvc-x64', 'ck3_build_match': True,
            'capabilities': ['game.state.snapshot', *FAMILIES]})
        resource = REPO / 'java/ck3-control/native-transport/src/test/resources/newnative/full1210/full-snapshot-producer-102.json'
        state.ingest(json.loads(resource.read_bytes()))
        before = state.semantic_snapshot()
        sent: list[dict[str, object]] = []
        class Endpoint:
            def send(self, request):
                if request['step'] != 'research-query-tactical-daily-sentinel-v1':
                    raise AssertionError('No fresh Full or mutation permitted in status-only cache port')
                sent.append(copy.deepcopy(request))
                state.ingest({'type': 'command_result', 'protocol_version': 1,
                    'request_id': request['request_id'], 'ok': True,
                    'result': {'step': request['step'], 'accepted': True, 'status': 'available',
                        'tactical_daily_sentinel': status(1)}})
        port = SimpleNamespace(state=state, endpoint=Endpoint(), _request_sequence=0, command_timeout_seconds=1,
            capabilities=state.capabilities, take_snapshot=state.semantic_snapshot,
            take_internal_semantic_snapshot=state.semantic_snapshot, _h3937_date_hold_active=lambda *args: False)
        port._verify_idempotent_map_control_postcondition = MethodType(
            NativeHeadlessGameplayDriver._verify_idempotent_map_control_postcondition, port)
        result = NativeHeadlessGameplayDriver._execute_primitive_step(port,
            'research-query-tactical-daily-sentinel-v1', expected_revision=None,
            required_capability=FAMILIES[1])
        self.assertEqual(_normalize_tactical_daily_sentinel_status(result['tactical_daily_sentinel']), status(1))
        self.assertEqual(len(sent), 1)
        self.assertEqual(state.semantic_snapshot()['date_raw'], before['date_raw'])
        self.assertEqual(state.semantic_snapshot()['native_revision'], before['native_revision'])
        self.assertIs(state.semantic_snapshot()['paused'], True)


class Continuous14PrepareJsonBoundaryTests(unittest.TestCase):
    """Actual generic/engine/profile/JSON producers with a software-only identity provider."""

    def context(self, root: Path, *, continuous: bool = True) -> dict[str, object]:
        import ck3_mod_acceptance_prepare as preparation
        shared = root / 'owned-software-shared'
        provider = shared / 'tools/fixture_engine_prepare.py'
        provider.parent.mkdir(parents=True)
        # Only the installed-engine identity boundary is authored. The real
        # _engine function loads it, validates it and creates its private tuple.
        provider.write_text("def engine_identity(repo, **kwargs):\n"
            "    return {'game_version':'software-only', 'exe_sha256':'" + '0' * 64 + "'}\n",
            encoding='utf-8')
        product = root / 'owned-software-product'; product.mkdir()
        (product / 'descriptor.mod').write_text('name="Owned software product"\nversion="0"\n', encoding='utf-8')
        plain = {}
        for name in preparation.CONFIG_NAMES:
            path = root / 'owned-software-plain' / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('software-only configuration\n', encoding='utf-8')
            plain[name] = adapter.pin(path)
        saved = root / 'owned-software-input.ck3'
        saved.write_bytes(b'Owned software fixture bytes; no Game SAVE or engine semantics claim.')
        saved_pin = adapter.pin(saved)
        config = json.loads(CONFIG.read_bytes())
        if not continuous:
            config['case_id'] = 'authored-static-load-control'
            config.pop('clock_purpose')
            config['acceptance_scope'] = 'static_and_basicload'
        output = root / 'output'; output.mkdir()
        return {'repo_root': str(REPO), 'shared_source_root': str(shared),
            'game_dir': str(root / 'owned-software-game-identity'),
            'shared_game': {'version': 'software-only', 'exe_sha256': '0' * 64},
            'output': str(output), 'state_dir': str(root / 'state'),
            'product': 'financial-markets', 'case': config['case_id'], 'case_contract': config,
            # Mirror Selection.prepare -> adapter_context(case_inputs), including
            # its explicit saved-case post_start binding; these are software inputs,
            # not observed Game government/title assertions.
            'case_inputs': {'product_dir': str(product), 'plain_configuration': plain,
                'post_start': {'government_key': 'feudal_government',
                    'primary_title_tier_key': 'duchy', 'independent': True}},
            'saved_campaign': {'save': saved_pin['path'], 'bytes': saved_pin['bytes'],
                'sha256': saved_pin['sha256'], 'player_id': 31254, 'date_raw': START}}

    def test_saved_prepare_real_engine_cache_never_crosses_public_json_boundary(self) -> None:
        import ck3_mod_acceptance_prepare as preparation
        with tempfile.TemporaryDirectory() as directory:
            context = self.context(Path(directory))
            with patch.object(preparation, '_engine', wraps=preparation._engine) as actual_engine:
                result = adapter.prepare_case(context)
            self.assertGreaterEqual(actual_engine.call_count, 1)
            internal = actual_engine.call_args_list[-1].args[0]
            cached = internal['_selected_engine']
            self.assertIsInstance(cached, tuple)
            self.assertEqual(len(cached), 2)
            self.assertEqual(type(cached[0]).__name__, 'module')
            # Global JSON admission remains strict; the private cached context
            # is intentionally not a serializable public value.
            with self.assertRaisesRegex(ValueError, 'finite JSON type domain'):
                adapter.json_object(internal)
            self.assertEqual(json.loads(json.dumps(result, allow_nan=False)), result)
            self.assertIs(result['business_contract_applicable'], False)
            self.assertIs(result['business_pass'], False)
            self.assertEqual(result['runtime_status'], 'NOT_RUN')
            self.assertEqual(result['startup']['mode'], 'saved_campaign')
            self.assertNotIn('_selected_engine', json.dumps(result))
            profile = Path(result['profile_preparation']['profile'])
            load = json.loads((profile / 'dlc_load.json').read_bytes())
            self.assertEqual(load['enabled_mods'], ['mod/product.mod', 'mod/fixture.mod'])
            passive = profile / 'mod-content/fixture/common/story_cycles/xfma_clock_cadence_passive.txt'
            self.assertEqual(passive.read_text(encoding='utf-8-sig'), ''.join(
                name + ' = { visible = no }\n' for name in CONTINUOUS14_PASSIVE_STORY_TYPES_V1))
            inventory = Path(result['startup']['saved_campaign']['product_inventory'])
            self.assertEqual(json.loads(inventory.read_bytes())['schema'], 'ck3-saved-campaign-profile-inventory-v2')
            self.assertEqual(json.loads((Path(context['output']) / 'initial-plan.json').read_bytes()), {'steps': []})

    def test_corrupt_contract_still_refuses_before_private_engine_or_profile_materialization(self) -> None:
        import ck3_mod_acceptance_prepare as preparation
        with tempfile.TemporaryDirectory() as directory:
            context = self.context(Path(directory))
            context['case_contract']['continuous14_contract']['days'] = True
            with patch.object(preparation, '_engine', wraps=preparation._engine) as actual_engine:
                with self.assertRaisesRegex(ValueError, 'Exact independent continuous14'):
                    adapter.prepare_case(context)
            self.assertEqual(actual_engine.call_count, 0)
            self.assertFalse((Path(context['state_dir']) / 'profile').exists())
            self.assertFalse((Path(context['output']) / 'empty-load-carrier').exists())

    def test_other_static_load_keeps_its_original_saved_startup_without_passive_catalog(self) -> None:
        import ck3_mod_acceptance_prepare as preparation
        with tempfile.TemporaryDirectory() as directory:
            context = self.context(Path(directory), continuous=False)
            with patch.object(preparation, '_engine', wraps=preparation._engine) as actual_engine:
                result = adapter.prepare_case(context)
            self.assertGreaterEqual(actual_engine.call_count, 1)
            self.assertEqual(result['startup']['mode'], 'saved_campaign')
            self.assertIs(result['business_contract_applicable'], False)
            profile = Path(result['profile_preparation']['profile'])
            self.assertFalse((profile / 'mod-content/fixture/common/story_cycles/xfma_clock_cadence_passive.txt').exists())
            self.assertEqual(json.loads(json.dumps(result, allow_nan=False)), result)

    def test_real_prepared_bound_post_start_runs_without_mutating_original_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            context = self.context(Path(directory))
            context['run_id'] = 'authored-prepared-run'
            prepared = adapter.prepare_case(context)
            compiled, binding = adapter.compiled_contract(context)
            self.assertEqual(compiled['config']['post_start'], context['case_inputs']['post_start'])
            self.assertTrue(all(value is None for value in context['case_contract']['post_start'].values()))
            host, _ = actual_host(); diagnostic = experiment(host)
            calls: list[str] = []
            class Client:
                def snapshot(self): calls.append('snapshot'); return frame()
                def continuous14_diagnostic(self):
                    calls.append('continuous14'); return {'result': diagnostic}
                def checkpoint(self, name, facts): calls.append(name)
            def reviewed_phase(client, selected, name, requirements, snapshot, actual_compiled):
                calls.append(name)
                self.assertEqual(actual_compiled, compiled)
                self.assertEqual(selected['case_contract'], compiled['config'])
                return {'authored_transport_review': name}
            with patch.object(adapter, 'root_phase', side_effect=reviewed_phase):
                result = adapter.run_case(context, Client())
            self.assertEqual(calls, ['snapshot', compiled['config']['gui_phases'][0]['id'],
                'continuous14', compiled['config']['gui_phases'][1]['id'], 'continuous14-case-result'])
            self.assertEqual(result['compiled_contract'], binding)
            self.assertEqual(prepared['startup']['mode'], 'saved_campaign')
            self.assertTrue(all(value is None for value in context['case_contract']['post_start'].values()))
            self.assertIs(result['financial_daily_coverage_verified'], False)
            self.assertIs(result['business_pass'], False)

    def test_bound_run_refuses_nonnull_override_and_other_compiled_drift_before_snapshot(self) -> None:
        for defect in ('nonnull-override', 'compiled-drift'):
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as directory:
                context = self.context(Path(directory))
                context['run_id'] = 'authored-negative-run'
                context['case_contract']['post_start']['government_key'] = 'feudal_government'
                prepared = adapter.prepare_case(context)
                if defect == 'nonnull-override':
                    context['case_inputs']['post_start']['government_key'] = 'clan_government'
                    message = 'Cannot overwrite original product post-start predicate'
                else:
                    path = Path(prepared['assertion_contract']['path'])
                    compiled = json.loads(path.read_bytes())
                    compiled['config']['source_contracts'].append('authored-unreviewed-contract')
                    path.write_text(json.dumps(compiled), encoding='utf-8')
                    message = 'Prepared continuous14 contract differs'
                class Client:
                    def snapshot(inner): self.fail('Rejected binding reached Native snapshot')
                with patch.object(adapter, 'root_phase') as phase:
                    with self.assertRaisesRegex(ValueError, message):
                        adapter.run_case(context, Client())
                phase.assert_not_called()

if __name__ == '__main__':
    unittest.main()
