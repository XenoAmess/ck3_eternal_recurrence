"""Verify the portable R0172 periodic-loss evidence with Python's standard library.

This confirms bytes, joins, cohorts and arithmetic, not a native applied-loss ledger.
"""
from pathlib import Path
import hashlib
import json
import sys

def require(condition, message):
    if not condition:
        raise ValueError(message)

def load(path):
    return json.loads(path.read_bytes())


def verify_neutral_boundaries(base):
    specifications=(('boarding',53148096,53148144,1506,725,[725,1009,2174],[1009,2174]),
                    ('landing',53148384,53148432,1009,2174,[2174],[]))
    for name,raw0,raw1,p0,p1,route0,route1 in specifications:
        frames=[]
        for phase in ('before','after'):
            b=load(base/'boundaries'/name/phase/'strength.json')
            s=load(base/'boundaries'/name/phase/'after.json')
            r=next(x for x in b['army_strengths'] if x['army_id']==0)
            a=next(x for x in s['player_armies'] if x['army_id']==0)
            for key in ('snapshot_id','revision','native_revision','date_raw','paused'):
                require(b['source'][key]==s[key],'Neutral endpoint join')
            require(s['paused'] is True and s['episode_run_id']=='native-33388-a329bf767116','Neutral episode/paused')
            require(r['status']=='available' and r['native_carmy_id']==0,'Neutral Main0 resolution')
            require(r['current_soldiers']==6679 and r['maximum_soldiers']==6747,'Neutral quantities')
            require(r['current_supply_raw']==11037716 and r['army_update_clock_v1']['last_supply_update_date_raw']==53147760,'Neutral supply/stamp')
            rec=[((c['army_regiment_id'],v['record_index'],v['persistent_regiment_id'],v['chunk_index']),v)
                 for c in r['regiment_replenishment_records_v1'] for v in c['records']]
            require(len(r['regiment_strengths'])==27 and len(rec)==37,'Neutral27/37')
            frames.append((s,r,a,rec))
        s0,r0,a0,z0=frames[0];s1,r1,a1,z1=frames[1]
        require((s0['date_raw'],s1['date_raw'])==(raw0,raw1),'Neutral exact interval')
        require((a0['current_province_id'],a1['current_province_id'])==(p0,p1),'Neutral provinces')
        require(a0['route_province_ids']==route0 and a1['route_province_ids']==route1,'Neutral routes')
        require(r0['regiment_strengths']==r1['regiment_strengths'],'Neutral actual rows')
        require([k for k,v in z0]==[k for k,v in z1],'Neutral DATA cohorts')
        d1=dict(z1)
        require(all(v[k]==d1[i][k] for i,v in z0 for k in ('current_soldiers','maximum_soldiers','effective_current_soldiers')),'Neutral DATA integers')
        if name=='landing':
            require(sum(v['native_chunk_can_replenish'] is True for i,v in z0)==0,'Before landing chunk permission')
            require(sum(v['native_chunk_can_replenish'] is True for i,v in z1)==18,'After landing chunk permission')
            require(r1['county_entry_inputs_v1']['condition']['passes'] is None,'After landing absent route predicate is null')
    savepin=load(base/'source'/'arrival-actual-checkpoint-pin.json')
    result=load(base/'source'/'arrival-checkpoint-result.json')
    require(savepin['bytes']==73795635 and savepin['sha256']=='d052a2e412109a28247b8844567100a272998c536711d75f0fbc29ee6a286f6a','Existing save proof pin')
    require(result['proof']['date_raw']==53148432 and result['preserved_actual_checkpoint']==savepin,'Existing save proof join')
    closure=load(base/'source'/'r0172-bootstrap-result.json')
    require(closure['sdk_thread_exited'] is True and closure['sdk_error'] is None and closure['supervisor_error'] is None,'SDK closure receipt')
    require(closure['screen_lease']['thread_exited'] is True and closure['screen_lease']['failure'] is None,'Lease keeper closure receipt')
    require(closure['session']['shutdown']['tree_gone'] is True and closure['session']['shutdown']['job_active_processes_final']==0,'Actual process tree closure receipt')
    require(closure['recorder']['state']=='NORMAL_TREE_EMPTY','Recorder receipt')
    require(closure['human_video_approval'] is False,'No invented video signoff')

def main():
    base=Path(__file__).resolve().parent
    index=load(base/'index.json')
    require(index['schema']=='r0172-periodic-loss-evidence-v1','Unknown evidence schema')
    for item in index['inputs']:
        name=Path(item['relative_path'])
        require(not name.is_absolute() and '..' not in name.parts,'Nonportable input path')
        data=(base/name).read_bytes()
        require(len(data)==item['size_bytes'],'Input size mismatch: '+str(name))
        require(hashlib.sha256(data).hexdigest()==item['sha256'],'Input hash mismatch: '+str(name))
    frames=[]
    for name in ('before','after'):
        body=load(base/'raw'/name/'strength.json')
        snap=load(base/'raw'/name/'after.json')
        for key in ('snapshot_id','revision','native_revision','date_raw','paused'):
            require(body['source'][key]==snap[key],'Paused endpoint join: '+key)
        require(snap['paused'] is True,'Endpoint must be paused')
        require(snap['episode_run_id']=='native-33388-a329bf767116','Wrong R0172 episode')
        require(snap['played_character']['character_id']==33388,'Wrong played actor')
        require(snap['active_event'] is None and snap['pending_character_interaction'] is None,'Endpoint event/interaction changed')
        row=next(x for x in body['army_strengths'] if x['army_id']==0)
        army=next(x for x in snap['player_armies'] if x['army_id']==0)
        require(row['status']=='available' and row['native_carmy_id']==0,'Wrong or unavailable Main0')
        require(row['maximum_soldiers']==6747,'Maximum changed')
        require(len(row['regiment_strengths'])==27,'Actual regiment count')
        require(sum(x['current_soldiers'] for x in row['regiment_strengths'])==row['current_soldiers'],'Actual sum')
        require(army['current_province_id']==1506 and army['route_province_ids']==[725,1009,2174],'Route/current province changed')
        require(army['in_combat'] is False and army['retreating'] is False,'Endpoint combat/retreat changed')
        require(army['army_state']=='sieging' and army['owner_character_id']==33388,'Army state/owner')
        require(row['gathering_days_status']=='not_gathering' and row['gathering_days_ready'] is True,'Gathering status')
        clock=row['army_update_clock_v1']
        require(clock['ready'] is True and clock['observed_army_bucket_phase']==0,'Actual clock unavailable/wrong bucket')
        require(clock['current_date_raw']==snap['date_raw'],'Clock source date')
        county=row['county_entry_inputs_v1']
        require(county['status']=='available' and county['effective_fraction_raw']==3500,'County fraction availability')
        require(county['minimum_multiplier_raw']==70000 and county['loaded_minimum_soldiers']==5,'County minimum inputs')
        condition=county['condition']
        require(condition['status']=='available' and condition['passes'] is False,'First edge predicate must be observed false')
        require((condition['actor_character_id'],condition['source_province_id'],condition['target_province_id'],condition['mode'])==(33388,1506,725,1),'Predicate tuple')
        records=[]
        for c in row['regiment_replenishment_records_v1']:
            require(c['status']=='available' and c['ready'] is True,'DATA container not complete')
            require(c['native_data_record_count']==len(c['records']),'DATA count changed')
            for v in c['records']:
                require(v['status']=='available','Unreadable DATA')
                records.append(((c['army_regiment_id'],v['record_index'],v['persistent_regiment_id'],v['chunk_index']),v))
        require(len(records)==37 and len({k for k,v in records})==37,'DATA identity count')
        require(sum(v['native_chunk_can_replenish'] is True for k,v in records)==0,'Endpoint chunk permission changed')
        require(sum(v['native_can_replenish'] is True for k,v in records)==22,'Persistent permission changed')
        require(sum(v['persistent_prepared_replenishment_fraction_raw']!=0 for k,v in records)==22,'Prepared fractions changed')
        require(sum(v['current_soldiers'] for k,v in records)==row['current_soldiers']-5,'Stable DATA-to-actual difference')
        frames.append((body,snap,row,army,records))
    b0,s0,r0,a0,records0=frames[0]
    b1,s1,r1,a1,records1=frames[1]
    require(s0['date_raw']==53147736 and s1['date_raw']==53147784,'Exact interval changed')
    require(s0['native_revision']==39 and s1['native_revision']==44,'Native endpoint revisions changed')
    require(r0['current_soldiers']==6746 and r1['current_soldiers']==6679,'Exact net integer loss changed')
    require((r0['current_supply_raw'],r1['current_supply_raw'])==(11651751,11037716),'Supply stock changed')
    require((r0['current_supply_change_monthly_raw'],r1['current_supply_change_monthly_raw'])==(-877192,-614035),'Getter value changed')
    c0,c1=r0['army_update_clock_v1'],r1['army_update_clock_v1']
    require(c0['last_supply_update_date_raw']==53147040 and c1['last_supply_update_date_raw']==53147760,'Success stamp changed')
    require(c0['grace_anchor_date_storage_raw64']==c1['grace_anchor_date_storage_raw64'],'Grace anchor changed')
    require(c0['native_day_index']==389489 and c1['native_day_index']==389491,'Native day index')
    require(c0['selected_bucket_phase']==29 and c1['selected_bucket_phase']==1,'Conditional bucket crossing')
    require([k for k,v in records0]==[k for k,v in records1],'DATA cohort/order changed')
    z0,z1=dict(records0),dict(records1)
    require([v['army_regiment_id'] for v in r0['regiment_strengths']]==[v['army_regiment_id'] for v in r1['regiment_strengths']],'Actual cohort/order changed')
    reg1={v['army_regiment_id']:v for v in r1['regiment_strengths']}
    ledger=r0['loss_application_inputs_v1']
    require(ledger['status']=='available' and ledger['current_supply_loss_budget']==0 and ledger['siege_loss_budget']==67 and ledger['raid_loss_budget']==0,'Before budgets changed')
    require(ledger['definition_le_zero_soldiers']==6677 and ledger['siege_active'] is True,'Aggregate eligibility/association changed')
    require(r1['loss_application_inputs_v1']['siege_loss_budget']==66,'After hypothetical siege budget')
    require(r0['county_entry_inputs_v1']['current_loss_budget']==236 and r1['county_entry_inputs_v1']['current_loss_budget']==233,'County budgets')
    remaining,denom=67,6677
    predicted={k:v['current_soldiers'] for k,v in records0}
    changed_reg=0
    for reg in r0['regiment_strengths']:
        army_reg=reg['army_regiment_id']
        require(reg['maximum_soldiers']==reg1[army_reg]['maximum_soldiers'],'Actual max changed')
        positive=reg['siege_tier_observable'] and reg['siege_tier']>0
        allocated=0 if positive or denom<=0 else reg['current_soldiers']*remaining//denom
        if not positive:
            remaining-=allocated
            denom-=reg['current_soldiers']
        observed=reg['current_soldiers']-reg1[army_reg]['current_soldiers']
        require(allocated==observed,'Conditional ordered regiment replay mismatch')
        changed_reg+=observed!=0
        chunk_remaining=allocated
        for identity,v in records0:
            if identity[0]!=army_reg:continue
            require(v['state_raw'] in (0,1),'Outside ordinary bounded writer')
            chunk_loss=min(chunk_remaining,v['current_soldiers'])
            predicted[identity]-=chunk_loss
            chunk_remaining-=chunk_loss
    require(remaining==0 and denom==0 and changed_reg==16,'Ordered allocation remainder')
    changed_data=0
    for k,v in records0:
        require(predicted[k]==z1[k]['current_soldiers'],'Conditional DATA writer replay mismatch')
        for field,value in v.items():
            if field not in ('current_soldiers','effective_current_soldiers'):
                require(value==z1[k][field],'Non-count DATA field changed: '+field)
        require(z1[k]['effective_current_soldiers']==z1[k]['current_soldiers'],'Effective/ordinary count')
        changed_data+=v['current_soldiers']!=z1[k]['current_soldiers']
    require(changed_data==17,'Changed DATA count')
    verify_neutral_boundaries(base)
    print(json.dumps({'status':'verified_bytes_joins_cohorts_and_conditional_arithmetic','indexed_input_count':len(index['inputs']),
                      'army_regiments':27,'data_records':37,'net_integer_loss':67,
                      'all_regiment_and_data_replay_match':True,
                      'applied_loss_ledger_available':False,'zero_hidden_refill_proved':False,
                      'death_count_proved':False,'starvation_proved':False},ensure_ascii=False))

if __name__=='__main__':
    try:main()
    except (OSError,ValueError,KeyError,StopIteration,TypeError) as e:
        print('R0172 evidence verification failed: '+str(e),file=sys.stderr)
        raise SystemExit(1)
