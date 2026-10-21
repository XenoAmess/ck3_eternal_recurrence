"""Close a consumed launch refused by its supervisor before host creation.

The CLI writes small metadata only. This new protocol proves its original
supervisor wait, never a host/game exit or business pass. Historical unknown
supervisor waits are not backfilled.
"""
from __future__ import annotations
from datetime import datetime, timezone
from collections.abc import Mapping
from ck3_mod_acceptance_background_types import JsonObject, PreviousRefusalClosure, keyed_file_pin, json_object, previous_refusal
from pathlib import Path
import argparse
import json
import os
from ck3_mod_acceptance import check_pin, pin, read_json

from ck3_mod_acceptance_launcher_protocol_v1 import (
    BACKGROUND_CLOSURE_SCHEMAS_V1, CURRENT_CLOSURE_SCHEMA_V1,
    LEGACY_CLOSURE_SCHEMA_V1,
    GATE_PROTOCOL_SHA256 as GATE_PROTOCOL_SHA256,
    LAUNCHER_PROTOCOL_SHA256 as LAUNCHER_PROTOCOL_SHA256,
    build_launcher_protocol_v1, verify_closure_protocol_v1,
)

SCHEMA = LEGACY_CLOSURE_SCHEMA_V1
SCHEMA_V2 = CURRENT_CLOSURE_SCHEMA_V1
FALSE_FIELDS = ('host_started', 'native_session_started', 'game_started',
                'normal_close_qualified', 'business_pass')


def need(value: object, message: str) -> None:
    if not value:
        raise ValueError(message)


def _read(path):
    path = Path(path)
    need(path.stat().st_size <= 1048576, 'Small original metadata required')
    value = read_json(path)
    need(isinstance(value, dict), 'Original metadata object required')
    return value


def _stamp(value):
    stamp = datetime.fromisoformat(value)
    need(stamp.tzinfo is not None and stamp.utcoffset() is not None,
         'Original timezone-aware observation required')
    return stamp


def _arg(argv, name):
    need(isinstance(argv, list) and all(isinstance(x, str) for x in argv)
         and argv.count(name) == 1 and argv.index(name) + 1 < len(argv),
         'Original command argument missing: ' + name)
    return argv[argv.index(name) + 1]


def _launcher(argv):
    paths = [Path(x).resolve() for x in argv if Path(x).name == 'ck3_mod_acceptance_launcher.py']
    need(len(paths) == 1, 'Original supervisor launcher missing or ambiguous')
    return paths[0]


def _validate_supervisor_refusal_impl(previous, freeze, close_path, keeper_root, release, bus_packet):
    from ck3_mod_acceptance_allocate import closed_lease, read_failed_runtime_release, runtime_process_inventory
    import ck3_live_run_id as ids
    import psutil
    previous, keeper_root = Path(previous).resolve(), Path(keeper_root).resolve()
    bundle = _read(close_path)
    machine, run, task = ids.current_machine_id(), freeze['run_id'], freeze['screen_task']
    need(bundle.get('schema') in BACKGROUND_CLOSURE_SCHEMAS_V1 and bundle.get('run_id') == run
         and previous.name == run and bundle.get('machine_id') == machine
         == freeze.get('identity_allocation', {}).get('machine_id'),
         'Supervisor refusal full run/machine identity differs')
    need(bundle.get('failure_stage') == 'BACKGROUND_SUPERVISOR_ADMISSION_BEFORE_RETAIN_HOST'
         and all(bundle.get(k) is False for k in FALSE_FIELDS)
         and 'supervisor_original_wait_returncode' in bundle
         and bundle['supervisor_original_wait_returncode'] == 2 and bundle.get('supervisor_original_wait_proven') is True,
         'Pre-host refusal cannot invent host/game/supervisor exit credit')
    _stamp(bundle['observed_at_utc'])
    evidence = {}

    def original(key, expected=None, decode=True):
        ref = bundle[key]
        path = Path(ref['path']).resolve()
        need(expected is None or path == Path(expected).resolve(),
             'Supervisor refusal original path differs: ' + key)
        need(path.stat().st_size <= 1048576, 'Small original metadata required: ' + key)
        check_pin(path, ref)
        evidence[key] = ref
        return _read(path) if decode else path

    ready = original('ready', previous / 'ready-context.json')
    need(original('frozen', previous / 'frozen-argv.json') == freeze,
         'Supervisor refusal supplied frozen allocation differs')
    context = original('allocated_context', previous / 'allocated-context.json')
    need(ready.get('schema') == context.get('schema') == 'ck3-mod-acceptance-run-context-v1'
         and ready.get('run_id') == context.get('run_id') == run
         and all(Path(row['run_dir']).resolve() == previous
                 and Path(row['keeper_root']).resolve() == keeper_root for row in (ready, context))
         and ready['frozen_argv'] == bundle['frozen']
         and ready['prepared_case'] == context['prepared_case'] == bundle['prepared_case']
         and ready['product'] == context['product'] and ready['case'] == context['case']
         and ready['case_inputs'] == context['case_inputs'], 'Original refused READY identity differs')
    prepared_path = Path(ready['prepared_case']['path']).resolve()
    prepared = original('prepared_case', prepared_path)
    state = Path(freeze['state_dir']).resolve()
    need(Path(prepared['startup']['state_dir']).resolve() == state,
         'Original refused prepared profile differs')
    intent = original('launch_intent', previous / 'launch-intent.json')
    supervisor = original('supervisor_started', previous / 'host-supervisor-started.json')
    stderr = original('supervisor_stderr', previous / 'host-supervisor-stderr.log')
    refused = original('background_refusal', previous/'supervisor-background-refused.json')
    waited = original('supervisor_original_wait', previous/'host-supervisor-original-wait.json')
    need(refused.get('schema')=='ck3-mod-acceptance-background-supervisor-prehost-refusal-v1'
         and refused.get('stage')=='BACKGROUND_ADMISSION_BEFORE_RETAIN_HOST'
         and refused.get('reason_code')=='BACKGROUND_OFFLINE_ADMISSION_REJECTED'
         and refused.get('error_type')=='BackgroundGateRefusal'
         and refused.get('machine_id')==machine and refused.get('run_id')==run
         and type(refused.get('supervisor_pid')) is int and refused['supervisor_pid']>0
         and refused.get('launch_intent')==bundle['launch_intent']
         and refused.get('frozen_argv')==bundle['frozen']
         and all(refused.get(k) is False for k in ('host_started','game_started','native_session_started','business_pass'))
         and stderr=={'status':'BLOCKED','error':refused.get('error_repr'),'business_pass':False},
         'Actual typed background refusal/stderr identity differs')
    need(waited.get('machine_id')==machine and waited.get('run_id')==run
         and waited.get('pid')==supervisor.get('pid') and waited.get('returncode')==2
         and waited.get('actual_original_popen_wait') is True
         and waited.get('launch_intent')==bundle['launch_intent']
         and waited.get('supervisor_started')==bundle['supervisor_started'],
         'Actual original supervisor wait differs')

    def generation(value):
        return (isinstance(value,dict) and set(value)=={'pid','birth_filetime'}
            and type(value['pid']) is int and value['pid']>0
            and isinstance(value['birth_filetime'],str) and value['birth_filetime'].isdigit()
            and 0<int(value['birth_filetime'])<2**64)
    original_generation=supervisor.get('original_popen_identity')
    runtime_generation=refused.get('runtime_identity')
    parent_generation=refused.get('runtime_parent_identity')
    need(generation(original_generation) and generation(runtime_generation) and generation(parent_generation)
         and supervisor.get('machine_id')==machine
         and original_generation['pid']==supervisor['pid']
         and waited.get('original_popen_identity')==original_generation
         and runtime_generation['pid']==refused['supervisor_pid']
         and (runtime_generation==original_generation or parent_generation==original_generation),
         'Exact supervisor runtime/original-Popen generation relation not proved')

    argv = supervisor.get('argv', [])
    launcher = _launcher(argv)
    original('launcher_source', launcher, decode=False)
    original('steam_gate_source',launcher.with_name('ck3_mod_acceptance_steam_gate.py'),decode=False)
    verify_closure_protocol_v1(bundle)
    gate_ref = keyed_file_pin(str(launcher.with_name('ck3_mod_acceptance_steam_gate.py')),
                              freeze['files'].get(str(launcher.with_name('ck3_mod_acceptance_steam_gate.py')), {}))
    need(gate_ref['sha256'] == bundle['steam_gate_source']['sha256']
         and gate_ref['bytes'] == bundle['steam_gate_source']['bytes'],
         'Reviewed background gate protocol differs')
    source_ref = keyed_file_pin(str(launcher), freeze.get('files', {}).get(str(launcher), {}))
    need(source_ref.get('sha256') == bundle['launcher_source']['sha256']
         and source_ref.get('bytes') == bundle['launcher_source']['bytes'],
         'Original frozen launcher is not the reviewed pre-retain-host refusal protocol')
    need(intent.get('run_id') == run and intent.get('business_pass') is False
         and intent.get('frozen_argv') == bundle['frozen']
         and intent.get('admitted_lease', {}).get('task_id') == task
         and type(supervisor.get('pid')) is int and supervisor['pid'] > 0
         and supervisor.get('business_pass') is False and argv.count('--supervise') == 1
         and _arg(argv, '--launch-ticket') == intent.get('ticket')
         and isinstance(intent.get('ticket'), str) and len(intent['ticket']) == 64
         and Path(_arg(argv, '--run-root')).resolve() == previous
         and Path(_arg(argv, '--keeper-root')).resolve() == keeper_root,
         'Consumed launch intent/supervisor identity differs')
    need(intent.get('schema')=='ck3-mod-acceptance-background-launch-intent-v1', 'Distinct background intent required')
    receipt_path=Path(_arg(argv,'--steam-offline-receipt')).resolve()
    receipt_ref=intent['steam_offline_receipt']
    need(Path(receipt_ref['path']).resolve()==receipt_path and refused['steam_offline_receipt']==receipt_ref,
         'Original background receipt path/pin differs')
    check_pin(receipt_path,receipt_ref);evidence['steam_offline_receipt']=receipt_ref
    from steam_offline_state_contract import parse_result
    observed=parse_result(_read(receipt_path))
    admitted=intent.get('background_admission',{})
    need(observed.status=='offline' and observed.machine_id==machine and observed.steam is not None
         and admitted.get('schema')=='ck3-mod-acceptance-background-offline-admission-v1'
         and admitted.get('machine_id')==machine and admitted.get('receipt')==receipt_ref
         and admitted.get('steam_pid')==observed.steam.pid
         and admitted.get('steam_birth_filetime')==observed.steam.birth_filetime
         and admitted.get('observed_at_utc')==observed.observed_at_utc
         and admitted.get('background_only') is True, 'Original parent background admission differs')

    waits = {}
    for mode, code in (('run', 2), ('allocate', 0)):
        row = original('public_' + mode + '_wait')
        command = row.get('argv', [])
        entries = [i for i, x in enumerate(command) if Path(x).name == 'ck3_mod_acceptance.py']
        need(row.get('machine_id') == machine and row.get('phase') == mode
             and row.get('actual_original_popen_wait') is True
             and type(row.get('returncode')) is int and row['returncode'] == code
             and type(row.get('pid')) is int and row['pid'] > 0
             and len(entries) == 1 and command.count(mode) == 1
             and (command[entries[0]+1:entries[0]+2] == [mode] or command[-1:] == [mode])
             and Path(_arg(command, '--prepared-case')).resolve() == prepared_path
             and _arg(command, '--product') == ready['product']
             and _arg(command, '--case') == ready['case'],
             'Actual original public ' + mode + ' Popen wait differs')
        for flag in ('--runtime', '--products'):
            path = Path(_arg(command, flag)).resolve()
            need(str(path) in freeze['files'], 'Original public input missing from allocation pins')
            check_pin(path, freeze['files'][str(path)])
            evidence[mode + flag] = pin(path)
        started, finished = (_stamp(row[k]) for k in ('started_at_utc', 'observed_at_utc'))
        need(started <= finished, 'Original public wait time order differs')
        waits[mode] = (row, started, finished)
    need(Path(_arg(waits['allocate'][0]['argv'], '--keeper-output')).resolve() == keeper_root
         and all(_arg(waits['allocate'][0]['argv'], k) == _arg(waits['run'][0]['argv'], k)
                 for k in ('--runtime', '--products', '--product', '--case')),
         'Original public run/allocator inputs differ')
    reviewed_path = Path(_arg(waits['run'][0]['argv'], '--run-context')).resolve()
    reviewed = _read(reviewed_path)
    need(reviewed.get('run_id')==run and Path(reviewed['run_dir']).resolve()==previous
         and Path(reviewed['keeper_root']).resolve()==keeper_root
         and reviewed.get('prepared_case')==bundle['prepared_case']
         and reviewed.get('frozen_argv')==bundle['frozen']
         and Path(reviewed['steam_offline_receipt']).resolve()==receipt_path,
         'Original public background run context differs')
    evidence['reviewed_context']=pin(reviewed_path)
    observed_at=_stamp(observed.observed_at_utc)
    intent_at,supervisor_at,refused_at,waited_at=(_stamp(row['at_utc']) for row in (intent,supervisor,refused,waited))
    need(waits['run'][1]<=intent_at<=supervisor_at<=refused_at<=waited_at<=waits['run'][2]
         and 0<=(intent_at-observed_at).total_seconds()<=30,
         'Actual initial admission and supervisor refusal chronology differs')

    original('keeper_STOP', keeper_root / 'STOP', decode=False)
    need((keeper_root / 'STOP').stat().st_size > 0, 'Actual keeper STOP is empty')
    keeper = original('keeper_report', keeper_root / 'report.json')
    parent = original('keeper_parent_exit', previous / 'keeper-actual-parent-exit.json')
    need(keeper.get('task_id') == task and keeper.get('thread_exited') is True
         and keeper.get('failure') is None and keeper.get('entry_error') is None
         and keeper.get('game_actions') is False and parent.get('run_id') == run
         and parent.get('keeper_actual_exit_code') == 0 and parent.get('keeper_report') == keeper
         and waits['allocate'][1] <= waits['run'][1]
         and waits['run'][2] <= _stamp(keeper['at_utc']) <= waits['allocate'][2],
         'Actual keeper STOP/original parent wait0/allocator wait0 differs')
    original('CAS_release')
    cas = read_failed_runtime_release(Path(bundle['CAS_release']['path']))
    event, task_row = cas.get('event', {}), cas.get('task', {})
    need(cas == release and closed_lease(keeper, cas, task)
         and task_row.get('state') == event.get('state') == 'done'
         and event.get('task_id') == task and event.get('kind') == 'completed'
         and event.get('sequence') == task_row.get('last_sequence')
         and event.get('resources') == [], 'Exact original keeper CAS completion differs')
    tasks = bus_packet.get('tasks', [])
    current = [row for row in tasks if row.get('task_id') == task]
    need(len(current) == 1 and all(current[0].get(k) == v for k, v in task_row.items())
         and not any('ck3-screen:acquired' in row.get('resources', []) for row in tasks),
         'Current predecessor task/released screen readback differs')

    identity, root = freeze['identity_allocation'], ids.default_state_root().resolve()
    need(Path(identity['state_root']).resolve() == root, 'Actual machine counter namespace differs')
    products = Path(_arg(waits['allocate'][0]['argv'], '--products')).resolve()
    product = _read(products)['products'][ready['product']]
    external = product.get('external_mod', False)
    need(type(external) is bool and (product.get('runtime_mod_key') or ready['product']) == freeze['mod_key'],
         'Original allocated product counter namespace differs')
    counter = root / machine / freeze['mod_key'] / 'counter.json'
    row = original('counter', counter)
    need(row.get('machine_id') == machine and row.get('mod_key') == freeze['mod_key']
         and ids.format_run_id(machine, freeze['mod_key'], row['last_sequence'], external_mod=external) == run,
         'Supervisor-refused run is not the latest actual machine/product counter')
    # Check now, but do not freeze the counter: the one subsequent allocation
    # must be able to advance it after the unchanged machine admission guard.
    evidence.pop('counter')
    absent = {name: not (previous / name).exists() for name in (
        'launch.json', 'host-started.json', 'host-stdout.log', 'host-stderr.log',
        'host-original-process-exit.json', 'native-report.json', 'native-report.session.log',
        'native-session', 'case-output')}
    absent['case-output*'] = not list(previous.glob('case-output*'))
    absent['native-report*'] = not list(previous.glob('native-report*'))
    absent['state/control'] = not (state / 'control').exists()
    absent['state/native-session'] = not (state / 'native-session').exists()
    absent['controls-empty'] = (previous / 'controls').is_dir() and not any((previous / 'controls').iterdir())
    for name in ('save games', 'logs', 'run'):
        path = state / 'profile' / name
        absent['profile/' + name] = not path.exists() or (path.is_dir() and not any(path.iterdir()))
    need(all(absent.values()), 'Supervisor refusal has actual host/native/control/profile evidence')
    need(all(not psutil.pid_exists(pid) for pid in
             (supervisor['pid'], refused['supervisor_pid'], waits['run'][0]['pid'], waits['allocate'][0]['pid'])),
         'Original supervisor/public process PID is still present; no wait inference allowed')
    inventory = runtime_process_inventory(psutil, os.getpid())
    need(not inventory['blockers'], 'Supervisor-refused predecessor runtime process is still running')
    return {'mode': 'previous-shared-background-supervisor-admission-refused', 'actual_process_inventory': inventory,
        'failure_cleanup': {'close': pin(Path(close_path)), 'original_evidence': evidence,
            'machine_id': machine, 'observed_at_utc': datetime.now(timezone.utc).isoformat(),
            'absent_host_native_control_profile': absent,
            'failure_stage': bundle['failure_stage'], 'original_public_run_exit_code': 2,
            'original_allocator_exit_code': 0, 'original_keeper_exit_code': 0,
            'original_host_exit_code': None, 'original_ck3_exit_code': None,
            'supervisor_original_wait_returncode': 2, 'supervisor_original_wait_proven':True, **{k: False for k in FALSE_FIELDS},
            'typed_normal_exit_proven': False, 'administrative_resource_admission_only': True}}


def validate_supervisor_refusal(previous: Path, freeze: Mapping[str,object], close_path: Path,
                                keeper_root: Path, release: Mapping[str,object],
                                bus_packet: Mapping[str,object]) -> PreviousRefusalClosure:
    # The inherited original-evidence checks run in full before the result crosses
    # this typed JSON boundary. No cast or inferred process absence supplies proof.
    return previous_refusal(_validate_supervisor_refusal_impl(
        previous, freeze, close_path, keeper_root, release, bus_packet))


def build_bundle(args: argparse.Namespace) -> JsonObject:
    import ck3_live_run_id as ids
    from ck3_mod_acceptance_allocate import current_screen_absent, read_failed_runtime_release
    previous, keeper = args.previous_live.resolve(), args.keeper_root.resolve()
    freeze = _read(previous / 'frozen-argv.json')
    ready = _read(previous / 'ready-context.json')
    machine = ids.current_machine_id()
    launcher = _launcher(_read(previous / 'host-supervisor-started.json')['argv'])
    paths = {'ready': previous / 'ready-context.json', 'frozen': previous / 'frozen-argv.json',
        'allocated_context': previous / 'allocated-context.json', 'prepared_case': Path(ready['prepared_case']['path']),
        'launch_intent': previous / 'launch-intent.json', 'supervisor_started': previous / 'host-supervisor-started.json',
        'supervisor_stderr': previous / 'host-supervisor-stderr.log',
        'background_refusal':previous/'supervisor-background-refused.json',
        'supervisor_original_wait':previous/'host-supervisor-original-wait.json','public_run_wait': args.public_run_wait,
        'public_allocate_wait': args.public_allocate_wait, 'keeper_STOP': keeper / 'STOP',
        'keeper_report': keeper / 'report.json', 'keeper_parent_exit': previous / 'keeper-actual-parent-exit.json',
        'CAS_release': args.release, 'launcher_source': launcher,'steam_gate_source':launcher.with_name('ck3_mod_acceptance_steam_gate.py'),
        'counter': ids.default_state_root() / machine / freeze['mod_key'] / 'counter.json'}
    need(all(Path(p).stat().st_size <= 1048576 for p in paths.values()), 'Bounded original metadata only')
    row = {'schema': SCHEMA_V2, 'machine_id': machine, 'observed_at_utc': datetime.now(timezone.utc).isoformat(),
        'run_id': freeze['run_id'], 'failure_stage': 'BACKGROUND_SUPERVISOR_ADMISSION_BEFORE_RETAIN_HOST',
        **{k: False for k in FALSE_FIELDS}, 'supervisor_original_wait_proven':True,'supervisor_original_wait_returncode':2,
        **{k: pin(Path(p).resolve()) for k, p in paths.items()}}
    row['launcher_protocol'] = json_object(build_launcher_protocol_v1(row['launcher_source'], row['steam_gate_source']))
    verify_closure_protocol_v1(row)
    output = args.output.resolve()
    need(not output.exists(), 'New immutable closure output required')
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(row, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    bus = Path(freeze['lease_anchor']) / 'tools/codex_task_bus.py'
    packet = current_screen_absent(Path(freeze['lease_anchor']), args.task_bus_root,
        freeze['files'][str(bus)]['sha256'], None)
    verdict = validate_supervisor_refusal(previous, freeze, output, keeper,
        read_failed_runtime_release(args.release), packet)
    return json_object({'bundle': pin(output), 'validation': verdict, 'SDK_or_launch': False})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ('previous-live', 'keeper-root', 'public-run-wait', 'public-allocate-wait',
                 'release', 'task-bus-root', 'output'):
        parser.add_argument('--' + flag, type=Path, required=True)
    print(json.dumps(build_bundle(parser.parse_args()), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
