"""Capture recovery is a gameplay pause only with current stop evidence.

Historical CURRENT_HALT alone is insufficient. A no-pending recovered halt and
following feeder never opens a gameplay incident. Root can withdraw the actual
unsupported recording incident without claiming a recovery or changing credit.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import time

from . import runtime_repair_auto_applied as auto
core = auto.core
RECOVERY_STATES={'waiting_feeder_exit','waiting_normal_cleanup','waiting_overlay',
 'waiting_segment','waiting_frame','waiting_attach','capture_restored_business_halt_preserved','blocked'}


def shared(path):
    path=Path(path)
    for attempt in range(6):
        try:
            if path.stat().st_size>1024**2:raise ValueError('Bounded small metadata required')
            return json.loads(core.read_bytes(path))
        except PermissionError:
            if attempt==5:raise
            time.sleep(.02)


def current_recording_pause(health,feeder,stop,loop,halt,recovered=False):
    if (health or {}).get('status') not in RECOVERY_STATES:return None
    pending=(loop or {}).get('pending_cycle') or {}
    original=(halt or {}).get('original_request') or {}
    active_halt=(type(original.get('sequence')) is int
        and pending.get('auto_sequence')==original['sequence']
        and original.get('tool')=='ck3_auto_turn'
        and (halt or {}).get('replay_allowed') is False
        and not recovered)
    feeder_status=(feeder or {}).get('status')
    explicit_stop=((stop or {}).get('reason')=='automatic_recording_recovery'
        and feeder_status=='operator_stopped')
    # A stale pointer, old stop marker, or capture-only waiting status cannot
    # turn an actively following feeder into a stopped gameplay claim.
    if not explicit_stop and not active_halt:return None
    return {'actual_capture_recovery':health['status'],
        'current_matching_unrecovered_pending_halt':active_halt,
        'current_operator_stopped_with_recording_stop_marker':explicit_stop,
        'historical_halt_pointer_alone_accepted':False}


def recovered_old_halt(halt,response,audit):
    body=core.decode(response) or {}
    return bool(audit.get('original_request')==halt.get('original_request')
        and audit.get('original_response')==halt.get('original_response')
        and audit.get('original_auto_replayed') is False
        and audit.get('failed_pending_business_credit')==0
        and body.get('status')=='readonly_planning_precondition_recovered'
        and body.get('new_auto_admitted') is True and body.get('original_auto_replayed') is False
        and body.get('gameplay_actions_submitted')==0
        and body.get('failed_pending_business_credit')==0
        and response.get('request',{}).get('sequence')==halt.get('next_sequence'))


class RecordingGuardPublisher(auto.AutoAppliedPublisher):
    def recording_inputs(self):
        root=self.session
        health_path=root/('automatic-recording-recovery-'+self.prefix)/'STATUS.json'
        feeder_path=root/('ROOT-CONTINUOUS-FEEDER-STATUS-'+self.prefix.upper()+'.json')
        stop_path=root/('ROOT-CONTINUOUS-FEEDER-STOP-'+self.prefix.upper())
        halt_path=root/('ROOT-CURRENT-HALT-'+self.prefix.upper()+'.json')
        loop_path=self.queue/'ROOT-CUMULATIVE-LOOP-STATE.json'
        health=shared(health_path)
        feeder=shared(feeder_path) if feeder_path.is_file() else {}
        stop=shared(stop_path) if stop_path.is_file() else None
        halt=shared(halt_path) if halt_path.is_file() else None
        loop=shared(loop_path)
        recovered=False
        recovery_paths=[]
        number=(halt or {}).get('next_sequence')
        if type(number) is int:
            audit_path=self.queue/f'READONLY-PRECONDITION-RECOVERY-{number:04d}.json'
            response_path=self.outbox/f'{number:04d}-1-result.json'
            if audit_path.is_file() and response_path.is_file():
                audit,response=shared(audit_path),shared(response_path)
                recovered=recovered_old_halt(halt,response,audit)
                if recovered:recovery_paths=[audit_path,response_path]
        return (health,feeder,stop,loop,halt,recovered),{
            'health':health_path,'feeder':feeder_path,'loop':loop_path,
            'stop':stop_path if stop_path.is_file() else None,
            'halt':halt_path if halt_path.is_file() else None,
            'recovery_paths':recovery_paths}

    def observe_recording_pause(self):
        state=self.state()
        if state and state.get('phase')!='expired':return
        health_path=self.session/('automatic-recording-recovery-'+self.prefix)/'STATUS.json'
        signature=tuple(auto.transfer.v5.v4.v3.v2.signature(path) for path in (
            health_path, self.queue/'ROOT-CUMULATIVE-LOOP-STATE.json',
            self.session/('ROOT-CONTINUOUS-FEEDER-STATUS-'+self.prefix.upper()+'.json'),
            self.session/('ROOT-CONTINUOUS-FEEDER-STOP-'+self.prefix.upper()),
            self.session/('ROOT-CURRENT-HALT-'+self.prefix.upper()+'.json')))
        if signature[0] is None or signature==getattr(self,'_qualified_recording_signature',None):return
        try:
            values,paths=self.recording_inputs()
        except (PermissionError,FileNotFoundError):
            # Temporary atomic replacement is unavailable observation, never
            # proof of a recording or gameplay failure. Retry on the next tick.
            return
        self._qualified_recording_signature=signature
        proof=current_recording_pause(*values)
        if proof is None:return
        proof.update(health=core.pin(paths['health']),feeder=core.pin(paths['feeder']),
            loop=core.pin(paths['loop']),retained_halt=core.pin(paths['halt']) if paths['halt'] else None,
            feeder_stop=core.pin(paths['stop']) if paths['stop'] else None)
        self.open_source_incident(paths['health'],'\u5f55\u5236\u6062\u590d\u671f\u95f4\u81ea\u52a8\u63a8\u8fdb\u6682\u505c',
            'actual_recording_recovery_and_feeder_pause',proof)

    def retract_stale_recording_incident(self):
        state=self.state()
        if (not state or state.get('source_kind')!='actual_recording_recovery_and_feeder_pause'
                or state.get('phase') not in ('repairing','repair_applied_waiting_for_progress')
                or state.get('source_details',{}).get('feeder_stop') is not None):
            raise ValueError('Only the unsupported recording incident with no stop evidence may withdraw')
        values,paths=self.recording_inputs()
        health,feeder,stop,loop,halt,recovered=values
        pending=loop.get('pending_cycle') or {}
        old_seq=(halt or {}).get('original_request',{}).get('sequence')
        if (health.get('status')!='healthy' or stop is not None or not recovered
                or not str(feeder.get('status','')).startswith('following')
                or pending.get('auto_sequence')==old_seq
                or current_recording_pause(*values) is not None
                or core.pin(paths['halt'])!=state.get('source_details',{}).get('retained_halt')):
            raise ValueError('Current live metadata does not establish the specific stale-halt misclassification')
        archive=self.store/(state['incident_id']+'-FALSE-STOP-CURRENT-BEFORE.json')
        with archive.open('xb') as stream:stream.write(self.current.read_bytes())
        original=core.pin(archive)
        audit={'schema':'xar.runtime-repair-false-stop-withdrawal/v1','at_utc':core.utc().isoformat(),
            'incident_id':state['incident_id'],'original_current_pin':original,
            'original_opened_at_utc':state['opened_at_utc'],
            'reason':'historical readonly halt was already recovered; no current feeder stop evidence',
            'current_health':health,'current_feeder':feeder,'current_loop_before':loop.get('before'),
            'current_pending_auto_sequence':pending.get('auto_sequence'),
            'current_halt':core.pin(paths['halt']),
            'actual_old_recovery_receipts':[core.pin(p) for p in paths['recovery_paths']],
            'recording_or_gameplay_pause_inferred':False,'recovery_claimed':False,
            'new_business_credit':0,'new_cycle_credit':0,'EDL_wait_interval_allowed':False,
            'normal_gameplay_in_misreported_window_must_not_be_compressed':True,
            'Game_MCP_OBS_Desktop_calls':0}
        path=self.store/(state['incident_id']+'-FALSE-STOP-WITHDRAWN.json')
        core.atomic(path,audit)
        state.update(phase='expired',withdrawn=True,status_visible=False,
            withdrawal=core.pin(path),withdrawn_at_utc=core.utc().isoformat(),
            withdrawal_is_not_recovery=True,EDL_wait_interval_allowed=False)
        # Restore a real decision projection. Do not fabricate a successful
        # business action or emit the "recovered" status for a false incident.
        latest,actual=self.latest_decision()
        if actual is not None:
            body=core.decode(actual) or {}
            plan=body.get('plan') if isinstance(body.get('plan'),dict) else {}
            displayed={key:body[key] for key in ('status','step','selected_step') if key in body}
            displayed['plan']={key:plan[key] for key in ('phase','selected_step') if key in plan}
            if isinstance(plan.get('reason'),str):
                displayed['plan']['reason']=plan['reason'][:1000]
            row={'tool':actual.get('tool'),'request':actual.get('request',{}),
                'result':{'structured_content':displayed},
                'display_projection_only':True,'Root_status_only':True}
            row.update(source='Root withdrew unsupported stop status; prior actual decision display projection; no action replay',
                source_ref=latest['source']['path'],source_sha256=latest['source']['sha256'],
                root_repair_status_withdrawn=state['incident_id'],new_action_submitted=False)
            core.atomic(self.session/'responses'/('zz-runtime-repair-'+core.utc().strftime('%Y%m%dT%H%M%S%fZ')+'-WITHDRAWN.json'),row)
        core.atomic(self.current,state,replace=True)
        return {'status':'UNSUPPORTED_RECORDING_STOP_WITHDRAWN','audit':core.pin(path),
                'recovery_claimed':False,'EDL_wait_interval_allowed':False}


def main():
    if 'retract-stale-recording-incident' in sys.argv[1:]:
        parser=argparse.ArgumentParser(description=__doc__)
        parser.add_argument('--session',type=Path,required=True)
        parser.add_argument('--sdk-prefix',required=True)
        parser.add_argument('command',choices=['retract-stale-recording-incident'])
        args=parser.parse_args()
        publisher=RecordingGuardPublisher(args.session,args.sdk_prefix)
        try:
            with core.writer_lock(publisher.store):result=publisher.retract_stale_recording_incident()
            print(json.dumps(result))
        finally:publisher.close()
        return
    core.Publisher=RecordingGuardPublisher
    try:core.main()
    finally:
        for publisher in auto.transfer.v5.v4.v3.v2.ACTIVE_PUBLISHERS:publisher.close()

if __name__=='__main__':main()
