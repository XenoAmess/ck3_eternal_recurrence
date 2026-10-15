"""Read-only exact-frame R12/R13 consequence checks; never sends a game command."""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path

class EvidenceError(ValueError):pass
def require(ok,message):
    if not ok:raise EvidenceError(message)
def integer(value,name,minimum=None):
    require(type(value) is int and (minimum is None or value>=minimum),name+' integer missing')
    return value
def amount(value,name,nullable=False):
    if value is None and nullable:return None
    require(type(value) is dict and set(value)=={'raw','scale'},name+' fixed shape missing')
    require(type(value['raw']) is int and -(2**63)<=value['raw']<2**63,name+' signed64 missing')
    require(type(value['scale']) is int and value['scale']==100000,name+' Q100000 missing')
    return value['raw']
def frame(snapshot,strength,binding):
    require(type(snapshot) is dict and type(strength) is dict,'frame objects missing')
    require(snapshot.get('paused') is True and snapshot.get('map_ready') is True,'not paused map')
    actor=snapshot.get('played_character') or {};diag=snapshot.get('diagnostics') or {}
    require(actor.get('character_id')==binding['actor'] and actor.get('alive') is True,'owner/death drift')
    require(not snapshot.get('active_event') and not snapshot.get('pending_character_interaction'),'modal requires owner handling')
    require(diag.get('bridge_pid')==binding['pid'] and diag.get('connection_generation')==binding['generation'],'PID/connection drift')
    require(snapshot.get('episode_run_id')==binding['episode'],'episode drift')
    integer(snapshot.get('date_raw'),'date',1)
    for key in ('revision','native_revision'):integer(snapshot.get(key),key,1)
    require(strength.get('accepted') is True and strength.get('step')=='query-army-strengths-v1','not a successful strength read')
    for left,right in (('queried_snapshot_id','snapshot_id'),('queried_revision','revision'),('queried_native_revision','native_revision'),('queried_date_raw','date_raw')):
        require(strength.get(left)==snapshot.get(right),'strength/snapshot '+right+' mismatch')
    require(strength.get('queried_connection_generation')==binding['generation'] and strength.get('queried_episode_run_id')==binding['episode'],'strength session drift')
    rows=strength.get('army_strengths');require(type(rows) is list,'Army rows missing')
    selected=[r for r in rows if type(r) is dict and r.get('army_id')==binding['army_id']]
    require(len(selected)==1,'selected Army absent/ambiguous')
    row=selected[0];require(row.get('status')=='available','selected strength unavailable')
    require(row.get('native_carmy_id')==binding['native_carmy_id'],'native full Army generation drift')
    armies=[r for r in snapshot.get('player_armies',[]) if r.get('army_id')==binding['army_id']]
    require(len(armies)==1,'player Army absent/ambiguous')
    army=armies[0]
    require(army.get('controllable') is True and army.get('owner_character_id')==binding['actor'],'control drift')
    require(army.get('in_combat') is False and army.get('retreating') is False,'combat/retreat intervened')
    route=army.get('route_province_ids');require(type(route) is list and all(type(p) is int and p>0 for p in route),'route payload malformed')
    require(type(army.get('route_source_count')) is int and army['route_source_count']==len(route),'route native count mismatch')
    require(army.get('route_read_status')==('complete_nonempty' if route else 'complete_empty'),'route not a complete native copy')
    if route:
        require(army.get('move_target_observable') is True and army.get('move_target_province_id')==route[-1],'complete route target does not match existing native contract')
    movement=row.get('current_movement_progress');require(type(movement) is dict,'movement block missing')
    require(movement.get('source')=='native_current_route_edge','movement source differs')
    return {'snapshot':snapshot,'strength':strength,'army':army,'movement':movement,'route':route,
            'province':integer(army.get('current_province_id'),'Province',1),'date':snapshot['date_raw']}
def stationary(observation):
    a=observation['army']
    require(observation['route']==[],'stationary baseline/arrival still has a route')
    require(a.get('army_state') in {'regular','embarked'},'stationary raw state unrecognized')
    # An explicitly unobservable target is preserved as unknown, never cleared.
    if a.get('move_target_observable') is True:
        require(a.get('move_target_province_id') is None,'observable target still present')
def admit_locked(observation):
    route=observation['route'];require(len(route)>=2 and route[0]!=route[-1],'not a distinct-front/tail multi-hop case')
    movement=observation['movement'];require(movement.get('status')=='available','movement progress unavailable')
    progress=amount(movement.get('normalized_edge_progress'),'actual progress')
    cutoff=amount(movement.get('loaded_movement_lock_cutoff'),'actual loaded cutoff')
    require(progress>cutoff,'actual progress does not exceed actual loaded cutoff')
    remaining=amount(movement.get('first_route_edge_remaining_duration'),'actual first edge remaining')
    require(remaining>=0,'first-edge remaining is negative')
    return {'front':route[0],'tail':route[-1],'progress_raw':progress,'cutoff_raw':cutoff,
            'first_edge_remaining_q100000':remaining,'consequence_day_limit':(remaining+99999)//100000+2}
def same_paused_applied(before,after):
    require(before['date']==after['date'] and before['province']==after['province'],'immediate consequence crossed date/Province')
    for key in ('revision','native_revision'):
        require(after['snapshot'][key]>before['snapshot'][key],'no independent later native publication')
def preview_path(value,observation,target):
    require(type(value) is dict,'preview result missing')
    p=value.get('route_preview') or {};route=p.get('route_province_ids')
    require(value.get('accepted') is True and p.get('status')=='available','native preview unavailable/rejected')
    require(p.get('army_id')==observation['army']['army_id'] and p.get('origin_province_id')==observation['province'] and p.get('target_province_id')==target,'preview subject/origin/target differs')
    require(type(route) is list and all(type(x) is int and x>0 for x in route),'preview route malformed')
    if route and route[0]==observation['province']:route=route[1:]
    require(route and route[-1]==target,'preview does not reach requested target')
    require(p.get('previewed_date_raw')==observation['date'],'preview date differs')
    for left,right in (('queried_snapshot_id','snapshot_id'),('queried_revision','revision'),('queried_native_revision','native_revision')):
        require(value.get(left)==observation['snapshot'][right],'preview native frame differs')
    require(value.get('queried_connection_generation')==observation['snapshot']['diagnostics']['connection_generation']
            and value.get('queried_episode_run_id')==observation['snapshot']['episode_run_id'],'preview session differs')
    return route
def action_once(request,response,step,before):
    require(type(request) is dict and type(response) is dict,'action request/result missing')
    arguments=request.get('arguments');require(type(arguments) is dict,'action arguments missing')
    move=re.fullmatch(r'move-army-([1-9][0-9]*)-to-([1-9][0-9]*)',step)
    if move:
        require(request.get('tool')=='ck3_move_army'
                and type(arguments.get('army_id')) is int and arguments['army_id']==int(move[1])
                and type(arguments.get('target_province_id')) is int and arguments['target_province_id']==int(move[2]),'Move must use existing typed ck3_move_army')
    else:
        require(request.get('tool')=='ck3_execute_step' and arguments.get('step')==step,'wrong Halt action request')
    require(arguments.get('expected_revision')==before['snapshot']['revision'],'action did not bind fresh locked frame')
    require(response.get('accepted') is True and response.get('step')==step,'action rejected/unknown; preserve outcome and do not resend')
def r12(locked,post,arrival,request,response):
    admission=admit_locked(locked);action_once(request,response,'halt-army-'+str(locked['army']['army_id']),locked)
    same_paused_applied(locked,post)
    require(post['route']==[admission['front']],'Halt did not actually remove just the suffix')
    require(amount(post['movement'].get('normalized_edge_progress'),'post progress')==admission['progress_raw'],'Halt did not retain locked progress')
    require(amount(post['movement'].get('loaded_movement_lock_cutoff'),'post cutoff')==admission['cutoff_raw'],'loaded cutoff changed during action')
    stationary(arrival);require(arrival['province']==admission['front'],'actual Army did not reach original front')
    delta=arrival['date']-locked['date'];require(delta>0 and delta%24==0 and delta//24<=admission['consequence_day_limit'],'R12 consequence is outside native remaining+2 day window')
    return {'case':'R12','status':'ACTUAL-CONSEQUENCE-PASS','locked':admission,'arrival_province':arrival['province'],'elapsed_actual_days':delta//24,'raw_target_observable':arrival['army'].get('move_target_observable')}
def r13(locked,post,first_arrival,arrival,preview,request,response,alt):
    admission=admit_locked(locked)
    require(alt not in {locked['province'],admission['front'],admission['tail']},'alternate equals current/front/old tail shortcut')
    proposed=preview_path(preview,locked,alt)
    require(proposed[0]==admission['front'] and admission['tail'] not in proposed[1:],'preview does not preserve first edge and genuinely branch before old tail')
    action_once(request,response,'move-army-'+str(locked['army']['army_id'])+'-to-'+str(alt),locked)
    same_paused_applied(locked,post)
    require(post['route']==proposed and post['route'][0]==admission['front'] and post['route'][1:]!=locked['route'][1:],'new committed route does not match actual alternate preview')
    require(amount(post['movement'].get('normalized_edge_progress'),'post progress')==admission['progress_raw'],'reroute did not retain first-edge progress')
    require(amount(post['movement'].get('loaded_movement_lock_cutoff'),'post cutoff')==admission['cutoff_raw'],'loaded cutoff changed during reroute')
    require(first_arrival['province']==admission['front'] and first_arrival['date']>locked['date'],'first locked edge actual arrival missing')
    first_delta=first_arrival['date']-locked['date']
    require(first_delta%24==0 and first_delta//24<=admission['consequence_day_limit'],'first locked edge arrival outside native remaining+2 window')
    require(first_arrival['route'] and first_arrival['route'][-1]==alt,'new suffix not observed after first edge')
    stationary(arrival);require(arrival['province']==alt and arrival['date']>=first_arrival['date'],'alternate destination not actually reached')
    delta=arrival['date']-locked['date'];require(delta>0 and delta%24==0,'actual destination date is not later natural time')
    return {'case':'R13','status':'ACTUAL-CONSEQUENCE-PASS','locked':admission,'actual_new_route':post['route'],'old_tail_avoided':admission['tail'],'first_arrival_province':first_arrival['province'],'actual_alternate_destination':arrival['province'],'elapsed_actual_days':delta//24}

class PinnedReader:
    def __init__(self,roots,base_dir=None):
        self.base_dir=Path(base_dir).resolve() if base_dir is not None else Path.cwd().resolve()
        self.roots=[self.resolve(r) for r in roots];self.bytes=0;self.pins=[]
    def resolve(self,value):
        path=Path(value)
        return (path if path.is_absolute() else self.base_dir/path).resolve()
    def read(self,ref):
        require(type(ref) is dict and type(ref.get('path')) is str,'precise file reference missing')
        path=Path(ref['path']);path=path if path.is_absolute() else self.base_dir/path
        require(not path.is_symlink(),'non-symlink evidence required')
        resolved=path.resolve();require(any(resolved==r or r in resolved.parents for r in self.roots),'evidence outside explicit owned roots')
        n=integer(ref.get('bytes'),'ref bytes',1);require(n<=16*1024*1024 and self.bytes+n<=64*1024*1024,'finite input read budget exceeded')
        with path.open('rb') as stream:
            b=stream.read(n+1)
        require(len(b)==n and hashlib.sha256(b).hexdigest()==ref.get('sha256'),'exact evidence bytes/hash changed')
        self.bytes+=n;self.pins.append(ref);value=json.loads(b)
        return value.get('body',value) if type(value) is dict else value
def audit_manifest(value,*,base_dir=None):
    machine=value.get('machine_id')
    require(type(machine) is str and bool(machine.strip()) and machine!='unknown','explicit source machine ID missing')
    require(value.get('case') in {'R12','R13'} and type(value.get('case_id')) is str and value['case_id'],'explicit independent case identity missing')
    binding=value['binding'];require(value.get('action_count')==1 and value.get('initial_move_count')==1,'exactly one normal initial Move and one case action required')
    reader=PinnedReader(value['owned_evidence_roots'],base_dir=base_dir)
    session=reader.read(value['session_receipt'])
    require(session.get('machine_id')==machine and session.get('pid')==binding['pid'],'session receipt machine/PID mismatch')
    created=session.get('creation_filetime_100ns',session.get('process_create_time_100ns'))
    require(type(created) is int and created>0 and created==binding['process_create_time_100ns'],'exact owned process creation identity missing')
    def load_frame(key):
        group=value[key];return frame(reader.read(group['snapshot']),reader.read(group['strength']),binding)
    baseline=load_frame('baseline');stationary(baseline)
    started=load_frame('new_move_post');locked=load_frame('locked');post=load_frame('post');arrival=load_frame('arrival')
    initial_request=reader.read(value['initial_move_request']);initial_response=reader.read(value['initial_move_response'])
    initial_target=integer(value['initial_target'],'initial target',1)
    initial_preview=preview_path(reader.read(value['initial_preview']),baseline,initial_target)
    action_once(initial_request,initial_response,'move-army-'+str(binding['army_id'])+'-to-'+str(initial_target),baseline)
    same_paused_applied(baseline,started)
    require(len(started['route'])>=2 and started['route'][-1]==initial_target,'new normal Move did not form a multi-hop route')
    require(started['route']==initial_preview,'normal new Move path differs from its actual input preview')
    require(locked['date']>=started['date'] and locked['province']==started['province'] and locked['route']==started['route'],'not the same initial route/first edge at lock admission')
    request=reader.read(value['action_request']);response=reader.read(value['action_response'])
    if value['case']=='R12':result=r12(locked,post,arrival,request,response)
    else:result=r13(locked,post,load_frame('first_arrival'),arrival,reader.read(value['alternate_preview']),request,response,integer(value['alternate_target'],'alternate',1))
    require(arrival['date']-locked['date']<=integer(value['maximum_natural_days'],'maximum natural days',1)*24,'declared finite case day budget exceeded')
    clocks=value.get('daily_clock_results');require(type(clocks) is list and clocks,'actual contiguous daily sentinel results missing')
    expected_start=started['date'];generations=set()
    for ref in clocks:
        clock_result=reader.read(ref);clock=clock_result.get('tactical_daily_sentinel') if type(clock_result) is dict else None
        require(type(clock) is dict and clock.get('state')=='triggered','daily sentinel did not actually trigger')
        require(clock.get('starting_date_raw')==expected_start and clock.get('target_date_raw')==expected_start+24
                and clock.get('trigger_date_raw')==expected_start+24 and clock.get('completed_daily_ticks')==1,'daily sentinel sequence/gap/overshoot')
        require(clock.get('abnormal') is False and clock.get('pause_observed') is True
                and clock.get('pause_wrapper_called') is True and clock.get('overshoot_days')==0,'daily natural stop not verified')
        reasons=clock.get('trigger_reasons');require(type(reasons) is list and 'date_deadline' in reasons
            and set(reasons)<={'date_deadline','army_position_changed','route_target_changed'},'unexpected daily stop reason')
        generation=integer(clock.get('generation'),'sentinel generation',1);require(generation not in generations,'daily generation reused')
        generations.add(generation);expected_start+=24
    require(expected_start==arrival['date'],'daily evidence does not reach actual final endpoint')
    result.update(machine_id=machine,case_id=value['case_id'],evidence_pins=reader.pins,input_bytes=reader.bytes,
                  scope='Only supplied exact native observations; original session custody and no-load identity must be preserved by the operator. This verifier sends no commands and creates no human signoff.')
    return result
def main():
    p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    require(not args.output.exists(),'append-only audit target already exists')
    machine='unknown'
    try:
        manifest=json.loads(args.manifest.read_bytes());machine=manifest.get('machine_id','unknown')
        result=audit_manifest(manifest,base_dir=args.manifest.resolve().parent);code=0
    except (EvidenceError,KeyError,TypeError,ValueError) as error:result={'machine_id':machine,'status':'NOT-QUALIFIED','error':str(error),'game_actions_sent':0};code=1
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,ensure_ascii=False));return code
if __name__=='__main__':raise SystemExit(main())
