"""Portable production prelaunch closure checks; no process/game/bus operations."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import ck3_mod_acceptance_allocate as allocation

class NeverLaunchedTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name);self.previous=self.root/'run';self.previous.mkdir()
        (self.previous/'controls').mkdir();self.keeper=self.root/'keeper';self.keeper.mkdir()
        self.state=self.root/'state';self.state.mkdir();self.case=self.root/'prepared.json'
        self.write(self.case,{})
        self.freeze={'run_id':'run','state_dir':str(self.state),'screen_task':'screen-a29'}
        self.write(self.previous/'frozen-argv.json',self.freeze)
        self.ready={'run_id':'run','run_dir':str(self.previous),'keeper_root':str(self.keeper),
          'prepared_case':allocation.pin(self.case),'frozen_argv':allocation.pin(self.previous/'frozen-argv.json')}
        self.write(self.previous/'ready-context.json',self.ready)
        self.report={'task_id':'screen-a29','thread_exited':True,'failure':None,'game_actions':False,
          'entry_error':"RuntimeError('screen task checkout has current tracked or untracked changes')",'last_sequence':10}
        self.write(self.keeper/'report.json',self.report)
        self.parent={'run_id':'run','keeper_actual_exit_code':1,'keeper_report':self.report}
        self.write(self.previous/'keeper-actual-parent-exit.json',self.parent)
        self.command=self.root/'RESULT.actual.json'
        self.command_value={'schema':'ck3-recorded-actual-command-v1','exit_code':0,'finished_at_utc':'actual',
          'argv':['python','entry.py','allocate','--keeper-output',str(self.keeper),'--prepared-case',str(self.case)]}
        self.bundle=self.root/'prelaunch-close.json';self.write_command(self.command_value)
        self.release={'ok':True,'task':{'task_id':'screen-a29','state':'done','resources':[],'last_sequence':11}}
        self.bus={'tasks':[self.release['task']]}
        self.inventory={'blockers':[],'process_absence_is_normal_exit_proof':False}

    def write(self,path,value):path.write_text(json.dumps(value),encoding='utf-8')
    def write_command(self,value):
        self.write(self.command,value)
        self.write(self.bundle,{'schema':'ck3-mod-acceptance-never-launched-closure-v1','run_id':'run',
          'allocator_result':allocation.pin(self.command)})
    def close(self):
        with patch.object(allocation,'runtime_process_inventory',return_value=self.inventory):
            return allocation.previous_never_launched_closure(self.previous,self.freeze,self.bundle,
                       self.keeper,self.release,self.bus)

    def test_actual_parent_and_CAS_close_without_native_or_host_read(self):
        reader=allocation.read_json
        def no_native(path):
            self.assertNotIn(Path(path).name,('native-report.json','host-started.json','host-original-process-exit.json'))
            return reader(path)
        with patch.object(allocation,'read_json',side_effect=no_native):result=self.close()
        self.assertEqual(result['mode'],'previous-shared-never-launched-checkout-failure')
        self.assertFalse(result['failure_cleanup']['native_session_started'])
        self.assertIsNone(result['failure_cleanup']['original_ck3_exit_code'])
        self.assertFalse(result['failure_cleanup']['typed_normal_exit_proven'])

    def test_any_launch_or_control_evidence_rejects(self):
        paths=[self.previous/name for name in ('launch-intent.json','launch.json','host-started.json',
          'host-original-process-exit.json','native-report.json')]
        paths.append(self.previous/'controls/queued.json')
        for path in paths:
            with self.subTest(path=path.name):
                path.write_text('evidence',encoding='utf-8')
                with self.assertRaisesRegex(ValueError,'launch/native/PID/control'):self.close()
                path.unlink()
        (self.state/'control').mkdir()
        with self.assertRaisesRegex(ValueError,'launch/native/PID/control'):self.close()

    def test_crossed_ready_keeper_wait_or_allocator_rejects(self):
        wrong=copy.deepcopy(self.ready);wrong['keeper_root']=str(self.root/'other')
        self.write(self.previous/'ready-context.json',wrong)
        with self.assertRaisesRegex(ValueError,'READY crossed'):self.close()
        self.write(self.previous/'ready-context.json',self.ready)
        wrong=copy.deepcopy(self.parent);wrong['keeper_actual_exit_code']=0
        self.write(self.previous/'keeper-actual-parent-exit.json',wrong)
        with self.assertRaisesRegex(ValueError,'keeper parent wait'):self.close()
        self.write(self.previous/'keeper-actual-parent-exit.json',self.parent)
        for changes in ({'exit_code':1},{'finished_at_utc':None},
            {'argv':['allocate','--keeper-output',str(self.root/'other'),'--prepared-case',str(self.case)]}):
            with self.subTest(changes=changes):
                self.write_command(dict(self.command_value,**changes))
                with self.assertRaises(ValueError):self.close()

    def test_unreleased_CAS_or_runtime_presence_rejects(self):
        self.release['task']['resources']=['ck3-screen:acquired']
        with self.assertRaisesRegex(ValueError,'CAS release'):self.close()
        self.release['task']['resources']=[]
        self.inventory['blockers']=[{'pid':123,'name':'ck3.exe'}]
        with self.assertRaisesRegex(ValueError,'still present'):self.close()

    def test_actual_waiting_empty_resources_CAS_release_is_closed(self):
        # R66 released its own expired claim at sequence 5048, state waiting.
        self.report['last_sequence']=5047
        self.write(self.keeper/'report.json',self.report)
        self.parent['keeper_report']=self.report
        self.write(self.previous/'keeper-actual-parent-exit.json',self.parent)
        self.release['task'].update(state='waiting',resources=[],last_sequence=5048)
        result=self.close()
        self.assertEqual(result['mode'],'previous-shared-never-launched-checkout-failure')
        self.assertFalse(result['failure_cleanup']['native_session_started'])
        self.assertIsNone(result['failure_cleanup']['original_ck3_exit_code'])
        self.release['task']['resources']=['ck3-screen:acquired']
        with self.assertRaisesRegex(ValueError,'CAS release'):self.close()

if __name__=='__main__':unittest.main(verbosity=2)
