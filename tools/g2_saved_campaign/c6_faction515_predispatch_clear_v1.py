"""Exact515 planning interruption bookkeeping; preserve the earlier gift pending."""
from __future__ import annotations
import copy,hashlib,json
from pathlib import Path

MACHINE='xenoamess-full-tower-eb9d2c1186'
KIND='faction515_presubmit_newer_paused_frame_for_readonly_PLAN'


async def recover(queue,session,request,path,env,*,packet_ref,context_ref,source_contract,birth_reader):
    def require(ok,why):
        if not ok:raise ValueError('faction515 predispatch clear denied: '+why)
    def checked(ref):
        raw=Path(ref['path']).read_bytes()
        require(len(raw)<=262144 and len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'],'exact bounded source differs')
        return json.loads(raw)
    require(request=={'sequence':516,'command':'clear_zero_rpc_preflight_rejection','arguments':{'repair_kind':KIND}},
        'exact unused local516')
    require(path==env['INBOX']/'0516-1-result.json' and queue.next_sequence==516 and queue.held_control is None,
        'current516 without another held control')
    require(packet_ref['sha256']=='d69a3998558f8220d70061bd162339f0f2f8e1fe991fce86df52c73eeb76d182'
        and context_ref['sha256']=='f0ec60d1288d2d297e3358ed6316b5222acd96491ccc314d44461894bd6c1e6c',
        'actual515 frozen interruption/context required')
    packet=checked(packet_ref);context=checked(context_ref);contract=checked(source_contract)
    require(packet['machine_id']==context['machine_id']==contract['machine_id']==MACHINE
        and contract['selected515_dispatch_occurred'] is False
        and contract['earlier_gift_pending_must_remain_untouched'] is True,'exact reviewed pre-submit source boundary')
    root=env['N'].resolve();values={}
    for ref in packet['sources']:
        actual=Path(ref['original_source']);value=checked(ref);raw=actual.read_bytes()
        require(len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'],'actual retained source changed: '+actual.name)
        values[actual.name]=value
    state=values['ROOT-CUMULATIVE-LOOP-STATE.json'];gov=values['ROOT-GOVERNANCE-RESULT-STATE.json'];row=values['0515-1-result.json']
    original={'request':row['request'],'row':row,'response':str(root/'p37-responses/0515-1-result.json')}
    require(queue.halted==original and queue.current_attempt==original
        and queue.halt_cause=={'error_type':'RuntimeError','message':'SDK error; original result retained; no automatic retry'}
        and row.get('client_error') is None and row['result']['is_error'] is True
        and row['result']['result_type']=='complete' and row['result']['structured_content'] is None
        and row['result']['content']==[{'type':'text','text':'Error executing tool ck3_auto_turn: private faction pending receipt has a newer same-date paused frame',
            'annotations':None,'meta':None}], 'only the completed exact515 planning error')
    require(queue.full_loop_state==state and state['completed_cycles']==219
        and state['pending_cycle']=={'global_turn':220,'before':state['before'],
            'before_metrics_response':state['before_metrics_response'],'auto_sequence':515,'stage':'auto_unsettled'}
        and all(state.get(k) is None for k in ('pending_checkpoint','terminal','pending_natural_succession','pending_unsafe_route_halt'))
        and state['start_date_raw']==53144328 and state['before']=={
            'snapshot_id':'native:418','revision':351,'native_revision':418,'date_raw':53153472,
            'actor_character_id':31254,'episode_run_id':'native-31254-6271ac8cd441'}
        and state['checkpoint_dirty_since_save'] is True,'exact219/day381/pending220 differs')
    require(queue.launch['pid']==153556 and queue.launch['creation_filetime']==134368602545256920
        and birth_reader(153556)==134368602545256920
        and queue.governance_result_state==gov['state'] and queue.lifestyle_pending_focus==gov['pending_focus']
        and queue.result_classifier_pin==gov['classifier'],'same resident Game/governance/classifier differs')
    ledger_ref=contract['gift_ledger'];ledger=checked(ledger_ref)
    actual_ledger=root/'state/native-session/faction-gift-pending-v1.json'
    ledger_raw=actual_ledger.read_bytes()
    require(ledger_ref['sha256']=='24268466d6c3a9c521885c9dee0aeaff7e035e9ec3f6d5af0862c54a3e9768a0'
        and len(ledger_raw)==ledger_ref['bytes'] and hashlib.sha256(ledger_raw).hexdigest()==ledger_ref['sha256']
        and ledger['pending']['request_id']=='faction-gift-d29a273508614be4aa0fdfaba560667c'
        and ledger['pending']['status']=='submitted_verification_pending'
        and ledger['pending']['pre_snapshot_revision']==ledger['pending']['pre_native_snapshot_revision']==418,
        'earlier submitted gift pending must remain exact and unresolved')
    require(not (root/'responses/0515-0-plan.json').exists()
        and not (root/'responses/0515-0-plan.lock').exists()
        and not list((root/'responses').glob('0515-????-0-plan.json')),
        'a515 callback/dispatch publication appeared')
    for name,ref in contract['immutable_sources'].items():
        raw=Path(ref['path']).read_bytes()
        require(len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'],'source contract changed: '+name)
    audit_path=env['Q']/'FACTION515-PREDISPATCH-CLEARED-0516.json'
    require(not audit_path.exists() and not (env['OUTBOX']/path.name).exists(),'one unreplayed local clear')
    queue.guard()
    audit={'schema':'xar.C6-faction515-before-dispatch-clear/v1','machine_id':MACHINE,
        'observed_at_utc':env['now']().isoformat(),'status':'faction515_before_dispatch_cleared_for_readonly_PLAN',
        'packet':packet_ref,'context':context_ref,'source_contract':source_contract,'completed_cycles':219,'game_days':381,
        'ordinary_cycle_credit':0,'business_action_credit':0,'selected515_dispatch_occurred':False,
        'earlier_gift_pending_must_remain_untouched':True,'earlier_gift_success_inferred':False,
        'faction_or_Driver_files_modified':False,'original_AUTO515_replayed':False,'new_RPC_calls':0,'new_Game_actions':0,
        'next_required_step':'new normal ck3_plan_turn517 with empty arguments; retain real halt if frame changed or planning fails'}
    changed=copy.deepcopy(state);changed['pending_cycle']=None
    queue.consume_sequence(request);env['atomic'](audit_path,audit,limit=16384)
    queue.full_loop_state=changed;queue.persist_loop_state()
    result={**audit,'next_sequence':queue.next_sequence}
    env['atomic'](env['OUTBOX']/path.name,{'request':request,'result':{'is_error':False,'structured_content':result}},limit=16384)
    queue.halted=queue.halt_cause=queue.current_attempt=queue.held_control=None
    env['atomic'](root/'ROOT-CURRENT-HALT-P37.json',{'schema':audit['schema'],'machine_id':MACHINE,
        'observed_at_utc':audit['observed_at_utc'],'status':'exact515_predispatch_resolved_for_readonly_PLAN',
        'audit':str(audit_path),'original515_error_retained':True},replace=True,limit=16384)
    return result
