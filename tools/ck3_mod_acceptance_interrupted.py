"""Resource-only admission after an interrupted owner lost terminal receipts.

The old state stays quarantined, including its unsafe controls. Nothing here
reconstructs process exit codes, edits historical reports or clears controls.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Final, Literal, TypedDict

from ck3_mod_acceptance_background_types import (FilePin, JsonObject, file_pin,
    json_object, object_field, text_field)
from ck3_mod_acceptance_fresh_machine_bootstrap import (MachineBinding,
    require_current_process_observation)

MODE: Final = 'previous-shared-interrupted-owner-quarantined'
KIND: Final = 'interrupted-owner-without-terminal-receipts'


class Evidence(TypedDict):
    frozen_argv: FilePin
    ready_context: FilePin
    prepared_case: FilePin
    host_started: FilePin
    host_supervisor: FilePin
    keeper_process: FilePin
    keeper_inputs: FilePin
    native_report: FilePin
    release: FilePin


class InterruptedClosure(TypedDict):
    schema: Literal['ck3-mod-acceptance-failed-live-resource-closure-v1']
    closure_kind: Literal['interrupted-owner-without-terminal-receipts']
    machine_id: str
    observed_at_utc: str
    run_id: str
    keeper_root: str
    quarantined_state: str
    original_evidence: Evidence
    quarantined_controls: dict[str, FilePin]
    normal_close_qualified: Literal[False]
    typed_normal_exit_proven: Literal[False]
    business_pass: Literal[False]
    release_pass: Literal[False]


def require(condition: object, message: str) -> None:
    if not condition:raise ValueError(message)


def checked(value: object, *, expected: Path | None = None) -> FilePin:
    row=json_object(value)
    require(set(row)==set(FilePin.__required_keys__),'Exact interrupted evidence pin required')
    reference=file_pin(row)
    path=Path(reference['path'])
    require(path.is_absolute() and not path.is_symlink() and
            (expected is None or path.resolve()==expected.resolve()),'Interrupted evidence path differs')
    require(type(reference['bytes']) is int and 0<reference['bytes']<=64*1024*1024,
            'Bounded nonempty interrupted evidence required')
    raw=path.read_bytes()
    require(len(raw)==reference['bytes'] and hashlib.sha256(raw).hexdigest()==reference['sha256'],
            'Interrupted evidence bytes changed')
    return reference


def read(reference: FilePin) -> JsonObject:
    return json_object(json.loads(Path(reference['path']).read_text(encoding='utf-8-sig')))


def argument(argv_value: object, flag: str) -> str:
    require(isinstance(argv_value,list),'Original argv must be an array')
    if not isinstance(argv_value,list):raise ValueError('Original argv missing')
    argv=[item for item in argv_value if isinstance(item,str)]
    require(len(argv)==len(argv_value) and argv.count(flag)==1 and argv.index(flag)+1<len(argv),
            'Original interrupted argv flag missing: '+flag)
    return argv[argv.index(flag)+1]


def integer(value: object, label: str) -> int:
    if type(value) is not int or not isinstance(value,int) or value<=0:
        raise ValueError('Positive exact integer required: '+label)
    return value


def validate_interrupted_owner(*, previous: Path, frozen: object, close_path: Path,
        keeper_root: Path, release: object, bus_packet: object, binding: MachineBinding,
        current_processes: object, present_pids: set[int], next_state: Path) -> JsonObject:
    """Validate original inputs and fresh absence; caller repeats under writer lock."""
    freeze=json_object(frozen)
    bundle=json_object(json.loads(close_path.read_text(encoding='utf-8-sig')))
    require(set(bundle)==set(InterruptedClosure.__required_keys__) and bundle.get('schema')==
            'ck3-mod-acceptance-failed-live-resource-closure-v1' and bundle.get('closure_kind')==KIND,
            'Closed interrupted-owner contract required')
    require(all(bundle.get(key) is False for key in ('normal_close_qualified','typed_normal_exit_proven','business_pass','release_pass')),
            'Interrupted owner grants no exit, business or release qualification')
    run_id=text_field(freeze,'run_id')
    require(bundle.get('run_id')==run_id==previous.name and bundle.get('machine_id')==binding['machine_id'],
            'Interrupted owner belongs to another run or machine')
    observed=datetime.fromisoformat(text_field(bundle,'observed_at_utc'))
    require(observed.tzinfo is not None and observed<=datetime.now(timezone.utc),'Actual interruption observation time required')
    state=Path(text_field(freeze,'state_dir')).resolve()
    require(Path(text_field(bundle,'keeper_root')).resolve()==keeper_root.resolve() and
            Path(text_field(bundle,'quarantined_state')).resolve()==state and next_state.resolve()!=state and
            not next_state.resolve().is_relative_to(state) and not state.is_relative_to(next_state.resolve()),
            'Quarantined interrupted state cannot be reused or nested')
    refs=object_field(bundle,'original_evidence')
    require(set(refs)==set(Evidence.__required_keys__),'Complete original interrupted evidence required')
    expected={'frozen_argv':previous/'frozen-argv.json','ready_context':previous/'ready-context.json',
        'host_started':previous/'host-started.json','host_supervisor':previous/'host-supervisor-started.json',
        'keeper_process':previous/'keeper-process.json','keeper_inputs':keeper_root/'inputs.json',
        'native_report':previous/'native-report.json'}
    pins={key:checked(value,expected=expected.get(key)) for key,value in refs.items()}
    ready=read(pins['ready_context'])
    require(ready.get('run_id')==run_id and ready.get('frozen_argv')==pins['frozen_argv'] and
            Path(text_field(ready,'run_dir')).resolve()==previous.resolve() and
            Path(text_field(ready,'keeper_root')).resolve()==keeper_root.resolve(),
            'Interrupted READY crossed original frozen run/keeper')
    prepared_pin=checked(pins['prepared_case'],expected=Path(text_field(object_field(ready,'prepared_case'),'path')))
    prepared=read(prepared_pin)
    require(ready.get('prepared_case')==prepared_pin and prepared.get('runtime_manifest')==freeze.get('runtime_manifest') and
            Path(text_field(object_field(prepared,'startup'),'state_dir')).resolve()==state,
            'Interrupted preparation crossed original state/runtime')
    host,supervisor,keeper,inputs=(read(pins[key]) for key in ('host_started','host_supervisor','keeper_process','keeper_inputs'))
    # Windows venv's original Popen redirector and the runtime interpreter can
    # have different PIDs. Keep both original observations and require absence;
    # their equality is not a producer contract or an exit attestation.
    integer(host.get('supervisor_pid'),'runtime supervisor')
    integer(supervisor.get('pid'),'original Popen supervisor')
    require(host.get('run_id')==run_id and host.get('argv')==freeze.get('argv') and host.get('actual_popen_retained') is True and
            Path(argument(supervisor.get('argv'),'--run-root')).resolve()==previous.resolve() and
            Path(argument(supervisor.get('argv'),'--keeper-root')).resolve()==keeper_root.resolve(),
            'Original interrupted host/supervisor binding differs')
    task=text_field(freeze,'screen_task')
    require(argument(keeper.get('argv'),'--task')==task and
            Path(argument(keeper.get('argv'),'--root')).resolve()==keeper_root.resolve() and
            inputs.get('task_id')==task,'Original interrupted keeper binding differs')
    report=read(pins['native_report'])
    require(report.get('status')=='RUNNING' and report.get('finished_at') is None and
            report.get('managed_session_thread_finished') is False and
            Path(text_field(report,'state_dir')).resolve()==state,
            'Interrupted report must remain its actual unfinished original')
    missing=[previous/'host-original-process-exit.json',previous/'keeper-actual-parent-exit.json',
             previous/'case-output/normal-close-result.json',keeper_root/'report.json']
    require(all(not path.exists() for path in missing),'Existing terminal receipts require the original closure route')
    controls=object_field(bundle,'quarantined_controls')
    root=state/'control'
    actual={path.name for path in root.iterdir() if path.is_file()}
    require(all(path.is_file() and not path.is_symlink() for path in root.iterdir()),'Unexpected control child in quarantine')
    require(set(controls)==actual and {'ck3.json','owner.json','unsafe-cleanup.json'}<=actual and
            len([name for name in actual if name.startswith('watchdog-') and name.endswith('.ready.json')])==1,
            'Complete unchanged unsafe-control quarantine required')
    control_pins={name:checked(value,expected=root/name) for name,value in controls.items()}
    game,owner,unsafe=(read(control_pins[key]) for key in ('ck3.json','owner.json','unsafe-cleanup.json'))
    nonce=text_field(game,'nonce')
    start=object_field(report,'frontend_fixture_start_submission')
    require(start.get('status')=='SINGLE_START_ACKNOWLEDGED_POST_STATE_PENDING' and
            start.get('acknowledged') is True and start.get('retry_allowed') is False and
            integer(object_field(object_field(start,'result'),'binding').get('bridge_pid'),'observed bridge PID')==
            integer(game.get('ck3_pid'),'quarantined CK3 PID'),
            'Original single Start must independently bind the interrupted CK3 identity')
    require(actual=={'ck3.json','owner.json','unsafe-cleanup.json',f'watchdog-{nonce}.ready.json',
                     f'ck3.{nonce}.watchdog_start.json'},'Quarantine control names differ from original nonce')
    watchdog=read(control_pins[f'watchdog-{nonce}.ready.json'])
    early=read(control_pins[f'ck3.{nonce}.watchdog_start.json'])
    require(unsafe.get('nonce')==nonce and integer(unsafe.get('ck3_pid'),'unsafe CK3')==integer(game.get('ck3_pid'),'CK3') and
            integer(game.get('parent_pid'),'game parent')==integer(owner.get('pid'),'owner') and
            Path(text_field(owner,'state_dir')).resolve()==state,'Quarantined controls cross original nonce/owner')
    original_pids={integer(row.get(key),label) for row,key,label in
        ((host,'pid','host'),(host,'supervisor_pid','runtime supervisor'),(supervisor,'pid','original Popen supervisor'),
         (keeper,'pid','keeper'),(game,'ck3_pid','CK3'),(owner,'pid','owner'))}
    require(watchdog.get('nonce')==early.get('nonce')==nonce and
            watchdog.get('parent_pid')==early.get('parent_pid')==owner.get('pid') and
            watchdog.get('watchdog_pid')==early.get('watchdog_pid'),'Original watchdog control bindings differ')
    original_pids.update((integer(watchdog.get('watchdog_pid'),'watchdog'),
                          integer(early.get('watchdog_parent_pid'),'watchdog parent')))
    require(original_pids.isdisjoint(present_pids),'An original interrupted process remains present')
    require_current_process_observation(current_processes,binding)
    packet=json_object(bus_packet);tasks=packet.get('tasks')
    require(isinstance(tasks,list),'Current actual bus task list required')
    if not isinstance(tasks,list):raise ValueError('Missing bus tasks')
    rows=[json_object(row) for row in tasks]
    require(not any('ck3-screen:acquired' in row.get('resources',[]) for row in rows),'An actual screen owner remains')
    released=json_object(release)
    checked(pins['release'])
    require(read(pins['release'])==released,'Original actual release differs from supplied release')
    event=object_field(released,'event');released_task=object_field(released,'task')
    bus_dir=Path(argument(keeper.get('argv'),'--bus-dir')).resolve()
    sequence=integer(event.get('sequence'),'release sequence')
    prior_sequence=integer(object_field(event,'retirement').get('prior_sequence'),'retired sequence')
    canonical: dict[int,JsonObject]={}
    with (bus_dir/'events.jsonl').open('rb') as stream:
        for raw in stream:
            require(len(raw)<=1024*1024,'Canonical event exceeds bound')
            value=json_object(json.loads(raw))
            if value.get('sequence') in (sequence,prior_sequence):
                key=integer(value.get('sequence'),'canonical sequence')
                require(key not in canonical,'Duplicate canonical sequence')
                canonical[key]=value
    require(canonical.get(sequence)==event and prior_sequence<sequence,'Release differs from original canonical event stream')
    prior=canonical.get(prior_sequence,{})
    require(prior.get('task_id')==task and prior.get('state')=='running' and
            prior.get('resources')==['ck3-screen:acquired'] and
            (datetime.fromisoformat(text_field(event,'timestamp_utc'))-
             datetime.fromisoformat(text_field(prior,'timestamp_utc'))).total_seconds()>600,
            'Exact prior screen claim was not expired at retirement')
    require(released.get('ok') is True and event.get('task_id')==released_task.get('task_id')==task and
            event.get('state')==released_task.get('state')=='waiting' and
            event.get('resources')==released_task.get('resources')==[] and
            event.get('sequence')==released_task.get('last_sequence') and
            object_field(event,'retirement').get('business_status')=='unresolved_red',
            'Actual interrupted CAS retirement differs')
    matching=[row for row in rows if row.get('task_id')==task]
    require(len(matching)==1 and {key:value for key,value in matching[0].items()
            if key not in ('age_seconds','stale')}==released_task,
            'Current task differs from the exact interrupted retirement')
    return json_object({'mode':MODE,'actual_process_inventory':object_field(json_object(current_processes),'runtime_inventory'),
        'failure_cleanup':{'close':checked({'path':str(close_path.resolve()),'bytes':close_path.stat().st_size,
            'sha256':hashlib.sha256(close_path.read_bytes()).hexdigest()}),
            'original_evidence':pins,'quarantined_state':str(state),'quarantined_controls':control_pins,
            'original_host_exit_code':None,'original_keeper_exit_code':None,'original_ck3_exit_code':None,
            'original_host_wait_proven':False,'original_keeper_wait_proven':False,'native_cleanup_qualified':None,
            'normal_close_qualified':False,'typed_normal_exit_proven':False,'business_pass':False,'release_pass':False,
            'administrative_resource_admission_only':True}})
