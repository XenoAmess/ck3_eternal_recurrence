"""Exact T02 original-Popen orchestration; no native source modification."""
import ctypes,datetime,hashlib,json,os,subprocess,time
from pathlib import Path
B=Path('C:/w/e04parentdr02'); S=Path('C:/ck3-war-episode04-research-20261004-a01/e04-r08-parent-dr-source-p02')
PY='D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe'
M='desktop-3fevhd2-1c74096080'
P=B/'control-metadata-a01/PARENT-DR-NATIVE-RECIPE.prepared-a03.json'; PS='824baf95a239267bf9288438b1dd283dbdb33ba2a377c3fd9de3503a433217c3'
C=B/'capacity/PARENT-DR-NATIVE64-2015-COLD.actual-a04.json'; CS='073c36fbd82dea4a4c424fd96216c7a0bce412d669e317674e2256ba6e6aef5f'
G=B/'capacity/fresh_parent_dr_native64_2015_prepared_a01.py'; GS='71bd048db4f5d3c9c093f699ed70edab2759e1ed97f7d9b417108b762a6c61ee'
OUT=B/'cold-execution-a01'
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def pin(p):
    b=Path(p).read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def put(p,v):
    with Path(p).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2);f.write('\n')
def identity(p):
    k=ctypes.WinDLL('kernel32',use_last_error=True);k.GetProcessTimes.argtypes=[ctypes.c_void_p]*5;k.GetProcessTimes.restype=ctypes.c_int
    t=[ctypes.c_uint64() for _ in range(4)]
    ok=k.GetProcessTimes(int(p._handle),*[ctypes.byref(v) for v in t])
    return dict(pid=p.pid,creation_time_100ns=t[0].value if ok else None,creation_time_read_error=None if ok else ctypes.get_last_error())
def measure(root):
    total=0; count=0
    for directory,dirs,files in os.walk(root):
        for n in files:
            q=Path(directory)/n;st=q.stat(follow_symlinks=False)
            assert not getattr(st,'st_file_attributes',0)&0x400
            total+=st.st_size;count+=1
    return dict(bytes=total,files=count)
env=os.environ.copy();env.update(GIT_OPTIONAL_LOCKS='0',PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',TEMP=str(B/'tmp-a01'),TMP=str(B/'tmp-a01'))
assert pin(P)['sha256']==PS and pin(C)['sha256']==CS and pin(G)['sha256']==GS
plan=json.loads(P.read_bytes());cap=json.loads(C.read_bytes())
assert cap['EXE_execution_admitted'] is True and cap['cold_execution_admitted'] is True
assert not OUT.exists() and not (B/'cold-a01').exists();OUT.mkdir()
def captured(label,argv):
    start=now();p=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env);ident=identity(p)
    out,err=p.communicate();rc=p.wait()
    (OUT/(label+'.stdout.log')).write_bytes(out);(OUT/(label+'.stderr.log')).write_bytes(err)
    put(OUT/(label+'-ORIGINAL-WAIT.actual.json'),dict(machine_id=M,argv=argv,**ident,original_Popen=True,original_wait=True,started_at_utc=start,finished_at_utc=now(),exit_code=rc))
    assert rc==0,(label,rc,err.decode('utf-8',errors='replace'))
    return out
fresh=captured('FRESH',[PY,'-B','-X','utf8',str(G),'--cap',str(C),'--cap-sha256',CS,'--phase','cold-selected-suite','--output','-'])
assert json.loads(fresh)['budget_status']=='GREEN';(OUT/'FRESH.actual.json').write_bytes(fresh)
verify=[PY,'-B','-X','utf8',str(B/'control-metadata-a01/freeze_parent_dr_sources_a01.py'),'--plan',str(P),'--plan-sha256',PS,'--capacity',str(C),'--capacity-sha256',CS,'--verify-only','--manifest-sha256','fbefc43570ccb9880b9d4362688eea732cb6e3d49813864a2866c0647fae68c7']
captured('VERIFY',verify)
argv=plan['phase_argv']['cold-selected-suite'];assert argv==cap['allowed_phase_argv']['cold-selected-suite']
put(OUT/'INTENT.actual-a01.json',dict(machine_id=M,observed_at_utc=now(),argv=argv,plan=pin(P),capacity=pin(C),fresh=pin(OUT/'FRESH.actual.json'),source_manifest=pin(S/'SOURCE-MANIFEST.actual.json'),Root_review=cap['Root_actual_SYSTEM_review'],no_replay=True))
bus='D:/workspace/.codex-task-bus/bin/codex_task_bus.py';task='e04-parent-dr-native64-2015-execution-20261020-a02'
subprocess.run([PY,'-B',bus,'status','--task',task,'--state','running','--summary',M+' T02 exact17 synthetic cold running; project EXEs only; no game SDK','--next-step','Original Popen waits and full6/warmup1 review; hard20:15','--resource','parent-dr-native64:C:/w/e04parentdr02'],env=env,stdout=subprocess.DEVNULL,check=True)
red=None;seen=set();peaks={'source_bytes':0,'build_bytes':0};start=now()
with (OUT/'stdout.log').open('xb') as so,(OUT/'stderr.log').open('xb') as se:
    p=subprocess.Popen(argv,stdout=so,stderr=se,env=env);ident=identity(p)
    put(OUT/'ORIGINAL-POPEN.actual-a01.json',dict(machine_id=M,argv=argv,**ident,original_Popen=True,started_at_utc=start));print('COLD_ORIGINAL',json.dumps(ident),flush=True)
    while p.poll() is None:
        try:
            sm=measure(S);bm=measure(B);peaks['source_bytes']=max(peaks['source_bytes'],sm['bytes']);peaks['build_bytes']=max(peaks['build_bytes'],bm['bytes'])
            if sm['bytes']>2097152 or bm['bytes']>31457280:
                if red is None:red=dict(observed_at_utc=now(),source=sm,build=bm);print('CAPACITY_RED_OWNER_RETAINED',json.dumps(red),flush=True)
            for q in (B/'cold-a01').glob('*/CASE.actual.json'):
                if str(q) not in seen:
                    v=json.loads(q.read_bytes());seen.add(str(q));print('CASE',v['case'],v['status'],flush=True)
            for q in (B/'cold-a01').glob('*/UNRESOLVED-OWNER-HOLD.actual.json'):
                if str(q) not in seen:seen.add(str(q));print('OWNER_HOLD',str(q),flush=True)
        except BaseException as exc:
            if red is None:red=dict(observed_at_utc=now(),read_error=repr(exc));print('MONITOR_READ_ERROR_OWNER_RETAINED',repr(exc),flush=True)
        time.sleep(1)
    rc=p.wait()
put(OUT/'ORIGINAL-WAIT.actual-a01.json',dict(machine_id=M,argv=argv,**ident,original_Popen=True,original_wait=True,started_at_utc=start,finished_at_utc=now(),exit_code=rc,capacity_red=red))
put(OUT/'LOCAL-CAPACITY-MONITOR.actual.json',dict(machine_id=M,observed_at_utc=now(),sample_interval_seconds=1,metadata_samples_not_continuous_peak_proof=True,peaks=peaks,capacity_red=red,protected_protocol_conservative_charge_bytes=33554432,protected_private_enumeration_not_claimed=True))
print('COLD_ORIGINAL_WAIT',rc,'CAPACITY_RED',json.dumps(red),flush=True)
raise SystemExit(rc)
