"""Typed original-tool evidence for an unconsumed launcher pin refusal."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Literal, TypedDict

from ck3_mod_acceptance_background_types import FilePin, JsonObject, file_pin, json_object, object_field, strings_field, text_field

PIN_ERROR = "ValueError('Fresh-machine helper absent from actual allocation pins')"
COOPERATIVE_STOP = 'Root cooperative STOP after launcher pin admission refused; no game/native/normal credit.\n'


class PublicOperationCommand(TypedDict):
    machine_id: str
    observed_at_utc: str
    argv: list[str]


class PublicOperationCompletion(TypedDict):
    machine_id: str
    observed_at_utc: str
    exit_code: int
    command: str
    original_subprocess_wait_observed: Literal[True]


class LauncherPinRefusal(TypedDict):
    schema: Literal['ck3-mod-acceptance-launcher-pin-refusal-v1']
    machine_id: str
    observed_at_utc: str
    run_command: FilePin
    run_completion: FilePin
    run_stdout: FilePin
    run_stderr: FilePin
    keeper_stop: FilePin


def exact_original(value: object) -> FilePin:
    ref = file_pin(value)
    path = Path(ref['path'])
    if not path.is_absolute() or not 0 < ref['bytes'] <= 1048576 or path.stat().st_size != ref['bytes']:
        raise ValueError('Bounded exact launcher-refusal original required')
    if hashlib.sha256(path.read_bytes()).hexdigest() != ref['sha256']:
        raise ValueError('Launcher-refusal original changed')
    return ref


def read_original(value: object) -> JsonObject:
    ref = exact_original(value)
    return json_object(json.loads(Path(ref['path']).read_text(encoding='utf-8-sig')))


def utc_stamp(value: str) -> datetime:
    stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if stamp.tzinfo is None or stamp.utcoffset() != timezone.utc.utcoffset(stamp):
        raise ValueError('Original UTC observation required')
    return stamp


def public_operation_argv(command: object, completion: object, *, machine_id: str,
                          mode: Literal['allocate', 'run'], exit_code: int) -> tuple[list[str], datetime]:
    command_ref = exact_original(command)
    intent, terminal = read_original(command_ref), read_original(completion)
    if (set(intent) != {'machine_id', 'observed_at_utc', 'argv'}
            or set(terminal) != {'machine_id', 'observed_at_utc', 'exit_code', 'command', 'original_subprocess_wait_observed'}
            or intent.get('machine_id') != machine_id or terminal.get('machine_id') != machine_id
            or type(terminal.get('exit_code')) is not int or terminal.get('exit_code') != exit_code
            or terminal.get('original_subprocess_wait_observed') is not True
            or Path(text_field(terminal, 'command')) != Path(command_ref['path'])):
        raise ValueError('Actual same-machine public command/completion wait differs')
    argv = strings_field(intent, 'argv')
    if argv.count(mode) != 1 or not any(Path(arg).name == 'ck3_mod_acceptance.py' for arg in argv):
        raise ValueError('Original public mode/entry differs')
    started, finished = utc_stamp(text_field(intent, 'observed_at_utc')), utc_stamp(text_field(terminal, 'observed_at_utc'))
    if started > finished:
        raise ValueError('Original public completion predates command')
    return argv, finished


def create_launcher_pin_refusal(*, machine_id: str, command: FilePin, completion: FilePin,
                                stdout: FilePin, stderr: FilePin, keeper_stop: FilePin) -> LauncherPinRefusal:
    return LauncherPinRefusal(schema='ck3-mod-acceptance-launcher-pin-refusal-v1', machine_id=machine_id,
        observed_at_utc=datetime.now(timezone.utc).isoformat(), run_command=exact_original(command),
        run_completion=exact_original(completion), run_stdout=exact_original(stdout), run_stderr=exact_original(stderr),
        keeper_stop=exact_original(keeper_stop))


def validate_launcher_pin_refusal(value: object, *, frozen: JsonObject, live: Path,
                                  keeper: Path, machine_id: str) -> dict[str, FilePin]:
    row = read_original(value)
    names = ('run_command', 'run_completion', 'run_stdout', 'run_stderr', 'keeper_stop')
    if (set(row) != {'schema', 'machine_id', 'observed_at_utc', *names}
            or row.get('schema') != 'ck3-mod-acceptance-launcher-pin-refusal-v1' or row.get('machine_id') != machine_id):
        raise ValueError('Exact same-machine cooperative launcher pin refusal required')
    utc_stamp(text_field(row, 'observed_at_utc'))
    refs = {key: exact_original(row[key]) for key in names}
    argv, _ = public_operation_argv(refs['run_command'], refs['run_completion'], machine_id=machine_id, mode='run', exit_code=2)
    if argv.count('--run-context') != 1 or argv.index('--run-context')+1 >= len(argv):
        raise ValueError('Original refused run context missing')
    context = json_object(json.loads(Path(argv[argv.index('--run-context')+1]).read_text(encoding='utf-8-sig')))
    if context.get('run_id') != frozen.get('run_id') or Path(text_field(context, 'run_dir')).resolve() != live.resolve():
        raise ValueError('Original refused run belongs to another allocation')
    stdout, stderr = read_original(refs['run_stdout']), read_original(refs['run_stderr'])
    if (stderr != {'status': 'BLOCKED', 'error': PIN_ERROR, 'business_pass': False}
            or stdout.get('run_id') != frozen.get('run_id') or stdout.get('runtime_status') != 'LAUNCH_FAILED'
            or stdout.get('business_acceptance') != 'NOT_ASSESSED'
            or type(stdout.get('launcher_exit_code')) is not int or stdout.get('launcher_exit_code') != 2):
        raise ValueError('Exact before-launch-intent pin refusal terminal required')
    launchers = [Path(arg).resolve() for arg in strings_field(stdout, 'launcher_argv') if Path(arg).name == 'ck3_mod_acceptance_launcher.py']
    files = object_field(frozen, 'files')
    if len(launchers) != 1 or str(launchers[0]) not in files:
        raise ValueError('Original refused launcher is not the frozen executable source')
    launcher = launchers[0]
    exact_original({'path': str(launcher), **object_field(files, str(launcher))})
    source = launcher.read_text(encoding='utf-8-sig')
    if 'Fresh-machine helper absent from actual allocation pins' not in source or 'def frozen_run(' not in source:
        raise ValueError('Original launcher lacks the observed pre-admission guard')
    consumer = launcher.with_name('ck3_mod_acceptance_fresh_machine_bootstrap.py')
    producers = [Path(path) for path in files if Path(path).name == consumer.name]
    if str(consumer) in files or not producers or not consumer.is_file():
        raise ValueError('Original allocation does not exhibit the missing consumer-source pin')
    if (Path(refs['keeper_stop']['path']).resolve() != keeper.resolve()/'STOP'
            or Path(refs['keeper_stop']['path']).read_text(encoding='utf-8') != COOPERATIVE_STOP):
        raise ValueError('Actual cooperative launcher-refusal STOP differs')
    return refs
