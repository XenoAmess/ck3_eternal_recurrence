"""Request normal publisher STOP and consume its original owner's exit proof.

Call only after the owned OBS inputs are independently confirmed unbound, and
before requesting normal Game close. This helper never stops a process itself.
"""
from datetime import datetime, timezone
from pathlib import Path
import time


def finish_owned_text_publisher(n, generation, deadline, read, *, maximum_seconds=20):
    from root_decision_text_api import load_api
    n=Path(n).resolve()
    outer=n/'ROOT-DECISION-TEXT-PUBLISHER-BINDING.json'
    if not outer.exists():
        return {'status':'PUBLISHER_NOT_STARTED','stop_requests':0,'normal_exit_claimed':False}
    api=load_api(n)
    binding=api.read(outer);reference=binding['publisher_started'];started=api.checked(reference)
    config=api.checked(started['configuration']);api.validate_config(config)
    if (binding.get('schema')!='xar.ck3.decision-text-publisher-binding/v1'
            or binding.get('publisher_sources')!=api.source_pins()
            or binding.get('OBS_draw_ack') is not False
            or started.get('schema')!=api.SCHEMA or started.get('status')!='DECISION_TEXT_PUBLISHER_STARTED'
            or started.get('publisher_sources')!=api.source_pins() or started.get('creates_legacy_window') is not False
            or started.get('OBS_draw_ack') is not False
            or started.get('qualified_for_game_recording') is not True or config.get('qualification_only') is not False
            or started.get('machine_id')!=binding.get('machine_id')
            or started.get('game')!=config.get('game')
            or started.get('game',{}).get('pid')!=generation.pid
            or started.get('game',{}).get('creation_filetime')!=generation.creation_filetime):
        raise ValueError('Exact normal publisher/Game/source binding differs')
    state=Path(started['state_root']).resolve()
    if not state.is_relative_to(n) or state!=Path(config['state_root']).resolve():
        raise ValueError('Publisher shutdown state escaped its owned session')
    stop=state/'STOP';owner_path=state/'OWNER-CLOSED.json'
    requests=0
    if not stop.exists():
        api.atomic(stop,{'reason':'owner_normal_stop','publisher':started['publisher'],
            'at_utc':datetime.now(timezone.utc).isoformat()},new=True)
        requests=1
    elif api.read(stop).get('publisher')!=started['publisher']:
        raise ValueError('Publisher STOP belongs to another generation')
    wait=maximum_seconds
    if deadline is not None:
        wait=min(wait,max(0,(deadline-datetime.now(timezone.utc)).total_seconds()-30))
    end=time.monotonic()+wait
    while True:
        if owner_path.exists():
            owner=api.read(owner_path);child_ref=owner['child_closed'];child=api.checked(child_ref)
            if (owner.get('schema')!=api.SCHEMA or owner.get('status')!='PUBLISHER_NORMAL_KERNEL_EXIT_ZERO'
                    or owner.get('machine_id')!=binding['machine_id']
                    or owner.get('publisher')!=started['publisher']
                    or owner.get('kernel_exit_observed') is not True or owner.get('exit_code')!=0
                    or owner.get('forced_process_calls')!=0
                    or owner.get('Popen_original_kernel_handle_retained') is not True
                    or Path(child_ref['path']).resolve()!=state/'CLOSED.json'
                    or child.get('schema')!=api.SCHEMA or child.get('machine_id')!=binding['machine_id']
                    or child.get('publisher')!=started['publisher']
                    or child.get('publisher_started')!=reference
                    or child.get('normal_STOP_observed') is not True or child.get('first_error') is not None):
                raise ValueError('Original retained PublisherOwner normal exit proof differs')
            return {'status':'PUBLISHER_NORMAL_KERNEL_EXIT_ZERO','publisher':started['publisher'],
                'machine_id':binding['machine_id'],'publisher_started':reference,'owner_closed':api.pin(owner_path),
                'stop_requests':requests,'stop_request_repeated':False,'exit_proof_consumed_from_original_owner':True,
                'normal_exit_claimed':True,'forced_process_calls':0,'Game_OBS_Native_calls':0}
        if time.monotonic()>=end:
            return {'status':'PUBLISHER_NORMAL_EXIT_UNOBSERVED','publisher_started':reference,
                'stop_requests':requests,'stop_request_repeated':False,'normal_exit_claimed':False,
                'forced_process_calls':0,'Game_OBS_Native_calls':0}
        time.sleep(.05)
