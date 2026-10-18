"""Focused regression for an interrupted, never-launched allocation."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from ck3_mod_acceptance_allocate import wait_for_allocated_keeper
import ck3_mod_acceptance_allocate as allocation
import json


class UnusedIdle(unittest.TestCase):
    def test_modern_idle_closure_actual_wrapper_shape(self):
        # Fully synthetic files, using the observed R0015 split-Popen schema.
        with tempfile.TemporaryDirectory(prefix='modern-idle-close-') as temporary:
            root=Path(temporary);live=root/'R0015';keeper=root/'keeper';state=root/'case/state'
            for path in (live,keeper,state):path.mkdir(parents=True)
            def write(path,value):
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_text(json.dumps(value),encoding='utf-8')
                return allocation.pin(path)
            freeze={'run_id':live.name,'screen_task':'task-test','state_dir':str(state),
                    'argv':['python','host.py'],'identity_allocation':{'machine_id':'machine-test'}}
            frozen=write(live/'frozen-argv.json',freeze)
            prepared=write(root/'common/prepared-case.json',{})
            context={'run_id':live.name,'run_dir':str(live),'keeper_root':str(keeper),
                     'prepared_case':prepared,'frozen_argv':frozen}
            refs={'frozen_argv_pin':frozen,'prepared_case_pin':prepared,
                  'ready_context_pin':write(live/'ready-context.json',context),
                  'allocated_context_pin':write(live/'allocated-context.json',context)}
            kr={'at_utc':'2026-10-18T09:58:27+00:00','lease':{'task_id':'task-test'}}
            report={'task_id':'task-test','thread_exited':True,'failure':None,'game_actions':False,
                    'last_sequence':20,'at_utc':'2026-10-18T10:08:28+00:00'}
            refs['keeper_report_pin']=write(keeper/'report.json',report)
            refs['keeper_actual_parent_exit_pin']=write(live/'keeper-actual-parent-exit.json',{
                'run_id':live.name,'keeper_actual_exit_code':0,'keeper_report':report})
            refs['keeper_ready_pin']=write(keeper/'ready.json',kr)
            ledger=state.parent/'single-use-ledger'
            refs['single_use_intent_pin']=write(ledger/'allocation-intent.json',{
                'status':'CONSUMED_ALLOCATION_INTENT_NOT_RUN','prepared_case':prepared})
            refs['single_use_allocated_pin']=write(ledger/'allocated.json',{
                'status':'ACTUAL_ALLOCATED_KEEPER_READY_NOT_RUN','live':str(live),'task':'task-test',
                'keeper_root':str(keeper),'prepared_case':prepared['path'],
                'actual_host_argv':str(live/'frozen-argv.json'),'keeper_ready':kr})
            idle={'utc':'2026-10-18T10:08:27+00:00','reason':'NEVER_LAUNCHED_ALLOCATION_IDLE_TIMEOUT',
                  'idle_seconds':600,'game_started':False,'native_session_started':False,
                  'normal_close_qualified':False,'business_pass':False}
            refs['idle_timeout_pin']=write(live/'allocation-unused-idle-timeout.json',idle)
            (keeper/'STOP').write_text('Unused allocation idle deadline; no game/native/normal credit.\n')
            refs['keeper_stop_pin']=allocation.pin(keeper/'STOP')
            for mode,code,pid in (('run',2,41),('allocate',0,42)):
                operation=root/'common/operations'/mode
                argv=['python','entry.py','--runtime',str(root/'runtime.json'),'--prepared-case',prepared['path']]
                argv+=['--run-context',str(live/'ready-context.json')] if mode=='run' else ['--keeper-output',str(keeper)]
                argv.append(mode);key='public_'+mode
                refs[key+'_intent_pin']=write(operation/'intent.json',{
                    'machine_id':'machine-test','stage':mode,'at_utc':'start','argv':argv})
                refs[key+'_process_pin']=write(operation/'original-process.json',{
                    'machine_id':'machine-test','pid':pid,'create_time':1000,'argv':argv})
                refs[key+'_exit_pin']=write(operation/'original-exit.json',{
                    'machine_id':'machine-test','pid':pid,'actual_original_popen_wait':True,
                    'returncode':code,'completed_at_utc':'end'})
            operation=root/'common/operations/run'
            refs['public_run_stdout_pin']=write(operation/'stdout.log',{
                'run_id':live.name,'host_argv':freeze['argv'],'runtime_status':'LAUNCH_FAILED',
                'business_acceptance':'NOT_ASSESSED','launcher_exit_code':2})
            refs['public_run_stderr_pin']=write(operation/'stderr.log',{
                'status':'BLOCKED','error':"ValueError('Original keeper has stopped or requested STOP')",'business_pass':False})
            release={'ok':True,'schema':'codex.task_bus.v1','task':{
                'task_id':'task-test','state':'done','resources':[],'last_sequence':21}}
            refs['release_result_pin']=write(live/'root-screen-release-a01.json',release)
            bundle={'schema':'ck3-public-cell-pre-consumption-close-v1','status':'CLOSED_RESOURCE_ONLY',
                'machine_id':'machine-test','run_id':live.name,'unused_reason':'NEVER_LAUNCHED_ALLOCATION_IDLE_TIMEOUT',
                'allocation_consumed':False,'native_session_started':False,'host_started':False,'game_started':False,
                'normal_close_qualified':False,'business_pass':False,'retained_actual_OS0':None,
                'original_process_exit_pins':{},**refs}
            close=root/'closure.json';write(close,bundle)
            def check():
                with patch.object(allocation,'runtime_process_inventory',return_value={'blockers':[]}):
                    return allocation.previous_allocated_unused_closure(live,freeze,close,keeper,release,{'tasks':[release['task']]})
            result=check()['failure_cleanup']
            self.assertFalse(result['native_session_started']);self.assertFalse(result['business_pass'])
            self.assertIsNone(result['original_ck3_exit_code'])
            idle['idle_seconds']=599
            bundle['idle_timeout_pin']=write(live/'allocation-unused-idle-timeout.json',idle);write(close,bundle)
            with self.assertRaisesRegex(ValueError,'idle STOP identity'):check()
            idle['idle_seconds']=600
            bundle['idle_timeout_pin']=write(live/'allocation-unused-idle-timeout.json',idle);write(close,bundle)
            (live/'host-started.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'actual launch/native/control'):check()

    def test_expired_unused_stops_but_existing_launch_keeps_original_wait(self):
        with tempfile.TemporaryDirectory(prefix='unused-idle-') as temporary:
            root=Path(temporary);live=root/'unused';keeper=root/'keeper'
            live.mkdir();keeper.mkdir()
            child=Mock();child.poll.return_value=None;child.wait.return_value=0
            with patch('ck3_mod_acceptance_allocate.time.monotonic',side_effect=[0,601]), \
                 patch('psutil.process_iter',return_value=[]):
                self.assertEqual(wait_for_allocated_keeper(child,live,keeper),0)
            child.wait.assert_called_once_with()
            self.assertTrue((keeper/'stop.request').is_file())
            self.assertTrue((live/'allocation-unused-idle-timeout.json').is_file())
            launched=root/'launched';launched.mkdir()
            (launched/'launch-intent.json').touch()
            child=Mock();child.poll.return_value=None;child.wait.return_value=0
            with patch('ck3_mod_acceptance_allocate.time.monotonic',return_value=0):
                self.assertEqual(wait_for_allocated_keeper(child,launched,root/'unmodified-keeper'),0)
            child.wait.assert_called_once_with()
            self.assertFalse((root/'unmodified-keeper').exists())
            self.assertFalse((launched/'allocation-unused-idle-timeout.json').exists())


if __name__=='__main__':unittest.main()
