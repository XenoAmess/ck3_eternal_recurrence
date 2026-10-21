"""First public allocation on an OS-bound machine with no prior live history.

This is an administrative admission, never a fictional previous game exit.
Canonical IDs and the existing machine admission chain remain authoritative.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import ast
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Final, Literal, TypedDict

from ck3_mod_acceptance_background_types import (
    FilePin, JsonObject, file_pin, json_object, object_field, text_field,
)

FRESH_BOOTSTRAP_SCHEMA: Final = 'ck3-mod-acceptance-fresh-machine-bootstrap-v1'
FRESH_ADMISSION_MODE: Final = 'first-machine-no-previous-session'


class MachineBinding(TypedDict):
    machine_id: str
    state_root: str
    admission_root: str


class FreshMachineBootstrap(TypedDict):
    schema: Literal['ck3-mod-acceptance-fresh-machine-bootstrap-v1']
    machine: MachineBinding
    runtime_config: FilePin
    runtime_manifest: FilePin
    repo_root: str
    bus_dir: str
    created_at_utc: str
    maintenance_closures: list[FilePin]


class MaintenanceScreenEvidence(TypedDict):
    machine_id: str
    task_id: str
    maintenance_only: Literal[True]
    no_game_start: Literal[True]
    registration: FilePin
    release: FilePin
    before_inventory: FilePin
    after_inventory: FilePin
    actions_result: FilePin


class MaintenanceScreenClosure(MaintenanceScreenEvidence):
    schema: Literal['ck3-mod-acceptance-maintenance-screen-closure-v1']


class MaintenanceScreenDeclaration(MaintenanceScreenEvidence):
    schema: Literal['ck3-mod-acceptance-maintenance-screen-declaration-v1']
    observed_at_utc: str
    raw_observation_identity: Literal['unknown']
    evidence_scope: Literal['declared-maintenance-not-previous-game-exit']


class FreshMachineAdmission(TypedDict):
    mode: Literal['first-machine-no-previous-session']
    machine: MachineBinding
    bootstrap: FilePin
    runtime_config: FilePin
    runtime_manifest: FilePin
    maintenance_evidence: list[FilePin]
    pre_identity_retirement_evidence: list[FilePin]
    canonical_history_empty: Literal[True]
    prior_session_exists: Literal[False]
    previous_normal_exit_claimed: Literal[False]
    initial_machine_no_predecessor: Literal[True]
    business_pass: Literal[False]


class FreshCurrentProcessObservation(TypedDict):
    machine_id: str
    observed_at_utc: str
    runtime_inventory: JsonObject
    ck3_inventory: JsonObject
    process_absence_is_normal_exit_proof: Literal[False]


def create_current_process_observation(*, runtime_inventory: object, ck3_inventory: object,
                                       binding: MachineBinding) -> FreshCurrentProcessObservation:
    """Bind two just-collected providers, never historical or cached inventories."""
    observed = datetime.now(timezone.utc).isoformat()
    identity = {'machine_id': binding['machine_id'], 'observed_at_utc': observed}
    value = FreshCurrentProcessObservation(
        machine_id=binding['machine_id'], observed_at_utc=observed,
        runtime_inventory=json_object({**json_object(runtime_inventory), **identity}),
        ck3_inventory=json_object({**json_object(ck3_inventory), **identity}),
        process_absence_is_normal_exit_proof=False)
    require_current_process_observation(value, binding)
    return value


def require_current_process_observation(value: object, binding: MachineBinding) -> None:
    row = json_object(value)
    if set(row) != {'machine_id', 'observed_at_utc', 'runtime_inventory', 'ck3_inventory',
                   'process_absence_is_normal_exit_proof'}:
        raise ValueError('Exact current fresh-machine process observation required')
    _machine_utc_observation(row, binding['machine_id'])
    runtime = object_field(row, 'runtime_inventory')
    game = object_field(row, 'ck3_inventory')
    for source in (runtime, game):
        _machine_utc_observation(source, binding['machine_id'])
    if (row.get('process_absence_is_normal_exit_proof') is not False
            or runtime.get('blockers') != []
            or runtime.get('process_absence_is_normal_exit_proof') is not False
            or type(game.get('tasklist_returncode')) is not int or game.get('tasklist_returncode') != 0
            or game.get('inventory_backend') != 'tasklist+toolhelp32'
            or any(game.get(key) != [] for key in ('tasklist_pids', 'wmi_pids', 'native_pids', 'processes'))):
        raise ValueError('Actual current dual-source CK3/runtime absence is not proven')


def machine_binding(value: object) -> MachineBinding:
    row = json_object(value)
    if set(row) != {'machine_id', 'state_root', 'admission_root'}:
        raise ValueError('Exact machine binding fields required')
    machine = text_field(row, 'machine_id')
    if Path(machine).name != machine:
        raise ValueError('Machine ID must be one canonical namespace component')
    state = Path(text_field(row, 'state_root'))
    admission = Path(text_field(row, 'admission_root'))
    if not state.is_absolute() or not admission.is_absolute():
        raise ValueError('Absolute canonical machine paths required')
    if admission.resolve() != (state / machine / '.shared-runtime-admissions-v1').resolve():
        raise ValueError('Machine admission directory crosses canonical ID namespace')
    return MachineBinding(machine_id=machine, state_root=str(state.resolve()),
                          admission_root=str(admission.resolve()))


def exact_pin(path: Path) -> FilePin:
    actual = path.resolve()
    with actual.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    return FilePin(path=str(actual), bytes=actual.stat().st_size, sha256=digest)


def parse_bootstrap(value: object) -> FreshMachineBootstrap:
    row = json_object(value)
    fields = {'schema', 'machine', 'runtime_config', 'runtime_manifest',
              'repo_root', 'bus_dir', 'created_at_utc', 'maintenance_closures'}
    if set(row) != fields or row.get('schema') != FRESH_BOOTSTRAP_SCHEMA:
        raise ValueError('Exact fresh-machine bootstrap contract required; no predecessor permitted')
    stamp = text_field(row, 'created_at_utc')
    observed = datetime.fromisoformat(stamp.replace('Z', '+00:00'))
    if observed.tzinfo is None or observed > datetime.now(timezone.utc):
        raise ValueError('Bootstrap timestamp must be an actual past UTC observation')
    for key in ('repo_root', 'bus_dir'):
        if not Path(text_field(row, key)).is_absolute():
            raise ValueError('Absolute fresh-machine root required: ' + key)
    closures = row.get('maintenance_closures')
    if not isinstance(closures, list):
        raise ValueError('Explicit maintenance closure pin list required')
    return FreshMachineBootstrap(
        schema=FRESH_BOOTSTRAP_SCHEMA, machine=machine_binding(row['machine']),
        runtime_config=file_pin(row['runtime_config']),
        runtime_manifest=file_pin(row['runtime_manifest']),
        repo_root=text_field(row, 'repo_root'), bus_dir=text_field(row, 'bus_dir'),
        created_at_utc=stamp,
        maintenance_closures=[file_pin(item) for item in closures],
    )


def create_bootstrap(*, binding: object, runtime_path: Path, manifest_path: Path,
                     repo_root: Path, bus_dir: Path,
                     maintenance_closures: tuple[Path, ...] = (),
                     pending_pre_identity_retirement: Path | None = None) -> FreshMachineBootstrap:
    """Prepare an identity-bound proposal; actual absence is rechecked at allocation."""
    return parse_bootstrap({
        'schema': FRESH_BOOTSTRAP_SCHEMA, 'machine': require_empty_machine_history(
            binding, pending_pre_identity_retirement=pending_pre_identity_retirement),
        'runtime_config': exact_pin(runtime_path), 'runtime_manifest': exact_pin(manifest_path),
        'repo_root': str(repo_root.resolve()), 'bus_dir': str(bus_dir.resolve()),
        'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'maintenance_closures': [exact_pin(path) for path in maintenance_closures],
    })


def require_empty_machine_history(value: object, *, pending_pre_identity_retirement: Path | None = None) -> MachineBinding:
    """Also called under the original machine chain lock before first intent."""
    binding = machine_binding(value)
    namespace = Path(binding['state_root']) / binding['machine_id']
    if namespace.is_symlink():
        raise ValueError('Canonical machine history cannot be a link')
    if namespace.exists():
        for child in namespace.iterdir():
            if child.name != '.shared-runtime-admissions-v1' or not child.is_dir() or child.is_symlink():
                raise ValueError('Machine already has canonical live history; use its actual predecessor')
            for record in child.iterdir():
                if record.name in {'chain.lock', 'machine.json'} and record.is_file():
                    continue
                if record.is_dir() and record.name == '000001':
                    if (record/'retired-pre-identity.json').is_file():
                        validate_pre_identity_retirement(record, binding, require_no_canonical=True)
                        continue
                    if pending_pre_identity_retirement is not None:
                        request = validate_pre_identity_request(pending_pre_identity_retirement, binding)
                        if Path(request['machine_intent']['path']).parent == record:
                            continue
                raise ValueError('First-machine admission already consumed, including failed intents')
    return binding


class PreIdentityRetirementRequest(TypedDict):
    schema: Literal['ck3-mod-acceptance-pre-identity-retirement-request-v1']
    machine: MachineBinding
    command: FilePin
    stdout: FilePin
    stderr: FilePin
    terminal_observation: FilePin
    terminal_tool_event: FilePin
    machine_intent: FilePin
    ledger_intent: FilePin
    id_source: FilePin
    products: FilePin


PRE_ID_REFERENCES: Final = ('command', 'stdout', 'stderr', 'terminal_observation',
                           'terminal_tool_event', 'machine_intent', 'ledger_intent', 'id_source', 'products')


class RetiredPreIdentityEpoch(TypedDict):
    schema: Literal['ck3-mod-acceptance-pre-identity-retirement-v1']
    machine: MachineBinding
    observed_at_utc: str
    request: FilePin
    current_process_observation: JsonObject
    canonical_id_allocated: Literal[False]
    normal_exit_proven: Literal[False]
    business_pass: Literal[False]


def create_pre_identity_request(*, binding: object, command: Path, stdout: Path, stderr: Path,
                                terminal_observation: Path, terminal_tool_event: Path,
                                machine_intent: Path, ledger_intent: Path, id_source: Path,
                                products: Path) -> PreIdentityRetirementRequest:
    """Freeze references to preserved originals; this grants no retirement or ID."""
    return PreIdentityRetirementRequest(
        schema='ck3-mod-acceptance-pre-identity-retirement-request-v1', machine=machine_binding(binding),
        command=exact_pin(command), stdout=exact_pin(stdout), stderr=exact_pin(stderr),
        terminal_observation=exact_pin(terminal_observation), terminal_tool_event=exact_pin(terminal_tool_event),
        machine_intent=exact_pin(machine_intent), ledger_intent=exact_pin(ledger_intent),
        id_source=exact_pin(id_source), products=exact_pin(products))


def _original_pin(value: object, *, maximum: int = 1048576) -> FilePin:
    reference = file_pin(value)
    if reference['bytes'] > maximum or exact_pin(Path(reference['path'])) != reference:
        raise ValueError('Original pre-identity evidence changed or exceeds bound')
    return reference


def _read_original(reference: FilePin) -> JsonObject:
    return json_object(json.loads(Path(reference['path']).read_text(encoding='utf-8-sig')))


def _argument(argv: list[str], flag: str) -> str:
    if argv.count(flag) != 1 or argv.index(flag)+1 >= len(argv):
        raise ValueError('Original pre-identity allocator argument missing/duplicate: '+flag)
    return argv[argv.index(flag)+1]


def _no_canonical_ids(binding: MachineBinding) -> None:
    namespace = Path(binding['state_root'])/binding['machine_id']
    if namespace.is_symlink() or any(child.name != '.shared-runtime-admissions-v1' for child in namespace.iterdir()):
        raise ValueError('A canonical ID namespace already exists; this is not a pre-identity failure')


def validate_pre_identity_request(path: Path, binding: MachineBinding, *,
                                  require_no_canonical: bool = True) -> PreIdentityRetirementRequest:
    row = json_object(json.loads(path.read_text(encoding='utf-8-sig')))
    if set(row) != {'schema', 'machine', *PRE_ID_REFERENCES} or row.get('schema') != 'ck3-mod-acceptance-pre-identity-retirement-request-v1':
        raise ValueError('Exact pre-identity retirement request required')
    if machine_binding(row['machine']) != binding:
        raise ValueError('Pre-identity retirement belongs to another actual machine/namespace')
    refs = {key: _original_pin(row[key]) for key in PRE_ID_REFERENCES}
    command, intent, ledger = (_read_original(refs[key]) for key in ('command', 'machine_intent', 'ledger_intent'))
    _machine_utc_observation(command, binding['machine_id'])
    raw_argv = command.get('argv')
    if not isinstance(raw_argv, list) or not all(isinstance(item, str) for item in raw_argv):
        raise ValueError('Original exact allocator argv required')
    argv = [text for text in raw_argv if isinstance(text, str)]
    if argv.count('allocate') != 1 or any(flag in argv for flag in ('--previous-live', '--previous-keeper', '--previous-release')):
        raise ValueError('Only an actual first allocator failure can retire before identity')
    record = Path(refs['machine_intent']['path']).parent
    if (record != Path(binding['admission_root'])/'000001' or record.is_symlink()
            or Path(refs['machine_intent']['path']).name != 'intent.json'
            or (record/'allocation.json').exists()
            or any(child.name not in {'intent.json', 'retired-pre-identity.json'} for child in record.iterdir())):
        raise ValueError('Exact sole first pre-identity intent without allocation required')
    if require_no_canonical:
        _no_canonical_ids(binding)
        if sorted(child.name for child in Path(binding['admission_root']).glob('[0-9]*')) != ['000001']:
            raise ValueError('A later machine admission already exists')
    closure = object_field(intent, 'closure')
    if (intent.get('schema') != 'ck3-mod-acceptance-machine-admission-intent-v1'
            or intent.get('machine') != binding or intent.get('status') != 'CONSUMED_ADMISSION_INTENT_NOT_RUN'
            or intent.get('business_pass') is not False
            or closure.get('mode') != FRESH_ADMISSION_MODE or closure.get('machine') != binding
            or closure.get('canonical_history_empty') is not True
            or closure.get('prior_session_exists') is not False
            or closure.get('previous_normal_exit_claimed') is not False
            or closure.get('initial_machine_no_predecessor') is not True or closure.get('business_pass') is not False
            or ledger.get('status') != 'CONSUMED_ALLOCATION_INTENT_NOT_RUN'
            or ledger.get('predecessor_admission') != closure
            or Path(text_field(ledger, 'machine_admission')) != record
            or ledger.get('product') != _argument(argv, '--product') or ledger.get('case') != _argument(argv, '--case')
            or ledger.get('attempt') != _argument(argv, '--attempt')):
        raise ValueError('Original machine/profile intent chain differs')
    for key, flag in (('runtime_config', '--runtime'), ('prepared_case', '--prepared-case')):
        reference = _original_pin(intent.get(key))
        if Path(reference['path']) != Path(_argument(argv, flag)) or (key == 'prepared_case' and ledger.get(key) != reference):
            raise ValueError('Original allocator inputs differ from the consumed intent')
    manifest_ref = _original_pin(intent.get('runtime_manifest'))
    bootstrap_ref = _original_pin(closure.get('bootstrap'))
    if Path(bootstrap_ref['path']) != Path(_argument(argv, '--first-machine-bootstrap')):
        raise ValueError('Original bootstrap differs')
    runtime = _read_original(file_pin(intent['runtime_config']))
    prepared = _read_original(file_pin(intent['prepared_case']))
    if runtime.get('manifest') != manifest_ref or prepared.get('runtime_manifest') != manifest_ref:
        raise ValueError('Original runtime/prepared manifest chain differs')
    startup = object_field(prepared, 'startup')
    state = Path(text_field(startup, 'state_dir'))
    ledger_children = {child.name for child in Path(refs['ledger_intent']['path']).parent.iterdir()}
    allowed_ledger_children = {'allocation-intent.json'}
    if not require_no_canonical:
        allowed_ledger_children.add('pre-identity-epoch-000002')
    if (Path(refs['ledger_intent']['path']) != state.parent/'single-use-ledger/allocation-intent.json'
            or not ledger_children.issubset(allowed_ledger_children)
            or 'allocation-intent.json' not in ledger_children
            or Path(_argument(argv, '--keeper-output')).exists() or (state/'control').exists()
            or any((state/'profile'/name).exists() and any((state/'profile'/name).iterdir()) for name in ('logs', 'save games', 'run'))):
        raise ValueError('Keeper, allocation result or played profile exists; not an unlaunched pre-ID epoch')
    if Path(refs['products']['path']) != Path(_argument(argv, '--products')):
        raise ValueError('Original products source differs')
    products = _read_original(refs['products'])
    product = object_field(object_field(products, 'products'), _argument(argv, '--product'))
    mod_key = product.get('runtime_mod_key') or _argument(argv, '--product')
    if not isinstance(mod_key, str) or re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', mod_key) is None or product.get('external_mod', False) is not False:
        raise ValueError('Only the original unregistered built-in mod key failure is supported')
    expected_id_source = Path(argv[argv.index('allocate')-1]).parent/'ck3_live_run_id.py'
    if Path(refs['id_source']['path']) != expected_id_source:
        raise ValueError('Original failed ID allocator source differs')
    tree = ast.parse(expected_id_source.read_text(encoding='utf-8-sig'))
    keys: set[str] | None = None
    for statement in tree.body:
        if isinstance(statement, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'CANONICAL_MOD_KEYS' for target in statement.targets):
            call = statement.value
            if isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == 'frozenset' and len(call.args) == 1:
                values = ast.literal_eval(call.args[0])
                if isinstance(values, set) and all(isinstance(item, str) for item in values):
                    keys = {item for item in values if isinstance(item, str)}
    if keys is None or mod_key in keys:
        raise ValueError('Pinned original allocator does not establish the unknown-key failure')
    stderr = Path(refs['stderr']['path']).read_text(encoding='utf-8-sig').replace('\r\n', '\n')
    expected = "ck3_live_run_id.LiveRunIdError: unknown mod key '"+mod_key+"'; expected one of: "+', '.join(sorted(keys))
    if (not stderr.startswith('Traceback (most recent call last):\n') or stderr.rstrip().splitlines()[-1] != expected
            or str(expected_id_source) not in stderr or Path(refs['stdout']['path']).read_bytes() != b''):
        raise ValueError('Original terminal failure is not the exact pre-ID unknown-key exception')
    observation = _read_original(refs['terminal_observation'])
    _machine_utc_observation(observation, binding['machine_id'])
    if (observation.get('schema') != 'ck3-preidentity-root-tool-observation-v1'
            or type(observation.get('observed_allocator_tool_exit_code')) is not int or observation.get('observed_allocator_tool_exit_code') != 1
            or observation.get('extracted_original_event') != refs['terminal_tool_event']
            or observation.get('historical_original_HANDLE_wait_claimed') is not False
            or observation.get('normal_game_exit_claimed') is not False):
        raise ValueError('Actual tool-exit-only observation required; no invented HANDLE/game exit')
    event = _read_original(refs['terminal_tool_event'])
    payload = object_field(event, 'payload')
    output = payload.get('output')
    if payload.get('type') != 'custom_tool_call_output' or not isinstance(output, list):
        raise ValueError('Original tool terminal event unavailable')
    matches = 0
    for raw in output:
        block = json_object(raw)
        value = block.get('text')
        if not isinstance(value, str):
            continue
        try:
            terminal = json_object(json.loads(value))
        except (ValueError, json.JSONDecodeError):
            continue
        text = terminal.get('output')
        if type(terminal.get('exit_code')) is not int or terminal.get('exit_code') != 1 or not isinstance(text, str):
            continue
        operation_bound = False
        for line in text.splitlines():
            try:
                detail = json_object(json.loads(line))
            except (ValueError, json.JSONDecodeError):
                continue
            operation = detail.get('operation')
            if isinstance(operation, str) and Path(operation) == Path(refs['command']['path']).parent:
                operation_bound = True
        if stderr.strip() in text.replace('\r\n', '\n') and operation_bound:
            matches += 1
    if matches != 1:
        raise ValueError('Exactly one original allocator tool exit1 with matching stderr/operation required')
    return PreIdentityRetirementRequest(schema='ck3-mod-acceptance-pre-identity-retirement-request-v1', machine=binding,
        command=refs['command'], stdout=refs['stdout'], stderr=refs['stderr'], terminal_observation=refs['terminal_observation'],
        terminal_tool_event=refs['terminal_tool_event'], machine_intent=refs['machine_intent'],
        ledger_intent=refs['ledger_intent'], id_source=refs['id_source'], products=refs['products'])


def validate_pre_identity_retirement(record: Path, binding: MachineBinding, *, require_no_canonical: bool) -> list[FilePin]:
    marker = record/'retired-pre-identity.json'
    row = _read_original(exact_pin(marker))
    if (set(row) != {'schema', 'machine', 'observed_at_utc', 'request', 'current_process_observation',
                     'canonical_id_allocated', 'normal_exit_proven', 'business_pass'}
            or row.get('schema') != 'ck3-mod-acceptance-pre-identity-retirement-v1'
            or row.get('machine') != binding or row.get('canonical_id_allocated') is not False
            or row.get('normal_exit_proven') is not False or row.get('business_pass') is not False):
        raise ValueError('Exact retired pre-identity epoch required')
    _machine_utc_observation(json_object({'machine_id': binding['machine_id'], 'observed_at_utc': row['observed_at_utc']}), binding['machine_id'])
    reference = _original_pin(row['request'])
    request = validate_pre_identity_request(Path(reference['path']), binding, require_no_canonical=require_no_canonical)
    if Path(request['machine_intent']['path']).parent != record:
        raise ValueError('Retirement crossed original machine intent')
    require_current_process_observation(row['current_process_observation'], binding)
    original = json_object(request)
    return [exact_pin(marker), reference, *[_original_pin(original[key]) for key in PRE_ID_REFERENCES]]


def retire_pre_identity_request(path: Path, *, binding: MachineBinding, product: str, case: str,
                                ledger_root: Path, process_inventory: object, bus_events: object,
                                bus_packet: object, maintenance_closures: list[FilePin]) -> FilePin:
    """Append a narrow retired epoch under the original machine lock; allocate no ID."""
    import ck3_live_run_id as ids
    require_current_process_observation(process_inventory, binding)
    require_unused_bus(bus_events, bus_packet, maintenance_closures=maintenance_closures, binding=binding)
    with ids._exclusive_file_lock(Path(binding['admission_root'])/'chain.lock'):
        request = validate_pre_identity_request(path, binding)
        command = _read_original(request['command'])
        argv_raw = command['argv']
        if not isinstance(argv_raw, list):
            raise ValueError('Original argv unavailable')
        argv = [item for item in argv_raw if isinstance(item, str)]
        if (_argument(argv, '--product') != product or _argument(argv, '--case') != case
                or Path(request['ledger_intent']['path']).parent != ledger_root):
            raise ValueError('Retirement cannot change original product/case/profile ledger namespace')
        marker = Path(request['machine_intent']['path']).parent/'retired-pre-identity.json'
        if marker.exists():
            validate_pre_identity_retirement(marker.parent, binding, require_no_canonical=True)
            if _read_original(exact_pin(marker)).get('request') != exact_pin(path):
                raise ValueError('Retirement already bound to a different original request')
            return exact_pin(marker)
        value = RetiredPreIdentityEpoch(schema='ck3-mod-acceptance-pre-identity-retirement-v1', machine=binding,
                 observed_at_utc=datetime.now(timezone.utc).isoformat(), request=exact_pin(path),
                 current_process_observation=json_object(process_inventory),
                 canonical_id_allocated=False, normal_exit_proven=False, business_pass=False)
        with marker.open('x', encoding='utf-8') as stream:
            json.dump(value, stream, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        return exact_pin(marker)


def pre_identity_retirement_evidence(binding: MachineBinding, *, require_no_canonical: bool = True) -> list[FilePin]:
    record = Path(binding['admission_root'])/'000001'
    if not (record/'retired-pre-identity.json').exists():
        return []
    return validate_pre_identity_retirement(record, binding, require_no_canonical=require_no_canonical)


def fresh_ledger_path(binding: MachineBinding, ledger: Path) -> Path:
    if not ledger.exists():
        return ledger
    evidence = pre_identity_retirement_evidence(binding)
    if not evidence:
        raise ValueError('Prepared cold input already consumed; preserve ledger')
    request = validate_pre_identity_request(Path(evidence[1]['path']), binding)
    if Path(request['ledger_intent']['path']).parent != ledger:
        raise ValueError('Retired epoch cannot bypass the original profile ledger namespace')
    return ledger/'pre-identity-epoch-000002'


def _pinned_object(reference: FilePin) -> JsonObject:
    path = Path(reference['path'])
    if not 0 < reference['bytes'] <= 1048576 or reference != exact_pin(path):
        raise ValueError('Bounded original maintenance evidence changed')
    return json_object(json.loads(path.read_text(encoding='utf-8-sig')))


def parse_maintenance_closure(value: object) -> MaintenanceScreenClosure | MaintenanceScreenDeclaration:
    row = json_object(value)
    fields = {'schema', 'machine_id', 'task_id', 'maintenance_only', 'no_game_start',
              'registration', 'release', 'before_inventory', 'after_inventory', 'actions_result'}
    declaration = row.get('schema') == 'ck3-mod-acceptance-maintenance-screen-declaration-v1'
    if declaration:
        fields |= {'observed_at_utc', 'raw_observation_identity', 'evidence_scope'}
    if (set(row) != fields or row.get('maintenance_only') is not True or row.get('no_game_start') is not True):
        raise ValueError('Exact maintenance-only/no-game-start closure required')
    common = MaintenanceScreenEvidence(
        machine_id=text_field(row, 'machine_id'), task_id=text_field(row, 'task_id'),
        maintenance_only=True, no_game_start=True,
        registration=file_pin(row['registration']), release=file_pin(row['release']),
        before_inventory=file_pin(row['before_inventory']), after_inventory=file_pin(row['after_inventory']),
        actions_result=file_pin(row['actions_result']),
    )
    if declaration:
        if (row.get('raw_observation_identity') != 'unknown'
                or row.get('evidence_scope') != 'declared-maintenance-not-previous-game-exit'):
            raise ValueError('Maintenance declaration must preserve unknown raw identity and its limited scope')
        _machine_utc_observation(row, common['machine_id'])
        return MaintenanceScreenDeclaration(
            **common, schema='ck3-mod-acceptance-maintenance-screen-declaration-v1',
            observed_at_utc=text_field(row, 'observed_at_utc'), raw_observation_identity='unknown',
            evidence_scope='declared-maintenance-not-previous-game-exit')
    if row.get('schema') != 'ck3-mod-acceptance-maintenance-screen-closure-v1':
        raise ValueError('Exact maintenance-only/no-game-start closure required')
    return MaintenanceScreenClosure(**common, schema='ck3-mod-acceptance-maintenance-screen-closure-v1')


def _machine_utc_observation(row: JsonObject, machine_id: str) -> datetime:
    if row.get('machine_id') != machine_id:
        raise ValueError('Maintenance raw observation belongs to another machine')
    stamp = datetime.fromisoformat(text_field(row, 'observed_at_utc').replace('Z', '+00:00'))
    if stamp.utcoffset() != timedelta(0) or stamp > datetime.now(timezone.utc):
        raise ValueError('Maintenance raw observation requires an actual past UTC timestamp')
    return stamp


def _maintenance_epochs(refs: list[FilePin], events: list[JsonObject], tasks: list[JsonObject],
                        binding: MachineBinding) -> dict[str, tuple[int, int]]:
    epochs: dict[str, tuple[int, int]] = {}
    for reference in refs:
        closure = parse_maintenance_closure(_pinned_object(reference))
        task = closure['task_id']
        if closure['machine_id'] != binding['machine_id'] or task in epochs:
            raise ValueError('Maintenance closure machine or task uniqueness differs')
        registration = _pinned_object(closure['registration'])
        release = _pinned_object(closure['release'])
        acquired = object_field(registration, 'event')
        released = object_field(release, 'event')
        acquired_task = object_field(registration, 'task')
        released_task = object_field(release, 'task')
        first, last = acquired.get('sequence'), released.get('sequence')
        if (type(first) is not int or not isinstance(first, int)
                or type(last) is not int or not isinstance(last, int) or not 0 < first < last
                or acquired.get('task_id') != task or released.get('task_id') != task
                or acquired_task.get('task_id') != task or released_task.get('task_id') != task
                or type(acquired_task.get('last_sequence')) is not int or acquired_task.get('last_sequence') != first
                or type(released_task.get('last_sequence')) is not int or released_task.get('last_sequence') != last
                or acquired.get('kind') != 'registered' or released.get('kind') != 'completed'
                or acquired.get('resources') != ['ck3-screen:acquired']
                or acquired_task.get('resources') != ['ck3-screen:acquired']
                or released.get('state') != 'done' or released.get('resources') != []
                or released_task.get('state') != 'done' or released_task.get('resources') != []
                or acquired not in events or released not in events):
            raise ValueError('Original maintenance screen registration/release is not proven by durable bus events')
        prefix = 'maintenance-only:no-game-start:'
        if not all(isinstance(row.get('summary'), str) and str(row['summary']).startswith(prefix)
                   for row in (acquired, released)):
            raise ValueError('Screen epoch was not explicitly declared maintenance-only before custody')
        matching = [row for row in tasks if row.get('task_id') == task]
        if (len(matching) != 1 or matching[0].get('last_sequence') != last
                or type(matching[0].get('last_sequence')) is not int
                or matching[0].get('state') != 'done' or matching[0].get('resources') != []):
            raise ValueError('Actual maintenance task is not the exact released head')
        if closure['schema'] == 'ck3-mod-acceptance-maintenance-screen-declaration-v1':
            # These originals retain unknown identity. They prove neither same-machine
            # process absence nor a previous game exit. Fresh admission still requires
            # canonical-history absence and actual current machine/process/resource guards.
            for reference in (closure['before_inventory'], closure['after_inventory'], closure['actions_result']):
                _pinned_object(reference)
            epochs[task] = first, last
            continue
        inventory_times: list[datetime] = []
        for field in ('before_inventory', 'after_inventory'):
            inventory = _pinned_object(closure['before_inventory'] if field == 'before_inventory' else closure['after_inventory'])
            inventory_times.append(_machine_utc_observation(inventory, binding['machine_id']))
            if (type(inventory.get('tasklist_returncode')) is not int or inventory.get('tasklist_returncode') != 0
                    or any(inventory.get(key) != [] for key in ('tasklist_pids', 'wmi_pids', 'processes'))):
                raise ValueError('Maintenance before/after actual CK3 absence is unavailable')
        actions = _pinned_object(closure['actions_result'])
        action_time = _machine_utc_observation(actions, binding['machine_id'])
        if not inventory_times[0] <= inventory_times[1] <= action_time:
            raise ValueError('Maintenance before/after/action observations are out of order')
        if (actions.get('machine_id') != binding['machine_id']
                or actions.get('maintenance_only') is not True or actions.get('no_game_start') is not True):
            raise ValueError('Maintenance action result cannot certify no game start')
        epochs[task] = first, last
    return epochs


def require_unused_bus(events: object, packet: object, *, maintenance_closures: list[FilePin],
                       binding: MachineBinding) -> None:
    if not isinstance(events, list):
        raise ValueError('Actual existing local bus history required')
    rows = [json_object(event) for event in events]
    tasks_raw = json_object(packet).get('tasks')
    if not isinstance(tasks_raw, list):
        raise ValueError('Fresh actual local task inventory required')
    tasks = [json_object(task) for task in tasks_raw]
    maintenance = _maintenance_epochs(maintenance_closures, rows, tasks, binding)
    for row in rows:
        sequence = row.get('sequence')
        if (row.get('schema') != 'codex.task_bus.v1' or type(sequence) is not int
                or not isinstance(sequence, int) or sequence < 1):
            raise ValueError('Actual bus sequence/schema is invalid')
        summary = row.get('summary', '')
        resources = row.get('resources', [])
        if (not isinstance(summary, str) or not isinstance(resources, list)
                or any(not isinstance(resource, str) for resource in resources)):
            raise ValueError('Actual bus history fields are invalid')
        if 'shared runtime acceptance' in summary:
            raise ValueError('Existing live/screen history cannot be bypassed by fresh-machine bootstrap')
        if 'ck3-screen:acquired' in resources:
            bounds = maintenance.get(str(row.get('task_id')))
            if bounds is None or not bounds[0] <= sequence < bounds[1]:
                raise ValueError('Existing live/screen history lacks an exact released maintenance-only epoch')
    for task in tasks:
        row = json_object(task)
        resources = row.get('resources')
        if not isinstance(resources, list):
            raise ValueError('Actual task resources are unavailable')
        if 'ck3-screen:acquired' in resources:
            raise ValueError('Exclusive CK3 screen resource is still owned')


def validate_fresh_bootstrap(
    value: object, *, bootstrap_path: Path, binding: object,
    runtime_path: Path, manifest_path: Path, repo_root: Path, bus_dir: Path,
    bus_events: object, bus_packet: object, process_inventory: object,
    previous_live: Path | None = None, previous_keeper: Path | None = None,
    previous_release: Path | None = None, previous_failure_close: Path | None = None,
    latest_screen_release: Path | None = None,
) -> FreshMachineAdmission:
    if any(path is not None for path in (previous_live, previous_keeper, previous_release,
                                         previous_failure_close, latest_screen_release)):
        raise ValueError('Fresh-machine bootstrap forbids every predecessor/release path')
    bundle = parse_bootstrap(value)
    actual = require_empty_machine_history(binding)
    if bundle['machine'] != actual:
        raise ValueError('Bootstrap belongs to another actual OS machine/ID store')
    if (bundle['runtime_config'] != exact_pin(runtime_path)
            or bundle['runtime_manifest'] != exact_pin(manifest_path)
            or Path(bundle['repo_root']).resolve() != repo_root.resolve()
            or Path(bundle['bus_dir']).resolve() != bus_dir.resolve()):
        raise ValueError('Fresh-machine bootstrap differs from selected runtime/repository/local bus')
    require_current_process_observation(process_inventory, actual)
    require_unused_bus(bus_events, bus_packet, maintenance_closures=bundle['maintenance_closures'], binding=actual)
    source = json.loads(bootstrap_path.read_text(encoding='utf-8-sig'))
    if parse_bootstrap(source) != bundle:
        raise ValueError('Bootstrap original changed during validation')
    maintenance_evidence = list(bundle['maintenance_closures'])
    for reference in bundle['maintenance_closures']:
        maintenance = parse_maintenance_closure(_pinned_object(reference))
        maintenance_evidence.extend((maintenance['registration'], maintenance['release'],
                                     maintenance['before_inventory'], maintenance['after_inventory'],
                                     maintenance['actions_result']))
    return FreshMachineAdmission(
        mode=FRESH_ADMISSION_MODE, machine=actual, bootstrap=exact_pin(bootstrap_path),
        runtime_config=bundle['runtime_config'], runtime_manifest=bundle['runtime_manifest'],
        maintenance_evidence=maintenance_evidence,
        pre_identity_retirement_evidence=pre_identity_retirement_evidence(actual),
        canonical_history_empty=True, prior_session_exists=False,
        previous_normal_exit_claimed=False, initial_machine_no_predecessor=True,
        business_pass=False,
    )


def validate_frozen_fresh_admission(frozen: JsonObject, run_root: Path) -> None:
    """Validate actual first allocation instead of inventing a previous normal exit."""
    if (frozen.get('initial_machine_no_predecessor') is not True
            or frozen.get('previous_session_closed') is not False
            or frozen.get('previous_screen_released') is not False):
        raise ValueError('Explicit first-machine no-predecessor state required')
    ref = file_pin(frozen.get('predecessor_admission'))
    path = run_root / 'predecessor-admission.json'
    if ref != exact_pin(path):
        raise ValueError('Fresh-machine admission receipt is not the frozen original')
    receipt = json_object(json.loads(path.read_text(encoding='utf-8-sig')))
    closure = object_field(receipt, 'closure')
    binding = machine_binding(closure.get('machine'))
    allocation = object_field(frozen, 'identity_allocation')
    if (closure.get('mode') != FRESH_ADMISSION_MODE
            or closure.get('canonical_history_empty') is not True
            or closure.get('prior_session_exists') is not False
            or closure.get('previous_normal_exit_claimed') is not False
            or closure.get('initial_machine_no_predecessor') is not True
            or closure.get('business_pass') is not False
            or allocation.get('machine_id') != binding['machine_id']
            or allocation.get('state_root') != binding['state_root']):
        raise ValueError('Fresh-machine admission semantics or machine differ')
    source = file_pin(closure.get('bootstrap'))
    if source != exact_pin(Path(source['path'])):
        raise ValueError('Original fresh-machine bootstrap changed')
    parse_bootstrap(json.loads(Path(source['path']).read_text(encoding='utf-8-sig')))
    maintenance_evidence = closure.get('maintenance_evidence')
    if not isinstance(maintenance_evidence, list):
        raise ValueError('Explicit frozen maintenance evidence list required')
    for value in maintenance_evidence:
        reference = file_pin(value)
        if reference != exact_pin(Path(reference['path'])):
            raise ValueError('Actual maintenance originals changed before fresh-machine launch')
    retirement = closure.get('pre_identity_retirement_evidence')
    if not isinstance(retirement, list):
        raise ValueError('Explicit frozen pre-identity retirement evidence list required')
    expected_retirement = pre_identity_retirement_evidence(binding, require_no_canonical=False)
    if retirement != json_object({'evidence': expected_retirement})['evidence']:
        raise ValueError('Frozen pre-identity retirement originals differ')
    records = sorted(Path(binding['admission_root']).glob('[0-9]*'))
    expected_names = ['000001', '000002'] if retirement else ['000001']
    if [record.name for record in records] != expected_names or any(not record.is_dir() or record.is_symlink() for record in records):
        raise ValueError('Fresh-machine launch is no longer the sole actual allocation')
    record = json_object(json.loads((records[-1]/'allocation.json').read_text(encoding='utf-8-sig')))
    intent = json_object(json.loads((records[-1]/'intent.json').read_text(encoding='utf-8-sig')))
    if (record.get('run_id') != frozen.get('run_id')
            or Path(text_field(record, 'live')).resolve() != run_root.resolve()
            or intent.get('closure') != closure):
        raise ValueError('Fresh-machine actual canonical allocation/intent differs')
    rows: list[JsonObject] = []
    for history in (Path(binding['state_root'])/binding['machine_id']).glob('*/allocations.jsonl'):
        rows.extend(json_object(json.loads(line)) for line in history.read_text(encoding='utf-8-sig').splitlines())
    if (len(rows) != 1 or rows[0].get('run_id') != frozen.get('run_id')
            or rows[0].get('machine_id') != binding['machine_id']):
        raise ValueError('Fresh-machine canonical live history differs from sole actual run')
