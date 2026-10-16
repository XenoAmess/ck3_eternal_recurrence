"""Root-invoked R0176 R09 stages; import and --help are entirely offline.

Only an explicitly invoked stage writes requests to Root's existing file relay.
No SDK import, session creation, clock advance, recorder, GUI, or byte writes.
"""
from __future__ import annotations
import argparse, ctypes, hashlib, importlib.util, json, re, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
sys.dont_write_bytecode=True

SOURCE='dcda9fde1afa1effb75d46fe99bba4bcd9aeabcb'
MACHINE='desktop-3fevhd2-1c74096080'
DEADLINE='2026-10-16T07:45:01.597+00:00'
EXE_SHA='98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518'
MAX_PACKET=16*1024*1024
MAX_DRIVER_RAW=64*1024*1024
READ_CAPS={'game.command.query-army-strengths-v1',
 'game.command.query-army-commander-candidates-v1-for-army-N'}
ACTION_CAP={'split':'game.command.split-army-half-N','merge':'game.command.merge-armies-N-with-N'}

def need(ok,message):
    if not ok:raise RuntimeError(message)
def utc():return datetime.now(timezone.utc).isoformat()
def load(path,limit=MAX_PACKET):
    path=Path(path);need(path.stat().st_size<=limit,'bounded input too large')
    b=path.read_bytes();need(len(b)<=limit,'bounded input grew')
    return json.loads(b.decode('utf-8-sig'))
def pin(path,limit=MAX_PACKET):
    path=Path(path);need(path.stat().st_size<=limit,'pin exceeds finite limit')
    b=path.read_bytes();need(len(b)<=limit,'pin input grew')
    return {'path':str(path.resolve()),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def driver_raw_pin(path):
    path=Path(path)
    need(path.parent.name=='army-query-history-results','64MiB applies only to a response-local Driver Army raw result')
    return {**pin(path,MAX_DRIVER_RAW),'pin_scope':'response_local_army_query_raw_v1'}
def verify_pin(value):
    actual=(driver_raw_pin(value['path']) if value.get('pin_scope')=='response_local_army_query_raw_v1' else pin(value['path']))
    need(actual==value,'pinned evidence changed');return actual
def write_new(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    b=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    need(len(b)<=2*1024*1024,'derived receipt exceeds2MiB; preserve raw refs')
    with path.open('xb') as stream:stream.write(b)
    return pin(path)
def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
def process_time(pid):
    from ctypes import wintypes as W
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenProcess.restype=W.HANDLE
    k.GetProcessTimes.argtypes=[W.HANDLE,*([ctypes.POINTER(W.FILETIME)]*4)];k.GetProcessTimes.restype=W.BOOL
    k.CloseHandle.argtypes=[W.HANDLE];k.CloseHandle.restype=W.BOOL
    handle=k.OpenProcess(0x1000,False,pid);need(bool(handle),'owned process unavailable')
    try:
        values=[W.FILETIME() for _ in range(4)]
        need(k.GetProcessTimes(handle,*[ctypes.byref(v) for v in values]),'creation time unavailable')
        return values[0].dwLowDateTime|(values[0].dwHighDateTime<<32)
    finally:k.CloseHandle(handle)
def frame_key(frame):
    return [frame[k] for k in ('snapshot_id','revision','native_revision','date_raw')]
def roster(frame):
    rows=frame.get('player_armies');need(type(rows) is list and 0<len(rows)<=32,'complete bounded player roster required')
    result={}
    for row in rows:
        identity=row.get('army_id')
        need(type(identity) is int and 0<=identity<2**31 and identity not in result,'public CUnit FullID duplicate/invalid')
        need(row.get('source')=='native','public CUnit identity lacks native roster source')
        result[identity]=row
    return result
def same_frame(first,second):need(frame_key(first)==frame_key(second),'paused frame drifted; do not submit')
def admission(context,proof,*,run_id,source=SOURCE,sequence=176):
    identity=context.get('identity',{})
    need(context.get('machine_id')==MACHINE and identity.get('machine_id')==MACHINE,'machine binding differs')
    need(re.fullmatch('[0-9a-f]{40}',source) is not None
         and context.get('source_head')==source and proof.get('source_head')==source,'reviewed normal source differs')
    need(type(sequence) is int and sequence>=176 and identity.get('run_id')==run_id
         and identity.get('sequence')==sequence and identity.get('mod_key')=='vanilla'
         and run_id==MACHINE+'--vanilla--R'+str(sequence).zfill(4),'actual explicitly allocated run differs')
    need(proof.get('machine_id')==MACHINE and proof.get('run_id')==run_id,'runtime proof belongs to another run')
    intent=proof.get('stable_character_intent',{})
    need(intent.get('historical_id')==1128 and intent.get('bookmark_character_name_key')=='bookmark_rags_to_riches_duke_robert',
         'normal Robert intent missing')
    binding={k:proof.get(v) for k,v in {
      'pid':'pid','process_create_time_100ns':'process_creation_filetime_100ns',
      'generation':'connection_generation','actor':'actual_runtime_character_full_id','episode':'episode_run_id'}.items()}
    need(all(type(binding[k]) is int and binding[k]>0 for k in ('pid','process_create_time_100ns','generation','actor')),
         'actual positive runtime identities missing')
    need(type(binding['episode']) is str and binding['episode'],'actual episode missing')
    return binding
def validate_frame(frame,binding):
    d=frame.get('diagnostics') or {};hello=d.get('hello') or {};actor=frame.get('played_character') or {}
    need(frame.get('paused') is True and frame.get('map_ready') is True and d.get('connected') is True,'paused connected map required')
    need(d.get('bridge_pid')==binding['pid'] and d.get('connection_generation')==binding['generation']
         and frame.get('episode_run_id')==binding['episode'] and actor.get('character_id')==binding['actor']
         and actor.get('alive') is True,'fresh frame crossed runtime/actor')
    need(hello.get('expected_ck3_version')=='1.20.0.4'
         and str(hello.get('expected_ck3_sha256','')).lower()==EXE_SHA
         and hello.get('game_adapter_status')=='ready' and hello.get('ck3_build_match') is True,'exact actual4 adapter not ready')
    need(hello.get('pid')==binding['pid'] and hello.get('connection_generation')==binding['generation'],
         'hello process/connection differs')
    need(not frame.get('active_event') and not frame.get('pending_character_interaction'),'Root must resolve modal with existing policy')
    need(type(frame.get('revision')) is int and type(frame.get('native_revision')) is int
         and type(frame.get('date_raw')) is int and isinstance(frame.get('snapshot_id'),str),'frame identity incomplete')
    roster(frame)
def action_gate(frame,caps,step,kind,ids,actor):
    need(caps.get('backend_id')=='native-headless' and caps.get('fallback_enabled') is False,'native ordinary route required')
    advertised=caps.get('bridge_capabilities',[])
    need(READ_CAPS|{ACTION_CAP[kind]}<=set(advertised),'actual native capabilities absent')
    need(step in caps.get('action_steps',[]),'current semantic step not advertised; preserve actual reason')
    rows=roster(frame)
    for identity in ids:
        row=rows.get(identity,{})
        need(row.get('controllable') is True and row.get('owner_character_id')==actor,'selected army not current owned controllable CUnit')
        need(row.get('in_combat') is False and row.get('retreating') is False,'combat/retreat blocks controlled experiment')
    if kind=='merge':
        need(rows[ids[0]].get('current_province_id')==rows[ids[1]].get('current_province_id'),
             'merge pair is not at the same actual province')
    # Advertisement is not CanExecute. SubmitSplit/SubmitMerge call CK3's actual
    # validator before enqueue. False (including sea restrictions) is final here.
    return {'advertised':True,'native_validator_result_before_submission':None,
            'native_validator_is_authoritative':True,'sea_legality_inferred':False}

def compare_data_roles(consumer,old_armies,new_armies):
    """Actual DATA comparison; explicitly does not close all merge callee effects."""
    old,physical0,occ0=consumer._observe(old_armies)
    new,physical1,occ1=consumer._observe(new_armies)
    added,removed=sorted(set(new)-set(old)),sorted(set(old)-set(new))
    reasons=[]
    if physical0!=physical1:reasons.append('unique_physical_DATA_changed')
    if occ0!=occ1:reasons.append('DATA_occurrence_or_backlink_changed')
    changed=[i for i in set(old)&set(new) if old[i]['signature']!=new[i]['signature']]
    if changed:reasons.append('original_ArRg_DATA_order_or_values_changed')
    role_added=[i for i in added if consumer._empty_character(new[i])]
    role_removed=[i for i in removed if consumer._empty_character(old[i])]
    if len(role_added)!=len(added) or len(role_removed)!=len(removed):reasons.append('unexplained_ArRg_birth_or_removal')
    def role_rows(rows):
        return [{'army_regiment_id':i,'army_id':v['army_id'],
          'native_character_role_v1':v['data'].get('native_character_role_v1'),
          'cache_current_max':[v['strength']['current_soldiers'],v['strength']['maximum_soldiers']],
          'DATA_count':v['data']['native_data_record_count']} for i,v in sorted(rows.items())]
    def total(rows):return [sum(v[index] for v in rows.values()) for index in (0,1)]
    return {'accepted':not reasons,'reasons':reasons,'added_empty_Character_1_1_ids':role_added,
      'removed_empty_Character_1_1_ids':role_removed,'added_ids':added,'removed_ids':removed,
      'unique_physical_before_current_max':total(physical0),'unique_physical_after_current_max':total(physical1),
      'roles_before':role_rows(old),'roles_after':role_rows(new),
      'birth_producer_observed':False,'physical_soldier_write_observed':False,'actual_physical_refill':None,
      'native_Knight_membership':None}

def resume_baseline_strengths(path,*,run,frame,capabilities,binding):
    path=Path(path).resolve();run=Path(run).resolve()
    exact='r09-land-baseline-a02-003-baseline-strengths'
    need(path.parent==run/'responses' and path.name==exact+'.json','only the exact original R0176 baseline response may resume')
    need(frame_key(frame)[1:]==[45,44,53146632],'fresh paused resume frame differs from original native44/revision45/date53146632')
    original=load(path);request=original.get('request') or {}
    need(original.get('machine_id')==MACHINE and original.get('is_error') is False
         and request.get('request_id')==exact and request.get('tool')=='ck3_query_army_strengths',
         'original baseline response identity/tool differs')
    expected={'army_ids':sorted(roster(frame)),'expected_revision':45,'profile':'ordinary_core_v1'}
    need(request.get('arguments')==expected,'original baseline request scope differs from fresh complete roster/frame')
    frame_path=path.with_name('r09-land-baseline-a02-001-baseline-frame.json')
    caps_path=path.with_name('r09-land-baseline-a02-002-baseline-capabilities.json')
    old_frame=load(frame_path);old_caps=load(caps_path)
    for value in (old_frame,old_caps):
        need(value.get('machine_id')==MACHINE and value.get('is_error') is False,'original baseline sibling response invalid')
    need(old_frame.get('request',{}).get('tool')=='ck3_take_snapshot'
         and old_caps.get('request',{}).get('tool')=='ck3_get_capabilities','original sibling tools differ')
    validate_frame(old_frame['body'],binding);same_frame(old_frame['body'],frame)
    need(sorted(roster(old_frame['body']))==expected['army_ids'],'original complete roster differs')
    for key in ('backend_id','fallback_enabled','bridge_capabilities','action_steps'):
        need(old_caps['body'].get(key)==capabilities.get(key),'fresh capability differs from original baseline: '+key)
    request_path=run/'requests'/path.name
    need(load(request_path)==request,'exact original request file differs')
    reference=(original.get('army_history_evidence') or {}).get('raw_result_reference') or {}
    need(reference.get('bytes')==38751601 and reference.get('sha256')=='e7546e83cb79fe33be30a4454a7c65e2f07b4adf1e34c7555ad002e2272e547a',
         'Root-pinned original39MB baseline raw reference differs')
    refs={'request':pin(request_path),'response':pin(path)}
    return original,refs,{'original_frame_response':pin(frame_path),'original_capabilities_response':pin(caps_path),
      'original_strength_response':pin(path),'new_strength_query_submitted':False,
      'same_fresh_paused_frame_verified':True,'old_request_scope_equals_fresh_roster':True}

def selected_available_cohorts(armies,frame,selected_id):
    need(type(selected_id) is int and 0<=selected_id<2**31,'selected public FullID required')
    rows=roster(frame);available=[];excluded=[]
    for army in armies:
        identity=army['army_id']
        if army.get('status')=='available':available.append(army);continue
        need(identity==16777321 and army.get('status')=='unavailable'
             and army.get('unavailable_reason')=='native_carmy_not_found',
             'unavailable selected/new/unexpected Army cannot be excluded')
        binding={key:rows[identity].get(key) for key in ('army_id','source','owner_character_id','current_province_id','controllable')}
        excluded.append({'army_id':identity,'status':army['status'],'unavailable_reason':army['unavailable_reason'],
          'snapshot_roster_binding':binding,
          'native_query_row_projection':{key:army.get(key) for key in ('army_id','native_carmy_id','status','unavailable_reason','regiment_count','current_soldiers','maximum_soldiers')},
          'complete_native_query_row_preserved_in_pinned_strength_raw':True,
          'strengths_qualified':False,'troop_values_filled_with_zero':False,'unit_type_name':None})
    need(selected_id in {army['army_id'] for army in available},'selected Army unavailable; cannot proceed')
    return available,excluded

def merge_ids(source,sibling,destination):
    need(destination in ('source','sibling'),'explicit merge direction required')
    need(type(source) is int and type(sibling) is int and source!=sibling,'distinct actual pair required')
    return [source,sibling] if destination=='source' else [sibling,source]

def compare_merge_supply(before,after,ids):
    """Observed D/S operands; caller separately binds frames and complete DATA."""
    old={a['army_id']:a for a in before['query']['army_strengths']}
    new={a['army_id']:a for a in after['query']['army_strengths']}
    d,s=ids;destination,source,post=old[d],old[s],new[d]
    required=('current_supply_raw','current_supply_scale','current_supply_capacity_raw','current_supply_capacity_scale')
    missing=[str(a['army_id'])+':'+key for a in (destination,source,post) for key in required if type(a.get(key)) is not int]
    missing += ['destination_native_weight'] if type(destination.get('merge_supply_destination_weight_raw')) is not int else []
    if missing:return {'status':'HOLD_NATIVE_SUPPLY_OR_WEIGHT_UNAVAILABLE','missing':missing,'upper_clamp_observed':False}
    need(all(a['current_supply_scale']==a['current_supply_capacity_scale']==100000 for a in (destination,source,post))
         and destination.get('merge_supply_destination_weight_scale')==100000,'native Q100000 scale differs')
    need(all(a['current_supply_raw']>=0 and a['current_supply_capacity_raw']>=0 for a in (destination,source,post)),
         'negative current stock/capacity is outside this positive branch')
    wd=destination['merge_supply_destination_weight_raw'];ws=source['current_soldiers']*100000
    need(type(source['current_soldiers']) is int and min(wd,ws)>=0,'native weights unavailable or negative')
    if wd+ws==0:return {'status':'HOLD_ZERO_NATIVE_WEIGHT_BRANCH','upper_clamp_observed':False}
    # Actual .4 2C55FD7..2C55FEF switches division algorithms above this
    # numerator range; 2C5607F..2C56093 similarly guards multiplication.
    # The unrestricted Python rational formula is not that fallback evaluator.
    div_max=0x53E2D6238DA3;mul_max=0xB504F333
    if any(weight>div_max or weight>0 and army['current_supply_raw']>mul_max
           for weight,army in zip((wd,ws),(destination,source))):
        return {'status':'HOLD_NATIVE_FIXED_FALLBACK_BRANCH','upper_clamp_observed':False,
          'native_fast_div_numerator_max':div_max,'native_fast_mul_operand_max':mul_max,
          'native_fallback_modelled':False,'full_card_closed':False}
    shares=[w*100000//(wd+ws) for w in (wd,ws)]
    contributions=[share*a['current_supply_raw']//100000 for share,a in zip(shares,(destination,source))]
    preclamp=sum(contributions);capacity=post['current_supply_capacity_raw'];expected=max(0,min(capacity,preclamp))
    matches=post['current_supply_raw']==expected
    return {'status':'NATIVE_WEIGHTED_SUPPLY_MATCH' if matches else 'NATIVE_WEIGHTED_SUPPLY_MISMATCH',
      'destination_army_id':d,'source_army_id':s,'weights_raw':[wd,ws],
      'source_weight_basis':'native current_soldiers getter checked against complete ArRg sum; not source destination-role weight',
      'stocks_raw':[destination['current_supply_raw'],source['current_supply_raw']],
      'shares_raw':shares,'contributions_raw':contributions,'preclamp_raw':preclamp,
      'post_actual_capacity_raw':capacity,'expected_stock_raw':expected,'actual_stock_raw':post['current_supply_raw'],
      'weighted_supply_match':matches,'upper_clamp_observed':matches and preclamp>capacity,
      'distinct_pre_stock_observed':destination['current_supply_raw']!=source['current_supply_raw'],
      'capacity_predicted_from_quality':False,'source_PC_execution_observed':False,'full_card_closed':False}

def selected_query_ids(frame,army_ids=None,*,split_before_roster=None):
    """Query scope never changes the complete native snapshot roster."""
    current=roster(frame)
    if army_ids is None:
        need(split_before_roster is None,'split delta requires explicit strategy scope')
        return sorted(current)
    need(type(army_ids) is list and 0<len(army_ids)<=32
         and all(type(i) is int and 0<=i<2**31 for i in army_ids)
         and len(set(army_ids))==len(army_ids),'complete distinct selected Army IDs required')
    ids=set(army_ids)
    if split_before_roster is not None:
        need(type(split_before_roster) is list and len(set(split_before_roster))==len(split_before_roster),
             'complete pre-split roster IDs required')
        old=set(split_before_roster);added=set(current)-old
        need(len(ids)==1 and ids<=old and len(added)==1 and set(current)==old|added,
             'fresh split requires exact full snapshot addition and no removal')
        ids|=added
    need(ids<=set(current),'selected Army absent from complete snapshot roster')
    return sorted(ids)


class Relay:
    def __init__(self,args,*,transport=None,process_probe=process_time):
        self.a=args;self.repo=args.repo.resolve();self.process_probe=process_probe
        self.source=getattr(args,'source_head',SOURCE);self.sequence=getattr(args,'run_sequence',176)
        if self.sequence==176:need(self.source==SOURCE and args.army_id==93,'historical R0176 scope remains exact')
        need(pin(Path(__file__))['sha256']==args.self_sha256,'reviewed stage helper SHA differs')
        for path,expected in ((args.context,args.context_sha256),(args.runtime_proof,args.runtime_proof_sha256),
                              (args.request_helper,args.request_helper_sha256)):
            need(pin(path)['sha256']==expected,'actual Root input SHA differs: '+str(path))
        head=subprocess.check_output(['git','-C',str(self.repo),'rev-parse','HEAD'],text=True).strip()
        need(head==self.source,'reviewed actual checkout changed')
        pins_path=getattr(args,'module_pins',None) or Path(__file__).with_name('MODULES.pins.json')
        if getattr(args,'module_pins',None):
            need(pin(pins_path)['sha256']==getattr(args,'module_pins_sha256',None),'reviewed producer pins SHA differs')
        pins=load(pins_path)
        expected_pin_keys=set(load(Path(__file__).with_name('MODULES.pins.json'))['repository_files'])
        need(set(pins.get('repository_files',{}))==expected_pin_keys,'reviewed producer file set changed')
        for rel,expected in pins['repository_files'].items():
            need(pin(self.repo/rel)['sha256']==expected,'production consumer/source changed: '+rel)
        self.sidecar=Path(__file__).with_name('army_split_transfer_assertions_12004.py')
        need(pin(self.sidecar)['sha256']==pins['split_consumer_sha256'],'closed freshsplit consumer changed')
        sys.path.insert(0,str(self.repo/'ck3_autonomous_player/src'))
        from xar_autoplayer.bridge import army_split_merge_observation_12004 as observation
        from xar_autoplayer.bridge.army_replenishment_records_contract import normalize_regiment_replenishment_records_v1
        self.observation=observation;self.normalize=normalize_regiment_replenishment_records_v1
        self.consumer=module(self.sidecar,'r09_pinned_freshsplit')
        self.c=load(args.context);proof=load(args.runtime_proof)
        self.binding=admission(self.c,proof,run_id=args.run_id,source=self.source,sequence=self.sequence)
        self.assets=args.context.resolve().parent;self.run=self.assets/args.run_id
        need(self.run.is_dir(),'Root existing run missing')
        self.case=self.assets/'r09-split-merge-relay-a01'/args.case_id
        need(re.fullmatch('[A-Za-z][A-Za-z0-9_-]{0,47}',args.case_id) is not None
             and re.fullmatch('[A-Za-z][A-Za-z0-9_-]{0,47}',args.attempt) is not None,'safe case/attempt required')
        self.attempt=self.case/args.attempt;self.attempt.mkdir(parents=True,exist_ok=False)
        self.meta={'machine_id':MACHINE,'observed_at_utc':utc(),'source_head':self.source,'run_id':args.run_id,
          'context':pin(args.context),'runtime_proof':pin(args.runtime_proof),'helper':pin(Path(__file__)),
          'request_helper':pin(args.request_helper),'consumer':pin(self.sidecar),'binding':self.binding,
          'deadline_utc':DEADLINE,'case_id':args.case_id,'stage':args.stage,'SDK_connection_created':False,
          'capture_started':False,'time_advanced':False,'unknown_action_retried':False,
          'merge_destination':getattr(args,'merge_destination','source'),
          'explicit_merge_source_army_id':getattr(args,'merge_source_army_id',None),'module_pins':pin(pins_path)}
        capacity_path=Path(self.c['capacity_admission']);capacity=load(capacity_path)
        shared_limit=capacity.get('shared_child_limit_bytes')
        if 'original_shared_child_total_limit_bytes' in capacity:
            need('shared_child_limit_bytes' not in capacity
                 and capacity.get('source_head')==self.source
                 and capacity.get('Root_sole_game_SDK_recorder_owner') is True
                 and capacity.get('new_scene_count')==1 and capacity.get('deadline_extensions')==0
                 and Path(capacity.get('new_assets_root','')).resolve()==self.assets.resolve(),
                 'actual R13 capacity schema/source/assets differs')
            shared_limit=capacity['original_shared_child_total_limit_bytes']
        need(capacity.get('machine_id')==MACHINE and capacity.get('admitted') is True
             and shared_limit==512*1024*1024
             and datetime.fromisoformat(capacity['quota_review_at_utc'])==datetime.fromisoformat(DEADLINE),
             'actual Root admission/shared pool/original deadline differs')
        self.meta['capacity_admission']=pin(capacity_path)
        fixed=self.case/'binding.actual.json'
        if fixed.exists():
            prior=load(fixed)
            for key in ('source_head','run_id','context','runtime_proof','helper','request_helper','consumer','binding','deadline_utc','capacity_admission','merge_destination','explicit_merge_source_army_id','module_pins'):
                need(prior[key]==self.meta[key],'case changed pinned identity/source/deadline: '+key)
        else:write_new(fixed,self.meta)
        self.serial=0;self.pending=False
        self.check_process()
        self.transport=transport if transport is not None else module(args.request_helper,'r09_existing_root_transport')
        need(Path(self.transport.RUN).resolve()==self.run.resolve()
             and Path(self.transport.ASSETS).resolve()==self.assets.resolve()
             and self.transport.CONTEXT==self.c,'reviewed Root transport context/run differs')
        write_new(self.attempt/'START.actual.json',self.meta)
    def check_process(self):
        need(self.process_probe(self.binding['pid'])==self.binding['process_create_time_100ns'],'PID/create-time differs')
    def request(self,name,tool,arguments):
        need(datetime.now(timezone.utc)<=datetime.fromisoformat(DEADLINE),'original deadline reached')
        self.check_process();self.serial+=1;identifier=self.a.attempt+'-'+str(self.serial).zfill(3)+'-'+name
        req=self.run/'requests'/(identifier+'.json');res=self.run/'responses'/req.name
        need(not req.exists() and not res.exists(),'exact request exists; inspect original, never replay')
        # One bounded request at a time. Root remains the sole heavy writer and
        # accounts other lanes; this also bounds the newly allocated run ledger.
        accounted=sum(p.stat().st_size for directory in (self.run/'requests',self.run/'responses')
                      for p in directory.iterdir() if p.is_file())
        accounted+=sum(p.stat().st_size for p in self.case.rglob('*') if p.is_file())
        need(accounted+MAX_PACKET+65536<=getattr(self,'runtime_total_budget_bytes',512*1024*1024),'admitted run/relay budget cannot admit next packet')
        self.pending=True
        try:value=self.transport.request(identifier,tool,arguments,timeout=55)
        finally:self.pending=not res.exists()
        need(res.exists(),'response not present; inspect exact original only')
        refs={'request':pin(req),'response':pin(res)}
        need(value.get('machine_id')==MACHINE and value.get('request',{}).get('request_id')==identifier,'response identity differs')
        need(value.get('is_error') is False,'actual native/MCP error retained at '+str(res))
        return value,refs
    def snapshot(self,name):
        value,refs=self.request(name,'ck3_take_snapshot',{'include_native_command_history':False})
        frame=value['body'];validate_frame(frame,self.binding);return frame,refs
    def packet(self,name,*,army_ids=None,split_before_roster=None,raw_file_limit=None):
        s,sref=self.snapshot(name+'-frame');full_roster=roster(s)
        selected=army_ids is not None
        ids=selected_query_ids(s,army_ids,split_before_roster=split_before_roster)
        cap,cref=self.request(name+'-capabilities','ck3_get_capabilities',{})
        need(READ_CAPS<=set(cap['body'].get('bridge_capabilities',[])),'actual query capabilities missing')
        resume=getattr(self.a,'resume_baseline_strength_response',None)
        if resume is not None:
            need(self.a.stage=='baseline' and name=='baseline','strength reuse is baseline-only')
            need(not (self.case/'split.once.claim.json').exists() and not (self.case/'merge.once.claim.json').exists(),
                 'baseline reuse cannot cross any action claim')
            row,qref,reused=resume_baseline_strengths(resume,run=self.run,frame=s,capabilities=cap['body'],binding=self.binding)
            write_new(self.attempt/'BASELINE-STRENGTH-REUSE.actual.json',{**self.meta,**reused})
        else:
            row,qref=self.request(name+'-strengths','ck3_query_army_strengths',{
              'army_ids':ids,'expected_revision':s['revision'],'profile':'ordinary_core_v1'})
        ev=row.get('army_history_evidence') or {};raw=ev.get('raw_result_reference') or {}
        path=Path(raw.get('path',''))
        need(path.is_absolute() and path.parent.resolve()==(self.assets/'state-a01/native-session/army-query-history-results').resolve()
             and raw.get('kind')=='complete-driver-army-query-result-json-v1' and raw.get('wire_bytes_preserved') is False,
             'response-local ordinary Driver reference missing; no latest/glob fallback')
        limit=MAX_DRIVER_RAW if raw_file_limit is None else raw_file_limit(path)
        need(type(limit) is int and 0<limit<=MAX_DRIVER_RAW,'bounded Driver input limit required')
        need(type(raw.get('bytes')) is int and 0<=raw['bytes']<=limit and path.stat().st_size<=limit,
             'response-local Driver exceeds admitted input limit; preserve raw and stop before hash/read')
        actual=driver_raw_pin(path);need(actual['bytes']==raw.get('bytes') and actual['sha256']==raw.get('sha256'),'Driver ref bytes/SHA differs')
        q=load(path,limit)
        need(ev.get('machine_id')==MACHINE and ev.get('request_id')==row['request']['request_id']
             and ev.get('query_sequence')==q.get('query_sequence'),'response-local query sequence differs')
        need(q.get('accepted') is True and q.get('status') in {'available','partial'}
             and type(q.get('query_sequence')) is int and q['query_sequence']>0
             and q.get('army_strengths_profile')=='ordinary_core_v1'
             and (q.get('army_strengths_query_scope') or {}).get('army_ids')==ids,'actual complete roster query scope/profile differs')
        for qkey,skey in (('queried_snapshot_id','snapshot_id'),('queried_revision','revision'),
                          ('queried_native_revision','native_revision'),('queried_date_raw','date_raw'),
                          ('queried_episode_run_id','episode_run_id')):
            need(q.get(qkey)==s.get(skey),'query frame differs: '+qkey)
        need(q.get('queried_connection_generation')==self.binding['generation'],'query connection differs')
        armies=q.get('army_strengths');need(type(armies) is list and sorted(v.get('army_id') for v in armies)==ids,'incomplete Army strength map')
        if selected:
            need(q.get('status')=='available' and (q.get('army_strengths_query_scope') or {}).get('published_scope_status')=='available'
                 and all(a.get('status')=='available' for a in armies),'actual selected query unavailable; no row deletion or zero fill')
            available,excluded=armies,[]
        else:available,excluded=selected_available_cohorts(armies,s,self.a.army_id)
        self.observation.compare_split_merge_cohorts(available,available)
        commanders={};commander_refs={}
        for army in available:
            identity=army['army_id'];normalized=self.normalize(army['regiment_replenishment_records_v1'])
            for data in normalized:
                role=data.get('native_character_role_v1')
                need(role is not None and role.get('status')=='available'
                     and role.get('same_ArRg_instance_after') is True
                     and role.get('native_carmy_id')==army['native_carmy_id'],'complete actual role leaf required')
            value,refs=self.request(name+'-commander-'+str(identity),'ck3_query_army_commander_candidates_v1',
              {'army_id':identity,'expected_revision':s['revision']})
            body=value['body'];self.observation.read_bound_current_commander(body,s,army_id=identity,native_carmy_id=army['native_carmy_id'])
            # Exact literal field projection, with full original response pin.
            commanders[str(identity)]={k:body[k] for k in ('accepted','read_only','queried_snapshot_id','queried_revision','queried_native_revision')}
            commanders[str(identity)]['army_commander_candidates']={k:body['army_commander_candidates'][k]
              for k in ('army_id','native_carmy_id','date_raw','snapshot_revision','current_commander')}
            commander_refs[str(identity)]=refs
        check,checkref=self.snapshot(name+'-same-frame');same_frame(s,check)
        # Full native roster retained; large unrelated query leaves stay in pinned raw result.
        qp={k:q[k] for k in ('accepted','queried_snapshot_id','queried_revision','queried_native_revision')}
        qp['army_strengths']=[{k:army[k] for k in ('army_id','native_carmy_id','status','regiment_count',
          'current_soldiers','maximum_soldiers','regiment_strengths','regiment_replenishment_records_v1','unavailable_reason',
          'current_supply_raw','current_supply_scale','current_supply_capacity_raw','current_supply_capacity_scale',
          'merge_supply_destination_weight_raw','merge_supply_destination_weight_scale') if k in army} for army in armies]
        frame={k:s[k] for k in ('snapshot_id','revision','native_revision','date_raw','episode_run_id',
                 'paused','map_ready','played_character','player_armies')}
        frame['diagnostics']={k:s['diagnostics'][k] for k in ('bridge_pid','connection_generation','connected','hello')}
        return {'frame':frame,'excluded_unavailable_cohorts':excluded,
          'strategy_army_ids':ids if selected else None,
          'unrelated_physical_DATA_coverage':'not_requested' if selected else 'available_cohorts_only',
          'qualified_scope':'only strategy cohort audited; complete snapshot roster retained' if selected else 'selected available pair; unchanged other available cohorts; explicit unavailable row excluded',
          'all_roster_strengths_qualified':False,'R09_full_card_closed':False,
          'query':qp,'commanders':commanders,'capabilities':cap['body'],
          'refs':{'snapshot':sref,'capabilities':cref,'strength_response':qref,'strength_raw':actual,
                  'commanders':commander_refs,'same_frame_readback':checkref},
          'literal_projection_only':True,'raw_CUnit_type_or_178_published':False,
          'CUnit_CArmy_type_source':'native roster CUnit+10; strengths ReadArmyStrengthRow resolves CUnit full generation then CUnit+178 CArmy full generation; source-pinned ck3_11906.cpp:8282-8298 reused by actual4 adapter'}
    def saved(self,name):
        p=self.case/(name+'.actual.json');value=load(p);need(value['binding']==self.binding,'stage runtime differs')
        def verify_refs(value):
            if isinstance(value,dict):
                if {'path','bytes','sha256'}<=set(value):verify_pin(value)
                else:
                    for child in value.values():verify_refs(child)
        verify_refs(value['packet']['refs'])
        return value
    def save_packet(self,name,packet,**extra):
        return write_new(self.case/(name+'.actual.json'),{**self.meta,'packet':packet,**extra})
    def baseline(self,*,strategy_scope=False,raw_file_limit=None):
        need(not (self.case/'split.once.claim.json').exists(),'split already claimed; baseline cannot reset case')
        packet=self.packet('baseline',army_ids=[self.a.army_id] if strategy_scope else None,raw_file_limit=raw_file_limit);need(self.a.army_id in roster(packet['frame']),'Root selected source absent')
        return self.save_packet('baseline',packet,source_army_id=self.a.army_id,live_split_merge_qualification=False,R09_full_card_closed=False)
    def submit_once(self,kind):
        phase='baseline' if kind=='split' else 'pre-merge' if (self.case/'pre-merge.actual.json').exists() else 'post-split'
        before=self.saved(phase)
        if kind=='merge' and phase=='post-split':need(before['split_assertion']['accepted'] is True,'fresh split assertions not accepted')
        source=before['source_army_id'];ids=[source]
        if kind=='split':step='split-army-half-'+str(source)
        else:
            ids=(before['merge_army_ids'] if phase=='pre-merge' else merge_ids(source,
                 before['split_assertion']['identity']['sibling_army_id'],getattr(self.a,'merge_destination','source')))
            step='merge-armies-'+str(ids[0])+'-with-'+str(ids[1])
        current,sref=self.snapshot(kind+'-current');same_frame(before['packet']['frame'],current)
        caps,cref=self.request(kind+'-current-capabilities','ck3_get_capabilities',{})
        gate=action_gate(current,caps['body'],step,kind,ids,self.binding['actor'])
        name=kind+'-once';identifier=self.a.attempt+'-'+str(self.serial+1).zfill(3)+'-'+name
        arguments={'step':step,'expected_revision':current['revision']}
        claim={**self.meta,'kind':kind,'step':step,'arguments':arguments,'source_army_id':source,
          'army_ids':ids,'before_phase':phase,
          'request_id':identifier,'request_path':str(self.run/'requests'/(identifier+'.json')),
          'response_path':str(self.run/'responses'/(identifier+'.json')),'gate':gate,
          'pre_submit_snapshot':sref,'pre_submit_capabilities':cref,'outcome':'unknown_until_original_read',
          'no_replay_even_if_rejected_or_timeout':True}
        claim_pin=write_new(self.case/(kind+'.once.claim.json'),claim)
        row,refs=self.request(name,'ck3_execute_step',arguments)
        result={**self.meta,'claim':claim_pin,'response':refs,'body':row.get('body'),
          'actual_native_validator_and_queue_accepted':row.get('body',{}).get('accepted') is True,
          'independent_postcondition_observed':False,'action_retry_allowed':False}
        receipt=write_new(self.case/(kind+'.submission.actual.json'),result)
        need(result['actual_native_validator_and_queue_accepted'] and row.get('body',{}).get('step')==step,
             'native rejection/mismatch preserved; stop, never bypass sea legality or retry')
        return receipt
    def original(self,kind):
        claim=load(self.case/(kind+'.once.claim.json'));need(claim['binding']==self.binding,'claim runtime differs')
        req=load(claim['request_path']);need(req.get('request_id')==claim['request_id'] and req.get('arguments')==claim['arguments'],'original request differs')
        row=load(claim['response_path']);need(row.get('machine_id')==MACHINE
          and row.get('request',{}).get('request_id')==claim['request_id'] and row.get('is_error') is False
          and row.get('body',{}).get('accepted') is True and row.get('body',{}).get('step')==claim['step'],
          'original pending/rejected/unknown; inspect exact response, never resubmit')
        return claim,{'request':pin(claim['request_path']),'response':pin(claim['response_path'])}
    def unchanged_others(self,before,after,selected):
        pre={r['army_id']:r for r in before['query']['army_strengths']}
        post={r['army_id']:r for r in after['query']['army_strengths']}
        pre_ex={row['army_id']:row for row in before['excluded_unavailable_cohorts']}
        post_ex={row['army_id']:row for row in after['excluded_unavailable_cohorts']}
        need(set(pre_ex)==set(post_ex),'unavailable exclusion identity/status changed')
        for identity in pre_ex:
            need(pre_ex[identity]['unavailable_reason']==post_ex[identity]['unavailable_reason']
                 and pre_ex[identity]['snapshot_roster_binding']==post_ex[identity]['snapshot_roster_binding'],
                 'unavailable Army reason/roster identity/owner/position changed')
        ids=sorted(set(pre)-set(selected)-set(pre_ex));need(set(ids)<=set(post),'unrelated Army disappeared')
        need(all(post[i]['status']=='available' for i in ids),'previously available unrelated Army became unavailable')
        value=self.observation.compare_split_merge_cohorts([pre[i] for i in ids],[post[i] for i in ids])
        value.update(excluded_unavailable_cohorts=list(post_ex.values()),all_roster_strengths_qualified=False)
        need(value['frozen_exact_cohort_pass'],'unrelated Army cohort changed')
        return value
    def post_split(self,*,strategy_scope=False,raw_file_limit=None):
        claim,original=self.original('split');before=self.saved('baseline')
        source=before['source_army_id']
        after=self.packet('post-split',army_ids=[source] if strategy_scope else None,
          split_before_roster=list(roster(before['packet']['frame'])) if strategy_scope else None,raw_file_limit=raw_file_limit)
        observed=self.save_packet('post-split-observation',after,original_action=original,
          qualification='Independent packet only; assertions have not run')
        source=before['source_army_id']
        result=self.consumer.assert_fresh_split_transfer_12004(before['packet']['frame'],after['frame'],source_army_id=source,
          pre_strengths=before['packet']['query'],post_strengths=after['query'],pre_commander=before['packet']['commanders'][str(source)],
          post_commanders={int(k):v for k,v in after['commanders'].items()})
        unchanged=({'coverage':'not_requested','only_strategy_cohort_audited':True} if strategy_scope
                   else self.unchanged_others(before['packet'],after,[source]))
        old={v['army_id']:v for v in before['packet']['query']['army_strengths']}
        new={v['army_id']:v for v in after['query']['army_strengths']}
        supply_fields=('current_supply_raw','current_supply_scale','current_supply_capacity_raw','current_supply_capacity_scale')
        split_supply={'before':{k:old[source].get(k) for k in supply_fields},
          'after':{str(i):{k:new[i].get(k) for k in supply_fields} for i in (source,result['identity']['sibling_army_id'])},
          'capacity_inferred_from_clone':False,'upper_clamp_observed':False}
        ref=self.save_packet('post-split',after,source_army_id=source,split_assertion=result,original_action=original,
          split_supply_observed=split_supply,observation=observed,unrelated_cohorts=unchanged,dynamic_video_qualification=False,recording_started_by_this_helper=False,R09_full_card_closed=False)
        need(result['accepted'],'complete split postcondition refused; keep actual packet and do not retry')
        return ref
    def post_merge(self):
        claim,original=self.original('merge');before=self.saved(claim.get('before_phase','post-split'));after=self.packet('post-merge')
        observed=self.save_packet('post-merge-observation',after,original_action=original,
          qualification='Independent packet only; assertions have not run')
        first,last=before['packet']['frame'],after['frame'];self.observation._fresh_pair(first,last)
        ids=claim['army_ids'];old=roster(first);new=roster(last)
        need(set(new)==set(old)-{ids[1]} and ids[0] in new,'independent merge roster is not exact source-removal delta')
        pre={v['army_id']:v for v in before['packet']['query']['army_strengths']}
        post={v['army_id']:v for v in after['query']['army_strengths']}
        need(pre[ids[0]]['native_carmy_id']==post[ids[0]]['native_carmy_id'],'destination CArmy generation changed')
        compare=self.observation.compare_split_merge_cohorts([pre[i] for i in ids],[post[ids[0]]])
        data=compare_data_roles(self.consumer,[pre[i] for i in ids],[post[ids[0]]])
        unchanged=self.unchanged_others(before['packet'],after,ids)
        commanders_before={str(i):self.observation.read_bound_current_commander(before['packet']['commanders'][str(i)],first,
          army_id=i,native_carmy_id=pre[i]['native_carmy_id']) for i in ids}
        commander_after=self.observation.read_bound_current_commander(after['commanders'][str(ids[0])],last,
          army_id=ids[0],native_carmy_id=post[ids[0]]['native_carmy_id'])
        old_commanders=set(commanders_before.values())-{None}
        data['old_commander_role_rows_after']=[r for r in data['roles_after']
          if (r.get('native_character_role_v1') or {}).get('resolved_character_id') in old_commanders]
        data.update(actual_commanders_before=commanders_before,actual_commander_after=commander_after,
          exact_source_removal_observed=True,current_commander_distinct_from_Character_and_Knight=True,
          current_commander_only_change_not_REQUIRED=True,dynamic_video_qualification=False)
        supply=compare_merge_supply(before['packet'],after,ids)
        ref=self.save_packet('post-merge',after,source_army_id=ids[0],merge_cohort=compare,merge_DATA_roles=data,merge_supply=supply,
          observation=observed,unrelated_cohorts=unchanged,original_action=original,R09_full_card_closed=False,
          video_claim='Use only actual listed DATA/role/commander differences. Producer cause remains source evidence; no dynamic shot credit.',
          agent_conclusion='MERGE_DATA_CONSERVED_WITH_SEPARATE_ROLE_CHANGES' if data['accepted'] else 'MERGE_DATA_POSTCONDITION_REFUSED')
        need(data['accepted'],'complete merge DATA postcondition refused; preserve actual differences, no retry')
        return ref

    def pre_merge(self):
        need(not (self.case/'merge.once.claim.json').exists(),'merge claim already exists; inspect original')
        if getattr(self.a,'merge_source_army_id',None) is not None:
            need(not (self.case/'split.once.claim.json').exists(),'explicit existing pair cannot replace a split pair')
            ids=merge_ids(self.a.army_id,self.a.merge_source_army_id,getattr(self.a,'merge_destination','source'))
        else:
            split=self.saved('post-split');need(split['split_assertion']['accepted'],'split not qualified')
            ids=merge_ids(split['source_army_id'],split['split_assertion']['identity']['sibling_army_id'],getattr(self.a,'merge_destination','source'))
        after=self.packet('pre-merge')
        observed=self.save_packet('pre-merge-observation',after,source_army_id=self.a.army_id,merge_army_ids=ids,
          qualification='Independent packet only; premerge gates have not run',R09_full_card_closed=False)
        rows={v['army_id']:v for v in after['query']['army_strengths']}
        need(all(rows.get(i,{}).get('status')=='available' for i in ids),'actual merge pair unavailable')
        if getattr(self.a,'merge_source_army_id',None) is None:
            first=split['packet']['frame'];last=after['frame']
            if frame_key(first)!=frame_key(last):self.observation._fresh_pair(first,last)
            need(set(roster(first))==set(roster(last)),'premerge changed split roster')
            pre={v['army_id']:v for v in split['packet']['query']['army_strengths']}
            need(all(pre[i]['native_carmy_id']==rows[i]['native_carmy_id'] for i in ids),'premerge pair generation changed')
            old=self.consumer._observe([a for a in pre.values() if a['status']=='available'])
            new=self.consumer._observe([a for a in rows.values() if a['status']=='available'])
            need(old[1:]==new[1:],'premerge physical DATA/occurrence changed after split')
        step='merge-armies-'+str(ids[0])+'-with-'+str(ids[1])
        action_gate(after['frame'],after['capabilities'],step,'merge',ids,self.binding['actor'])
        return self.save_packet('pre-merge',after,source_army_id=self.a.army_id,merge_army_ids=ids,observation=observed,
          qualification='Fresh complete pair before one merge; no cap guarantee',R09_full_card_closed=False)

    def supply_clamp(self):
        claim,original=self.original('merge');before=self.saved(claim.get('before_phase','post-split'))
        after=self.saved('post-merge')
        need(after['merge_DATA_roles']['accepted'] is True and after['merge_DATA_roles']['exact_source_removal_observed'] is True,
             'complete same-date independent merge DATA postcondition has not passed')
        value=compare_merge_supply(before['packet'],after['packet'],claim['army_ids'])
        return write_new(self.attempt/'SUPPLY-CLAMP.actual.json',{**self.meta,'result':value,'original_action':original,
          'new_native_requests':0,'R09_full_card_closed':False,'dynamic_video_qualification':False})

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=('baseline','split-once','post-split','pre-merge','merge-once','post-merge','supply-clamp'))
    for name in ('repo','context','runtime-proof','request-helper'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('self-sha256','context-sha256','runtime-proof-sha256','request-helper-sha256','run-id','case-id','attempt'):
        p.add_argument('--'+name,required=True)
    p.add_argument('--resume-baseline-strength-response',type=Path,help='Baseline-only exact original39MB strengths response; fresh same-frame/caps/scope required, no new strengths query')
    p.add_argument('--army-id',type=int,required=True)
    p.add_argument('--source-head',default=SOURCE,help='Exact actual normal build/context/proof Git source; no inferred upgrade')
    p.add_argument('--run-sequence',type=int,default=176,help='Exact independently allocated actual run sequence')
    p.add_argument('--module-pins',type=Path);p.add_argument('--module-pins-sha256')
    p.add_argument('--merge-destination',choices=('source','sibling'),default='source')
    p.add_argument('--merge-source-army-id',type=int,help='pre-merge only: explicit existing pair for distinct-stock/cap observation, no split')
    args=p.parse_args();live=None
    try:
        live=Relay(args)
        stages={'baseline':live.baseline,'split-once':lambda:live.submit_once('split'),'post-split':live.post_split,
                'pre-merge':live.pre_merge,'merge-once':lambda:live.submit_once('merge'),'post-merge':live.post_merge,
                'supply-clamp':live.supply_clamp}
        result=stages[args.stage]();receipt=write_new(live.attempt/'RESULT.actual.json',{**live.meta,'result':result})
        print(json.dumps(receipt));return 0
    except BaseException as error:
        if live is not None:
            write_new(live.attempt/'FAILURE.actual.json',{**live.meta,'error_type':type(error).__name__,
              'error':str(error)[:4000],'original_response_pending':live.pending,'action_retry_allowed':False,
              'Root_recovery':'Read exact original request/response and fresh state only; never remove onceclaim or submit again.'})
        raise
if __name__=='__main__':raise SystemExit(main())
