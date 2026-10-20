"""Own one parent observer and one public exact-day request; never construct SDK."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import subprocess
import time
from typing import Callable, TypedDict, NoReturn, BinaryIO
from ck3_mod_acceptance_background_types import process_handle

MODE = 'parent-entry-execution-once-v1'


class FilePin(TypedDict):
    path: str
    bytes: int
    sha256: str


@dataclass
class Session:
    process: subprocess.Popen[bytes]
    output: Path
    started: float
    stdout: BinaryIO
    stderr: BinaryIO
    cancel_handle: int
    machine_id: str = ''
    created_filetime: str | None = None


# This owner survives a return to the actor and retains unresolved native cleanup.
SESSIONS: dict[str, Session] = {}
EVENTS: dict[str, int] = {}


def create_cancel(name: str) -> int:
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateEventW.argtypes = (wintypes.LPVOID, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR)
    kernel.CreateEventW.restype = wintypes.HANDLE
    handle = kernel.CreateEventW(None, True, False, name)
    error = ctypes.get_last_error()
    if not handle or error == 183:
        if handle:
            close_cancel(int(handle))
        raise OSError(error, 'New unique parent cancel event required')
    return int(handle)


def close_cancel(handle: int) -> None:
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel.CloseHandle.restype = wintypes.BOOL
    if not kernel.CloseHandle(handle):
        raise ctypes.WinError(ctypes.get_last_error())


def need(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def pin(path: Path) -> FilePin:
    payload = path.read_bytes()
    return FilePin(path=str(path.resolve()), bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())


def read_pin(ref: FilePin, maximum: int = 65536) -> dict:
    path = Path(ref['path'])
    need(type(ref['bytes']) is int and 0 < ref['bytes'] <= maximum
         and path.stat().st_size == ref['bytes'], 'Exact bounded file required')
    payload = path.read_bytes()
    need(len(payload) == ref['bytes'] and hashlib.sha256(payload).hexdigest() == ref['sha256'], 'File changed')
    value = json.loads(payload)
    need(type(value) is dict, 'JSON object required')
    return value


def write(path: Path, value: dict) -> FilePin:
    from ck3_live_run_id import current_machine_id
    value = {'machine_id': current_machine_id(),
             'observed_at_utc': datetime.now(timezone.utc).isoformat(), **value}
    payload = (json.dumps(value, sort_keys=True, allow_nan=False, indent=2) + '\n').encode()
    need(len(payload) <= 65536, 'Bounded controller record')
    with path.open('xb') as output:
        output.write(payload)
    return pin(path)


def process_birth(process: subprocess.Popen[bytes]) -> str:
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetProcessTimes.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.FILETIME),
        ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME))
    kernel.GetProcessTimes.restype = wintypes.BOOL
    fields = [wintypes.FILETIME() for _ in range(4)]
    if not kernel.GetProcessTimes(process_handle(process), *(ctypes.byref(field) for field in fields)):
        raise ctypes.WinError(ctypes.get_last_error())
    return str((fields[0].dwHighDateTime << 32) | fields[0].dwLowDateTime)


def bind_ready(raw_path: Path, binding: dict, ready: dict) -> dict:
    need(raw_path.stat().st_size <= 1024*1024, 'Bounded actual parent raw')
    with raw_path.open('rb') as source:
        prefix = source.read(131072)
    lines = prefix.splitlines(keepends=True)
    rows = [json.loads(line) for line in lines if line.endswith(b'\n')]
    need(bool(rows) and rows[0].get('kind') == 'start', 'Actual raw start absent')
    start = rows[0]
    need(start.get('schema') == 'xar.maintenance.parent_entry.raw.v1'
         and start.get('mode') == MODE, 'Actual parent start schema/mode')
    for key, value in binding['expected'].items():
        need(type(start.get(key)) is type(value) and start.get(key) == value, 'Raw/prepared identity differs: '+key)
    active: dict[int, int] = {}
    found = False
    for row in rows[1:]:
        if row.get('kind') == 'arm':
            tid, generation = row.get('thread_id'), row.get('thread_generation')
            need(type(tid) is int and tid > 0 and type(generation) is int and generation > 0
                 and type(row.get('thread_created')) is int and row['thread_created'] > 0
                 and row.get('success') is True and row.get('readback') is True,
                 'Actual successful thread generation/readback required')
            debug = row.get('armed_debug')
            need(type(debug) is list and len(debug) == 6 and debug[0] == binding['expected']['entry']
                 and debug[1:4] == [0,0,0] and debug[5] & 0xffff00ff == 1,
                 'Actual mode DR0 execute vector required')
            active[tid] = generation
        elif row.get('kind') == 'thread_exited':
            need(active.get(row.get('thread_id')) == row.get('thread_generation'), 'Retired generation differs')
            active.pop(row['thread_id'])
        elif row.get('kind') == 'ready':
            need(row.get('census_complete') is True, 'Actual raw census absent')
            found = True
            break
    need(found and len(active) == ready['armed_thread_count'] > 0, 'READY/raw census size differs')
    return {'raw_start': start, 'armed_generations': active, 'actual_raw_ready': True}


def fresh(scope: dict, *, machine: str, collected_at: float,
          monotonic: Callable[[], float] = time.monotonic) -> None:
    now = datetime.now(timezone.utc)
    issued = datetime.fromisoformat(scope['observed_at_utc'].replace('Z', '+00:00'))
    expires = datetime.fromisoformat(scope['expires_at_utc'].replace('Z', '+00:00'))
    need(scope.get('machine_id') == machine and scope.get('mode') == MODE
         and scope.get('execution_authorized') is True and issued.tzinfo is not None
         and issued <= now < expires and (expires-issued).total_seconds() <= 300,
         'Fresh separate parent Root scope required')
    need(0 <= monotonic() - collected_at <= 30, 'Same-client owner pair older than 30 seconds')


def observer_argv(exe: Path, prepared: Path, output: Path, machine: str) -> list[str]:
    return [str(exe), '--enable-ck3-12004-parent-entry-once', '--admission-meta',
        str(prepared/'PARENT-ENTRY.meta.txt'), '--timeout-ms', '30000', '--raw',
        str(output/'parent.raw.ndjson'), '--ready', str(output/'parent.ready.json'),
        '--machine-id', machine, '--explicit-execution-breakpoint-v1']


def prepare(python: str, repo: Path, tools: Path, collected: dict, scope_pin: FilePin,
            qualification: FilePin, observer: FilePin, output: Path) -> Path:
    need(not output.exists(), 'New parent control root required')
    output.mkdir(parents=True)
    prepared = output/'prepared'
    read_pin(scope_pin); read_pin(qualification)
    exe = Path(observer['path'])
    need(pin(exe) == observer, 'Observer content differs from reviewed Q')
    argv = [python, '-B', '-X', 'utf8', str(tools/'prepare_parent_entry_admission.py'),
        '--prepare-parent-entry', '--repo', str(repo), '--snapshot', collected['before_response']['path'],
        '--cash', collected['cash_response']['path'], '--root-scope', scope_pin['path'],
        '--qualification', qualification['path'], '--observer', str(exe), '--output-root', str(prepared)]
    write(output/'prepare.once.json', {'argv': argv, 'observer_started': False})
    with (output/'prepare.stdout').open('xb') as out, (output/'prepare.stderr').open('xb') as err:
        result = subprocess.run(argv, stdout=out, stderr=err, timeout=45, check=False,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    write(output/'PREPARE.actual.json', {'returncode': result.returncode, 'argv': argv,
        'stdout': pin(output/'prepare.stdout'), 'stderr': pin(output/'prepare.stderr'), 'observer_started': False})
    need(result.returncode == 0, 'Actual parent prepare rejected; preserve and never retry directory')
    return prepared


def await_ready(session: Session, *, monotonic: Callable[[], float] = time.monotonic,
                sleep: Callable[[float], None] = time.sleep) -> dict:
    path = session.output/'parent.ready.json'
    deadline = session.started + 12
    while monotonic() < deadline:
        need(session.process.poll() is None, 'Observer exited before READY; zero day')
        if path.exists():
            need(0 < path.stat().st_size <= 65536, 'READY size')
            try:
                value = json.loads(path.read_bytes())
            except json.JSONDecodeError:
                sleep(.025)
                continue
            need(value.get('mode') == MODE and value.get('ready') is True
                 and value.get('census_complete') is True and type(value.get('armed_thread_count')) is int
                 and value['armed_thread_count'] > 0, 'Actual complete parent READY required')
            need(session.process.poll() is None, 'Observer exited while reading READY')
            return value
        sleep(.025)
    raise TimeoutError('Finite READY absent; no day/relaunch')


def finish(session: Session, *, python: str, tools: Path, prepared: Path) -> dict:
    warned = False
    while True:
        try:
            code = session.process.wait(timeout=max(.25, session.started + 45 - time.monotonic()))
            break
        except subprocess.TimeoutExpired:
            if not warned:
                write(session.output/'UNRESOLVED-NATIVE-HOLD.actual.json', {'machine_id': session.machine_id,
                    'pid': session.process.pid, 'observer_created_filetime': session.created_filetime,
                    'original_popen_retained': True, 'diagnostic_threshold_seconds': 45,
                    'SDK_game_close_relaunch_kill': False})
                warned = True
            time.sleep(.25)
    session.stdout.close(); session.stderr.close()
    close_cancel(session.cancel_handle)
    EVENTS.pop(str(session.output), None)
    write(session.output/'OBSERVER-ORIGINAL-WAIT.actual.json', {'pid': session.process.pid,
        'observer_created_filetime': session.created_filetime, 'machine_id': session.machine_id,
        'returncode': code, 'actual_original_popen_wait': True})
    result_path = session.output/'PARENT-ENTRY.actual.json'
    argv = [python, '-B', '-X', 'utf8', str(tools/'consume_parent_entry_actual.py'),
        '--raw', str(session.output/'parent.raw.ndjson'), '--binding', str(prepared/'BINDING.prepared.json'),
        '--output', str(result_path)]
    write(session.output/'consume.once.json', {'argv': argv})
    with (session.output/'consume.stdout').open('xb') as out, (session.output/'consume.stderr').open('xb') as err:
        result = subprocess.run(argv, stdout=out, stderr=err, timeout=20, check=False)
    write(session.output/'CONSUME.actual.json', {'returncode': result.returncode, 'argv': argv})
    need(result.returncode == 0, 'Typed parent consumption rejected; no cleanup credit')
    actual = read_pin(pin(result_path))
    need(actual.get('synthetic') is False and actual.get('cleanup_complete') is True,
         'Actual nonsynthetic cleanup required')
    return actual


def hold_uncertain(session: Session, error: BaseException) -> NoReturn:
    # Returning would let the public CLI destroy its original ownership stack.
    # No timed auto-release, force-kill, repeated consumer or SDK recovery occurs.
    try:
        write(session.output/'UNRESOLVED-TYPED-CLEANUP-HOLD.actual.json', {
            'machine_id': session.machine_id, 'pid': session.process.pid,
            'observer_created_filetime': session.created_filetime,
            'error': (type(error).__name__+': '+str(error))[:4096], 'original_cli_retains_owner': True})
    except BaseException:
        pass
    while True:
        try:
            time.sleep(1)
        except BaseException:
            # A Python interrupt or wait/reporting error is not permission to
            # abandon the native owner. Keep one OS wait slice before retry.
            try:
                kernel = ctypes.WinDLL('kernel32', use_last_error=True)
                kernel.Sleep(1000)
            except BaseException:
                continue


def observe(*, python: str, tools: Path, observer: FilePin, prepared: Path, output: Path,
            machine: str, scope_pin: FilePin, collected_at: float, before: dict, deadline_utc: str,
            call: Callable[[str, str, dict], dict]) -> dict:
    scope = read_pin(scope_pin)
    fresh(scope, machine=machine, collected_at=collected_at)
    binding = read_pin(pin(prepared/'BINDING.prepared.json'))
    need(binding['root_scope_sha256'] == scope_pin['sha256'], 'Prepared scope changed')
    exe = Path(observer['path'])
    need(pin(exe) == observer, 'Final observer bytes differ; never use old Q after rebuild')
    deadline = datetime.fromisoformat(deadline_utc.replace('Z', '+00:00'))
    need(deadline.tzinfo is not None and (deadline-datetime.now(timezone.utc)).total_seconds() >= 1050,
         'Insufficient original close/cleanup/observation reserve immediately before observer claim')
    argv = observer_argv(exe, prepared, output, machine)
    handle = create_cancel(scope['cancel_event'])
    EVENTS[str(output)] = handle
    try:
        write(output/'observer-start.once.json', {'argv': argv, 'no_replay': True})
    except BaseException:
        close_cancel(handle); EVENTS.pop(str(output), None)
        raise
    out, err = (output/'observer.stdout').open('xb'), (output/'observer.stderr').open('xb')
    started = time.monotonic()
    try:
        proc = subprocess.Popen(argv, stdout=out, stderr=err, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    except BaseException:
        out.close(); err.close()
        raise
    session = Session(proc, output, started, out, err, handle, machine)
    SESSIONS[str(output)] = session  # Register the original object before recording identity/READY.
    day: dict = {'submitted': False, 'exact_day_verified': False}
    error: str | None = None
    step = None
    step_error = None
    try:
        session.created_filetime = process_birth(proc)
        write(output/'OBSERVER-ORIGINAL-POPEN.actual.json', {'machine_id': machine, 'pid': proc.pid,
            'observer_created_filetime': session.created_filetime, 'actual_original_popen_retained': True,
            'argv': argv})
        ready = await_ready(session)
        ready_binding = bind_ready(output/'parent.raw.ndjson', binding, ready)
        write(output/'READY-OBSERVED.actual.json', {'ready': ready, 'binding': ready_binding})
        fresh(read_pin(scope_pin), machine=machine, collected_at=collected_at)
        need(proc.poll() is None and time.monotonic()-started < 18, 'Insufficient watch headroom; zero day')
        write(output/'day.once.json', {'tool': 'ck3_execute_step', 'step': 'life-advance-one-day', 'no_replay': True})
        day['submitted'] = True
        try:
            step = call('day-once', 'ck3_execute_step', {'step': 'life-advance-one-day', 'expected_revision': None})
        except BaseException as exc:
            step_error = type(exc).__name__ + ': ' + str(exc)
    except BaseException as exc:
        error = type(exc).__name__ + ': ' + str(exc)
    finally:
        try:
            actual = finish(session, python=python, tools=tools, prepared=prepared)
        except BaseException as exc:
            hold_uncertain(session, exc)
    # Only the unique composite executes during the debugger window. Every SDK
    # post-read waits for the original observer wait and typed full cleanup.
    if actual.get('cleanup_complete') is True and day['submitted']:
        try:
            after = call('independent-after', 'ck3_take_snapshot', {'include_native_command_history': False})
            need(after.get('date_raw') == before['date_raw']+24 and after.get('paused') is True
                 and after.get('played_character', {}).get('character_id') == before['played_character']['character_id']
                 and after.get('diagnostics', {}).get('bridge_pid') == before['diagnostics']['bridge_pid']
                 and after.get('diagnostics', {}).get('connection_generation') == before['diagnostics']['connection_generation'],
                 'Independent exact-day owner/date mismatch')
            if step is not None and step_error is None:
                from xar_autoplayer.bridge.exact_one_day_postcondition import exact_day_postcondition
                day['postcondition'] = exact_day_postcondition(step, before, after)
                day['exact_day_verified'] = True
            day.update(after=after, original_step_error=step_error)
            need(step_error is None, 'Original day unknown; no replay')
        except BaseException as exc:
            error = type(exc).__name__ + ': ' + str(exc)
    result = {'day': day, 'observer': actual, 'primary_error': error,
              'safe_to_begin_normal_close': actual.get('cleanup_complete') is True,
              'full_R08_qualified': False, 'paid_maintenance_raw': None}
    write(output/'ROOT-WINDOW-RESULT.actual.json', result)
    return result
