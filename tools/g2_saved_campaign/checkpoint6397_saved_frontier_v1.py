"""Finite saved-frontier projection for actual direct SAVE6397, not a launcher.

Only bounded immutable JSON is read. Current facts come from the pre-recovery
3039 snapshot, its completed read-only recovery and the actual SAVE receipt.
The later interrupted branch is historical; its missing AUTO reply stays unknown.
"""
import copy
import hashlib
import json
from pathlib import Path

MACHINE='xenoamess-full-tower-eb9d2c1186'
ACTOR=40526
EPISODE='native-40526-1bec95182886'
SAVE_SHA='417b06a63310cf3c59544394024b387a3fc2700dced3c08b42aa5980bfeb27cb'
PINS={
 'frontier':(4785,'bca6c74e62d01361882caa27e300ed3ec02c2d4126f7a2b1748e2a899ad1142a'),
 'historical_tail':(36135,'0f6acfccdbb27fcc999bd91148cddc5c9196edd9f503dadd9d9cca426a0b68a8'),
 'interruption':(13369,'e84e889772141a8b3e31bc1d5b9b27577eb830860429c2d8f48403339389d8bd'),
 'original_frozen_state_before6394':(7107,'3a45d3e8f165bf4f810af016d04656053c7f85e33da50dadfdc6c495af0acd26'),
 'original_frozen_governance_before6394':(881,'d395e573697ad83c3d17ce61951cd6d83c3dc56ef3d4e6fe9085e16b38d44bac'),
 'CUM3039':(2160,'9d39705e15090894036f59213deb87837b3cb4d5c9f1651298cfeb4256145507'),
 'recovery6394':(982,'33edf387a8ac41b198b08ebf47870243f033ecda1d97faae10b2cc47bb82cc9e'),
 'semantic6395':(69093,'17d79361820151b5ad9104721d2ade5967044f3903ddd5726e304083833c36c7'),
 'PLAN6396':(43372,'a05eb4b9d24ee8c6d5e1dbecc736748a8d476cd211bc31c102b6d253a854ea0a'),
 'SAVE6397':(10230,'88d315c10bc409db658d331a5ddad5eec81abc4f0b6e0bc0d76697b32d5c6da8'),
}

def require(ok,message):
    if not ok:raise ValueError('SAVE6397 frontier denied: '+message)

def exact(ref,key):
    expected=PINS[key]
    require((ref.get('bytes'),ref.get('sha256'))==expected,'finite '+key+' pin differs')
    with Path(ref['path']).open('rb') as f:raw=f.read(262145)
    require(len(raw)==expected[0] and hashlib.sha256(raw).hexdigest()==expected[1],key+' source changed')
    return json.loads(raw)

def completed(row,sequence,tool):
    require(row.get('client_error') is None and row['request']['sequence']==sequence
        and row['request'].get('tool')==tool and row['result'].get('is_error') is False,'original tool/result differs')
    return row['result']['structured_content']

def project_saved_frontier(admission,*,checkpoint_saved):
    """Return a source reconstruction; never assert an original SAVE-time snapshot."""
    require(admission.get('machine_id')==MACHINE,'machine differs')
    frontier=exact(admission['frontier'],'frontier')
    tail=exact(admission['historical_tail'],'historical_tail')
    ended=exact(admission['interruption'],'interruption')
    refs={**frontier['sources'],**admission.get('relocated_sources',{})}
    # Content pins are fixed; an explicit archived copy of CUM3039 is supported
    # from the outset. No current queue path is required after queue archival.
    require(set(admission.get('relocated_sources',{}))<= {'CUM3039'},'unexpected relocation')
    values={k:exact(refs[k],k) for k in frontier['sources']}
    old=values['original_frozen_state_before6394'];gov=values['original_frozen_governance_before6394']
    turn=values['CUM3039'];recovery=values['recovery6394']
    require(recovery['request']=={'sequence':6394,'command':'recover_partial_life_advance','arguments':{
        'recovery_kind':'ordinary_campaign_succession','recovery_mode':'readonly_planning_precondition'}}
        and recovery['result']['is_error'] is False,'read-only recovery identity differs')
    r=recovery['result']['structured_content']
    expected={'status':'readonly_planning_precondition_recovered','completed_cycles':3039,
        'failed_pending_business_credit':0,'original_auto_replayed':False,'new_auto_admitted':True,
        'succession_performed':False,'gameplay_actions_submitted':0,'fresh_readonly_calls':1,'actual_paused':True,
        'observed_date_raw':53202720,'observed_actor_character_id':ACTOR}
    require(all(r.get(k)==v for k,v in expected.items()),'actual recovery did not verify zero-credit boundary')
    sem=completed(values['semantic6395'],6395,'ck3_take_semantic_snapshot_private_v1')
    completed(values['PLAN6396'],6396,'ck3_plan_turn')
    saved=completed(values['SAVE6397'],6397,'ck3_save_checkpoint');cp=saved['checkpoint']
    current={k:sem[k] for k in ('snapshot_id','revision','native_revision','date_raw','episode_run_id')}
    current['actor_character_id']=sem['played_character']['character_id']
    require(current==old['before']==turn['after']==frontier['settled_frame_before_recovery']
        and sem['paused'] is True and sem['map_ready'] is True and sem['played_character']['alive'] is True
        and sem['diagnostics']['bridge_pid']==115472 and current['actor_character_id']==ACTOR
        and current['episode_run_id']==EPISODE and current['date_raw']==53202720
        and values['SAVE6397']['request']['arguments']=={'expected_revision':sem['revision']},'saved semantic frame differs')
    require(cp==frontier['checkpoint'] and cp['status']=='saved' and cp['sha256']==SAVE_SHA
        and cp['size']==95619534 and cp['history_index']==2083 and cp['date_raw']==53202720
        and cp['episode_character_id']==ACTOR and cp['episode_run_id']==EPISODE,'actual new checkpoint differs')
    replace=saved['driver_state_replace_receipt']
    require(replace['save_binding_verified'] is True and replace['write_replace_returned'] is True
        and replace['save_history_index']==replace['encoded_history_rows']==2083
        and replace['attempt_binding']['bridge_pid']==115472 and replace['checkpoint']==cp,
        'canonical SAVE/Driver receipt is incomplete')
    require(old['completed_cycles']==gov['completed_cycles']==turn['global_turn']==3039
        and old['start_date_raw']==53144328 and old['counts']==turn['cumulative_observation_counts']
        ==frontier['counts_at_last_settlement_before_direct_SAVE6397']
        and old['counts']['checkpoint_saved']==35 and frontier['direct_SAVE6397_was_counted_by_loop_cadence'] is False
        and old['pending_cycle']['auto_sequence']==6393 and old['pending_cycle']['global_turn']==3040
        and all(old.get(k) is None for k in ('pending_checkpoint','terminal','pending_natural_succession','pending_unsafe_route_halt')),
        'original 3039 state/counts differ')
    require(gov['state']=={'council_pending':None,'construction_actions':{},'prisoner_release_pending':None}
        and gov['pending_cycle']==old['pending_cycle'] and gov['pending_focus'] is None,'saved governance obligation differs')
    require(frontier['machine_id']==tail['machine_id']==ended['machine_id']==MACHINE
        and [row[0] for row in tail['rows']]==list(range(3040,3274))
        and sum(row[4] for row in tail['rows'])==71*24
        and tail['rows'][-1][3]==ended['last_observed_date_raw']==53204424
        and ended['last_observed_cycles']==3273 and ended['pending_unknown_AUTO']==6874
        and tail['unsettled_pending_global_turn']==3274 and tail['unsettled_unknown_AUTO6874_replayed'] is False,
        'complete interrupted historical tail differs')
    seed=copy.deepcopy(old)
    seed.update(before=current,before_metrics_response=refs['semantic6395']['path'],pending_cycle=None,
        before_source_kind='actual_semantic6395_before_direct_SAVE6397',actual_saved_checkpoint=copy.deepcopy(cp),
        actual_saved_checkpoint_source={'global_turn':3039,'semantic_response':refs['semantic6395']['path'],'save_response':refs['SAVE6397']['path']})
    seed['readonly_planning_precondition_recovery_last']={'audit':r['audit'],'failed_pending_business_credit':0,'original_auto_replayed':False}
    seed['checkpoint_calendar_v1']={'last_saved_date_raw':53202720,'actor_character_id':ACTOR,'episode_run_id':EPISODE,'war_ids':None}
    checkpoint_saved(seed,cp)
    seed.pop('checkpoint_last_decision',None)
    seed['checkpoint6397_rollback']={'machine_id':MACHINE,'source_frontier':admission['frontier'],
        'historical_tail':admission['historical_tail'],'saved_cycles':3039,'saved_date_raw':53202720,
        'historical_later_cycles':3273,'historical_later_date_raw':53204424,'rolled_back_cycles':234,'rolled_back_game_days':71,
        'unknown_original_AUTO':6874,'unknown_original_replayed':False,'old_full_snapshot_claimed':False,
        'original_history_truncated':False,'new_cycle_credit':0,'loop_checkpoint_saved_count_preserved':35,
        'direct_maintenance_SAVE6397_adopted':True}
    projected=copy.deepcopy(gov);projected['pending_cycle']=None
    return seed,projected

def validate_rollback(admission,seed,governance,*,checkpoint_saved):
    expected=project_saved_frontier(admission,checkpoint_saved=checkpoint_saved)
    require((seed,governance)==expected,'seed/governance differ from exact source reconstruction')

def validate_abnormal_closure(admission):
    ended=exact(admission['interruption'],'interruption')
    expected={'Game':(115472,134368932806525787),'SDKQueue':(188716,134368947981891115),'SDKApp':(15156,134368948030748335)}
    for role,(pid,birth) in expected.items():
        item=next(v for v in ended['kernel_exit_times'] if v['role']==role)
        require(item['pid']==pid and item['creation_filetime']==item['expected_creation_filetime']==birth
            and item['exact_birth_matches'] is True and item['wait_result']==0 and item['exit_code']==1,
            'exact interrupted '+role+' exit is missing')
    return {'status':'EXACT_C15_INTERRUPTED_KERNEL_EXITS_SOURCE_BOUND','normal_Game_or_SDK_exit':False,
        'Job_or_user_abort_cause_proven':False,'publisher_child_numeric_exit_code':None,
        'replay_unknown_AUTO6874':False,'durable_new_owner_admitted':False}
