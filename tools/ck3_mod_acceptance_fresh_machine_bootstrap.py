"""First public allocation on an OS-bound machine with no prior live history.

This is an administrative admission, never a fictional previous game exit.
Canonical IDs and the existing machine admission chain remain authoritative.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
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


class FreshMachineAdmission(TypedDict):
    mode: Literal['first-machine-no-previous-session']
    machine: MachineBinding
    bootstrap: FilePin
    runtime_config: FilePin
    runtime_manifest: FilePin
    canonical_history_empty: Literal[True]
    prior_session_exists: Literal[False]
    previous_normal_exit_claimed: Literal[False]
    initial_machine_no_predecessor: Literal[True]
    business_pass: Literal[False]


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
              'repo_root', 'bus_dir', 'created_at_utc'}
    if set(row) != fields or row.get('schema') != FRESH_BOOTSTRAP_SCHEMA:
        raise ValueError('Exact fresh-machine bootstrap contract required; no predecessor permitted')
    stamp = text_field(row, 'created_at_utc')
    observed = datetime.fromisoformat(stamp.replace('Z', '+00:00'))
    if observed.tzinfo is None or observed > datetime.now(timezone.utc):
        raise ValueError('Bootstrap timestamp must be an actual past UTC observation')
    for key in ('repo_root', 'bus_dir'):
        if not Path(text_field(row, key)).is_absolute():
            raise ValueError('Absolute fresh-machine root required: ' + key)
    return FreshMachineBootstrap(
        schema=FRESH_BOOTSTRAP_SCHEMA, machine=machine_binding(row['machine']),
        runtime_config=file_pin(row['runtime_config']),
        runtime_manifest=file_pin(row['runtime_manifest']),
        repo_root=text_field(row, 'repo_root'), bus_dir=text_field(row, 'bus_dir'),
        created_at_utc=stamp,
    )


def create_bootstrap(*, binding: object, runtime_path: Path, manifest_path: Path,
                     repo_root: Path, bus_dir: Path) -> FreshMachineBootstrap:
    """Prepare an identity-bound proposal; actual absence is rechecked at allocation."""
    return parse_bootstrap({
        'schema': FRESH_BOOTSTRAP_SCHEMA, 'machine': require_empty_machine_history(binding),
        'runtime_config': exact_pin(runtime_path), 'runtime_manifest': exact_pin(manifest_path),
        'repo_root': str(repo_root.resolve()), 'bus_dir': str(bus_dir.resolve()),
        'created_at_utc': datetime.now(timezone.utc).isoformat(),
    })


def require_empty_machine_history(value: object) -> MachineBinding:
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
                if record.name not in {'chain.lock', 'machine.json'} or not record.is_file():
                    raise ValueError('First-machine admission already consumed, including failed intents')
    return binding


def require_unused_bus(events: object, packet: object) -> None:
    if not isinstance(events, list):
        raise ValueError('Actual existing local bus history required')
    for event in events:
        row = json_object(event)
        sequence = row.get('sequence')
        if (row.get('schema') != 'codex.task_bus.v1' or type(sequence) is not int
                or not isinstance(sequence, int) or sequence < 1):
            raise ValueError('Actual bus sequence/schema is invalid')
        summary = row.get('summary', '')
        resources = row.get('resources', [])
        if not isinstance(summary, str) or not isinstance(resources, list):
            raise ValueError('Actual bus history fields are invalid')
        if ('shared runtime acceptance' in summary or 'ck3-screen:acquired' in resources):
            raise ValueError('Existing live/screen history cannot be bypassed by fresh-machine bootstrap')
    tasks = json_object(packet).get('tasks')
    if not isinstance(tasks, list):
        raise ValueError('Fresh actual local task inventory required')
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
    # The caller generated this inventory using the existing native/process provider.
    inventory = json_object(process_inventory)
    if inventory.get('blockers') != [] or inventory.get('process_absence_is_normal_exit_proof') is not False:
        raise ValueError('Actual CK3/keeper/controller absence is not proven')
    require_unused_bus(bus_events, bus_packet)
    source = json.loads(bootstrap_path.read_text(encoding='utf-8-sig'))
    if parse_bootstrap(source) != bundle:
        raise ValueError('Bootstrap original changed during validation')
    return FreshMachineAdmission(
        mode=FRESH_ADMISSION_MODE, machine=actual, bootstrap=exact_pin(bootstrap_path),
        runtime_config=bundle['runtime_config'], runtime_manifest=bundle['runtime_manifest'],
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
    records = sorted(Path(binding['admission_root']).glob('[0-9]*'))
    if len(records) != 1 or records[0].name != '000001':
        raise ValueError('Fresh-machine launch is no longer the sole actual allocation')
    record = json_object(json.loads((records[0]/'allocation.json').read_text(encoding='utf-8-sig')))
    intent = json_object(json.loads((records[0]/'intent.json').read_text(encoding='utf-8-sig')))
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
