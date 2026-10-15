"""Offline R10 record schemas. Generate JSON; never edit generated schema bytes."""
from __future__ import annotations
import json
from pathlib import Path

def obj(properties, required=None):
    return {'type':'object','properties':properties,'required':list(properties) if required is None else required,'additionalProperties':False}
def arr(items, minimum=0, unique=False):
    x={'type':'array','items':items,'minItems':minimum}
    if unique:x['uniqueItems']=True
    return x
def ref(key):return {'$ref':'#/$defs/'+key}
S={'type':'string','minLength':1}
I={'type':'integer'}
U={'type':'integer','minimum':0}
B={'type':'boolean'}
NULL={'type':'null'}
SHA={'type':'string','pattern':'^[0-9a-f]{64}$'}
HEAD={'type':'string','pattern':'^[0-9a-f]{40}$'}
PIN=obj({'path':S,'bytes':{'type':'integer','minimum':1,'maximum':16777216},'sha256':SHA})
BOUND=obj({'source':ref('pin'),'pointer':{'type':'string','pattern':'^(/.*)?$'}})
ENDPOINT=obj({'day':{'type':'integer','minimum':0,'maximum':90},'snapshot':ref('pin'),'army_result':ref('pin'),'strategy_army_ids':arr(U,1,True),'commander':ref('bound'),'loaded_features':ref('bound')})
STRATEGIES=obj({
 'A':obj({'mode':{'const':'whole-direct'},'route_preview':ref('pin')}),
 'B':obj({'mode':{'const':'split-rest-merge'},'rest_province_ids':{'type':'array','items':U,'minItems':2,'maxItems':2,'uniqueItems':True},'site_actual_stock_increase_evidence':{'type':'array','items':ref('pin'),'minItems':2,'maxItems':2},'minimum_stock_raw':U,'maximum_deficit':U,'maximum_rest_days':{'type':'integer','minimum':1,'maximum':90},'merge_province_id':U,'merge_destination_policy':S,'commander_policy':S,'r09_result':ref('pin')}),
 'C':obj({'mode':{'const':'whole-via'},'waypoint_province_ids':arr(U,1,True),'route_preview':ref('pin')})})
PLAN=obj({
 'schema':{'const':'xar.e04.r10.plan.v1'},'status':{'const':'frozen'},'frozen_at_utc':S,'plan_id':S,
 'build':obj({'version':{'const':'1.20.0.4'},'steam_build':{'const':25734779},'exe_sha256':{'const':'98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518'},'source_head':HEAD,'native_dll_sha256':SHA}),
 'normal_save':obj({'kind':{'const':'normal-native-checkpoint'},'bytes':{'type':'integer','minimum':1},'sha256':SHA,'save_receipt':ref('pin'),'normal_origin_proof':ref('pin')}),
 't0_raw':I,'max_natural_days':{'const':90},'raw_per_day':{'const':24},'goal_province_id':U,'arrival_states':arr(S,1,True),'original_regiment_ids':arr(U,1,True),
 'baseline':ref('endpoint'),'strategies':STRATEGIES,'report_days':arr({'type':'integer','minimum':1,'maximum':90},0,True),
 'compare_fees':B,'follow_after_arrival_to_day90':B,'post_arrival_policy':{'anyOf':[S,NULL]},'event_policy':S,'wall_budget_seconds_per_arm':{'type':'integer','minimum':1},
 'prerequisites':obj({'exact_clock':ref('pin'),'loss_refill_subject_qualification':ref('pin'),'B_microexperiment':ref('pin'),'boarding_payment':{'anyOf':[ref('pin'),NULL]},'maintenance_settlement':{'anyOf':[ref('pin'),NULL]}})
})
RUNTIME=obj({'machine_id':S,'started_at_utc':S,'pid':{'type':'integer','minimum':1},'process_create_time_100ns':{'type':'integer','minimum':1},'connection_generation':{'type':'integer','minimum':1},'episode':S,'player_character_id':U,'source_head':HEAD,'native_dll_sha256':SHA,'source_proof':ref('pin')})
CLOCK_DAY=obj({'day':{'type':'integer','minimum':1,'maximum':90},'clock_source':ref('pin'),'paused_snapshot':ref('pin'),'strategy_army_ids':arr(U,1,True)})
LEDGER=obj({'loss_refill_qualified':B,'payment_qualified':B,'loss_physical_debits':{'anyOf':[U,NULL]},'refill_physical_adds':{'anyOf':[U,NULL]},'boarding_gold_raw':{'anyOf':[U,NULL]},'maintenance_gold_raw':{'anyOf':[U,NULL]},'other_cash_income_raw':{'anyOf':[U,NULL]},'other_cash_expense_raw':{'anyOf':[U,NULL]},'through_day':{'type':'integer','minimum':0,'maximum':90},'evidence':arr(ref('pin'))})
EXECUTION=obj({'prespecified_policy_followed':B,'B_merge_destination_policy':{'anyOf':[S,NULL]},'B_commander_policy':{'anyOf':[S,NULL]},'B_rest_exit_records':arr(obj({'province_id':U,'unit_id':U,'start_day':U,'end_day':U,'reason':{'enum':['threshold','maximum_rest_days']},'endpoint_day':U})), 'C_waypoint_observed_days':arr(obj({'province_id':U,'day':U})),'evidence':arr(ref('pin'),1)})
ARM=obj({'label':{'enum':['A','B','C']},'runtime':ref('runtime'),'loaded_save_sha256':SHA,'cold_start':ref('endpoint'),'days':arr(ref('clock_day')),'observations':arr(ref('endpoint'),1),'execution':ref('execution'),
 'disposition':obj({'kind':{'enum':['arrived','budget-censored','measurement-stop','strategy-stop','competing-event']},'day':{'type':'integer','minimum':0,'maximum':90},'last_not_arrived_day':{'anyOf':[U,NULL]},'reason':{'anyOf':[S,NULL]},'evidence':arr(ref('pin'),1)}),
 'ledger':ref('ledger'),'deviations':arr(obj({'kind':{'enum':['measurement','world-event']},'description':S,'evidence':ref('pin')}))})
RESULTS=obj({'schema':{'const':'xar.e04.r10.results.v1'},'plan_sha256':SHA,'arms':{'type':'array','items':ref('arm'),'minItems':3,'maxItems':3}})
SCHEMA={'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:xar:e04:r10:v1','$defs':{'pin':PIN,'bound':BOUND,'endpoint':ENDPOINT,'runtime':RUNTIME,'clock_day':CLOCK_DAY,'ledger':LEDGER,'execution':EXECUTION,'arm':ARM,'plan':PLAN,'results':RESULTS},'oneOf':[ref('plan'),ref('results')]}
if __name__=='__main__':
    p=Path(__file__).with_name('r10.schema.json')
    with p.open('w',encoding='utf-8',newline='\n') as f:json.dump(SCHEMA,f,ensure_ascii=False,indent=2);f.write('\n')
