"""Distinct parent execution observation through the original public CaseClient."""
from __future__ import annotations
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from typing import Protocol

from . import r08_writer_common_adapter as bridge
from . import r08_writer_one_day as cleanup_library
from . import r08_parent_entry_controller as controller


class PublicClient(Protocol):
    output: Path
    selection: object
    def guard(self) -> None: ...
    def checkpoint(self, name: str, value: dict) -> object: ...
    def normal_close(self, disposition: str) -> dict: ...


def need(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def validate_contract(context: dict) -> dict:
    value = context['case_inputs']['r08_parent_entry_one_day']
    fields = {'bundle_index_pin', 'qualification_pin', 'observer_pin', 'root_scope_path',
        'actor_id', 'expected_start_date_raw', 'parent_tools', 'prefix', 'deadline_utc',
        'payment_enable_once_authorized', 'natural_phase_enable_once_authorized'}
    need(type(value) is dict and set(value) == fields, 'Exact parent one-day settings required')
    need(type(value['actor_id']) is int and value['actor_id'] > 0
         and type(value['expected_start_date_raw']) is int and value['expected_start_date_raw'] > 0,
         'Parent actor/start date must be predeclared')
    for name in ('payment_enable_once_authorized', 'natural_phase_enable_once_authorized'):
        need(type(value[name]) is bool, 'Explicit once-enable decision required')
    need(type(value['prefix']) is str and value['prefix'].startswith('r08-parent-')
         and len(value['prefix']) < 45, 'Bounded parent prefix required')
    deadline = datetime.fromisoformat(value['deadline_utc'].replace('Z', '+00:00'))
    need(deadline.tzinfo is not None and (deadline-datetime.now(timezone.utc)).total_seconds() >= 1050,
         'Parent window requires original 900s close +120s cleanup +30s observation reserve')
    source_index = controller.read_pin(value['bundle_index_pin'])
    indexed = {Path(row['path']).resolve(): row for row in source_index['files']}
    parent_tools = Path(value['parent_tools']).resolve()
    for name in ('prepare_parent_entry_admission.py','consume_parent_entry_actual.py',
                 'parent_entry_execution_contract.py','owner_binding.py',
                 'cold_observer.cpp','parent_entry_execution_once.inc'):
        path = (parent_tools/name).resolve()
        need(path in indexed and controller.pin(path) == indexed[path],
             'Executed parent_tools path is not in the exact source bundle: '+name)
    controller.read_pin(value['qualification_pin'])
    return value


def run_case(context: dict, client: PublicClient) -> dict:
    from ck3_live_run_id import current_machine_id
    from xar_autoplayer.bridge.war_payment_observations_v1 import normalize_payment_extras, JOURNAL_KEY
    cfg = validate_contract(context)
    machine = current_machine_id()
    output = Path(client.output)
    scope_path = Path(cfg['root_scope_path'])
    need(not scope_path.exists(), 'Root scope must be issued for this fresh actual owner pair')
    controller.write(output/'r08-parent.once.json', {'machine_id': machine, 'run_id': context['run_id'],
        'predeclared_date_raw': cfg['expected_start_date_raw'], 'maximum_actual_days': 1, 'no_replay': True})
    gate = cleanup_library.CloseGate(client)
    packets = bridge.CommonPackets(context, client, output/'r08-parent-common-packets', machine=machine)
    serial = 0
    result: dict = {'machine_id': machine, 'run_id': context['run_id'], 'actual_days': 0,
        'exact_day_verified': False, 'full_R08_qualified': False, 'business_pass': False,
        'status': 'ENTERED', 'errors': []}

    def call(label: str, tool: str, args: dict) -> dict:
        nonlocal serial
        serial += 1
        return packets.request(cfg['prefix']+'-'+str(serial)+'-'+label, tool, args)[0]

    def snapshot(label: str) -> dict:
        frame = call(label, 'ck3_take_snapshot', {'include_native_command_history': False})
        need(frame.get('episode_run_id') is None and frame.get('episode_projection') == 'native_campaign'
             and frame.get('map_ready') is True and frame.get('paused') is True
             and frame.get('played_character', {}).get('character_id') == cfg['actor_id'],
             'Fresh ordinary paused same owner required')
        return frame

    def payment(label: str, mode: str) -> dict:
        frame = snapshot(label+'-frame')
        args = {'expected_revision': frame['revision'], 'payment_sampling': mode}
        if mode == 'enable':
            args['payment_window_contract'] = 'same_owned_process_no_load_v1'
        normalized = normalize_payment_extras(call(label, bridge.CASH_TOOL, args),
            snapshot=frame, payment_sampling=mode)
        if mode != 'query':
            need(normalized['war_payment_control_v1']['accepted'] is True, 'Payment action rejected')
        return normalized[JOURNAL_KEY]

    control = output/'r08-parent-control'
    try:
        initial = payment('initial-payment', 'query')
        if initial['sampling']['capture_enabled'] is not True:
            need(cfg['payment_enable_once_authorized'], 'Payment once-enable not authorized')
            cleanup_library.prepare_natural_phase(call, snapshot,
                enable_once_authorized=cfg['natural_phase_enable_once_authorized'])
            payment('payment-enable-once', 'enable')
        need(payment('payment-independent-on', 'query')['sampling']['capture_enabled'] is True,
             'Independent payment ON required')
        collected_at = time.monotonic()
        collected = bridge.collect_current_context(context, client, machine=machine,
            prefix=cfg['prefix']+'-owner', packet_root=output/'r08-parent-inputs',
            owner_binding_mode='native_campaign_owned_no_load_v2')
        expected = collected['expected']
        need(expected['date'] == cfg['expected_start_date_raw'] and expected['character_id'] == cfg['actor_id'],
             'Predeclared parent actor/day differs')
        controller.write(output/'R08-PARENT-AWAITING-ROOT.json', {'machine_id': machine,
            'run_id': context['run_id'], 'snapshot_view_pin': collected['before_response'],
            'cash_view_pin': collected['cash_response'], 'common_output': str(output),
            'retained_process': collected['common_retained_process'], 'expected': expected,
            'root_scope_path': str(scope_path), 'owner_pair_freshness_seconds': 30,
            'observer_started': False})
        # Root completes image review before this phase. Waiting never refreshes or resubmits a query.
        while not scope_path.exists():
            need(time.monotonic()-collected_at <= 30, 'Root grant absent before pair freshness expired; zero launch/day')
            time.sleep(.05)
        scope_pin = controller.pin(scope_path)
        controller.fresh(controller.read_pin(scope_pin), machine=machine, collected_at=collected_at)
        python = str(client.selection.locations['python'])
        tools = Path(cfg['parent_tools'])
        prepared = controller.prepare(python, Path(context['repo_root']), tools, collected,
            scope_pin, cfg['qualification_pin'], cfg['observer_pin'], control)
        # These bytes are the exact snapshot that admitted the native observer, not a new clock arm.
        before = controller.read_pin(collected['before_response'], 3*1024*1024)['body']
        client.guard()
        validate_contract(context)
        gate.restored = False
        try:
            window = controller.observe(python=python, tools=tools, observer=cfg['observer_pin'],
                prepared=prepared, output=control, machine=machine, scope_pin=scope_pin,
                collected_at=collected_at, before=before, deadline_utc=cfg['deadline_utc'], call=call)
            result['window'] = window
        finally:
            gate.restored = not (control/'observer-start.once.json').exists() or (
                result.get('window', {}).get('safe_to_begin_normal_close') is True)
        result['exact_day_verified'] = window['day'].get('exact_day_verified') is True
        result['status'] = 'PARENT_WINDOW_CONSUMED' if not window['primary_error'] else 'STOPPED_ERROR_PRESERVED_NO_REPLAY'
    except BaseException as exc:
        result.update(status='STOPPED_ERROR_PRESERVED_NO_REPLAY', error=type(exc).__name__+': '+str(exc))
    finally:
        claimed = (control/'day.once.json').exists()
        cleanup, errors, days = cleanup_library.cleanup_writer_window(call, snapshot, payment, gate,
            observer_claimed=claimed, expected_start_date_raw=cfg['expected_start_date_raw'])
        result.update(cleanup=cleanup, native_restore_verified=gate.restored,
            normal_close_owned_by_shared_entry=True)
        result['errors'].extend(errors)
        if days is not None:
            result['actual_days'] = days
        client.checkpoint('R08-PARENT-RESULT', result)
        client.checkpoint('R08-PARENT-TERMINAL', {'machine_id': machine, 'run_id': context['run_id'],
            'status': result['status'], 'actual_days': result['actual_days'],
            'exact_day_verified': result['exact_day_verified'], 'native_restore_verified': gate.restored,
            'OFFclear': cleanup['OFFclear'], 'Save': cleanup['Save'],
            'full_R08_qualified': False, 'business_pass': False})
    return result
