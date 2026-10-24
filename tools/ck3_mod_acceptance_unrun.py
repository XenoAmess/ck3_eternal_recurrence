"""Close an actual idle, allocated-only public run without host/OS exit credit.

The CLI writes bounded metadata only. Public allocate remains the only allocator.
"""
from __future__ import annotations
from pathlib import Path, PureWindowsPath
from datetime import datetime, timezone
from dataclasses import dataclass
from collections.abc import Mapping
from typing import Literal, TypedDict
import argparse, hashlib, importlib, json, math, os, re, sys
from ck3_mod_acceptance import check_pin, pin, read_json, same_directory_control_peer
from ck3_mod_acceptance_launcher_pin_refusal import public_operation_argv, validate_launcher_pin_refusal
from ck3_mod_acceptance_background_types import FilePin, JsonObject, file_pin, json_object, object_field

SCHEMA = 'ck3-mod-acceptance-allocated-unrun-closure-v1'
ABORTED_KIND = 'wrapper-aborted-before-launch-without-terminal-waits'


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


class AbortedAllocationClosureV1(TypedDict):
    schema: Literal['ck3-mod-acceptance-allocated-unrun-closure-v1']
    closure_kind: Literal['wrapper-aborted-before-launch-without-terminal-waits']
    machine_id: str
    observed_at_utc: str
    run_id: str
    quarantined_state: str
    allocator_exit_code: None
    keeper_exit_code: None
    host_started: Literal[False]
    native_session_started: Literal[False]
    game_started: Literal[False]
    normal_close_qualified: Literal[False]
    original_host_exit0: Literal[False]
    business_pass: Literal[False]
    allocator_original_wait_observed: Literal[False]
    keeper_original_wait_observed: Literal[False]
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
def _exact(bundle, key, path):
    ref=bundle[key];need(Path(ref['path']).resolve()==Path(path).resolve(),'Unrun original path differs: '+key)
    check_pin(Path(path),ref);return _read(path)

def _allocator_argv(bundle: Mapping[str, object], machine: str, keeper_stamps: list[datetime]) -> list[str]:
    """Read one original allocator completion evidence form.

    The triplet credits its actual Popen wait. The external form preserves the
    actual cmd.exe tool session and exact final output block without inventing
    a Popen wait or a complete process stdout stream. No form credits host/CK3.
    """
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

def _journal_events(raw,start,release_sequence,done_sequence):
    requested={release_sequence,done_sequence};lines={};offset=start
    for line in raw.splitlines(keepends=True):
        row=json.loads(line)
        if row.get('sequence') in requested:
            need(row['sequence'] not in lines,'Duplicate original CAS/DONE sequence in bounded journal tail')
            lines[row['sequence']]=(offset,line,row)
        offset+=len(line)
    need(len(lines)==len(requested),'Exact original CAS/DONE events absent from bounded journal tail')
    return lines

def validate_aborted_allocation_v1(previous: Path, freeze_value: object, close_path: Path,
        keeper_root: Path, release_value: object, bus_value: object, next_state: Path) -> JsonObject:
    """Administrative admission only; lost original waits remain unknown."""
    import psutil
    import ck3_live_run_id as ids
    allocator = same_directory_control_peer('ck3_mod_acceptance_allocate')
    freeze = json_object(freeze_value)
    bundle = json_object(_read(close_path))
    machine, run, task = ids.current_machine_id(), _text(freeze['run_id'],'run'), _text(freeze['screen_task'],'task')
    if (set(bundle) != set(AbortedAllocationClosureV1.__required_keys__)
            or bundle.get('schema') != SCHEMA or bundle.get('closure_kind') != ABORTED_KIND
            or bundle.get('machine_id') != machine or bundle.get('run_id') != run
            or any(bundle.get(k) is not False for k in ('host_started','native_session_started',
                'game_started','normal_close_qualified','original_host_exit0','business_pass',
                'allocator_original_wait_observed','keeper_original_wait_observed'))
            or 'allocator_exit_code' not in bundle or bundle['allocator_exit_code'] is not None
            or 'keeper_exit_code' not in bundle or bundle['keeper_exit_code'] is not None):
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
            or process.get('argv') != argv or intent.get('machine_id') != machine
            or process.get('machine_id') != machine or intent.get('stage') != 'allocate'):
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
            or 'session_id' not in tool or tool['session_id'] is not None
            or not isinstance(tool.get('chunk_id'),str) or not tool['chunk_id']
            or Path(argument('--prepared-case')).resolve() != Path(prepared_ref['path']).resolve()
            or Path(argument('--keeper-output')).resolve() != keeper_root.resolve()
            or argv.count('allocate') != 1):
        raise ValueError('Original pre-game wrapper failure/unknown wait differs')
    stamps = [_timestamp(intent.get('at_utc'),'allocator intent'),
              _timestamp(keeper_ready.get('at_utc'),'keeper ready'),
              _timestamp(wrapper.get('observed_at_utc'),'wrapper failure'),
              _timestamp(bundle.get('observed_at_utc'),'closure observation')]
    if stamps != sorted(stamps) or stamps[-1] > datetime.now(timezone.utc):
        raise ValueError('Aborted original timestamps differ')
    stdout_ref = _evidence_pin(bundle.get('allocator_stdout'),'allocator stdout')
    check_pin(Path(stdout_ref['path']),dict(stdout_ref))
    allocated = json_object(json.loads(Path(stdout_ref['path']).read_text(encoding='utf-8-sig')))
    if (allocated.get('status') != 'ACTUAL_ALLOCATED_KEEPER_READY_NOT_RUN'
            or allocated.get('task') != task or _integer(allocated.get('keeper_pid'),'READY keeper PID',1) != keeper_pid
            or Path(str(allocated.get('live'))).resolve() != previous.resolve()
            or Path(str(allocated.get('context'))).resolve() != (previous/'ready-context.json').resolve()):
        raise ValueError('Actual aborted allocator READY stdout differs')
    absent = {name:not (previous/name).exists() for name in ('launch-intent.json','launch.json',
        'host-started.json','host-supervisor.json','host-supervisor-started.json','supervisor.json',
        'host-original-process-exit.json','native-report.json','native-report.session.log','case-output',
        'keeper-actual-parent-exit.json')}
    absent.update({'keeper/report':not (keeper_root/'report.json').exists(),
        'state/control':not (state/'control').exists(), 'state/native-session':not (state/'native-session').exists(),
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
    retirement = json_object(event.get('retirement'))
    if (done != release or actual.get('ok') is not True or done.get('ok') is not True
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
    return json_object({'mode':'previous-shared-allocated-aborted-wrapper-resource-only',
        'actual_process_inventory':inventory,'failure_cleanup':{'close':pin(close_path),'original_evidence':evidence,
            'absent_launch_native_control_Save':absent,'quarantined_state':str(state),
            'original_allocator_wait_proven':False,'original_allocator_exit_code':None,
            'original_keeper_wait_proven':False,'original_keeper_exit_code':None,
            'original_host_exit_code':None,'original_ck3_exit_code':None,
            'normal_close_qualified':False,'typed_normal_exit_proven':False,'business_pass':False,'release_pass':False,
            'native_cleanup_qualified':None,
            'administrative_resource_admission_only':True}})


def validate_allocated_unrun(previous, freeze, close_path, keeper_root, release, bus_packet, *, next_state=None):
    if _read(close_path).get('closure_kind') == ABORTED_KIND:
        if not isinstance(next_state,Path):raise ValueError('Aborted allocation requires a new separate state')
        return validate_aborted_allocation_v1(Path(previous),freeze,Path(close_path),Path(keeper_root),release,bus_packet,next_state)
    control_allocator = same_directory_control_peer('ck3_mod_acceptance_allocate')
    read_failed_runtime_release, runtime_process_inventory = control_allocator.read_failed_runtime_release, control_allocator.runtime_process_inventory
    import ck3_live_run_id as ids
    previous,keeper_root=Path(previous).resolve(),Path(keeper_root).resolve()
    bundle=_read(close_path);machine=ids.current_machine_id();run=freeze['run_id'];task=freeze['screen_task']
    need(bundle.get('schema')==SCHEMA and bundle.get('run_id')==run and bundle.get('machine_id')==machine
         ==freeze.get('identity_allocation',{}).get('machine_id'),'Unrun full run/machine identity differs')
    need(all(bundle.get(k) is False for k in ('host_started','native_session_started','game_started',
         'normal_close_qualified','original_host_exit0','business_pass')),'Allocated-only closure cannot grant game/host credit')
    ready=_exact(bundle,'ready',previous/'ready-context.json')
    _exact(bundle,'frozen',previous/'frozen-argv.json')
    context=_exact(bundle,'allocated_context',previous/'allocated-context.json')
    need(ready['run_id']==context['run_id']==run and Path(ready['run_dir']).resolve()==previous
         and Path(ready['keeper_root']).resolve()==keeper_root and ready['frozen_argv']==bundle['frozen']
         and ready['prepared_case']==context['prepared_case'],'Original allocated-only READY differs')
    check_pin(Path(ready['prepared_case']['path']),ready['prepared_case'])
    keeper=_exact(bundle,'keeper',keeper_root/'report.json')
    parent=_exact(bundle,'keeper_parent_exit',previous/'keeper-actual-parent-exit.json')
    need(keeper.get('task_id')==task and keeper.get('thread_exited') is True and keeper.get('failure') is None
         and keeper.get('entry_error') is None and keeper.get('game_actions') is False
         and parent.get('run_id')==run and parent.get('keeper_actual_exit_code')==0
         and parent.get('keeper_report')==keeper,'Original idle keeper STOP/wait0 unavailable')
    cooperative=bundle.get('closure_kind')=='launcher-pin-admission-refused-before-launch-intent'
    need(bundle.get('closure_kind') is None or cooperative,'Unknown allocated-unrun closure kind')
    refusal_evidence={}
    if cooperative:
        refusal_evidence=validate_launcher_pin_refusal(bundle['launcher_pin_refusal'],frozen=freeze,
            live=previous,keeper=keeper_root,machine_id=machine)
        need(bundle['keeper_STOP']==refusal_evidence['keeper_stop'],'Cooperative STOP references differ')
    else:
        idle=_exact(bundle,'idle_timeout',previous/'allocation-unused-idle-timeout.json')
        stop=bundle['keeper_STOP'];need(Path(stop['path']).resolve()==keeper_root/'STOP','Original STOP crossed keeper')
        check_pin(keeper_root/'STOP',stop)
        need((keeper_root/'STOP').read_text(encoding='utf-8')=='Unused allocation idle deadline; no game/native/normal credit.\n'
             and idle.get('reason')=='NEVER_LAUNCHED_ALLOCATION_IDLE_TIMEOUT' and idle.get('idle_seconds')==600
             and all(idle.get(k) is False for k in ('game_started','native_session_started','normal_close_qualified','business_pass')),
             'Original unused idle STOP differs')
    keeper_ready=_exact(bundle,'keeper_ready',keeper_root/'ready.json')
    stamps=[datetime.fromisoformat(v) for v in ((keeper_ready['at_utc'],keeper['at_utc']) if cooperative else
        (keeper_ready['at_utc'],idle['utc'],keeper['at_utc']))]
    need(all(x.tzinfo is not None for x in stamps) and stamps==sorted(stamps)
         and (cooperative or (stamps[1]-stamps[0]).total_seconds()>=600),'Original unused interval unproven')
    argv=_allocator_argv(bundle,machine,stamps)
    def argument(name):
        need(argv.count(name)==1 and argv.index(name)+1<len(argv),'Original allocator argument missing: '+name)
        return argv[argv.index(name)+1]
    need(Path(argument('--prepared-case')).resolve()==Path(ready['prepared_case']['path']).resolve()
         and Path(argument('--keeper-output')).resolve()==keeper_root,'Actual original allocator wait0 differs')
    stdout=bundle['allocator_stdout'];check_pin(Path(stdout['path']),stdout)
    allocated,end=json.JSONDecoder().raw_decode(Path(stdout['path']).read_text(encoding='utf-8-sig').lstrip())
    need(allocated.get('status')=='ACTUAL_ALLOCATED_KEEPER_READY_NOT_RUN' and allocated.get('task')==task
         and Path(allocated['live']).resolve()==previous and Path(allocated['keeper_root']).resolve()==keeper_root,
         'Actual original allocator READY output differs')
    state=Path(freeze['state_dir']).resolve()
    absent={name:not (previous/name).exists() for name in ('launch-intent.json','launch.json','host-started.json',
        'host-supervisor.json','host-supervisor-started.json','supervisor.json','host-original-process-exit.json',
        'native-report.json','native-report.session.log','case-output')}
    absent['state/control']=not (state/'control').exists()
    absent['state/native-session']=not (state/'native-session').exists()
    absent['controls-empty']=(previous/'controls').is_dir() and not any((previous/'controls').iterdir())
    for name in ('save games','logs','run'):
        path=state/'profile'/name;absent['profile/'+name]=not path.exists() or not any(path.iterdir())
    need(all(absent.values()),'Allocated-unrun predecessor has actual host/native/control/Save evidence')
    identity=freeze['identity_allocation'];root=ids.default_state_root().resolve()
    need(Path(identity['state_root']).resolve()==root,'Actual machine counter namespace differs')
    products=Path(argument('--products')).resolve();product_key=argument('--product')
    need(str(products) in freeze['files'],'Original allocated product registry pin missing')
    check_pin(products,freeze['files'][str(products)])
    product=_read(products)['products'][product_key];external_mod=product.get('external_mod',False)
    need(type(external_mod) is bool and product_key==ready['product']
         and (product.get('runtime_mod_key') or product_key)==freeze['mod_key'],
         'Original allocated product namespace differs')
    counter=root/machine/freeze['mod_key']/'counter.json';row=_exact(bundle,'counter',counter)
    need(row.get('machine_id')==machine and row.get('mod_key')==freeze['mod_key']
         and ids.format_run_id(machine,freeze['mod_key'],row['last_sequence'],external_mod=external_mod)==run,
         'Allocated-unrun run is not the latest actual machine/product counter')
    cas=read_failed_runtime_release(Path(bundle['CAS_release']['path']))
    done=read_failed_runtime_release(Path(bundle['admin_done']['path']))
    for key in ('CAS_release','admin_done'):
        check_pin(Path(bundle[key]['path']),bundle[key])
    _release_stages(keeper,cas,done,_read(bundle['CAS_release']['path']),
        _read(bundle['admin_done']['path']),release,task,cooperative_pin_refusal=cooperative)
    current=[x for x in bus_packet.get('tasks',[]) if x.get('task_id')==task]
    # The canonical list command adds only age_seconds/stale to raw task files.
    # Keep every original field exact, and reject undeclared or invalid extras.
    original=done['task'];snapshot=current[0] if len(current)==1 else {}
    need(len(current)==1 and set(snapshot)==set(original)|{'age_seconds','stale'}
         and {key:snapshot[key] for key in original}==original
         and type(snapshot['age_seconds']) is int and snapshot['age_seconds']>=0
         and snapshot['stale'] is False,'Current allocated-unrun task readback differs')
    import psutil
    inventory={**runtime_process_inventory(psutil,os.getpid()),'machine_id':machine,
               'observed_at_utc':datetime.now(timezone.utc).isoformat()}
    need(not inventory['blockers'],'Allocated-unrun predecessor process still running: '+repr(inventory['blockers']))
    return {'mode':'previous-shared-allocated-unrun-launcher-pin-refused' if cooperative else 'previous-shared-allocated-unrun-idle','actual_process_inventory':inventory,
        'failure_cleanup':{'close':pin(close_path),'original_evidence':{**{k:v for k,v in bundle.items() if k!='counter' and isinstance(v,dict) and 'sha256' in v},**refusal_evidence},
            'absent_launch_native_control_Save':absent,'original_keeper_wait_proven':True,'original_keeper_exit_code':0,
            'host_started':False,'native_session_started':False,'original_host_exit_code':None,
            'original_ck3_exit_code':None,'typed_normal_exit_proven':False,'business_pass':False}}

def _write(path: str | Path, value: object) -> FilePin:
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
    return file_pin(pin(path))
def build_bundle(args: argparse.Namespace) -> UnrunBundleReport:
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
    machine=ids.current_machine_id();taskpath=args.task_bus_root/'tasks'/(freeze['screen_task']+'.json');task=_read(taskpath)
    journal=args.task_bus_root/'events.jsonl';size=journal.stat().st_size;start=max(0,size-65536)
    with journal.open('rb') as f:f.seek(start);raw=f.read(65536)
    if start:
        first=raw.index(b'\n')+1;start+=first;raw=raw[first:]
    lines=_journal_events(raw,start,args.release_sequence,args.done_sequence)
    output=args.output.resolve();need(not output.exists(),'New C metadata output required');output.mkdir(parents=True)
    proofs={}
    for label,sequence in (('CAS_release',args.release_sequence),('admin_done',args.done_sequence)):
        offset,line,event=lines[sequence]
        proofs[label]=_write(output/(label+'.canonical.json'),{'schema':'xar-screen-release-canonical-reconstruction-v1',
            'machine_id':machine,'source_event_stream':str(journal.resolve()),'source_event_byte_offset':offset,
            'source_event_bytes':len(line),'source_event_raw_utf8':line.decode(),'source_event_raw_sha256':hashlib.sha256(line).hexdigest(),
            'event':event,'actual_task_pin':pin(taskpath),'task':task,'release_confirmed_by_canonical_readback':True,'original_stdout_captured':False})
    row={'schema':SCHEMA,'machine_id':machine,'observed_at_utc':datetime.now(timezone.utc).isoformat(),'run_id':freeze['run_id'],
         **{k:False for k in ('host_started','native_session_started','game_started','normal_close_qualified','original_host_exit0','business_pass')},**proofs}
    paths={'ready':live/'ready-context.json','frozen':live/'frozen-argv.json','allocated_context':live/'allocated-context.json',
        'keeper':keeper/'report.json','keeper_parent_exit':live/'keeper-actual-parent-exit.json','keeper_STOP':keeper/'STOP',
        'keeper_ready':keeper/'ready.json','idle_timeout':live/'allocation-unused-idle-timeout.json',
        **{k:v for k,v in allocator.items() if v is not None},'allocator_stdout':args.allocator_stdout,
        'counter':ids.default_state_root()/machine/freeze['mod_key']/'counter.json'}
    if getattr(args,'launcher_pin_refusal',None):
        row['closure_kind']='launcher-pin-admission-refused-before-launch-intent'
        paths.pop('idle_timeout')
        paths['launcher_pin_refusal']=args.launcher_pin_refusal
        need(getattr(args,'allocator_command',None),'Cooperative original wrapper allocator command required')
        paths['allocator_command']=args.allocator_command
    row.update({k:pin(v) for k,v in paths.items()});bundle=_write(output/'ALLOCATED-UNRUN.actual.json',row)
    release=read_failed_runtime_release(Path(proofs['admin_done']['path']))
    bus=args.task_bus_root/'bin/codex_task_bus.py'
    packet=current_screen_absent(Path(freeze['lease_anchor']),args.task_bus_root,
        freeze['files'][str(bus.resolve())]['sha256'],None)
    verdict=validate_allocated_unrun(live,freeze,Path(bundle['path']),keeper,release,packet)
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
    paths = {'ready':live/'ready-context.json','frozen':live/'frozen-argv.json',
        'allocated_context':live/'allocated-context.json','prepared_case':Path(prepared['path']),
        'keeper_process':live/'keeper-process.json','keeper_inputs':keeper/'inputs.json',
        'keeper_ready':keeper/'ready.json','allocator_intent':args.allocator_intent,
        'allocator_process':args.allocator_process,'allocator_stdout':args.allocator_stdout,
        'allocator_aborted_wrapper':args.aborted_wrapper,'CAS_release':args.aborted_release,
        'admin_done':args.admin_release,'counter':ids.default_state_root()/ids.current_machine_id()/str(frozen['mod_key'])/'counter.json'}
    row = {'schema':SCHEMA,'closure_kind':ABORTED_KIND,'machine_id':ids.current_machine_id(),
        'observed_at_utc':datetime.now(timezone.utc).isoformat(),'run_id':frozen['run_id'],
        'quarantined_state':frozen['state_dir'],'allocator_exit_code':None,'keeper_exit_code':None,
        **{k:False for k in ('host_started','native_session_started','game_started','normal_close_qualified',
            'original_host_exit0','business_pass','allocator_original_wait_observed','keeper_original_wait_observed')},
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
    verdict = validate_aborted_allocation_v1(live,frozen,Path(bundle['path']),keeper,release,packet,args.next_state)
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
    p.add_argument('--aborted-release',type=Path)
    p.add_argument('--admin-release',type=Path)
    p.add_argument('--next-state',type=Path)
    p.add_argument('--launcher-pin-refusal',type=Path)
    allocator.add_argument('--allocator-intent',type=Path)
    p.add_argument('--allocator-process',type=Path);p.add_argument('--allocator-exit',type=Path)
    p.add_argument('--allocator-stdout',type=Path,required=True);p.add_argument('--task-bus-root',type=Path,required=True)
    p.add_argument('--release-sequence',type=int,required=True);p.add_argument('--done-sequence',type=int,required=True)
    p.add_argument('--output',type=Path,required=True)
    print(json.dumps(build_bundle(p.parse_args()),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
