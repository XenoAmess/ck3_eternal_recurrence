"""Source-bound conditional Root grant after an actual fresh owner pair.

This helper only reads files and the retained process identity/modules/debugger
state. It never starts the observer, game, Steam, SDK or a desktop operation.
"""
from __future__ import annotations
from collections.abc import Callable
from datetime import datetime,timedelta,timezone
import argparse,ctypes,json,os,time
from ctypes import wintypes
from pathlib import Path
from postload_admission import (Object,MODE,ROOT_SCHEMA,file_pin,pin,read,verify,obj,text,need,
    utc,scope_value,expected_from_scope,packet,validate_index,validate_qualification)
from postload_wire import decimal64,numeric32,wire_json
import postload_owner_binding as owner

class ModuleInfo(ctypes.Structure):
    _fields_=[('base',wintypes.LPVOID),('size',wintypes.DWORD),('entry',wintypes.LPVOID)]

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

def build(authorization: Object,awaiting_pin: object,*,inspect: Callable[[int,int,Path],Object]=inspect_process) -> Object:
    fields={'schema','machine_id','run_id','execute_after_actual_awaiting','ready_context_pin','runtime_pin',
        'prepared_pin','frozen_argv_pin','bundle_index_pin','helper_pin','qualification_pin','observer_pin',
        'Game_capacity_pin','game_exe_path','root_scope_path','deadline_utc','declarations'}
    need(set(authorization)==fields and authorization['schema']=='xar.maintenance.parent_postload.conditional-root-authorization.v1'
        and authorization['execute_after_actual_awaiting'] is True,'explicit source-bound conditional Root authorization')
    declarations=obj(authorization['declarations'],'Root declarations')
    need(declarations=={'one_original_window_only':True,'no_replay_unknown':True,'postload_execution_reviewed':True},
        'Root declarations required, not inferred from qualification')
    need(verify(authorization['helper_pin'])==Path(__file__).resolve(),'Root adopted helper differs')
    ready=read(authorization['ready_context_pin'])
    machine=text(authorization['machine_id'],'machine');run=text(authorization['run_id'],'run')
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
        ref=file_pin(raw);path=verify(ref,1024*1024)
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
    settings=obj(obj(prepared.get('case_inputs'))['r08_parent_postload_one_day'],'settings')
    for key in ('bundle_index_pin','qualification_pin','observer_pin'):
        need(file_pin(settings.get(key))==file_pin(authorization[key]),'prepared source/admission pin differs')
    need(Path(text(settings.get('root_scope_path'),'prepared scope')).resolve()==Path(text(authorization['root_scope_path'],'scope')).resolve(),
        'actual prepared Root scope path')
    need(settings.get('deadline_utc')==authorization['deadline_utc'],'prepared deadline differs')
    awaiting_ref=file_pin(awaiting_pin);path=verify(awaiting_ref)
    need(path==live/'case-output/R08-POSTLOAD-AWAITING-ROOT.json','actual same-run awaiting marker')
    awaiting=read(awaiting_ref)
    need(awaiting.get('run_id')==run and awaiting.get('observer_started') is False,'actual pre-observer phase')
    now=datetime.now(timezone.utc)
    deadline=utc(authorization['deadline_utc'])
    need((deadline-now).total_seconds()>=1050,'1050s normal close reserve')
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
    validate_qualification(read(qref),observer=observer_ref,typed_root=Path(__file__).parent)
    need((datetime.now(timezone.utc)-utc(facts.get('observed_at_utc'))).total_seconds()<=5,'OS owner observation too old')
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
    need((deadline-final).total_seconds()>=1050 and (final-utc(facts['observed_at_utc'])).total_seconds()<=5,
        'owner/close reserve expired during source checks')
    for ref in (awaiting_ref,snapshot_ref,cash_ref):
        verify(ref,3*1024*1024);need(0<=final.timestamp()-Path(ref['path']).stat().st_mtime<=30,'pair expired during checks')
    return obj(wire_json(scope),'Root scope wire')

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--Root-authorization',type=Path,required=True)
    parser.add_argument('--actual-awaiting',type=Path,required=True)
    parser.add_argument('--execute-once-after-actual-awaiting',action='store_true')
    args=parser.parse_args();need(args.execute_once_after_actual_awaiting,'default OFF')
    authorization=read(pin(args.Root_authorization))
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
