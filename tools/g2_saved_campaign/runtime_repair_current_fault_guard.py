"""Current fault qualification and terminal evidence deduplication.

Frozen observers remain intact. Historical FULL errors and CURRENT_HALT pointers
are evidence, not a current stop. Root alone runs the display-side commands.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

from . import runtime_repair_recording_guard as record
core = record.core


def stopped_feeder(feeder):
    value=(feeder or {}).get('status')
    return isinstance(value,str) and value.startswith(('halted','failed','error'))


def current_queue_stop(halt,loop,feeder,full_sequence=None,recovered=False,terminal=False):
    """Pending AUTO, or the currently stopped exact FULL, never a prior FULL."""
    if recovered or terminal:return False
    request=(halt or {}).get('original_request') or {}
    number=request.get('sequence')
    if type(number) is not int:return False
    pending=(loop or {}).get('pending_cycle') or {}
    if request.get('tool')=='ck3_auto_turn' and pending.get('auto_sequence')==number:
        return (halt or {}).get('replay_allowed') is False
    current=(feeder or {}).get('control_sequence',(feeder or {}).get('failed_control_sequence'))
    return stopped_feeder(feeder) and type(full_sequence) is int and current==full_sequence


def fault_identity(binding,halt,original_pin):
    """The original raw failure and HALT bytes identify the fault across restarts."""
    return {'schema':'xar.runtime-repair-original-fault-identity/v1',
        'session':binding.get('session'),'sdk_prefix':binding.get('sdk_prefix'),
        'game_pid':binding.get('game_pid'),'game_creation_filetime':binding.get('game_creation_filetime'),
        'halt_sha256':hashlib.sha256(json.dumps(halt,sort_keys=True,separators=(',',':'),
            ensure_ascii=False).encode('utf-8')).hexdigest(),
        'original_request':halt.get('original_request'),
        'original_response':original_pin}


def fingerprint(identity):
    return hashlib.sha256(json.dumps(identity,sort_keys=True,separators=(',',':'),
        ensure_ascii=False).encode('utf-8')).hexdigest()


class CurrentFaultPublisher(record.RecordingGuardPublisher):
    def small_inputs(self):
        loop_path=self.queue/'ROOT-CUMULATIVE-LOOP-STATE.json'
        feeder_path=self.session/('ROOT-CONTINUOUS-FEEDER-STATUS-'+self.prefix.upper()+'.json')
        return record.shared(loop_path),record.shared(feeder_path) if feeder_path.is_file() else {},loop_path,feeder_path

    def identity_for_halt(self,path,binding=None):
        path=Path(path).resolve(strict=True)
        halt=record.shared(path)
        original=Path(halt.get('original_response','')).resolve(strict=True)
        source_binding=binding or self.binding
        expected=self.session/(source_binding['sdk_prefix']+'-responses')
        if original.parent!=expected.resolve():raise ValueError('Original failure is outside bound SDK outbox')
        identity=fault_identity(source_binding,halt,core.pin(original))
        identity['halt_raw_sha256']=core.pin(path)['sha256']
        return identity,halt

    def terminal_faults(self):
        if getattr(self,'_terminal_faults_loaded',False):return self._terminal_faults
        self._terminal_faults_loaded=True
        self._terminal_faults={}
        # One bounded startup migration of tiny terminal status receipts, never
        # a per-tick response/HALT directory walk. Future closures enter memory.
        count=0
        for path in self.store.iterdir():
            if not path.name.endswith(('-EXPIRED.json','-RESOLVED-SETTLED-PAIR.json','-CLOSED-FAULT.json')):continue
            count+=1
            if count>4096:raise ValueError('Terminal status migration exceeds4096 receipts')
            row=record.shared(path)
            if path.name.endswith('-CLOSED-FAULT.json'):
                if row.get('schema')=='xar.runtime-repair-terminal-fault/v1':
                    self._terminal_faults[row['fingerprint']]=core.pin(path)
                continue
            if row.get('schema')!=core.SCHEMA or row.get('phase') not in ('resolved','expired'):continue
            proof=row.get('recovery_proof') or {}
            if not row.get('withdrawn') and not (type(proof.get('actual_date_delta_raw')) is int and proof['actual_date_delta_raw']>0):continue
            pin=row.get('halt_receipt') or {}
            target=Path(pin.get('path',''))
            if not target.is_file() or core.pin(target)!=pin:continue
            binding=row.get('source_binding',row.get('binding')) or {}
            if any(binding.get(k)!=self.binding.get(k) for k in ('session','game_pid','game_creation_filetime')):continue
            try:identity,_=self.identity_for_halt(target,binding)
            except (ValueError,FileNotFoundError):continue
            self._terminal_faults[fingerprint(identity)]=core.pin(path)
        return self._terminal_faults

    def remember_terminal(self,state):
        pin=state.get('halt_receipt') or {}
        target=Path(pin.get('path',''))
        if not target.is_file() or core.pin(target)!=pin:return
        try:identity,_=self.identity_for_halt(target,state.get('source_binding',state.get('binding')))
        except (ValueError,FileNotFoundError):return
        key=fingerprint(identity)
        path=self.store/(key+'-CLOSED-FAULT.json')
        if not path.exists():core.atomic(path,{'schema':'xar.runtime-repair-terminal-fault/v1',
            'fingerprint':key,'identity':identity,'incident_id':state['incident_id'],
            'terminal_phase':state['phase'],'withdrawn':state.get('withdrawn',False),
            'terminal_state':core.pin(self.current),'business_credit':0})
        self.terminal_faults()[key]=core.pin(path)

    def qualification(self,path,full_sequence=None):
        identity,halt=self.identity_for_halt(path)
        loop,feeder,_,_=self.small_inputs()
        recovered=False
        number=halt.get('next_sequence')
        if type(number) is int:
            a=self.queue/f'READONLY-PRECONDITION-RECOVERY-{number:04d}.json'
            r=self.outbox/f'{number:04d}-1-result.json'
            if a.is_file() and r.is_file():recovered=record.recovered_old_halt(halt,record.shared(r),record.shared(a))
        terminal=self.terminal_faults().get(fingerprint(identity))
        return current_queue_stop(halt,loop,feeder,full_sequence,recovered,bool(terminal)),{
            'identity':identity,'terminal_receipt':terminal,'known_readonly_recovered':recovered,
            'current_pending_auto_sequence':(loop.get('pending_cycle') or {}).get('auto_sequence'),
            'current_feeder_status':feeder.get('status'),'current_feeder_control':feeder.get('control_sequence')}

    def repairing(self,halt_path,reason):
        qualified,_=self.qualification(halt_path)
        if not qualified:return None
        return super().repairing(halt_path,reason)

    def _open_exact(self,path,request,reason,kind,companion=None):
        path=Path(path)
        if path.parent==self.queue:
            try:full=int(path.stem.rsplit('-',1)[1])
            except ValueError:return
            qualified,_=self.qualification(path,full)
            if not qualified:return
        else:
            _,feeder,_,_=self.small_inputs()
            if not stopped_feeder(feeder) or feeder.get('control_sequence',feeder.get('failed_control_sequence'))!=request.get('sequence'):return
        return super()._open_exact(path,request,reason,kind,companion)

    def observe_feeder_error(self):
        _,feeder,_,_=self.small_inputs()
        # Guard both old feeder implementations, including the one that writes
        # its status directly instead of passing through _open_exact.
        if not stopped_feeder(feeder):return
        number=feeder.get('control_sequence',feeder.get('failed_control_sequence'))
        if type(number) is not int:return
        halt=self.queue/f'ROOT-REQUEST-HALTED-{number:04d}.json'
        if halt.is_file() and not self.qualification(halt,number)[0]:return
        return super().observe_feeder_error()

    def resolve_if_proved(self,state,semantic_path=None,batch_path=None):
        result=super().resolve_if_proved(state,semantic_path,batch_path)
        if result:self.remember_terminal(self.state())
        return result

    def expire(self,state):
        result=super().expire(state)
        if result:self.remember_terminal(self.state())
        return result

    def retract_stale_queue_incident(self):
        state=self.state()
        if not state or state.get('phase') not in ('repairing','repair_applied_waiting_for_progress'):
            raise ValueError('An active reopened historical queue incident is required')
        pin=state.get('halt_receipt') or {}
        path=Path(pin.get('path','')).resolve(strict=True)
        if path.parent!=self.queue.resolve() or core.pin(path)!=pin:raise ValueError('Original immutable HALT differs')
        qualified,proof=self.qualification(path)
        if qualified or not proof['terminal_receipt'] or not proof['known_readonly_recovered']:
            raise ValueError('Exact previously resolved fault and old recovery are required')
        loop,feeder,loop_path,feeder_path=self.small_inputs()
        if not str(feeder.get('status','')).startswith('following'):
            raise ValueError('Current feeder is not advancing through the actual control chain')
        archive=self.store/(state['incident_id']+'-FALSE-REOPEN-CURRENT-BEFORE.json')
        with archive.open('xb') as stream:stream.write(self.current.read_bytes())
        audit={'schema':'xar.runtime-repair-false-reopen-withdrawal/v1','at_utc':core.utc().isoformat(),
            'incident_id':state['incident_id'],'original_current':core.pin(archive),
            'original_opened_at_utc':state['opened_at_utc'],'qualification':proof,
            'loop':core.pin(loop_path),'feeder':core.pin(feeder_path),
            'new_business_credit':0,'new_cycle_credit':0,'recovery_claimed':False,
            'EDL_wait_interval_allowed':False,'normal_gameplay_must_not_be_compressed':True,
            'Game_MCP_OBS_Desktop_calls':0}
        target=self.store/(state['incident_id']+'-FALSE-REOPEN-WITHDRAWN.json')
        core.atomic(target,audit)
        state.update(phase='expired',withdrawn=True,status_visible=False,withdrawal=core.pin(target),
            withdrawn_at_utc=core.utc().isoformat(),withdrawal_is_not_recovery=True,EDL_wait_interval_allowed=False)
        latest,actual=self.latest_decision()
        if actual is not None:
            body=core.decode(actual) or {};plan=body.get('plan') or {}
            projection={k:body[k] for k in ('status','step','selected_step') if k in body}
            projection['plan']={k:plan[k] for k in ('phase','selected_step','reason') if k in plan}
            row={'tool':actual.get('tool'),'request':actual.get('request',{}),
                'result':{'structured_content':projection},'display_projection_only':True,'Root_status_only':True,
                'source':'Root withdrew reopened historical fault; redisplay prior real decision, no replay',
                'source_ref':latest['source']['path'],'source_sha256':latest['source']['sha256'],
                'root_repair_status_withdrawn':state['incident_id'],'new_action_submitted':False}
            core.atomic(self.session/'responses'/('zz-runtime-repair-'+core.utc().strftime('%Y%m%dT%H%M%S%fZ')+'-WITHDRAWN.json'),row)
        core.atomic(self.current,state,replace=True)
        self.remember_terminal(state)
        return {'status':'REOPENED_HISTORICAL_FAULT_WITHDRAWN','audit':core.pin(target),
            'recovery_claimed':False,'EDL_wait_interval_allowed':False}


def main():
    if 'retract-stale-queue-incident' in sys.argv[1:]:
        p=argparse.ArgumentParser(description=__doc__)
        p.add_argument('--session',type=Path,required=True);p.add_argument('--sdk-prefix',required=True)
        p.add_argument('command',choices=['retract-stale-queue-incident']);a=p.parse_args()
        publisher=CurrentFaultPublisher(a.session,a.sdk_prefix)
        try:
            with core.writer_lock(publisher.store):result=publisher.retract_stale_queue_incident()
            print(json.dumps(result))
        finally:publisher.close()
        return
    core.Publisher=CurrentFaultPublisher
    try:core.main()
    finally:
        for publisher in record.auto.transfer.v5.v4.v3.v2.ACTIVE_PUBLISHERS:publisher.close()

if __name__=='__main__':main()
