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

    def test_exact_legacy_keeper_uses_only_original_flags_and_bus_binding(self):
        with tempfile.TemporaryDirectory() as temporary:
            keeper=Path(temporary)/'screen_keeper.py';keeper.write_bytes(b'known frozen legacy')
            with patch.object(allocation,'LEGACY_KEEPER_SHA',allocation.pin(keeper)['sha256']):
                args=('python',keeper,Path('lease'),Path('new-keeper'),'task-a31',5055,
                      allocation.LEGACY_KEEPER_BUS,allocation.LEGACY_KEEPER_BUS_SHA)
                argv=allocation.keeper_command(*args)
                self.assertEqual(argv[5:],['--repo','lease','--root',str(Path('new-keeper').resolve()),
                                          '--task','task-a31','--sequence','5055'])
                self.assertNotIn('--bus-dir',argv)
                with self.assertRaisesRegex(ValueError,'original installed bus'):
                    allocation.keeper_command(*args[:-2],Path('another-bus'),args[-1])
                with self.assertRaisesRegex(ValueError,'original installed bus'):
                    allocation.keeper_command(*args[:-1],'0'*64)

    def test_legacy_argparse_failure_retains_actual_wait2_not_normal_exit(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);run=root/'run';run.mkdir();(run/'controls').mkdir()
            keeper=root/'keeper';state=root/'state';state.mkdir();prepared=root/'prepared.json'
            source=root/'screen_keeper.py';source.write_bytes(b'x'*1600)
            def write(path,value):path.write_text(json.dumps(value),encoding='utf-8')
            write(prepared,{})
            legacy=allocation.pin(source)
            freeze={'run_id':'run','state_dir':str(state),'screen_task':'task-a31',
                    'files':{str(source.resolve()):{k:legacy[k] for k in ('bytes','sha256')}}}
            write(run/'frozen-argv.json',freeze)
            write(run/'allocated-context.json',{'run_id':'run','run_dir':str(run),'keeper_root':str(keeper),
                                               'prepared_case':allocation.pin(prepared)})
            extras=['--bus-dir',str(root/'bus'),'--bus-cli',str(root/'lease/tools/codex_task_bus.py'),
                    '--bus-cli-sha256','A'*64]
            write(run/'keeper-process.json',{'pid':77,'create_time':1.5,
                'argv':['python','-B','-X','utf8',str(source),'--repo',str(root/'lease'),
                        '--root',str(keeper),'--task','task-a31','--sequence','5055',*extras]})
            (run/'keeper-stderr.log').write_text('usage: original legacy flags\n'
                'screen_keeper.py: error: unrecognized arguments: '+' '.join(extras)+'\n',encoding='utf-8')
            parent=run/'keeper-pre-ready-parent-exit.json'
            wait={'schema':'ck3-keeper-pre-ready-original-parent-exit-v1','run_id':'run','pid':77,
                  'actual_original_popen_wait':True,'actual_poll_exit_code':2,'keeper_actual_exit_code':2,
                  'ready_absent':True,'game_started':False,'business_pass':False}
            write(parent,wait)
            stdout=root/'stdout.log'
            write(stdout,{'status':'BLOCKED','error':'Original keeper failed before READY; preserve actual stderr'})
            operation=root/'operation.json'
            write(operation,{'schema':'xar-root-exact-public-command-v1','actor':'/root',
                'argv':['entry.py','allocate','--keeper-output',str(keeper),'--prepared-case',str(prepared)]})
            command=root/'exit.json'
            write(command,{'schema':'xar-root-exact-public-command-exit-v1','actor':'/root','returncode':2,
                'finished_utc':'actual','operation':allocation.pin(operation),'stdout':allocation.pin(stdout)})
            write(run/'screen-registration.json',{'ok':True,'task':{'task_id':'task-a31','last_sequence':5055}})
            bundle=root/'pre-ready.json'
            def seal():
                write(bundle,{'schema':'ck3-mod-acceptance-pre-ready-closure-v1','run_id':'run',
                    'allocator_result':allocation.pin(command),'allocator_stdout':allocation.pin(stdout),
                    'keeper_parent_wait':allocation.pin(parent),
                    **{key:allocation.pin(run/name) for key,name in {'allocated_context':'allocated-context.json',
                      'frozen_argv':'frozen-argv.json','keeper_process':'keeper-process.json',
                      'keeper_stderr':'keeper-stderr.log'}.items()}})
            seal()
            task={'task_id':'task-a31','last_sequence':5056,'state':'done','resources':[]}
            with (patch.object(allocation,'LEGACY_KEEPER_SHA',legacy['sha256']),
                  patch.dict(sys.modules,{'psutil':SimpleNamespace(pid_exists=Mock(return_value=False))}),
                  patch.object(allocation,'runtime_process_inventory',return_value={'blockers':[]})):
                def close():return allocation.previous_pre_ready_closure(run,freeze,bundle,keeper,
                                                                         {'ok':True,'task':task},{'tasks':[task]})
                proof=close()['failure_cleanup']
                self.assertEqual(proof['original_keeper_exit_code'],2)
                self.assertTrue(proof['original_keeper_wait_proven'])
                self.assertEqual(proof['original_evidence']['keeper_parent_wait'],allocation.pin(parent))
                self.assertFalse(proof['typed_normal_exit_proven'])
                self.assertFalse(proof['business_pass'])
                self.assertIsNone(proof['original_ck3_exit_code'])
                for field,value in [('pid',78),('keeper_actual_exit_code',0),('actual_original_popen_wait',False)]:
                    with self.subTest(field=field):
                        write(parent,{**wait,field:value});seal()
                        with self.assertRaisesRegex(ValueError,'original keeper argparse wait2'):close()
                write(parent,wait);seal()
                (run/'host-started.json').write_text('{}',encoding='utf-8')
                with self.assertRaisesRegex(ValueError,'READY/launch/native'):close()

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




class RecorderPreReadyClosureTests(unittest.TestCase):
    """Authored failure fixtures exercise the real publisher, creator and reducer."""
    def setUp(self) -> None:
        import subprocess
        import hashlib
        import os
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root/'repo'
        (self.repo/'tools').mkdir(parents=True)
        source_root = Path(__file__).resolve().parent.parent
        for name in ('ck3_mod_acceptance_keeper.py','ck3_mod_acceptance_recorder.py'):
            raw = subprocess.run(['git','show','HEAD:tools/'+name],cwd=source_root,
                check=True,capture_output=True).stdout
            (self.repo/'tools'/name).write_bytes(raw)
        def git(*args: str) -> str:
            return subprocess.run(['git','-C',str(self.repo),*args],check=True,
                capture_output=True,text=True).stdout.strip()
        git('init','-q')
        git('add','tools')
        git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','Fixture original sources')
        self.commit = git('rev-parse','HEAD')
        self.live = self.root/'run';self.live.mkdir();(self.live/'controls').mkdir()
        self.keeper = self.root/'keeper';self.keeper.mkdir()
        self.state = self.root/'state';self.state.mkdir()
        self.prepared = self.root/'prepared.json';self.write(self.prepared,{})
        self.task = 'fixture-recorder-task'
        self.machine = 'fixture-machine'
        self.config = self.root/'recording.json'
        self.grant = self.root/'grant.json'
        self.write(self.grant,{'machine_id':self.machine,'approved_root':str(self.root),
            'this_write_peak_bytes':2815242240,'raw_subcap_bytes':67108864})
        dummy=self.root/'dummy';dummy.write_bytes(b'fixture binary; never executed')
        job=self.repo/'promo/ck3_native_war_ai/integration/recorder_job.py'
        job.parent.mkdir(parents=True);job.write_bytes(b'fixture job; never executed')
        self.write(self.config,{'schema':'ck3-mod-acceptance-recording-config-v2',
            'machine_id':self.machine,'capture_root':str(self.root/'captures'),
            'ffmpeg':allocation.pin(dummy),'ffprobe':allocation.pin(dummy),'recorder_job':allocation.pin(job),
            'storage_reservation':allocation.pin(self.grant),'reservation_task':'raw_2x32MiB',
            'max_seconds':25,'peak_bytes':33554432,'max_takes':2,'total_seconds':50,
            'total_raw_bytes':67108864,'required_size':[2560,1440]})
        manifest=self.root/'manifest.json'
        self.write(manifest,{'machine_id':self.machine,'source_commit':self.commit})
        files={}
        for p in (self.repo/'tools/ck3_mod_acceptance_keeper.py',
                  self.repo/'tools/ck3_mod_acceptance_recorder.py',self.config):
            ref=allocation.pin(p);files[str(p.resolve())]={'bytes':ref['bytes'],'sha256':ref['sha256']}
        self.freeze={'run_id':'run','screen_task':self.task,'state_dir':str(self.state),
            'source_root':str(self.repo),'identity_allocation':{'machine_id':self.machine},
            'runtime_manifest':allocation.pin(manifest),'files':files}
        self.write(self.live/'frozen-argv.json',self.freeze)
        self.write(self.live/'allocated-context.json',{'run_id':'run','run_dir':str(self.live),
            'keeper_root':str(self.keeper),'prepared_case':allocation.pin(self.prepared)})
        keeper_path=self.repo/'tools/ck3_mod_acceptance_keeper.py'
        keeper_argv=[sys.executable,'-B','-X','utf8',str(keeper_path),'--repo',str(self.repo),
            '--root',str(self.keeper),'--task',self.task,'--sequence','7',
            '--recorder-config',str(self.config),'--recorder-config-sha256',allocation.pin(self.config)['sha256'],
            '--recorder-service-sha256',allocation.pin(self.repo/'tools/ck3_mod_acceptance_recorder.py')['sha256']]
        # This is a genuine failed child and the existing actual wait publisher.
        child=subprocess.Popen([sys.executable,'-B','-c',
            'import sys;sys.stdin.buffer.read();raise SystemExit(1)'],stdin=subprocess.PIPE)
        def close_child() -> None:
            if child.stdin is not None and not child.stdin.closed:child.stdin.close()
            if child.poll() is None:child.kill()
            child.wait()
        self.addCleanup(close_child)
        import psutil
        birth=psutil.Process(child.pid).create_time()
        self.write(self.live/'keeper-process.json',{'pid':child.pid,'create_time':birth,'argv':keeper_argv})
        if child.stdin is None:raise RuntimeError('Fixture child handshake pipe missing')
        child.stdin.close()
        with self.assertRaisesRegex(ValueError,'Original keeper failed before READY'):
            allocation.wait_for_keeper_ready(child,self.keeper,self.live,__import__('time').monotonic(),io.BytesIO(),io.BytesIO())
        self.assertEqual(child.returncode,1)
        self.report={'schema':'xar.promo.screen-lease-keeper/v1','task_id':self.task,'last_sequence':7,
            'failure':None,'thread_exited':False,'journal':str(self.keeper/'journal.jsonl'),
            'at_utc':'2026-10-23T00:00:00+00:00',
            'entry_error':"ValueError('Segmented recorder requires the existing scene and raw ceilings')",
            'checkout_head':self.commit,'screen_released':False,'game_actions':False}
        self.write(self.keeper/'report.json',self.report)
        self.write(self.live/'keeper-stdout.log',self.report)
        (self.live/'keeper-stderr.log').write_bytes(b'')
        self.write(self.keeper/'inputs.json',{'schema':'ck3-mod-acceptance-keeper-inputs-v1',
            'repo':str(self.repo),'checkout_head':self.commit,'task_id':self.task,
            'initial_sequence':7,'screen_acquired_by_this_tool':False})
        self.write(self.live/'screen-registration.json',{'ok':True,
            'task':{'task_id':self.task,'last_sequence':7}})
        self.started=self.root/'STARTED.json';self.exited=self.root/'EXIT.json'
        self.stdout=self.root/'stdout.json';self.stderr=self.root/'stderr.txt'
        self.producer=self.root/'producer.py'
        public=self.repo/'tools/ck3_mod_acceptance.py'
        public.write_text("import json;print(json.dumps({'status':'BLOCKED','error':"
            "'Original keeper failed before READY; preserve actual stderr'}));raise SystemExit(2)",encoding='utf-8')
        argv=[sys.executable,str(public),'allocate','--keeper-output',str(self.keeper),
              '--prepared-case',str(self.prepared)]
        # The exact shared recorded-public producer contract is executed, not ACKed.
        self.producer.write_text(
            "import subprocess,json,time\nfrom pathlib import Path\nfrom datetime import datetime,timezone\n"
            f"argv={argv!r}\nREPO=Path({str(self.repo)!r})\nmode='allocate'\n"
            f"stdout=Path({str(self.stdout)!r});stderr=Path({str(self.stderr)!r})\n"
            f"start=Path({str(self.started)!r});exitp=Path({str(self.exited)!r})\n"
            "t=time.monotonic_ns()\nwith stdout.open('wb') as out,stderr.open('wb') as err:\n"
            " child=subprocess.Popen(argv,env=env,cwd=REPO,stdout=out,stderr=err)\n"
            " v={'schema':'ck3-recorded-actual-command-v1','machine_id':MACHINE,'argv':argv,'shell':False,"
            "'pid':child.pid,'started_at_utc':datetime.now(timezone.utc).isoformat(),"
            "'started_monotonic_ns':str(t),'original_wait_pending':True}\n"
            " if mode=='allocate':v.update(custody_deadline_monotonic_ns=str(t+6000*1000000000),"
            "root_quit_deadline_monotonic_ns=str(t+5400*1000000000))\n"
            " with start.open('x',encoding='utf-8') as h:json.dump(v,h)\n"
            " print(json.dumps(v),flush=True)\n code=child.wait()\n"
            " v.update(original_wait_pending=False,actual_original_popen_wait=True,exit_code=code,"
            "finished_at_utc=datetime.now(timezone.utc).isoformat(),finished_monotonic_ns=str(time.monotonic_ns()))\n"
            " with exitp.open('x',encoding='utf-8') as h:json.dump(v,h)\n"
            " print(json.dumps({'operation':mode,'original_wait':code,'receipt':str(exitp)}),flush=True)\n"
            .replace("'machine_id':MACHINE","'machine_id':"+repr(self.machine))
            .replace("t=time.monotonic_ns()","env=None\nt=time.monotonic_ns()"),encoding='utf-8',newline='\n')
        # Substitute the machine literal, as the actual Root producer does.
        producer=self.producer.read_text(encoding='utf-8').replace("'machine_id':MACHINE","'machine_id':"+repr(self.machine))
        self.producer.write_text(producer,encoding='utf-8',newline='\n')
        subprocess.run([sys.executable,'-B',str(self.producer)],check=True,capture_output=True)
        self.close=self.root/'closure.json'
        task={'task_id':self.task,'last_sequence':8,'state':'done','resources':[]}
        self.release={'ok':True,'task':task}
        self.bus={'tasks':[task]}
        self.seal()

    @staticmethod
    def write(path: Path, value: object) -> None:
        path.write_text(json.dumps(value),encoding='utf-8',newline='\n')

    def seal(self) -> None:
        bundle=allocation.create_recorder_pre_ready_closure(self.live,self.keeper,
            allocator_started=allocation.pin(self.started),allocator_result=allocation.pin(self.exited),
            allocator_producer=allocation.pin(self.producer),allocator_stdout=allocation.pin(self.stdout),
            allocator_stderr=allocation.pin(self.stderr))
        self.write(self.close,json.loads(json.dumps(bundle)))

    def consume(self) -> object:
        return allocation.previous_pre_ready_closure(self.live,self.freeze,self.close,self.keeper,self.release,self.bus)

    def test_actual_wait_publisher_creator_consumer_and_json_roundtrip(self) -> None:
        result=self.consume()
        self.assertIsInstance(result,dict)
        if not isinstance(result,dict):self.fail('Expected closure object')
        self.assertEqual(result['mode'],'previous-shared-recorder-pre-ready-failure')
        proof=result['failure_cleanup']
        self.assertEqual(proof['original_allocator_exit_code'],2)
        self.assertEqual(proof['original_keeper_exit_code'],1)
        self.assertFalse(proof['original_keeper_thread_exited'])
        self.assertFalse(proof['typed_normal_exit_proven'])
        self.assertFalse(proof['business_pass'])
        self.assertEqual(json.loads(json.dumps(result)),result)
        # The source path may now contain the fix; original Git bytes remain authoritative.
        with (self.repo/'tools/ck3_mod_acceptance_recorder.py').open('ab') as stream:stream.write(b'\n# later fix\n')
        self.consume()

    def test_wrong_types_missing_fields_and_unknown_error_reject(self) -> None:
        parent_path=self.live/'keeper-pre-ready-parent-exit.json'
        parent=allocation.read_json(parent_path)
        for field,value in (('pid',True),('pid',1.0),('actual_poll_exit_code',True),
                ('keeper_actual_exit_code',1.0),('keeper_actual_exit_code',0),('ready_absent',None)):
            with self.subTest(field=field,value=value):
                self.write(parent_path,{**parent,field:value});self.seal()
                with self.assertRaises(ValueError):self.consume()
        self.write(parent_path,parent)
        for field in ('failure','entry_error','thread_exited'):
            report=dict(self.report);report.pop(field)
            self.write(self.keeper/'report.json',report);self.write(self.live/'keeper-stdout.log',report);self.seal()
            with self.assertRaises(ValueError):self.consume()
        report={**self.report,'entry_error':"ValueError('arbitrary failure')"}
        self.write(self.keeper/'report.json',report);self.write(self.live/'keeper-stdout.log',report);self.seal()
        with self.assertRaises(ValueError):self.consume()

    def test_source_drift_wait_tampering_and_live_artifacts_reject(self) -> None:
        original=self.exited.read_bytes()
        waited=allocation.read_json(self.exited)
        self.write(self.exited,{**waited,'pid':True});self.seal()
        with self.assertRaises(ValueError):self.consume()
        self.exited.write_bytes(original);self.seal()
        closed=allocation.read_json(self.close)
        self.write(self.close,{**closed,'failure_kind':True})
        with self.assertRaises(ValueError):self.consume()
        self.seal()
        manifest=self.root/'manifest.json';old_manifest=manifest.read_bytes()
        self.write(manifest,{'machine_id':self.machine,'source_commit':'0'*40})
        self.freeze['runtime_manifest']=allocation.pin(manifest)
        self.write(self.live/'frozen-argv.json',self.freeze);self.seal()
        with self.assertRaisesRegex(ValueError,'source commit'):self.consume()
        manifest.write_bytes(old_manifest)
        self.freeze['runtime_manifest']=allocation.pin(manifest)
        self.write(self.live/'frozen-argv.json',self.freeze);self.seal()
        for path in (self.keeper/'ready.json',self.keeper/'journal.jsonl',self.live/'host-started.json',
                     self.live/'native-report.json'):
            path.write_text('{}',encoding='utf-8')
            with self.assertRaises(ValueError):self.consume()
            path.unlink()
        released=self.release['task']
        if not isinstance(released,dict):self.fail('Expected resource task object')
        released['resources']=['ck3-screen:acquired']
        with self.assertRaises(ValueError):self.consume()

    def test_keeper_generation_and_writer_lock_refresh_are_required(self) -> None:
        import ck3_live_run_id as ids
        from contextlib import contextmanager
        from collections.abc import Iterator
        from unittest.mock import patch
        parent=allocation.read_json(self.live/'keeper-process.json')
        provider=SimpleNamespace(create_time=lambda:parent['create_time'])
        with patch('psutil.Process',return_value=provider):
            with self.assertRaisesRegex(ValueError,'generation still present'):self.consume()
        result=self.consume()
        called=[]
        @contextmanager
        def locked(path: Path) -> Iterator[None]:
            called.append('locked')
            yield
        binding={'admission_root':str(self.root/'admissions')}
        selection=SimpleNamespace(prepared_path=self.prepared,
            runtime_path=self.root/'runtime.json',manifest_path=self.root/'manifest',
            state_dir=self.state,runtime={'allocation':{'lease_repo':str(self.repo),
            'task_bus':{'path':str(self.root/'bus/bin/codex_task_bus.py'),'sha256':'a'*64}}})
        args=SimpleNamespace(previous_live=self.live,previous_keeper=self.keeper,
                             previous_failure_close=self.close,previous_release=self.root/'release')
        def changed(*values: object) -> object:
            self.assertEqual(called,['locked'])
            return {'tasks':[{'task_id':self.task,'last_sequence':8,'state':'done',
                             'resources':['ck3-screen:acquired']}]}
        with patch.object(ids,'_exclusive_file_lock',locked), \
                patch.object(allocation,'current_screen_absent',side_effect=changed), \
                patch.object(allocation,'read_failed_runtime_release',return_value=self.release):
            with self.assertRaisesRegex(ValueError,'CAS release/current no-owner'):
                allocation.claim_machine_admission(binding,selection,args,result)
        self.assertFalse((self.root/'admissions/000001').exists())

if __name__=='__main__':unittest.main(verbosity=2)
