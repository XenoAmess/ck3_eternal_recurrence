"""Offline regression for an actual failed-case resource boundary, with no process queries."""
from __future__ import annotations
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

TOOLS=Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:sys.path.insert(0,str(TOOLS))
import ck3_mod_acceptance_allocate as allocation


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


if __name__=='__main__':unittest.main()
