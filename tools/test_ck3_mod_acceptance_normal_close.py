"""Portable Root-review race regressions using the actual client and native predicate."""
from __future__ import annotations
import argparse
import copy
import ctypes
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

REPO = Path(__file__).resolve().parents[1]
CLIENT_SOURCE = REPO / 'tools/ck3_mod_acceptance_client.py'
HOST_SOURCE = REPO / 'ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py'


class NormalCloseReviewRaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(CLIENT_SOURCE.parent))
        cls.addClassCleanup(sys.path.remove, str(CLIENT_SOURCE.parent))
        spec = importlib.util.spec_from_file_location('_normal_close_client_under_test', CLIENT_SOURCE)
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def make_client(self, root, *, review_at=.3, deadline=1, os_exit=0, native_exit=0, reviewer='/root',
                    screen_task='synthetic-screen', runtime_environment=None):
        from ck3_mod_acceptance import pin
        module = self.module
        client = module.CaseClient.__new__(module.CaseClient)
        client.output = root
        client.live = root / 'SYNTHETIC_ROOT_REVIEW_RACE'
        client.live.mkdir()
        client.keeper = root / 'synthetic-keeper'
        client._handle = object()
        client._process = {'pid': 2468, 'create_time': 123.5}
        client.frozen = {'run_id': client.live.name, 'screen_task': screen_task, 'reviewer': '/root',
                         'argv': ['SYNTHETIC ONLY'], 'runtime_environment': dict(runtime_environment or {})}
        frozen_path = client.live / 'frozen-argv.json'
        module.write_once(frozen_path, client.frozen)
        client._hold = deadline
        client._started = 0
        client.manifest = {'host': {}}
        client.context = {'run_id': client.live.name, 'reviewer': '/root', 'frozen_argv': pin(frozen_path)}
        client.selection = SimpleNamespace(case={'budgets': {}}, manifest_path_key=lambda _: HOST_SOURCE,
            context=client.context, run_dir=client.live, argv=client.frozen['argv'],
            runtime_environment=client.frozen['runtime_environment'])
        client.selection.context_path = root / 'actual-run-context.json'
        client.selection.context_path.write_text(json.dumps(client.context), encoding='utf-8')
        client.execute_plan = Mock(side_effect=AssertionError('No finish/control submission after terminal host'))
        clock = SimpleNamespace(now=0.0, review_written=False)
        image = root / 'synthetic-reviewed-quit.not-image'
        image.write_bytes(b'SYNTHETIC ONLY: no actual GUI review or input')
        evidence = {'path': str(image), 'bytes': image.stat().st_size,
                    'sha256': hashlib.sha256(image.read_bytes()).hexdigest()}
        response = root / 'normal-quit-root-result.json'
        def sleep(seconds):
            clock.now += seconds
            if review_at is not None and clock.now >= review_at and not clock.review_written:
                module.write_once(response, {'run_id': client.frozen['run_id'], 'reviewer': reviewer,
                    'normal_gui_quit': True, 'evidence': [evidence]})
                clock.review_written = True
        client_time = SimpleNamespace(time=lambda: clock.now, sleep=sleep)
        def exit_code(_handle, pointer):
            ctypes.cast(pointer, ctypes.POINTER(ctypes.c_uint32)).contents.value = os_exit
            return 1
        waits = iter((258,))  # Live at normal_close entry; then the original GUI exit is observed.
        client._kernel = SimpleNamespace(WaitForSingleObject=lambda _handle, _timeout: next(waits, 0),
                                        GetExitCodeProcess=exit_code)
        pipe = r'\\.\pipe\synthetic-root-review-race'
        report = {'fixture_only': False, 'error': None, 'pipe': pipe, 'phase': 'hold',
            'finished_at': '2026-10-09T10:00:11+00:00', 'managed_session_done': True,
            'managed_session_thread_finished': True, 'cleanup_ok': True,
            'session': {'error': None, 'report': {
                'kind': 'ck3_native_headless_session', 'mode': 'native-headless',
                'format_version': 1, 'ok': True, 'error': None,
                'exit_reason': 'process_exit', 'process_exit_code': native_exit, 'pid': 2468, 'pipe': pipe,
                'started_at': '2026-10-09T10:00:00+00:00', 'finished_at': '2026-10-09T10:00:10+00:00',
                'shutdown': {'ok': True, 'cleanup_proven': True, 'tree_gone': True,
                    'ck3_pid': 2468, 'ck3_exit_code': native_exit, 'job_active_processes_final': 0,
                    'contract_errors': [], 'watchdog_state_after': 'absent', 'nonce': 'a' * 32,
                    'ck3_creation_date': 'synthetic-creation-date',
                    'control_files_absent': {'ck3.json': True, 'watchdog.json': True},
                    'final_ck3_inventory': {'tasklist_returncode': 0, 'tasklist_pids': [], 'wmi_pids': [],
                        'native_pids': [], 'processes': []}}}}}
        client.read_report = lambda allow_error=False: report
        return client, clock, client_time, report

    def process_poll_client(self, root, wait_result):
        client = self.module.CaseClient.__new__(self.module.CaseClient)
        client._handle = object()
        client._kernel = SimpleNamespace(WaitForSingleObject=Mock(return_value=wait_result))
        client._process = {'pid': 2468, 'create_time': 123.5}
        client.frozen = {'run_id': 'synthetic-retained-process-poll', 'screen_task': 'synthetic-screen'}
        client._hold = 123456.5
        client.live = root / client.frozen['run_id']
        client.keeper = root / 'synthetic-keeper'
        client.normal_quit_reviewer = Mock(return_value='/root')
        client.read_report = Mock(return_value={'error': 'original pause readback failure'})
        client.start_normal_quit_automation = Mock()
        return client

    def test_signaled_retained_process_rejects_before_quit_checkpoint_or_automation(self):
        with tempfile.TemporaryDirectory() as directory:
            for wait_result in (0, 0xFFFFFFFF):
                with self.subTest(wait_result=wait_result):
                    client = self.process_poll_client(Path(directory), wait_result)
                    client.checkpoint = Mock()
                    with self.assertRaisesRegex(ValueError, 'no longer running; normal GUI Quit unavailable'):
                        client.normal_close('business_failure_preserved')
                    client._kernel.WaitForSingleObject.assert_called_once_with(client._handle, 0)
                    client.checkpoint.assert_not_called()
                    client.start_normal_quit_automation.assert_not_called()
                    client.read_report.assert_not_called()

    def test_running_retained_process_enters_original_quit_checkpoint(self):
        class ReachedOriginalCheckpoint(Exception):
            pass

        with tempfile.TemporaryDirectory() as directory:
            client = self.process_poll_client(Path(directory), 258)
            client.checkpoint = Mock(side_effect=ReachedOriginalCheckpoint)
            with self.assertRaises(ReachedOriginalCheckpoint):
                client.normal_close('business_failure_preserved')
            client._kernel.WaitForSingleObject.assert_called_once_with(client._handle, 0)
            client.checkpoint.assert_called_once()
            name, request = client.checkpoint.call_args.args
            self.assertEqual(name, 'normal-quit-awaiting')
            self.assertEqual((request['pid'], request['create_time']), (2468, 123.5))
            self.assertEqual(request['original_hold_deadline'], client._hold)
            self.assertEqual(request['disposition'], 'business_failure_preserved')
            self.assertEqual(request['host_error_preserved'], 'original pause readback failure')
            client.read_report.assert_called_once_with(allow_error=True)
            client.start_normal_quit_automation.assert_not_called()

    def test_terminal_host_and_os0_wait_for_explicit_root_review(self):
        with tempfile.TemporaryDirectory() as directory:
            client, clock, fake_time, report = self.make_client(Path(directory))
            self.assertIs(client.selection.context, client.context)
            self.assertEqual(client.resolve_operator_reviewer(), '/root')
            self.assertIsNotNone(client.native_zero_proof(report))  # The actual shared full predicate.
            with patch.object(self.module, 'time', fake_time):
                result = client.normal_close('synthetic-delayed-root-review')
            self.assertGreaterEqual(clock.now, .3)
            self.assertTrue(result['normal_close_qualified'])
            self.assertEqual(result['root_normal_gui_review']['reviewer'], '/root')
            self.assertIsNotNone(result['native_zero_proof'])
            client.execute_plan.assert_not_called()

    def test_selected_typed_close_starts_immediately_without_root_or_template_wait(self):
        for failed in (False, True):
            with self.subTest(failed=failed), tempfile.TemporaryDirectory() as directory:
                client, clock, fake_time, report = self.make_client(Path(directory), review_at=None)
                self.typed_route(Path(directory), client, report)
                client.selection.case['required_mcp_tools'] = ['ck3_query_normal_exit_context_v1',
                    'ck3_request_normal_exit_v1', 'ck3_observe_normal_exit_v1']
                client.selection.normal_quit_automation = {'must_not_run': True}
                if failed:
                    report['error'] = 'authored original failed host'
                    report['status'] = 'RED'
                evidence = client.typed_normal_quit_evidence(report, allow_preserved_failure=True)
                client.start_typed_normal_quit_automation = Mock(return_value=evidence)
                client.start_normal_quit_automation = Mock(side_effect=AssertionError('No template fallback'))
                with patch.object(self.module, 'time', fake_time):
                    result = client.normal_close('actual_case_evidence_recorded')
                client.start_typed_normal_quit_automation.assert_called_once_with()
                client.start_normal_quit_automation.assert_not_called()
                self.assertFalse((Path(directory)/'manual-quit-awaiting.json').exists())
                self.assertIsNotNone(result['typed_normal_exit_route'])
                self.assertEqual(result['normal_close_qualified'], not failed)
                self.assertEqual(report.get('error'), 'authored original failed host' if failed else None)

    def test_actual_R0008_context_through_sdk_producer_and_automatic_typed_consumer(self):
        sys.path.insert(0, str(REPO/'ck3_autonomous_player/tests/unit'))
        self.addCleanup(sys.path.remove, str(REPO/'ck3_autonomous_player/tests/unit'))
        from test_normal_exit_integrated_v1 import FakeExitDriver, driver_module
        from xar_autoplayer.bridge.service import GameplayBridgeService
        from xar_autoplayer.bridge.normal_exit_public_wire_v2 import parse_normal_exit_public_result_v2, normal_exit_public_result_v2
        from xar_autoplayer.bridge import normal_exit_public_wire_v2 as codec
        capture = json.loads((REPO/'tools/fixtures/ck3_R0008_normal_exit_context.json').read_bytes())
        original = parse_normal_exit_public_result_v2(capture['result']).to_memory()
        native_start = original['native_observation']
        birth = original['process_creation_filetime_100ns']
        pid = native_start['game_pid']
        for unknown in (False, True):
            with self.subTest(unknown=unknown), tempfile.TemporaryDirectory() as directory:
                class R8Driver(FakeExitDriver):
                    def __init__(self, path):
                        super().__init__(path)
                        self.api.pid, self.api.creation = pid, birth
                        self.phase, self.save_enabled = 0, True
                        self.remain_pending, self.fail_after_confirm = True, unknown
                    def take_snapshot(self):
                        if self.dead: raise AssertionError('No snapshot after desktop confirmation')
                        return copy.deepcopy(capture['after_snapshot'])
                    def send(self, request):
                        self.sent.append(copy.deepcopy(request))
                        action = request['action']
                        if action == 'prepare_confirmation': self.phase = 1
                        elif action == 'continue_preparation': self.phase = 2
                        elif action == 'disable_exit_autosave': self.save_enabled = False
                        elif action == 'confirm_desktop':
                            self.dead = True
                            if unknown: raise OSError('Authored unknown confirm delivery')
                    def wait_for_command_result(self, request_id, timeout):
                        request = self.sent[-1]
                        action = request['action']
                        native = copy.deepcopy(native_start)
                        native.update(action=action, context_signature_verified=action!='query_context',
                            confirmation_visible=self.phase==2, stage_consumed=[self.phase>=1,self.phase>=2,action=='confirm_desktop'])
                        native['status'] = ('context_observed' if action=='query_context' else
                            'autosave_disabled' if action=='disable_exit_autosave' else
                            'confirmation_observed' if action=='continue_preparation' else 'dispatch_pending')
                        if self.phase>=1:
                            native['targets'][1].update({key:True for key,value in native['targets'][1].items() if type(value) is bool})
                        if self.phase==2:
                            native['targets'][2].update({key:True for key,value in native['targets'][2].items() if type(value) is bool})
                            native['exit_autosave'].update(state_available=True,control_visible=True,
                                control_enabled=True,should_save=self.save_enabled)
                        if action=='disable_exit_autosave':
                            native['exit_autosave'].update(disable_claimed=True,dispatch_invoked=True,postcondition_observed=True)
                        elif action!='query_context':
                            index = {'prepare_confirmation':0,'continue_preparation':1,'confirm_desktop':2}[action]
                            native['dispatches'][index] = {key:True for key in native['dispatches'][index]}
                        return {'ok':True,'request_id':request_id,'result':native}
                driver = R8Driver(Path(directory))
                service = GameplayBridgeService(driver)
                initial_wire = None
                def invoke(tool, arguments):
                    nonlocal initial_wire
                    if tool=='ck3_query_normal_exit_context_v1':
                        value = service.query_normal_exit_context_v1(expected_revision=10)
                        wire = normal_exit_public_result_v2(value)
                        if initial_wire is None:
                            initial_wire = wire
                            self.assertEqual(wire, capture['result'])
                        return wire
                    if tool=='ck3_request_normal_exit_v1':
                        return normal_exit_public_result_v2(service.request_normal_exit_v1(arguments['action'],
                            expected_revision=int(arguments['expected_revision']),
                            expected_exit_context_signature=arguments['expected_exit_context_signature']))
                    self.assertEqual(tool,'ck3_observe_normal_exit_v1')
                    driver.api.wait_result,driver.api.code=0,0
                    return normal_exit_public_result_v2(service.observe_normal_exit_v1())
                with patch.object(driver_module,'verify_source_inventory_v1',return_value={
                        'source_inventory_sha256':capture['result']['source_inventory_sha256']}):
                    if unknown:
                        with self.assertRaisesRegex(ValueError,'without typed normal Quit proof'):
                            self.module._typed_quit_run_v1(codec,invoke,lambda:80.0,pid=pid,birth=birth)
                    else:
                        result=self.module._typed_quit_run_v1(codec,invoke,lambda:80.0,pid=pid,birth=birth)
                        self.assertTrue(result['typed_normal_exit_observed'])
                        self.assertFalse(result['observer_retained'])
                self.assertEqual([r['action'] for r in driver.sent],['query_context','prepare_confirmation',
                    'query_context','continue_preparation','query_context','disable_exit_autosave','query_context','confirm_desktop'])
                self.assertEqual(sum(r['action']=='confirm_desktop' for r in driver.sent),1)
                self.assertIsNone(driver._normal_exit_owned_observer_v1)

    def test_typed_automation_deadline_and_identity_do_not_dispatch_mutations(self):
        from xar_autoplayer.bridge import normal_exit_public_wire_v2 as codec
        capture=json.loads((REPO/'tools/fixtures/ck3_R0008_normal_exit_context.json').read_bytes())
        invoke=Mock(return_value=capture['result'])
        with self.assertRaises(TimeoutError):
            self.module._typed_quit_run_v1(codec,invoke,lambda:0.0,pid=7552,birth=134373608090284000)
        invoke.assert_not_called()
        with self.assertRaisesRegex(ValueError,'retained PID'):
            self.module._typed_quit_run_v1(codec,invoke,lambda:80.0,pid=7553,birth=134373608090284000)
        self.assertEqual(invoke.call_args.args[0],'ck3_query_normal_exit_context_v1')
        self.assertEqual(invoke.call_count,1)

    def test_complete_modified_typed_quit_function_scope_is_strict(self):
        import ast, os, subprocess
        tree=ast.parse(CLIENT_SOURCE.read_text(encoding='utf-8-sig'))
        names={'TypedNormalQuitEvidenceV1','NormalQuitDecodedV2','NormalQuitCodecV2',
            '_typed_quit_plan_v1','_typed_quit_preparation_v1','_typed_quit_run_v1',
            '_typed_quit_pairs','_typed_quit_original','_typed_quit_codec','typed_normal_quit_evidence_v1'}
        nodes=[node for node in tree.body if isinstance(node,(ast.ClassDef,ast.FunctionDef)) and node.name in names]
        self.assertEqual(len(nodes),len(names))
        prefix='from __future__ import annotations\nfrom collections.abc import Callable\nfrom typing import Literal,Protocol,TypedDict,runtime_checkable\nfrom pathlib import Path\nfrom datetime import datetime,timezone\nimport hashlib,json\nfrom ck3_mod_acceptance_background_types import FilePin,JsonObject,json_object,keyed_file_pin,file_pin,text_field\n'
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'actual_typed_quit_scope.py'
            source.write_text(prefix+ast.unparse(ast.Module(body=nodes,type_ignores=[])),encoding='utf-8')
            environment=dict(os.environ)
            environment['MYPYPATH']=os.pathsep.join((str(REPO/'tools'),str(REPO/'ck3_autonomous_player/src'),environment.get('MYPYPATH','')))
            result=subprocess.run([sys.executable,'-B','-m','mypy','--strict','--follow-imports=skip',
                '--no-incremental','--cache-dir','nul',str(source)],cwd=REPO,env=environment,capture_output=True,text=True,timeout=60)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_missing_review_waits_only_to_original_deadline_and_stays_unqualified(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            client, clock, fake_time, _ = self.make_client(root, review_at=None, deadline=.4)
            with patch.object(self.module, 'time', fake_time):
                result = client.normal_close('synthetic-missing-root-review')
            self.assertGreaterEqual(clock.now, .4)
            self.assertLess(clock.now, .51)
            self.assertFalse(result['normal_close_qualified'])
            self.assertIsNone(result['root_normal_gui_review'])
            self.assertFalse((root / 'normal-quit-root-result.json').exists())
            client.execute_plan.assert_not_called()

    def test_late_review_cannot_replace_either_real_zero_proof(self):
        for os_exit, native_exit in ((1, 0), (0, 1)):
            with self.subTest(os_exit=os_exit, native_exit=native_exit), tempfile.TemporaryDirectory() as directory:
                client, _, fake_time, _ = self.make_client(Path(directory), os_exit=os_exit, native_exit=native_exit)
                with patch.object(self.module, 'time', fake_time):
                    result = client.normal_close('synthetic-nonzero-preserved')
                self.assertFalse(result['normal_close_qualified'])
                client.execute_plan.assert_not_called()

    def test_terminal_failure_does_not_wait_for_unqualifiable_manual_review(self):
        for failure in ('os_nonzero', 'os_unavailable', 'native_nonzero', 'thread', 'cleanup', 'host_error'):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                client, clock, fake_time, report = self.make_client(root,
                    os_exit=1 if failure=='os_nonzero' else 0,
                    native_exit=1 if failure=='native_nonzero' else 0)
                if failure=='os_unavailable':
                    client._kernel.GetExitCodeProcess=lambda *_: 0
                elif failure=='thread':
                    report['managed_session_thread_finished']=False
                elif failure=='cleanup':
                    report['cleanup_ok']=False
                elif failure=='host_error':
                    report['error']='original host failure'
                original = copy.deepcopy(report)
                with patch.object(self.module, 'time', fake_time):
                    result = client.normal_close('synthetic-terminal-failure')
                self.assertEqual(clock.now, 0)
                self.assertEqual(client._hold, 1)
                self.assertFalse(result['normal_close_qualified'])
                self.assertIsNone(result['root_normal_gui_review'])
                self.assertFalse((root / 'normal-quit-root-result.json').exists())
                self.assertEqual(report, original)
                client.execute_plan.assert_not_called()

    def test_late_review_from_another_reviewer_is_still_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            client, _, fake_time, _ = self.make_client(Path(directory), reviewer='not-root')
            with patch.object(self.module, 'time', fake_time), self.assertRaisesRegex(ValueError, 'crossed scene'):
                client.normal_close('synthetic-wrong-reviewer')
            self.assertFalse((Path(directory) / 'normal-close-result.json').exists())
            client.execute_plan.assert_not_called()

    def typed_route(self, root, client, report, *, observe=True, inventory_defect=None):
        """Actual inventory producer/SDK encoder -> CaseClient, with inert native facts."""
        from ck3_mod_acceptance import pin
        from build_normal_exit_source_inventory_v1 import (
            build_inventory, STOCK_GUI_PATHS, verify_source_inventory_v1)
        birth = 134373157160016545
        client._process['creation_filetime_100ns'] = str(birth)
        client._process['retained_synchronize_query_handle_acquired'] = True
        client.frozen['identity_allocation']={'machine_id':'synthetic-normal-quit-machine'}
        client.state = root / 'state'
        directory = client.state / 'native-session/normal-exit-map-requests'
        directory.mkdir(parents=True)
        bridge = REPO / 'ck3_autonomous_player/src/xar_autoplayer/bridge'
        index = root / 'source-index.json'
        # build_runtime.py's actual source-index producer uses repository-relative
        # keys and two-field signatures, rather than a list of absolute FilePins.
        index.write_text(json.dumps({'schema': 'ck3-common-source-index-v1', 'files': {
            (bridge / (name + '.py')).relative_to(REPO).as_posix(): {
                key: pin(bridge / (name + '.py'))[key] for key in ('bytes', 'sha256')}
            for name in ('normal_exit_process_observer_v1', 'normal_exit_contract_v1',
                         'normal_exit_public_wire_v2')}}), encoding='utf-8')
        codec, _, _ = self.module._typed_quit_codec(REPO, index, pin(index))
        client.manifest.update({'source_root': {'path_key':'source_root'},
                                'source_index': {'path_key':'source_index', **pin(index)}})
        client.selection.manifest_path_key = lambda ref: {'source_root':REPO, 'source_index':index}.get(ref.get('path_key'), HOST_SOURCE)
        profile = {'schema_version':1, 'guard_profile':str(root/'guard.json'), 'guard_profile_sha256':'a'*64,
            'userdir':str(client.state/'profile'), 'state_directory':str(client.state),
            'evidence_directory':str(client.live), 'game_version':'1.20.0.4',
            'dll':{'path':str(root/'bridge.dll'), 'sha256':'a'*64},
            'injector':{'path':str(root/'injector.exe'), 'sha256':'b'*64}}
        inventory = client.state/'profile/normal-exit-source-inventory-v1.json'
        inventory.parent.mkdir()
        (inventory.parent/'pdx_settings.txt').write_bytes(b'authored static inventory fixture settings')
        (inventory.parent/'dlc_load.json').write_text(json.dumps({'enabled_mods':[]}),encoding='utf-8')
        game=root/'authored-stock-game'
        for relative in STOCK_GUI_PATHS:
            path=game/relative;path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(b'authored protected stock GUI fixture')
        executable=root/'authored-executable.bin';executable.write_bytes(b'authored exact-build fixture')
        producer_profile={**profile,'guard':{'target':{'executable':str(executable),
            'executable_sha256':hashlib.sha256(executable.read_bytes()).hexdigest()}}}
        produced,_=build_inventory(producer_profile,game)
        inventory.write_text(json.dumps(produced),encoding='utf-8')
        inventory_reference={key:pin(inventory)[key] for key in ('path','sha256')}
        self.assertTrue(verify_source_inventory_v1(inventory_reference,producer_profile)['static_sources_verified'])
        # Mutate only authored negative inputs after exercising the real producer
        # and verifier. Every later reference is freshly bound, so these cases
        # reach the consumer's path guard rather than merely failing a SHA check.
        if inventory_defect=='wrong_root':produced['userdir']=(root/'other-state/profile').resolve().as_posix()
        elif inventory_defect=='relative':produced['userdir']='profile'
        elif inventory_defect=='missing':del produced['userdir']
        elif inventory_defect=='null':produced['userdir']=None
        elif inventory_defect=='bool':produced['userdir']=True
        elif inventory_defect=='float':produced['userdir']=1.0
        elif inventory_defect is not None:raise ValueError('Unknown authored inventory defect')
        inventory.write_text(json.dumps(produced),encoding='utf-8')
        profile['normal_exit_source_inventory'] = {key:pin(inventory)[key] for key in ('path','sha256')}
        profile_path = root/'normal-exit-managed-profile.json'
        profile_path.write_text(json.dumps(profile),encoding='utf-8')
        client.context['normal_exit_managed_profile'] = pin(profile_path)
        client.frozen['argv'] += ['--normal-exit-managed-profile',str(profile_path),
                                  '--normal-exit-managed-profile-sha256',pin(profile_path)['sha256']]
        frozen_path=client.live/'frozen-argv.json'
        frozen_path.write_text(json.dumps(client.frozen),encoding='utf-8')
        client.context['frozen_argv']=pin(frozen_path)
        client.selection.context_path.write_text(json.dumps(client.context),encoding='utf-8')
        process_pin = {'pid':2468,'creation_filetime_100ns':birth,'retained_handle_token':'same-original-handle',
            'wait_result':258,'verified_monotonic_ns':20,'observation_clock_domain':'driver_monotonic_v1'}
        native = {'schema':'ck3-normal-exit-map-v1','step':'normal-exit-map-v1','action':'confirm_desktop',
            'status':'dispatch_pending','native_revision':6,'connection_generation':1,'game_pid':2468,
            'played_character_id':31254,'process_creation_filetime_100ns':birth,'pump_epoch':74258,
            **{key:True for key in ('exact_build_verified','owner_verified','process_identity_verified',
                'source_abi_pins_verified','stock_files_verified','loaded_source_binding_verified','frame_verified')},
            'context_signature_verified':True,'confirmation_visible':True,
            'exit_autosave':{'state_available':True,'control_visible':True,'control_enabled':True,
                'should_save':False,'disable_claimed':False,'dispatch_invoked':False,'postcondition_observed':False},
            'orderly_exit_verified':False,'autosave_verified':False,'exit_context_signature':'c'*64,
            'reason':'desktop_dispatch_pending_independent_process_observation','stage_consumed':[True,True,True],
            'targets':[{**{key:True for key in ('read_complete','root_exists','root_visible','target_exists',
                'target_visible','target_enabled','unique_target','dispatch_admitted')},'target_vtable_rva':76961544} for _ in range(3)],
            'dispatches':[{key:i==2 for key in ('claim_latched','dispatch_invoked','native_handled',
                'post_read_complete','postcondition_observed')} for i in range(3)]}
        request_id = 'normal-exit-confirm_desktop-fixture'
        (directory/(request_id+'.request.json')).write_text(json.dumps({
            'type':'execute_step','protocol_version':1,'request_id':request_id,
            'step':'normal-exit-map-v1','action':'confirm_desktop',
            'expected_revision':native['native_revision'],'expected_player_character_id':31254,
            'expected_game_pid':2468,'expected_connection_generation':1,
            'expected_process_creation_filetime_100ns':birth,
            'source_inventory_sha256':pin(inventory)['sha256'],'request_nonce':request_id,
            'expected_exit_context_signature':'c'*64}),encoding='utf-8')
        identity = {'game_pid':2468,'creation_filetime_100ns':birth,'action':'confirm_desktop'}
        claim_key = hashlib.sha256(json.dumps(identity,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        claim_path = directory/(claim_key+'.claim.json')
        claim = {'schema':'ck3-normal-exit-once-claim-v1','identity':identity,'request_id':request_id,
            'status':'claimed_result_unknown_no_retry','exit_context_signature':'c'*64,
            'source_inventory_sha256':pin(inventory)['sha256'],'process_preconfirm_pin':process_pin}
        claim_path.write_text(json.dumps(claim),encoding='utf-8')
        terminal = {'schema':'ck3-normal-exit-request-result-v1','action':'confirm_desktop','public_revision':7,
            'request_id':request_id,'claim_path':str(claim_path),'source_inventory_sha256':pin(inventory)['sha256'],
            'process_creation_filetime_100ns':birth,'process_preconfirm_pin':process_pin,
            'claim_consumed':True,'retry_authorized':False,'process_exit_observed':True,'exit_code':0,
            'typed_normal_exit_observed':True,'autosave_verified':False,'status':'process_exit_observed_zero',
            'native_observation':native,'process_observation':{'pid':2468,'creation_filetime_100ns':birth,
                'retained_handle_token':'same-original-handle','wait_result':0,'wait_state':'signaled','exit_code':0,
                'process_identity_verified':True,'process_exit_observed':True,'observed_monotonic_ns':40,
                'timeout_ms':5000,'observation_deadline_reached':False,'observation_clock_domain':'driver_monotonic_v1','errors':[]},
            'driver_dispatch_receipt_observed_monotonic_ns':30,'snapshot_after_required':False,
            'observer_retained':True,'native_submission_count':1,'uses_desktop_input':False,'uses_ocr':False}
        confirm = copy.deepcopy(terminal)
        if observe:
            confirm.update(status='dispatch_pending',process_exit_observed=False,typed_normal_exit_observed=False,exit_code=None)
            confirm['process_observation'].update(wait_result=258,wait_state='timeout',exit_code=259,
                process_exit_observed=False,observation_deadline_reached=True)
            terminal.update(schema='ck3-normal-exit-process-observation-result-v1',native_submission_count=0,
                receipt_path=str(directory/'original.observe.json'))
        terminal_path = Path(terminal.get('receipt_path',str(directory/(request_id+'.result.json'))))
        terminal_path.write_text(json.dumps(terminal),encoding='utf-8')
        close_path = directory/'original.observer-close.json'
        close_path.write_text(json.dumps({'schema':'ck3-normal-exit-observer-close-v1',
            'reason':'independent_exit_fact_preserved','fact_receipt_path':str(terminal_path),
            'pid':2468,'creation_filetime_100ns':birth,'retained_handle_token':'same-original-handle',
            'close_error':None,'retry_authorized':False}),encoding='utf-8')
        terminal.update(observer_retained=False,observer_close_receipt_path=str(close_path))
        if not observe:confirm=terminal
        disabled = copy.deepcopy(terminal)
        disabled = {key:disabled[key] for key in ('public_revision','source_inventory_sha256','process_creation_filetime_100ns')}
        disabled.update(schema='ck3-normal-exit-request-result-v1',action='disable_exit_autosave',status='autosave_disabled',
            request_id='normal-exit-disable-fixture',claim_path=str(directory/'disabled.claim.json'),
            claim_consumed=True,retry_authorized=False,process_exit_observed=False,typed_normal_exit_observed=False,
            orderly_exit_verified=False,autosave_verified=False,confirmation_observed=False,
            exit_autosave_disabled_observed=True,uses_desktop_input=False,uses_ocr=False,native_submission_count=1)
        disabled_native=copy.deepcopy(native)
        disabled_native.update(action='disable_exit_autosave',status='autosave_disabled',stage_consumed=[True,True,False])
        disabled_native['exit_autosave']['postcondition_observed']=True
        disabled_native['dispatches']=[{key:False for key in row} for row in native['dispatches']]
        disabled['native_observation']=disabled_native
        (directory/'normal-exit-disable-fixture.result.json').write_text(json.dumps(disabled),encoding='utf-8')
        rows=[{'id':'disable','ok':True,'finished_at':'actual','plan':{'tool':'ck3_request_normal_exit_v1',
                  'args':{'action':'disable_exit_autosave'}},'result':codec.normal_exit_public_result_v2(disabled)},
              {'id':'confirm','ok':True,'finished_at':'actual','plan':{'tool':'ck3_request_normal_exit_v1',
                  'args':{'action':'confirm_desktop','expected_revision':'7','expected_exit_context_signature':'c'*64}},
               'result':codec.normal_exit_public_result_v2(confirm)}]
        if observe:rows.append({'id':'observe','ok':True,'finished_at':'actual',
            'plan':{'tool':'ck3_observe_normal_exit_v1','args':{}},'result':codec.normal_exit_public_result_v2(terminal)})
        report['steps']=rows
        return rows

    def test_typed_terminal_sdk_to_normal_close_without_gui_evidence(self):
        for observe in (False,True):
            with self.subTest(observe=observe), tempfile.TemporaryDirectory() as directory:
                root=Path(directory)
                client, clock, fake_time, report=self.make_client(root,review_at=None)
                self.typed_route(root,client,report,observe=observe)
                with patch.object(self.module,'time',fake_time):result=client.normal_close('synthetic-clean-typed-route')
                self.assertTrue(result['normal_close_qualified'])
                self.assertEqual(clock.now,0)
                self.assertIsNone(result['root_normal_gui_review'])
                self.assertIsNone(result['normal_quit_automation'])
                self.assertFalse(result['typed_normal_exit_route']['autosave_verified'])
                self.assertFalse(result['business_pass'])
                client.execute_plan.assert_not_called()

    def test_actual_inventory_producer_path_representation_reaches_normal_close(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            client,_,fake_time,report=self.make_client(root,review_at=None)
            self.typed_route(root,client,report)
            profile=json.loads(Path(client.context['normal_exit_managed_profile']['path']).read_text(encoding='utf-8'))
            inventory=json.loads(Path(profile['normal_exit_source_inventory']['path']).read_text(encoding='utf-8'))
            self.assertEqual(inventory['userdir'],Path(profile['userdir']).resolve().as_posix())
            self.assertEqual(Path(inventory['userdir']).resolve(),Path(profile['userdir']).resolve())
            if sys.platform=='win32':
                self.assertNotEqual(inventory['userdir'],profile['userdir'])
            with patch.object(self.module,'time',fake_time):result=client.normal_close('authored-real-producer-path')
            self.assertTrue(result['normal_close_qualified'])
            self.assertFalse(result['typed_normal_exit_route']['autosave_verified'])
            self.assertFalse(result['business_pass'])

    def test_actual_inventory_producer_keeps_wrong_root_relative_missing_and_type_guards(self):
        for defect in ('wrong_root','relative','missing','null','bool','float'):
            with self.subTest(defect=defect),tempfile.TemporaryDirectory() as directory:
                root=Path(directory)
                client,_,_,report=self.make_client(root,review_at=None)
                self.typed_route(root,client,report,inventory_defect=defect)
                with self.assertRaises(ValueError):client.typed_normal_quit_evidence(report)

    def test_typed_route_preserves_host_error_and_cleanup_failure(self):
        for defect in ('host_error','cleanup','native_exit','retained_exit'):
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as directory:
                root=Path(directory)
                client,_,fake_time,report=self.make_client(root,review_at=None,
                    os_exit=1 if defect=='retained_exit' else 0,native_exit=1 if defect=='native_exit' else 0)
                self.typed_route(root,client,report)
                if defect=='host_error':report['error']='original R0003-like collect failure'
                if defect=='cleanup':report['cleanup_ok']=False
                with patch.object(self.module,'time',fake_time):result=client.normal_close('synthetic-original-failure')
                self.assertFalse(result['normal_close_qualified'])
                self.assertFalse(result['business_pass'])
                self.assertEqual(result['host_error'],report['error'])

    def test_typed_route_requires_actual_producer_index_shape_and_exact_leaf_pins(self):
        from ck3_mod_acceptance import pin
        for defect in ('schema', 'missing_files', 'list', 'null', 'bool', 'missing_leaf',
                'absolute_key', 'bool_bytes', 'float_bytes', 'missing_sha', 'changed_sha', 'extra_path'):
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as directory:
                root=Path(directory)
                client,_,_,report=self.make_client(root,review_at=None)
                self.typed_route(root,client,report)
                index=Path(client.manifest['source_index']['path'])
                value=json.loads(index.read_bytes())
                files=value['files']
                leaf=next(iter(files))
                if defect=='schema':value['schema']='authored-other-index'
                elif defect=='missing_files':del value['files']
                elif defect=='list':value['files']=[pin(REPO/path) for path in files]
                elif defect=='null':value['files']=None
                elif defect=='bool':value['files']=True
                elif defect=='missing_leaf':del files[leaf]
                elif defect=='absolute_key':files[str(REPO/leaf)]=files.pop(leaf)
                elif defect=='bool_bytes':files[leaf]['bytes']=True
                elif defect=='float_bytes':files[leaf]['bytes']=float(files[leaf]['bytes'])
                elif defect=='missing_sha':del files[leaf]['sha256']
                elif defect=='changed_sha':files[leaf]['sha256']='f'*64
                elif defect=='extra_path':files[leaf]['path']=str(REPO/leaf)
                index.write_text(json.dumps(value),encoding='utf-8')
                client.manifest['source_index'].update(pin(index))
                with self.assertRaises(ValueError):
                    client.typed_normal_quit_evidence(report)

    def test_typed_route_mapping_round_trips_only_three_frozen_codec_sources(self):
        from ck3_mod_acceptance import pin
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            client,_,_,report=self.make_client(root,review_at=None)
            self.typed_route(root,client,report)
            index=Path(client.manifest['source_index']['path'])
            original=json.loads(index.read_bytes())
            # Match the real global index: unrelated source entries coexist with
            # the three leaves; loading the codec must not execute those entries.
            original['files']['authored-unselected.py']={'bytes':0,'sha256':'a'*64}
            index.write_text(json.dumps(original),encoding='utf-8')
            client.manifest['source_index'].update(pin(index))
            evidence=client.typed_normal_quit_evidence(report)
            self.assertIsNotNone(evidence)
            self.assertEqual(len(evidence['source_modules']),3)
            self.assertEqual(evidence['source_index'],pin(index))
            self.assertEqual(json.loads(json.dumps(evidence)),evidence)
            self.assertFalse(evidence['autosave_verified'])

    def test_actual_submitted_native_request_binds_fresh_public_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            client,_,_,report=self.make_client(root,review_at=None)
            rows=self.typed_route(root,client,report)
            confirm=rows[1]['plan']
            del confirm['args']['expected_revision']
            confirm['fresh_revision']=True
            evidence=client.typed_normal_quit_evidence(report)
            self.assertIsNotNone(evidence)
            self.assertTrue(Path(evidence['confirmation_request']['path']).name.endswith('.request.json'))
            for fresh in (False,None,1,'true'):
                with self.subTest(fresh=fresh):
                    confirm['fresh_revision']=fresh
                    with self.assertRaises(ValueError):client.typed_normal_quit_evidence(report)
            del confirm['fresh_revision']
            with self.assertRaises(ValueError):client.typed_normal_quit_evidence(report)

    def test_submitted_native_request_and_explicit_public_revision_keep_exact_guards(self):
        for defect in ('revision','revision_bool','revision_float','pid','actor','birth','generation',
                'nonce','inventory','signature','missing_request','explicit_wrong_revision'):
            with self.subTest(defect=defect),tempfile.TemporaryDirectory() as directory:
                root=Path(directory)
                client,_,_,report=self.make_client(root,review_at=None)
                rows=self.typed_route(root,client,report)
                request=root/'state/native-session/normal-exit-map-requests/normal-exit-confirm_desktop-fixture.request.json'
                value=json.loads(request.read_bytes())
                if defect=='revision':value['expected_revision']=7
                elif defect=='revision_bool':value['expected_revision']=True
                elif defect=='revision_float':value['expected_revision']=6.0
                elif defect=='pid':value['expected_game_pid']=99
                elif defect=='actor':value['expected_player_character_id']=99
                elif defect=='birth':value['expected_process_creation_filetime_100ns']+=1
                elif defect=='generation':value['expected_connection_generation']=2
                elif defect=='nonce':value['request_nonce']='other'
                elif defect=='inventory':value['source_inventory_sha256']='f'*64
                elif defect=='signature':value['expected_exit_context_signature']='f'*64
                elif defect=='explicit_wrong_revision':
                    rows[1]['plan']['fresh_revision']=True
                    rows[1]['plan']['args']['expected_revision']='8'
                if defect=='missing_request':request.unlink()
                else:request.write_text(json.dumps(value),encoding='utf-8')
                with self.assertRaises((ValueError,FileNotFoundError)):
                    client.typed_normal_quit_evidence(report)

    def test_typed_route_uses_original_finish_hold_and_final_native_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            client,_,fake_time,report=self.make_client(root,review_at=None)
            self.typed_route(root,client,report)
            report['finished_at']=None
            def finish(steps,name,reserve):
                self.assertEqual(steps,[{'id':'acceptance-normal-exit-finish-hold','kind':'finish_hold',
                                         'expect':{'hold_finished':True}}])
                self.assertEqual(reserve,0)
                report['finished_at']='2026-10-24T12:00:00+00:00'
                return [{'id':steps[0]['id'],'ok':True}]
            client.execute_plan=Mock(side_effect=finish)
            with patch.object(self.module,'time',fake_time):result=client.normal_close('synthetic-original-hold')
            client.execute_plan.assert_called_once()
            self.assertTrue(result['normal_close_qualified'])
            self.assertIsNotNone(result['native_zero_proof'])
            self.assertTrue(result['cleanup_ok'])

    def test_typed_route_rejects_foreign_sources_claims_types_and_missing_originals(self):
        for defect in ('birth','pid_bool','inventory','profile','claim','close','fact','source','duplicate_confirm','missing_disable'):
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as directory:
                root=Path(directory)
                client,_,_,report=self.make_client(root,review_at=None)
                rows=self.typed_route(root,client,report)
                terminal=rows[-1]['result']
                if defect=='birth':client._process['creation_filetime_100ns']='134373157160016546'
                elif defect=='pid_bool':terminal['process_observation']['pid']=True
                elif defect=='inventory':terminal['source_inventory_sha256']='f'*64
                elif defect=='profile':client.context['normal_exit_managed_profile']['sha256']='f'*64
                elif defect=='claim':Path(terminal['claim_path']).write_text('{}',encoding='utf-8')
                elif defect=='close':Path(terminal['observer_close_receipt_path']).unlink()
                elif defect=='fact':Path(terminal['receipt_path']).write_text('{}',encoding='utf-8')
                elif defect=='source':client.manifest['source_index']['sha256']='f'*64
                elif defect=='duplicate_confirm':rows.append(copy.deepcopy(rows[1]))
                elif defect=='missing_disable':rows.pop(0)
                with self.assertRaises((ValueError,FileNotFoundError)):
                    client.typed_normal_quit_evidence(report)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--client-source', type=Path, default=CLIENT_SOURCE)
    parser.add_argument('--host-source', type=Path, default=HOST_SOURCE)
    parser.add_argument('--tools-dir', type=Path, default=REPO / 'tools')
    args, remaining = parser.parse_known_args()
    CLIENT_SOURCE, HOST_SOURCE = args.client_source.resolve(), args.host_source.resolve()
    sys.path.insert(0, str(args.tools_dir.resolve()))  # Only the original pure check_pin import.
    unittest.main(argv=[sys.argv[0], *remaining])
