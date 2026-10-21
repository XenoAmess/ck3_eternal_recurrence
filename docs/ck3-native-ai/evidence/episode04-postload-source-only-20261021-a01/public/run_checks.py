"""Only bounded Python source checks; own original Popen through actual wait."""
from __future__ import annotations
import argparse,ctypes,hashlib,json,os,subprocess,sys,time
from ctypes import wintypes
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def pin(path: Path) -> dict[str,object]:
    data=path.read_bytes();return {'path':str(path),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}

def main() -> None:
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['mypy','focused']);parser.add_argument('attempt')
    args=parser.parse_args()
    if datetime.now(timezone.utc)>=datetime(2026,10,21,2,30,tzinfo=timezone.utc):raise ValueError('source scope expired')
    actual=sum(path.stat().st_size for path in ROOT.rglob('*') if path.is_file())
    if actual>=1900000:raise ValueError('leave source lane receipt headroom')
    tmp=ROOT/'tmp';tmp.mkdir(exist_ok=True)
    output=ROOT/('checks-'+args.mode+'-'+args.attempt);output.mkdir()
    tools=ROOT/'candidate/native-tools';cases=ROOT/'candidate/tools/ck3_mod_acceptance_cases'
    env=dict(os.environ,PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1',TEMP=str(tmp),TMP=str(tmp),
        PYTHONPATH=';'.join([str(tools),str(ROOT/'candidate/tools'),
            'D:/workspace/ck3_eternal_recurrence/tools',
            'D:/workspace/ck3_eternal_recurrence/ck3_autonomous_player/src',
            'C:/ck3-e04-resume-20261020-a01/r08-mypy1201-tools-2115-a01/Lib']),
        MYPYPATH=';'.join([str(tools),str(ROOT/'candidate/tools'),'D:/workspace/ck3_eternal_recurrence/tools','D:/workspace/ck3_eternal_recurrence/ck3_autonomous_player/src']),POSTLOAD_TEST_TMP=str(tmp))
    names=['postload_admission.py','prepare_parent_postload_admission.py','consume_parent_postload_actual.py','postload_root_scope.py']
    sources=[tools/name for name in names]
    sources += [cases/name for name in ['postload_public_models.py','r08_parent_postload_controller.py',
        'r08_parent_postload_one_day.py','postload_bundle_loader.py','r08_postload_adapter.py']]
    argv=[sys.executable,'-B','-X','utf8']
    if args.mode=='mypy':argv+=['-m','mypy','--strict','--no-incremental','--cache-dir=nul','--follow-imports=skip',*[str(path) for path in sources]]
    else:argv+=[str(ROOT/'test_postload_public.py')]
    start=datetime.now(timezone.utc).isoformat();tick=time.monotonic()
    with (output/'stdout.log').open('xb') as stdout,(output/'stderr.log').open('xb') as stderr:
        process=subprocess.Popen(argv,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,
            creationflags=subprocess.CREATE_NO_WINDOW,shell=False)
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.GetProcessTimes.argtypes=(wintypes.HANDLE,)+(ctypes.POINTER(wintypes.FILETIME),)*4
        kernel.GetProcessTimes.restype=wintypes.BOOL
        a,b,c,d=(wintypes.FILETIME() for _ in range(4))
        good=bool(kernel.GetProcessTimes(int(process._handle),ctypes.byref(a),ctypes.byref(b),ctypes.byref(c),ctypes.byref(d)))
        code=process.wait()
        if not good:raise ctypes.WinError(ctypes.get_last_error())
        birth=str((int(a.dwHighDateTime)<<32)|int(a.dwLowDateTime))
    result={'schema':'xar.e04.postload.public-source-check.v1','machine_id':'desktop-3fevhd2-1c74096080',
        'started_at_utc':start,'observed_at_utc':datetime.now(timezone.utc).isoformat(),
        'original_pid':process.pid,'creation_time_100ns':birth,'original_wait_returncode':code,
        'elapsed_seconds':time.monotonic()-tick,'argv':argv,'cwd':str(ROOT),
        'sources':[pin(path) for path in sources],
        'stdout':pin(output/'stdout.log'),'stderr':pin(output/'stderr.log'),
        'tmp_remaining':[str(path) for path in tmp.rglob('*')],
        'native_Game_SDK_Steam_UI_EXE':False,'source_only_not_qualification':True}
    target=output/'ORIGINAL-WAIT.actual.json';target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'receipt':pin(target),'code':code}))
    raise SystemExit(code)

if __name__=='__main__':main()
