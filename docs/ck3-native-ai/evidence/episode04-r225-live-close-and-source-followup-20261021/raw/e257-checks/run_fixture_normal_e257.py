"""Focused normal imports, typed Save boundaries, and traced executed-source scope."""
from __future__ import annotations
import ctypes
from ctypes import wintypes
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys
from types import FrameType
import unittest

ROOT=Path(__file__).resolve().parent
TOP=Path('C:/ck3-e04-resume-20261020-a01/r08-pointer-live-0030-a01/immutable-a01/tools')
D=Path('D:/workspace/ck3_eternal_recurrence')
W=Path('C:/ck3-e04-resume-20261020-a01/r06-resume-a02/integration-worktree')
HEAD='e2578b59273b886a7ab58eff24ba76a161d84e6c'
MACHINE='desktop-3fevhd2-1c74096080'

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def created(child:subprocess.Popen[bytes])->str:
    class FT(ctypes.Structure):
        _fields_=[('low',wintypes.DWORD),('high',wintypes.DWORD)]
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.GetProcessTimes.argtypes=[wintypes.HANDLE,ctypes.POINTER(FT),ctypes.POINTER(FT),ctypes.POINTER(FT),ctypes.POINTER(FT)]
    k.GetProcessTimes.restype=wintypes.BOOL
    a,b,c,d=FT(),FT(),FT(),FT()
    handle=getattr(child,'_handle',None)
    if not isinstance(handle,int):
        raise ValueError('Original Popen Windows handle absent')
    if not k.GetProcessTimes(wintypes.HANDLE(handle),ctypes.byref(a),ctypes.byref(b),ctypes.byref(c),ctypes.byref(d)):
        raise OSError(ctypes.get_last_error(),'GetProcessTimes')
    return str((a.high<<32)|a.low)

def target(path:Path)->str|None:
    for root,prefix in ((TOP,'tools'),(D/'tools','tools'),(D/'ck3_autonomous_player/src','ck3_autonomous_player/src')):
        if path.is_relative_to(root):
            return prefix+'/'+path.relative_to(root).as_posix()
    return None

def main()->int:
    variant=sys.argv[1]
    if variant not in ('baseline','candidate'):
        raise ValueError('Exact fixture variant required')
    sys.path[:0]=[str(TOP),str(D/'tools'),str(D/'ck3_autonomous_player/src')]
    test=ROOT/variant/'tools/test_r08_writer_save_gate.py';original=test.read_bytes()
    namespace=runpy.run_path(str(test),run_name='save_gate_source_fixture')
    case=namespace['SaveGate']
    if not isinstance(case,type) or not issubclass(case,unittest.TestCase):
        raise ValueError('Actual unittest class absent')
    cache:dict[str,bytes]={}
    waits:list[dict[str,object]]=[]
    def checked(path:Path)->dict[str,object]:
        name=target(path)
        if name is None:
            raise ValueError('Unexpected repository source')
        if name not in cache:
            child=subprocess.Popen(['git','--no-optional-locks','--no-lazy-fetch','-c','gc.auto=0','-c','maintenance.auto=false','-C',str(W),'show',HEAD+':'+name],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            birth:str|None=None;error:BaseException|None=None
            try:birth=created(child)
            except BaseException as exc:error=exc
            data,stderr=child.communicate()
            waits.append(dict(target=name,pid=child.pid,creation_filetime=birth,original_wait=child.returncode))
            if error is not None:raise error
            if child.returncode!=0 or stderr:raise ValueError('Git source unavailable '+name)
            cache[name]=data
        data=path.read_bytes()
        if data!=cache[name]:raise ValueError('Executed input differs frome257 '+str(path))
        return dict(target=name,actual_path=str(path),bytes=len(data),sha256=sha(data))
    primary=[TOP/'ck3_mod_acceptance_cases/r08_writer_one_day.py',
        TOP/'ck3_mod_acceptance_cases/ordinary_save_contract.py']
    before=[checked(p) for p in primary]
    calls:dict[tuple[str,str],int]={}
    def trace(frame:FrameType,event:str,arg:object)->None:
        if event=='call' and frame.f_code.co_flags&2:
            path=Path(frame.f_code.co_filename).resolve()
            if target(path) is not None:
                key=(str(path),frame.f_code.co_qualname)
                calls[key]=calls.get(key,0)+1
    sys.setprofile(trace)
    try:
        result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(case))
    finally:
        sys.setprofile(None)
    executed=[checked(Path(p)) for p in sorted({p for p,n in calls})]
    after=[checked(p) for p in primary]
    if before!=after or test.read_bytes()!=original:raise ValueError('Frozen input changed')
    driver_calls=[(p,n,c) for (p,n),c in calls.items() if Path(p).name in ('driver.py','native_driver.py')]
    if driver_calls:raise ValueError('Real driver functions unexpectedly executed '+str(driver_calls))
    imported_driver=Path(str(getattr(sys.modules['xar_autoplayer.bridge.driver'],'__file__'))).resolve()
    facts=dict(machine_id=MACHINE,source_HEAD=HEAD,variant=variant,normal_imports=True,
        primary_before=before,primary_after=after,executed_sources_exact_e257=executed,
        repository_function_trace=[dict(path=p,function=n,calls=c) for (p,n),c in sorted(calls.items())],
        real_driver_runtime_calls=driver_calls,imported_driver=dict(path=str(imported_driver),
            sha256=sha(imported_driver.read_bytes()),canonical_equivalence_claimed=False,
            reason='D is frozen older; imported dependency, no real driver function executed'),
        Git_source_original_waits=waits,tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),
        Game_SDK_native_D_W_Git_mutation=False)
    out=ROOT/(variant+'.EXECUTED-SOURCE-a02.actual.json')
    with out.open('xb') as stream:stream.write((json.dumps(facts,indent=2)+'\n').encode())
    print(json.dumps(dict(variant=variant,tests_run=result.testsRun,failures=len(result.failures),
        errors=len(result.errors),executed_source_count=len(executed),real_driver_runtime_calls=0,source_proof=str(out))))
    return 0 if result.wasSuccessful() else 1

if __name__=='__main__':
    raise SystemExit(main())
