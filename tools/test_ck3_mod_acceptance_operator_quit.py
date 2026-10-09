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
                    if complete_at is None:
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
