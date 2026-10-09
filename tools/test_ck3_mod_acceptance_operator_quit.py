"""Portable actual-client tests for explicit GUI delegation and opt-in normal Quit.

Synthetic files, subprocesses and clocks only; no screenshots or desktop input.
"""
from __future__ import annotations
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

REPO = Path(__file__).resolve().parents[1]
TOOLS = REPO / 'tools'
CLIENT = TOOLS / 'ck3_mod_acceptance_client.py'
ENTRY = TOOLS / 'ck3_mod_acceptance.py'
HOST = REPO / 'ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OperatorQuitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load('_operator_quit_actual_client', CLIENT)
        cls.entry = load('_operator_quit_actual_entry', ENTRY)
        cls.close_fixture = load('_existing_close_fixture', TOOLS / 'test_ck3_mod_acceptance_normal_close.py')
        cls.entry_fixture = load('_existing_entry_fixture', TOOLS / 'test_ck3_mod_acceptance.py')
        cls.entry_fixture.entry = cls.entry
        cls.close_fixture.HOST_SOURCE = HOST

    def make_client(self, root, **kwargs):
        client, clock, fake_time, report = self.close_fixture.NormalCloseReviewRaceTests.make_client(self, root, **kwargs)
        client.live = root / client.frozen['run_id']
        client.keeper = root / 'keeper'
        client.frozen['screen_task'] = 'SYNTHETIC_SCREEN_OWNER'
        client.operator_reviewer = '/root'
        client.selection.locations = {'python': Path(sys.executable), 'repo_root': root}
        client.selection.runtime_environment = {'PYTHONUTF8': '1', 'PYTHONDONTWRITEBYTECODE': '1'}
        client.selection.normal_quit_automation = None
        client.focus_retained_process_for_quit = Mock(return_value={'synthetic_focus': True})
        return client, clock, fake_time, report

    def automation(self, client, clock, fake_time, *, mutate=None, exit_code=0, complete_at=.3, emit=True):
        config = {}
        for name in ('helper', 'matcher', 'templates'):
            path = client.output / (name + '.synthetic-source')
            path.write_bytes(b'SYNTHETIC ONLY: ' + name.encode())
            config[name] = self.entry.pin(path)
        client.selection.normal_quit_automation = config
        mapper = client.output / 'synthetic-final-mapper.json'
        mapper.write_text(json.dumps({'click_completed': True, 'failures': ['foreground_changed_after_click']}), encoding='utf-8')
        final = self.entry.pin(mapper)
        request = client.output / 'normal-quit-awaiting.json'
        process = SimpleNamespace(poll=lambda: exit_code if complete_at is not None and clock.now >= complete_at else None)
        real_sleep = fake_time.sleep
        written = False
        def sleep(seconds):
            nonlocal written
            real_sleep(seconds)
            if emit and complete_at is not None and clock.now >= complete_at and not written:
                receipt = {'schema': 'ck3.common-normal-quit-automation.v1',
                    'status': 'GUI_QUIT_ROUTE_COMPLETE_NATIVE_PROOF_PENDING', 'route_complete': True,
                    'automation_actor': 'template-automation', 'human_review_claimed': False,
                    'run_id': client.frozen['run_id'], **client._process, 'hwnd': 500,
                    'original_hold_deadline': client._hold, 'quit_request': self.entry.pin(request), **copy.deepcopy(config),
                    'autosave_unchecked_observed': True, 'final_click_completed': True,
                    'steps': [{'final': True, 'mapping_receipt': final, 'click_completed': True}],
                    'final_click': final, 'evidence': [final], 'actual_os0_proven': False,
                    'actual_native0_proven': False, 'finish_hold_dispatched': False, 'business_pass': False}
                if mutate: mutate(receipt)
                self.module.write_once(client.output / 'normal-quit-automation-result.json', receipt)
                written = True
        fake_time.sleep = sleep
        return Mock(return_value=process)

    def test_opt_in_dispatches_once_and_independent_route_needs_actual_native_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            client, clock, fake_time, report = self.make_client(Path(directory), review_at=None)
            popen = self.automation(client, clock, fake_time)
            self.assertIsNotNone(client.native_zero_proof(report))
            with patch.object(self.module, 'time', fake_time), patch.object(self.module.subprocess, 'Popen', popen):
                result = client.normal_close('SYNTHETIC_AUTOMATION')
            popen.assert_called_once()
            argv = popen.call_args.args[0]
            for flag, value in (('--live', client.live), ('--keeper-root', client.keeper), ('--output', client.output)):
                self.assertEqual(Path(argv[argv.index(flag)+1]), value.resolve())
            self.assertEqual(Path(argv[argv.index('--repo-root')+1]), client.selection.locations['repo_root'])
            for name in ('matcher','templates'):
                expected=client.selection.normal_quit_automation[name]
                self.assertEqual(argv[argv.index('--'+name)+1],expected['path'])
                self.assertEqual(argv[argv.index('--'+name+'-sha256')+1],expected['sha256'])
                self.assertEqual(argv[argv.index('--'+name+'-bytes')+1],str(expected['bytes']))
            request = self.module.read_json(client.output / 'normal-quit-awaiting.json')
            self.assertEqual(request['screen_task'], client.frozen['screen_task'])
            self.assertEqual(request['original_hold_deadline'], client._hold)
            self.assertTrue(result['normal_close_qualified'])
            self.assertIsNone(result['root_normal_gui_review'])
            self.assertIs(result['normal_quit_automation']['human_review_claimed'], False)
            self.assertFalse((client.output / 'normal-quit-root-result.json').exists())
            client.execute_plan.assert_not_called()

    def test_route_cannot_replace_os_native_cleanup_done_or_business_error(self):
        for boundary in ('os1', 'native1', 'cleanup', 'done', 'error'):
            with self.subTest(boundary=boundary), tempfile.TemporaryDirectory() as directory:
                client, clock, fake_time, report = self.make_client(Path(directory), review_at=None,
                    os_exit=1 if boundary == 'os1' else 0, native_exit=1 if boundary == 'native1' else 0)
                if boundary == 'cleanup': report['cleanup_ok'] = False
                if boundary == 'done': report['managed_session_done'] = False
                if boundary == 'error': report['error'] = 'SYNTHETIC ORIGINAL BUSINESS FAILURE'
                popen = self.automation(client, clock, fake_time)
                with patch.object(self.module, 'time', fake_time), patch.object(self.module.subprocess, 'Popen', popen):
                    result = client.normal_close('SYNTHETIC_FAILURE_PRESERVED')
                self.assertFalse(result['normal_close_qualified'])
                self.assertEqual(result['host_error'], report['error'])
                popen.assert_called_once()
                client.execute_plan.assert_not_called()

    def test_cross_scene_or_claimed_human_or_invalid_click_receipts_are_rejected(self):
        mutations = {'run': lambda r:r.update(run_id='OTHER_RUN'), 'pid':lambda r:r.update(pid=True),
            'ctime': lambda r:r.update(create_time=999), 'deadline':lambda r:r.update(original_hold_deadline=999),
            'human':lambda r:r.update(human_review_claimed=True), 'business':lambda r:r.update(business_pass=True),
            'source':lambda r:r['matcher'].update(sha256='0'*64), 'final':lambda r:r.update(final_click={}),
            'native_claim':lambda r:r.update(actual_native0_proven=True)}
        for name, mutate in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                client, clock, fake_time, _ = self.make_client(Path(directory), review_at=None)
                popen = self.automation(client, clock, fake_time, mutate=mutate)
                with patch.object(self.module, 'time', fake_time), patch.object(self.module.subprocess, 'Popen', popen), self.assertRaises(ValueError):
                    client.normal_close('SYNTHETIC_BAD_RECEIPT')
                self.assertFalse((client.output / 'normal-close-result.json').exists())
                popen.assert_called_once()
                client.execute_plan.assert_not_called()

    def test_helper_failure_or_original_deadline_never_replays(self):
        for exit_code, complete_at, emit in ((1,.2,False),(0,None,False),(0,.2,False)):
            with self.subTest(exit_code=exit_code, complete_at=complete_at), tempfile.TemporaryDirectory() as directory:
                client, clock, fake_time, _ = self.make_client(Path(directory), review_at=None, deadline=.4)
                popen = self.automation(client, clock, fake_time, exit_code=exit_code, complete_at=complete_at, emit=emit)
                with patch.object(self.module, 'time', fake_time), patch.object(self.module.subprocess, 'Popen', popen):
                    if complete_at is None or exit_code != 0:
                        result = client.normal_close('SYNTHETIC_PENDING_UNTIL_DEADLINE')
                        self.assertFalse(result['normal_close_qualified'])
                        self.assertLess(clock.now, .51)
                    else:
                        with self.assertRaises((ValueError, FileNotFoundError)):
                            client.normal_close('SYNTHETIC_FAILED_NO_REPLAY')
                popen.assert_called_once()
                client.execute_plan.assert_not_called()

    def test_default_manual_path_never_starts_automation(self):
        with tempfile.TemporaryDirectory() as directory:
            client, _, fake_time, _ = self.make_client(Path(directory))
            with patch.object(self.module, 'time', fake_time), patch.object(self.module.subprocess, 'Popen') as popen:
                result = client.normal_close('SYNTHETIC_ORIGINAL_MANUAL')
            popen.assert_not_called()
            self.assertTrue(result['normal_close_qualified'])
            self.assertEqual(result['root_normal_gui_review']['reviewer'], '/root')
            self.assertIsNone(result['normal_quit_automation'])

    def test_actual_selection_keeps_default_and_pins_shared_opt_in(self):
        fixture = self.entry_fixture.SharedEntryTests(methodName='test_changed_shared_pin_blocks')
        fixture.setUp()
        try:
            self.assertIsNone(fixture.select().normal_quit_automation)
            config = {key:self.entry.pin(fixture.files['initial']) for key in ('helper','matcher','templates')}
            fixture.runtime['normal_quit_automation'] = config
            fixture.write(fixture.runtime_path, fixture.runtime)
            selected = fixture.select()
            self.assertEqual(selected.normal_quit_automation, config)
            self.assertEqual(selected.preflight()['blockers'], [])
            fixture.files['initial'].write_bytes(b'CHANGED INPUT')
            self.assertTrue(any('Pinned input changed' in row for row in selected.preflight()['blockers']))
            fixture.runtime['normal_quit_automation']['unreviewed'] = {}
            fixture.write(fixture.runtime_path, fixture.runtime)
            with self.assertRaisesRegex(ValueError, 'exactly helper/matcher/templates'): fixture.select()
        finally:
            fixture.doCleanups()

    def delegated_client(self, root, mutation=None, *, enabled=True):
        live = root / 'SYNTHETIC_DELEGATED_RUN'
        live.mkdir()
        frozen = live / 'frozen-argv.json'
        self.module.write_once(frozen, {'run_id':live.name, 'screen_task':'SYNTHETIC_SCREEN', 'argv':['SYNTHETIC ONLY']})
        context = {'reviewer':'/root','frozen_argv':self.entry.pin(frozen), 'keeper_root':str(root/'keeper')}
        if enabled:
            value = {'schema':'ck3-mod-acceptance-operator-delegation-v1','run_id':live.name,
                'screen_task':'SYNTHETIC_SCREEN','frozen_argv':self.entry.pin(frozen),'delegated_by':'/root',
                'delegate_reviewer':'/root/synthetic_operator','scopes':['ui','checkpoint']}
            if mutation: mutation(value)
            artifact = root / 'delegation.json'
            self.module.write_once(artifact,value)
            context['operator_delegation'] = self.entry.pin(artifact)
        selection=SimpleNamespace(context=context,context_path=root/'context.json',run_dir=live,state_dir=root/'state',
            manifest={},product_key='SYNTHETIC',case={'id':'SYNTHETIC'},argv=['SYNTHETIC ONLY'],manifest_path=root/'manifest.json')
        self.module.write_once(selection.context_path, context)
        return self.module.CaseClient(selection)

    def test_delegation_is_explicit_and_checkpoint_records_actual_operator(self):
        for enabled in (False,True):
            with self.subTest(enabled=enabled), tempfile.TemporaryDirectory() as directory:
                client = self.delegated_client(Path(directory), enabled=enabled)
                expected = '/root/synthetic_operator' if enabled else '/root'
                self.assertEqual(client.operator_reviewer, expected)
                client._hold=1;client.remaining=lambda:100;client.guard=lambda reserve:None
                self.module.write_once(client.output/'synthetic-root-result.json',{'run_id':client.frozen['run_id'],'reviewer':expected})
                value=client.root_checkpoint('synthetic',{'operator_reviewer':'NOT_AUTHORITY'})
                self.assertEqual(value['reviewer'],expected)
                self.assertEqual(self.module.read_json(client.output/'synthetic-awaiting.json')['operator_reviewer'],expected)
                self.module.write_once(client.output/'cross-root-result.json',{'run_id':client.frozen['run_id'],'reviewer':'OTHER_OPERATOR'})
                with self.assertRaisesRegex(ValueError,'crossed scene'):client.root_checkpoint('cross',{})

    def test_delegation_cannot_cross_run_screen_frozen_authority_or_scope(self):
        mutations = (lambda v:v.update(run_id='OTHER'),lambda v:v.update(screen_task='OTHER'),
            lambda v:v['frozen_argv'].update(sha256='0'*64),lambda v:v.update(delegated_by='OTHER'),
            lambda v:v.update(scopes=['ui','launch']),lambda v:v.update(delegate_reviewer='/root'))
        for index,mutation in enumerate(mutations):
            with self.subTest(index=index), tempfile.TemporaryDirectory() as directory, self.assertRaises(ValueError):
                self.delegated_client(Path(directory),mutation)

    def test_template_profile_uses_explicit_pack_geometry_without_scaling(self):
        helper=load('_portable_normal_quit_helper',CLIENT.with_name('ck3_mod_acceptance_normal_quit.py'))
        names=('decisions-quill','map-pause-menu-button','quit-menu-button','quit-to-desktop',
               'quit-autosave-checked','quit-autosave-unchecked','character-profile-close','production-decisions-close')
        templates={name:{'source':{'size':[640,480]},'minimum_correlation':.92,
                   'minimum_runner_up_gap':.05,'scale':1.0} for name in names}
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'synthetic-profile.json'
            path.write_text(json.dumps({'templates':templates}),encoding='utf-8')
            actual,size=helper.template_profile(path)
            self.assertEqual(size,(640,480))
            self.assertEqual(actual,templates)
            for key,value in (('source',{'size':[800,600]}),('minimum_correlation',.9),('scale',True)):
                changed=copy.deepcopy(templates);changed[names[0]][key]=value
                path.write_text(json.dumps({'templates':changed}),encoding='utf-8')
                with self.subTest(key=key),self.assertRaises(RuntimeError):helper.template_profile(path)

    def test_failed_startup_retains_actual_control_handle_before_business_rejection(self):
        import ctypes
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            client, clock, fake_time, report=self.make_client(root,review_at=None)
            fake_time.monotonic=lambda:clock.now
            client._handle=None;client._process=None;client._hold=None
            client.state=root/'state';client.state.mkdir()
            self.module.write_once(client.state/'control/ck3.json',{'ck3_pid':2468,'creation_date':'SYNTHETIC'})
            client.manifest={'host':{'kind':'host'},'source_root':{'kind':'source'}}
            client.selection.manifest_path_key=lambda row:HOST if row['kind']=='host' else root/'shared-source'
            client.selection.case['budgets']={'timeout':1,'readiness_timeout':1,'hold_seconds':600}
            client.selection.prepared={}
            client.report_path=root/'native-report.json';client._report=None;client._report_stat=None
            report.update(state_dir=str(client.state),agent_source_root=str(root/'shared-source'),
                error='SYNTHETIC ORIGINAL STARTUP FAILURE',status='RED',finished_at=None,hold_until_utc_estimated=1000)
            self.module.write_once(client.report_path,report)
            client.read_report=self.module.CaseClient.read_report.__get__(client)
            process=SimpleNamespace(name=lambda:'ck3.exe',create_time=lambda:123.5)
            kernel=SimpleNamespace(**{name:Mock(return_value=8642 if name=='OpenProcess' else 1)
                for name in ('OpenProcess','WaitForSingleObject','GetExitCodeProcess','CloseHandle')})
            with patch.object(self.module,'time',fake_time),patch.dict(sys.modules,{'psutil':SimpleNamespace(Process=lambda pid:process)}), \
                 patch.object(ctypes,'WinDLL',return_value=kernel,create=True), \
                 self.assertRaisesRegex(ValueError,'Actual shared host failed'):
                client.wait_hold()
            self.assertEqual(client._handle,8642)
            self.assertEqual(client._process['pid'],2468)
            self.assertEqual(client._process['create_time'],123.5)
            self.assertEqual(client.read_report(allow_error=True)['error'],'SYNTHETIC ORIGINAL STARTUP FAILURE')
            self.assertIsNone(client.native_zero_proof(report))
            kernel.OpenProcess.assert_called_once_with(0x100000|0x1000,False,2468)
            client.close_handle()
            kernel.CloseHandle.assert_called_once_with(8642)

    def test_failed_entry_finally_uses_actual_hold_fallback_and_keeps_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            launcher=root/'synthetic-launcher.py';launcher.write_text('SYNTHETIC ONLY')
            selected=self.entry.Selection.__new__(self.entry.Selection)
            selected.preflight=lambda:{'blockers':[]}
            selected.context={'run_id':'SYNTHETIC_FAILED_ENTRY','keeper_root':str(root/'keeper'),
                'proof':str(root/'proof'),'challenge':str(root/'challenge'),'observed_nonce':'SYNTHETIC','reviewer':'/root'}
            selected.runtime={'reviewed_launcher':self.entry.pin(launcher)}
            selected.runtime_path=root/'runtime.json';selected.context_path=root/'context.json'
            selected.run_dir=root/'SYNTHETIC_FAILED_ENTRY';selected.locations={'python':Path(sys.executable),'repo_root':root}
            selected.runtime_environment={};selected.adapter_path=root/'synthetic-adapter.py'
            adapter=SimpleNamespace(run_case=Mock(side_effect=AssertionError('Never replay failed startup business')))
            selected.load_adapter=lambda:adapter;selected.adapter_context=lambda output:{'synthetic':True}
            client=SimpleNamespace(_handle=None,output=root/'case-output',
                wait_hold=Mock(side_effect=ValueError('SYNTHETIC ORIGINAL STARTUP FAILURE')),
                normal_close=Mock(return_value={'normal_close_qualified':False,'host_error':'SYNTHETIC ORIGINAL STARTUP FAILURE'}),
                close_handle=Mock())
            def retain_held(**kwargs):
                client._handle='SYNTHETIC RETAINED HANDLE';return True
            client.retain_held_process=Mock(side_effect=retain_held)
            with patch.dict(sys.modules,{'ck3_mod_acceptance_client':self.module}), \
                 patch.object(self.module,'CaseClient',return_value=client), \
                 patch.object(self.entry.subprocess,'run',return_value=SimpleNamespace(returncode=0)):
                answer=selected.run()
            client.retain_held_process.assert_called_once_with(wait=True)
            client.normal_close.assert_called_once_with('business_failure_preserved')
            client.close_handle.assert_called_once()
            adapter.run_case.assert_not_called()
            self.assertIn('SYNTHETIC ORIGINAL STARTUP FAILURE',answer['case_error'])
            self.assertFalse(answer['normal_close']['normal_close_qualified'])
            self.assertEqual(answer['business_acceptance'],'RED_OR_INCOMPLETE')

    def test_retention_fallback_never_manufactures_a_launch_or_pre_hold_quit(self):
        with tempfile.TemporaryDirectory() as directory:
            client, _, _, report=self.make_client(Path(directory),review_at=None)
            client.state=Path(directory)/'unused-state';client._handle=None
            client.retain_process=Mock(side_effect=AssertionError('No actual control means no retained handle'))
            report.update(finished_at=None,phase='starting')
            self.assertFalse(client.retain_held_process(report))
            report['phase']='hold'
            self.assertFalse(client.retain_held_process(report))
            client.read_report=Mock(side_effect=FileNotFoundError('No actual launch report'))
            self.assertFalse(client.retain_held_process())
            client.retain_process.assert_not_called()

    def test_failure_finally_waits_for_actual_hold_only_inside_original_readiness(self):
        for reaches_hold in (True,False):
            with self.subTest(reaches_hold=reaches_hold),tempfile.TemporaryDirectory() as directory:
                root=Path(directory)
                client,clock,fake_time,report=self.make_client(root,review_at=None,deadline=1)
                fake_time.monotonic=lambda:clock.now
                client.state=root/'state';client._handle=None;client._readiness_limit=.4
                self.module.write_once(client.state/'control/ck3.json',{'ck3_pid':2468})
                report.update(finished_at=None,error='SYNTHETIC ORIGINAL STARTUP FAILURE')
                def read_report(allow_error=False):
                    self.assertTrue(allow_error)
                    return {**report,'phase':'hold' if reaches_hold and clock.now>=.2 else 'starting'}
                client.read_report=read_report
                def retain():client._handle='SYNTHETIC RETAINED HANDLE'
                client.retain_process=Mock(side_effect=retain)
                with patch.object(self.module,'time',fake_time):
                    retained=client.retain_held_process(wait=True)
                self.assertIs(retained,reaches_hold)
                self.assertLess(clock.now,.51)
                self.assertEqual(report['error'],'SYNTHETIC ORIGINAL STARTUP FAILURE')
                if reaches_hold:client.retain_process.assert_called_once()
                else:client.retain_process.assert_not_called()

    def test_failed_host_keeps_strict_native0_false_and_waits_only_original_hold(self):
        with tempfile.TemporaryDirectory() as directory:
            client, clock, fake_time, report=self.make_client(Path(directory),review_at=None,deadline=.4)
            report.update(error='SYNTHETIC ORIGINAL STARTUP FAILURE',status='RED',finished_at=None)
            popen=self.automation(client,clock,fake_time,complete_at=.2)
            self.assertIsNone(client.native_zero_proof(report))
            with patch.object(self.module,'time',fake_time),patch.object(self.module.subprocess,'Popen',popen):
                result=client.normal_close('business_failure_preserved')
            self.assertFalse(result['normal_close_qualified'])
            self.assertIsNone(result['native_zero_proof'])
            self.assertIsNone(result['finish_hold_rows'])
            self.assertEqual(result['host_error'],'SYNTHETIC ORIGINAL STARTUP FAILURE')
            self.assertTrue(result['retained_handle']['actual_retained_os0'])
            self.assertLess(clock.now,.51)
            client.execute_plan.assert_not_called()

    def focus_fixture(self,root,*,boundary=None):
        client,clock,fake_time,_=self.make_client(root,review_at=None,deadline=10)
        client.state=root/'state'
        self.module.write_once(client.state/'control/ck3.json',{'ck3_pid':2468})
        client.keeper.mkdir()
        (client.keeper/'journal.jsonl').write_text(json.dumps({'result':'OWNED_CAS',
            'lease':{'task_id':'OTHER_SCREEN' if boundary=='lease' else client.frozen['screen_task']}})+'\n',encoding='utf-8')
        process=SimpleNamespace(name=lambda:'ck3.exe',create_time=lambda:999 if boundary=='ctime' else 123.5)
        windows=[101,202,303] if boundary=='multiple' else [101,202]
        gui=SimpleNamespace(EnumWindows=lambda visit,arg:[visit(hwnd,arg) for hwnd in windows],IsWindowVisible=lambda hwnd:True)
        window_process=SimpleNamespace(GetWindowThreadProcessId=lambda hwnd:(1,16360 if hwnd==101 else 2468))
        steam={'foreground_pid':16360,'foreground_hwnd':101,'focus_hwnd':101}
        ck3={'foreground_pid':2468,'foreground_hwnd':202,'focus_hwnd':202}
        activated=SimpleNamespace(value=False)
        activation=Mock(side_effect=lambda hwnd:setattr(activated,'value',True))
        coords=SimpleNamespace(foreground_state=lambda:steam if boundary=='blocked' or not activated.value else ck3)
        modules={'psutil':SimpleNamespace(Process=lambda pid:process),'win32gui':gui,'win32process':window_process,
            'desktop_coordinate_map':coords,'record_native_capability_segment':SimpleNamespace(bring_forward=activation)}
        client.focus_retained_process_for_quit=self.module.CaseClient.focus_retained_process_for_quit.__get__(client)
        return client,clock,fake_time,modules,activation

    def test_quit_focus_binds_unique_retained_pid_window_and_reads_actual_focus(self):
        with tempfile.TemporaryDirectory() as directory:
            client,_,fake_time,modules,activation=self.focus_fixture(Path(directory))
            with patch.object(self.module,'time',fake_time),patch.dict(sys.modules,modules):
                receipt=client.focus_retained_process_for_quit()
            activation.assert_called_once_with(202)
            self.assertTrue(receipt['success'])
            self.assertEqual(receipt['pid'],2468)
            self.assertEqual(receipt['after']['foreground_hwnd'],202)
            self.assertIs(receipt['mouse_or_keyboard_input'],False)
            self.assertIs(receipt['human_review_claimed'],False)

    def test_bad_identity_lease_ambiguous_or_unfocused_window_never_dispatches_helper(self):
        for boundary in ('ctime','lease','multiple','blocked','consumed'):
            with self.subTest(boundary=boundary),tempfile.TemporaryDirectory() as directory:
                root=Path(directory)
                client,clock,fake_time,modules,activation=self.focus_fixture(root,boundary=boundary)
                config={}
                for name in ('helper','matcher','templates'):
                    source=root/(name+'.synthetic-source');source.write_text('SYNTHETIC ONLY')
                    config[name]=self.entry.pin(source)
                if boundary=='consumed':
                    self.module.write_once(client.output/'normal-quit-automation-dispatch.json',{'SYNTHETIC':'ALREADY CONSUMED'})
                with patch.object(self.module,'time',fake_time),patch.dict(sys.modules,modules), \
                     patch.object(self.module.subprocess,'Popen') as popen,self.assertRaises(ValueError):
                    client.start_normal_quit_automation(root/'synthetic-request.json',config)
                popen.assert_not_called()
                if boundary!='blocked':activation.assert_not_called()
                self.assertLessEqual(clock.now,2.1)


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--tools-dir',type=Path,default=TOOLS)
    parser.add_argument('--client-source',type=Path,default=CLIENT)
    parser.add_argument('--entry-source',type=Path,default=ENTRY)
    parser.add_argument('--host-source',type=Path,default=HOST)
    args, remaining=parser.parse_known_args()
    TOOLS,CLIENT,ENTRY,HOST=map(Path,(args.tools_dir,args.client_source,args.entry_source,args.host_source))
    sys.path.insert(0,str(TOOLS.resolve()))
    unittest.main(argv=[sys.argv[0],*remaining],verbosity=2)
