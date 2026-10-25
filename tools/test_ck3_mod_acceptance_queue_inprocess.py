"""Pure isolated fixtures. No actual lease, bus, process, CK3 or native calls."""
from pathlib import Path
import copy
from typing import NotRequired, TypedDict, get_type_hints
from ck3_mod_acceptance_background_types import CONTROL_QUEUE_MODULE_ORDER_V1, FilePin, JsonObject
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import patch

CANDIDATE = Path(__file__).resolve().parents[1]

class FixtureFrozen(TypedDict):
    files: dict[str, FilePin | JsonObject]
    run_id: str
    state_dir: str
    source_root: str
    argv: list[str]
    runtime_manifest: NotRequired[FilePin]
    launch_requires_fresh_owned_cas_and_background_offline: NotRequired[bool]
    previous_session_closed: NotRequired[bool]
    previous_screen_released: NotRequired[bool]


class NativeExitFixture(TypedDict):
    report: dict[str, object]
    capabilities: dict[str, object]
    diagnostics: dict[str, object]
    hello: dict[str, object]


def normal_exit_fixture(tool_name: str) -> NativeExitFixture:
    """Actual report/SDK field layout; synthetic pipe/PID and no native calls."""
    advertised = ['bridge.identity', 'normal-exit-map-v1']
    hello: dict[str, object] = {
        'type': 'hello', 'protocol_version': 1, 'pid': 123,
        'connection_generation': 1, 'capabilities': list(advertised),
    }
    diagnostics: dict[str, object] = {
        'protocol_version': 1, 'pipe_name': 'pure-pipe', 'connected': True,
        'bridge_pid': 123, 'connection_generation': 1, 'hello': hello,
    }
    capabilities: dict[str, object] = {
        'bridge_capabilities': list(advertised), 'diagnostics': diagnostics,
    }
    properties: dict[str, object] = {}
    required: list[str] = []
    if tool_name in ('ck3_query_normal_exit_context_v1', 'ck3_request_normal_exit_v1'):
        properties['expected_revision'] = {'type': 'string', 'pattern': '^[1-9][0-9]*$'}
        required.append('expected_revision')
    if tool_name == 'ck3_request_normal_exit_v1':
        properties['action'] = {'type': 'string', 'enum': [
            'prepare_confirmation', 'continue_preparation', 'disable_exit_autosave', 'confirm_desktop',
        ]}
        properties['expected_exit_context_signature'] = {'type': 'string', 'pattern': '^[0-9a-f]{64}$'}
        required.extend(['action', 'expected_exit_context_signature'])
    schema: dict[str, object] = {
        'type': 'object', 'properties': properties, 'required': required, 'additionalProperties': False,
    }
    report: dict[str, object] = {
        'pipe': 'pure-pipe', 'steps': [], 'capabilities': capabilities,
        'mcp_tools': {'tools': [{'name': tool_name, 'inputSchema': schema}]},
    }
    return NativeExitFixture(report=report, capabilities=capabilities, diagnostics=diagnostics, hello=hello)


def pin(path: Path) -> FilePin:
    raw=path.read_bytes()
    return FilePin(path=str(path.resolve()),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())

def load(path: Path, name: str) -> types.ModuleType:
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:
        raise ValueError('Fixture module loader unavailable')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class InprocessQueueTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='lyd-pure-queue-')
        self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name).resolve()
        self.helpers=self.root/'selected-tools';self.helpers.mkdir()
        for name in CONTROL_QUEUE_MODULE_ORDER_V1:
            file=name+'.py'
            shutil.copyfile(CANDIDATE/'tools'/file,self.helpers/file)
        self.queue=self.helpers/'ck3_mod_acceptance_queue.py'
        files: dict[str, FilePin | JsonObject]={str(path.resolve()):pin(path)for path in self.helpers.iterdir()}
        self.live=self.root/'live';self.live.mkdir()
        self.controls=self.live/'controls';self.controls.mkdir()
        self.keeper=self.root/'keeper';self.keeper.mkdir()
        self.state=self.root/'state';self.state.mkdir()
        self.source=self.root/'source';self.source.mkdir()
        self.frozen: FixtureFrozen={'files':files,'run_id':'pure-fixture-run','state_dir':str(self.state),'source_root':str(self.source),
                     'argv':['python','host.py','--agent-source-root',str(self.source),'--bridge-pipe','pure-pipe','--control-plan-dir',str(self.controls)]}
        self.report={'state_dir':str(self.state),'agent_source_root':str(self.source),'pipe':'pure-pipe','phase':'hold',
                     'hold_until_utc_estimated':time.time()+1000,'steps':[],
                     'mcp_tools':{'tools':[{'name':'fixture_readonly_query','inputSchema':{'type':'object','properties':{},'additionalProperties':False}}]}}
        (self.live/'native-report.json').write_text(json.dumps(self.report),encoding='utf-8')
        self.client_module=load(CANDIDATE/'tools/ck3_mod_acceptance_client.py','pure_selected_case_client')
        self.bundle=self.client_module.load_pinned_control_queue(self.queue,self.frozen)
        self.module=self.bundle['module']
        self.module.frozen_run=lambda *a,**k:(self.frozen,{'keeper_root':str(self.keeper)})
        self.lease_calls: list[tuple[tuple[object,...],dict[str,object]]]=[]
        def lease(*args,**kwargs):
            self.lease_calls.append((args,kwargs))
            return {'lease':{'task_id':'pure-task','sequence':1}}
        self.module.live_lease=lease
        self.client=self.client_module.CaseClient.__new__(self.client_module.CaseClient)
        self.client.selection=types.SimpleNamespace(locations={'python':Path(sys.executable),'repo_root':self.root},
            runtime_environment={},runtime={'control_queue':pin(self.queue)},runtime_path=self.root/'runtime.json')
        self.client.frozen=self.frozen;self.client.live=self.live
        self.client.output=self.root/'case-output';self.client.output.mkdir()
        self.client._queue_library=self.bundle
        self.client.guard=lambda *a,**k:self.report
        self.client.remaining=lambda:1000
        self.steps=[{'id':'pure-step','tool':'fixture_readonly_query','args':{},'fresh_revision':False}]
        self.rows=[{'id':'pure-step','ok':True,'finished_at':'fixture-only','result':{'fixture':True}}]
        self.await_calls: list[tuple[object,...]]=[]
        def await_steps(*args):self.await_calls.append(args);return self.rows
        self.client.await_steps=await_steps

    def test_01_complete_selected_modules_do_not_import_main_siblings(self):
        poisoned={name:types.ModuleType('poisoned_'+name)for name in CONTROL_QUEUE_MODULE_ORDER_V1}
        with patch.dict(sys.modules,poisoned):
            bundle=self.client_module.load_pinned_control_queue(self.queue,self.frozen)
            self.assertIs(bundle['module'].live_lease,bundle['modules']['ck3_mod_acceptance_keeper'].live_lease)
            self.assertIs(bundle['module'].frozen_run,bundle['modules']['ck3_mod_acceptance_launcher'].frozen_run)
            for name,module in poisoned.items():self.assertIs(sys.modules[name],module)
        self.assertEqual(Path(bundle['module'].__file__),self.queue)
        modules=bundle['modules']
        self.assertIs(modules['ck3_mod_acceptance_steam_gate'].ProcessIdentity,
                      modules['steam_offline_state_contract'].ProcessIdentity)
        self.assertIs(modules['steam_offline_native_provider_v1'].ProcessIdentity,
                      modules['steam_offline_state_contract'].ProcessIdentity)
        self.assertIs(get_type_hints(modules['steam_offline_state_contract'].parse_result)['return'],
                      modules['steam_offline_state_contract'].ProbeResult)

    def test_02_cached_code_still_checks_exact_frozen_bytes(self):
        keeper=self.helpers/'ck3_mod_acceptance_keeper.py'
        keeper.write_bytes(keeper.read_bytes()+b'\n# fixture mutation\n')
        with self.assertRaisesRegex(ValueError,'bytes changed'):
            self.client_module.load_pinned_control_queue(self.queue,self.frozen,self.bundle)
        with patch.object(self.client_module.subprocess,'run',side_effect=AssertionError('no binding failure fallback')):
            with self.assertRaisesRegex(ValueError,'queue failed'):
                self.client.execute_plan(self.steps,'changed-sibling')
        ack=json.loads((self.client.output/'changed-sibling.stdout.log').read_bytes())
        self.assertEqual(ack['status'],'BLOCKED_NEVER_REPLAY')
        self.assertFalse(list(self.controls.iterdir()))

    def test_03_direct_ack_original_refs_rows_and_no_queue_subprocess(self):
        with patch.object(self.client_module.subprocess,'run',side_effect=AssertionError('queue subprocess forbidden in direct fixture')):
            rows=self.client.execute_plan(self.steps,'direct')
        self.assertIs(rows,self.rows)
        self.assertEqual(len(self.lease_calls),2)
        self.assertTrue(all('deadline'in kwargs for _,kwargs in self.lease_calls))
        ack=json.loads((self.client.output/'direct.stdout.log').read_bytes())
        self.assertEqual(ack['status'],'QUEUED_ONCE_ACK_NOT_BUSINESS_PASS')
        self.assertFalse(ack['business_pass'])
        self.assertEqual(ack['published'],pin(self.controls/'direct.json'))
        self.assertEqual(ack['plan'],pin(self.client.output/'plans/direct.json'))
        self.assertEqual((self.controls/'direct.json').read_bytes(),(self.client.output/'plans/direct.json').read_bytes())
        result=json.loads((self.client.output/'direct.queue-result.json').read_bytes())
        self.assertEqual(result['execution_mode'],'IN_PROCESS_PINNED_QUEUE_LIBRARY')
        self.assertFalse(result['argv_executed']);self.assertEqual(result['exit_code'],0)
        self.assertEqual(len(self.await_calls),1)

    def test_04_initial_lease_refusal_never_publishes_or_falls_back(self):
        count=[]
        def refused(*a,**k):count.append(1);raise RuntimeError('actual lease refused fixture')
        self.module.live_lease=refused
        with patch.object(self.client_module.subprocess,'run',side_effect=AssertionError('no failure fallback')):
            with self.assertRaisesRegex(ValueError,'queue failed'):
                self.client.execute_plan(self.steps,'refused')
        self.assertEqual(len(count),1);self.assertFalse(list(self.controls.iterdir()))
        self.assertFalse((self.live/'control-once-ledger').exists());self.assertFalse(self.await_calls)
        ack=json.loads((self.client.output/'refused.stdout.log').read_bytes())
        self.assertEqual(ack['status'],'BLOCKED_NEVER_REPLAY')

    def test_05_second_lease_refusal_preserves_claim_and_never_retries(self):
        count=[]
        def lease(*a,**k):
            count.append(1)
            if len(count)==2:raise RuntimeError('lease changed before publish fixture')
            return {'lease':{'sequence':1}}
        self.module.live_lease=lease
        with patch.object(self.client_module.subprocess,'run',side_effect=AssertionError('no failure fallback')):
            with self.assertRaisesRegex(ValueError,'queue failed'):
                self.client.execute_plan(self.steps,'second-refused')
            with self.assertRaises(FileExistsError):
                self.client.execute_plan(self.steps,'second-refused')
        self.assertEqual(len(count),2)
        self.assertFalse(list(self.controls.glob('*.json')))
        self.assertTrue(list((self.live/'control-once-ledger').glob('step-*.json')))
        self.assertFalse(self.await_calls)

    def test_06_legacy_selection_happens_before_submit_and_only_once(self):
        # Test a fresh once-only name for each legitimate eligibility mismatch.
        scenarios=('environment','python','old-api','legacy-error')
        for reason in scenarios:
            with self.subTest(reason=reason):
                old_python=self.client.selection.locations['python']
                old_environment=self.client.selection.runtime_environment
                original_deadline=self.module.enqueue_deadline
                if reason in ('environment','legacy-error'):
                    selected='selected-value'if os.environ.get('LYD_PURE_TEST_REQUIRED_ENV')!='selected-value'else'other-selected-value'
                    self.client.selection.runtime_environment={'LYD_PURE_TEST_REQUIRED_ENV':selected}
                elif reason=='python':self.client.selection.locations['python']=self.root/'different-python.exe'
                else:del self.module.enqueue_deadline
                try:
                    with patch.object(self.client_module.subprocess,'run',return_value=types.SimpleNamespace(returncode=2 if reason=='legacy-error'else 0))as called:
                        if reason=='legacy-error':
                            with self.assertRaisesRegex(ValueError,'queue failed'):self.client.execute_plan(self.steps,'legacy-'+reason)
                        else:self.client.execute_plan(self.steps,'legacy-'+reason)
                    self.assertEqual(called.call_count,1)
                    record=json.loads((self.client.output/('legacy-'+reason+'.queue-result.json')).read_bytes())
                    self.assertEqual(record['execution_mode'],'LEGACY_QUEUE_SUBPROCESS')
                    self.assertTrue(record['argv_executed']);self.assertTrue(record['legacy_reasons'])
                    self.assertEqual(called.call_args.kwargs['env'].get('LYD_PURE_TEST_REQUIRED_ENV'),
                                     os.environ.get('LYD_PURE_TEST_REQUIRED_ENV')if reason not in ('environment','legacy-error')else selected)
                finally:
                    self.client.selection.locations['python']=old_python
                    self.client.selection.runtime_environment=old_environment
                    self.module.enqueue_deadline=original_deadline
        self.assertFalse(self.lease_calls)

    def test_07_each_git_and_bus_process_gets_remaining_original_deadline(self):
        module=load(CANDIDATE/'promo/ck3_native_war_ai/integration/screen_bus_lease.py','pure_deadline_screen_lease')
        results=[types.SimpleNamespace(stdout='a'*40+'\n'),types.SimpleNamespace(stdout='')]
        with patch.object(module.time,'monotonic',side_effect=[100,102]),patch.object(module.subprocess,'run',side_effect=results)as calls:
            self.assertEqual(module.checkout_head(self.root,deadline=105),'a'*40)
        self.assertEqual([c.kwargs['timeout']for c in calls.call_args_list],[5,3])
        body=json.dumps({'schema':'codex.task_bus.v1','ok':True}).encode()
        with patch.object(module,'checked_cli_pair'),patch.object(module.time,'monotonic',return_value=103),patch.object(module.subprocess,'run',return_value=types.SimpleNamespace(returncode=0,stdout=body,stderr=b''))as calls:
            self.assertTrue(module.call_bus(self.root/'source',self.root,'A'*64,'list',deadline=105)['ok'])
        self.assertEqual(calls.call_args.kwargs['timeout'],2)
        with patch.object(module,'checked_cli_pair'),patch.object(module.time,'monotonic',return_value=105),patch.object(module.subprocess,'run')as calls:
            with self.assertRaises(TimeoutError):module.call_bus(self.root/'source',self.root,'A'*64,'list',deadline=105)
        calls.assert_not_called()

    def test_08_expiry_after_final_cas_read_refuses_publication(self):
        plan=self.root/'late-plan.json';plan.write_text(json.dumps({'steps':self.steps}),encoding='utf-8')
        clock=[100];calls=[]
        def lease(*a,**k):
            calls.append(k)
            if len(calls)==2:clock[0]=150
            return {'lease':{'sequence':1}}
        self.module.live_lease=lease
        with patch.object(self.module.time,'monotonic',side_effect=lambda:clock[0]):
            with self.assertRaises(TimeoutError):self.module.enqueue(self.live,plan,'late.json',deadline=150)
        self.assertEqual(len(calls),2);self.assertFalse((self.controls/'late.json').exists())
        self.assertTrue(list((self.live/'control-once-ledger').glob('step-*.json')))

    def test_09_cli_default_and_optional_deadline_share_original_enqueue(self):
        for timeout,expected in ((None,None),('7',107)):
            argv=['--live',str(self.live),'--plan',str(self.root/'unused-plan'),'--name','cli.json']
            if timeout is not None:argv.extend(['--timeout-seconds',timeout])
            with patch.object(self.module,'enqueue',return_value={'fixture_only':True})as enqueue,patch.object(self.module.time,'monotonic',return_value=100),contextlib.redirect_stdout(io.StringIO())as output:
                self.assertEqual(self.module.main(argv),0)
            self.assertEqual(enqueue.call_args.kwargs['deadline'],expected)
            self.assertEqual(json.loads(output.getvalue()),{'fixture_only':True})

    def test_normal_exit_default_off_refuses_before_claim_publish_or_host(self) -> None:
        actions = ('prepare_confirmation', 'continue_preparation', 'disable_exit_autosave', 'confirm_desktop')
        scenarios = [('ck3_query_normal_exit_context_v1', '')]
        scenarios.extend(('ck3_request_normal_exit_v1', action) for action in actions)
        for index, (tool_name, action) in enumerate(scenarios):
            with self.subTest(tool=tool_name, action=action):
                fixture = normal_exit_fixture(tool_name)
                fixture['capabilities']['bridge_capabilities'] = ['bridge.identity']
                fixture['hello']['capabilities'] = ['bridge.identity']
                self.report.update(fixture['report'])
                (self.live/'native-report.json').write_text(json.dumps(self.report), encoding='utf-8')
                arguments: dict[str, object] = {}
                if action:
                    arguments.update(action=action, expected_exit_context_signature='a'*64)
                steps = [{'id': 'native-off-'+str(index), 'tool': tool_name, 'args': arguments}]
                with patch.object(self.module, 'claim_plan', side_effect=AssertionError('must reject before once-only claim')), \
                     patch.object(self.module.os, 'link', side_effect=AssertionError('must never publish')), \
                     patch.object(self.client_module.subprocess, 'run', side_effect=AssertionError('no subprocess fallback')):
                    with self.assertRaisesRegex(ValueError, 'queue failed'):
                        self.client.execute_plan(steps, 'native-off-'+str(index))
                ack = json.loads((self.client.output/('native-off-'+str(index)+'.stdout.log')).read_bytes())
                self.assertEqual(ack['status'], 'BLOCKED_NEVER_REPLAY')
                self.assertIn('normal-exit-map-v1 capability is unavailable', ack['error'])
                self.assertIs(ack['business_pass'], False)
        self.assertEqual(len(self.lease_calls), len(scenarios))
        self.assertFalse(list(self.controls.iterdir()))
        self.assertFalse((self.live/'control-once-ledger').exists())
        self.assertFalse(self.await_calls)

    def test_normal_exit_supported_query_and_each_request_preserve_exact_plan(self) -> None:
        scenarios = [('ck3_query_normal_exit_context_v1', '')]
        scenarios.extend(('ck3_request_normal_exit_v1', action) for action in
                         ('prepare_confirmation', 'continue_preparation', 'disable_exit_autosave', 'confirm_desktop'))
        for index, (tool_name, action) in enumerate(scenarios):
            fixture = normal_exit_fixture(tool_name)
            self.report.update(fixture['report'])
            (self.live/'native-report.json').write_text(json.dumps(self.report), encoding='utf-8')
            arguments: dict[str, object] = {}
            if action:
                arguments.update(action=action, expected_exit_context_signature='b'*64)
            label = 'native-supported-'+str(index)
            steps = [{'id': label, 'tool': tool_name, 'args': arguments}]
            with patch.object(self.client_module.subprocess, 'run', side_effect=AssertionError('no native/host process')):
                self.client.execute_plan(steps, label)
            self.assertEqual((self.controls/(label+'.json')).read_bytes(),
                             (self.client.output/('plans/'+label+'.json')).read_bytes())
            ack = json.loads((self.client.output/(label+'.stdout.log')).read_bytes())
            self.assertEqual(ack['status'], 'QUEUED_ONCE_ACK_NOT_BUSINESS_PASS')
            self.assertIs(ack['business_pass'], False)
        self.assertEqual(len(self.lease_calls), 2*len(scenarios))
        self.assertEqual(len(self.await_calls), len(scenarios))

    def test_failed_R0007_host_allows_only_the_existing_typed_exit_route(self) -> None:
        capture = CANDIDATE/'ck3_autonomous_player/tests/fixtures/scripted_widget_owner_sampling_R0007.json'
        failure = json.loads(capture.read_bytes())['failed_host_error']
        scenarios = [('ck3_query_normal_exit_context_v1', '')]
        scenarios.extend(('ck3_request_normal_exit_v1', action) for action in (
            'prepare_confirmation', 'continue_preparation', 'disable_exit_autosave', 'confirm_desktop'))
        scenarios.append(('ck3_observe_normal_exit_v1', ''))
        for index, (tool, action) in enumerate(scenarios):
            fixture = normal_exit_fixture(tool)
            self.report.update(fixture['report'])
            self.report['error'] = failure
            (self.live/'native-report.json').write_text(json.dumps(self.report),encoding='utf-8')
            arguments: dict[str, object] = {}
            if action: arguments.update(action=action, expected_exit_context_signature='b'*64)
            steps = [{'id':'failed-exit-'+str(index),'tool':tool,'args':arguments,'fresh_revision':True}]
            plan = self.root/('failed-exit-'+str(index)+'.json')
            plan.write_text(json.dumps({'steps':steps}),encoding='utf-8')
            result = self.module.enqueue(self.live,plan,plan.name)
            self.assertEqual(result['status'],'QUEUED_ONCE_ACK_NOT_BUSINESS_PASS')
            self.assertEqual(json.loads((self.live/'native-report.json').read_bytes())['error'],failure)
            self.assertEqual(json.loads((self.controls/plan.name).read_bytes())['steps'],steps)

    def test_failed_host_rejects_business_mixed_exit_and_bad_revision_before_claim(self) -> None:
        from jsonschema import ValidationError
        fixture = normal_exit_fixture('ck3_query_normal_exit_context_v1')
        self.report.update(fixture['report'])
        catalog = self.report['mcp_tools']
        assert isinstance(catalog, dict)
        advertised = catalog['tools']
        assert isinstance(advertised, list)
        advertised.append({'name':'fixture_readonly_query',
            'inputSchema':{'type':'object','properties':{},'additionalProperties':False}})
        self.report['error'] = 'RuntimeError: original R0007 owner failure'
        (self.live/'native-report.json').write_text(json.dumps(self.report),encoding='utf-8')
        business = {'id':'business-after-failure','tool':'fixture_readonly_query','args':{}}
        query = {'id':'quit-after-failure','tool':'ck3_query_normal_exit_context_v1','args':{}}
        invalid = [[business],[query,business],[dict(query,unexpected=True)],
            [dict(query,fresh_revision=False)],
            [dict(query,args={'expected_revision':True})],
            [dict(query,args={'expected_revision':1})],
            [dict(query,args={'expected_revision':1.0})]]
        for index, steps in enumerate(invalid):
            plan = self.root/('failed-reject-'+str(index)+'.json')
            plan.write_text(json.dumps({'steps':steps}),encoding='utf-8')
            with patch.object(self.module,'claim_plan',side_effect=AssertionError('must reject before claim')):
                with self.assertRaises((ValueError,ValidationError)):
                    self.module.enqueue(self.live,plan,plan.name)
            self.assertFalse((self.controls/plan.name).exists())

    def test_os_normal_exit_observer_and_other_normal_exit_named_tool_are_not_native_gated(self) -> None:
        for index, tool_name in enumerate(('ck3_observe_normal_exit_v1',
                                          'ck3_query_zhongguo_workforce_normal_exit_snapshot_v1')):
            fixture = normal_exit_fixture(tool_name)
            # No native hello/capabilities whatsoever: OS retained-handle
            # observation must remain available after transport has disappeared.
            fixture['report'].pop('capabilities')
            self.report.update(fixture['report'])
            self.report.pop('capabilities', None)
            (self.live/'native-report.json').write_text(json.dumps(self.report), encoding='utf-8')
            label = 'observer-only-'+str(index)
            self.client.execute_plan([{'id': label, 'tool': tool_name, 'args': {}}], label)
            self.assertTrue((self.controls/(label+'.json')).is_file())
        self.assertEqual(len(self.await_calls), 2)

    def test_normal_exit_native_evidence_rejects_unknown_malformed_or_crossed_binding(self) -> None:
        mutations: tuple[tuple[str, str, object], ...] = (
            ('report', 'capabilities', None),
            ('capabilities', 'diagnostics', []),
            ('capabilities', 'bridge_capabilities', True),
            ('capabilities', 'bridge_capabilities', ['bridge.identity']),
            ('capabilities', 'bridge_capabilities', ['normal-exit-map-v1', 'normal-exit-map-v1']),
            ('diagnostics', 'hello', None),
            ('diagnostics', 'pipe_name', 'foreign-pipe'),
            ('diagnostics', 'connected', 1),
            ('diagnostics', 'protocol_version', True),
            ('diagnostics', 'protocol_version', 1.0),
            ('diagnostics', 'bridge_pid', True),
            ('diagnostics', 'bridge_pid', 123.0),
            ('diagnostics', 'bridge_pid', 0x100000000),
            ('diagnostics', 'connection_generation', False),
            ('hello', 'type', 'metadata'),
            ('hello', 'protocol_version', 1.0),
            ('hello', 'pid', 124),
            ('hello', 'pid', 123.0),
            ('hello', 'connection_generation', 2),
            ('hello', 'connection_generation', True),
            ('hello', 'capabilities', {'normal-exit-map-v1': True}),
            ('hello', 'capabilities', ['bridge.identity', True]),
            ('hello', 'capabilities', ['bridge.identity', 'game.command.normal-exit-map-v1']),
        )
        for target_name, field, invalid in mutations:
            with self.subTest(target=target_name, field=field, invalid=invalid):
                fixture = normal_exit_fixture('ck3_query_normal_exit_context_v1')
                targets = {'report': fixture['report'], 'capabilities': fixture['capabilities'],
                           'diagnostics': fixture['diagnostics'], 'hello': fixture['hello']}
                targets[target_name][field] = invalid
                with self.assertRaises(ValueError):
                    self.module.validate_steps([{'id': 'bad-native', 'tool': 'ck3_query_normal_exit_context_v1'}],
                                               fixture['report'])
        for target_name, field in (('report', 'capabilities'), ('capabilities', 'bridge_capabilities'),
                                   ('capabilities', 'diagnostics'), ('diagnostics', 'hello'),
                                   ('hello', 'capabilities'), ('hello', 'pid'), ('hello', 'connection_generation')):
            with self.subTest(missing=target_name+'.'+field):
                fixture = normal_exit_fixture('ck3_query_normal_exit_context_v1')
                targets = {'report': fixture['report'], 'capabilities': fixture['capabilities'],
                           'diagnostics': fixture['diagnostics'], 'hello': fixture['hello']}
                targets[target_name].pop(field)
                with self.assertRaises(ValueError):
                    self.module.validate_steps([{'id': 'missing-native', 'tool': 'ck3_query_normal_exit_context_v1'}],
                                               fixture['report'])

    def test_normal_exit_json_roundtrip_and_exact_unprefixed_capability(self) -> None:
        fixture = normal_exit_fixture('ck3_query_normal_exit_context_v1')
        report = json.loads(json.dumps(fixture['report']))
        steps = [{'id': 'roundtrip-native', 'tool': 'ck3_query_normal_exit_context_v1', 'args': {}}]
        self.assertEqual(self.module.validate_steps(json.loads(json.dumps(steps)), report), ['roundtrip-native'])
        # Both mirrors can agree on an alias and still fail: the actual SDK
        # accepts only normal-exit-map-v1, without a game.command prefix.
        fixture['capabilities']['bridge_capabilities'] = ['game.command.normal-exit-map-v1']
        fixture['hello']['capabilities'] = ['game.command.normal-exit-map-v1']
        with self.assertRaisesRegex(ValueError, 'capability is unavailable'):
            self.module.validate_steps(steps, fixture['report'])

    def tearDown(self) -> None:
        # Release only this test's selected modules; public/importing peers stay.
        for name, module in tuple(sys.modules.items()):
            if not name.startswith('_selected_control_queue_') or not isinstance(module,types.ModuleType):
                continue
            location=getattr(module,'__file__',None)
            if isinstance(location,str) and Path(location).parent==self.helpers:
                if sys.modules.get(name) is module:
                    del sys.modules[name]

    def test_10_shared_closure_matches_actual_launcher_required_pins(self) -> None:
        launcher=self.bundle['modules']['ck3_mod_acceptance_launcher']
        self.assertIs(launcher.frozen_run.__globals__['CONTROL_QUEUE_MODULE_ORDER_V1'],
                      launcher.CONTROL_QUEUE_MODULE_ORDER_V1)
        self.assertEqual(launcher.CONTROL_QUEUE_MODULE_ORDER_V1,CONTROL_QUEUE_MODULE_ORDER_V1)
        self.assertEqual(len(CONTROL_QUEUE_MODULE_ORDER_V1),len(set(CONTROL_QUEUE_MODULE_ORDER_V1)))
        self.assertEqual(set(self.bundle['modules']),set(CONTROL_QUEUE_MODULE_ORDER_V1))
        launcher=self.bundle['modules']['ck3_mod_acceptance_launcher']
        host=self.root/'host.py';host.write_text('# no process is launched\n',encoding='utf-8')
        manifest=self.root/'manifest.json';manifest.write_text('{}',encoding='utf-8')
        frozen=copy.deepcopy(self.frozen)
        frozen['launch_requires_fresh_owned_cas_and_background_offline']=True
        frozen['previous_session_closed']=True
        frozen['previous_screen_released']=True
        frozen['runtime_manifest']=pin(manifest)
        frozen['argv']=['python',str(host),'--agent-source-root',str(self.source)]
        frozen['files'][str(host.resolve())]=pin(host)

        def publish() -> None:
            path=self.live/'frozen-argv.json'
            path.write_text(json.dumps(frozen),encoding='utf-8')
            context={'frozen_argv':pin(path),'run_id':frozen['run_id'],'run_dir':str(self.live)}
            (self.live/'ready-context.json').write_text(json.dumps(context),encoding='utf-8')

        # Exercise the real selected launcher, including its on-disk boundary.
        # Missing helper pins must fail even when broad input revalidation is off.
        publish()
        for all_pins in (True,False):
            checked,_=launcher.frozen_run(self.live,all_pins=all_pins)
            self.assertEqual(checked['run_id'],frozen['run_id'])
        for name in CONTROL_QUEUE_MODULE_ORDER_V1:
            with self.subTest(helper=name):
                key=str((self.helpers/(name+'.py')).resolve())
                original=frozen['files'].pop(key)
                publish()
                with self.assertRaisesRegex(ValueError,'Public helper is absent'):
                    launcher.frozen_run(self.live,all_pins=False)
                frozen['files'][key]=original

    def test_11_each_helper_requires_present_exact_runtime_pin(self) -> None:
        for name in CONTROL_QUEUE_MODULE_ORDER_V1:
            key=str(self.helpers/(name+'.py'))
            for mode in ('missing','boolean_bytes','float_bytes','wrong_sha'):
                with self.subTest(module=name,mode=mode):
                    frozen=copy.deepcopy(self.frozen)
                    if mode=='missing':
                        del frozen['files'][key]
                    elif mode=='boolean_bytes':
                        frozen['files'][key]['bytes']=True
                    elif mode=='float_bytes':
                        frozen['files'][key]['bytes']=float(frozen['files'][key]['bytes'])
                    else:
                        frozen['files'][key]['sha256']='0'*64
                    with self.assertRaises(ValueError):
                        self.client_module.load_pinned_control_queue(self.queue,frozen,self.bundle)

    def test_12_changed_transitive_closure_never_executes_or_reuses_cache(self) -> None:
        source=self.helpers/'steam_offline_native_profiles.py'
        source.write_bytes(source.read_bytes()+b'\nraise AssertionError("new closure must not execute")\n')
        frozen=copy.deepcopy(self.frozen)
        frozen['files'][str(source)]=pin(source)
        before={name:sys.modules[name] for name in
                (module.__name__ for module in self.bundle['modules'].values())}
        with self.assertRaisesRegex(ValueError,'closure changed'):
            self.client_module.load_pinned_control_queue(self.queue,frozen,self.bundle)
        for name,module in before.items():
            self.assertIs(sys.modules[name],module)

    def test_13_unknown_sibling_import_rolls_back_only_owned_registry(self) -> None:
        original=self.queue.read_bytes()
        retained_name='_selected_control_queue_unrelated_retained_fixture'
        retained=types.ModuleType(retained_name)
        for foreign in ('ck3_mod_acceptance_unpinned_fixture','steam_offline_unpinned_fixture'):
            with self.subTest(module=foreign):
                self.queue.write_bytes(original+('\nimport '+foreign+'\n').encode())
                frozen=copy.deepcopy(self.frozen)
                frozen['files'][str(self.queue)]=pin(self.queue)
                poisoned={name:types.ModuleType('poisoned_'+name)
                          for name in (*CONTROL_QUEUE_MODULE_ORDER_V1,foreign)}
                poisoned[retained_name]=retained
                with patch.dict(sys.modules,poisoned):
                    before={name:module for name,module in sys.modules.items()
                            if name.startswith('_selected_control_queue_')}
                    with self.assertRaisesRegex(ImportError,'Unpinned selected queue sibling import'):
                        self.client_module.load_pinned_control_queue(self.queue,frozen)
                    after={name:module for name,module in sys.modules.items()
                           if name.startswith('_selected_control_queue_')}
                    self.assertEqual(before,after)
                    for name,module in poisoned.items():
                        self.assertIs(sys.modules[name],module)

    def test_14_identical_closure_has_independent_private_module_instances(self) -> None:
        second=self.client_module.load_pinned_control_queue(self.queue,self.frozen)
        closure=hashlib.sha256(json.dumps(self.bundle['refs'],sort_keys=True,
                              separators=(',',':')).encode('utf-8')).hexdigest()
        self.assertEqual(self.bundle['refs'],second['refs'])
        for name in CONTROL_QUEUE_MODULE_ORDER_V1:
            original,rebound=self.bundle['modules'][name],second['modules'][name]
            self.assertIsNot(original,rebound)
            self.assertNotEqual(original.__name__,rebound.__name__)
            self.assertIn(closure,original.__name__)
            self.assertIn(closure,rebound.__name__)
            self.assertIs(sys.modules[original.__name__],original)
            self.assertIs(sys.modules[rebound.__name__],rebound)
        second['module'].fixture_mutable_state=['second only']
        self.assertFalse(hasattr(self.bundle['module'],'fixture_mutable_state'))
        self.assertIs(self.client_module.load_pinned_control_queue(
            self.queue,self.frozen,self.bundle),self.bundle)

    def test_15_namespace_collision_preserves_previous_binding(self) -> None:
        import secrets
        with patch.object(secrets,'token_hex',return_value='f'*32):
            first=self.client_module.load_pinned_control_queue(self.queue,self.frozen)
            before={module.__name__:module for module in first['modules'].values()}
            with self.assertRaisesRegex(ValueError,'namespace collision'):
                self.client_module.load_pinned_control_queue(self.queue,self.frozen)
            for name,module in before.items():
                self.assertIs(sys.modules[name],module)

    def test_16_base_exception_rolls_back_all_new_private_modules(self) -> None:
        self.queue.write_bytes(self.queue.read_bytes()+b'\nraise SystemExit("synthetic module refusal")\n')
        frozen=copy.deepcopy(self.frozen)
        frozen['files'][str(self.queue)]=pin(self.queue)
        before={name:module for name,module in sys.modules.items()
                if name.startswith('_selected_control_queue_')}
        with self.assertRaisesRegex(SystemExit,'synthetic module refusal'):
            self.client_module.load_pinned_control_queue(self.queue,frozen)
        after={name:module for name,module in sys.modules.items()
               if name.startswith('_selected_control_queue_')}
        self.assertEqual(before,after)

    def test_17_loader_public_annotations_resolve_to_shared_binding(self) -> None:
        from ck3_mod_acceptance_background_types import ControlQueueBindingV1
        hints=get_type_hints(self.client_module.load_pinned_control_queue)
        self.assertIs(hints['return'],ControlQueueBindingV1)
        binding_hints=get_type_hints(ControlQueueBindingV1)
        self.assertEqual(set(binding_hints),{'refs','module','modules'})
        self.assertEqual(binding_hints['module'],types.ModuleType)

    def test_18_keyed_pins_do_not_override_an_explicit_declared_path(self) -> None:
        # The real allocator stores bytes/sha256 under the absolute path key.
        keyed = copy.deepcopy(self.frozen)
        keyed['files'] = {key: {'bytes': row['bytes'], 'sha256': row['sha256']}
                          for key, row in keyed['files'].items()}
        roundtrip = json.loads(json.dumps(keyed))
        rebound = self.client_module.load_pinned_control_queue(self.queue, roundtrip)
        self.assertEqual(rebound['refs'], self.bundle['refs'])
        self.assertIs(self.client_module.load_pinned_control_queue(
            self.queue, roundtrip, self.bundle), self.bundle)
        for name in CONTROL_QUEUE_MODULE_ORDER_V1:
            key = str(self.helpers / (name + '.py'))
            for wrong in ('another-selected-source.py', None, True):
                for cached in (False, True):
                    with self.subTest(helper=name, declared_path=wrong, cached=cached):
                        frozen = copy.deepcopy(self.frozen)
                        frozen['files'][key]['path'] = wrong
                        with self.assertRaises(ValueError):
                            self.client_module.load_pinned_control_queue(
                                self.queue, frozen, self.bundle if cached else None)

if __name__ == '__main__':
    unittest.main()
