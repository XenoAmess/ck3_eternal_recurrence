"""Controlled sibling process only. Gate both project EXEs before first execution."""
from pathlib import Path
import argparse, ctypes, datetime as dt, hashlib, json, subprocess, sys, time
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--repo', type=Path, required=True)
parser.add_argument('--build-dir', type=Path, required=True)
parser.add_argument('--machine-build-record',type=Path,required=True)
parser.add_argument('--output-root', type=Path, required=True)
args = parser.parse_args()
REPO = args.repo.resolve()
BUILD = args.build_dir.resolve()
OUT = args.output_root.resolve()
PYTHON = REPO / 'tools/.venv/Scripts/python.exe'
MACHINE = subprocess.check_output([str(PYTHON), '-B', str(REPO / 'tools/ck3_live_run_id.py'), 'machine'], text=True).strip()

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def write(p, v):
    Path(p).write_text(json.dumps(v, indent=2) + '\n', encoding='utf-8')

def gate():
    current_machine = subprocess.check_output([str(PYTHON), '-B', str(REPO / 'tools/ck3_live_run_id.py'), 'machine'], text=True).strip()
    if not current_machine == MACHINE:
        raise RuntimeError('Exact SYSTEM/build gate rejected')
    result = json.loads((BUILD / 'native-msvc-result.json').read_text())
    machine_record=json.loads(args.machine_build_record.read_bytes())
    if machine_record['machine_id']!=current_machine or machine_record['returncode']!=0:
        raise RuntimeError('Current host machine-labelled successful build record missing')
    if str(BUILD) not in machine_record['argv']:
        raise RuntimeError('Machine build record bound to another output path')
    if Path(result['source_dir'])!=Path(machine_record['source_pins'][0]['path']).parent:
        raise RuntimeError('Source/build identity changed')
    for source_pin in machine_record['source_pins']:
        path=Path(source_pin['path'])
        if path.stat().st_size!=source_pin['bytes'] or sha(path)!=source_pin['sha256']:
            raise RuntimeError('Machine build source pin differs')

    exclusion = result['defender_exclusions']
    receipt_path = Path(exclusion['receipt'])
    receipt = json.loads(receipt_path.read_text())
    manifest_path = Path(exclusion['manifest'])
    manifest = json.loads(manifest_path.read_text())
    if not (result['built'] and exclusion['status'] == 'verified'):
        raise RuntimeError('Exact SYSTEM/build gate rejected')
    if not sha(receipt_path) == exclusion['receipt_sha256']:
        raise RuntimeError('Exact SYSTEM/build gate rejected')
    if not (receipt['status'] == 'verified' and receipt['admin_token'] is True):
        raise RuntimeError('Exact SYSTEM/build gate rejected')
    if not receipt['system_token_sid'] == 'S-1-5-18':
        raise RuntimeError('Exact SYSTEM/build gate rejected')
    if not receipt['manifest_sha256'] == hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest():
        raise RuntimeError('Exact SYSTEM/build gate rejected')
    if not receipt['missing_requested_paths'] == []:
        raise RuntimeError('Exact SYSTEM/build gate rejected')
    if not {Path(x['path']).name for x in manifest['files']} == {'maintenance_writer_cold_target.exe', 'maintenance_writer_cold_observer.exe'}:
        raise RuntimeError('Exact SYSTEM/build gate rejected')
    files = []
    for item in manifest['files']:
        p = Path(item['path'])
        if not p.parent == BUILD:
            raise RuntimeError('Exact SYSTEM/build gate rejected')
        if not str(p) in receipt['verified_requested_paths']:
            raise RuntimeError('Exact SYSTEM/build gate rejected')
        if not (p.stat().st_size == item['size'] and sha(p) == item['sha256']):
            raise RuntimeError('Exact SYSTEM/build gate rejected')
        if not any((x['path'] == str(p) and x['sha256'] == item['sha256'] for x in receipt['files'])):
            raise RuntimeError('Exact SYSTEM/build gate rejected')
        files.append(item)
    for pin in receipt['input_pins']:
        if not sha(pin['path']) == pin['sha256']:
            raise RuntimeError('Exact SYSTEM/build gate rejected')
    return {'machine_id': MACHINE, 'observed_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'status': 'verified-before-first-project-EXE-execution', 'receipt': str(receipt_path), 'receipt_sha256': sha(receipt_path), 'manifest_file_sha256': sha(manifest_path), 'manifest_canonical_sha256': receipt['manifest_sha256'], 'system_token_sid': receipt['system_token_sid'], 'admin_token': True, 'files': files, 'game_contacted': False}
kernel = ctypes.WinDLL('kernel32', use_last_error=True)
kernel.OpenEventW.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_wchar_p]
kernel.OpenEventW.restype = ctypes.c_void_p
kernel.SetEvent.argtypes = [ctypes.c_void_p]
kernel.SetEvent.restype = ctypes.c_int
kernel.CloseHandle.argtypes = [ctypes.c_void_p]
kernel.CloseHandle.restype = ctypes.c_int
kernel.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
kernel.OpenProcess.restype = ctypes.c_void_p
kernel.ReadProcessMemory.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
kernel.ReadProcessMemory.restype = ctypes.c_int
kernel.CheckRemoteDebuggerPresent.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)]
kernel.CheckRemoteDebuggerPresent.restype = ctypes.c_int

def presence_query(meta):
    checks = []
    for label, rights in [('prior_limited_query', 4114), ('fixed_query_information', 5138)]:
        h = kernel.OpenProcess(rights, False, int(meta['pid']))
        if not h:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            detected = ctypes.c_int(-1)
            ctypes.set_last_error(0)
            ok = bool(kernel.CheckRemoteDebuggerPresent(h, ctypes.byref(detected)))
            checks.append({'handle_rights': hex(rights), 'label': label, 'api_return_success': ok, 'last_error': ctypes.get_last_error(), 'debugger_present': bool(detected.value) if ok else None})
        finally:
            kernel.CloseHandle(h)
    if not (not checks[0]['api_return_success'] and checks[0]['last_error'] == 5):
        raise RuntimeError(checks)
    if not (checks[1]['api_return_success'] and (not checks[1]['debugger_present'])):
        raise RuntimeError(checks)
    return {'machine_id': MACHINE, 'observed_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'pid': int(meta['pid']), 'process_created_filetime': int(meta['created']), 'scope': 'read-only API checks on controlled synthetic target before observer attach', 'checks': checks}

def owned_site_bytes(meta):
    h = kernel.OpenProcess(4112, False, int(meta['pid']))
    if not h:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        result = []
        for key, n, expected in [('site0', 3, '0150f4'), ('site1', 6, '8b48f43b48f0')]:
            buf = ctypes.create_string_buffer(n)
            actual = ctypes.c_size_t()
            if not kernel.ReadProcessMemory(h, int(meta[key]), buf, n, ctypes.byref(actual)) or actual.value != n:
                raise ctypes.WinError(ctypes.get_last_error())
            b = buf.raw
            if not b.hex() == expected:
                raise RuntimeError('Exact SYSTEM/build gate rejected')
            result.append({'synthetic_site_address': int(meta[key]), 'bytes': n, 'hex': b.hex(), 'sha256': hashlib.sha256(b).hexdigest()})
        return {'machine_id': MACHINE, 'observed_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'source': 'ReadProcessMemory of owned synthetic sibling target before debugger attach', 'pid': int(meta['pid']), 'process_created_filetime': int(meta['created']), 'CK3_binary_read': False, 'sites': result}
    finally:
        kernel.CloseHandle(h)

def signal(name):
    h = kernel.OpenEventW(2, False, name)
    if not h:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        if not kernel.SetEvent(h):
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        kernel.CloseHandle(h)

def wait_file(p, proc, timeout=10):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if p.exists() and p.stat().st_size:
            try:
                return p.read_text(encoding='utf-8')
            except PermissionError:
                pass
        if proc.poll() is not None:
            raise RuntimeError(f'{p.name} missing, process exited {proc.returncode}')
        time.sleep(0.02)
    raise TimeoutError(str(p))

def read_json(p, proc):
    end = time.monotonic() + 10
    while True:
        try:
            return json.loads(wait_file(p, proc))
        except json.JSONDecodeError:
            if time.monotonic() > end:
                raise
            time.sleep(0.02)

def require(ok,message):
    if not ok:raise RuntimeError(message)
def source_bytes(meta):
    h=kernel.OpenProcess(0x1010,False,int(meta['pid']))
    if not h:raise ctypes.WinError(ctypes.get_last_error())
    try:
        buffer=ctypes.create_string_buffer(4);n=ctypes.c_size_t()
        require(bool(kernel.ReadProcessMemory(h,int(meta['writer_start']),buffer,4,ctypes.byref(n))) and n.value==4,'Synthetic writer source read failed')
        require(buffer.raw.hex()=='488911c3','Actual synthetic writer differs from3B MOV+RET')
        require(int(meta['writer_after'])==int(meta['writer_start'])+3,'Actual fixture poststore label differs')
        return dict(bytes=4,raw_hex=buffer.raw.hex(),sha256=hashlib.sha256(buffer.raw).hexdigest(),actual_writer_start=int(meta['writer_start']),actual_RIP_after=int(meta['writer_after']),source='Owned sibling target actual4B only; never CK3')
    finally:kernel.CloseHandle(h)
def run_case(mode):
    case=OUT/mode;case.mkdir(exist_ok=False);prefix=case/'target'
    target_argv=[str(BUILD/'maintenance_writer_cold_target.exe'),'--mode',mode,'--prefix',str(prefix)]
    with (case/'target.stdout').open('xb') as tso,(case/'target.stderr').open('xb') as tse:
        target=subprocess.Popen(target_argv,stdout=tso,stderr=tse,creationflags=0x08000000)
        observer=None;meta={}
        try:
            meta=dict(line.split('=',1) for line in wait_file(Path(str(prefix)+'.meta.txt'),target).splitlines())
            require(int(meta['pid'])==target.pid,'Owned PID mismatch')
            write(case/'owned-writer-source.actual.json',source_bytes(meta))
            original_meta=dict(meta);selected=Path(str(prefix)+'.meta.txt')
            if mode in ('unaligned','wrong-fullid'):
                meta=dict(meta);key='context' if mode=='unaligned' else 'full_id';meta[key]=str(int(meta[key])+1)
                selected=case/'invalid.meta.txt';selected.write_text(''.join(k+'='+v+'\n' for k,v in meta.items()),encoding='utf-8')
            raw=case/'observer.raw.ndjson';ready=case/'observer.ready.json'
            observer_argv=[str(BUILD/'maintenance_writer_cold_observer.exe')]
            if mode!='default-off':observer_argv+=['--enable-cold-fixture','--fixture-meta',str(selected),'--timeout-ms','1000' if mode=='timeout' else '5000','--raw',str(raw),'--ready',str(ready),'--expected-hits','4','--machine-id',MACHINE]
            negative=mode in ('default-off','unaligned','wrong-fullid')
            with (case/'observer.stdout').open('xb') as oso,(case/'observer.stderr').open('xb') as ose:
                observer=subprocess.Popen(observer_argv,stdout=oso,stderr=ose,creationflags=0x08000000)
                ready_json=None
                if not negative:
                    ready_json=read_json(ready,observer)
                    require(ready_json['ready'] is True and ready_json['armed_thread_count']>=2,'All existing fixture writer/auditor threads not armed')
                    if mode!='timeout':signal(original_meta['go_event'])
                observer_code=observer.wait(timeout=15)
            rows=[json.loads(x) for x in raw.read_text().splitlines()] if raw.exists() else []
            terminal=next((x for x in rows if x.get('kind')=='terminal'),None)
            if negative:
                require(observer_code==2 and not rows and not ready.exists(),'Default/invalid admission did not reject before attach')
            else:
                require(terminal is not None and terminal['cleanup_complete'] is True and terminal['restored'] is True and terminal['detached'] is True and terminal['pending_event'] is False,'Native restore/detach not proved')
                expected='timeout' if mode=='timeout' else 'context_identity_changed' if mode=='changed-context' else 'complete'
                require(terminal['reason']==expected and observer_code==(0 if expected=='complete' else 1),'Wrong native terminal reason/code')
                require(terminal['observation_thread_admission_complete'] is True,'Observation thread admission incomplete')
            if mode=='timeout' or negative:signal(original_meta['go_event'])
            target_result=read_json(Path(str(prefix)+'.writes.json'),target)
            signal(original_meta['audit_event'])
            before=read_json(Path(str(prefix)+'.initial-debug.json'),target);after=read_json(Path(str(prefix)+'.after-debug.json'),target)
            require(len(before)==1 and before[0]['ok'] is True and after[0]==before[0],'Independent original main DR restoration differs')
            arms={x['thread_id']:x for x in rows if x.get('kind')=='arm' and x['success'] is True}
            restores={x['thread_id']:x for x in rows if x.get('kind')=='restore'}
            exited={x['thread_id'] for x in rows if x.get('kind')=='thread_exited'}
            if not negative:
                for tid,arm in arms.items():
                    require(len(arm['saved_debug'])==6,'Missing original DR state')
                    require(arm['armed_debug'][:4]==[int(original_meta['context'])+x for x in (704,712,40,48)],'Wrong four exact DR addresses')
                    require(arm['armed_debug'][5]&0xffff00ff==0x99990055,'Wrong DR7 RW/LEN/local enable bits')
                    if tid not in exited:
                        require(tid in restores and restores[tid]['readback'] is True and restores[tid]['debug']==arm['saved_debug'],'Per-live-thread exact restore differs')
                for audit in after:
                    require(audit['ok'] is True and audit['thread_id'] in arms and audit['debug']==arms[audit['thread_id']]['saved_debug'],'Independent post-target DR differs from saved state')
            hits=[x for x in rows if x.get('kind')=='raw_field_write_trap']
            positive=mode in ('correct-character-base-abi','same-value','new-worker')
            require(len(hits)==(4 if positive else 0),'Unexpected observed field count')
            if positive:
                require({x['offset'] for x in hits}=={704,712,40,48},'Not all four fields actually trapped')
                for hit in hits:
                    require(hit['writer_instruction_start'] is None and hit['RIP_after']==int(original_meta['writer_after']),'Post-store RIP must not be forged into instruction_start')
                    require(hit['before_basis']=='last_observed_sample_not_atomic_preinstruction' and hit['after_read_complete'] is True and hit['context_identity_stable'] is True,'Raw value basis/completeness differs')
                    require(hit['known_producer'] is False and hit['military_attribution']=='unclosed' and hit['synthetic'] is True,'Cold data promoted to game producer')
                if mode=='same-value':require(all(x['same_value_write'] is True and x['before_raw']==x['after_raw'] for x in hits),'Same-value physical writes were lost')
                if mode=='new-worker':
                    tid=target_result['worker_tid'];require(tid!=int(original_meta['tid']) and tid in arms and all(x['thread_id']==tid for x in hits),'Actual new worker coverage absent')
                    require(len(after)==2,'New worker must remain alive for independent post-DR audit')
            expected_store_count=0 if mode in ('timeout','default-off') else 4
            require(target_result['actual_store_count']==expected_store_count,'Target did not execute exact intended native store count')
            signal(original_meta['finish_event']);target_code=target.wait(timeout=5);require(target_code==0,'Target exit not clean')
            result=dict(schema='xar.maintenance.writer_pc.cold.case.v1',machine_id=MACHINE,actual_utc=dt.datetime.now(dt.timezone.utc).isoformat(),mode=mode,status='PASS',synthetic=True,CK3_observed=False,maintenance_attribution='unclosed',target_argv=target_argv,observer_argv=observer_argv,target_exit_code=target_code,observer_exit_code=observer_code,actual_target_result=target_result,actual_raw_slot_hits=len(hits),native_terminal=terminal,ready=ready_json,independent_DR_before=before,independent_DR_after=after,exact_main_DR_equal=True,raw_sha256=sha(raw) if raw.exists() else None,raw_bytes=raw.stat().st_size if raw.exists() else 0)
            write(case/'RESULT.actual.json',result)
            print(json.dumps(dict(mode=mode,status='PASS',hits=len(hits),observer=observer_code)),flush=True)
            return result
        except BaseException as error:
            write(case/'FAILURE.actual.json',dict(mode=mode,error=repr(error),target_pid=target.pid,observer_pid=None if observer is None else observer.pid,target_status=target.poll(),observer_status=None if observer is None else observer.poll()))
            if observer is not None and observer.poll() is None:
                try:observer.wait(timeout=15)
                except subprocess.TimeoutExpired:pass
            for key in ('go_event','audit_event','finish_event'):
                if key in meta:
                    try:signal(meta[key])
                    except OSError:pass
            try:target.wait(timeout=35)
            except subprocess.TimeoutExpired:pass
            raise
original_source_bytes=source_bytes
def source_bytes(meta):
    result=original_source_bytes(meta)
    h=kernel.OpenProcess(0x1010,False,int(meta['pid']))
    if not h:raise ctypes.WinError(ctypes.get_last_error())
    try:
        buf=ctypes.create_string_buffer(16);n=ctypes.c_size_t()
        require(bool(kernel.ReadProcessMemory(h,int(meta['character'])+0x10,buf,16,ctypes.byref(n))) and n.value==16,'Owned Character ABI read failed')
        import struct
        old_id,old_magic,actual_id,actual_magic=struct.unpack('<IIII',buf.raw)
        require(old_id==old_magic==0 and actual_id==31254 and actual_magic==0x43686172,'Synthetic Character must match source-bound+18/+1C and refute+10/+14')
        result['actual_Character_ABI']=dict(base=int(meta['character']),observed_10=old_id,observed_14=old_magic,observed_18=actual_id,observed_1c=actual_magic,source='dcda existing production Frame and cash ActorMatches; target has actual current ABI')
        return result
    finally:kernel.CloseHandle(h)
def stale_case():
    mode='stale-tid-occupied';case=OUT/mode;case.mkdir(exist_ok=False);prefix=case/'target';meta={};observer=None
    argv=[str(BUILD/'maintenance_writer_cold_target.exe'),'--mode',mode,'--prefix',str(prefix)]
    with (case/'target.stdout').open('xb') as so,(case/'target.stderr').open('xb') as se:
        target=subprocess.Popen(argv,stdout=so,stderr=se,creationflags=0x08000000)
        try:
            meta=dict(line.split('=',1) for line in wait_file(Path(str(prefix)+'.meta.txt'),target).splitlines())
            require(int(meta['pid'])==target.pid and meta['cold_stale_tid_guard']=='1','Explicit cold stale seam absent')
            write(case/'owned-Character-ABI.actual.json',source_bytes(meta))
            raw=case/'observer.raw.ndjson';ready=case/'observer.ready.json'
            command=[str(BUILD/'maintenance_writer_cold_observer.exe'),'--enable-cold-fixture','--fixture-meta',str(prefix)+'.meta.txt','--timeout-ms','5000','--raw',str(raw),'--ready',str(ready),'--expected-hits','4','--machine-id',MACHINE]
            with (case/'observer.stdout').open('xb') as oso,(case/'observer.stderr').open('xb') as ose:
                observer=subprocess.Popen(command,stdout=oso,stderr=ose,creationflags=0x08000000)
                code=observer.wait(timeout=15)
            rows=[json.loads(line) for line in raw.read_text().splitlines()]
            arm=next(x for x in rows if x['kind']=='arm');terminal=rows[-1]
            require(code==1 and terminal['kind']=='terminal' and terminal['reason']=='cannot_arm_existing_thread','Actual occupied current thread not refused')
            require(arm['cold_stale_map_seeded'] is True and arm['prior_saved_entry_erased'] is True and arm['success'] is False and arm['saved_debug']==[],'Old generation state was not retired before rejection')
            require(arm['armed_debug'][0]==0x12345000 and not any(x['kind']=='restore' and x['thread_id']==arm['thread_id'] for x in rows),'Old stale DR was applied to unowned new generation')
            require(terminal['cleanup_complete'] is True and terminal['restored'] is True and terminal['detached'] is True and terminal['pending_event'] is False and terminal['hit_count']==0 and terminal['observation_thread_admission_complete'] is False,'Refusal cleanup/detach boundary failed')
            require(not ready.exists(),'Refused occupied thread incorrectly admitted ready')
            signal(meta['go_event']);actual=read_json(Path(str(prefix)+'.writes.json'),target);require(actual['actual_store_count']==4,'Owned target normal stores did not complete after refusal')
            signal(meta['audit_event']);before=read_json(Path(str(prefix)+'.initial-debug.json'),target);after=read_json(Path(str(prefix)+'.after-debug.json'),target)
            require(before==after and before[0]['ok'] is True and before[0]['debug'][0]==0x12345000,'Actual occupied original DR state was changed')
            signal(meta['finish_event']);target_code=target.wait(timeout=5);require(target_code==0,'Owned target exit failed')
            result=dict(schema='xar.maintenance.writer_pc.stale_generation_counterexample.v1',status='PASS',mode=mode,machine_id=MACHINE,actual_utc=dt.datetime.now(dt.timezone.utc).isoformat(),cold_stale_map_fault_injection=True,actual_OS_TID_reuse_claimed=False,actual_owned_thread_occupied_DR=True,native_saved_old_state_refused=True,independent_target_DR_before=before,independent_target_DR_after=after,exact_DR_equal=True,target_result=actual,target_exit_code=target_code,observer_exit_code=code,native_terminal=terminal,raw_sha256=sha(raw),target_argv=argv,observer_argv=command,CK3_observed=False,known_producer=False,military_attribution='unclosed')
            write(case/'RESULT.actual.json',result);print(json.dumps(dict(mode=mode,status='PASS',old_state_not_applied=True,detached=True)),flush=True);return result
        except BaseException as error:
            write(case/'FAILURE.actual.json',dict(error=repr(error),target_pid=target.pid,observer_pid=None if observer is None else observer.pid,target_status=target.poll(),observer_status=None if observer is None else observer.poll()))
            if observer is not None and observer.poll() is None:
                try:observer.wait(timeout=15)
                except subprocess.TimeoutExpired:pass
            for key in ['go_event','audit_event','finish_event']:
                if key in meta:
                    try:signal(meta[key])
                    except OSError:pass
            try:target.wait(timeout=35)
            except subprocess.TimeoutExpired:pass
            raise
def occupied_preflight_case():
    mode='stale-tid-occupied';case=OUT/mode;case.mkdir(exist_ok=False);prefix=case/'target';meta={};observer=None
    command=[str(BUILD/'maintenance_writer_cold_target.exe'),'--mode',mode,'--prefix',str(prefix)]
    with (case/'target.stdout').open('xb') as so,(case/'target.stderr').open('xb') as se:
        target=subprocess.Popen(command,stdout=so,stderr=se,creationflags=0x08000000)
        try:
            meta=dict(line.split('=',1) for line in wait_file(Path(str(prefix)+'.meta.txt'),target).splitlines())
            seed=read_json(Path(str(prefix)+'.occupied-seed-readback.json'),target)
            require(seed['api_and_readback_ok'] is True and seed['Dr0']==0x12345000 and seed['Dr7']&3==1,'Actual reserved hardware slot never established')
            raw=case/'observer.raw.ndjson';ready=case/'observer.ready.json'
            argv=[str(BUILD/'maintenance_writer_cold_observer.exe'),'--enable-cold-fixture','--fixture-meta',str(prefix)+'.meta.txt','--timeout-ms','5000','--raw',str(raw),'--ready',str(ready),'--expected-hits','4','--machine-id',MACHINE]
            with (case/'observer.stdout').open('xb') as oso,(case/'observer.stderr').open('xb') as ose:
                observer=subprocess.Popen(argv,stdout=oso,stderr=ose,creationflags=0x08000000);code=observer.wait(timeout=10)
            require(code==2 and not raw.exists() and not ready.exists(),'Occupied DR must reject before DebugActiveProcess/raw-ready')
            signal(meta['go_event']);actual=read_json(Path(str(prefix)+'.writes.json'),target);signal(meta['audit_event'])
            before=read_json(Path(str(prefix)+'.initial-debug.json'),target);after=read_json(Path(str(prefix)+'.after-debug.json'),target)
            require(before==after and before[0]['debug'][0]==0x12345000 and before[0]['debug'][5]&3==1,'Pre-existing actual hardware state changed')
            signal(meta['finish_event']);exit_code=target.wait(timeout=5);require(exit_code==0 and actual['actual_store_count']==4,'Owned target did not finish normally')
            result=dict(status='PASS',mode='occupied-before-attach',machine_id=MACHINE,observed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),synthetic=True,actual_native_occupied_DR_seed=seed,independent_DR_before=before,independent_DR_after=after,exact_all6_DR_equal=True,observer_exit_code=code,target_exit_code=exit_code,raw_not_created=True,ready_not_created=True,debug_attach=False,CK3_observed=False,known_producer=False,actual_OS_TID_reuse_claimed=False,source_map_regression='Separate actual compiled ownership unit; not an OS TID reuse claim')
            write(case/'RESULT.actual.json',result);print(json.dumps(dict(mode='occupied-before-attach',status='PASS',exact_all6_DR_equal=True)),flush=True);return result
        except BaseException as error:
            write(case/'FAILURE.actual.json',dict(error=repr(error),target_pid=target.pid,observer_pid=None if observer is None else observer.pid))
            if observer is not None and observer.poll() is None:
                try:observer.wait(timeout=15)
                except subprocess.TimeoutExpired:pass
            for key in ['go_event','audit_event','finish_event']:
                if key in meta:
                    try:signal(meta[key])
                    except OSError:pass
            try:target.wait(timeout=35)
            except subprocess.TimeoutExpired:pass
            raise
OUT.mkdir(exist_ok=False)
write(OUT/'EXECUTION-GATE.actual.json',gate())
unit_argv=[str(BUILD/'maintenance_writer_cold_observer.exe'),'--qualify-cold-thread-ownership']
unit=subprocess.run(unit_argv,capture_output=True,check=False,creationflags=0x08000000)
(OUT/'OWNERSHIP-UNIT.stdout.txt').write_bytes(unit.stdout);(OUT/'OWNERSHIP-UNIT.stderr.txt').write_bytes(unit.stderr)
require(unit.returncode==0,'Actual compiled stale-generation unit failed');unit_body=json.loads(unit.stdout)
require(unit_body['passed_checks']==4 and unit_body['actual_OS_TID_reuse'] is False and unit_body['debug_attach'] is False,'Ownership counterexample scope incorrect')
write(OUT/'OWNERSHIP-UNIT.actual.json',dict(argv=unit_argv,returncode=unit.returncode,result=unit_body,observed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),machine_id=MACHINE))
positive=run_case('correct-character-base-abi')
occupied=occupied_preflight_case()
# Validate only the new actual positive raw packet; do not repeat the prior24 malformed regression suite.
import importlib.util
consumer_path=Path(__file__).resolve().parent/'consume_writer_cold.py'
spec=importlib.util.spec_from_file_location('writer_consumer_narrow',consumer_path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
raw=OUT/'correct-character-base-abi/observer.raw.ndjson';validated=module.consume([json.loads(x) for x in raw.read_text().splitlines()])
write(OUT/'FINAL-NARROW-QUALIFICATION.actual.json',dict(status='PASS',machine_id=MACHINE,observed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),compiled_ownership_unit=unit_body,correct_character_case=positive,occupied_preflight_case=occupied,strict_new_raw_consumption=validated,old_8case_and24negative_not_repeated=True,CK3_observed=False,known_producer=False,military_attribution='unclosed'))
