"""Portable pure-host preserved-failure lifecycle tests; no game or OS actions."""
from __future__ import annotations
import argparse, ast, asyncio, copy, json, re
from datetime import datetime, timezone
from pathlib import Path
import sys, unittest
from types import SimpleNamespace

REPO=Path(__file__).resolve().parents[1]
HOST=REPO/'ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py'

class FailureShutdownTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tree=ast.parse(HOST.read_text(encoding='utf-8'))
        names={'finished_native_process_exit_zero_proof','finished_native_exit_zero_proof','finished_native_failure_shutdown_proof','lookup'}
        body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
        plan=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='PlanClient')
        body.append(ast.ClassDef(name='PlanClient',bases=[],keywords=[],decorator_list=[],body=[n for n in plan.body if isinstance(n,ast.AsyncFunctionDef) and n.name in {'execute','observe_final'}]))
        cls.ns={'datetime':datetime,'timezone':timezone,'re':re,'copy':copy,'asyncio':asyncio,'now':lambda:datetime.now(timezone.utc).isoformat()}
        exec(compile(ast.fix_missing_locations(ast.Module(body=body,type_ignores=[])),str(HOST),'exec'),cls.ns)

    def report(self):
        pipe=r'\\.\pipe\SYNTHETIC-FAILURE-NO-PROCESS'
        error='RuntimeError: SYNTHETIC original startup failure'
        return {'fixture_only':False,'error':error,'pipe':pipe,'phase':'hold','status':'RED','cleanup_ok':True,
            'managed_session_done':True,'managed_session_thread_finished':True,
            'steps':[{'id':'original-failure','ok':False,'error':error,'finished_at':'2026-10-10T00:00:00+00:00'}],
            'session':{'error':None,'report':{'kind':'ck3_native_headless_session','mode':'native-headless','format_version':1,
            'ok':True,'error':None,'exit_reason':'process_exit','process_exit_code':0,'pid':2468,'pipe':pipe,
            'started_at':'2026-10-10T00:00:00+00:00','finished_at':'2026-10-10T00:00:01+00:00',
            'shutdown':{'ok':True,'cleanup_proven':True,'tree_gone':True,'ck3_pid':2468,'ck3_exit_code':0,
            'job_active_processes_final':0,'contract_errors':[],'watchdog_state_after':'absent','nonce':'a'*32,
            'ck3_creation_date':'SYNTHETIC-NO-REAL-PROCESS','control_files_absent':{'ck3.json':True,'watchdog.json':True},
            'final_ck3_inventory':{'tasklist_returncode':0,'tasklist_pids':[],'wmi_pids':[],'native_pids':[],'processes':[]}}}}}

    def test_error_keeps_strict_success_none_and_separate_failure_only(self):
        report=self.report();strict=self.ns['finished_native_exit_zero_proof'];failure=self.ns['finished_native_failure_shutdown_proof']
        self.assertIsNone(strict(report,True));proof=failure(report,True)
        self.assertIsNotNone(proof);self.assertEqual(proof['host_error'],report['error'])
        self.assertTrue(proof['failure_preserved']);self.assertFalse(proof['normal_close_qualified']);self.assertFalse(proof['business_pass'])
        healthy=copy.deepcopy(report);healthy['error']=None;healthy.pop('managed_session_thread_finished')
        self.assertIsNotNone(strict(healthy,True))
        self.assertIsNone(failure(healthy,True))

    def test_missing_actual_process_thread_cleanup_evidence_rejects(self):
        mutations=(lambda r:r.update(managed_session_thread_finished=False),
            lambda r:r['session']['report'].update(process_exit_code=1),
            lambda r:r['session']['report']['shutdown'].update(tree_gone=False),
            lambda r:r['session']['report']['shutdown'].update(control_files_absent={'ck3.json':False,'watchdog.json':True}))
        for mutate in mutations:
            report=self.report();mutate(report)
            self.assertIsNone(self.ns['finished_native_failure_shutdown_proof'](report,True))

    def client(self,report):
        client=self.ns['PlanClient'].__new__(self.ns['PlanClient'])
        client.report=report;client.results={};client.episode_identity={'bridge_pid':2468}
        client.args=SimpleNamespace(frontend_mod_load_observation=False)
        client.managed_done=SimpleNamespace(is_set=lambda:True);client.write=lambda:None
        async def forbidden(*_,**__):raise AssertionError('Dead native or business snapshot must never be queried')
        client.fresh=forbidden;client.call=forbidden
        return client

    def test_once_failure_finish_avoids_dead_queries_and_preserves_RED(self):
        report=self.report();old=copy.deepcopy(report['steps'][0]);error=report['error'];client=self.client(report)
        step={'id':'failure-lifecycle','kind':'finish_hold','failure_shutdown':True,
              'expect':{'hold_finished':True,'failure_preserved':True,'business_pass':False,'normal_close_qualified':False}}
        asyncio.run(client.execute([step]));self.assertIs(report['steps'][-1]['ok'],True)
        asyncio.run(client.observe_final())
        self.assertEqual(report['steps'][0],old);self.assertEqual(report['error'],error);self.assertEqual(report['status'],'RED')
        self.assertTrue(report['final_observation']['failure_preserved']);self.assertFalse(report['final_observation']['normal_close_qualified'])
        self.assertIn('post_failure_exit_finish_hold',report);self.assertNotIn('post_exit_finish_hold',report)
        with self.assertRaisesRegex(RuntimeError,'once-only'):
            asyncio.run(client.execute([{**step,'id':'second-must-reject'}]))
        self.assertIs(report['steps'][-1]['ok'],False)
        self.assertIn('once-only',report['steps'][-1]['error'])

    def test_unfinished_native_thread_cannot_finish_failed_hold(self):
        report=self.report();report['managed_session_thread_finished']=False;client=self.client(report)
        with self.assertRaisesRegex(RuntimeError,'actual native/thread cleanup'):
            asyncio.run(client.execute([{'id':'reject-unfinished','kind':'finish_hold','failure_shutdown':True}]))
        self.assertIs(report['steps'][-1]['ok'],False);self.assertNotIn('hold_finished_by_control_plan',report)
        self.assertNotIn('post_failure_exit_finish_hold',report);self.assertEqual(report['status'],'RED')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--host-source',type=Path,default=HOST)
    args,remaining=parser.parse_known_args();HOST=args.host_source.resolve()
    unittest.main(argv=[sys.argv[0],*remaining])
