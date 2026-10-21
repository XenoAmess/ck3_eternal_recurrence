"""Own the original watcher; perform no SDK post-read before typed cleanup."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import ctypes
from ctypes import wintypes
import hashlib
import json
import subprocess
import time
from typing import BinaryIO, Callable, NoReturn
from parent_postload_contract import PREFIX_SHA
from .postload_public_models import (Binding, Call, Collected, FilePin, MODE, Object, PinLookup, Ready,
    SCHEMA, Snapshot, decoded, file_pin, need, number, object_value, output_json, pin as pin, read_pin, text, utc)


@dataclass
class Session:
    process: subprocess.Popen[bytes]
    output: Path
    started: float
    stdout: BinaryIO
    stderr: BinaryIO
    cancel_handle: int
    machine_id: str
    created_filetime: str | None = None


SESSIONS: dict[str,Session] = {}
COMMANDS: dict[int,subprocess.Popen[bytes]] = {}
EVENTS: dict[str,int] = {}


def write(path: Path, value: Object) -> FilePin:
    from ck3_live_run_id import current_machine_id
    document: Object = {'machine_id':text(current_machine_id(),'actual machine'),
        'observed_at_utc':datetime.now(timezone.utc).isoformat(),**value}
    payload = output_json(document)
    need(len(payload) <= 65536,'Bounded controller record')
    with path.open('xb') as stream:
        stream.write(payload)
    return pin(path)


def process_birth(process: subprocess.Popen[bytes]) -> str:
    kernel = ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.GetProcessTimes.argtypes = (wintypes.HANDLE,ctypes.POINTER(wintypes.FILETIME),ctypes.POINTER(wintypes.FILETIME),ctypes.POINTER(wintypes.FILETIME),ctypes.POINTER(wintypes.FILETIME))
    kernel.GetProcessTimes.restype = wintypes.BOOL
    handle: object = getattr(process,'_handle',None)
    if not isinstance(handle,int):
        raise ValueError('Original Popen handle unavailable')
    a,b,c,d = (wintypes.FILETIME() for _ in range(4))
    if not kernel.GetProcessTimes(wintypes.HANDLE(handle),ctypes.byref(a),ctypes.byref(b),ctypes.byref(c),ctypes.byref(d)):
        raise ctypes.WinError(ctypes.get_last_error())
    return str((int(a.dwHighDateTime)<<32)|int(a.dwLowDateTime))


def create_cancel(name: str) -> int:
    kernel = ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.CreateEventW.argtypes = (wintypes.LPVOID,wintypes.BOOL,wintypes.BOOL,wintypes.LPCWSTR)
    kernel.CreateEventW.restype = wintypes.HANDLE
    handle = kernel.CreateEventW(None,True,False,name)
    error = ctypes.get_last_error()
    if not handle or error == 183:
        if handle:
            close_cancel(int(handle))
        raise OSError(error,'New unique pointer cancel event required')
    return int(handle)


def close_cancel(handle: int) -> None:
    kernel = ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel.CloseHandle.restype = wintypes.BOOL
    if not kernel.CloseHandle(handle):
        raise ctypes.WinError(ctypes.get_last_error())


def wait_original(process: subprocess.Popen[bytes], *, threshold: float,
                  warning: Callable[[],None], sleep: Callable[[float],None] = time.sleep) -> int:
    warned = False
    while True:
        try:
            return process.wait(timeout=max(.25,threshold-time.monotonic()))
        except BaseException:
            if not warned:
                warned = True
                try:
                    warning()
                except BaseException:
                    pass
            try:
                sleep(.25)
            except BaseException:
                try:
                    ctypes.WinDLL('kernel32').Sleep(250)
                except BaseException:
                    pass


def run_owned(argv: list[str], output: Path, label: str, timeout: float) -> int:
    """Readonly prepare/consume commands retain their original owner as well."""
    write(output/(label+'.once.json'),{'argv':argv,'no_replay':True})
    created: str | None = None
    errors: list[str] = []
    with (output/(label+'.stdout')).open('xb') as stdout, (output/(label+'.stderr')).open('xb') as stderr:
        process: subprocess.Popen[bytes] = subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,
            creationflags=subprocess.CREATE_NO_WINDOW)
        COMMANDS[process.pid] = process
        started = time.monotonic()
        try:
            created = process_birth(process)
            write(output/(label+'.CREATED.actual.json'),{'argv':argv,'pid':process.pid,'creation_filetime_decimal':created})
        except BaseException as exc:
            errors.append(type(exc).__name__+': '+str(exc)[:1024])
        finally:
            def warning() -> None:
                write(output/(label+'.OWNER-HOLD.actual.json'),{'pid':process.pid,
                    'original_popen_retained':True,'kill_retry_SDK':False})
            code = wait_original(process,threshold=started+timeout,warning=warning)
            COMMANDS.pop(process.pid)
    write(output/(label+'.ORIGINAL-WAIT.actual.json'),{'argv':argv,'pid':process.pid,
        'creation_filetime_decimal':created,'returncode':code,'actual_original_popen_wait':True,'errors':errors,
        'stdout':pin(output/(label+'.stdout')),'stderr':pin(output/(label+'.stderr'))})
    need(not errors,'Original command identity/receipt error; no replay')
    return code


def fresh(scope: Object, *, machine: str, collected_at: float,
          monotonic: Callable[[],float] = time.monotonic) -> None:
    issued,expires = utc(scope.get('observed_at_utc'),'issued'),utc(scope.get('expires_at_utc'),'expiry')
    current = datetime.now(timezone.utc)
    need(scope.get('schema') == 'xar.maintenance.parent_postload.root-scope.v1'
         and scope.get('machine_id') == machine and scope.get('mode') == MODE
         and scope.get('postload_execution_authorized') is True and issued <= current < expires
         and 0 < (expires-issued).total_seconds() <= 30,'Fresh separate pointer Root scope required')
    need(0 <= monotonic()-collected_at <= 30,'Same-client owner pair older than 30s')


def observer_argv(exe: Path, prepared: Path, output: Path, machine: str) -> list[str]:
    return [str(exe),'--enable-ck3-12004-parent-postload-once','--admission-meta',
        str(prepared/'PARENT-POSTLOAD.meta.txt'),'--timeout-ms','30000','--raw',str(output/'parent.raw.ndjson'),
        '--ready',str(output/'parent.ready.json'),'--machine-id',machine,'--explicit-postload-execution-breakpoint-v1']


def prepare(python: str, repo: Path, tools: Path, collected: Collected, scope_pin: FilePin,
            qualification: FilePin, observer: FilePin, bundle_index: FilePin, output: Path) -> Path:
    need(not output.exists(),'New control directory required; no prepare replay')
    output.mkdir(parents=True)
    read_pin(scope_pin)
    read_pin(qualification)
    need(pin(Path(observer['path'])) == observer,'Observer changed before prepare')
    prepared = output/'prepared'
    argv = [python,'-B','-X','utf8',str(tools/'prepare_parent_postload_admission.py'),
        '--prepare-parent-postload','--repo',str(repo),'--snapshot',collected.before['path'],
        '--cash',collected.cash['path'],'--root-scope',scope_pin['path'],'--qualification',qualification['path'],
        '--observer',observer['path'],'--bundle-index',bundle_index['path'],'--output-root',str(prepared)]
    need(run_owned(argv,output,'prepare',45) == 0,'Actual pointer prepare rejected')
    Binding.parse(read_pin(pin(prepared/'BINDING.prepared.json')))
    return prepared


def bind_ready(raw_path: Path, binding: Binding, ready: Ready) -> Object | None:
    """Validate the entire observed census; sidecar may precede raw READY flush."""
    need(raw_path.stat().st_size <= 1048576,'Bounded actual raw')
    with raw_path.open('rb') as stream:
        prefix = stream.read(262144)
    complete = prefix.rfind(b'\n')+1
    lines = prefix[:complete].splitlines(keepends=True)
    if not lines:
        return None
    parsed: list[Object] = []
    for line in lines:
        value: object = json.loads(line)
        parsed.append(object_value(value,'raw row'))
    start_wire = parsed[0]
    start = decoded(start_wire)
    need(start.get('kind') == 'start' and start.get('schema') == SCHEMA and start.get('mode') == MODE,
         'Actual raw v2 start required')
    need(start.get('entryExact') is False and start.get('observation_kind') == 'parent_postload_execution',
         'Post-read evidence only')
    need(start.get('breakpoint_kind') == 'execution','New postload execution breakpoint required before day')
    need(number(start.get('target_record_limit'),'target record limit') == 1
         and start.get('prefix_sha256') == PREFIX_SHA,'Exact one-target source contract')
    for key,value in binding.expected.items():
        need(key in start and type(start[key]) is type(value) and start[key] == value,'Raw/prepared binding differs: '+key)
    active: dict[int,tuple[int,int,list[int],list[int]]] = {}
    highest: dict[int,int] = {}
    length = len(lines[0])
    for wire,line in zip(parsed[1:],lines[1:]):
        row = decoded(wire)
        length += len(line)
        kind = row.get('kind')
        if kind == 'arm':
            tid = number(row.get('thread_id'),'TID',minimum=1)
            generation = number(row.get('thread_generation'),'generation',minimum=1)
            birth = number(row.get('thread_created'),'thread FILETIME',(1<<64)-1,1)
            need(tid not in active and generation > highest.get(tid,0),'Distinct live thread generation')
            need(row.get('success') is True and row.get('readback') is True,'Actual arm/readback required')
            vectors: list[list[int]] = []
            for name in ('saved_debug','armed_debug'):
                raw_vector = row.get(name)
                need(isinstance(raw_vector,list) and len(raw_vector) == 6,'Complete six debug registers')
                vector: list[int] = []
                if isinstance(raw_vector,list):
                    vector = [number(v,name,(1<<64)-1) for v in raw_vector]
                vectors.append(vector)
            saved,actual = vectors
            need(saved[:4] == [0,0,0,0] and saved[5] & (0xff|0xffff0000) == 0,'Original debug slots free')
            need(actual[:4] == [binding.expected['post_pc'],0,0,0]
                 and actual[4] & 15 == 0 and actual[5] == saved[5] | 1,'Actual full watch vector')
            active[tid] = (generation,birth,saved,actual)
            highest[tid] = generation
        elif kind == 'thread_exited':
            tid = number(row.get('thread_id'),'exit TID',minimum=1)
            generation = number(row.get('thread_generation'),'exit generation',minimum=1)
            need(tid in active and active[tid][0] == generation,'Exact retired generation')
            active.pop(tid)
        elif kind == 'ready':
            need(row.get('census_complete') is True and len(active) == ready.count,'Actual READY/raw census differs')
            table = [{'thread_id':tid,'thread_generation':state[0],'thread_created':state[1],
                'saved_debug':state[2],'armed_debug':state[3]} for tid,state in sorted(active.items())]
            return {'actual_raw_ready':True,'active_thread_count':len(active),
                'all_six_debug_registers_validated':True,'generation_table_sha256':hashlib.sha256(output_json(table)).hexdigest(),
                'raw_prefix':{'path':str(raw_path),'offset':0,'bytes':length,'sha256':hashlib.sha256(prefix[:length]).hexdigest()}}
        else:
            raise ValueError('Unexpected pre-READY row: '+str(kind))
    need(len(prefix) < 262144,'READY absent from bounded prefix')
    return None


def await_ready(session: Session, binding: Binding, *, monotonic: Callable[[],float] = time.monotonic,
                sleep: Callable[[float],None] = time.sleep) -> Object:
    sidecar = session.output/'parent.ready.json'
    raw = session.output/'parent.raw.ndjson'
    while monotonic() < session.started+12:
        need(session.process.poll() is None,'Observer exited before READY; zero day')
        if sidecar.exists():
            need(0 < sidecar.stat().st_size <= 65536,'READY size')
            try:
                value: object = json.loads(sidecar.read_bytes())
            except json.JSONDecodeError:
                sleep(.025)
                continue
            ready = Ready.parse(value)
            if raw.exists():
                proof = bind_ready(raw,binding,ready)
                if proof is not None:
                    need(session.process.poll() is None,'Observer exited while observing census')
                    return {'ready':ready.raw,'binding':proof}
        sleep(.025)
    raise TimeoutError('Complete READY/raw census absent; zero day/no replay')


def validate_cleanup(actual: Object, code: int, raw: Path, binding_path: Path) -> None:
    number(code,'original exit status',1)
    need(actual.get('schema') == 'xar.maintenance.parent_postload.result.v1'
         and actual.get('synthetic') is False and actual.get('cleanup_complete') is True
         and actual.get('full_R08') is False and actual.get('entryExact') is False
         and actual.get('observation_kind') == 'parent_postload_execution','Actual nonsynthetic narrow cleanup required')
    need(type(actual.get('target_postload_qualified')) is bool
         and code in (0,1) and (code == 0) is actual['target_postload_qualified'],'Original exit/result differs')
    need(file_pin(actual.get('raw_pin')) == pin(raw)
         and file_pin(actual.get('binding_pin')) == pin(binding_path),'Consumer source pins differ')
    binding = Binding.parse(read_pin(pin(binding_path)))
    need(actual.get('machine_id') == binding.expected['machine_id'] and binding.expected['synthetic'] is False,
         'Cleanup machine/ordinary binding differs')
    for key in ('paid_maintenance_raw','payer','cadence'):
        need(key in actual and actual[key] is None,'Payment remains explicit null')


def finish(session: Session, *, python: str, tools: Path, prepared: Path) -> Object:
    def warning() -> None:
        write(session.output/'UNRESOLVED-NATIVE-HOLD.actual.json',{'pid':session.process.pid,
            'observer_created_filetime':session.created_filetime,'original_popen_retained':True,'kill_relaunch_SDK':False})
    code = wait_original(session.process,threshold=session.started+45,warning=warning)
    session.stdout.close()
    session.stderr.close()
    close_cancel(session.cancel_handle)
    EVENTS.pop(str(session.output),None)
    write(session.output/'OBSERVER-ORIGINAL-WAIT.actual.json',{'pid':session.process.pid,
        'observer_created_filetime':session.created_filetime,'returncode':code,'actual_original_popen_wait':True})
    result_path = session.output/'PARENT-POSTLOAD.actual.json'
    argv = [python,'-B','-X','utf8',str(tools/'consume_parent_postload_actual.py'),
        '--raw',str(session.output/'parent.raw.ndjson'),'--binding',str(prepared/'BINDING.prepared.json'),
        '--output',str(result_path)]
    need(run_owned(argv,session.output,'consume',20) == 0,'Typed consumer rejected; no cleanup credit')
    actual = read_pin(pin(result_path))
    validate_cleanup(actual,code,session.output/'parent.raw.ndjson',prepared/'BINDING.prepared.json')
    SESSIONS.pop(str(session.output),None)
    return actual


def hold_uncertain(session: Session, error: BaseException) -> NoReturn:
    try:
        write(session.output/'UNRESOLVED-TYPED-CLEANUP-HOLD.actual.json',{'pid':session.process.pid,
            'observer_created_filetime':session.created_filetime,'error':(type(error).__name__+': '+str(error))[:4096],
            'original_cli_retains_owner':True,'SDK_Quit_kill_retry':False})
    except BaseException:
        pass
    while True:
        try:
            time.sleep(1)
        except BaseException:
            try:
                ctypes.WinDLL('kernel32').Sleep(1000)
            except BaseException:
                pass


def observe(*, python: str, tools: Path, observer: FilePin, prepared: Path, output: Path,
            machine: str, scope_pin: FilePin, collected_at: float, before: Snapshot, deadline_utc: str,
            call: Call, packet_pin: PinLookup, guard: Callable[[], None]) -> Object:
    guard()
    scope = read_pin(scope_pin)
    binding = Binding.parse(read_pin(pin(prepared/'BINDING.prepared.json')))
    need(binding.root_scope_sha256 == scope_pin['sha256'],'Prepared scope changed')
    need(binding.expected['synthetic'] is False and binding.expected['machine_id'] == machine,'Actual public owner required')
    need(pin(Path(observer['path'])) == observer,'Observer content changed after qualification')
    deadline = utc(deadline_utc,'deadline')
    fresh(scope,machine=machine,collected_at=collected_at)
    need((deadline-datetime.now(timezone.utc)).total_seconds() >= 1050,'Original close reserve expired before observer')
    argv = observer_argv(Path(observer['path']),prepared,output,machine)
    handle = create_cancel(text(scope.get('cancel_event'),'cancel event'))
    EVENTS[str(output)] = handle
    try:
        stdout = (output/'observer.stdout').open('xb')
        try:
            stderr = (output/'observer.stderr').open('xb')
        except BaseException:
            stdout.close()
            raise
        try:
            guard()
            fresh(read_pin(scope_pin),machine=machine,collected_at=collected_at)
            write(output/'observer-start.once.json',{'argv':argv,'no_replay':True})
            process: subprocess.Popen[bytes] = subprocess.Popen(argv,stdout=stdout,stderr=stderr,
                creationflags=subprocess.CREATE_NO_WINDOW)
        except BaseException:
            stdout.close()
            stderr.close()
            raise
    except BaseException:
        close_cancel(handle)
        EVENTS.pop(str(output),None)
        raise
    session = Session(process,output,time.monotonic(),stdout,stderr,handle,machine)
    SESSIONS[str(output)] = session
    day: Object = {'submitted':False,'exact_day_verified':False}
    error: str | None = None
    step: MappingResult | None = None
    step_error: str | None = None
    try:
        session.created_filetime = process_birth(process)
        write(output/'OBSERVER-ORIGINAL-POPEN.actual.json',{'pid':process.pid,
            'observer_created_filetime':session.created_filetime,'actual_original_popen_retained':True,'argv':argv})
        write(output/'READY-OBSERVED.actual.json',await_ready(session,binding))
        fresh(read_pin(scope_pin),machine=machine,collected_at=collected_at)
        need(process.poll() is None and time.monotonic()-session.started < 18,'Watch headroom absent; zero day')
        write(output/'day.once.json',{'tool':'ck3_execute_step','step':'life-advance-one-day','no_replay':True})
        day['submitted'] = True
        try:
            step = object_value(call('day-once','ck3_execute_step',{'step':'life-advance-one-day','expected_revision':None}))
        except BaseException as exc:
            step_error = type(exc).__name__+': '+str(exc)
    except BaseException as exc:
        error = type(exc).__name__+': '+str(exc)
    finally:
        try:
            actual = finish(session,python=python,tools=tools,prepared=prepared)
        except BaseException as exc:
            hold_uncertain(session,exc)
    if day['submitted'] is True:
        try:
            after = Snapshot.parse(call('independent-after','ck3_take_snapshot',{'include_native_command_history':False}),before.actor)
            need(after.date == before.date+24 and after.pid == before.pid and after.generation == before.generation
                 and after.episode_present == before.episode_present,'Independent exact-day owner/date differs')
            if step is not None and step_error is None:
                from xar_autoplayer.bridge.exact_one_day_postcondition import exact_day_postcondition
                day['postcondition'] = object_value(exact_day_postcondition(step,before.raw,after.raw))
                day['exact_day_verified'] = True
            day['independent_after_source'] = packet_pin('independent-after')
            day['original_step_error'] = step_error
            need(step_error is None,'Original day unknown; no replay')
        except BaseException as exc:
            error = type(exc).__name__+': '+str(exc)
    result: Object = {'day':day,'observer':actual,'primary_error':error,'safe_to_begin_normal_close':True,
        'full_R08_qualified':False,'paid_maintenance_raw':None,'payer':None,'cadence':None,
        'entryExact':False,'observation_kind':'parent_postload_execution'}
    write(output/'ROOT-WINDOW-RESULT.actual.json',result)
    return result


MappingResult = dict[str,object]
