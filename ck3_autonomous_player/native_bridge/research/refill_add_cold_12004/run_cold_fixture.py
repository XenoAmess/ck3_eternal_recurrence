"""Controlled sibling process only. Gate both project EXEs before first execution."""
from pathlib import Path
import argparse, ctypes, datetime as dt, hashlib, json, subprocess, sys, time

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--repo',type=Path,required=True)
parser.add_argument('--build-dir',type=Path,required=True)
parser.add_argument('--output-root',type=Path,required=True)
args=parser.parse_args()
REPO=args.repo.resolve();BUILD=args.build_dir.resolve();OUT=args.output_root.resolve()
PYTHON=REPO/'tools/.venv/Scripts/python.exe'
MACHINE=subprocess.check_output([str(PYTHON),'-B',str(REPO/'tools/ck3_live_run_id.py'),'machine'],text=True).strip()

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def gate():
    current_machine=subprocess.check_output([str(PYTHON),'-B',str(REPO/'tools/ck3_live_run_id.py'),'machine'],text=True).strip()
    assert current_machine==MACHINE
    result=json.loads((BUILD/'native-msvc-result.json').read_text())
    exclusion=result['defender_exclusions']
    receipt_path=Path(exclusion['receipt']); receipt=json.loads(receipt_path.read_text())
    manifest_path=Path(exclusion['manifest']);manifest=json.loads(manifest_path.read_text())
    assert result['built'] and exclusion['status']=='verified'
    assert sha(receipt_path)==exclusion['receipt_sha256']
    assert receipt['status']=='verified' and receipt['admin_token'] is True
    assert receipt['system_token_sid']=='S-1-5-18'
    # The standard producer binds the parsed manifest using its canonical JSON encoding.
    assert receipt['manifest_sha256']==hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()
    assert receipt['missing_requested_paths']==[]
    assert {Path(x['path']).name for x in manifest['files']}=={'refill_cold_target.exe','refill_cold_observer.exe'}
    files=[]
    for item in manifest['files']:
        p=Path(item['path']);assert p.parent==BUILD
        assert str(p) in receipt['verified_requested_paths']
        assert p.stat().st_size==item['size'] and sha(p)==item['sha256']
        assert any(x['path']==str(p) and x['sha256']==item['sha256'] for x in receipt['files'])
        files.append(item)
    for pin in receipt['input_pins']:
        assert sha(pin['path'])==pin['sha256']
    return {'machine_id':MACHINE,'observed_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
      'status':'verified-before-first-project-EXE-execution','receipt':str(receipt_path),
      'receipt_sha256':sha(receipt_path),'manifest_file_sha256':sha(manifest_path),
      'manifest_canonical_sha256':receipt['manifest_sha256'],'system_token_sid':receipt['system_token_sid'],
      'admin_token':True,'files':files,'game_contacted':False}

kernel=ctypes.WinDLL('kernel32',use_last_error=True)
kernel.OpenEventW.argtypes=[ctypes.c_uint32,ctypes.c_int,ctypes.c_wchar_p]
kernel.OpenEventW.restype=ctypes.c_void_p
kernel.SetEvent.argtypes=[ctypes.c_void_p];kernel.SetEvent.restype=ctypes.c_int
kernel.CloseHandle.argtypes=[ctypes.c_void_p];kernel.CloseHandle.restype=ctypes.c_int
kernel.OpenProcess.argtypes=[ctypes.c_uint32,ctypes.c_int,ctypes.c_uint32];kernel.OpenProcess.restype=ctypes.c_void_p
kernel.ReadProcessMemory.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
kernel.ReadProcessMemory.restype=ctypes.c_int
kernel.CheckRemoteDebuggerPresent.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_int)]
kernel.CheckRemoteDebuggerPresent.restype=ctypes.c_int
def presence_query(meta):
    checks=[]
    for label,rights in [('prior_limited_query',0x1012),('fixed_query_information',0x1412)]:
        h=kernel.OpenProcess(rights,False,int(meta['pid']))
        if not h:raise ctypes.WinError(ctypes.get_last_error())
        try:
            detected=ctypes.c_int(-1);ctypes.set_last_error(0)
            ok=bool(kernel.CheckRemoteDebuggerPresent(h,ctypes.byref(detected)))
            checks.append({'handle_rights':hex(rights),'label':label,'api_return_success':ok,
              'last_error':ctypes.get_last_error(),'debugger_present':bool(detected.value) if ok else None})
        finally:kernel.CloseHandle(h)
    assert not checks[0]['api_return_success'] and checks[0]['last_error']==5,checks
    assert checks[1]['api_return_success'] and not checks[1]['debugger_present'],checks
    return {'machine_id':MACHINE,'observed_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
      'pid':int(meta['pid']),'process_created_filetime':int(meta['created']),
      'scope':'read-only API checks on controlled synthetic target before observer attach','checks':checks}
def owned_site_bytes(meta):
    h=kernel.OpenProcess(0x1010,False,int(meta['pid']))
    if not h:raise ctypes.WinError(ctypes.get_last_error())
    try:
        result=[]
        for key,n,expected in [('site0',3,'0150f4'),('site1',6,'8b48f43b48f0')]:
            buf=ctypes.create_string_buffer(n);actual=ctypes.c_size_t()
            if not kernel.ReadProcessMemory(h,int(meta[key]),buf,n,ctypes.byref(actual)) or actual.value!=n:
                raise ctypes.WinError(ctypes.get_last_error())
            b=buf.raw;assert b.hex()==expected
            result.append({'synthetic_site_address':int(meta[key]),'bytes':n,'hex':b.hex(),'sha256':hashlib.sha256(b).hexdigest()})
        return {'machine_id':MACHINE,'observed_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
          'source':'ReadProcessMemory of owned synthetic sibling target before debugger attach',
          'pid':int(meta['pid']),'process_created_filetime':int(meta['created']),'CK3_binary_read':False,'sites':result}
    finally:kernel.CloseHandle(h)
def signal(name):
    h=kernel.OpenEventW(2,False,name)
    if not h:raise ctypes.WinError(ctypes.get_last_error())
    try:
        if not kernel.SetEvent(h):raise ctypes.WinError(ctypes.get_last_error())
    finally:kernel.CloseHandle(h)
def wait_file(p,proc,timeout=10):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        if p.exists() and p.stat().st_size:
            try:return p.read_text(encoding='utf-8')
            except PermissionError:pass
        if proc.poll() is not None:raise RuntimeError(f'{p.name} missing, process exited {proc.returncode}')
        time.sleep(.02)
    raise TimeoutError(str(p))
def read_json(p,proc):
    # Writers close before later synchronization. Retry a short incomplete read.
    end=time.monotonic()+10
    while True:
        try:return json.loads(wait_file(p,proc))
        except json.JSONDecodeError:
            if time.monotonic()>end:raise
            time.sleep(.02)
def run(mode):
    case=OUT/mode;case.mkdir(parents=True,exist_ok=False);prefix=case/'target'
    started=dt.datetime.now(dt.timezone.utc).isoformat()
    target_args=[str(BUILD/'refill_cold_target.exe'),'--mode',mode,'--prefix',str(prefix)]
    with (case/'target.stdout').open('wb') as tso,(case/'target.stderr').open('wb') as tse:
        target=subprocess.Popen(target_args,stdout=tso,stderr=tse,creationflags=0x08000000)
        observer=None;meta={}
        try:
            meta=dict(line.split('=',1) for line in wait_file(Path(str(prefix)+'.meta.txt'),target).splitlines())
            assert int(meta['pid'])==target.pid
            write(case/'owned-site-bytes.actual.json',owned_site_bytes(meta))
            write(case/'debugger-presence-rights.actual.json',presence_query(meta))
            raw=case/'observer.raw.ndjson';ready=case/'observer.ready.json'
            observer_args=[str(BUILD/'refill_cold_observer.exe'),'--fixture-meta',str(prefix)+'.meta.txt',
              '--timeout-ms','1000' if mode=='timeout' else '5000','--raw',str(raw),'--ready',str(ready),
              '--max-hits','4' if mode=='finite-hit' else '100000','--select-missing','1' if mode=='finite-hit' else '0',
              '--machine-id',MACHINE]
            with (case/'observer.stdout').open('wb') as oso,(case/'observer.stderr').open('wb') as ose:
                observer=subprocess.Popen(observer_args,stdout=oso,stderr=ose,creationflags=0x08000000)
                ready_json=read_json(ready,observer)
                if mode!='timeout':signal(meta['go_event'])
                observer_code=observer.wait(timeout=12)
            rows=[json.loads(x) for x in raw.read_text().splitlines()]
            terminal=next(x for x in rows if x.get('kind')=='terminal')
            assert terminal['debug_registers_cleared'] and terminal['detached'],terminal
            if mode=='exit-before-add':
                target_code=target.wait(timeout=5);assert target_code==0
                result=None;audit={'process_normal_exit':True,'restore_readback':'not-applicable-target-exited'}
            else:
                if mode=='timeout':signal(meta['go_event'])
                result=read_json(Path(str(prefix)+'.add.json'),target)
                signal(meta['audit_event'])
                initial=read_json(Path(str(prefix)+'.initial-debug.json'),target)
                after=read_json(Path(str(prefix)+'.after-debug.json'),target)
                assert initial['ok'] and after['ok']
                assert initial==after,(initial,after)
                audit={'initial':initial,'after':after,'exact_equal':True}
                signal(meta['finish_event']);target_code=target.wait(timeout=5);assert target_code==0
                assert result['main_ADD_execution_count']==(16 if mode=='finite-hit' else 1)
                assert result['worker_ADD_execution_count']==(1 if mode=='other-thread' else 0)
                assert result['after_u32']==(result['before_u32']+result['q_u32']*result['main_ADD_execution_count'])&0xffffffff
            expected_pair=mode not in ('timeout','finite-hit','exit-before-add')
            assert observer_code==(0 if expected_pair else 1),(observer_code,terminal)
            assert terminal['reason']==('paired' if expected_pair else 'timeout_before_unique_pair' if mode=='timeout' else 'debug_hit_budget_exhausted' if mode=='finite-hit' else 'process_exited_during_probe'),terminal
            boundary=[x for x in rows if x.get('kind')=='raw_ADD_boundary']
            if expected_pair:
                assert len(boundary)==2
                assert all(x['thread_id']==int(meta['tid']) for x in boundary)
                guard=next(x for x in rows if x.get('kind')=='fixture_mismatch_guard')
                assert guard['derived_from_actual_owned_hits'] and guard['cross_tid_q_pointer_current_all_refused']
            else:assert len(boundary)==0
            record={'machine_id':MACHINE,'observed_at_utc':started,'mode':mode,'status':'PASS',
              'synthetic':True,'CK3_actual_ADD_observed':False,'target_argv':target_args,'observer_argv':observer_args,
              'target_exit_code':target_code,'observer_exit_code':observer_code,'ready':ready_json,'target_result':result,
              'debug_register_audit':audit,'terminal':terminal,'raw_sha256':sha(raw),'raw_bytes':raw.stat().st_size,
              'raw_boundary_count':len(boundary)}
            write(case/'RESULT.actual.json',record)
            print(json.dumps({'mode':mode,'status':'PASS','terminal':terminal,'target':result}),flush=True)
            return record
        except BaseException as ex:
            write(case/'FAILURE.actual.json',{'machine_id':MACHINE,'observed_at_utc':started,'error':repr(ex),
              'target_pid':target.pid,'observer_pid':None if observer is None else observer.pid,
              'target_status':target.poll(),'observer_status':None if observer is None else observer.poll()})
            # Never kill a debugged target. Observer has an internal finite window and cleanup.
            if observer is not None and observer.poll() is None:
                try:observer.wait(timeout=12)
                except subprocess.TimeoutExpired:pass
            for key in ('go_event','audit_event','finish_event'):
                if key in meta:
                    try:signal(meta[key])
                    except OSError:pass
            try:target.wait(timeout=35)
            except subprocess.TimeoutExpired:pass
            raise

if __name__=='__main__':
    OUT.mkdir(exist_ok=False)
    write(OUT/'EXECUTION-GATE.actual.json',gate())
    modes=['normal','zero','wrap','negative','other-thread','finite-hit','timeout','exit-before-add']
    results=[]
    for mode in modes:results.append(run(mode))
    write(OUT/'COLD-SUITE.actual.json',{'machine_id':MACHINE,
      'observed_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'cases':results,'status':'PASS',
      'CK3_actual_ADD_observed':False,'scope':'controlled synthetic sibling target only'})
