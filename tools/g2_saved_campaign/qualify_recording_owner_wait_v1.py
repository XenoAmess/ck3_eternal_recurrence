"""RAM cases and one owned Python Job fixture; no Game/OBS/Task or scratch."""
from pathlib import Path
import ctypes as C
import hashlib
import json
import os
import subprocess
import sys
import time
import types
import unittest
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parents[1])]
import project_recording_owner_wait_v1 as new

N=Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep')
T=N/'robert30-v20261019-campaign01/runtime'
T4=T.with_name('runtime-a04')
MACHINE='xenoamess-full-tower-eb9d2c1186'
BASE=Path(getattr(sys,'_base_executable',sys.executable)).resolve()


def functions(debug=False):
    env={'Path':Path,'json':json,'SPEC':{'machine_id':MACHINE},
         'require':lambda ok,why:None if ok else (_ for _ in ()).throw(ValueError(why)),
         'read':lambda p:json.loads(p.read_bytes())}
    source=new.RUNTIME
    if debug:
        source=source.replace('    k.GetExitCodeProcess.argtypes=',
            "    print(json.dumps({'phase':'worker_wait_done'}),flush=True)\n    k.GetExitCodeProcess.argtypes=",1)
    exec(compile(source,'qualified-owner-wait-runtime','exec'),env)
    return env


def dependencies():
    s=(T/'presentation-c23/hotfix_provider.py').read_text(encoding='utf-8')
    exec(compile(s.split('\nspec=importlib.util.spec_from_file_location(',1)[0],
        'exact-existing-display-dependency-prefix','exec'),
        {'__file__':str(T/'presentation-c23/hotfix_provider.py'),'__name__':'_fixture_deps'})


class Cases(unittest.TestCase):
    def test_exact_source_projection_and_changed_input_rejection(self):
        from tools.g2_saved_campaign import prepare_c23_display_capture_amendment_v1 as original
        values,_,_=original.plan(T,T4,N/'A04-WAIT-RAM-ONLY',generation='C23',machine_id=MACHINE)
        raw=values['presentation-c23/start_new_game_display.py']
        projected=new.project(raw)
        self.assertIn(b'retained_recording_worker=Generation',projected)
        self.assertIn(b'finally:retained_recording_worker.close()',projected)
        self.assertEqual(projected.count(b'owner.process.wait()'),1)
        with self.assertRaisesRegex(ValueError,'exact A04'):new.project(raw+b' ')

    def test_media_terminal_missing_failure_nonzero_and_success(self):
        root=T4/'recordings/RAM-ONLY-SESSION';request={'receipt_root':str(root),
            'session_id':root.name,'worker_pid':100,'worker_creation_filetime':999}
        complete={'state':'completed','path':'RAM-only-video','bytes':123,'sha256':'a'*64}
        closed={'output_path':'RAM-only-video','output_bytes':123}
        for terminal,exitcode,status in [('missing',0,'MEDIA_TERMINAL_MISSING'),
                ('failure',0,'MEDIA_FINALIZATION_FAILED'),('missing',1,'WORKER_EXIT_NONZERO'),
                ('completed',0,'WORKER_MEDIA_NORMAL_CLOSED_JOB_TAIL_PENDING')]:
            env=functions();env['_wait_recording_worker_v1']=lambda w:{'worker_exit_code':exitcode}
            data={root/'capture_closed.json':json.dumps(closed).encode()}
            if terminal=='completed':data[root/'completed.json']=json.dumps(complete).encode()
            if terminal=='failure':data[root/'media-finalization-failed.json']=b'{}'
            capture=types.SimpleNamespace(read_capture_closed_receipt=lambda *a,**k:{'validated':True})
            with self.subTest(terminal=terminal,exitcode=exitcode), \
                 patch.object(Path,'exists',lambda p:p in data), \
                 patch.object(Path,'read_bytes',lambda p:data[p]):
                actual=env['_recording_worker_terminal_v1'](None,request,capture,101,1000)
                self.assertEqual(actual['status'],status)


def stage():
    dependencies()
    from managed_desktop1_placement import ProcessGeneration
    import win32job,threading
    watchdog=threading.Timer(20,lambda:os._exit(63));watchdog.start()
    print(json.dumps({'phase':'stage_identity','pid':os.getpid(),'sys_executable':sys.executable,
        'base':str(BASE),'current_job_pids':win32job.QueryInformationJobObject(None,3)}),flush=True)
    started=time.monotonic()
    worker=subprocess.Popen([str(BASE),'-B','-c','import time;time.sleep(.3)'],
        creationflags=subprocess.CREATE_NO_WINDOW)
    tail=subprocess.Popen([str(BASE),'-B','-c','import time;time.sleep(.1)'],
        creationflags=subprocess.CREATE_NO_WINDOW)
    with ProcessGeneration(worker.pid,BASE) as held:
        birth=held.creation_filetime
        print(json.dumps({'phase':'held_worker_before_wait','worker_pid':worker.pid,
            'worker_birth':birth,'tail_pid':tail.pid}),flush=True)
        row=functions(True)['_wait_recording_worker_v1'](held)
    row.update(machine_id=MACHINE,worker_pid=worker.pid,worker_birth=birth,
        worker_popen_exit=worker.wait(),tail_pid=tail.pid,tail_exit=tail.wait(),
        elapsed_seconds=time.monotonic()-started,Game_OBS_Task_calls=0)
    assert row['worker_exit_code']==row['worker_popen_exit']==row['tail_exit']==0
    assert row['job_tail']=='JOB_TAIL_PENDING_ORIGINAL_OWNER'
    watchdog.cancel()
    print(json.dumps(row),flush=True)


def owned():
    dependencies()
    from tools.g2_saved_campaign.interactive_task_owner_v1 import Windows
    import msvcrt
    w=Windows();job=w.job();r,write=os.pipe();process=thread=None
    with open(os.devnull,'rb') as null:
        handles=[msvcrt.get_osfhandle(null.fileno()),msvcrt.get_osfhandle(write)]
        for h in handles:os.set_handle_inheritable(h,True)
        info=subprocess.STARTUPINFO();info.dwFlags=subprocess.STARTF_USESTDHANDLES|subprocess.STARTF_USESHOWWINDOW
        info.wShowWindow=0;info.hStdInput=handles[0];info.hStdOutput=info.hStdError=handles[1]
        info.lpAttributeList={'handle_list':handles}
        try:
            argv=[str(BASE),'-B','-X','utf8',str(Path(__file__).resolve()),'--stage']
            process,thread,pid,tid=w.w.CreateProcess(str(BASE),subprocess.list2cmdline(argv),
                None,None,True,4|0x08000000|0x00080000,dict(os.environ),str(HERE.parents[1]),info)
            identity=w.identity(process);w.assign(job,process);w.resume(thread);w.close(thread);thread=None
        finally:
            for h in handles:os.set_handle_inheritable(h,False)
            os.close(write)
    try:
        if w.w.WaitForSingleObject(int(process),30000)!=0:
            w.close(job);job=None
            w.w.WaitForSingleObject(int(process),5000)
            raise RuntimeError('owned fixture timed out; exact fixture Job closed; stdout='+os.read(r,8192).decode())
        output=os.read(r,8192).decode();code=w.w.GetExitCodeProcess(int(process));active=w.active(job)
        end=time.monotonic()+2
        while active and time.monotonic()<end:time.sleep(.05);active=w.active(job)
        assert code==0 and active==0,(code,active,output)
        row=json.loads(output.splitlines()[-1]);assert row['job_tail']=='JOB_TAIL_PENDING_ORIGINAL_OWNER'
        result={'status':'ACTUAL_OWNED_PYTHON_WORKER_AND_JOB_TAIL_PASS',
            'stage':identity,'stage_exit':code,'original_job_active_after_stage':active,'child':row,
            'forced_cleanup':False,'Task_created':False,'scratch_bytes':0}
        print(json.dumps(result,indent=2))
        return result
    finally:
        os.close(r)
        if thread is not None:w.close(thread)
        if process is not None:w.close(process)
        if job is not None:w.close(job)


def seal(actual,attempt='owned01'):
    from datetime import datetime,timezone
    root=HERE.parents[1]
    refs=[]
    for p in [HERE/'project_recording_owner_wait_v1.py',Path(__file__).resolve()]:
        raw=p.read_bytes();refs.append({'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
    value={'schema':'xar.A04-recording-owner-worker-wait-source-qualification/v1',
        'machine_id':MACHINE,'observed_at_utc':datetime.now(timezone.utc).isoformat(),
        'sources':refs,'RAM_cases':'2 PASS 0.184s; four media terminal subcases; not repeated',
        'earlier_owned_attempt':'UNKNOWN: exec session ID not retained; process absence gives no credit',
        'first_source_peak':{'bytes':13202,'old_cap':12288,'over_by':914,'status':'RED preserved'},
        'current_joint_cap':20480,'attempt':attempt,'actual_owned_probe':actual,'T04_writes':0,
        'Game_OBS_Task_desktop_calls':0,'scratch_bytes':0,
        'current_Job_API_source':'https://learn.microsoft.com/windows/win32/api/jobapi2/nf-jobapi2-queryinformationjobobject'}
    raw=(json.dumps(value,indent=2)+'\n').encode()
    assert sum(r['bytes'] for r in refs)+len(raw)<=20480
    suffix='' if attempt=='owned01' else '-'+attempt
    target=root/('docs/ck3-native-ai/evidence/c23-a04-recording-owner-wait-source-qualification-2026-10-20'+suffix+'.json')
    with target.open('xb') as f:f.write(raw)
    print(json.dumps({'proof':str(target),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
        'source_joint_bytes':sum(r['bytes'] for r in refs)+len(raw)}))


if __name__=='__main__':
    if sys.argv[1:]==['--identity']:
        dependencies()
        from tools.g2_saved_campaign.interactive_task_owner_v1 import Windows
        print(json.dumps({'sys_executable':sys.executable,'base_executable':sys._base_executable,
            'actual':Windows().current()}))
    elif sys.argv[1:]==['--stage']:stage()
    elif sys.argv[1:] in (['--owned'],['--owned02']):
        attempt='owned02' if sys.argv[1:]==['--owned02'] else 'owned01'
        suffix='' if attempt=='owned01' else '-'+attempt
        target=HERE.parents[1]/('docs/ck3-native-ai/evidence/c23-a04-recording-owner-wait-source-qualification-2026-10-20'+suffix+'.json')
        if target.exists():raise FileExistsError('owned attempt already sealed; no replay')
        try:actual=owned()
        except BaseException as error:
            seal({'status':'ACTUAL_OWNED_PROBE_FAILED','error':repr(error)},attempt)
            raise
        else:seal(actual,attempt)
    else:unittest.main(verbosity=2)
