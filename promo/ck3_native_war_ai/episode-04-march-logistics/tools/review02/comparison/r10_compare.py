"""Finite offline R10 comparison of existing paired snapshots/Driver JSON.

No SDK, media, raw save, process, network or gameplay access. Requires jsonschema.
Pins bind supplied small evidence bytes, not their authenticity or causal truth.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from collections import OrderedDict
from jsonschema import Draft202012Validator

EXE='98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518'
MAX_FILE=16*1024*1024

def need(ok,message):
    if not ok:raise ValueError(message)

def integer(x):return type(x) is int

def parse(raw):
    def pairs(items):
        out={}
        for k,v in items:
            need(k not in out,'duplicate JSON key: '+k);out[k]=v
        return out
    return json.loads(raw.decode('utf-8-sig'),object_pairs_hook=pairs,parse_constant=lambda s:(_ for _ in ()).throw(ValueError('non-finite JSON '+s)))

def digest(raw):return hashlib.sha256(raw).hexdigest()

def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False)

def schema_check(value,kind):
    schema=parse(Path(__file__).with_name('r10.schema.json').read_bytes())
    Draft202012Validator.check_schema(schema)
    selected={**schema,'oneOf':[{'$ref':'#/$defs/'+kind}]}
    errors=sorted(Draft202012Validator(selected).iter_errors(value),key=lambda e:str(list(e.path)))
    if errors:
        e=errors[0]
        detail='; '.join('/'.join(map(str,x.absolute_path))+': '+x.message for x in e.context[:8])
        raise ValueError('schema '+kind+': '+(detail or e.message))

class Evidence:
    def __init__(self,root):self.root=Path(root).resolve();self.cache=OrderedDict();self.cache_bytes=0
    def raw(self,pin):
        path=Path(pin['path'])
        need(not path.is_absolute() and ':' not in str(path),'evidence paths must be package-relative, not historical machine locators')
        need(path.suffix.lower() in {'.json','.md','.txt','.csv','.jsonl','.asm','.py','.cpp','.h','.hpp'},'evidence must be small text; media/save/EXE/DLL/binary pins are not opened')
        full=(self.root/path).resolve()
        need(full.is_relative_to(self.root),'evidence path escapes root')
        key=(str(full),pin['bytes'],pin['sha256'])
        if key not in self.cache:
            need(full.is_file() and full.stat().st_size==pin['bytes'] and pin['bytes']<=MAX_FILE,'evidence missing/size/16MiB limit: '+str(path))
            raw=full.read_bytes();need(len(raw)==pin['bytes'] and digest(raw)==pin['sha256'],'evidence SHA mismatch: '+str(path))
            while self.cache and self.cache_bytes+len(raw)>32*1024*1024:
                _,old=self.cache.popitem(last=False);self.cache_bytes-=len(old)
            self.cache[key]=raw;self.cache_bytes+=len(raw)
        else:self.cache.move_to_end(key)
        return self.cache[key]
    def json(self,pin):return parse(self.raw(pin))
    def bound(self,binding):
        node=self.json(binding['source']);pointer=binding['pointer']
        if pointer:
            for token in pointer[1:].split('/'):
                token=token.replace('~1','/').replace('~0','~')
                node=node[int(token)] if isinstance(node,list) else node[token]
        return node
    def all_pins(self,node):
        if isinstance(node,dict):
            if set(node)=={'path','bytes','sha256'}:self.raw(node)
            else:
                for x in node.values():self.all_pins(x)
        elif isinstance(node,list):
            for x in node:self.all_pins(x)

def body(value):
    need(isinstance(value,dict),'evidence must be object')
    need(value.get('is_error') is not True,'source SDK response is_error')
    return value['body'] if isinstance(value.get('body'),dict) else value

def frame(value,runtime=None):
    b=body(value);d=b.get('diagnostics') or {};h=d.get('hello') or {}
    need(b.get('paused') is True and b.get('map_ready') is True,'snapshot is not actual paused map')
    actor=b.get('played_character') or {}
    need(actor.get('alive') is True and integer(actor.get('character_id')),'missing living player')
    need(h.get('expected_ck3_version')=='1.20.0.4' and str(h.get('expected_ck3_sha256','')).lower()==EXE,'snapshot exact build mismatch')
    need(integer(b.get('date_raw')) and integer(b.get('revision')) and integer(b.get('native_revision')),'snapshot missing integer frame')
    if runtime:
        need(d.get('bridge_pid')==runtime['pid'] and d.get('connection_generation')==runtime['connection_generation'] and b.get('episode_run_id')==runtime['episode'] and actor['character_id']==runtime['player_character_id'],'snapshot runtime/player mismatch')
        if 'machine_id' in value:need(value['machine_id']==runtime['machine_id'],'snapshot machine mismatch')
    return b

def endpoint(ep,plan,evidence,runtime=None):
    b=frame(evidence.json(ep['snapshot']),runtime)
    need(b['date_raw']==plan['t0_raw']+24*ep['day'],'endpoint natural day/raw mismatch')
    q=body(evidence.json(ep['army_result']))
    need(q.get('accepted') is True and isinstance(q.get('army_strengths'),list),'not a complete Driver Army result; summary/partial rejected')
    for qk,bk in [('queried_snapshot_id','snapshot_id'),('queried_revision','revision'),('queried_native_revision','native_revision'),('queried_date_raw','date_raw'),('queried_episode_run_id','episode_run_id')]:
        need(q.get(qk)==b.get(bk),'Army result/snapshot frame differs: '+qk)
    need(q.get('queried_connection_generation')==(b.get('diagnostics') or {}).get('connection_generation'),'Army result generation differs')
    wanted=set(ep['strategy_army_ids']);scope=q.get('army_strengths_query_scope')
    if scope is not None:need(scope.get('published_scope_status')=='available' and set(scope.get('army_ids',[]))==wanted,'query scope is partial or differs from strategy scope')
    rows={}
    for a in q['army_strengths']:
        key=a.get('army_id');need(integer(key) and key not in rows,'duplicate/malformed Army row');rows[key]=a
    need(wanted<=set(rows),'missing required strategy Army row')
    positions={a['army_id']:a for a in b.get('player_armies',[])}
    regiments={};units=[];data_projection=[]
    for aid in sorted(wanted):
        a=rows[aid];p=positions.get(aid)
        need(a.get('status')=='available' and p is not None,'Army unavailable/unmapped shadow; cannot fill zero')
        need(p.get('owner_character_id')==b['played_character']['character_id'],'strategy Army owner differs')
        rs=a.get('regiment_strengths');need(isinstance(rs,list) and rs and a.get('regiment_count')==len(rs),'missing complete regiment vector/count')
        total=0;maximum=0
        for r in rs:
            rid=r.get('army_regiment_id');cur=r.get('current_soldiers');cap=r.get('maximum_soldiers')
            need(integer(rid) and rid not in regiments and integer(cur) and integer(cap) and min(cur,cap)>=0 and r.get('scale')==1,'duplicate/unknown/noninteger regiment row')
            regiments[rid]={'army_regiment_id':rid,'current_soldiers':cur,'maximum_soldiers':cap};total+=cur;maximum+=cap
        need(a.get('current_soldiers')==total and a.get('maximum_soldiers')==maximum,'Army total differs from complete integer vector')
        data=a.get('regiment_replenishment_records_v1')
        need(isinstance(data,list) and len(data)==len(rs) and {r.get('army_regiment_id') for r in data}=={r['army_regiment_id'] for r in rs},'missing DATA coverage; absent-first-record is not a zero regiment')
        for r in data:
            need(r.get('status')=='available' and integer(r.get('native_data_record_count')) and isinstance(r.get('records'),list) and len(r['records'])==r['native_data_record_count'],'partial DATA row')
        data_projection.extend(data)
        for key in ('current_supply_raw','current_supply_scale','current_supply_capacity_raw','current_supply_capacity_scale'):
            need(integer(a.get(key)),'unknown supply/capacity, not zero')
        need(a['current_supply_scale']==a['current_supply_capacity_scale']==100000,'unexpected supply scale')
        need(p.get('route_read_status') in ('complete_empty','complete_nonempty') and isinstance(p.get('route_province_ids'),list),'incomplete route')
        units.append({'army_id':aid,'current_soldiers':total,'maximum_soldiers':maximum,'stock_raw':a['current_supply_raw'],'capacity_raw':a['current_supply_capacity_raw'],'scale':100000,'current_province_id':p.get('current_province_id'),'state':p.get('army_state'),'route':p['route_province_ids'],'target':p.get('move_target_province_id')})
    original=set(plan['original_regiment_ids'])
    need(original<=set(regiments),'original cohort missing; unknown/destroyed rows require a separately scoped consumer, never implicit zero')
    gold=b.get('played_character_gold') or {};need(integer(gold.get('raw')) and gold.get('scale')==100000,'wallet raw/scale absent')
    commander=evidence.bound(ep['commander']);need(integer(commander),'typed commander witness is not integer')
    cohort=[regiments[k] for k in sorted(original)]
    return {'day':ep['day'],'date_raw':b['date_raw'],'player_character_id':b['played_character']['character_id'],'war_state':b.get('active_wars',[]),'units':units,'cohort_regiments':cohort,'cohort_current':sum(r['current_soldiers'] for r in cohort),'cohort_maximum':sum(r['maximum_soldiers'] for r in cohort),'all_strategy_current':sum(u['current_soldiers'] for u in units),'all_strategy_maximum':sum(u['maximum_soldiers'] for u in units),'treasury_raw':gold['raw'],'commander_id':commander,'loaded_features':evidence.bound(ep['loaded_features']),'DATA':sorted(data_projection,key=lambda r:r['army_regiment_id'])}

def check_plan(plan,evidence):
    schema_check(plan,'plan');evidence.all_pins(plan)
    frozen=datetime.fromisoformat(plan['frozen_at_utc'].replace('Z','+00:00'))
    need(frozen.tzinfo is not None,'freeze timestamp must have timezone')
    need(plan['baseline']['day']==0,'baseline must be T0/day0')
    need(plan['report_days']==sorted(plan['report_days']),'report days must be sorted')
    need(plan['follow_after_arrival_to_day90']==(plan['post_arrival_policy'] is not None),'D90 continuation needs a frozen post-arrival policy; otherwise no D90 columns')
    if plan['compare_fees']:
        need(plan['prerequisites']['boarding_payment'] is not None and plan['prerequisites']['maintenance_settlement'] is not None,'fee comparison needs R07/R08 actual qualification references')
    base=endpoint(plan['baseline'],plan,evidence)
    need(set(plan['original_regiment_ids'])=={r['army_regiment_id'] for r in base['cohort_regiments']},'baseline cohort differs')
    return base

def arrived(ep,plan):
    return bool(ep['units']) and all(u['current_province_id']==plan['goal_province_id'] and u['state'] in plan['arrival_states'] and u['route']==[] and u['target'] is None for u in ep['units'])

def clock_days(arm,plan,evidence):
    previous_generation=0
    first_arrival=None;scope_by_day={}
    for n,row in enumerate(arm['days'],1):
        need(row['day']==n,'clock days missing/duplicate/noncontiguous')
        original=evidence.json(row['clock_source']);v=body(original)
        c=v.get('clock',v.get('tactical_daily_sentinel'))
        need(isinstance(c,dict),'missing actual native clock status')
        start=plan['t0_raw']+(n-1)*24;end=start+24
        need(c.get('state')=='triggered' and c.get('starting_date_raw')==start and c.get('target_date_raw')==end and c.get('last_observed_date_raw')==end and c.get('trigger_date_raw')==end,'clock actual start/target/end mismatch')
        need(c.get('speed')==5 and c.get('completed_daily_ticks')==1 and c.get('overshoot_days')==0 and c.get('signed_date_delta_from_target_raw')==0 and c.get('abnormal') is False and c.get('pause_observed') is True,'clock tick/pause/overshoot failed')
        need(c.get('mode')=='terminal_or_sentinel' and c.get('army_count')==0 and c.get('combat_count')==0,'clock not date-only terminal-a-0')
        need(integer(c.get('generation')) and c['generation']>previous_generation,'clock lacks distinct increasing actual generation')
        previous_generation=c['generation']
        why=c.get('trigger_reasons')
        if why==['date_deadline']:
            need(c.get('pause_wrapper_called') is True and c.get('intermediate_pause_count')==0,'date deadline pause provenance differs')
        else:
            need(isinstance(why,list) and 'native_pause' in why and c.get('pause_wrapper_called') is False and c.get('intermediate_pause_count')==1,'unexpected stop reason or intermediate pause')
        f=frame(evidence.json(row['paused_snapshot']),arm['runtime']);need(f['date_raw']==end,'clock/independent paused endpoint differs')
        positions={u.get('army_id'):u for u in f.get('player_armies',[])}
        scope_by_day[n]=set(row['strategy_army_ids'])
        need(scope_by_day[n]<=set(positions),'daily strategy Army has no actual map row')
        us=[positions[k] for k in row['strategy_army_ids']]
        need(all(u.get('owner_character_id')==arm['runtime']['player_character_id'] and u.get('route_read_status') in ('complete_empty','complete_nonempty') for u in us),'daily strategy ownership/route incomplete')
        if all(u.get('current_province_id')==plan['goal_province_id'] and u.get('army_state') in plan['arrival_states'] and u.get('route_province_ids')==[] and u.get('move_target_province_id') is None for u in us):
            if first_arrival is None:first_arrival=n
        if 'machine_id' in original:need(original['machine_id']==arm['runtime']['machine_id'],'clock source machine differs')
        for key,expected in [('PID',arm['runtime']['pid']),('episode',arm['runtime']['episode']),('create_filetime',arm['runtime']['process_create_time_100ns'])]:
            if key in original:need(original[key]==expected,'clock source runtime differs: '+key)
    return {'count':len(arm['days']),'first_arrival':first_arrival,'scope_by_day':scope_by_day}

def legacy_rejection(value):
    if value.get('schema')=='ck3.e04.B.closed-gate-terminal.v1':
        return {'accepted_as_R10_result':False,'arm':'B','observed_days':value['days_used'],'remaining_days':value['remaining_days'],'reasons':['old_12003_scope','strategy_gate_stopped_not_arrived','not_a_90_day_deadline_censor','cohort_or_commander_gate_failed'],'source_disposition':value['B_disposition'],'London_endpoint_metrics':value['London_endpoint_metrics'],'winner':None}
    if 'sampling_deviations' in value and 'controlled_comparison_eligibility' in value:
        return {'accepted_as_R10_result':False,'arm':'C','actual_observation_preserved':value['observed_arrival_interval_days'],'reasons':['old_12003_scope','controlled_comparison_NOT_GRANTED','retained_sampling_deviations','arrival_interval_wider_than_one_day'],'sampling_deviation_count':len(value['sampling_deviations']),'source_eligibility':value['controlled_comparison_eligibility'],'winner':None}
    raise ValueError('unrecognized historical small result; no generic success coercion')

def compare(plan,results,evidence):
    base=check_plan(plan,evidence);schema_check(results,'results');evidence.all_pins(results)
    need({a['label'] for a in results['arms']}=={'A','B','C'},'need one independent A/B/C arm each')
    need(len({(a['runtime']['machine_id'],a['runtime']['pid'],a['runtime']['process_create_time_100ns'],a['runtime']['episode']) for a in results['arms']})==3,'three independent normal cold sessions required')
    rows=[];all_obs={};reasons=[];world=[]
    for arm in sorted(results['arms'],key=lambda a:a['label']):
        label=arm['label'];rt=arm['runtime'];ex=arm['execution'];dis=arm['disposition']
        frozen=datetime.fromisoformat(plan['frozen_at_utc'].replace('Z','+00:00'))
        started=datetime.fromisoformat(rt['started_at_utc'].replace('Z','+00:00'))
        need(started.tzinfo is not None and frozen<started,'plan was not frozen before this arm started')
        need(rt['source_head']==plan['build']['source_head'] and rt['native_dll_sha256']==plan['build']['native_dll_sha256'],'arm runtime source/DLL differs')
        need(arm['loaded_save_sha256']==plan['normal_save']['sha256'],'arm normal save SHA differs')
        cold=endpoint(arm['cold_start'],plan,evidence,rt)
        need(cold==base,'cold T0 observable baseline differs: '+label)
        daily=clock_days(arm,plan,evidence);end_days=daily['count']
        need(end_days>=dis['day'] and end_days<=90,'terminal day exceeds actual exact days or horizon')
        need(end_days==dis['day'] or (plan['follow_after_arrival_to_day90'] and dis['kind']=='arrived' and end_days==90),'continuation reset/extra days or unregistered post-arrival continuation')
        obs={0:cold}
        for ep in arm['observations']:
            need(ep['day'] not in obs,'duplicate observed day')
            need(ep['day'] in daily['scope_by_day'] and set(ep['strategy_army_ids'])==daily['scope_by_day'][ep['day']],'endpoint/daily strategy Army scope differs')
            obs[ep['day']]=endpoint(ep,plan,evidence,rt)
        need(max(obs)<=end_days,'observation beyond actual days')
        need(dis['day'] in obs,'terminal actual observation missing')
        for day in plan['report_days']:
            if day<=end_days:need(day in obs,'prespecified common date missing: '+label+'/'+str(day))
        actual=obs[dis['day']];lower=dis['last_not_arrived_day']
        if dis['kind']=='arrived':
            need(daily['first_arrival']==dis['day'],'claimed first arrival differs from daily independent snapshot scan')
            need(integer(lower) and 0<=lower<dis['day'] and dis['day']-lower<=1,'arrival interval must be (last_not,first_arrived] no wider than1day')
            need(lower in obs and not arrived(obs[lower],plan) and arrived(actual,plan),'arrival bracket does not bind actual location/state/route')
            need(all(not arrived(o,plan) for d,o in obs.items() if d<dis['day']),'claimed first arrival follows an earlier arrived observation')
        elif dis['kind']=='budget-censored':
            need(dis['day']==90 and end_days==90 and daily['first_arrival'] is None and not arrived(actual,plan),'only actual day90 nonarrival is a budget censor')
        else:reasons.append(label+': '+dis['kind']+' is not an arrived/deadline result')
        if not ex['prespecified_policy_followed']:reasons.append(label+': prespecified policy failed')
        if label=='B':
            bp=plan['strategies']['B']
            need(ex['B_merge_destination_policy']==bp['merge_destination_policy'] and ex['B_commander_policy']==bp['commander_policy'],'B merge/commander policy changed after seeing outcomes')
            need({r['province_id'] for r in ex['B_rest_exit_records']}==set(bp['rest_province_ids']),'B actual rest exit sites incomplete')
            for rest in ex['B_rest_exit_records']:
                need(rest['end_day']==rest['endpoint_day'] and rest['start_day']<=rest['end_day'] and rest['end_day'] in obs,'B rest has no actual dated endpoint')
                match=[u for u in obs[rest['end_day']]['units'] if u['army_id']==rest['unit_id'] and u['current_province_id']==rest['province_id']]
                need(len(match)==1,'B rest endpoint unit/site differs')
                u=match[0];elapsed=rest['end_day']-rest['start_day']
                need(elapsed<=bp['maximum_rest_days'],'B rest exceeded frozen maximum')
                if rest['reason']=='maximum_rest_days':need(elapsed==bp['maximum_rest_days'],'B max-stay exit did not reach cap')
                else:need(u['stock_raw']>=bp['minimum_stock_raw'] and u['maximum_soldiers']-u['current_soldiers']<=bp['maximum_deficit'],'B threshold not actually met')
        if label=='C':
            way=ex['C_waypoint_observed_days']
            need([w['province_id'] for w in way]==plan['strategies']['C']['waypoint_province_ids'],'C waypoint policy changed')
            need([w['day'] for w in way]==sorted(w['day'] for w in way),'C waypoints out of order')
            for w in way:need(w['day'] in obs and any(u['current_province_id']==w['province_id'] for u in obs[w['day']]['units']),'C waypoint lacks actual location observation')
        for dev in arm['deviations']:
            if dev['kind']=='measurement':reasons.append(label+': measurement deviation: '+dev['description'])
            else:world.append({'arm':label,'description':dev['description']})
        ledger=arm['ledger'];need(ledger['through_day']==dis['day'],'ledger time scope differs from per-arm endpoint')
        if ledger['loss_refill_qualified']:
            need(integer(ledger['loss_physical_debits']) and integer(ledger['refill_physical_adds']) and ledger['evidence'],'qualified loss/refill needs actual integer application evidence')
        else:reasons.append(label+': loss/refill ledger unqualified')
        fee=None
        if plan['compare_fees']:
            need(ledger['payment_qualified'] and ledger['evidence'],'fee comparison lacks actual payment ledger')
            vals=[ledger[k] for k in ('boarding_gold_raw','maintenance_gold_raw','other_cash_income_raw','other_cash_expense_raw')]
            need(all(integer(v) for v in vals),'unknown fee/income/other expense cannot become zero')
            board,maint,inc,expense=vals
            need(actual['treasury_raw']-cold['treasury_raw']==inc-expense-board-maint,'wallet does not reconcile; never add military twice to NET/full expenses')
            fee={'boarding_raw':board,'maintenance_raw':maint,'actual_military_and_boarding_total_raw':board+maint,'scale':100000,'through_day':dis['day']}
        rows.append({'arm':label,'disposition':dis['kind'],'arrival_interval_days':([lower,dis['day']] if dis['kind']=='arrived' else None),'observed_day':dis['day'],'observed_date_raw':actual['date_raw'],'original_cohort_current':actual['cohort_current'],'original_cohort_maximum':actual['cohort_maximum'],'all_strategy_current':actual['all_strategy_current'],'all_strategy_maximum':actual['all_strategy_maximum'],'per_army_supply':actual['units'],'wallet_net_raw':actual['treasury_raw']-cold['treasury_raw'],'wallet_net_is_military_cost':False,'actual_fees':fee,'loss_physical_debits':ledger['loss_physical_debits'] if ledger['loss_refill_qualified'] else None,'refill_physical_adds':ledger['refill_physical_adds'] if ledger['loss_refill_qualified'] else None,'net_cohort_change':actual['cohort_current']-cold['cohort_current']})
        all_obs[label]=obs
    common=[]
    for day in plan['report_days']:
        if all(day in all_obs[a] for a in ('A','B','C')):
            common.append({'day':day,'date_raw':plan['t0_raw']+24*day,'arms':{a:{k:all_obs[a][day][k] for k in ('cohort_current','cohort_maximum','all_strategy_current','all_strategy_maximum','treasury_raw','units')} for a in ('A','B','C')}})
    d90=None
    if plan['follow_after_arrival_to_day90'] and all(90 in all_obs[a] for a in ('A','B','C')):
        d90={a:{k:all_obs[a][90][k] for k in ('cohort_current','all_strategy_current','treasury_raw')} for a in ('A','B','C')}
    return {'schema':'xar.e04.r10.comparison-check.v1','controlled_comparison_records_eligible':not reasons,'reasons':reasons,'observations_only':rows,'comparison_rows':rows if not reasons else None,'common_date_rows':common if not reasons else None,'D90_rows':d90 if not reasons else None,'world_events_retained':world,'winner':None,'arrival_rows_have_arm_specific_observation_dates':True,'actual_arrival_fees_are_not_equal_duration_rate_effects':True,'live_execution_performed':False,'research_card_closed':False,'human_media_review_performed':False,'scope':'Consistency, exact supplied evidence bytes, native queried counts/frame and declared ledgers. Does not prove source authenticity, causal ledger qualification, every policy action, clean footage, human review or live R10 completion.'}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=('check-plan','compare','reject-legacy'));p.add_argument('input',type=Path);p.add_argument('--plan',type=Path);p.add_argument('--evidence-root',type=Path);p.add_argument('--output',type=Path)
    a=p.parse_args(argv)
    try:
        data=parse(a.input.read_bytes());need(isinstance(data,dict),'input must be JSON object')
        if a.mode=='reject-legacy':out=legacy_rejection(data)
        else:
            need(a.evidence_root is not None,'--evidence-root required');e=Evidence(a.evidence_root)
            if a.mode=='check-plan':
                b=check_plan(data,e);out={'plan_consistent':True,'baseline_date_raw':b['date_raw'],'deadline_date_raw':data['t0_raw']+2160,'live_execution_performed':False,'semantic_qualification_granted':False}
            else:
                need(a.plan is not None,'--plan required');pr=a.plan.read_bytes();plan=parse(pr)
                need(data.get('plan_sha256')==digest(pr),'results do not bind exact frozen plan bytes');out=compare(plan,data,e)
        code=0 if out.get('controlled_comparison_records_eligible',True) and out.get('accepted_as_R10_result',True) else 2
    except (ValueError,KeyError,TypeError,OSError,json.JSONDecodeError) as error:
        out={'accepted':False,'reason':str(error),'live_execution_performed':False};code=2
    out['checked_at_utc']=datetime.now(timezone.utc).isoformat()
    result=json.dumps(out,ensure_ascii=False,indent=2)+'\n'
    if a.output:
        with a.output.open('x',encoding='utf-8',newline='\n') as f:f.write(result)
    else:sys.stdout.write(result)
    return code

if __name__=='__main__':raise SystemExit(main())
