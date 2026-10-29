"""Close an actual idle, allocated-only public run without host/OS exit credit.

The CLI writes bounded metadata only. Public allocate remains the only allocator.
"""
from __future__ import annotations
from pathlib import Path, PureWindowsPath
from datetime import datetime, timezone
from decimal import Decimal
from dataclasses import dataclass
from collections.abc import Mapping
from typing import Literal, TypedDict, Protocol, runtime_checkable
import argparse, ast, hashlib, importlib, json, math, os, re, subprocess, sys
from ck3_mod_acceptance import check_pin, pin, read_json, same_directory_control_peer
from ck3_mod_acceptance_launcher_pin_refusal import public_operation_argv, validate_launcher_pin_refusal
from ck3_mod_acceptance_background_types import FilePin, JsonObject, file_pin, json_object, object_field, text_field, strings_field

SCHEMA = 'ck3-mod-acceptance-allocated-unrun-closure-v1'
ABORTED_KIND = 'wrapper-aborted-before-launch-without-terminal-waits'
CLOSED_KEEPER_ABORTED_KIND: Literal['wrapper-aborted-before-launch-with-closed-keeper'] = 'wrapper-aborted-before-launch-with-closed-keeper'
OFFLINE_TTL_KIND: Literal['pre-intent-background-offline-ttl-refused'] = 'pre-intent-background-offline-ttl-refused'
PRELAUNCH_KIND: Literal['prelaunch-orchestrator-failed-with-observed-waits'] = 'prelaunch-orchestrator-failed-with-observed-waits'
SERIAL_PRELAUNCH_FORMAT: Literal['root-serial-prepublic-original-waits-v1'] = 'root-serial-prepublic-original-waits-v1'
CAPACITY_WAIT_KIND: Literal['root-capacity-wait-timeout-before-public'] = 'root-capacity-wait-timeout-before-public'
CAPACITY_WAIT_FORMAT: Literal['root-serial-external-capacity-wait-v1'] = 'root-serial-external-capacity-wait-v1'
PrelaunchGuardState = Literal['armed-cancelled', 'failed-before-armed']


def _prelaunch_guard_state(bundle: Mapping[str, object]) -> PrelaunchGuardState:
    value = bundle.get('prelaunch_guard_state', 'armed-cancelled')
    if value == 'armed-cancelled':
        return 'armed-cancelled'
    if value == 'failed-before-armed':
        return 'failed-before-armed'
    raise ValueError('Exact typed prelaunch guard state required')


@dataclass(frozen=True)
class RootPrelaunchInvocation:
    argv: tuple[str, ...]
    started_at: datetime
    finished_at: datetime
    guard: Path
    source_commit: str


@dataclass(frozen=True)
class SerialObservedProcess:
    role: Literal['root', 'allocator', 'guard']
    label: str
    argv: tuple[str, ...]
    pid: int
    birth_filetime: str | None
    started_at: datetime
    finished_at: datetime
    returncode: int


class SerialPrelaunchGuardEvidence(TypedDict):
    label: str
    intent: FilePin
    started: FilePin
    original_wait: FilePin
    armed: FilePin
    stdout: FilePin
    stderr: FilePin


class SerialUnarmedGuardEvidence(TypedDict):
    label: Literal['CORE-GUARD-0', 'COLD-GUARD-0']
    intent: FilePin
    started: FilePin
    original_wait: FilePin
    stdout: FilePin
    stderr: FilePin


@runtime_checkable
class _SerialUnrunResources(Protocol):
    def current_screen_absent(self, lease_repo: Path, bus_dir: Path, bus_sha: str,
                             audit_dir: Path | None) -> object: ...
    def read_failed_runtime_release(self, path: Path) -> object: ...


@runtime_checkable
class _SerialUnrunReducer(Protocol):
    def __call__(self, previous: Path, freeze: object, close_path: Path, keeper_root: Path,
                 release: object, bus_packet: object, *, next_state: Path) -> object: ...


def _serial_resources() -> _SerialUnrunResources:
    provider: object = same_directory_control_peer('ck3_mod_acceptance_allocate')
    if not isinstance(provider, _SerialUnrunResources):
        raise ValueError('Original shared serial resource reader unavailable')
    return provider


def _serial_original(reference: object, expected: Path | None = None) -> tuple[FilePin, JsonObject]:
    ref = file_pin(reference)
    path = Path(ref['path'])
    if (set(json_object(reference)) != {'path', 'bytes', 'sha256'} or not path.is_absolute()
            or ref['bytes'] > 1048576 or (expected is not None and path.resolve() != expected.resolve())):
        raise ValueError('Exact bounded serial original pin/path required')
    if _ttl_pin(path) != ref:
        raise ValueError('Original serial bytes changed')
    return ref, json_object(json.loads(path.read_bytes()))


def _serial_raw(reference: object, expected: Path | None = None) -> bytes:
    ref = file_pin(reference)
    path = Path(ref['path'])
    if (set(json_object(reference)) != {'path', 'bytes', 'sha256'} or not path.is_absolute()
            or ref['bytes'] > 1048576 or (expected is not None and path.resolve() != expected.resolve())):
        raise ValueError('Exact bounded serial raw pin/path required')
    if _ttl_pin(path) != ref:
        raise ValueError('Original serial raw bytes changed')
    return path.read_bytes()


def _serial_child(intent: JsonObject, started: JsonObject, waited: JsonObject,
        machine: str, commit: str, role: Literal['allocator', 'guard'], label: str,
        code: int) -> SerialObservedProcess:
    shapes = ({'machine_id', 'observed_at_utc', 'argv', 'source_commit', 'started_at_utc'},
        {'machine_id', 'observed_at_utc', 'pid', 'process_creation_filetime_100ns',
         'process_create_time_seconds', 'started_at_utc', 'original_wait_pending'},
        {'machine_id', 'observed_at_utc', 'pid', 'process_creation_filetime_100ns',
         'original_wait_returncode', 'elapsed_seconds', 'finished_at_utc'})
    if any(set(row) != fields or row.get('machine_id') != machine
           for row, fields in zip((intent, started, waited), shapes, strict=True)):
        raise ValueError('Exact serial child original fields/machine required')
    pid = _integer(started.get('pid'), 'Serial child PID', 1)
    birth = text_field(started, 'process_creation_filetime_100ns')
    seconds = text_field(started, 'process_create_time_seconds')
    if (re.fullmatch('[1-9][0-9]{0,19}', birth) is None or int(birth) >= 1 << 64
            or re.fullmatch('(?:0|[1-9][0-9]{0,12})(?:\\.[0-9]{1,7})?', seconds) is None
            or Decimal(seconds) * 10000000 + 116444736000000000 != Decimal(birth)
            or _integer(waited.get('pid'), 'Serial waited PID', 1) != pid
            or waited.get('process_creation_filetime_100ns') != birth
            or type(waited.get('original_wait_returncode')) is not int or waited['original_wait_returncode'] != code
            or started.get('original_wait_pending') is not True or intent.get('source_commit') != commit):
        raise ValueError('Serial original PID/FILETIME/wait/source differs')
    elapsed = waited.get('elapsed_seconds')
    if (type(elapsed) not in (int, float) or not isinstance(elapsed, (int, float))
            or not math.isfinite(elapsed) or elapsed < 0):
        raise ValueError('Finite serial original elapsed time required')
    stamps = [_timestamp(row.get(key), 'Serial original chronology') for row, key in (
        (intent, 'started_at_utc'), (intent, 'observed_at_utc'), (started, 'started_at_utc'),
        (started, 'observed_at_utc'), (waited, 'finished_at_utc'), (waited, 'observed_at_utc'))]
    if stamps != sorted(stamps):
        raise ValueError('Serial original child chronology differs')
    return SerialObservedProcess(role, label, tuple(strings_field(intent, 'argv')), pid, birth,
        stamps[0], stamps[-1], code)


def _serial_argument(argv: tuple[str, ...], flag: str) -> str:
    if argv.count(flag) != 1 or argv.index(flag) + 1 >= len(argv):
        raise ValueError('Exact serial argument required: ' + flag)
    return argv[argv.index(flag) + 1]


def _serial_root_paths(root_wait: Path) -> tuple[Path, Path, Path]:
    """Select one exact original recorder format; never manufacture aliases."""
    if root_wait.name == 'ROOT-SERIAL.original-wait.json':
        names = ('ROOT-SERIAL.started.json', 'ROOT-SERIAL.stdout.log', 'ROOT-SERIAL.stderr.log')
    elif root_wait.name == 'INNER-ORIGINAL-WAIT.actual.json':
        names = ('INNER-STARTED.actual.json', 'SERIAL.stdout.log', 'SERIAL.stderr.log')
    else:
        raise ValueError('Known original serial root wait filename required')
    return root_wait.with_name(names[0]), root_wait.with_name(names[1]), root_wait.with_name(names[2])


def _serial_prepared_phases(bundle: Mapping[str, object], previous: Path,
        output: Path) -> tuple[tuple[str, ...], dict[str, FilePin]]:
    """Require every actual Prepared phase, in order, with no invented guard."""
    ready_ref, ready = _serial_original(bundle.get('ready'), previous/'ready-context.json')
    prepared_ref, prepared = _serial_original(ready.get('prepared_case'))
    contract_ref, contract = _serial_original(prepared.get('contract'))
    values = contract.get('gui_phases')
    if not isinstance(values, list) or not values:
        raise ValueError('Actual serial prepared contract phases required')
    phases = tuple(text_field(json_object(value), 'id') for value in values)
    if len(set(phases)) != len(phases) or any(not phase.replace('-', '').isalnum() for phase in phases):
        raise ValueError('Unique exact serial prepared phase identifiers required')
    labels = {'COLD-GUARD-'+str(index) for index in range(len(phases))}
    observed = {path.name.split('.', 1)[0] for path in output.glob('COLD-GUARD-*')}
    if observed != labels or any(output.glob('CORE-GUARD-*')):
        raise ValueError('Actual serial guard roles differ from all Prepared phases')
    return phases, {'serial_phase_ready':ready_ref, 'serial_phase_prepared':prepared_ref,
        'serial_phase_contract':contract_ref}


def _serial_allocator(bundle: Mapping[str, object], machine: str, commit: str | None = None) -> SerialObservedProcess:
    intent_ref, intent = _serial_original(bundle.get('allocator_intent'))
    root = Path(intent_ref['path']).parent
    _, started = _serial_original(bundle.get('allocator_process'), root/'ALLOCATE.started.actual.json')
    _, waited = _serial_original(bundle.get('allocator_exit'), root/'ALLOCATE.original-wait.actual.json')
    if Path(intent_ref['path']).name != 'ALLOCATE.intent.actual.json':
        raise ValueError('Original serial allocator intent path differs')
    child = _serial_child(intent, started, waited, machine, commit or text_field(intent, 'source_commit'),
        'allocator', 'ALLOCATE', 0)
    indices = [i for i, arg in enumerate(child.argv) if Path(arg).name == 'ck3_mod_acceptance.py']
    if len(indices) != 1 or child.argv[indices[0]+1:indices[0]+2] != ('allocate',) or child.argv.count('allocate') != 1:
        raise ValueError('Original serial child is not the public allocate command')
    return child


def _serial_unarmed_guard(bundle: Mapping[str, object], static: JsonObject,
        failure: JsonObject, *, previous: Path, output: Path, machine: str,
        commit: str, ready_at: datetime, root_finished_at: datetime,
        evidence: dict[str, FilePin]) -> SerialObservedProcess:
    """Bind the actual serial guard startup refusal, without an ARMED claim."""
    guards = bundle.get('serial_guards')
    fields = {'label', 'intent', 'started', 'original_wait', 'stdout', 'stderr'}
    if not isinstance(guards, list) or len(guards) != 1:
        raise ValueError('One actual before-ARMED serial guard role required')
    row = json_object(guards[0])
    label: Literal['CORE-GUARD-0', 'COLD-GUARD-0']
    if row.get('label') == 'CORE-GUARD-0':
        label = 'CORE-GUARD-0'
    elif row.get('label') == 'COLD-GUARD-0':
        label = 'COLD-GUARD-0'
    else:
        raise ValueError('Exact before-ARMED serial guard role required')
    if set(row) != fields:
        raise ValueError('Exact before-ARMED serial guard fields required')
    other_role = 'COLD-GUARD-*' if label == 'CORE-GUARD-0' else 'CORE-GUARD-*'
    later_role = (any(output.glob('CORE-GUARD-1*')) if label == 'CORE-GUARD-0' else
        any(not path.name.startswith(label+'.') for path in output.glob('COLD-GUARD-*')))
    if (any(output.glob(other_role)) or later_role
            or any(output.glob('CAPACITY*'))
            or any((output/(label+suffix)).exists() for suffix in
                ('.ARMED.actual.json', '.CANCEL.actual.json', '.actual.json'))
            or any(key in bundle for key in
                ('serial_capacity_start', 'serial_capacity_stdout', 'serial_capacity_refusal'))):
        raise ValueError('Before-ARMED serial recovery has later guard/capacity evidence')
    originals: dict[str, JsonObject] = {}
    for key, suffix in (('intent', '.intent.actual.json'), ('started', '.started.actual.json'),
            ('original_wait', '.original-wait.actual.json')):
        ref, originals[key] = _serial_original(row.get(key), output/(label+suffix))
        evidence[label+'.'+key] = ref
    child = _serial_child(originals['intent'], originals['started'], originals['original_wait'],
        machine, commit, 'guard', label, 1)
    argv = child.argv
    guard = file_pin(static.get('guard_original'))
    guard_raw = _serial_raw(guard).decode('utf-8-sig').replace('\r\n', '\n').replace('\r', '\n')
    interpreter = file_pin(static.get('guard_interpreter'))
    _serial_raw(interpreter)
    if (len(argv) < 6 or argv[1:5] != ('-B', '-X', 'utf8', '-c')
            or Path(argv[0]).resolve() != Path(interpreter['path']).resolve()
            or hashlib.sha256(argv[5].encode()).hexdigest() != static.get('guard_code_sha256')):
        raise ValueError('Before-ARMED serial interpreter/compiled source differs')
    compiled = [node for node in ast.walk(ast.parse(argv[5])) if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name) and node.func.id == 'compile']
    if (len(compiled) != 1 or len(compiled[0].args) != 3
            or not isinstance(compiled[0].args[0], ast.Constant) or compiled[0].args[0].value != guard_raw
            or not isinstance(compiled[0].args[1], ast.Constant) or compiled[0].args[1].value != guard['path']
            or not isinstance(compiled[0].args[2], ast.Constant) or compiled[0].args[2].value != 'exec'):
        raise ValueError('Before-ARMED serial source must be the exact pinned guard')
    _, ready = _serial_original(bundle.get('ready'), previous/'ready-context.json')
    prepared_ref, prepared = _serial_original(ready.get('prepared_case'))
    contract_ref, contract = _serial_original(prepared.get('contract'))
    phases = contract.get('gui_phases')
    if not isinstance(phases, list) or not phases:
        raise ValueError('Before-ARMED serial original prepared phases required')
    phase = text_field(json_object(phases[0]), 'id')
    waiting = _serial_argument(argv, '--wait-awaiting-seconds')
    diagnostic = 'Reviewed exact run/phase and the fixed1200-second reserve required'
    diagnostic_frame: str | None = None
    if label == 'CORE-GUARD-0':
        if re.fullmatch('[1-9][0-9]{0,8}', waiting) is None or int(waiting) <= 5400:
            raise ValueError('Before-ARMED serial refusal requires the actual unsupported wait bound')
    else:
        product = text_field(prepared, 'product')
        if (ready.get('schema') != 'ck3-mod-acceptance-run-context-v1'
                or ready.get('run_id') != previous.name or ready.get('case') != 'cold_reload'
                or ready.get('product') != product or Path(text_field(ready, 'run_dir')).resolve() != previous
                or prepared.get('schema') != 'ck3-mod-acceptance-prepared-case-v1'
                or prepared.get('case') != 'cold_reload'
                or contract.get('schema') != 'ck3-mod-acceptance-product-case-v1'
                or contract.get('product') != product or contract.get('case_id') != 'cold_reload'
                or re.fullmatch('[1-9][0-9]{0,8}', waiting) is None or int(waiting) > 5400):
            raise ValueError('Cold before-ARMED refusal requires the original prepared cold_reload and supported wait')
        diagnostic = 'Actual allocated ready-context crossed exact live/run/product/case'
        bound = ast.parse("if (live.name != args.run_id or not args.phase.replace('-', '').isalnum() "
            "or args.reserve_seconds != 1200 or not 0 < args.wait_awaiting_seconds <= 5400):\n"
            "    raise ValueError('Reviewed exact run/phase and the fixed1200-second reserve required')\n").body[0]
        crossed = ast.parse("if (not isinstance(ready, dict) or ready.get('schema') != 'ck3-mod-acceptance-run-context-v1' "
            "or ready.get('run_id') != args.run_id or Path(str(ready.get('run_dir', ''))).resolve() != live "
            "or ready.get('product') != "+repr(product)+" or ready.get('case') != 'core'):\n"
            "    raise ValueError("+repr(diagnostic)+")\n").body[0]
        mains = [node for node in ast.parse(guard_raw).body if isinstance(node, ast.FunctionDef) and node.name == 'main']
        if len(mains) != 1:
            raise ValueError('Cold before-ARMED original guard main required')
        bounds = [node for node in mains[0].body if ast.dump(node) == ast.dump(bound)]
        cases = [node for node in mains[0].body if ast.dump(node) == ast.dump(crossed)]
        if len(bounds) != 1 or len(cases) != 1 or bounds[0].lineno >= cases[0].lineno:
            raise ValueError('Cold before-ARMED original core-case refusal AST differs')
        if not isinstance(cases[0], ast.If):
            raise ValueError('Cold before-ARMED original case condition required')
        diagnostic_frame = 'File "'+guard['path']+'", line '+str(cases[0].body[0].lineno)+', in main'
    expected = ('--live', str(previous), '--ready-context', str(previous/'ready-context.json'),
        '--run-id', previous.name, '--phase', phase, '--reserve-seconds', '1200',
        '--wait-awaiting-seconds', waiting, '--armed', str(output/(label+'.ARMED.actual.json')),
        '--output', str(output/(label+'.actual.json')))
    if argv[6:] != expected:
        raise ValueError('Before-ARMED serial original first phase/live/argv differs')
    error = repr(RuntimeError('Original child ended before '+str(output/(label+'.ARMED.actual.json'))))
    stdout = _serial_raw(row.get('stdout'), output/(label+'.stdout.log'))
    stderr = _serial_raw(row.get('stderr'), output/(label+'.stderr.log')).decode('utf-8')
    if (failure.get('error') != error or stdout != b''
            or not stderr.replace('\r\n', '\n').endswith('ValueError: '+diagnostic+'\n')
            or guard['path'] not in stderr or (diagnostic_frame is not None and diagnostic_frame not in stderr)):
        raise ValueError('Original before-ARMED serial startup diagnostic differs')
    failed_at = _timestamp(failure.get('observed_at_utc'), 'Serial startup failure')
    if not ready_at <= child.started_at <= failed_at <= child.finished_at <= root_finished_at:
        raise ValueError('Before-ARMED serial guard/failure chronology differs')
    evidence.update({'serial_guard_prepared':prepared_ref, 'serial_guard_contract':contract_ref,
        label+'.stdout':file_pin(row.get('stdout')), label+'.stderr':file_pin(row.get('stderr'))})
    return child


def _serial_cleanup_waits(bundle: Mapping[str, object]) -> JsonObject:
    guards = bundle.get('serial_guards')
    if not isinstance(guards, list) or not guards:
        raise ValueError('Actual serial guard original waits required')
    codes: list[int] = []
    for guard in guards:
        _, waited = _serial_original(json_object(guard).get('original_wait'))
        code = _integer(waited.get('original_wait_returncode'), 'Serial cleanup guard original wait')
        if code != 1:
            raise ValueError('Serial cleanup cannot change the actual guard wait1')
        codes.append(code)
    return json_object({'receipt_format':SERIAL_PRELAUNCH_FORMAT, 'original_root_exit_code':1,
        'original_allocator_exit_code':0, 'guard_original_wait_codes':codes,
        'normal_close_qualified':False, 'release_pass':False})


def validate_serial_prelaunch(bundle: Mapping[str, object], *, previous: Path,
        keeper: Path, machine: str, ready_at: datetime, keeper_closed_at: datetime) -> dict[str, FilePin]:
    """Consume known original waits before Game; no idle or unknown-wait fiction."""
    if bundle.get('closure_kind') != PRELAUNCH_KIND or bundle.get('receipt_format') != SERIAL_PRELAUNCH_FORMAT:
        raise ValueError('Serial receipt format crossed prelaunch terminal states')
    guard_state = _prelaunch_guard_state(bundle)
    evidence: dict[str, FilePin] = {}
    for key in ('prelaunch_orchestrator_source', 'prelaunch_orchestrator_started',
            'prelaunch_orchestrator_wait', 'serial_root_stdout', 'serial_root_stderr', 'serial_static',
            'serial_failure', 'serial_release_original'):
        evidence[key] = file_pin(bundle.get(key))
    source = evidence['prelaunch_orchestrator_source']
    source_raw = _serial_raw(source)
    tree = ast.parse(source_raw.decode('utf-8-sig'))
    if not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
               and node.func.attr == 'Popen' for node in ast.walk(tree)):
        raise ValueError('Original serial source lacks its Popen producer')
    if not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
               and node.func.attr == 'wait' for node in ast.walk(tree)):
        raise ValueError('Original serial source lacks its retained wait consumer')
    root_wait = Path(evidence['prelaunch_orchestrator_wait']['path'])
    root_start, root_stdout_path, root_stderr_path = _serial_root_paths(root_wait)
    start_pin, start = _serial_original(evidence['prelaunch_orchestrator_started'], root_start)
    _, wait = _serial_original(evidence['prelaunch_orchestrator_wait'], root_wait)
    native_root = root_wait.name == 'INNER-ORIGINAL-WAIT.actual.json'
    start_fields = {'machine_id', 'pid', 'argv', 'started_at_utc', 'original_wait_pending'}
    wait_fields = {'machine_id', 'pid', 'argv', 'actual_original_popen_wait', 'original_wait_returncode', 'finished_at_utc'}
    if native_root:
        start_fields.add('process_creation_filetime_100ns')
        wait_fields.update({'process_creation_filetime_100ns', 'started_at_utc', 'elapsed_seconds'})
    if (set(start) != start_fields or set(wait) != wait_fields
            or start.get('machine_id') != machine or wait.get('machine_id') != machine
            or start.get('original_wait_pending') is not True or wait.get('actual_original_popen_wait') is not True
            or type(wait.get('original_wait_returncode')) is not int or wait['original_wait_returncode'] != 1
            or _integer(start.get('pid'), 'Serial root PID', 1) != _integer(wait.get('pid'), 'Serial root waited PID', 1)
            or strings_field(start, 'argv') != strings_field(wait, 'argv')):
        raise ValueError('Original serial root retained Popen wait1 differs')
    root_argv = tuple(strings_field(start, 'argv'))
    if len(root_argv) < 5 or root_argv[1:4] != ('-B', '-X', 'utf8') or Path(root_argv[4]).resolve() != Path(source['path']).resolve():
        raise ValueError('Original serial root source/argv differs')
    root_started = _timestamp(start.get('started_at_utc'), 'Serial root start')
    root_finished = _timestamp(wait.get('finished_at_utc'), 'Serial root wait')
    root_birth: str | None = None
    if native_root:
        root_birth = text_field(start, 'process_creation_filetime_100ns')
        elapsed = wait.get('elapsed_seconds')
        if (re.fullmatch('[1-9][0-9]{0,19}', root_birth) is None or int(root_birth) >= 1 << 64
                or wait.get('process_creation_filetime_100ns') != root_birth
                or wait.get('started_at_utc') != start.get('started_at_utc')
                or type(elapsed) not in (int, float) or not isinstance(elapsed, (int, float))
                or not math.isfinite(elapsed) or elapsed < 0
                or abs((root_finished-root_started).total_seconds()-elapsed) > 1):
            raise ValueError('Original native serial root birth/elapsed/wait identity differs')
        try:
            born = datetime.fromtimestamp(float((Decimal(root_birth)-116444736000000000)/10000000), timezone.utc)
        except (ValueError, OverflowError, OSError) as error:
            raise ValueError('Original native serial root FILETIME outside timestamp range') from error
        if not root_started <= born <= root_finished:
            raise ValueError('Original native serial root FILETIME chronology differs')
    root_process = SerialObservedProcess('root', 'ROOT-SERIAL', root_argv,
        _integer(start.get('pid'), 'Serial root PID', 1), root_birth, root_started, root_finished, 1)
    # Historical ROOT receipts retain their absent birth; INNER receipts retain
    # their exact native uint64 decimal FILETIME, with no synthetic projection.
    _, frozen = _serial_original(bundle.get('frozen'), previous/'frozen-argv.json')
    _, manifest = _serial_original(frozen.get('runtime_manifest'))
    commit = _serial_argument(root_argv, '--source-commit')
    if re.fullmatch('[a-f0-9]{40}', commit) is None or manifest.get('source_commit') != commit:
        raise ValueError('Original serial root commit differs from frozen runtime')
    allocated = _serial_allocator(bundle, machine, commit)
    allocator_terminal = _ttl_allocator_stdout(json_object({'allocator_stdout':bundle.get('allocator_stdout')}))
    _, keeper_parent = _serial_original(bundle.get('keeper_parent_exit'), previous/'keeper-actual-parent-exit.json')
    if (type(keeper_parent.get('keeper_actual_exit_code')) is not int
            or keeper_parent.get('keeper_actual_exit_code') != 0
            or any(allocator_terminal.get(key) != value for key, value in keeper_parent.items())):
        raise ValueError('Original serial allocator stdout crossed its internal keeper wait')
    output = Path(file_pin(bundle.get('allocator_intent'))['path']).parent
    _, failure = _serial_original(evidence['serial_failure'], output/'ROOT-SERIAL-FAILURE.actual.json')
    _, static = _serial_original(evidence['serial_static'], output/'STATIC-INPUTS-PRECOMPILED.actual.json')
    if (set(failure) != {'machine_id', 'observed_at_utc', 'error', 'public_started', 'display_before',
                        'no_automatic_replay', 'screen_CAS_attempted', 'original_handles'}
            or failure.get('machine_id') != machine or failure.get('public_started') is not False
            or failure.get('display_before') is not None or failure.get('no_automatic_replay') is not True
            or failure.get('screen_CAS_attempted') is not False or static.get('machine_id') != machine
            or static.get('source_commit') != commit or static.get('original_Popen_registry_retained') is not True):
        raise ValueError('Serial failure must preserve pre-public/pre-display state')
    for field, flag in (('grant', '--grant'), ('ready', '--ready')):
        ref = file_pin(static.get(field))
        _serial_raw(ref, Path(_serial_argument(root_argv, flag)))
        if ref['sha256'] != _serial_argument(root_argv, flag+'-sha256'):
            raise ValueError('Original serial launch input binding differs')
        evidence['serial_bound_'+field] = ref
    for field in ('capacity_original', 'guard_original', 'guard_interpreter'):
        ref = file_pin(static.get(field))
        _serial_raw(ref)
        evidence['serial_source_'+field] = ref
    processes = [allocated]
    if guard_state == 'failed-before-armed':
        processes.append(_serial_unarmed_guard(bundle, static, failure, previous=previous,
            output=output, machine=machine, commit=commit, ready_at=ready_at,
            root_finished_at=root_process.finished_at, evidence=evidence))
    else:
        for key in ('serial_capacity_start', 'serial_capacity_stdout', 'serial_capacity_refusal'):
            evidence[key] = file_pin(bundle.get(key))
        _, capacity = _serial_original(evidence['serial_capacity_start'], output/'CAPACITY-START.actual.json')
        cap_stdout = json_object(json.loads(_serial_raw(evidence['serial_capacity_stdout'], output/'CAPACITY.stdout.log')))
        refusal_ref, refusal = _serial_original(evidence['serial_capacity_refusal'])
        if (file_pin(cap_stdout.get('refusal')) != refusal_ref or refusal.get('schema') != 'rrf-parameterized-prelaunch-refusal-v1'
                or refusal.get('machine_id') != machine or refusal.get('no_automatic_retry') is not True
                or refusal.get('receipt_exists') is not False or refusal.get('error') != failure.get('error')
                or Path(text_field(refusal, 'requested_receipt')).exists()
                or capacity.get('machine_id') != machine or capacity.get('derived_source_sha256') != static.get('capacity_source_sha256')):
            raise ValueError('Actual serial mechanical prelaunch refusal differs')
        cap_argv = tuple(strings_field(capacity, 'argv'))
        if _serial_argument(cap_argv, '--output') != refusal.get('requested_receipt'):
            raise ValueError('Original capacity refusal crossed the requested output')
        guards = bundle.get('serial_guards')
        phases, phase_evidence = _serial_prepared_phases(bundle, previous, output)
        evidence.update(phase_evidence)
        if not isinstance(guards, list) or len(guards) != len(phases):
            raise ValueError('Every actual Prepared phase needs its original serial guard')
        for index, raw in enumerate(guards):
            row = json_object(raw)
            label = 'COLD-GUARD-'+str(index)
            if set(row) != {'label', 'intent', 'started', 'original_wait', 'armed', 'stdout', 'stderr'} or row.get('label') != label:
                raise ValueError('Exact consecutive serial guard role required')
            originals: dict[str, JsonObject] = {}
            for key, suffix in (('intent', '.intent.actual.json'), ('started', '.started.actual.json'),
                    ('original_wait', '.original-wait.actual.json'), ('armed', '.ARMED.actual.json')):
                ref, originals[key] = _serial_original(row.get(key), output/(label+suffix))
                evidence[label+'.'+key] = ref
            child = _serial_child(originals['intent'], originals['started'], originals['original_wait'],
                machine, commit, 'guard', label, 1)
            armed = originals['armed']
            if (armed.get('schema') != 'root-external-deadline-guard-armed-v1' or armed.get('machine_id') != machine
                    or armed.get('run_id') != previous.name or Path(text_field(armed, 'live')).resolve() != previous
                    or file_pin(armed.get('ready_context')) != file_pin(bundle.get('ready'))
                    or type(armed.get('pid')) is not int or armed.get('pid') != child.pid
                    or armed.get('process_creation_filetime_100ns') != child.birth_filetime
                    or armed.get('birth_source') != 'GetProcessTimes(GetCurrentProcess)'
                    or armed.get('state') != 'WAITING_FOR_ACTUAL_FROZEN_AND_PHASE'
                    or type(armed.get('reserve_seconds')) is not int or armed.get('reserve_seconds') != 1200
                    or type(armed.get('wait_awaiting_seconds')) is not int or armed.get('wait_awaiting_seconds') != 5400
                    or armed.get('game_or_queue_action_sent') is not False or armed.get('deadline_bound') is not False
                    or armed.get('phase') != phases[index]
                    or file_pin(armed.get('guard')) != file_pin(static.get('guard_original'))):
                raise ValueError('Original serial ARMED guard identity/action state differs')
            argv = child.argv
            if (len(argv) < 6 or argv[1:5] != ('-B', '-X', 'utf8', '-c')
                    or Path(argv[0]).resolve() != Path(file_pin(static.get('guard_interpreter'))['path']).resolve()):
                raise ValueError('Original serial guard interpreter/compile route differs')
            compiled = [node for node in ast.walk(ast.parse(argv[5])) if isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Name) and node.func.id == 'compile']
            if (len(compiled) != 1 or len(compiled[0].args) != 3 or not isinstance(compiled[0].args[0], ast.Constant)
                    or not isinstance(compiled[0].args[0].value, str)
                    or not isinstance(compiled[0].args[1], ast.Constant)
                    or compiled[0].args[1].value != file_pin(static.get('guard_original'))['path']
                    or not isinstance(compiled[0].args[2], ast.Constant) or compiled[0].args[2].value != 'exec'
                    or hashlib.sha256(argv[5].encode()).hexdigest() != static.get('guard_code_sha256')):
                raise ValueError('Original serial guard compiled source SHA differs')
            expected = {'--live':str(previous), '--ready-context':str(previous/'ready-context.json'),
                '--run-id':previous.name, '--phase':text_field(armed, 'phase'), '--reserve-seconds':'1200',
                '--wait-awaiting-seconds':'5400', '--armed':str(output/(label+'.ARMED.actual.json')),
                '--output':str(output/(label+'.actual.json'))}
            if any(_serial_argument(argv, flag) != value for flag, value in expected.items()) or (output/(label+'.actual.json')).exists():
                raise ValueError('Original serial guard crossed live/phase or sent an action')
            stdout = _serial_raw(row.get('stdout'), output/(label+'.stdout.log')).decode('utf-8').strip()
            if (not stdout.startswith('ROOT_DEADLINE_GUARD_ARMED ')
                    or file_pin(json.loads(stdout.removeprefix('ROOT_DEADLINE_GUARD_ARMED '))) != file_pin(row.get('armed'))
                    or _serial_raw(row.get('stderr'), output/(label+'.stderr.log')) != b''):
                raise ValueError('Original serial guard streams differ')
            if not ready_at <= child.started_at <= _timestamp(armed.get('armed_at_utc'), 'Guard armed') <= _timestamp(failure.get('observed_at_utc'), 'Root failure') <= child.finished_at <= root_process.finished_at:
                raise ValueError('Original serial guard/failure chronology differs')
            processes.append(child)
            evidence[label+'.stdout'] = file_pin(row.get('stdout'))
            evidence[label+'.stderr'] = file_pin(row.get('stderr'))
    handles = failure.get('original_handles')
    if not isinstance(handles, list) or len(handles) != len(processes):
        raise ValueError('Serial failure retained Popen roles are incomplete')
    root_stdout = _serial_raw(evidence['serial_root_stdout'], root_stdout_path).decode('utf-8')
    _serial_raw(evidence['serial_root_stderr'], root_stderr_path)
    terminal_rows = [json_object(json.loads(line.removeprefix('ORIGINAL_WAIT_ACTUAL ')))
        for line in root_stdout.splitlines() if line.startswith('ORIGINAL_WAIT_ACTUAL ')]
    if (len(terminal_rows) != len(processes) or root_stdout.splitlines().count('ACTUAL_READY '+previous.name) != 1
            or any(line.startswith('ACTUAL_PUBLIC') for line in root_stdout.splitlines())):
        raise ValueError('Actual serial stdout original waits are incomplete')
    for child, raw, terminal in zip(processes, handles, terminal_rows, strict=True):
        handle = json_object(raw)
        if (type(handle.get('pid')) is not int or type(terminal.get('pid')) is not int
                or type(terminal.get('returncode')) is not int or terminal.get('receipt_written') is not True
                or handle.get('original_wait_consumed') is not False or handle.get('actual_returncode') is not None
                or handle != {'label':child.label, 'pid':child.pid, 'birth_filetime':child.birth_filetime,
                       'original_wait_consumed':False, 'actual_returncode':None}
                or terminal != {'label':child.label, 'pid':child.pid, 'process_creation_filetime_100ns':child.birth_filetime,
                                'receipt_written':True, 'returncode':child.returncode}):
            raise ValueError('Serial failure and terminal stdout crossed retained Popen identities')
    if (not root_process.started_at <= allocated.started_at <= ready_at <= _timestamp(failure.get('observed_at_utc'), 'Failure')
            <= keeper_closed_at <= allocated.finished_at <= root_process.finished_at):
        raise ValueError('Original serial root/allocator/keeper chronology differs')
    if _serial_raw(bundle.get('keeper_STOP'), keeper/'STOP').decode('utf-8').replace('\r\n','\n') != 'Root pre-public failure; original allocation proves own never-Game keeper; no continuation qualification.\n':
        raise ValueError('Original serial cooperative STOP differs')
    for name in ('PUBLIC-RUN.intent.actual.json', 'PUBLIC-RUN.started.actual.json', 'LAUNCH-GATES-CONSUMED.actual.json',
            'DISPLAY-MODE.actual.json', 'STEAM-OFFLINE.prelaunch.actual.json'):
        if (output/name).exists():
            raise ValueError('Serial predecessor has later public/display/Steam activity')
    _, original_release = _serial_original(evidence['serial_release_original'])
    allocator = _serial_resources()
    actual_release = json_object(allocator.read_failed_runtime_release(Path(evidence['serial_release_original']['path'])))
    canonical_cas = json_object(allocator.read_failed_runtime_release(Path(file_pin(bundle.get('CAS_release'))['path'])))
    if (any(actual_release.get(key) != canonical_cas.get(key) for key in ('schema','ok','task','event'))
            or original_release.get('ok') is not True):
        raise ValueError('Original serial screen release differs from canonical closure')
    if guard_state == 'failed-before-armed' or 'serial_admin_original' in bundle:
        admin_pin, _ = _serial_original(bundle.get('serial_admin_original'))
        original_admin = json_object(allocator.read_failed_runtime_release(Path(admin_pin['path'])))
        done = json_object(allocator.read_failed_runtime_release(Path(file_pin(bundle.get('admin_done'))['path'])))
        if any(original_admin.get(key) != done.get(key) for key in ('schema','ok','task','event')):
            raise ValueError('Original serial administrative DONE differs from canonical closure')
        evidence['serial_admin_original'] = admin_pin
    return evidence


class PrelaunchPhaseGuardEvidence(TypedDict):
    label: str
    phase: str
    intent: FilePin
    started: FilePin
    armed: FilePin
    cancel: FilePin
    original_wait: FilePin


def _phase_guard_evidence(output: Path) -> list[PrelaunchPhaseGuardEvidence]:
    """Pin complete, consecutive original phase guards, without synthesizing waits."""
    suffixes = ('.intent.actual.json', '.started.actual.json', '.ARMED.actual.json',
        '.CANCEL.actual.json', '.original-wait.actual.json', '.stdout.log', '.stderr.log')
    found = list(output.glob('DEADLINE-GUARD-*'))
    if not found:
        return []
    labels = tuple('DEADLINE-GUARD-' + str(index) for index in range(1, len(found) // len(suffixes) + 1))
    if {path.name for path in found} != {label + suffix for label in labels for suffix in suffixes}:
        raise ValueError('Exact consecutive complete additional original phase guard file sets required')
    rows: list[PrelaunchPhaseGuardEvidence] = []
    for label in labels:
        armed = json_object(_read(output / (label + '.ARMED.actual.json')))
        rows.append(PrelaunchPhaseGuardEvidence(label=label, phase=text_field(armed, 'phase'),
            intent=file_pin(pin(output / (label + '.intent.actual.json'))),
            started=file_pin(pin(output / (label + '.started.actual.json'))),
            armed=file_pin(pin(output / (label + '.ARMED.actual.json'))),
            cancel=file_pin(pin(output / (label + '.CANCEL.actual.json'))),
            original_wait=file_pin(pin(output / (label + '.original-wait.actual.json')))))
    return rows


def _observed_phase_guards(bundle: Mapping[str, object], invocation: RootPrelaunchInvocation,
        output: Path, previous: Path, machine: str, ready_at: datetime,
        failure_at: datetime, base_phase: str) -> dict[str, FilePin]:
    rows = _phase_guard_evidence(output)
    if not rows:
        if 'prelaunch_phase_guards' in bundle:
            raise ValueError('Unexpected additional phase guard evidence')
        if 'prelaunch_orchestrator_intent' not in bundle:
            return {}
    if rows and bundle.get('prelaunch_phase_guards') != rows:
        raise ValueError('Original additional phase guard pins changed')
    ready = json_object(_pinned_object(bundle.get('ready'), 'Original allocated ready'))
    prepared = json_object(_pinned_object(ready.get('prepared_case'), 'Original prepared case'))
    contract = json_object(_pinned_object(prepared.get('contract'), 'Original prepared contract'))
    phases_value = contract.get('gui_phases')
    if not isinstance(phases_value, list) or len(phases_value) != len(rows) + 1:
        raise ValueError('Original prepared contract and phase guard count differ')
    phases = [text_field(json_object(value), 'id') for value in phases_value]
    if len(set(phases)) != len(phases) or phases != [base_phase, *(row['phase'] for row in rows)]:
        raise ValueError('Original phase guard order differs from prepared contract')
    evidence: dict[str, FilePin] = {}
    for row in rows:
        label = row['label']
        values: dict[str, JsonObject] = {}
        for key in ('intent', 'started', 'armed', 'cancel', 'original_wait'):
            values[key] = json_object(_pinned_object(row[key], 'Original phase guard ' + key))
        intent, started, armed, cancel, waited = (values[key] for key in values)
        if (set(intent) != {'machine_id', 'observed_at_utc', 'argv', 'source_commit'}
                or set(started) != {'machine_id', 'observed_at_utc', 'argv', 'pid', 'process_creation_filetime_100ns', 'initial_exit_code', 'original_wait_pending'}
                or set(armed) != {'schema','machine_id','run_id','live','ready_context','pid','process_creation_filetime_100ns','birth_source','guard','armed_at_utc','phase','state','wait_awaiting_seconds','reserve_seconds','game_or_queue_action_sent','deadline_bound'}
                or set(cancel) != {'machine_id', 'observed_at_utc', 'pid', 'reason'}
                or set(waited) != {'machine_id', 'observed_at_utc', 'original_wait_returncode', 'argv', 'pid'}
                or any(value.get('machine_id') != machine for value in values.values())):
            raise ValueError('Exact original additional phase guard fields required')
        wrapper = _integer(started.get('pid'), 'Phase guard wrapper pid', 1)
        actual = _integer(armed.get('pid'), 'Phase guard actual pid', 1)
        births = [_text(value.get('process_creation_filetime_100ns'), 'Original phase guard birth') for value in (started, armed)]
        if (any(re.fullmatch(r'[1-9][0-9]*', birth) is None or int(birth) > 18446744073709551615 for birth in births)
                or (wrapper == actual and births[0] != births[1])
                or any(_integer(value.get('pid'), 'Original canceled/waited phase pid', 1) != wrapper for value in (cancel, waited))
                or started.get('original_wait_pending') is not True
                or _integer(started.get('initial_exit_code'), 'Original phase guard active') != 259
                or _integer(waited.get('original_wait_returncode'), 'Original phase guard wait') != 1
                or cancel.get('reason') != 'Actual mechanical prelaunch failure; no Game action'):
            raise ValueError('Original phase guard identity/cancellation/wait differs')
        guard = _evidence_pin(armed.get('guard'), 'Original phase guard source')
        check_pin(Path(guard['path']), dict(guard))
        if (Path(guard['path']).resolve() != invocation.guard or armed.get('phase') != row['phase']
                or armed.get('schema') != 'root-external-deadline-guard-armed-v1'
                or armed.get('run_id') != previous.name or Path(text_field(armed, 'live')).resolve() != previous
                or _evidence_pin(armed.get('ready_context'), 'Original phase ready') != _evidence_pin(bundle.get('ready'), 'Original ready')
                or armed.get('birth_source') != 'GetProcessTimes(GetCurrentProcess)'
                or armed.get('state') != 'WAITING_FOR_ACTUAL_FROZEN_AND_PHASE'
                or armed.get('game_or_queue_action_sent') is not False or armed.get('deadline_bound') is not False
                or _integer(armed.get('reserve_seconds'), 'Original phase reserve', 1) != 1200
                or _integer(armed.get('wait_awaiting_seconds'), 'Original phase waiting bound', 1) != 5400):
            raise ValueError('Original phase guard crossed source/run or sent action')
        argv = strings_field(started, 'argv')
        expected = ['-B','-X','utf8',guard['path'],'--live',str(previous),'--ready-context',str(previous/'ready-context.json'),
            '--run-id',previous.name,'--phase',row['phase'],'--reserve-seconds','1200','--wait-awaiting-seconds','5400',
            '--armed',str(output/(label+'.ARMED.actual.json')),'--output',str(output/(label+'.actual.json'))]
        if (argv[1:] != expected or strings_field(intent, 'argv') != argv or strings_field(waited, 'argv') != argv
                or intent.get('source_commit') != invocation.source_commit):
            raise ValueError('Original phase guard argv/source differs')
        stamps = [invocation.started_at, ready_at, _timestamp(intent.get('observed_at_utc'), 'Original phase intent'),
            _timestamp(started.get('observed_at_utc'), 'Original phase start'), _timestamp(armed.get('armed_at_utc'), 'Original phase armed'),
            failure_at, _timestamp(cancel.get('observed_at_utc'), 'Original phase cancel'),
            _timestamp(waited.get('observed_at_utc'), 'Original phase wait'), invocation.finished_at]
        if stamps != sorted(stamps) or any(stamp.utcoffset() != timezone.utc.utcoffset(stamp) for stamp in stamps):
            raise ValueError('Original phase guard chronology differs')
        import psutil
        if any(psutil.pid_exists(pid) for pid in (wrapper, actual)):
            raise ValueError('Original phase guard process still present; absence grants no wait code')
        for name, reference in (('intent', row['intent']), ('started', row['started']),
                ('armed', row['armed']), ('cancel', row['cancel']), ('original_wait', row['original_wait'])):
            evidence[label + '.' + name] = reference
    return evidence


def _root_prelaunch_invocation(bundle: Mapping[str, object], output: Path,
        keeper: Path, machine: str) -> RootPrelaunchInvocation:
    """Bind an original retained Root invocation, without an operator AST template."""
    source = _evidence_pin(bundle.get('prelaunch_orchestrator_source'), 'Root orchestrator source')
    source_path = Path(source['path'])
    if not source_path.is_absolute() or source_path.is_symlink() or not 0 < source['bytes'] <= 1048576:
        raise ValueError('Bounded original Root orchestrator source required')
    check_pin(source_path, dict(source))
    started = json_object(_pinned_object(bundle.get('prelaunch_orchestrator_started'), 'Root original start'))
    waited = json_object(_pinned_object(bundle.get('prelaunch_orchestrator_wait'), 'Root original wait'))
    fields = {'machine_id', 'source_commit', 'pid', 'process_birth_seconds', 'argv', 'started_at_utc'}
    split_fields = {'machine_id', 'source_commit', 'pid', 'process_create_time_seconds', 'argv',
        'observed_at_utc', 'ambient_pythonpath_removed', 'original_wait_pending'}
    intent_split = 'prelaunch_orchestrator_intent' in bundle
    split = set(started) == split_fields
    elapsed_seconds = 0.0
    commit_value = started.get('source_commit')
    intent_at: datetime | None = None
    if intent_split:
        intent_ref = _evidence_pin(bundle.get('prelaunch_orchestrator_intent'), 'Root original intent')
        intent_path = Path(intent_ref['path']).resolve()
        intent = json_object(_pinned_object(intent_ref, 'Root original intent'))
        if (set(intent) != {'machine_id', 'observed_at_utc', 'argv', 'binding', 'ambient_pythonpath_removed', 'no_manual_sdk_import_path'}
                or set(started) != {'machine_id', 'observed_at_utc', 'argv', 'pid', 'process_create_time_seconds', 'original_wait_pending'}
                or set(waited) != {'machine_id', 'observed_at_utc', 'original_wait_returncode', 'elapsed_seconds', 'argv', 'pid'}
                or intent.get('machine_id') != machine
                or intent.get('ambient_pythonpath_removed') is not True
                or intent.get('no_manual_sdk_import_path') is not True
                or started.get('original_wait_pending') is not True):
            raise ValueError('Exact original intent-bound Root start/wait fields required')
        prefix = intent_path.name.removesuffix('.intent.actual.json')
        if (prefix == intent_path.name
                or Path(_evidence_pin(bundle.get('prelaunch_orchestrator_started'), 'Root start')['path']).resolve() != intent_path.with_name(prefix + '.started.actual.json')
                or Path(_evidence_pin(bundle.get('prelaunch_orchestrator_wait'), 'Root wait')['path']).resolve() != intent_path.with_name(prefix + '.original-wait.actual.json')
                or strings_field(intent, 'argv') != strings_field(started, 'argv')
                or strings_field(waited, 'argv') != strings_field(started, 'argv')
                or _integer(waited.get('pid'), 'Root original waited pid', 1) != _integer(started.get('pid'), 'Root original started pid', 1)):
            raise ValueError('Original intent-bound Root invocation crossed original files or identity')
        binding = json_object(_pinned_object(intent.get('binding'), 'Root original launch binding'))
        if (binding.get('machine_id') != machine
                or _evidence_pin(binding.get('orchestrator'), 'Bound Root orchestrator') != source
                or _evidence_pin(binding.get('public_recorder'), 'Bound Root recorder') != _evidence_pin(bundle.get('allocator_command'), 'Root public recorder')):
            raise ValueError('Original Root launch binding machine or producer differs')
        commit_value = binding.get('source_commit')
        intent_at = _timestamp(intent.get('observed_at_utc'), 'Root original intent')
        birth = _text(started.get('process_create_time_seconds'), 'Root original birth')
        began = _timestamp(started.get('observed_at_utc'), 'Root original start')
        ended = _timestamp(waited.get('observed_at_utc'), 'Root original finish')
        elapsed = waited.get('elapsed_seconds')
        if type(elapsed) not in (int, float) or not isinstance(elapsed, (int, float)) or not math.isfinite(elapsed) or elapsed < 0:
            raise ValueError('Original Root elapsed must be a finite nonnegative number')
        elapsed_seconds = float(elapsed)
    elif split:
        if (set(waited) != {'machine_id', 'observed_at_utc', 'original_wait_returncode', 'elapsed_seconds'}
                or started.get('ambient_pythonpath_removed') is not True
                or started.get('original_wait_pending') is not True):
            raise ValueError('Exact original split Root start/wait fields required')
        birth = _text(started.get('process_create_time_seconds'), 'Root original birth')
        began = _timestamp(started.get('observed_at_utc'), 'Root original start')
        ended = _timestamp(waited.get('observed_at_utc'), 'Root original finish')
        elapsed = waited.get('elapsed_seconds')
        if type(elapsed) not in (int, float) or not isinstance(elapsed, (int, float)) or not math.isfinite(elapsed) or elapsed < 0:
            raise ValueError('Original Root elapsed must be a finite nonnegative number')
        elapsed_seconds = float(elapsed)
    else:
        if (set(started) != fields or set(waited) != fields | {'finished_at_utc', 'original_wait_returncode'}
                or any(started.get(key) != waited.get(key) for key in fields)):
            raise ValueError('Exact original Root start/wait1 identity required')
        birth = _text(started.get('process_birth_seconds'), 'Root original birth')
        began = _timestamp(started.get('started_at_utc'), 'Root original start')
        ended = _timestamp(waited.get('finished_at_utc'), 'Root original finish')
    if (started.get('machine_id') != machine or waited.get('machine_id') != machine
            or _integer(waited.get('original_wait_returncode'), 'Root original exit') != 1):
        raise ValueError('Original Root machine/wait1 differs')
    _integer(started.get('pid'), 'Root original pid', 1)
    commit = _text(commit_value, 'Root original source commit')
    if re.fullmatch(r'[1-9][0-9]*(?:\.[0-9]+)?', birth) is None or re.fullmatch(r'[a-f0-9]{40}', commit) is None:
        raise ValueError('Canonical Root process/source identity required')
    if began > ended:
        raise ValueError('Root original wait chronology differs')
    if split or intent_split:
        born = datetime.fromtimestamp(float(Decimal(birth)), timezone.utc)
        if born > began or (intent_at is not None and intent_at > born) or abs((ended - born).total_seconds() - elapsed_seconds) > 1:
            raise ValueError('Original split Root birth/elapsed chronology differs')
    frozen = json_object(_pinned_object(bundle.get('frozen'), 'Original Root frozen inputs'))
    manifest = json_object(_pinned_object(frozen.get('runtime_manifest'), 'Original Root runtime manifest'))
    if manifest.get('source_commit') != commit:
        raise ValueError('Original Root source commit differs from frozen runtime')
    argv = strings_field(started, 'argv')
    if len(argv) < 6 or argv[1:4] != ['-B', '-X', 'utf8'] or Path(argv[4]).resolve() != source_path.resolve():
        raise ValueError('Original Root invocation source differs')

    def argument(name: str) -> str:
        if argv.count(name) != 1 or argv.index(name) + 1 >= len(argv):
            raise ValueError('Exact original Root argument required: ' + name)
        return argv[argv.index(name) + 1]

    if intent_split:
        binding_pin = _evidence_pin(intent.get('binding'), 'Original Root launch binding')
        if (Path(argument('--input-binding')).resolve() != Path(binding_pin['path']).resolve()
                or argument('--input-binding-sha256') != binding_pin['sha256']):
            raise ValueError('Original Root arguments crossed launch binding')
    command = _evidence_pin(bundle.get('allocator_command'), 'Root public recorder')
    if (argument('--mode') != 'launch' or argv.count('--execute-root-reviewed-launch') != 1
            or Path(argument('--repo-root')).resolve() != Path(text_field(frozen, 'source_root')).resolve()
            or Path(argument('--out')).resolve() != output
            or Path(argument('--keeper-output')).resolve() != keeper
            or Path(argument('--public-recorder')).resolve() != Path(command['path']).resolve()):
        raise ValueError('Original Root invocation crossed output/keeper/recorder')
    scene = Path(argument('--scene-root')).resolve()
    if not output.is_relative_to(scene) or not keeper.is_relative_to(scene):
        raise ValueError('Original Root invocation crossed scene')
    return RootPrelaunchInvocation(tuple(argv), began, ended, Path(argument('--deadline-guard')).resolve(), commit)


def _observed_guard_failed_before_armed(bundle: Mapping[str, object], invocation: RootPrelaunchInvocation,
        output: Path, previous: Path, keeper: Path, machine: str, ready_at: datetime,
        keeper_closed_at: datetime) -> dict[str, FilePin]:
    """Close an observed startup failure; absence never supplies an ARMED or wait."""
    if 'prelaunch_orchestrator_intent' not in bundle:
        raise ValueError('Before-ARMED recovery requires the original intent-bound Root')
    forbidden = ('DEADLINE-GUARD.ARMED.actual.json', 'DEADLINE-GUARD.CANCEL.actual.json',
        'DEADLINE-GUARD.actual.json', 'ORCHESTRATOR.PUBLIC-RUN.intent.actual.json',
        'ORCHESTRATOR.PUBLIC-RUN.started.actual.json', 'PUBLIC-RUN.intent.actual.json',
        'LAUNCH-GATES-CONSUMED.actual.json')
    if (any((output / name).exists() for name in forbidden) or list(output.glob('DEADLINE-GUARD-*'))
            or any(key in bundle for key in ('prelaunch_guard_armed', 'prelaunch_guard_cancel', 'prelaunch_phase_guards'))):
        raise ValueError('Before-ARMED recovery has armed/canceled/later guard or public evidence')
    names = {'prelaunch_failure': 'ORCHESTRATOR.failure.actual.json',
        'prelaunch_guard_intent': 'DEADLINE-GUARD.intent.actual.json',
        'prelaunch_guard_started': 'DEADLINE-GUARD.started.actual.json',
        'prelaunch_guard_wait': 'DEADLINE-GUARD.original-wait.actual.json',
        'prelaunch_allocator_wait': 'ORCHESTRATOR.ALLOCATE.original-wait.actual.json',
        'prelaunch_guard_stdout': 'DEADLINE-GUARD.stdout.log',
        'prelaunch_guard_stderr': 'DEADLINE-GUARD.stderr.log'}
    evidence: dict[str, FilePin] = {}
    for key, name in names.items():
        reference = _evidence_pin(bundle.get(key), key)
        if Path(reference['path']).resolve() != output / name:
            raise ValueError('Before-ARMED original output differs: ' + key)
        check_pin(Path(reference['path']), dict(reference))
        evidence[key] = reference
    failure, intent, started, waited, allocated = [json_object(_pinned_object(evidence[key], key))
        for key in ('prelaunch_failure', 'prelaunch_guard_intent', 'prelaunch_guard_started',
            'prelaunch_guard_wait', 'prelaunch_allocator_wait')]
    shapes = ({'machine_id','observed_at_utc','error','public_started','normal_closed','business_pass','no_automatic_replay','no_manual_case_client_created'},
        {'machine_id','observed_at_utc','argv','source_commit'},
        {'machine_id','observed_at_utc','argv','pid','process_creation_filetime_100ns','initial_exit_code','original_wait_pending'},
        {'machine_id','observed_at_utc','original_wait_returncode','argv','pid'},
        {'machine_id','observed_at_utc','original_wait_returncode','argv','pid'})
    if any(set(row) != shape or row.get('machine_id') != machine
            for row, shape in zip((failure, intent, started, waited, allocated), shapes)):
        raise ValueError('Exact before-ARMED original fields/machine required')
    if (any(failure.get(key) is not False for key in ('public_started','normal_closed','business_pass'))
            or failure.get('no_automatic_replay') is not True or failure.get('no_manual_case_client_created') is not True
            or failure.get('error') != "ValueError('Original producer exited before publication')"
            or evidence['prelaunch_guard_stderr']['bytes'] == 0
            or evidence['prelaunch_guard_stdout']['bytes'] > 1048576 or evidence['prelaunch_guard_stderr']['bytes'] > 1048576):
        raise ValueError('Before-ARMED failure has no original bounded startup diagnostic')
    pid = _integer(started.get('pid'), 'Before-ARMED started pid', 1)
    birth = _text(started.get('process_creation_filetime_100ns'), 'Before-ARMED original birth')
    if (re.fullmatch(r'[1-9][0-9]*', birth) is None or int(birth) > 18446744073709551615
            or _integer(waited.get('pid'), 'Before-ARMED waited pid', 1) != pid
            or started.get('original_wait_pending') is not True
            or _integer(started.get('initial_exit_code'), 'Before-ARMED initial exit') != 259
            or _integer(waited.get('original_wait_returncode'), 'Before-ARMED original wait') != 1
            or _integer(allocated.get('original_wait_returncode'), 'Before-ARMED recorder wait') != 0):
        raise ValueError('Before-ARMED original identity/observed waits differ')
    root_intent = _pinned_object(bundle.get('prelaunch_orchestrator_intent'), 'Root original intent')
    binding = _pinned_object(root_intent.get('binding'), 'Root original launch binding')
    guard = _evidence_pin(binding.get('deadline_guard'), 'Original unarmed guard source')
    check_pin(Path(guard['path']), dict(guard))
    if Path(guard['path']).resolve() != invocation.guard:
        raise ValueError('Before-ARMED guard source crossed original Root binding')
    interpreter = _evidence_pin(binding.get('guard_interpreter'), 'Original guard interpreter')
    check_pin(Path(interpreter['path']), dict(interpreter))
    root_argv = invocation.argv
    if any(name in root_argv for name in ('--guard-interpreter', '--guard-interpreter-sha256')):
        for name, expected_value in (('--guard-interpreter', interpreter['path']),
                ('--guard-interpreter-sha256', interpreter['sha256'])):
            if root_argv.count(name) != 1 or root_argv.index(name) + 1 >= len(root_argv):
                raise ValueError('Exact original Root guard interpreter arguments required')
            actual_value = root_argv[root_argv.index(name) + 1]
            if (Path(actual_value).resolve() != Path(expected_value).resolve() if name == '--guard-interpreter'
                    else actual_value != expected_value):
                raise ValueError('Original Root guard interpreter crossed launch binding')
    ready = json_object(_pinned_object(bundle.get('ready'), 'Original allocated ready'))
    prepared = json_object(_pinned_object(ready.get('prepared_case'), 'Original prepared case'))
    contract = json_object(_pinned_object(prepared.get('contract'), 'Original prepared contract'))
    phases_value = contract.get('gui_phases')
    if not isinstance(phases_value, list) or not phases_value:
        raise ValueError('Before-ARMED original prepared phases required')
    phases = [text_field(json_object(value), 'id') for value in phases_value]
    if len(set(phases)) != len(phases):
        raise ValueError('Before-ARMED original prepared phases must be unique')
    argv = strings_field(started, 'argv')
    expected = ['-B','-X','utf8',guard['path'],'--live',str(previous),'--ready-context',str(previous/'ready-context.json'),
        '--run-id',previous.name,'--phase',phases[0],'--reserve-seconds','1200','--wait-awaiting-seconds','5400',
        '--armed',str(output/'DEADLINE-GUARD.ARMED.actual.json'),'--output',str(output/'DEADLINE-GUARD.actual.json')]
    if (not argv or Path(argv[0]).resolve() != Path(interpreter['path']).resolve()
            or argv[1:] != expected or strings_field(intent, 'argv') != argv or strings_field(waited, 'argv') != argv
            or intent.get('source_commit') != invocation.source_commit):
        raise ValueError('Before-ARMED original argv/first phase/source differs')
    recorder = _evidence_pin(bundle.get('allocator_command'), 'Original public recorder')
    binding_pin = _evidence_pin(root_intent.get('binding'), 'Original Root binding')
    if strings_field(allocated, 'argv')[1:] != ['-B','-X','utf8',recorder['path'],'allocate','--binding-sha256',binding_pin['sha256']]:
        raise ValueError('Before-ARMED original recorder invocation differs')
    _integer(allocated.get('pid'), 'Before-ARMED recorder pid', 1)
    stamps = [invocation.started_at, ready_at, _timestamp(intent.get('observed_at_utc'), 'Guard original intent'),
        _timestamp(started.get('observed_at_utc'), 'Guard original start'),
        _timestamp(waited.get('observed_at_utc'), 'Guard original wait'),
        _timestamp(failure.get('observed_at_utc'), 'Root original failure'), keeper_closed_at,
        _timestamp(_pinned_object(bundle.get('allocator_exit'), 'Original allocator wait').get('finished_at_utc'), 'Allocator original finish'),
        _timestamp(allocated.get('observed_at_utc'), 'Recorder original finish'), invocation.finished_at]
    if stamps != sorted(stamps) or any(stamp.utcoffset() != timezone.utc.utcoffset(stamp) for stamp in stamps):
        raise ValueError('Before-ARMED original failure/STOP/wait chronology differs')
    stop = _evidence_pin(bundle.get('keeper_STOP'), 'Original keeper STOP')
    check_pin(keeper/'STOP', dict(stop))
    if Path(stop['path']).resolve() != keeper/'STOP' or (keeper/'STOP').read_text(encoding='utf8') != 'Root mechanical prelaunch refused before public run.\n':
        raise ValueError('Before-ARMED original STOP differs')
    import psutil
    if psutil.pid_exists(pid):
        from ck3_mod_acceptance_launcher import process_identity
        from ck3_mod_acceptance_allocate import validate_failed_supervisor_generation
        try:
            current = json_object(process_identity(pid))
        except (OSError, ValueError, RuntimeError) as error:
            raise ValueError('Before-ARMED current native process generation unavailable') from error
        validate_failed_supervisor_generation({'pid': pid,
            'original_popen_identity': {'pid': pid, 'birth_filetime': birth}}, current)
    for key in ('prelaunch_orchestrator_source', 'prelaunch_orchestrator_intent',
            'prelaunch_orchestrator_started', 'prelaunch_orchestrator_wait'):
        evidence[key] = _evidence_pin(bundle.get(key), key)
    evidence['prelaunch_launch_binding'] = binding_pin
    evidence['prelaunch_guard_source'] = guard
    evidence['prelaunch_guard_interpreter'] = interpreter
    evidence['prelaunch_prepared_contract'] = _evidence_pin(prepared.get('contract'), 'Original prepared contract')
    return evidence


def _observed_prelaunch_orchestrator(bundle: Mapping[str, object], *, previous: Path,
        keeper: Path, machine: str, ready_at: datetime, keeper_closed_at: datetime) -> dict[str, FilePin]:
    """Read the real Root/child waits; a failed guard identity grants no guard credit."""
    output = Path(_evidence_pin(bundle.get('allocator_intent'), 'Root allocator intent')['path']).resolve().parent
    invocation = _root_prelaunch_invocation(bundle, output, keeper, machine)
    if _prelaunch_guard_state(bundle) == 'failed-before-armed':
        return _observed_guard_failed_before_armed(bundle, invocation, output, previous,
            keeper, machine, ready_at, keeper_closed_at)
    names = {'prelaunch_failure': 'ORCHESTRATOR.failure.actual.json',
        'prelaunch_guard_started': 'DEADLINE-GUARD.started.actual.json',
        'prelaunch_guard_armed': 'DEADLINE-GUARD.ARMED.actual.json',
        'prelaunch_guard_cancel': 'DEADLINE-GUARD.CANCEL.actual.json',
        'prelaunch_guard_wait': 'DEADLINE-GUARD.original-wait.actual.json',
        'prelaunch_allocator_wait': 'ORCHESTRATOR.ALLOCATE.original-wait.actual.json'}
    rows: dict[str, JsonObject] = {}
    for key, name in names.items():
        ref = _evidence_pin(bundle.get(key), key)
        if Path(ref['path']).resolve() != output / name:
            raise ValueError('Root prelaunch original output differs: ' + key)
        rows[key] = json_object(_pinned_object(ref, key))
    failure, started, armed, cancel, waited, allocated = (rows[key] for key in names)
    shapes = ({'machine_id','observed_at_utc','error','public_started','normal_closed','business_pass','no_automatic_replay','no_manual_case_client_created'},
        {'machine_id','observed_at_utc','argv','pid','process_creation_filetime_100ns','initial_exit_code','original_wait_pending'},
        {'schema','machine_id','run_id','live','ready_context','pid','process_creation_filetime_100ns','birth_source','guard','armed_at_utc','phase','state','wait_awaiting_seconds','reserve_seconds','game_or_queue_action_sent','deadline_bound'},
        {'machine_id','observed_at_utc','pid','reason'},
        {'machine_id','observed_at_utc','original_wait_returncode','argv','pid'},
        {'machine_id','observed_at_utc','original_wait_returncode','argv','pid'})
    if any(set(row) != shape or row.get('machine_id') != machine for row, shape in zip(rows.values(), shapes)):
        raise ValueError('Exact original observed Root prelaunch fields required')
    if (any(failure.get(key) is not False for key in ('public_started','normal_closed','business_pass'))
            or failure.get('no_automatic_replay') is not True or failure.get('no_manual_case_client_created') is not True
            or not _text(failure.get('error'), 'Original Root prelaunch error')):
        raise ValueError('Root prelaunch failure cannot grant public/business credit')
    wrapper = _integer(started.get('pid'), 'Original guard wrapper pid', 1)
    actual = _integer(armed.get('pid'), 'Original armed guard pid', 1)
    if (any(_integer(row.get('pid'), 'Original guard wrapper pid', 1) != wrapper for row in (cancel, waited))
            or started.get('original_wait_pending') is not True
            or _integer(started.get('initial_exit_code'), 'Original guard still active') != 259
            or _integer(waited.get('original_wait_returncode'), 'Original guard wrapper wait') != 1
            or _integer(allocated.get('original_wait_returncode'), 'Original recorder wait') != 0
            or cancel.get('reason') != 'Actual mechanical prelaunch failure; no Game action'):
        raise ValueError('Original Root cancellation/observed waits differ')
    births = [_text(row.get('process_creation_filetime_100ns'), 'Original native process birth') for row in (started, armed)]
    if any(re.fullmatch(r'[1-9][0-9]*', value) is None or int(value) > 18446744073709551615 for value in births):
        raise ValueError('Original native births must remain uint64 decimal strings')
    if wrapper == actual and births[0] != births[1]:
        raise ValueError('Same guard pid has different original native births')
    if (armed.get('schema') != 'root-external-deadline-guard-armed-v1' or armed.get('run_id') != previous.name
            or Path(text_field(armed, 'live')).resolve() != previous
            or _evidence_pin(armed.get('ready_context'), 'Original guard ready') != _evidence_pin(bundle.get('ready'), 'Allocated ready')
            or armed.get('birth_source') != 'GetProcessTimes(GetCurrentProcess)'
            or armed.get('state') != 'WAITING_FOR_ACTUAL_FROZEN_AND_PHASE'
            or armed.get('game_or_queue_action_sent') is not False or armed.get('deadline_bound') is not False
            or _integer(armed.get('reserve_seconds'), 'Guard reserve', 1) != 1200
            or _integer(armed.get('wait_awaiting_seconds'), 'Guard awaiting bound', 1) != 5400):
        raise ValueError('Original armed guard crossed run or sent action')
    guard = _evidence_pin(armed.get('guard'), 'Original guard source')
    check_pin(Path(guard['path']), dict(guard))
    if Path(guard['path']).resolve() != invocation.guard:
        raise ValueError('Original Root guard source differs')
    argv = strings_field(started, 'argv')
    expected = ['-B','-X','utf8',guard['path'],'--live',str(previous),'--ready-context',str(previous/'ready-context.json'),
        '--run-id',previous.name,'--phase',text_field(armed,'phase'),'--reserve-seconds','1200','--wait-awaiting-seconds','5400',
        '--armed',str(output/'DEADLINE-GUARD.ARMED.actual.json'),'--output',str(output/'DEADLINE-GUARD.actual.json')]
    if argv[1:] != expected or strings_field(waited, 'argv') != argv:
        raise ValueError('Original guard invocation/wait argv differs')
    recorder = _evidence_pin(bundle.get('allocator_command'), 'Original public recorder')
    outer_argv = strings_field(allocated, 'argv')
    expected_recorder = ['-B','-X','utf8',recorder['path'],'allocate']
    if 'prelaunch_orchestrator_intent' in bundle:
        root_intent = _pinned_object(bundle.get('prelaunch_orchestrator_intent'), 'Original Root intent')
        binding_pin = _evidence_pin(root_intent.get('binding'), 'Original Root launch binding')
        expected_recorder += ['--binding-sha256', binding_pin['sha256']]
    if outer_argv[1:] != expected_recorder:
        raise ValueError('Original Root public recorder invocation differs')
    _integer(allocated.get('pid'), 'Original public recorder pid', 1)
    stamps = [invocation.started_at, ready_at, _timestamp(started.get('observed_at_utc'), 'Original guard start'),
        _timestamp(armed.get('armed_at_utc'), 'Original guard armed'), _timestamp(failure.get('observed_at_utc'), 'Original prelaunch failure'),
        _timestamp(cancel.get('observed_at_utc'), 'Original guard cancel'), _timestamp(waited.get('observed_at_utc'), 'Original guard wait')]
    inner_end = _timestamp(_pinned_object(bundle.get('allocator_exit'), 'Original public allocator wait').get('finished_at_utc'), 'Original allocator finish')
    outer_end = _timestamp(allocated.get('observed_at_utc'), 'Original recorder finish')
    if (stamps != sorted(stamps) or not stamps[4] <= keeper_closed_at <= inner_end <= outer_end <= invocation.finished_at
            or any(stamp.utcoffset() != timezone.utc.utcoffset(stamp) for stamp in [*stamps, keeper_closed_at, inner_end, outer_end, invocation.finished_at])):
        raise ValueError('Original Root prelaunch STOP/wait chronology differs')
    stop = _evidence_pin(bundle.get('keeper_STOP'), 'Original keeper STOP')
    if Path(stop['path']).resolve() != keeper/'STOP':
        raise ValueError('Original Root STOP crossed keeper')
    check_pin(keeper/'STOP', dict(stop))
    if (keeper/'STOP').read_text(encoding='utf8') != 'Root mechanical prelaunch refused before public run.\n':
        raise ValueError('Original Root prelaunch STOP differs')
    forbidden = ('ORCHESTRATOR.PUBLIC-RUN.intent.actual.json','ORCHESTRATOR.PUBLIC-RUN.started.actual.json',
        'PUBLIC-RUN.intent.actual.json','LAUNCH-GATES-CONSUMED.actual.json','DEADLINE-GUARD.actual.json')
    if any((output/name).exists() for name in forbidden):
        raise ValueError('Original Root prelaunch output has later public/guard action evidence')
    phase_guards = _observed_phase_guards(bundle, invocation, output, previous, machine,
        ready_at, stamps[4], text_field(armed, 'phase'))
    import psutil
    if any(psutil.pid_exists(pid) for pid in (wrapper, actual)):
        raise ValueError('Original guard wrapper/armed process still present; absence grants no wait code')
    keys = [*names, 'prelaunch_orchestrator_source', 'prelaunch_orchestrator_started', 'prelaunch_orchestrator_wait']
    if 'prelaunch_orchestrator_intent' in bundle:
        keys.append('prelaunch_orchestrator_intent')
    evidence = {**{key: _evidence_pin(bundle.get(key), key) for key in keys}, **phase_guards}
    if 'prelaunch_orchestrator_intent' in bundle:
        intent = _pinned_object(bundle.get('prelaunch_orchestrator_intent'), 'Root original intent')
        evidence['prelaunch_launch_binding'] = _evidence_pin(intent.get('binding'), 'Root launch binding')
    return evidence


def _prelaunch_source(reference: object, output: Path, keeper: Path,
        allocator_command: object, machine: str) -> None:
    """Bind original failure/STOP/cancellation records to their real writer."""
    source = _evidence_pin(reference, 'Prelaunch orchestrator source')
    path = Path(source['path'])
    if not path.is_absolute() or path.is_symlink() or not 0 < source['bytes'] <= 1048576:
        raise ValueError('Bounded original prelaunch orchestrator source required')
    check_pin(path, dict(source))
    tree = ast.parse(path.read_text(encoding='utf-8-sig'))
    assignments = {node.targets[0].id: node.value for node in tree.body
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)}

    def location(node: ast.expr, seen: tuple[str, ...] = ()) -> Path:
        if isinstance(node, ast.Name) and node.id in assignments and node.id not in seen:
            return location(assignments[node.id], (*seen, node.id))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'Path' and len(node.args) == 1 and not node.keywords:
            return location(node.args[0], seen)
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return Path(node.value)
        if isinstance(node, ast.Attribute) and node.attr == 'parent':
            return location(node.value, seen).parent
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div) and isinstance(node.right, ast.Constant) and isinstance(node.right.value, str):
            return location(node.left, seen) / node.right.value
        raise ValueError('Prelaunch original source path expression differs')

    command = _evidence_pin(allocator_command, 'Prelaunch public recorder')
    required = {'OUT': output, 'keeper': keeper, 'PUBLIC': Path(command['path'])}
    machine_node = assignments.get('MACHINE')
    if any(name not in assignments or location(assignments[name]).resolve() != expected.resolve()
            for name, expected in required.items()) or not isinstance(machine_node, ast.Constant) or machine_node.value != machine:
        raise ValueError('Prelaunch original source machine/output/public recorder differs')
    signatures = ast.parse(r'''
def put(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump({'machine_id': MACHINE, 'at': datetime.now(timezone.utc).isoformat(), **value}, stream, indent=2)
        stream.write('\n')
def start(label, argv):
    out = (OUT / (label + '.stdout.log')).open('xb')
    err = (OUT / (label + '.stderr.log')).open('xb')
    child = subprocess.Popen(argv, cwd=REPO, stdout=out, stderr=err)
    put(OUT / (label + '.started.actual.json'), {'argv': argv, 'pid': child.pid, 'original_wait_pending': True})
    def wait():
        code = child.wait()
        out.close()
        err.close()
        put(OUT / (label + '.original-wait.actual.json'), {'original_wait_returncode': code})
    thread = threading.Thread(target=wait, daemon=False)
    thread.start()
    return child, thread
''').body
    for signature in signatures:
        if sum(ast.dump(node) == ast.dump(signature) for node in tree.body) != 1:
            raise ValueError('Prelaunch source original Popen/wait/exclusive publisher differs')
    allocation = ast.parse("allocate, allocate_thread = start('ORCHESTRATOR.ALLOCATE', [sys.executable, '-B', '-X', 'utf8', str(PUBLIC), 'allocate'])").body[0]
    if sum(ast.dump(node) == ast.dump(allocation) for node in tree.body) != 1:
        raise ValueError('Prelaunch source original public allocator invocation differs')
    expected = ast.parse(r'''
try:
    pass
except BaseException as error:
    put(OUT / 'ORCHESTRATOR.failure.actual.json', {'error': repr(error),
        'public_started': public_started, 'business_pass': False})
    print('ORCHESTRATOR_FAILURE_PRESERVED', repr(error), flush=True)
    if not public_started:
        if keeper.is_dir() and not (keeper / 'STOP').exists():
            (keeper / 'STOP').write_text('Root mechanical prelaunch refused before public run\n', encoding='utf-8')
        if guard is not None and guard.poll() is None:
            put(OUT / 'DEADLINE-GUARD.CANCEL.actual.json', {'pid': guard.pid,
                'reason': 'Mechanical prelaunch refused before public run; cancel retained Root helper'})
            guard.terminate()
finally:
    print('PUBLIC_STAGE_ENDED_KEEPER_REQUIRES_ROOT_CLOSURE', flush=True)
    if guard_thread is not None:
        guard_thread.join()
    allocate_thread.join()
    print('ALL_ORIGINAL_OPERATOR_CHILD_WAITS_CONSUMED', flush=True)
''').body[0]
    if not isinstance(expected, ast.Try):
        raise ValueError('Internal prelaunch source signature unavailable')
    tries = [node for node in tree.body if isinstance(node, ast.Try)]
    if len(tries) != 1 or [ast.dump(node) for node in tries[0].handlers] != [ast.dump(node) for node in expected.handlers] or [ast.dump(node) for node in tries[0].finalbody] != [ast.dump(node) for node in expected.finalbody]:
        raise ValueError('Prelaunch source failure/STOP/cancel/final original waits differ')
    required_imports = {'Path': ('pathlib', 'Path'), 'datetime': ('datetime', 'datetime'), 'timezone': ('datetime', 'timezone')}
    for name, (module, imported) in required_imports.items():
        found = [alias for node in tree.body if isinstance(node, ast.ImportFrom) and node.module == module and node.level == 0 for alias in node.names if alias.name == imported and alias.asname is None]
        if len(found) != 1:
            raise ValueError('Prelaunch source original imports differ')
    protected = {'json', 'subprocess', 'threading', 'datetime', 'timezone', 'Path', 'put', 'start'}
    for name in protected:
        definitions = [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == name]
        if len(definitions) != (1 if name in ('put', 'start') else 0):
            raise ValueError('Prelaunch source original callable binding differs')
    for name in ('json', 'subprocess', 'threading'):
        if sum(alias.name == name and alias.asname is None for node in tree.body if isinstance(node, ast.Import) for alias in node.names) != 1:
            raise ValueError('Prelaunch source original module imports differ')
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                if alias.name == '*':
                    raise ValueError('Prelaunch source wildcard import differs')
                bound = alias.asname or alias.name.split('.')[0]
                if bound in protected and alias.asname is not None:
                    raise ValueError('Prelaunch source original import alias differs')
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)) and node.id in protected:
            raise ValueError('Prelaunch source original imported binding was reassigned')
        if isinstance(node, ast.arg) and node.arg in protected or isinstance(node, ast.ExceptHandler) and node.name in protected:
            raise ValueError('Prelaunch source original binding was shadowed')
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ('exec', 'eval', 'globals', 'locals', 'setattr', 'delattr'):
            raise ValueError('Prelaunch source dynamic binding differs')
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.NamedExpr)) and isinstance(node.value, ast.Name) and node.value.id in protected:
            raise ValueError('Prelaunch source imported object alias differs')
        if isinstance(node, (ast.Attribute, ast.Subscript)) and isinstance(node.ctx, (ast.Store, ast.Del)):
            target = node.value
            while isinstance(target, (ast.Attribute, ast.Subscript)):
                target = target.value
            if isinstance(target, ast.Name) and target.id in protected:
                raise ValueError('Prelaunch source imported object mutation differs')
    writes = [node.value for node in ast.walk(tree) if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'public_started' for target in node.targets)]
    if [ast.dump(node) for node in writes] != [ast.dump(ast.Constant(False)), ast.dump(ast.Constant(True))]:
        raise ValueError('Prelaunch source public-started state differs')


def validate_prelaunch_orchestrator(bundle: Mapping[str, object], *, previous: Path,
        keeper: Path, machine: str, ready_at: datetime, keeper_closed_at: datetime) -> dict[str, FilePin]:
    """Validate an actual mechanical refusal; grant only administrative closure."""
    if 'receipt_format' in bundle:
        if bundle.get('receipt_format') != SERIAL_PRELAUNCH_FORMAT:
            raise ValueError('Unknown prelaunch original receipt format')
        return validate_serial_prelaunch(bundle, previous=previous, keeper=keeper, machine=machine,
            ready_at=ready_at, keeper_closed_at=keeper_closed_at)
    root_keys = ('prelaunch_orchestrator_started', 'prelaunch_orchestrator_wait')
    if _prelaunch_guard_state(bundle) == 'failed-before-armed' and not all(key in bundle for key in (*root_keys, 'prelaunch_orchestrator_intent')):
        raise ValueError('Before-ARMED recovery requires original Root intent/start/wait')
    if any(key in bundle for key in root_keys):
        if not all(key in bundle for key in root_keys):
            raise ValueError('Complete original Root orchestrator start/wait required')
        return _observed_prelaunch_orchestrator(bundle, previous=previous, keeper=keeper,
            machine=machine, ready_at=ready_at, keeper_closed_at=keeper_closed_at)
    intent_ref = _evidence_pin(bundle.get('allocator_intent'), 'Prelaunch allocator intent')
    output = Path(intent_ref['path']).resolve().parent
    _prelaunch_source(bundle.get('prelaunch_orchestrator_source'), output, keeper,
        bundle.get('allocator_command'), machine)
    names = {'prelaunch_failure': 'ORCHESTRATOR.failure.actual.json',
        'prelaunch_guard_started': 'DEADLINE-GUARD.started.actual.json',
        'prelaunch_guard_armed': 'DEADLINE-GUARD.ARMED.actual.json',
        'prelaunch_guard_cancel': 'DEADLINE-GUARD.CANCEL.actual.json',
        'prelaunch_guard_wait': 'DEADLINE-GUARD.original-wait.actual.json',
        'prelaunch_allocator_wait': 'ORCHESTRATOR.ALLOCATE.original-wait.actual.json'}
    rows: dict[str, JsonObject] = {}
    for key, filename in names.items():
        ref = _evidence_pin(bundle.get(key), key)
        if Path(ref['path']).resolve() != output / filename:
            raise ValueError('Prelaunch original output path differs: ' + key)
        rows[key] = json_object(_pinned_object(ref, key))
    failure, started, armed, cancel, waited, allocated = (rows[key] for key in names)
    shapes = ({'machine_id','at','error','public_started','business_pass'}, {'machine_id','at','argv','pid','original_wait_pending'},
        {'schema','machine_id','run_id','live','ready_context','pid','process_creation_filetime_100ns','birth_source','guard','armed_at_utc','phase','state','wait_awaiting_seconds','reserve_seconds','game_or_queue_action_sent','deadline_bound'},
        {'machine_id','at','pid','reason'}, {'machine_id','at','original_wait_returncode'}, {'machine_id','at','original_wait_returncode'})
    if any(set(row) != shape or row.get('machine_id') != machine for row, shape in zip(rows.values(), shapes)):
        raise ValueError('Exact original prelaunch fields/machine required')
    if failure.get('public_started') is not False or failure.get('business_pass') is not False or not _text(failure.get('error'), 'Prelaunch error'):
        raise ValueError('Prelaunch original failure cannot grant public/business credit')
    pid = _integer(started.get('pid'), 'Prelaunch guard pid', 1)
    if (_integer(cancel.get('pid'), 'Prelaunch canceled guard pid', 1) != pid or _integer(armed.get('pid'), 'Prelaunch armed guard pid', 1) != pid
            or started.get('original_wait_pending') is not True or _integer(waited.get('original_wait_returncode'), 'Prelaunch guard original wait') != 1
            or _integer(allocated.get('original_wait_returncode'), 'Prelaunch recorder original wait') != 0
            or cancel.get('reason') != 'Mechanical prelaunch refused before public run; cancel retained Root helper'):
        raise ValueError('Prelaunch original cancellation/observed waits differ')
    birth = _text(armed.get('process_creation_filetime_100ns'), 'Prelaunch guard native birth')
    if re.fullmatch(r'[1-9][0-9]*', birth) is None or int(birth) > 18446744073709551615:
        raise ValueError('Prelaunch guard birth must be canonical uint64 decimal')
    if (armed.get('schema') != 'root-external-deadline-guard-armed-v1' or armed.get('run_id') != previous.name
            or Path(text_field(armed, 'live')).resolve() != previous or _evidence_pin(armed.get('ready_context'), 'Prelaunch ready') != _evidence_pin(bundle.get('ready'), 'Allocated ready')
            or armed.get('birth_source') != 'GetProcessTimes(GetCurrentProcess)' or armed.get('state') != 'WAITING_FOR_ACTUAL_FROZEN_AND_PHASE'
            or armed.get('game_or_queue_action_sent') is not False or armed.get('deadline_bound') is not False
            or _integer(armed.get('reserve_seconds'), 'Prelaunch guard reserve', 1) != 1200
            or _integer(armed.get('wait_awaiting_seconds'), 'Prelaunch guard bound', 1) != 5400):
        raise ValueError('Prelaunch original armed guard crossed allocated scene or sent action')
    guard = _evidence_pin(armed.get('guard'), 'Prelaunch guard source')
    check_pin(Path(guard['path']), dict(guard))
    argv = strings_field(started, 'argv')
    expected_tail = ['-B','-X','utf8',guard['path'],'--live',str(previous),'--ready-context',str(previous/'ready-context.json'),
        '--run-id',previous.name,'--phase',text_field(armed,'phase'),'--reserve-seconds','1200','--wait-awaiting-seconds','5400',
        '--armed',str(output/'DEADLINE-GUARD.ARMED.actual.json'),'--output',str(output/'DEADLINE-GUARD.actual.json')]
    if len(argv) != len(expected_tail) + 1 or argv[1:] != expected_tail:
        raise ValueError('Prelaunch original guard argv differs')
    stamps = [ready_at, _timestamp(started.get('at'), 'Prelaunch guard start'), _timestamp(armed.get('armed_at_utc'), 'Prelaunch armed'),
        _timestamp(failure.get('at'), 'Prelaunch failure'), _timestamp(cancel.get('at'), 'Prelaunch cancel'),
        _timestamp(waited.get('at'), 'Prelaunch guard wait')]
    allocator_finish = _timestamp(_pinned_object(bundle.get('allocator_exit'), 'Prelaunch allocator wait').get('finished_at_utc'), 'Prelaunch allocator finished')
    outer_finish = _timestamp(allocated.get('at'), 'Prelaunch recorder finished')
    if stamps != sorted(stamps) or not stamps[3] <= keeper_closed_at <= allocator_finish <= outer_finish or any(stamp.utcoffset() != timezone.utc.utcoffset(stamp) for stamp in [*stamps, keeper_closed_at, allocator_finish, outer_finish]):
        raise ValueError('Prelaunch original failure/STOP/observed waits chronology differs')
    stop = _evidence_pin(bundle.get('keeper_STOP'), 'Prelaunch keeper STOP')
    if Path(stop['path']).resolve() != keeper/'STOP':
        raise ValueError('Prelaunch STOP crossed keeper')
    check_pin(keeper/'STOP', dict(stop))
    if (keeper/'STOP').read_text(encoding='utf8') != 'Root mechanical prelaunch refused before public run\n':
        raise ValueError('Prelaunch original STOP differs')
    if any((output/name).exists() for name in ('ORCHESTRATOR.PUBLIC-PRELUDE.started.actual.json','ORCHESTRATOR.READY-TO-RUN.actual.json',
            'PUBLIC-RUN.intent.actual.json','DEADLINE-GUARD.actual.json')):
        raise ValueError('Prelaunch original output has public/action evidence')
    return {key: _evidence_pin(bundle.get(key), key) for key in [*names, 'prelaunch_orchestrator_source']}


@runtime_checkable
class _UnrunProcessInventory(Protocol):
    def __call__(self, process_module: object, current_pid: int) -> object: ...


def _ttl_pin(path: Path) -> FilePin:
    if not path.is_absolute() or path.is_symlink() or not path.is_file() or path.stat().st_size > 1048576:
        raise ValueError('Bounded ordinary original TTL-refusal metadata required')
    raw = path.read_bytes()
    return FilePin(path=str(path.resolve()), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def _ttl_original(refs: JsonObject, key: str, expected: Path | None = None) -> tuple[FilePin, JsonObject]:
    ref = file_pin(refs.get(key))
    if set(json_object(refs[key])) != {'path', 'bytes', 'sha256'}:
        raise ValueError('Exact TTL-refusal original pin fields required: ' + key)
    path = Path(ref['path']).resolve()
    if (expected is not None and path != expected.resolve()) or _ttl_pin(path) != ref:
        raise ValueError('TTL-refusal original path or bytes changed: ' + key)
    return ref, json_object(json.loads(path.read_bytes()))


def _ttl_public_exit(value: JsonObject, machine: str,
        mode: Literal['run', 'allocate'], code: int) -> list[str]:
    """Read distinct original receipt formats without rewriting either one."""
    from ck3_mod_acceptance_allocate import validate_root_observed_public_exit
    if 'original_wait_returncode' not in value:
        return validate_root_observed_public_exit(value, machine, mode, code)
    fields = {'machine_id', 'argv', 'pid', 'process_create_time_seconds', 'started_at_utc',
              'original_wait_pending', 'original_wait_returncode', 'finished_at_utc'}
    birth, pid = value.get('process_create_time_seconds'), value.get('pid')
    if (set(value) != fields or value.get('machine_id') != machine
            or type(pid) is not int or not isinstance(pid, int) or pid <= 0
            or value.get('original_wait_pending') is not False
            or type(value.get('original_wait_returncode')) is not int or value['original_wait_returncode'] != code
            or not isinstance(birth, str) or re.fullmatch(r'[1-9][0-9]*(?:\.[0-9]+)?', birth) is None):
        raise ValueError('Original TTL-refusal public Popen wait identity differs')
    started = _timestamp(value.get('started_at_utc'), 'Original public Popen start')
    finished = _timestamp(value.get('finished_at_utc'), 'Original public Popen finish')
    epoch = finished - datetime(1970, 1, 1, tzinfo=timezone.utc)
    finished_seconds = Decimal(epoch.days * 86400 + epoch.seconds) + Decimal(epoch.microseconds) / Decimal(1000000)
    # Root can record started_at immediately before Popen or immediately after
    # it. Both the command observation and the OS birth must precede its wait.
    if started > finished or Decimal(birth) > finished_seconds:
        raise ValueError('Original public Popen chronology differs')
    argv = strings_field(value, 'argv')
    indices = [index for index, item in enumerate(argv) if Path(item).name == 'ck3_mod_acceptance.py']
    if len(indices) != 1 or indices[0] + 1 >= len(argv) or argv[indices[0] + 1] != mode:
        raise ValueError('Original public Popen operation differs')
    return argv


class TTLStopFileObservation(TypedDict):
    schema: Literal['ck3-original-plain-ttl-stop-file-v1']
    file: FilePin
    device_id_decimal: str
    file_id_decimal: str
    mtime_ns_decimal: str
    original_stop_at_utc: str


def _ttl_stop(refs: JsonObject, expected: Path, machine: str,
        run_finished: datetime, keeper_finished: datetime) -> tuple[datetime, TTLStopFileObservation | None]:
    """Observe the actual STOP file; never replace a historical command."""
    ref = file_pin(refs.get('keeper_stop'))
    if (set(json_object(refs['keeper_stop'])) != {'path', 'bytes', 'sha256'}
            or Path(ref['path']).resolve() != expected.resolve() or _ttl_pin(expected) != ref):
        raise ValueError('Original TTL STOP path or bytes changed')
    with expected.open('rb') as stream:
        before = os.fstat(stream.fileno())
        raw = stream.read(1048577)
        after = os.fstat(stream.fileno())
    current = expected.stat()
    identities = {(stat.st_dev, stat.st_ino, stat.st_mtime_ns, stat.st_size) for stat in (before, after, current)}
    if (len(identities) != 1 or len(raw) != ref['bytes'] or hashlib.sha256(raw).hexdigest() != ref['sha256']):
        raise ValueError('Original TTL STOP identity changed during observation')
    try:
        stop = json_object(json.loads(raw))
    except json.JSONDecodeError:
        match = re.fullmatch(r'([^\r\n]{1,512}) ([0-9]{4}-[0-9]{2}-[0-9]{2}T[^\r\n ]+)\r?\n?', raw.decode('utf-8'))
        if match is None:
            raise ValueError('Original plain TTL STOP must contain one description and actual timestamp')
        description = match[1].lower()
        if (not all(re.search(pattern, description) for pattern in
                (r'\bpre[- ]intent\b', r'\boffline\b', r'\bttl\b', r'\brefus(?:al|ed)\b'))
                or re.search(r'\bno\s+host\s*(?:/|or|and)\s*native\s+(?:was\s+)?(?:started|launched)\b', description) is None):
            raise ValueError('Original plain STOP does not describe the unlaunched pre-intent offline refusal')
        observed = _timestamp(match[2], 'Original plain STOP timestamp')
        epoch = observed - datetime(1970, 1, 1, tzinfo=timezone.utc)
        observed_ns = (epoch.days * 86400 + epoch.seconds) * 1000000000 + epoch.microseconds * 1000
        modified = datetime.fromtimestamp(after.st_mtime_ns // 1000000000, timezone.utc).replace(
            microsecond=(after.st_mtime_ns % 1000000000) // 1000)
        if (after.st_dev <= 0 or after.st_ino <= 0 or not run_finished <= observed <= keeper_finished
                or not observed_ns <= after.st_mtime_ns or modified > keeper_finished):
            raise ValueError('Original plain STOP file identity/mtime is outside the original run/keeper closure')
        return observed, TTLStopFileObservation(schema='ck3-original-plain-ttl-stop-file-v1', file=ref,
            device_id_decimal=str(after.st_dev), file_id_decimal=str(after.st_ino),
            mtime_ns_decimal=str(after.st_mtime_ns), original_stop_at_utc=match[2])
    if (set(stop) != {'machine_id', 'reason', 'observed_at_utc'}
            or stop.get('machine_id') != machine or stop.get('reason') !=
            'Public launcher refused expired background offline receipt before host/Game start; preserve source and original failure, close keeper cooperatively.'):
        raise ValueError('Original JSON TTL STOP machine/reason differs')
    observed = _timestamp(stop.get('observed_at_utc'), 'Original cooperative STOP')
    if not run_finished <= observed <= keeper_finished:
        raise ValueError('Original JSON STOP is outside the original run/keeper closure')
    return observed, None


def _ttl_allocator_stdout(refs: JsonObject) -> JsonObject:
    ref = file_pin(refs.get('allocator_stdout'))
    path = Path(ref['path']).resolve()
    if set(json_object(refs['allocator_stdout'])) != {'path', 'bytes', 'sha256'} or _ttl_pin(path) != ref:
        raise ValueError('Original complete allocator stdout changed')
    raw, decoder, rows = path.read_text(encoding='utf-8'), json.JSONDecoder(), []
    while raw.strip():
        raw = raw.lstrip()
        value, end = decoder.raw_decode(raw)
        rows.append(json_object(value))
        raw = raw[end:]
    if len(rows) != 2 or {key: value for key, value in rows[1].items()
            if key not in ('keeper_actual_exit_code', 'keeper_report', 'run_id')} != rows[0]:
        raise ValueError('Original allocator stdout must retain READY followed by the matching keeper completion')
    return rows[1]


class TTLRecoverySource(TypedDict):
    original_path: str
    repository_relative_path: str
    original_snapshot: FilePin
    current_source: FilePin


class TTLRecoveryEvolutionFields(TypedDict):
    original_runtime_manifest: FilePin
    original_source_commit: str
    source_root: str
    changed_recovery_sources: list[TTLRecoverySource]
    actual_recovery_reader: FilePin
    actual_allocator_consumer: FilePin
    actual_running_input_contract: FilePin


class TTLReaderEvolution(TTLRecoveryEvolutionFields):
    schema: Literal['ck3-prelaunch-recovery-reader-evolution-v1']


class RecoveryContentPin(TypedDict):
    bytes: int
    sha256: str


class RegistrySupportChange(TTLRecoverySource):
    original_support: RecoveryContentPin
    current_support: RecoveryContentPin


class RegistrySelectedCase(TypedDict):
    ready: FilePin
    prepared: FilePin
    contract: FilePin
    adapter: FilePin
    product: str
    case: str
    unchanged_frozen_prepare: FilePin


class TTLRegistrySupportEvolution(TTLRecoveryEvolutionFields):
    schema: Literal['ck3-prelaunch-recovery-reader-evolution-v2']
    registry_scope: Literal['unselected-xqol-prepare-support-only-resource-recovery']
    selected_case: RegistrySelectedCase
    registry_support_changes: list[RegistrySupportChange]


TTLRecoveryEvolution = TTLReaderEvolution | TTLRegistrySupportEvolution


def _registry_support_paths() -> tuple[str, ...]:
    return tuple('tools/ck3_mod_acceptance_cases/'+name+'.json' for name in (
        'xqol_administrative_appointments', 'xqol_liege_shared_ransom',
        'xqol_meritocratic_appointments', 'xqol_pam_negative', 'xqol_pam_positive',
        'xqol_prison_payment', 'xqol_selfpaid_ransom'))


def _registry_json_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate recovery registry JSON key')
        result[key] = value
    return result


def _registry_json(raw: bytes) -> JsonObject:
    if len(raw) > 1048576:
        raise ValueError('Bounded recovery registry JSON required')
    return json_object(json.loads(raw.decode('utf-8-sig'), object_pairs_hook=_registry_json_pairs))


def _registry_content_pin(value: object) -> RecoveryContentPin:
    row = json_object(value)
    if set(row) != {'bytes', 'sha256'}:
        raise ValueError('Exact recovery ContentPin fields required')
    size = _integer(row.get('bytes'), 'Recovery ContentPin bytes')
    digest = text_field(row, 'sha256')
    if re.fullmatch('[a-f0-9]{64}', digest) is None:
        raise ValueError('Exact recovery ContentPin digest required')
    return RecoveryContentPin(bytes=size, sha256=digest)


def _recovery_git_snapshot(repo: Path, commit: str, path: Path, relative: str,
        original: FilePin, close_path: Path, *, produce: bool) -> FilePin:
    object_name = commit + ':' + relative
    size = subprocess.run(['git', '-C', str(repo), 'cat-file', '-s', object_name],
        capture_output=True, check=True).stdout.strip()
    if not size.isdigit() or int(size) != original['bytes'] or int(size) > 1048576:
        raise ValueError('Original recovery Git blob size differs from frozen input')
    raw = subprocess.run(['git', '-C', str(repo), 'cat-file', 'blob', object_name],
        capture_output=True, check=True).stdout
    if len(raw) != original['bytes'] or hashlib.sha256(raw).hexdigest() != original['sha256']:
        raise ValueError('Original recovery Git blob differs from frozen input')
    snapshot = close_path.parent/'original-recovery-sources'/path.name
    if produce:
        snapshot.parent.mkdir(exist_ok=True)
        with snapshot.open('xb') as stream:
            stream.write(raw)
    retained = _ttl_pin(snapshot)
    if retained['bytes'] != original['bytes'] or retained['sha256'] != original['sha256']:
        raise ValueError('Retained original recovery source differs')
    return retained


def _registry_selected_case(previous: Path, freeze: JsonObject, repo: Path) -> RegistrySelectedCase:
    """The exception belongs to an unlaunched, frozen, non-XQOL selected case."""
    ready_ref = _ttl_pin(previous/'ready-context.json')
    ready = json_object(json.loads(Path(ready_ref['path']).read_bytes()))
    actual_frozen = json_object(json.loads((previous/'frozen-argv.json').read_bytes()))
    if json.dumps(actual_frozen, sort_keys=True) != json.dumps(freeze, sort_keys=True):
        raise ValueError('Actual original frozen registry context differs')
    prepared_ref = file_pin(ready.get('prepared_case'))
    prepared = json_object(_pinned_object(prepared_ref, 'Selected original Prepared'))
    contract_ref = file_pin(prepared.get('contract'))
    contract = json_object(_pinned_object(contract_ref, 'Selected original contract'))
    adapter_ref = file_pin(prepared.get('adapter'))
    product, case = text_field(ready, 'product'), text_field(ready, 'case')
    if (ready.get('schema') != 'ck3-mod-acceptance-run-context-v1'
            or ready.get('run_id') != previous.name or ready.get('run_id') != freeze.get('run_id')
            or Path(text_field(ready, 'run_dir')).resolve() != previous
            or file_pin(ready.get('frozen_argv')) != _ttl_pin(previous/'frozen-argv.json')
            or prepared.get('schema') != 'ck3-mod-acceptance-prepared-case-v1'
            or prepared.get('product') != product or prepared.get('case') != case
            or contract.get('schema') != 'ck3-mod-acceptance-product-case-v1'
            or contract.get('product') != product or contract.get('case_id') != case
            or product == 'xqol' or freeze.get('mod_key') != product or freeze.get('cell') != case
            or file_pin(prepared.get('runtime_manifest')) != file_pin(freeze.get('runtime_manifest'))
            or Path(contract_ref['path']).resolve() in {(repo/name).resolve() for name in _registry_support_paths()}
            or Path(adapter_ref['path']).resolve() != repo/'tools/ck3_mod_acceptance_cases/generic_product_adapter.py'):
        raise ValueError('Original selected case is not an exact unselected-XQOL resource context')
    files = object_field(freeze, 'files')
    for ref in (prepared_ref, contract_ref, adapter_ref):
        if (file_pin({'path':ref['path'], **object_field(files, ref['path'])}) != ref
                or _ttl_pin(Path(ref['path'])) != ref):
            raise ValueError('Original selected case input differs from frozen full table')
    state = Path(text_field(freeze, 'state_dir')).resolve()
    forbidden = ('launch-intent.json','launch.json','host-started.json','host-supervisor.json',
        'host-supervisor-started.json','supervisor.json','host-original-process-exit.json',
        'native-report.json','native-report.session.log','case-output')
    if (any((previous/name).exists() for name in forbidden)
            or any((state/name).exists() for name in ('control','native-session'))
            or not (previous/'controls').is_dir() or any((previous/'controls').iterdir())
            or any(path.exists() and any(path.iterdir()) for path in
                (state/'profile'/name for name in ('save games','logs','run')))):
        raise ValueError('Registry support recovery refuses any actual launch/native/control/Save evidence')
    prepare_path = repo/'tools/ck3_mod_acceptance_prepare.py'
    prepare_ref = file_pin({'path':str(prepare_path), **object_field(files, str(prepare_path))})
    if _ttl_pin(prepare_path) != prepare_ref:
        raise ValueError('Registry support requires raw byte-equal frozen prepare source')
    return RegistrySelectedCase(ready=ready_ref, prepared=prepared_ref, contract=contract_ref,
        adapter=adapter_ref, product=product, case=case, unchanged_frozen_prepare=prepare_ref)


def _registry_support_change(repo: Path, relative: str, original: FilePin, retained: FilePin,
        current: FilePin, prepare: FilePin) -> RegistrySupportChange:
    if (relative not in _registry_support_paths()
            or Path(original['path']).resolve() != (repo/relative).resolve()
            or Path(current['path']).resolve() != (repo/relative).resolve()
            or retained['bytes'] != original['bytes'] or retained['sha256'] != original['sha256']):
        raise ValueError('Exact allowed registry path/original snapshot required')
    before = _registry_json(Path(retained['path']).read_bytes())
    after = _registry_json(Path(current['path']).read_bytes())
    key = '../ck3_mod_acceptance_prepare.py'
    old_support = _registry_content_pin(object_field(before, 'support_files').get(key))
    new_support = _registry_content_pin(object_field(after, 'support_files').get(key))
    expected_support = RecoveryContentPin(bytes=prepare['bytes'], sha256=prepare['sha256'])
    if (before.get('schema') != 'ck3-xqol-original-followup-case-v1'
            or before.get('case') != Path(relative).stem.removeprefix('xqol_')
            or new_support != expected_support or old_support == new_support):
        raise ValueError('Only exact XQOL prepare support ContentPin renewal is admissible')
    expected = json_object(before)
    support = object_field(expected, 'support_files'); support[key] = json_object(new_support)
    expected['support_files'] = support
    if json.dumps(expected, sort_keys=True, allow_nan=False) != json.dumps(after, sort_keys=True, allow_nan=False):
        raise ValueError('Unselected registry changed outside its prepare support ContentPin')
    if _ttl_pin(Path(current['path'])) != current or _ttl_pin(Path(prepare['path'])) != prepare:
        raise ValueError('Current registry/prepare changed during recovery observation')
    return RegistrySupportChange(original_path=str((repo/relative).resolve()),
        repository_relative_path=relative, original_snapshot=retained, current_source=current,
        original_support=old_support, current_support=new_support)


def _ttl_recovery_sources(freeze: JsonObject, close_path: Path, *, produce: bool,
        previous: Path | None = None, registry_support: bool = False) -> TTLRecoveryEvolution | None:
    """Retain old Git bytes for two recovery readers, without editing the freeze.

    This exception belongs only to the unlaunched recovery reducers. Every
    other frozen input still uses its actual path and the ordinary full guard.
    """
    repo = Path(text_field(freeze, 'source_root')).resolve()
    files = object_field(freeze, 'files')
    changed: list[tuple[Path, str, FilePin]] = []
    for relative in ('tools/ck3_mod_acceptance_unrun.py', 'tools/ck3_mod_acceptance_allocate.py'):
        path = (repo / relative).resolve()
        if str(path) not in files:
            continue
        original = file_pin({'path': str(path), **object_field(files, str(path))})
        if _ttl_pin(path) != original:
            changed.append((path, relative, original))
    registry_changed: list[tuple[Path, str, FilePin]] = []
    if registry_support:
        for relative in _registry_support_paths():
            path = (repo/relative).resolve()
            if str(path) in files:
                original = file_pin({'path':str(path), **object_field(files, str(path))})
                if _ttl_pin(path) != original:
                    registry_changed.append((path, relative, original))
    if not changed and not registry_changed:
        return None
    manifest_ref = file_pin(freeze.get('runtime_manifest'))
    manifest_path = Path(manifest_ref['path'])
    if _ttl_pin(manifest_path) != manifest_ref:
        raise ValueError('Original recovery runtime manifest changed')
    manifest = json_object(json.loads(manifest_path.read_bytes()))
    commit = text_field(manifest, 'source_commit')
    if (re.fullmatch('[0-9a-f]{40}', commit) is None
            or manifest.get('machine_id') != object_field(freeze, 'identity_allocation').get('machine_id')):
        raise ValueError('Original recovery Git source commit/machine differs')
    sources: list[TTLRecoverySource] = []
    for path, relative, original in changed:
        retained = _recovery_git_snapshot(repo, commit, path, relative, original, close_path, produce=produce)
        sources.append(TTLRecoverySource(original_path=str(path), repository_relative_path=relative,
            original_snapshot=retained, current_source=_ttl_pin(path)))
    from xar_autoplayer.bridge import runtime_input_contract_v1
    allocator = same_directory_control_peer('ck3_mod_acceptance_allocate')
    contract_source = runtime_input_contract_v1.__file__
    allocator_source = allocator.__file__
    if not isinstance(contract_source, str) or not isinstance(allocator_source, str):
        raise ValueError('Actual recovery consumer source unavailable')
    common = TTLRecoveryEvolutionFields(original_runtime_manifest=manifest_ref,
        original_source_commit=commit, source_root=str(repo),
        changed_recovery_sources=sources, actual_recovery_reader=_ttl_pin(Path(__file__).resolve()),
        actual_allocator_consumer=_ttl_pin(Path(allocator_source).resolve()),
        actual_running_input_contract=_ttl_pin(Path(contract_source).resolve()))
    if not registry_changed:
        return TTLReaderEvolution(**common, schema='ck3-prelaunch-recovery-reader-evolution-v1')
    if previous is None:
        raise ValueError('Exact original selected case required for registry recovery')
    selected = _registry_selected_case(previous.resolve(), freeze, repo)
    registry_changes: list[RegistrySupportChange] = []
    for path, relative, original in registry_changed:
        retained = _recovery_git_snapshot(repo, commit, path, relative, original, close_path, produce=produce)
        registry_changes.append(_registry_support_change(repo, relative, original, retained,
            _ttl_pin(path), selected['unchanged_frozen_prepare']))
    return TTLRegistrySupportEvolution(**common, schema='ck3-prelaunch-recovery-reader-evolution-v2',
        registry_scope='unselected-xqol-prepare-support-only-resource-recovery',
        selected_case=selected, registry_support_changes=registry_changes)


def _recovery_input_validation(previous: Path, freeze: JsonObject, close_path: Path,
        bundle: Mapping[str, object], *, registry_support: bool = False) -> tuple[TTLRecoveryEvolution | None, JsonObject]:
    """Use retained original reader bytes; every other frozen input remains exact."""
    from xar_autoplayer.bridge.runtime_input_contract_v1 import FileIdentity, identity, validate_running_inputs
    evolution = _ttl_recovery_sources(freeze, close_path, produce=False,
        previous=previous, registry_support=registry_support)
    if ((evolution is None and 'recovery_reader_evolution' in bundle)
            or (evolution is not None and bundle.get('recovery_reader_evolution') != json_object(evolution))):
        raise ValueError('Recovery reader evolution differs from original Git inputs/current consumers')
    retained_sources: dict[Path, FilePin] = {} if evolution is None else {
        Path(row['original_path']): row['original_snapshot'] for row in evolution['changed_recovery_sources']}
    if evolution is not None and evolution['schema'] == 'ck3-prelaunch-recovery-reader-evolution-v2':
        for change in evolution['registry_support_changes']:
            retained_sources[Path(change['original_path'])] = change['original_snapshot']

    def observe_input(path: Path) -> FileIdentity:
        if path not in retained_sources:
            return identity(path)
        retained = identity(Path(retained_sources[path]['path']))
        return FileIdentity(path=str(path), bytes=retained['bytes'], sha256=retained['sha256'])

    return evolution, json_object(validate_running_inputs(previous, freeze, observer=observe_input))


def validate_pre_intent_offline_ttl_refusal(previous: Path, freeze_value: object, close_path: Path,
        keeper_root: Path, release_value: object, bus_value: object, next_state: Path) -> JsonObject:
    """Resource admission after the original parent rejected an expired receipt."""
    import ck3_live_run_id as ids
    import psutil
    from ck3_mod_acceptance_launcher_protocol_v1 import build_launcher_protocol_v1
    from ck3_mod_acceptance_background_types import product_acceptance_purpose_v1
    from steam_offline_state_contract import parse_result

    bundle = json_object(json.loads(close_path.read_bytes()))
    freeze, release, bus = json_object(freeze_value), json_object(release_value), json_object(bus_value)
    machine, run, task = ids.current_machine_id(), text_field(freeze, 'run_id'), text_field(freeze, 'screen_task')
    state = Path(text_field(freeze, 'state_dir')).resolve()
    if (bundle.get('schema') != SCHEMA or bundle.get('closure_kind') != OFFLINE_TTL_KIND
            or bundle.get('machine_id') != machine or bundle.get('run_id') != run or previous.name != run
            or object_field(freeze, 'identity_allocation').get('machine_id') != machine
            or Path(text_field(bundle, 'quarantined_state')).resolve() != state
            or next_state.resolve() == state or next_state.resolve().is_relative_to(state) or state.is_relative_to(next_state.resolve())
            or any(bundle.get(key) is not False for key in ('host_started', 'native_session_started', 'game_started',
                'normal_close_qualified', 'typed_normal_exit_proven', 'original_host_exit0', 'business_pass', 'release_pass'))):
        raise ValueError('TTL-refusal must preserve this unlaunched allocation and require a separate next state')
    refs = object_field(bundle, 'original_evidence')
    frozen_pin, original = _ttl_original(refs, 'frozen', previous / 'frozen-argv.json')
    _, ready = _ttl_original(refs, 'ready', previous / 'ready-context.json')
    _, allocated = _ttl_original(refs, 'allocated_context', previous / 'allocated-context.json')
    prepared_pin, prepared = _ttl_original(refs, 'prepared_case')
    context_pin, context = _ttl_original(refs, 'reviewed_context')
    if (original != freeze or ready.get('run_id') != run or allocated.get('run_id') != run
            or context.get('run_id') != run or context.get('reviewer') != '/root'
            or any(Path(text_field(row, 'run_dir')).resolve() != previous.resolve() for row in (ready, allocated, context))
            or any(Path(text_field(row, 'keeper_root')).resolve() != keeper_root.resolve() for row in (ready, allocated, context))
            or any(row.get('prepared_case') != prepared_pin for row in (ready, allocated, context))
            or ready.get('frozen_argv') != frozen_pin or context.get('frozen_argv') != frozen_pin
            or prepared.get('runtime_manifest') != freeze.get('runtime_manifest')
            or Path(text_field(object_field(prepared, 'startup'), 'state_dir')).resolve() != state):
        raise ValueError('TTL-refusal crossed the original allocation, Root review or preparation')
    _, run_result = _ttl_original(refs, 'run_result')
    _, allocate_result = _ttl_original(refs, 'allocator_result')
    run_argv = _ttl_public_exit(run_result, machine, 'run', 2)
    allocate_argv = _ttl_public_exit(allocate_result, machine, 'allocate', 0)

    def option(argv: list[str], flag: str) -> str:
        if argv.count(flag) != 1 or argv.index(flag) + 1 >= len(argv):
            raise ValueError('Original TTL-refusal public argument absent: ' + flag)
        return argv[argv.index(flag) + 1]

    if (Path(option(run_argv, '--run-context')).resolve() != Path(context_pin['path']).resolve()
            or Path(option(allocate_argv, '--keeper-output')).resolve() != keeper_root.resolve()
            or any(Path(option(argv, '--prepared-case')).resolve() != Path(prepared_pin['path']).resolve()
                   or option(argv, '--product') != ready.get('product') or option(argv, '--case') != ready.get('case')
                   for argv in (run_argv, allocate_argv))
            or option(run_argv, '--runtime') != option(allocate_argv, '--runtime')):
        raise ValueError('TTL-refusal original public commands crossed run, case, runtime or keeper')
    _, stdout = _ttl_original(refs, 'run_stdout')
    _, stderr = _ttl_original(refs, 'run_stderr')
    if (stdout.get('run_id') != run or stdout.get('host_argv') != freeze.get('argv')
            or stdout.get('runtime_status') != 'LAUNCH_FAILED' or stdout.get('business_acceptance') != 'NOT_ASSESSED'
            or type(stdout.get('launcher_exit_code')) is not int or stdout.get('launcher_exit_code') != 2
            or stderr != {'status': 'BLOCKED', 'error': "BackgroundGateRefusal('Fresh same-machine background offline observation required')", 'business_pass': False}):
        raise ValueError('Original parent TTL-refusal terminal differs')
    allocator_stdout = _ttl_allocator_stdout(refs)
    if (allocator_stdout.get('status') != 'ACTUAL_ALLOCATED_KEEPER_READY_NOT_RUN'
            or allocator_stdout.get('task') != task or Path(text_field(allocator_stdout, 'live')).resolve() != previous.resolve()):
        raise ValueError('Original allocator READY output differs')
    offline_pin, offline = _ttl_original(refs, 'offline_receipt', Path(text_field(context, 'steam_offline_receipt')))
    observation = parse_result(offline)
    run_started = _timestamp(run_result.get('started_at_utc'), 'Original refused run start')
    run_finished = _timestamp(run_result.get('finished_at_utc'), 'Original refused run finish')
    observed = _timestamp(observation.observed_at_utc, 'Historical offline observation')
    if (observation.machine_id != machine or observation.status != 'offline' or observation.steam is None
            or observation.source is None or not observed < run_started <= run_finished
            or (run_started - observed).total_seconds() <= 30):
        raise ValueError('Original receipt is not proved expired before this parent launcher attempt')
    launchers = [Path(value).resolve() for value in strings_field(stdout, 'launcher_argv')
                 if Path(value).name == 'ck3_mod_acceptance_launcher.py']
    if len(launchers) != 1:
        raise ValueError('Original refused launcher identity absent')
    launcher_source = file_pin(json_object(refs['launcher_source']))
    gate_source = file_pin(json_object(refs['gate_source']))
    files = object_field(freeze, 'files')
    if (Path(launcher_source['path']).resolve() != launchers[0] or _ttl_pin(launchers[0]) != launcher_source
            or Path(gate_source['path']).resolve() != launchers[0].with_name('ck3_mod_acceptance_steam_gate.py')
            or _ttl_pin(Path(gate_source['path'])) != gate_source
            or any(object_field(files, ref['path']) != {'bytes': ref['bytes'], 'sha256': ref['sha256']}
                   for ref in (launcher_source, gate_source))):
        raise ValueError('TTL-refusal source branch differs from the original frozen launcher/gate')
    protocol = build_launcher_protocol_v1(launcher_source, gate_source)
    purpose_pin, purpose = _ttl_original(refs, 'purpose', previous / 'product-acceptance-purpose.json')
    host_argv = strings_field(freeze, 'argv')
    product_acceptance_purpose_v1(purpose, purpose_path=Path(purpose_pin['path']), host_path=Path(host_argv[4]),
        state_dir=state, bridge_pipe=option(host_argv, '--bridge-pipe'))
    profile_pin, _ = _ttl_original(refs, 'normal_exit_profile', Path(option(host_argv, '--normal-exit-managed-profile')))
    if context.get('normal_exit_managed_profile') != profile_pin or option(host_argv, '--normal-exit-managed-profile-sha256') != profile_pin['sha256']:
        raise ValueError('Original prepared normal-exit profile binding changed')
    _, keeper = _ttl_original(refs, 'keeper', keeper_root / 'report.json')
    _, parent = _ttl_original(refs, 'keeper_parent_exit', previous / 'keeper-actual-parent-exit.json')
    _, keeper_ready = _ttl_original(refs, 'keeper_ready', keeper_root / 'ready.json')
    stop_at, stop_observation = _ttl_stop(refs, keeper_root / 'STOP', machine, run_finished,
        _timestamp(keeper.get('at_utc'), 'Keeper completion'))
    if ((stop_observation is None and 'keeper_stop_file_observation' in bundle)
            or (stop_observation is not None and bundle.get('keeper_stop_file_observation') != json_object(stop_observation))):
        raise ValueError('Original plain STOP immutable file observation changed or is missing')
    if (keeper.get('task_id') != task or keeper.get('thread_exited') is not True
            or keeper.get('failure') is not None or keeper.get('entry_error') is not None or keeper.get('game_actions') is not False
            or parent.get('run_id') != run or type(parent.get('keeper_actual_exit_code')) is not int
            or parent.get('keeper_actual_exit_code') != 0 or parent.get('keeper_report') != keeper
            or allocator_stdout.get('run_id') != run or allocator_stdout.get('keeper_report') != keeper
            or type(allocator_stdout.get('keeper_actual_exit_code')) is not int or allocator_stdout.get('keeper_actual_exit_code') != 0
            or not _timestamp(keeper_ready.get('at_utc'), 'Keeper ready') <= run_started <= run_finished
                    <= stop_at <= _timestamp(keeper.get('at_utc'), 'Keeper completion')):
        raise ValueError('Original cooperative no-game keeper STOP/wait0 differs')
    cas_pin, cas_source = _ttl_original(refs, 'CAS_release')
    _, done_source = _ttl_original(refs, 'admin_done')
    _, root_release = _ttl_original(refs, 'root_release')
    allocator = same_directory_control_peer('ck3_mod_acceptance_allocate')
    cas = json_object(allocator.read_failed_runtime_release(Path(cas_pin['path'])))
    _release_stages(keeper, cas, release, cas_source, done_source, release, task)
    if root_release.get('event') != release.get('event') or root_release.get('task') != release.get('task'):
        raise ValueError('Root original release and canonical reconstruction differ')
    counter_path = (ids.default_state_root() / machine / text_field(freeze, 'mod_key') / 'counter.json').resolve()
    counter_snapshot, counter = _ttl_original(refs, 'counter', close_path.parent / 'counter.original.json')
    provenance = object_field(bundle, 'counter_snapshot_provenance')
    source_counter = file_pin(provenance.get('source'))
    if (set(provenance) != {'machine_id', 'observed_at_utc', 'source'}
            or provenance.get('machine_id') != machine
            or _timestamp(provenance.get('observed_at_utc'), 'Counter snapshot observation') > datetime.now(timezone.utc)
            or Path(source_counter['path']).resolve() != counter_path or _ttl_pin(counter_path) != source_counter
            or source_counter['bytes'] != counter_snapshot['bytes'] or source_counter['sha256'] != counter_snapshot['sha256']
            or counter_path.read_bytes() != Path(counter_snapshot['path']).read_bytes()):
        raise ValueError('Current canonical counter differs from its original immutable TTL snapshot')
    sequence = _integer(counter.get('last_sequence'), 'Original product counter', 1)
    if ids.format_run_id(machine, text_field(freeze, 'mod_key'), sequence) != run:
        raise ValueError('TTL-refusal predecessor is not the latest product counter')
    absent: JsonObject = {name: not (previous / name).exists() for name in (
        'launch-intent.json', 'host-started.json', 'host-supervisor-started.json', 'host-original-process-exit.json',
        'native-report.json', 'native-report.session.log', 'case-output')}
    absent.update({'state/control': not (state / 'control').exists(), 'state/native-session': not (state / 'native-session').exists(),
        'controls-empty': (previous / 'controls').is_dir() and not any((previous / 'controls').iterdir())})
    for name in ('logs', 'save games', 'run'):
        path = state / 'profile' / name
        absent['profile/' + name] = not path.exists() or not any(path.iterdir())
    if any(value is not True for value in absent.values()):
        raise ValueError('TTL-refused allocation has actual launch/native/control/save evidence')
    tasks = bus.get('tasks')
    if not isinstance(tasks, list):
        raise ValueError('Original current task list required')
    current_tasks = [json_object(row) for row in tasks]
    for row in current_tasks:
        resources = row.get('resources')
        if (not isinstance(resources, list) or any(not isinstance(item, str) for item in resources)
                or 'ck3-screen:acquired' in resources):
            raise ValueError('TTL-refused allocation still has a screen owner')
    matching = [row for row in current_tasks if row.get('task_id') == task]
    released_task = object_field(release, 'task')
    if (len(matching) != 1 or {key: matching[0].get(key) for key in released_task} != released_task
            or set(matching[0]) != set(released_task) | {'age_seconds', 'stale'}
            or type(matching[0].get('age_seconds')) is not int or matching[0].get('stale') is not False):
        raise ValueError('TTL-refusal current canonical task differs from the actual release')
    evolution, inputs = _recovery_input_validation(previous, freeze, close_path, bundle)
    inventory_reader: object = allocator.runtime_process_inventory
    if not isinstance(inventory_reader, _UnrunProcessInventory):
        raise ValueError('Existing process inventory boundary unavailable')
    inventory = json_object(inventory_reader(psutil, os.getpid()))
    if inventory.get('blockers') != []:
        raise ValueError('TTL-refused predecessor still has active runtime processes')
    return json_object({'mode': 'previous-shared-allocated-pre-intent-offline-ttl-refused', 'actual_process_inventory': inventory,
        'failure_cleanup': {'close': _ttl_pin(close_path), 'original_evidence': refs, 'launcher_protocol': protocol,
            'offline_observation_age_at_run_start_seconds': (run_started - observed).total_seconds(),
            'historical_receipt_is_current_offline_admission': False, 'original_keeper_exit_code': 0,
            'original_host_exit_code': None, 'original_ck3_exit_code': None, 'host_started': False, 'native_session_started': False,
            'normal_close_qualified': False, 'typed_normal_exit_proven': False, 'business_pass': False, 'release_pass': False,
            'consumed_purpose_preserved': purpose_pin, 'original_inputs_verified': inputs,
            'recovery_reader_evolution': evolution,
            'absent_launch_native_control_Save': absent}})


class ExternalCompletionRequest(TypedDict):
    session_id: int
    chars: Literal['']
    max_output_tokens: int
    yield_time_ms: int


class ExternalExecCompletionReceipt(TypedDict):
    """Final tool output, never a full process stream or Popen/host receipt."""
    schema: Literal['external-exec-completion-v1']
    machine_id: str
    original_request: FilePin
    initial_response: FilePin
    completion_request: ExternalCompletionRequest
    completion_response: FilePin
    completion_observed_at_utc: str
    exit_code: int
    allocator_stdout: FilePin


@dataclass(frozen=True)
class ExternalAllocatorCompletion:
    command_text: str
    shell: Literal['cmd.exe']
    workdir: str
    session_id: int
    exit_code: int
    completion_observed_at: datetime
    argv: tuple[str, ...]


class UnrunBundleReport(TypedDict):
    bundle: FilePin
    previous_release: FilePin
    validation: JsonObject
    SDK_or_launch: Literal[False]


class AbortedAllocationEvidenceV1(TypedDict):
    schema: Literal['ck3-mod-acceptance-allocated-unrun-closure-v1']
    machine_id: str
    observed_at_utc: str
    run_id: str
    quarantined_state: str
    allocator_exit_code: None
    host_started: Literal[False]
    native_session_started: Literal[False]
    game_started: Literal[False]
    normal_close_qualified: Literal[False]
    original_host_exit0: Literal[False]
    business_pass: Literal[False]
    allocator_original_wait_observed: Literal[False]
    ready: FilePin
    frozen: FilePin
    allocated_context: FilePin
    prepared_case: FilePin
    keeper_process: FilePin
    keeper_inputs: FilePin
    keeper_ready: FilePin
    allocator_intent: FilePin
    allocator_process: FilePin
    allocator_stdout: FilePin
    allocator_aborted_wrapper: FilePin
    CAS_release: FilePin
    admin_done: FilePin
    counter: FilePin


class AbortedAllocationClosureV1(AbortedAllocationEvidenceV1):
    closure_kind: Literal['wrapper-aborted-before-launch-without-terminal-waits']
    keeper_exit_code: None
    keeper_original_wait_observed: Literal[False]


class ClosedKeeperAbortedAllocationClosureV1(AbortedAllocationEvidenceV1):
    closure_kind: Literal['wrapper-aborted-before-launch-with-closed-keeper']
    keeper_exit_code: Literal[0]
    keeper_original_wait_observed: Literal[True]
    keeper: FilePin
    keeper_parent_exit: FilePin
    keeper_STOP: FilePin
    idle_timeout: FilePin


def _object(raw: object, label: str) -> dict[str, object]:
    if not isinstance(raw, dict):
        raise ValueError(label + ' must be an object')
    result: dict[str, object] = {}
    for key, value in raw.items():
        if not isinstance(key, str):
            raise ValueError(label + ' keys must be strings')
        result[key] = value
    return result


def _text(raw: object, label: str) -> str:
    if not isinstance(raw, str) or not raw:
        raise ValueError(label + ' must be a nonempty string')
    return raw


def _integer(raw: object, label: str, minimum: int = 0) -> int:
    # IDs and codes reject bool, equal floats and rounded JavaScript numbers.
    if type(raw) is not int or not isinstance(raw, int) or not minimum <= raw <= 9007199254740991:
        raise ValueError(label + ' must be an exact safe integer')
    return raw


def _timestamp(raw: object, label: str) -> datetime:
    value = datetime.fromisoformat(_text(raw, label))
    if value.tzinfo is None:
        raise ValueError(label + ' must include a timezone')
    return value


def _evidence_pin(raw: object, label: str) -> FilePin:
    value = _object(raw, label)
    if set(value) != {'path', 'bytes', 'sha256'}:
        raise ValueError(label + ' pin fields differ')
    path = _text(value['path'], label + '.path')
    size = _integer(value['bytes'], label + '.bytes')
    digest = _text(value['sha256'], label + '.sha256')
    if not re.fullmatch('[0-9a-fA-F]{64}', digest):
        raise ValueError(label + ' SHA-256 differs')
    return {'path': path, 'bytes': size, 'sha256': digest}


def _pinned_object(raw: object, label: str) -> dict[str, object]:
    reference = _evidence_pin(raw, label)
    check_pin(Path(reference['path']), dict(reference))
    return _object(_read(reference['path']), label)


def _tool_duration(raw: object, label: str) -> None:
    if type(raw) not in (int, float) or not isinstance(raw, (int, float)) or not math.isfinite(raw) or raw < 0:
        raise ValueError(label + ' must be a finite nonnegative duration')


def _cmd_allocator_argv(command: str) -> tuple[str, ...]:
    """Read one literal cmd.exe command without executing or normalizing it.

    Only bare/whole-quoted arguments are admitted. Expansion, escaping,
    operators, concatenated quotes and redirection are rejected rather than
    translated into a fictitious shell=False invocation.
    """
    if any(character in command for character in '&|<>^%!\r\n\0'):
        raise ValueError('External allocator command must be one literal cmd.exe command')
    result: list[str] = []
    end = 0
    for match in re.finditer(r'"([^"\r\n]*)"|([^\s"]+)', command):
        gap = command[end:match.start()]
        if gap.strip(' \t') or (result and not gap):
            raise ValueError('External allocator command quoting differs')
        argument = match.group(1) if match.group(1) is not None else match.group(2)
        if not argument:
            raise ValueError('External allocator empty argument unsupported')
        result.append(argument)
        end = match.end()
    if not result or command[end:].strip(' \t'):
        raise ValueError('External allocator command quoting differs')
    return tuple(result)


def parse_external_exec_completion(
    raw: object, machine: str, keeper_stamps: list[datetime], allocator_stdout: object,
) -> ExternalAllocatorCompletion:
    """Validate original tool data for allocator-only exit0 admission.

    This form cannot establish a process PID, original Popen wait, host exit or
    CK3 business credit. All keeper, absence, source and CAS guards still apply.
    """
    value = _object(raw, 'External allocator completion')
    fields = {'schema', 'machine_id', 'original_request', 'initial_response', 'completion_request',
              'completion_response', 'completion_observed_at_utc', 'exit_code', 'allocator_stdout'}
    if set(value) != fields or value.get('schema') != 'external-exec-completion-v1' or value.get('machine_id') != machine:
        raise ValueError('External allocator completion fields/schema/machine differ')
    exit_code = _integer(value['exit_code'], 'External allocator exit_code')
    if exit_code != 0:
        raise ValueError('External allocator actual completion must be exit0')
    observed = _timestamp(value['completion_observed_at_utc'], 'External completion observation')
    if not keeper_stamps or any(stamp.tzinfo is None for stamp in keeper_stamps) or not keeper_stamps[0] <= keeper_stamps[-1] <= observed:
        raise ValueError('External allocator completion observation predates keeper completion')
    request = _pinned_object(value['original_request'], 'External original request')
    if set(request) != {'cmd', 'shell', 'workdir', 'max_output_tokens', 'yield_time_ms'} or request.get('shell') != 'cmd.exe':
        raise ValueError('External allocator original cmd.exe request differs')
    command = _text(request['cmd'], 'External original cmd')
    workdir = _text(request['workdir'], 'External original workdir')
    if not PureWindowsPath(workdir).is_absolute():
        raise ValueError('External original workdir must be absolute')
    _integer(request['max_output_tokens'], 'External original max_output_tokens', 1)
    _integer(request['yield_time_ms'], 'External original yield_time_ms', 1)
    initial = _pinned_object(value['initial_response'], 'External initial response')
    if set(initial) != {'chunk_id', 'wall_time_seconds', 'session_id', 'original_token_count', 'output'}:
        raise ValueError('External initial response must be the original running session')
    session = _integer(initial['session_id'], 'External initial session_id', 1)
    _text(initial['chunk_id'], 'External initial chunk_id')
    _tool_duration(initial['wall_time_seconds'], 'External initial wall time')
    _integer(initial['original_token_count'], 'External initial original_token_count')
    if not isinstance(initial['output'], str):
        raise ValueError('External initial response output must be text')
    completion_request = _object(value['completion_request'], 'External completion request')
    if set(completion_request) != {'session_id', 'chars', 'max_output_tokens', 'yield_time_ms'}:
        raise ValueError('External completion request fields differ')
    if _integer(completion_request['session_id'], 'External completion session_id', 1) != session or completion_request['chars'] != '':
        raise ValueError('External actual completion request session differs')
    _integer(completion_request['max_output_tokens'], 'External completion max_output_tokens', 1)
    _integer(completion_request['yield_time_ms'], 'External completion yield_time_ms', 1)
    final = _pinned_object(value['completion_response'], 'External completion response')
    if set(final) != {'chunk_id', 'wall_time_seconds', 'exit_code', 'original_token_count', 'output'}:
        raise ValueError('External completion response must be a finished tool result')
    _text(final['chunk_id'], 'External completion chunk_id')
    _tool_duration(final['wall_time_seconds'], 'External completion wall time')
    _integer(final['original_token_count'], 'External completion original_token_count')
    if _integer(final['exit_code'], 'External completion response exit_code') != exit_code:
        raise ValueError('External actual completion exit code differs')
    output = _text(final['output'], 'External completion output')
    reference = _evidence_pin(value['allocator_stdout'], 'External raw allocator stdout')
    expected = _evidence_pin(allocator_stdout, 'Closure allocator stdout')
    if reference != expected:
        raise ValueError('External allocator stdout pin differs from closure')
    check_pin(Path(reference['path']), dict(reference))
    if output.encode('utf-8') != Path(reference['path']).read_bytes():
        raise ValueError('External allocator final tool output bytes differ; preserve CRLF exactly')
    # Exact final write_stdin output block, not stdout accumulated since process
    # creation. Earlier polls are neither reconstructed nor claimed. The final
    # block itself must contain the complete READY JSON object.
    allocated: object = json.loads(output)
    if not isinstance(allocated, dict) or allocated.get('status') != 'ACTUAL_ALLOCATED_KEEPER_READY_NOT_RUN':
        raise ValueError('External allocator complete READY stdout missing')
    return ExternalAllocatorCompletion(command, 'cmd.exe', workdir, session, exit_code, observed, _cmd_allocator_argv(command))

def need(value: object, message: object) -> None:
    if not value: raise ValueError(message)
def _read(path: str | Path) -> JsonObject:
    path=Path(path);need(path.stat().st_size<=1024*1024,'Small original metadata required')
    return json_object(read_json(path))
def _exact(bundle: Mapping[str, object], key: str, path: Path) -> JsonObject:
    ref=file_pin(bundle.get(key));need(Path(ref['path']).resolve()==path.resolve(),'Unrun original path differs: '+key)
    check_pin(path,dict(ref));return _read(path)


@dataclass(frozen=True)
class RootAllocatorTriplet:
    argv: tuple[str, ...]
    pid: int
    process_create_time_seconds: Decimal
    intended_at: datetime
    process_observed_at: datetime
    finished_at: datetime


def _root_allocator_source(command: object, paths: tuple[Path, Path, Path],
        machine: str, argv: list[str]) -> None:
    """Bind the real split recorder to its child, exact files and wait result."""
    ref = _evidence_pin(command, 'Root allocator producer')
    source = Path(ref['path'])
    if not source.is_absolute() or source.is_symlink() or not 0 < ref['bytes'] <= 1048576:
        raise ValueError('Bounded original Root allocator producer required')
    check_pin(source, dict(ref))
    tree = ast.parse(source.read_text(encoding='utf-8-sig'))
    imports: dict[str, tuple[str, ...]] = {
        'Path': ('from', 'pathlib', 'Path'),
        'datetime': ('from', 'datetime', 'datetime'), 'timezone': ('from', 'datetime', 'timezone'),
        **{name: ('import', name) for name in ('json', 'subprocess', 'sys', 'time', 'psutil')},
    }
    observed_imports: dict[str, list[tuple[str, ...]]] = {name: [] for name in imports}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                name = alias.asname or alias.name.split('.')[0]
                if isinstance(node, ast.ImportFrom) and alias.name == '*':
                    raise ValueError('Root allocator producer wildcard import differs')
                if name in imports:
                    if alias.asname is not None:
                        raise ValueError('Root allocator producer import alias differs')
                    observed_imports[name].append(('import', alias.name) if isinstance(node, ast.Import)
                        else ('from', '.' * node.level + (node.module or ''), alias.name))
        if (isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)) and node.id in imports
                or isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name in imports
                or isinstance(node, ast.arg) and node.arg in imports
                or isinstance(node, ast.ExceptHandler) and node.name in imports):
            raise ValueError('Root allocator producer imported binding was reassigned')
        target: ast.expr | None = None
        if isinstance(node, (ast.Attribute, ast.Subscript)) and isinstance(node.ctx, (ast.Store, ast.Del)):
            target = node.value
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.NamedExpr)):
            target = node.value
            if isinstance(target, ast.Call):
                target = None
            elif (isinstance(node, ast.Assign) and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name) and node.targets[0].id == 'mode'
                    and target is not None and ast.dump(target) == ast.dump(ast.parse('sys.argv[1]', mode='eval').body)):
                target = None
        while isinstance(target, (ast.Attribute, ast.Subscript)):
            target = target.value
        if isinstance(target, ast.Name) and target.id in imports:
            raise ValueError('Root allocator producer imported object alias or mutation differs')
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id in ('exec', 'eval', 'globals', 'locals', 'setattr', 'delattr'):
            raise ValueError('Root allocator producer dynamic binding differs')
    if any(observed_imports[name] != [expected] for name, expected in imports.items()):
        raise ValueError('Root allocator producer original imports differ')
    assignments: dict[str, ast.expr] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in assignments:
                raise ValueError('Root allocator producer reassigned a recorded binding')
            assignments[name] = node.value

    def path_value(node: ast.expr, seen: tuple[str, ...] = ()) -> Path:
        if isinstance(node, ast.Name) and node.id in assignments and node.id not in seen:
            return path_value(assignments[node.id], (*seen, node.id))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ('Path', 'str') \
                and len(node.args) == 1 and not node.keywords:
            return path_value(node.args[0], seen)
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return Path(node.value)
        if isinstance(node, ast.Attribute) and node.attr == 'parent':
            return path_value(node.value, seen).parent
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div) \
                and isinstance(node.right, ast.Constant) and isinstance(node.right.value, str):
            return path_value(node.left, seen) / node.right.value
        raise ValueError('Root allocator producer path expression differs')

    if not all(name in assignments for name in ('OUT', 'REPO', 'PYTHON', 'MACHINE', 'argv', 'mode', 'prefix')):
        raise ValueError('Root allocator producer bindings missing')
    output, repo, python = (path_value(assignments[name]) for name in ('OUT', 'REPO', 'PYTHON'))
    if (not all(path.is_absolute() for path in (output, repo, python))
            or tuple(path.resolve() for path in paths) != tuple(output.resolve() / name for name in
                ('ALLOCATE.intent.actual.json', 'ALLOCATE.started.actual.json', 'ALLOCATE.original-wait.actual.json'))
            or not isinstance(assignments['MACHINE'], ast.Constant) or assignments['MACHINE'].value != machine
            or not isinstance(assignments['argv'], ast.List)):
        raise ValueError('Root allocator producer crossed machine or original output paths')
    prefix = ast.parse("argv=[PYTHON,'-B','-X','utf8','tools/ck3_mod_acceptance.py',mode]").body[0]
    if not isinstance(prefix, ast.Assign) or not isinstance(prefix.value, ast.List):
        raise ValueError('Internal Root argv signature unavailable')
    if (len(assignments['argv'].elts) < 6 or any(ast.dump(a) != ast.dump(b)
            for a, b in zip(assignments['argv'].elts[:6], prefix.value.elts))
            or len(argv) < 6 or Path(argv[0]).resolve() != python.resolve()
            or argv[1:6] != ['-B', '-X', 'utf8', 'tools/ck3_mod_acceptance.py', 'allocate']):
        raise ValueError('Root allocator producer argv differs from actual public command')
    expected = ast.parse(r'''
def stamp():
    return datetime.now(timezone.utc).isoformat()
def write_new(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')
mode = sys.argv[1]
prefix = {'run': 'PUBLIC-RUN', 'allocate': 'ALLOCATE', 'preflight': 'PREFLIGHT'}[mode]
write_new(OUT / (prefix + '.intent.actual.json'), {'machine_id': MACHINE, 'argv': argv, 'started_at_utc': stamp()})
started = time.monotonic()
with (OUT / (prefix + '.stdout.log')).open('xb') as out, (OUT / (prefix + '.stderr.log')).open('xb') as err:
    child = subprocess.Popen(argv, cwd=REPO, stdout=out, stderr=err)
    write_new(OUT / (prefix + '.started.actual.json'), {'machine_id': MACHINE,
        'pid': child.pid, 'process_create_time_seconds': str(psutil.Process(child.pid).create_time()),
        'started_at_utc': stamp(), 'original_wait_pending': True})
    code = child.wait()
write_new(OUT / (prefix + '.original-wait.actual.json'), {'machine_id': MACHINE,
    'original_wait_returncode': code, 'elapsed_seconds': time.monotonic() - started, 'finished_at_utc': stamp()})
''').body
    signature = [ast.dump(node) for node in expected[4:]]
    candidates = [tree.body[i:i + len(signature)] for i in range(len(tree.body))
        if [ast.dump(node) for node in tree.body[i:i + len(signature)]] == signature]
    for required in expected[:4]:
        if sum(ast.dump(node) == ast.dump(required) for node in tree.body) != 1:
            raise ValueError('Root allocator producer stamp/write_new/mode binding differs')
    stores = {name: sum(isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store) and node.id == name
        for node in ast.walk(tree)) for name in ('child', 'code')}
    popens = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute) and node.func.attr == 'Popen']
    if len(candidates) != 1 or stores != {'child': 1, 'code': 1} or len(popens) != 1:
        raise ValueError('Root allocator producer must publish the original child Popen.wait result')


def _root_allocator_triplet(intent: JsonObject, process: JsonObject, waited: JsonObject,
        *, command: object, paths: tuple[Path, Path, Path], machine: str,
        keeper_stamps: list[datetime]) -> RootAllocatorTriplet:
    if (set(intent) != {'machine_id', 'argv', 'started_at_utc'}
            or set(process) != {'machine_id', 'pid', 'process_create_time_seconds', 'started_at_utc', 'original_wait_pending'}
            or set(waited) != {'machine_id', 'original_wait_returncode', 'elapsed_seconds', 'finished_at_utc'}
            or any(row.get('machine_id') != machine for row in (intent, process, waited))
            or process.get('original_wait_pending') is not True
            or _integer(waited.get('original_wait_returncode'), 'Root original wait code') != 0):
        raise ValueError('Exact original Root allocator triplet fields/machine/wait0 required')
    pid = _integer(process.get('pid'), 'Root original child pid', 1)
    birth = _text(process.get('process_create_time_seconds'), 'Root original process birth')
    if re.fullmatch(r'[1-9][0-9]*(?:\.[0-9]+)?', birth) is None:
        raise ValueError('Canonical original Root child birth decimal required')
    created = Decimal(birth)
    _tool_duration(waited.get('elapsed_seconds'), 'Root original elapsed seconds')
    intended = _timestamp(intent.get('started_at_utc'), 'Root allocator intent')
    observed = _timestamp(process.get('started_at_utc'), 'Root child observation')
    finished = _timestamp(waited.get('finished_at_utc'), 'Root allocator original wait')
    stamps = [intended, observed, *keeper_stamps, finished]
    if len(keeper_stamps) < 2 or any(stamp.utcoffset() != timezone.utc.utcoffset(stamp) for stamp in stamps):
        raise ValueError('Root original allocator/keeper UTC chronology required')

    def seconds(stamp: datetime) -> Decimal:
        delta = stamp - datetime(1970, 1, 1, tzinfo=timezone.utc)
        return Decimal(delta.days * 86400 + delta.seconds) + Decimal(delta.microseconds) / Decimal(1000000)

    # Keep the OS birth's decimal precision; no rounded datetime/float identity.
    if not seconds(intended) <= created <= seconds(observed) <= seconds(keeper_stamps[0]) \
            or stamps != sorted(stamps):
        raise ValueError('Original Root allocator intent/child/keeper/wait chronology differs')
    argv = strings_field(intent, 'argv')
    _root_allocator_source(command, paths, machine, argv)
    return RootAllocatorTriplet(tuple(argv), pid, created, intended, observed, finished)


def _allocator_argv(bundle: Mapping[str, object], machine: str, keeper_stamps: list[datetime]) -> list[str]:
    """Read one original allocator completion evidence form.

    The triplet credits its actual Popen wait. The external form preserves the
    actual cmd.exe tool session and exact final output block without inventing
    a Popen wait or a complete process stdout stream. No form credits host/CK3.
    """
    if bundle.get('receipt_format') == SERIAL_PRELAUNCH_FORMAT:
        actual = _serial_allocator(bundle, machine)
        if not actual.started_at <= keeper_stamps[0] <= keeper_stamps[-1] <= actual.finished_at:
            raise ValueError('Original serial allocator wait0 predates keeper closure')
        return list(actual.argv)
    keys=('allocator_intent','allocator_process','allocator_exit')
    combined='allocator_result' in bundle
    external='allocator_external_exec' in bundle
    need((combined and not external and not any(k in bundle for k in keys))
         or (external and not combined and not any(k in bundle for k in keys))
         or (not combined and not external and all(k in bundle for k in keys)),
         'One complete original allocator evidence form required')
    def original(key):
        ref=bundle[key];check_pin(Path(ref['path']),ref);return _read(ref['path'])
    if external:
        external_command=parse_external_exec_completion(original('allocator_external_exec'),machine,
            keeper_stamps,bundle.get('allocator_stdout'))
        argv=list(external_command.argv)
    elif combined:
        command=original('allocator_result')
        if command.get('original_subprocess_wait_observed') is True:
            argv,finished=public_operation_argv(bundle['allocator_command'],bundle['allocator_result'],
                machine_id=machine,mode='allocate',exit_code=0)
            need(keeper_stamps[-1]<=finished,'Actual allocator completion predates keeper exit')
        else:
            need(command.get('machine_id')==machine and type(command.get('exit_code')) is int and command.get('exit_code')==0
                 and command.get('shell') is False and bool(command.get('finished_at_utc')),
                 'Actual original allocator wait0 differs')
            argv=command.get('argv',[])
    else:
        intent,process,exit_row=(original(k) for k in keys)
        if 'original_wait_returncode' in exit_row or 'process_create_time_seconds' in process:
            paths = tuple(Path(_evidence_pin(bundle[key], key)['path']) for key in keys)
            root = _root_allocator_triplet(intent, process, exit_row, command=bundle.get('allocator_command'),
                paths=(paths[0], paths[1], paths[2]), machine=machine, keeper_stamps=keeper_stamps)
            argv = list(root.argv)
            return argv
        pid=process.get('pid');created=process.get('create_time')
        need(all(row.get('machine_id')==machine for row in (intent,process,exit_row))
             and intent.get('stage')=='allocate' and type(pid) is int and pid>0
             and type(exit_row.get('pid')) is int and exit_row.get('pid')==pid and exit_row.get('actual_original_popen_wait') is True
             and type(exit_row.get('returncode')) is int and exit_row['returncode']==0
             and intent.get('argv')==process.get('argv'),
             'Actual original allocator intent/process/wait0 differs')
        need(type(created) in (int,float),'Original allocator process creation time missing')
        started=datetime.fromtimestamp(created,timezone.utc)
        intended=datetime.fromisoformat(intent['at_utc']);finished=datetime.fromisoformat(exit_row['completed_at_utc'])
        need(intended.tzinfo is not None and finished.tzinfo is not None
             and intended<=started<=keeper_stamps[0]<=keeper_stamps[-1]<=finished,
             'Original allocator intent/process/wait time differs')
        argv=process.get('argv',[])
    need(isinstance(argv,list) and all(isinstance(x,str) for x in argv),'Original allocator argv missing')
    index=next((i for i,x in enumerate(argv) if Path(x).name=='ck3_mod_acceptance.py'),-1)
    # The public CLI's mode is positional: it accepts both mode-first and
    # global-options-first invocations. Preserve the actual argv unchanged.
    need(index>=0 and argv.count('allocate')==1 and
         (argv[index+1:index+2]==['allocate'] or argv[-1:] == ['allocate']),
         'Actual original allocator command differs')
    return argv

def _sequence(row: JsonObject, key: str) -> int:
    value=row.get(key)
    if type(value) is not int or not isinstance(value,int) or value<1:
        raise ValueError('Exact positive release sequence required: '+key)
    return value

def _release_stages(keeper: JsonObject, cas: JsonObject, done: JsonObject,
                    cas_source: JsonObject, done_source: JsonObject, release: JsonObject,
                    task: str, *, cooperative_pin_refusal: bool=False) -> str:
    closed_lease = same_directory_control_peer('ck3_mod_acceptance_allocate').closed_lease
    for value in (cas,done):
        event=object_field(value,'event')
        need(event['task_id']==task and event['resources']==[],
             'Wrong allocated-unrun CAS task/resources')
    cas_event=object_field(cas,'event');done_event=object_field(done,'event')
    cas_task=object_field(cas,'task');done_task=object_field(done,'task')
    first_sequence=_sequence(cas_event,'sequence')
    last_sequence=_sequence(done_event,'sequence')
    separate=(cas_event['kind']=='status' and done_event['kind']=='completed'
               and first_sequence<last_sequence)
    # release-screen-cas completes by default for idle and refused allocations.
    # A later administrative completion preserves that original release.
    completed_then_admin=(cas_event['kind']==done_event['kind']=='completed'
                          and first_sequence<last_sequence
                          and cas_task.get('task_id')==task and cas_task.get('state')=='done'
                          and cas_task.get('resources')==[]
                          and _sequence(cas_task,'last_sequence')==first_sequence)
    # A direct CAS completion is one original event. The two proof files must
    # preserve the same canonical bytes/offset/task, rather than mix releases.
    direct=(cas_event['kind']==done_event['kind']=='completed'
             and first_sequence==last_sequence
             and cas_event==done_event and cas_task==done_task
            and cas_source.get('schema')=='xar-screen-release-canonical-reconstruction-v1'
            and cas_source==done_source)
    need((separate or direct or completed_then_admin) and _sequence(keeper,'last_sequence')<first_sequence
         and _sequence(done_task,'last_sequence')==last_sequence and done_task['state']=='done'
         and release==done and closed_lease(keeper,done,task),
         'Actual allocated-unrun CAS then admin DONE differs')
    return 'direct-completed' if direct else ('completed-then-admin-completed' if completed_then_admin else 'status-then-completed')

def _journal_events(raw: bytes, start: int, release_sequence: int,
        done_sequence: int) -> dict[int, tuple[int, bytes, JsonObject]]:
    sequences: JsonObject = {'release_sequence': release_sequence, 'done_sequence': done_sequence}
    requested = {_sequence(sequences, 'release_sequence'), _sequence(sequences, 'done_sequence')}
    lines: dict[int, tuple[int, bytes, JsonObject]] = {}
    offset = start
    for line in raw.splitlines(keepends=True):
        row = json_object(json.loads(line))
        sequence = _sequence(row, 'sequence')
        if sequence in requested:
            need(sequence not in lines,'Duplicate original CAS/DONE sequence in bounded journal tail')
            lines[sequence]=(offset,line,row)
        offset+=len(line)
    need(len(lines)==len(requested),'Exact original CAS/DONE events absent from bounded journal tail')
    return lines

def _closed_keeper_aborted_start(intent: JsonObject, process: JsonObject,
        wrapper: JsonObject, machine: str) -> datetime:
    """Bind the original serial records; never reconstruct its lost Popen wait."""
    if (set(intent) != {'machine_id', 'observed_at_utc', 'argv', 'started_at_utc'}
            or set(process) != {'machine_id', 'observed_at_utc', 'pid',
                'process_create_time_seconds', 'started_at_utc', 'original_wait_pending'}
            or process.get('original_wait_pending') is not True):
        raise ValueError('Exact original serial allocator intent/start fields required')
    source = _evidence_pin(wrapper.get('original_source'), 'Original aborted serial source')
    source_path = Path(source['path'])
    check_pin(source_path, dict(source))
    if source_path.suffix != '.py':
        raise ValueError('Original aborted serial Python source required')
    ast.parse(source_path.read_bytes(), filename=str(source_path))
    failure = json_object(_pinned_object(wrapper.get('original_failure'), 'Original serial failure'))
    tool = json_object(_pinned_object(wrapper.get('original_tool_result'), 'Original wrapper tool terminal'))
    if (set(failure) != {'machine_id', 'observed_at_utc', 'error', 'public_started',
                'display_before', 'no_automatic_replay'}
            or failure.get('machine_id') != machine or failure.get('public_started') is not False
            or failure.get('display_before') is not None or failure.get('no_automatic_replay') is not True
            or not isinstance(failure.get('error'), str) or not failure['error']
            or failure.get('observed_at_utc') != wrapper.get('observed_at_utc')
            or tool != wrapper.get('tool_result')):
        raise ValueError('Original serial failure/source/tool provenance differs')
    intended = _timestamp(intent.get('started_at_utc'), 'Original serial allocator start')
    stamps = [intended, _timestamp(intent.get('observed_at_utc'), 'Original serial allocator intent'),
        _timestamp(process.get('started_at_utc'), 'Original serial Popen observation'),
        _timestamp(process.get('observed_at_utc'), 'Original serial process record')]
    birth = process.get('process_create_time_seconds')
    if not isinstance(birth, str) or re.fullmatch(r'(?:0|[1-9][0-9]*)\.[0-9]+', birth) is None:
        raise ValueError('Original allocator birth must retain exact decimal seconds')
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    def seconds(value: datetime) -> Decimal:
        delta = value - epoch
        return Decimal(delta.days * 86400 + delta.seconds) + Decimal(delta.microseconds) / Decimal(1000000)
    if (stamps != sorted(stamps) or not seconds(intended) <= Decimal(birth) <= seconds(stamps[-1])):
        raise ValueError('Original serial allocator birth/observation chronology differs')
    return intended


def _closed_aborted_keeper(bundle: JsonObject, previous: Path, keeper_root: Path,
        task: str, run: str, ready_at: datetime, failure_at: datetime, closed_at: datetime) -> JsonObject:
    """Credit only the allocator's actual retained keeper Popen wait0."""
    keeper = json_object(_exact(bundle, 'keeper', keeper_root/'report.json'))
    parent = json_object(_exact(bundle, 'keeper_parent_exit', previous/'keeper-actual-parent-exit.json'))
    idle = json_object(_exact(bundle, 'idle_timeout', previous/'allocation-unused-idle-timeout.json'))
    stop = _evidence_pin(bundle.get('keeper_STOP'), 'Actual idle STOP')
    if Path(stop['path']).resolve() != (keeper_root/'STOP').resolve():
        raise ValueError('Actual closed keeper STOP crossed original path')
    check_pin(keeper_root/'STOP', dict(stop))
    if (keeper.get('task_id') != task or keeper.get('thread_exited') is not True
            or keeper.get('failure') is not None or keeper.get('entry_error') is not None
            or keeper.get('game_actions') is not False or parent.get('run_id') != run
            or type(parent.get('keeper_actual_exit_code')) is not int or parent['keeper_actual_exit_code'] != 0
            or parent.get('keeper_report') != keeper or parent.get('business_pass') is not False
            or idle.get('reason') != 'NEVER_LAUNCHED_ALLOCATION_IDLE_TIMEOUT'
            or type(idle.get('idle_seconds')) is not int or idle['idle_seconds'] != 600
            or any(idle.get(key) is not False for key in
                ('game_started', 'native_session_started', 'normal_close_qualified', 'business_pass'))
            or (keeper_root/'STOP').read_text(encoding='utf-8') !=
                'Unused allocation idle deadline; no game/native/normal credit.\n'):
        raise ValueError('Original closed keeper idle STOP/internal Popen wait0 differs')
    idle_at = _timestamp(idle.get('utc'), 'Original idle timeout')
    finished = _timestamp(keeper.get('at_utc'), 'Original keeper completion')
    if (not ready_at <= failure_at <= idle_at <= finished <= closed_at
            or (idle_at-ready_at).total_seconds() < 600):
        raise ValueError('Original closed keeper ten-minute idle interval differs')
    return keeper


def validate_aborted_allocation_v1(previous: Path, freeze_value: object, close_path: Path,
        keeper_root: Path, release_value: object, bus_value: object, next_state: Path) -> JsonObject:
    """Administrative admission only; lost original waits remain unknown."""
    import psutil
    import ck3_live_run_id as ids
    allocator = same_directory_control_peer('ck3_mod_acceptance_allocate')
    freeze = json_object(freeze_value)
    bundle = json_object(_read(close_path))
    machine, run, task = ids.current_machine_id(), _text(freeze['run_id'],'run'), _text(freeze['screen_task'],'task')
    closed_keeper = bundle.get('closure_kind') == CLOSED_KEEPER_ABORTED_KIND
    required = (ClosedKeeperAbortedAllocationClosureV1.__required_keys__ if closed_keeper
        else AbortedAllocationClosureV1.__required_keys__)
    if (set(bundle) != set(required)
            or bundle.get('schema') != SCHEMA or bundle.get('closure_kind') not in (ABORTED_KIND, CLOSED_KEEPER_ABORTED_KIND)
            or bundle.get('machine_id') != machine or bundle.get('run_id') != run
            or any(bundle.get(k) is not False for k in ('host_started','native_session_started',
                'game_started','normal_close_qualified','original_host_exit0','business_pass',
                'allocator_original_wait_observed'))
            or 'allocator_exit_code' not in bundle or bundle['allocator_exit_code'] is not None
            or bundle.get('keeper_original_wait_observed') is not closed_keeper
            or (closed_keeper and (type(bundle.get('keeper_exit_code')) is not int or bundle['keeper_exit_code'] != 0))
            or (not closed_keeper and ('keeper_exit_code' not in bundle or bundle['keeper_exit_code'] is not None))):
        raise ValueError('Aborted allocation must preserve unknown waits and no game credit')
    identity = json_object(freeze['identity_allocation'])
    state = Path(str(freeze['state_dir'])).resolve()
    if (identity.get('machine_id') != machine or previous.resolve().name != run
            or Path(str(bundle.get('quarantined_state'))).resolve() != state
            or next_state.resolve() == state or next_state.resolve().is_relative_to(state)
            or state.is_relative_to(next_state.resolve())):
        raise ValueError('Aborted original state must remain separate and quarantined')
    def original(key: str, path: Path) -> JsonObject:
        reference = _evidence_pin(bundle.get(key), key)
        if Path(reference['path']).resolve() != path.resolve():
            raise ValueError('Aborted original path differs: ' + key)
        return json_object(_pinned_object(reference, key))
    original('frozen', previous/'frozen-argv.json')
    ready = original('ready', previous/'ready-context.json')
    context = original('allocated_context', previous/'allocated-context.json')
    prepared_ref = _evidence_pin(ready.get('prepared_case'), 'prepared case')
    original('prepared_case', Path(prepared_ref['path']))
    if (ready.get('run_id') != run or context.get('run_id') != run
            or ready.get('frozen_argv') != bundle.get('frozen')
            or ready.get('prepared_case') != bundle.get('prepared_case')
            or context.get('prepared_case') != ready.get('prepared_case')
            or Path(str(ready.get('run_dir'))).resolve() != previous.resolve()
            or Path(str(ready.get('keeper_root'))).resolve() != keeper_root.resolve()):
        raise ValueError('Aborted READY/context/frozen identity differs')
    keeper_process = original('keeper_process', previous/'keeper-process.json')
    inputs = original('keeper_inputs', keeper_root/'inputs.json')
    keeper_ready = original('keeper_ready', keeper_root/'ready.json')
    lease = json_object(keeper_ready['lease'])
    if inputs.get('task_id') != task or lease.get('task_id') != task:
        raise ValueError('Aborted original keeper task differs')
    intent = json_object(_pinned_object(bundle.get('allocator_intent'), 'allocator intent'))
    process = json_object(_pinned_object(bundle.get('allocator_process'), 'allocator process'))
    wrapper = json_object(_pinned_object(bundle.get('allocator_aborted_wrapper'), 'wrapper failure'))
    argv = intent.get('argv')
    if (not isinstance(argv,list) or not all(isinstance(x,str) for x in argv)
            or (not closed_keeper and (process.get('argv') != argv or intent.get('stage') != 'allocate'))
            or intent.get('machine_id') != machine or process.get('machine_id') != machine):
        raise ValueError('Aborted original allocator command differs')
    def argument(flag: str) -> str:
        if argv.count(flag) != 1 or argv.index(flag)+1 >= len(argv):
            raise ValueError('Aborted original allocator argument missing: '+flag)
        return _text(argv[argv.index(flag)+1], flag)
    pid = _integer(process.get('pid'), 'allocator PID', 1)
    keeper_pid = _integer(keeper_process.get('pid'), 'keeper PID', 1)
    tool = json_object(wrapper.get('tool_result'))
    if (wrapper.get('schema') != 'operational-wrapper-external-exec-failure-v1'
            or wrapper.get('machine_id') != machine or _integer(wrapper.get('allocator_started_pid'),'wrapper allocator PID',1) != pid
            or _integer(wrapper.get('keeper_started_pid'),'wrapper keeper PID',1) != keeper_pid
            or wrapper.get('allocator_original_popen_wait_observed') is not False
            or 'allocator_exit_code' not in wrapper or wrapper['allocator_exit_code'] is not None
            or wrapper.get('run_invoked') is not False or wrapper.get('game_started') is not False
            or type(tool.get('exit_code')) is not int or tool['exit_code'] != 1
            or (not closed_keeper and 'session_id' not in tool) or tool.get('session_id') is not None
            or not isinstance(tool.get('chunk_id'),str) or not tool['chunk_id']
            or Path(argument('--prepared-case')).resolve() != Path(prepared_ref['path']).resolve()
            or Path(argument('--keeper-output')).resolve() != keeper_root.resolve()
            or argv.count('allocate') != 1):
        raise ValueError('Original pre-game wrapper failure/unknown wait differs')
    intended = (_closed_keeper_aborted_start(intent, process, wrapper, machine) if closed_keeper
        else _timestamp(intent.get('at_utc'),'allocator intent'))
    stamps = [intended,
              _timestamp(keeper_ready.get('at_utc'),'keeper ready'),
              _timestamp(wrapper.get('observed_at_utc'),'wrapper failure'),
              _timestamp(bundle.get('observed_at_utc'),'closure observation')]
    if (stamps != sorted(stamps) or stamps[-1] > datetime.now(timezone.utc)
            or (closed_keeper and _timestamp(process.get('observed_at_utc'), 'Original allocator process') > stamps[1])):
        raise ValueError('Aborted original timestamps differ')
    stdout_ref = _evidence_pin(bundle.get('allocator_stdout'),'allocator stdout')
    check_pin(Path(stdout_ref['path']),dict(stdout_ref))
    stdout = Path(stdout_ref['path']).read_text(encoding='utf-8-sig').lstrip()
    terminal: JsonObject | None = None
    if closed_keeper:
        value, end = json.JSONDecoder().raw_decode(stdout)
        allocated = json_object(value)
        terminal = json_object(json.loads(stdout[end:]))
    else:
        allocated = json_object(json.loads(stdout))
    if (allocated.get('status') != 'ACTUAL_ALLOCATED_KEEPER_READY_NOT_RUN'
            or allocated.get('task') != task or _integer(allocated.get('keeper_pid'),'READY keeper PID',1) != keeper_pid
            or Path(str(allocated.get('live'))).resolve() != previous.resolve()
            or Path(str(allocated.get('context'))).resolve() != (previous/'ready-context.json').resolve()
            or (closed_keeper and any(allocated.get(key) is not False for key in ('game_started', 'business_pass')))):
        raise ValueError('Actual aborted allocator READY stdout differs')
    keeper: JsonObject | None = None
    if closed_keeper:
        keeper = _closed_aborted_keeper(bundle, previous, keeper_root, task, run, stamps[1], stamps[2], stamps[3])
        parent = _exact(bundle, 'keeper_parent_exit', previous/'keeper-actual-parent-exit.json')
        if terminal is None or terminal != {**allocated, **parent}:
            raise ValueError('Original allocator final stdout differs from its internal keeper wait')
    absent = {name:not (previous/name).exists() for name in ('launch-intent.json','launch.json',
        'host-started.json','host-supervisor.json','host-supervisor-started.json','supervisor.json',
        'host-original-process-exit.json','native-report.json','native-report.session.log','case-output')}
    if not closed_keeper:
        absent.update({'keeper-actual-parent-exit.json':not (previous/'keeper-actual-parent-exit.json').exists(),
            'keeper/report':not (keeper_root/'report.json').exists()})
    absent.update({'state/control':not (state/'control').exists(), 'state/native-session':not (state/'native-session').exists(),
        'controls-empty':(previous/'controls').is_dir() and not any((previous/'controls').iterdir())})
    for name in ('save games','logs','run'):
        path = state/'profile'/name
        absent['profile/'+name] = not path.exists() or not any(path.iterdir())
    if not all(absent.values()):
        raise ValueError('Aborted allocation has launch/native/control/Save or original terminal evidence')
    root = ids.default_state_root().resolve()
    if Path(str(identity['state_root'])).resolve() != root:
        raise ValueError('Aborted machine counter namespace differs')
    products = Path(argument('--products')).resolve()
    files = json_object(freeze['files'])
    check_pin(products, json_object(files[str(products)]))
    product_key = argument('--product')
    product = json_object(json_object(_read(products)['products'])[product_key])
    external = product.get('external_mod',False)
    counter = original('counter', root/machine/str(freeze['mod_key'])/'counter.json')
    if (type(external) is not bool or counter.get('machine_id') != machine
            or counter.get('mod_key') != freeze['mod_key'] or product_key != ready.get('product')
            or ids.format_run_id(machine,str(freeze['mod_key']),_integer(counter.get('last_sequence'),'counter',1),
                external_mod=external) != run):
        raise ValueError('Aborted allocation is not the latest actual counter')
    release_ref = _evidence_pin(bundle.get('CAS_release'),'CAS release')
    check_pin(Path(release_ref['path']),dict(release_ref))
    actual = json_object(allocator.read_failed_runtime_release(Path(release_ref['path'])))
    release = json_object(release_value)
    done_ref = _evidence_pin(bundle.get('admin_done'),'administrative completion')
    check_pin(Path(done_ref['path']),dict(done_ref))
    done = json_object(allocator.read_failed_runtime_release(Path(done_ref['path'])))
    done_event, done_task = json_object(done['event']), json_object(done['task'])
    event, released_task = json_object(actual['event']), json_object(actual['task'])
    retirement = {} if closed_keeper else json_object(event.get('retirement'))
    if closed_keeper:
        if keeper is None:
            raise ValueError('Actual closed keeper report required')
        _release_stages(keeper, actual, done, _read(release_ref['path']), _read(done_ref['path']), release, task)
    elif (done != release or actual.get('ok') is not True or done.get('ok') is not True
            or event.get('task_id') != task or released_task.get('task_id') != task
            or event.get('resources') != [] or released_task.get('resources') != []
            or event.get('state') != 'waiting' or released_task.get('state') != 'waiting'
            or _integer(event.get('sequence'),'release sequence',1) != _integer(released_task.get('last_sequence'),'CAS task sequence',1)
            or retirement.get('kind') != 'expired-own-claim-released'
            or retirement.get('business_status') != 'unresolved_red'
            or _integer(retirement.get('prior_sequence'),'prior sequence',1) != _integer(lease.get('sequence'),'keeper lease sequence',1)
            or done_event.get('kind') != 'completed' or done_event.get('task_id') != task
            or done_task.get('task_id') != task or done_task.get('state') != 'done'
            or done_event.get('state') != 'done' or done_event.get('resources') != [] or done_task.get('resources') != []
            or _integer(done_event.get('sequence'),'done sequence',1) != _integer(done_task.get('last_sequence'),'done task sequence',1)
            or _integer(done_event.get('sequence'),'done sequence',1) <= _integer(event.get('sequence'),'CAS sequence',1)
            or done_task.get('repo') != released_task.get('repo') or done_task.get('git') != released_task.get('git')):
        raise ValueError('Original aborted allocation CAS retirement differs')
    tasks = json_object(bus_value).get('tasks')
    if not isinstance(tasks,list):raise ValueError('Current canonical bus tasks required')
    rows = [json_object(item) for item in tasks]
    matches = [item for item in rows if item.get('task_id') == task]
    if (any('ck3-screen:acquired' in item.get('resources',[]) for item in rows)
            or len(matches) != 1 or {k:v for k,v in matches[0].items() if k not in ('age_seconds','stale')} != done_task):
        raise ValueError('Current aborted allocation task/resources differ')
    source = Path(str(freeze['source_root']))/'ck3_autonomous_player/src'
    sys.path.insert(0,str(source))
    try:
        provider = importlib.import_module('xar_autoplayer.environment')
        if not Path(str(provider.__file__)).resolve().is_relative_to(source.resolve()):
            raise ValueError('Aborted process provider crossed frozen source')
        game = json_object(provider.ck3_process_inventory())
    finally:
        sys.path.remove(str(source))
    inventory = json_object(allocator.runtime_process_inventory(psutil,os.getpid()))
    if (inventory.get('blockers') != [] or type(game.get('tasklist_returncode')) is not int or game.get('tasklist_returncode') != 0
            or game.get('tasklist_pids') != [] or game.get('wmi_pids') != []
            or game.get('processes') != [] or psutil.pid_exists(pid) or psutil.pid_exists(keeper_pid)):
        raise ValueError('Fresh dual-provider aborted process absence failed')
    evidence = {k:v for k,v in bundle.items() if k != 'counter' and isinstance(v,dict) and 'sha256' in v}
    evidence['actual_unrun_consumer'] = pin(Path(__file__))
    evidence['actual_allocator_consumer'] = pin(Path(allocator.__file__))
    # This existing mode invokes the real reducer again under the allocator's
    # original machine writer lock. It grants resource continuation, not play.
    return json_object({'mode':('previous-shared-allocated-unrun-prelaunch-orchestrator-failed' if closed_keeper
            else 'previous-shared-allocated-aborted-wrapper-resource-only'),
        'actual_process_inventory':inventory,'failure_cleanup':{'close':pin(close_path),'original_evidence':evidence,
            'absent_launch_native_control_Save':absent,'quarantined_state':str(state),
            'original_allocator_wait_proven':False,'original_allocator_exit_code':None,
            'original_keeper_wait_proven':closed_keeper,'original_keeper_exit_code':0 if closed_keeper else None,
            'original_host_exit_code':None,'original_ck3_exit_code':None,
            'normal_close_qualified':False,'typed_normal_exit_proven':False,'business_pass':False,'release_pass':False,
            'native_cleanup_qualified':None,
            'administrative_resource_admission_only':True}})


def _capacity_wait_source(reference: object) -> None:
    """Attest the recorder's wait/STOP/timeout control flow, never execute it.

    The AST signatures describe reusable recorder functions and the bounded
    capacity loop. They contain no machine, attempt, path, PID or source commit.
    A different recorder requires its own reviewed receipt format.
    """
    tree = ast.parse(_serial_raw(reference).decode('utf-8-sig'))
    mains = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main']
    if len(mains) != 1:
        raise ValueError('One original capacity-wait recorder main required')
    nodes: dict[str, ast.AST] = {n.name:n for n in tree.body if isinstance(n, ast.FunctionDef)}
    nodes.update({'main.'+n.name:n for n in mains[0].body if isinstance(n, ast.FunctionDef)})
    tries = [n for n in mains[0].body if isinstance(n, ast.Try)]
    if len(tries) != 1:
        raise ValueError('One original capacity-wait failure boundary required')
    observed = tries[0]
    waits = [i for i,n in enumerate(observed.body) if isinstance(n, ast.While)]
    if len(waits) != 1 or waits[0] < 4:
        raise ValueError('One bounded original capacity-wait loop required')
    nodes['capacity_wait'] = ast.Module(body=observed.body[waits[0]-4:waits[0]+1], type_ignores=[])
    nodes['failure_handlers'] = ast.Try(body=[], handlers=observed.handlers, orelse=[], finalbody=[])
    expected = {
        'consume_original':'7ca90dfbace6c5a25fb52b0fac1b8f7a651dc2e5d03d7e023296f420e12f5f75',
        'creation_seconds':'4e0ae5561a49af6f8fb112df1362a8351c134e51232209058faf77ce9ae08437',
        'put':'6c0188db154c453d052468c202902a64186a7fdc5e9cc30e287c1756ce17e7a6',
        'drain_original_handles':'398b962452a7071067f33fa1ad471b7c9db930b4cab40c7e42f9cef5c062513d',
        'main.start':'daba89c3dbcf116ca1a5d6550a682b54b186029eb491b6b758ca3a4e3b839af7',
        'main.wait':'3a5a340bdbcb0e16ff3c362b02399cec5feef75cf28cfde7c5e0419f260b1326',
        'main.stop_keeper':'9e66a70ccd3cf6ea0e5d4ee98b6e4120f70e5ef6fa341ffc3654485a2f3b10bc',
        'main.cancel_own_guards':'7b4fa35d78b00cd3d77d0c36549737a007b4d6224cc802c02c250949659a33f5',
        'capacity_wait':'37865d0687bc3e56f5079fa56643f881cf1f7f0e800b2444c7d428b2d7d8021e',
        'failure_handlers':'0e402a2d10a853bfe943fe7e3c888f7dbde61dbd4c1adb1b655e3e7c4efb0486',
    }
    if any(name not in nodes or hashlib.sha256(ast.dump(nodes[name], include_attributes=False).encode()).hexdigest()!=sha
           for name,sha in expected.items()):
        raise ValueError('Original capacity-wait recorder source AST differs')
    popens = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute) and n.func.attr == 'Popen']
    if len(popens) != 1:
        raise ValueError('Original capacity-wait recorder must retain its single Popen producer')
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ('exec','eval','setattr','delattr'):
            raise ValueError('Capacity-wait recorder dynamic source mutation refused')
        if isinstance(n, ast.Name) and isinstance(n.ctx,(ast.Store,ast.Del)) and n.id in ('subprocess','time','json','datetime','Path'):
            raise ValueError('Capacity-wait recorder imported binding changed')


def _capacity_wait_root_paths(wait: Path) -> tuple[Path, Path, Path]:
    if wait.name != 'ROOT-SERIAL.original-wait.actual.json':
        raise ValueError('Exact external-capacity Root recorder filename required')
    return (wait.with_name('ROOT-SERIAL.started.actual.json'),
        wait.with_name('ROOT-SERIAL.stdout.log'), wait.with_name('ROOT-SERIAL.stderr.log'))


def _capacity_wait_ready_prefix(reference: object, complete: object) -> None:
    """The original READY pin predates the appended actual keeper wait result."""
    prefix=file_pin(reference);whole=file_pin(complete)
    raw=_serial_raw(whole)
    if (Path(prefix['path']).resolve()!=Path(whole['path']).resolve()
            or not 0<prefix['bytes']<len(raw)
            or hashlib.sha256(raw[:prefix['bytes']]).hexdigest()!=prefix['sha256']):
        raise ValueError('Original capacity READY stdout prefix changed')
    initial=json_object(json.loads(raw[:prefix['bytes']]))
    first,_=json.JSONDecoder().raw_decode(raw.decode('utf-8-sig').lstrip())
    if initial!=json_object(first) or initial.get('status')!='ACTUAL_ALLOCATED_KEEPER_READY_NOT_RUN':
        raise ValueError('Capacity stdout prefix must be exactly the original complete READY JSON')


def validate_capacity_wait(bundle: Mapping[str, object], *, previous: Path,
        keeper: Path, machine: str, ready_at: datetime, keeper_closed_at: datetime) -> dict[str, FilePin]:
    """Observe a real external-capacity timeout; no guard/idle/DONE projection."""
    if bundle.get('closure_kind') != CAPACITY_WAIT_KIND or bundle.get('receipt_format') != CAPACITY_WAIT_FORMAT:
        raise ValueError('Exact external-capacity-wait closure kind/format required')
    if any(key in bundle for key in ('serial_guards','prelaunch_guard_state','idle_timeout','admin_done')):
        raise ValueError('Capacity-wait closure cannot claim a guard, idle timeout or administrative DONE')
    evidence: dict[str,FilePin] = {}
    def original(key: str, path: Path | None = None) -> JsonObject:
        ref,value = _serial_original(bundle.get(key),path);evidence[key]=ref;return value
    root_wait = Path(file_pin(bundle.get('prelaunch_orchestrator_wait'))['path'])
    root_start,stdout_path,stderr_path = _capacity_wait_root_paths(root_wait)
    start=original('prelaunch_orchestrator_started',root_start)
    waited=original('prelaunch_orchestrator_wait',root_wait)
    base={'machine_id','argv','pid','process_create_time_seconds','started_at_utc'}
    if (set(start)!=base|{'original_wait_pending'} or set(waited)!=base|{
            'actual_original_popen_wait','original_wait_returncode','finished_at_utc'}
            or start.get('machine_id')!=machine or waited.get('machine_id')!=machine
            or start.get('original_wait_pending') is not True or waited.get('actual_original_popen_wait') is not True
            or type(waited.get('original_wait_returncode')) is not int or waited['original_wait_returncode']!=1
            or _integer(start.get('pid'),'Capacity Root PID',1)!=_integer(waited.get('pid'),'Waited capacity Root PID',1)
            or start.get('argv')!=waited.get('argv') or start.get('started_at_utc')!=waited.get('started_at_utc')
            or start.get('process_create_time_seconds')!=waited.get('process_create_time_seconds')):
        raise ValueError('Exact original capacity Root start/birth/wait1 required')
    birth=text_field(start,'process_create_time_seconds')
    if re.fullmatch(r'(?:0|[1-9][0-9]{0,12})(?:\.[0-9]{1,7})?',birth) is None:
        raise ValueError('Original capacity Root birth must be a canonical decimal string')
    def epoch(stamp: datetime) -> Decimal:
        delta=stamp-datetime(1970,1,1,tzinfo=timezone.utc)
        return Decimal(delta.days*86400+delta.seconds)+Decimal(delta.microseconds)/1000000
    began=_timestamp(start.get('started_at_utc'),'Root capacity start')
    finished=_timestamp(waited.get('finished_at_utc'),'Root capacity finish')
    if not epoch(began)<=Decimal(birth)<=epoch(finished):
        raise ValueError('Original capacity Root birth chronology differs')
    argv=tuple(strings_field(start,'argv'));source=file_pin(bundle.get('prelaunch_orchestrator_source'))
    _capacity_wait_source(source);evidence['prelaunch_orchestrator_source']=source
    if len(argv)<5 or argv[1:4]!=('-B','-X','utf8') or Path(argv[4]).resolve()!=Path(source['path']).resolve():
        raise ValueError('Capacity Root source/argv differs')
    commit=_serial_argument(argv,'--source-commit')
    frozen=original('frozen',previous/'frozen-argv.json')
    _,manifest=_serial_original(frozen.get('runtime_manifest'))
    if re.fullmatch('[a-f0-9]{40}',commit) is None or manifest.get('source_commit')!=commit:
        raise ValueError('Capacity Root source differs from original frozen runtime')
    allocated=_serial_allocator(bundle,machine,commit)
    terminal=_ttl_allocator_stdout(json_object({'allocator_stdout':bundle.get('allocator_stdout')}))
    parent=original('keeper_parent_exit',previous/'keeper-actual-parent-exit.json')
    if (type(parent.get('keeper_actual_exit_code')) is not int or parent['keeper_actual_exit_code']!=0
            or any(terminal.get(key)!=value for key,value in parent.items())):
        raise ValueError('Capacity allocator original stdout crossed keeper original wait0')
    execution=Path(file_pin(bundle.get('allocator_intent'))['path']).parent
    static=original('serial_static',execution/'STATIC-INPUTS-PRECOMPILED.actual.json')
    failure=original('serial_failure',execution/'ROOT-SERIAL-FAILURE.actual.json')
    awaiting=original('capacity_wait_awaiting',execution/'AWAITING-ROOT-PRELAUNCH-CAPACITY.actual.json')
    if (static.get('machine_id')!=machine or static.get('source_commit')!=commit
            or static.get('new_capacity_scanner_created') is not False or static.get('cold_guard_used') is not False
            or static.get('original_Popen_registry_retained') is not True
            or any(key in static for key in ('guard_original','guard_interpreter','capacity_original'))):
        raise ValueError('Capacity-wait original static scope differs')
    for field,flag in (('grant','--grant'),('ready','--ready'),('preallocate_capacity','--preallocate-capacity')):
        ref=file_pin(static.get(field));_serial_raw(ref,Path(_serial_argument(argv,flag)))
        if ref['sha256']!=_serial_argument(argv,flag+'-sha256'):
            raise ValueError('Capacity-wait original launch input binding differs')
        evidence['capacity_bound_'+field]=ref
    requested=Path(_serial_argument(argv,'--prelaunch-capacity'))
    fields={'machine_id','observed_at_utc','run_id','ready_context','allocation_stdout','grant','expected_output',
        'maximum_wait_seconds','Game_not_started','capacity_collector_owner'}
    if (set(awaiting)!=fields or awaiting.get('machine_id')!=machine or awaiting.get('run_id')!=previous.name
            or awaiting.get('Game_not_started') is not True or awaiting.get('capacity_collector_owner')!='/root'
            or type(awaiting.get('maximum_wait_seconds')) is not int or awaiting['maximum_wait_seconds']!=180
            or Path(text_field(awaiting,'expected_output')).resolve()!=requested.resolve()
            or static.get('postallocate_capacity_path')!=str(requested)
            or requested.exists() or file_pin(awaiting.get('ready_context'))!=file_pin(bundle.get('ready'))
            or file_pin(awaiting.get('grant'))!=file_pin(static.get('grant'))):
        raise ValueError('Exact original capacity wait/READY/requested output differs')
    _capacity_wait_ready_prefix(awaiting.get('allocation_stdout'),bundle.get('allocator_stdout'))
    expected_error=repr(TimeoutError('Root postallocate capacity not delivered within180s; no public run'))
    failure_fields={'machine_id','observed_at_utc','error','public_started','display_before','no_automatic_replay',
        'screen_CAS_attempted','original_handles'}
    handle={'label':'ALLOCATE','pid':allocated.pid,'birth_filetime':allocated.birth_filetime,
        'original_wait_consumed':False,'actual_returncode':None}
    handles=failure.get('original_handles')
    actual_handle=json_object(handles[0]) if isinstance(handles,list) and len(handles)==1 else {}
    if (set(failure)!=failure_fields or failure.get('machine_id')!=machine or failure.get('error')!=expected_error
            or failure.get('public_started') is not False or failure.get('display_before') is not None
            or failure.get('no_automatic_replay') is not True or failure.get('screen_CAS_attempted') is not False
            or type(actual_handle.get('pid')) is not int or actual_handle.get('original_wait_consumed') is not False
            or failure.get('original_handles')!=[handle]):
        raise ValueError('Capacity-wait original failure/retained allocator differs')
    waiting_at=_timestamp(awaiting.get('observed_at_utc'),'Original capacity waiting start')
    failed_at=_timestamp(failure.get('observed_at_utc'),'Original capacity wait timeout')
    if (not began<=allocated.started_at<=ready_at<=waiting_at<=failed_at<=keeper_closed_at<=allocated.finished_at<=finished
            or not 180<=(failed_at-waiting_at).total_seconds()<=210):
        raise ValueError('Actual bounded capacity wait/Root/allocator/keeper chronology differs')
    stdout=_serial_raw(bundle.get('serial_root_stdout'),stdout_path).decode('utf-8')
    stderr=_serial_raw(bundle.get('serial_root_stderr'),stderr_path).decode('utf-8')
    terminals=[json_object(json.loads(line.removeprefix('ORIGINAL_WAIT_ACTUAL '))) for line in stdout.splitlines()
        if line.startswith('ORIGINAL_WAIT_ACTUAL ')]
    typed_terminal=(len(terminals)==1 and type(terminals[0].get('pid')) is int
        and type(terminals[0].get('returncode')) is int and terminals[0].get('receipt_written') is True)
    if (stdout.splitlines().count('ACTUAL_READY_ROOT_CAPACITY_REQUIRED '+previous.name)!=1
            or any(line.startswith('ACTUAL_PUBLIC') for line in stdout.splitlines())
            or not typed_terminal or terminals!=[{'label':'ALLOCATE','pid':allocated.pid,'process_creation_filetime_100ns':allocated.birth_filetime,
                'receipt_written':True,'returncode':0}]
            or not stderr.replace('\r\n','\n').endswith('TimeoutError: Root postallocate capacity not delivered within180s; no public run\n')):
        raise ValueError('Original capacity Root stdout/timeout/allocator terminal differs')
    for key in ('serial_root_stdout','serial_root_stderr','keeper_STOP'):
        ref=file_pin(bundle.get(key));_serial_raw(ref);evidence[key]=ref
    if _serial_raw(bundle.get('keeper_STOP'),keeper/'STOP').decode('utf-8').replace('\r\n','\n')!='Root pre-public failure; original allocation proves own never-Game keeper; no continuation qualification.\n':
        raise ValueError('Actual capacity-wait cooperative STOP differs')
    if (any(execution.glob('*GUARD*')) or any(execution.glob('CAPACITY*')) or any((execution/name).exists() for name in
            ('PUBLIC-RUN.intent.actual.json','PUBLIC-RUN.started.actual.json','LAUNCH-GATES-CONSUMED.actual.json',
             'DISPLAY-MODE.actual.json','STEAM-OFFLINE.prelaunch.actual.json'))):
        raise ValueError('Capacity-wait original scope contains guard/public/display activity')
    return evidence


def _capacity_wait_release(bundle: Mapping[str,object], keeper: JsonObject, released: JsonObject,
        packet: JsonObject, task: str) -> JsonObject:
    """Old heartbeat age is separate from a fresh global SCREEN/OS observation."""
    ref=file_pin(bundle.get('resource_release'));canonical=json_object(_serial_resources().read_failed_runtime_release(Path(ref['path'])))
    _serial_raw(ref)
    task_row=object_field(canonical,'task');event=object_field(canonical,'event')
    retirement=object_field(event,'retirement')
    if (canonical!=released or canonical.get('ok') is not True or task_row.get('task_id')!=task
            or event.get('task_id')!=task or task_row.get('state')!='waiting' or event.get('state')!='waiting'
            or task_row.get('resources')!=[] or event.get('resources')!=[] or event.get('kind')!='status'
            or set(retirement)!={'kind','business_status','prior_sequence'}
            or retirement.get('kind')!='expired-own-claim-released' or retirement.get('business_status')!='unresolved_red'
            or _sequence(retirement,'prior_sequence')!=_sequence(keeper,'last_sequence')
            or _sequence(event,'sequence')<=_sequence(retirement,'prior_sequence')
            or _sequence(task_row,'last_sequence')!=_sequence(event,'sequence')
            or _timestamp(event.get('timestamp_utc'),'Expired release')<_timestamp(keeper.get('at_utc'),'Closed keeper')):
        raise ValueError('Exact expired waiting resource release/retirement chronology required')
    original_ref=file_pin(bundle.get('serial_release_original'))
    original=json_object(_serial_resources().read_failed_runtime_release(Path(original_ref['path'])))
    _serial_raw(original_ref)
    if any(original.get(key)!=canonical.get(key) for key in ('schema','ok','task','event')):
        raise ValueError('Original expired resource release differs from canonical event')
    tasks=packet.get('tasks')
    if not isinstance(tasks,list):
        raise ValueError('Fresh global SCREEN observation required')
    rows=[json_object(row) for row in tasks]
    for row in rows:
        resources=row.get('resources')
        if not isinstance(resources,list) or any(not isinstance(value,str) for value in resources):
            raise ValueError('Current SCREEN resource observation has invalid fields')
        if 'ck3-screen:acquired' in resources:
            raise ValueError('Current SCREEN owner revived after capacity-wait closure')
    matches=[row for row in rows if row.get('task_id')==task]
    snapshot=matches[0] if len(matches)==1 else {}
    age=snapshot.get('age_seconds');stale=snapshot.get('stale')
    if (len(matches)!=1 or set(snapshot)!=set(task_row)|{'age_seconds','stale'}
            or any(snapshot.get(key)!=value for key,value in task_row.items())
            or type(age) is not int or not isinstance(age,int) or age<0 or type(stale) is not bool):
        raise ValueError('Current historical closed task fields/age/stale types differ')
    return json_object({'receipt_format':CAPACITY_WAIT_FORMAT,'original_root_exit_code':1,
        'original_allocator_exit_code':0,'guard_original_wait_codes':[],
        'normal_close_qualified':False,'release_pass':False,'closed_task_age_seconds':age,
        'closed_task_stale':stale,'expired_waiting_release_sequence':_sequence(event,'sequence')})


def validate_allocated_unrun(previous: Path, freeze: object, close_path: Path, keeper_root: Path,
        release: object, bus_packet: object, *, next_state: Path | None = None) -> JsonObject:
    freeze=json_object(freeze);release=json_object(release);bus_packet=json_object(bus_packet)
    capacity_wait = _read(close_path).get('closure_kind') == CAPACITY_WAIT_KIND
    serial = _read(close_path).get('receipt_format') == SERIAL_PRELAUNCH_FORMAT
    if serial or capacity_wait:
        state = Path(text_field(json_object(freeze), 'state_dir')).resolve()
        if (not isinstance(next_state, Path) or next_state.resolve() == state
                or next_state.resolve().is_relative_to(state) or state.is_relative_to(next_state.resolve())):
            raise ValueError('Serial prelaunch recovery requires a separate next state')
    if _read(close_path).get('closure_kind') == OFFLINE_TTL_KIND:
        if not isinstance(next_state, Path):
            raise ValueError('TTL-refused allocation requires a separate next state')
        return validate_pre_intent_offline_ttl_refusal(Path(previous), freeze, Path(close_path),
            Path(keeper_root), release, bus_packet, next_state)
    if _read(close_path).get('closure_kind') in (ABORTED_KIND, CLOSED_KEEPER_ABORTED_KIND):
        if not isinstance(next_state,Path):raise ValueError('Aborted allocation requires a new separate state')
        return validate_aborted_allocation_v1(Path(previous),freeze,Path(close_path),Path(keeper_root),release,bus_packet,next_state)
    control_allocator = same_directory_control_peer('ck3_mod_acceptance_allocate')
    process_reader: object=control_allocator.runtime_process_inventory
    if not isinstance(process_reader,_UnrunProcessInventory):
        raise ValueError('Actual unrun process inventory provider required')
    resources=_serial_resources()
    import ck3_live_run_id as ids
    previous,keeper_root=Path(previous).resolve(),Path(keeper_root).resolve()
    bundle=_read(close_path);machine=ids.current_machine_id();run=text_field(freeze,'run_id');task=text_field(freeze,'screen_task')
    need(bundle.get('schema')==SCHEMA and bundle.get('run_id')==run and bundle.get('machine_id')==machine
         ==object_field(freeze,'identity_allocation').get('machine_id'),'Unrun full run/machine identity differs')
    need(all(bundle.get(k) is False for k in ('host_started','native_session_started','game_started',
         'normal_close_qualified','original_host_exit0','business_pass')),'Allocated-only closure cannot grant game/host credit')
    ready=_exact(bundle,'ready',previous/'ready-context.json')
    _exact(bundle,'frozen',previous/'frozen-argv.json')
    context=_exact(bundle,'allocated_context',previous/'allocated-context.json')
    need(ready['run_id']==context['run_id']==run and Path(text_field(ready,'run_dir')).resolve()==previous
         and Path(text_field(ready,'keeper_root')).resolve()==keeper_root and ready['frozen_argv']==bundle['frozen']
         and ready['prepared_case']==context['prepared_case'],'Original allocated-only READY differs')
    prepared_ref=file_pin(ready.get('prepared_case'))
    check_pin(Path(prepared_ref['path']),dict(prepared_ref))
    keeper=_exact(bundle,'keeper',keeper_root/'report.json')
    parent=_exact(bundle,'keeper_parent_exit',previous/'keeper-actual-parent-exit.json')
    need(keeper.get('task_id')==task and keeper.get('thread_exited') is True and keeper.get('failure') is None
         and keeper.get('entry_error') is None and keeper.get('game_actions') is False
         and parent.get('run_id')==run and parent.get('keeper_actual_exit_code')==0
         and parent.get('keeper_report')==keeper,'Original idle keeper STOP/wait0 unavailable')
    cooperative=bundle.get('closure_kind')=='launcher-pin-admission-refused-before-launch-intent'
    prelaunch=bundle.get('closure_kind')==PRELAUNCH_KIND
    need(bundle.get('closure_kind') is None or cooperative or prelaunch or capacity_wait,'Unknown allocated-unrun closure kind')
    refusal_evidence={}
    keeper_ready=_exact(bundle,'keeper_ready',keeper_root/'ready.json')
    if capacity_wait:
        refusal_evidence=validate_capacity_wait(bundle,previous=previous,keeper=keeper_root,machine=machine,
            ready_at=_timestamp(keeper_ready.get('at_utc'),'Capacity keeper ready'),
            keeper_closed_at=_timestamp(keeper.get('at_utc'),'Capacity keeper finished'))
    elif cooperative:
        refusal_evidence=validate_launcher_pin_refusal(bundle['launcher_pin_refusal'],frozen=freeze,
            live=previous,keeper=keeper_root,machine_id=machine)
        need(bundle['keeper_STOP']==refusal_evidence['keeper_stop'],'Cooperative STOP references differ')
    elif prelaunch:
        refusal_evidence=validate_prelaunch_orchestrator(bundle,previous=previous,keeper=keeper_root,machine=machine,
            ready_at=_timestamp(keeper_ready.get('at_utc'),'Prelaunch keeper ready'),
            keeper_closed_at=_timestamp(keeper.get('at_utc'),'Prelaunch keeper finished'))
    else:
        idle=_exact(bundle,'idle_timeout',previous/'allocation-unused-idle-timeout.json')
        stop=file_pin(bundle.get('keeper_STOP'));need(Path(stop['path']).resolve()==keeper_root/'STOP','Original STOP crossed keeper')
        check_pin(keeper_root/'STOP',dict(stop))
        need((keeper_root/'STOP').read_text(encoding='utf-8')=='Unused allocation idle deadline; no game/native/normal credit.\n'
             and idle.get('reason')=='NEVER_LAUNCHED_ALLOCATION_IDLE_TIMEOUT' and idle.get('idle_seconds')==600
             and all(idle.get(k) is False for k in ('game_started','native_session_started','normal_close_qualified','business_pass')),
             'Original unused idle STOP differs')
    stamps=[_timestamp(v,'Original unused interval') for v in ((keeper_ready['at_utc'],keeper['at_utc']) if cooperative or prelaunch or capacity_wait else
        (keeper_ready['at_utc'],idle['utc'],keeper['at_utc']))]
    need(all(x.tzinfo is not None for x in stamps) and stamps==sorted(stamps)
         and (cooperative or prelaunch or capacity_wait or (stamps[1]-stamps[0]).total_seconds()>=600),'Original unused interval unproven')
    argv=list(_serial_allocator(bundle,machine).argv) if capacity_wait else _allocator_argv(bundle,machine,stamps)
    def argument(name: str) -> str:
        need(argv.count(name)==1 and argv.index(name)+1<len(argv),'Original allocator argument missing: '+name)
        return argv[argv.index(name)+1]
    need(Path(argument('--prepared-case')).resolve()==Path(prepared_ref['path']).resolve()
         and Path(argument('--keeper-output')).resolve()==keeper_root,'Actual original allocator wait0 differs')
    stdout=file_pin(bundle.get('allocator_stdout'));check_pin(Path(stdout['path']),dict(stdout))
    allocated,end=json.JSONDecoder().raw_decode(Path(stdout['path']).read_text(encoding='utf-8-sig').lstrip())
    allocated=json_object(allocated)
    need(allocated.get('status')=='ACTUAL_ALLOCATED_KEEPER_READY_NOT_RUN' and allocated.get('task')==task
         and Path(text_field(allocated,'live')).resolve()==previous and Path(text_field(allocated,'keeper_root')).resolve()==keeper_root,
         'Actual original allocator READY output differs')
    state=Path(text_field(freeze,'state_dir')).resolve()
    absent={name:not (previous/name).exists() for name in ('launch-intent.json','launch.json','host-started.json',
        'host-supervisor.json','host-supervisor-started.json','supervisor.json','host-original-process-exit.json',
        'native-report.json','native-report.session.log','case-output')}
    absent['state/control']=not (state/'control').exists()
    absent['state/native-session']=not (state/'native-session').exists()
    absent['controls-empty']=(previous/'controls').is_dir() and not any((previous/'controls').iterdir())
    for name in ('save games','logs','run'):
        path=state/'profile'/name;absent['profile/'+name]=not path.exists() or not any(path.iterdir())
    need(all(absent.values()),'Allocated-unrun predecessor has actual host/native/control/Save evidence')
    identity=object_field(freeze,'identity_allocation');root=ids.default_state_root().resolve()
    need(Path(text_field(identity,'state_root')).resolve()==root,'Actual machine counter namespace differs')
    products=Path(argument('--products')).resolve();product_key=argument('--product')
    need(str(products) in object_field(freeze,'files'),'Original allocated product registry pin missing')
    check_pin(products,object_field(object_field(freeze,'files'),str(products)))
    product=object_field(object_field(_read(products),'products'),product_key);external_mod=product.get('external_mod',False)
    if type(external_mod) is not bool or not isinstance(external_mod,bool):
        raise ValueError('Product external_mod must be an exact boolean')
    need(type(external_mod) is bool and product_key==ready['product']
         and (product.get('runtime_mod_key') or product_key)==freeze['mod_key'],
         'Original allocated product namespace differs')
    counter=root/machine/text_field(freeze,'mod_key')/'counter.json';row=_exact(bundle,'counter',counter)
    need(row.get('machine_id')==machine and row.get('mod_key')==freeze['mod_key']
         and ids.format_run_id(machine,text_field(freeze,'mod_key'),_integer(row.get('last_sequence'),'Actual last allocation sequence',1),external_mod=external_mod)==run,
         'Allocated-unrun run is not the latest actual machine/product counter')
    capacity_cleanup: JsonObject = {}
    if capacity_wait:
        capacity_cleanup=_capacity_wait_release(bundle,keeper,json_object(release),json_object(bus_packet),task)
    else:
        cas_ref=file_pin(bundle.get('CAS_release'));done_ref=file_pin(bundle.get('admin_done'))
        cas=json_object(resources.read_failed_runtime_release(Path(cas_ref['path'])))
        done=json_object(resources.read_failed_runtime_release(Path(done_ref['path'])))
        for key in ('CAS_release','admin_done'):
            ref=file_pin(bundle.get(key));check_pin(Path(ref['path']),dict(ref))
        _release_stages(keeper,cas,done,_read(cas_ref['path']),
            _read(done_ref['path']),release,task,cooperative_pin_refusal=cooperative)
        values=bus_packet.get('tasks')
        if not isinstance(values,list):
            raise ValueError('Current unrun tasks must be an array')
        current=[json_object(x) for x in values if json_object(x).get('task_id')==task]
        # The canonical list command adds only age_seconds/stale to raw task files.
        # Keep every original field exact, and reject undeclared or invalid extras.
        original=object_field(done,'task');snapshot=current[0] if len(current)==1 else {}
        need(len(current)==1 and set(snapshot)==set(original)|{'age_seconds','stale'}
             and {key:snapshot[key] for key in original}==original
             and type(snapshot.get('age_seconds')) is int and _integer(snapshot.get('age_seconds'),'Closed task age')>=0
             and snapshot['stale'] is False,'Current allocated-unrun task readback differs')
    import psutil
    inventory={**json_object(process_reader(psutil,os.getpid())),'machine_id':machine,
               'observed_at_utc':datetime.now(timezone.utc).isoformat()}
    need(not inventory['blockers'],'Allocated-unrun predecessor process still running: '+repr(inventory['blockers']))
    # Registry evolution is a resource-only recovery qualification, after the
    # complete actual waits, selected product, no-Game, SCREEN and OS checks.
    if (prelaunch or capacity_wait) and 'prelaunch_orchestrator_started' in bundle:
        _recovery_input_validation(previous, json_object(freeze), Path(close_path), bundle,
            registry_support=serial or capacity_wait)
    return json_object({'mode':('previous-shared-allocated-unrun-prelaunch-orchestrator-failed' if prelaunch or capacity_wait else
        'previous-shared-allocated-unrun-launcher-pin-refused' if cooperative else 'previous-shared-allocated-unrun-idle'),'actual_process_inventory':inventory,
        'failure_cleanup':{'close':pin(close_path),'original_evidence':{**{k:v for k,v in bundle.items() if k!='counter' and isinstance(v,dict) and 'sha256' in v},**refusal_evidence},
            'absent_launch_native_control_Save':absent,'original_keeper_wait_proven':True,'original_keeper_exit_code':0,
            'host_started':False,'native_session_started':False,'original_host_exit_code':None,
            'original_ck3_exit_code':None,'typed_normal_exit_proven':False,'business_pass':False,
            **(_serial_cleanup_waits(bundle) if serial else capacity_cleanup)}})

def _write(path: str | Path, value: object) -> FilePin:
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
    return file_pin(pin(path))


def build_pre_intent_offline_ttl_bundle(args: argparse.Namespace, frozen_value: object,
        proofs_value: object, output: Path) -> UnrunBundleReport:
    """Pin the original rejected public call; never recreate a launch or wait."""
    import ck3_live_run_id as ids
    frozen, proofs = json_object(frozen_value), json_object(proofs_value)
    live, keeper = args.previous_live.resolve(), args.keeper_root.resolve()
    if not all(isinstance(getattr(args, name, None), Path) for name in (
            'allocator_result', 'pre_intent_offline_run_result', 'public_run_stdout',
            'public_run_stderr', 'root_screen_release', 'next_state')):
        raise ValueError('TTL closure requires original Root run/allocate waits, streams, release and a separate next state')
    ready = _read(live / 'ready-context.json')
    run = _read(args.pre_intent_offline_run_result)
    argv = strings_field(run, 'argv')
    if argv.count('--run-context') != 1 or argv.index('--run-context') + 1 >= len(argv):
        raise ValueError('Original public run context argument required')
    context_path = Path(argv[argv.index('--run-context') + 1])
    context = _read(context_path)
    stdout = _read(args.public_run_stdout)
    launchers = [Path(value) for value in strings_field(stdout, 'launcher_argv')
                 if Path(value).name == 'ck3_mod_acceptance_launcher.py']
    if len(launchers) != 1:
        raise ValueError('Original refused launcher path required')
    paths: dict[str, Path] = {
        'ready': live / 'ready-context.json', 'frozen': live / 'frozen-argv.json',
        'allocated_context': live / 'allocated-context.json',
        'prepared_case': Path(file_pin(ready.get('prepared_case'))['path']),
        'reviewed_context': context_path, 'run_result': args.pre_intent_offline_run_result,
        'run_stdout': args.public_run_stdout, 'run_stderr': args.public_run_stderr,
        'allocator_result': args.allocator_result, 'allocator_stdout': args.allocator_stdout,
        'offline_receipt': Path(text_field(context, 'steam_offline_receipt')),
        'launcher_source': launchers[0], 'gate_source': launchers[0].with_name('ck3_mod_acceptance_steam_gate.py'),
        'purpose': live / 'product-acceptance-purpose.json',
        'normal_exit_profile': Path(file_pin(context.get('normal_exit_managed_profile'))['path']),
        'keeper': keeper / 'report.json', 'keeper_parent_exit': live / 'keeper-actual-parent-exit.json',
        'keeper_ready': keeper / 'ready.json', 'keeper_stop': keeper / 'STOP',
        'root_release': args.root_screen_release}
    refs: JsonObject = {name: json_object(_ttl_pin(path.resolve())) for name, path in paths.items()}
    refs.update(proofs)
    canonical_counter = (ids.default_state_root() / ids.current_machine_id() / text_field(frozen, 'mod_key') / 'counter.json').resolve()
    source_counter = _ttl_pin(canonical_counter)
    counter_bytes = canonical_counter.read_bytes()
    if len(counter_bytes) != source_counter['bytes'] or hashlib.sha256(counter_bytes).hexdigest() != source_counter['sha256']:
        raise ValueError('Canonical counter changed during original snapshot acquisition')
    counter_snapshot = output / 'counter.original.json'
    with counter_snapshot.open('xb') as stream:
        stream.write(counter_bytes)
    refs['counter'] = json_object(_ttl_pin(counter_snapshot))
    bundle: JsonObject = {'schema': SCHEMA, 'closure_kind': OFFLINE_TTL_KIND,
        'machine_id': ids.current_machine_id(), 'observed_at_utc': datetime.now(timezone.utc).isoformat(),
        'run_id': text_field(frozen, 'run_id'), 'quarantined_state': text_field(frozen, 'state_dir'),
        'original_evidence': refs,
        'counter_snapshot_provenance': {'machine_id': ids.current_machine_id(),
            'observed_at_utc': datetime.now(timezone.utc).isoformat(), 'source': json_object(source_counter)},
        **{name: False for name in ('host_started', 'native_session_started', 'game_started', 'normal_close_qualified',
             'typed_normal_exit_proven', 'original_host_exit0', 'business_pass', 'release_pass')}}
    _, stop_observation = _ttl_stop(refs, keeper / 'STOP', ids.current_machine_id(),
        _timestamp(run.get('finished_at_utc'), 'Original refused run finish'),
        _timestamp(_read(keeper / 'report.json').get('at_utc'), 'Keeper completion'))
    if stop_observation is not None:
        bundle['keeper_stop_file_observation'] = json_object(stop_observation)
    evolution = _ttl_recovery_sources(frozen, output / 'ALLOCATED-UNRUN.actual.json', produce=True)
    if evolution is not None:
        bundle['recovery_reader_evolution'] = json_object(evolution)
    bundle_pin = _write(output / 'ALLOCATED-UNRUN.actual.json', bundle)
    allocator = same_directory_control_peer('ck3_mod_acceptance_allocate')
    release_pin = file_pin(proofs['admin_done'])
    release = allocator.read_failed_runtime_release(Path(release_pin['path']))
    bus = args.task_bus_root / 'bin/codex_task_bus.py'
    packet = allocator.current_screen_absent(Path(text_field(frozen, 'lease_anchor')), args.task_bus_root,
        text_field(object_field(object_field(frozen, 'files'), str(bus.resolve())), 'sha256'), None)
    verdict = validate_pre_intent_offline_ttl_refusal(live, frozen, Path(bundle_pin['path']), keeper,
        release, packet, args.next_state)
    return {'bundle': bundle_pin, 'previous_release': release_pin, 'validation': verdict, 'SDK_or_launch': False}


def _captured_release(path: Path, event: JsonObject, task: str, sequence: int) -> FilePin:
    """Keep an original task snapshot and bind its event to the actual journal."""
    value = json_object(read_json(path))
    original_event, original_task = object_field(value, 'event'), object_field(value, 'task')
    if (set(value) != {'schema', 'ok', 'event', 'task'}
            or value.get('schema') != 'codex.task_bus.v1' or value.get('ok') is not True
            or original_event != event or _sequence(original_event, 'sequence') != sequence
            or original_event.get('task_id') != task or original_event.get('resources') != []
            or original_task.get('task_id') != task or original_task.get('resources') != []
            or original_task.get('state') != event.get('state')
            or _sequence(original_task, 'last_sequence') != sequence):
        raise ValueError('Original captured release differs from its actual journal event/task')
    return file_pin(pin(path))


def _serial_required_path(args: argparse.Namespace, name: str) -> Path:
    value: object = getattr(args, name, None)
    if not isinstance(value, Path):
        raise ValueError('Original serial path argument required: '+name)
    return value.resolve()


def build_serial_prelaunch_bundle(args: argparse.Namespace) -> UnrunBundleReport:
    """The normal unrun producer, using the distinct modern original format."""
    import ck3_live_run_id as ids
    capacity_wait = getattr(args,'capacity_wait_root_wait',None) is not None
    if capacity_wait and getattr(args,'serial_prelaunch_root_wait',None) is not None:
        raise ValueError('One exact original serial receipt format required')
    live, keeper, output, root_wait, source, root_release, next_state, bus_root = (
        _serial_required_path(args, name) for name in ('previous_live', 'keeper_root', 'output',
            'capacity_wait_root_wait' if capacity_wait else 'serial_prelaunch_root_wait', 'prelaunch_orchestrator_source', 'root_screen_release',
            'next_state', 'task_bus_root'))
    root_start, root_stdout, root_stderr = (_capacity_wait_root_paths(root_wait) if capacity_wait else _serial_root_paths(root_wait))
    if output.exists():
        raise ValueError('New serial prelaunch output required')
    frozen = json_object(json.loads((live/'frozen-argv.json').read_bytes()))
    machine = ids.current_machine_id()
    task = text_field(frozen, 'screen_task')
    allocator_intent = _serial_required_path(args, 'allocator_intent')
    execution = allocator_intent.parent
    core_unarmed = (execution/'CORE-GUARD-0.intent.actual.json').exists()
    cold_unarmed = ((execution/'COLD-GUARD-0.intent.actual.json').exists()
        and not (execution/'COLD-GUARD-0.ARMED.actual.json').exists())
    if core_unarmed and cold_unarmed:
        raise ValueError('One actual before-ARMED serial guard role required')
    guard_state: PrelaunchGuardState = 'failed-before-armed' if core_unarmed or cold_unarmed else 'armed-cancelled'
    if (getattr(args, 'aborted_wrapper', None) or getattr(args, 'launcher_pin_refusal', None)
            or getattr(args, 'allocator_result', None) or getattr(args, 'allocator_external_exec', None)):
        raise ValueError('Serial known waits cannot mix unknown/legacy receipt formats')
    journal = bus_root/'events.jsonl'
    size = journal.stat().st_size
    start = max(0, size-65536)
    with journal.open('rb') as stream:
        stream.seek(start)
        raw = stream.read(65536)
    if start:
        length = raw.index(b'\n')+1
        start += length
        raw = raw[length:]
    sequences = json_object({'release':getattr(args, 'release_sequence', None),
        'done':getattr(args, 'done_sequence', None)})
    release_sequence = _sequence(sequences,'release')
    done_sequence = release_sequence if capacity_wait else _sequence(sequences,'done')
    lines = _journal_events(raw, start, release_sequence, done_sequence)
    _, _, release_event = lines[release_sequence]
    original_release = _captured_release(root_release, release_event, task, release_sequence)
    admin_original = (_serial_required_path(args, 'admin_release')
        if not capacity_wait and (guard_state == 'failed-before-armed' or getattr(args, 'admin_release', None) is not None) else None)
    output.mkdir(parents=True)
    proofs: JsonObject = {}
    release_roles = (('resource_release',release_sequence),) if capacity_wait else (('CAS_release',release_sequence),('admin_done',done_sequence))
    for key, sequence in release_roles:
        offset, line, event = lines[sequence]
        if admin_original is not None:
            original = root_release if key == 'CAS_release' else admin_original
            proofs[key] = json_object(_captured_release(original, event, task, sequence))
            continue
        task_path = bus_root/'tasks'/(task+'.json')
        task_value = json_object(json.loads(task_path.read_bytes()))
        proofs[key] = json_object(_write(output/(key+'.canonical.json'), {
            'schema':'xar-screen-release-canonical-reconstruction-v1', 'machine_id':machine,
            'source_event_stream':str(journal), 'source_event_byte_offset':offset,
            'source_event_bytes':len(line), 'source_event_raw_utf8':line.decode('utf-8'),
            'source_event_raw_sha256':hashlib.sha256(line).hexdigest(), 'event':event,
            'actual_task_pin':_ttl_pin(task_path), 'task':task_value,
            'release_confirmed_by_canonical_readback':True, 'original_stdout_captured':False}))
    paths = {'ready':live/'ready-context.json', 'frozen':live/'frozen-argv.json',
        'allocated_context':live/'allocated-context.json', 'keeper':keeper/'report.json',
        'keeper_parent_exit':live/'keeper-actual-parent-exit.json', 'keeper_STOP':keeper/'STOP',
        'keeper_ready':keeper/'ready.json', 'allocator_intent':allocator_intent,
        'allocator_process':_serial_required_path(args, 'allocator_process'),
        'allocator_exit':_serial_required_path(args, 'allocator_exit'),
        'allocator_stdout':_serial_required_path(args, 'allocator_stdout'),
        'counter':ids.default_state_root()/machine/text_field(frozen, 'mod_key')/'counter.json',
        'prelaunch_orchestrator_source':source, 'prelaunch_orchestrator_wait':root_wait,
        'prelaunch_orchestrator_started':root_start,
        'serial_root_stdout':root_stdout,
        'serial_root_stderr':root_stderr,
        'serial_static':execution/'STATIC-INPUTS-PRECOMPILED.actual.json',
        'serial_failure':execution/'ROOT-SERIAL-FAILURE.actual.json'}
    guards: list[SerialPrelaunchGuardEvidence | SerialUnarmedGuardEvidence] = []
    if admin_original is not None:
        paths['serial_admin_original'] = admin_original
    if capacity_wait:
        if any(execution.glob('*GUARD*')):
            raise ValueError('External capacity wait cannot reuse guard receipts')
        paths['capacity_wait_awaiting']=execution/'AWAITING-ROOT-PRELAUNCH-CAPACITY.actual.json'
    elif guard_state == 'failed-before-armed':
        unarmed_label: Literal['CORE-GUARD-0', 'COLD-GUARD-0'] = 'CORE-GUARD-0' if core_unarmed else 'COLD-GUARD-0'
        guards.append(SerialUnarmedGuardEvidence(label=unarmed_label,
            intent=_ttl_pin(execution/(unarmed_label+'.intent.actual.json')),
            started=_ttl_pin(execution/(unarmed_label+'.started.actual.json')),
            original_wait=_ttl_pin(execution/(unarmed_label+'.original-wait.actual.json')),
            stdout=_ttl_pin(execution/(unarmed_label+'.stdout.log')), stderr=_ttl_pin(execution/(unarmed_label+'.stderr.log'))))
    else:
        paths['serial_capacity_start'] = execution/'CAPACITY-START.actual.json'
        paths['serial_capacity_stdout'] = execution/'CAPACITY.stdout.log'
        capacity = json_object(json.loads(paths['serial_capacity_start'].read_bytes()))
        requested = Path(_serial_argument(tuple(strings_field(capacity, 'argv')), '--output'))
        paths['serial_capacity_refusal'] = requested.with_name(requested.name+'.REFUSAL.json')
        phases, _ = _serial_prepared_phases({'ready':json_object(_ttl_pin(live/'ready-context.json'))}, live, execution)
        for index in range(len(phases)):
            label = 'COLD-GUARD-'+str(index)
            guards.append(SerialPrelaunchGuardEvidence(label=label,
                intent=_ttl_pin(execution/(label+'.intent.actual.json')),
                started=_ttl_pin(execution/(label+'.started.actual.json')),
                original_wait=_ttl_pin(execution/(label+'.original-wait.actual.json')),
                armed=_ttl_pin(execution/(label+'.ARMED.actual.json')),
                stdout=_ttl_pin(execution/(label+'.stdout.log')), stderr=_ttl_pin(execution/(label+'.stderr.log'))))
    row = json_object({'schema':SCHEMA, 'closure_kind':CAPACITY_WAIT_KIND if capacity_wait else PRELAUNCH_KIND,
        'receipt_format':CAPACITY_WAIT_FORMAT if capacity_wait else SERIAL_PRELAUNCH_FORMAT,
        'machine_id':machine, 'observed_at_utc':datetime.now(timezone.utc).isoformat(),
        'run_id':text_field(frozen,'run_id'),
        **({} if capacity_wait else {'serial_guards':guards,'prelaunch_guard_state':guard_state}),
        'serial_release_original':original_release,
        **{key:False for key in ('host_started','native_session_started','game_started',
            'normal_close_qualified','original_host_exit0','business_pass')}, **proofs,
        **{key:_ttl_pin(path) for key, path in paths.items()}})
    evolution = _ttl_recovery_sources(frozen, output/'ALLOCATED-UNRUN.actual.json', produce=True,
        previous=live, registry_support=True)
    if evolution is not None:
        row['recovery_reader_evolution'] = json_object(evolution)
    bundle = _write(output/'ALLOCATED-UNRUN.actual.json', row)
    allocator = _serial_resources()
    bus = bus_root/'bin/codex_task_bus.py'
    bus_entry = object_field(object_field(frozen, 'files'), str(bus))
    packet = allocator.current_screen_absent(Path(text_field(frozen, 'lease_anchor')), bus_root,
        text_field(bus_entry, 'sha256'), None)
    admin = file_pin(proofs['resource_release' if capacity_wait else 'admin_done'])
    release = allocator.read_failed_runtime_release(Path(admin['path']))
    reducer: object = validate_allocated_unrun
    if not isinstance(reducer, _SerialUnrunReducer):
        raise ValueError('Original shared serial unrun reducer unavailable')
    verdict = json_object(reducer(live, frozen, Path(bundle['path']), keeper,
        release, packet, next_state=next_state))
    return {'bundle':bundle, 'previous_release':admin, 'validation':verdict, 'SDK_or_launch':False}


def build_bundle(args: argparse.Namespace) -> UnrunBundleReport:
    if getattr(args,'capacity_wait_root_wait',None) or getattr(args,'serial_prelaunch_root_wait',None):
        return build_serial_prelaunch_bundle(args)
    if getattr(args,'aborted_wrapper',None):
        return build_aborted_bundle_v1(args)
    import ck3_live_run_id as ids
    control_allocator = same_directory_control_peer('ck3_mod_acceptance_allocate')
    read_failed_runtime_release, current_screen_absent = control_allocator.read_failed_runtime_release, control_allocator.current_screen_absent
    allocator={key:getattr(args,key,None) for key in ('allocator_result','allocator_external_exec','allocator_intent','allocator_process','allocator_exit')}
    singles=('allocator_result','allocator_external_exec');triplet=('allocator_intent','allocator_process','allocator_exit')
    need(any(allocator[key] is not None and all(allocator[other] is None for other in allocator if other!=key) for key in singles)
         or (all(allocator[key] is None for key in singles) and all(allocator[key] is not None for key in triplet)),
         'Provide --allocator-result, --allocator-external-exec, or all three original Popen evidence files')
    live=args.previous_live.resolve();keeper=args.keeper_root.resolve();freeze=_read(live/'frozen-argv.json')
    screen_task = text_field(freeze, 'screen_task')
    machine=ids.current_machine_id();taskpath=args.task_bus_root/'tasks'/(screen_task+'.json');task=_read(taskpath)
    journal=args.task_bus_root/'events.jsonl';size=journal.stat().st_size;start=max(0,size-65536)
    with journal.open('rb') as f:f.seek(start);raw=f.read(65536)
    if start:
        first=raw.index(b'\n')+1;start+=first;raw=raw[first:]
    lines=_journal_events(raw,start,args.release_sequence,args.done_sequence)
    output=args.output.resolve();need(not output.exists(),'New C metadata output required');output.mkdir(parents=True)
    proofs={}
    captured = ((getattr(args, 'root_screen_release', None), getattr(args, 'admin_release', None))
                if getattr(args, 'prelaunch_orchestrator_source', None) else (None, None))
    if any(path is not None for path in captured):
        need(all(isinstance(path, Path) for path in captured) and getattr(args, 'prelaunch_orchestrator_source', None),
             'Captured prelaunch release requires both original CAS and administrative stdout')
    for label,sequence in (('CAS_release',args.release_sequence),('admin_done',args.done_sequence)):
        offset,line,event=lines[sequence]
        original = captured[0 if label == 'CAS_release' else 1]
        if isinstance(original, Path):
            proofs[label] = _captured_release(original, json_object(event), screen_task, sequence)
            continue
        proofs[label]=_write(output/(label+'.canonical.json'),{'schema':'xar-screen-release-canonical-reconstruction-v1',
            'machine_id':machine,'source_event_stream':str(journal.resolve()),'source_event_byte_offset':offset,
            'source_event_bytes':len(line),'source_event_raw_utf8':line.decode(),'source_event_raw_sha256':hashlib.sha256(line).hexdigest(),
            'event':event,'actual_task_pin':pin(taskpath),'task':task,'release_confirmed_by_canonical_readback':True,'original_stdout_captured':False})
    if getattr(args, 'pre_intent_offline_run_result', None):
        return build_pre_intent_offline_ttl_bundle(args, freeze, proofs, output)
    row=json_object({'schema':SCHEMA,'machine_id':machine,'observed_at_utc':datetime.now(timezone.utc).isoformat(),'run_id':freeze['run_id'],
         **{k:False for k in ('host_started','native_session_started','game_started','normal_close_qualified','original_host_exit0','business_pass')},**proofs})
    paths={'ready':live/'ready-context.json','frozen':live/'frozen-argv.json','allocated_context':live/'allocated-context.json',
        'keeper':keeper/'report.json','keeper_parent_exit':live/'keeper-actual-parent-exit.json','keeper_STOP':keeper/'STOP',
        'keeper_ready':keeper/'ready.json','idle_timeout':live/'allocation-unused-idle-timeout.json',
        **{k:v for k,v in allocator.items() if v is not None},'allocator_stdout':args.allocator_stdout,
        'counter':ids.default_state_root()/machine/text_field(freeze, 'mod_key')/'counter.json'}
    if getattr(args, 'allocator_command', None) is not None:
        paths['allocator_command'] = args.allocator_command
    if getattr(args,'launcher_pin_refusal',None):
        row['closure_kind']='launcher-pin-admission-refused-before-launch-intent'
        paths.pop('idle_timeout')
        paths['launcher_pin_refusal']=args.launcher_pin_refusal
        need(getattr(args,'allocator_command',None),'Cooperative original wrapper allocator command required')
        paths['allocator_command']=args.allocator_command
    if getattr(args,'prelaunch_orchestrator_source',None):
        need(not getattr(args,'launcher_pin_refusal',None) and getattr(args,'allocator_command',None)
             and args.allocator_intent and args.allocator_process and args.allocator_exit,
             'Prelaunch closure requires the original Root triplet and recorder only')
        row['closure_kind']=PRELAUNCH_KIND
        paths.pop('idle_timeout')
        paths['prelaunch_orchestrator_source']=args.prelaunch_orchestrator_source
        root_started = getattr(args, 'prelaunch_orchestrator_started', None)
        root_wait = getattr(args, 'prelaunch_orchestrator_wait', None)
        root_intent = getattr(args, 'prelaunch_orchestrator_intent', None)
        need((root_started is None) == (root_wait is None),
             'Provide both original Root orchestrator start and wait')
        if root_started is not None:
            paths['prelaunch_orchestrator_started'] = root_started
            paths['prelaunch_orchestrator_wait'] = root_wait
        if root_intent is not None:
            need(root_started is not None, 'Original Root intent requires both original start and wait')
            paths['prelaunch_orchestrator_intent'] = root_intent
        original_output=args.allocator_intent.resolve().parent
        guard_state: PrelaunchGuardState = ('failed-before-armed' if root_intent is not None
            and not (original_output/'DEADLINE-GUARD.ARMED.actual.json').exists() else 'armed-cancelled')
        row['prelaunch_guard_state'] = guard_state
        paths.update({key:original_output/name for key,name in {
            'prelaunch_failure':'ORCHESTRATOR.failure.actual.json',
            'prelaunch_guard_started':'DEADLINE-GUARD.started.actual.json',
            'prelaunch_guard_wait':'DEADLINE-GUARD.original-wait.actual.json',
            'prelaunch_allocator_wait':'ORCHESTRATOR.ALLOCATE.original-wait.actual.json'}.items()})
        guard_paths = ({'prelaunch_guard_intent':'DEADLINE-GUARD.intent.actual.json',
            'prelaunch_guard_stdout':'DEADLINE-GUARD.stdout.log',
            'prelaunch_guard_stderr':'DEADLINE-GUARD.stderr.log'} if guard_state == 'failed-before-armed' else
            {'prelaunch_guard_armed':'DEADLINE-GUARD.ARMED.actual.json',
             'prelaunch_guard_cancel':'DEADLINE-GUARD.CANCEL.actual.json'})
        paths.update({key:original_output/name for key,name in guard_paths.items()})
    row.update(json_object({k:pin(v) for k,v in paths.items()}))
    if 'prelaunch_orchestrator_started' in row:
        phase_guards = ([] if _prelaunch_guard_state(row) == 'failed-before-armed' else
            _phase_guard_evidence(args.allocator_intent.resolve().parent))
        if phase_guards:
            row.update(json_object({'prelaunch_phase_guards': phase_guards}))
        evolution = _ttl_recovery_sources(json_object(freeze), output/'ALLOCATED-UNRUN.actual.json', produce=True)
        if evolution is not None:
            row['recovery_reader_evolution'] = json_object(evolution)
    bundle=_write(output/'ALLOCATED-UNRUN.actual.json',row)
    release=read_failed_runtime_release(Path(proofs['admin_done']['path']))
    bus=args.task_bus_root/'bin/codex_task_bus.py'
    bus_entry = object_field(object_field(freeze, 'files'), str(bus.resolve()))
    if set(bus_entry) != {'bytes', 'sha256'}:
        raise ValueError('Exact frozen path-keyed file entry required')
    bus_pin = file_pin({'path': str(bus.resolve()), 'bytes': bus_entry['bytes'],
        'sha256': bus_entry['sha256']})
    packet=current_screen_absent(Path(text_field(freeze, 'lease_anchor')),args.task_bus_root,
        bus_pin['sha256'],None)
    reducer: object = validate_allocated_unrun
    if not callable(reducer):
        raise ValueError('Existing allocated-unrun reducer unavailable')
    verdict=json_object(reducer(live,freeze,Path(bundle['path']),keeper,release,packet))
    return {'bundle':file_pin(bundle),'previous_release':file_pin(proofs['admin_done']),
            'validation':json_object(verdict),'SDK_or_launch':False}
def build_aborted_bundle_v1(args: argparse.Namespace) -> UnrunBundleReport:
    """Produce the missing-wait branch from actual original files, never a wait receipt."""
    import ck3_live_run_id as ids
    allocator = same_directory_control_peer('ck3_mod_acceptance_allocate')
    if (not args.allocator_intent or not args.allocator_process or args.allocator_exit
            or args.allocator_result or args.allocator_external_exec
            or not args.aborted_release or not args.admin_release or not args.next_state):
        raise ValueError('Exact original aborted intent/process/releases and new state required')
    live, keeper = args.previous_live.resolve(), args.keeper_root.resolve()
    frozen = json_object(_read(live/'frozen-argv.json'))
    ready = json_object(_read(live/'ready-context.json'))
    prepared = _evidence_pin(ready.get('prepared_case'),'prepared')
    closed_keeper = getattr(args, 'aborted_keeper_closed', False)
    if type(closed_keeper) is not bool:
        raise ValueError('Explicit closed-keeper recovery selector must be boolean')
    paths = {'ready':live/'ready-context.json','frozen':live/'frozen-argv.json',
        'allocated_context':live/'allocated-context.json','prepared_case':Path(prepared['path']),
        'keeper_process':live/'keeper-process.json','keeper_inputs':keeper/'inputs.json',
        'keeper_ready':keeper/'ready.json','allocator_intent':args.allocator_intent,
        'allocator_process':args.allocator_process,'allocator_stdout':args.allocator_stdout,
        'allocator_aborted_wrapper':args.aborted_wrapper,'CAS_release':args.aborted_release,
        'admin_done':args.admin_release,'counter':ids.default_state_root()/ids.current_machine_id()/str(frozen['mod_key'])/'counter.json'}
    if closed_keeper:
        paths.update({'keeper':keeper/'report.json', 'keeper_parent_exit':live/'keeper-actual-parent-exit.json',
            'keeper_STOP':keeper/'STOP', 'idle_timeout':live/'allocation-unused-idle-timeout.json'})
    row = {'schema':SCHEMA,'closure_kind':CLOSED_KEEPER_ABORTED_KIND if closed_keeper else ABORTED_KIND,
        'machine_id':ids.current_machine_id(),
        'observed_at_utc':datetime.now(timezone.utc).isoformat(),'run_id':frozen['run_id'],
        'quarantined_state':frozen['state_dir'],'allocator_exit_code':None,
        'keeper_exit_code':0 if closed_keeper else None, 'keeper_original_wait_observed':closed_keeper,
        **{k:False for k in ('host_started','native_session_started','game_started','normal_close_qualified',
            'original_host_exit0','business_pass','allocator_original_wait_observed')},
        **{key:pin(path) for key,path in paths.items()}}
    output = args.output.resolve()
    if output.exists():raise ValueError('New aborted allocation output required')
    output.mkdir(parents=True)
    bundle = _write(output/'ALLOCATED-UNRUN.actual.json',row)
    bus = args.task_bus_root/'bin/codex_task_bus.py'
    files = json_object(frozen['files'])
    packet = allocator.current_screen_absent(Path(str(frozen['lease_anchor'])),args.task_bus_root,
        json_object(files[str(bus.resolve())])['sha256'],None)
    release = allocator.read_failed_runtime_release(args.admin_release)
    verdict = json_object(validate_allocated_unrun(live,frozen,Path(bundle['path']),keeper,release,packet,
        next_state=args.next_state))
    return {'bundle':file_pin(bundle),'previous_release':file_pin(pin(args.admin_release)),
        'validation':verdict,'SDK_or_launch':False}


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--previous-live',type=Path,required=True)
    p.add_argument('--keeper-root',type=Path,required=True)
    allocator=p.add_mutually_exclusive_group(required=True)
    allocator.add_argument('--allocator-result',type=Path)
    allocator.add_argument('--allocator-external-exec',type=Path)
    p.add_argument('--allocator-command',type=Path)
    p.add_argument('--aborted-wrapper',type=Path)
    p.add_argument('--aborted-keeper-closed',action='store_true',
        help='Keep outer allocator wait unknown while validating its actual idle keeper wait0')
    p.add_argument('--aborted-release',type=Path)
    p.add_argument('--admin-release',type=Path)
    p.add_argument('--next-state',type=Path)
    p.add_argument('--launcher-pin-refusal',type=Path)
    p.add_argument('--prelaunch-orchestrator-source',type=Path)
    p.add_argument('--prelaunch-orchestrator-intent',type=Path)
    p.add_argument('--prelaunch-orchestrator-started',type=Path)
    p.add_argument('--prelaunch-orchestrator-wait',type=Path)
    roots=p.add_mutually_exclusive_group()
    roots.add_argument('--serial-prelaunch-root-wait',type=Path,
        help='Known original serial root1/allocator0/guards1/keeper0 before any public run; no idle claim')
    roots.add_argument('--capacity-wait-root-wait',type=Path,
        help='Original Root capacity180s timeout/allocator0/keeper0, no guard or Game, expired waiting release')
    p.add_argument('--pre-intent-offline-run-result',type=Path)
    p.add_argument('--public-run-stdout',type=Path)
    p.add_argument('--public-run-stderr',type=Path)
    p.add_argument('--root-screen-release',type=Path)
    allocator.add_argument('--allocator-intent',type=Path)
    p.add_argument('--allocator-process',type=Path);p.add_argument('--allocator-exit',type=Path)
    p.add_argument('--allocator-stdout',type=Path,required=True);p.add_argument('--task-bus-root',type=Path,required=True)
    p.add_argument('--release-sequence',type=int,required=True);p.add_argument('--done-sequence',type=int)
    p.add_argument('--output',type=Path,required=True)
    print(json.dumps(build_bundle(p.parse_args()),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
