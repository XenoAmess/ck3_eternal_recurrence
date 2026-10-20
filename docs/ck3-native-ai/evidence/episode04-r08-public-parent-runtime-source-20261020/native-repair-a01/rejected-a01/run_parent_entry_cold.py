"""Future qualified synthetic execution-DR cold only; --help never runs EXEs.

Unknown debugger/restore state retains both Popen owners. It never kills a
debugger. A proven detached synthetic target may finish after audit FAIL;
that explicit failed audit never becomes a PASS.
"""
import argparse,ctypes,datetime,hashlib,json,os,subprocess,sys,time
from ctypes import wintypes as W
from pathlib import Path

CASES=('foreign257_then_target','created_thread','foreign4096_limit','timeout',
       'cancel_late','restore-fault','readback-fault','continue-fault',
       'default-off','missing-ack','bad-schema','occupied-dr','occupied-tf',
       'context-drift','fullid-drift','magic-drift','session-drift')
REFUSALS={'default-off','missing-ack','bad-schema','occupied-dr','occupied-tf'}
FAULTS={'restore-fault':'restore','readback-fault':'readback','continue-fault':'continue'}
PARTIAL_REASONS={'foreign4096_limit':'foreign_limit','timeout':'timeout','cancel_late':'cancel',
                 'fullid-drift':'target_read_incomplete','magic-drift':'target_read_incomplete',
                 'session-drift':'target_read_incomplete'}

def parser():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('repo','build-dir','machine-build-record','output-root'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--case',choices=CASES,action='append',required=True)
    p.add_argument('--execute-qualified-cold',action='store_true',help='Explicit future execution acknowledgement; still requires actual build and SYSTEM proof')
    return p

def select_cases(values):
    if not values or len(set(values))!=len(values) or any(x not in CASES for x in values):raise ValueError('Select distinct explicit finite cold cases')
    return tuple(values)

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def pin(p):
    p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def load(p):return json.loads(Path(p).read_bytes())
def load_complete(p,seconds=5):
    until=time.monotonic()+seconds
    while True:
        try:return load(p)
        except (FileNotFoundError,json.JSONDecodeError):
            if time.monotonic()>until:raise
            time.sleep(.01)
def write(p,v):
    with Path(p).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2);f.write('\n')
def read_meta(p):
    p=Path(p)
    if p.stat().st_size>16384:raise ValueError('Oversize target metadata before read')
    with p.open('rb') as f:b=f.read(16385)
    if len(b)>16384:raise ValueError('Oversize target metadata')
    rows={}
    for line in b.decode('ascii').splitlines():
        key,sep,value=line.partition('=')
        if not sep or key in rows:raise ValueError('Malformed or duplicate target metadata')
        rows[key]=value
    if rows.get('parent_schema')!='xar.maintenance.parent_entry.cold-meta.v1':raise ValueError('Wrong parent fixture schema')
    return rows
def raw_rows(p,final=False):
    if not p.exists():return []
    if p.stat().st_size>262144:raise ValueError('Raw bounded-output ceiling exceeded before read')
    with p.open('rb') as f:b=f.read(262145)
    if len(b)>262144:raise ValueError('Raw bounded-output ceiling exceeded')
    if final and b and not b.endswith(b'\n'):raise ValueError('Truncated final native raw')
    lines=b.splitlines() if final or b.endswith(b'\n') else b.splitlines()[:-1]
    return [json.loads(x) for x in lines if x]

class Windows:
    def __init__(self):
        self.k=ctypes.WinDLL('kernel32',use_last_error=True)
        self.k.GetProcessTimes.argtypes=[W.HANDLE]+[ctypes.POINTER(W.FILETIME)]*4;self.k.GetProcessTimes.restype=W.BOOL
        self.k.OpenEventW.argtypes=[W.DWORD,W.BOOL,W.LPCWSTR];self.k.OpenEventW.restype=W.HANDLE
        self.k.SetEvent.argtypes=[W.HANDLE];self.k.SetEvent.restype=W.BOOL
        self.k.CloseHandle.argtypes=[W.HANDLE]
    def identity(self,p):
        c,e,k,u=W.FILETIME(),W.FILETIME(),W.FILETIME(),W.FILETIME()
        if not self.k.GetProcessTimes(W.HANDLE(int(p._handle)),ctypes.byref(c),ctypes.byref(e),ctypes.byref(k),ctypes.byref(u)):raise ctypes.WinError(ctypes.get_last_error())
        return dict(pid=p.pid,created=(c.dwHighDateTime<<32)|c.dwLowDateTime)
    def event(self,name):
        if not name.startswith('Local\\XarParentEntryCold'):raise ValueError('Not an exact synthetic target event')
        h=self.k.OpenEventW(2,False,name)
        if not h:raise ctypes.WinError(ctypes.get_last_error())
        try:
            if not self.k.SetEvent(h):raise ctypes.WinError(ctypes.get_last_error())
        finally:self.k.CloseHandle(h)

def verify_build(options,machine):
    build=options.build_dir.resolve();report=load(build/'native-msvc-result.json');record=load(options.machine_build_record)
    if record.get('machine_id')!=machine or record.get('returncode')!=0 or str(build) not in record.get('argv',[]):raise ValueError('Actual machine-labelled original build is missing')
    if report.get('build_succeeded') is not True:raise ValueError('Requested built=true is not actual successful build')
    for item in record['source_pins']:
        value=pin(item['path'])
        if any(value[k]!=item[k] for k in ('bytes','sha256')):raise ValueError('Build source changed')
    names={Path(x['path']).name for x in record['source_pins']}
    if not {'cold_observer.cpp','parent_entry_execution_once.inc','parent_entry_cold_target.cpp','parent_entry_cold_call.asm','CMakeLists.txt'}<=names:raise ValueError('New execution-DR source closure is not bound')
    ex=report['defender_exclusions'];receipt=load(ex['receipt']);manifest=load(ex['manifest'])
    if ex['status']!='verified' or pin(ex['receipt'])['sha256']!=ex['receipt_sha256']:raise ValueError('Actual exact SYSTEM receipt missing')
    if receipt.get('status')!='verified' or receipt.get('admin_token') is not True or receipt.get('system_token_sid')!='S-1-5-18':raise ValueError('SYSTEM actual setting not verified')
    if receipt['files']!=manifest['files'] or receipt['missing_requested_paths'] or receipt.get('partial_mutation') is not False:raise ValueError('Partial or mismatched SYSTEM setting')
    if not all(receipt.get(x) is True for x in ('observed_extensions_unchanged','observed_processes_unchanged','observed_prior_settings_preserved')):raise ValueError('Other Defender settings not independently preserved')
    wanted={'maintenance_parent_entry_observer.exe','maintenance_parent_entry_cold_target.exe'}
    if {Path(x['path']).name for x in manifest['files']}!=wanted:raise ValueError('This runner cannot inherit A08 or unrelated EXE qualification')
    for item in manifest['files']:
        p=Path(item['path']).resolve()
        if p.parent!=build or p.stat().st_size!=item['size'] or pin(p)['sha256']!=item['sha256']:raise ValueError('New exact project EXE bytes changed')
        if os.path.normcase(str(p)) not in {os.path.normcase(x) for x in receipt['verified_requested_paths']}:raise ValueError('New EXE path not actually excluded')
    return dict(machine_id=machine,observed_at_utc=now(),producer=pin(build/'native-msvc-result.json'),original_build=pin(options.machine_build_record),SYSTEM_receipt=pin(ex['receipt']),SYSTEM_manifest=pin(ex['manifest']),files=manifest['files'],no_CK3_contact=True)

def observer_argv(exe,meta,raw,ready,machine,case):
    timeout=750 if case=='timeout' else 30000 if case=='foreign4096_limit' else 15000
    argv=[str(exe),'--enable-parent-entry-execution-cold','--admission-meta',str(meta),'--timeout-ms',str(timeout),'--raw',str(raw),'--ready',str(ready),'--machine-id',machine,'--explicit-execution-breakpoint-v1']
    if case=='default-off':argv.remove('--enable-parent-entry-execution-cold')
    if case=='missing-ack':argv.remove('--explicit-execution-breakpoint-v1')
    if case in FAULTS:argv+=['--cold-fault',FAULTS[case]]
    return argv,timeout

def expected_from_meta(meta,machine,timeout):
    return dict(machine_id=machine,synthetic=True,pid=int(meta['pid']),created=int(meta['created']),entry=int(meta['parent_entry']),character=int(meta['character']),full_id=int(meta['full_id']),context=int(meta['context']),local_player_id=int(meta['local_player_id']),game_state=int(meta['game_state']),date_raw=int(meta['date_raw']),absolute_day=int(meta['absolute_day']),foreign_limit=int(meta['foreign_limit']),capture_ms=timeout,admission_id='synthetic-cold',owner_binding=None)

def verify_audit(rows,before,after,refusal=False):
    def key(x):return int(x['tid']),int(x['created'])
    if any(not x.get('complete') or len(x.get('dr',[]))!=6 for x in before+after):raise ValueError('Independent peer audit incomplete')
    baseline={key(x):x for x in before};observed={key(x):x for x in after}
    if len(observed)!=len(after) or len(baseline)!=len(before):raise ValueError('Duplicate TID creation audit')
    arms={};retired=set();unarmed={}
    for row in rows:
        if row.get('kind')=='arm' and row.get('success'):
            ident=(int(row['thread_id']),int(row['thread_generation']));created=int(row['thread_created'])
            if len(row['saved_debug'])!=6 or not row.get('readback'):raise ValueError('Native saved debug vector missing')
            arms[ident]=(created,row['saved_debug'])
        if row.get('kind')=='thread_exited':retired.add((int(row['thread_id']),int(row['thread_generation'])))
        if row.get('kind')=='cleanup_thread_unarmed':
            if not row.get('readback') or len(row.get('debug',[]))!=6:raise ValueError('Cleanup-created unarmed generation is not independently readable')
            unarmed[(int(row['thread_id']),int(row['thread_created']))]=row['debug']
    checked=[]
    for ident,(created,saved) in arms.items():
        if ident in retired:continue
        k=(ident[0],created)
        if k not in observed or observed[k]['dr']!=saved:raise ValueError('Live owned generation missing or its six debug registers drifted')
        if k in baseline and baseline[k]['dr']!=saved:raise ValueError('Original saved vector differs from independent pre-attach audit')
        checked.append(dict(thread_id=ident[0],thread_generation=ident[1],created=created))
    for k,item in baseline.items():
        if k in observed and observed[k]['dr']!=item['dr']:raise ValueError('Independent existing thread debug vector changed')
    if refusal:
        if arms:raise ValueError('Refusal case unexpectedly armed a thread')
    else:
        for k,debug in unarmed.items():
            if k in observed and observed[k]['dr']!=debug:raise ValueError('Cleanup-only unarmed generation changed after detach')
        known=set(baseline)|{(tid,value[0]) for (tid,generation),value in arms.items()}|set(unarmed)
        if set(observed)-known:raise ValueError('Unaudited live thread/generation is not explained by native arm or original census')
    return dict(checked_live_owned_generations=checked,retired_generations=[list(x) for x in sorted(retired)],independent_peer_rows=len(after),all_required_owned_DR_vectors_equal=True)

def assert_zero_arm_refusal(rows,observer_code,ready_exists):
    if type(observer_code) is not int or observer_code not in (1,2) or ready_exists:
        raise ValueError('Expected zero-arm refusal did not occur')
    for row in rows:
        if not isinstance(row,dict):raise ValueError('Unknown refusal diagnostic')
        if row.get('kind') in {'parent_entry','restore','foreign_resume','ready','cleanup_owned_execution'}:
            raise ValueError('Refusal contains execution or mutation evidence')
        if row.get('kind')=='arm':
            vector=row.get('armed_debug')
            if not(row.get('success') is False and row.get('saved_debug')==[] and row.get('readback') is True and
                   isinstance(vector,list) and len(vector)==6 and all(type(x) is int and 0<=x<2**64 for x in vector) and
                   all(type(row.get(k)) is int and row[k]>0 for k in ('thread_id','thread_generation','thread_created'))):
                raise ValueError('Actual, partial or unknown arm cannot pass refusal')

def synthetic_detached_cleanup_proven(rows,meta,identity,observer_closed,observer_waited,machine):
    if observer_closed is not True or observer_waited is not True or not isinstance(meta,dict):return False
    starts=[r for r in rows if r.get('kind')=='start'];terms=[r for r in rows if r.get('kind')=='terminal']
    if len(starts)!=1 or len(terms)!=1 or not rows or rows[-1] is not terms[0]:return False
    s,t=starts[0],terms[0]
    try:
        same=(meta['parent_schema']=='xar.maintenance.parent_entry.cold-meta.v1' and
              s['schema']=='xar.maintenance.parent_entry.raw.v1' and s['mode']=='parent-entry-execution-once-v1' and
              s['machine_id']==machine and s['synthetic'] is True and 'owner_binding' in s and s['owner_binding'] is None and
              int(s['pid'])==int(meta['pid'])==identity['pid'] and int(s['created'])==int(meta['created'])==identity['created'] and
              int(s['entry'])==int(meta['parent_entry']))
    except (KeyError,TypeError,ValueError):return False
    return same and all(t.get(k) is True for k in ('restored','detached','cleanup_complete')) and t.get('pending_event') is False

def run_case(options,case,machine,gate,win):
    from parent_entry_execution_contract import normalize_rows
    out=options.output_root/case;out.mkdir(exist_ok=False);prefix=out/'target';raw=out/'observer.raw.ndjson';ready=out/'READY.actual.json'
    target_mode='foreign257_then_target' if case in FAULTS else 'timeout' if case in {'default-off','missing-ack','bad-schema'} else case
    ta=[str(options.build_dir/'maintenance_parent_entry_cold_target.exe'),'--mode',target_mode,'--prefix',str(prefix)]
    handles=[];waited=set();owned={};target=observer=None;meta=None;rows=[];released=False;target_audited=False;fault_released=False;error=None
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',GIT_OPTIONAL_LOCKS='0',TEMP=str(out),TMP=str(out))
    def spawn(label,argv):
        write(out/(label+'.INTENT.json'),dict(machine_id=machine,observed_at_utc=now(),argv=argv,gate=gate,synthetic_only=True))
        so=(out/(label+'.stdout.log')).open('xb');se=(out/(label+'.stderr.log')).open('xb');handles.extend([so,se])
        # Ownership is registered before identity/readback/receipt operations.
        # A failure in any of those operations must not lose the Popen handle.
        owned[label]=subprocess.Popen(argv,stdout=so,stderr=se,env=env);p=owned[label];ident=win.identity(p)
        write(out/(label+'.POPEN.actual.json'),dict(machine_id=machine,observed_at_utc=now(),argv=argv,**ident));return p
    def original_wait(label,p):
        if label in waited:return p.returncode
        code=p.wait();write(out/(label+'.ORIGINAL-WAIT.actual.json'),dict(machine_id=machine,observed_at_utc=now(),original_Popen=True,original_wait=True,exit_code=code,**win.identity(p)));waited.add(label);return code
    def wait_file(p,seconds=5):
        until=time.monotonic()+seconds
        while not p.exists():
            if target is not None and target.poll() is not None:raise RuntimeError('Synthetic target exited before '+p.name)
            if time.monotonic()>until:raise TimeoutError(p.name)
            time.sleep(.01)
        return p
    def hold(reason,process):
        nonlocal fault_released
        def notify(value):
            try:print(value,flush=True)
            except BaseException:pass
        hp=out/'UNRESOLVED-OWNER-HOLD.actual.json'
        try:
            if not hp.exists():write(hp,dict(machine_id=machine,observed_at_utc=now(),reason=reason,pid=process.pid,original_Popen_retained=True,cleanup_complete=False,no_forced_detach_or_terminate=True))
        except BaseException:pass # Receipt failure never relinquishes the owner.
        notify(json.dumps(dict(case=case,status='UNRESOLVED_OWNER_HOLD',reason=reason,pid=process.pid)))
        # Deliberately retain ownership. Parent orchestration must arrange legal
        # cleanup/release; neither deadline nor a test exception permits abandon.
        hold_error_reported=False
        while True:
            try:
                if process.poll() is not None:break
                if process is owned.get('observer') and case in FAULTS and meta is not None and not fault_released:
                    current=raw_rows(raw)
                    if any(x.get('kind')=='unresolved_cleanup_hold' for x in current):
                        # The same explicit cold seam remains serviceable during
                        # failure cleanup. This permits cleanup only, no capture.
                        win.event(meta['fault_release_event']);fault_released=True
                        try:write(out/'FAULT-RELEASE-DURING-OWNER-CLEANUP.actual.json',dict(machine_id=machine,observed_at_utc=now(),observer_pid=process.pid,raw_prefix=pin(raw),fault=FAULTS[case],cleanup_only=True,real_OS_fault_proven=False))
                        except OSError as e:notify('Fault released; cleanup receipt write failed: '+repr(e))
                if process is owned.get('observer') and meta is not None:
                    win.event(meta['cancel_event']) # Same idempotent cleanup request only.
                process.wait(timeout=1)
            except (subprocess.TimeoutExpired,KeyboardInterrupt):continue
            except BaseException as e:
                if not hold_error_reported:
                    notify('Owned cleanup hold retained despite read/release failure: '+repr(e));hold_error_reported=True
                time.sleep(1)
    def finish_target(refusal=False):
        nonlocal target_audited,released
        if target is None:return None
        if target.poll() is not None:return original_wait('target',target)
        if not ready.exists():win.event(meta['cancel_event'])
        win.event(meta['audit_event'])
        try:
            after=load_complete(wait_file(Path(str(prefix)+'.after-debug.json'),5));before=load_complete(Path(str(prefix)+'.initial-debug.json'))
            audit=verify_audit(rows,before,after,refusal)
            if case=='occupied-tf':
                # Main thread creation differs from process creation. Bind the
                # main TID first, then require the same independently read birth.
                first=next((r for r in before if int(r['tid'])==int(meta['tid'])),None)
                last=next((r for r in after if first and int(r['tid'])==int(first['tid']) and int(r['created'])==int(first['created'])),None)
                if first is None or last is None or not(int(first['eflags'])&0x100) or not(int(last['eflags'])&0x100):raise ValueError('Pre-existing TF was not independently preserved before target-owned release')
                audit['independent_preexisting_TF_preserved_before_target_release']=True
            write(out/'INDEPENDENT-DR-AUDIT.actual.json',dict(machine_id=machine,observed_at_utc=now(),before=before,after=after,**audit));target_audited=True
        except BaseException as exc:
            write(out/'INDEPENDENT-DR-AUDIT-FAILED.actual.json',dict(machine_id=machine,observed_at_utc=now(),error=repr(exc),qualified=False,before=before if 'before' in locals() else None,after=after if 'after' in locals() else None))
            if synthetic_detached_cleanup_proven(rows,meta,win.identity(target),observer is not None and observer.poll() is not None,'observer' in waited,machine):
                # Normal end of this exact private fixture only. The failed six-DR
                # audit remains failed; never release an unknown debugger/restore.
                win.event(meta['finish_event']);released=True
                until=time.monotonic()+5
                while target.poll() is None and time.monotonic()<until:time.sleep(.01)
                if target.poll() is None:hold('Failed synthetic audit: original Finish did not close target',target)
                original_wait('target',target)
                raise
            hold('Independent restoration proof failed: '+repr(exc),target);raise
        win.event(meta['finish_event']);released=True
        until=time.monotonic()+5
        while target.poll() is None and time.monotonic()<until:time.sleep(.01)
        if target.poll() is None:hold('Audited target did not finish; no forced termination',target)
        return original_wait('target',target)
    try:
        target=spawn('target',ta);mp=wait_file(Path(str(prefix)+'.meta.txt'));meta_until=time.monotonic()+5
        while True:
            try:
                meta=read_meta(mp)
                if not {'pid','created','parent_entry','clock_pointer','absolute_day','fault_release_event'}<=set(meta):raise ValueError('Metadata publication incomplete')
                break
            except (ValueError,UnicodeDecodeError):
                if time.monotonic()>meta_until:raise
                time.sleep(.01)
        if int(meta['pid'])!=target.pid or int(meta['created'])!=win.identity(target)['created']:raise ValueError('Metadata does not bind retained original target Popen')
        wait_file(Path(str(prefix)+'.initial-debug.json'))
        selected=mp
        if case=='bad-schema':
            selected=out/'BAD-SCHEMA.meta.txt';selected.write_text(mp.read_text().replace(meta['parent_schema'],'wrong-parent-schema'),encoding='ascii')
        oa,timeout=observer_argv(options.build_dir/'maintenance_parent_entry_observer.exe',selected,raw,ready,machine,case)
        observer=spawn('observer',oa);until=time.monotonic()+timeout/1000+15;go=False;cancelled=False
        while observer.poll() is None:
            rows=raw_rows(raw)
            if ready.exists() and not go:
                value=load_complete(ready)
                if value.get('ready') is not True or value.get('mode')!='parent-entry-execution-once-v1' or value.get('census_complete') is not True:raise ValueError('Native READY does not prove owned initial generation census')
                if case in REFUSALS:raise ValueError('Refusal unexpectedly published READY')
                write(out/'READY-GO.actual.json',dict(machine_id=machine,observed_at_utc=now(),native_READY=pin(ready),target_meta=pin(mp),target_original_Popen=win.identity(target)));win.event(meta['go_event']);go=True
            if case=='cancel_late' and not cancelled and any(x.get('kind')=='foreign_resume' for x in rows):
                win.event(meta['cancel_event']);cancelled=True;write(out/'CANCEL-AFTER-ACTUAL-FOREIGN.actual.json',dict(machine_id=machine,observed_at_utc=now(),raw_prefix=pin(raw),trigger='actual native foreign_resume record'))
            if case in FAULTS and not fault_released and any(x.get('kind')=='unresolved_cleanup_hold' for x in rows):
                if observer.poll() is not None:raise ValueError('Fault did not retain original debugger Popen')
                write(out/'ACTUAL-NATIVE-FAULT-HOLD.actual.json',dict(machine_id=machine,observed_at_utc=now(),fault=FAULTS[case],observer_original_Popen=win.identity(observer),target_original_Popen=win.identity(target),raw_prefix=pin(raw),injected_native_API_seam=True,real_OS_fault_proven=False))
                win.event(meta['fault_release_event']);fault_released=True
            if time.monotonic()>until:
                win.event(meta['cancel_event']);hold('Observer did not close within finite capture; original debugger remains owned',observer)
            time.sleep(.005)
        observer_code=original_wait('observer',observer);rows=raw_rows(raw,True)
        if case in REFUSALS:
            assert_zero_arm_refusal(rows,observer_code,ready.exists())
            win.event(meta['cancel_event']);normalized=None
        else:
            expected_code=1 if case in PARTIAL_REASONS else 0
            if observer_code!=expected_code or not go:raise ValueError('Unexpected native exit for this exact qualified/partial case')
            normalized=normalize_rows(rows,expected_from_meta(meta,machine,timeout))
            if case in PARTIAL_REASONS and normalized['reason']!=PARTIAL_REASONS[case]:raise ValueError('Nonzero exit has the wrong typed partial reason')
        target_code=finish_target(case in REFUSALS)
        result=load_complete(Path(str(prefix)+'.result.json'))
        if target_code!=0 or result['return_failures'] or result['audit_failures']:raise ValueError('Original declared function/return or independent audit failed')
        expected_counts=(257,1) if case=='foreign257_then_target' or case in FAULTS else (4096,1) if case in {'foreign4096_limit','cancel_late'} else (0,0) if case=='timeout' or case in REFUSALS else (0,1)
        if (result['foreign_body_calls'],result['target_body_calls'])!=expected_counts or result['actual_body_calls']!=sum(expected_counts):raise ValueError('Original synthetic function did not execute each actual call exactly once')
        if normalized is not None:
            if not normalized['cleanup_complete']:raise ValueError('Incomplete cleanup cannot be a cold pass')
            if case=='foreign257_then_target' and (normalized['foreign_count']!=257 or not normalized['target_entry_qualified']):raise ValueError('Repeated RF continuation or final target not proven')
            if case=='foreign4096_limit' and (normalized['foreign_count']!=4096 or normalized['target_entry_retained']):raise ValueError('4096 cap must remain partial before later unobserved target')
            if case=='foreign4096_limit' and normalized['reason']!='foreign_limit':raise ValueError('Cap case did not close at its actual foreign limit')
            if case=='timeout' and (normalized['reason']!='timeout' or normalized['foreign_count'] or normalized['target_entry_retained']):raise ValueError('No-hit timeout did not remain an incomplete zero-hit window')
            if case in {'created_thread','context-drift'} and not normalized['target_entry_qualified']:raise ValueError('Real new-thread/context-drift owner entry missing')
            if case=='context-drift' and normalized['admitted_context_unchanged'] is not False:raise ValueError('Context drift hidden by pre-filter')
            if case in {'fullid-drift','magic-drift','session-drift'} and (not normalized['target_entry_retained'] or normalized['target_entry_qualified']):raise ValueError('Input drift must retain pointer diagnostic without false owner join')
            if case in FAULTS and not fault_released:raise ValueError('Native fault/retained-owner/release path was not actually reached')
            if case=='cancel_late':
                late=[x for x in rows if x.get('owned_late_event') is True]
                if not cancelled or not late or normalized['target_entry_retained']:raise ValueError('Cancel/late-owned timing not actually witnessed; no retry or synthetic PASS')
            if case=='created_thread':
                arms={int(x['thread_id']) for x in rows if x.get('kind')=='arm' and x.get('success')}
                if not result['worker_tid'] or result['worker_tid'] not in arms:raise ValueError('Worker created after READY was not actually armed')
        write(out/'CASE.actual.json',dict(schema='xar.maintenance.parent_entry.cold.case.v1',machine_id=machine,observed_at_utc=now(),status='PASS',case=case,actual_target_result=result,native_consumer=normalized,raw=pin(raw) if raw.exists() else None,target_original_exit=target_code,observer_original_exit=observer_code,independent_audit=pin(out/'INDEPENDENT-DR-AUDIT.actual.json'),actual_debugger_fault_injected=case in FAULTS,real_OS_failure_proven=False,real_CK3=False,parent_return_observed=False,full_R08=False))
    except BaseException as exc:
        error=repr(exc)
        target=target or owned.get('target');observer=observer or owned.get('observer')
        if meta is not None:
            if observer is not None and observer.poll() is None:
                win.event(meta['cancel_event']);hold('Case failure requires native cleanup before return: '+error,observer)
            if observer is not None:original_wait('observer',observer)
            rows=raw_rows(raw,True)
            if target is not None and not released:finish_target(case in REFUSALS)
        elif target is not None and target.poll() is None:hold('Target startup metadata missing; retained target owner: '+error,target)
        if target is not None and target.poll() is not None:original_wait('target',target)
        write(out/'FAILED.actual.json',dict(machine_id=machine,observed_at_utc=now(),error=error,automatic_replay=False,original_owners_preserved=True,target_audited=target_audited,qualified=False));raise
    finally:
        # Cleanup code can itself fail (cancel/read/receipt/disk error). The
        # registry remains authoritative; no live original is GC-abandoned.
        for label in ('observer','target'):
            p=owned.get(label)
            if p is None:continue
            try:alive=p.poll() is None
            except BaseException:alive=True
            if alive:
                hold('Final ownership backstop after incomplete case cleanup: '+label,p)
            # Also consume the actual original Popen after an inner hold already
            # observed its exit. A new handle/current absence is never a wait.
            try:original_wait(label,p)
            except BaseException as wait_error:
                try:write(out/(label+'.WAIT-RECEIPT-ERROR.actual.json'),dict(machine_id=machine,observed_at_utc=now(),error=repr(wait_error),original_wait_receipt_missing=True,qualified=False))
                except BaseException:pass
        if error is not None and not (out/'FAILED.actual.json').exists():
            write(out/'FAILED.actual.json',dict(machine_id=machine,observed_at_utc=now(),error=error,cleanup_exception=repr(sys.exc_info()[1]),automatic_replay=False,qualified=False,target_audited=target_audited))
        for h in handles:h.close()
    return pin(out/'CASE.actual.json')

def main(argv=None):
    options=parser().parse_args(argv);selected=select_cases(options.case)
    if not options.execute_qualified_cold:raise ValueError('Source-only preparation is not native execution admission')
    options.repo=options.repo.resolve();options.build_dir=options.build_dir.resolve();options.output_root=options.output_root.resolve()
    if options.output_root.exists():raise ValueError('New output root required; original cases cannot be rewritten')
    python=options.repo/'tools/.venv/Scripts/python.exe';machine=subprocess.check_output([str(python),'-B','-X','utf8',str(options.repo/'tools/ck3_live_run_id.py'),'machine'],text=True).strip()
    gate=verify_build(options,machine);options.output_root.mkdir(parents=True)
    write(options.output_root/'EXACT-SYSTEM-GATE.actual.json',gate)
    win=Windows();results=[]
    for case in selected:results.append(run_case(options,case,machine,gate,win))
    write(options.output_root/'SELECTED-COLD.actual.json',dict(schema='xar.maintenance.parent_entry.cold.suite.v1',mode='parent-entry-execution-once-v1',status='SELECTED_CASES_COMPLETED_NOT_QUALIFICATION',execution_DR_qualified=False,machine_id=machine,observed_at_utc=now(),selected_cases=selected,cases=results,Root_required_cases_qualification_not_self_issued=True,real_CK3=False,paid_maintenance_raw=None,payer=None,cadence=None,full_R08=False))
    return 0
if __name__=='__main__':raise SystemExit(main())
