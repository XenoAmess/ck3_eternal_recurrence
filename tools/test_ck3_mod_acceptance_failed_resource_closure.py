"""Offline regression for an actual failed-case resource boundary, with no process queries."""
from __future__ import annotations
import ast
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

TOOLS=Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:sys.path.insert(0,str(TOOLS))
import ck3_mod_acceptance_allocate as allocation
from ck3_mod_acceptance_background_types import FilePin, JsonObject, json_object, object_field, text_field


class FailedResourceClosureTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.run=self.root/'R0069';self.run.mkdir()
        (self.run/'case-output').mkdir();self.keeper=self.root/'a32';self.keeper.mkdir()
        self.state=self.root/'CASE020/state';self.state.mkdir(parents=True)
        self.freeze={'run_id':'R0069','screen_task':'screen-a32','cell':'release012-keypaths',
                     'argv':['python','host.py','--output',str(self.run/'native-report.json')],
                     'state_dir':str(self.state)}
        self.write(self.run/'frozen-argv.json',self.freeze)
        self.normal={'normal_close_qualified':False,'business_pass':False,'native_zero_proof':None}
        normal=self.write(self.run/'case-output/normal-close-result.json',self.normal)
        self.host={'run_id':'R0069','pid':7564,'create_time':100.0,'supervisor_pid':12876,
                   'argv':self.freeze['argv'],'actual_popen_retained':True}
        host=self.write(self.run/'host-started.json',self.host)
        self.exited={'run_id':'R0069','pid':7564,'returncode':0,'actual_original_popen_wait':True,
                     'normal_ck3_exit_inferred':False,'business_pass':False}
        exited=self.write(self.run/'host-original-process-exit.json',self.exited)
        supervisor=self.write(self.run/'host-supervisor-started.json',{'pid':12876})
        keeper=self.write(self.run/'keeper-process.json',{'pid':13496,'create_time':90.0})
        self.write(self.run/'case-output/retained-current-process-identity.json',
                   {'pid':17168,'create_time':110.0,'retained_synchronize_query_handle_acquired':True})
        context=self.root/'reviewed-context.json'
        self.write(context,{'schema':'ck3-mod-acceptance-run-context-v1','run_id':'R0069','run_dir':str(self.run)})
        prepared=self.state.parent/'prepared/prepared-case.json'
        common=['--runtime',str(self.root/'runtime.json'),'--case','release012-keypaths','--prepared-case',str(prepared)]
        self.public={'schema':'ck3-recorded-actual-command-v1','exit_code':2,'finished_at_utc':'actual',
                     'argv':['python','-B','-X','utf8','overlay_entry.py','run',*common,'--run-context',str(context)]}
        public=self.write(self.root/'run-result.json',self.public)
        allocator=self.write(self.root/'allocator-result.json',{'schema':'ck3-recorded-actual-command-v1',
                'exit_code':0,'finished_at_utc':'actual','argv':['python','overlay_entry.py','allocate',*common,
                '--attempt','a32','--keeper-output',str(self.keeper)]})
        self.keeper_report={'task_id':'screen-a32','last_sequence':5105,'thread_exited':True,
                            'failure':None,'entry_error':None}
        self.write(self.keeper/'report.json',self.keeper_report)
        parent=self.write(self.run/'keeper-actual-parent-exit.json',{'run_id':'R0069',
                          'keeper_actual_exit_code':0,'keeper_report':self.keeper_report,'business_pass':False})
        self.release_path=self.run/'release.json'
        self.release={'schema':'codex.task_bus.v1','ok':True,'task':{'task_id':'screen-a32','state':'done',
                       'resources':[],'last_sequence':5106},'event':{'task_id':'screen-a32','state':'done',
                       'resources':[],'sequence':5106}}
        release=self.write(self.release_path,self.release)
        self.stop={'schema':'lyd.actual-failed-resource-closure.v1','run_id':'R0069','keeper_root':str(self.keeper),
                   'public_run':public,'original_public_exit_code':2,'original_host_started':host,
                   'original_host_supervisor':supervisor,'original_host_exit':exited,
                   'original_host_actual_wait_returncode':0,'original_normal_close_result':normal,
                   'normal_close_result_original':self.normal,'game_os_exit_zero_qualified':False,
                   'normal_gui_quit_qualified':False,'native_cleanup_qualified':None,'native_report_read':False,
                   'business_pass':False,'original_failure_preserved':True,'keeper_process':keeper,
                   'resource_close_only_not_native_or_normal_acceptance':True,
                   'allocator_original_wait':None,'actual_CAS_release':None}
        stop=self.write(self.run/'keeper-stop-proof-001.json',self.stop)
        self.bundle={**self.stop,'original_stop_proof':stop,'allocator_original_wait':allocator,
                     'actual_CAS_release':release,'keeper_actual_exit':parent}
        self.close=self.root/'final-resource-close.json';self.save()
        self.live=set();self.blockers=[];self.bus={'tasks':[]}
        class MissingProcess(Exception):pass
        def process(pid):
            if pid not in self.live:raise MissingProcess()
            return SimpleNamespace(create_time=lambda:{7564:100.0,13496:90.0,17168:110.0}[pid])
        self.psutil=SimpleNamespace(Process=process,NoSuchProcess=MissingProcess,pid_exists=lambda pid:pid in self.live)

    def write(self,path,value):
        path.write_text(json.dumps(value),encoding='utf-8')
        return allocation.pin(path)

    def save(self):self.write(self.close,self.bundle)

    def amend_original(self,key,value):
        row=self.write(Path(self.stop[key]['path']),value)
        self.stop[key]=row;self.bundle[key]=row
        self.bundle['original_stop_proof']=self.write(self.run/'keeper-stop-proof-001.json',self.stop)
        self.save()

    def check(self):
        original_read=allocation.read_json
        def bounded_read(path):
            if Path(path).name=='native-report.json':raise AssertionError('Native body must not be read')
            return original_read(path)
        with patch.dict(sys.modules,{'psutil':self.psutil}),patch.object(allocation,'read_json',side_effect=bounded_read),\
             patch.object(allocation,'runtime_process_inventory',return_value={'blockers':self.blockers}):
            return allocation.previous_failed_resource_closure(self.run,self.freeze,self.close,self.keeper,
                                                               self.release_path,self.bus)

    def test_r69_shape_admits_resources_and_preserves_all_failed_credit(self):
        result=self.check();proof=result['failure_cleanup']
        self.assertEqual(result['mode'],'previous-shared-failed-attempt-resource-closed')
        self.assertTrue(proof['original_host_wait_proven'])
        for key in ('actual_retained_os0','normal_close_qualified','typed_normal_exit_proven','business_pass','release_pass'):
            self.assertIs(proof[key],False)
        self.assertIsNone(proof['original_ck3_exit_code']);self.assertIsNone(proof['native_cleanup_qualified'])

    def test_original_host_still_alive_rejected(self):
        self.live.add(7564)
        with self.assertRaisesRegex(ValueError,'host still present'):self.check()

    def test_original_keeper_still_alive_rejected(self):
        self.live.add(13496)
        with self.assertRaisesRegex(ValueError,'keeper still present'):self.check()

    def test_cas_not_newer_than_keeper_rejected(self):
        self.release['task']['last_sequence']=5105;self.release['event']['sequence']=5105
        self.bundle['actual_CAS_release']=self.write(self.release_path,self.release);self.save()
        with self.assertRaisesRegex(ValueError,'CAS completion'):self.check()

    def test_wrong_cas_task_rejected(self):
        self.release['event']['task_id']='other'
        self.bundle['actual_CAS_release']=self.write(self.release_path,self.release);self.save()
        with self.assertRaisesRegex(ValueError,'CAS completion'):self.check()

    def test_active_screen_or_runtime_controller_rejected(self):
        self.bus={'tasks':[{'resources':['ck3-screen:acquired']}]}
        with self.assertRaisesRegex(ValueError,'screen owner'):self.check()
        self.bus={'tasks':[]};self.blockers=[{'pid':999,'name':'ck3.exe'}]
        with self.assertRaisesRegex(ValueError,'controller still running'):self.check()

    def test_host_wait_missing_rejected(self):
        self.exited['actual_original_popen_wait']=False;self.amend_original('original_host_exit',self.exited)
        with self.assertRaisesRegex(ValueError,'host/supervisor wait'):self.check()

    def test_public_run_must_retain_exit2(self):
        self.public['exit_code']=0;self.amend_original('public_run',self.public)
        with self.assertRaisesRegex(ValueError,'public run completion'):self.check()

    def test_original_stop_facts_cannot_be_upgraded(self):
        self.bundle['native_cleanup_qualified']=True;self.save()
        with self.assertRaisesRegex(ValueError,'STOP facts changed'):self.check()

    def test_original_normal_close_cannot_be_upgraded(self):
        self.normal['normal_close_qualified']=True
        self.stop['normal_close_result_original']=self.normal
        self.bundle['normal_close_result_original']=self.normal
        self.amend_original('original_normal_close_result',self.normal)
        with self.assertRaisesRegex(ValueError,'claims PASS'):self.check()


class PreservedObserverClosureTests(unittest.TestCase):
    """Actual SDK claim/observer/wire producers reach the full resource consumer.

    The surrounding host/keeper files and process absence are synthetic. The
    original SDK writes its own once claim, pending/final fact and handle-close
    receipts; no game, native process, queue or task-bus operation is invoked.
    """

    def setUp(self) -> None:
        import test_ck3_mod_acceptance_split_public_closure as existing
        repo = TOOLS.parent
        sys.path[:0] = [str(repo/'ck3_autonomous_player/src'), str(repo/'ck3_autonomous_player/tests/unit')]
        from test_normal_exit_integrated_v1 import FakeExitDriver, driver_module
        from xar_autoplayer.bridge.normal_exit_public_wire_v2 import normal_exit_public_result_v2

        self.fixture = existing.SplitPublicClosureTests()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        f = self.fixture
        self.source_root = Path(str(f.freeze['source_root']))
        self.requests = f.state/'native-session/normal-exit-map-requests'
        self.inventory_pin = self.write(f.state/'profile/normal-exit-source-inventory-v1.json',
            {'schema': 'SYNTHETIC_SOURCE_INVENTORY_NO_GAME'})
        profile_pin = self.write(f.run_dir/'normal-exit-binding/normal-exit-managed-profile.json',
            {'schema_version': 1, 'state_directory': str(f.state), 'evidence_directory': str(f.run_dir),
             'normal_exit_source_inventory': {'path': self.inventory_pin['path'], 'sha256': self.inventory_pin['sha256']}})
        self.sdk_pins: dict[str, FilePin] = {}
        for key, name in (('normal_exit_wire_source', 'normal_exit_public_wire_v2.py'),
                          ('normal_exit_observer_source', 'normal_exit_pending_observer_v1.py'),
                          ('normal_exit_process_source', 'normal_exit_process_observer_v1.py')):
            relative = Path('ck3_autonomous_player/src/xar_autoplayer/bridge')/name
            path = self.source_root/relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((repo/relative).read_bytes())
            self.sdk_pins[key] = allocation.pin(path)
        # Match R0003's real graph: wire is in source-index.files, without a
        # duplicate direct frozen-argv.files entry.
        self.index = {'schema': 'ck3-shared-source-frozen-successor-v1',
                      'machine_id': f.machine, 'files': list(self.sdk_pins.values())}
        index_pin = self.write(self.source_root.parent/'source-index.json', self.index)
        refs = f.refs
        refs.update(self.sdk_pins)
        refs.update(normal_exit_profile=profile_pin, normal_exit_source_inventory=self.inventory_pin,
                    normal_exit_frozen_source_index=index_pin)
        f.freeze['files'] = {pin['path']: {'bytes': pin['bytes'], 'sha256': pin['sha256']}
                             for pin in (profile_pin, self.inventory_pin, index_pin)}
        f.reseal('frozen_argv', f.freeze)
        ready = json_object(json.loads(Path(str(json_object(f.refs['ready_context'])['path'])).read_bytes()))
        ready['normal_exit_managed_profile'] = profile_pin
        ready['frozen_argv'] = f.refs['frozen_argv']
        f.reseal('ready_context', ready)

        driver = FakeExitDriver(f.state/'native-session')
        driver.path.mkdir(parents=True)
        driver.remain_pending = True
        driver.normal_exit_managed_profile['normal_exit_source_inventory'] = {
            'path': self.inventory_pin['path'], 'sha256': self.inventory_pin['sha256']}
        with patch.object(driver_module, 'verify_source_inventory_v1',
                          return_value={'source_inventory_sha256': self.inventory_pin['sha256']}):
            first = driver.query_normal_exit_context_v1(expected_revision=72)
            driver.request_normal_exit_v1('prepare_confirmation', expected_revision=72,
                expected_exit_context_signature=first['exit_context_signature'])
            context = driver.query_normal_exit_context_v1(expected_revision=72)
            confirm = driver.request_normal_exit_v1('confirm_desktop', expected_revision=72,
                expected_exit_context_signature=context['exit_context_signature'])
            pending = driver.observe_normal_exit_v1()
            driver.api.wait_result, driver.api.code = 0, 0
            final = driver.observe_normal_exit_v1()
        self.birth = str(driver.api.creation)
        self.final = json_object(normal_exit_public_result_v2(final))
        self.confirm = json_object(normal_exit_public_result_v2(confirm))
        for key, field in (('typed_exit_observer_receipt', 'receipt_path'),
                           ('typed_exit_observer_close', 'observer_close_receipt_path'),
                           ('typed_exit_confirm_claim', 'claim_path')):
            refs[key] = allocation.pin(Path(text_field(self.final, field)))
        f.bundle.update(closure_kind='preserved-failure-native-process-exit-zero',
            public_wait_format='root-observed-command-exit-v1', process_exit_evidence_format='typed-native-observer-v2')
        f.bundle.pop('failed_query')
        for mode, code in (('run', 2), ('allocate', 0)):
            command = existing.obj(f.leaves[mode+'_command'])
            wait = {'machine_id': f.machine, 'argv': command['argv'], 'exit_code': code,
                    'started_at_utc': '2026-10-24T10:00:00+00:00',
                    'finished_at_utc': '2026-10-24T11:00:00+00:00'}
            refs[mode+'_wait'] = self.write(f.root/(mode+'-root.actual.json'), wait)
        error = 'SYNTHETIC preserved original business failure'
        f.native.update(pid=43, process_exit_code=0, exit_reason='process_exit',
                        finished_at='2026-10-24T10:58:00+00:00')
        shutdown = existing.obj(f.native['shutdown'])
        shutdown.update(ck3_pid=43, ck3_exit_code=0, job_active_processes_before_termination=0)
        f.native['shutdown'] = shutdown
        session = existing.obj(f.native_report['session'])
        session['report'] = f.native
        f.native_report['session'] = session
        after = {'status': 'failure_shutdown_lifecycle_only', 'business_pass': False,
                 'normal_close_qualified': False, 'process_exit_zero_proof': {
                     'managed_session_done': True, 'pid': 43, 'exit_reason': 'process_exit',
                     'process_exit_code': 0, 'shutdown': shutdown}}
        game = existing.obj(f.leaves['retained_identity'])
        game['pid'] = 43
        retained = {**game, 'signaled': True, 'exit_code': 0, 'actual_retained_os0': True}
        f.normal.update(retained_handle=retained, failure_preserved=True,
            failure_shutdown_proof=after, host_error=error, managed_thread_finished=True,
            cleanup_ok=True, host_finished_at='2026-10-24T10:59:00+00:00')
        f.native_report.update(error=error, finished_at=f.normal['host_finished_at'], steps=[
            {'id': 'original-business-error', 'ok': False, 'plan': {'kind': 'query'}, 'error': error},
            {'ok': True, 'plan': {'tool': 'ck3_request_normal_exit_v1', 'args': {'action': 'confirm_desktop'}},
             'result': self.confirm},
            {'ok': True, 'plan': {'tool': 'ck3_observe_normal_exit_v1'},
             'result': normal_exit_public_result_v2(pending)},
            {'ok': True, 'plan': {'tool': 'ck3_observe_normal_exit_v1'}, 'result': self.final},
            {'ok': True, 'plan': {'kind': 'finish_hold', 'failure_shutdown': True},
             'result': {'hold_finished': True, 'failure_preserved': True, 'host_error': error,
                        'business_pass': False, 'normal_close_qualified': False},
             'after_snapshot': after, 'finished_at': '2026-10-24T10:58:30+00:00'}])
        f.reseal('retained_identity', game)
        f.reseal('retained_exit', retained)
        f.reseal('normal_close', f.normal)
        f.reseal('native_report', f.native_report)
        self.driver = driver

    def write(self, path: Path, value: object) -> FilePin:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value)+'\n', encoding='utf-8')
        return allocation.pin(path)

    def save(self) -> None:
        self.fixture.write(self.fixture.close, self.fixture.bundle)

    def check(self) -> JsonObject:
        return json_object(self.fixture.check())

    def test_actual_sdk_pending_then_terminal_producer_to_full_consumer_roundtrip(self) -> None:
        original = {key: Path(str(json_object(value)['path'])).read_bytes()
                    for key, value in self.fixture.refs.items()}
        proof = object_field(self.check(), 'failure_cleanup')
        self.assertEqual(proof['win32_birth_filetime'], self.birth)
        self.assertIs(proof['actual_retained_os0'], True)
        self.assertIs(proof['failure_lifecycle_completed'], True)
        self.assertIs(proof['original_normal_close_lifecycle_completed'], False)
        for key in ('normal_close_qualified', 'typed_normal_exit_proven', 'business_pass', 'release_pass'):
            self.assertIs(proof[key], False)
        self.assertIs(self.final['autosave_verified'], False)
        self.assertEqual(sum(row[0] == 'close' for row in self.driver.api.calls), 3)
        self.assertEqual(original, {key: Path(str(json_object(value)['path'])).read_bytes()
                                   for key, value in self.fixture.refs.items()})
        serialized = json.loads(json.dumps(self.fixture.bundle))
        self.fixture.bundle = serialized
        self.save()
        self.assertEqual(object_field(self.check(), 'failure_cleanup')['win32_birth_filetime'], self.birth)

    def test_historical_gui_window_format_remains_a_separate_valid_route(self) -> None:
        f = self.fixture
        f.bundle.pop('process_exit_evidence_format')
        for key in allocation.PRESERVED_TYPED_OBSERVER_SOURCE_KEYS:
            f.refs.pop(key)
        f.refs['root_window_start'] = self.write(f.root/'root-window-start.json',
            {'machine_id': f.machine, 'pid': 43, 'birth_filetime': self.birth})
        f.refs['root_window_exit'] = self.write(f.root/'root-window-exit.json',
            {'machine_id': f.machine, 'pid': 43, 'opened': True, 'exit_code_read': True,
             'wait_result': 0, 'actual_exit_code': 0})
        # Historical allocator snapshots retain their observed timestamp.
        wait = json_object(json.loads(Path(str(json_object(f.refs['allocate_wait'])['path'])).read_bytes()))
        wait.pop('started_at_utc'); wait.pop('finished_at_utc')
        wait['observed_at_utc'] = '2026-10-24T11:00:00+00:00'
        f.reseal('allocate_wait', wait)
        self.assertEqual(object_field(self.check(), 'failure_cleanup')['win32_birth_filetime'], self.birth)

    def test_mixed_and_missing_explicit_formats_are_rejected(self) -> None:
        f = self.fixture
        f.refs['root_window_start'] = self.write(f.root/'mixed.json', {})
        self.save()
        with self.assertRaisesRegex(ValueError, 'mix GUI'):
            self.check()
        f.refs.pop('root_window_start'); f.bundle.pop('process_exit_evidence_format'); self.save()
        with self.assertRaisesRegex(ValueError, 'explicit evidence format'):
            self.check()

    def test_changed_original_receipt_is_rejected_before_use(self) -> None:
        path = Path(str(json_object(self.fixture.refs['typed_exit_observer_receipt'])['path']))
        path.write_bytes(path.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError, 'original bytes changed'):
            self.check()

    def test_other_state_and_unfrozen_sdk_source_are_rejected(self) -> None:
        f = self.fixture
        path = f.root/'other-state/normal-exit-map-requests/claim.json'
        value = json.loads(Path(str(json_object(f.refs['typed_exit_confirm_claim'])['path'])).read_bytes())
        f.refs['typed_exit_confirm_claim'] = self.write(path, value); self.save()
        with self.assertRaisesRegex(ValueError, 'allocated state directory'):
            self.check()
        f.refs['typed_exit_confirm_claim'] = allocation.pin(Path(text_field(self.final, 'claim_path')))
        f.refs['normal_exit_wire_source'] = self.write(f.root/'normal_exit_public_wire_v2.py', {})
        self.save()
        with self.assertRaisesRegex(ValueError, 'different frozen source'):
            self.check()

    def test_bool_float_missing_null_and_rounded_public_identity_are_rejected(self) -> None:
        f = self.fixture
        report = copy.deepcopy(f.native_report)
        for value in (True, 1.0, None, int(self.birth), str(int(float(self.birth)))):
            with self.subTest(value=value):
                bad = copy.deepcopy(report)
                json_object(bad)  # Prove the fixture remains in the JSON domain.
                final = next(row['result'] for row in bad['steps'] if
                             row.get('result', {}).get('schema') == 'ck3-normal-exit-process-observation-result-v2'
                             and row['result'].get('process_exit_observed') is True)
                final['process_creation_filetime_100ns'] = value
                f.reseal('native_report', bad)
                with self.assertRaises(ValueError):
                    self.check()
        bad = copy.deepcopy(report)
        final = next(row['result'] for row in bad['steps'] if
                     row.get('result', {}).get('process_exit_observed') is True)
        final.pop('process_creation_filetime_100ns')
        f.reseal('native_report', bad)
        with self.assertRaises(ValueError):
            self.check()

    def test_source_inventory_claim_and_handle_must_match_original_confirmation(self) -> None:
        f = self.fixture
        path = Path(str(json_object(f.refs['typed_exit_confirm_claim'])['path']))
        original = json_object(json.loads(path.read_bytes()))
        for key, value in (('source_inventory_sha256', 'a'*64), ('request_id', 'other-confirm'),
                           ('process_preconfirm_pin', {}), ('exit_context_signature', 'a'*64)):
            with self.subTest(key=key):
                f.reseal('typed_exit_confirm_claim', {**original, key: value})
                with self.assertRaises(ValueError):
                    self.check()

    def test_wrong_close_identity_and_unknown_format_cannot_grant_resource_credit(self) -> None:
        f = self.fixture
        for value in (None, True, 'typed-native-observer-v1'):
            with self.subTest(format=value):
                f.bundle['process_exit_evidence_format'] = value; self.save()
                with self.assertRaisesRegex(ValueError, 'evidence format'):
                    self.check()
        f.bundle['process_exit_evidence_format'] = 'typed-native-observer-v2'
        path = Path(str(json_object(f.refs['typed_exit_observer_close'])['path']))
        original = json_object(json.loads(path.read_bytes()))
        for key, value in (('pid', True), ('pid', 43.0), ('creation_filetime_100ns', True),
                           ('creation_filetime_100ns', float(self.birth)),
                           ('retained_handle_token', 'other-handle'), ('close_error', 'failed')):
            with self.subTest(key=key, value=value):
                f.reseal('typed_exit_observer_close', {**original, key: value})
                with self.assertRaises(ValueError):
                    self.check()
        missing = dict(original); missing.pop('close_error')
        f.reseal('typed_exit_observer_close', missing)
        with self.assertRaises(ValueError):
            self.check()

    def test_frozen_source_index_requires_original_version_machine_and_unique_wire(self) -> None:
        f = self.fixture
        index_path = Path(str(json_object(f.refs['normal_exit_frozen_source_index'])['path']))
        original = json_object(json.loads(index_path.read_bytes()))
        for key, value in (('schema', None), ('schema', 'other-index-v1'), ('machine_id', 'other-machine'),
                           ('files', [self.sdk_pins['normal_exit_wire_source']]*2)):
            with self.subTest(key=key, value=value):
                ref = self.write(index_path, {**original, key: value})
                f.refs['normal_exit_frozen_source_index'] = ref
                files = json_object(f.freeze['files'])
                files[ref['path']] = {'bytes': ref['bytes'], 'sha256': ref['sha256']}
                f.freeze['files'] = files
                f.reseal('frozen_argv', f.freeze)
                with self.assertRaises(ValueError):
                    self.check()

    def replace_source_index(self, value: object) -> None:
        """Reseal only authored temporary test inputs, never a recorded predecessor."""
        f = self.fixture
        path = Path(text_field(json_object(f.refs['normal_exit_frozen_source_index']), 'path'))
        ref = self.write(path, value)
        f.refs['normal_exit_frozen_source_index'] = ref
        files = json_object(f.freeze['files'])
        files[ref['path']] = {'bytes': ref['bytes'], 'sha256': ref['sha256']}
        f.freeze['files'] = files
        f.reseal('frozen_argv', f.freeze)
        ready = json_object(json.loads(Path(text_field(json_object(f.refs['ready_context']), 'path')).read_bytes()))
        ready['frozen_argv'] = f.refs['frozen_argv']
        f.reseal('ready_context', ready)

    def canonical_index(self) -> JsonObject:
        return json_object({'schema': 'ck3-common-source-index-v1',
            'machine_id': self.fixture.machine, 'files': {
                Path(row['path']).relative_to(self.source_root).as_posix(): {
                    'bytes': row['bytes'], 'sha256': row['sha256']}
                for row in self.sdk_pins.values()}})

    def test_canonical_source_index_serialization_reaches_full_preserved_consumer(self) -> None:
        self.replace_source_index(json.loads(json.dumps(self.canonical_index())))
        result = object_field(self.check(), 'failure_cleanup')
        self.assertIs(result['actual_retained_os0'], True)
        self.assertIs(result['failure_lifecycle_completed'], True)
        self.assertIs(result['business_pass'], False)

    def test_canonical_signature_types_paths_and_missing_wire_are_rejected(self) -> None:
        baseline = self.canonical_index()
        wire = Path(self.sdk_pins['normal_exit_wire_source']['path']).relative_to(self.source_root).as_posix()
        for defect in ('missing', 'bool', 'float', 'null', 'extra_path', 'escape', 'backslash', 'absolute'):
            with self.subTest(defect=defect):
                candidate = copy.deepcopy(baseline)
                entries = object_field(candidate, 'files')
                row = object_field(entries, wire)
                if defect == 'missing': del entries[wire]
                elif defect in ('bool', 'float', 'null'):
                    row['bytes'] = {'bool': True, 'float': 1.0, 'null': None}[defect]
                    entries[wire] = row
                elif defect == 'extra_path':
                    row['path'] = self.sdk_pins['normal_exit_wire_source']['path']; entries[wire] = row
                else:
                    key = '../'+wire if defect == 'escape' else wire.replace('/', '\\') if defect == 'backslash' else self.sdk_pins['normal_exit_wire_source']['path']
                    entries[key] = entries.pop(wire)
                candidate['files'] = entries
                self.replace_source_index(candidate)
                with self.assertRaises(ValueError): self.check()

    def test_recorded_r0012_legacy_sdk_sources_still_reach_full_consumer(self) -> None:
        # Source excerpt only: actual R0012's immutable a11 index is 1057186B,
        # SHA c87f6fea5f65a5135acac5476672c69c9b39fc1b90d812fe9057a13148670fa0.
        # This test uses relocated temporary files with their own pins. The
        # recorded R0012 original is never read, changed, or presented as new.
        recorded = {
            'normal_exit_wire_source': (14287, '63f06a97d555fbf6b6ff12012d9d6f297f77de4be54349aed1af93c5b67d564d'),
            'normal_exit_observer_source': (6415, '630ab09bd15ac6558b878332de0956579e8231f1178484731b185794a1b03996'),
            'normal_exit_process_source': (10155, 'ed6e041ed0555807cd7956cb73c0d978a5b39945a9b69beb6a9724796bd8dd70')}
        for key, (size, digest) in recorded.items():
            self.assertEqual((self.sdk_pins[key]['bytes'], self.sdk_pins[key]['sha256']), (size, digest))
        self.assertEqual(self.index['schema'], 'ck3-shared-source-frozen-successor-v1')
        self.assertIs(object_field(self.check(), 'failure_cleanup')['actual_retained_os0'], True)

    def test_actual_modified_consumer_scope_is_strict(self) -> None:
        from mypy import api
        source = TOOLS/'ck3_mod_acceptance_allocate.py'
        tree = ast.parse(source.read_text(encoding='utf-8-sig'))
        names = {'PreservedFailureOS0Facts', 'PreservedTypedObserverSources',
                  'preserved_failure_typed_format', 'preserved_typed_observer_sources',
                  '_canonical_source_index_files', '_typed_frozen_source_index_files',
                 'validate_preserved_typed_observer', '_late_integer',
                 'validate_preserved_failure_native_os0', 'validate_root_observed_public_exit'}
        nodes = [node for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef))
                 and node.name in names]
        self.assertEqual({node.name for node in nodes}, names)
        prelude = '''from __future__ import annotations
from typing import Literal, TypedDict
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
import json, math, re
from ck3_mod_acceptance_background_types import FilePin, JsonObject, json_object, file_pin, keyed_file_pin, object_field, text_field, strings_field
from ck3_mod_acceptance import _verification_actual_pin_v1
'''
        constants = [node for node in tree.body if isinstance(node, ast.Assign) and
                     any(isinstance(target, ast.Name) and target.id == 'PRESERVED_TYPED_OBSERVER_SOURCE_KEYS'
                         for target in node.targets)]
        self.assertEqual(len(constants), 1)
        consumer = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                        and node.name == 'previous_failed_live_resource_closure')
        branches = [node for node in ast.walk(consumer) if isinstance(node, ast.If)
                    and isinstance(node.test, ast.Name) and node.test.id == 'preserved_os0']
        self.assertEqual(len(branches), 1)
        dispatch = ast.parse('''def checked_dispatch(freeze: JsonObject, ready: JsonObject,
        refs: JsonObject, evidence: JsonObject, bundle: JsonObject, typed_observer: bool,
        normal: object, retained: object, game: object, native: object, report: object,
        original: Callable[[str], object]) -> PreservedFailureOS0Facts:
    pass
''').body[0]
        if not isinstance(dispatch, ast.FunctionDef):
            self.fail('Expected the extracted dispatcher to be a function')
        dispatch.body = copy.deepcopy(branches[0].body)+[ast.Return(value=ast.Name(id='preserved_facts', ctx=ast.Load()))]
        actual = prelude+ast.unparse(ast.fix_missing_locations(
            ast.Module(body=[*constants, *nodes, dispatch], type_ignores=[])))
        source_roots = os.pathsep.join(str(path) for path in
            (TOOLS, TOOLS.parent/'ck3_autonomous_player'/'src'))
        with patch.dict(os.environ, {'MYPYPATH': source_roots}):
            stdout, stderr, code = api.run(['--strict', '--strict-equality', '--follow-imports=silent',
                '--no-incremental', '--cache-dir', 'nul', '-c', actual])
        self.assertEqual(code, 0, stdout+stderr)


def assert_java_produced_source_consumers(runtime_path: Path) -> None:
    """JUnit supplies the real Java output; the process/host facts stay inert."""
    from test_ck3_mod_acceptance_normal_close import NormalCloseReviewRaceTests
    runtime = json_object(json.loads(runtime_path.read_bytes()))
    paths = object_field(runtime, 'paths')
    source = Path(text_field(paths, 'source_root')).resolve()
    index_path = Path(text_field(paths, 'source_index'))
    index = json_object(json.loads(index_path.read_bytes()))
    index_original = index_path.read_bytes()
    if index.get('schema') != 'ck3-common-source-index-v1':
        raise AssertionError('Java must emit the single canonical source-index version')
    codec_names = ('normal_exit_process_observer_v1', 'normal_exit_contract_v1', 'normal_exit_public_wire_v2')
    NormalCloseReviewRaceTests.setUpClass()
    normal = NormalCloseReviewRaceTests()
    try:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            client, _, fake_time, report = normal.make_client(root, review_at=None)
            normal.typed_route(root, client, report)
            client.manifest['source_root'] = {'path_key': 'source_root'}
            client.manifest['source_index'] = {'path_key': 'source_index', **allocation.pin(index_path)}
            previous_resolver = client.selection.manifest_path_key
            client.selection.manifest_path_key = lambda ref: {
                'source_root': source, 'source_index': index_path}.get(ref.get('path_key'), previous_resolver(ref))
            codec, consumed, leaves = normal.module._typed_quit_codec(source, index_path, allocation.pin(index_path))
            if consumed != allocation.pin(index_path) or {Path(row['path']).stem for row in leaves} != set(codec_names):
                raise AssertionError('Actual Java source index did not supply the three real codec modules')
            with patch.object(normal.module, 'time', fake_time):
                result = client.normal_close('authored-Java-source-index-roundtrip')
            if result['normal_close_qualified'] is not True:
                raise AssertionError(result)
            original_entries = object_field(index, 'files')
            leaf = 'ck3_autonomous_player/src/xar_autoplayer/bridge/normal_exit_public_wire_v2.py'
            for defect in ('missing', 'bool', 'float', 'null', 'extra_path', 'basename'):
                bad = copy.deepcopy(index)
                entries = object_field(bad, 'files')
                row = object_field(entries, leaf)
                if defect == 'missing': del entries[leaf]
                elif defect == 'basename': entries[Path(leaf).name] = entries.pop(leaf)
                elif defect == 'extra_path':
                    row['path'] = str(source/leaf); entries[leaf] = row
                else:
                    row['bytes'] = {'bool': True, 'float': 1.0, 'null': None}[defect]; entries[leaf] = row
                bad['files'] = entries
                candidate = root/(defect+'-index.json')
                candidate.write_text(json.dumps(bad), encoding='utf-8')
                with normal.assertRaises(ValueError):
                    normal.module._typed_quit_codec(source, candidate, allocation.pin(candidate))
            if original_entries != object_field(json_object(json.loads(index_path.read_bytes())), 'files'):
                raise AssertionError('Negative fixtures changed the actual Java output')
    finally:
        NormalCloseReviewRaceTests.doClassCleanups()
    preserved = PreservedObserverClosureTests()
    preserved.setUp()
    try:
        f = preserved.fixture
        if text_field(index, 'machine_id') != f.machine:
            raise AssertionError('Java authored machine must match the independently sourced closure fixture')
        f.freeze['source_root'] = str(source)
        f.native_report['agent_source_root'] = str(source)
        f.reseal('native_report', f.native_report)
        for key, name in (('normal_exit_wire_source', 'normal_exit_public_wire_v2.py'),
                          ('normal_exit_observer_source', 'normal_exit_pending_observer_v1.py'),
                          ('normal_exit_process_source', 'normal_exit_process_observer_v1.py')):
            f.refs[key] = allocation.pin(source/'ck3_autonomous_player/src/xar_autoplayer/bridge'/name)
        index_ref = allocation.pin(index_path)
        f.refs['normal_exit_frozen_source_index'] = index_ref
        files = json_object(f.freeze['files'])
        files[index_ref['path']] = {'bytes': index_ref['bytes'], 'sha256': index_ref['sha256']}
        f.freeze['files'] = files
        f.reseal('frozen_argv', f.freeze)
        ready = json_object(json.loads(Path(text_field(json_object(f.refs['ready_context']), 'path')).read_bytes()))
        ready['frozen_argv'] = f.refs['frozen_argv']
        f.reseal('ready_context', ready)
        sources = allocation.preserved_typed_observer_sources(f.freeze, ready, f.refs)
        birth = allocation.validate_preserved_typed_observer(f.native_report, sources, 43)
        if birth != preserved.birth:
            raise AssertionError('Actual Java index crossed the independent SDK process observer')
        full = object_field(preserved.check(), 'failure_cleanup')
        if full['actual_retained_os0'] is not True or full['failure_lifecycle_completed'] is not True:
            raise AssertionError(full)
        if full['business_pass'] is not False:
            raise AssertionError('A preserved business failure cannot be upgraded by the new source index')
    finally:
        preserved.doCleanups()
    if index_path.read_bytes() != index_original:
        raise AssertionError('Actual producer output was modified by a consumer')


class RootObservedCompletionTests(unittest.TestCase):
    def example(self) -> JsonObject:
        return {'machine_id': 'authored-machine', 'exit_code': 0,
                'argv': ['python.exe', 'ck3_mod_acceptance.py', 'allocate'],
                'started_at_utc': '2026-10-24T10:00:00+00:00',
                'finished_at_utc': '2026-10-24T11:00:00+00:00'}

    def test_explicit_original_timestamp_shapes_remain_readable(self) -> None:
        current = self.example()
        expected = ['python.exe', 'ck3_mod_acceptance.py', 'allocate']
        self.assertEqual(allocation.validate_root_observed_public_exit(
            current, 'authored-machine', 'allocate', 0), expected)
        current.pop('started_at_utc'); current.pop('finished_at_utc')
        current['observed_at_utc'] = '2026-10-24T11:00:00+00:00'
        self.assertEqual(allocation.validate_root_observed_public_exit(
            current, 'authored-machine', 'allocate', 0), expected)

    def test_wrong_missing_mixed_or_reversed_completion_fails(self) -> None:
        for field, value in (('started_at_utc', None), ('finished_at_utc', True),
                             ('started_at_utc', '2026-10-24T12:00:00+00:00'),
                             ('finished_at_utc', '2026-10-24T11:00:00'),
                             ('observed_at_utc', '2026-10-24T11:00:00+00:00'),
                             ('exit_code', False), ('exit_code', 0.0)):
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                allocation.validate_root_observed_public_exit(
                    {**self.example(), field: value}, 'authored-machine', 'allocate', 0)
        for field in ('started_at_utc', 'finished_at_utc'):
            bad = self.example(); bad.pop(field)
            with self.subTest(missing=field), self.assertRaises(ValueError):
                allocation.validate_root_observed_public_exit(bad, 'authored-machine', 'allocate', 0)


if __name__=='__main__':unittest.main()
