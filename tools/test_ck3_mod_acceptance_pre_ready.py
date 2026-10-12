"""Production pre-READY failure/explicit bus seams, no runtime side effects."""
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import ck3_mod_acceptance_allocate as allocation


class PreReadyFailureTests(unittest.TestCase):
    def test_pre_ready_terminal2_release_preserves_unknown_wait_and_rejects_live_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);run=root/'run';run.mkdir();(run/'controls').mkdir()
            keeper=root/'keeper';state=root/'state';state.mkdir();prepared=root/'prepared.json'
            def write(path,value):path.write_text(json.dumps(value),encoding='utf-8')
            write(prepared,{})
            freeze={'run_id':'run','state_dir':str(state),'screen_task':'task-a30'}
            write(run/'frozen-argv.json',freeze)
            write(run/'allocated-context.json',{'run_id':'run','run_dir':str(run),'keeper_root':str(keeper),
                  'prepared_case':allocation.pin(prepared)})
            write(run/'keeper-process.json',{'pid':13184,'create_time':1.5,
                  'argv':['keeper.py','--root',str(keeper),'--task','task-a30','--sequence','5053']})
            (run/'keeper-stderr.log').write_text('RuntimeError: bus source or installed CLI is missing\n',encoding='utf-8')
            stdout=root/'stdout.log'
            write(stdout,{'status':'BLOCKED','error':'Original keeper failed before READY; preserve actual stderr'})
            command=root/'RESULT.actual.json'
            write(command,{'schema':'ck3-recorded-actual-command-v1','exit_code':2,'finished_at_utc':'actual',
                'argv':['entry.py','allocate','--keeper-output',str(keeper),'--prepared-case',str(prepared)],
                'stdout':allocation.pin(stdout)})
            write(run/'screen-registration.json',{'ok':True,'task':{'task_id':'task-a30','last_sequence':5053}})
            bundle=root/'pre-ready.json'
            write(bundle,{'schema':'ck3-mod-acceptance-pre-ready-closure-v1','run_id':'run',
                'allocator_result':allocation.pin(command),'allocator_stdout':allocation.pin(stdout),
                **{key:allocation.pin(run/name) for key,name in {'allocated_context':'allocated-context.json',
                    'frozen_argv':'frozen-argv.json','keeper_process':'keeper-process.json',
                    'keeper_stderr':'keeper-stderr.log'}.items()}})
            task={'task_id':'task-a30','last_sequence':5054,'state':'waiting','resources':[]}
            release={'ok':True,'task':task};bus={'tasks':[task]}
            provider=SimpleNamespace(pid_exists=Mock(return_value=False))
            with (patch.dict(sys.modules,{'psutil':provider}),
                  patch.object(allocation,'runtime_process_inventory',return_value={'blockers':[]})):
                def close():return allocation.previous_pre_ready_closure(run,freeze,bundle,keeper,release,bus)
                proof=close()['failure_cleanup']
                self.assertIsNone(proof['original_keeper_exit_code'])
                self.assertFalse(proof['original_keeper_wait_proven'])
                self.assertFalse(proof['native_session_started'])
                self.assertIsNone(proof['original_ck3_exit_code'])
                provider.pid_exists.return_value=True
                with self.assertRaisesRegex(ValueError,'keeper PID still present'):close()
                provider.pid_exists.return_value=False
                task['resources']=['ck3-screen:acquired']
                with self.assertRaisesRegex(ValueError,'CAS release'):close()
                task['resources']=[]
                keeper.mkdir()
                with self.assertRaisesRegex(ValueError,'READY/launch/native'):close()
                keeper.rmdir()
                (run/'host-started.json').write_text('{}',encoding='utf-8')
                with self.assertRaisesRegex(ValueError,'READY/launch/native'):close()

    def test_keeper_bus_arguments_reach_existing_keeper_parser(self):
        # Use the repository keeper parser, which already provides these flags.
        path=Path(__file__).with_name('ck3_mod_acceptance_keeper.py')
        spec=importlib.util.spec_from_file_location('keeper_parser_seam',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        lease=Path('synthetic/lease');bus=Path('actual/installed-bus')
        argv=allocation.keeper_command('python',path,lease,Path('new-keeper'),'task-a31',5055,bus,'a'*64)
        with patch.object(module,'run_keeper',return_value=0) as run:
            self.assertEqual(module.main(argv[argv.index('--repo'):]),0)
        args=run.call_args.args[0]
        self.assertEqual(args.bus_dir,bus)
        self.assertEqual(args.bus_cli,lease/'tools/codex_task_bus.py')
        self.assertEqual(args.bus_cli_sha256,'A'*64)

    def test_future_pre_ready_exit_retains_original_wait_before_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            run=Path(temporary)/'new-run';run.mkdir();keeper=Path(temporary)/'never-created'
            child=SimpleNamespace(pid=77,poll=Mock(return_value=1),wait=Mock(return_value=1))
            stdout=io.BytesIO();stderr=io.BytesIO()
            with self.assertRaisesRegex(ValueError,'Original keeper failed before READY'):
                allocation.wait_for_keeper_ready(child,keeper,run,0,stdout,stderr)
            child.wait.assert_called_once_with()
            proof=allocation.read_json(run/'keeper-pre-ready-parent-exit.json')
            self.assertEqual(proof['actual_poll_exit_code'],1)
            self.assertEqual(proof['keeper_actual_exit_code'],1)
            self.assertTrue(proof['actual_original_popen_wait'])
            self.assertTrue(proof['ready_absent'])
            self.assertFalse(proof['game_started'])
            self.assertTrue(stdout.closed and stderr.closed)


if __name__=='__main__':unittest.main(verbosity=2)
