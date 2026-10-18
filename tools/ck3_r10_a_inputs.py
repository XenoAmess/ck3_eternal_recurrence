"""Bind explicit independent A inputs, freeze real baseline, or stage Root mail.

Only bounded metadata is read. No SDK, launcher, host, Save/media payload or
action is executed. Public ck3_mod_acceptance remains the only runtime entry.
"""
from pathlib import Path
from datetime import datetime, timezone
from copy import deepcopy
import argparse, hashlib, importlib, json, subprocess, sys

REPO=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(REPO/'tools'),str(REPO/'ck3_autonomous_player/src')]
from ck3_mod_acceptance_cases import r10_prepare_adapter as normal
from ck3_mod_acceptance_cases.r10_common_arm import A_ONLY_SCHEMA, public_plan_baseline
from ck3_live_run_id import current_machine_id

def now():return datetime.now(timezone.utc).isoformat()
def read(path):
    path=Path(path);normal.need(0<path.stat().st_size<=1024*1024,'Bounded small JSON required')
    return json.loads(path.read_bytes())
def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
    with path.open('xb') as f:f.write(raw)
    return normal.pin(path)
def relative(ref,root):
    p=Path(ref['path']).resolve();normal.need(p.is_relative_to(root),'Evidence must be under one explicit root')
    return {**ref,'path':p.relative_to(root).as_posix()}
def imports(repo):
    sys.path.insert(0,str(repo/'promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison'))
    return importlib.import_module('r10_compare'),importlib.import_module('strategy_a')

def bind(o):
    normal.need(o.label=='A' or o.frozen_plan is not None,
        'B/C require the complete frozen joint PLAN including two actual positive-stock B sites; no partial fixture is admitted')
    spec=read(o.spec);runtime=read(o.runtime);cap=read(o.capacity);machine=current_machine_id()
    normal.need(spec['machine_id']==cap['machine_id']==machine,'Current/source/capacity machines differ')
    repo=Path(runtime['repo_root']).resolve();head=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
    manifest=normal.small_json(runtime['manifest'])
    normal.need(manifest['qualification']['runtime_source_head']==head==cap['source_head']
        and cap['admitted'] is True and cap['root_atomic_adoption_required'] is False,'Actual runtime/capacity/current source differs')
    normal.need(manifest['host_features'].get('war_cash_queries') is True,'Existing private current-cash query opt-in required')
    scene=o.scene.resolve();state=scene/'state-a01'
    normal.need(Path(cap['component_roots']['profile']).resolve()==state,'Actual capacity does not bind this new state')
    normal.need(datetime.fromisoformat(cap['quota_review_at_utc'].replace('Z','+00:00'))>datetime.now(timezone.utc),'Actual capacity expired')
    root=Path(spec['evidence_root']).resolve();save=spec['saved_campaign']
    for key in ('army_id','war_id','goal_province_id','staging_province_id'):
        normal.need(type(spec.get(key)) is int and 0<=spec[key]<2**31,'Actual selected '+key+' required before binding')
    normal.need(type(spec.get('native_carmy_id')) is int and spec['native_carmy_id']!=-1,
        'Actual resolved native CArmy full ID required before binding')
    normal.need(Path(save['save']).stat().st_size==save['bytes'],'Original normal Save unavailable/changed size')
    # Read small receipts/config only. The public prepare verifies opaque Save.
    for k in ('normal_checkpoint_receipt','normal_checkpoint_build_receipt','normal_origin_proof'):
        normal.small_json(spec[k])
    for ref in spec['plain_configuration'].values():
        normal.need(type(ref.get('bytes')) is int and 0<ref['bytes']<=1024*1024
            and Path(ref['path']).stat().st_size==ref['bytes'],'Bounded exact plain configuration required')
        actual=normal.pin(ref['path']);normal.need(actual==ref,'Exact plain configuration changed')
    output=o.output.resolve();output.mkdir(exist_ok=False,parents=True)
    if o.frozen_plan:
        plan=read(o.frozen_plan);phase='execute';planref=normal.pin(o.frozen_plan)
        normal.need(plan['build']['source_head']==head and plan['normal_save']['sha256']==save['sha256']
            and plan['build']['native_dll_sha256']==manifest['native']['dll']['sha256']
            and plan['t0_raw']==save['date_raw'] and plan['goal_province_id']==spec['goal_province_id'],
            'Frozen source/Save/DLL/T0/goal changed')
        c,a=imports(repo)
        if o.label=='A':public_plan_baseline({'case':'r10-independent-a','case_contract':{'schema':A_ONLY_SCHEMA},
            'case_inputs':{'arm':{'label':'A','phase':'execute'}}},plan,c.Evidence(root),c)
        else:c.check_plan(plan,c.Evidence(root))
    else:
        phase='collect-baseline'
        plan={'schema':'xar.e04.r10.plan.v1','status':'baseline-capture','execution_scope':'independent-A-only',
            'plan_id':spec['plan_id'],'build':{'version':'1.20.0.4','steam_build':25734779,
                'exe_sha256':'98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518',
                'source_head':head,'native_dll_sha256':manifest['native']['dll']['sha256']},
            'normal_save':{'kind':'normal-native-checkpoint','bytes':save['bytes'],'sha256':save['sha256'],
                'save_receipt':relative(spec['normal_checkpoint_receipt'],root),
                'normal_origin_proof':relative(spec['normal_origin_proof'],root)},
            't0_raw':save['date_raw'],'max_natural_days':90,'raw_per_day':24,'goal_province_id':spec['goal_province_id'],
            'arrival_states':spec['arrival_states'],'original_regiment_ids':[],'baseline':None,
            'strategies':{'A':{'mode':'whole-direct','route_preview':None},'B':None,'C':None},
            'report_days':spec['report_days'],'compare_fees':False,'follow_after_arrival_to_day90':False,
            'post_arrival_policy':None,'event_policy':spec['event_policy'],
            'wall_budget_seconds_per_arm':spec['budgets']['hold_seconds'],'prerequisites':{}}
        planref=write(output/'A-BASELINE-SEED.json',plan)
    values={'normal_checkpoint_receipt':spec['normal_checkpoint_receipt'],
        'normal_checkpoint_build_receipt':spec['normal_checkpoint_build_receipt'],
        'plain_configuration':spec['plain_configuration'],'phase':'readiness','army_id':spec['army_id'],
        'native_carmy_id':spec['native_carmy_id'],'war_id':spec['war_id'],
        'goal_province_id':spec['goal_province_id'],'staging_province_id':spec['staging_province_id'],
        'agreed_commander_id':None,'director_scope_revision':head,'budgets':spec['budgets'],
        'arm':{'label':o.label,'plan':planref,'capacity_admission':normal.pin(o.capacity),
            'deadline_utc':cap['quota_review_at_utc'],'evidence_root':str(root),
            'max_runtime_total_bytes':cap['component_ceiling_bytes']['driver'],'max_evidence_file_bytes':16*1024*1024,
            'one_day_timeout_seconds':spec['one_day_timeout_seconds'],'maximum_modal_choices':32,
            'maximum_stages':96,'poll_interval_seconds':0.25}}
    if o.label=='A':values['arm']['phase']=phase
    inputs={'machine_id':machine,'observed_at_utc':now(),'source_head':head,'state_dir':str(state),
        'saved_campaign':save,'case_inputs':values,'capacity_admitted':True,'formal_ABC_completed':0}
    inp=write(output/(o.label+'-CASE-INPUTS.json'),inputs)
    base=[runtime['python'],'-B','-X','utf8',str(repo/'tools/ck3_mod_acceptance.py')]
    common=['--runtime',str(o.runtime.resolve()),'--products',str(repo/'tools/ck3_mod_acceptance_r10_arm_products.json'),
        '--product','war-episode04-r10','--case','r10-independent-a' if o.label=='A' else 'r10-common-arm']
    prepared=scene/'prepared-a01/prepared-case.json'
    commands={mode:base+[mode]+common+(['--case-inputs',inp['path'],'--prepare-output',str(prepared.parent)] if mode=='prepare'
        else ['--prepared-case',str(prepared)]) for mode in ('prepare','plan')}
    write(output/'PUBLIC-PREPARE-ARGV.json',{'machine_id':machine,'phase':phase,'commands':commands,
        'allocate_preflight_run':'Use the existing public common lifecycle with this SAME products/case/prepared-case and fresh actual READY/review; no guessed run ID.',
        'stage_cli':str(repo/'tools/ck3_r10_a_inputs.py'),'Save_payload_hashed_here':False,'native_or_formal_credit':False})
    print(json.dumps({'inputs':inp,'plan':planref,'phase':phase,'executed_prepare_or_game':False}))

def freeze(o):
    capture=read(o.capture);state=capture['state'];machine=current_machine_id()
    normal.need(capture['machine_id']==state['runtime']['machine_id']==machine and state['schema']=='xar.e04.r10-independent-a-baseline.v1'
        and state['Move_submitted'] is False and state['natural_days']==0,'Actual A readonly baseline required')
    seed=normal.small_json(state['seed_plan']);plan=deepcopy(seed)
    normal.need(plan['status']=='baseline-capture' and plan['execution_scope']=='independent-A-only','Original A baseline seed differs')
    c,a=imports(o.repo_root.resolve());e=c.Evidence(o.evidence_root)
    c.schema_check(state['runtime'],'runtime');e.all_pins(state['runtime'])
    plan.update(status='frozen',frozen_at_utc=now(),baseline=state['baseline'],original_regiment_ids=state['original_regiment_ids'])
    plan['strategies']['A']['route_preview']=state['route_preview']
    baseline,snapshot=a._whole(plan['baseline'],plan,e,state['runtime'])
    route=a._preview(state['route_preview'],plan['baseline'],plan,e,state['runtime'])
    normal.need(route==state['route'] and not c.arrived(baseline,plan),'Actual baseline route/goal differs')
    normal.need(state['runtime']['source_head']==plan['build']['source_head']
        and state['runtime']['native_dll_sha256']==plan['build']['native_dll_sha256'],'Baseline runtime source/DLL differs')
    e.raw(plan['normal_save']['save_receipt']);e.raw(plan['normal_save']['normal_origin_proof'])
    normal.need(set(plan['original_regiment_ids'])=={r['army_regiment_id'] for r in baseline['DATA']},'Original whole cohort incomplete')
    print(json.dumps({'frozen_plan':write(o.output,plan),'next':'New independent cold public run execute phase; never Move in baseline capture PID.',
        'joint_ABC_eligible':False,'actual_formal_qualified':False}))

def stage(o):
    request=read(o.awaiting);normal.need(request['schema']=='xar.e04.r10-common-stage-request.v1','Existing actual stage awaiting required')
    label=request['label'];normal.need(request['machine_id']==current_machine_id() and label in ('A','B','C'),'Actual stage/current machine required')
    choices={'baseline','finish'}
    choices.update({'Move-once','Move-post','advance','advance-common-horizon'} if label in ('A','C') else
        {'split-once','post-split','rest','merge-once','post-merge','route','move-stage-once','move-stage-post',
         'advance-stage-day','recover-stage-day','advance-common-horizon','recover-common-horizon-day'})
    normal.need(o.stage in choices,'Stage is not an existing operation for this arm')
    normal.need(datetime.now(timezone.utc).timestamp()<request['original_hold_deadline']-request['reserve_seconds'],'Original hold reserve reached')
    result={'run_id':request['run_id'],'reviewer':request['operator_reviewer'],'machine_id':request['machine_id'],'label':label,'stage':o.stage}
    if o.army_id is not None:
        normal.need(label=='B' and type(o.army_id) is int and o.army_id>=0,'Actual B public Army ID required')
        result['army_id']=o.army_id
    if o.day_start_raw is not None:result['day_start_raw']=o.day_start_raw
    if o.arrival_arm:result['arrival_arm']=normal.pin(o.arrival_arm)
    if o.stage in ('move-stage-once','move-stage-post'):normal.need(o.army_id is not None,'B role Move needs its actual Army ID')
    if o.stage in ('recover-stage-day','recover-common-horizon-day'):normal.need(o.day_start_raw is not None,'Recovery needs original day start; never a new Arm')
    output=o.awaiting.with_name(o.awaiting.name.replace('-awaiting.json','-root-result.json'))
    normal.need(output!=o.awaiting,'Exact awaiting filename required')
    print(json.dumps({'output':str(output),'body':result,'written':bool(o.write)},ensure_ascii=False))
    if o.write:write(output,result)

def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='mode',required=True)
    b=sub.add_parser('bind');b.add_argument('--spec',type=Path,required=True);b.add_argument('--runtime',type=Path,required=True)
    b.add_argument('--capacity',type=Path,required=True);b.add_argument('--scene',type=Path,required=True)
    b.add_argument('--output',type=Path,required=True);b.add_argument('--frozen-plan',type=Path)
    b.add_argument('--label',choices=('A','B','C'),default='A')
    f=sub.add_parser('freeze');f.add_argument('--capture',type=Path,required=True);f.add_argument('--evidence-root',type=Path,required=True)
    f.add_argument('--repo-root',type=Path,default=REPO);f.add_argument('--output',type=Path,required=True)
    s=sub.add_parser('stage');s.add_argument('--awaiting',type=Path,required=True)
    s.add_argument('--stage',required=True);s.add_argument('--army-id',type=int);s.add_argument('--day-start-raw',type=int)
    s.add_argument('--arrival-arm',type=Path)
    s.add_argument('--write',action='store_true')
    o=p.parse_args();{'bind':bind,'freeze':freeze,'stage':stage}[o.mode](o)
if __name__=='__main__':main()
