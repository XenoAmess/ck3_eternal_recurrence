from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
import subprocess

ROOT=Path(__file__).parent
B=ROOT.parent
W=B/'r06-resume-a02/integration-worktree'
OLD=B/'r08-post-window-source-0130-a01/reviewer-preflight-a01'
SAVE=B/'r08-pointer-live-0030-a01/scene-a01/ci-save-fixture-a01'
HEAD='e2578b59273b886a7ab58eff24ba76a161d84e6c'
PY=Path('D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe')
TOOLS=B/'r08-mypy1201-tools-2115-a01/Lib'
CHECK=ROOT/'source-checks-e257-a01'
MACHINE='desktop-3fevhd2-1c74096080'
G=['git','--no-optional-locks','--no-lazy-fetch','-c','gc.auto=0','-c','maintenance.auto=false','-C',str(W)]

def need(value: bool, message: str) -> None:
    if not value: raise ValueError(message)

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def pin(path: Path) -> dict[str, object]:
    data=path.read_bytes()
    return {'path':str(path),'bytes':len(data),'sha256':sha(data)}

def put(path: Path, data: bytes) -> None:
    need(datetime.now(timezone.utc)<datetime(2026,10,21,2,30,tzinfo=timezone.utc),'Deadline')
    need(sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())+len(data)<8388608,'C8 hard cap')
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as stream: need(stream.write(data)==len(data),'Short write')

def birth(child: subprocess.Popen[bytes]) -> str:
    class FT(ctypes.Structure):
        _fields_=[('low',wintypes.DWORD),('high',wintypes.DWORD)]
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.GetProcessTimes.argtypes=[wintypes.HANDLE]+[ctypes.POINTER(FT)]*4
    kernel.GetProcessTimes.restype=wintypes.BOOL
    a,b,c,d=FT(),FT(),FT(),FT()
    handle=getattr(child,'_handle',None)
    need(isinstance(handle,int),'Original handle missing')
    if not kernel.GetProcessTimes(handle,ctypes.byref(a),ctypes.byref(b),ctypes.byref(c),ctypes.byref(d)):
        raise OSError(ctypes.get_last_error(),'GetProcessTimes')
    return str((a.high<<32)|a.low)

def run(label: str, argv: list[str], env: dict[str,str]) -> tuple[int,bytes,bytes]:
    started=datetime.now(timezone.utc).isoformat()
    child=subprocess.Popen(argv,cwd=CHECK,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=False)
    identity: str|None=None
    diagnostic: str|None=None
    try:
        try: identity=birth(child)
        except BaseException as error: diagnostic=type(error).__name__+': '+str(error)
        stdout,stderr=child.communicate()
    finally:
        code=child.wait()
    need(len(stdout)<=131072 and len(stderr)<=131072,'Bounded output, owner already waited')
    out=CHECK/'receipts'/label
    put(out.with_suffix('.stdout.log'),stdout)
    put(out.with_suffix('.stderr.log'),stderr)
    receipt={'machine_id':MACHINE,'source_head':HEAD,'argv':argv,'cwd':str(CHECK),
             'started_at_utc':started,'completed_at_utc':datetime.now(timezone.utc).isoformat(),
             'pid':child.pid,'creation_filetime':identity,'actual_original_popen_wait':True,
             'returncode':code,'identity_diagnostic':diagnostic,'stdout':pin(out.with_suffix('.stdout.log')),
             'stderr':pin(out.with_suffix('.stderr.log')),'D_W_Git_Game_SDK_Steam_mutation':False}
    put(out.with_suffix('.ORIGINAL-WAIT.actual.json'),(json.dumps(receipt,indent=2)+'\n').encode())
    need(diagnostic is None,'Identity failed after actual wait')
    print(json.dumps({'label':label,'pid':child.pid,'birth':identity,'wait':code}))
    return code,stdout,stderr

def source(name: str) -> bytes:
    process=subprocess.Popen(G+['show',HEAD+':'+name],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try: stdout,stderr=process.communicate()
    finally: code=process.wait()
    need(code==0 and not stderr,'Exact Git source '+name)
    return stdout

def main() -> None:
    CHECK.mkdir()
    base=source('tools/test_r08_writer_save_gate.py')
    needle=b'                with self.assertRaisesRegex(ValueError,\'Save unproved\'):client.normal_close(\'must not Quit\')\n'
    need(base.count(needle)==1,'Unique Save assertion seam')
    add=b'''                self.assertEqual(sum(label=='Save-independent-after' for label,_,_ in calls),
                    0 if failed=='Save-once' else 1)
                proof = obj(cleanup['ordinary_save_proof'], 'synthetic unconfirmed proof')
                self.assertEqual(proof['reason_code'], 'TimeoutError')
                expected = ('synthetic original result unknown' if failed=='Save-once'
                    else 'synthetic independent endpoint unknown')
                self.assertIn(expected, str(proof['detail']))
                self.assertEqual('Save_result' in cleanup, failed=='Save-independent-after')
'''
    old=b'from xar_autoplayer.bridge.army_observer_research_sampling_control import FAMILIES\n'
    need(base.count(old)==1,'Unique Save obj import seam')
    candidate=base.replace(old,old+b'from ck3_mod_acceptance_cases.ordinary_save_contract import obj\n').replace(needle,add+needle)
    put(CHECK/'save/baseline/tools/test_r08_writer_save_gate.py',base)
    put(CHECK/'save/candidate/tools/test_r08_writer_save_gate.py',candidate)
    helper=(SAVE/'run_fixture_normal_a02.py').read_text()
    helper=helper.replace("HEAD='81ac4459a19451c8435d91f16f9d6ede7038a7ac'","HEAD='"+HEAD+"'")
    helper=helper.replace('exact_81ac','exact_e257').replace('differs from81ac','differs frome257')
    put(CHECK/'save/run_fixture_normal_e257.py',helper.encode())
    for name in ['ck3_mod_acceptance.py','test_ck3_mod_acceptance_reviewer_prelaunch.py','test_ck3_mod_acceptance_operator_quit.py']:
        put(CHECK/'reviewer/candidate/tools'/name,(OLD/'candidate/tools'/name).read_bytes())
    support=['ck3_mod_acceptance_client.py','ck3_mod_acceptance_background_types.py','ck3_mod_acceptance_native_day.py','ck3_mod_acceptance_launcher_protocol_v1.py']
    for name in support: put(CHECK/'reviewer/candidate/tools'/name,source('tools/'+name))
    helper=(OLD/'check_existing_finally.py').read_text().replace('9592cefdda846fc0242430d8fef1fef1f58c81a0',HEAD).replace('git:9592cef:','git:e2578b:')
    put(CHECK/'reviewer/check_existing_finally_e257.py',helper.encode())
    workflow=source('.github/workflows/static-ci.yml')
    anchor=b'          python -B -X utf8 tools/test_ck3_mod_acceptance_business_reviewer.py\n'
    need(workflow.count(anchor)==1,'Unique latest workflow anchor')
    rendered=workflow.replace(anchor,anchor+b'          if not "%errorlevel%"=="0" exit /b %errorlevel%\n          python -B -X utf8 tools/test_ck3_mod_acceptance_reviewer_prelaunch.py\n')
    put(CHECK/'workflow/static-ci.yml',rendered)
    temporary=CHECK/'tmp';temporary.mkdir()
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',TMP=str(temporary),TEMP=str(temporary),CK3_REVIEWER_TEST_TMP=str(temporary))
    checks=[]
    for mode in ['baseline','candidate']:
        checks.append(run('SAVE-'+mode,[str(PY),'-B','-X','utf8',str(CHECK/'save/run_fixture_normal_e257.py'),mode],env)[0])
    checks.append(run('REVIEWER-8',[str(PY),'-B','-X','utf8',str(CHECK/'reviewer/candidate/tools/test_ck3_mod_acceptance_reviewer_prelaunch.py')],env)[0])
    checks.append(run('REVIEWER-FINALLY-1',[str(PY),'-B','-X','utf8',str(CHECK/'reviewer/check_existing_finally_e257.py')],env)[0])
    typed=dict(env,PYTHONPATH=str(TOOLS),MYPYPATH=os.pathsep.join([str(CHECK/'reviewer/candidate/tools'),str(B/'r08-pointer-live-0030-a01/immutable-a01/tools'),str(Path('D:/workspace/ck3_eternal_recurrence/ck3_autonomous_player/src'))]))
    for mode in ['baseline','candidate']:
        checks.append(run('STRICT-MYPY-SAVE-'+mode,[str(PY),'-B','-X','utf8','-m','mypy','--strict','--strict-equality','--follow-imports=skip','--no-incremental','--cache-dir','nul',str(CHECK/'save'/mode/'tools/test_r08_writer_save_gate.py')],typed)[0])
    summary={'machine_id':MACHINE,'observed_at_utc':datetime.now(timezone.utc).isoformat(),
             'source_head':HEAD,'codes':checks,'all_expected_zero':all(x==0 for x in checks),
             'Save_source':pin(CHECK/'save/candidate/tools/test_r08_writer_save_gate.py'),
             'workflow_source':pin(CHECK/'workflow/static-ci.yml'),'support_sources':[pin(CHECK/'reviewer/candidate/tools'/n) for n in support],
             'only_added_to_upstream_Save':'obj import and four stronger branch assertions',
             'temporary_remaining':[str(p) for p in temporary.rglob('*')],
             'D_W_Git_Game_SDK_Steam_mutation':False}
    put(CHECK/'CHECKS.actual-a01.json',(json.dumps(summary,indent=2)+'\n').encode())
    print(json.dumps(summary))
    need(all(x==0 for x in checks),'Retain actual nonzero; no blind rerun')

if __name__=='__main__': main()
