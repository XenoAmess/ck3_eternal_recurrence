"""Clear only FULL520's local map-review preflight after actual Root review."""
from __future__ import annotations
import hashlib,json
from pathlib import Path

MACHINE='xenoamess-full-tower-eb9d2c1186'
KIND='map520_local_preflight_after_Root_primary_review'


async def recover(queue,session,request,path,env,*,packet_ref,corrected_map_ref,root_review_ref,birth_reader):
    def require(ok,why):
        if not ok:raise ValueError('map520 local preflight clear denied: '+why)
    def checked(ref):
        raw=Path(ref['path']).read_bytes()
        require(len(raw)<=262144 and len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'],'exact bounded source differs')
        return json.loads(raw)
    require(request=={'sequence':521,'command':'clear_zero_rpc_preflight_rejection','arguments':{'repair_kind':KIND}}
        and path==env['INBOX']/'0521-1-result.json' and queue.next_sequence==521 and queue.held_control is None,
        'exact unused local521/current control')
    require(packet_ref['sha256']=='ba5c98d373ef20dc14358ebcebe895f142ca28b3ad31c3a17febd5d2a739c3b6','actual520 frozen preflight required')
    packet=checked(packet_ref);refs={Path(ref['original_source']).name:ref for ref in packet['sources']}
    root=env['N'].resolve();values={}
    for name in ('ROOT-CUMULATIVE-LOOP-STATE.json','ROOT-CURRENT-HALT-P37.json','ROOT-FIRST-QUEUE-EXCEPTION-P37C7.json',
            'NEXT-SEQUENCE-P37.json','CURRENT-REQUEST-P37.json','0520-1-result.json','0518-1-result.json','0519-1-result.json','ROOT-C7-SOURCE-ONLY-WARM-BOUND.json'):
        ref=refs[name];value=checked(ref);raw=Path(ref['original_source']).read_bytes()
        require(len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'],'actual preflight input changed: '+name)
        values[name]=value
    state=values['ROOT-CUMULATIVE-LOOP-STATE.json'];error=values['0520-1-result.json'];halt=values['ROOT-CURRENT-HALT-P37.json']
    original_request={'sequence':520,'command':'full_loop','arguments':{'max_turns':30}}
    message='Root must review the new actual map and overlay before initial SAVE'
    require(queue.halted=={'request':original_request,'row':None,'response':None}
        and queue.current_attempt is None and queue.halt_cause=={'error_type':'ValueError','message':message}
        and halt['original_request']==original_request and halt['original_response'] is None
        and error['request']==original_request and error['client_error']==message and error['original_response'] is None
        and values['CURRENT-REQUEST-P37.json']['sequence']==519
        and not (env['Q']/'INFLIGHT-0520.json').exists() and not (env['Q']/'0520-before-action.json').exists(),
        'only exact FULL520 before consumption/dispatch is eligible')
    require(queue.full_loop_state==state and state['completed_cycles']==219 and state['start_date_raw']==53144328
        and state['before']['date_raw']==53153472
        and all(state.get(k) is None for k in ('pending_cycle','pending_checkpoint','terminal','pending_natural_succession','pending_unsafe_route_halt'))
        and queue.initial_frame==values['ROOT-C7-SOURCE-ONLY-WARM-BOUND.json']['fresh_opening']
        and queue._source_only381['phase']=='ready' and queue.launch['pid']==153556
        and queue.launch['creation_filetime']==birth_reader(153556)==134368602545256920,
        'same clean219/day381/C7 opening required')
    oldmap=checked(refs['ROOT-CAMPAIGN-MAP-ADMITTED-C7.json']);newmap=checked(corrected_map_ref);review=checked(root_review_ref)
    require(root_review_ref['sha256']=='17e3cb081b1065102127513c3a650464d66227b7e64cfa537642f956d2f185b6'
        and oldmap['reviewer']=='/root/runtime_v20261019' and newmap['reviewer']=='/root'
        and newmap['reviewed_by_agent']=='/root/runtime_v20261019' and newmap['root_review']==root_review_ref
        and review['machine_id']==MACHINE and review['reviewer']=='/root' and review['status']=='GREEN'
        and review['frozen_pair']==oldmap['current_reviewed_pair']
        and newmap['machine_id']==MACHINE
        and all(newmap[key]==oldmap[key] for key in ('game_pid','game_creation_filetime','Game_map_visible','decision_text_visible',
            'recording_session_id','actual_initial_frame','current_reviewed_pair','semantic','capabilities','warm_bound')),
        'actual Root primary review and unchanged pixel/Game/frame/source binding required')
    actual_map=root/'ROOT-CAMPAIGN-MAP-ADMITTED-C7.json';raw=actual_map.read_bytes()
    require(len(raw)==corrected_map_ref['bytes'] and hashlib.sha256(raw).hexdigest()==corrected_map_ref['sha256'],
        'current corrected map must match exact Root-reviewed source')
    queue.guard();queue.require_camera_pixel_admission()
    audit_path=env['Q']/'MAP520-PREFLIGHT-CLEARED-0521.json'
    require(not audit_path.exists() and not (env['OUTBOX']/path.name).exists(),'one unconsumed local clear')
    audit={'schema':'xar.C7-map520-zeroRPC-local-preflight-clear/v1','machine_id':MACHINE,'observed_at_utc':env['now']().isoformat(),
        'status':'map520_local_preflight_cleared','original520_and_wrong_map_retained':True,'packet':packet_ref,
        'corrected_map':corrected_map_ref,'Root_primary_review':root_review_ref,'completed_cycles':219,'game_days':381,
        'ordinary_cycle_credit':0,'business_action_credit':0,'state_or_gift_or_Driver_changed':False,
        'new_RPC_calls':0,'original520_or_other_action_replayed':False,'original_camera_guard_revalidated':True}
    queue.consume_sequence(request);env['atomic'](audit_path,audit,limit=16384)
    result={**audit,'next_sequence':queue.next_sequence}
    env['atomic'](env['OUTBOX']/path.name,{'request':request,'result':{'is_error':False,'structured_content':result}},limit=16384)
    queue.halted=queue.halt_cause=queue.current_attempt=queue.held_control=None
    env['atomic'](root/'ROOT-CURRENT-HALT-P37.json',{'schema':audit['schema'],'machine_id':MACHINE,
        'observed_at_utc':audit['observed_at_utc'],'status':'map520_preflight_resolved','audit':str(audit_path),
        'original520_and_wrong_map_retained':True},replace=True,limit=16384)
    return result
