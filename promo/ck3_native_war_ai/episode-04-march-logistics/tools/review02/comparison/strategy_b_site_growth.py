"""Offline B rest-site semantics over original normal-day endpoint/clock pins.

Requires event-time before/after.province_id plus original endpoint/DATA/clock
chains. Older events with unknown Province cannot receive site credit.
No SDK, action, provider or native mutation; deployment and live readiness are separate.
"""
from pathlib import Path
import argparse,json,sys

def need(ok,why):
    if not ok:raise ValueError(why)

def relative(e,ref):
    p=Path(ref['path']);p=p.resolve()if p.is_absolute()else(e.root/p).resolve()
    need(p.is_relative_to(e.root),'site original escapes Evidence.root')
    out={'path':p.relative_to(e.root).as_posix(),'bytes':ref['bytes'],'sha256':ref['sha256']}
    e.raw(out);return out

def signature(view,aid):
    row=view['rows'][aid]
    fields=('record_index','persistent_regiment_id','chunk_index','maximum_soldiers','chunk_army_regiment_id')
    need(all(all(type(r.get(k))is int for k in fields)for x in row['regiment_replenishment_records_v1']for r in x['records']),'unknown DATA identity/max/backlink')
    return (view['native'][aid],view['endpoint']['commander_id'],
        [(x['army_regiment_id'],x['maximum_soldiers'])for x in row['regiment_strengths']],
        [(x['army_regiment_id'],x['native_data_record_count'],
          [tuple(r[k]for k in ('record_index','persistent_regiment_id','chunk_index','maximum_soldiers','chunk_army_regiment_id'))for r in x['records']])
         for x in row['regiment_replenishment_records_v1']])

def qualify_site(e,ref,b):
    c=b.c;ref=relative(e,ref);sample=e.json(ref)
    need(sample.get('schema')=='xar.e04.B-rest-site-input.v1','actual site-input adapter schema required')
    p,aid=sample.get('province_id'),sample.get('army_id')
    need(type(p)is int and p>0 and type(aid)is int and 0<=aid<2**31,'actual Province/public Army required')
    rt=e.json(relative(e,sample['runtime']));c.schema_check(rt,'runtime');e.all_pins(rt)
    chain=[];cursor=sample['normal_day'];seen=set();fixed=None
    while cursor is not None:
        cp=relative(e,cursor);key=(cp['path'],cp['sha256']);need(key not in seen and len(chain)<90,'normal-day chain cycle/exceeds90')
        seen.add(key);row=e.json(cp)
        need(row.get('qualified')is True and row.get('machine_id')==rt['machine_id']and row.get('source_head')==rt['source_head'],'unqualified/foreign normal day')
        ident=(row['binding'],row['plan'],row['helper'])
        if fixed is None:fixed=ident
        need(ident==fixed,'normal day source/helper/runtime chain changed')
        expected={'pid':rt['pid'],'process_create_time_100ns':rt['process_create_time_100ns'],
            'generation':rt['connection_generation'],'actor':rt['player_character_id'],'episode':rt['episode']}
        need(all(row['binding'].get(k)==v for k,v in expected.items()),'normal-day process lifetime differs')
        claim=e.json(relative(e,row['claim']))
        need(all(claim.get(k)==row.get(k)for k in ('machine_id','source_head','binding','plan','helper')),'claim original machine/source/helper differs')
        need(claim['before']==row['before']and claim['previous_complete']==row['previous_complete']
             and claim['start']+24==claim['target'],'normal-day original claim differs')
        chain.append((cp,row));cursor=row['previous_complete']
    need(chain,'normal-day original required');chain.reverse();plan=e.json(relative(e,fixed[1]))
    need(plan['build']['version']=='1.20.0.4'and plan['build']['source_head']==rt['source_head']
         and plan['build']['native_dll_sha256']==rt['native_dll_sha256'],'sampling plan actual build differs')
    days=[x[1]['day']for x in chain];c.clock_days({'runtime':rt,'days':days},plan,e)
    for n,(_,row)in enumerate(chain,1):
        need(row['before']['day']==n-1 and row['after']['day']==n and row['day']['paused_snapshot']==row['after']['snapshot'],'normal-day endpoint sequence differs')
        if n>1:need(c.endpoint(chain[n-2][1]['after'],plan,e,rt)==c.endpoint(row['before'],plan,e,rt),'normal-day independent observable endpoint chain gap')
    cp,last=chain[-1];before=b.observe(last['before'],plan,e,rt);after=b.observe(last['after'],plan,e,rt)
    b._frame_order(before,after);b._stationary(before,[aid],p);b._stationary(after,[aid],p)
    need(after['snapshot']['date_raw']==before['snapshot']['date_raw']+24 and signature(before,aid)==signature(after,aid),'rest day/cohort/DATA/commander/native identity changed')
    old,new=before['rows'][aid],after['rows'][aid]
    stock0,stock1=old['current_supply_raw'],new['current_supply_raw'];delta=stock1-stock0
    need(delta>0 and 0<=stock0<stock1<=new['current_supply_capacity_raw'],'no actual positive site stock delta; monthly rate/gain/zero is insufficient')
    f0,f1=old.get('actual_supply_callback_observations_v1'),new.get('actual_supply_callback_observations_v1')
    need(type(f0)is dict and type(f1)is dict,'actual callback original absent')
    from xar_autoplayer.bridge.army_actual_supply_callback_observations_contract import normalize_actual_supply_callback_observations_v1 as normalize
    # Production strict parser preserves optional event-time Province values.
    oldf=normalize(f0,current_army_id=aid,current_native_carmy_id=after['native'][aid])
    newf=normalize(f1,current_army_id=aid,current_native_carmy_id=after['native'][aid])
    need(oldf['observer_installed']and newf['observer_installed']and newf['unattributed_capture_failures']==oldf['unattributed_capture_failures'],'actual callback observer/capture failed')
    fence=oldf['latest_sequence'];need(newf['oldest_available_sequence']<=fence+1,'retained callback gap after exact before fence')
    packed=(new.get('source_derived_next_daily_supply_frame_inputs_v1')or{}).get('current_date_storage_raw64')
    need(type(packed)is int and packed>=0,'actual current complete CDate64 wire required; no raw*constant reconstruction')
    events=[x for x in newf['events']if x['sequence']>fence]
    need(events,'no new natural callback; empty is unknown')
    seqs=[x['sequence']for x in events];need(seqs==sorted(set(seqs))and seqs[-1]<=newf['latest_sequence'],'callback sequence duplicate/unordered/outside journal')
    previous=stock0;positive=[]
    for event in events:
        need(event['same_instance_after']is True and event['capture_failure_flags']==0 and event['passed_date_raw64']==packed,'callback identity/date/capture differs')
        need(event['before']['supply_raw']==previous and type(event['after']['supply_raw'])is int,'callback stock chain gap/unknown')
        need(all(type(event[side].get('province_id'))is int
             and event[side]['province_id']==p for side in ('before','after')),
             'callback actual Province absent/changed; endpoint location cannot attribute history')
        value=event['after']['supply_raw']-previous
        if value>0:positive.append(event['sequence'])
        previous=event['after']['supply_raw']
    need(previous==stock1 and positive,'actual callback after does not reconcile positive endpoint stock')
    return {'province_id':p,'army_id':aid,'native_carmy_id':after['native'][aid],
        'runtime':rt,'source':ref,'normal_day':cp,'before':last['before'],'after':last['after'],
        'stock_before_raw':stock0,'stock_after_raw':stock1,'actual_stock_delta_raw':delta,'scale':100000,
        'positive_callback_sequences':positive,'site_growth_semantically_qualified':True,
        'future_safety_guaranteed':False,'actual_soldier_ADD_or_loss_qualified':False}

def qualify_plan_sites(plan,e,b):
    bp=plan['strategies']['B'];ids=bp['rest_province_ids'];refs=bp['site_actual_stock_increase_evidence']
    need(type(ids)is list and len(ids)==2 and len(set(ids))==2 and len(refs)==2,'two distinct actual B rest Provinces and inputs required')
    sites=[qualify_site(e,ref,b)for ref in refs]
    need([x['province_id']for x in sites]==ids,'site originals do not match frozen B rest order')
    actor=b.c.frame(e.json(plan['baseline']['snapshot']))['played_character']['character_id']
    need(all(x['runtime']['player_character_id']==actor for x in sites),'site samples belong to another played owner')
    keys=[(x['runtime']['machine_id'],x['runtime']['pid'],x['runtime']['process_create_time_100ns'],
        x['runtime']['episode'],x['native_carmy_id'],q)for x in sites for q in x['positive_callback_sequences']]
    need(len(keys)==len(set(keys)),'same actual callback reused for two sites')
    return {'schema':'xar.e04.B-two-rest-sites-qualified.v1','site_growth_semantically_qualified':True,'sites':sites,
        'formal_ABC_completed_arms':0,'B_live_readiness_granted':False,'source_truth_or_native_deployment_granted':False}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',type=Path,required=True)
    p.add_argument('--evidence-root',type=Path,required=True);p.add_argument('--plan',type=Path,required=True)
    p.add_argument('--plan-sha256',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    root=a.repo/'promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison'
    sys.path[:0]=[str(root),str(a.repo/'ck3_autonomous_player/src')]
    import r10_compare as c,strategy_b as b
    raw=a.plan.read_bytes();need(c.digest(raw)==a.plan_sha256,'actual plan SHA differs')
    result=qualify_plan_sites(c.parse(raw),c.Evidence(a.evidence_root),b)
    with a.output.open('x',encoding='utf-8')as f:json.dump(result,f,indent=2);f.write('\n')
if __name__=='__main__':main()
