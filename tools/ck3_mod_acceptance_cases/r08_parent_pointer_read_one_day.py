"""One same-CaseClient ordinary day; post-pointer evidence is not payment."""
from __future__ import annotations
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
import importlib
import time
from . import r08_writer_common_adapter as bridge
from . import r08_writer_one_day as cleanup_library
from . import r08_parent_pointer_read_controller as controller
from .pointer_read_public_models import (Bundle, CORE_NAMES, Collected, FilePin, MODE, Object, Settings, Snapshot,
    client_value, file_pin, need, number, object_value, read_pin, text)


def validate_contract(context: Mapping[str,object]) -> Settings:
    cfg = Settings.parse(context)
    cfg.budget()
    bundle = Bundle.parse(cfg.bundle_index_pin)
    bundle.verify()
    bundle.tools(cfg.parent_tools)
    for name in ('ck3_live_run_id','xar_autoplayer.bridge.war_payment_observations_v1',
                 'xar_autoplayer.bridge.exact_one_day_postcondition'):
        runtime_module = importlib.import_module(name)
        runtime_path: object = runtime_module.__file__
        if not isinstance(runtime_path,str) or Path(runtime_path).resolve() not in bundle.files:
            raise ValueError('Actual runtime dependency lacks an explicit source pin: '+name)
    for module in (controller,bridge,cleanup_library):
        peer_path: object = module.__file__
        if not isinstance(peer_path,str) or Path(peer_path).resolve() not in bundle.files:
            raise ValueError('Actual public module not in source index')
        need(controller.pin(Path(peer_path)) == bundle.files[Path(peer_path).resolve()],'Actual public peer differs')
    q = read_pin(cfg.qualification_pin)
    need(q.get('schema') == 'xar.maintenance.parent_pointer_read.pointer-read-qualification.v1'
         and q.get('status') == 'SELECTED_POINTER_READ_COLD_PASS' and q.get('mode') == MODE,
         'New independent pointer qualification required before SDK; execution/A08 is ineligible')
    need(file_pin(q.get('observer_pin')) == cfg.observer_pin,'Exact qualified observer required')
    rows = q.get('source_pins')
    need(isinstance(rows,list),'Qualification source pins required')
    sources: dict[str,FilePin] = {}
    if isinstance(rows,list):
        for raw in rows:
            ref = file_pin(raw)
            name = Path(ref['path']).name
            need(name not in sources,'Ambiguous qualified basename')
            sources[name] = ref
    need(set(sources) == CORE_NAMES,'All current 21 source files must be qualified')
    for name,ref in sources.items():
        portable = bundle.files[(cfg.parent_tools/name).resolve()]
        need(ref['bytes'] == portable['bytes'] and ref['sha256'] == portable['sha256'],'Tool copy differs from qualified source')
    return cfg


def executable(value: object) -> str:
    if isinstance(value,Path):
        return str(value)
    return text(value,'Python path')


def run_case(context: Mapping[str,object], client: object) -> Object:
    from ck3_live_run_id import current_machine_id
    from xar_autoplayer.bridge.war_payment_observations_v1 import normalize_payment_extras, JOURNAL_KEY
    cfg = validate_contract(context)
    actual_client = client_value(client)
    machine = text(current_machine_id(),'actual machine')
    q = read_pin(cfg.qualification_pin)
    need(q.get('machine_id') == machine,'Qualification belongs to another machine')
    output = actual_client.output
    scope_path = cfg.root_scope_path
    need(not scope_path.exists(),'Root scope must follow this fresh actual owner pair')
    run_id = text(context.get('run_id'),'run ID')
    repo = Path(text(context.get('repo_root'),'repo root'))
    controller.write(output/'r08-parent.once.json',{'run_id':run_id,'predeclared_date_raw':cfg.expected_start_date_raw,
        'maximum_actual_days':1,'no_replay':True,'full_R08_qualified':False})
    gate = cleanup_library.CloseGate(actual_client)
    packets = bridge.CommonPackets(context,actual_client,output/'r08-pointer-common-packets',machine=machine)
    serial = 0
    views: dict[str,FilePin] = {}
    errors: list[str] = []
    result: Object = {'machine_id':machine,'run_id':run_id,'observation_kind':'post_parent_pointer_read',
        'entryExact':False,'reconstructed_arguments_basis':'preserved post-read registers, not entry atomic raw',
        'actual_days':0,'exact_day_verified':False,'full_R08_qualified':False,'business_pass':False,
        'paid_maintenance_raw':None,'payer':None,'cadence':None,'status':'ENTERED','errors':errors}

    def call(label: str, tool: str, args: dict[str,object]) -> Mapping[str,object]:
        nonlocal serial
        serial += 1
        response: object = packets.request(cfg.prefix+'-'+str(serial)+'-'+label,tool,args)
        need(isinstance(response,tuple) and len(response) == 2,'Original CommonPackets pair required')
        if not isinstance(response,tuple):
            raise ValueError('CommonPackets response')
        body = object_value(response[0],'common body')
        views[label] = file_pin(response[1])
        return body

    def packet_pin(label: str) -> FilePin:
        need(label in views,'Original common-view pin absent')
        return views[label]

    def snapshot(label: str) -> Mapping[str,object]:
        return Snapshot.parse(call(label,'ck3_take_snapshot',{'include_native_command_history':False}),cfg.actor_id).raw

    def payment(label: str, mode: str) -> Mapping[str,object]:
        frame = object_value(snapshot(label+'-frame'),'payment snapshot')
        args: dict[str,object] = {'expected_revision':frame['revision'],'payment_sampling':mode}
        if mode == 'enable':
            args['payment_window_contract'] = 'same_owned_process_no_load_v1'
        normalized = object_value(normalize_payment_extras(call(label,bridge.CASH_TOOL,args),
            snapshot=frame,payment_sampling=mode),'payment normalization')
        if mode != 'query':
            need(object_value(normalized.get('war_payment_control_v1'),'payment control').get('accepted') is True,
                 'Payment control not accepted; no replay')
        return object_value(normalized.get(JOURNAL_KEY),'payment journal')

    control = output/'r08-pointer-control'
    try:
        initial = object_value(payment('initial-payment','query'),'initial payment')
        if object_value(initial.get('sampling'),'initial sampling').get('capture_enabled') is not True:
            need(cfg.payment_enable_once_authorized,'Payment enable not authorized')
            cleanup_library.prepare_natural_phase(call,snapshot,enable_once_authorized=cfg.natural_phase_enable_once_authorized)
            payment('payment-enable-once','enable')
        current = object_value(payment('payment-independent-on','query'),'independent payment')
        need(object_value(current.get('sampling'),'sampling').get('capture_enabled') is True,'Independent payment ON required')
        collected_at = time.monotonic()
        collected = Collected.parse(bridge.collect_current_context(context,actual_client,machine=machine,
            prefix=cfg.prefix+'-owner',packet_root=output/'r08-pointer-inputs',
            owner_binding_mode='native_campaign_owned_no_load_v2'),machine)
        need(collected.date == cfg.expected_start_date_raw and collected.actor == cfg.actor_id,'Predeclared owner/day differs')
        controller.write(output/'R08-PARENT-AWAITING-ROOT.json',{'run_id':run_id,'snapshot_view_pin':collected.before,
            'cash_view_pin':collected.cash,'common_inputs_receipt_pin':collected.receipt,'common_output':str(output),
            'root_scope_path':str(scope_path),'owner_pair_freshness_seconds':30,'observer_started':False,
            'actor_id':collected.actor,'date_raw':collected.date,
            'created':collected.created,
            'retained_owner_evidence':'Read original common_inputs_receipt_pin; no invented case_client_id'})
        while not scope_path.exists():
            need(time.monotonic()-collected_at <= 30,'Root grant absent before owner-pair expiry; zero launch/day')
            time.sleep(.05)
        scope_pin = controller.pin(scope_path)
        controller.fresh(read_pin(scope_pin),machine=machine,collected_at=collected_at)
        python = executable(actual_client.selection.locations['python'])
        prepared = controller.prepare(python,repo,cfg.parent_tools,collected,scope_pin,
            cfg.qualification_pin,cfg.observer_pin,control)
        before_view = read_pin(collected.before,3*1024*1024)
        before = Snapshot.parse(before_view.get('body'),cfg.actor_id)
        actual_client.guard(reserve=1050)
        validate_contract(context)
        gate.restored = False
        window: Object = {}
        try:
            window = controller.observe(python=python,tools=cfg.parent_tools,observer=cfg.observer_pin,
                prepared=prepared,output=control,machine=machine,scope_pin=scope_pin,collected_at=collected_at,
                before=before,deadline_utc=cfg.deadline.isoformat(),call=call,packet_pin=packet_pin,
                guard=lambda: actual_client.guard(reserve=1050))
            result['window'] = window
        finally:
            gate.restored = not (control/'observer-start.once.json').exists() or window.get('safe_to_begin_normal_close') is True
        day = object_value(window.get('day'),'day proof')
        result['exact_day_verified'] = day.get('exact_day_verified') is True
        result['status'] = 'PARENT_WINDOW_CONSUMED' if window.get('primary_error') is None else 'STOPPED_ERROR_PRESERVED_NO_REPLAY'
    except BaseException as exc:
        result.update(status='STOPPED_ERROR_PRESERVED_NO_REPLAY',error=type(exc).__name__+': '+str(exc))
    finally:
        cleanup,cleanup_errors,days = cleanup_library.cleanup_writer_window(call,snapshot,payment,gate,
            observer_claimed=(control/'day.once.json').exists(),expected_start_date_raw=cfg.expected_start_date_raw)
        result.update(cleanup=cleanup,native_restore_verified=gate.restored,normal_close_owned_by_shared_entry=True)
        errors.extend(cleanup_errors)
        if days is not None:
            result['actual_days'] = number(days,'actual days',1)
        actual_client.checkpoint('R08-PARENT-RESULT',result)
        actual_client.checkpoint('R08-PARENT-TERMINAL',{'machine_id':machine,'run_id':run_id,'status':result['status'],
            'actual_days':result['actual_days'],'exact_day_verified':result['exact_day_verified'],
            'native_restore_verified':gate.restored,'OFFclear':cleanup['OFFclear'],'Save':cleanup['Save'],
            'full_R08_qualified':False,'business_pass':False})
    return result
