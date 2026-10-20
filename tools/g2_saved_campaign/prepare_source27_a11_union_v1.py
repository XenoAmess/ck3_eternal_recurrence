"""Independent A11 retry of Source27; Root alone adopts the new runtime."""
from __future__ import annotations
import ast,hashlib,json,sys,types
from pathlib import Path
sys.dont_write_bytecode=True
OWN=Path(__file__).resolve().parent
sys.path.insert(0,str(OWN))
import prepare_c23_a10_union_v1 as old
from prepare_c23_a10_union_v1 import ExactRef,JSONObject,Outputs
MACHINE,O,T0=old.MACHINE,old.O,old.T0
U10,U11=old.U10,old.U10.with_name("runtime-a11")
T5=U11
PIN=(36861,"7b656c6d11ebaa511e998f014ea182931a90fe95ba118a98bb357d44b7f569a9")
PREPARED=O/"A10-PREPARED01.json"
PREPARED_PIN=(38291,"32244a661bf909dcb2c4a578d599a42d7cd7a50a29b31d8cf1292d1fc05bbd3f")
QUOTE=old.P/"A10-ROOT-QUOTE02.json"
QUOTE_PIN=(172391,"8ec8d672bc88e6dd47824f6262f3a2d419f42a572137b9c43ec7baeb54c976e4")
INDEX=U10/"A10-ACTUAL-CLOSURE-INDEX01.json"
INDEX_PIN=(3126,"c4ee7589b59be1ad78324c2f6ec190dc28cbd31136c25751665869d7feb9f0a6")
require,exact,prior=old.require,old.exact,old.prior

def closed_source():
    return "A11_A10_INDEX="+repr(prior.ref(INDEX))+"\n"+r'''
def validate_actual_a10_index_v1(reference,checked):
    require(reference==A11_A10_INDEX,'exact actual A10 closed attempt')
    x=checked(reference,16384)
    require(x['schema']=='xar.C23-A10-actual-closure-index/v1' and x['machine_id']==MACHINE
        and x['attempt_id']=='a10' and x['failure_phase']=='native_injector_before_primary_resume'
        and x['created_Game']=={'pid':139908,'creation_filetime':'134369688444824386'}
        and x['Game_launch_handle_returned'] is False and x['owned_job_active_final']==0
        and x['next_sequence']==10521 and x['business_RPC_count']==x['new_game_credit_days']==x['new_cycle_credit']==0
        and x['SDK_created'] is False and x['recording_created'] is False
        and x['normal_Game_exit_proven'] is False and x['source27_and_SAVE_unchanged'] is True
        and x['original_saved_days']==5429 and x['original_saved_cycles']==4753,'A10 failed startup gives no business credit')
    rows={n:checked(r,16384) for n,r in x['refs'].items()}
    osdoc=checked(x['actual_OS_closed'],16384);task=checked(x['Task_closed'],16384)
    require(osdoc['machine_id']==task['machine_id']==MACHINE and osdoc['active_ck3_pids']==[]
        and {(p['pid'],p['exists']) for p in osdoc['actual_attempt_processes']}=={(139908,False),(145068,False),(275908,False)}
        and osdoc['mutations_to_games']==0 and task['child_exit_code']==task['bootstrap_exit_code']==1
        and task['job_active_after_stage']==0 and task['forced_remaining_cleanup'] is False,'actual A10 kernel absence and owned Task Job0')
    closed=rows['ROOT-FRESH-SUPERVISOR-CLOSED-C23-A10.json']
    require(closed['machine_id']==MACHINE and closed['attempt_id']=='a10'
        and closed['cleanup_classification']=='LAUNCH_FAILED_HANDLE_NOT_RETURNED'
        and 'native bridge injector failed: rc=3' in closed['failure']['message']
        and 'error=258' in closed['failure']['message'] and closed['sdk_actual_exit'] is None
        and closed['keeper']['thread_exited'] is True and closed['keeper']['last_sequence']==7706,'actual failed native preparation')
    wrapper=rows['ROOT-A10-SUPERVISOR-UNREGISTER01.json'];unregistered=json.loads(wrapper['stdout'])
    require(wrapper['returncode']==0 and wrapper['stderr']=='' and unregistered['machine_id']==MACHINE
        and unregistered['operation']=='unregister' and unregistered['actual']['absent_after'] is True
        and unregistered['actual']['instances']==0 and unregistered['task_name']=='XARG2ManagedOwner-'+task['nonce'],'old once-only A10 Task absent')
    wrapper=rows['ROOT-A10-SCREEN-RELEASE01.json'];released=json.loads(wrapper['stdout'])
    require(wrapper['returncode']==0 and released['ok'] is True and released['task']['state']=='done'
        and released['task']['resources']==[] and released['task']['last_sequence']==7710
        and released['task']['task_id']==closed['keeper']['task_id'],'actual A10 screen release')
    wrapper=rows['ROOT-A10-RUN-CLOSED01.json'];run=json.loads(wrapper['stdout'])
    require(wrapper['returncode']==0 and run['machine_id']==MACHINE and run['status']=='completed-red'
        and run['sequence']==8 and rows['NEXT-SEQUENCE-P37.json']['next_sequence']==10521,'original A10 run/NEXT remain consumed')
    return closed
'''

def closure_guard():
    exact(INDEX,INDEX_PIN)
    scope={"MACHINE":MACHINE,"require":require,"json":json}
    exec(closed_source(),scope)
    return scope["validate_actual_a10_index_v1"](prior.ref(INDEX),prior.checked)

def actual_graph():
    exact(old.__file__,PIN)
    closure_guard()
    accepted=json.loads(exact(PREPARED,PREPARED_PIN));quote=json.loads(exact(QUOTE,QUOTE_PIN))
    require(accepted['machine_id']==quote['machine_id']==MACHINE and len(accepted['outputs'])==140
        and accepted['outputs']==[{k:r[k] for k in ('path','bytes','sha256')} for r in quote['files']],'actual complete140 A10 inputs')
    values,rows={},{}
    for row in accepted['outputs']:
        path=Path(row['path']).resolve();body=prior.raw(path,524288)
        require(prior.ref(path)==row,'accepted A10 input changed: '+str(path))
        values[path],rows[path]=body,row
    names=quote['sources']['runtime_source_output_names']
    require(len(names)==len(set(names))==110 and all(U10/n in values for n in names),'all110 original source inputs')
    return values,rows,quote,[],names

def build_sources(plan):
    values,rows,quote,_,names=actual_graph()
    staged,stage_refs=old.stage_values(plan)
    source={n:values[U10/n] if n in staged else values[U10/n].replace(b'C23-A10',b'C23-A11') for n in names}
    name='root_checkpoint_bootstrap_c23.py'
    source[name]=prior.swap(source[name],"xar.C23-A11-environment-migration/v1","xar.C23-A10-environment-migration/v1",1)
    source[name]=prior.swap(source[name],"def verify_cold_profile(spec):",closed_source()+"\ndef verify_cold_profile(spec):",1)
    name='root_native30_supervisor_c23.py'
    body=source[name]
    for a,b,n in (("args.attempt=='a10'","args.attempt=='a11'",1),("value.get('attempt_id')=='a10'","value.get('attempt_id')=='a11'",1),
        ('choices=("a10",)','choices=("a11",)',1),('"attempt_id":"a10"','"attempt_id":"a11"',2),
        ("_validate_a10_attempt(args, config)","_validate_a11_attempt(args, config)",1)):
        body=prior.swap(body,a,b,n)
    guard=r'''
def _validate_a11_attempt(args,config):
    value=_validate_a10_attempt(args,config)
    from root_checkpoint_bootstrap_c23 import validate_actual_a10_index_v1
    closed=validate_actual_a10_index_v1(value['prior_failure_a10'],_a03_checked)
    require(args.attempt_nonce not in (closed['attempt_nonce'],closed['task_nonce'])
        and args.task_nonce not in (closed['attempt_nonce'],closed['task_nonce']),'independent A11 once-only nonces')
    return value

'''
    source[name]=prior.swap(body,"def main(args):",guard+"def main(args):",1)
    for n,b in source.items():
        if n.endswith('.py'):compile(b,n,'exec')
    return source,{"schema":"xar.A11-Source27-source/v1","machine_id":MACHINE,"feeder":{},
        "actual_source_rows":[rows[U10/n] for n in names],"runtime_source_output_names":names,
        "supplemental_import_rows":[rows[U10/Path(r['path']).name] for r in quote['sources']['supplemental_import_rows']],
        "staging_files":[stage_refs[n] for n in old.STAGE_NAMES],"mutable_OBS_config_observations":[],
        "actual_A10_index":prior.ref(INDEX),"new_day_credit":0}

def state_guard(plan):
    closure_guard()
    result=old.state_guard(plan)
    return {**result,"actual_A10_index":prior.ref(INDEX)}

def projected(name):
    return old.get_function(old,name,PIN)

def scope():
    ram=projected('ram_supervisor_spec')
    ram=prior.swap(ram.encode(),'"--attempt","a10"','"--attempt","a11"',1).decode()
    out={**vars(old),"__file__":__file__,"U9":U10,"U10":U11,"T5":U11,
        "build_sources":build_sources,"state_guard":state_guard}
    exec(compile(ram,'A11-typed-SPEC-RAM','exec'),out)
    return out

def compose(plan,*,display_values,display_review,companion_values):
    text=projected('compose')
    for a,b,n in (('.replace("C23-A05","C23-A10")','.replace("C23-A05","C23-A11")',1),
        ('.replace("C23-A04","C23-A09")','.replace("C23-A04","C23-A10")',1),
        ('.replace("\'a05\'","\'a10\'")','.replace("\'a05\'","\'a11\'")',1),
        ('.replace("spec-supervisor-a05","spec-supervisor-a10")','.replace("spec-supervisor-a05","spec-supervisor-a11")',1),
        ('prior_failure_a09=ref(INDEX))','prior_failure_a09=ref(INDEX),prior_failure_a10=A11_INDEX_REF)',1)):
        text=prior.swap(text.encode(),a,b,n).decode()
    text=prior.swap(text.encode(),'"INDEX":INDEX','"INDEX":INDEX,"A11_INDEX_REF":A11_INDEX_REF',1).decode()
    env=scope();env.update(INDEX=old.INDEX,A11_INDEX_REF=prior.ref(INDEX))
    env['campaign_score_guard']=campaign_score_guard
    exec(compile(text,'A11-full140-union-RAM','exec'),env)
    outputs,quote=env['compose'](plan,display_values=display_values,display_review=display_review,companion_values=companion_values)
    quote.update(schema='xar.C23-A11-union-prepare-quote/v1',actual_A10_index=prior.ref(INDEX))
    return outputs,quote

def compose_plan(plan_ref:ExactRef)->tuple[JSONObject,Outputs,JSONObject]:
    plan=prior.checked(plan_ref,131072)
    require(prior.ref(__file__)==plan['union_producer'],'exact A11 producer')
    display_values,display_review,companions=display_compose(plan)
    outputs,quote=compose(plan,display_values=display_values,display_review=display_review,companion_values=companions)
    quote.update(adopter=prior.ref(__file__),input_plan=plan_ref,original_adopter_source=prior.ref(OWN/'adopt_c23_a05_union_v1.py'))
    return plan,outputs,quote

def adopt(plan_ref:ExactRef,quote_ref:ExactRef,card_ref:ExactRef)->ExactRef:
    text=projected('adopt').replace('A10','A11').replace('a10','a11')
    env=scope();env.update(compose_plan=compose_plan,campaign_score_guard=campaign_score_guard)
    exec(compile(text,'A11-Root-only-adopt','exec'),env)
    return env['adopt'](plan_ref,quote_ref,card_ref)

def cold_owner(inputs:JSONObject)->tuple[Outputs,JSONObject]:
    text=projected('cold_owner').replace('A10','A11').replace('a10','a11')
    env=scope();exec(compile(text,'A11-cold-owner-RAM','exec'),env)
    return env['cold_owner'](inputs)

def display_module():
    path=OWN/"prepare_source27_a10_display_v1.py"
    exact(path,old.DISPLAY_PIN)
    return prior._module(path,"_a11_pinned_display_primitive")

def display_compose(plan):
    d=display_module();b=d.base
    refs,forbidden=d.predecessor()
    closed=closure_guard()
    forbidden.update((closed['attempt_nonce'],closed['task_nonce'],"807f943bfbed4552992431e6c1fd56c4"))
    require(plan['display']['display_nonce'] not in forbidden,'fresh A11 display nonce')
    require(prior.ref(d.__file__)==plan['display_producer'],'exact display source input')
    d.source(Path(b.__file__),d.prior.PRIOR_PIN)
    edits={
        "spec['generation'] == 'C23-A05'":"spec['generation'] == 'Source27-A10'",
        "spec.update(generation='C23-A06', target_runtime=str(T6), display_nonce=display_nonce)":
            "spec.update(generation='Source27-A11', target_runtime=str(T6), display_nonce=display_nonce, previous_Game_tuple=[139908,134369688444824386])",
        "A06_display_nonce=display_nonce":"A11_display_nonce=display_nonce",
        "profile.pop('A05_display_nonce', None)":"profile.pop('A10_display_nonce', None)",
        "xar.C23-A06-complete-display-RAM-review/v1":"xar.Source27-A11-complete-display-RAM-review/v1",
        "xar.C23-A06-display-prepare-input/v1":"xar.Source27-A11-display-prepare-input/v1",
        "spec['previous_Game_tuple'] == list(prior.OLD_GAME)":"spec['previous_Game_tuple'] == [251852,134369595515684194]"}
    patches=tuple((a,edits.get(a,z)) for a,z in b.PATCHES)+(
        ("profile['storage_review_at_utc'] == REVIEW_AT","profile['storage_review_at_utc'] == '2026-10-20T12:30:00+00:00'"),)
    env=dict(b.recipe.__globals__,U7=U10,U8=U11,TASK8=O/"tasks/spec-display-a11",QUOTE7=QUOTE,QUOTE7_PIN=QUOTE_PIN,
        PROFILE7_PIN=(3437,"f9b29ec7e5bc4d4c2beedbc16bc27c0da0505dfb1beec6dc145c292a454aca8c"),
        DISPLAY7_NONCE="807f943bfbed4552992431e6c1fd56c4",PATCHES=patches)
    namespace,recipe_ref=types.FunctionType(b.recipe.__code__,env)()
    namespace.update(REVIEW_AT='2026-10-20T12:30:00+00:00',FULL5_SHA=d.FULL_PIN[1])
    v,r,c=namespace['compose'](plan['display'])
    r.pop('actual_A05_Game_created',None)
    r['inputs'].extend([*refs,prior.ref(d.__file__),prior.ref(b.__file__),recipe_ref,prior.ref(INDEX)])
    return v,r,c

def build_task_spec(display_values:dict[str,bytes],display_review:JSONObject,*,task_nonce:str,
                    game_launch_ref:ExactRef,placement_ref:ExactRef,bootstrap_ref:ExactRef,
                    owner_contract_ref:ExactRef)->tuple[Outputs,JSONObject]:
    d=display_module()
    def predecessor():
        refs,forbidden=d.predecessor()
        closed=closure_guard()
        return [prior.ref(INDEX),*refs],forbidden|{closed['attempt_nonce'],closed['task_nonce'],"807f943bfbed4552992431e6c1fd56c4"}
    binder=types.FunctionType(d.build_task_spec.__code__,dict(d.build_task_spec.__globals__,
        U10=U11,TASK10=O/"tasks/spec-display-a11",GAME9=[139908,134369688444824386],predecessor=predecessor))
    values,review=binder(display_values,display_review,task_nonce=task_nonce,game_launch_ref=game_launch_ref,
        placement_ref=placement_ref,bootstrap_ref=bootstrap_ref,owner_contract_ref=owner_contract_ref)
    review['source_closed_A10']=review.pop('source_closed_A09')
    return values,review

def campaign_score_guard(*,alias_required=False):
    f=types.FunctionType(old.campaign_score_guard.__code__,{**vars(old),"U10":U11})
    return f(alias_required=alias_required)
