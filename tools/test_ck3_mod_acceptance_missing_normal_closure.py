"""Failed-host resource recovery preserves genuinely missing normal/OS receipts."""
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import ck3_mod_acceptance_allocate as allocation
import test_ck3_mod_acceptance_expired_keeper as fixture_module

class MissingNormalClosureTests(unittest.TestCase):
    write=fixture_module.ExpiredKeeperResourceClosureTests.write
    save=fixture_module.ExpiredKeeperResourceClosureTests.save
    seal_bus=fixture_module.ExpiredKeeperResourceClosureTests.seal_bus
    check=fixture_module.ExpiredKeeperResourceClosureTests.check
    def setUp(self):
        fixture_module.ExpiredKeeperResourceClosureTests.setUp(self)
        self.freeze.update(source_root=str(self.root/'repo'),cell='failed-case')
        self.freeze['argv'].extend(['--bridge-pipe','synthetic-pipe'])
        refs=self.bundle['original_evidence']
        refs['frozen_argv']=self.write(self.run/'frozen-argv.json',self.freeze)
        ready=allocation.read_json(self.run/'ready-context.json');ready['frozen_argv']=refs['frozen_argv']
        refs['ready_context']=self.write(self.run/'ready-context.json',ready)
        host=allocation.read_json(self.run/'host-started.json');host['argv']=self.freeze['argv']
        refs['host_started']=self.write(self.run/'host-started.json',host)
        exited=allocation.read_json(self.run/'host-original-process-exit.json');exited['returncode']=1
        refs['host_exit']=self.write(self.run/'host-original-process-exit.json',exited)
        self.bundle['closure_kind']='failed-host-without-normal-close-result'
        refs.pop('normal_close');(self.run/'case-output/normal-close-result.json').unlink()
        refs.pop('handover_snapshot');self.bundle.pop('keeper_final_report_missing')
        self.native=self.run/'native-report.json';self.native.write_bytes(b'synthetic native body must only be statted')
        shutdown=dict(ok=True,cleanup_proven=True,tree_gone=True,job_active_processes_final=0,contract_errors=[],
            ck3_pid=13,ck3_exit_code=1,control_files_absent={'synthetic-control':True},
            final_ck3_inventory=dict(tasklist_returncode=0,tasklist_pids=[],wmi_pids=[],native_pids=[],processes=[]))
        self.report=dict(status='RED',error='Some source-bound tool failed',finished_at='2026-10-20T01:00:00+00:00',
            managed_session_done=True,managed_session_thread_finished=True,cleanup_ok=True,
            state_dir=str(self.state),agent_source_root=self.freeze['source_root'],pipe='synthetic-pipe',
            session=dict(error=None,report=dict(pid=13,finished_at='2026-10-20T01:00:00+00:00',shutdown=shutdown)))
        self.projection=dict(schema='lyd.native-cleanup-field-projection.v1',run_id=self.run.name,machine_id=self.machine,
            observed_at_utc='2026-10-20T01:01:00+00:00',original_native_report=allocation.pin(self.native),
            original_host_exit=refs['host_exit'],projection=self.report)
        self.projection_path=self.run/'native-cleanup-projection.actual.json'
        refs['native_cleanup_projection']=self.write(self.projection_path,self.projection)
        self.entry=dict(run_id=self.run.name,host_argv=self.freeze['argv'],case_error='Case stopped after host failure',
                        normal_close_error='Original process already ended')
        refs['entry_result']=self.write(self.run/'case-output/entry-run-result.json',self.entry)
        refs['normal_close_error']=self.write(self.run/'case-output/normal-close-error-preserved.json',
            dict(error=self.entry['normal_close_error'],business_pass=False))
        refs['retained_identity']=self.write(self.run/'case-output/retained-current-process-identity.json',
            dict(pid=13,create_time=3.5,retained_synchronize_query_handle_acquired=True))
        common=['--runtime',str(self.root/'runtime.json'),'--case',self.freeze['cell'],'--prepared-case',refs['prepared_case']['path']]
        self.public=dict(machine_id=self.machine,observed_at_utc='2026-10-20T01:01:00+00:00',
            actual_original_popen_wait=True,returncode=2,pid=21,argv=['python','ck3_mod_acceptance.py','run',*common,
                '--run-context',str(self.run/'ready-context.json')])
        refs['public_wait']=self.write(self.root/'public-wait.json',self.public)
        refs['public_run_context']=refs['ready_context']
        self.allocator=dict(machine_id=self.machine,observed_at_utc='2026-10-20T01:02:00+00:00',
            actual_original_popen_wait=True,returncode=0,pid=22,argv=['python','ck3_mod_acceptance.py','allocate',*common,
                '--keeper-output',str(self.keeper)])
        refs['allocator_wait']=self.write(self.root/'allocator-wait.json',self.allocator)
        keeper=dict(task_id=self.task_id,last_sequence=7124,thread_exited=True,failure=None,entry_error=None)
        refs['keeper_report']=self.write(self.keeper/'report.json',keeper)
        refs['keeper_exit']=self.write(self.run/'keeper-actual-parent-exit.json',
            dict(run_id=self.run.name,keeper_actual_exit_code=0,keeper_report=keeper))
        self.task['state']='done';self.event['state']='done';self.event['kind']='completed';self.event.pop('retirement')
        self.seal_bus()

    def reseal_projection(self):
        self.bundle['original_evidence']['native_cleanup_projection']=self.write(self.projection_path,self.projection);self.save()

    def test_only_resources_admitted_with_missing_normal_and_os_receipts(self):
        result=self.check();proof=result['failure_cleanup']
        self.assertEqual(result['mode'],'previous-shared-failed-host-missing-normal-resource-closed')
        self.assertEqual(proof['original_host_exit_code'],1);self.assertEqual(proof['native_reported_ck3_exit_code'],1)
        self.assertIsNone(proof['original_ck3_exit_code']);self.assertIsNone(proof['retained_os_exit_receipt'])
        self.assertIsNone(proof['normal_close_result']);self.assertIsNone(proof['native_cleanup_qualified'])
        for key in ('normal_close_qualified','typed_normal_exit_proven','actual_retained_os0','business_pass','release_pass'):
            self.assertIs(proof[key],False)
        self.assertTrue(proof['original_keeper_wait_proven'])

    def test_incomplete_native_failure_or_cleanup_is_rejected(self):
        for key,bad in (('status','GREEN'),('error',None),('managed_session_done',False),('cleanup_ok',False)):
            with self.subTest(key=key):
                old=self.report[key];self.report[key]=bad;self.reseal_projection()
                with self.assertRaisesRegex(ValueError,'failure/Job cleanup'):self.check()
                self.report[key]=old

    def test_native_process_zero_does_not_match_failed_process_class(self):
        self.report['session']['report']['shutdown']['ck3_exit_code']=0;self.reseal_projection()
        with self.assertRaisesRegex(ValueError,'failed-process'):self.check()

    def test_source_projection_must_bind_original_host_and_report(self):
        self.native.write_bytes(b'changed-size')
        with self.assertRaisesRegex(ValueError,'original path/size/pin'):self.check()

    def test_missing_or_crossed_case_error_is_rejected(self):
        self.entry['normal_close_error']='another error'
        self.bundle['original_evidence']['entry_result']=self.write(self.run/'case-output/entry-run-result.json',self.entry);self.save()
        with self.assertRaisesRegex(ValueError,'case/close error'):self.check()

    def test_existing_original_close_or_retained_receipt_is_not_bypassed(self):
        for name in ('normal-close-result.json','actual-retained-handle-os-exit.json'):
            path=self.run/'case-output'/name;self.write(path,{})
            with self.assertRaisesRegex(ValueError,'replace existing'):self.check()
            path.unlink()

    def test_actual_public_failure_and_allocator_wait_are_required(self):
        self.public['returncode']=0
        self.bundle['original_evidence']['public_wait']=self.write(self.root/'public-wait.json',self.public);self.save()
        with self.assertRaisesRegex(ValueError,'public completion'):self.check()

    def test_keeper_report_must_match_actual_parent_wait(self):
        parent=allocation.read_json(self.run/'keeper-actual-parent-exit.json');parent['keeper_actual_exit_code']=1
        self.bundle['original_evidence']['keeper_exit']=self.write(self.run/'keeper-actual-parent-exit.json',parent);self.save()
        with self.assertRaisesRegex(ValueError,'keeper wait/thread'):self.check()

    def test_active_original_process_or_controller_is_rejected(self):
        self.live={13}
        with self.assertRaisesRegex(ValueError,'still present'):self.check()
        self.live=set();self.blockers=[{'pid':999}]
        with self.assertRaisesRegex(ValueError,'still running'):self.check()

    def test_owned_recorder_and_stale_controls_are_rejected(self):
        recorder=SimpleNamespace(info={'pid':99,'name':'ffmpeg.exe'},pid=99,
            cmdline=lambda:['ffmpeg.exe',str(self.keeper.parent/'raw/recording.mkv')])
        self.psutil.process_iter=lambda fields:[recorder]
        with self.assertRaisesRegex(ValueError,'recorder still running'):self.check()
        self.psutil.process_iter=lambda fields:[];self.write(self.state/'control/unsafe-cleanup.json',{})
        with self.assertRaisesRegex(ValueError,'controls remain'):self.check()

    def test_actual_cas_and_current_bus_must_remain_closed(self):
        self.bus['tasks'].append({'task_id':'other','resources':['ck3-screen:acquired']})
        with self.assertRaisesRegex(ValueError,'current screen task'):self.check()

    def test_nonmatching_closure_kind_remains_strict(self):
        self.bundle['closure_kind']='unknown-failure';self.save()
        with self.assertRaises((KeyError,FileNotFoundError,ValueError)):self.check()

if __name__=='__main__':unittest.main(verbosity=2)
