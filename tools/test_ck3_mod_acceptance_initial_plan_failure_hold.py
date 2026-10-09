"""Pure execution of the actual host's failed-plan try/finally and queue methods.

Every process, native DTO, clock, GUI exit and control directory is synthetic.
No imports or calls into a game, bridge, runtime supervisor or desktop are made.
"""
import argparse
import ast
import asyncio
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import tempfile
import threading
import traceback
from types import SimpleNamespace
import unittest

parser = argparse.ArgumentParser()
parser.add_argument('--host-source', type=Path, action='append', required=True)
options, remaining = parser.parse_known_args()


def phase_assignment(node, value):
    return (isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant)
            and node.value.value == value and any(isinstance(target, ast.Subscript)
            and isinstance(target.value, ast.Name) and target.value.id == 'report'
            and isinstance(target.slice, ast.Constant) and target.slice.value == 'phase'
            for target in node.targets))


class InitialPlanFailureHoldTests(unittest.TestCase):
    def exercise_source(self, source, root):
        tree = ast.parse(source.read_text(encoding='utf-8-sig'))
        run = next(node for node in tree.body if isinstance(node, ast.AsyncFunctionDef) and node.name == 'run')
        original = next(node for node in ast.walk(run) if isinstance(node, ast.Try)
                        and any(phase_assignment(stmt, 'executing-plan') for stmt in node.body))
        selected = copy.deepcopy(original)
        first = next(index for index, stmt in enumerate(selected.body) if phase_assignment(stmt, 'executing-plan'))
        selected.body = selected.body[first:]
        outer = next(node for node in run.body if isinstance(node, ast.Try) and node.finalbody
                     and any(isinstance(stmt, ast.Assign) and any(isinstance(target, ast.Subscript)
                         and isinstance(target.slice, ast.Constant) and target.slice.value == 'finished_at'
                         for target in stmt.targets) for stmt in node.finalbody))
        production_path = ast.AsyncFunctionDef(name='exercise_actual_initial_plan_path',
            args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),
            body=[selected,*copy.deepcopy(outer.finalbody)],decorator_list=[])
        names = {'load_plan','lookup','resolve','finished_native_process_exit_zero_proof',
                 'finished_native_exit_zero_proof','finished_native_failure_shutdown_proof'}
        nodes = [copy.deepcopy(node) for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in names]
        client_node = next(node for node in tree.body if isinstance(node,ast.ClassDef) and node.name == 'PlanClient')
        pure_client = ast.ClassDef(name='PlanClient',bases=[],keywords=[],decorator_list=[],body=[
            copy.deepcopy(node) for node in client_node.body if isinstance(node,ast.AsyncFunctionDef)
            and node.name in {'execute','hold','observe_final'}])
        clock = SimpleNamespace(value=0.0)
        done = threading.Event()
        events = []
        state = {'gui_exit':False}
        session_state = {'error':None,'report':None}
        error = 'ValueError: result matches.1.line_count expected 0, received 2'
        pipe = r'\\.\pipe\SYNTHETIC-INITIAL-FAILURE-NO-PROCESS'
        report = {'fixture_only':False,'error':None,'status':'RUNNING','steps':[],
            'pipe':pipe,'readiness':{'SYNTHETIC_ALREADY_LOADED_MAP':True},'session':session_state}

        def native_dto(normal):
            return {'kind':'ck3_native_headless_session','mode':'native-headless','format_version':1,
                'ok':True,'error':None,'exit_reason':'process_exit' if normal else 'stop',
                'process_exit_code':0 if normal else None,'pid':2468,'pipe':pipe,
                'started_at':'2026-10-10T00:00:00+00:00','finished_at':'2026-10-10T00:00:01+00:00',
                'shutdown':{'ok':True,'cleanup_proven':True,'tree_gone':True,'ck3_pid':2468,
                    'ck3_exit_code':0 if normal else 1,'job_active_processes_final':0,
                    'contract_errors':[],'watchdog_state_after':'absent','nonce':'a'*32,
                    'ck3_creation_date':'SYNTHETIC-NO-PROCESS',
                    'control_files_absent':{'ck3.json':True,'watchdog.json':True},
                    'final_ck3_inventory':{'tasklist_returncode':0,'tasklist_pids':[],
                        'wmi_pids':[],'native_pids':[],'processes':[]}}}

        class Stop:
            def set(self):
                events.append(('stop',state['gui_exit'],report.get('hold_finished_by_control_plan')))

        class Supervisor:
            ident = 1
            def is_alive(self):return not done.is_set()
            def join(self, _timeout):
                if not done.is_set():
                    events.append(('synthetic-managed-cleanup-before-gui',))
                    session_state['report'] = native_dto(False)
                    done.set()

        supervisor = Supervisor()
        stop = Stop()
        controls = root/'controls'
        controls.mkdir()
        failed_step = {'id':'qol-ordinary-async-day001-no-fail','tool':'ck3_query_engine_log_literals_v1',
            'args':{},'expect':{'matches.1.line_count':0}}
        initial_plan = root/'initial-plan.json'
        initial_plan.write_text(json.dumps({'steps':[failed_step,
            {'id':'NEVER-REPLAY-REMAINING-BUSINESS','tool':'NEVER-DISPATCH'}]}),encoding='utf-8')
        initial_bytes = initial_plan.read_bytes()
        args = SimpleNamespace(sdk_error_smoke_test=False,sdk_smoke_test=False,plan=initial_plan,
            frontend_mod_load_observation=False,frontend_robert_bootstrap=False,turns=1,
            hold_seconds=600,control_plan_dir=controls)

        def write():
            report['managed_session_done'] = done.is_set()
            report['managed_session_thread_finished'] = supervisor.ident is not None and not supervisor.is_alive()

        async def sleep(seconds):
            clock.value += seconds
            if report.get('phase') == 'hold' and not state['gui_exit']:
                # Pure fixture publishes a synthetic normal exit DTO and only
                # then queues the same typed failure-only lifecycle request.
                state['gui_exit'] = True
                events.append(('synthetic-normal-gui-exit',))
                session_state['report'] = native_dto(True)
                report['cleanup_ok'] = True
                done.set()
                (controls/'once-failure-finish.json').write_text(json.dumps({'steps':[{
                    'id':'only-failure-finish','kind':'finish_hold','failure_shutdown':True,
                    'expect':{'hold_finished':True,'failure_preserved':True,
                        'business_pass':False,'normal_close_qualified':False}}]}),encoding='utf-8')

        async def to_thread(call,*arguments):return call(*arguments)
        namespace = {'argparse':argparse,'copy':copy,'datetime':datetime,'timezone':timezone,
            'json':json,'Path':Path,'re':re,'traceback':traceback,
            'time':SimpleNamespace(monotonic=lambda:clock.value,time=lambda:clock.value),
            'asyncio':SimpleNamespace(sleep=sleep,to_thread=to_thread),
            'now':lambda:'2026-10-10T00:00:02+00:00','report':report,'args':args,
            'write':write,'done':done,'supervisor':supervisor,'stop':stop,'session_state':session_state}
        module = ast.fix_missing_locations(ast.Module(body=[*nodes,pure_client,production_path],type_ignores=[]))
        exec(compile(module,str(source),'exec'),namespace)
        client = namespace['PlanClient'].__new__(namespace['PlanClient'])
        client.args=args;client.report=report;client.results={};client.snapshot={}
        client.episode_identity={'bridge_pid':2468};client.managed_done=done;client.write=write
        client.control_plan_execution_depth=0;client.consumed_control_plans=set()
        calls=[]
        async def invoke(name, *_arguments, **_keywords):
            calls.append(name)
            self.assertEqual(name,'ck3_query_engine_log_literals_v1','Business must stop after the original failed step')
            return {'matches':[{'line_count':0},{'line_count':2}]}
        async def forbidden(*_arguments,**_keywords):
            raise AssertionError('No dead-native snapshot or additional business call after failure')
        client.invoke=invoke;client.call=forbidden;client.fresh=forbidden
        namespace['client']=client
        asyncio.run(namespace['exercise_actual_initial_plan_path']())
        self.assertIn('initial_plan_failure_hold',report,'Original exception must enter existing hold before managed cleanup')
        self.assertEqual(report['initial_plan_failure_hold']['seconds'],600)
        self.assertEqual(report['hold_until_utc_estimated'],600)
        self.assertLess(clock.value,1,'Actual pure failure finish must end the original hold early')
        self.assertEqual(report['error'],error)
        self.assertEqual(report['status'],'RED')
        self.assertEqual(report['steps'][0]['plan'],failed_step)
        self.assertIs(report['steps'][0]['ok'],False)
        self.assertEqual(report['steps'][0]['error'],error)
        self.assertTrue(report['steps'][0]['finished_at'])
        self.assertEqual([row['id'] for row in report['steps']],[failed_step['id'],'only-failure-finish'])
        self.assertEqual(calls,['ck3_query_engine_log_literals_v1'])
        self.assertEqual(initial_plan.read_bytes(),initial_bytes)
        self.assertIs(report['hold_finished_by_control_plan'],True)
        self.assertEqual(len(client.consumed_control_plans),1)
        self.assertTrue(report['post_failure_exit_finish_hold']['proof']['failure_preserved'])
        self.assertFalse(report['post_failure_exit_finish_hold']['proof']['business_pass'])
        self.assertFalse(report['post_failure_exit_finish_hold']['proof']['normal_close_qualified'])
        self.assertIsNone(namespace['finished_native_exit_zero_proof'](report,True,client.episode_identity))
        self.assertNotIn('post_exit_finish_hold',report)
        self.assertNotIn(('synthetic-managed-cleanup-before-gui',),events)
        self.assertTrue(all(event[1] and event[2] for event in events if event[0] == 'stop'))
        self.assertTrue(report['cleanup_ok']);self.assertTrue(report['managed_session_thread_finished'])
        self.assertEqual(args.hold_seconds,600)

    def test_actual_initial_plan_exception_preserves_RED_and_uses_original_hold_then_failure_finish(self):
        for source in options.host_source:
            with self.subTest(host=str(source)),tempfile.TemporaryDirectory(prefix='PURE_INITIAL_FAIL_NO_GAME_') as directory:
                self.exercise_source(source,Path(directory))


if __name__ == '__main__':
    unittest.main(argv=[__file__,*remaining],verbosity=2)
