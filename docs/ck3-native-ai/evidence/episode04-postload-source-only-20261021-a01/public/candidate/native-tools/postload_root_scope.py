"""Source-bound conditional Root grant after an actual fresh owner pair.

This helper only reads files and the retained process identity/modules/debugger
state. It never starts the observer, game, Steam, SDK or a desktop operation.
"""
from __future__ import annotations
from collections.abc import Callable
from datetime import datetime,timedelta,timezone
import argparse,ctypes,json,math,os,time
from ctypes import wintypes
from pathlib import Path
from postload_admission import (Object,MODE,ROOT_SCHEMA,file_pin,pin,read,verify,obj,text,need,
    utc,scope_value,expected_from_scope,packet,validate_index,validate_qualification)
from postload_wire import decimal64,numeric32,wire_json
import postload_owner_binding as owner

class ModuleInfo(ctypes.Structure):
    _fields_=[('base',wintypes.LPVOID),('size',wintypes.DWORD),('entry',wintypes.LPVOID)]

def current_machine() -> str:
    from ck3_live_run_id import current_machine_id
    value: object=current_machine_id()
    return text(value,'actual current machine')

def actual_hold(ready: Object,runtime: Object,*,allow_not_ready: bool=False) -> float|None:
    """Read the original held host deadline, preserving its legacy time format."""
    path=Path(text(ready.get('run_dir'),'actual run'))/'native-report.json'
    before=path.stat()
    need(0<before.st_size<=96*1024*1024,'bounded original host report')
    report=obj(json.loads(path.read_bytes()),'actual host report')
    after=path.stat()
    if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):
        raise PermissionError('Host report changed during hold observation')
    need(not report.get('finished_at') and not report.get('hold_finished_by_control_plan')
        and not report.get('error'),'actual original host alive without error')
    # Standard ready-context does not contain state_dir. Its exact prepared
    # source owns the startup state; never invent a ready-context extension.
    prepared=read(ready.get('prepared_case'))
    startup=obj(prepared.get('startup'),'actual prepared startup')
    need(Path(text(report.get('state_dir'),'report state')).resolve()==Path(text(startup.get('state_dir'),'prepared state')).resolve()
        and Path(text(report.get('agent_source_root'),'report source')).resolve()==Path(text(runtime.get('repo_root'),'runtime source')).resolve(),
        'actual held source/state crossed allocation')
    if report.get('phase')!='hold':
        need(allow_not_ready,'actual original host hold required')
        return None
    value=report.get('hold_until_utc_estimated')
    if not isinstance(value,(int,float)) or isinstance(value,bool) or not math.isfinite(value):
        raise ValueError('original finite legacy hold time required')
    return float(value)

def inspect_process(pid: int,created: int,exe: Path) -> Object:
    """Exact current process; no input, focus, suspend, context write or VM write."""
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    psapi=ctypes.WinDLL('psapi',use_last_error=True)
    kernel.OpenProcess.argtypes=(wintypes.DWORD,wintypes.BOOL,wintypes.DWORD)
    kernel.OpenProcess.restype=wintypes.HANDLE
    handle=kernel.OpenProcess(0x0400|0x0010,False,pid)
    if not handle:raise ctypes.WinError(ctypes.get_last_error())
    kernel.CloseHandle.argtypes=(wintypes.HANDLE,)
    kernel.CloseHandle.restype=wintypes.BOOL
    try:
        kernel.GetProcessTimes.argtypes=(wintypes.HANDLE,)+(ctypes.POINTER(wintypes.FILETIME),)*4
        kernel.GetProcessTimes.restype=wintypes.BOOL
        a,b,c,d=(wintypes.FILETIME() for _ in range(4))
        need(bool(kernel.GetProcessTimes(handle,ctypes.byref(a),ctypes.byref(b),ctypes.byref(c),ctypes.byref(d))), 'GetProcessTimes')
        birth=(int(a.dwHighDateTime)<<32)|int(a.dwLowDateTime)
        need(birth==created,'current PID birth differs')
        kernel.GetExitCodeProcess.argtypes=(wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD))
        kernel.GetExitCodeProcess.restype=wintypes.BOOL
        exitcode=wintypes.DWORD()
        need(bool(kernel.GetExitCodeProcess(handle,ctypes.byref(exitcode))) and exitcode.value==259,'current owner not alive')
        kernel.CheckRemoteDebuggerPresent.argtypes=(wintypes.HANDLE,ctypes.POINTER(wintypes.BOOL))
        kernel.CheckRemoteDebuggerPresent.restype=wintypes.BOOL
        debug=wintypes.BOOL()
        need(bool(kernel.CheckRemoteDebuggerPresent(handle,ctypes.byref(debug))) and not bool(debug.value),
            'actual debugger present or unreadable')
        modules=(wintypes.HMODULE*1024)();needed=wintypes.DWORD()
        psapi.EnumProcessModulesEx.argtypes=(wintypes.HANDLE,ctypes.POINTER(wintypes.HMODULE),wintypes.DWORD,ctypes.POINTER(wintypes.DWORD),wintypes.DWORD)
        psapi.EnumProcessModulesEx.restype=wintypes.BOOL
        need(bool(psapi.EnumProcessModulesEx(handle,modules,ctypes.sizeof(modules),ctypes.byref(needed),3))
            and needed.value<=ctypes.sizeof(modules),'bounded complete module list')
        psapi.GetModuleFileNameExW.argtypes=(wintypes.HANDLE,wintypes.HMODULE,wintypes.LPWSTR,wintypes.DWORD)
        psapi.GetModuleFileNameExW.restype=wintypes.DWORD
        psapi.GetModuleInformation.argtypes=(wintypes.HANDLE,wintypes.HMODULE,ctypes.POINTER(ModuleInfo),wintypes.DWORD)
        psapi.GetModuleInformation.restype=wintypes.BOOL
        found: Object|None=None
        for index in range(needed.value//ctypes.sizeof(wintypes.HMODULE)):
            path=ctypes.create_unicode_buffer(32768)
            size=int(psapi.GetModuleFileNameExW(handle,modules[index],path,len(path)))
            need(0<size<len(path)-1,'module path unavailable/truncated')
            if Path(path.value).resolve()==exe.resolve():
                need(found is None,'ambiguous exact executable module')
                info=ModuleInfo()
                need(bool(psapi.GetModuleInformation(handle,modules[index],ctypes.byref(info),ctypes.sizeof(info))), 'module identity')
                found={'pid':pid,'created':str(created),'module_base':str(int(info.base or 0)),
                    'module_size':str(int(info.size)),'path':str(exe.resolve()),'debugger_present':False,
                    'process_alive':True,'observed_at_utc':datetime.now(timezone.utc).isoformat()}
        need(found is not None,'expected executable module absent')
        if found is None:raise ValueError('module absent')
        return found
    finally:
        need(bool(kernel.CloseHandle(handle)),'close owned readonly process handle')

def build(authorization: Object,awaiting_pin: object,*,inspect: Callable[[int,int,Path],Object]=inspect_process,
        machine_reader: Callable[[],str]=current_machine) -> Object:
    fields={'schema','machine_id','run_id','execute_after_actual_awaiting','ready_context_pin','runtime_pin',
        'prepared_pin','frozen_argv_pin','bundle_index_pin','helper_pin','qualification_pin','observer_pin',
        'Game_capacity_pin','game_exe_path','root_scope_path','deadline_utc','declarations'}
    need(set(authorization)==fields and authorization['schema']=='xar.maintenance.parent_postload.conditional-root-authorization.v1'
        and authorization['execute_after_actual_awaiting'] is True,'explicit source-bound conditional Root authorization')
    declarations=obj(authorization['declarations'],'Root declarations')
    need(set(declarations)=={'one_original_window_only','no_replay_unknown','postload_execution_reviewed'}
        and all(value is True for value in declarations.values()),
        'Root declarations required, not inferred from qualification')
    need(verify(authorization['helper_pin'])==Path(__file__).resolve(),'Root adopted helper differs')
    ready=read(authorization['ready_context_pin'])
    runtime=read(authorization['runtime_pin'],1024*1024)
    machine=text(authorization['machine_id'],'machine');run=text(authorization['run_id'],'run')
    need(machine_reader()==machine,'Root scope belongs to another current machine')
    need(ready.get('run_id')==run,'actual allocated run differs')
    live=Path(text(ready.get('run_dir'),'actual live')).resolve()
    need(live.name==run and file_pin(ready.get('frozen_argv'))==file_pin(authorization['frozen_argv_pin'])
        and file_pin(ready.get('prepared_case'))==file_pin(authorization['prepared_pin']),'actual allocation pins differ')
    frozen=read(authorization['frozen_argv_pin'],2*1024*1024)
    need(frozen.get('run_id')==run and obj(frozen.get('identity_allocation')).get('machine_id')==machine,'frozen run/machine')
    files=obj(frozen.get('files'),'actual expanded frozen files')
    index_ref=file_pin(authorization['bundle_index_pin'])
    validate_index(index_ref,self_path=Path(__file__))
    index=read(index_ref)
    expanded=index['files']
    need(isinstance(expanded,list),'expanded source index files')
    if not isinstance(expanded,list):raise ValueError('index files')
    for raw in [authorization['runtime_pin'],authorization['helper_pin'],index_ref,*expanded]:
        ref=file_pin(raw);path=verify(ref,1024*1024,allow_empty=True)
        declared=obj(files.get(str(path)),'actual frozen source')
        need(declared.get('bytes')==ref['bytes'] and declared.get('sha256')==ref['sha256'],'source not frozen by allocator')
    cap=read(authorization['Game_capacity_pin'])
    need(cap.get('schema')=='xar.capacity.parent-postload.game-financial.v1'
        and cap.get('financial_reservation_admitted') is True and cap.get('admitted') is True
        and cap.get('budget_status')=='GREEN' and cap.get('machine_id')==machine,'actual separate Game financial scope')
    need(file_pin(cap.get('runtime_pin'))==file_pin(authorization['runtime_pin'])
        and cap.get('hard_deadline_utc')==authorization['deadline_utc'],'financial/runtime/deadline binding')
    scene=Path(text(cap.get('scene_root'),'scene')).resolve()
    need(scene==Path(text(cap.get('aggregate_root'),'aggregate')).resolve()
        and live.is_relative_to(scene),'same independent scene root')
    prepared=read(authorization['prepared_pin'])
    contract_ref=file_pin(prepared.get('contract'));contract=read(contract_ref)
    contract_path=Path(contract_ref['path']).resolve()
    frozen_contract=obj(files.get(str(contract_path)),'actual frozen case contract')
    need(frozen_contract.get('bytes')==contract_ref['bytes']
        and frozen_contract.get('sha256')==contract_ref['sha256']
        and contract.get('schema')=='xar.e04.r10-common-preparation.v1','actual prepared/frozen common contract')
    settings=obj(obj(prepared.get('case_inputs'))['r08_parent_postload_one_day'],'settings')
    for key in ('bundle_index_pin','qualification_pin','observer_pin'):
        need(file_pin(settings.get(key))==file_pin(authorization[key]),'prepared source/admission pin differs')
    need(Path(text(authorization['root_scope_path'],'scope')).resolve().is_relative_to(scene),'Root scope outside scene')
    need(Path(text(settings.get('root_scope_path'),'prepared scope')).resolve()==Path(text(authorization['root_scope_path'],'scope')).resolve(),
        'actual prepared Root scope path')
    need(settings.get('deadline_utc')==authorization['deadline_utc'],'prepared deadline differs')
    awaiting_ref=file_pin(awaiting_pin);path=verify(awaiting_ref)
    need(path==live/'case-output/R08-POSTLOAD-AWAITING-ROOT.json','actual same-run awaiting marker')
    awaiting=read(awaiting_ref)
    need(awaiting.get('run_id')==run and awaiting.get('observer_started') is False,'actual pre-observer phase')
    now=datetime.now(timezone.utc)
    deadline=utc(authorization['deadline_utc'])
    original_hold=actual_hold(ready,runtime)
    if original_hold is None:raise ValueError('actual original host hold required')
    need(min(deadline.timestamp(),original_hold)-now.timestamp()>=1050,'1050s original hold/scene close reserve')
    common=Path(text(awaiting.get('common_output'),'actual common output')).resolve()
    need(common==live/'case-output','same public CaseClient output')
    snapshot_ref=file_pin(awaiting.get('snapshot_view_pin'));cash_ref=file_pin(awaiting.get('cash_view_pin'))
    for ref in (awaiting_ref,snapshot_ref,cash_ref):
        need(0<=now.timestamp()-Path(ref['path']).stat().st_mtime<=25,'fresh current owner pair required')
    snapshot=packet(snapshot_ref,tool='ck3_take_snapshot',common=common,machine=machine)
    cash=packet(cash_ref,tool='ck3_query_war_cash_current_resources_private_v1',common=common,machine=machine)
    receipt=read(awaiting.get('common_inputs_receipt_pin'),3*1024*1024)
    expected=obj(receipt.get('expected'),'retained original input')
    need(expected.get('machine')==machine and receipt.get('observer_started') is False,'original same-client input role')
    game_state=expected.get('game_state_identity_witness');player=expected.get('local_player_id')
    if not isinstance(game_state,int) or type(game_state) is not int:raise ValueError('legacy native state integer')
    local=numeric32(player,'local player')
    actual_owner=owner.qualify(owner.ORDINARY,None,snapshot,obj(cash.get('war_payment_observations_v1')),
        obj(cash.get('current_raw_context_v1')),expected_game_state=game_state,expected_local_player_id=local)
    created=decimal64(awaiting.get('created'),'marker FILETIME')
    need(type(expected.get('created')) is int and expected['created']==created==actual_owner['process_create_time_100ns']
        and expected.get('pid')==actual_owner['pid'],'retained handle/native birth identity')
    facts=inspect(actual_owner['pid'],created,Path(text(authorization['game_exe_path'],'game executable')))
    need(facts.get('debugger_present') is False and facts.get('process_alive') is True
        and facts.get('pid')==actual_owner['pid'] and decimal64(facts.get('created'),'current FILETIME')==created,
        'actual fresh anti-debug/current owner')
    qref=file_pin(authorization['qualification_pin']);observer_ref=file_pin(authorization['observer_pin'])
    qualified=validate_qualification(read(qref),observer=observer_ref,typed_root=Path(__file__).parent)
    need(qualified.machine==machine,'actual Q belongs to another machine')
    need(0<=(datetime.now(timezone.utc)-utc(facts.get('observed_at_utc'))).total_seconds()<=5,'OS owner observation stale/future')
    scope: Object={'schema':ROOT_SCHEMA,'mode':MODE,'machine_id':machine,'postload_execution_authorized':True,
        'observed_at_utc':datetime.now(timezone.utc).isoformat(),
        'expires_at_utc':(now+timedelta(seconds=30)).isoformat(),
        'qualification_sha256':qref['sha256'],'observer_sha256':observer_ref['sha256'],
        'common_output':str(common),'snapshot_view_pin':snapshot_ref,'cash_view_pin':cash_ref,
        'owner_binding':actual_owner,'module_base':facts['module_base'],'module_size':facts['module_size'],
        'foreign_limit':4096,'capture_ms':30000,'cancel_event':'Local\\XAR_POSTLOAD_'+run.replace('-','_'),
        'public_bundle_index_pin':index_ref}
    parsed=scope_value(wire_json(scope));expected_from_scope(parsed,snapshot,cash)
    # Validation may take time. Neither stale files nor a completed process read
    # are silently renewed by a newly written signal timestamp.
    final=datetime.now(timezone.utc)
    current_hold=actual_hold(ready,runtime)
    if current_hold is None:raise ValueError('actual original host hold required')
    need(current_hold==original_hold and min(deadline.timestamp(),current_hold)-final.timestamp()>=1050
        and 0<=(final-utc(facts['observed_at_utc'])).total_seconds()<=5,
        'owner/close reserve expired during source checks')
    for ref in (awaiting_ref,snapshot_ref,cash_ref):
        verify(ref,3*1024*1024);need(0<=final.timestamp()-Path(ref['path']).stat().st_mtime<=30,'pair expired during checks')
    return obj(wire_json(scope),'Root scope wire')

def wait_awaiting(path: Path,authorization: Object,*,
        sleep: Callable[[float],None]=time.sleep) -> None:
    """Pre-startable metadata wait, bounded by the real host/scene reserve."""
    ready=read(authorization['ready_context_pin'])
    runtime=read(authorization['runtime_pin'],1024*1024)
    deadline=utc(authorization['deadline_utc']).timestamp()
    cached: float|None=None
    checked=0.0
    while not path.exists():
        current=time.time()
        if time.monotonic()-checked>=1:
            checked=time.monotonic()
            try:
                observed=actual_hold(ready,runtime,allow_not_ready=True)
                if observed is not None:
                    need(cached is None or cached==observed,'original host hold changed while waiting')
                    cached=observed
            except (FileNotFoundError,PermissionError,json.JSONDecodeError):
                # No signal/action exists yet. Retain genuine startup/in-flight
                # file absence, without swallowing host/source/identity errors.
                pass
        effective=deadline if cached is None else min(deadline,cached)
        need(effective-current>=1050,'Root metadata wait close reserve exhausted; no signal')
        sleep(.025)

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--Root-authorization',type=Path,required=True)
    parser.add_argument('--actual-awaiting',type=Path,required=True)
    parser.add_argument('--execute-once-after-actual-awaiting',action='store_true')
    args=parser.parse_args();need(args.execute_once_after_actual_awaiting,'default OFF')
    authorization=read(pin(args.Root_authorization))
    need(authorization.get('execute_after_actual_awaiting') is True,'Root conditional authorization required')
    validate_qualification(read(authorization.get('qualification_pin')),
        observer=file_pin(authorization.get('observer_pin')),typed_root=Path(__file__).parent)
    wait_awaiting(args.actual_awaiting,authorization)
    result=build(authorization,pin(args.actual_awaiting))
    path=Path(text(authorization.get('root_scope_path'),'new Root signal'))
    need(not path.exists(),'Root scope already exists; never overwrite/replay')
    complete=path.with_name(path.name+'.complete')
    payload=(json.dumps(result,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
    need(len(payload)<=65536,'bounded Root scope')
    with complete.open('xb') as stream:stream.write(payload);stream.flush();os.fsync(stream.fileno())
    os.link(complete,path)
    return 0

if __name__=='__main__':raise SystemExit(main())
