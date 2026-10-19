"""Exact256 bookkeeping; estate stays untouched for a new normal readonly PLAN."""
from __future__ import annotations
import copy,hashlib,json
from pathlib import Path

PINS={
 'p37-queue/ROOT-CUMULATIVE-LOOP-STATE.json':'1d40e45069d6ba610006419b97f591a1f97ae1a1c258e12b4f00650dfccb7cc0',
 'p37-queue/ROOT-GOVERNANCE-RESULT-STATE.json':'afaacd28c74b98f559bab592b8645656f775f7f52556e45c7c8eb2b6d271727a',
 'ROOT-CURRENT-HALT-P37.json':'8fbedd0fe2d7863c4707dc1562a4451673a30aa3418268710be54783e5da5e1e',
 'NEXT-SEQUENCE-P37.json':'c9578ca84f974d13a36b76e9e7b1b05b7d9734e960b7079ef07dcd48670cc8aa',
 'p37-responses/0252-1-result.json':'76c62d88abeda99e05f2937c8cdffdd54ab0e5bb3cbc7333f38aa181756c3155',
 'p37-responses/0253-1-result.json':'fa451ba86216bdc0943f3d27fa63093f40c19efd45274da2b860fb4e4c2dd68b',
 'p37-responses/0255-1-result.json':'2169d7152cc02bf3b59c39d72f8161fe5c5c5ac151b67bc66f6c537853b93d52',
 'p37-queue/ROOT-PUBLISHER251-WARM-BOUND.json':'adf312fa7af93b2bb523b615d9738610d791bca9cfa3ba5a88fa91d8318b800d',
}


async def recover(queue,session,request,path,env,*,retained,birth_reader,source_contract):
    def require(ok,why):
        if not ok:raise ValueError('estate255 predispatch clear denied: '+why)
    require(request=={'sequence':256,'command':'clear_zero_rpc_preflight_rejection',
        'arguments':{'repair_kind':'estate255_before_dispatch_for_readonly_PLAN'}},'exact unused local256')
    require(path==env['INBOX']/'0256-1-result.json' and queue.next_sequence==256 and queue.held_control is None,
        'current256 without another held control')
    root=env['N'].resolve();values={};originals=[]
    for relative,digest in PINS.items():
        raw=(root/relative).read_bytes();ref=retained[relative]
        require(len(raw)<=65536 and hashlib.sha256(raw).hexdigest()==digest
            and Path(ref['path']).read_bytes()==raw,'actual retained source differs: '+relative)
        values[relative]=json.loads(raw);originals.append(ref)
    state=values['p37-queue/ROOT-CUMULATIVE-LOOP-STATE.json'];gov=values['p37-queue/ROOT-GOVERNANCE-RESULT-STATE.json']
    row=values['p37-responses/0255-1-result.json'];sem=values['p37-responses/0252-1-result.json'];cap=values['p37-responses/0253-1-result.json']
    original={'request':row['request'],'row':row,'response':str(root/'p37-responses/0255-1-result.json')}
    require(queue.halted==original and queue.current_attempt==original
        and queue.halt_cause=={'error_type':'RuntimeError','message':'SDK error; original result retained; no automatic retry'}
        and row.get('client_error') is None and row['result']['is_error'] is True
        and row['result']['result_type']=='complete' and row['result']['structured_content'] is None
        and row['result']['content']==[{'type':'text','text':'Error executing tool ck3_auto_turn: retained estate differs from the current actor/episode sequence',
            'annotations':None,'meta':None}], 'only exact completed255 planning error')
    require(queue.full_loop_state==state and state['completed_cycles']==98
        and state['pending_cycle']=={'global_turn':99,'before':state['before'],
            'before_metrics_response':state['before_metrics_response'],'auto_sequence':255,'stage':'auto_unsettled'}
        and all(state.get(k) is None for k in ('pending_checkpoint','terminal','pending_natural_succession','pending_unsafe_route_halt'))
        and state['before']['date_raw']==53146896 and state['before']['native_revision']==61
        and state['before']['revision']==2 and state['before']['actor_character_id']==31254
        and state['before']['episode_run_id']=='native-31254-6271ac8cd441'
        and state['actual_saved_checkpoint']['date_raw']==53145792 and state['checkpoint_dirty_since_save'] is True,
        'exact98/day107/pending255/lastSaved61 state differs')
    body=env['decoded'](sem);capbody=env['decoded'](cap);control=capbody['native_session_control']
    actual=env['frame'](body,semantic=True,expected_lifecycle=queue.expected_lifecycle_binding)
    require(queue.launch['pid']==153556 and queue.launch['creation_filetime']==134368602545256920
        and birth_reader(153556)==134368602545256920 and actual==state['before']==queue.initial_frame
        and queue.semantic==body and queue._publisher251_warm['phase']=='ready'
        and control['driver_state_restored'] is True and control['driver_state_restore_kind']=='same_pid_hot'
        and control['episode_binding_state']=='active_resumed' and control['driver_state_error'] is None
        and queue.governance_result_state==gov['state'] and queue.lifestyle_pending_focus==gov['pending_focus']
        and queue.result_classifier_pin==gov['classifier'],'actual same resident/frame/lifecycle/governance metadata differs')
    contract=Path(source_contract['path']).read_bytes()
    require(len(contract)==source_contract['bytes'] and hashlib.sha256(contract).hexdigest()==source_contract['sha256'],
        'reviewed exact255 source contract differs')
    audit_path=env['Q']/'ESTATE255-BEFORE-DISPATCH-CLEARED-0256.json'
    require(not audit_path.exists() and not (env['OUTBOX']/path.name).exists(),'one unreplayed local clear')
    audit={'schema':'xar.c5-estate255-before-dispatch-clear/v1','machine_id':'xenoamess-full-tower-eb9d2c1186',
        'observed_at_utc':env['now']().isoformat(),'status':'estate255_before_dispatch_cleared_for_readonly_PLAN',
        'original255_error_retained':True,'retained_originals':originals,'source_contract':source_contract,
        'completed_cycles':98,'observed_game_days':107,'ordinary_cycle_credit':0,'business_action_credit':0,
        'selected_business_dispatch_occurred':False,'readonly_root_query_did_occur':True,
        'estate_fields_changed_by_this_control':False,'new_RPC_calls':0,'new_Game_actions':0,
        'original_AUTO_replayed':False,'next_required_step':'new normal ck3_plan_turn257 with empty arguments',
        'current_resident_frame_only_from_retained_metadata':True,'PLAN_must_revalidate_root_and_retain_strictly':True}
    changed=copy.deepcopy(state);changed['pending_cycle']=None
    queue.consume_sequence(request)
    env['atomic'](audit_path,audit,limit=16384)
    queue.full_loop_state=changed;queue.persist_loop_state()
    result={**audit,'next_sequence':queue.next_sequence}
    env['atomic'](env['OUTBOX']/path.name,{'request':request,'result':{'is_error':False,'structured_content':result}},limit=16384)
    queue.halted=queue.halt_cause=queue.current_attempt=queue.held_control=None
    env['atomic'](root/'ROOT-CURRENT-HALT-P37.json',{'status':'exact255_predispatch_resolved_for_readonly_PLAN',
        'audit':str(audit_path),'original255_error_retained':True},replace=True,limit=16384)
    return result
