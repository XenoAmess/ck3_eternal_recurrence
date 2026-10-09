"""Portable synthetic regressions for failed-helper manual Quit custody.

No game, desktop, process, task lease, native pipe or GUI review is real here.
"""
from __future__ import annotations
import argparse, copy, ctypes, hashlib, importlib.util, json
from pathlib import Path
import sys, tempfile, unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from PIL import Image

REPO=Path(__file__).resolve().parents[1]
CLIENT=REPO/'tools/ck3_mod_acceptance_client.py'
HOST=REPO/'ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py'

def pin(path):
    raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

class ManualFallbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('_manual_fallback_client',CLIENT)
        cls.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.module)

    def make_client(self, root, *, review=True, mutate=None):
        c=self.module.CaseClient.__new__(self.module.CaseClient)
        c.output=root;c.live=root;c.keeper=root/'SYNTHETIC-keeper';c._handle=object()
        c._process={'pid':2468,'create_time':123.5}
        c.frozen={'run_id':root.name,'screen_task':'SYNTHETIC_SCREEN','reviewer':'/root/actual-runner',
            'argv':['SYNTHETIC_ONLY'],'runtime_environment':{}}
        frozen_path=root/'frozen-argv.json';frozen_path.write_text(json.dumps(c.frozen),encoding='utf-8')
        c.context={'run_id':root.name,'reviewer':'/root/actual-runner','frozen_argv':pin(frozen_path)}
        context_path=root/'actual-run-context.json'
        context_path.write_text(json.dumps(c.context),encoding='utf-8')
        c._hold=1.0;c._started=0;c.manifest={'host':{}}
        c.selection=SimpleNamespace(case={'budgets':{}},manifest_path_key=lambda _:HOST,context_path=context_path,
            context=c.context,run_dir=c.live,argv=c.frozen['argv'],runtime_environment={},normal_quit_automation={'synthetic':True})
        c.operator_reviewer='/root/actual-runner'
        clock=SimpleNamespace(now=0.0,review_written=False)
        source=root/'SYNTHETIC-unchecked.png';after=root/'SYNTHETIC-after-click.png'
        Image.new('RGB',(3,2),'black').save(source);Image.new('RGB',(3,2),'white').save(after)
        mapped=root/'SYNTHETIC-canonical-final.json'
        mapped.write_text(json.dumps({'click_completed':True,'failures':['foreground_changed_after_click'],
            'source_image':str(source),'source_image_size':[3,2],'receipt_path':str(after)}),encoding='utf-8')
        evidence=[pin(source),pin(mapped),pin(after)]
        reviewed={'run_id':c.frozen['run_id'],'reviewer':'/root/actual-runner','normal_gui_quit':True,
            **c._process,'original_hold_deadline':c._hold,'autosave_unchecked_observed':True,
            'autosave_unchecked_screenshot':evidence[0],'final_click':evidence[1],'evidence':evidence,'synthetic_only':True}
        if mutate:mutate(reviewed)
        def sleep(seconds):
            clock.now+=seconds
            if review and not clock.review_written:
                self.module.write_once(root/'normal-quit-root-result.json',reviewed);clock.review_written=True
        fake_time=SimpleNamespace(time=lambda:clock.now,sleep=sleep)
        def exit_code(_handle,pointer):ctypes.cast(pointer,ctypes.POINTER(ctypes.c_uint32)).contents.value=0;return 1
        c._kernel=SimpleNamespace(WaitForSingleObject=lambda *_:0,GetExitCodeProcess=exit_code)
        pipe=r'\\.\pipe\SYNTHETIC-NO-NATIVE-PROCESS'
        error='RuntimeError: SYNTHETIC original startup TEST FAIL'
        report={'fixture_only':False,'error':error,'pipe':pipe,'phase':'hold','managed_session_done':True,
            'managed_session_thread_finished':True,'cleanup_ok':True,'steps':[{'ok':False,'error':error}],
            'session':{'error':None,'report':{'kind':'ck3_native_headless_session','mode':'native-headless','format_version':1,
            'ok':True,'error':None,'exit_reason':'process_exit','process_exit_code':0,'pid':2468,'pipe':pipe,
            'started_at':'2026-10-10T00:00:00+00:00','finished_at':'2026-10-10T00:00:01+00:00',
            'shutdown':{'ok':True,'cleanup_proven':True,'tree_gone':True,'ck3_pid':2468,'ck3_exit_code':0,
            'job_active_processes_final':0,'contract_errors':[],'watchdog_state_after':'absent','nonce':'a'*32,
            'ck3_creation_date':'SYNTHETIC-NO-PROCESS','control_files_absent':{'ck3.json':True,'watchdog.json':True},
            'final_ck3_inventory':{'tasklist_returncode':0,'tasklist_pids':[],'wmi_pids':[],'native_pids':[],'processes':[]}}}}}
        c.read_report=lambda allow_error=False:report
        c.start_normal_quit_automation=Mock(return_value=SimpleNamespace(poll=lambda:1))
        failed_route=root/'normal-quit-automation-result.json';failed_route.write_text('{"status":"SYNTHETIC_FAILED_HELPER"}',encoding='utf-8')
        c.validate_normal_quit_automation=Mock(side_effect=AssertionError('Nonzero helper receipt must not qualify'))
        def finish(steps,*_,**__):
            self.assertEqual(len(steps),1);self.assertEqual(steps[0]['kind'],'finish_hold');self.assertIs(steps[0]['failure_shutdown'],True)
            self.assertIs(c._failure_shutdown_retained['actual_retained_os0'],True)
            proof=c.native_failure_shutdown_proof(report);self.assertIsNotNone(proof)
            report['post_failure_exit_finish_hold']={'proof':proof};report['finished_at']='2026-10-10T00:00:02+00:00'
            return [{'ok':True}]
        c.execute_plan=Mock(side_effect=finish)
        return c,clock,fake_time,report,failed_route

    def test_failed_helper_actual_runner_review_closes_failure_once(self):
        with tempfile.TemporaryDirectory() as directory:
            c,clock,fake_time,report,failed=self.make_client(Path(directory));original=failed.read_bytes();error=report['error']
            with patch.object(self.module,'time',fake_time):result=c.normal_close('SYNTHETIC_FAILURE')
            c.start_normal_quit_automation.assert_called_once();c.execute_plan.assert_called_once()
            self.assertLess(clock.now,.3);self.assertIsNotNone(c._handle)
            self.assertEqual(failed.read_bytes(),original);self.assertEqual(report['error'],error)
            self.assertEqual(result['operator_normal_gui_review']['reviewer'],'/root/actual-runner')
            self.assertTrue(result['failure_lifecycle_completed']);self.assertTrue(result['failure_preserved'])
            self.assertFalse(result['normal_close_qualified']);self.assertFalse(result['business_pass']);self.assertIsNone(result['native_zero_proof'])
            self.assertTrue((c.output/'manual-quit-awaiting.json').is_file())

    def test_missing_manual_review_uses_only_original_deadline_no_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            c,clock,fake_time,_,_=self.make_client(Path(directory),review=False)
            with patch.object(self.module,'time',fake_time):result=c.normal_close('SYNTHETIC_NO_REVIEW')
            self.assertGreaterEqual(clock.now,1);self.assertLess(clock.now,1.11)
            c.start_normal_quit_automation.assert_called_once();c.execute_plan.assert_not_called()
            self.assertFalse(result['normal_close_qualified']);self.assertFalse(result['failure_lifecycle_completed'])

    def test_forged_root_or_missing_unchecked_or_mapping_is_rejected(self):
        for mutate in (lambda r:r.update(reviewer='/root'),lambda r:r.update(autosave_unchecked_observed=False),lambda r:r.update(final_click={})):
            with self.subTest(mutate=mutate),tempfile.TemporaryDirectory() as directory:
                c,_,fake_time,_,_=self.make_client(Path(directory),mutate=mutate)
                with patch.object(self.module,'time',fake_time),self.assertRaises(ValueError):c.normal_close('SYNTHETIC_INVALID_REVIEW')
                c.execute_plan.assert_not_called();self.assertIsNotNone(c._handle)

    def test_actual_context_reviewer_must_match_persisted_and_frozen_context(self):
        with tempfile.TemporaryDirectory() as directory:
            c,_,_,_,_=self.make_client(Path(directory))
            self.assertEqual(c.resolve_operator_reviewer(),'/root/actual-runner')
            for value in ('', ' /root/actual-runner','/root/forged'):
                c.context['reviewer']=value
                with self.subTest(value=value),self.assertRaises(ValueError):c.resolve_operator_reviewer()
            c.context['reviewer']='/root/actual-runner';c.frozen['reviewer']='/root/another'
            frozen_path=c.live/'frozen-argv.json';frozen_path.write_text(json.dumps(c.frozen),encoding='utf-8')
            c.context['frozen_argv']=pin(frozen_path)
            c.selection.context_path.write_text(json.dumps(c.context),encoding='utf-8')
            with self.assertRaises(ValueError):c.resolve_operator_reviewer()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--client-source',type=Path,default=CLIENT)
    parser.add_argument('--host-source',type=Path,default=HOST);parser.add_argument('--tools-dir',type=Path,default=REPO/'tools')
    args,remaining=parser.parse_known_args();CLIENT=args.client_source.resolve();HOST=args.host_source.resolve()
    sys.path.insert(0,str(args.tools_dir.resolve()));unittest.main(argv=[sys.argv[0],*remaining])
